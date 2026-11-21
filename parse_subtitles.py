import json

with open('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/WL8qVKfw0Dk.en.json3', encoding='utf-8') as f:
    j3 = json.load(f)

events = j3.get('events', [])
for ev in events:
    if 'segs' in ev:
        text = ''.join([s.get('utf8', '') for s in ev['segs']]).strip()
        t_start = ev.get('tStartMs', 0) / 1000.0
        dur = ev.get('dDurationMs', 0) / 1000.0
        if text:
            print(f"[{t_start:6.2f}s - {t_start+dur:6.2f}s | dur {dur:4.2f}s] {text}")
