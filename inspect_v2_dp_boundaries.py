import json

with open('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/scripts/egm_master_screenplay_v2.json', encoding='utf-8') as f:
    sp = json.load(f)

cues = sp['cues']
s_cues = [c for c in cues if c['speaker'] == 'Steve']
m_cues = [c for c in cues if c['speaker'] == 'Maggie']

print(f"Steve cues count: {len(s_cues)}")
print(f"Maggie cues count: {len(m_cues)}")

manifest_path = 'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_cues_v2/egm_v2_cues_manifest.json'
with open(manifest_path, encoding='utf-8') as f:
    manifest = json.load(f)

for m in manifest:
    if m['speaker'] == 'Steve':
        print(f"Cue {m['id']:02d}: master_seg_start={m['master_seg_start_s']:6.3f}s raw_dur={m['raw_seg_dur']:5.3f}s text={m['bn']}")
