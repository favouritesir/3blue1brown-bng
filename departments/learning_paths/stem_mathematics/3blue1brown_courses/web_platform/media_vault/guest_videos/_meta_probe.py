import json
from pathlib import Path
base = Path(__file__).resolve().parents[2]  # web_platform
for n in range(1, 6):
    L = json.loads((base / "data" / "guest_videos" / f"lesson_{n:02d}.json").read_text(encoding="utf-8"))
    M = json.loads((base / "assets" / "audio" / "guest_videos" / f"lesson_{n:02d}" / "manifest.json").read_text(encoding="utf-8"))
    cues = [c for s in M["sections"].values() for c in s["cues"]]
    tot = sum(c["duration_ms"] for c in cues) + 350 * (len(cues) - len(M["sections"]))
    print(f"L{n:02d} id={L['youtube_id']} cues={len(cues)} authored_sec={tot/1000:.1f} title={L['title_en'][:70]}")
