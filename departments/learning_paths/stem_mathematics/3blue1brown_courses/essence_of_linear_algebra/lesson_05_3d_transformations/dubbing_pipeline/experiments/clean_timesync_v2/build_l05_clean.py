"""
EXPERIMENT — Phase-2 full-length clean absolute-sample dubbing (Lesson 05)
==========================================================================
Adapted from lesson_01 .../clean_timesync_v2/build_clean_v2.py + fix_tail_sync.py.

Rules (identical to the proven pipeline):
  * edge_tts bn-BD-PradeepNeural, robust retries (purge 0-byte, 12 attempts,
    half-split and sentence-split fallbacks).
  * Absolute sample placement: start * 44100 -> zero cumulative drift.
  * atempo fit, PAD ONLY, NEVER truncate. No SFX: clean speech only.
  * Expand a last cue if its Bengali TTS is shorter than its visual window.
  * Speed up the final cue so speech ends before the video end.
  * loudnorm -14 LUFS; mux with the FULL original video, video stream copied.
  * Canvas is padded to the full original duration so -shortest keeps the
    complete 285.8 s video (silent intro/outro -> -91 dB).

Everything is written under NEW experiment folders / the lesson_05 experiments
output folder. Teacher audio, manifests and other lessons are untouched.
"""
import os
import re
import json
import asyncio
import subprocess
import wave
from pathlib import Path

import numpy as np
import edge_tts

EXP = Path(__file__).resolve().parent
BASE = EXP.parent.parent                       # .../lesson_05_3d_transformations/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"         # .../3blue1brown_courses/web_platform
SCRIPT_JSON = BASE / "3b1b_lesson_05_bangla_master_script.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_05" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "lesson_05" / "experiments" / "3b1b_lesson_05_full_dubbed.mp4"

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

# Richer Bengali wording for the closing cues, used ONLY when a cue's natural
# TTS is shorter than its visual window (see expand_tail_cues). Kept here so
# the decision is data-driven, never applied blindly.
TAIL_EXPANSIONS = {
    27: ("সংখ্যাগতভাবে এই গুণন সম্পন্ন করার নিয়মও আগের পর্বের মতোই। প্রতিটি কলামের "
         "সাথে সংশ্লিষ্ট স্থানাঙ্ক পরিচয়ে গুণ করে তারা কীভাবে যোগ হয়ে চূড়ান্ত ফলাফল "
         "তৈরি করে, সেটি অনুসরণ করলেই বিষয়টি পরিষ্কার হয়ে যায়।"),
    28: ("প্রকৃতপক্ষে আগের পর্বটি আপনি কতটা গভীরভাবে বুঝেছেন তা যাচাই করার সেরা "
         "উপায় হলো নিজে নিজে যুক্তি দিয়ে বের করা—দুটি রূপান্তর ধারাবাহিকভাবে ঘটলে "
         "তাদের ম্যাট্রিক্স গুণনের রূপ কেমন হবে। কীভাবে একটি রূপান্তরের পর অন্যটি "
         "প্রয়োগ হয়, সেই ধারণাটির সাথে ম্যাট্রিক্স গুণনের সম্পর্ক মিলিয়ে ভাবুন; "
         "তাহলেই পরবর্তী পর্বের জন্য ভিত্তি মজবুত হবে।"),
    29: ("পরবর্তী পর্বে আমরা লিনিয়ার অ্যালজেবরার অন্যতম চিত্তাকর্ষক বিষয়—ডিটারমিন্যান্ট— "
         "নিয়ে আলোচনা শুরু করব। সেই পর্বে দেখব কীভাবে একটি ম্যাট্রিক্সের ডিটারমিন্যান্ট "
         "রূপান্তরের ফলে স্পেস কতটা প্রসারিত বা সংকুচিত হয় তা বলে দেয়।"),
}


def run(cmd):
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"cmd failed: {cmd}\n{r.stderr[-1500:]}")
    return r.stdout


