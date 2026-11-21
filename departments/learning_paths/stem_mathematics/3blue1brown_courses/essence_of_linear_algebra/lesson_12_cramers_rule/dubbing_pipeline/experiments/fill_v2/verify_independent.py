"""Independent cross-check of the fill_v2 render (does not modify anything).

Checks, from the actual rendered artifacts:
  1. ffprobe duration of original vs output (delta <= 1.0 s).
  2. ffmpeg silencedetect @ -40 dB : internal silence runs > 2 s inside
     (LEAD_IN+0.1, vend-TAIL_MARGIN-0.1) -> must be 0.
  3. Raw-PCM RMS scan (threshold 0.01, 20 ms hop) over the same internal
     window -> runs > 2 s must be 0, max run reported.
  4. All gates in the build's verification.json must be true.
"""
import re
import json
import subprocess
import wave
from pathlib import Path

import numpy as np

EXP = Path(__file__).resolve().parent
BASE = EXP.parent.parent
WEB = BASE.parents[2] / "web_platform"
ORIGINAL = WEB / "media_vault" / "lesson_12" / "original_source" / "full_original.mp4"
OUTPUT = WEB / "media_vault" / "lesson_12" / "experiments" / "fill_v2" / "3b1b_lesson_12_full_dubbed_fill2.mp4"
VERIFY = EXP / "verification.json"
TMP = EXP / "_verify_decode.wav"

LEAD_IN = 2.5
TAIL_MARGIN = 3.0
SR = 44100
GATE_SEC = 2.0


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(r.stdout.strip())


def silencedetect(path, lo, hi):
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-vn", "-i", str(path),
           "-af", "silencedetect=noise=-40dB:d=0.5", "-f", "null", "-"]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    txt = r.stderr or ""
    starts = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", txt)]
    ends = re.findall(r"silence_end:\s*([\d.]+)\s*\|\s*silence_duration:\s*([\d.]+)", txt)
    internal = []
    for s, (e, d) in zip(starts, ends):
        e, d = float(e), float(d)
        if s >= lo and e <= hi and d > GATE_SEC:
            internal.append({"start": round(s, 3), "end": round(e, 3), "duration": round(d, 3)})
    return internal


def rms_scan(path, lo, hi):
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-nostats", "-vn", "-i", str(path),
                    "-af", "aresample=44100", "-ar", "44100", "-ac", "1",
                    "-c:a", "pcm_s16le", str(TMP)],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with wave.open(str(TMP), "rb") as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    seg = x[int(lo * SR):int(hi * SR)]
    hop = int(0.020 * SR)
    frames = [np.sqrt(np.mean(seg[i:i + hop] ** 2)) < 0.01
              for i in range(0, len(seg), hop)]
    runs = []
    f = 0
    while f < len(frames):
        if frames[f]:
            g = f
            while g + 1 < len(frames) and frames[g + 1]:
                g += 1
            runs.append(round((g - f + 1) * hop / SR, 3))
            f = g + 1
        else:
            f += 1
    TMP.unlink(missing_ok=True)
    big = [r for r in runs if r > GATE_SEC]
    return big, (max(runs) if runs else 0.0)


def main():
    vd, od = dur(ORIGINAL), dur(OUTPUT)
    lo, hi = LEAD_IN + 0.1, vd - TAIL_MARGIN - 0.1
    sd = silencedetect(OUTPUT, lo, hi)
    big, max_run = rms_scan(OUTPUT, lo, hi)
    rep = json.loads(VERIFY.read_text(encoding="utf-8"))
    gates = {k: rep.get(k) for k in ("gate_median_fill_ok", "gate_internal_gap_ok",
                                     "gate_pockets_ok", "gate_duration_ok", "all_gates_pass")}
    ok = (abs(od - vd) <= 1.0 and not sd and not big and all(gates.values()))
    print(json.dumps({
        "original_duration_s": round(vd, 3),
        "output_duration_s": round(od, 3),
        "duration_delta_s": round(od - vd, 3),
        "silencedetect_minus40_internal_runs_gt2s": len(sd),
        "silencedetect_details": sd,
        "rms_scan_runs_gt2s": len(big),
        "rms_scan_max_run_s": max_run,
        "rms_scan_details": big,
        "build_gates": gates,
        "median_fill": rep.get("median_fill"),
        "max_internal_gap_s": rep.get("max_internal_gap_s"),
        "INDEPENDENT_PASS": bool(ok),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
