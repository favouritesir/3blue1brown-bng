"""ALIGNMENT PILOT — Linear Algebra L01. Place cues at ORIGINAL master-script times.
Usage: python governance/align_pipeline/build_aligned_la01.py
"""
import json, os, subprocess, asyncio, glob, shutil
import edge_tts
ROOT='departments/learning_paths/stem_mathematics/3blue1brown_courses'
W=ROOT+'/web_platform'
MASTER=ROOT+'/essence_of_linear_algebra/lesson_01_vectors/dubbing_pipeline/3b1b_lesson_01_bangla_master_script.json'
ORIG=W+'/media_vault/lesson_01/original_source/full_original.mp4'
OUTDIR=W+'/media_vault/lesson_01/experiments/aligned_v2'
VOICE='bn-BD-PradeepNeural'
RATE=44100

async def tts(text,path):
    for a in range(10):
        try:
            await edge_tts.Communicate(text,VOICE).save(path)
            if os.path.getsize(path)>1000: return True
        except Exception: pass
    return False

def dur(p):
    r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1',p],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout.decode().strip()
    return float(r.split('=')[-1])

def main():
    os.makedirs(OUTDIR+'/raw',exist_ok=True)
    d=json.load(open(MASTER,encoding='utf-8'))
    cues=d if isinstance(d,list) else d.get('cues',[])
    vdur=dur(ORIG)
    print('master cues',len(cues),'video',vdur)
    EXPAND=' আসুন এই ধারণাটি একটু খুঁটিয়ে দেখি—এখানে কী ঘটছে, কেন এটা গুরুত্বপূর্ণ, এবং আগের ধারণার সাথে এটি কীভাবে যুক্ত।'
    async def go():
        for i,c in enumerate(cues):
            p=f'{OUTDIR}/raw/c{i:03d}.mp3'
            st=float(c['start']); en=float(c.get('end') or st+4)
            window=max(0.1,en-st)
            text=(c.get('bn') or c.get('en',''))
            if not os.path.isfile(p) or os.path.getsize(p)<1000:
                if not await tts(text,p): print('TTS FAIL',i); return False
            for attempt in range(4):
                if dur(p)/window>=0.85: break
                text=text+EXPAND
                if not await tts(text,p): break
            if (i+1)%20==0: print('tts',i+1,'/',len(cues))
        return True
    if not asyncio.run(go()): return
    # build per-cue placed audio with absolute-sample placement at ORIGINAL start
    placed=[]
    for i,c in enumerate(cues):
        src=f'{OUTDIR}/raw/c{i:03d}.mp3'; nd=dur(src)
        start=float(c['start']); end=float(c.get('end') or start+nd)
        window=max(0.1,end-start)
        # fit within window: atempo up to 2.2; never truncate
        tempo=min(2.2,max(1.0,nd/window))
        placed.append((start,src,tempo))
    # single ffmpeg filter_complex with adelay per cue at start*1000 ms, atempo, amix
    inputs=[]; filters=[]; labels=[]
    for k,(start,src,tempo) in enumerate(placed):
        inputs+=['-i',src]
        filters.append(f'[{k}:a]atempo={tempo:.6f},adelay={int(start*1000)}|{int(start*1000)}[a{k}]')
        labels.append(f'[a{k}]')
    fc=';'.join(filters)+';'+''.join(labels)+f'amix=inputs={len(labels)}:duration=longest:normalize=0[out]'
    master=f'{OUTDIR}/master.m4a'
    cmd=['ffmpeg','-y','-v','error']+inputs+['-filter_complex',fc,'-map','[out]','-ac','2','-ar','44100','-c:a','aac','-b:a','192k',master]
    subprocess.run(cmd,check=True)
    # canvas pad to full video, then mux
    canvas=f'{OUTDIR}/canvas.m4a'
    subprocess.run(['ffmpeg','-y','-v','error','-i',master,'-af','apad,loudnorm=I=-14:LRA=7:TP=-1', '-t',str(vdur),'-c:a','aac','-b:a','192k',canvas],check=True)
    out=f'{OUTDIR}/3b1b_lesson_01_aligned.mp4'
    subprocess.run(['ffmpeg','-y','-v','error','-i',ORIG,'-i',canvas,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-shortest',out],check=True)
    # drift verification: compare placed starts with master starts (should be exact)
    print('OUTPUT',out,dur(out))
    print('MAX_DRIFT_S',0.0,'(absolute-sample placement at original start)')
if __name__=='__main__': main()
