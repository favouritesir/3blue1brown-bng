"""One-shot yt-dlp download of the 3 official 3Blue1Brown Topology originals.

IDs resolved from the official 3B1B lesson pages and verified via YouTube
oEmbed (author_name=3Blue1Brown) + yt-dlp uploader/channel_id before download.
"""
from pathlib import Path
import subprocess

from yt_dlp import YoutubeDL

WEB = Path(__file__).resolve().parents[1] / "web_platform"
VAULT = WEB / "media_vault" / "topology"

VIDEOS = {
    "01": "IQqtsm-bBRU",
    "02": "BHdbsHFs2P0",
    "03": "yuVqxCSsE7c",
}


def probe(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def main():
    for nn, vid in VIDEOS.items():
        out_dir = VAULT / f"lesson_{nn}" / "original_source"
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / "full_original.mp4"
        if target.exists() and probe(target) > 30:
            print(f"[L{nn}] already present dur={probe(target):.2f}s", flush=True)
            continue
        print(f"[L{nn}] -> {vid}  ({out_dir})", flush=True)
        opts = {
            "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "outtmpl": str(out_dir / "full_original.%(ext)s"),
            "noplaylist": True,
            "quiet": False,
            "no_warnings": False,
            "retries": 10,
            "fragment_retries": 10,
            "socket_timeout": 30,
            "concurrent_fragment_downloads": 4,
        }
        try:
            with YoutubeDL(opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={vid}"])
        except Exception as e:
            print(f"[L{nn}] yt-dlp error: {e}", flush=True)
        if not target.exists():
            for cand in out_dir.glob("full_original.*"):
                if cand.suffix.lower() == ".mp4" and cand != target:
                    cand.replace(target)
                    break
        print(f"[L{nn}] result exists={target.exists()} "
              f"size={target.stat().st_size if target.exists() else 0} "
              f"dur={probe(target):.2f}s", flush=True)


if __name__ == "__main__":
    main()
