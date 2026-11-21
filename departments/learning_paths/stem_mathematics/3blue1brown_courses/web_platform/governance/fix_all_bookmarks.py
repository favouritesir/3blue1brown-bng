"""Regenerate every lesson page's bookmark times from its FINAL audio manifest section timings."""
import os, glob, re, json
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
BN='০১২৩৪৫৬৭৮৯'
def bn(n): return ''.join(BN[int(d)] for d in str(n))
def fmt(sec):
    sec=int(sec); m,s=divmod(sec,60)
    if m>=60:
        h,m=divmod(m,60); return f'{bn(h)}:{bn(m):0>2}:{bn(s):0>2}'
    return f'{bn(m):0>2}:{bn(s):0>2}'
fixed=[]; skipped=[]
for page in sorted(glob.glob(W+'/courses/*/lesson_*.html')):
    rel=os.path.relpath(page,W).replace('\\','/')
    course=rel.split('/')[1]; num=re.search(r'lesson_(\d+)',rel).group(1)
    man=f'{W}/assets/audio/{course}/lesson_{int(num):02d}/manifest.json'
    if not os.path.isfile(man): continue
    try: m=json.load(open(man,encoding='utf-8'))
    except: continue
    secs=m.get('sections',{})
    if not secs: continue
    if isinstance(secs,dict): items=list(secs.values())
    else: items=secs
    starts=[]; t=0.0
    for s in items:
        starts.append(t)
        dur=s.get('total_duration_ms') or 0
        try: t+=float(dur)/1000.0
        except: pass
    s=open(page,encoding='utf-8').read()
    bm=re.findall(r'<b1b-bookmark\s+time="[^"]*"\s+time-bn="[^"]*"[^>]*>',s)
    if not bm: continue
    n=min(len(bm),len(starts))
    out=s
    for i in range(n):
        old=bm[i]
        new=re.sub(r'time="[^"]*"',f'time="{int(starts[i])}"',old,count=1)
        new=re.sub(r'time-bn="[^"]*"',f'time-bn="{fmt(starts[i])}"',new,count=1)
        out=out.replace(old,new,1)
    if out!=s:
        open(page,'w',encoding='utf-8').write(out); fixed.append((rel,n))
print('pages fixed:',len(fixed))
for r,n in fixed[:20]: print(' ',r,n)
