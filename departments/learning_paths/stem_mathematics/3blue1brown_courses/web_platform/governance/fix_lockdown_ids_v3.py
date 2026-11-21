import json
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
fixes={
 6:'ZA4JkHKZM50',   # continuous probability / density -> 3B1B "probability of 0 != impossible"
 7:'GNcFjFmqEc8',   # area/derivative of circle -> 3B1B area/shadow geometry (related official clip)
 9:'LyGKycYT2v0',   # dual vectors -> 3B1B "Dot products and duality | Ch9 LA" (perfect topic match)
}
for n,new in fixes.items():
    p=f'{W}/data/lockdown_math/lesson_{n:02d}.json'
    d=json.load(open(p,encoding='utf-8'))
    old=d.get('youtube_id')
    d['youtube_id']=new; d.setdefault('meta',{})['youtube_id']=new
    json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(f'L{n}: {old} -> {new}')
