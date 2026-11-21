import soundfile as sf
import numpy as np

# Load Maggie master take
m, sr_m = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/maggie_master_take_google_studio.wav')
if m.ndim > 1:
    m = m.mean(axis=1)

print(f"Maggie master: {len(m)/sr_m:.3f}s, sr={sr_m}")

# Maggie has 8 cues:
# Cue 12: স্কেলটা খুঁজে বের করো! হিহিহি, খোঁজো খোঁজো!
# Cue 13: স্কেলটা!
# Cue 15: খোঁজো খোঁজো! জলদি খোঁজো!
# Cue 17: হিহিহিহি! স্কেল! হ্যাঁ! রুলার! রুলার! রুলার! দেখো!
# Cue 24: হিহিহি! একটা বই!
# Cue 40: ঠিক আছে স্টিভ! হিহিহি!
# Cue 41: আমি স্বাদ নিচ্ছি! টেস্ট! রসালো আপেল!
# Cue 43: হ্যাঁ! হিহিহি, এবার স্বাদের পালা!

# Let's inspect energy envelope of Maggie master
win = int(sr_m * 0.02)
hop = int(sr_m * 0.005)
n = (len(m) - win) // hop + 1
e = np.empty(n)
for i in range(n):
    seg = m[i*hop : i*hop+win]
    e[i] = 20.0 * np.log10(np.sqrt(np.mean(seg*seg)) + 1e-9)
hop_s = hop / sr_m

# Find silence gaps > 0.3s
thresh = -40.0
quiet = e < thresh
gaps = []
i = 0
while i < n:
    if quiet[i]:
        j = i
        while j < n and quiet[j]:
            j += 1
        if (j - i) * hop_s >= 0.25:
            gaps.append((i*hop_s, j*hop_s))
        i = j
    else:
        i += 1

print(f"Maggie gaps >= 0.25s: {len(gaps)}")
for g in gaps:
    print(f"  gap: {g[0]:6.3f}s - {g[1]:6.3f}s (dur {g[1]-g[0]:5.3f}s)")
