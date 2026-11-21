import soundfile as sf
import numpy as np
import json

path = 'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/isolated_stems/pure_ai_sfx_bells.wav'
data, sr = sf.read(path)
print("File exists, shape:", data.shape, "Sample rate:", sr)

# 1. Verify Vocal Bleed = 0 during spoken words
with open('word_level_vocal_timeline.json', 'r', encoding='utf-8') as f:
    words = json.load(f)

vocal_bleed_max = 0.0
for w in words:
    s = int((w['start'] + 0.05) * sr)
    e = int((w['end'] - 0.05) * sr)
    if e > s:
        chunk = data[s:e]
        peak = np.max(np.abs(chunk))
        if peak > vocal_bleed_max:
            vocal_bleed_max = peak

print(f"Max vocal bleed during spoken tokens: {vocal_bleed_max:.6f} (Should be 0.0)")

# 2. Verify Cartoon Sound Effects / Bells / Chimes preserved
# Check intro bells & theme (0.0 to 1.3s)
intro_peak = np.max(np.abs(data[:int(1.3*sr)]))
intro_rms = np.sqrt(np.mean(data[:int(1.3*sr)]**2))
print(f"Intro Bells & Music (0.0 - 1.3s): Peak = {intro_peak:.4f}, RMS = {intro_rms:.4f}")

# Check pencil reaction / boing gag (12.7s - 13.5s)
pencil_gag = data[int(12.7*sr):int(13.5*sr)]
print(f"Pencil Reaction Gag (12.7 - 13.5s): Peak = {np.max(np.abs(pencil_gag)):.4f}, RMS = {np.sqrt(np.mean(pencil_gag**2)):.4f}")

# Check Maggie magic chime (36.0 - 38.0s)
maggie_chime = data[int(36.0*sr):int(38.0*sr)]
print(f"Maggie Magic Chime (36.0 - 38.0s): Peak = {np.max(np.abs(maggie_chime)):.4f}, RMS = {np.sqrt(np.mean(maggie_chime**2)):.4f}")

# Check Ruler flourish (44.5 - 46.5s)
ruler_sfx = data[int(44.5*sr):int(46.5*sr)]
print(f"Ruler Gag & Chime (44.5 - 46.5s): Peak = {np.max(np.abs(ruler_sfx)):.4f}, RMS = {np.sqrt(np.mean(ruler_sfx**2)):.4f}")

# Check Chili taste reaction gag (206.5 - 209.0s)
chili_gag = data[int(206.8*sr):int(209.0*sr)]
print(f"Chili Reaction Gag (206.8 - 209.0s): Peak = {np.max(np.abs(chili_gag)):.4f}, RMS = {np.sqrt(np.mean(chili_gag**2)):.4f}")
