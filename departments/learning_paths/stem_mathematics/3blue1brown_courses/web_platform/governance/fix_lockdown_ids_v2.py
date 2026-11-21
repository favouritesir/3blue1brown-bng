import json
p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/data/lockdown_math/lesson_04.json'
d=json.load(open(p,encoding='utf-8'))
old=d.get('youtube_id'); new='5PcpBw5Hbwo'  # correct case: 3B1B "Complex number fundamentals | Ep.3"
d['youtube_id']=new; d.setdefault('meta',{})['youtube_id']=new
json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(f'L04: {old} -> {new}')
