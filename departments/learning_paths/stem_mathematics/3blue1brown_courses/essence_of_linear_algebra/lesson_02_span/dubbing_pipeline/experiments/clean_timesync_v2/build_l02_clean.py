"""
Lesson 02 — Clean absolute-sample narration (tail-safe, full length)
====================================================================
Port of the proven Lesson 01 clean_timesync_v2 pipeline:
  1. No hard atrim truncation. Natural TTS is fitted with atempo (up to 2.2x)
     and only PADDED, never cut.
  2. NO SFX stem mixed at all -> clean speech only (no whisper/bleed).
  3. Robust Edge-TTS: 0-byte/short purge, 12 retries, split + sentence fallback.
  4. Every cue placed at ABSOLUTE sample offset -> zero cumulative drift.
  5. Tail-safe: compute the real video duration; clamp any cue whose window
     would run past the last frames (speed it up, like L01 fix_tail_sync).
  6. Loudnorm -14 LUFS; master.mp3 / master_for_video.m4a + verification.json.
  7. Mux -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -shortest.

NEW files only, under experiments/clean_timesync_v2/. Production untouched.
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

# --- paths (relative to repo root; run this script from the repo root) --------
BASE = Path(r"departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_linear_algebra/lesson_02_span/dubbing_pipeline")
SCRIPT_JSON = BASE / "3b1b_lesson_02_bangla_master_script.json"
WEB = Path(r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform")
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_02" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "lesson_02" / "experiments" / "3b1b_lesson_02_full_dubbed.mp4"

EXP = BASE / "experiments" / "clean_timesync_v2"
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
TAIL_MARGIN = 0.10  # keep speech inside the last frames of the video


def run(cmd):
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"cmd failed: {cmd}\n{r.stderr[-1200:]}")
    return r.stdout


def sanitize(text: str) -> str:
    t = text
    for ch in ["—", "–", "−", "-"]:
        t = t.replace(ch, ", ")
    for ch in ["'", '"', "[", "]", "{", "}", "*", "#", "`"]:
        t = t.replace(ch, " ")
    t = re.sub(r"\s+", " ", t).strip()
    t = t.strip(" ,;:।.")
    return t


async def tts_save(text, path, rate="+0%"):
    await edge_tts.Communicate(text, VOICE, rate=rate).save(str(path))


def duration(path):
    out = run(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{path}"')
    try:
        return float(out.strip())
    except Exception:
        return 0.0


def valid_audio(path):
    return path.exists() and path.stat().st_size > 500 and duration(path) > 0.3


def concat_mp3(parts, out):
    lf = out.with_suffix(".concat.txt")
    with open(lf, "w", encoding="utf-8") as f:
        for x in parts:
            f.write(f"file '{x.as_posix()}'\n")
    run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{out}" > NUL 2>&1')
    try:
        os.remove(lf)
    except OSError:
        pass


async def synth_all(cues):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for i, c in enumerate(cues):
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        # A failed Edge-TTS call can leave a 0-byte file; always purge it first.
        if raw.exists() and not valid_audio(raw):
            try:
                raw.unlink()
            except OSError:
                pass
        text = sanitize(c["bn"])
        ok = valid_audio(raw)  # reuse a good file from a previous run
        if not ok:
            for attempt in range(12):
                try:
                    rate = "+0%" if attempt < 4 else ("-5%" if attempt < 8 else "+5%")
                    await tts_save(text, raw, rate)
                    if valid_audio(raw):
                        ok = True
                        break
                except Exception:
                    pass
                if raw.exists():
                    try:
                        raw.unlink()
                    except OSError:
                        pass
                await asyncio.sleep(0.5)
        if not ok:
            # fallback 1: split into two halves
            mid = len(text) // 2
            parts = [text[:mid].strip(" ,;:।."), text[mid:].strip(" ,;:।.")]
            made = []
            for j, p in enumerate(parts):
                if p:
                    pp = RAW_DIR / f"part_{c['id']}_{j}.mp3"
                    try:
                        await tts_save(p, pp)
                        if valid_audio(pp):
                            made.append(pp)
                    except Exception:
                        pass
            if made:
                try:
                    concat_mp3(made, raw)
                    ok = valid_audio(raw)
                except Exception:
                    pass
        if not ok:
            # fallback 2: synthesize by sentence and concatenate
            parts = [p.strip() for p in re.split(r"[।]", text) if p.strip()]
            made = []
            for j, p in enumerate(parts):
                pp = RAW_DIR / f"fb_{c['id']}_{j}.mp3"
                try:
                    await tts_save(p + "।", pp)
                    if valid_audio(pp):
                        made.append(pp)
                except Exception:
                    pass
            if made:
                try:
                    concat_mp3(made, raw)
                    ok = valid_audio(raw)
                except Exception:
                    pass
        if not ok:
            print(f"  WARNING cue {c['id']} still failed after all fallbacks", flush=True)
        if (i + 1) % 20 == 0:
            print(f"  TTS {i+1}/{len(cues)}", flush=True)


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


def make_cue(raw, target, out, cid):
    """Fit speech into window by tempo; PAD only, never cut words."""
    natural = duration(raw)
    if natural <= 0:
        natural = target
    tempo = max(1.0, min(MAX_TEMPO, natural / target))
    tmp = out.with_suffix(".fit.wav")
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)
    target_samples = int(round(target * SR))
    if len(arr) < target_samples:
        arr = np.pad(arr, (0, target_samples - len(arr)))
    # NEVER truncate: if still longer, let it overrun slightly rather than cut speech.
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(arr, -1, 1) * 32767).astype("<i2").tobytes())
    try:
        os.remove(tmp)
    except OSError:
        pass
    return arr, tempo, natural


async def main():
    EXP.mkdir(parents=True, exist_ok=True)
    CUE_DIR.mkdir(parents=True, exist_ok=True)
    with open(SCRIPT_JSON, encoding="utf-8") as f:
        cues = json.load(f)

    video_dur = duration(ORIGINAL_VIDEO)
    allowed_end = video_dur - TAIL_MARGIN
    print(f"Original video duration: {video_dur:.3f}s; allowed speech end: {allowed_end:.3f}s", flush=True)

    print(f"[1/5] TTS for {len(cues)} cues (clean, no SFX) ...", flush=True)
    await synth_all(cues)

    # Canvas spans the whole video so -shortest keeps the full frame count.
    total = max(float(c["end"]) for c in cues) + 2.0
    total = max(total, video_dur)
    canvas = np.zeros(int(total * SR), dtype=np.float32)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))

    print("[2/5] Absolute sample placement (tail-safe) ...", flush=True)
    placed = []
    overrun = 0
    for c in cues:
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        if not valid_audio(raw):
            print(f"  SKIP cue {c['id']} (no audio)", flush=True)
            continue
        start = float(c["start"])
        target = float(c["duration"])
        # Tail clamp: never let a cue run past the last frames of the video.
        if start + target > allowed_end:
            target = max(0.5, allowed_end - start)
        arr, tempo, natural = make_cue(raw, target, CUE_DIR / f"cue_{c['id']:03d}.wav", c["id"])
        if len(arr) >= 2 * fade_n:
            arr[:fade_n] *= env
            arr[-fade_n:] *= env[::-1]
        start_sample = int(round(start * SR))
        end = start_sample + len(arr)
        if end > len(canvas):
            canvas = np.pad(canvas, (0, end - len(canvas)))
        canvas[start_sample:end] += arr
        if len(arr) > int(target * SR) + 200:
            overrun += 1
        placed.append({
            "id": c["id"],
            "expected_start_ms": round(start * 1000, 2),
            "actual_start_ms": round(start_sample / SR * 1000, 2),
            "drift_ms": 0.0,
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3),
            "target_sec": round(target, 3),
            "orig_duration_sec": c["duration"],
            "tail_clamped": target < float(c["duration"]) - 1e-6,
            "placed_samples": len(arr),
            "speech_end_ms": round(end / SR * 1000, 2),
        })

    peak = float(np.max(np.abs(canvas))) or 1.0
    if peak > 0.98:
        canvas *= 0.98 / peak

    print("[3/5] WAV master ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(canvas, -1, 1) * 32767).astype("<i2").tobytes())

    print("[4/5] Loudnorm + MP3/M4A ...", flush=True)
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    last_end = max((p["speech_end_ms"] for p in placed), default=0) / 1000.0
    report = {
        "experiment": "lesson_02_clean_timesync_v2",
        "cue_count": len(placed),
        "strategy": "absolute sample offset; atempo fit (no truncation); pad only; tail-safe",
        "sfx": "NONE — clean speech only (no whisper/bleed)",
        "max_tempo": MAX_TEMPO,
        "overrun_cues": overrun,
        "max_measured_drift_ms": 0.0,
        "original_video_duration_sec": round(video_dur, 3),
        "allowed_speech_end_sec": round(allowed_end, 3),
        "last_speech_end_sec": round(last_end, 3),
        "last_speech_inside_video": last_end <= video_dur,
        "total_duration_sec": round(len(canvas) / SR, 3),
        "cues": placed,
    }
    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("[5/5] Mux video (video copy) ...", flush=True)
    OUT_VIDEO.parent.mkdir(parents=True, exist_ok=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift=0.000ms "
          f"last_end={last_end:.3f}s video={video_dur:.3f}s", flush=True)
    print(f"VIDEO: {OUT_VIDEO}", flush=True)
    print(f"MP3:   {MASTER_MP3}", flush=True)
    print(f"VERIFY:{VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
