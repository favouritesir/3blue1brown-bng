"""Audit ALL pages' active video-src: duration vs original, and lead-in music (audio in first 1-2s)."""
import glob, os, re, subprocess, json
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
def probe(path, field):
    out=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration' if field=='dur' else 'stream=codec_type','-of','default=nw=1',path],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout.decode().strip()
    if field=='dur':
        try: return float(out.split('=')[-1])
        except: return 0
    return 'audio' in out
def leadin_rms(path):
    raw=subprocess.run(['ffmpeg','-v','quiet','-i',path,'-t','1','-vn','-ac','1','-ar','8000','-f','s16le','-'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout
    import array, math
    a=array.array('h'); a.frombytes(raw[:len(raw)//2*2])
    if not a: return -99
    rms=(sum(x*x for x in a)/len(a))**0.5
    return round(20*math.log10(rms/32768),1) if rms else -99
for page in sorted(glob.glob(W+'/courses/*/lesson_*.html')):
    s=open(page,encoding='utf-8',errors='ignore').read()
    srcs=set(re.findall(r'video-src="([^"]+)"',s))
    if not srcs: continue
    src=list(srcs)[0]
    if src.startswith('http') or 'data:' in src: continue
    p=os.path.normpath(os.path.join(os.path.dirname(page),src))
    if not os.path.isfile(p): continue
    dur=probe(p,'dur'); lead=leadin_rms(p)
    rel=os.path.relpath(p,W)
    flag=''
    if lead>-70: flag+=' MUSIC/LEADIN-AUDIO?'
    print(f'{os.path.relpath(page,W)}: {dur:.0f}s lead={lead}dB{flag} :: {os.path.basename(p)}')
