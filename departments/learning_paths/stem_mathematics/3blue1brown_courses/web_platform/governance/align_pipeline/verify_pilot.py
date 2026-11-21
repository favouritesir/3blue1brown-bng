import subprocess, array, math, json
P='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/lesson_01/experiments/aligned_v2/3b1b_lesson_01_aligned.mp4'
def energy(t,dur=2):
    raw=subprocess.run(['ffmpeg','-v','quiet','-i',P,'-ss',str(t),'-t',str(dur),'-vn','-ac','1','-ar','8000','-f','s16le','-'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout
    a=array.array('h'); a.frombytes(raw[:len(raw)//2*2])
    if not a: return -99,0
    rms=(sum(x*x for x in a)/len(a))**0.5
    return round(20*math.log10(rms/32768),1),max(abs(x) for x in a)
for t in [10.9,30,60,120,240,360,480,560]:
    db,pk=energy(t)
    print(f't={t:>5}s rms={db:>6} dBFS peak={pk}')
# silence runs >2s using ffmpeg silencedetect to file
r=subprocess.run(['ffmpeg','-v','info','-i',P,'-vn','-af','silencedetect=noise=-45dB:d=2','-f','null','-'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT).stdout.decode('utf-8','ignore')
runs=[l for l in r.splitlines() if 'silence_start' in l or 'silence_end' in l]
print('silence events:',len(runs))
for l in runs[:12]: print(' ',l.strip()[-90:])
