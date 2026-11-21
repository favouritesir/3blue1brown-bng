import os
import json
import soundfile as sf
import numpy as np

p = 'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/cues_rendered_perfect/processed_cues_manifest.json'
with open(p) as f:
    manifest = json.load(f)

print(f"Manifest has {len(manifest)} items:")
for m in manifest:
    fpath = m['file']
    data, sr = sf.read(fpath)
    rms = np.sqrt(np.mean(data**2))
    peak = np.max(np.abs(data))
    print(f"Cue {m['id']:02d} [{m['speaker']}] {m['start']:5.2f}s - {m['end']:5.2f}s ({m['duration']:4.2f}s) -> file dur={m['actual_dur']:4.2f}s rms={rms:.4f} peak={peak:.4f}")
