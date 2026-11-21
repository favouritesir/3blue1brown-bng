import soundfile as sf
import numpy as np

# Load the original audio
orig, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/original_audio.wav')
print("Loaded original audio:", orig.shape, sr)
