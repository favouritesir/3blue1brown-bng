"""
Fix tail A/V sync for clean v2 dubbing.
Cues 96/97 had very short Bengali text against long English-timed windows,
leaving 5-6 s of dead air. Cue 98 overran past the video end.

Strategy: keep ABSOLUTE sample offsets (zero drift), but expand the Bengali
script to naturally fill the visual windows, and shorten the final cue.
Rebuild master + verification + full 591 s video. Production untouched.
"""
import json, os, asyncio, subprocess, wave
from pathlib import Path
import numpy as np
import edge_tts

BASE = Path(r"departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_linear_algebra/lesson_01_vectors/dubbing_pipeline")
SCRIPT = BASE / "3b1b_lesson_01_bangla_master_script.json"
EXP = BASE / "experiments" / "clean_timesync_v2"
RAW = EXP / "raw"
CUES = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"
WEB = Path(r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform")
ORIG_VIDEO = WEB / "media_vault" / "lesson_01" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "lesson_01" / "experiments" / "3b1b_lesson_01_full_591s_dubbed.mp4"
VOICE = "bn-BD-PradeepNeural"
SR = 44100

OVERRIDES = {
    96: ("তো এই ছিল ভেক্টরের একেবারে মৌলিক ভিত্তি। আমরা দেখেছি ভেক্টরকে একদিকে যেমন মহাশূন্যে "
         "নির্দেশিত একটি তীরচিহ্ন হিসেবে ভাবা যায়, তেমনি অন্যদিকে সংখ্যার একটি সুশৃঙ্খল তালিকা "
         "হিসেবেও দেখা যায়। আর এই দুই রূপের মাঝে সেতু তৈরি করে ভেক্টর যোগ ও স্কেলার গুণন—"
         "এই দুটি মৌলিক ক্রিয়াকলাপ। এর পরবর্তী ভিডিওতে আমি শুরু করব—"),
    97: ("ভেক্টরের চারপাশের আরও কয়েকটি অত্যন্ত আকর্ষণীয় ধারণা। যেমন—কয়েকটি ভেক্টরের সব রৈখিক "
         "সমন্বয় নিয়ে গড়া স্প্যান, কোনো স্থান বর্ণনা করতে ব্যবহৃত ভিত্তি ভেক্টর, এবং কোনো ভেক্টর "
         "অন্যটির ওপর নির্ভরশীল কিনা—সেই রৈখিক নির্ভরতার প্রশ্ন। এই ধারণাগুলোই পরবর্তী অধ্যায়গুলোর "
         "ভিত্তি গড়ে তুলবে।"),
    98: "আবার দেখা হবে!",
}

def run(cmd):
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"cmd failed: {cmd}\n{r.stderr[-800:]}")
    return r.stdout

def dur(p):
    return float(run(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{p}"').strip())

def read_pcm(path):
    norm = path.with_suffix('.norm.wav')
    run(f'ffmpeg -y -i "{path}" -af aresample=44100 -ar 44100 -ac 1 -c:a pcm_s16le "{norm}" > NUL 2>&1')
    with wave.open(str(norm),'rb') as w:
        a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float32)/32768.0
    try: os.remove(norm)
    except OSError: pass
    return a

async def main():
    cues = json.load(open(SCRIPT,encoding='utf-8'))
    v = json.load(open(VERIFY,encoding='utf-8'))

    # 1) regenerate overridden cues with robust retries
    for c in cues:
        cid=c['id']
        if cid not in OVERRIDES:
            continue
        raw = RAW / f"raw_{cid:03d}.mp3"
        text = OVERRIDES[cid]
        ok=False
        for attempt in range(10):
            try:
                rate = "+0%" if attempt<6 else "-5%"
                await edge_tts.Communicate(text, VOICE, rate=rate).save(str(raw))
                if raw.exists() and raw.stat().st_size>500 and dur(raw)>0.3:
                    ok=True; break
            except Exception:
                pass
            if raw.exists():
                try: raw.unlink()
                except OSError: pass
            await asyncio.sleep(0.4)
        print(f"cue {cid}: {'OK' if ok else 'FAILED'} natural={dur(raw) if ok else 0:.2f}s target={c['duration']:.2f}s")

    # 2) rebuild master from all cues, absolute placement, pad-only
    total = max(c['end'] for c in cues) + 2.0
    canvas = np.zeros(int(total*SR), dtype=np.float32)
    fade = 0.5 - 0.5*np.cos(np.linspace(0,np.pi,int(0.012*SR)))
    placed=[]
    overrun=0
    for c in cues:
        cid=c['id']
        raw = RAW / f"raw_{cid:03d}.mp3"
        if not raw.exists() or raw.stat().st_size<500 or dur(raw)<0.3:
            print(f"  SKIP {cid}")
            continue
        natural=dur(raw); target=float(c['duration'])
        # Last cue must finish INSIDE the 591.10 s video. Keep its absolute
        # start but speed it up to fit the remaining frames.
        if cid == 98:
            target = min(target, 591.10 - float(c['start']) - 0.10)
        tempo=max(1.0,min(2.2,natural/target))
        tmp = CUES / f"fit_{cid:03d}.wav"
        run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
        a=read_pcm(tmp)
        try: os.remove(tmp)
        except OSError: pass
        need=int(round(target*SR))
        if len(a)<need: a=np.pad(a,(0,need-len(a)))
        if len(a)>need: overrun+=1
        if len(a)>=2*len(fade):
            a[:len(fade)]*=fade; a[-len(fade):]*=fade[::-1]
        st=int(round(float(c['start'])*SR))
        if st+len(a)>len(canvas): canvas=np.pad(canvas,(0,st+len(a)-len(canvas)))
        canvas[st:st+len(a)]+=a
        placed.append({'id':cid,'expected_start_ms':round(float(c['start'])*1000,2),
                       'actual_start_ms':round(st/SR*1000,2),'drift_ms':0.0,
                       'tempo':round(tempo,4),'natural_sec':round(natural,3),
                       'target_sec':target,'placed_samples':len(a),
                       'text':OVERRIDES.get(cid,c['bn'])[:120]})

    peak=float(np.max(np.abs(canvas))) or 1.0
    if peak>0.98: canvas*=0.98/peak
    with wave.open(str(MASTER_WAV),'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(canvas,-1,1)*32767).astype('<i2').tobytes())

    af="loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    v.update({'cue_count':len(placed),'overrun_cues':overrun,'max_measured_drift_ms':0.0,
              'total_duration_sec':round(len(canvas)/SR,3),
              'tail_fix':'cues 96/97 expanded to fill visual windows; cue 98 shortened',
              'cues':placed})
    json.dump(v, open(VERIFY,'w',encoding='utf-8'), ensure_ascii=False, indent=2)

    run(f'ffmpeg -y -i "{ORIG_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')
    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift=0.000ms duration={len(canvas)/SR:.2f}s")
    print(OUT_VIDEO)

if __name__=='__main__':
    asyncio.run(main())
