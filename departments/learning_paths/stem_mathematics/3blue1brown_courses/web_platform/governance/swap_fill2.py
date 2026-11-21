import re, sys, os, glob
course, num = sys.argv[1], int(sys.argv[2])
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
page=f'{W}/courses/{course}/lesson_{num:02d}.html'
s=open(page,encoding='utf-8').read()
srcs=set(re.findall(r'video-src="([^"]+)"',s))
# LA course videos live in media_vault/lesson_XX (no course dir); others in media_vault/<course>/lesson_XX
if course=='linear_algebra':
    pattern=f'{W}/media_vault/lesson_{num:02d}/**/fill_v2/*fill2.mp4'
else:
    pattern=f'{W}/media_vault/{course}/lesson_{num:02d}/**/fill_v2/*fill2.mp4'
cands=[c for c in glob.glob(pattern,recursive=True) if '/fill_v2/' in c.replace('\\','/')]
if not cands:
    print('NO fill2 for',course,num); sys.exit(1)
actual=sorted(cands)[0]
rel=os.path.relpath(actual,os.path.dirname(page)).replace('\\','/')
new='../../'+rel if not rel.startswith('../') else rel
for src in srcs:
    s=s.replace(src,new)
    print(f'swapped: {src} -> {new}')
open(page,'w',encoding='utf-8').write(s)
