"""V2: regenerate ALL bookmarks from final manifest; format real Bengali digits; clamp extras to last section."""
import os, glob, re, json
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
BD='০১২৩৪৫৬৭৮৯'
def bn(s): return ''.join(BD[int(c)] if c.isdigit() else c for c in str(s))
def fmt(sec):
    sec=int(sec); m,s=divmod(sec,60)
    if m>=60:
        h,m=divmod(m,60); return f'{bn(h)}:{bn(m).rjust(2,"০")}:{bn(s).rjust(2,"০")}'
    return f'{bn(m).rjust(2,"০")}:{bn(s).rjust(2,"০")}'
fixed=0
for page in sorted(glob.glob(W+'/courses/*/lesson_*.html')):
    rel=os.path.relpath(page,W).replace('\\','/'); parts=rel.split('/'); course=parts[1]; num=int(re.search(r'lesson_(\d+)',rel).group(1))
    man=f'{W}/assets/audio/{course}/lesson_{num:02d}/manifest.json'
    if not os.path.isfile(man): continue
    try: m=json.load(open(man,encoding='utf-8'))
    except: continue
    secs=m.get('sections',{})
    items=list(secs.values()) if isinstance(secs,dict) else (secs or [])
    starts=[]; t=0.0
    for s in items:
        starts.append(t)
        try: t+=float(s.get('total_duration_ms') or 0)/1000.0
        except: pass
    if not starts: continue
    s=open(page,encoding='utf-8').read()
    bm=re.findall(r'<b1b-bookmark\s+time="[^"]*"\s+time-bn="[^"]*"[^>]*>',s)
    if not bm: continue
    out=s
    for i,old in enumerate(bm):
        # extra bookmarks beyond sections: place near end (last section start), never stale huge times
        sec=starts[i] if i<len(starts) else starts[-1]
        new=re.sub(r'time="[^"]*"',f'time="{int(sec)}"',old,count=1)
        new=re.sub(r'time-bn="[^"]*"',f'time-bn="{fmt(sec)}"',new,count=1)
        out=out.replace(old,new,1)
    if out!=s: open(page,'w',encoding='utf-8').write(out); fixed+=1
print('pages fixed:',fixed)
