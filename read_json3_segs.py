import json

with open('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/WL8qVKfw0Dk.en.json3', 'r', encoding='utf-8') as f:
    data = json.load(f)

for ev in data.get('events', [])[1:5]:
    tStart = ev.get('tStartMs', 0)
    print("EVENT:", ev.get('tStartMs'), ev.get('dDurationMs'))
    for s in ev.get('segs', []):
        print("   SEG:", s)
