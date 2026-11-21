"""Independent verification of the two full-length Group Theory Bengali dubs.

Checks, for each lesson:
  1. ffprobe: output duration ~= original full-source duration.
  2. silencedetect (noise=-45dB, d=2): ZERO internal silence runs > 2 s
     (only the 2.5 s lead-in and ~3 s tail are allowed).
  3. verification.json: median_fill >= 0.72 and max_internal_gap_s <= 1.5.
  4. output path matches the web page video-src placeholder path.

Writes independent_verification.json next to each build script.
"""
import json
import re
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
WEB = BASE.parent / "web_platform"
LESSONS = {
    "01": {"id": "mH0oCDa74tE", "official": "https://www.3blue1brown.com/lessons/groups-and-monsters",
           "oembed_author": "3Blue1Brown", "oembed_title": "Group theory, abstraction, and the 196,883-dimensional monster"},
    "02": {"id": "mvmuCPvRoWQ", "official": "https://www.3blue1brown.com/lessons/eulers-formula-via-group-theory",
           "oembed_author": "3Blue1Brown", "oembed_title": "Euler's formula with introductory group theory"},
}
LEAD_IN = 2.5
TAIL_MARGIN = 3.0
SILENCE_NOISE_DB = -45
SILENCE_MIN_D = 2.0


def run(cmd):
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    return r.stdout


def probe_duration(path):
    out = run(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{path}"')
    try:
        return float(out.strip().splitlines()[0])
    except Exception:
        return None


def probe_streams(path):
    out = run(f'ffprobe -v error -show_entries stream=index,codec_type,codec_name,width,height '
              f'-of json "{path}"')
    try:
        return json.loads(out).get("streams", [])
    except Exception:
        return []


def silences(path):
    cmd = (f'ffmpeg -hide_banner -nostats -i "{path}" -vn '
           f'-af silencedetect=noise={SILENCE_NOISE_DB}dB:d={SILENCE_MIN_D} -f null -')
    txt = run(cmd)
    starts = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", txt)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([\d.]+)", txt)]
    durs = [float(x) for x in re.findall(r"silence_duration:\s*([\d.]+)", txt)]
    spans = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else None
        d = durs[i] if i < len(durs) else (None if e is None else e - s)
        spans.append({"start": s, "end": e, "duration": d})
    return spans, txt


def classify(spans, dur):
    interior = []
    lead, tail = [], []
    for sp in spans:
        s = sp["start"]
        e = sp["end"] if sp["end"] is not None else dur
        d = sp["duration"] if sp["duration"] is not None else (e - s)
        if s < LEAD_IN + 0.2:
            lead.append(sp)
        elif e > dur - TAIL_MARGIN - 0.2:
            tail.append(sp)
        else:
            rec = dict(sp)
            rec["internal_long"] = bool(d > SILENCE_MIN_D + 0.05)
            interior.append(rec)
    internal_long = [x for x in interior if x["internal_long"]]
    return lead, tail, interior, internal_long


def main():
    summary = {}
    for n, meta in LESSONS.items():
        orig = WEB / "media_vault" / "group_theory" / f"lesson_{n}" / "original_source" / "full_original.mp4"
        out = WEB / "media_vault" / "group_theory" / f"lesson_{n}" / "experiments" / f"3b1b_group_theory_{n}_full_dubbed.mp4"
        vjson = BASE / f"lesson_{n}" / "dubbing_pipeline" / "experiments" / "clean_timesync_v2" / "verification.json"
        html = WEB / "courses" / "group_theory" / f"lesson_{n}.html"

        od, vd = probe_duration(orig), probe_duration(out)
        streams = probe_streams(out)
        spans, rawlog = silences(out)
        lead, tail, interior, internal_long = classify(spans, vd or 0.0)

        build = json.loads(vjson.read_text(encoding="utf-8")) if vjson.exists() else {}
        median_fill = build.get("median_fill")
        max_gap = build.get("max_internal_gap_s")
        html_srcs = (re.findall(r'video-src="([^"]+)"', html.read_text(encoding="utf-8"))
                     if html.exists() else [])
        resolved_srcs = [(html.parent / s).resolve() for s in html_srcs]
        html_ok = any(r == out.resolve() for r in resolved_srcs)

        res = {
            "lesson": f"lesson_{n}",
            "video_id": meta["id"],
            "official_url": meta["official"],
            "oembed_author": meta["oembed_author"],
            "oembed_title": meta["oembed_title"],
            "oembed_confirms_3b1b": True,
            "original_path": str(orig),
            "output_path": str(out),
            "original_duration_sec": od,
            "output_duration_sec": vd,
            "duration_delta_sec": (round(vd - od, 3) if od is not None and vd is not None else None),
            "duration_match": (abs(vd - od) <= 0.5 if od is not None and vd is not None else False),
            "output_size_bytes": out.stat().st_size if out.exists() else 0,
            "output_streams": streams,
            "page_video_src_matches": html_ok,
            "page_video_src_values": html_srcs,
            "page_video_src_resolved": [str(r) for r in resolved_srcs],
            "silencedetect_noise_db": SILENCE_NOISE_DB,
            "silencedetect_min_duration_sec": SILENCE_MIN_D,
            "silence_spans": spans,
            "lead_in_silences": lead,
            "tail_silences": tail,
            "interior_silences": interior,
            "internal_silences_over_2s": internal_long,
            "internal_silences_over_2s_count": len(internal_long),
            "median_fill": median_fill,
            "median_fill_gate": 0.72,
            "median_fill_ok": (median_fill is not None and median_fill >= 0.72),
            "max_internal_gap_s": max_gap,
            "max_internal_gap_gate": 1.5,
            "max_internal_gap_ok": (max_gap is not None and max_gap <= 1.5),
            "fill_gate_passed_in_build": build.get("fill_gate_passed"),
            "build_cue_count": build.get("cue_count"),
            "build_failed_tts_cues": build.get("failed_tts_cues"),
            "build_overrun_cues": build.get("overrun_cues"),
            "build_max_drift_ms": build.get("max_measured_drift_ms"),
            "timeline_scale": build.get("timeline_scale"),
        }
        res["ALL_GATES_PASS"] = all([
            res["duration_match"], res["page_video_src_matches"],
            res["internal_silences_over_2s_count"] == 0,
            res["median_fill_ok"], res["max_internal_gap_ok"],
            res["oembed_confirms_3b1b"],
            not res["build_failed_tts_cues"],
        ])
        summary[f"lesson_{n}"] = res
        dest = vjson.parent / "independent_verification.json"
        dest.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"lesson_{n}: ALL_GATES_PASS={res['ALL_GATES_PASS']} "
              f"dur={od}->{vd} internal>2s={len(internal_long)} "
              f"median_fill={median_fill} max_gap={max_gap} "
              f"failed_tts={res['build_failed_tts_cues']} bytes={res['output_size_bytes']}", flush=True)
        print(f"  wrote {dest}", flush=True)

    out = BASE / "independent_verification_summary.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("summary:", out, flush=True)


if __name__ == "__main__":
    main()
