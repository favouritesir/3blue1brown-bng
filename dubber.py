"""
Bangla Video Dubbing Studio - Automated Pipeline
Features:
1. YouTube / Local Video Input
2. Subtitle extraction (English / Source language)
3. Smart sentence grouping & Bengali Translation (Multi-tier resilient translation)
4. Edge-TTS Audio Generation (Neural Voice bn-BD-PradeepNeural / bn-BD-NabanitaNeural)
5. Precision Time-stretching & Sync with FFmpeg
6. Optional Audio Ducking / Background Mix or Clean Dub Track
7. Final Video Export (Lossless Video Copy)
"""

import os
import sys
import json
import re
import asyncio
import subprocess
import argparse
import urllib.request
import urllib.parse
from pathlib import Path
import edge_tts
from deep_translator import MyMemoryTranslator

# Configuration Defaults
DEFAULT_VOICE = "bn-BD-PradeepNeural"  # bn-BD-PradeepNeural (Male) or bn-BD-NabanitaNeural (Female)
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"
DOWNLOAD_DIR = BASE_DIR / "downloads"

# Audio Engine Architecture:
# - 'edge_tts'   : Single narrator, zero cost, standard tutorial delivery
# - 'ai_studio'  : Gemini 2.0 Multimodal Audio (Emotion, expressive pitch, multi-character dialogs)
# - 'flow_music' : Ambient sound design, background track & flow audio
AUDIO_ENGINE = "edge_tts"

for p in [TEMP_DIR, OUTPUT_DIR, DOWNLOAD_DIR]:
    p.mkdir(parents=True, exist_ok=True)


def run_cmd(cmd):
    """Run shell command safely"""
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\nError: {res.stderr}")
    return res.stdout


def get_audio_duration(file_path):
    """Get duration of audio file in seconds using ffprobe"""
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
    try:
        out = run_cmd(cmd).strip()
        return float(out)
    except Exception:
        return 0.0


def parse_vtt_time(timestr):
    """Convert HH:MM:SS.mmm or MM:SS.mmm to seconds"""
    parts = timestr.strip().split(":")
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h = 0
        m, s = parts
    else:
        return 0.0
    return float(h) * 3600 + float(m) * 60 + float(s)


def parse_raw_json(json_file):
    """Parse raw YouTube timedtext JSON (or standard transcript format) and group into natural sentences"""
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    events = data.get("events", []) if isinstance(data, dict) else data
    raw_cues = []
    for ev in events:
        if isinstance(ev, dict) and "segs" in ev:
            t_start = ev.get("tStartMs", 0) / 1000.0
            dur = ev.get("dDurationMs", 0) / 1000.0
            text = "".join([s.get("utf8", "") for s in ev["segs"]]).strip()
            text = text.replace("\n", " ").strip()
            if text and dur > 0:
                raw_cues.append({"start": t_start, "end": t_start + dur, "duration": dur, "text": text})
        elif isinstance(ev, dict) and "time" in ev and "text" in ev:
            # Simple timestamped format
            raw_cues.append({"start": 0, "end": 0, "duration": 3.0, "text": ev["text"]})

    # Group into natural spoken sentences (respecting speaker change '>>' and terminal punctuation)
    merged = []
    for cue in raw_cues:
        if not merged:
            merged.append(dict(cue))
            continue
        last = merged[-1]
        gap = cue["start"] - last["end"]
        is_speaker_change = cue["text"].startswith(">>") or (last["text"].startswith(">>") and not cue["text"].startswith(">>"))
        if not is_speaker_change and gap < 1.5 and (cue["end"] - last["start"]) < 9.0 and not last["text"].endswith((".", "?", "!")):
            last["end"] = cue["end"]
            last["duration"] = last["end"] - last["start"]
            last["text"] += " " + cue["text"]
        else:
            merged.append(dict(cue))

    return merged


