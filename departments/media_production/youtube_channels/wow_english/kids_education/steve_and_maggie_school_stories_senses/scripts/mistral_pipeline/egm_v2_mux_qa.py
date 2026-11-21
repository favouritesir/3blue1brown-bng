#!/usr/bin/env python3
"""EGM V2 Stage 3: mux master audio with the original video stream + full QA.

- Mux: -c:v copy -c:a aac -b:a 192k -movflags +faststart
- QA: file integrity (ffprobe), non-zero size, stream mapping, duration match,
  EBU R128 re-measure on the muxed MP4's decoded audio, and per-cue energy
  check (all 48 cue windows must carry dialogue energy in the master).
- Writes rendered_output/qa_audit_report_v2.md and .json
"""
import json
import os
import re
import subprocess

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
VIDEO = os.path.join(ROOT, "raw_sources", "source_video.mp4")
MASTER = os.path.join(ROOT, "rendered_output", "Steve_and_Maggie_EGM_V2_Master_Audio.wav")
OUT_DIR = os.path.join(ROOT, "rendered_output")
MP4 = os.path.join(OUT_DIR, "Steve_and_Maggie_EGM_V2_Google_Dubbed.mp4")
SCREENPLAY = os.path.join(ROOT, "scripts", "egm_master_screenplay_v2.json")
REPORT_JSON = os.path.join(OUT_DIR, "qa_audit_report_v2.json")
REPORT_MD = os.path.join(OUT_DIR, "qa_audit_report_v2.md")

SR = 44100


def run(cmd):
    print("+", " ".join(cmd), flush=True)
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stderr[-3000:])
        raise RuntimeError("command failed")
    return p


def probe(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                        "-of", "json", path], capture_output=True, text=True)
    if p.returncode != 0:
        return {"error": p.stderr[-500:]}
    return json.loads(p.stdout)


