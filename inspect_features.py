import librosa
import numpy as np

y, sr = librosa.load('slice_0_2.wav', sr=None)
# Estimate fundamental frequency
f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
voiced_f0 = f0[~np.isnan(f0)]
print("Voiced frames count:", len(voiced_f0))
if len(voiced_f0) > 0:
    print(f"Mean f0: {np.mean(voiced_f0):.2f} Hz, Min: {np.min(voiced_f0):.2f} Hz, Max: {np.max(voiced_f0):.2f} Hz")
# Spectral centroid and flatness
sc = librosa.feature.spectral_centroid(y=y, sr=sr)
sf = librosa.feature.spectral_flatness(y=y)
print(f"Mean Spectral Centroid: {np.mean(sc):.2f} Hz")
print(f"Mean Spectral Flatness: {np.mean(sf):.4f}")
