import os, json
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
for n in [9,10]:
    m=W+f'/assets/audio/lockdown_math/lesson_{n:02d}/manifest.json'
    d=json.load(open(W+f'/data/lockdown_math/lesson_{n:02d}.json',encoding='utf-8'))
    forb=open(m,encoding='utf-8').read().count('চিত্র প্রদর্শনী') if os.path.isfile(m) else 'n/a'
    print(f'L{n}: id={d.get("youtube_id")} manifest={os.path.isfile(m)} forb={forb}')
    print('  sections:',[s.get('id') for s in d.get('sections',[])])
