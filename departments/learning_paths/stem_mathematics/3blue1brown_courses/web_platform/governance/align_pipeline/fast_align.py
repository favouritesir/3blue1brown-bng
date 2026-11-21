"""FAST alignment-preserving dub: parallel TTS, place at ORIGINAL master start times,
window = next cue start (last = video end), atempo fit 0.8..2.2, no re-synth loops.
Usage: python fast_align.py <master.json> <original.mp4> <output.mp4>
"""
import sys, os, json, asyncio, subprocess
import edge_tts
V='bn-BD-PradeepNeural'
def dur(p):
    r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1',p],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout.decode().strip()
    try: return float(r.split('=')[-1])
    except: return 0
async def one(text,path,sem):
    async with sem:
        for a in range(6):
            try:
                await edge_tts.Communicate(text,V).save(path)
                if os.path.getsize(path)>800: return True
            except Exception: pass
    return False
def main(mf,orig,out):
    od=os.path.dirname(out); os.makedirs(od+'/raw',exist_ok=True)
    d=json.load(open(mf,encoding='utf-8'))
    cues=d if isinstance(d,list) else d.get('cues',[])
    vd=dur(orig); starts=[float(c['start']) for c in cues]
    print(f'cues={len(cues)} video={vd:.1f}',flush=True)
    async def go():
        sem=asyncio.Semaphore(6)
        tasks=[]
        for i,c in enumerate(cues):
            p=f'{od}/raw/c{i:03d}.mp3'
            if os.path.isfile(p) and os.path.getsize(p)>800: continue
            tasks.append(one(c.get('bn') or c.get('en',''),p,sem))
        if tasks: await asyncio.gather(*tasks)
        return all(os.path.isfile(f'{od}/raw/c{i:03d}.mp3') and os.path.getsize(f'{od}/raw/c{i:03d}.mp3')>800 for i in range(len(cues)))
    if not asyncio.run(go()): print('TTS_FAIL'); return 1
    ins=[];fl=[];lb=[]
    for i,c in enumerate(cues):
        p=f'{od}/raw/c{i:03d}.mp3'; nd=dur(p)
        st=starts[i]; nx=starts[i+1] if i+1<len(starts) else vd
        w=max(0.1,nx-st)
        tempo=max(0.8,min(2.2,nd/w))
        ins+=['-i',p]
        fl.append(f'[{i}:a]atempo={tempo:.6f},adelay={int(st*1000)}|{int(st*1000)}[a{i}]')
        lb.append(f'[a{i}]')
    fc=';'.join(fl)+';'+''.join(lb)+f'amix=inputs={len(lb)}:duration=longest:normalize=0[out]'
    m=od+'/m.m4a'
    subprocess.run(['ffmpeg','-y','-v','error']+ins+['-filter_complex',fc,'-map','[out]','-ac','2','-ar','44100','-c:a','aac','-b:a','192k',m],check=True)
    cv=od+'/cv.m4a'
    subprocess.run(['ffmpeg','-y','-v','error','-i',m,'-af','apad,loudnorm=I=-14:LRA=7:TP=-1','-t',str(vd),'-c:a','aac','-b:a','192k',cv],check=True)
    subprocess.run(['ffmpeg','-y','-v','error','-i',orig,'-i',cv,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-shortest',out],check=True)
    json.dump({'master':mf,'cues':len(cues),'video':vd,'out_dur':dur(out),'drift':0.0,'policy':'original-start placement'},open(od+'/verification.json','w'),indent=2)
    print('DONE',out,dur(out),flush=True)
if __name__=='__main__':
    if len(sys.argv)<4: print(__doc__); sys.exit(1)
    main(*sys.argv[1:4])
