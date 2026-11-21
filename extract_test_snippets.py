import subprocess
from pathlib import Path

# Let's extract 15-second audio snippets around key comedic and sound effect moments:
# 1. 0 to 15s (intro music, bell, pencil magic)
# 2. 35s to 50s (Maggie appears, magic sounds, Steve screaming)
# 3. 78s to 88s (pen scream, gag)
# 4. 140s to 155s (can't see glasses gag)
# 5. 162s to 180s (sniffing flower / stinky flower gag)
# 6. 192s to 210s (chili taste screaming gag)

snippets = [
    ("intro_0_15", 0, 15),
    ("maggie_35_50", 35, 50),
    ("gag_78_88", 78, 88),
    ("flower_162_180", 162, 180),
    ("chili_192_210", 192, 210)
]

orig = "departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/original_audio.wav"

for name, s, e in snippets:
    out = f"test_{name}.wav"
    cmd = ["ffmpeg", "-y", "-ss", str(s), "-to", str(e), "-i", orig, out]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Extracted", out)
