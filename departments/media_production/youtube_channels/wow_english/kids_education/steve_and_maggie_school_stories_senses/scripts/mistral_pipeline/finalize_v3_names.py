import json
import os
import shutil

ROOT = "departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses"
RENDERED = os.path.join(ROOT, "rendered_output")

src_audio = os.path.join(RENDERED, "Steve_and_Maggie_EGM_V3_Master_Audio.wav")
dst_audio = os.path.join(RENDERED, "Steve_and_Maggie_EGM_V3_Precision_Synced_Master_Audio.wav")

src_video = os.path.join(RENDERED, "Steve_and_Maggie_EGM_V3_Authentic_Synced.mp4")
dst_video = os.path.join(RENDERED, "Steve_and_Maggie_EGM_V3_Precision_Synced.mp4")

if os.path.exists(src_audio):
    shutil.copy2(src_audio, dst_audio)
    print(f"Copied Master Audio -> {dst_audio}")

if os.path.exists(src_video):
    shutil.copy2(src_video, dst_video)
    print(f"Copied Synced Video -> {dst_video}")