def parse_vtt(vtt_file):
    """Parse WebVTT file and extract clean cues with timestamps"""
    with open(vtt_file, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()
    cues = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "-->" in line:
            times = line.split("-->")
            start = parse_vtt_time(times[0].split()[0])
            end = parse_vtt_time(times[1].split()[0])

            i += 1
            text_lines = []
            while i < len(lines) and lines[i].strip() != "" and "-->" not in lines[i]:
                cleaned = re.sub(r"<[^>]+>", "", lines[i]).strip()
                if cleaned and cleaned not in text_lines:
                    text_lines.append(cleaned)
                i += 1

            full_text = " ".join(text_lines).strip()
            if full_text and end > start:
                cues.append({
                    "start": start,
                    "end": end,
                    "duration": end - start,
                    "text": full_text
                })
        else:
            i += 1

    # Merge consecutive cues if close and short (< 5.5s) to form natural spoken sentences
    merged = []
    for cue in cues:
        if not merged:
            merged.append(cue)
            continue
        last = merged[-1]
        if cue["start"] - last["end"] < 0.8 and (cue["end"] - last["start"]) < 5.5:
            last["end"] = cue["end"]
            last["duration"] = last["end"] - last["start"]
            last["text"] += " " + cue["text"]
        else:
            merged.append(cue)
    return merged


def download_youtube(url):
    """Download video and English subtitles using yt-dlp"""
    print(f"[*] Downloading video and subtitles from: {url}")
    out_template = str(DOWNLOAD_DIR / "%(id)s.%(ext)s")

    cmd = (
        f'python -m yt_dlp --write-auto-subs --write-subs --sub-lang "en.*,en" '
        f'--sub-format vtt --skip-unavailable-fragments '
        f'-f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" '
        f'-o "{out_template}" "{url}"'
    )
    run_cmd(cmd)

    mp4_files = sorted(DOWNLOAD_DIR.glob("*.mp4"), key=os.path.getmtime, reverse=True)
    vtt_files = sorted(DOWNLOAD_DIR.glob("*.vtt"), key=os.path.getmtime, reverse=True)

    if not mp4_files:
        raise FileNotFoundError("Video download failed, no .mp4 found.")
    video_file = mp4_files[0]
    sub_file = vtt_files[0] if vtt_files else None
    return video_file, sub_file


def translate_text_resilient(text):
    """
    Multi-tier resilient translation engine:
    Tier 1: Google Translate client gtx (Fast, resilient, zero auth required)
    Tier 2: MyMemoryTranslator (en-GB -> bn-IN)
    Tier 3: Original text fallback
    """
    clean_text = text.strip()
    if not clean_text:
        return clean_text

    # Tier 1: Google gtx endpoint
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = "https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode({
        "client": "gtx",
        "sl": "en",
        "tl": "bn",
        "dt": "t",
        "q": clean_text
    })
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and data[0]:
                translated = "".join([segment[0] for segment in data[0] if segment and segment[0]]).strip()
                if translated:
                    return translated
    except Exception as e:
        print(f"  [!] Tier 1 translation failed: {e}. Falling back to Tier 2 (MyMemory)...")

    # Tier 2: MyMemory
    try:
        mem_trans = MyMemoryTranslator(source="en-GB", target="bn-IN")
        res = mem_trans.translate(clean_text)
        if res and res.strip():
            return res.strip()
    except Exception as e:
        print(f"  [!] Tier 2 translation failed: {e}. Falling back to raw text.")

    # Tier 3: Fallback
    return clean_text


def translate_cues(cues):
    """Translate cues to natural Bengali with persistent disk caching"""
    cache_file = DOWNLOAD_DIR / "translations_cache.json"
    cache = {}
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
            print(f"[*] Loaded {len(cache)} cached translations.")
        except Exception:
            cache = {}

    print(f"[*] Translating {len(cues)} segments to Bengali...")
    for i, cue in enumerate(cues):
        text_key = cue["text"].strip()
        if text_key in cache:
            cue["bn_text"] = cache[text_key]
        else:
            cue["bn_text"] = translate_text_resilient(text_key)
            cache[text_key] = cue["bn_text"]
            if i % 5 == 0 or i == len(cues) - 1:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)

        print(f"  [{i+1}/{len(cues)}] {cue['text'][:35]}... -> {cue['bn_text'][:35]}...")

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    return cues


async def generate_speech_segment(text, voice, out_path, sem):
    """Generate audio for a single text segment using edge-tts with rate limiting semaphore"""
    async with sem:
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(out_path)
        except Exception as e:
            print(f"  [!] Edge-TTS error for '{text[:20]}...': {e}")


