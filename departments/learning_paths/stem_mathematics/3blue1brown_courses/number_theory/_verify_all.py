"""Independent verification of the 3 number_theory full-length dubbed videos.

Does NOT trust the build's verification.json gates — it re-measures the rendered
audio from the final MP4. Checks, for each lesson:
  1. ffprobe: output duration ~= original duration (full-length, no trim)
  2. silence scan on the final audio: ZERO internal silent runs > 2 s
     (only lead-in / tail may be silent)
  3. verification.json: median_fill >= 0.72 and max_internal_gap_s <= 1.5
  4. provenance: YouTube oEmbed / yt-dlp metadata confirms 3Blue1Brown
Writes a consolidated report to number_theory/_verify_all_report.json.
"""
import json
import re
import subprocess
import urllib.parse
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
WEB = ROOT.parent / "web_platform"

LESSONS = {
    "lesson_01": {"vid": "EK32jo7i5LQ", "title": "Why do prime numbers make these spirals?"},
    "lesson_02": {"vid": "QJYmyhnaaek", "title": "All possible pythagorean triples, visualized"},
    "lesson_03": {"vid": "NaL_Cb42WyY", "title": "Pi hiding in prime regularities"},
}
SR = 8000
SIL_THR = 0.01          # amplitude threshold for "silence"
LEAD_S = 2.5
TAIL_S = 3.0
RUN_GATE_S = 2.0


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout


