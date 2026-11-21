import json
from pathlib import Path
import yt_dlp

DATA = Path("web_platform/data/physics")
AUDIO = Path("web_platform/assets/audio/physics")
for i in range(1, 14):
    d = json.loads((DATA / f"lesson_{i:02d}.json").read_text(encoding="utf-8"))
    m = json.loads((AUDIO / f"lesson_{i:02d}" / "manifest.json").read_text(encoding="utf-8"))
    vid = d.get("youtube_id") or d.get("video_id")
    manifest_s = sum(c["duration_ms"] for s in m["sections"].values() for c in s["cues"]) / 1000.0
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True}) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
        vdur = info.get("duration") or 0
        print(f"lesson_{i:02d} | id={vid} | video={vdur:8.1f}s ({vdur/60:5.1f}m) | manifest={manifest_s:7.1f}s | ratio={vdur/max(manifest_s,1):5.2f}x")
    except Exception as e:
        print(f"lesson_{i:02d} | id={vid} | probe FAILED: {type(e).__name__}: {e}")
