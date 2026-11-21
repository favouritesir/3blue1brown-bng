# -*- coding: utf-8 -*-
"""Generate the 10 lesson-specific build scripts from build_an_template.py."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WEB = HERE.parents[2]
TEMPLATE = (HERE / "build_an_template.py").read_text(encoding="utf-8")
IDS = json.loads((HERE / "official_ids.json").read_text(encoding="utf-8"))
EXPECTED = [27, 22, 24, 21, 23, 23, 22, 20, 21, 21]

for i, row in enumerate(IDS):
    nn = row["lesson"].split("_")[1]
    text = TEMPLATE
    for key, val in {
        "__NN__": nn,
        "__SLUG__": row["slug"],
        "__VIDEO_ID__": row["video_id"],
        "__OFFICIAL_URL__": row["official_url"],
        "__EMBED_URL__": row["embed_url"],
        "__OEMBED_TITLE__": row["oembed_title"],
        "__EXPECTED_CUES__": str(EXPECTED[i]),
    }.items():
        text = text.replace(key, val)
    for ph in ("__NN__", "__SLUG__", "__VIDEO_ID__", "__OFFICIAL_URL__",
               "__EMBED_URL__", "__OEMBED_TITLE__", "__EXPECTED_CUES__"):
        assert ph not in text, f"unreplaced {ph} in L{nn}"
    out = (WEB / "media_vault" / "analysis" / f"lesson_{nn}" / "dubbing_pipeline"
           / "experiments" / "clean_timesync_v2" / f"build_an{nn}_clean.py")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"WROTE {out}")
