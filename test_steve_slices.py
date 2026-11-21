import soundfile as sf
import os
import numpy as np

x, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/steve_master_take_google_studio.wav')
os.makedirs('temp_steve_slices', exist_ok=True)

# Let's inspect the first 4 seconds of Steve master
# Save 0.0 to 3.0s in small chunks
sf.write('temp_steve_slices/s_0_to_1.wav', x[int(0.0*sr):int(1.0*sr)], sr)
sf.write('temp_steve_slices/s_1_to_2.wav', x[int(1.0*sr):int(2.0*sr)], sr)
sf.write('temp_steve_slices/s_2_to_3.wav', x[int(2.0*sr):int(3.0*sr)], sr)
sf.write('temp_steve_slices/s_0_to_3.wav', x[int(0.0*sr):int(3.0*sr)], sr)
sf.write('temp_steve_slices/s_3_to_6.wav', x[int(3.5*sr):int(6.0*sr)], sr)
sf.write('temp_steve_slices/s_6_to_9.wav', x[int(6.3*sr):int(8.8*sr)], sr)

print("Saved test slices")
