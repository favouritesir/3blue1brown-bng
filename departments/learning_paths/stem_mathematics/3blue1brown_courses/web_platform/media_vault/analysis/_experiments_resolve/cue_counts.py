# -*- coding: utf-8 -*-
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[3] / "assets" / "audio" / "analysis"
for n in range(1, 11):
    d = json.loads((BASE / f"lesson_{n:02d}" / "manifest.json").read_text(encoding="utf-8"))
    cues = [c for s in d["sections"].values() for c in s["cues"]]
    total = sum(float(c.get("duration_ms", 0)) for c in cues)
    print(f"lesson_{n:02d}: sections={len(d['sections'])} cues={len(cues)} cue_total_ms={total:.0f}")
