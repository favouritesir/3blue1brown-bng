import librosa
import numpy as np
import soundfile as sf

# Load full original audio
audio, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/original_audio.wav')
mono = np.mean(audio, axis=1)

# A school bell (like an electric school bell ring) or musical chime has very distinct frequencies:
# e.g., ringing bell is around 1 kHz - 4 kHz with rapid modulation or continuous ringing harmonics.
# Let's inspect intervals between dialogue where Steve stops speaking:
import json
with open('word_level_vocal_timeline.json', 'r') as f:
    words = json.load(f)

# Find silence / non-speech gaps longer than 0.4s
gaps = []
for i in range(len(words)-1):
    gap_start = words[i]['end']
    gap_end = words[i+1]['start']
    if gap_end - gap_start > 0.4:
        gaps.append((gap_start, gap_end))

print(f"Total non-speech gaps > 0.4s: {len(gaps)}")
gap_peaks = []
for s, e in gaps:
    chunk = mono[int(s*sr):int(e*sr)]
    if len(chunk) > 0:
        rms = np.sqrt(np.mean(chunk**2))
        max_a = np.max(np.abs(chunk))
        if max_a > 0.05:
            gap_peaks.append((s, e, rms, max_a))

gap_peaks.sort(key=lambda x: x[3], reverse=True)
print("Top 20 loudest sounds during non-speech gaps:")
for s, e, rms, max_a in gap_peaks[:20]:
    print(f"[{s:6.2f} - {e:6.2f}] duration: {e-s:4.2f}s | max: {max_a:.4f} | RMS: {rms:.4f}")
