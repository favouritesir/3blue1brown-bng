import soundfile as sf
import numpy as np
import librosa
import json

audio, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/original_audio.wav')
mono = np.mean(audio, axis=1)

# Let's check the screenplay script to see what actions / reactions / SFX are noted
with open('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/scripts/master_bangla_screenplay_script.json', 'r', encoding='utf-8') as f:
    cues = json.load(f)

for c in cues:
    acting = c.get('acting_notes', '')
    en = c.get('en', '')
    if any(k in en.lower() or k in acting.lower() for k in ['scream', 'laugh', 'gasp', 'pencil', 'snort', 'sniff', 'taste', 'bell', 'chime', 'ruler', 'magic']):
        print(f"[{c['start']:6.2f} - {c['end']:6.2f}] {c['speaker']}: {en} | notes: {acting}")
