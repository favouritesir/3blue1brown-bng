"""V3: bookmarks scaled to ACTUAL video duration (manifest audio span may differ from final video)."""
import os, glob, re, json, subprocess
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
BD='০১২৩৪৫৬৭৮৯'
def bn(s): return ''.join(BD[int(c)] if c.isdigit() else c for c in str(s))
def fmt(sec):
    sec=int(sec); m,s=divmod(sec,60)
    if m>=60:
        h,m=divmod(m,60); return f'{bn(h)}:{bn(m).rjust(2,"০")}:{bn(s).rjust(2,"০")}'
    return f'{bn(m).rjust(2,"০")}:{bn(s).rjust(2,"০")}'
def dur(p):
    try:
        r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1',p],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=10).stdout.decode().strip()
        return float(r.split('=')[-1])
    except: return 0
fixed=0
for page in sorted(glob.glob(W+'/courses/*/lesson_*.html')):
    rel=os.path.relpath(page,W).replace('\\','/'); parts=rel.split('/'); course=parts[1]; num=int(re.search(r'lesson_(\d+)',rel).group(1))
    mpath=f'{W}/assets/audio/{course}/lesson_{num:02d}/manifest.json'
    if not os.path.isfile(mpath): continue
    try: m=json.load(open(mpath,encoding='utf-8'))
    except: continue
    secs=m.get('sections',{}); items=list(secs.values()) if isinstance(secs,dict) else (secs or [])
    if not items: continue
    starts=[]; t=0.0
    for s in items:
        starts.append(t)
        try: t+=float(s.get('total_duration_ms') or 0)/1000.0
        except: pass
    if t<=0: continue
    s0=open(page,encoding='utf-8').read()
    src=re.search(r'video-src="([^"]+)"',s0)
    vp=os.path.normpath(os.path.join(os.path.dirname(page),src.group(1))) if src else ''
    vd=dur(vp) if os.path.isfile(vp) and os.path.getsize(vp)>1000000 else 0
    scale=min(1.0, vd/t) if vd else 1.0  # never place bookmark past video; keep 1 if placeholder
    bms=re.findall(r'<b1b-bookmark\s+time="[^"]*"\s+time-bn="[^"]*"[^>]*>',s0)
    if not bms: continue
    out=s0
    for i,old in enumerate(bms):
        sec=(starts[i] if i<len(starts) else starts[-1])*scale
        sec=min(int(sec), int(vd)-1) if vd else int(sec)
        new=re.sub(r'time="[^"]*"',f'time="{sec}"',old,count=1)
        new=re.sub(r'time-bn="[^"]*"',f'time-bn="{fmt(sec)}"',new,count=1)
        out=out.replace(old,new,1)
    if out!=s0: open(page,'w',encoding='utf-8').write(out); fixed+=1
print('pages fixed:',fixed)
