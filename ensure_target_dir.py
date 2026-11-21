from pathlib import Path
out_dir = Path('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/isolated_stems/nemotron_3_nano_omni')
out_dir.mkdir(parents=True, exist_ok=True)
print("Created target directory:", out_dir.resolve())
