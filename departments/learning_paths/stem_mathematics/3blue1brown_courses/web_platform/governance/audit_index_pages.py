import os, glob, re, json
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
for c in ['linear_algebra','calculus','neural_networks','probability','differential_equations','lockdown_math']:
    p=f'{W}/courses/{c}/index.html'
    s=open(p,encoding='utf-8').read()
    hrefs=set(re.findall(r'href="([^"]*lesson_\d+\.html)"',s))
    data=len(glob.glob(f'{W}/data/{c}/lesson_*.json'))
    print(f'{c}: index lists {len(hrefs)} lesson links, data has {data}')
    missing=[f'lesson_{n:02d}.html' for n in range(1,data+1) if f'lesson_{n:02d}.html' not in ' '.join(hrefs)]
    if missing: print('   MISSING from index:',missing)
print('\n=== curriculum_index.json lesson counts vs actual ===')
d=json.load(open(W+'/curriculum_index.json',encoding='utf-8'))
for c in d['courses']:
    listed=len(c.get('lessons',[]))
    actual=len(glob.glob(f'{W}/data/{c["id"]}/lesson_*.json'))
    print(f'  {c["id"]}: listed={listed} dubbed_field={c.get("lessons_dubbed")} actual={actual}')
