import json
from pathlib import Path

base = Path("web_platform/data/physics")
audio = Path("web_platform/assets/audio/physics")
expected = [17, 18, 14, 15, 14, 15, 15, 15, 16, 16, 16, 15, 14]
for i in range(1, 14):
    d = json.loads((base / f"lesson_{i:02d}.json").read_text(encoding="utf-8"))
    m = json.loads((audio / f"lesson_{i:02d}" / "manifest.json").read_text(encoding="utf-8"))
    cues = sum(len(s["cues"]) for s in m["sections"].values())
    got_video = d.get("youtube_id") or d.get("video_id")
    flag = "OK" if cues == expected[i - 1] else f"MISMATCH(exp {expected[i-1]})"
    print(f"lesson_{i:02d} | id={got_video} | cues={cues} {flag} | {d.get('title_en')} | {d.get('official_url')}")
