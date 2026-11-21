#!/usr/bin/env python3
"""Stage 1+2: Build the unified theatrical Bengali screenplay and generate
continuous master TTS blocks (one per character) via Google AI Studio
gemini-3.8-flash-tts with responseModalities=["AUDIO"].

Batching protocol: exactly ONE master take per character (no fragmented
line-by-line calls). Steve -> Orus (male), Maggie -> Aoede (female/puppet).
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tts_client import call_tts, save_audio

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPTS = os.path.join(ROOT, "scripts")
TAKES = os.path.join(ROOT, "audio_takes", "mistral_google_studio_masters")
LOG = os.path.join(ROOT, "audio_takes", "mistral_generation_log.txt")

MASTER_SCREENPLAY = os.path.join(SCRIPTS, "master_bangla_screenplay_script.json")
UNIFIED_OUT = os.path.join(SCRIPTS, "mistral_pipeline", "mistral_unified_screenplay.json")

PAUSE = "\n\n"  # calibrated separator: reliably yields >=0.5 s clean silence between phrases


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    os.makedirs(TAKES, exist_ok=True)
    with open(MASTER_SCREENPLAY, encoding="utf-8") as f:
        cues = json.load(f)

    steve_cues = [c for c in cues if c["speaker"] == "Steve"]
    maggie_cues = [c for c in cues if c["speaker"] == "Maggie"]
    log(f"Loaded {len(cues)} timing cues ({len(steve_cues)} Steve / {len(maggie_cues)} Maggie)")

    # ---- Unified theatrical screenplay (both characters, burst annotations) ----
    unified = {
        "project": "Steve and Maggie | Learn the Senses (School Stories)",
        "video": "raw_sources/source_video.mp4",
        "duration_seconds": 213.53,
        "target_language": "bn-BD",
        "voice_engine": "Google AI Studio gemini-3.8-flash-tts, responseModalities=[AUDIO]",
        "casting": {
            "Steve": {"voice": "Orus", "gender": "male",
                      "character": "Enthusiastic comedic teacher; cheers, gasps, screams, laughs"},
            "Maggie": {"voice": "Aoede", "gender": "female_puppet",
                       "character": "High-pitched mischievous magpie puppet; giggles, teasing squawks"},
        },
        "vocal_burst_legend": {
            "<laugh>": "ハhahaha burst -> হা হা হা! / হихихি!",
            "<gasp>": "comic shock inhale -> আরেহ্! ওরেব্বাবা!",
            "<cheer>": "joyful exclamation -> আরে বাহ্!",
            "<scream>": "loud cartoon scream -> আআাহ্!",
            "<groan>": "strain/pain groan ->ウহুহুহু!",
            "<sigh>": "theatrical sigh -> ওহ্ না...",
        },
        "master_blocks": {
            "Steve": {
                "voice": "Orus",
                "phrases": [c["google_tts_prompt"] for c in steve_cues],
                "full_text": PAUSE.join(c["google_tts_prompt"] for c in steve_cues),
            },
            "Maggie": {
                "voice": "Aoede",
                "phrases": [c["google_tts_prompt"] for c in maggie_cues],
                "full_text": PAUSE.join(c["google_tts_prompt"] for c in maggie_cues),
            },
        },
        "cues": cues,
    }
    with open(UNIFIED_OUT, "w", encoding="utf-8") as f:
        json.dump(unified, f, ensure_ascii=False, indent=2)
    log(f"Unified screenplay written -> {os.path.relpath(UNIFIED_OUT, ROOT)}")

    # ---- Stage 2: one continuous master take per character ----
    archive = os.path.join(TAKES, "archive_v1_ellipsis_separator")
    jobs = [
        ("Steve", "Orus", unified["master_blocks"]["Steve"]["full_text"],
         os.path.join(TAKES, "steve_master_take_mistral_google.wav")),
        ("Maggie", "Aoede", unified["master_blocks"]["Maggie"]["full_text"],
         os.path.join(TAKES, "maggie_master_take_mistral_google.wav")),
    ]
    # preserve any earlier takes instead of overwriting (versioning rule)
    for _, _, _, out in jobs:
        if os.path.exists(out):
            os.makedirs(archive, exist_ok=True)
            dst = os.path.join(archive, os.path.basename(out))
            if not os.path.exists(dst):
                os.replace(out, dst)
                log(f"Archived previous take -> {os.path.relpath(dst, ROOT)}")
    for name, voice, text, out in jobs:
        log(f"{name}: generating ONE master take ({len(text)} chars, voice={voice})")
        t0 = time.time()
        pcm, rate, meta = call_tts(text, voice)
        save_audio(pcm, rate, out)
        log(f"{name}: master saved -> {os.path.relpath(out, ROOT)} "
            f"({meta['bytes']} bytes, {meta['bytes']/2/rate:.1f}s @ {rate}Hz, mime={meta['mime']}, "
            f"attempt={meta['attempt']}, {time.time()-t0:.1f}s wall)")

    log("Master take generation complete.")


if __name__ == "__main__":
    main()