def probe_duration(path):
    out = run(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{path}"')
    try:
        return float(out.strip())
    except Exception:
        return 0.0


def probe_streams(path):
    out = run(f'ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,duration -of json "{path}"')
    try:
        return json.loads(out).get("streams", [])
    except Exception:
        return []


def silence_runs(path):
    """Decode final MP4 audio to mono 8k PCM and find silent runs."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1",
         "-ar", str(SR), "-f", "s16le", "-"],
        capture_output=True).stdout
    if not raw:
        return [], 0.0, 0
    a = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    total = len(a) / SR
    loud = np.abs(a) > SIL_THR
    # silent runs (maximal False stretches), ignoring very short ones
    padded = np.concatenate(([True], loud, [True]))
    d = np.diff(padded.astype(np.int8))
    starts = np.flatnonzero(d == -1)
    ends = np.flatnonzero(d == 1)
    runs = []
    for s, e in zip(starts, ends):
        sec = (e - s) / SR
        if sec >= 0.05:
            runs.append({"start_s": round(s / SR, 3),
                         "end_s": round(e / SR, 3),
                         "len_s": round(sec, 3)})
    # A run is INTERNAL only when it lies fully between the designed lead-in
    # and tail margins. Runs touching 0 (lead-in) or the end (tail) are allowed.
    internal = [r for r in runs
                if r["start_s"] >= LEAD_S - 0.15
                and r["end_s"] <= total - TAIL_S + 0.60
                and r["len_s"] > RUN_GATE_S]
    return internal, total, len(runs)


def oembed(vid):
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
    try:
        from urllib import request as _urlrequest
        req = _urlrequest.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with _urlrequest.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode("utf-8"))
            return {"ok": True, "author_name": d.get("author_name"),
                    "title": d.get("title"), "author_url": d.get("author_url")}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def ytdlp_meta(vid):
    out = run(f'python -m yt_dlp --skip-download --no-warnings --print '
              f'"%(id)s|%(uploader)s|%(channel)s|%(title)s|%(duration)s" '
              f'"https://www.youtube.com/watch?v={vid}"')
    parts = (out.strip().splitlines() or [""])[-1].split("|")
    if len(parts) >= 4:
        return {"ok": True, "id": parts[0], "uploader": parts[1],
                "channel": parts[2], "title": parts[3],
                "duration": parts[4] if len(parts) > 4 else None}
    return {"ok": False, "raw": out[-300:]}


def main():
    report = {"generated_by": "number_theory/_verify_all.py (independent re-measurement)", "lessons": {}}
    for lesson, cfg in LESSONS.items():
        orig = WEB / "media_vault" / "number_theory" / lesson / "original_source" / "full_original.mp4"
        out = WEB / "media_vault" / "number_theory" / lesson / "experiments" / f"3b1b_number_theory_{lesson[-2:]}_full_dubbed.mp4"
        verify = ROOT / lesson / "dubbing_pipeline" / "experiments" / "clean_timesync_v2" / "verification.json"

        odur = probe_duration(orig)
        xdur = probe_duration(out)
        internal, adur, nruns = silence_runs(out)
        streams = probe_streams(out)
        v = json.loads(verify.read_text(encoding="utf-8")) if verify.exists() else {}
        gate = v.get("quality_gate", {})

        oe = oembed(cfg["vid"])
        yt = ytdlp_meta(cfg["vid"])
        provenance_ok = (oe.get("ok") and "3blue1brown" in str(oe.get("author_name", "")).lower()) or \
                        (yt.get("ok") and "3blue1brown" in str(yt.get("uploader", "")).lower())

        dur_ok = abs(xdur - odur) <= 3.0
        silence_ok = len(internal) == 0
        fill_ok = bool(gate.get("median_fill_ok")) and v.get("median_fill", 0) >= 0.72
        gap_ok = bool(gate.get("max_internal_gap_ok")) and v.get("max_internal_gap_s", 99) <= 1.5

        entry = {
            "video_id": cfg["vid"],
            "original_duration_sec": round(odur, 3),
            "output_duration_sec": round(xdur, 3),
            "duration_delta_sec": round(xdur - odur, 3),
            "full_length_ok": dur_ok,
            "audio_decoded_duration_sec": round(adur, 3),
            "total_silent_runs_detected": nruns,
            "internal_silent_runs_gt_2s": internal,
            "internal_silence_gate_ok": silence_ok,
            "verification_json": {
                "exists": verify.exists(),
                "cue_count": v.get("cue_count"),
                "expected_cue_count": v.get("expected_cue_count"),
                "failed_tts_cues": v.get("failed_tts_cues"),
                "median_fill": v.get("median_fill"),
                "max_internal_gap_s": v.get("max_internal_gap_s"),
                "timeline_scale": v.get("timeline_scale"),
                "render_rounds": v.get("render_rounds"),
                "scale_recomputed_from_rendered_speech": v.get("scale_recomputed_from_rendered_speech"),
                "quality_gate_passed": gate.get("passed"),
                "speech_ends_before_video_end": v.get("speech_ends_before_video_end"),
                "tail_silence_sec": v.get("tail_silence_sec"),
                "output_size_bytes": v.get("output_size_bytes"),
            },
            "median_fill_gate_ok": fill_ok,
            "max_internal_gap_gate_ok": gap_ok,
            "provenance": {"oembed": oe, "ytdlp": yt, "confirms_3b1b": provenance_ok},
            "output_streams": [{"codec_type": s.get("codec_type"), "codec_name": s.get("codec_name"),
                                "width": s.get("width"), "height": s.get("height"),
                                "duration": s.get("duration")} for s in streams],
            "ALL_GATES_PASS": bool(dur_ok and silence_ok and fill_ok and gap_ok and provenance_ok),
        }
        report["lessons"][lesson] = entry
        print(f"==== {lesson} ====", flush=True)
        print(f"  duration orig={odur:.3f}s out={xdur:.3f}s delta={xdur-odur:+.3f}s ok={dur_ok}", flush=True)
        print(f"  internal silent runs >2s = {len(internal)} ok={silence_ok}", flush=True)
        print(f"  median_fill={v.get('median_fill')} ok={fill_ok}; "
              f"max_internal_gap={v.get('max_internal_gap_s')} ok={gap_ok}", flush=True)
        print(f"  provenance oembed={oe.get('ok')} ytdlp={yt.get('ok')} confirms_3b1b={provenance_ok}", flush=True)
        print(f"  ALL_GATES_PASS={entry['ALL_GATES_PASS']}", flush=True)

    outp = ROOT / "_verify_all_report.json"
    outp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"REPORT: {outp}", flush=True)
    print("OVERALL:", all(x["ALL_GATES_PASS"] for x in report["lessons"].values()), flush=True)


if __name__ == "__main__":
    main()
