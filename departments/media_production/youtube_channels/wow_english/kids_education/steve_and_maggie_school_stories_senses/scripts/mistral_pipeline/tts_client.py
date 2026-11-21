#!/usr/bin/env python3
"""Google AI Studio TTS client (gemini-3.8-flash-tts) for the Mistral Bengali dub pipeline.

Single master-block generation with responseModalities=["AUDIO"] and
prebuilt voiceConfig (Orus=Steve male, Aoede=Maggie female/puppet).
Retries 429/5xx with exponential backoff (reactive to rate-limit signal only).
"""
import base64
import json
import sys
import time
import urllib.request
import urllib.error

import os
API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL = "gemini-3.8-flash-tts"
ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent?key={API_KEY}"
)


def build_payload(text: str, voice: str) -> dict:
    return {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Speak the following Bengali dialogue as a single continuous "
                            "theatrical performance with natural laughter, gasps, cheers and "
                            "screams exactly as marked. Do not add any other words.\n\n"
                            + text
                        )
                    }
                ],
            }
        ],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {"voiceName": voice}
                }
            },
        },
    }


def call_tts(text: str, voice: str, max_retries: int = 12, timeout: int = 180):
    """Returns (pcm_bytes, sample_rate, meta). PCM is 24 kHz mono s16le by default."""
    payload = build_payload(text, voice)
    body = json.dumps(payload).encode("utf-8")
    last_err = None
    for attempt in range(1, max_retries + 1):
        req = urllib.request.Request(
            ENDPOINT,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
            data = json.loads(raw.decode("utf-8"))
            part = data["candidates"][0]["content"]["parts"][0]
            inline = part.get("inlineData") or part.get("inline_data")
            if not inline:
                raise RuntimeError(f"No inlineData in response: {json.dumps(data)[:800]}")
            pcm = base64.b64decode(inline["data"])
            mime = inline.get("mimeType", "audio/L16;codec=pcm;rate=24000")
            rate = 24000
            if "rate=" in mime:
                rate = int(mime.split("rate=")[1].split(";")[0].split(">")[0])
            return pcm, rate, {"attempt": attempt, "mime": mime, "bytes": len(pcm), "is_wav": pcm[:4] == b"RIFF", "resp_keys": list(data.keys())}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", "replace")[:400]
            last_err = f"HTTP {e.code}: {err_body}"
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries:
                wait = min(60.0, 2.0 ** attempt)
                print(f"  attempt {attempt}: {last_err} -> retrying in {wait:.0f}s", flush=True)
                time.sleep(wait)
                continue
            raise RuntimeError(f"TTS failed after {attempt} attempts: {last_err}")
        except Exception as e:
            last_err = str(e)
            if attempt < max_retries:
                wait = min(60.0, 2.0 ** attempt)
                print(f"  attempt {attempt}: {last_err} -> retrying in {wait:.0f}s", flush=True)
                time.sleep(wait)
                continue
            raise RuntimeError(f"TTS failed after {attempt} attempts: {last_err}")
    raise RuntimeError(f"TTS failed: {last_err}")


def pcm_to_wav(pcm: bytes, rate: int, path: str, channels: int = 1):
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)


def save_audio(pcm: bytes, rate: int, path: str):
    """If the payload already carries a RIFF/WAVE header, write it verbatim;
    otherwise wrap raw L16 PCM into a WAV container."""
    if pcm[:4] == b"RIFF":
        with open(path, "wb") as f:
            f.write(pcm)
    else:
        pcm_to_wav(pcm, rate, path)


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "<cheer> আরে দেখো! এটা তো একটা পেন্সিল!"
    voice = sys.argv[2] if len(sys.argv) > 2 else "Orus"
    out = sys.argv[3] if len(sys.argv) > 3 else "tts_test.wav"
    pcm, rate, meta = call_tts(text, voice)
    save_audio(pcm, rate, out)
    print("OK", meta, "->", out, f"({len(pcm)/2/rate:.2f}s @ {rate}Hz)")
