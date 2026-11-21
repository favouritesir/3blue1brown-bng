import json
import soundfile as sf
import numpy as np

with open('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/scripts/egm_master_screenplay_v2.json', encoding='utf-8') as f:
    sp = json.load(f)

steve_cues = [c for c in sp['cues'] if c['speaker'] == 'Steve']
maggie_cues = [c for c in sp['cues'] if c['speaker'] == 'Maggie']

print(f"Total Steve cues: {len(steve_cues)}")
for idx, c in enumerate(steve_cues):
    prompt = c.get('google_tts_prompt') or c['bn']
    print(f"  Cue {c['id']:02d}: {prompt}")

print(f"\nTotal Maggie cues: {len(maggie_cues)}")
for idx, c in enumerate(maggie_cues):
    prompt = c.get('google_tts_prompt') or c['bn']
    print(f"  Cue {c['id']:02d}: {prompt}")
