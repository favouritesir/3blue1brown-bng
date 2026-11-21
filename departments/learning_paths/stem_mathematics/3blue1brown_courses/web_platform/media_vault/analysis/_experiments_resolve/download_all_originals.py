# -*- coding: utf-8 -*-
"""Download the 10 official 3Blue1Brown Analysis originals with yt-dlp.

IDs were resolved from the official 3blue1brown.com lesson pages
(VideoObject embedUrl) and verified with YouTube oEmbed (author=3Blue1Brown).
See official_ids.json in this folder.
"""
import json
import subprocess
import sys
from pathlib import Path

from yt_dlp import YoutubeDL

HERE = Path(__file__).resolve().parent
WEB = HERE.parents[2]           # .../web_platform
VAULT = WEB / "media_vault" / "analysis"
IDS = json.loads((HERE / "official_ids.json").read_text(encoding="utf-8"))


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
    only = set(sys.argv[1:])
    for row in IDS:
        nn = row["lesson"].split("_")[1]
        if only and nn not in only:
            continue
        vid = row["video_id"]
        assert row["author_verified"], f"oEmbed author not verified for {row['lesson']}"
        out_dir = VAULT / f"lesson_{nn}" / "original_source"
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / "full_original.mp4"
        if target.exists() and probe(target) > 30:
            print(f"[L{nn}] already present dur={probe(target):.2f}s", flush=True)
            continue
        print(f"[L{nn}] {row['slug']} -> {vid}", flush=True)
        opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
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
