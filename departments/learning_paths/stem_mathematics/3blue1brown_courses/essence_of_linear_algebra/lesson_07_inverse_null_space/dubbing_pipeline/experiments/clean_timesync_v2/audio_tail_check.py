"""Definitive waveform-level check of intro/final silence (numpy, no ffmpeg -ss)."""
import sys
import wave
import numpy as np


def load(path):
    with wave.open(path, "rb") as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32768.0
        sr = w.getframerate()
    return a, sr


def rms_db(a):
    r = float(np.sqrt(np.mean(a * a)))
    if r == 0.0:
        return -91.0
    return round(20 * np.log10(r), 2)


def check(path):
    a, sr = load(path)
    n = len(a)
    last_loud = int(np.max(np.where(np.abs(a) > 1e-4)[0])) if np.any(np.abs(a) > 1e-4) else -1
    print(f"--- {path} ---")
    print(f"duration={n/sr:.3f}s sr={sr} samples={n}")
    print(f"intro[0:2]   mean_volume = {rms_db(a[0:2*sr])} dB")
    print(f"final[-2s:]  mean_volume = {rms_db(a[-2*sr:])} dB")
    print(f"final[-3s:]  mean_volume = {rms_db(a[-3*sr:])} dB")
    print(f"peak overall = {float(np.max(np.abs(a))):.4f}")
    print(f"last audible sample = {last_loud/sr:.3f}s  -> tail silence = {(n-last_loud)/sr:.3f}s")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        check(p)
