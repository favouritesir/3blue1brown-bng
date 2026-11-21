"""
High-Fidelity Bengali Video Dubber (Natural Script & Halal Pure Voice)
"""
import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
import edge_tts

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp_dub"
OUTPUT_DIR = BASE_DIR / "output"
DOWNLOADS_DIR = BASE_DIR / "downloads"

TEMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_SRC = DOWNLOADS_DIR / "i0p-B-_kr5c.webm"
OUTPUT_VIDEO = OUTPUT_DIR / "700_AI_Agents_Escaped_Bangla_Dubbed.mp4"
SCRIPT_JSON = BASE_DIR / "master_bangla_script.json"


def run_cmd(cmd):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\nError: {res.stderr}")
    return res.stdout


def get_audio_duration(file_path):
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
    try:
        out = run_cmd(cmd).strip()
        return float(out)
    except Exception:
        return 0.0


async def generate_tts(text, voice, out_file, sem, idx):
    async with sem:
        for attempt in range(3):
            try:
                communicator = edge_tts.Communicate(text, voice)
                await communicator.save(str(out_file))
                if os.path.exists(out_file) and os.path.getsize(out_file) > 100:
                    return True
            except Exception as e:
                print(f"[{idx}] TTS retry {attempt+1}: {e}")
                await asyncio.sleep(0.5)
        return False


async def batch_generate_audio(script_items):
    sem = asyncio.Semaphore(10)
    tasks = []
    print(f"Generating TTS for {len(script_items)} segments...")
    for item in script_items:
        idx = item["id"]
        out_mp3 = TEMP_DIR / f"raw_{idx:04d}.mp3"
        tasks.append(generate_tts(item["bn"], item["voice"], out_mp3, sem, idx))
    
    results = await asyncio.gather(*tasks)
    success_count = sum(1 for r in results if r)
    print(f"TTS generation complete: {success_count}/{len(script_items)} succeeded.")
    return success_count == len(script_items)


def build_audio_track(script_items):
    print("Synchronizing and assembling audio track...")
    concat_list = TEMP_DIR / "concat_list.txt"
    entries = []
    
    current_time = 0.0
    
    for item in script_items:
        idx = item["id"]
        start = item["start"]
        end = item["end"]
        target_dur = item["duration"]
        
        raw_mp3 = TEMP_DIR / f"raw_{idx:04d}.mp3"
        timed_wav = TEMP_DIR / f"timed_{idx:04d}.wav"
        
        # 1. Silence padding if needed
        silence_dur = max(0.0, start - current_time)
        if silence_dur > 0.04:
            silence_wav = TEMP_DIR / f"silence_{idx:04d}.wav"
            run_cmd(f'ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=mono -t {silence_dur:.3f} -q:a 9 -acodec pcm_s16le "{silence_wav}"')
            entries.append(silence_wav)
            current_time += silence_dur
        
        # 2. Measure actual duration
        actual_dur = get_audio_duration(raw_mp3)
        if actual_dur <= 0:
            actual_dur = target_dur
        
        # 3. Tempo adjustment
        tempo = actual_dur / target_dur
        tempo = max(0.85, min(1.40, tempo))
        
        filter_str = f"atempo={tempo:.3f}"
        run_cmd(f'ffmpeg -y -i "{raw_mp3}" -filter:a "{filter_str}" -ar 44100 -ac 1 -acodec pcm_s16le "{timed_wav}"')
        
        new_dur = get_audio_duration(timed_wav)
        entries.append(timed_wav)
        current_time += new_dur
        
        if idx % 20 == 0 or idx == len(script_items) - 1:
            print(f"Processed segment #{idx:03d} (timeline: {current_time/60:.2f} min)")
    
    # Write concat list
    with open(concat_list, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(f"file '{entry.as_posix()}'\n")
            
    final_master_wav = TEMP_DIR / "master_dubbed_audio.wav"
    print("Concatenating all segments into master audio track...")
    run_cmd(f'ffmpeg -y -f concat -safe 0 -i "{concat_list}" -c copy "{final_master_wav}"')
    
    final_dur = get_audio_duration(final_master_wav)
    print(f"Master audio track generated: {final_dur:.2f}s ({final_dur/60:.2f} mins)")
    return final_master_wav


def mux_video(final_master_wav):
    print("Muxing final video with master Bangla audio track (Pure Halal - 0% music)...")
    cmd = (
        f'ffmpeg -y -i "{VIDEO_SRC}" -i "{final_master_wav}" '
        f'-map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -b:a 192k -shortest "{OUTPUT_VIDEO}"'
    )
    run_cmd(cmd)
    
    if OUTPUT_VIDEO.exists():
        size_mb = OUTPUT_VIDEO.stat().st_size / (1024 * 1024)
        print(f"\n==========================================")
        print(f"SUCCESS: Dubbed video generated successfully!")
        print(f"Output: {OUTPUT_VIDEO}")
        print(f"File size: {size_mb:.2f} MB")
        print(f"==========================================\n")
    else:
        raise RuntimeError("Failed to generate final video output!")


async def main():
    with open(SCRIPT_JSON, "r", encoding="utf-8") as f:
        script_items = json.load(f)
        
    print(f"Loaded {len(script_items)} script cues.")
    
    # Step 1: Batch generate TTS
    await batch_generate_audio(script_items)
    
    # Step 2: Time-stretch & Concat
    master_wav = build_audio_track(script_items)
    
    # Step 3: Mux with original video
    mux_video(master_wav)


if __name__ == "__main__":
    asyncio.run(main())
