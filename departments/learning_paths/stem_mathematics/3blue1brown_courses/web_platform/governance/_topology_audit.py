# -*- coding: utf-8 -*-
import os, json
base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "assets", "audio", "topology")
for n in (1, 2, 3):
    d = os.path.join(base, "lesson_%02d" % n)
    m = json.load(open(os.path.join(d, "manifest.json"), encoding="utf-8"))
    cues = sum(len(s["cues"]) for s in m["sections"].values())
    mp3s = sorted(f for f in os.listdir(d) if f.endswith(".mp3"))
    sizes = [os.path.getsize(os.path.join(d, f)) for f in mp3s]
    print("lesson_%02d: mode=%s sections=%d cues=%d mp3s=%d all_nonzero=%s total=%.2fs" % (
        n, m["mode"], len(m["sections"]), cues, len(mp3s), all(s > 0 for s in sizes),
        sum(s["total_duration_ms"] for s in m["sections"].values()) / 1000.0))
    b = os.path.join(d, "_backup_before_expressive_build")
    bm = json.load(open(os.path.join(b, "manifest.json"), encoding="utf-8"))
    print("   backup mode=%s files=%s" % (bm["mode"], sorted(os.listdir(b))))
