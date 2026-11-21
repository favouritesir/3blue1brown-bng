import json, re
p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/data/neural_networks/lesson_01.json'
d=json.load(open(p,encoding='utf-8'))
print('keys', list(d.keys())[:10])
print(str(d.get('meta',{}))[:300])
s=open(p,encoding='utf-8').read()
print('urls', re.findall(r'https?://[^" ]+', s)[:6])
print('ids', re.findall(r'"[A-Za-z0-9_-]{11}"', s)[:6])
