import wave
import numpy as np

# Load 02_extracted_vocals_only.wav and 03_extracted_sfx_and_music_only.wav
VOC_PATH = 'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/isolated_stems/02_extracted_vocals_only.wav'
SFX_PATH = 'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/isolated_stems/03_extracted_sfx_and_music_only.wav'

with wave.open(VOC_PATH, 'rb') as wf:
    voc = np.frombuffer(wf.readframes(44100*10), dtype=np.int16)
with wave.open(SFX_PATH, 'rb') as wf:
    sfx = np.frombuffer(wf.readframes(44100*10), dtype=np.int16).reshape(-1, 2)

print("VOC RMS first 10s:", np.sqrt(np.mean(voc.astype(np.float32)**2)))
print("SFX RMS first 10s (L, R):", np.sqrt(np.mean(sfx[:, 0].astype(np.float32)**2)), np.sqrt(np.mean(sfx[:, 1].astype(np.float32)**2)))

# Check 0.0s to 2.2s (the intro bell chime)
intro_voc = voc[:int(44100*2.2)]
intro_sfx = sfx[:int(44100*2.2)]
print("\nIntro (0.0s - 2.2s):")
print("VOC RMS:", np.sqrt(np.mean(intro_voc.astype(np.float32)**2)))
print("SFX RMS:", np.sqrt(np.mean(intro_sfx[:, 0].astype(np.float32)**2)))

# Check 2.2s to 6.3s (Steve: Look, it's a pencil)
speech_voc = voc[int(44100*2.2):int(44100*6.3)]
speech_sfx = sfx[int(44100*2.2):int(44100*6.3)]
print("\nSpeech 1 (2.2s - 6.3s):")
print("VOC RMS:", np.sqrt(np.mean(speech_voc.astype(np.float32)**2)))
print("SFX RMS:", np.sqrt(np.mean(speech_sfx[:, 0].astype(np.float32)**2)))
