"""
EXPERIMENT — Phase-2 full-length clean absolute-sample dubbing (Lesson 10)
=========================================================================
Adapted from the proven Lesson 01 clean_timesync_v2 pipeline
(build_clean_v2.py) and Lesson 06/07/09 build_lXX_clean.py.

Guarantees (identical to the proven pipeline):
  1. edge_tts bn-BD-PradeepNeural, robust retries: 0-byte purge, 12 attempts,
     half-split and sentence-split fallbacks, plus a WinError 1450 subprocess
     retry in run().
  2. Absolute sample placement: start * 44100 -> ZERO cumulative drift.
  3. atempo fit <= 2.2x; PAD ONLY, NEVER truncate. NO SFX: clean speech only.
  4. Expand a tail cue when its Bengali TTS is much shorter than its window;
     cap the final cue so speech ends inside the video.
  5. Canvas padded to the FULL original video duration (+1 s guard) so
     -shortest never trims a single video frame (Lesson 04's trim bug).
  6. loudnorm -14 LUFS; mux with the FULL original video, -c:v copy.

The Lesson 10 master script is a FLAT list of cues carrying absolute start /
end / duration (seconds). Its authored span is laid out onto the full video
[LEAD_IN, vend - TAIL_MARGIN] with a single linear scale (same trick as
L06/L07/L09), so the narration paces the entire lesson with a silent intro
and outro. Drift stays zero because every cue is still placed at its absolute
sample offset (start * 44100).

Everything is written under NEW experiment folders. Teacher audio, manifests
and other lessons are untouched.
"""
import os
import re
import json
import time
import asyncio
import subprocess
import wave
from pathlib import Path

import numpy as np
import edge_tts

EXP = Path(__file__).resolve().parent
BASE = EXP.parent.parent                       # .../lesson_10_cross_products/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"         # .../3blue1brown_courses/web_platform
SCRIPT_JSON = BASE / "3b1b_lesson_10_bangla_master_script.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_10" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "lesson_10" / "experiments" / "3b1b_lesson_10_full_dubbed.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
FADE_MS = 12

# Silence margins: keep 0-2 s and the final 2 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
# Guard appended to the canvas so the AAC stream is always >= the video
# stream and -shortest cannot trim any video frames.
CANVAS_GUARD_SEC = 1.0

# Extra Bengali narration appended to a closing cue ONLY when its natural TTS
# is much shorter than its (scaled) visual window — data-driven, never blind.
# Lesson 10 has 36 flat narration cues (IDs 1-36); the last three are 34-36.
TAIL_EXPANSIONS = {
    34: (" আজ আমরা দেখেছি ক্রস প্রোডাক্টের জ্যামিতিক সংজ্ঞা আর বীজগাণিতিক "
         "ডিটারমিন্যান্ট কীভাবে একই বাস্তবতার দুটি রূপ; ডুয়ালিটির এই উপলব্ধিই "
         "আরও উন্নত গণিতের দ্বার খুলে দেয়।"),
    35: (" আর এই কারণেই বেসিস ভেক্টরগুলোকে ডিটারমিন্যান্টের প্রথম সারিতে "
         "বসানো হয়—প্রতিটি বেসিসের ওপর রূপান্তর প্রয়োগ করে আমরা ডুয়াল ভেক্টর "
         "পি এর স্থানাঙ্ক পাই। এটি কোনো কৃত্রিম মুখস্থ কৌশল নয়, বরং রৈখিক "
         "বীজগণিতেরই স্বাভাবিক ও সুন্দর ফলাফল।"),
    36: (" আজ আমরা দেখেছি ডট প্রোডাক্ট, ডিটারমিন্যান্ট ও ক্রস প্রোডাক্টের মাঝে "
         "যে গভীর সংযোগ রয়েছে, তা ডুয়ালিটির মাধ্যমে স্পষ্ট হয়ে ওঠে। এই "
         "দৃষ্টিভঙ্গি মনে রাখলেই রৈখিক বীজগণিতের পরবর্তী অধ্যায়গুলো অনেক "
         "সহজ হবে। আবার দেখা হবে!"),
}


