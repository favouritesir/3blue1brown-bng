import json

with open('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/WL8qVKfw0Dk.en.json3', 'r', encoding='utf-8') as f:
    data = json.load(f)

events = data.get('events', [])
print(f"Total events in json3: {len(events)}")
for ev in events[:15]:
    tStart = ev.get('tStartMs', 0) / 1000.0
    dDuration = ev.get('dDurationMs', 0) / 1000.0
    segs = ev.get('segs', [])
    text = "".join([s.get('utf8', '') for s in segs])
    print(f"[{tStart:6.2f} - {tStart+dDuration:6.2f}] : {repr(text)}")
