"""
EXPERIMENT — Full-length clean absolute-sample Bengali dub (Neural Networks, Lesson 01)
======================================================================================
"But what is a neural network?" — YouTube ID aircAruvnKk

Adapted verbatim from the proven clean_timesync_v2 pipeline:
  essence_of_calculus/lesson_05_euler_number/dubbing_pipeline/experiments/clean_timesync_v2/build_calc05_clean.py

Guarantees (identical to the proven pipeline):
   1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
      half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
   2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
   3. atempo fit <= 2.2x; PAD ONLY, NEVER truncate. NO SFX: clean speech only.
   4. Expand a tail cue when its Bengali TTS is much shorter than its window;
      speed the final cue up so speech ends before the video end (final-cue cap).
   5. Canvas padded to the FULL original video duration so -shortest can never
      trim video frames.
   6. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
   7. Lightweight volumedetect (-vn -nostats, log to FILE) on intro 0-2s and
      the final 2s, written into verification.json.

Cue source (read-only; teacher audio / manifests are NEVER modified):
   1. .../lesson_01_intro/dubbing_pipeline/*master_script*.json  (PRIMARY)
      -- NOTE: this master script stores start/end/duration in SECONDS, so
         duration is converted x1000 to milliseconds before layout. The authored
         cues are then cumulatively laid out and scaled to span the FULL video
         (the original is ~1120s while authored cues cover ~700s; scaling is
         expected, exactly as in the proven calculus pipeline).
   2. web_platform/data/neural_networks/lesson_01.json -> audio_manifest (if any).
   3. last resort: derive cues from the sections of lesson_01.json itself.

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
BASE = EXP.parent.parent                        # .../lesson_01_intro/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "neural_networks" / "lesson_01.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "neural_networks" / "lesson_01" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "neural_networks" / "lesson_01" / "experiments" / "3b1b_nn_01_full_dubbed.mp4"

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
VIDEO_ID = "aircAruvnKk"
LESSON = "lesson_01_intro"

# Silence margins: keep 0-2 s and the final 2 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Extra Bengali narration appended to a closing cue ONLY when its natural TTS
# is much shorter than its visual window (data-driven, never applied blindly).
# There are 49 authored cues; the last three are IDs 47-49.
TAIL_EXPANSIONS = {
    47: (" মাত্র কয়েকটি সরল গুণ ও যোগের মাধ্যমেই এই রূপান্তরটি সম্পন্ন হয়। "
         "প্রতিটি স্তর একই নিয়ম অনুসরণ করে, শুধু সংখ্যার মাত্রা বদলায়।"),
    48: (" আর এই একই সমীকরণের ফলাফলের ওপরেই নির্ভর করে আমরা কোন সংখ্যাটি চিনতে "
         "পারব। গঠন জটিল হলেও এর ভিত্তি অত্যন্ত সুন্দর ও সরল।"),
    49: (" পরের পাঠে আমরা দেখব কীভাবে এই নেটওয়ার্ক নিজের ভুল থেকে শিখে নিজের "
         "প্যারামিটারগুলোকে লক্ষ্যভেদীভাবে পরিবর্তন করে। আবার দেখা হবে!"),
}


def is_win1450(err):
    return getattr(err, "winerror", None) == 1450 or "1450" in str(err)


def run(cmd, retries=6):
    """subprocess runner with explicit WinError 1450 / transient-failure retry."""
    last = None
    for attempt in range(retries):
        try:
            r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
            if r.returncode == 0:
                return r.stdout
            last = RuntimeError(f"cmd failed: {cmd}\n{r.stderr[-1500:]}")
        except OSError as e:
            last = e
            if not is_win1450(e):
                raise
        if attempt < retries - 1:
            time.sleep(0.5 * (attempt + 1))
    raise last


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
    """Edge-TTS save with a dedicated WinError 1450 retry."""
    last = None
    for attempt in range(5):
        try:
            await edge_tts.Communicate(text, VOICE, rate=rate).save(str(path))
            return
        except OSError as e:
            last = e
            if not is_win1450(e):
                raise
            await asyncio.sleep(0.5 * (attempt + 1))
        except Exception:
            raise
    if last is not None:
        raise last


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
    purge(raw)
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


def load_master_cues():
    """Read the PRIMARY master script. Its start/end/duration are in SECONDS.

    Convert duration (s) -> milliseconds so the shared layout code works.
    """
    masters = sorted(BASE.glob("*master_script*.json"))
    if not masters:
        return None, None
    mpath = masters[0]
    data = json.loads(mpath.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("cues") or data.get("sections") or []
    out = []
    for c in data:
        if not isinstance(c, dict):
            continue
        text = c.get("bn") or c.get("text")
        if not text:
            continue
        # Master script timing is in seconds -> convert to ms.
        dur_s = c.get("duration")
        if dur_s is None:
            dur_s = (float(c.get("end", 0)) - float(c.get("start", 0)))
        dur_ms = float(dur_s) * 1000.0
        out.append({
            "text": text,
            "dur_ms": dur_ms,
            "section": str(c.get("section", "master")),
        })
    if out:
        return out, f"master_script:{mpath.name} (seconds->ms x1000)"
    return None, None


def derive_from_lesson(lesson):
    """Last-resort cue derivation from the lesson JSON's rich text sections."""
    out = []
    for sec in lesson.get("sections", []):
        sec_id = sec.get("id") or sec.get("alias") or "section"
        texts = []
        q = sec.get("quote") or {}
        if q.get("text_bn"):
            texts.append(q["text_bn"])
        texts.extend(sec.get("paragraphs", []))
        for fm in sec.get("formulas", []):
            if fm.get("caption_bn"):
                texts.append(fm["caption_bn"])
        co = sec.get("callout") or {}
        if co.get("text_bn"):
            texts.append(co["text_bn"])
        if sec.get("closing_thought_bn"):
            texts.append(sec["closing_thought_bn"])
        for t in texts:
            clean = re.sub(r"\$[^\$]*\$", " ", t)          # drop LaTeX math
            clean = re.sub(r"[\\\{\}\[\]#*]", " ", clean)
            clean = re.sub(r"\s+", " ", clean).strip()
            if clean:
                out.append({"text": clean,
                            "dur_ms": max(2000.0, len(clean) * 90.0),
                            "section": sec_id})
    return out


