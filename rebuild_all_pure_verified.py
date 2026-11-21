import os
import sys
import json
import subprocess
from pathlib import Path

def run(cmd):
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Failed: {cmd}\n{p.stderr}")
    return p.stdout

def synthesize_and_mux_pure(lesson_id, script_path, video_in, final_video_out, final_audio_out):
    print(f"\n=======================================================")
    print(f"[*] STRICT RE-BUILD: {lesson_id}")
    print(f"=======================================================")
    
    script_path = Path(script_path)
    video_in = Path(video_in)
    final_video_out = Path(final_video_out)
    final_audio_out = Path(final_audio_out)
    
    temp_dir = Path(f"temp_strict_{lesson_id}")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    with open(script_path, "r", encoding="utf-8") as f:
        cues = json.load(f)

    # 1. Synthesize each cue directly with edge_tts python CLI/module
    print(f"[*] Step 1: Synthesizing {len(cues)} cues with bn-BD-PradeepNeural...")
    
    import asyncio, edge_tts
    
    async def syn_all():
        sem = asyncio.Semaphore(3)
        async def syn_one(c):
            out_file = temp_dir / f"cue_{c['id']:03d}.mp3"
            async with sem:
                for att in range(3):
                    try:
                        comm = edge_tts.Communicate(c["bn"], "bn-BD-PradeepNeural")
                        await comm.save(str(out_file))
                        if out_file.exists() and out_file.stat().st_size > 100:
                            return True
                    except Exception as e:
                        await asyncio.sleep(1.0)
                return False
        await asyncio.gather(*(syn_one(c) for c in cues))

    asyncio.run(syn_all())

    # 2. Build time-locked assembly
    print("[*] Step 2: Time-locking cues with exact silence and dynamic atempo...")
    concat_txt = temp_dir / "concat.txt"
    entries = []
    current_time = 0.0
    
    for i, c in enumerate(cues):
        cid = c["id"]
        start = float(c["start"])
        end = float(c["end"])
        target_dur = end - start
        
        raw_mp3 = temp_dir / f"cue_{cid:03d}.mp3"
        timed_wav = temp_dir / f"timed_{cid:03d}.wav"
        
        # Silence gap before this cue
        silence_gap = start - current_time
        if silence_gap > 0.03:
            silence_wav = temp_dir / f"silence_{cid:03d}.wav"
            run(f'ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=stereo -t {silence_gap:.4f} -acodec pcm_s16le "{silence_wav.resolve()}"')
            entries.append(silence_wav.resolve())
            current_time += silence_gap
            
        # Get raw duration
        p = run(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{raw_mp3.resolve()}"')
        try:
            raw_dur = float(p.strip())
        except:
            raw_dur = target_dur
            
        tempo = raw_dur / target_dur
        tempo = max(0.90, min(1.45, tempo))
        
        # Pure speech, presence EQ, zero music, zero SFX
        run(f'ffmpeg -y -i "{raw_mp3.resolve()}" -af "atempo={tempo:.3f},equalizer=f=1800:t=q:w=1.2:g=1.5" -ar 44100 -ac 2 -acodec pcm_s16le "{timed_wav.resolve()}"')
        
        p2 = run(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{timed_wav.resolve()}"')
        try:
            adj_dur = float(p2.strip())
        except:
            adj_dur = target_dur
            
        entries.append(timed_wav.resolve())
        current_time += adj_dur

    with open(concat_txt, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(f"file '{entry.as_posix()}'\n")

    assembled_wav = temp_dir / "assembled.wav"
    run(f'ffmpeg -y -f concat -safe 0 -i "{concat_txt.resolve()}" -c:a pcm_s16le "{assembled_wav.resolve()}"')

    # 3. Normalize strictly with EBU R128 (-14 LUFS)
    final_audio_out.parent.mkdir(parents=True, exist_ok=True)
    print(f"[*] Step 3: Loudness normalization to {final_audio_out}...")
    run(f'ffmpeg -y -i "{assembled_wav.resolve()}" -af "loudnorm=I=-14:LRA=7:TP=-1" -ar 44100 -ac 2 -b:a 192k "{final_audio_out.resolve()}"')

    # 4. Re-mux video with pure audio
    print(f"[*] Step 4: Re-muxing video to {final_video_out} (0% original sound)...")
    final_video_out.parent.mkdir(parents=True, exist_ok=True)
    temp_mp4 = temp_dir / "temp_mux.mp4"
    run(f'ffmpeg -y -i "{video_in.resolve()}" -i "{final_audio_out.resolve()}" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest "{temp_mp4.resolve()}"')
    
    import shutil
    shutil.move(temp_mp4, final_video_out)
    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"[SUCCESS] {lesson_id} is 100% pure voice and remuxed!")

if __name__ == "__main__":
    for i in range(1, 6):
        lid = f"lesson_{i:02d}"
        script = f"departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_linear_algebra/{lid}_*/dubbing_pipeline/*master_script.json"
        import glob
        matches = glob.glob(script)
        if not matches:
            # fallback
            matches = glob.glob(f"departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_linear_algebra/*{lid}*/*/*master_script.json")
        if not matches:
            matches = glob.glob(f"departments/learning_paths/stem_mathematics/3blue1brown_courses/*{lid}*/*/*master_script.json")
            
        if matches:
            s_path = matches[0]
            v_in = f"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/{lid}/3b1b_{lid}_bangla_dubbed_video.mp4"
            v_out = v_in
            a_out = f"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/{lid}/3b1b_{lid}_bangla_master.mp3"
            synthesize_and_mux_pure(lid, s_path, v_in, v_out, a_out)
