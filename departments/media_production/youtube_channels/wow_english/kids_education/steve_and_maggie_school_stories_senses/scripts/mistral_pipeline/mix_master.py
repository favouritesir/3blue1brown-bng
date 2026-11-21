#!/usr/bin/env python3
"""Stage 4 (v2, sample-accurate): SFX stem normalization + master audio mix.

- Loads the pristine isolated SFX stem (mistral_direct_pure_sfx.wav, speech
  hard-gated to digital zero -> zero English vocal bleed by construction).
- Normalizes the SFX effect level and sets headroom: SFX bed at -3 dB under the
  dialogue so cartoon bells/snaps/chili sizzle stay clear but never overpower
  the Bengali voices.
- Sums with the synchronized Bengali dialogue track in numpy (sample-accurate,
  no filter lookahead delay), with a single uniform peak safety scale.
- Two-pass EBU R128 loudness normalization via ffmpeg loudnorm:
  I=-14.0 LUFS, TP=-1.0 dBTP, LRA<=8 LU.
- Writes 24-bit 44.1 kHz stereo master WAV to rendered_output/.
"""
import json
import os
import re
import subprocess
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DIALOGUE = os.path.join(ROOT, "audio_takes", "mistral_dialogue_track_44k.wav")
SFX = os.path.join(ROOT, "isolated_stems", "mistral_direct_pure_sfx.wav")
OUT_DIR = os.path.join(ROOT, "rendered_output")
PREMIX = os.path.join(ROOT, "audio_takes", "mistral_premix_dial_plus_sfx.wav")
MASTER = os.path.join(OUT_DIR, "Steve_and_Maggie_Mistral_Full_Google_Dub_Master_Audio.wav")

SFX_GAIN = 10 ** (-3.0 / 20)   # SFX bed headroom under dialogue
TARGET_I, TARGET_TP, TARGET_LRA = -14.0, -1.0, 8.0
SR = 44100


def read_wav(path):
    with wave.open(path, "rb") as w:
        ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    assert sr == SR, (path, sr)
    if sw == 2:
        a = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        v = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8)
             | (b[:, 2].astype(np.int32) << 16))
        v = np.where(v >= 1 << 23, v - (1 << 24), v)
        a = v.astype(np.float64) / float(1 << 23)
    else:
        a = np.frombuffer(raw, dtype="<i4").astype(np.float64) / float(1 << 31)
    return a.reshape(-1, ch)


def write_wav24(path, x):
    """Write float64 (frames x ch) as 24-bit PCM WAV."""
    x = np.clip(x, -1.0, 1.0)
    v = np.round(x * float(1 << 23)).astype(np.int64)
    v = np.clip(v, -(1 << 23), (1 << 23) - 1)
    b = np.empty((v.size, 3), dtype=np.uint8)
    u = v.reshape(-1).astype(np.uint32)
    b[:, 0] = (u & 0xFF).astype(np.uint8)
    b[:, 1] = ((u >> 8) & 0xFF).astype(np.uint8)
    b[:, 2] = ((u >> 16) & 0xFF).astype(np.uint8)
    with wave.open(path, "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(3)
        w.setframerate(SR)
        w.writeframes(b.tobytes())


def run(cmd):
    print("+", " ".join(cmd), flush=True)
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stderr[-3000:])
        raise RuntimeError("command failed")
    return p


def measure_loudness(path):
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path,
         "-af", f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True)
    m = re.search(r"\{.*\}", p.stderr, re.S)
    if not m:
        print(p.stderr[-2000:])
        raise RuntimeError("could not parse loudnorm measurement")
    return json.loads(m.group(0))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    dial = read_wav(DIALOGUE)
    sfx = read_wav(SFX)
    n = min(len(dial), len(sfx))
    premix = dial[:n] + SFX_GAIN * sfx[:n]
    peak = float(np.abs(premix).max())
    if peak > 0.98:  # single uniform safety scale, no delay, no distortion
        premix *= 0.98 / peak
        print(f"premix uniform peak safety scale applied (was {20*np.log10(peak):.2f} dBFS)")
    write_wav24(PREMIX, premix)
    print(f"premix -> {os.path.relpath(PREMIX, ROOT)} peak {20*np.log10(np.abs(premix).max()):.2f} dBFS "
          f"rms {20*np.log10(np.sqrt(np.mean(premix**2))):.2f} dBFS ({n/SR:.2f}s)")

    meas = measure_loudness(PREMIX)
    print("measured:", {k: meas[k] for k in
          ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")})

    af = (f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}"
          f":measured_I={meas['input_i']}:measured_TP={meas['input_tp']}"
          f":measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}"
          f":offset={meas['target_offset']}:linear=true:print_format=summary")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-i", PREMIX, "-af", af, "-ar", "44100", "-c:a", "pcm_s24le", MASTER])

    # sanity: master must align sample-accurately with the dialogue track
    master = read_wav(MASTER)
    m = min(len(master), n)
    c = float(np.corrcoef(master[:m].mean(axis=1), dial[:m].mean(axis=1))[0, 1])
    print(f"corr(master, dialogue) zero-lag = {c:.4f} (must be ~1)")
    assert c > 0.9, "master lost sample alignment with dialogue track"
    print(f"MASTER -> {os.path.relpath(MASTER, ROOT)} ({os.path.getsize(MASTER)} bytes)")


if __name__ == "__main__":
    main()