def load_source_cues():
    """Return (list_of_{text,dur_ms,section}, source_description)."""
    # 1) master script (primary) -- durations are in SECONDS
    out, desc = load_master_cues()
    if out:
        return out, desc

    # 2) audio manifest referenced by web_platform/data/neural_networks/lesson_01.json (read-only)
    if LESSON_JSON.exists():
        lesson = json.loads(LESSON_JSON.read_text(encoding="utf-8"))
        rel = lesson.get("audio_manifest") or (lesson.get("meta") or {}).get("audio_manifest")
        if rel:
            manifest = (LESSON_JSON.parent / rel).resolve()
            if manifest.exists():
                data = json.loads(manifest.read_text(encoding="utf-8"))
                out = []
                for sec_id, sec in data.get("sections", {}).items():
                    for c in sec.get("cues", []):
                        out.append({
                            "text": c["text"],
                            "dur_ms": float(c.get("duration_ms", 0)),
                            "section": sec_id,
                        })
                if out:
                    return out, f"audio_manifest:{manifest.name}"
        return derive_from_lesson(lesson), "lesson_01.json:sections"
    return [], "NO SOURCE"


def load_cues(vend, source_cues):
    """Lay the authored cues out cumulatively, then scale to span the full video."""
    authored_total = sum(c["dur_ms"] for c in source_cues) + INTER_CUE_PAUSE_MS * (len(source_cues) - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    scale = usable / (authored_total / 1000.0) if authored_total > 0 else 1.0

    cues = []
    cursor_ms = 0.0
    for i, c in enumerate(source_cues):
        start = LEAD_IN_SEC + (cursor_ms / 1000.0) * scale
        dur = (c["dur_ms"] / 1000.0) * scale
        cues.append({
            "id": i + 1,
            "start": round(start, 3),
            "end": round(start + dur, 3),
            "duration": round(dur, 3),
            "bn": c["text"],
            "section": c["section"],
        })
        cursor_ms += c["dur_ms"] + INTER_CUE_PAUSE_MS
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
    """Audio-only volumedetect; log to a FILE so ffmpeg output never floods RAM."""
    log = EXP / "_volumedetect.log"
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-nostats", "-vn",
        "-i", str(path),
        "-af", f"atrim=start={start}:duration={length},volumedetect",
        "-f", "null", "-",
    ]
    for attempt in range(6):
        try:
            with open(log, "wb") as fh:
                subprocess.run(cmd, stdout=fh, stderr=fh)
            break
        except OSError as e:
            if not is_win1450(e):
                raise
            time.sleep(0.5 * (attempt + 1))
    txt = log.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"mean_volume:\s*([-\d.]+) dB", txt)
    return float(m.group(1)) if m else None


