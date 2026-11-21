import soundfile as sf
import numpy as np
import scipy.signal

audio, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/original_audio.wav')
mono = np.mean(audio, axis=1)

# Check energy in high frequency bands (bell / chime range: 2500 - 12000 Hz)
sos_high = scipy.signal.butter(4, [2500, 12000], btype='bandpass', fs=sr, output='sos')
high_band = scipy.signal.sosfilt(sos_high, mono)

# Calculate RMS in 100ms windows
window = int(0.1 * sr)
step = int(0.05 * sr)
times = []
rms_high = []
rms_full = []
for i in range(0, len(mono) - window, step):
    t = i / sr
    w_h = high_band[i:i+window]
    w_f = mono[i:i+window]
    times.append(t)
    rms_high.append(np.sqrt(np.mean(w_h**2)))
    rms_full.append(np.sqrt(np.mean(w_f**2)))

times = np.array(times)
rms_high = np.array(rms_high)
rms_full = np.array(rms_full)

# Find moments where high_band RMS is very high (chimes/bells/sizzles)
peaks, props = scipy.signal.find_peaks(rms_high, height=0.015, distance=int(1.0/0.05))
print(f"Detected {len(peaks)} prominent high-frequency/chime/sfx events:")
for p in peaks:
    t = times[p]
    print(f"t = {t:6.2f}s | high_rms = {rms_high[p]:.4f} | full_rms = {rms_full[p]:.4f}")
