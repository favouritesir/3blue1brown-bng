import json, os, re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
groups=[('differential_equations',[4,5,6]),('lockdown_math',list(range(3,11)))]
for course,nums in groups:
    print('\n###',course)
    for n in nums:
        dpath=f'{W}/data/{course}/lesson_{n:02d}.json'
        mpath=f'{W}/assets/audio/{course}/lesson_{n:02d}/manifest.json'
        ppage=f'{W}/courses/{course}/lesson_{n:02d}.html'
        if not os.path.isfile(dpath):
            print(f' L{n}: NO DATA'); continue
        d=json.load(open(dpath,encoding='utf-8'))
        vid=d.get('youtube_id') or d.get('meta',{}).get('youtube_id')
        secs=[s.get('id') for s in d.get('sections',[])]
        title=str(d.get('title_en') or d.get('meta',{}).get('title_en') or d.get('title',''))[:44]
        forb='?'
        if os.path.isfile(mpath):
            forb=open(mpath,encoding='utf-8').read().count('চিত্র প্রদর্শনী')
        print(f' L{n}: id={vid} secs={len(secs)} manifest={os.path.isfile(mpath)} forb={forb} page={os.path.isfile(ppage)} | {title}')
        print(f'    sections: {secs}')
