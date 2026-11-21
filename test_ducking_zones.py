import json
import subprocess
from pathlib import Path

BASE = Path('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses')
ORIG = BASE / 'raw_sources' / 'original_audio.wav'
OUT = BASE / 'clean_sfx_bed.wav'

with open(BASE / 'scripts' / 'master_bangla_screenplay_script.json', encoding='utf-8') as f:
    cues = json.load(f)

# Build volume expression or adelay/volume filter
# Between speech cues: Volume = 1.0 (Full SFX, chimes, pops, music)
# During speech cues: Volume = 0.05 or 0.0 (Completely muted or minimal music so English vocals are inaudible!)
# Let's inspect intervals!
print(f"Total cues: {len(cues)}")
print("First cue:", cues[0]['start'], cues[0]['end'])
print("Last cue:", cues[-1]['start'], cues[-1]['end'])
