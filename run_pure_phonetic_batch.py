import os
import sys
import json
import time
import shutil
import asyncio
import subprocess
from pathlib import Path
import edge_tts

VOICE_ID = "bn-BD-PradeepNeural"

def run_cmd(cmd):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\nError: {res.stderr}")
    return res.stdout

def get_duration(file_path):
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
    try:
        return float(run_cmd(cmd).strip())
    except Exception:
        return 0.0

async def generate_single_tts(cue, raw_mp3, sem):
    cid = cue["id"]
    text = cue["bn"]
    async with sem:
        for attempt in range(4):
            try:
                communicator = edge_tts.Communicate(text, VOICE_ID)
                await communicator.save(str(raw_mp3))
                if raw_mp3.exists() and raw_mp3.stat().st_size > 200:
                    return cid, True
            except Exception as e:
                await asyncio.sleep(1.0 * (attempt + 1))
        return cid, False

def process_lesson(script_path, output_mp3, video_path):
    print(f"\n==================================================")
    print(f" Processing: {script_path}")
    print(f"==================================================")
    
    script_path = Path(script_path)
    with open(script_path, "r", encoding="utf-8") as f:
        cues = json.load(f)

    temp_dir = Path("temp_phonetic_build")
    temp_dir.mkdir(parents=True, exist_ok=True)

    sem = asyncio.Semaphore(3) # max 3 concurrent edge requests

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def synthesize_all():
        tasks = []
        for cue in cues:
            raw_file = temp_dir / f"cue_{cue['id']:03d}.mp3"
            tasks.append(generate_single_tts(cue, raw_file, sem))
        results = await asyncio.gather(*tasks)
        return results

    results = loop.run_until_complete(synthesize_all())
    loop.close()

    success_count = sum(1 for cid, ok in results if ok)
    print(f" Synthesized {success_count}/{len(cues)} cues successfully.")

    # Alignment and Assembly
    concat_list_file = temp_dir / "concat_manifest.txt"
    entries = []
    current_time = 0.0

    for i, cue in enumerate(cues):
        cid = cue["id"]
        start = cue["start"]
        end = cue["end"]
        target_dur = end - start
        
        raw_mp3 = temp_dir / f"cue_{cid:03d}.mp3"
        timed_wav = temp_dir / f"timed_cue_{cid:03d}.wav"
        
        silence_gap = start - current_time
        if silence_gap > 0.04:
            silence_wav = temp_dir / f"silence_{cid:03d}.wav"
            cmd_silence = f'ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=mono -t {silence_gap:.4f} -acodec pcm_s16le "{silence_wav.resolve()}"'
            run_cmd(cmd_silence)
            entries.append(silence_wav.resolve())
            current_time += silence_gap
            
        raw_dur = get_duration(raw_mp3)
        if raw_dur <= 0:
            raw_dur = target_dur
            
        tempo = raw_dur / target_dur
        # Clamp tempo smoothly between 0.88 and 1.45
        tempo = max(0.88, min(1.45, tempo))
        
        filter_str = f"atempo={tempo:.3f},equalizer=f=1800:t=q:w=1.2:g=1.5"
        cmd_stretch = f'ffmpeg -y -i "{raw_mp3.resolve()}" -filter:a "{filter_str}" -ar 44100 -ac 1 -acodec pcm_s16le "{timed_wav.resolve()}"'
        run_cmd(cmd_stretch)
        
        actual_stretched_dur = get_duration(timed_wav)
        entries.append(timed_wav.resolve())
        current_time += actual_stretched_dur

    with open(concat_list_file, "w", encoding="utf-8") as f:
        for entry in entries:
            # Normalized forward slashes for ffmpeg concat on Windows
            clean_path = entry.as_posix()
            f.write(f"file '{clean_path}'\n")

    speech_track_wav = temp_dir / "speech_track_assembled.wav"
    run_cmd(f'ffmpeg -y -f concat -safe 0 -i "{concat_list_file}" -c:a pcm_s16le "{speech_track_wav}"')

    # Normalize pure speech with EBU R128 (-14 LUFS)
    output_mp3 = Path(output_mp3)
    output_mp3.parent.mkdir(parents=True, exist_ok=True)
    
    norm_cmd = (
        f'ffmpeg -y -i "{speech_track_wav}" '
        f'-af "loudnorm=I=-14:LRA=7:TP=-1" '
        f'-ar 44100 -ac 2 -b:a 192k "{output_mp3}"'
    )
    run_cmd(norm_cmd)
    print(f" Master Pure Audio Delivered: {output_mp3} (Duration: {get_duration(output_mp3):.2f}s)")

    # Remux Video
    video_path = Path(video_path)
    if video_path.exists():
        temp_video = temp_dir / "remuxed.mp4"
        remux_cmd = f'ffmpeg -y -i "{video_path}" -i "{output_mp3}" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest "{temp_video}"'
        run_cmd(remux_cmd)
        if temp_video.exists() and temp_video.stat().st_size > 1000000:
            shutil.move(temp_video, video_path)
            print(f" Video Remuxed Successfully: {video_path}")

    shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    # Lesson 01
    process_lesson(
        "departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_linear_algebra/lesson_01_vectors/dubbing_pipeline/3b1b_lesson_01_bangla_master_script.json",
        "departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/lesson_01/3b1b_lesson_01_bangla_master.mp3",
        "departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/lesson_01/3b1b_lesson_01_bangla_dubbed_video.mp4"
    )
    # Lesson 02
    process_lesson(
        "departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_linear_algebra/lesson_02_span/dubbing_pipeline/3b1b_lesson_02_bangla_master_script.json",
        "departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/lesson_02/3b1b_lesson_02_bangla_master.mp3",
        "departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/lesson_02/3b1b_lesson_02_bangla_dubbed_video.mp4"
    )
    # Lesson 03
    process_lesson(
        "departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_linear_algebra/lesson_03_linear_transformations/dubbing_pipeline/3b1b_lesson_03_bangla_master_script.json",
        "departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/lesson_03/3b1b_lesson_03_bangla_master.mp3",
        "departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/lesson_03/3b1b_lesson_03_bangla_dubbed_video.mp4"
    )
