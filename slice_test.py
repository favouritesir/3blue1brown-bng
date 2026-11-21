import soundfile as sf
import os
import subprocess

x, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/steve_master_take_google_studio.wav')
os.makedirs('temp_audit_slices', exist_ok=True)

# Let's save the first 10 utterance blocks found earlier and inspect their energy / content
from find_exact_blocks import find_speech_blocks
s_blocks, _ = find_speech_blocks('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/steve_master_take_google_studio.wav', -38, 0.25)

for i, (s, e) in enumerate(s_blocks[:15]):
    s0 = int(s * sr)
    s1 = int(e * sr)
    seg = x[s0:s1]
    out_path = f"temp_audit_slices/s_blk_{i+1:02d}.wav"
    sf.write(out_path, seg, sr)
    print(f"Block {i+1:02d}: {s:6.3f}s - {e:6.3f}s (dur {e-s:5.3f}s) -> {out_path}")
