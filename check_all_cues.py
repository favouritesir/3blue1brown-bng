import os
import soundfile as sf
import numpy as np

cues_dir = 'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_cues_v2'
cues = sorted([f for f in os.listdir(cues_dir) if f.startswith('fitted_cue_') and f.endswith('.wav')])

for c in cues:
    p = os.path.join(cues_dir, c)
    data, sr = sf.read(p)
    rms = np.sqrt(np.mean(data**2))
    peak = np.max(np.abs(data))
    status = "OK" if rms > 0.03 else "SILENT/LOW!!!"
    print(f"{c:26s} dur={len(data)/sr:5.3f}s rms={rms:7.4f} peak={peak:7.4f} [{status}]")
