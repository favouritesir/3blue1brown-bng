"""Download the 8 official 3Blue1Browm Why-Pi originals (full length) with yt-dlp.

IDs resolved from the official https://www.3blue1brown.com/lessons/<slug> pages
(VideoObject embedUrl) and verified via YouTube oEmbed (author=3Blue1Brown).
"""
from pathlib import Path
import subprocess
import sys

from yt_dlp import YoutubeDL

WEB = Path(__file__).resolve().parents[5]  # .../3blue1brown_courses/web_platform
VAULT = WEB / "media_vault" / "why_pi"

VIDEOS = {
    "01": ("clacks", "HEfHFsfGXjs"),
    "02": ("colliding-blocks-v2", "6dTyOl1fmDo"),
    "03": ("clacks-via-light", "brU5yLm9DZM"),
    "04": ("basel-problem", "d-o3eB9sfls"),
    "05": ("leibniz-formula", "NaL_Cb42WyY"),
    "06": ("gaussian-integral", "cy8r7WSuT1I"),
    "07": ("wallis-product", "8GPy_UMV-08"),
    "08": ("pi-was-628", "bcPTiiiYDs8"),
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
    only = sys.argv[1:] or list(VIDEOS)
    for nn in only:
        slug, vid = VIDEOS[nn]
        out_dir = VAULT / f"lesson_{nn}" / "original_source"
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / "full_original.mp4"
        if target.exists() and probe(target) > 30:
            print(f"[L{nn}] already present dur={probe(target):.2f}s", flush=True)
            continue
        print(f"[L{nn}] {slug} -> {vid}  ({out_dir})", flush=True)
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
        # Normalise to full_original.mp4
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
