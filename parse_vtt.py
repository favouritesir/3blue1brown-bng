import re
import json

with open('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/WL8qVKfw0Dk.en.vtt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def parse_time(t_str):
    parts = t_str.split(':')
    return float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])

words = []
# Match patterns like: Look,<00:00:03.280><c> it's</c><00:00:03.840><c> a</c>
time_block_regex = re.compile(r'(\d\d:\d\d:\d\d\.\d\d\d) --> (\d\d:\d\d:\d\d\.\d\d\d)')
word_regex = re.compile(r'([^<>\n]+)(?:<(\d\d:\d\d:\d\d\.\d\d\d)>|$)')

current_block = None
for line in lines:
    m = time_block_regex.match(line)
    if m:
        current_block = (parse_time(m.group(1)), parse_time(m.group(2)))
        continue
    if '<' in line and current_block:
        # print first 5 matches to see structure
        print("SAMPLE LINE:", line.strip()[:80])
        break
