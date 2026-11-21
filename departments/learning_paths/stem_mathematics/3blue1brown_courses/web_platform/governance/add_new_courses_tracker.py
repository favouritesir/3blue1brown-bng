"""Add new-course lesson IDs to tracker ONLY when real audio+video exist; then board regen."""
import os, glob, json, re, subprocess
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
tp=W+'/governance/completed_lessons.json'
t=json.load(open(tp,encoding='utf-8')); ids=t.get('completed_lessons',t)
def dur(p):
    try:
        r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1',p],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=8).stdout.decode().strip()
        return float(r.split('=')[-1])
    except: return 0
added=[]
for page in sorted(glob.glob(W+'/courses/*/lesson_*.html')):
    rel=os.path.relpath(page,W).replace('\\','/'); parts=rel.split('/'); course=parts[1]; num=int(re.search(r'lesson_(\d+)',rel).group(1))
    lid=f'{course}_l{num:02d}'
    # only NEW courses (not original 6)
    if course in ('linear_algebra','calculus','neural_networks','probability','differential_equations','lockdown_math'): continue
    if lid in ids: continue
    mp=f'{W}/assets/audio/{course}/lesson_{num:02d}/manifest.json'
    try: mode=json.load(open(mp,encoding='utf-8')).get('mode','')
    except: mode=''
    audios=glob.glob(f'{W}/assets/audio/{course}/lesson_{num:02d}/**/*.mp3',recursive=True)
    src=re.search(r'video-src="([^"]+)"',open(page,encoding='utf-8').read())
    vp=os.path.normpath(os.path.join(os.path.dirname(page),src.group(1))) if src else ''
    real_video=os.path.isfile(vp) and os.path.getsize(vp)>1000000 and dur(vp)>5
    real_audio='authentic' in str(mode) and len(audios)>0
    if real_video and real_audio:
        ids.append(lid); added.append(lid)
json.dump(t,open(tp,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('added to tracker:',len(added),added[:30])
print('total tracker:',len(ids))
