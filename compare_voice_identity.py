import soundfile as sf
import numpy as np

# Let's inspect the spectrum / pitch of raw_cue_001_Steve.wav vs steve_master_take_google_studio.wav
d1, sr1 = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/cues_rendered_perfect/raw_cue_001_Steve.wav')
d2, sr2 = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/steve_master_take_google_studio.wav')

print("raw_cue_001 sr:", sr1, "len:", len(d1)/sr1)
print("steve_master sr:", sr2, "len:", len(d2)/sr2)

# Check Maggie voice
dm1, srm1 = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/cues_rendered_perfect/raw_cue_012_Maggie.wav')
dm2, srm2 = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/maggie_master_take_google_studio.wav')

print("raw_cue_012 sr:", srm1, "len:", len(dm1)/srm1)
print("maggie_master sr:", srm2, "len:", len(dm2)/srm2)
