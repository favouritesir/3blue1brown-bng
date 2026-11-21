import soundfile as sf
import numpy as np

def analyze_audio(path):
    x, sr = sf.read(path)
    if x.ndim > 1:
        x = x.mean(axis=1)
    dur = len(x) / sr
    win_ms = 20
    hop_ms = 5
    win = int(sr * win_ms / 1000)
    hop = int(sr * hop_ms / 1000)
    n = (len(x) - win) // hop + 1
    e = np.empty(n)
    for i in range(n):
        seg = x[i*hop : i*hop + win]
        e[i] = 20.0 * np.log10(np.sqrt(np.mean(seg*seg)) + 1e-9)
    hop_s = hop / sr
    thresh = -40.0
    quiet = e < thresh
    
    # find speech segments
    speech_segs = []
    i = 0
    while i < n:
        if not quiet[i]:
            j = i
            while j < n and not quiet[j]:
                j += 1
            speech_segs.append((i * hop_s, j * hop_s))
            i = j
        else:
            i += 1
            
    # merge speech segments that have gap < 0.25s
    merged = []
    for s, end in speech_segs:
        if not merged:
            merged.append([s, end])
        else:
            if s - merged[-1][1] < 0.25:
                merged[-1][1] = end
            else:
                merged.append([s, end])
    print(f"File {path}: total dur={dur:.2f}s, found {len(merged)} utterance blocks")
    for idx, (s, end) in enumerate(merged):
        print(f"  [{idx+1:02d}] {s:6.3f}s - {end:6.3f}s (dur {end-s:5.3f}s)")
    return merged

print("--- Steve Master Take ---")
s_segs = analyze_audio('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/steve_master_take_google_studio.wav')
print("\n--- Maggie Master Take ---")
m_segs = analyze_audio('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/maggie_master_take_google_studio.wav')
