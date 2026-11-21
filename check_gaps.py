import soundfile as sf
import numpy as np

def find_gaps(path, thresh_db=-35, min_gap_s=0.3):
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
    is_silence = e < thresh_db
    gaps = []
    i = 0
    while i < n:
        if is_silence[i]:
            j = i
            while j < n and is_silence[j]:
                j += 1
            if (j - i) * hop_s >= min_gap_s:
                gaps.append((i*hop_s, j*hop_s))
            i = j
        else:
            i += 1
    print(f"Path: {path} (total {len(x)/sr:.2f}s): found {len(gaps)} silence gaps >= {min_gap_s}s (thresh {thresh_db}dB) -> {len(gaps)+1} segments")
    return gaps

print("Checking mistral_google_studio_masters:")
find_gaps('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/mistral_google_studio_masters/steve_master_take_mistral_google.wav', -35, 0.4)
find_gaps('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/mistral_google_studio_masters/maggie_master_take_mistral_google.wav', -35, 0.4)

print("\nChecking google_studio_masters:")
find_gaps('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/steve_master_take_google_studio.wav', -35, 0.3)
find_gaps('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/maggie_master_take_google_studio.wav', -35, 0.3)
