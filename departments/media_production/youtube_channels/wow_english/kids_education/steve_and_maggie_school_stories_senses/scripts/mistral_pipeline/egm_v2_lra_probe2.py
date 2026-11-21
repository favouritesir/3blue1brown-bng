#!/usr/bin/env python3
"""Probe 2: chained loudnorm dynamic passes / lower LRA targets to reach <=8 LU."""
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PREMIX = os.path.join(ROOT, "audio_takes", "egm_v2_premix_dial_plus_sfx.wav")
TMP = r"C:\Users\Ashik\AppData\Local\Temp\opencode\egm_v2_probe2"
os.makedirs(TMP, exist_ok=True)


def measure_file(path):
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path,
         "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True)
    txt = p.stderr
    i = re.search(r"Integrated loudness:\s*\n\s*I:\s*(-?[\d.]+)\s*LUFS", txt)
    lra = re.search(r"Loudness range:\s*\n\s*LRA:\s*(-?[\d.]+)\s*LU", txt)
    tp = re.search(r"True peak:\s*\n\s*Peak:\s*(-?[\d.]+)\s*dBFS", txt)
    return (round(float(i.group(1)), 2) if i else None,
            round(float(lra.group(1)), 2) if lra else None,
            round(float(tp.group(1)), 2) if tp else None)


def loudnorm_pass(src, dst, lra_target):
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", src,
         "-af", f"loudnorm=I=-14:TP=-1:LRA={lra_target}:print_format=json",
         "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"\{.*\}", p.stderr, re.S)
    import json
    meas = json.loads(m.group(0))
    af = (f"loudnorm=I=-14:TP=-1:LRA={lra_target}"
          f":measured_I={meas['input_i']}:measured_TP={meas['input_tp']}"
          f":measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}"
          f":offset={meas['target_offset']}:linear=false")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src,
                    "-af", af, "-ar", "44100", "-ac", "2", "-c:a", "pcm_s24le", dst],
                   check=True)
    return meas


cur = PREMIX
for k in range(1, 5):
    dst = os.path.join(TMP, f"ln_pass{k}.wav")
    meas = loudnorm_pass(cur, dst, 8)
    print(f"pass {k}: measured_in I={meas['input_i']} LRA={meas['input_lra']} TP={meas['input_tp']} -> out {measure_file(dst)}")
    cur = dst

# lower LRA target single pass from premix
for lra_t in (6, 5, 4):
    dst = os.path.join(TMP, f"ln_lra{lra_t}.wav")
    loudnorm_pass(PREMIX, dst, lra_t)
    print(f"LRA target {lra_t}: out {measure_file(dst)}")

# mild comp + loudnorm LRA=6
comp = "acompressor=threshold=-22dB:ratio=3:attack=15:release=350:knee=9dB"
mid = os.path.join(TMP, "comp.wav")
subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", PREMIX,
                "-af", comp, "-ar", "44100", "-c:a", "pcm_s24le", mid], check=True)
print("comp only:", measure_file(mid))
for lra_t in (8, 6):
    dst = os.path.join(TMP, f"comp_ln{lra_t}.wav")
    loudnorm_pass(mid, dst, lra_t)
    print(f"comp + loudnorm LRA={lra_t}: out {measure_file(dst)}")
