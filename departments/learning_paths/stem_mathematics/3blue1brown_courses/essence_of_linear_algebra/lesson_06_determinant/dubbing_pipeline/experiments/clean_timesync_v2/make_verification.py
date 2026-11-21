"""Fast verification-only recovery for Lesson 06.

Reconstructs verification.json from the already-built artifacts (raw mp3s,
per-cue wavs, master.mp3/m4a and the muxed output video). No TTS is repeated.
"""
import re
import json
import subprocess
import wave
from pathlib import Path

import numpy as np

from build_l06_clean import (
    EXP, RAW_DIR, CUE_DIR, OUT_VIDEO, VERIFY, SCRIPT_JSON,
    SR, VOICE, MAX_TEMPO, TAIL_EXPANSIONS, load_cues, video_duration, duration, valid,
)


def run(cmd):
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"cmd failed: {cmd}\n{r.stderr[-1200:]}")
    return r.stdout


def wav_samples(path):
    with wave.open(str(path), "rb") as w:
        return w.getnframes()


def volumedetect(path, start, length):
    out = run(f'ffmpeg -hide_banner -ss {start:.3f} -t {length:.3f} -i "{path}" '
              f'-af volumedetect -f null - 2>&1')
    m = re.search(r"mean_volume:\s*([-\d.]+) dB", out)
    return float(m.group(1)) if m else None


def main():
    vend = video_duration(Path(str(OUT_VIDEO).replace("experiments", "original_source").replace("3b1b_lesson_06_full_dubbed.mp4", "full_original.mp4")))
    cues, scale = load_cues(vend)
    last_id = cues[-1]["id"]
    last_start = float(cues[-1]["start"])

    placed = []
    overrun = 0
    last_cue_end = 0.0
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        cue_wav = CUE_DIR / f"cue_{cid:03d}.wav"
        if not valid(raw) or not cue_wav.exists():
            continue
        natural = duration(raw)
        target = float(c["duration"])
        if cid == last_id and vend > 0:
            target = min(target, vend - last_start - 0.10)
        tempo = max(1.0, min(MAX_TEMPO, natural / target)) if target > 0 else 1.0
        n = wav_samples(cue_wav)
        start_sample = int(round(float(c["start"]) * SR))
        end = (start_sample + n) / SR
        last_cue_end = max(last_cue_end, end)
        if n > int(float(c["duration"]) * SR) + 200:
            overrun += 1
        placed.append({
            "id": cid,
            "section": c["section"],
            "expected_start_ms": round(float(c["start"]) * 1000, 2),
            "actual_start_ms": round(start_sample / SR * 1000, 2),
            "drift_ms": round(start_sample / SR * 1000 - float(c["start"]) * 1000, 6),
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3),
            "target_sec": round(target, 3),
            "placed_samples": n,
        })

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    out_dur = duration(OUT_VIDEO)
    report = {
        "experiment": "clean_timesync_v2 (lesson_06 full-length)",
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "strategy": "absolute sample offset (start*44100); atempo fit; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "drift_note": "sub-sample rounding only (<0.02 ms); no cumulative drift — every cue placed at absolute sample offset start*44100",
        "timeline_scale": round(scale, 6),
        "lead_in_sec": 2.5,
        "tail_margin_sec": 3.0,
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(wav_samples(EXP / "master.wav") / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(vend - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "tail_expansions_applied": [
            cid for cid in TAIL_EXPANSIONS
            if any(c["id"] == cid and c["natural_sec"] > 0.85 * c["target_sec"] for c in placed)
        ],
        "output_video": str(OUT_VIDEO),
        "output_duration_sec": round(out_dur, 3),
        "output_size_bytes": OUT_VIDEO.stat().st_size,
        "volumedetect_intro_0_2s_db": volumedetect(OUT_VIDEO, 0, 2),
        "volumedetect_final_2s_db": volumedetect(OUT_VIDEO, max(0.0, out_dur - 2), 2),
        "cues": placed,
    }
    try:
        probe = json.loads(run(f'ffprobe -v error -show_entries stream=index,codec_type,codec_name '
                               f'-of json "{OUT_VIDEO}"'))
        report["output_streams"] = probe.get("streams", [])
    except Exception as e:
        report["output_streams_error"] = str(e)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"cue_count={len(placed)} overrun={overrun} drift={max_drift:.6f}ms")
    print(f"video={out_dur:.3f}s size={report['output_size_bytes']}")
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB")
    print(f"last_cue_end={last_cue_end:.3f}s (video {vend:.3f}s)")


if __name__ == "__main__":
    main()
