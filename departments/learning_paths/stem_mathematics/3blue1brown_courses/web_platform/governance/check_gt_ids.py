import json
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
for n in [1,2]:
    d=json.load(open(f'{W}/data/group_theory/lesson_{n:02d}.json',encoding='utf-8'))
    print(f'L{n}: youtube={d.get("youtube_id") or d.get("meta",{}).get("youtube_id")} title={d.get("title_en") or d.get("meta",{}).get("title_en","")[:60]}')
