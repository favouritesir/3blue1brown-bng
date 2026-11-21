import json, urllib.request
from pathlib import Path

ids = []
for i in range(1, 14):
    d = json.loads((Path("web_platform/data/physics") / f"lesson_{i:02d}.json").read_text(encoding="utf-8"))
    ids.append((i, d.get("youtube_id") or d.get("video_id")))

for i, vid in ids:
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        print(f"lesson_{i:02d} | {vid} | author={data.get('author_name')!r} | title={data.get('title')!r}")
    except Exception as e:
        print(f"lesson_{i:02d} | {vid} | OEmbed FAILED: {e}")
