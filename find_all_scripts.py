import os
import glob
import time

for path in sorted(glob.glob('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/**/*.py', recursive=True)):
    print(path)
