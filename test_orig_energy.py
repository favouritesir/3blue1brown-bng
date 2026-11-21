import soundfile as sf
import numpy as np

# Load original audio
orig, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/original_audio.wav')
if orig.ndim > 1:
    orig = orig.mean(axis=1)

print(f"Original audio: {len(orig)/sr:.2f}s, sr={sr}")

# Let's check energy around Cue 1 (2.0s to 7.0s)
def get_energy_profile(t_start, t_end, res_ms=20):
    i0 = int(t_start * sr)
    i1 = int(t_end * sr)
    seg = orig[i0:i1]
    hop = int(sr * res_ms / 1000)
    n = len(seg) // hop
    profile = []
    for k in range(n):
        chunk = seg[k*hop : (k+1)*hop]
        rms = np.sqrt(np.mean(chunk**2))
        t = t_start + k * (res_ms / 1000)
        profile.append((t, rms))
    return profile

prof = get_energy_profile(2.0, 14.0, 50)
print("Time, RMS (every 100ms from 2.0s to 14.0s):")
for t, r in prof[::2]:
    bar = "#" * int(min(r * 200, 50))
    print(f"{t:5.2f}s: {r:6.4f} | {bar}")