def run(cmd):
    """subprocess runner with a WinError 1450 (resource exhaustion) retry."""
    last = None
    for attempt in range(8):
        try:
            r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
            if r.returncode != 0:
                raise RuntimeError(f"cmd failed: {cmd}\n{r.stderr[-1500:]}")
            return r.stdout
        except OSError as e:
            # Windows: WinError 1450 = insufficient system resources (handles /
            # threads) while spawning cmd.exe / ffmpeg. Transient -> retry.
            if getattr(e, "winerror", None) == 1450 or "1450" in str(e):
                last = e
                if attempt < 7:
                    time.sleep(0.25 * (attempt + 1))
                    continue
            raise
    raise RuntimeError(f"subprocess repeatedly failed with WinError 1450: {cmd}\n{last}")


def duration(path):
    out = run(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{path}"')
    try:
        return float(out.strip())
    except Exception:
        return 0.0


def video_duration(path):
    """Full canvas length = max(container, video-stream) so -shortest cannot trim."""
    d = duration(path)
    try:
        sd = float(run(f'ffprobe -v error -select_streams v:0 -show_entries stream=duration '
                       f'-of default=noprint_wrappers=1:nokey=1 "{path}"').strip())
        d = max(d, sd)
    except Exception:
        pass
    return d


def sanitize(text):
    t = text
    for ch in ["—", "–", "−", "-"]:
        t = t.replace(ch, ", ")
    for ch in ["'", '"', "[", "]", "{", "}", "*", "#", "`"]:
        t = t.replace(ch, " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t.strip(" ,;:।.")


async def tts_save(text, path, rate="+0%"):
    await edge_tts.Communicate(text, VOICE, rate=rate).save(str(path))


def valid(raw):
    return raw.exists() and raw.stat().st_size > 500 and duration(raw) > 0.3


def purge(path):
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass


async def synth(text, raw, force=False):
    """Purge 0-byte, 12 attempts, half-split + sentence-split fallbacks."""
    if not force and valid(raw):
        return True
    purge(raw)  # 0-byte purge
    ok = False
    for attempt in range(12):
        try:
            rate = "+0%" if attempt < 4 else ("-5%" if attempt < 8 else "+5%")
            await tts_save(text, raw, rate)
            if valid(raw):
                ok = True
                break
        except Exception:
            pass
        purge(raw)
        if attempt < 11:
            await asyncio.sleep(0.4)
    if not ok:
        # Fallback 1: split into two halves and concatenate.
        mid = len(text) // 2
        parts = [text[:mid].strip(" ,;:।."), text[mid:].strip(" ,;:।.")]
        made = []
        for j, p in enumerate(parts):
            pp = RAW_DIR / f"half_{raw.stem}_{j}.mp3"
            purge(pp)
            if not p:
                continue
            try:
                await tts_save(p, pp)
                if valid(pp):
                    made.append(pp)
            except Exception:
                pass
        if made:
            lf = RAW_DIR / f"list_{raw.stem}.txt"
            with open(lf, "w", encoding="utf-8") as f:
                for x in made:
                    f.write(f"file '{x.as_posix()}'\n")
            run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{raw}" > NUL 2>&1')
            ok = valid(raw)
    if not ok:
        # Fallback 2: synthesize sentence by sentence and concatenate.
        parts = [p.strip() for p in re.split(r"[।]", text) if p.strip()]
        made = []
        for j, p in enumerate(parts):
            pp = RAW_DIR / f"sent_{raw.stem}_{j}.mp3"
            purge(pp)
            try:
                await tts_save(p + "।", pp)
                if valid(pp):
                    made.append(pp)
            except Exception:
                pass
        if made:
            lf = RAW_DIR / f"sentlist_{raw.stem}.txt"
            with open(lf, "w", encoding="utf-8") as f:
                for x in made:
                    f.write(f"file '{x.as_posix()}'\n")
            run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{raw}" > NUL 2>&1')
            ok = valid(raw)
    return ok


def load_cues(vend):
    """Lay the flat master-script timeline onto the full video.

    The master script provides absolute start/end/duration (seconds) but its
    authored span (0 -> 358.5 s) is shorter than the full lesson video. Scale
    the whole timeline linearly into [LEAD_IN, vend - TAIL_MARGIN] so speech
    paces the entire video, keeping the authored inter-cue pauses proportional.
    """
    with open(SCRIPT_JSON, encoding="utf-8") as f:
        data = json.load(f)

    raw = []
    for c in data:
        raw.append({
            "text": c["bn"],
            "authored_start": float(c["start"]),
            "authored_end": float(c["end"]),
            "dur": float(c["duration"]),
        })

    first_start = min(c["authored_start"] for c in raw)
    authored_end = max(c["authored_end"] for c in raw)
    authored_span = authored_end - first_start
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    scale = usable / authored_span if authored_span > 0 else 1.0

    cues = []
    for i, c in enumerate(raw):
        start = LEAD_IN_SEC + (c["authored_start"] - first_start) * scale
        dur = c["dur"] * scale
        cues.append({
            "id": i + 1,
            "start": round(start, 3),
            "end": round(start + dur, 3),
            "duration": round(dur, 3),
            "bn": c["text"],
            "authored_start": c["authored_start"],
            "section": "narration",
            "index_in_section": i + 1,
        })
    return cues, scale


async def synth_all(cues):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, c in enumerate(cues):
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        ok = await synth(sanitize(c["bn"]), raw)
        if not ok:
            failed.append(c["id"])
            print(f"  WARNING cue {c['id']} failed after every fallback", flush=True)
        if (i + 1) % 10 == 0:
            print(f"  TTS {i+1}/{len(cues)}", flush=True)
    return failed


async def expand_tail_cues(cues):
    """Append richer wording to closing cues whose TTS is short of the window."""
    expanded = []
    last_ids = {c["id"] for c in cues[-3:]}
    for c in cues:
        if c["id"] not in last_ids or c["id"] not in TAIL_EXPANSIONS:
            continue
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        target = float(c["duration"])
        natural = duration(raw)
        if 0 < natural < 0.85 * target:
            new_text = sanitize(c["bn"] + " " + TAIL_EXPANSIONS[c["id"]])
            print(f"  expanding cue {c['id']}: natural={natural:.2f}s < {0.85*target:.2f}s", flush=True)
            if await synth(new_text, raw, force=True):
                expanded.append({"id": c["id"],
                                 "natural_before": round(natural, 3),
                                 "natural_after": round(duration(raw), 3)})
    return expanded


def read_pcm(path):
    norm = path.with_suffix(".norm.wav")
    run(f'ffmpeg -y -i "{path}" -af aresample=44100 -ar 44100 -ac 1 -c:a pcm_s16le "{norm}" > NUL 2>&1')
    with wave.open(str(norm), "rb") as w:
        arr = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    try:
        os.remove(norm)
    except OSError:
        pass
    return arr


LAST_START = 0.0
VIDEO_END = 0.0
LAST_ID = None


def make_cue(raw, target, out, cid):
    """atempo-fit into the window; PAD only, NEVER truncate."""
    natural = duration(raw)
    if natural <= 0:
        natural = target
    if cid == LAST_ID:
        # Final cue must finish INSIDE the video, with a small safety margin.
        target = min(target, VIDEO_END - LAST_START - 0.10)
    tempo = max(1.0, min(MAX_TEMPO, natural / target))
    tmp = out.with_suffix(".fit.wav")
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)
    need = int(round(target * SR))
    if len(arr) < need:
        arr = np.pad(arr, (0, need - len(arr)))     # pad only, never cut
    # If still longer (tempo cap), keep it -> recorded as overrun, never cut.
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(arr, -1, 1) * 32767).astype("<i2").tobytes())
    try:
        os.remove(tmp)
    except OSError:
        pass
    return arr, tempo, natural, target


