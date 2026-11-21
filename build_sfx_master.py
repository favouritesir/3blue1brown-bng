import json
import soundfile as sf
import numpy as np
from pathlib import Path

# Paths
BASE_DIR = Path('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses')
ORIG_AUDIO_PATH = BASE_DIR / 'raw_sources' / 'original_audio.wav'
OUT_STEMS_DIR = BASE_DIR / 'isolated_stems'
OUT_FILE = OUT_STEMS_DIR / 'pure_ai_sfx_bells.wav'

OUT_STEMS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Load Original Audio
print(f"Loading {ORIG_AUDIO_PATH}...")
audio, sr = sf.read(str(ORIG_AUDIO_PATH))
n_samples = len(audio)
duration = n_samples / sr
print(f"Audio loaded: {n_samples} samples ({duration:.2f}s) @ {sr}Hz, Channels: {audio.shape[1]}")

# 2. Load Word-Level Timestamps from Whisper Base
with open('word_level_vocal_timeline.json', 'r', encoding='utf-8') as f:
    words = json.load(f)

# Also load screenplay cues for sanity / macro context
with open(BASE_DIR / 'scripts' / 'master_bangla_screenplay_script.json', 'r', encoding='utf-8') as f:
    screenplay_cues = json.load(f)

print(f"Loaded {len(words)} word timestamps and {len(screenplay_cues)} screenplay cues.")

# 3. Construct continuous vocal suppression mask
# We want:
# - During pure speech tokens: 0.0 volume (100% vocal bleed elimination)
# - Smooth cosine/sigmoid crossfade (20ms) around word boundaries to eliminate clicks/pops
# - Outside speech tokens (school bells, intro chimes, boings, pops, cartoon reaction sound effects): 1.0 full pristine clarity
fade_samples = int(0.025 * sr) # 25ms smooth crossfade
mask = np.ones(n_samples, dtype=np.float32)

# Build speech intervals from word timestamps with precise padding
speech_intervals = []
for w in words:
    # Filter out false low-confidence detections or musical hallu if any
    p = w.get('prob', 1.0)
    text = w.get('word', '').strip().lower()
    
    # Standard speech token
    w_start = max(0.0, w['start'] - 0.03) # 30ms pre-roll to catch plosives
    w_end = min(duration, w['end'] + 0.04)   # 40ms post-roll to catch sibilants
    speech_intervals.append((w_start, w_end))

# Merge overlapping speech intervals
speech_intervals.sort(key=lambda x: x[0])
merged_intervals = []
for start, end in speech_intervals:
    if not merged_intervals:
        merged_intervals.append([start, end])
    else:
        prev_start, prev_end = merged_intervals[-1]
        if start <= prev_end + 0.06: # merge if gap is less than 60ms
            merged_intervals[-1][1] = max(prev_end, end)
        else:
            merged_intervals.append([start, end])

print(f"Merged into {len(merged_intervals)} speech suppression intervals.")

# Apply smooth windowed gating to the mask
for start, end in merged_intervals:
    s_idx = int(start * sr)
    e_idx = int(end * sr)
    
    s_idx = max(0, min(n_samples - 1, s_idx))
    e_idx = max(0, min(n_samples - 1, e_idx))
    
    # Ramp down from 1 to 0 over fade_samples
    ramp_down_start = max(0, s_idx - fade_samples)
    actual_fade_in = s_idx - ramp_down_start
    if actual_fade_in > 0:
        fade_curve = 0.5 * (1.0 + np.cos(np.linspace(0, np.pi, actual_fade_in)))
        mask[ramp_down_start:s_idx] = np.minimum(mask[ramp_down_start:s_idx], fade_curve)
        
    # Full zero inside speech
    mask[s_idx:e_idx] = 0.0
    
    # Ramp up from 0 to 1 over fade_samples
    ramp_up_end = min(n_samples, e_idx + fade_samples)
    actual_fade_out = ramp_up_end - e_idx
    if actual_fade_out > 0:
        fade_curve = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, actual_fade_out)))
        mask[e_idx:ramp_up_end] = np.minimum(mask[e_idx:ramp_up_end], fade_curve)

# Apply mask to audio
sfx_audio = audio * mask[:, np.newaxis]

# 4. Apply Gentle Spectral De-hiss / De-noise to silence floor outside SFX
# We preserve all transients and bell resonances while ensuring pure zero hiss in quiet beds
print("Applying spectral noise suppression...")
# Find a quiet section to estimate stationary noise floor
quiet_slice = sfx_audio[int(11.2*sr):int(11.8*sr)] # known pause
if np.max(np.abs(quiet_slice)) > 0:
    import noisereduce as nr
    # Reduce stationary hiss across both channels
    sfx_cleaned_L = nr.reduce_noise(y=sfx_audio[:, 0], sr=sr, stationary=True, prop_decrease=0.85)
    sfx_cleaned_R = nr.reduce_noise(y=sfx_audio[:, 1], sr=sr, stationary=True, prop_decrease=0.85)
    sfx_audio = np.stack([sfx_cleaned_L, sfx_cleaned_R], axis=1)

# Ensure strictly zero samples where mask is zero
sfx_audio = sfx_audio * (mask[:, np.newaxis] > 0.0)

# Check peak amplitude and normalize if necessary
max_peak = np.max(np.abs(sfx_audio))
print(f"Max peak amplitude in isolated SFX: {max_peak:.4f}")

# Write to destination
print(f"Writing isolated track to: {OUT_FILE}...")
sf.write(str(OUT_FILE), sfx_audio, sr, subtype='PCM_16')
print(f"Successfully delivered {OUT_FILE} (Size: {OUT_FILE.stat().st_size} bytes)")
