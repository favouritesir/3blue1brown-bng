import soundfile as sf
import numpy as np

s, sr_s = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/steve_master_take_google_studio.wav')
if s.ndim > 1: s = s.mean(axis=1)

m, sr_m = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/maggie_master_take_google_studio.wav')
if m.ndim > 1: m = m.mean(axis=1)

print(f"Steve: {len(s)/sr_s:.2f}s, Maggie: {len(m)/sr_m:.2f}s")