async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    source_cues, source_desc = load_source_cues()
    if not source_cues:
        raise RuntimeError("No cue source found -- refusing to build an empty dub.")
    cues, scale = load_cues(vend, source_cues)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"video duration = {vend:.3f}s; cues = {len(cues)}; source = {source_desc}; "
          f"timeline scale = {scale:.4f}", flush=True)

    print("[1/5] TTS (clean, no SFX) ...", flush=True)
    failed = await synth_all(cues)

    print("[2/5] Conditional tail-cue expansion ...", flush=True)
    expanded = await expand_tail_cues(cues)

    print("[3/5] Absolute sample placement (start*44100, pad-only) ...", flush=True)
    # FULL-length canvas: -shortest can never trim the video.
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    CHUNK = 1_000_000
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
        i16 = (np.clip(arr, -1.0, 1.0) * 32767.0).astype(np.int16)
        seg = canvas[start_sample:end].astype(np.int32)
        seg += i16.astype(np.int32)
        np.clip(seg, -32768, 32767, out=seg)
        canvas[start_sample:end] = seg.astype(np.int16)
        del arr, i16, seg
        placed_len = int(round(end - start_sample))
        if placed_len > int(float(c["duration"]) * SR) + 200:
            overrun += 1
        last_cue_end = max(last_cue_end, end / SR)
        expected_ms = round(float(c["start"]) * 1000, 2)
        actual_ms = round(start_sample / SR * 1000, 2)
        placed.append({
            "id": cid,
            "section": c["section"],
            "expected_start_ms": expected_ms,
            "actual_start_ms": actual_ms,
            "drift_ms": round(actual_ms - expected_ms, 6),
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3),
            "target_sec": round(target, 3),
            "placed_samples": placed_len,
            "expanded": cid in [x["id"] for x in expanded],
        })

    peak_i = 0
    for i in range(0, len(canvas), CHUNK):
        seg = canvas[i:i + CHUNK]
        peak_i = max(peak_i, int(seg.max()), int(-seg.min()))
    peak_i = peak_i or 1
    if peak_i > 32112:  # 0.98 * 32767
        scale_pk = 32112.0 / peak_i
        for i in range(0, len(canvas), CHUNK):
            seg = canvas[i:i + CHUNK].astype(np.float32)
            seg *= scale_pk
            np.rint(seg, out=seg)
            canvas[i:i + CHUNK] = seg.astype(np.int16)

    print("[4/5] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    report = {
        "experiment": "clean_timesync_v2 (neural_networks lesson_01 full-length)",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": source_desc,
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": "absolute sample offset (start*44100); atempo fit; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "timeline_scale": round(scale, 6),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
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
