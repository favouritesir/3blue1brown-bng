import json, re, glob, os
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
p=f'{W}/data/lockdown_math/lesson_01.json'
s=open(p,encoding='utf-8').read()
d=json.loads(s)
print('meta keys:',list(d.get('meta',{}).keys()))
print('ids in file:',re.findall(r'"([A-Za-z0-9_-]{11})"',s)[:10])
print('MHXO present:', 'MHXO86wKeDY' in s)
# where is video id stored?
def walk(o,path=''):
    if isinstance(o,dict):
        for k,v in o.items():
            if isinstance(v,str) and re.fullmatch(r'[A-Za-z0-9_-]{11}',v):
                print(' ID field:',path+'/'+k,'=',v)
            walk(v,path+'/'+k)
    elif isinstance(o,list):
        for i,v in enumerate(o): walk(v,path+f'[{i}]')
walk(d)
