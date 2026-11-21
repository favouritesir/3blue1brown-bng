"""One-shot yt-dlp download of the full original for number_theory lesson 01.

Source: 3Blue1Brown (Grant Sanderson), YouTube EK32jo7i5LQ.
Output: web_platform/media_vault/number_theory/lesson_01/original_source/full_original.mp4
"""
import json
import subprocess
from pathlib import Path

from yt_dlp import YoutubeDL

WEB = Path(r"D:\0PEN CODE\Dub Studio\departments\learning_paths\stem_mathematics\3blue1brown_courses\web_platform")
OUT = WEB / "media_vault" / "number_theory" / "lesson_01" / "original_source"
OUT.mkdir(parents=True, exist_ok=True)
target = OUT / "full_original.mp4"
vid = "EK32jo7i5LQ"
url = f"https://www.youtube.com/watch?v={vid}"

opts = {
    "format": ("bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/"
               "best[height<=720][ext=mp4]/best[height<=720]/best"),
    "merge_output_format": "mp4",
    "outtmpl": str(OUT / "full_original.%(ext)s"),
    "noplaylist": True,
    "quiet": False,
    "no_warnings": False,
    "retries": 5,
    "fragment_retries": 5,
    "socket_timeout": 30,
}

print("Downloading", url, "->", target, flush=True)
with YoutubeDL(opts) as ydl:
    info = ydl.extract_info(url, download=True)
    print("PROVENANCE id=%s uploader=%s channel=%s title=%s duration=%s" % (
        info.get("id"), info.get("uploader"), info.get("channel"),
        info.get("title"), info.get("duration")), flush=True)

if not target.exists():
    for cand in OUT.glob("full_original.*"):
        if cand.suffix.lower() == ".mp4" and cand != target:
            cand.replace(target)
            break

if not target.exists():
    raise SystemExit("DOWNLOAD FAILED: no full_original.mp4")

probe = json.loads(subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries",
     "format=duration,size:stream=codec_type,codec_name,width,height",
     "-of", "json", str(target)], capture_output=True, text=True).stdout)
print("FFPROBE", json.dumps(probe, ensure_ascii=False), flush=True)
print("EXISTS", target.exists(), "SIZE", target.stat().st_size, flush=True)
