import glob, os, re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
for p in sorted(glob.glob(W+'/courses/*/lesson_*.html')):
    s=open(p,encoding='utf-8',errors='ignore').read()
    times=re.findall(r'<b1b-bookmark\s+time="([^"]+)"',s)
    if not times: continue
    bad=[t for t in times if not re.fullmatch(r'\d+',t)]
    print(f'{os.path.relpath(p,W)}: {len(times)} bookmarks, first={times[:3]}, NON-ASCII={bad[:4]}')
