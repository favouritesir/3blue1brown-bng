"""One-shot yt-dlp download of the full originals for Fractals lessons 01..04.

Writes only to NEW original_source folders under
web_platform/media_vault/fractals/lesson_NN/original_source/.
"""
from pathlib import Path

from yt_dlp import YoutubeDL

WEB = Path(r"D:\0PEN CODE\Dub Studio\departments\learning_paths\stem_mathematics"
           r"\3blue1brown_courses\web_platform")

VIDEOS = {
    "01": "-RdOwhmqP5s",
    "02": "LqbZpur38nw",
    "03": "gB9n2gHsHN4",
    "04": "3s7h2MHQtxc",
}


def download(nn, vid):
    out = WEB / "media_vault" / "fractals" / f"lesson_{nn}" / "original_source"
    out.mkdir(parents=True, exist_ok=True)
    target = out / "full_original.mp4"
    url = f"https://www.youtube.com/watch?v={vid}"
    opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "outtmpl": str(out / "full_original.%(ext)s"),
        "noplaylist": True,
        "quiet": False,
        "no_warnings": False,
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 30,
    }
    print(f"=== lesson {nn} vid={vid} -> {target}", flush=True)
    with YoutubeDL(opts) as ydl:
        ydl.download([url])
    if not target.exists():
        for cand in out.glob("full_original.*"):
            if cand.suffix.lower() == ".mp4" and cand != target:
                cand.replace(target)
                break
    size = target.stat().st_size if target.exists() else 0
    print(f"=== lesson {nn} EXISTS={target.exists()} SIZE={size}", flush=True)
    return size


if __name__ == "__main__":
    results = {}
    for nn, vid in VIDEOS.items():
        results[nn] = download(nn, vid)
    print("ALL DONE", results, flush=True)
