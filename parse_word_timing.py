import json

with open('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/WL8qVKfw0Dk.en.json3', encoding='utf-8') as f:
    d = json.load(f)

events = d.get('events', [])
for ev in events:
    if 'segs' in ev:
        t0 = ev.get('tStartMs', 0) / 1000.0
        dur = ev.get('dDurationMs', 0) / 1000.0
        segs = ev['segs']
        words = []
        for s in segs:
            w_text = s.get('utf8', '').replace('\n', ' ').strip()
            w_off = s.get('tOffsetMs', 0) / 1000.0
            if w_text:
                words.append((f"{t0 + w_off:.2f}s", w_text))
        if words:
            print(f"[{t0:6.2f}s - {t0+dur:6.2f}s]: {' '.join([f'{w}({t})' for t, w in words])}")
