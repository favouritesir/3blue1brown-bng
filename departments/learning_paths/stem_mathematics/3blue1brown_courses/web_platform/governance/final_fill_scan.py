"""Final Gate 3 verification: all 22 fill2 videos are complete, no internal pockets."""
import glob, os, subprocess, array
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault'
files=sorted(glob.glob(W+'/**/fill_v2/*fill2.mp4',recursive=True))
print('fill2 videos:',len(files))
def internal_pockets(mp4):
    raw=subprocess.run(['ffmpeg','-v','quiet','-i',mp4,'-vn','-ac','1','-ar','8000','-f','s16le','-'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout
    a=array.array('h'); a.frombytes(raw[:len(raw)//2*2])
    if len(a)<8000: return -1,0
    win=4000; sil=0; runs=[]
    total=len(a)//win
    for i in range(total):
        seg=a[i*win:(i+1)*win]
        if max((abs(x) for x in seg),default=0)<200: sil+=1
        else:
            if sil>=5 and i>4 and i<total-6: runs.append(sil*0.5)
            sil=0
    return len(runs),max(runs) if runs else 0
bad=[]
for f in files:
    p,mx=internal_pockets(f)
    name=os.path.relpath(f,W)
    if p!=0 or os.path.getsize(f)<1000000: bad.append((name,p,mx,os.path.getsize(f)))
    print(f'{name}: internal_pockets={p} max={mx:.1f}s')
print('\nBAD:',bad)
print('PASS' if len(files)==22 and not bad else 'CHECK')
