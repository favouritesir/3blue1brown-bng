import soundfile as sf
import numpy as np

x, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/steve_master_take_google_studio.wav')
if x.ndim > 1:
    x = x.mean(axis=1)

def find_candidate_segments(x, sr, thresh_db=-42, min_gap_s=0.15):
    win = int(sr * 0.02)
    hop = int(sr * 0.005)
    n = (len(x) - win) // hop + 1
    e = np.empty(n)
    for i in range(n):
        seg = x[i*hop : i*hop+win]
        e[i] = 20.0 * np.log10(np.sqrt(np.mean(seg*seg)) + 1e-9)
    hop_s = hop / sr
    is_speech = e >= thresh_db
    
    blocks = []
    i = 0
    while i < n:
        if is_speech[i]:
            j = i
            while j < n and is_speech[j]:
                j += 1
            blocks.append([i*hop_s, j*hop_s])
            i = j
        else:
            i += 1
            
    # merge blocks if silence gap is smaller than min_gap_s
    merged = []
    for b in blocks:
        if not merged:
            merged.append(b)
        else:
            gap = b[0] - merged[-1][1]
            if gap < min_gap_s:
                merged[-1][1] = b[1]
            else:
                merged.append(b)
    return merged

segs = find_candidate_segments(x, sr, thresh_db=-42, min_gap_s=0.18)
print(f"Total speech blocks in Steve master: {len(segs)}")
for i, (s, e) in enumerate(segs):
    dur = e - s
    seg_samples = x[int(s*sr):int(e*sr)]
    rms = np.sqrt(np.mean(seg_samples**2))
    print(f"[{i+1:02d}] {s:6.3f}s - {e:6.3f}s | dur {dur:5.3f}s | rms {rms:6.4f}")
