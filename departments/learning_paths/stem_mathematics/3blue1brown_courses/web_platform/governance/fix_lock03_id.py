import json
p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/data/lockdown_math/lesson_03.json'
d=json.load(open(p,encoding='utf-8'))
old_top=d.get('youtube_id'); old_meta=d.get('meta',{}).get('youtube_id')
# bT1p5tJwn_0 = jbstatistics "Intro to Bernoulli Distribution" (NOT 3B1B).
# Use official 3B1B binomial-distributions video (same as probability L03) as the closest official source.
new='8idr1WZ1A7Q'
d['youtube_id']=new
d.setdefault('meta',{})['youtube_id']=new
json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('lockdown L03 id:',old_top,'/',old_meta,'->',new)
