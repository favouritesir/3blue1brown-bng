import json, os
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
m=f'{W}/assets/audio/calculus/lesson_11/manifest.json'
s=open(m,encoding='utf-8').read()
print('forbidden label count:', s.count('চিত্র প্রদর্শনী'))
d=json.load(open(m,encoding='utf-8'))
print('sections:', list(d.keys())[:12] if isinstance(d,dict) else type(d))
print('backup exists:', os.path.isdir(os.path.dirname(m)+'/_backup_before_expressive_build'))
