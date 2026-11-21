import re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
for n in [1,2,15]:
    p=f'{W}/courses/linear_algebra/lesson_{n:02d}.html'
    s=open(p,encoding='utf-8').read()
    m=re.search(r'<b1b-watch-panel[^>]*>(.*?)</b1b-watch-panel>',s,re.S)
    print(f'L{n} watch-panel: slot={"slot=\"playlist\"" in (m.group(1) if m else "")} playlist-items in source={s.count("playlist-item")}, len={len(m.group(1)) if m else 0}')
    if m and n==2: print('  inner:',m.group(1)[:400])
