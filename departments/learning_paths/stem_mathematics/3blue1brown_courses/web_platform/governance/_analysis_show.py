# -*- coding: utf-8 -*-
"""Compact print of extracted analysis cue content for script authoring."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "analysis_dom")

n = int(sys.argv[1])
path = os.path.join(OUT_DIR, f"lesson_{n:02d}.json")
data = json.load(open(path, encoding="utf-8"))
print(f"######## LESSON {n:02d} ########")
for sec in data["sections"]:
    print(f"\n===== {sec['id']}  ({len(sec['cues'])} cues)  {sec['audio_file']}")
    for c in sec["cues"]:
        ann = " | ".join(c["annotations"])
        print(f"\n  [{c['index']}] {c['type']}")
        print(f"    ANNOT: {ann}")
        print(f"    ENGINE: {c['text']}")
