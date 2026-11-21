import os
import soundfile as sf
import numpy as np

cues_dir = 'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_cues_v2'
cues = sorted([f for f in os.listdir(cues_dir) if f.startswith('fitted_cue_') and f.endswith('.wav')])

print(f"Total fitted cue files: {len(cues)}")
for c in cues[:12]:
    p = os.path.join(cues_dir, c)
    data, sr = sf.read(p)
    rms = np.sqrt(np.mean(data**2))
    peak = np.max(np.abs(data))
    print(f"{c:26s} dur={len(data)/sr:5.3f}s rms={rms:.4f} peak={peak:.4f}")
