import urllib.request, re, json
u='https://www.3blue1brown.com/assets/Header-qk6vXxWo.js'
s=urllib.request.urlopen(u,timeout=30).read().decode('utf-8','ignore')
topics={}
pat=r'["\']?([\w-]+)["\']?:\{title:[`\'"]([^`\'"]+)[`\'"],[^}]{0,500}?lessons:\[([^\]]+)\]'
for m in re.finditer(pat,s):
    key,title,arr=m.group(1),m.group(2),m.group(3)
    slugs=re.findall(r'[`\'"]([\w-]+)[`\'"]',arr)
    if slugs and key not in ('all',):
        topics[key]={'title':title,'lessons':slugs}
print('topics:',len(topics))
total=0
for k,v in topics.items():
    total+=len(v['lessons'])
    print(f'  {k}: {len(v["lessons"]):2d} — {v["title"]}')
json.dump(topics,open('departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/governance/topic_lesson_map.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('total mapped (with overlaps):',total,'unique:',len(set(l for v in topics.values() for l in v['lessons'])))
