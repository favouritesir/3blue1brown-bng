import json, re
p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/data/probability/lesson_02.json'
s=open(p,encoding='utf-8').read()
d=json.loads(s)
print('keys', list(d.keys()))
print('ids', re.findall(r'"[A-Za-z0-9_-]{11}"',s)[:10])
print('meta', str(d.get('meta',{}))[:500])
print('sections:')
for sec in d.get('sections',[]):
    print('  ', sec.get('id'), '|', str(sec.get('title_en') or sec.get('title') or sec.get('headline_bn',''))[:70])
