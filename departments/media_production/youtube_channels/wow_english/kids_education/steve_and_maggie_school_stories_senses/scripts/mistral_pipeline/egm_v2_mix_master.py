#!/usr/bin/env python3
"""EGM V2 Stage 2: SFX bed balancing + two-pass EBU R128 mastering.

- Dialogue bed: audio_takes/egm_v2_dialogue_track_44k.wav (48 cues synced).
- SFX stem: isolated_stems/mistral_direct_pure_sfx.wav (zero vocal bleed).
  Balanced UNDER the dialogue bed at -3 dB headroom: SFX RMS is set to
  (dialogue RMS - 3 dB), clamped to a sane gain range.
- Premix summed in float64 (sample-accurate), single uniform peak safety scale.
- Two-pass EBU R128 loudness normalization, target I=-14.0 LUFS, TP=-1.0 dBTP,
  LRA<=8 LU:
    pass 1  ffmpeg loudnorm measurement (integrated I, true peak, LRA, thresh)
    pass 2  linear gain applied in numpy (sample-accurate, no resample) when
            feasible within the TP ceiling; otherwise ffmpeg loudnorm dynamic
            mode (linear=false) to also pull LRA into range.
- Verification: ffmpeg ebur128 re-measure of the written master.
- Output: rendered_output/Steve_and_Maggie_EGM_V2_Master_Audio.wav (PCM24 44.1k)
"""
import json
import os
import re
import subprocess

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DIALOGUE = os.path.join(ROOT, "audio_takes", "egm_v2_dialogue_track_44k.wav")
SFX = os.path.join(ROOT, "isolated_stems", "mistral_direct_pure_sfx.wav")
OUT_DIR = os.path.join(ROOT, "rendered_output")
PREMIX = os.path.join(ROOT, "audio_takes", "egm_v2_premix_dial_plus_sfx.wav")
MASTER = os.path.join(OUT_DIR, "Steve_and_Maggie_EGM_V2_Master_Audio.wav")
REPORT = os.path.join(OUT_DIR, "egm_v2_mastering_report.json")

SR = 44100
TARGET_I, TARGET_TP, TARGET_LRA = -14.0, -1.0, 8.0
SFX_HEADROOM_DB = -3.0


def run(cmd):
    print("+", " ".join(cmd), flush=True)
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stderr[-3000:])
        raise RuntimeError("command failed: " + " ".join(cmd))
    return p


def measure_loudnorm(path):
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path,
         "-af", f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json",
         "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"\{.*\}", p.stderr, re.S)
    if not m:
        print(p.stderr[-2000:])
        raise RuntimeError("could not parse loudnorm measurement")
    return json.loads(m.group(0))


def measure_ebur128(path):
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path,
         "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True)
    txt = p.stderr
    out = {}
    m = re.search(r"Integrated loudness:\s*\n\s*I:\s*(-?[\d.]+)\s*LUFS", txt)
    out["I_lufs"] = float(m.group(1)) if m else None
    m = re.search(r"Loudness range:\s*\n\s*LRA:\s*(-?[\d.]+)\s*LU", txt)
    out["LRA_lu"] = float(m.group(1)) if m else None
    m = re.search(r"Threshold:\s*(-?[\d.]+)\s*LUFS", txt)
    out["threshold_lufs"] = float(m.group(1)) if m else None
    m = re.search(r"True peak:\s*\n\s*Peak:\s*(-?[\d.]+)\s*dB(?:TP|FS)", txt)
    if not m:
        peaks = re.findall(r"True peak:\s*\n\s*Peak:\s*(-?[\d.]+)", txt)
        out["true_peak_dbtp"] = max(float(v) for v in peaks) if peaks else None
    else:
        out["true_peak_dbtp"] = float(m.group(1))
    return out


