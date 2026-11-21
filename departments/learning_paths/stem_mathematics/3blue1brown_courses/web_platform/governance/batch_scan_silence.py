import subprocess, glob, os, array
ROOT='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault'
def pockets(mp4):
    cmd=['ffmpeg','-v','quiet','-i',mp4,'-vn','-ac','1','-ar','8000','-f','s16le','-']
    raw=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout
    a=array.array('h'); a.frombytes(raw[:len(raw)//2*2])
    if not a: return -1,0
    win=4000; sil=0; runs=[]
    for i in range(len(a)//win):
        seg=a[i*win:(i+1)*win]
        peak=max((abs(x) for x in seg),default=0)
        if peak<200: sil+=1
        else:
            if sil>=5: runs.append(sil*0.5)
            sil=0
    if sil>=5: runs.append(sil*0.5)
    return len(runs), (max(runs) if runs else 0)
for course in ['linear_algebra','calculus','neural_networks']:
    for mp4 in sorted(glob.glob(f'{ROOT}/{course}/lesson_*/experiments/*full_dubbed*.mp4')):
        if '/fill_v2/' in mp4: continue
        n,mx=pockets(mp4)
        print(f'{course} {os.path.basename(os.path.dirname(os.path.dirname(mp4)))}: pockets={n} max={mx:.0f}s')
