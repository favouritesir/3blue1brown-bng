# -*- coding: utf-8 -*-
"""Resolve official YouTube IDs from 3blue1brown.com lesson pages (VideoObject
embedUrl) and verify the author with YouTube oEmbed. Read-only helper."""
import json
import re
import urllib.request
from pathlib import Path

SLUGS = [
    "zeta",
    "print-gallery",
    "fourier-transforms",
    "uncertainty-principle",
    "fourier-series",
    "borwein",
    "convolutions",
    "winding-numbers",
    "inventing-math",
    "music-and-measure-theory",
]
OUT = Path(__file__).resolve().parent / "official_ids.json"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


def main():
    rows = []
    for i, slug in enumerate(SLUGS, 1):
        page = get(f"https://www.3blue1brown.com/lessons/{slug}")
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
        embed = None
        title = None
        for b in blocks:
            try:
                obj = json.loads(b)
            except Exception:
                continue
            if obj.get("@type") == "VideoObject" and obj.get("embedUrl"):
                embed = obj["embedUrl"]
                title = obj.get("name")
                break
        m = re.search(r"(?:embed/|v=)([A-Za-z0-9_-]{11})", embed or "")
        vid = m.group(1) if m else None
        oe = None
        author = None
        oe_title = None
        if vid:
            try:
                oe = json.loads(get(
                    f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"))
                author = oe.get("author_name")
                oe_title = oe.get("title")
            except Exception as e:
                oe = {"error": str(e)}
        row = {
            "lesson": f"lesson_{i:02d}",
            "slug": slug,
            "official_url": f"https://www.3blue1brown.com/lessons/{slug}",
            "videoobject_title": title,
            "embed_url": embed,
            "video_id": vid,
            "youtube_url": f"https://www.youtube.com/watch?v={vid}" if vid else None,
            "oembed_author": author,
            "oembed_title": oe_title,
            "author_verified": author == "3Blue1Brown",
        }
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWROTE {OUT}")


if __name__ == "__main__":
    main()
