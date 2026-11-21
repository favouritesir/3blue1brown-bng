"""Independent verification of the 3 full-length Topology Bengali dubs.

Does NOT import or trust the build scripts' self-report except to cross-check
the fill metrics. It re-probes both files with ffprobe, detects silence runs
> 2 s in the muxed audio with ffmpeg silencedetect, and asserts the gates:

  * output duration ~= original duration
  * zero INTERNAL silent runs > 2 s (only lead-in / tail allowed)
  * median_fill >= 0.72 and max_internal_gap_s <= 1.5 (from verification.json)
"""
from pathlib import Path
import json
import re
import subprocess

WEB = Path(__file__).resolve().parents[1] / "web_platform"
COURSE = WEB.parents[0]  # 3blue1brown_courses
IDS = {"01": "IQqtsm-bBRU", "02": "BHdbsHFs2P0", "03": "yuVqxCSsE7c"}
SILENCE_DB = "-45dB"
SILENCE_DUR = 2.0
LEAD_ZONE_S = 5.0   # a >2s run starting before this counts as lead-in
TAIL_ZONE_S = 8.0   # a >2s run ending within this of the end counts as tail


def ffprobe_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def stream_info(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=index,codec_type,codec_name,width,height",
         "-of", "json", str(path)], capture_output=True, text=True)
    try:
        return json.loads(r.stdout).get("streams", [])
    except Exception:
        return []


def silence_runs(path):
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-vn", "-i", str(path),
         "-af", f"silencedetect=noise={SILENCE_DB}:d={SILENCE_DUR}",
         "-f", "null", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    txt = r.stderr
    runs = []
    cur = None
    for line in txt.splitlines():
        m = re.search(r"silence_start:\s*([\d.]+)", line)
        if m:
            cur = float(m.group(1))
            continue
        m = re.search(r"silence_end:\s*([\d.]+)", line)
        if m and cur is not None:
            runs.append({"start": round(cur, 3), "end": round(float(m.group(1)), 3),
                         "length": round(float(m.group(1)) - cur, 3)})
            cur = None
    return runs


def verify_one(nn):
    lesson = f"lesson_{nn}"
    base = WEB / "media_vault" / "topology" / lesson
    original = base / "original_source" / "full_original.mp4"
    output = base / "experiments" / f"3b1b_topology_{nn}_full_dubbed.mp4"
    vjson = (COURSE / "topology" / lesson / "dubbing_pipeline" / "experiments"
             / "clean_timesync_v2" / "verification.json")

    odur = ffprobe_duration(original)
    xdur = ffprobe_duration(output)
    runs = silence_runs(output) if xdur > 0 else []
    internal = [r for r in runs
                if not (r["start"] <= LEAD_ZONE_S or r["end"] >= xdur - TAIL_ZONE_S)]
    fill = {}
    if vjson.exists():
        d = json.loads(vjson.read_text(encoding="utf-8"))
        fill = {
            "median_fill": d.get("median_fill"),
            "max_internal_gap_s": d.get("max_internal_gap_s"),
            "fill_policy_met": d.get("fill_policy_met"),
            "cue_count": d.get("cue_count"),
            "expected_cue_count": d.get("expected_cue_count"),
            "timeline_scale": d.get("timeline_scale"),
            "max_measured_drift_ms": d.get("max_measured_drift_ms"),
            "overrun_cues": d.get("overrun_cues"),
            "oembed_ok": (d.get("provenance") or {}).get("oembed", {}).get("ok"),
            "yt_dlp_uploader": (d.get("provenance") or {}).get("yt_dlp_uploader"),
            "sfx": d.get("sfx"),
        }

    dur_ok = odur > 0 and abs(xdur - odur) <= max(2.0, 0.005 * odur)
    gates = {
        "duration_matches_original": bool(dur_ok),
        "no_internal_silence_over_2s": len(internal) == 0,
        "median_fill_ge_0.72": bool((fill.get("median_fill") or 0) >= 0.72),
        "max_internal_gap_le_1.5s": bool((fill.get("max_internal_gap_s") or 999) <= 1.5),
    }
    result = {
        "lesson": lesson,
        "youtube_id": IDS[nn],
        "original": {
            "path": str(original), "duration_sec": round(odur, 3),
            "size_bytes": original.stat().st_size if original.exists() else 0,
            "streams": stream_info(original) if original.exists() else [],
        },
        "output": {
            "path": str(output), "duration_sec": round(xdur, 3),
            "size_bytes": output.stat().st_size if output.exists() else 0,
            "streams": stream_info(output) if output.exists() else [],
        },
        "duration_delta_sec": round(xdur - odur, 3),
        "silence_runs_over_2s": runs,
        "internal_silence_runs_over_2s": internal,
        "build_report": fill,
        "gates": gates,
        "ALL_GATES_PASS": all(gates.values()) and bool(fill.get("fill_policy_met")),
    }
    return result


def main():
    results = [verify_one(nn) for nn in ("01", "02", "03")]
    out = WEB.parent / "topology" / "verification_independent.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "standard": "independent ffprobe + ffmpeg silencedetect verification",
        "silencedetect": {"noise": SILENCE_DB, "duration_s": SILENCE_DUR,
                          "lead_zone_s": LEAD_ZONE_S, "tail_zone_s": TAIL_ZONE_S},
        "lessons": results,
        "ALL_LESSONS_PASS": all(r["ALL_GATES_PASS"] for r in results),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    for r in results:
        print(f"[{r['lesson']}] original={r['original']['duration_sec']}s "
              f"output={r['output']['duration_sec']}s delta={r['duration_delta_sec']}s")
        print(f"  silence>2s runs: {len(r['silence_runs_over_2s'])} total, "
              f"{len(r['internal_silence_runs_over_2s'])} internal")
        for s in r["silence_runs_over_2s"]:
            print(f"    {s['start']:.2f} -> {s['end']:.2f} ({s['length']:.2f}s)")
        b = r["build_report"]
        print(f"  cues={b.get('cue_count')}/{b.get('expected_cue_count')} "
              f"median_fill={b.get('median_fill')} "
              f"max_internal_gap={b.get('max_internal_gap_s')}s "
              f"scale={b.get('timeline_scale')} drift={b.get('max_measured_drift_ms')}ms "
              f"overrun={b.get('overrun_cues')} sfx={b.get('sfx')}")
        print(f"  provenance: oembed_ok={b.get('oembed_ok')} "
              f"uploader={b.get('yt_dlp_uploader')}")
        print(f"  gates: {r['gates']}  ALL={r['ALL_GATES_PASS']}")
    print(f"\nREPORT: {out}")
    print(f"ALL_LESSONS_PASS = {all(r['ALL_GATES_PASS'] for r in results)}")


if __name__ == "__main__":
    main()
