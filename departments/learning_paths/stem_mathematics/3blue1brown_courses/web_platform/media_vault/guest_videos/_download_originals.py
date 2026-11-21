"""Download full original 3Blue1Brown guest videos via yt-dlp into each lesson's
original_source/ folder as full_original.mp4. Idempotent: skips valid existing files.
"""
import os
import sys
import time
import json
import subprocess
from pathlib import Path

import yt_dlp

WEB = Path(__file__).resolve().parent
VAULT = WEB  # .../web_platform/media_vault/guest_videos

LESSONS = {
    1: "iv-5mZ_9CPY",
    2: "_BrFKp-U8GI",
    3: "itRV2jEtV8Q",
    4: "4NlrfOl0l8U",
    5: "M-MgQC6z3VU",
}

MIN_BYTES = 5_000_000  # a real full video is far larger than 5 MB


def valid(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < MIN_BYTES:
        return False
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            text=True,
        )
        return float(out.strip()) > 600.0
    except Exception:
        return False


def download_one(n: int, vid: str) -> dict:
    dest_dir = VAULT / f"lesson_{n:02d}" / "original_source"
    dest_dir.mkdir(parents=True, exist_ok=True)
    final = dest_dir / "full_original.mp4"
    if valid(final):
        dur = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(final)], text=True).strip()
        return {"lesson": n, "status": "already_valid", "path": str(final),
                "bytes": final.stat().st_size, "duration": float(dur)}

    url = f"https://www.youtube.com/watch?v={vid}"
    opts = {
        "format": "best[height<=720][ext=mp4]/best[height<=720]/best[ext=mp4]/best",
        "outtmpl": str(dest_dir / "dl.%(ext)s"),
        "noplaylist": True,
        "quiet": False,
        "no_warnings": False,
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,
        "concurrent_fragment_downloads": 4,
        "merge_output_format": "mp4",
    }
    last = None
    for attempt in range(4):
        try:
            with yt_dlp.YoutubeDL(opts) as y:
                y.download([url])
            # locate downloaded file
            cands = [p for p in dest_dir.glob("dl.*")
                     if p.suffix.lower() in (".mp4", ".mkv", ".webm")]
            if not cands:
                raise RuntimeError("no downloaded file found")
            got = max(cands, key=lambda p: p.stat().st_size)
            if got.resolve() != final.resolve():
                if final.exists():
                    final.unlink()
                got.replace(final)
            if valid(final):
                dur = subprocess.check_output(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", str(final)], text=True).strip()
                return {"lesson": n, "status": "downloaded", "path": str(final),
                        "bytes": final.stat().st_size, "duration": float(dur)}
            raise RuntimeError("downloaded file failed validity check")
        except Exception as e:  # noqa: BLE001
            last = e
            print(f"[L{n:02d}] attempt {attempt+1} failed: {e}", flush=True)
            time.sleep(3 * (attempt + 1))
    return {"lesson": n, "status": "FAILED", "error": str(last)}


def main():
    results = []
    for n, vid in LESSONS.items():
        print(f"\n===== lesson_{n:02d} ({vid}) =====", flush=True)
        r = download_one(n, vid)
        print(json.dumps(r, ensure_ascii=False), flush=True)
        results.append(r)
    (VAULT / "_download_report.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nDOWNLOAD SUMMARY", flush=True)
    for r in results:
        print(json.dumps(r, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
