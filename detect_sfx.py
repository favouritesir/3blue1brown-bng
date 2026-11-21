import soundfile as sf
import numpy as np
import librosa

orig, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/original_audio.wav')
mono = np.mean(orig, axis=1)

# Detect onsets
onset_env = librosa.onset.onset_strength(y=mono, sr=sr)
onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, units='time')

print(f"Total onsets detected: {len(onsets)}")
# Let's inspect spectral centroid at onsets
# School bells and chimes have high frequency resonance (> 2000Hz up to 8000Hz) and long decay/sustain
spec_cent = librosa.feature.spectral_centroid(y=mono, sr=sr)[0]
spec_flat = librosa.feature.spectral_flatness(y=mono)[0]
frames_time = librosa.frames_to_time(np.arange(len(spec_cent)), sr=sr)

print("Onset samples (first 25):")
for t in onsets[:25]:
    idx = int(t * sr / 512)
    if idx < len(spec_cent):
        print(f"Time: {t:6.2f}s | Centroid: {spec_cent[idx]:7.1f} Hz | Flatness: {spec_flat[idx]:.4f}")
