"""Independent verification for the fill_v2 LA10 re-render.

Checks (all read-only):
  1. ffprobe full duration ~= original (533.06 s)
  2. silencedetect: internal silence runs > 2 s == 0
     (intro 2.5 s and final 3 s are deliberately silent and excluded)
  3. median_fill >= 0.72  (from verification.json + cues)
  4. max_internal_gap_s <= 1.5  (from verification.json + cues)
  5. old video still present (backup), video source not swapped
"""
import json
import re
import subprocess
from pathlib import Path

EXP = Path(__file__).resolve().parent
WEB = EXP.parents[4] / "web_platform"
OUT = WEB / "media_vault" / "lesson_10" / "experiments" / "fill_v2" / "3b1b_lesson_10_full_dubbed_fill2.mp4"
OLD = WEB / "media_vault" / "lesson_10" / "experiments" / "3b1b_lesson_10_full_dubbed.mp4"
ORIG = WEB / "media_vault" / "lesson_10" / "original_source" / "full_original.mp4"
VERIFY = EXP / "verification.json"

LEAD_IN = 2.5
TAIL_MARGIN = 3.0
RUN_LIMIT = 2.0
NOISE_DB = "-45dB"
DETECT_D = 1.5


def sh(cmd):
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    return r.stdout


def main():
    res = {}
    orig_dur = float(sh(f'ffprobe -v error -show_entries format=duration '
                        f'-of default=noprint_wrappers=1:nokey=1 "{ORIG}"').strip())
    dur = float(sh(f'ffprobe -v error -show_entries format=duration '
                   f'-of default=noprint_wrappers=1:nokey=1 "{OUT}"').strip())
    res["original_duration_sec"] = round(orig_dur, 3)
    res["duration_sec"] = round(dur, 3)
    res["duration_ok"] = abs(dur - orig_dur) <= 3.0

    log = sh(f'ffmpeg -hide_banner -nostats -i "{OUT}" -af '
             f'"silencedetect=noise={NOISE_DB}:d={DETECT_D}" -f null - 2>&1')
    starts = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([\d.]+)", log)]
    runs = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else dur
        runs.append((round(s, 3), round(e, 3), round(e - s, 3)))
    internal = [(s, e, d) for s, e, d in runs
                if d > RUN_LIMIT and s >= LEAD_IN and e <= max(0.0, dur - TAIL_MARGIN)]
    boundary = [(s, e, d) for s, e, d in runs
                if d > RUN_LIMIT and not (s >= LEAD_IN and e <= max(0.0, dur - TAIL_MARGIN))]
    res["silence_runs_over_2s_total"] = len([r for r in runs if r[2] > RUN_LIMIT])
    res["silence_runs_over_2s_internal"] = len(internal)
    res["max_internal_run_sec"] = max((r[2] for r in internal), default=0.0)
    res["internal_runs_detail"] = internal[:20]
    res["boundary_runs_detail"] = boundary[:10]
    res["silencedetect_ok"] = len(internal) == 0

    v = json.loads(VERIFY.read_text(encoding="utf-8"))
    fills = [c["fill"] for c in v.get("cues", [])]
    gaps = [c["max_internal_gap_s"] for c in v.get("cues", [])]
    median_fill = round(sorted(fills)[len(fills) // 2], 4) if fills else 0.0
    max_gap = round(max(gaps, default=0.0), 4)
    res["cue_count"] = len(fills)
    res["median_fill"] = median_fill
    res["median_fill_ok"] = median_fill >= 0.72
    res["max_internal_gap_s"] = max_gap
    res["max_internal_gap_ok"] = max_gap <= 1.5
    res["reported_median_fill"] = v.get("median_fill")
    res["reported_max_internal_gap_s"] = v.get("max_internal_gap_s")
    res["reported_internal_silence_runs_over_2s"] = v.get("internal_silence_runs_over_2s")
    res["quality_gate_passed"] = v.get("quality_gate", {}).get("passed")
    res["scale_recomputed_from_rendered_speech"] = v.get("scale_recomputed_from_rendered_speech")
    res["timeline_scale"] = v.get("timeline_scale")
    res["render_rounds"] = v.get("render_rounds")
    res["video_source_swapped"] = v.get("video_source_swapped")
    res["backup_video_exists"] = OLD.exists()
    res["output_size_bytes"] = OUT.stat().st_size if OUT.exists() else 0

    passed = (res["duration_ok"] and res["silencedetect_ok"] and
              res["median_fill_ok"] and res["max_internal_gap_ok"] and
              res["quality_gate_passed"] is True and
              res["video_source_swapped"] is False and res["backup_video_exists"])
    res["ALL_GATES_PASS"] = passed
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
