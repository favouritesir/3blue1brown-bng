# -*- coding: utf-8 -*-
"""Print extracted DOM texts for selected lessons (authoring aid)."""
import json
import sys

d = json.load(open("governance/puzzles_dom_extract.json", encoding="utf-8"))
for ln in sys.argv[1:]:
    print("\n##########", ln)
    for s in d[ln]["sections"]:
        print("\n== SECTION", s["id"], "|", s["title"])
        for i, b in enumerate(s["blocks"]):
            print("  [%d] %s: %s" % (i, b["type"], b["text"]))
            if b.get("tex_list"):
                print("       TEX:", " || ".join(b["tex_list"]))
