import soundfile as sf
import os
import numpy as np

s, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/steve_master_take_google_studio.wav')

os.makedirs('temp_steve_inspect', exist_ok=True)

# Let's save each segment bounded by the gaps
gaps = [
    (0.800, 1.080),   # 1
    (2.085, 2.315),   # 2
    (2.780, 3.565),   # 3
    (5.940, 6.375),   # 4
    (8.750, 9.110),   # 5
    (10.380, 10.925), # 6
    (11.825, 12.080), # 8
    (12.390, 15.245), # 9
    (16.875, 17.255), # 11
    (17.740, 18.185), # 12
]

# Let's write out chunks
chunks = [
    (0.0, 0.800),
    (1.080, 2.085),
    (2.315, 2.780),
    (3.565, 5.940),
    (6.375, 8.750),
    (9.110, 10.380),
    (10.925, 11.825),
    (12.080, 12.390),
    (15.245, 16.875),
    (17.255, 17.740),
]

for idx, (t0, t1) in enumerate(chunks):
    c = s[int(t0*sr):int(t1*sr)]
    p = f"temp_steve_inspect/chk_{idx+1:02d}.wav"
    sf.write(p, c, sr)
    print(f"Chunk {idx+1:02d} [{t0:6.3f}s - {t1:6.3f}s] dur={t1-t0:5.3f}s rms={np.sqrt(np.mean(c**2)):.4f}")
