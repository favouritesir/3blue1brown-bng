# -*- coding: utf-8 -*-
import json, os, sys
gov = os.path.dirname(os.path.abspath(__file__))
for n in (1, 2, 3):
    d = json.load(open(os.path.join(gov, f"topology{n:02d}_dom_blocks.json"), encoding="utf-8"))
    print("#" * 80)
    print("LESSON", n)
    for s in d["sections"]:
        print()
        print("=== SECTION", s["id"], "|", s["title"], "===")
        for i, b in enumerate(s["blocks"]):
            t = b["text"].replace("\n", " ")
            if len(t) > 360:
                t = t[:360] + "..."
            print("  [%02d] %-13s | %s" % (i, b["type"], t))
