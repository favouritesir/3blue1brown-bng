import soundfile as sf
import numpy as np
import librosa
import scipy.signal

# Test on test_intro_0_15.wav
y, sr = librosa.load('test_intro_0_15.wav', sr=None, mono=False)
if y.ndim == 1:
    y = np.stack([y, y])

mono = np.mean(y, axis=0)

# 1. Harmonic-Percussive Separation
# SFX like pops, boings, clicks, bell strikes have strong percussive & high-frequency components
y_harm, y_perc = librosa.effects.hpss(mono, margin=(1.2, 3.0))

print(f"y RMS: {np.sqrt(np.mean(mono**2)):.4f}")
print(f"y_harm RMS: {np.sqrt(np.mean(y_harm**2)):.4f}")
print(f"y_perc RMS: {np.sqrt(np.mean(y_perc**2)):.4f}")
