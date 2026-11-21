#!/usr/bin/env python3
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tts_client import call_tts, save_audio

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TAKES = os.path.join(ROOT, "audio_takes", "v3_authentic_masters")
LOG = os.path.join(ROOT, "audio_takes", "v3_generation_log.txt")
SCREENPLAY_V3 = os.path.join(ROOT, "scripts", "master_screenplay_v3_authentic.json")

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def main():
    os.makedirs(TAKES, exist_ok=True)
    with open(SCREENPLAY_V3, "r", encoding="utf-8") as f:
        sp = json.load(f)

    steve_text = sp["master_continuous_blocks"]["Steve"]["full_text"]
    maggie_text = sp["master_continuous_blocks"]["Maggie"]["full_text"]

    jobs = [
        ("Steve", "Orus", steve_text, os.path.join(TAKES, "steve_master_take_v3_authentic.wav")),
        ("Maggie", "Aoede", maggie_text, os.path.join(TAKES, "maggie_master_take_v3_authentic.wav"))
    ]

    for name, voice, text, out in jobs:
        log(f"{name}: generating continuous master take ({len(text)} chars, voice={voice})")
        t0 = time.time()
        pcm, rate, meta = call_tts(text, voice)
        save_audio(pcm, rate, out)
        log(f"{name}: master saved -> {out} "
            f"({meta['bytes']} bytes, {meta['bytes']/2/rate:.1f}s @ {rate}Hz, "
            f"attempt={meta['attempt']}, {time.time()-t0:.1f}s wall)")

    log("V3 Master take generation complete!")

if __name__ == "__main__":
    main()
