# -*- coding: utf-8 -*-
"""Final compact audit of the Group Theory expressive audio build."""
import os
import re
import json

HERE = os.path.dirname(os.path.abspath(__file__))
WP = os.path.dirname(HERE)
BASE = os.path.join(WP, "assets", "audio", "group_theory")
BAD = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")

for n in (1, 2):
    d = os.path.join(BASE, f"lesson_{n:02d}")
    m = json.load(open(os.path.join(d, "manifest.json"), encoding="utf-8"))
    texts = [c["text"] for s in m["sections"].values() for c in s["cues"]]
    bad = [t for t in texts if BAD.findall(t) or "চিত্র প্রদর্শনী" in t]
    bk = os.path.join(d, "_backup_before_expressive_build")
    print(f"\nlesson_{n:02d}: cues={len(texts)} sections={len(m['sections'])} "
          f"bad_scripts={len(bad)} backup={sorted(os.listdir(bk))}")
    for sid, s in m["sections"].items():
        p = os.path.join(d, s["audio_file"])
        print(f"   {sid:<22} {len(s['cues']):>2} cues "
              f"{s['total_duration_ms'] / 1000:7.2f}s {os.path.getsize(p):>8}B")

# HTML version bump integrity
for n in (1, 2):
    p = os.path.join(WP, "courses", "group_theory", f"lesson_{n:02d}.html")
    raw = open(p, "rb").read()
    txt = raw.decode("utf-8")
    print(f"lesson_{n:02d}.html: bytes={len(raw)} bom={raw[:3] == b'\xef\xbb\xbf'} "
          f"v2={txt.count('?v=2')} v1={txt.count('?v=1')} page_errors_check=headless")
