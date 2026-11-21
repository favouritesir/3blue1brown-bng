"""Parse official 3B1B sitemap into topic-wise lesson inventory."""
import urllib.request, re, json, html
u='https://www.3blue1brown.com/sitemap.xml'
x=urllib.request.urlopen(u,timeout=30).read().decode('utf-8','ignore')
locs=re.findall(r'<loc>(.*?)</loc>',x)
lessons=[l for l in locs if '/lessons/' in l]
print('total URLs:',len(locs),'lesson URLs:',len(lessons))
out={}
for l in lessons:
    slug=html.unescape(l.split('/lessons/')[-1].split('?')[0].strip('/'))
    # canonical topic info not in sitemap; store slug list
    out.setdefault('__all__',[]).append(slug)
    print(' ',slug)
json.dump(out,open('departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/governance/lessons_inventory.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('saved lessons_inventory.json:',len(out['__all__']))
