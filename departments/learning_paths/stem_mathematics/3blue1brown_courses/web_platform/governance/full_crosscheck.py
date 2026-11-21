"""Cross-check ALL courses: content page, audio (real vs placeholder), video (real vs placeholder), bookmark sanity."""
import os, glob, json, re, subprocess
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
def probe_dur(p):
    try:
        r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1',p],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=10).stdout.decode().strip()
        return float(r.split('=')[-1])
    except: return 0
rows=[]
for page in sorted(glob.glob(W+'/courses/*/lesson_*.html')):
    rel=os.path.relpath(page,W).replace('\\','/'); parts=rel.split('/')
    course,num=parts[1],int(re.search(r'lesson_(\d+)',rel).group(1))
    s=open(page,encoding='utf-8').read()
    # audio
    mpath=f'{W}/assets/audio/{course}/lesson_{num:02d}/manifest.json'
    mode='NONE'; audios=0
    if os.path.isfile(mpath):
        try: mode=json.load(open(mpath,encoding='utf-8')).get('mode','?')
        except: mode='ERR'
        audios=len(glob.glob(f'{W}/assets/audio/{course}/lesson_{num:02d}/**/*.mp3',recursive=True))
    # video
    src=re.search(r'video-src="([^"]+)"',s)
    vp=os.path.normpath(os.path.join(os.path.dirname(page),src.group(1))) if src else ''
    vsize=os.path.getsize(vp) if os.path.isfile(vp) else 0
    vdur=probe_dur(vp) if vsize else 0
    # bookmarks
    bms=re.findall(r'time="(\d+)"\s+time-bn="([^"]+)"',s)
    badbm=[t for t,_ in bms if vdur and int(t)>vdur+1]
    rows.append((course,num,mode,audios,vsize,vdur,len(bms),badbm))
# summary
from collections import Counter, defaultdict
byc=defaultdict(list)
for r in rows: byc[r[0]].append(r)
print(f'{"course":<24}{"lessons":>7}{"real_audio":>11}{"real_video":>11}{"bad_bookmarks":>14}')
for c,rs in sorted(byc.items()):
    ra=sum(1 for r in rs if r[2] not in ('NONE','ERR','placeholder_pending_audio_agent') and r[3]>0)
    rv=sum(1 for r in rs if r[4]>1000000)
    bb=sum(1 for r in rs if r[7])
    print(f'{c:<24}{len(rs):>7}{ra:>11}{rv:>11}{bb:>14}')
print('\nDETAIL (problem rows only):')
for r in rows:
    c,n,mode,audios,sz,dur,nb,bb=r
    probs=[]
    if mode in ('NONE','ERR','placeholder_pending_audio_agent') or audios==0: probs.append('AUDIO_PLACEHOLDER')
    if sz<=1000000: probs.append('VIDEO_PLACEHOLDER' if sz else 'VIDEO_MISSING')
    if bb: probs.append('BOOKMARK>OUTPUT:'+','.join(bb))
    if probs: print(f'  {c} L{n:02d}: {mode} audio={audios} video={sz//1024}KB/{dur:.0f}s bm={nb} -> {probs}')
