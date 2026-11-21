# -*- coding: utf-8 -*-
"""INDEPENDENT verification of all 10 Analysis dubbed videos.

Re-measures every gate directly from the artefacts (not from the builder's
self-report):

  * ffprobe full duration of original vs final MP4 (must match within 1 s)
  * silencedetect on the FINAL MP4: zero internal silent runs > 2 s
    (lead-in and tail runs are allowed)
  * median_fill recomputed from the rendered cue WAVs (last non-silent sample
    over total window length) >= 0.72
  * max_internal_gap_s recomputed as the largest trailing padded silence in a
    cue WAV <= 1.5 s
  * official ID / oEmbed author as recorded in the builder's verification.json
"""
import json
import re
import statistics
import subprocess
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WEB = HERE.parents[2]
VAULT = WEB / "media_vault" / "analysis"
SR = 44100
THRESH = 0.001


def ffprobe_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def silence_runs(path):
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-af", "silencedetect=noise=-45dB:d=2.0", "-f", "null", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    txt = r.stderr
    starts = [float(x) for x in re.findall(r"silence_start:\s*([0-9.]+)", txt)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([0-9.]+)", txt)]
    return [(s, ends[i] if i < len(ends) else None) for i, s in enumerate(starts)]


def cue_metrics(cue_dir):
    fills = []
    gaps = []
    for wav in sorted(cue_dir.glob("cue_*.wav")):
        with wave.open(str(wav), "rb") as w:
            arr = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
        if arr.size == 0:
            continue
        loud = np.flatnonzero(np.abs(arr) > THRESH)
        if loud.size == 0:
            fills.append(0.0)
            gaps.append(round(len(arr) / SR, 4))
            continue
        speech_end = int(loud[-1]) + 1
        fills.append(min(1.0, speech_end / len(arr)))
        gaps.append(round((len(arr) - speech_end) / SR, 4))
    return (round(statistics.median(fills), 4) if fills else 0.0,
            round(max(gaps), 4) if gaps else 0.0, len(fills))


def main():
    rows = []
    all_ok = True
    for n in range(1, 11):
        nn = f"{n:02d}"
        lesson = VAULT / f"lesson_{nn}"
        original = lesson / "original_source" / "full_original.mp4"
        output = lesson / "experiments" / f"3b1b_analysis_{nn}_full_dubbed.mp4"
        verify = lesson / "experiments" / "verification.json"
        cues = lesson / "dubbing_pipeline" / "experiments" / "clean_timesync_v2" / "cues"
        odur = ffprobe_duration(original)
        vdur = ffprobe_duration(output)
        runs = silence_runs(output)
        internal = []
        for s, e in runs:
            end = e if e is not None else vdur
            # Lead-in (< 5 s) and tail (>= last 6 s) are allowed.
            if s < 5.0:
                continue
            if end >= vdur - 6.0:
                continue
            internal.append(round(end - s, 3))
        long_internal = [d for d in internal if d > 2.0]
        median_fill, max_gap, n_cues = cue_metrics(cues)
        rep = json.loads(verify.read_text(encoding="utf-8")) if verify.exists() else {}
        gates = {
            "original_exists": original.exists(),
            "output_exists": output.exists(),
            "official_id_verified": bool(rep.get("oembed_author_verified")) and bool(rep.get("source_is_official_3b1b_video")),
            "expected_cue_count_met": rep.get("cue_count") == rep.get("expected_cue_count"),
            "duration_match": bool(odur > 30 and abs(vdur - odur) <= 1.0),
            "no_internal_silence_gt_2s": len(long_internal) == 0,
            "median_fill_ge_0.72": median_fill >= 0.72,
            "max_internal_gap_le_1.5": max_gap <= 1.5,
        }
        ok = all(gates.values())
        all_ok = all_ok and ok
        row = {
            "lesson": f"lesson_{nn}",
            "video_id": rep.get("video_id"),
            "oembed_author": rep.get("oembed_author"),
            "cue_count_reported": rep.get("cue_count"),
            "cue_count_expected": rep.get("expected_cue_count"),
            "cue_wavs_measured": n_cues,
            "original_duration_sec": round(odur, 3),
            "output_duration_sec": round(vdur, 3),
            "duration_delta_sec": round(vdur - odur, 3),
            "silence_runs_total": len(runs),
            "internal_silence_runs_sec": internal,
            "internal_runs_gt_2s": long_internal,
            "median_fill_recomputed": median_fill,
            "max_internal_gap_recomputed_sec": max_gap,
            "gates": gates,
            "PASS": ok,
        }
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    out = HERE / "final_verification.json"
    out.write_text(json.dumps({"all_pass": all_ok, "lessons": rows}, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\nALL_PASS={all_ok} -> {out}", flush=True)


if __name__ == "__main__":
    main()
