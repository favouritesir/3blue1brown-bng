"""One-shot yt-dlp download of the full original for Lockdown Math Lesson 02.

YouTube ID Kas0tIxDvrg is verified as "Exponential growth and epidemics".
Writes only into a NEW lesson_02 folder; never touches lesson_01 or other lessons.
"""
import time
from pathlib import Path

from yt_dlp import YoutubeDL

WEB = Path(r"D:\0PEN CODE\Dub Studio\departments\learning_paths\stem_mathematics\3blue1brown_courses\web_platform")
OUT = WEB / "media_vault" / "lockdown_math" / "lesson_02" / "original_source"
OUT.mkdir(parents=True, exist_ok=True)
target = OUT / "full_original.mp4"
vid = "Kas0tIxDvrg"
url = f"https://www.youtube.com/watch?v={vid}"

opts = {
    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "merge_output_format": "mp4",
    "outtmpl": str(OUT / "full_original.%(ext)s"),
    "noplaylist": True,
    "quiet": False,
    "no_warnings": False,
    "retries": 8,
    "fragment_retries": 8,
    "socket_timeout": 30,
    "concurrent_fragment_downloads": 4,
}

print("Downloading", url, "->", target, flush=True)
last = None
for attempt in range(3):
    try:
        with YoutubeDL(opts) as ydl:
            ydl.download([url])
        last = None
        break
    except Exception as e:  # noqa: BLE001 - transient network/format errors
        last = e
        print(f"download attempt {attempt + 1} failed: {e}", flush=True)
        time.sleep(2 * (attempt + 1))

if not target.exists():
    for cand in OUT.glob("full_original.*"):
        if cand.suffix.lower() == ".mp4" and cand != target:
            cand.replace(target)
            break

print("EXISTS", target.exists(), "SIZE", target.stat().st_size if target.exists() else 0, flush=True)
if last is not None:
    raise last
