import numpy as np
import soundfile as sf
from scipy.signal import spectrogram
import json

BASE = 'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses'
SRC_WAV = f'{BASE}/raw_sources/original_audio.wav'

data, sr = sf.read(SRC_WAV)
print(f"Loaded {SRC_WAV}, shape: {data.shape}, sr: {sr}")

# Check intro (0.0 - 2.2s)
intro = data[:int(sr*2.2)]
# FFT of intro
fft_intro = np.abs(np.fft.rfft(intro[:, 0]))
freqs = np.fft.rfftfreq(len(intro[:, 0]), 1/sr)

# Top 5 frequencies of intro chime
top_idx = np.argsort(fft_intro)[-10:][::-1]
print("Intro chime top frequencies (Hz):", [int(freqs[i]) for i in top_idx])

# Check a speech segment: 3.0s to 5.0s
speech = data[int(sr*3.0):int(sr*5.0)]
fft_speech = np.abs(np.fft.rfft(speech[:, 0]))
freqs_sp = np.fft.rfftfreq(len(speech[:, 0]), 1/sr)
top_sp_idx = np.argsort(fft_speech)[-10:][::-1]
print("Speech top frequencies (Hz):", [int(freqs_sp[i]) for i in top_sp_idx])
