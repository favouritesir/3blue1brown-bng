import soundfile as sf
import numpy as np
import json
from scipy.signal import butter, sosfilt

BASE = 'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses'
SRC_WAV = f'{BASE}/raw_sources/original_audio.wav'
CUES_FILE = f'{BASE}/scripts/master_bangla_screenplay_script.json'

data, sr = sf.read(SRC_WAV)
with open(CUES_FILE, encoding='utf-8') as f:
    cues = json.load(f)

print(f"Loaded {SRC_WAV}: sr={sr}, shape={data.shape}")

# Let's inspect Cue 1 (2.2s to 6.3s) and the surrounding audio
# Let's see the exact speech energy inside Cue 1
c1 = cues[0]
s1 = int(c1['start'] * sr)
e1 = int(c1['end'] * sr)
cue1_audio = data[s1:e1]

# Design filters:
# 1. High frequency sparkle / chime filter (>4200 Hz)
sos_sparkle = butter(4, 4200, 'hp', fs=sr, output='sos')
sparkle_cue1 = sosfilt(sos_sparkle, cue1_audio, axis=0)

# 2. Voice band filter (120 Hz to 3800 Hz)
sos_voice = butter(4, [120, 3800], 'bp', fs=sr, output='sos')
voice_cue1 = sosfilt(sos_voice, cue1_audio, axis=0)

print("Cue 1 Original RMS:", np.sqrt(np.mean(cue1_audio**2)))
print("Cue 1 Sparkle (>4.2kHz) RMS:", np.sqrt(np.mean(sparkle_cue1**2)))
print("Cue 1 Voice (120-3800Hz) RMS:", np.sqrt(np.mean(voice_cue1**2)))
