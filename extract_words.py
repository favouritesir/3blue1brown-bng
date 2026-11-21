import json
from pathlib import Path

# Load json3 events and cues
with open('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/WL8qVKfw0Dk.en.json3', 'r', encoding='utf-8') as f:
    json3_data = json.load(f)

# Collect speech intervals from json3
speech_intervals = []
for ev in json3_data.get('events', []):
    tStart = ev.get('tStartMs', 0) / 1000.0
    dDuration = ev.get('dDurationMs', 0) / 1000.0
    segs = ev.get('segs', [])
    text = "".join([s.get('utf8', '') for s in segs]).strip()
    if text and text != '\n':
        # Let's inspect words inside
        t_cur = tStart
        for s in segs:
            w_text = s.get('utf8', '').strip()
            w_off = s.get('tOffsetMs', 0) / 1000.0
            if w_text:
                w_start = tStart + w_off
                speech_intervals.append((w_start, w_text))

print(f"Total word segments extracted: {len(speech_intervals)}")
for w in speech_intervals[:20]:
    print(f"{w[0]:6.2f}s : {w[1]}")
