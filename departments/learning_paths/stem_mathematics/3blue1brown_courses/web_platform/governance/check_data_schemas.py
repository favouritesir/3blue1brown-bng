import json, glob, os
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
for course in ['linear_algebra','calculus','neural_networks','probability','differential_equations','lockdown_math']:
    p=f'{W}/data/{course}/lesson_01.json'
    d=json.load(open(p,encoding='utf-8'))
    print(f'\n=== {course} ===')
    print('keys:',list(d.keys())[:14])
    for k in ('title_en','title_bn','title','description_bn','description_en','headline_bn','subtitle_bn','duration','youtube_id','video_id'):
        if k in d: print(f'  {k}: {str(d[k])[:70]}')
    if 'meta' in d:
        m=d['meta']
        print('  meta keys:',list(m.keys())[:12])
        for k in ('title_en','title_bn','duration','youtube_id','description_bn'):
            if k in m: print(f'    meta.{k}: {str(m[k])[:70]}')
