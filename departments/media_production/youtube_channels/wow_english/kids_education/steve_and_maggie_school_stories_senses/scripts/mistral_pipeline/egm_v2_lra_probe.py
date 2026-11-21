#!/usr/bin/env python3
"""Probe: how much compression is needed to bring premix LRA <= 8 LU."""
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PREMIX = os.path.join(ROOT, "audio_takes", "egm_v2_premix_dial_plus_sfx.wav")


def measure(af):
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", PREMIX,
         "-af", af + ",ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True)
    txt = p.stderr
    i = re.search(r"Integrated loudness:\s*\n\s*I:\s*(-?[\d.]+)\s*LUFS", txt)
    lra = re.search(r"Loudness range:\s*\n\s*LRA:\s*(-?[\d.]+)\s*LU", txt)
    tp = re.search(r"True peak:\s*\n\s*Peak:\s*(-?[\d.]+)\s*dBFS", txt)
    return (float(i.group(1)) if i else None,
            float(lra.group(1)) if lra else None,
            float(tp.group(1)) if tp else None)


print("baseline premix:", measure("anull"))
for thr, ratio in [(-24, 2), (-22, 3), (-20, 3), (-18, 4), (-16, 5), (-24, 4), (-20, 5)]:
    af = (f"acompressor=threshold={thr}dB:ratio={ratio}:attack=15:release=350:"
          f"knee=9dB:makeup=0dB:detection=peak")
    print(f"acompressor thr={thr} ratio={ratio}:", measure(af))
# compand alternative
for args in ["0.05,0.2:-60/-60,-30/-20,0/-15,20/0"]:
    pass
print("loudnorm dynamic alone:", end=" ")
p = subprocess.run(
    ["ffmpeg", "-hide_banner", "-nostats", "-i", PREMIX,
     "-af", "loudnorm=I=-14:TP=-1:LRA=8,ebur128=peak=true", "-f", "null", "-"],
    capture_output=True, text=True)
txt = p.stderr
i = re.search(r"Integrated loudness:\s*\n\s*I:\s*(-?[\d.]+)\s*LUFS", txt)
lra = re.search(r"Loudness range:\s*\n\s*LRA:\s*(-?[\d.]+)\s*LU", txt)
tp = re.search(r"True peak:\s*\n\s*Peak:\s*(-?[\d.]+)\s*dBFS", txt)
print((float(i.group(1)) if i else None, float(lra.group(1)) if lra else None, float(tp.group(1)) if tp else None))
# combo: mild comp + loudnorm
for thr, ratio in [(-22, 3), (-20, 4)]:
    af = (f"acompressor=threshold={thr}dB:ratio={ratio}:attack=15:release=350:knee=9dB,"
          f"loudnorm=I=-14:TP=-1:LRA=8")
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", PREMIX,
         "-af", af + ",ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True)
    txt = p.stderr
    i = re.search(r"Integrated loudness:\s*\n\s*I:\s*(-?[\d.]+)\s*LUFS", txt)
    lra = re.search(r"Loudness range:\s*\n\s*LRA:\s*(-?[\d.]+)\s*LU", txt)
    tp = re.search(r"True peak:\s*\n\s*Peak:\s*(-?[\d.]+)\s*dBFS", txt)
    print(f"comp thr={thr} r={ratio} + loudnorm:",
          (float(i.group(1)) if i else None, float(lra.group(1)) if lra else None, float(tp.group(1)) if tp else None))