def rms(x):
    return float(np.sqrt(np.mean(x ** 2))) if x.size else 0.0


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    dial, sr1 = sf.read(DIALOGUE, dtype="float64")
    sfx, sr2 = sf.read(SFX, dtype="float64")
    assert sr1 == sr2 == SR, (sr1, sr2)
    n = min(len(dial), len(sfx))
    dial, sfx = dial[:n], sfx[:n]
    if dial.ndim == 1:
        dial = np.stack([dial, dial], axis=1)
    if sfx.ndim == 1:
        sfx = np.stack([sfx, sfx], axis=1)

    # --- SFX bed at -3 dB headroom under the dialogue bed (RMS-balanced) ---
    r_d, r_s = rms(dial), rms(sfx)
    gain = (r_d * 10 ** (SFX_HEADROOM_DB / 20.0)) / max(r_s, 1e-12)
    gain = float(min(max(gain, 0.05), 4.0))
    print(f"dialogue RMS {20*np.log10(r_d+1e-12):.2f} dBFS | sfx RMS {20*np.log10(r_s+1e-12):.2f} dBFS "
          f"-> sfx gain {20*np.log10(gain):.2f} dB ({gain:.4f}) => bed at {SFX_HEADROOM_DB} dB under dialogue")

    premix = dial + gain * sfx
    peak = float(np.abs(premix).max())
    safety = 1.0
    if peak > 0.98:
        safety = 0.98 / peak
        premix *= safety
        print(f"premix peak safety scale x{safety:.4f} (peak was {20*np.log10(peak):.2f} dBFS)")
    sf.write(PREMIX, premix, SR, subtype="PCM_24")
    print(f"premix -> {os.path.relpath(PREMIX, ROOT)} ({n/SR:.3f}s, peak {20*np.log10(np.abs(premix).max()+1e-12):.2f} dBFS)")

    # --- pass 1: EBU R128 measurement ---
    meas = measure_loudnorm(PREMIX)
    I, TP, LRA, thresh = (float(meas["input_i"]), float(meas["input_tp"]),
                          float(meas["input_lra"]), float(meas["input_thresh"]))
    print(f"pass 1 measured: I={I:.2f} LUFS, TP={TP:.2f} dBTP, LRA={LRA:.2f} LU, thresh={thresh:.2f}")

    # --- pass 2: apply normalization; iterate until EBU R128 compliant ---
    # Pure linear gain is TP-infeasible here (premix TP -0.18 dBTP, needs +4.5 dB),
    # and LRA 12.7 > 8, so ffmpeg loudnorm dynamic mode is applied iteratively
    # (measure -> apply) until I=-14 LUFS, TP<=-1.0 dBTP (with margin), LRA<=8 LU.
    TP_MARGIN = 1.3   # loudnorm TP target, leaves 0.3 dB margin under -1.0
    tmpdir = r"C:\Users\Ashik\AppData\Local\Temp\opencode\egm_v2_loudnorm"
    os.makedirs(tmpdir, exist_ok=True)
    tmps = [os.path.join(tmpdir, "iter_a.wav"), os.path.join(tmpdir, "iter_b.wav")]
    cur = PREMIX
    passes = []
    ver = None
    for k in range(1, 7):
        m = measure_loudnorm(cur)
        af = (f"loudnorm=I={TARGET_I}:TP=-{TP_MARGIN}:LRA={TARGET_LRA}"
              f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
              f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
              f":offset={m['target_offset']}:linear=false")
        dst = tmps[k % 2]
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", cur,
             "-af", af, "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s24le", dst])
        ver = measure_ebur128(dst)
        passes.append({"pass": k, "measured_in": {k2: m[k2] for k2 in
                        ("input_i", "input_tp", "input_lra", "input_thresh")},
                       "out": ver})
        print(f"pass 2.{k}: in I={m['input_i']} LRA={m['input_lra']} TP={m['input_tp']} "
              f"-> out I={ver['I_lufs']:.2f} LUFS, LRA={ver['LRA_lu']:.2f} LU, TP={ver['true_peak_dbtp']:.2f} dBTP")
        cur = dst
        if (abs(ver["I_lufs"] - TARGET_I) <= 0.3 and ver["LRA_lu"] <= TARGET_LRA
                and ver["true_peak_dbtp"] <= TARGET_TP - 0.05):
            break
    # write final compliant result to the master path
    if cur != MASTER:
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", cur,
             "-c:a", "copy", MASTER])
    mode = "dynamic_iterated"
    g_applied = None
    # final linear trim in numpy if I is off but TP has room
    if abs(ver["I_lufs"] - TARGET_I) > 0.05 and ver["true_peak_dbtp"] + (TARGET_I - ver["I_lufs"]) <= TARGET_TP - 0.05:
        master, _ = sf.read(MASTER, dtype="float64")
        g2 = TARGET_I - ver["I_lufs"]
        master *= 10 ** (g2 / 20.0)
        sf.write(MASTER, master, SR, subtype="PCM_24")
        ver = measure_ebur128(MASTER)
        print(f"pass 3 final linear trim {g2:+.2f} dB -> I={ver['I_lufs']:.2f} LUFS, "
              f"LRA={ver['LRA_lu']:.2f} LU, TP={ver['true_peak_dbtp']:.2f} dBTP")
    print(f"verify (ebur128) final: I={ver['I_lufs']:.2f} LUFS, LRA={ver['LRA_lu']:.2f} LU, "
          f"TP={ver['true_peak_dbtp']:.2f} dBTP")

    size = os.path.getsize(MASTER)
    info = sf.info(MASTER)
    report = {
        "stage": "egm_v2_mastering",
        "dialogue_bed": os.path.relpath(DIALOGUE, ROOT),
        "sfx_stem": os.path.relpath(SFX, ROOT),
        "sfx_headroom_db": SFX_HEADROOM_DB,
        "sfx_gain_db": round(20 * np.log10(gain), 3),
        "premix_peak_safety_scale": round(safety, 5),
        "pass1_measured": {"I_lufs": I, "TP_dbtp": TP, "LRA_lu": LRA, "thresh_lufs": thresh},
        "pass2_mode": mode,
        "pass2_iterations": passes,
        "pass2_linear_gain_db": g_applied,
        "verification_ebur128": ver,
        "targets": {"I_lufs": TARGET_I, "TP_dbtp": TARGET_TP, "LRA_lu_max": TARGET_LRA},
        "master_wav": os.path.relpath(MASTER, ROOT),
        "master_bytes": size,
        "master_format": {"samplerate": info.samplerate, "channels": info.channels,
                          "subtype": info.subtype, "duration_s": round(info.frames / info.samplerate, 3)},
        "pass": bool(ver["I_lufs"] is not None and abs(ver["I_lufs"] - TARGET_I) <= 0.5
                     and ver["true_peak_dbtp"] is not None and ver["true_peak_dbtp"] <= TARGET_TP + 0.05
                     and ver["LRA_lu"] is not None and ver["LRA_lu"] <= TARGET_LRA + 0.05
                     and size > 0),
    }
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"report -> {os.path.relpath(REPORT, ROOT)} | pass={report['pass']}")
    print(f"MASTER -> {os.path.relpath(MASTER, ROOT)} ({size} bytes, {info.frames/info.samplerate:.3f}s, {info.subtype})")
    assert report["pass"], "master failed EBU R128 verification"


if __name__ == "__main__":
    main()
