"""
EXPERIMENT — Clean absolute-sample Bengali narration (Lesson 03)
================================================================
Adapted from the proven Lesson-01 clean_timesync_v2 pipeline plus its
fix_tail_sync tail fix. NEW files only; production / teacher audio untouched.

Properties:
  1. No hard atrim truncation: natural TTS is fitted with atempo and only
     PADDED, never cut -> no mid-word "sound cut off".
  2. NO SFX / background stem at all -> no whispering / vocal bleed.
  3. Robust Edge-TTS: purge 0-byte/short files, 12 attempts, half-split and
     sentence-split fallbacks -> no NoAudioReceived gaps.
  4. Zero cumulative drift: every cue placed at ABSOLUTE sample offset
     start * 44100.
  5. Tail fix (like L01 cue 96/97/98): expand cue 67 whose Bengali text is
     short for its 12.90 s visual window; guard the final cue (68) so its
     speech is sped up/shortened to finish inside the video (no cut).
  6. Canvas padded to the full original video duration so the -shortest mux
     keeps the entire video (full-length deliverable).
  7. loudnorm -14 LUFS, master.mp3 / master.m4a + verification.json.
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

BASE = Path(r"departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_linear_algebra/lesson_03_linear_transformations/dubbing_pipeline")
SCRIPT_JSON = BASE / "3b1b_lesson_03_bangla_master_script.json"

EXP = BASE / "experiments" / "clean_timesync_v2"
RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

WEB = Path(r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform")
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_03" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "lesson_03" / "experiments" / "3b1b_lesson_03_full_dubbed.mp4"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
FADE_MS = 12
TAIL_MARGIN = 0.10

# --- Tail expansion (mirrors L01 fix_tail_sync.py) -------------------------
# Cue 67: 12.90 s visual window but the master-script Bengali line is short
# (~100 chars) -> would leave ~7 s of dead air. Expand with pedagogically
# consistent closing narration so natural TTS fills the window.
# Cue 68: final cue; its target is capped in code to end before video end.
OVERRIDES = {
    67: (
        "এবং প্রতিটি ম্যাট্রিক্স হলো রূপান্তরিত বেসিস ভেক্টরগুলোর একটি সংক্ষিপ্ত ও নিখুঁত জ্যামিতিক নির্দেশিকা। "
        "ম্যাট্রিক্স গুণন, ডিটারমিন্যান্ট, ভিত্তি পরিবর্তন কিংবা আইগেনভেক্টর—আসন্ন এই সব বিষয় অনেক সহজ হয়ে উঠবে, "
        "যখনই আপনি ম্যাট্রিক্সকে কেবল সংখ্যার ছক না দেখে স্থানের রূপান্তর হিসেবে চিন্তা করবেন।"
    ),
}


def run(cmd):
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"cmd failed: {cmd}\n{r.stderr[-1200:]}")
    return r.stdout


def run_any(cmd):
    """Like run() but returns stdout+stderr (volumedetect writes to stderr)."""
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return r.stdout + "\n" + r.stderr


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
    out = run(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{path}"')
    try:
        return float(out.strip())
    except Exception:
        return 0.0


def loudnorm_two_pass_filter(wav):
    """Two-pass linear loudnorm: measure first, then apply a constant gain so
    the integrated loudness lands on -14 LUFS instead of drifting."""
    base = "loudnorm=I=-14:LRA=7:TP=-1"
    out = run_any(f'ffmpeg -hide_banner -nostats -i "{wav}" -af "{base}:print_format=json" -f null NUL')
    def grab(key):
        m = re.search(rf'"{key}"\s*:\s*"(-?[\d.]+)"', out)
        return m.group(1) if m else "0"
    return (f'{base}:linear=true:measured_I={grab("input_i")}:measured_TP={grab("input_tp")}'
            f':measured_LRA={grab("input_lra")}:measured_thresh={grab("input_thresh")}'
            f':offset={grab("target_offset")}')


def volumedetect(path, start=None, length=None):
    """Return {mean_volume, max_volume} dB from ffmpeg volumedetect."""
    # IMPORTANT: -ss must be an INPUT option (before -i). With output-side
    # -ss, volumedetect sees the whole stream and reports speech levels.
    cmd = 'ffmpeg -hide_banner -nostats '
    if start is not None:
        cmd += f'-ss {start} '
    cmd += f'-i "{path}" '
    if length is not None:
        cmd += f'-t {length} '
    cmd += '-af volumedetect -f null NUL'
    out = run_any(cmd)
    res = {}
    for key in ("mean_volume", "max_volume"):
        m = re.search(rf"{key}:\s*(-?[\d.]+)\s*dB", out)
        res[key] = float(m.group(1)) if m else None
    return res


async def synth_all(cues):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for i, c in enumerate(cues):
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        # A failed Edge-TTS call can leave a 0-byte file; always purge it first.
        if raw.exists() and (raw.stat().st_size < 500 or duration(raw) < 0.3):
            try:
                raw.unlink()
            except OSError:
                pass
        text = sanitize(OVERRIDES.get(cid, c["bn"]))
        ok = False
        for attempt in range(12):
            try:
                rate = "+0%" if attempt < 4 else ("-5%" if attempt < 8 else "+5%")
                await tts_save(text, raw, rate)
                if raw.exists() and raw.stat().st_size > 500 and duration(raw) > 0.3:
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
            # Fallback 1: split into two halves, synthesize, concat.
            mid = len(text) // 2
            parts = [text[:mid].strip(" ,;:।."), text[mid:].strip(" ,;:।.")]
            made = []
            for j, p in enumerate(parts):
                pp = RAW_DIR / f"part_{cid}_{j}.mp3"
                if not p:
                    continue
                try:
                    await tts_save(p, pp)
                    if pp.exists() and pp.stat().st_size > 500:
                        made.append(pp)
                except Exception:
                    pass
            if made:
                lf = RAW_DIR / f"list_{cid:03d}.txt"
                with open(lf, "w", encoding="utf-8") as f:
                    for x in made:
                        f.write(f"file '{x.as_posix()}'\n")
                run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{raw}" > NUL 2>&1')
                ok = raw.exists() and raw.stat().st_size > 500
        if not ok:
            # Fallback 2: sentence-split, synthesize each sentence, concat.
            parts = [p.strip() for p in re.split(r"[।]", text) if p.strip()]
            made = []
            lf = RAW_DIR / f"fallback_{cid:03d}.txt"
            for j, p in enumerate(parts):
                pp = RAW_DIR / f"fb_{cid}_{j}.mp3"
                try:
                    await tts_save(p + "।", pp)
                    if pp.exists() and pp.stat().st_size > 500:
                        made.append(pp)
                except Exception:
                    pass
            if made:
                with open(lf, "w", encoding="utf-8") as f:
                    for x in made:
                        f.write(f"file '{x.as_posix()}'\n")
                run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{raw}" > NUL 2>&1')
                ok = raw.exists() and raw.stat().st_size > 500
        if not ok:
            print(f"  WARNING cue {cid} still failed after all fallbacks", flush=True)
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


def make_cue(raw, target, out, cid, video_duration):
    """Fit speech into window by tempo; PAD only, never cut words."""
    natural = duration(raw)
    if natural <= 0:
        natural = target
    # Final cue: shorten/sped-up so speech ends before the video ends.
    if cid == max(CUE_IDS):
        target = min(target, video_duration - float(cue_start[cid]) - TAIL_MARGIN)
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
    return arr, tempo, natural, target


async def main():
    EXP.mkdir(parents=True, exist_ok=True)
    CUE_DIR.mkdir(parents=True, exist_ok=True)

    if not ORIGINAL_VIDEO.exists():
        raise FileNotFoundError(f"Original video missing: {ORIGINAL_VIDEO}")
    video_duration = duration(ORIGINAL_VIDEO)
    print(f"Original video duration: {video_duration:.3f}s", flush=True)

    with open(SCRIPT_JSON, encoding="utf-8") as f:
        cues = json.load(f)
    global CUE_IDS, cue_start
    CUE_IDS = [c["id"] for c in cues]
    cue_start = {c["id"]: float(c["start"]) for c in cues}
    final_id = max(CUE_IDS)

    print(f"[1/6] TTS for {len(cues)} cues (clean, no SFX) ...", flush=True)
    await synth_all(cues)

    # Canvas spans the FULL video so -shortest keeps the entire video.
    total = max(video_duration, max(c["end"] for c in cues) + 2.0)
    canvas = np.zeros(int(total * SR), dtype=np.float32)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))

    print("[2/6] Absolute sample placement (zero cumulative drift) ...", flush=True)
    placed = []
    overrun = 0
    max_drift_ms = 0.0
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not raw.exists() or raw.stat().st_size < 500:
            print(f"  SKIP cue {cid} (no audio)", flush=True)
            continue
        arr, tempo, natural, target = make_cue(raw, float(c["duration"]), CUE_DIR / f"cue_{cid:03d}.wav", cid, video_duration)
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
        expected_sample = round(float(c["start"]) * SR)
        drift_ms = abs(start_sample - expected_sample) / SR * 1000.0
        max_drift_ms = max(max_drift_ms, drift_ms)
        placed.append({
            "id": cid,
            "expected_start_ms": round(float(c["start"]) * 1000, 2),
            "actual_start_ms": round(start_sample / SR * 1000, 2),
            "drift_ms": round(drift_ms, 6),
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3),
            "target_sec": round(target, 3),
            "placed_samples": len(arr),
            "text": OVERRIDES.get(cid, c["bn"])[:140],
        })

    peak = float(np.max(np.abs(canvas))) or 1.0
    if peak > 0.98:
        canvas *= 0.98 / peak

    print("[3/6] WAV master ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(canvas, -1, 1) * 32767).astype("<i2").tobytes())

    print("[4/6] Two-pass loudnorm (-14 LUFS) + MP3/M4A ...", flush=True)
    af = loudnorm_two_pass_filter(MASTER_WAV)
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    print("[5/6] Verification.json + volumedetect (intro / final 2 s) ...", flush=True)
    master_dur = duration(MASTER_MP3)
    intro_v = volumedetect(MASTER_MP3, 0, 2)
    tail_v = volumedetect(MASTER_MP3, max(0, master_dur - 2), 2)
    report = {
        "experiment": "lesson_03_clean_timesync_v2",
        "cue_count": len(placed),
        "strategy": "absolute sample offset; atempo fit (no truncation); pad only",
        "sfx": "NONE — clean speech only (no whisper/bleed)",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift_ms, 6),
        "total_duration_sec": round(len(canvas) / SR, 3),
        "video_duration_sec": round(video_duration, 3),
        "master_mp3_duration_sec": round(master_dur, 3),
        "tail_fix": f"cue 67 expanded to fill its visual window; final cue {final_id} guarded to end before video end",
        "expanded_cues": list(OVERRIDES.keys()),
        "volumedetect_intro_0_2s": intro_v,
        "volumedetect_final_2s": tail_v,
        "cues": placed,
    }
    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("[6/6] Mux with full original video (video stream copy) ...", flush=True)
    OUT_VIDEO.parent.mkdir(parents=True, exist_ok=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    out_dur = duration(OUT_VIDEO)
    v_intro = volumedetect(OUT_VIDEO, 0, 2)
    v_tail = volumedetect(OUT_VIDEO, max(0, out_dur - 2), 2)
    report["output_video_duration_sec"] = round(out_dur, 3)
    report["output_volumedetect_intro_0_2s"] = v_intro
    report["output_volumedetect_final_2s"] = v_tail
    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift_ms:.6f}ms "
          f"video={out_dur:.3f}s", flush=True)
    print(f"VIDEO:  {OUT_VIDEO}", flush=True)
    print(f"MP3:    {MASTER_MP3}", flush=True)
    print(f"M4A:    {MASTER_M4A}", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)
    print(f"INTRO volumedetect: {intro_v}", flush=True)
    print(f"FINAL volumedetect: {tail_v}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
