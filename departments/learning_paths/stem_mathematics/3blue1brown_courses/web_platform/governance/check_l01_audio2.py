import subprocess, array, os, math
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/lesson_01'
files=['3b1b_lesson_01_bangla_dubbed_video_v2.mp4','3b1b_lesson_01_full_591s_dubbed.mp4','full_original.mp4']
def energy_range(path, start, dur=2):
    raw=subprocess.run(['ffmpeg','-v','quiet','-i',path,'-ss',str(start),'-t',str(dur),'-vn','-ac','1','-ar','8000','-f','s16le','-'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout
    a=array.array('h'); a.frombytes(raw[:len(raw)//2*2])
    if not a: return -99,0,0
    peak=max(abs(x) for x in a)
    rms=(sum(x*x for x in a)/len(a))**0.5
    db=20*math.log10(rms/32768) if rms else -99
    return round(db,1),peak,len(a)
for f in files:
    p=os.path.join(W,f)
    print('\n'+f)
    for t in [0, 2, 4, 10, 30, 60, 120, 300, 500, 580]:
        db,pk,n=energy_range(p,t)
        print(f'   t={t:>4}s: rms={db:>6} dBFS peak={pk:>6} samples={n}')