def duration(path):
    out = run(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{path}"')
    try:
        return float(out.strip())
    except Exception:
        return 0.0


def video_duration(path):
    """True video duration (stream or container), used to size the full canvas."""
    out = run(f'ffprobe -v error -select_streams v:0 -show_entries stream=duration '
              f'-of default=noprint_wrappers=1:nokey=1 "{path}"')
    try:
        d = float(out.strip())
        if d > 0:
            return d
    except Exception:
        pass
    return duration(path)


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


async def synth(text, raw, force=False):
    """12 attempts + half-split + sentence-split fallbacks; purge 0-byte files."""
    if not force and valid(raw):
        return True
    if raw.exists():
        try:
            raw.unlink()                      # purge a partial/0-byte output
        except OSError:
            pass
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
        if raw.exists():
            try:
                raw.unlink()
            except OSError:
                pass
        await asyncio.sleep(0.4)
    if not ok:
        # Fallback 1: split into two halves.
        mid = len(text) // 2
        parts = [text[:mid].strip(" ,;:।."), text[mid:].strip(" ,;:।.")]
        made = []
        for j, p in enumerate(parts):
            pp = RAW_DIR / f"half_{raw.stem}_{j}.mp3"
            if pp.exists():
                try:
                    pp.unlink()
                except OSError:
                    pass
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
            if pp.exists():
                try:
                    pp.unlink()
                except OSError:
                    pass
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


async def synth_all(cues):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for i, c in enumerate(cues):
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        ok = await synth(sanitize(c["bn"]), raw)
        if not ok:
            print(f"  WARNING cue {c['id']} failed after every fallback", flush=True)
        if (i + 1) % 10 == 0:
            print(f"  TTS {i+1}/{len(cues)}", flush=True)


async def expand_tail_cues(cues):
    """Expand closing cues whose Bengali TTS is shorter than the visual window."""
    expanded = []
    last_ids = [c["id"] for c in cues[-3:]]
    for c in cues:
        if c["id"] not in last_ids or c["id"] not in TAIL_EXPANSIONS:
            continue
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        target = float(c["duration"])
        natural = duration(raw)
        if 0 < natural < 0.85 * target:
            print(f"  expanding cue {c['id']}: natural={natural:.2f}s < {0.85*target:.2f}s", flush=True)
            ok = await synth(sanitize(TAIL_EXPANSIONS[c["id"]]), raw, force=True)
            if ok:
                expanded.append({"id": c["id"], "natural_before": round(natural, 3),
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


def make_cue(raw, target, out, video_end, cid, is_last):
    """atempo-fit into the window; PAD only, NEVER truncate."""
    natural = duration(raw)
    if natural <= 0:
        natural = target
    if is_last:
        # Final cue must finish INSIDE the video, with a small safety margin.
        target = min(target, video_end - float(LAST_START) - 0.10)
    tempo = max(1.0, min(MAX_TEMPO, natural / target))
    tmp = out.with_suffix(".fit.wav")
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)
    need = int(round(target * SR))
    if len(arr) < need:
        arr = np.pad(arr, (0, need - len(arr)))     # pad only
    # Never truncate: if still longer (tempo cap), let it overrun slightly.
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(arr, -1, 1) * 32767).astype("<i2").tobytes())
    try:
        os.remove(tmp)
    except OSError:
        pass
    return arr, tempo, natural, target


LAST_START = 0.0


async def main():
    EXP.mkdir(parents=True, exist_ok=True)
    CUE_DIR.mkdir(parents=True, exist_ok=True)
    with open(SCRIPT_JSON, encoding="utf-8") as f:
        cues = json.load(f)

    global LAST_START
    LAST_START = float(cues[-1]["start"])
    vend = video_duration(ORIGINAL_VIDEO)
    print(f"video duration = {vend:.3f}s; cues = {len(cues)}", flush=True)

    print("[1/5] TTS (clean, no SFX) ...", flush=True)
    await synth_all(cues)

    print("[2/5] Conditional tail-cue expansion ...", flush=True)
    expanded = await expand_tail_cues(cues)

    print("[3/5] Absolute sample placement (pad-only) ...", flush=True)
    # Canvas covers the FULL original video so -shortest keeps every frame.
    canvas = np.zeros(int(round(vend * SR)), dtype=np.float32)
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
            raw, float(c["duration"]), CUE_DIR / f"cue_{cid:03d}.wav",
            vend, cid, cid == cues[-1]["id"])
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
        cue_end = end / SR
        last_cue_end = max(last_cue_end, cue_end)
        expected_ms = round(float(c["start"]) * 1000, 2)
        actual_ms = round(start_sample / SR * 1000, 2)
        placed.append({
            "id": cid,
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

    print("[4/5] WAV master + loudnorm ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(canvas, -1, 1) * 32767).astype("<i2").tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    tail_sec = len(canvas) / SR - last_cue_end
    report = {
        "experiment": "clean_timesync_v2 (lesson_05 full-length)",
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "strategy": "absolute sample offset (start*44100); atempo fit; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(tail_sec, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "tail_expansions_applied": expanded,
        "cues": placed,
    }

    print("[5/5] Mux with FULL original (video copy) ...", flush=True)
    OUT_VIDEO.parent.mkdir(parents=True, exist_ok=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    # Post-mux verification data appended to verification.json.
    report["output_video"] = str(OUT_VIDEO)
    report["output_duration_sec"] = round(duration(OUT_VIDEO), 3)
    report["output_size_bytes"] = OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0
    try:
        probe = json.loads(run(f'ffprobe -v error -show_entries stream=index,codec_type,codec_name '
                               f'-of json "{OUT_VIDEO}"'))
        report["output_streams"] = probe.get("streams", [])
    except Exception as e:
        report["output_streams_error"] = str(e)

    def vol(start, length):
        out = run(f'ffmpeg -hide_banner -i "{OUT_VIDEO}" -af '
                  f'afade=in:st=0:d=0,atrim=start={start}:duration={length},volumedetect '
                  f'-f null - 2>&1')
        m = re.search(r"mean_volume:\s*([-\d.]+) dB", out)
        return float(m.group(1)) if m else None

    report["volumedetect_intro_0_2s_db"] = vol(0, 2)
    vdur = duration(OUT_VIDEO)
    report["volumedetect_final_2s_db"] = vol(max(0.0, vdur - 2), 2)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms")
    print(f"video={report['output_duration_sec']}s size={report['output_size_bytes']}")
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB")
    print(f"VERIFY: {VERIFY}")


if __name__ == "__main__":
    asyncio.run(main())
