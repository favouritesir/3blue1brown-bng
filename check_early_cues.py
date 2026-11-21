import soundfile as sf
import numpy as np

for i in [1, 2, 3, 4, 5, 6, 7]:
    p = f'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_cues_v2/fitted_cue_{i:03d}_Steve.wav'
    d, sr = sf.read(p)
    print(f"Cue {i:02d}: dur={len(d)/sr:.3f}s rms={np.sqrt(np.mean(d**2)):.4f} peak={np.max(np.abs(d)):.4f}")