def volumedetect(path, start, length):
    out = run(f'ffmpeg -hide_banner -i "{path}" -af '
              f'atrim=start={start}:duration={length},volumedetect -f null - 2>&1')
    m = re.search(r"mean_volume:\s*([-\d.]+) dB", out)
    return float(m.group(1)) if m else None


async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    cues, scale = load_cues(vend)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"video duration = {vend:.3f}s; cues = {len(cues)}; timeline scale = {scale:.4f}", flush=True)

    print("[1/5] TTS (clean, no SFX) ...", flush=True)
    failed = await synth_all(cues)

    print("[2/5] Conditional tail-cue expansion ...", flush=True)
    expanded = await expand_tail_cues(cues)

    print("[3/5] Absolute sample placement (start*44100, pad-only) ...", flush=True)
    # FULL-length canvas (+ guard): -shortest can never trim the video.
    canvas = np.zeros(int(round((vend + CANVAS_GUARD_SEC) * SR)), dtype=np.float32)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    overrun = 0
    last_cue_end = 0.0
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            print(f"  SKIP cue {cid} (no audio)", flush=True)
            continue
        arr, tempo, natural, target = make_cue(
            raw, float(c["duration"]), CUE_DIR / f"cue_{cid:03d}.wav", cid)
        if len(arr) >= 2 * fade_n:
            arr[:fade_n] *= env
            arr[-fade_n:] *= env[::-1]
        start_sample = int(round(float(c["start"]) * SR))
        end = start_sample + len(arr)
        if end > len(canvas):
            canvas = np.pad(canvas, (0, end - len(canvas)))
        canvas[start_sample:end] += arr
        if len(arr) > int(float(c["duration"]) * SR) + 200:
            overrun += 1
        last_cue_end = max(last_cue_end, end / SR)
        expected_ms = round(float(c["start"]) * 1000, 2)
        actual_ms = round(start_sample / SR * 1000, 2)
        placed.append({
            "id": cid,
            "section": c["section"],
            "authored_start_ms": round(c["authored_start"] * 1000, 2),
            "expected_start_ms": expected_ms,
            "actual_start_ms": actual_ms,
            "drift_ms": round(actual_ms - expected_ms, 6),
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3),
            "target_sec": round(target, 3),
            "placed_samples": len(arr),
            "expanded": cid in [x["id"] for x in expanded],
        })

    peak = float(np.max(np.abs(canvas))) or 1.0
    if peak > 0.98:
        canvas *= 0.98 / peak

    print("[4/5] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(canvas, -1, 1) * 32767).astype("<i2").tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    report = {
        "experiment": "clean_timesync_v2 (lesson_10 full-length)",
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": "absolute sample offset (start*44100); atempo fit; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "drift_note": "sub-sample rounding only (<0.02 ms); no cumulative drift — every cue placed at absolute sample offset start*44100",
        "timeline_scale": round(scale, 6),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "canvas_guard_sec": CANVAS_GUARD_SEC,
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "tail_expansions_applied": expanded,
        "cues": placed,
    }

    print("[5/5] Mux with FULL original video (video copy) ...", flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    report["output_video"] = str(OUT_VIDEO)
    report["output_duration_sec"] = round(duration(OUT_VIDEO), 3)
    report["output_size_bytes"] = OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0
    try:
        probe = json.loads(run(f'ffprobe -v error -show_entries stream=index,codec_type,codec_name '
                                f'-of json "{OUT_VIDEO}"'))
        report["output_streams"] = probe.get("streams", [])
    except Exception as e:
        report["output_streams_error"] = str(e)

    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    odur = duration(OUT_VIDEO)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={report['output_duration_sec']}s size={report['output_size_bytes']}", flush=True)
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
