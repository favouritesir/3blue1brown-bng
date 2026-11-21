import soundfile as sf
import os
import numpy as np

m, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/maggie_master_take_google_studio.wav')
os.makedirs('temp_maggie_chunks', exist_ok=True)

# Gaps:
# 0.0 to 1.335s
# 2.0 to 2.68s
# 2.97 to 4.89s
# 5.295 to 5.9s
# 6.22 to 7.01s
# 7.37 to 7.82s
# 8.29 to 8.61s
# 9.83 to 10.915s
# 11.33 to 12.005s
# 12.55 to 13.855s
# 14.255 to 14.665s
# 15.49 to 16.055s
# 17.38 to 18.31s
# 18.65 to 23.005s

segs = [
    (0.0, 1.335),
    (2.0, 2.68),
    (2.97, 4.89),
    (5.295, 5.9),
    (6.22, 7.01),
    (7.37, 7.82),
    (8.29, 8.61),
    (9.83, 10.915),
    (11.33, 12.005),
    (12.55, 13.855),
    (14.255, 14.665),
    (15.49, 16.055),
    (17.38, 18.31),
    (18.65, 23.005)
]

for idx, (s, e) in enumerate(segs):
    chunk = m[int(s*sr):int(e*sr)]
    rms = np.sqrt(np.mean(chunk**2))
    p = f"temp_maggie_chunks/seg_{idx+1:02d}.wav"
    sf.write(p, chunk, sr)
    print(f"Seg {idx+1:02d} [{s:6.3f}s - {e:6.3f}s]: dur={e-s:5.3f}s rms={rms:.4f} -> {p}")
