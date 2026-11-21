import soundfile as sf
import numpy as np

x, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/steve_master_take_google_studio.wav')

# Let's inspect block 1, 2, 3, 4, 5
def print_block(t0, t1, idx):
    s0 = int(t0 * sr)
    s1 = int(t1 * sr)
    chunk = x[s0:s1]
    rms = np.sqrt(np.mean(chunk**2))
    peak = np.max(np.abs(chunk))
    print(f"Block {idx:02d} [{t0:6.3f}s - {t1:6.3f}s] dur={t1-t0:5.3f}s, rms={rms:.4f}, peak={peak:.4f}")

from find_exact_blocks import find_speech_blocks
s_blocks, _ = find_speech_blocks('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/steve_master_take_google_studio.wav', -38, 0.25)
for i, (s, e) in enumerate(s_blocks):
    print_block(s, e, i+1)
