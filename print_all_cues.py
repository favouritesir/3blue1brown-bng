import json
from pathlib import Path

BASE = Path('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses')
with open(BASE / 'scripts' / 'master_bangla_screenplay_script.json', encoding='utf-8') as f:
    cues = json.load(f)

for c in cues:
    print(f"ID {c['id']:02d}: {c['start']:6.2f} - {c['end']:6.2f} [{c['speaker']:6s}] EN: {c['en']}")
