# -*- coding: utf-8 -*-
"""Download the 10 FULL official 3Blue1Brown puzzle videos (one per lesson).

Every ID comes from official_ids_verified.json (official lesson-page VideoObject
embedUrl + YouTube oEmbed author==3Blue1Brown). No third-party video is used.

Only the VIDEO stream is needed: the dubbing pipeline replaces the audio and
muxes with -c:v copy, so we prefer a 720p H.264 MP4 (DASH/https) video stream.
"""
import json
import subprocess
from pathlib import Path

from yt_dlp import YoutubeDL

HERE = Path(__file__).resolve().parent
COURSES = HERE.parent.parent                       # .../3blue1brown_courses
WEB = COURSES / "web_platform"
IDS = json.loads((HERE / "official_ids_verified.json").read_text(encoding="utf-8"))

FMT = ("bestvideo[height<=720][vcodec^=avc][protocol^=https]/"
       "bestvideo[height<=720][ext=mp4]/bestvideo[ext=mp4]/best")


def ffprobe_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def main():
    report = []
    for entry in IDS["lessons"]:
        n = int(entry["lesson"])
        nn = f"{n:02d}"
        vid = entry["video_id"]
        out_dir = WEB / "media_vault" / "puzzles" / f"lesson_{nn}" / "original_source"
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / "full_original.mp4"
        url = f"https://www.youtube.com/watch?v={vid}"

        if target.exists() and ffprobe_duration(target) > 60:
            print(f"SKIP L{nn} {vid}: already downloaded ({ffprobe_duration(target):.1f}s)",
                  flush=True)
            report.append({"lesson": n, "video_id": vid, "status": "already_present",
                           "duration_sec": round(ffprobe_duration(target), 3),
                           "size_bytes": target.stat().st_size})
            continue

        # purge partials from a failed run
        for p in out_dir.glob("full_original.*"):
            try:
                p.unlink()
            except OSError:
                pass

        opts = {
            "format": FMT,
            "outtmpl": str(out_dir / "full_original.%(ext)s"),
            "noplaylist": True,
            "quiet": False,
            "no_warnings": False,
            "retries": 8,
            "fragment_retries": 8,
            "socket_timeout": 30,
            "concurrent_fragment_downloads": 4,
            "overwrites": True,
        }
        print(f"DOWNLOAD L{nn} {vid} {entry['official_page']} -> {target}", flush=True)
        err = None
        for attempt in range(3):
            try:
                with YoutubeDL(opts) as ydl:
                    ydl.download([url])
                err = None
                break
            except Exception as e:  # noqa: BLE001
                err = e
                print(f"  retry {attempt + 1}/3 after error: {e}", flush=True)

        if not target.exists():
            for cand in out_dir.glob("full_original.*"):
                if cand.suffix.lower() == ".mp4" and cand != target:
                    cand.replace(target)
                    break

        dur = ffprobe_duration(target) if target.exists() else 0.0
        ok = target.exists() and dur > 60
        print(f"  L{nn} result exists={target.exists()} duration={dur:.3f}s "
              f"size={target.stat().st_size if target.exists() else 0}", flush=True)
        report.append({"lesson": n, "video_id": vid, "status": "ok" if ok else "FAILED",
                       "duration_sec": round(dur, 3),
                       "size_bytes": target.stat().st_size if target.exists() else 0,
                       "error": str(err) if err and not ok else None})

    (HERE / "download_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    bad = [r for r in report if r["status"] == "FAILED"]
    print(f"\nDOWNLOAD DONE: {len(report) - len(bad)}/{len(report)} ok", flush=True)
    if bad:
        print("FAILED:", [r["lesson"] for r in bad], flush=True)


if __name__ == "__main__":
    main()
