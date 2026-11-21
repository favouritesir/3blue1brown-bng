# -*- coding: utf-8 -*-
import json, os
base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "topology")
for n in (1, 2, 3):
    d = json.load(open(os.path.join(base, f"lesson_{n:02d}.json"), encoding="utf-8"))
    print("=" * 70)
    print("LESSON", n, "|", d["meta"]["title_en"])
    for s in d["sections"]:
        print("  id=%s alias=%s audio_ref=%s noNarration=%s" % (
            s["id"], s.get("alias"), s.get("audio_ref"), s.get("data-no-narration", False)))
        print("     title=%s" % s.get("title_bn"))
