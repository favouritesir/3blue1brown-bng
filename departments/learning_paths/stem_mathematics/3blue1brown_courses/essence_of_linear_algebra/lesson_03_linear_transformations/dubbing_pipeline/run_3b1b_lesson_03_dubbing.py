"""
3Blue1Brown - Lesson 03: Linear Transformations and Matrices
Natural Bangla Dubbing & Music-Free Audio Pipeline
Bangla Resource Factory (BRF)
Approved by: Studio Director (CEO)
"""

import os
import sys
import json
import time
import shutil
import asyncio
import subprocess
from pathlib import Path
import edge_tts

BASE_DIR = Path(__file__).resolve().parent
SCRIPT_JSON = BASE_DIR / "3b1b_lesson_03_bangla_master_script.json"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp_audio_chunks"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

VOICE_ID = "bn-BD-PradeepNeural"
FINAL_MASTER_WAV = OUTPUT_DIR / "3b1b_lesson_03_bangla_dubbed_master.wav"
FINAL_MASTER_MP3 = OUTPUT_DIR / "3b1b_lesson_03_bangla_dubbed_master.mp3"
AUDIT_REPORT = OUTPUT_DIR / "audio_pipeline_report.json"


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


async def generate_single_tts(cue, sem):
    cid = cue["id"]
    text = cue["bn"]
    raw_mp3 = TEMP_DIR / f"raw_cue_{cid:03d}.mp3"
    
    async with sem:
        for attempt in range(5):
            try:
                communicator = edge_tts.Communicate(text, VOICE_ID)
                await communicator.save(str(raw_mp3))
                if raw_mp3.exists() and raw_mp3.stat().st_size > 500:
                    return cid, True
                else:
                    if raw_mp3.exists():
                        raw_mp3.unlink()
            except Exception as e:
                print(f"[!] Cue {cid} TTS attempt {attempt+1} failed: {e}")
                await asyncio.sleep(1.0)
        return cid, False


async def batch_generate_tts(cues):
    print(f"[*] Checking Edge-TTS synthesis for {len(cues)} cues using '{VOICE_ID}' (Governor: Concurrency=2)...")
    sem = asyncio.Semaphore(2)  # Strictly governed concurrency for low RAM usage
    missing_cues = []
    for c in cues:
        raw_mp3 = TEMP_DIR / f"raw_cue_{c['id']:03d}.mp3"
        if not raw_mp3.exists() or raw_mp3.stat().st_size < 100:
            missing_cues.append(c)
    if missing_cues:
        print(f"  -> Generating TTS for {len(missing_cues)} cues...")
        tasks = [generate_single_tts(c, sem) for c in missing_cues]
        results = await asyncio.gather(*tasks)
        succeeded = sum(1 for _, ok in results if ok)
        print(f"[*] TTS generation completed: {succeeded}/{len(missing_cues)} succeeded.")
    else:
        print("  -> All cues already generated in cache.")


def process_and_align_cues(cues):
    print("[*] Processing time-stretching and timeline assembly...")
    entries = []
    current_time = 0.0
    concat_list_file = TEMP_DIR / "timeline_concat_list.txt"

    for cue in cues:
        cid = cue["id"]
        start = cue["start"]
        end = cue["end"]
        target_dur = cue["duration"]
        
        raw_mp3 = TEMP_DIR / f"raw_cue_{cid:03d}.mp3"
        timed_wav = TEMP_DIR / f"timed_cue_{cid:03d}.wav"
        
        # 1. Insert silence padding if needed before this cue
        silence_dur = max(0.0, start - current_time)
        if silence_dur > 0.04:
            silence_wav = TEMP_DIR / f"silence_before_{cid:03d}.wav"
            cmd_silence = f'ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=mono -t {silence_dur:.3f} -acodec pcm_s16le "{silence_wav}"'
            run_cmd(cmd_silence)
            entries.append(silence_wav)
            current_time += silence_dur
            
        # 2. Check raw duration and adjust tempo
        raw_dur = get_duration(raw_mp3)
        if raw_dur <= 0:
            raw_dur = target_dur
            
        tempo = raw_dur / target_dur
        tempo = max(0.85, min(1.35, tempo))
        
        # High quality atempo filter + speech presence EQ
        cmd_tempo = (
            f'ffmpeg -y -i "{raw_mp3}" -filter_complex '
            f'"atempo={tempo:.4f},volume=1.05,highpass=f=80,lowpass=f=12000" '
            f'-ar 44100 -ac 1 -acodec pcm_s16le "{timed_wav}"'
        )
        run_cmd(cmd_tempo)
        
        actual_timed_dur = get_duration(timed_wav)
        entries.append(timed_wav)
        current_time += actual_timed_dur

    with open(concat_list_file, "w", encoding="utf-8") as f:
        for p in entries:
            escaped_path = str(p.resolve()).replace("\\", "/")
            f.write(f"file '{escaped_path}'\n")

    print(f"[*] Concatenating master audio stream ({len(entries)} segments, ~{current_time/60:.2f} mins)...")
    cmd_concat = (
        f'ffmpeg -y -f concat -safe 0 -i "{concat_list_file}" '
        f'-filter_complex "dynaudnorm=p=0.9:m=10.0:s=12.0" '
        f'-ar 44100 -ac 2 "{FINAL_MASTER_WAV}"'
    )
    run_cmd(cmd_concat)

    print(f"[*] Compressing high-fidelity MP3 master (192 kbps, pure halal vocal track)...")
    cmd_mp3 = f'ffmpeg -y -i "{FINAL_MASTER_WAV}" -b:a 192k "{FINAL_MASTER_MP3}"'
    run_cmd(cmd_mp3)

    master_dur = get_duration(FINAL_MASTER_WAV)
    print(f"[+] Dubbed Master Rendered Successfully: {FINAL_MASTER_WAV}")
    print(f"    Total Runtime: {master_dur:.2f} seconds ({master_dur/60:.2f} minutes)")

    report = {
        "lesson": "03_linear_transformations",
        "voice": VOICE_ID,
        "total_cues": len(cues),
        "total_segments_stitched": len(entries),
        "runtime_seconds": master_dur,
        "runtime_minutes": round(master_dur / 60, 2),
        "halal_pure_vocal": True,
        "background_music": "none",
        "output_wav": str(FINAL_MASTER_WAV),
        "output_mp3": str(FINAL_MASTER_MP3)
    }
    with open(AUDIT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"[+] Audio Audit Report generated at: {AUDIT_REPORT}")


async def main():
    print("=== BANGLA RESOURCE FACTORY: 3B1B LESSON 03 DUBBING PIPELINE ===")
    with open(SCRIPT_JSON, "r", encoding="utf-8") as f:
        cues = json.load(f)

    await batch_generate_tts(cues)
    process_and_align_cues(cues)
    print("=== PIPELINE EXECUTION COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(main())
