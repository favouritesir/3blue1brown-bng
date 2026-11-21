import os
import soundfile as sf
import numpy as np

def info(p):
    if os.path.exists(p):
        i = sf.info(p)
        print(f"{p}: dur={i.duration:.2f}s, sr={i.samplerate}, frames={i.frames}")
    else:
        print(f"{p}: NOT FOUND")

info('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_ai_studio_steve_master.wav')
info('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_ai_studio_maggie_master.wav')
info('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_ai_studio_voice_track.wav')

cues = sorted(os.listdir('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/sliced_cues'))
print(f"Total files in sliced_cues: {len(cues)}")
for c in cues[:10]:
    p = os.path.join('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/sliced_cues', c)
    d, sr = sf.read(p)
    print(f"  {c:25s} dur={len(d)/sr:.3f}s rms={np.sqrt(np.mean(d**2)):.4f}")
