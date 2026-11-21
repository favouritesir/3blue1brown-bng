"""Download full official 3Blue1Brown physics source videos via yt-dlp.

Usage:
    python temp_download_physics.py 1        # single lesson
    python temp_download_physics.py          # all 13 lessons
"""
import json
import subprocess
import sys
from pathlib import Path

import yt_dlp

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "web_platform" / "data" / "physics"
VAULT = ROOT / "web_platform" / "media_vault" / "physics"


def ffprobe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except Exception:
        return 0.0


def download_one(i):
    d = json.loads((DATA / f"lesson_{i:02d}.json").read_text(encoding="utf-8"))
    vid = d.get("youtube_id") or d.get("video_id")
    if not vid:
        print(f"[lesson {i:02d}] NO ID — SKIP", flush=True)
        return False
    outdir = VAULT / f"lesson_{i:02d}" / "original_source"
    outdir.mkdir(parents=True, exist_ok=True)
    # Remove any prior partial output so the merge target is unambiguous.
    for p in outdir.glob("full_original.*"):
        try:
            p.unlink()
        except OSError:
            pass
    opts = {
        "outtmpl": str(outdir / "full_original.%(ext)s"),
        "format": "bv*[ext=mp4][height<=1080]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
        "merge_output_format": "mp4",
        "retries": 12,
        "fragment_retries": 12,
        "socket_timeout": 40,
        "noplaylist": True,
        "quiet": False,
        "no_warnings": False,
        "noprogress": False,
    }
    print(f"[lesson {i:02d}] downloading {vid} -> {outdir}", flush=True)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=True)
        final = outdir / "full_original.mp4"
        if not final.exists():
            cands = sorted(outdir.glob("full_original.*"), key=lambda p: p.stat().st_mtime, reverse=True)
            if cands:
                cands[0].rename(final)
        dur = ffprobe_duration(final) if final.exists() else 0.0
        size = final.stat().st_size if final.exists() else 0
        ok = dur > 60 and size > 1_000_000
        print(f"[lesson {i:02d}] DONE id={vid} dur={dur:.2f}s size={size} bytes ok={ok} "
              f"channel={info.get('channel')!r}", flush=True)
        return ok
    except Exception as e:
        print(f"[lesson {i:02d}] FAILED id={vid}: {type(e).__name__}: {e}", flush=True)
        return False


if __name__ == "__main__":
    args = [int(a) for a in sys.argv[1:]]
    lessons = args if args else list(range(1, 14))
    results = {}
    for i in lessons:
        results[i] = download_one(i)
    print("SUMMARY:", json.dumps({str(k): v for k, v in results.items()}), flush=True)
