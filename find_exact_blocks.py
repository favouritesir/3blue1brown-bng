import soundfile as sf
import numpy as np

def find_speech_blocks(path, thresh_db=-40, min_sil_s=0.2):
    x, sr = sf.read(path)
    if x.ndim > 1:
        x = x.mean(axis=1)
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
            blocks.append((i*hop_s, j*hop_s))
            i = j
        else:
            i += 1
            
    merged = []
    for s, end in blocks:
        if not merged:
            merged.append([s, end])
        else:
            if s - merged[-1][1] < min_sil_s:
                merged[-1][1] = end
            else:
                merged.append([s, end])
    return merged, len(x)/sr

s_blocks, s_dur = find_speech_blocks('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/steve_master_take_google_studio.wav', -38, 0.25)
print(f"Steve: {len(s_blocks)} blocks in {s_dur:.2f}s")
for i, (s, e) in enumerate(s_blocks):
    print(f"  [{i+1:02d}] {s:6.3f}s - {e:6.3f}s (dur {e-s:5.3f}s)")

m_blocks, m_dur = find_speech_blocks('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/maggie_master_take_google_studio.wav', -38, 0.25)
print(f"\nMaggie: {len(m_blocks)} blocks in {m_dur:.2f}s")
for i, (s, e) in enumerate(m_blocks):
    print(f"  [{i+1:02d}] {s:6.3f}s - {e:6.3f}s (dur {e-s:5.3f}s)")
