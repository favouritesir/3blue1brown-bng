import soundfile as sf
import numpy as np

s, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/steve_master_take_google_studio.wav')
if s.ndim > 1: s = s.mean(axis=1)

# Let's inspect energy envelope and find silence gaps >= 0.18s
win = int(sr * 0.02)
hop = int(sr * 0.005)
n = (len(s) - win) // hop + 1
e = np.empty(n)
for i in range(n):
    seg = s[i*hop : i*hop+win]
    e[i] = 20.0 * np.log10(np.sqrt(np.mean(seg*seg)) + 1e-9)

hop_s = hop / sr
thresh = -40.0
quiet = e < thresh

# find all quiet runs
gaps = []
i = 0
while i < n:
    if quiet[i]:
        j = i
        while j < n and quiet[j]:
            j += 1
        dur = (j - i) * hop_s
        if dur >= 0.18:
            gaps.append((i * hop_s, j * hop_s, dur))
        i = j
    else:
        i += 1

print(f"Total quiet gaps >= 0.18s: {len(gaps)}")
for idx, (t0, t1, d) in enumerate(gaps):
    print(f"  Gap {idx+1:02d}: {t0:6.3f}s - {t1:6.3f}s (dur {d:5.3f}s)")
