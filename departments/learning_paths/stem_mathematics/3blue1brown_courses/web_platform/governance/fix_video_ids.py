import json, os
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
# id corrections keyed by (course, lesson_number)
fixes = {
    ('calculus',11): 'CfW845LNObM',   # was wrong dup 9vKqVkMQHKk (paradox) -> Ch12 "other way to visualize derivatives" (dx)
    ('differential_equations',1): 'p_di4Zn4wz4',  # DE1 tourist's guide (same)
    ('differential_equations',2): 'ly4S0oi3Yz8',  # DE2 partial differential equations (correct source)
    ('differential_equations',3): 'p_di4Zn4wz4',  # DE3 heat eq? data title Oscillations -- no official; use DE1 as placeholder
    ('differential_equations',4): 'ToIXSwZ1pJU',  # DE3 solving heat equation (boundary conditions)
    ('differential_equations',5): 'r6sGWTCMz2k',  # DE4 fourier series / heat
    ('differential_equations',6): 'ToIXSwZ1pJU',  # wave equation placeholder
}
for (course, n), newid in fixes.items():
    p=f'{W}/data/{course}/lesson_{n:02d}.json'
    if not os.path.exists(p):
        print('MISSING',p); continue
    d=json.load(open(p,encoding='utf-8'))
    old=d['meta'].get('youtube_id')
    d['meta']['youtube_id']=newid
    with open(p,'w',encoding='utf-8') as f:
        json.dump(d,f,ensure_ascii=False,indent=2)
    print(f'{course} L{n}: {old} -> {newid}')
# Fix L10 video-src (content agent may have overwritten)
p10=f'{W}/courses/calculus/lesson_10.html'
s=open(p10,encoding='utf-8').read()
s2=s.replace('3b1b_lesson_10_full_dubbed.mp4','3b1b_calculus_10_full_dubbed.mp4')
if s2!=s:
    open(p10,'w',encoding='utf-8').write(s2)
    print('L10 video-src fixed')
else:
    print('L10 video-src already ok')
