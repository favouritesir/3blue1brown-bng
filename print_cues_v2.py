import json

with open('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/scripts/egm_master_screenplay_v2.json', encoding='utf-8') as f:
    sp = json.load(f)

print(f"Total cues: {len(sp['cues'])}")
for c in sp['cues']:
    print(f"Cue {c['id']:02d} [{c['speaker']}] {c['start']:6.2f}s - {c['end']:6.2f}s ({c['duration']:4.2f}s) | Scene: {c.get('scene_title','')} | EN: {c.get('en','')} | BN: {c.get('bn','')}")
