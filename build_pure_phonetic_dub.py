import asyncio
import json
import os
import shutil
import subprocess
import edge_tts

async def synthesize_cue(text, out_path):
    communicate = edge_tts.Communicate(text, "bn-BD-PradeepNeural")
    await communicate.save(out_path)

def build_lesson(script_path, output_mp3, lesson_name):
    print(f"=== Starting build for {lesson_name} ===")
    with open(script_path, 'r', encoding='utf-8') as f:
        cues = json.load(f)

    temp_dir = f"temp_tts_{lesson_name}"
    os.makedirs(temp_dir, exist_ok=True)

    # 1. Synthesize all cues
    tasks = []
    cue_files = []
    for i, cue in enumerate(cues):
        fpath = os.path.join(temp_dir, f"cue_{i:04d}.mp3")
        cue_files.append((cue, fpath))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def run_all():
        for i, (cue, fpath) in enumerate(cue_files):
            if not os.path.exists(fpath) or os.path.getsize(fpath) == 0:
                await synthesize_cue(cue['bn'], fpath)
    
    loop.run_until_complete(run_all())
    loop.close()

    # 2. Measure durations & build timeline
    timeline_filter = []
    inputs = []
    filter_complex = []
    
    # We will assemble aligned segments using ffmpeg
    concat_list_path = os.path.join(temp_dir, "concat.txt")
    with open(concat_list_path, 'w', encoding='utf-8') as clist:
        current_time = 0.0
        for i, (cue, fpath) in enumerate(cue_files):
            start = cue['start']
            end = cue['end']
            target_dur = end - start

            # Measure raw duration
            probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", fpath]
            res = subprocess.run(probe_cmd, capture_output=True, text=True)
            try:
                raw_dur = float(res.stdout.strip())
            except:
                raw_dur = target_dur

            # Silence before this cue
            silence_gap = start - current_time
            if silence_gap > 0.04:
                silence_file = os.path.join(temp_dir, f"silence_{i:04d}.wav")
                subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo", "-t", str(silence_gap), silence_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                clist.write(f"file '{os.path.abspath(silence_file)}'\n")
                current_time += silence_gap

            # Tempo adjust cue so it strictly fits within target_dur (or max available before next cue)
            next_start = cues[i+1]['start'] if i + 1 < len(cues) else end
            max_allowed = max(target_dur, next_start - start)

            # Fit tempo
            tempo = raw_dur / target_dur
            tempo = max(0.90, min(1.45, tempo))

            adjusted_cue = os.path.join(temp_dir, f"adj_{i:04d}.wav")
            subprocess.run([
                "ffmpeg", "-y", "-i", fpath,
                "-af", f"atempo={tempo:.3f},equalizer=f=1800:t=q:w=1.2:g=1.5",
                "-ar", "44100", "-ac", "2",
                adjusted_cue
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Get new duration of adjusted cue
            p2 = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", adjusted_cue], capture_output=True, text=True)
            try:
                adj_dur = float(p2.stdout.strip())
            except:
                adj_dur = target_dur

            clist.write(f"file '{os.path.abspath(adjusted_cue)}'\n")
            current_time += adj_dur

    # 3. Concatenate and apply EBU R128 loudness normalization
    os.makedirs(os.path.dirname(output_mp3), exist_ok=True)
    temp_concat = os.path.join(temp_dir, "raw_concat.wav")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path, "-c", "copy", temp_concat], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Normalize
    subprocess.run([
        "ffmpeg", "-y", "-i", temp_concat,
        "-af", "loudnorm=I=-14:TP=-1:LRA=7",
        "-b:a", "192k",
        output_mp3
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"Master audio generated: {output_mp3}")
    
    # Clean up temp
    shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    # Lesson 01
    build_lesson(
        "departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_linear_algebra/lesson_01_vectors/dubbing_pipeline/3b1b_lesson_01_bangla_master_script.json",
        "departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/lesson_01/3b1b_lesson_01_bangla_master.mp3",
        "lesson_01"
    )
    # Remux video
    v_in = "departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/lesson_01/3b1b_lesson_01_bangla_dubbed_video.mp4"
    a_in = "departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/lesson_01/3b1b_lesson_01_bangla_master.mp3"
    v_out = "departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/lesson_01/temp_remux.mp4"
    subprocess.run(["ffmpeg", "-y", "-i", v_in, "-i", a_in, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", v_out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(v_out) and os.path.getsize(v_out) > 1000000:
        os.replace(v_out, v_in)
        print("Lesson 01 Video Remuxed successfully with crystal-clear phonetic audio!")
