import subprocess

# Check volume of clean_sfx_bed at 00:02 to 00:06 (during speech) -> should be -inf
# And at 00:00 to 00:02 (intro chime) -> should be normal
for seg, s, d in [("intro_chime", "00:00:00", "2"), ("speech_cue_1", "00:00:02.5", "3")]:
    cmd = [
        'ffmpeg', '-ss', s, '-t', d,
        '-i', 'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/clean_sfx_bed.wav',
        '-af', 'volumedetect', '-f', 'null', '-'
    ]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    max_v = [l for l in res.stderr.split('\n') if 'max_volume' in l]
    print(f"{seg}: {max_v}")
