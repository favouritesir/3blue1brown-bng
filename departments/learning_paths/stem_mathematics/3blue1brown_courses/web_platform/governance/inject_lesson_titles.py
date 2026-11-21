import json, re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
ci=json.load(open(W+'/curriculum_index.json',encoding='utf-8'))
titles={}
for c in ci['courses']:
    titles[c['id']]={l['id']: l.get('title_bn') or l.get('title_en','') for l in c.get('lessons',[])}
js=json.dumps(titles,ensure_ascii=False,separators=(',',':'))
p=W+'/assets/js/lesson_components.js'
s=open(p,encoding='utf-8').read()
marker='const BN_DIGITS = '
inject='const B1B_LESSON_TITLES = '+js+';\n  '
if 'const B1B_LESSON_TITLES' in s:
    s=re.sub(r'const B1B_LESSON_TITLES = .*?;\n  ',inject,s,count=1,flags=re.S)
else:
    s=s.replace(marker,inject+marker,1)
open(p,'w',encoding='utf-8').write(s)
print('injected titles for',len(titles),'courses,',sum(len(v) for v in titles.values()),'lessons')
