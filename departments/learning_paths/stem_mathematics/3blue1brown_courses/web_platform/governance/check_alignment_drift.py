"""Compare final manifest cue start times with ORIGINAL master-script cue start times.
Large drift => dubbed narration no longer matches what the video shows at that second."""
import glob, json, os, re
ROOT='departments/learning_paths/stem_mathematics/3blue1brown_courses'
rows=[]
for mp in sorted(glob.glob(ROOT+'/web_platform/assets/audio/*/lesson_*/manifest.json')):
    course=re.search(r'audio/([^/]+)/lesson_(\d+)',mp.replace('\\','/'))
    if not course: continue
    c,n=course.group(1),int(course.group(2))
    mv=glob.glob(f'{ROOT}/web_platform/media_vault/**/lesson_{n:02d}/experiments/*full_dubbed*.mp4',recursive=True)
    mv=[v for v in mv if os.path.getsize(v)>1000000]
    if not mv: continue
    try: m=json.load(open(mp,encoding='utf-8'))
    except: continue
    secs=m.get('sections',{}); items=list(secs.values()) if isinstance(secs,dict) else []
    final=[]; t=0.0
    for s in items:
        for cu in s.get('cues',[])[:1]:
            final.append(t/1000.0)
        try: t+=float(s.get('total_duration_ms') or 0)
        except: pass
    # find original master script for this lesson
    masters=glob.glob(f'{ROOT}/**/lesson_{n:02d}*/dubbing_pipeline/**/*master_script*.json',recursive=True)
    orig=[]
    if masters:
        try:
            ms=json.load(open(masters[0],encoding='utf-8'))
            arr=ms if isinstance(ms,list) else (ms.get('cues') or ms.get('segments') or [])
            for x in arr[:len(final)]:
                st=x.get('start') or x.get('start_ms') or 0
                orig.append(float(st)/1000.0 if st>1000 else float(st))
        except: pass
    if not orig or len(orig)<2: continue
    # compare only if same section count; compute drift at each comparable point
    ds=[abs(f-o) for f,o in zip(final,orig)]
    rows.append((c,n,len(final),round(max(ds),1),round(sum(ds)/len(ds),1)))
rows.sort(key=lambda x:-x[3])
print(f'{"course":<22}{"L":>3}{"sections":>9}{"max_drift_s":>12}{"mean_drift_s":>13}')
for r in rows[:30]: print(f'{r[0]:<22}{r[1]:>3}{r[2]:>9}{r[3]:>12}{r[4]:>13}')
print('\nlessons compared:',len(rows),'| max drift >60s:',sum(1 for r in rows if r[3]>60))
