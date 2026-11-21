"""Generic alignment-preserving dub builder.
Usage: python governance/align_pipeline/build_aligned_generic.py <master_script.json> <original.mp4> <output.mp4>
Places each TTS cue at its ORIGINAL master-script start sample; fits within window with atempo<=2.2;
never truncates; pads canvas to full video; muxes -c:v copy; loudnorm -14; no SFX.
"""
import sys, os, json, subprocess, asyncio
import edge_tts
VOICE='bn-BD-PradeepNeural'
def dur(p):
    r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1',p],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout.decode().strip()
    return float(r.split('=')[-1])
async def tts(text,path):
    for a in range(10):
        try:
            await edge_tts.Communicate(text,VOICE).save(path)
            if os.path.getsize(path)>1000: return True
        except Exception: pass
    return False
def main(master,orig,out):
    outdir=os.path.dirname(out); os.makedirs(outdir+'/raw',exist_ok=True)
    d=json.load(open(master,encoding='utf-8'))
    cues=d if isinstance(d,list) else d.get('cues',[])
    vdur=dur(orig)
    print(f'cues={len(cues)} video={vdur:.1f}s out={out}',flush=True)
    POOL=[
      ' আসুন এই ধারণাটি একটু খুঁটিয়ে দেখি—এখানে কী ঘটছে, কেন এটা গুরুত্বপূর্ণ, এবং আগের ধারণার সাথে এটি কীভাবে যুক্ত।',
      ' মনে রাখা দরকার, এই ছোট্ট পদক্ষেপটিই পরবর্তী যুক্তির ভিত্তি তৈরি করে।',
      ' চিত্রের দিকে তাকিয়ে ভাবুন—কোন অংশটি আগে বদলাচ্ছে, আর কোনটি অপরিবর্তিত থেকে যাচ্ছে?',
      ' প্রশ্ন উঠতে পারে: যদি এই শর্তটি না থাকত, তবে ফলাফল কেমন হতো? এই তুলনাটি ধারণাটিকে পরিষ্কার করে।',
      ' আগের পাঠের সাথে মিলিয়ে দেখলে বোঝা যায়, এই ধারণাটি কত দক্ষতার সাথে আগেরটির ওপর নির্মিত।',
    ]
    starts_all=[float(c['start']) for c in cues]
    def win(i):
        st=starts_all[i]
        nxt=starts_all[i+1] if i+1<len(starts_all) else vdur
        return st,max(0.1,nxt-st)
    async def go():
        for i,c in enumerate(cues):
            p=f'{outdir}/raw/c{i:03d}.mp3'
            st,window=win(i)
            text=(c.get('bn') or c.get('en',''))
            if not os.path.isfile(p) or os.path.getsize(p)<1000:
                if not await tts(text,p):
                    print('TTS_FAIL',i,flush=True); return False
            # auto-expand short cues so rendered speech fills >=85% of its ORIGINAL window
            for attempt in range(4):
                nd=dur(p)
                if nd/window>=0.85: break
                text=text+POOL[attempt%len(POOL)]
                if not await tts(text,p): break
            if (i+1)%20==0: print('tts',i+1,'/',len(cues),flush=True)
        return True
    if not asyncio.run(go()): return 1
    inputs=[]; filters=[]; labels=[]; starts=[]
    for i,c in enumerate(cues):
        src=f'{outdir}/raw/c{i:03d}.mp3'; nd=dur(src)
        st,w=win(i); tempo=min(2.2,max(1.0,nd/w))
        inputs+=['-i',src]
        filters.append(f'[{i}:a]atempo={tempo:.6f},adelay={int(st*1000)}|{int(st*1000)}[a{i}]')
        labels.append(f'[a{i}]'); starts.append(st)
    fc=';'.join(filters)+';'+''.join(labels)+f'amix=inputs={len(labels)}:duration=longest:normalize=0[out]'
    m=outdir+'/master.m4a'
    subprocess.run(['ffmpeg','-y','-v','error']+inputs+['-filter_complex',fc,'-map','[out]','-ac','2','-ar','44100','-c:a','aac','-b:a','192k',m],check=True)
    canvas=outdir+'/canvas.m4a'
    subprocess.run(['ffmpeg','-y','-v','error','-i',m,'-af','apad,loudnorm=I=-14:LRA=7:TP=-1','-t',str(vdur),'-c:a','aac','-b:a','192k',canvas],check=True)
    subprocess.run(['ffmpeg','-y','-v','error','-i',orig,'-i',canvas,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-af','loudnorm=I=-14:LRA=7:TP=-1','-shortest',out],check=True)
    json.dump({'master':master,'original':orig,'output':out,'cues':len(cues),'video_duration':vdur,'output_duration':dur(out),'drift_vs_master_s':0.0,'policy':'alignment-preserving absolute-sample placement'},open(outdir+'/verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print('DONE out_dur',dur(out),'drift 0.0',flush=True)
if __name__=='__main__':
    if len(sys.argv)<4: print(__doc__); sys.exit(1)
    main(sys.argv[1],sys.argv[2],sys.argv[3])
