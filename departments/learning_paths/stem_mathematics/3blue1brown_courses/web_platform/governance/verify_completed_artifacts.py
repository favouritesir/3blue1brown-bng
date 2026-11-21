"""Read-only: for every 'completed' lesson in tracker, verify page+video+audio manifest exist."""
import os, json, glob, re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
completed=json.load(open(f'{W}/governance/completed_lessons.json',encoding='utf-8'))
ids=completed.get('completed_lessons',completed)
if isinstance(ids,dict):
    ids=ids.get('completed',[])

# lessons with NO official 3B1B video (video-src optional by design)
NO_OFFICIAL_VIDEO={('calculus',12),('probability',5),('differential_equations',3),('differential_equations',6),('lockdown_math',10)}
problems=[]
for lid in ids:
    m=re.match(r'([a-z_]+)_l(\d+)', lid)
    if not m:
        problems.append((lid,'unparsable id')); continue
    course, num=m.group(1), int(m.group(2))
    page=f'{W}/courses/{course}/lesson_{num:02d}.html'
    if not os.path.isfile(page):
        problems.append((lid,'PAGE missing')); continue
    s=open(page,encoding='utf-8',errors='ignore').read()
    if '<b1b-' not in s:
        problems.append((lid,'PAGE not component-based'))
    # video file referenced by page (skip for lessons with no official video)
    if (course,num) in NO_OFFICIAL_VIDEO:
        srcs=set()
    else:
        srcs=set(re.findall(r'video-src="([^"]+)"',s))
    if not srcs:
        if (course,num) not in NO_OFFICIAL_VIDEO:
            problems.append((lid,'no video-src'))
    else:
        for src in srcs:
            if src.startswith('data:') or src.startswith('http'):
                problems.append((lid,'video-src placeholder/external: '+src[:40])); break
            resolved=os.path.normpath(os.path.join(os.path.dirname(page),src))
            if not os.path.isfile(resolved):
                problems.append((lid,'video-src MISSING: '+src))
    # expressive audio manifest
    man=f'{W}/assets/audio/{course}/lesson_{num:02d}/manifest.json'
    if not os.path.isfile(man):
        problems.append((lid,'AUDIO manifest missing'))
    elif '_backup_before_expressive_build' not in os.listdir(os.path.dirname(man)):
        problems.append((lid,'AUDIO no expressive backup'))

print('completed lessons:',len(ids))
print('problems:',len(problems))
for lid,msg in problems:
    print(' ',lid,'->',msg)
