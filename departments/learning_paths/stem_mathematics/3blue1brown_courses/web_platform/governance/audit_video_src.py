"""Read-only audit: check every component lesson page's video-src resolves to an existing file."""
import os, re, glob
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
pages=[]
for course in sorted(os.listdir(f'{W}/courses')):
    cdir=f'{W}/courses/{course}'
    if not os.path.isdir(cdir): continue
    for p in sorted(glob.glob(f'{cdir}/lesson_*.html')):
        pages.append(p)
bad=[]; ok=0; no_video=0
for p in pages:
    s=open(p,encoding='utf-8',errors='ignore').read()
    srcs=set(re.findall(r'video-src="([^"]+)"', s))
    if not srcs:
        no_video+=1
        continue
    for src in srcs:
        if src.startswith('http'):
            continue
        resolved=os.path.normpath(os.path.join(os.path.dirname(p), src))
        if not os.path.isfile(resolved):
            bad.append((p, src))
        else:
            ok+=1
print('pages',len(pages),'resolved-ok refs',ok,'missing',len(bad),'no-video pages',no_video)
for p,src in bad:
    print(' MISSING:',os.path.relpath(p,W),'->',src)
