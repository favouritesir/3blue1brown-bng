"""Independent verification of the four full-length Fractals Bengali dubs.

Checks (per lesson):
  * ffprobe full duration of original vs output (must be ~equal).
  * zero INTERNAL silent runs > 2s (only lead-in / tail silence allowed).
  * median_fill >= 0.72 and max_internal_gap_s <= 1.5s (from verification.json).
  * no failed TTS cues, cue count matches manifest.

Writes a consolidated report to verify_independent_report.json next to this file.
"""
import json
import re
import subprocess
from pathlib import Path

WEB = Path(r"D:\0PEN CODE\Dub Studio\departments\learning_paths\stem_mathematics"
           r"\3blue1brown_courses\web_platform")
EXP_ROOT = Path(r"D:\0PEN CODE\Dub Studio\departments\learning_paths\stem_mathematics"
                r"\3blue1brown_courses\fractals")
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
DURATION_TOLERANCE_SEC = 1.0
SILENCE_THRESHOLD = "-35dB"
SILENCE_MIN_DURATION = 2.0


def ffprobe_duration(path, stream=None):
    sel = "-select_streams v:0 " if stream == "v" else ""
    ent = "stream=duration" if stream else "format=duration"
    out = subprocess.run(
        f'ffprobe -v error {sel}-show_entries {ent} -of default=noprint_wrappers=1:nokey=1 "{path}"',
        shell=True, capture_output=True, text=True).stdout.strip()
    try:
        return float(out.splitlines()[0])
    except Exception:
        return None


def container_and_video_duration(path):
    c = ffprobe_duration(path)
    v = ffprobe_duration(path, stream="v")
    return c, v


def silent_runs(path, dur):
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
           "-af", f"silencedetect=noise={SILENCE_THRESHOLD}:d={SILENCE_MIN_DURATION}",
           "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    txt = r.stderr
    starts = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", txt)]
    ends = []
    for m in re.finditer(r"silence_end:\s*([\d.]+)\s*\|\s*silence_duration:\s*([\d.]+)", txt):
        ends.append((float(m.group(1)), float(m.group(2))))
    runs = []
    for i, s in enumerate(starts):
        if i < len(ends):
            e, d = ends[i]
        else:
            e, d = dur, dur - s
        runs.append({"start": round(s, 3), "end": round(e, 3), "duration": round(d, 3)})
    return runs


def classify(runs, dur):
    lead, tail, internal = [], [], []
    for r in runs:
        if r["start"] <= LEAD_IN_SEC + 1.5:
            lead.append(r)
        elif r["end"] >= dur - TAIL_MARGIN_SEC - 1.5:
            tail.append(r)
        else:
            internal.append(r)
    return lead, tail, internal


def main():
    results = {}
    all_pass = True
    for nn in ("01", "02", "03", "04"):
        exp = EXP_ROOT / f"lesson_{nn}" / "dubbing_pipeline" / "experiments" / "clean_timesync_v2"
        orig = WEB / "media_vault" / "fractals" / f"lesson_{nn}" / "original_source" / "full_original.mp4"
        out = WEB / "media_vault" / "fractals" / f"lesson_{nn}" / "experiments" / f"3b1b_fractals_{nn}_full_dubbed.mp4"
        vfile = exp / "verification.json"
        row = {"lesson": nn, "output": str(out)}

        oc, ov = container_and_video_duration(orig)
        dc, dv = container_and_video_duration(out)
        row["original_container_sec"] = oc
        row["original_video_stream_sec"] = ov
        row["output_container_sec"] = dc
        row["output_video_stream_sec"] = dv
        ref = ov if ov is not None else oc
        got = dc if dc is not None else dv
        diff = abs(got - ref) if (ref is not None and got is not None) else None
        row["duration_diff_sec"] = round(diff, 3) if diff is not None else None
        row["duration_gate"] = bool(diff is not None and diff <= DURATION_TOLERANCE_SEC)

        if out.exists():
            runs = silent_runs(out, got or 0.0)
            lead, tail, internal = classify(runs, got or 0.0)
            long_internal = [r for r in internal if r["duration"] > SILENCE_MIN_DURATION]
            row["silent_runs"] = runs
            row["lead_in_runs"] = lead
            row["tail_runs"] = tail
            row["internal_runs"] = internal
            row["internal_runs_over_2s"] = long_internal
            row["internal_silence_gate"] = (len(long_internal) == 0)
        else:
            row["silent_runs"] = []
            row["internal_runs_over_2s"] = []
            row["internal_silence_gate"] = False

        if vfile.exists():
            v = json.loads(vfile.read_text(encoding="utf-8"))
            row["median_fill"] = v.get("median_fill")
            row["max_internal_gap_s"] = v.get("max_internal_gap_s")
            row["fill_policy_met"] = v.get("fill_policy_met")
            row["failed_tts_cues"] = v.get("failed_tts_cues")
            row["cue_count"] = v.get("cue_count")
            row["expected_cue_count"] = v.get("expected_cue_count")
            row["timeline_scale"] = v.get("timeline_scale")
            row["overrun_cues"] = v.get("overrun_cues")
            row["max_measured_drift_ms"] = v.get("max_measured_drift_ms")
            row["output_size_bytes"] = v.get("output_size_bytes")
            row["fill_gate"] = bool(v.get("median_fill", 0) >= 0.72 and
                                    v.get("max_internal_gap_s", 99) <= 1.5)
            row["tts_gate"] = (v.get("failed_tts_cues") == [] and
                               v.get("cue_count") == v.get("expected_cue_count"))
        else:
            row["fill_gate"] = False
            row["tts_gate"] = False

        row["PASS"] = bool(row["duration_gate"] and row["internal_silence_gate"] and
                           row["fill_gate"] and row["tts_gate"])
        all_pass = all_pass and row["PASS"]
        results[nn] = row
        print(f"lesson {nn}: PASS={row['PASS']} dur_diff={row['duration_diff_sec']}s "
              f"internal>2s={len(row['internal_runs_over_2s'])} "
              f"median_fill={row.get('median_fill')} max_gap={row.get('max_internal_gap_s')} "
              f"failed_tts={row.get('failed_tts_cues')}", flush=True)

    report = {"all_pass": all_pass, "lessons": results}
    rp = EXP_ROOT / "lesson_01" / "dubbing_pipeline" / "experiments" / "clean_timesync_v2" / "verify_independent_report.json"
    rp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ALL_PASS={all_pass} report={rp}", flush=True)
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
