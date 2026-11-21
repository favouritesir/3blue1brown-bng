import json
import os
import soundfile as sf
import numpy as np

cues_dir = 'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/sliced_cues'
files = sorted(os.listdir(cues_dir))
print(f"Total sliced cues: {len(files)}")
for f in files:
    p = os.path.join(cues_dir, f)
    d, sr = sf.read(p)
    rms = np.sqrt(np.mean(d**2))
    peak = np.max(np.abs(d))
    print(f"{f:25s} dur={len(d)/sr:5.3f}s rms={rms:7.4f} peak={peak:7.4f}")
