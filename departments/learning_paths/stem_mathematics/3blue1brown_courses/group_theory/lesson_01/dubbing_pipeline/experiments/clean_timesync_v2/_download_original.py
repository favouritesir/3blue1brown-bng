"""One-shot yt-dlp download of the full original for Group Theory lesson 01 (mH0oCDa74tE)."""
from pathlib import Path
from yt_dlp import YoutubeDL

WEB = Path(r"D:\0PEN CODE\Dub Studio\departments\learning_paths\stem_mathematics\3blue1brown_courses\web_platform")
OUT = WEB / "media_vault" / "group_theory" / "lesson_01" / "original_source"
OUT.mkdir(parents=True, exist_ok=True)
target = OUT / "full_original.mp4"
vid = "mH0oCDa74tE"
url = f"https://www.youtube.com/watch?v={vid}"

opts = {
    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
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
    ydl.download([url])

if not target.exists():
    for cand in OUT.glob("full_original.*"):
        if cand.suffix.lower() == ".mp4" and cand != target:
            cand.replace(target)
            break

print("EXISTS", target.exists(), "SIZE", target.stat().st_size if target.exists() else 0, flush=True)
