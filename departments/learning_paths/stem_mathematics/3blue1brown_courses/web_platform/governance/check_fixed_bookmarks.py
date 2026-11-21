import re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
for c,n in [('lockdown_math',2),('linear_algebra',1),('probability',2),('analysis',1),('fractals',1)]:
    p=f'{W}/courses/{c}/lesson_{n:02d}.html'
    s=open(p,encoding='utf-8').read()
    print(c,f'L{n}:',re.findall(r'time="(\d+)"\s+time-bn="([^"]+)"',s)[:8])
