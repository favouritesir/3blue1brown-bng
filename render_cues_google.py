import json
import time
import subprocess
from pathlib import Path
from google import genai
from google.genai import types

import os
api_key = os.environ.get('GEMINI_API_KEY', '')
client = genai.Client(api_key=api_key)

BASE = Path('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses')
CUES_PATH = BASE / 'scripts' / 'master_bangla_screenplay_script.json'
OUT_VOICE_DIR = BASE / 'cues_google_voice'
OUT_VOICE_DIR.mkdir(parents=True, exist_ok=True)

with open(CUES_PATH, encoding='utf-8') as f:
    cues = json.load(f)

print(f"Total cues to render: {len(cues)}")

# Let's inspect cues
# For Steve: Voice 'Orus', For Maggie: Voice 'Fola'
# We will generate each cue, and time-stretch (atempo) to EXACT duration of Steve/Maggie mouth movement!

failed = []
for c in cues:
    cid = c['id']
    speaker = c['speaker']
    voice_name = 'Orus' if speaker == 'Steve' else 'Fola'
    text = c['google_tts_prompt']
    out_wav = OUT_VOICE_DIR / f"cue_{cid:03d}_{speaker}.wav"
    
    if out_wav.exists() and out_wav.stat().st_size > 1000:
        continue
        
    print(f"Generating Cue {cid} [{speaker} - {voice_name}]: {text[:35]}...")
    config = types.GenerateContentConfig(
        temperature=1,
        response_modalities=['audio'],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
            )
        )
    )
    try:
        res = client.models.generate_content(
            model='gemini-3.8-flash-tts',
            contents=[types.Content(role='user', parts=[types.Part.from_text(text=text)])],
            config=config
        )
        audio = b''
        for p in res.candidates[0].content.parts:
            if p.inline_data:
                audio += p.inline_data.data
        if audio:
            with open(out_wav, 'wb') as f:
                f.write(audio)
            print(f"  [OK] Cue {cid} saved ({len(audio)} bytes)")
        else:
            print(f"  [EMPTY] Cue {cid}")
            failed.append(cid)
    except Exception as e:
        print(f"  [ERROR] Cue {cid}: {e}")
        failed.append(cid)
        # If rate limit, wait 10s
        time.sleep(5)
    time.sleep(0.5)

print(f"Completed! Total generated: {len(list(OUT_VOICE_DIR.glob('*.wav')))}, Failed: {len(failed)}")
