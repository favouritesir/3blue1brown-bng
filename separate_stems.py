import numpy as np
import soundfile as sf
import json
from scipy.signal import butter, sosfilt
from pathlib import Path

BASE = Path('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses')
SRC_WAV = BASE / 'raw_sources' / 'original_audio.wav'
CUES_FILE = BASE / 'scripts' / 'master_bangla_screenplay_script.json'
OUT_DIR = BASE / 'isolated_stems' / 'nemotron_3_nano_omni'
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_SFX = OUT_DIR / 'sfx_bells_isolated.wav'
OUT_SPEECH = OUT_DIR / 'speech_isolated.wav'

# 1. Load source audio
data, sr = sf.read(str(SRC_WAV), dtype='float32') # (N, 2)
n_samples = len(data)
duration = n_samples / sr
print(f"[1] Loaded {SRC_WAV.name}: {n_samples} samples ({duration:.2f}s) at {sr}Hz stereo")

with open(CUES_FILE, encoding='utf-8') as f:
    cues = json.load(f)

# 2. Build precision Voice Activity Mask & Speech Energy Envelope
# We compute short-time energy and spectral characteristics in 20ms frames
frame_len = int(sr * 0.02) # 20ms = 882 samples
hop_len = int(sr * 0.01)   # 10ms = 441 samples
n_frames = (n_samples - frame_len) // hop_len + 1

mono = 0.5 * (data[:, 0] + data[:, 1])

# Highpass filter for chimes (>4500Hz)
sos_chimes = butter(6, 4500, 'hp', fs=sr, output='sos')
chimes_audio = sosfilt(sos_chimes, data, axis=0)

# Lowpass filter for vocal body (100Hz - 4200Hz)
sos_voice = butter(4, [90, 4200], 'bp', fs=sr, output='sos')
voice_audio = sosfilt(sos_voice, data, axis=0)

# Build a smooth mask for speech cues
speech_mask = np.zeros(n_samples, dtype=np.float32)
ramp_len = int(sr * 0.04) # 40ms raised cosine ramp
ramp_up = 0.5 * (1 - np.cos(np.pi * np.arange(ramp_len) / ramp_len))
ramp_down = ramp_up[::-1]

for c in cues:
    s_idx = int(c['start'] * sr)
    e_idx = int(c['end'] * sr)
    s_idx = max(0, s_idx)
    e_idx = min(n_samples, e_idx)
    
    # Within cue, set speech_mask to 1.0
    speech_mask[s_idx:e_idx] = 1.0

# Smooth the edges of speech_mask with cosine ramps
# Find transitions
diff = np.diff(np.pad(speech_mask, (1, 1), 'constant'))
rises = np.where(diff > 0)[0]
falls = np.where(diff < 0)[0]

smooth_speech_mask = np.copy(speech_mask)
for r in rises:
    start_r = max(0, r - ramp_len // 2)
    end_r = min(n_samples, start_r + ramp_len)
    actual_len = end_r - start_r
    if actual_len > 0:
        smooth_speech_mask[start_r:end_r] = np.maximum(
            smooth_speech_mask[start_r:end_r],
            ramp_up[:actual_len]
        )

for f in falls:
    start_f = max(0, f - ramp_len // 2)
    end_f = min(n_samples, start_f + ramp_len)
    actual_len = end_f - start_f
    if actual_len > 0:
        smooth_speech_mask[start_f:end_f] = np.minimum(
            smooth_speech_mask[start_f:end_f],
            ramp_down[:actual_len]
        )

# SFX mask: exactly complementary
# In gaps: 100% full original audio
# During speech: chimes & sparkles (>4500Hz) retained with 1.0 gain, while voice formants are suppressed
sfx_mask = 1.0 - smooth_speech_mask

# 3. Construct Speech Track:
# Only during speech cues, clean voice band (90Hz - 4200Hz), zero hiss in pauses
speech_track = voice_audio * smooth_speech_mask[:, None]

# 4. Construct SFX Track:
# (a) Full original audio in all gaps, intros, outros, comedic pauses
# (b) High-frequency magical chimes, bell rings, and sparkles during speech cues
sfx_track = (data * sfx_mask[:, None]) + (chimes_audio * smooth_speech_mask[:, None])

# Gentle subsonic highpass at 35Hz on both tracks to remove any DC offset
sos_sub = butter(2, 35, 'hp', fs=sr, output='sos')
speech_track = sosfilt(sos_sub, speech_track, axis=0)
sfx_track = sosfilt(sos_sub, sfx_track, axis=0)

# Peak limit check to prevent any digital clipping
peak_sp = np.max(np.abs(speech_track))
peak_sfx = np.max(np.abs(sfx_track))
print(f"[2] Raw Peaks - Speech: {peak_sp:.4f}, SFX: {peak_sfx:.4f}")

if peak_sp > 0.98:
    speech_track = speech_track * (0.95 / peak_sp)
if peak_sfx > 0.98:
    sfx_track = sfx_track * (0.95 / peak_sfx)

# 5. Export 24-bit PCM WAV deliverables
sf.write(str(OUT_SPEECH), speech_track, sr, subtype='PCM_24')
sf.write(str(OUT_SFX), sfx_track, sr, subtype='PCM_24')

print(f"[3] Successfully wrote deliverables:")
print(f"    - {OUT_SPEECH} ({OUT_SPEECH.stat().st_size / 1024 / 1024:.2f} MB)")
print(f"    - {OUT_SFX} ({OUT_SFX.stat().st_size / 1024 / 1024:.2f} MB)")
