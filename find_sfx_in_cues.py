import json

BASE = 'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses'
with open(f'{BASE}/scripts/master_bangla_screenplay_script.json', encoding='utf-8') as f:
    cues = json.load(f)

for c in cues:
    txt = c['en']
    notes = c.get('acting_notes', '')
    if any(k in txt.lower() or k in notes.lower() for k in ['bell', 'scream', 'snort', 'sigh', 'gasp', 'laugh', 'chili', 'sniff', 'magic']):
        print(f"Cue {c['id']:02d} [{c['start']:6.2f} - {c['end']:6.2f}]: {txt} | Notes: {notes}")
