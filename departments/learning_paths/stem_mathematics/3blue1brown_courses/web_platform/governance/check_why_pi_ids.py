import json,re,os
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
for n in range(1,9):
    s=open(f'{W}/data/why_pi/lesson_{n:02d}.json',encoding='utf-8').read()
    ids=re.findall(r'"([A-Za-z0-9_-]{11})"',s)
    print(f'L{n}:',ids[:3])
