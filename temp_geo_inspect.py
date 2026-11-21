import json, os

base = os.path.join('departments', 'learning_paths', 'stem_mathematics',
                    '3blue1brown_courses', 'web_platform')
exp_ids = ['GNcFjFmqEc8', 'pQa_tWZmlGs', 'fsLh-NYhOoU',
           'd4EgbgTm0Bg', 'zjMuIxRvygQ', 'zwAD6dRSVyI']

for n in range(1, 7):
    nn = f'{n:02d}'
    mp = os.path.join(base, 'assets', 'audio', 'geometry', f'lesson_{nn}', 'manifest.json')
    lp = os.path.join(base, 'data', 'geometry', f'lesson_{nn}.json')
    m = json.load(open(mp, encoding='utf-8'))
    l = json.load(open(lp, encoding='utf-8'))
    vid = l.get('video_id')
    total = 0
    sec_detail = []
    for sid, sec in m.get('sections', {}).items():
        c = sec.get('cues', [])
        total += len(c)
        sec_detail.append((sid, len(c)))
    title = l.get('title_en')
    print(f'L{nn}: video_id={vid} expected={exp_ids[n-1]} '
          f'MATCH={vid == exp_ids[n-1]} title={title}')
    print(f'     voice={m.get("voice")} mode={m.get("mode")} '
          f'sections={sec_detail} TOTAL_CUES={total}')
    # Show first cue structure
    for sid, sec in m.get('sections', {}).items():
        cues = sec.get('cues', [])
        if cues:
            print(f'     first cue keys={list(cues[0].keys())}')
            print(f'     first cue sample={json.dumps(cues[0], ensure_ascii=False)[:400]}')
            break
