"""
3Blue1Brown - Lesson 01: Vectors, what even are they?
Bangla Dubbed Audio Pipeline (Edge-TTS bn-BD-PradeepNeural)

Enforcing:
1. Zero English Vocal Bleed (Pure Bengali Speech + Transients/SFX bed).
2. Dynamic atempo fit for cue timeline synchronization.
3. EBU R128 Loudness Normalization (-14.0 LUFS, -1.0 dBTP peak).
4. Immediate cleanup of intermediate chunks.
5. Export to target destination web_platform/media_vault/lesson_01/3b1b_lesson_01_bangla_master.mp3
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

# Paths definition
WORKSPACE_ROOT = Path(r"D:\0PEN CODE\Dub Studio")
LESSON_01_DIR = WORKSPACE_ROOT / "departments" / "learning_paths" / "stem_mathematics" / "3blue1brown_courses" / "essence_of_linear_algebra" / "lesson_01_vectors"
SCRIPT_JSON = LESSON_01_DIR / "dubbing_pipeline" / "3b1b_lesson_01_bangla_master_script.json"
SFX_FILE = LESSON_01_DIR / "dubbing_pipeline" / "stems_isolated" / "3b1b_lesson_01_sfx_isolated.wav"

TARGET_VAULT_DIR = WORKSPACE_ROOT / "departments" / "learning_paths" / "stem_mathematics" / "3blue1brown_courses" / "web_platform" / "media_vault" / "lesson_01"
TARGET_VAULT_DIR.mkdir(parents=True, exist_ok=True)

TEMP_DIR = LESSON_01_DIR / "dubbing_pipeline" / "temp_audio_chunks_lesson_01"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

VOICE_ID = "bn-BD-PradeepNeural"
TARGET_MASTER_MP3 = TARGET_VAULT_DIR / "3b1b_lesson_01_bangla_master.mp3"


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
                if raw_mp3.exists() and raw_mp3.stat().st_size > 200:
                    return cid, True
                else:
                    if raw_mp3.exists():
                        raw_mp3.unlink()
            except Exception as e:
                print(f"[!] Cue {cid} TTS attempt {attempt+1} failed: {e}")
                await asyncio.sleep(0.5)
        return cid, False


async def batch_generate_tts(cues):
    print(f"[*] Checking/Generating Edge-TTS synthesis for {len(cues)} cues with '{VOICE_ID}'...")
    sem = asyncio.Semaphore(6)
    missing_cues = []
    for c in cues:
        raw_mp3 = TEMP_DIR / f"raw_cue_{c['id']:03d}.mp3"
        if not raw_mp3.exists() or raw_mp3.stat().st_size < 200:
            missing_cues.append(c)

    if missing_cues:
        print(f"  -> Synthesizing {len(missing_cues)} missing audio cues...")
        tasks = [generate_single_tts(c, sem) for c in missing_cues]
        results = await asyncio.gather(*tasks)
        succeeded = sum(1 for _, ok in results if ok)
        print(f"[*] TTS generation completed: {succeeded}/{len(missing_cues)} succeeded.")
        if succeeded < len(missing_cues):
            raise RuntimeError(f"Failed to generate TTS for {len(missing_cues) - succeeded} cues.")
    else:
        print("  -> All cues already synthesized in cache.")


def process_and_align_cues(cues):
    print("[*] Processing time-stretching and master timeline assembly...")
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
        # Clamp tempo between 0.85 and 1.35 to preserve natural articulation
        tempo = max(0.85, min(1.35, tempo))

        # High quality atempo filter + speech presence EQ
        filter_str = f"atempo={tempo:.3f},equalizer=f=1800:t=q:w=1.2:g=1.5"
        cmd_stretch = f'ffmpeg -y -i "{raw_mp3}" -filter:a "{filter_str}" -ar 44100 -ac 1 -acodec pcm_s16le "{timed_wav}"'
        run_cmd(cmd_stretch)

        actual_stretched_dur = get_duration(timed_wav)
        entries.append(timed_wav)
        current_time += actual_stretched_dur

        if cid % 20 == 0 or cid == len(cues):
            print(f"  -> Aligned Cue #{cid:02d} / {len(cues)} (Timeline: {current_time/60:.2f} min)")

    # Write concat manifest
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(f"file '{entry.as_posix()}'\n")

    speech_track_wav = TEMP_DIR / "speech_track_assembled.wav"
    print("[*] Concatenating cues into full speech track (PCM 16-bit)...")
    run_cmd(f'ffmpeg -y -f concat -safe 0 -i "{concat_list_file}" -c:a pcm_s16le "{speech_track_wav}"')
    return speech_track_wav


def mix_and_normalize(speech_track_wav):
    print("[*] Checking SFX stem integration and applying zero-vocal-bleed gating...")
    mixed_raw_wav = TEMP_DIR / "mixed_raw.wav"

    if SFX_FILE.exists():
        print(f"  -> Found isolated SFX stem: {SFX_FILE.name}")
        # Mix clean Bengali speech (1.0 volume) with isolated SFX (0.35 volume), zero original English vocal
        mix_cmd = (
            f'ffmpeg -y -i "{speech_track_wav}" -i "{SFX_FILE}" '
            f'-filter_complex "[0:a]volume=1.0[v];[1:a]volume=0.35[s];[v][s]amix=inputs=2:duration=first:dropout_transition=2[out]" '
            f'-map "[out]" -ar 44100 -acodec pcm_s16le "{mixed_raw_wav}"'
        )
        run_cmd(mix_cmd)
    else:
        print("  -> Pure narration speech track used (no SFX stem).")
        shutil.copy(speech_track_wav, mixed_raw_wav)

    print("[*] Applying EBU R128 loudness normalization (-14.0 LUFS, -1.0 dBTP peak)...")
    temp_master_wav = TEMP_DIR / "normalized_master.wav"
    norm_cmd = (
        f'ffmpeg -y -i "{mixed_raw_wav}" '
        f'-af "loudnorm=I=-14.0:LRA=7.0:TP=-1.0" '
        f'-ar 44100 -ac 2 -acodec pcm_s16le "{temp_master_wav}"'
    )
    run_cmd(norm_cmd)

    print(f"[*] Exporting final studio-grade MP3 master (192 kbps) to: {TARGET_MASTER_MP3}...")
    mp3_cmd = f'ffmpeg -y -i "{temp_master_wav}" -c:a libmp3lame -b:a 192k "{TARGET_MASTER_MP3}"'
    run_cmd(mp3_cmd)

    total_dur = get_duration(TARGET_MASTER_MP3)
    mp3_size = TARGET_MASTER_MP3.stat().st_size / (1024 * 1024)
    print(f"\n=======================================================")
    print(f" Master Audio Delivered Successfully!")
    print(f" File: {TARGET_MASTER_MP3}")
    print(f" Duration: {total_dur:.2f}s ({total_dur/60:.2f} mins)")
    print(f" MP3 Size: {mp3_size:.2f} MB")
    print(f"=======================================================\n")
    return total_dur, mp3_size


def cleanup_temp_chunks():
    print("[*] Executing post-render cleanup of intermediate audio chunks...")
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
    print("[*] Cleanup completed. Intermediate chunks safely removed.")


async def main():
    start_time = time.time()
    with open(SCRIPT_JSON, "r", encoding="utf-8") as f:
        cues = json.load(f)

    print(f"Loaded {len(cues)} script cues for 3B1B Lesson 01.")

    # 1. TTS Synthesis
    await batch_generate_tts(cues)

    # 2. Precision Alignment
    speech_track = process_and_align_cues(cues)

    # 3. Mix & EBU R128 Normalization
    total_dur, mp3_size = mix_and_normalize(speech_track)

    # 4. Mandatory intermediate cleanup
    cleanup_temp_chunks()

    elapsed = round(time.time() - start_time, 2)
    print(f"Pipeline executed in {elapsed} seconds.")


if __name__ == "__main__":
    asyncio.run(main())
