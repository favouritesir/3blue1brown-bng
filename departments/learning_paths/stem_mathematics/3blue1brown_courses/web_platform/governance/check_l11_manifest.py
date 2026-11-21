import json
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
d=json.load(open(f'{W}/assets/audio/calculus/lesson_11/manifest.json',encoding='utf-8'))
secs=d.get('sections',{})
print('sections type:',type(secs).__name__)
if isinstance(secs,dict):
    print('section keys:',list(secs.keys()))
    for k,v in list(secs.items())[:1]:
        print('first section sample:',k, json.dumps(v,ensure_ascii=False)[:400])
elif isinstance(secs,list):
    print('num sections:',len(secs))
    print('first:',json.dumps(secs[0],ensure_ascii=False)[:500] if secs else 'empty')
