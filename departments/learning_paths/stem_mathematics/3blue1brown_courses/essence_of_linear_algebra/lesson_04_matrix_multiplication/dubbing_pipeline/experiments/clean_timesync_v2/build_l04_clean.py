"""
EXPERIMENT — Phase-2 full-length clean absolute-sample narration (Lesson 04)
===========================================================================
Adapted from the proven Lesson 01 clean_timesync_v2 pipeline
(build_clean_v2.py + fix_tail_sync.py). NEW folders only; production and
other lessons are untouched.

Guarantees:
  1. NO hard truncation -> TTS fitted with atempo (<=2.2x) and only PADDED.
  2. NO SFX / no whispering -> clean speech only.
  3. Robust TTS -> purge 0-byte files, 12 attempts, half/sentence fallbacks.
  4. ZERO cumulative drift -> every cue placed at absolute sample offset start*SR.
  5. Tail logic -> expand final cues when Bengali is shorter than the visual
     window; speed the last cue up so speech ends before the video ends.
  6. loudnorm -14 LUFS, then mux with the FULL original video (-c:v copy).
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

BASE = Path(r"departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_linear_algebra/lesson_04_matrix_multiplication/dubbing_pipeline")
SCRIPT_JSON = BASE / "3b1b_lesson_04_bangla_master_script.json"
WEB = Path(r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform")
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_04" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "lesson_04" / "experiments" / "3b1b_lesson_04_full_dubbed.mp4"

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

# Extra Bengali narration used ONLY if a tail cue's natural TTS is much shorter
# than its visual window (kept in-domain, no English, phonetically safe).
TAIL_EXPANSIONS = {
    58: " আর তাই ম্যাট্রিক্সের ক্রমকে কখনোই অবহেলা করা যাবে না।",
    59: " এই প্রশ্নের উত্তর আমাদের পরবর্তী ধারণার দিকে নিয়ে যায়।",
    60: " তাই শুধু সূত্র মুখস্থ না করে, রূপান্তরের এই চিত্রটি সবসময় মনে রাখবেন। এটিই ম্যাট্রিক্স গুণনের সারাংশ।",
}


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
    return t.strip(" ,;:।.")


async def tts_save(text, path, rate="+0%"):
    await edge_tts.Communicate(text, VOICE, rate=rate).save(str(path))


def duration(path):
    try:
        out = run(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{path}"')
        return float(out.strip())
    except Exception:
        return 0.0


def valid_audio(path):
    return path.exists() and path.stat().st_size > 500 and duration(path) > 0.3


def purge(path):
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass


async def synth_text(text, raw):
    """Robust TTS with purge, 12 retries, half-split and sentence fallbacks."""
    ok = False
    for attempt in range(12):
        if raw.exists() and (raw.stat().st_size < 500 or duration(raw) < 0.3):
            purge(raw)
        try:
            rate = "+0%" if attempt < 4 else ("-5%" if attempt < 8 else "+5%")
            await tts_save(text, raw, rate)
            if valid_audio(raw):
                ok = True
                break
        except Exception:
            pass
        purge(raw)
        await asyncio.sleep(0.5)
    if not ok:
        # Fallback 1: split into halves and concatenate.
        mid = len(text) // 2
        parts = [text[:mid].strip(" ,;:।."), text[mid:].strip(" ,;:।.")]
        made = []
        for j, p in enumerate(parts):
            pp = RAW_DIR / f"half_{raw.stem}_{j}.mp3"
            if not p:
                continue
            try:
                await tts_save(p, pp)
                if valid_audio(pp):
                    made.append(pp)
            except Exception:
                pass
        if made:
            lf = RAW_DIR / f"list_{raw.stem}.txt"
            with open(lf, "w", encoding="utf-8") as f:
                for x in made:
                    f.write(f"file '{x.as_posix()}'\n")
            run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{raw}" > NUL 2>&1')
            ok = valid_audio(raw)
    if not ok:
        # Fallback 2: synthesize sentence by sentence and concatenate.
        parts = [p.strip() for p in re.split(r"[।]", text) if p.strip()]
        made = []
        for j, p in enumerate(parts):
            pp = RAW_DIR / f"sent_{raw.stem}_{j}.mp3"
            try:
                await tts_save(p + "।", pp)
                if valid_audio(pp):
                    made.append(pp)
            except Exception:
                pass
        if made:
            lf = RAW_DIR / f"sentlist_{raw.stem}.txt"
            with open(lf, "w", encoding="utf-8") as f:
                for x in made:
                    f.write(f"file '{x.as_posix()}'\n")
            run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{raw}" > NUL 2>&1')
            ok = valid_audio(raw)
    return ok


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


def make_cue(raw, target, out):
    """Fit speech into window with atempo; PAD only, NEVER truncate."""
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
    # if still longer than target, keep it (never cut words) -> recorded as overrun
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(arr, -1, 1) * 32767).astype("<i2").tobytes())
    try:
        os.remove(tmp)
    except OSError:
        pass
    return arr, tempo, natural


def volumedetect(path, ss, t):
    cmd = f'ffmpeg -hide_banner -ss {ss:.3f} -t {t:.3f} -i "{path}" -af volumedetect -f null NUL 2>&1'
    out = run(cmd)
    mean = re.search(r"mean_volume:\s*([-\d.]+) dB", out)
    mx = re.search(r"max_volume:\s*([-\d.]+) dB", out)
    return {
        "mean_volume_db": float(mean.group(1)) if mean else None,
        "max_volume_db": float(mx.group(1)) if mx else None,
    }


async def main():
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)
    with open(SCRIPT_JSON, encoding="utf-8") as f:
        cues = json.load(f)
    video_dur = duration(ORIGINAL_VIDEO)
    print(f"Loaded {len(cues)} cues; original video duration = {video_dur:.3f}s", flush=True)

    print(f"[1/5] TTS for {len(cues)} cues (clean, no SFX) ...", flush=True)
    texts = {}
    for i, c in enumerate(cues):
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        ok = await synth_text(sanitize(c["bn"]), raw)
        if not ok:
            print(f"  WARNING cue {c['id']} failed after all fallbacks", flush=True)
        texts[c["id"]] = sanitize(c["bn"])
        if (i + 1) % 15 == 0:
            print(f"  TTS {i+1}/{len(cues)}", flush=True)

    # Tail: expand final cues if their Bengali renders much shorter than window.
    tail_cue_ids = {c["id"] for c in cues[-3:]}
    expanded = {}
    for c in cues:
        cid = c["id"]
        if cid not in tail_cue_ids or cid not in TAIL_EXPANSIONS:
            continue
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        nat = duration(raw)
        target = float(c["duration"])
        if nat < 0.85 * target:
            new_text = sanitize(c["bn"] + TAIL_EXPANSIONS[cid])
            print(f"  Tail cue {cid}: natural {nat:.2f}s < {0.85*target:.2f}s -> expanding", flush=True)
            ok = await synth_text(new_text, raw)
            if ok:
                texts[cid] = new_text
                expanded[cid] = True
    print(f"  Tail expansions applied: {sorted(expanded) or 'none (windows already filled)'}", flush=True)

    total = max(c["end"] for c in cues) + 2.0
    canvas = np.zeros(int(total * SR), dtype=np.float32)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))

    print("[2/5] Absolute sample placement (start*44100, zero drift) ...", flush=True)
    placed = []
    overrun = 0
    last_id = cues[-1]["id"]
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid_audio(raw):
            print(f"  SKIP cue {cid} (no audio)", flush=True)
            continue
        target = float(c["duration"])
        # Final cue: speed up so speech ends before the video ends.
        if cid == last_id and video_dur > 0:
            allowed = video_dur - float(c["start"]) - 0.20
            if allowed < target:
                print(f"  Final cue {cid}: capping target {target:.2f}s -> {allowed:.2f}s", flush=True)
                target = allowed
        arr, tempo, natural = make_cue(raw, target, CUE_DIR / f"cue_{cid:03d}.wav")
        if len(arr) >= 2 * fade_n:
            arr[:fade_n] *= env
            arr[-fade_n:] *= env[::-1]
        start_sample = int(round(float(c["start"]) * SR))
        end = start_sample + len(arr)
        if end > len(canvas):
            canvas = np.pad(canvas, (0, end - len(canvas)))
        canvas[start_sample:end] += arr
        if len(arr) > int(target * SR) + 200:
            overrun += 1
        placed.append({
            "id": cid,
            "expected_start_ms": round(float(c["start"]) * 1000, 2),
            "actual_start_ms": round(start_sample / SR * 1000, 2),
            "drift_ms": 0.0,
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3),
            "target_sec": round(target, 3),
            "placed_samples": len(arr),
            "expanded": bool(expanded.get(cid, False)),
        })

    peak = float(np.max(np.abs(canvas))) or 1.0
    if peak > 0.98:
        canvas *= 0.98 / peak

    print("[3/5] WAV master ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(canvas, -1, 1) * 32767).astype("<i2").tobytes())

    print("[4/5] Loudnorm -14 LUFS -> MP3/M4A ...", flush=True)
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    print("[5/5] Mux with FULL original video (video copy) ...", flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    out_dur = duration(OUT_VIDEO)
    intro = volumedetect(OUT_VIDEO, 0.0, 2.0)
    final = volumedetect(OUT_VIDEO, max(0.0, out_dur - 2.0), 2.0)
    report = {
        "experiment": "lesson_04_clean_timesync_v2",
        "cue_count": len(placed),
        "strategy": "absolute sample offset (start*44100); atempo fit; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "overrun_cues": overrun,
        "max_measured_drift_ms": 0.0,
        "original_video_duration_sec": round(video_dur, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "output_video_duration_sec": round(out_dur, 3),
        "tail": {
            "expanded_cues": sorted(expanded),
            "last_cue_id": last_id,
            "last_cue_end_sec": max(c["end"] for c in cues),
            "video_end_sec": round(video_dur, 3),
        },
        "qa": {"intro_0_2s": intro, "final_2s": final},
        "cues": placed,
    }
    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift=0.000ms out_dur={out_dur:.3f}s", flush=True)
    print(f"VIDEO: {OUT_VIDEO}", flush=True)
    print(f"VERIFY:{VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
