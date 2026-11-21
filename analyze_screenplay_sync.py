import json
import soundfile as sf
import numpy as np

# Load original audio
orig, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/original_audio.wav')
if orig.ndim > 1:
    orig = orig.mean(axis=1)

with open('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/WL8qVKfw0Dk.en.json3', encoding='utf-8') as f:
    j3 = json.load(f)

# Extract word segments from json3
speech_events = []
for ev in j3.get('events', []):
    if 'segs' in ev:
        t0 = ev.get('tStartMs', 0) / 1000.0
        dur = ev.get('dDurationMs', 0) / 1000.0
        text = ''.join([s.get('utf8', '') for s in ev['segs']]).strip().replace('\n', ' ')
        if text:
            # find first word offset and last word end
            first_w_off = ev['segs'][0].get('tOffsetMs', 0) / 1000.0
            last_w_off = ev['segs'][-1].get('tOffsetMs', 0) / 1000.0
            speech_events.append({
                'start': t0,
                'end': t0 + dur,
                'text': text,
                'first_word_t': t0 + first_w_off,
            })

with open('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/scripts/egm_master_screenplay_v2.json', encoding='utf-8') as f:
    sp = json.load(f)

cues = sp['cues']

print(f"Total Cues: {len(cues)}")
print(f"{'ID':3s} {'Speaker':7s} {'Screenplay Start-End':22s} {'Cue BN Text':40s}")
print("-" * 80)
for c in cues:
    print(f"{c['id']:02d}  {c['speaker']:7s} {c['start']:6.2f}s - {c['end']:6.2f}s ({c['duration']:4.2f}s)  {c['bn']}")
