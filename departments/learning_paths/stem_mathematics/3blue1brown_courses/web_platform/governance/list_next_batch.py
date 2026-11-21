import json, re, os
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
for course, nums in [('calculus',[10,11,12]),('neural_networks',[2,3,4]),('probability',[2,3,4,5,6]),('differential_equations',[1,2,3,4,5,6]),('lockdown_math',[1,2,3,4,5,6,7,8,9,10])]:
    print('\n###',course)
    for n in nums:
        p=f'{W}/data/{course}/lesson_{n:02d}.json'
        if not os.path.exists(p):
            print(f' L{n:02d}: NO DATA'); continue
        s=open(p,encoding='utf-8').read()
        d=json.loads(s)
        ids=re.findall(r'"[A-Za-z0-9_-]{11}"',s)
        meta=d.get('meta',{})
        title=meta.get('title_en') or meta.get('title') or d.get('title_en') or d.get('title') or ''
        if not title:
            # look for headline/title keys anywhere
            for k in ('headline','headline_bn','title_bn','topic'):
                if k in d: title=str(d[k])[:80]; break
        print(f' L{n:02d}: id={ids[1] if len(ids)>1 else "?"} title={title[:80]}')
