import json, collections
p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/linear_algebra/lesson_02/manifest.json'
m=json.load(open(p,encoding='utf-8'))
for sid,s in m['sections'].items():
    types=collections.Counter(c['type'] for c in s['cues'])
    texts=collections.Counter(c['text'] for c in s['cues'])
    dups=sum(1 for t,n in texts.items() if n>1)
    print(sid,'cues',len(s['cues']),'unique_text',len(texts),'dup_texts',dups,'types',dict(types))
