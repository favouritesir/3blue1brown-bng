"""Extract full topic->lesson slugs map from 3B1B site bundle."""
import urllib.request, re, json
u='https://www.3blue1brown.com/assets/Header-qk6vXxWo.js'
s=urllib.request.urlopen(u,timeout=30).read().decode('utf-8','ignore')
# Find the object literal: "topic":{title:...,lessons:[...]}
topics={}
for m in re.finditer(r'([\w-]+):\{title:[`\'"]([^`\'"]+)[`\'"][^}]{0,400}?lessons:\[([^\]]+)\]',s):
    key,title,arr=m.group(1),m.group(2),m.group(3)
    slugs=re.findall(r'[`\'"]([\w-]+)[`\'"]',arr)
    if slugs:
        topics[key]={'title':title,'lessons':slugs}
print('topics:',len(topics))
for k,v in topics.items(): print(f'  {k}: {len(v["lessons"])} lessons — {v["title"]}')
json.dump(topics,open('departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/governance/topic_lesson_map.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('saved. total mapped lessons:',sum(len(v['lessons']) for v in topics.values()))
