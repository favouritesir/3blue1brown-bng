"""Detect long internal silent pockets in a dubbed mp4's audio via ffmpeg silencedetect."""
import subprocess, sys, re, os
mp4=sys.argv[1]
# lightweight: decode audio to raw pcm s16le mono 8k via ffmpeg, then scan in python
rate=8000
cmd=['ffmpeg','-v','quiet','-i',mp4,'-vn','-ac','1','-ar',str(rate),'-f','s16le','-']
raw=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout
import array
a=array.array('h'); a.frombytes(raw[:len(raw)//2*2])
win=rate//2  # 0.5s windows
sil=0; maxsil=0; total=len(a)//win
sil_runs=[]
for i in range(total):
    seg=a[i*win:(i+1)*win]
    peak=max((abs(x) for x in seg), default=0)
    if peak < 200:  # ~ -45 dBFS threshold
        sil+=1
    else:
        if sil>=4: sil_runs.append((round((i-sil)*0.5,1), round(sil*0.5,1)))
        maxsil=max(maxsil,sil); sil=0
if sil>=4: sil_runs.append((round((total-sil)*0.5,1), round(sil*0.5,1)))
print(f'{os.path.basename(mp4)}: duration~{total*0.5:.0f}s, max_silence_run={maxsil*0.5:.1f}s, internal_runs>2s={len([r for r in sil_runs if r[1]>2])}')
for st,dur in sil_runs:
    if dur>2: print(f'   silent {st}s for {dur}s')
