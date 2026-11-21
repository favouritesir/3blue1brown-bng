import soundfile as sf
import numpy as np
import scipy.signal

vocals, sr = sf.read('demucs_test/htdemucs/test_intro_0_15/vocals.wav')
f, t, Zxx = scipy.signal.stft(vocals[:int(2.2*sr), 0], fs=sr, nperseg=2048)
mag = np.abs(Zxx)
print("0-2.2s vocals STFT max mag:", np.max(mag))
# Top frequencies in 0-2.2s
mean_freq = np.mean(mag, axis=1)
top_bins = np.argsort(mean_freq)[-10:]
print("Top freq bins (Hz):", f[top_bins])
