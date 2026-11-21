import soundfile as sf
import numpy as np
import json
from scipy.signal import butter, sosfilt

BASE = 'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses'
SRC_WAV = f'{BASE}/raw_sources/original_audio.wav'
cues_file = f'{BASE}/scripts/master_bangla_screenplay_script.json'

data, sr = sf.read(SRC_WAV)
mono = (data[:, 0] + data[:, 1]) / 2.0
side = (data[:, 0] - data[:, 1]) / 2.0

with open(cues_file, encoding='utf-8') as f:
    cues = json.load(f)

# Highpass filter at 4kHz to detect magic chimes/sparkles
sos_hf = butter(4, 4000, 'hp', fs=sr, output='sos')
hf_audio = sosfilt(sos_hf, mono)

# Check side energy (stereo SFX/chimes)
# Check RMS in 100ms windows across entire audio
win = int(sr * 0.1)
n_win = len(mono) // win

events = []
for i in range(n_win):
    t = i * 0.1
    c_mono = mono[i*win:(i+1)*win]
    c_hf = hf_audio[i*win:(i+1)*win]
    c_side = side[i*win:(i+1)*win]
    
    rms_mono = np.sqrt(np.mean(c_mono**2))
    rms_hf = np.sqrt(np.mean(c_hf**2))
    rms_side = np.sqrt(np.mean(c_side**2))
    
    # Check if inside any cue
    inside_cue = [c for c in cues if c['start'] <= t <= c['end']]
    cue_info = f"Cue {inside_cue[0]['id']} ({inside_cue[0]['speaker']})" if inside_cue else "GAP / PAUSE"
    
    # If high frequency or side energy is significant
    if rms_hf > 0.02 or rms_side > 0.01:
        events.append((t, rms_mono, rms_hf, rms_side, cue_info))

print(f"Total time: {len(mono)/sr:.2f}s")
print(f"Detected {len(events)} SFX/Chime active windows (100ms)")
print("\nSample detected events:")
for ev in events[:30]:
    print(f"t={ev[0]:5.1f}s | Mono RMS={ev[1]:6.3f} | HF RMS={ev[2]:6.3f} | Side RMS={ev[3]:6.3f} | {ev[4]}")
