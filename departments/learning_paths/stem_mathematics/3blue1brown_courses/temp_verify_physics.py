"""Independent quality-gate verification for all 13 physics full-length dubs.

Checks, per lesson:
  * ffprobe full duration of original vs output (must be ~equal)
  * zero internal silent runs > 2.0s (silencedetect, lead-in/tail excluded)
  * median_fill >= 0.72 and max_internal_gap_s <= 1.5s (from build verification.json)
Writes a JSON summary artifact (never prints large reports to chat).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web_platform"
LEAD_IN = 2.5
TAIL_MARGIN = 3.0
SILENCE_DB = "-38dB"
SILENCE_D = 2.0


def probe_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def probe_streams(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=index,codec_type,codec_name,width,height",
         "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    try:
        return json.loads(r.stdout).get("streams", [])
    except Exception:
        return []


def silent_runs(path):
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
           "-af", f"silencedetect=noise={SILENCE_DB}:d={SILENCE_D}", "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    txt = r.stderr
    starts = [float(m.group(1)) for m in re.finditer(r"silence_start:\s*([0-9.]+)", txt)]
    # durations are paired with end lines; build intervals in order.
    intervals = []
    ev = re.findall(r"silence_(start|end):\s*([0-9.]+)(?:\s*\|\s*silence_duration:\s*([0-9.]+))?", txt)
    cur = None
    for kind, val, dur in ev:
        v = float(val)
        if kind == "start":
            cur = v
        else:
            d = float(dur) if dur else (v - cur if cur is not None else 0.0)
            intervals.append((cur if cur is not None else 0.0, v, d))
            cur = None
    if cur is not None:
        intervals.append((cur, probe_duration(path), probe_duration(path) - cur))
    return intervals


def main():
    results = {}
    all_pass = True
    lessons = [int(x) for x in sys.argv[1:]] or list(range(1, 14))
    for i in lessons:
        lid = f"lesson_{i:02d}"
        original = WEB / "media_vault" / "physics" / lid / "original_source" / "full_original.mp4"
        out = WEB / "media_vault" / "physics" / lid / "experiments" / f"3b1b_physics_{i:02d}_full_dubbed.mp4"
        vjson = (ROOT / "physics" / lid / "dubbing_pipeline" / "experiments"
                 / "clean_timesync_v2" / "verification.json")
        entry = {"lesson": lid, "output_exists": out.exists()}
        if not out.exists() or not original.exists():
            entry["pass"] = False
            results[lid] = entry
            all_pass = False
            continue
        odur = probe_duration(original)
        xdur = probe_duration(out)
        streams = probe_streams(out)
        has_video = any(s.get("codec_type") == "video" for s in streams)
        has_audio = any(s.get("codec_type") == "audio" for s in streams)
        runs = silent_runs(out)
        internal = [(s, e, d) for (s, e, d) in runs
                    if s >= LEAD_IN - 0.1 and e <= odur - TAIL_MARGIN + 0.1 and d > 2.0]
        build = json.loads(vjson.read_text(encoding="utf-8")) if vjson.exists() else {}
        median_fill = build.get("median_fill")
        max_gap = build.get("max_internal_gap_s")
        dur_ok = abs(xdur - odur) <= 1.0
        silence_ok = len(internal) == 0
        fill_ok = (median_fill is not None and median_fill >= 0.72)
        gap_ok = (max_gap is not None and max_gap <= 1.5)
        ok = dur_ok and silence_ok and fill_ok and gap_ok and has_video and has_audio
        entry.update({
            "original_duration_s": round(odur, 3),
            "output_duration_s": round(xdur, 3),
            "duration_diff_s": round(xdur - odur, 3),
            "duration_ok": dur_ok,
            "has_video_stream": has_video,
            "has_audio_stream": has_audio,
            "internal_silent_runs_gt_2s": len(internal),
            "internal_run_details": [(round(s, 2), round(e, 2), round(d, 2)) for s, e, d in internal[:10]],
            "median_fill": median_fill,
            "max_internal_gap_s": max_gap,
            "fill_ok": fill_ok,
            "gap_ok": gap_ok,
            "silence_ok": silence_ok,
            "build_cue_count": build.get("cue_count"),
            "build_failed_tts_cues": build.get("failed_tts_cues"),
            "build_overrun_cues": build.get("overrun_cues"),
            "max_measured_drift_ms": build.get("max_measured_drift_ms"),
            "video_id": build.get("video_id"),
            "pass": ok,
        })
        results[lid] = entry
        all_pass = all_pass and ok
        print(f"{lid} | id={entry.get('video_id')} | orig={odur:.1f}s out={xdur:.1f}s "
              f"| runs>2s={len(internal)} | median_fill={median_fill} maxgap={max_gap} "
              f"| PASS={ok}", flush=True)

    summary = {
        "all_pass": all_pass,
        "lessons": results,
        "thresholds": {
            "duration_diff_s": 1.0,
            "internal_silent_run_s": 2.0,
            "median_fill": 0.72,
            "max_internal_gap_s": 1.5,
        },
    }
    path = ROOT / "temp_physics_verification_summary.json"
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ALL_PASS={all_pass} ; summary={path}", flush=True)


if __name__ == "__main__":
    main()