async def generate_all_speech(cues, default_voice):
    """Generate TTS audio files concurrently for all translated cues with character voice assignment"""
    print(f"[*] Concurrently generating Bengali neural voices for {len(cues)} segments...")
    sem = asyncio.Semaphore(10)
    tasks = []

    for i, cue in enumerate(cues):
        audio_path = TEMP_DIR / f"seg_{i:04d}.mp3"
        raw_text = cue["text"].strip()
        # Multi-character voice detection:
        # If line starts with '>>' or dialog quote, assign female or distinct agent voice
        if raw_text.startswith(">>") or raw_text.startswith('"') or "agent" in raw_text.lower()[:15]:
            char_voice = "bn-BD-NabanitaNeural"
        else:
            char_voice = default_voice

        cue["voice"] = char_voice
        cue["audio_path"] = str(audio_path)
        # Clean text for TTS (strip leading >> or quotes so pronunciation is natural)
        clean_bn = re.sub(r'^[>"\s]+', '', cue["bn_text"]).strip()
        tasks.append(generate_speech_segment(clean_bn or cue["bn_text"], char_voice, str(audio_path), sem))

    await asyncio.gather(*tasks)

    # Compute actual durations
    for cue in cues:
        if os.path.exists(cue["audio_path"]):
            cue["actual_audio_dur"] = get_audio_duration(cue["audio_path"])
        else:
            cue["actual_audio_dur"] = cue["duration"]


def create_silence(duration_sec, out_path):
    """Generate exact silence wav file"""
    if duration_sec <= 0.01:
        return
    cmd = f'ffmpeg -y -v error -f lavfi -i anullsrc=r=24000:cl=mono -t {duration_sec:.3f} -acodec pcm_s16le "{out_path}"'
    run_cmd(cmd)


def build_dubbed_audio(cues, total_video_duration, out_audio_path):
    """
    Assemble dubbed speech audio into a single timeline matching the video duration.
    Uses ffmpeg concat demuxer with precision silence padding.
    Supports chainable atempo filtering if speed adjustment is needed.
    """
    print("[*] Synchronizing audio timeline with video timestamps...")
    concat_list_path = TEMP_DIR / "concat_list.txt"
    entries = []

    current_time = 0.0

    for i, cue in enumerate(cues):
        in_audio = cue["audio_path"]
        target_dur = cue["duration"]
        actual_dur = cue["actual_audio_dur"]

        timed_audio = TEMP_DIR / f"timed_{i:04d}.wav"

        # Speed up if actual duration exceeds segment window (capped at 1.45x)
        if actual_dur > target_dur and target_dur > 0.5:
            speed = min(actual_dur / target_dur, 1.45)
            # Chain atempo if ever needed (atempo accepts 0.5 - 2.0)
            if speed > 2.0:
                atempo_filter = f"atempo=2.0,atempo={speed/2.0:.2f}"
            else:
                atempo_filter = f"atempo={speed:.2f}"
            cmd = f'ffmpeg -y -v error -i "{in_audio}" -filter:a "{atempo_filter}" -ar 24000 -ac 1 "{timed_audio}"'
        else:
            cmd = f'ffmpeg -y -v error -i "{in_audio}" -ar 24000 -ac 1 "{timed_audio}"'

        run_cmd(cmd)
        timed_dur = get_audio_duration(str(timed_audio))

        # Check gap between current timeline and this cue's start
        gap = cue["start"] - current_time
        if gap > 0.05:
            silence_path = TEMP_DIR / f"silence_{i:04d}.wav"
            create_silence(gap, str(silence_path))
            if silence_path.exists():
                entries.append(f"file '{silence_path.resolve().as_posix()}'")
                current_time += gap

        entries.append(f"file '{timed_audio.resolve().as_posix()}'")
        current_time += timed_dur

    # Pad remaining silence up to total_video_duration
    if total_video_duration > current_time:
        rem_gap = total_video_duration - current_time
        rem_silence = TEMP_DIR / "silence_final.wav"
        create_silence(rem_gap, str(rem_silence))
        if rem_silence.exists():
            entries.append(f"file '{rem_silence.resolve().as_posix()}'")

    with open(concat_list_path, "w", encoding="utf-8") as f:
        f.write("\n".join(entries))

    concat_cmd = f'ffmpeg -y -v error -f concat -safe 0 -i "{concat_list_path}" -c:a pcm_s16le "{out_audio_path}"'
    run_cmd(concat_cmd)
    print(f"[*] Dubbed audio track assembled: {out_audio_path}")


