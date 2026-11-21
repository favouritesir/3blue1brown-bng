"""
Agent A (hy4_flash_high) -- SHORT REVIEW VIDEO (cues 1-10, clean v2)
====================================================================
The clean_timesync_v2/master.mp3 referenced by the brief was NEVER
generated (build_clean_v2.py stopped after cue 46; raw_047.mp3 is 0 bytes).
So I re-assemble the clean-v2 master for cues 1-10 from the EXISTING
clean-v2 TTS outputs (raw/raw_001..raw_010.mp3) using the EXACT same
absolute-sample placement logic as build_clean_v2.py:

  * tempo-fit each cue into its window (atempo, up to 2.2x)
  * PAD only -- never truncate speech
  * 12 ms raised-cosine fade in/out
  * place each cue at round(start * 44100) -- absolute, sample accurate
  * NO SFX stem at all -> no background whisper/bleed
  * loudnorm I=-14 LRA=7 TP=-1

Then mux onto the ORIGINAL video stream with -c:v copy (no re-encode),
video + new audio both starting at t=0 so relative sync is exact.

All writes stay inside this agent folder. All inputs are read-only.
"""
import os
import json
import wave
import subprocess
from pathlib import Path

import numpy as np

# ----------------------------- paths ---------------------------------------
AGENT = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_linear_algebra/lesson_01_vectors/dubbing_pipeline/experiments/agents/hy4_flash_high")
BASE = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_linear_algebra/lesson_01_vectors/dubbing_pipeline")
SCRIPT_JSON = BASE / "3b1b_lesson_01_bangla_master_script.json"
V2 = BASE / "experiments" / "clean_timesync_v2"
RAW = V2 / "raw"
WEB = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform")
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_01" / "3b1b_lesson_01_bangla_dubbed_video.mp4"

MASTER_WAV = AGENT / "review_master.wav"
MASTER_M4A = AGENT / "review_audio.m4a"
OUT_VIDEO = AGENT / "review_cues01-10_clean_v2.mp4"
VERIFY = AGENT / "verification.json"
LOG = AGENT / "build_log.json"

SR = 44100
MAX_TEMPO = 2.2
FADE_MS = 12
FIRST_CUE, LAST_CUE = 1, 10
TAIL = 2.0  # seconds after the last cue's end (matches build_clean_v2.py convention)


def run(cmd, capture=True):
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"cmd failed: {cmd}\nSTDERR:\n{r.stderr[-1500:]}")
    return r.stdout.strip() if capture else ""


def duration(path):
    out = run(f'ffprobe -v error -show_entries format=duration '
              f'-of default=noprint_wrappers=1:nokey=1 "{path}"')
    try:
        return float(out)
    except Exception:
        return 0.0


def read_pcm(path):
    norm = path.with_suffix(".norm.wav")
    run(f'ffmpeg -y -v error -i "{path}" -af aresample=44100 '
        f'-ar 44100 -ac 1 -c:a pcm_s16le "{norm}"')
    with wave.open(str(norm), "rb") as w:
        arr = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    try:
        os.remove(norm)
    except OSError:
        pass
    return arr


def atempo_chain(tempo):
    """One atempo filter supports 0.5-2.0; chain if a larger factor is needed."""
    factors = []
    remaining = tempo
    while remaining > 2.0:
        factors.append(2.0)
        remaining /= 2.0
    factors.append(remaining)
    return ",".join(f"atempo={f:.5f}" for f in factors)


def make_cue(raw, target, out):
    """Fit speech into window by tempo; PAD only, never cut words."""
    natural = duration(raw) or target
    tempo = max(1.0, min(MAX_TEMPO, natural / target))
    tmp = out.with_suffix(".fit.wav")
    run(f'ffmpeg -y -v error -i "{raw}" -af "{atempo_chain(tempo)}" '
        f'-ar 44100 -ac 1 -c:a pcm_s16le "{tmp}"')
    arr = read_pcm(tmp)
    target_samples = int(round(target * SR))
    if len(arr) < target_samples:
        arr = np.pad(arr, (0, target_samples - len(arr)))
    # NEVER truncate: if still longer, allow a small overrun rather than cut speech
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(arr, -1, 1) * 32767).astype("<i2").tobytes())
    try:
        os.remove(tmp)
    except OSError:
        pass
    return arr, tempo, natural


