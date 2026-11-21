import subprocess, os, array
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
def pockets(mp4):
    raw=subprocess.run(['ffmpeg','-v','quiet','-i',mp4,'-vn','-ac','1','-ar','8000','-f','s16le','-'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout
    a=array.array('h'); a.frombytes(raw[:len(raw)//2*2])
    if not a: return 0,0
    win=4000; sil=0; runs=[]
    for i in range(len(a)//win):
        seg=a[i*win:(i+1)*win]
        if max((abs(x) for x in seg),default=0)<200: sil+=1
        else:
            if sil>=5: runs.append(sil*0.5)
            sil=0
    if sil>=5: runs.append(sil*0.5)
    return len(runs),max(runs) if runs else 0
for n in range(1,16):
    d=f'{W}/media_vault/lesson_{n:02d}'
    page=f'{W}/courses/linear_algebra/lesson_{n:02d}.html'
    import re
    src=re.search(r'video-src="([^"]+)"',open(page,encoding='utf-8').read())
    if not src: continue
    p=os.path.normpath(os.path.join(os.path.dirname(page),src.group(1)))
    if not os.path.isfile(p): print(f'L{n}: MISSING'); continue
    c,mx=pockets(p)
    print(f'L{n}: pockets={c} max={mx:.0f}s :: {os.path.basename(p)}')