def merge_video_audio(video_file, audio_file, output_file, mix_background=False):
    """Merge newly created Bengali audio track with original video (lossless copy)"""
    print(f"[*] Merging Bengali audio with original video...")
    if mix_background:
        # Background music/audio at 15% volume + Bengali speech track
        cmd = (
            f'ffmpeg -y -v error -i "{video_file}" -i "{audio_file}" '
            f'-filter_complex "[0:a]volume=0.15[bg];[bg][1:a]amix=inputs=2:duration=first[aout]" '
            f'-c:v copy -map 0:v:0 -map "[aout]" -c:a aac -b:a 192k -shortest "{output_file}"'
        )
    else:
        cmd = (
            f'ffmpeg -y -v error -i "{video_file}" -i "{audio_file}" '
            f'-c:v copy -c:a aac -b:a 192k -map 0:v:0 -map 1:a:0 '
            f'-shortest "{output_file}"'
        )
    run_cmd(cmd)
    print(f"[SUCCESS] Final Dubbed Video Created at:\n-> {output_file}")


def process_video(url_or_path, transcript_path=None, voice=DEFAULT_VOICE, mix_background=False, limit=0):
    """Main Orchestrator"""
    cues = None
    if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
        video_file, sub_file = download_youtube(url_or_path)
    else:
        video_file = Path(url_or_path)
        sub_file = None

    # Resolve transcript / cues
    if transcript_path and Path(transcript_path).exists():
        tp = Path(transcript_path)
        if tp.suffix.lower() == ".json":
            cues = parse_raw_json(tp)
        else:
            cues = parse_vtt(tp)
    elif sub_file and sub_file.exists():
        cues = parse_vtt(sub_file)
    else:
        # Check potential transcript files in downloads or next to video
        potential_jsons = [
            video_file.with_suffix(".json"),
            DOWNLOAD_DIR / "raw_transcript.json",
            DOWNLOAD_DIR / "transcript.json"
        ]
        for pj in potential_jsons:
            if pj.exists():
                print(f"[*] Found transcript file: {pj}")
                cues = parse_raw_json(pj)
                break

    if not cues:
        print("[!] No transcript or subtitles found. Please provide a video with captions or a transcript file.")
        return None

    if limit > 0:
        cues = cues[:limit]
        print(f"[*] Limiting to first {limit} cues for preview run.")

    print(f"[*] Total sentence cues to process: {len(cues)}")

    # 1. Translate Cues
    cues = translate_cues(cues)

    # 2. Generate Speech
    asyncio.run(generate_all_speech(cues, voice))

    # 3. Synchronize & Build Audio Track
    total_dur = get_audio_duration(str(video_file))
    final_audio = TEMP_DIR / "final_dubbed_bn.wav"
    build_dubbed_audio(cues, total_dur, str(final_audio))

    # 4. Merge into Final Output Video
    video_stem = Path(video_file).stem
    final_video = OUTPUT_DIR / f"{video_stem}_Bangla_Dubbed.mp4"
    merge_video_audio(str(video_file), str(final_audio), str(final_video), mix_background=mix_background)

    return str(final_video)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bangla Video Dubbing Studio")
    parser.add_argument("source", help="YouTube URL or local video file path")
    parser.add_argument("--transcript", default=None, help="Path to transcript (JSON or VTT)")
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help="Voice name (e.g., bn-BD-PradeepNeural, bn-BD-NabanitaNeural)"
    )
    parser.add_argument(
        "--mix-background",
        action="store_true",
        help="Keep original background audio mixed at 15 percent volume"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of cues for rapid test preview"
    )
    args = parser.parse_args()

    process_video(
        args.source,
        transcript_path=args.transcript,
        voice=args.voice,
        mix_background=args.mix_background,
        limit=args.limit
    )
