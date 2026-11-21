import soundfile as sf
import numpy as np

s, sr_s = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/steve_master_take_google_studio.wav')
if s.ndim > 1: s = s.mean(axis=1)

# Let's inspect energy over time with high resolution (e.g. 10ms hop)
win = int(sr_s * 0.02)
hop = int(sr_s * 0.01)
n = (len(s) - win) // hop + 1
e = np.empty(n)
for i in range(n):
    seg = s[i*hop : i*hop+win]
    e[i] = 20.0 * np.log10(np.sqrt(np.mean(seg*seg)) + 1e-9)

times = np.arange(n) * (hop / sr_s)

# Print all significant silence regions (e < -38 dB lasting >= 0.2s)
quiet = e < -38.0
silences = []
i = 0
while i < n:
    if quiet[i]:
        j = i
        while j < n and quiet[j]:
            j += 1
        dur = (j - i) * (hop / sr_s)
        if dur >= 0.15:
            silences.append((times[i], times[j-1] + hop/sr_s, dur))
        i = j
    else:
        i += 1

print(f"Total silences found in Steve master: {len(silences)}")
for idx, (t0, t1, d) in enumerate(silences):
    print(f"  Silence {idx+1:02d}: {t0:6.3f}s - {t1:6.3f}s (gap {d:5.3f}s)")
