# -*- coding: utf-8 -*-
"""Materialise the 10 per-lesson build scripts from the proven template."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSES = HERE.parent.parent
TPL = (HERE / "build_puzNN_clean.TEMPLATE.py").read_text(encoding="utf-8")
IDS = json.loads((HERE / "official_ids_verified.json").read_text(encoding="utf-8"))

EXPECTED = {1: 22, 2: 26, 3: 24, 4: 23, 5: 22, 6: 21, 7: 23, 8: 23, 9: 23, 10: 24}

for e in IDS["lessons"]:
    n = int(e["lesson"])
    nn = f"{n:02d}"
    text = TPL
    for key, val in (
        ("__NN__", nn),
        ("__SLUG__", e["slug"]),
        ("__VIDEO_ID__", e["video_id"]),
        ("__OFFICIAL_URL__", e["official_page"]),
        ("__OEMBED_TITLE__", e["oembed_title"]),
        ("__EXPECTED_CUES__", str(EXPECTED[n])),
    ):
        text = text.replace(key, val)
    out = (COURSES / "puzzles" / f"lesson_{nn}" / "dubbing_pipeline" /
           "experiments" / "clean_timesync_v2" / f"build_puz{nn}_clean.py")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"WROTE {out} ({len(text)} chars)")

print("DONE")
