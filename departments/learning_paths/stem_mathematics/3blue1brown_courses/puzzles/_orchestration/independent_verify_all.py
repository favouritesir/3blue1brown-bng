# -*- coding: utf-8 -*-
"""Fully independent final verification of all 10 dubbed puzzle videos.

Does NOT trust verification.json: it re-probes the original and the output with
ffprobe, runs ffmpeg silencedetect on the FINAL MP4, measures silence runs, and
compares against the gold manifest cue count. Results are written to
independent_verification.json.
"""
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSES = HERE.parent.parent
WEB = COURSES / "web_platform"
IDS = json.loads((HERE / "official_ids_verified.json").read_text(encoding="utf-8"))
EXPECTED_CUES = {1: 22, 2: 26, 3: 24, 4: 23, 5: 22, 6: 21, 7: 23, 8: 23, 9: 23, 10: 24}


def probe(path, stream=None):
    cmd = ["ffprobe", "-v", "error"]
    if stream:
        cmd += ["-select_streams", stream]
    cmd += ["-show_entries", "format=duration:stream=codec_name,codec_type,width,height",
            "-of", "json", str(path)]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return json.loads(r.stdout) if r.stdout.strip() else {}


def dur(path):
    p = probe(path)
    try:
        return float(p["format"]["duration"])
    except Exception:
        return 0.0


def silence_runs(path, min_dur=2.0, noise="-45dB"):
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-af", f"silencedetect=noise={noise}:d={min_dur}", "-f", "null", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    txt = r.stderr
    starts = [float(x) for x in re.findall(r"silence_start:\s*([0-9.]+)", txt)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([0-9.]+)", txt)]
    return [{"start": round(s, 3),
             "end": round(ends[i], 3) if i < len(ends) else None}
            for i, s in enumerate(starts)]


def main():
    report = []
    for e in IDS["lessons"]:
        n = int(e["lesson"])
        nn = f"{n:02d}"
        base = WEB / "media_vault" / "puzzles" / f"lesson_{nn}"
        orig = base / "original_source" / "full_original.mp4"
        out = base / "experiments" / f"3b1b_puzzles_{nn}_full_dubbed.mp4"
        man = WEB / "assets" / "audio" / "puzzles" / f"lesson_{nn}" / "manifest.json"
        vj = WEB / "data" / "puzzles" / f"lesson_{nn}.json"

        m = json.loads(man.read_text(encoding="utf-8"))
        cue_count = sum(len(s.get("cues", [])) for s in m.get("sections", {}).values())
        lesson = json.loads(vj.read_text(encoding="utf-8"))

        od, vd = dur(orig), dur(out)
        op, vp = probe(orig), probe(out)
        streams = vp.get("streams", [])
        vcodec = next((s.get("codec_name") for s in streams if s.get("codec_type") == "video"), None)
        acodec = next((s.get("codec_name") for s in streams if s.get("codec_type") == "audio"), None)
        runs = silence_runs(out)

        # A silence run is 'internal' if it is bracketed by speech on both
        # sides: it starts after >2s of audio content and ends before the end.
        internal = [r for r in runs
                    if r["start"] > 2.5 and r["end"] is not None and r["end"] < od - 2.5]
        long_internal = [r for r in internal if round(r["end"] - r["start"], 3) > 2.0]

        # Read the pipeline's self-reported gates for cross-check only.
        selfrep = {}
        vpj = base / "experiments" / "verification.json"
        if vpj.exists():
            d = json.loads(vpj.read_text(encoding="utf-8"))
            selfrep = {"self_median_fill": d.get("median_fill"),
                       "self_max_internal_gap_s": d.get("max_internal_gap_s"),
                       "self_gates": d.get("gates"),
                       "self_success": d.get("success")}

        gates = {
            "video_exists": out.exists(),
            "size_gt_placeholder": out.exists() and out.stat().st_size > 100000,
            "duration_match_1s": abs(vd - od) <= 1.0,
            "no_internal_silence_gt_2s": len(long_internal) == 0,
            "cue_count_matches_manifest": cue_count == EXPECTED_CUES[n],
            "official_id_matches_page": lesson.get("yt_id") == e["video_id"],
            "video_codec_h264": vcodec == "h264",
            "audio_codec_aac": acodec == "aac",
        }
        gates["all_pass"] = all(gates.values())
        rec = {
            "lesson": n,
            "slug": e["slug"],
            "video_id": e["video_id"],
            "oembed_author": e["oembed_author"],
            "original_duration_sec": round(od, 3),
            "output_duration_sec": round(vd, 3),
            "duration_delta_sec": round(vd - od, 3),
            "output_size_bytes": out.stat().st_size if out.exists() else 0,
            "video_codec": vcodec,
            "audio_codec": acodec,
            "cue_count_manifest": cue_count,
            "all_silence_runs_ge_2s": runs,
            "internal_silence_runs_gt_2s": long_internal,
            "self_reported": selfrep,
            "gates": gates,
        }
        report.append(rec)
        print(f"L{nn}: dur {vd:.1f}/{od:.1f}s delta={vd-od:+.3f} "
              f"size={rec['output_size_bytes']} "
              f"internal>2s={len(long_internal)} "
              f"gates={gates}", flush=True)

    summary = {
        "all_10_pass": all(r["gates"]["all_pass"] for r in report),
        "pass_count": sum(1 for r in report if r["gates"]["all_pass"]),
        "lessons": report,
    }
    (HERE / "independent_verification.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSUMMARY: {summary['pass_count']}/10 pass; all_10_pass={summary['all_10_pass']}",
          flush=True)


if __name__ == "__main__":
    main()
