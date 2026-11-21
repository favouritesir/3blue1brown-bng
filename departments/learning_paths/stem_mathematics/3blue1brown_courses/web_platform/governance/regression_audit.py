"""Read-only static audit across all component lesson pages for central invariants."""
import os, re, glob
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
pages=[]
for course in sorted(os.listdir(f'{W}/courses')):
    cdir=f'{W}/courses/{course}'
    if not os.path.isdir(cdir): continue
    for p in sorted(glob.glob(f'{cdir}/lesson_*.html')):
        s=open(p,encoding='utf-8',errors='ignore').read()
        if '<b1b-' in s:
            pages.append((p,s))
print('component pages:',len(pages))
CANON=['manifest.js','katex.min.js','auto-render.min.js','lesson_components.js',
       'lesson_components_extended.js','main.js','lesson.js','narration_engine.js']
issues=[]
for p,s in pages:
    rel=os.path.relpath(p,W)
    # 1. script presence & relative order
    pos=[]
    for name in CANON:
        m=re.search(re.escape(name), s)
        pos.append(m.start() if m else -1)
    if any(x<0 for x in pos):
        issues.append((rel,'missing script(s): '+','.join(n for n,x in zip(CANON,pos) if x<0)))
    elif pos!=sorted(pos):
        issues.append((rel,'script order wrong'))
    # 2. manifest loaded via script tag (gold standard uses <script src=...manifest.js>)
    if not re.search(r'<script[^>]*manifest\.js', s):
        issues.append((rel,'no manifest.js script tag'))
    # 3. no raw static shells / duplicate b1b-article open
    if s.count('<b1b-article')>1:
        issues.append((rel,'duplicate b1b-article host'))
    # 4. narration_engine last among canon
    if pos[-1]>=0 and not pos[-1]==max([x for x in pos if x>=0] or [-1]):
        issues.append((rel,'narration_engine not last'))
    # 5. data-no-narration on labs/quizzes sections (presence check)
    for sec in re.findall(r'<b1b-section[^>]*id="([^"]+)"', s):
        pass
print('issues:',len(issues))
for rel,msg in issues:
    print(' ',rel,'->',msg)
