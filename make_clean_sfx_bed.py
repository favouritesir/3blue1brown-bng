import json
import subprocess
from pathlib import Path

BASE = Path('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses')
ORIG = BASE / 'raw_sources' / 'original_audio.wav'
OUT = BASE / 'clean_sfx_bed.wav'

with open(BASE / 'scripts' / 'master_bangla_screenplay_script.json', encoding='utf-8') as f:
    cues = json.load(f)

# Build volume expression:
# If t is inside any cue [start, end], volume = 0 (100% MUTED - English voice totally removed!)
# If t is outside cues (SFX, magic chimes, bell sounds, comedy music pauses), volume = 1.0!
conditions = []
for c in cues:
    # slight 0.1s margin
    s = max(0, c['start'] - 0.05)
    e = c['end'] + 0.05
    conditions.append(f"between(t,{s:.2f},{e:.2f})")

expr = "+".join(conditions)
# volume='if(expr, 0.0, 1.0)'
vol_filter = f"volume='if({expr}, 0.0, 1.0)':eval=frame"

print("Generating clean SFX & Music pauses bed...")
cmd = [
    'ffmpeg', '-y', '-i', str(ORIG),
    '-af', vol_filter,
    '-c:a', 'pcm_s16le', str(OUT)
]
subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("Clean SFX bed generated:", OUT.exists(), OUT.stat().st_size)
