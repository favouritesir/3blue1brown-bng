import subprocess

cmd = [
    'ffmpeg', '-y', '-i',
    'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/original_audio.wav',
    '-af', 'pan=stereo|c0=0.5*c0-0.5*c1|c1=0.5*c1-0.5*c0,volumedetect',
    '-f', 'null', '-'
]
res = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
for line in res.stderr.split('\n'):
    if 'volume' in line:
        print(line)
