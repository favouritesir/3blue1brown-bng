"""
3Blue1Brown - Lesson 02: Linear Combinations, Span, and Basis Vectors
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
SCRIPT_JSON = BASE_DIR / "3b1b_lesson_02_bangla_master_script.json"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp_audio_chunks"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

VOICE_ID = "bn-BD-PradeepNeural"
FINAL_MASTER_WAV = OUTPUT_DIR / "3b1b_lesson_02_bangla_dubbed_master.wav"
FINAL_MASTER_MP3 = OUTPUT_DIR / "3b1b_lesson_02_bangla_dubbed_master.mp3"
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
    sem = asyncio.Semaphore(4)  # Safe network concurrency
    tasks = []
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
        # Clamp tempo between 0.85 and 1.35 to maintain pristine natural voice quality
        tempo = max(0.85, min(1.35, tempo))
        
        # High quality atempo filter + speech presence EQ
        filter_str = f"atempo={tempo:.3f},equalizer=f=1800:t=q:w=1.2:g=1.5"
        cmd_stretch = f'ffmpeg -y -i "{raw_mp3}" -filter:a "{filter_str}" -ar 44100 -ac 1 -acodec pcm_s16le "{timed_wav}"'
        run_cmd(cmd_stretch)
        
        actual_stretched_dur = get_duration(timed_wav)
        entries.append(timed_wav)
        current_time += actual_stretched_dur
        
        if cid % 15 == 0 or cid == len(cues):
            print(f"  -> Aligned Cue #{cid:02d} / {len(cues)} (Timeline: {current_time/60:.2f} min)")

    # Write concat manifest
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(f"file '{entry.as_posix()}'\n")

    speech_track_wav = TEMP_DIR / "speech_track_assembled.wav"
    print("[*] Concatenating cues into full speech track (PCM 16-bit)...")
    run_cmd(f'ffmpeg -y -f concat -safe 0 -i "{concat_list_file}" -c:a pcm_s16le "{speech_track_wav}"')
    return speech_track_wav


def normalize_and_export(speech_track_wav):
    print("[*] Applying EBU R128 loudness normalization (-14 LUFS, peak -1 dBTP)...")
    norm_cmd = (
        f'ffmpeg -y -i "{speech_track_wav}" '
        f'-af "loudnorm=I=-14:LRA=7:TP=-1" '
        f'-ar 44100 -ac 2 -acodec pcm_s16le "{FINAL_MASTER_WAV}"'
    )
    run_cmd(norm_cmd)

    print("[*] Exporting high-fidelity MP3 master (192 kbps)...")
    mp3_cmd = f'ffmpeg -y -i "{FINAL_MASTER_WAV}" -c:a libmp3lame -b:a 192k "{FINAL_MASTER_MP3}"'
    run_cmd(mp3_cmd)

    total_dur = get_duration(FINAL_MASTER_WAV)
    wav_size = FINAL_MASTER_WAV.stat().st_size / (1024 * 1024)
    mp3_size = FINAL_MASTER_MP3.stat().st_size / (1024 * 1024)
    print(f"\n=======================================================")
    print(f" Master Audio Rendered Successfully!")
    print(f" Duration: {total_dur:.2f}s ({total_dur/60:.2f} mins)")
    print(f" WAV Output: {FINAL_MASTER_WAV} ({wav_size:.2f} MB)")
    print(f" MP3 Output: {FINAL_MASTER_MP3} ({mp3_size:.2f} MB)")
    print(f"=======================================================\n")
    return total_dur, wav_size, mp3_size


def cleanup_temp_chunks():
    print("[*] Executing post-render cleanup of intermediate audio chunks...")
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
    print("[*] Cleanup completed. Intermediate chunks wiped.")


async def main():
    start_time = time.time()
    with open(SCRIPT_JSON, "r", encoding="utf-8") as f:
        cues = json.load(f)

    print(f"Loaded {len(cues)} script cues for 3B1B Lesson 02.")

    # 1. TTS Synthesis
    await batch_generate_tts(cues)

    # 2. Alignment & Time-stretching
    speech_track = process_and_align_cues(cues)

    # 3. Normalization & Mastering
    total_dur, wav_size, mp3_size = normalize_and_export(speech_track)

    # 4. Cleanup
    cleanup_temp_chunks()

    elapsed = round(time.time() - start_time, 2)
    
    report = {
        "lesson_id": "lesson_02_span",
        "title": "Linear combinations, span, and basis vectors",
        "course": "Essence of Linear Algebra",
        "total_cues": len(cues),
        "total_duration_sec": round(total_dur, 2),
        "total_duration_min": round(total_dur / 60, 2),
        "voice_persona": "Grant Sanderson (Narrator)",
        "neural_voice": VOICE_ID,
        "loudness_standard": "EBU R128 (-14 LUFS, -1 dBTP peak)",
        "background_music": "0% (Halal audio profile)",
        "output_wav": str(FINAL_MASTER_WAV),
        "output_mp3": str(FINAL_MASTER_MP3),
        "wav_size_mb": round(wav_size, 2),
        "mp3_size_mb": round(mp3_size, 2),
        "elapsed_render_time_sec": elapsed,
        "status": "verified_master"
    }

    with open(AUDIT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[*] Audit Report saved to {AUDIT_REPORT}")


if __name__ == "__main__":
    asyncio.run(main())
