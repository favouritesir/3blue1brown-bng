import os
import time

for path in [
    'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/steve_master_take_google_studio.wav',
    'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/maggie_master_take_google_studio.wav',
    'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/mistral_google_studio_masters/steve_master_take_mistral_google.wav',
    'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/mistral_google_studio_masters/maggie_master_take_mistral_google.wav',
    'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/mistral_google_studio_masters/archive_v1_ellipsis_separator/steve_master_take_mistral_google.wav'
]:
    if os.path.exists(path):
        st = os.stat(path)
        print(f"{path}: size={st.st_size} mtime={time.ctime(st.st_mtime)}")
