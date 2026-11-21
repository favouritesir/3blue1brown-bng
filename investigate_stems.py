import wave
import numpy as np

BASE = 'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses'
SRC_WAV = f'{BASE}/raw_sources/original_audio.wav'
VOC_WAV = f'{BASE}/isolated_stems/02_extracted_vocals_only.wav'
SFX_WAV = f'{BASE}/isolated_stems/03_extracted_sfx_and_music_only.wav'

with wave.open(SRC_WAV, 'rb') as wf:
    sr = wf.getframerate()
    nframes = wf.getnframes()
    orig = np.frombuffer(wf.readframes(nframes), dtype=np.int16).reshape(-1, 2)

with wave.open(VOC_WAV, 'rb') as wf:
    voc = np.frombuffer(wf.readframes(nframes), dtype=np.int16)

with wave.open(SFX_WAV, 'rb') as wf:
    sfx = np.frombuffer(wf.readframes(nframes), dtype=np.int16).reshape(-1, 2)

print(f"Sample rate: {sr}, Frames: {nframes}, Duration: {nframes/sr:.2f}s")
print(f"Original shape: {orig.shape}, dtype: {orig.dtype}, max={np.max(np.abs(orig))}")
print(f"Vocals shape: {voc.shape}, max={np.max(np.abs(voc))}")
print(f"SFX shape: {sfx.shape}, max={np.max(np.abs(sfx))}")

# Check difference between original and sfx
# In Demucs or stem separation: is original == sfx + voc?
voc_stereo = np.column_stack([voc, voc])
rec = sfx.astype(np.float32) + voc_stereo.astype(np.float32)
diff = np.abs(orig.astype(np.float32) - rec)
print(f"Max diff (orig - (sfx+voc)): {np.max(diff):.2f}, Mean diff: {np.mean(diff):.2f}")
