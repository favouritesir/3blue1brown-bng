import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
import edge_tts

VOICE_ID = "bn-BD-PradeepNeural"

def run(cmd):
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{p.stderr}")
    return p.stdout

def get_dur(f):
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{f}"'
    try:
        return float(run(cmd).strip())
    except:
        return 0.0

async def syn_all_cues(cues, temp_dir):
    sem = asyncio.Semaphore(4)
    async def syn(c):
        raw = temp_dir / f"raw_{c['id']:03d}.mp3"
        async with sem:
            for _ in range(3):
                try:
                    comm = edge_tts.Communicate(c["bn"], VOICE_ID)
                    await comm.save(str(raw))
                    if raw.exists() and raw.stat().st_size > 100:
                        return
                except:
                    await asyncio.sleep(0.5)
    await asyncio.gather(*(syn(c) for c in cues))

def retime_and_build(script_path, out_audio, out_video, in_video):
    script_path = Path(script_path)
    with open(script_path, "r", encoding="utf-8") as f:
        cues = json.load(f)

    temp_dir = Path("temp_precision_sync")
    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Step 1: Synthesizing {len(cues)} cues...")
    asyncio.run(syn_all_cues(cues, temp_dir))

    print("[*] Step 2: Time-locking cues into exact video timeline slots...")
    # Target video total duration
    total_vid_dur = get_dur(in_video)
    
    # We will assemble each cue padded to its EXACT window length
    # slot duration = next_start - current_start
    slot_files = []
    
    for i, c in enumerate(cues):
        cid = c["id"]
        start = float(c["start"])
        end = float(c["end"])
        dur = end - start
        
        # Next start determine the maximum slot length
        if i + 1 < len(cues):
            next_start = float(cues[i+1]["start"])
        else:
            next_start = end
            
        slot_len = next_start - start
        
        raw_mp3 = temp_dir / f"raw_{cid:03d}.mp3"
        raw_d = get_dur(raw_mp3)
        if raw_d <= 0:
            raw_d = dur
            
        # Target speed so spoken text finishes comfortably within dur (leaving slight breathing room before next cue)
        target_speech_dur = min(dur, slot_len - 0.15) if slot_len > 0.3 else dur
        tempo = raw_d / target_speech_dur
        tempo = max(0.95, min(1.85, tempo)) # allow higher tempo if word count demands it so speech NEVER spills!
        
        timed_cue = temp_dir / f"timed_{cid:03d}.wav"
        # Speech + EQ
        run(f'ffmpeg -y -i "{raw_mp3.resolve()}" -af "atempo={tempo:.3f},equalizer=f=1800:t=q:w=1.2:g=1.5" -ar 44100 -ac 2 -acodec pcm_s16le "{timed_cue.resolve()}"')
        
        actual_speech_dur = get_dur(timed_cue)
        
        # Exact silence to pad up to slot_len
        pad = slot_len - actual_speech_dur
        final_slot = temp_dir / f"slot_{cid:03d}.wav"
        
        if pad > 0.02:
            pad_wav = temp_dir / f"pad_{cid:03d}.wav"
            run(f'ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=stereo -t {pad:.4f} -acodec pcm_s16le "{pad_wav.resolve()}"')
            c_txt = temp_dir / f"slot_c_{cid:03d}.txt"
            with open(c_txt, "w", encoding="utf-8") as ct:
                ct.write(f"file '{timed_cue.resolve().as_posix()}'\nfile '{pad_wav.resolve().as_posix()}'\n")
            run(f'ffmpeg -y -f concat -safe 0 -i "{c_txt.resolve()}" -c:a pcm_s16le "{final_slot.resolve()}"')
        else:
            # If speech still slightly longer, trim exactly to slot_len so zero spillover occurs!
            run(f'ffmpeg -y -i "{timed_cue.resolve()}" -t {slot_len:.4f} -c:a pcm_s16le "{final_slot.resolve()}"')
            
        slot_files.append(final_slot)

    # Initial silence before cue #1
    initial_silence_dur = float(cues[0]["start"])
    initial_wav = temp_dir / "initial_silence.wav"
    run(f'ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=stereo -t {initial_silence_dur:.4f} -acodec pcm_s16le "{initial_wav.resolve()}"')
    
    master_concat_txt = temp_dir / "master_concat.txt"
    with open(master_concat_txt, "w", encoding="utf-8") as mc:
        mc.write(f"file '{initial_wav.resolve().as_posix()}'\n")
        for sf in slot_files:
            mc.write(f"file '{sf.resolve().as_posix()}'\n")

    assembled_wav = temp_dir / "assembled_pure.wav"
    run(f'ffmpeg -y -f concat -safe 0 -i "{master_concat_txt.resolve()}" -c:a pcm_s16le "{assembled_wav.resolve()}"')

    # Loudness Normalization
    out_audio = Path(out_audio)
    out_audio.parent.mkdir(parents=True, exist_ok=True)
    print(f"[*] Step 3: Loudness Normalization to {out_audio}...")
    run(f'ffmpeg -y -i "{assembled_wav.resolve()}" -af "loudnorm=I=-14:LRA=7:TP=-1" -ar 44100 -ac 2 -b:a 192k "{out_audio.resolve()}"')

    # Re-mux to video
    out_video = Path(out_video)
    in_video = Path(in_video)
    print(f"[*] Step 4: Re-muxing video to {out_video}...")
    temp_mux = temp_dir / "mux.mp4"
    run(f'ffmpeg -y -i "{in_video.resolve()}" -i "{out_audio.resolve()}" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest "{temp_mux.resolve()}"')
    
    import shutil
    shutil.move(temp_mux, out_video)
    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"[SUCCESS] 100% Time-Locked Pure Audio & Video Rendered: {out_video}")

if __name__ == "__main__":
    retime_and_build(
        "departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_linear_algebra/lesson_01_vectors/dubbing_pipeline/3b1b_lesson_01_bangla_master_script.json",
        "departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/lesson_01/3b1b_lesson_01_bangla_master.mp3",
        "departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/lesson_01/3b1b_lesson_01_bangla_dubbed_video.mp4",
        "departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/lesson_01/3b1b_lesson_01_bangla_dubbed_video.mp4"
    )
