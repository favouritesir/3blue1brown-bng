"""Read-only: list all lesson youtube_ids per course and flag duplicates."""
import os, json, glob, collections
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
root=f'{W}/data'
for course in sorted(os.listdir(root)):
    cdir=f'{root}/{course}'
    if not os.path.isdir(cdir): continue
    rows=[]
    for p in sorted(glob.glob(f'{cdir}/lesson_*.json')):
        try:
            m=json.load(open(p,encoding='utf-8')).get('meta',{})
        except Exception as e:
            print(course, p, 'ERR', e); continue
        n=m.get('lesson_number','?'); vid=m.get('youtube_id','?')
        rows.append((n,vid,str(m.get('title_en',''))[:42]))
    cnt=collections.Counter(v for _,v,_ in rows)
    dups={v for v,c in cnt.items() if c>1 and v not in ('?','')}
    print(f'\n### {course}' + ('   ⚠ DUPLICATES: '+', '.join(dups) if dups else ''))
    for n,v,t in rows:
        print(f'  L{n}: {v}  {t}' + ('  <-- DUP' if v in dups else ''))