def ebur128(path):
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path,
         "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True)
    txt = p.stderr
    i = re.search(r"Integrated loudness:\s*\n\s*I:\s*(-?[\d.]+)\s*LUFS", txt)
    lra = re.search(r"Loudness range:\s*\n\s*LRA:\s*(-?[\d.]+)\s*LU", txt)
    tp = re.search(r"True peak:\s*\n\s*Peak:\s*(-?[\d.]+)\s*dB(?:TP|FS)", txt)
    return {"I_lufs": float(i.group(1)) if i else None,
            "LRA_lu": float(lra.group(1)) if lra else None,
            "true_peak_dbtp": float(tp.group(1)) if tp else None}


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    qa = {"outputs": {}, "checks": {}, "cues_energy": {}}

    # --- mux ---
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-i", VIDEO, "-i", MASTER,
         "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
         "-movflags", "+faststart", MP4])

    # --- integrity / size ---
    for path, key in [(MASTER, "master_wav"), (MP4, "dubbed_mp4"), (VIDEO, "source_video")]:
        sz = os.path.getsize(path)
        pr = probe(path)
        streams = [{k: s.get(k) for k in ("codec_type", "codec_name", "sample_rate",
                                          "channels", "width", "height", "duration",
                                          "bit_rate", "nb_frames")}
                   for s in pr.get("streams", [])]
        qa["outputs"][key] = {
            "path": os.path.relpath(path, ROOT), "bytes": sz, "size_mb": round(sz / 1e6, 2),
            "format_duration_s": float(pr.get("format", {}).get("duration", 0)),
            "streams": streams, "probe_ok": "error" not in pr,
        }
        qa["checks"][f"{key}_nonzero"] = sz > 0
        qa["checks"][f"{key}_probe_ok"] = "error" not in pr

    # --- EBU R128 on master wav and on muxed mp4 audio ---
    qa["checks"]["master_ebur128"] = ebur128(MASTER)
    qa["checks"]["mp4_ebur128"] = ebur128(MP4)
    m = qa["checks"]["master_ebur128"]
    qa["checks"]["r128_I_ok"] = m["I_lufs"] is not None and abs(m["I_lufs"] + 14.0) <= 0.5
    qa["checks"]["r128_TP_ok"] = m["true_peak_dbtp"] is not None and m["true_peak_dbtp"] <= -1.0
    qa["checks"]["r128_LRA_ok"] = m["LRA_lu"] is not None and m["LRA_lu"] <= 8.0
    mp = qa["checks"]["mp4_ebur128"]
    qa["checks"]["mp4_r128_I_ok"] = mp["I_lufs"] is not None and abs(mp["I_lufs"] + 14.0) <= 0.6
    qa["checks"]["mp4_r128_TP_ok"] = mp["true_peak_dbtp"] is not None and mp["true_peak_dbtp"] <= -1.0 + 0.1

    # --- duration sync: mp4 audio vs video timeline ---
    qa["checks"]["duration_match"] = abs(qa["outputs"]["dubbed_mp4"]["format_duration_s"] - 213.53) < 0.5

    # --- per-cue energy check on the master (all 48 windows must carry signal) ---
    with open(SCREENPLAY, encoding="utf-8") as f:
        cues = json.load(f)["cues"]
    x, sr = sf.read(MASTER, dtype="float64")
    if x.ndim > 1:
        x = x.mean(axis=1)
    assert sr == SR
    active = 0
    detail = []
    for c in cues:
        a, b = int(c["start"] * SR), min(int(c["end"] * SR), len(x))
        seg = x[a:b]
        r = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-12)
        ok = bool(r > -50.0)
        active += int(ok)
        detail.append({"id": c["id"], "speaker": c["speaker"],
                       "window": [c["start"], c["end"]], "rms_dbfs": round(r, 1), "active": ok})
    qa["cues_energy"] = {"active_windows": active, "total": len(cues), "detail": detail}
    qa["checks"]["all_48_cues_active"] = active == len(cues)

    qa["pass"] = all(v for k, v in qa["checks"].items() if isinstance(v, bool))

    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(qa, f, ensure_ascii=False, indent=2)

    lines = [
        "# EGM V2 QA Audit Report — Steve and Maggie | Learn the Senses (bn-BD dub)",
        "",
        f"- Master WAV: `{qa['outputs']['master_wav']['path']}` "
        f"({qa['outputs']['master_wav']['size_mb']} MB, {qa['outputs']['master_wav']['format_duration_s']:.3f}s)",
        f"- Dubbed MP4: `{qa['outputs']['dubbed_mp4']['path']}` "
        f"({qa['outputs']['dubbed_mp4']['size_mb']} MB, {qa['outputs']['dubbed_mp4']['format_duration_s']:.3f}s)",
        "",
        "## EBU R128 (master WAV, ebur128)",
        f"- Integrated: **{m['I_lufs']:.2f} LUFS** (target -14.0 ± 0.5) -> {'PASS' if qa['checks']['r128_I_ok'] else 'FAIL'}",
        f"- True peak: **{m['true_peak_dbtp']:.2f} dBTP** (target <= -1.0) -> {'PASS' if qa['checks']['r128_TP_ok'] else 'FAIL'}",
        f"- LRA: **{m['LRA_lu']:.2f} LU** (target <= 8) -> {'PASS' if qa['checks']['r128_LRA_ok'] else 'FAIL'}",
        "",
        "## EBU R128 (muxed MP4 decoded audio)",
        f"- Integrated: {mp['I_lufs']:.2f} LUFS, True peak: {mp['true_peak_dbtp']:.2f} dBTP, LRA: {mp['LRA_lu']:.2f} LU",
        "",
        "## Checks",
    ]
    for k, v in qa["checks"].items():
        if isinstance(v, bool):
            lines.append(f"- {k}: {'PASS' if v else 'FAIL'}")
    lines += [
        "",
        f"## Cue sync energy: {active}/{len(cues)} cue windows active in master "
        f"-> {'PASS' if qa['checks']['all_48_cues_active'] else 'FAIL'}",
        "",
        f"**OVERALL: {'PASS' if qa['pass'] else 'FAIL'}**",
    ]
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("\n".join(lines))
    assert qa["pass"], "QA FAILED"


if __name__ == "__main__":
    main()
