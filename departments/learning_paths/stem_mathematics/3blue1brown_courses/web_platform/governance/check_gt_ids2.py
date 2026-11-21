import json,re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
for n in [1,2]:
    s=open(f'{W}/data/group_theory/lesson_{n:02d}.json',encoding='utf-8').read()
    print(f'L{n} ids:',re.findall(r'"([A-Za-z0-9_-]{11})"',s)[:5])
    d=json.loads(s)
    print('  keys:',list(d.keys())[:10])