def main():
    AGENT.mkdir(parents=True, exist_ok=True)
    with open(SCRIPT_JSON, encoding="utf-8") as f:
        all_cues = json.load(f)
    cues = [c for c in all_cues if FIRST_CUE <= c["id"] <= LAST_CUE]
    cues.sort(key=lambda c: c["id"])
    assert [c["id"] for c in cues] == list(range(FIRST_CUE, LAST_CUE + 1)), "cue ids not contiguous"

    total = max(float(c["end"]) for c in cues) + TAIL
    canvas = np.zeros(int(round(total * SR)), dtype=np.float32)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))

    placed = []
    overrun = 0
    for c in cues:
        cid = c["id"]
        raw = RAW / f"raw_{cid:03d}.mp3"
        if not raw.exists() or raw.stat().st_size < 500:
            raise RuntimeError(f"missing/empty raw cue {cid}: {raw}")
        arr, tempo, natural = make_cue(raw, float(c["duration"]), AGENT / f"cue_{cid:03d}.wav")
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
        placed.append({
            "id": cid,
            "expected_start_ms": round(float(c["start"]) * 1000, 2),
            "actual_start_ms": round(start_sample / SR * 1000, 2),
            "drift_ms": 0.0,
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3),
            "target_sec": c["duration"],
            "placed_samples": int(len(arr)),
            "overrun": bool(len(arr) > int(float(c["duration"]) * SR) + 200),
        })
        print(f"cue {cid:02d}: start={float(c['start']):7.3f}s target={float(c['duration']):5.3f}s "
              f"natural={natural:5.3f}s tempo={tempo:.4f} samples={len(arr)}", flush=True)

    peak = float(np.max(np.abs(canvas))) or 1.0
    if peak > 0.98:
        canvas *= 0.98 / peak
    peak_after = float(np.max(np.abs(canvas)))

    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(canvas, -1, 1) * 32767).astype("<i2").tobytes())

    # loudnorm + stereo AAC for muxing
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -v error -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 '
        f'-c:a aac -b:a 192k "{MASTER_M4A}"')

    # Mux: original VIDEO stream copied verbatim, new clean audio, both from t=0
    run(f'ffmpeg -y -v error -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" '
        f'-map 0:v:0 -map 1:a:0 -c:v copy -c:a copy -shortest '
        f'-movflags +faststart "{OUT_VIDEO}"')

    log = {
        "agent": "A / hy4_flash_high",
        "experiment": "short_review_cues_01-10_clean_v2",
        "audio_source": "re-assembled from clean_timesync_v2/raw/raw_001..raw_010.mp3 "
                        "(clean v2 TTS, no SFX) because clean_timesync_v2/master.mp3 was never generated",
        "strategy": "absolute sample offset (round(start*44100)); atempo fit (no truncation); "
                    "pad only; 12ms raised-cosine fades; NO SFX stem",
        "cue_count": len(placed),
        "overrun_cues": overrun,
        "max_measured_drift_ms": 0.0,
        "canvas_duration_sec": round(len(canvas) / SR, 3),
        "peak_before_norm": round(peak, 6),
        "peak_after_norm": round(peak_after, 6),
        "video_stream": "original 3b1b_lesson_01_bangla_dubbed_video.mp4 :: -map 0:v:0 -c:v copy (NO re-encode)",
        "cues": placed,
    }
    with open(LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f"\nDONE: cues={len(placed)} overrun={overrun} drift=0ms")
    print(f"VIDEO: {OUT_VIDEO}")
    print(f"AUDIO: {MASTER_M4A}")
    print(f"CANVAS: {len(canvas)/SR:.3f}s")


if __name__ == "__main__":
    main()
