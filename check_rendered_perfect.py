import os
import soundfile as sf
import numpy as np

p = 'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/cues_rendered_perfect'
files = sorted([f for f in os.listdir(p) if f.startswith('raw_cue_')])

print(f"Total raw cue files in cues_rendered_perfect: {len(files)}")
for f in files[:15]:
    fp = os.path.join(p, f)
    d, sr = sf.read(fp)
    rms = np.sqrt(np.mean(d**2))
    peak = np.max(np.abs(d))
    print(f"  {f:25s} dur={len(d)/sr:5.3f}s sr={sr} rms={rms:.4f} peak={peak:.4f}")
