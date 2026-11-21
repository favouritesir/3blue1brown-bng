import json, re, os
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
for n in [3,4]:
    p=f'{W}/data/neural_networks/lesson_{n:02d}.json'
    d=json.load(open(p,encoding='utf-8'))
    print(f'L{n} keys:',list(d.keys())[:12])
    s=open(p,encoding='utf-8').read()
    print(f'  ids:',re.findall(r'"([A-Za-z0-9_-]{11})"',s)[:6])
    sec=d.get('sections',[])
    print(f'  sections:',[x.get('id') for x in sec][:10] if sec else 'n/a')
    # find title
    for k in ('title','title_en','headline','headline_bn'):
        if k in d: print(f'  {k}:',str(d[k])[:70]); break
    man=f'{W}/assets/audio/neural_networks/lesson_{n:02d}/manifest.json'
    print(f'  audio manifest exists:',os.path.isfile(man))
