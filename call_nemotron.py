import urllib.request
import json

nv_api_key = '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'
nv_url = 'https://integrate.api.nvidia.com/v1/chat/completions'

system_prompt = (
    "You are nvidia/nemotron-3-nano-omni-30b-a3b-reasoning (Nemotron 3 Nano Omni), an elite multimodal and audio engineering AI agent. "
    "You are executing a specialized subagent audio separation task on 'Steve and Maggie | Learn the Senses' (3m33s, 44.1kHz stereo, kids educational cartoon)."
)

user_task = """TASK:
Separate the audio of "Steve and Maggie | Learn the Senses" into:
1. Pure cartoon sound effects (bell rings, magical chimes, comic boings, pops, sniffs, sizzles) WITHOUT ANY hissing, buzz, or robotic distortion.
2. Dialogue/speech track.

SOURCE AUDIO:
departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/original_audio.wav

TARGET OUTPUT DIRECTORY:
departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/isolated_stems/nemotron_3_nano_omni/

Deliverables:
- sfx_bells_isolated.wav
- speech_isolated.wav
- A brief audit report on clarity and zero-hiss quality.

CONTEXT & CONSTRAINTS:
In this video, Steve and Maggie speak with clear dialogue cues (we have the exact timestamps for all 48 dialogue cues in master_bangla_screenplay_script.json).
Cartoon SFX includes:
- Intro / magic chimes, school bells, comic boings, funny sniffing sounds, sizzling chilli, cheering and cartoon sound transitions.
- Naive vocal cancellation (e.g. naive L-R side channel extraction) leaves center-residual hiss and phase distortion.
- Naive threshold gating or spectral subtraction creates robotic musical noise / flanging.

Provide your architectural blueprint, exact DSP algorithm, and Python / FFmpeg implementation script to generate these exact deliverables cleanly with zero hiss."""

payload = {
    "model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_task}
    ],
    "temperature": 0.2,
    "max_tokens": 3000
}

req = urllib.request.Request(
    nv_url,
    data=json.dumps(payload).encode('utf-8'),
    headers={'Authorization': f'Bearer {nv_api_key}', 'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        choice = res['choices'][0]['message']
        content = choice.get('content') or choice.get('reasoning_content') or ""
        print(f"Received {len(content)} characters from Nemotron 3 Nano Omni")
        with open("nemotron_nano_omni_execution_plan.md", "w", encoding="utf-8") as f:
            f.write(content)
        print("Saved to nemotron_nano_omni_execution_plan.md")
except Exception as e:
    print(f"Error calling Nemotron: {e}")
