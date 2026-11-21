import soundfile as sf
import numpy as np

orig, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/original_audio.wav')
# Check 10.5 - 13.5s (pencil scream/boing)
sf.write('check_10_14.wav', orig[int(10.5*sr):int(13.8*sr)], sr)
# Check 36.0 - 40.0s (Maggie chime / magic appearance)
sf.write('check_36_40.wav', orig[int(36.0*sr):int(40.0*sr)], sr)
# Check 45.0 - 47.0s (ruler sound effect)
sf.write('check_45_47.wav', orig[int(45.0*sr):int(47.0*sr)], sr)
print("Saved checks")
