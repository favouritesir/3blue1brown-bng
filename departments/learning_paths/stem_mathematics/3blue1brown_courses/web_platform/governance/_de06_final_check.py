# -*- coding: utf-8 -*-
"""Independent sanity checks for the DE06 expressive audio build."""
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
D = os.path.join(WORKSPACE, "assets", "audio", "differential_equations", "lesson_06")

m = json.load(open(os.path.join(D, "manifest.json"), encoding="utf-8"))
print("lesson/voice/mode:", m["lesson"], m["voice"], m["mode"])
total = 0.0
for sid, s in m["sections"].items():
    p = os.path.join(D, s["audio_file"])
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", p],
        capture_output=True, text=True).stdout
    dur = float(out) * 1000.0
    md = s["total_duration_ms"]
    total += md
    print(f"{sid:<26} cues={len(s['cues']):>2} "
          f"manifest_ms={md:>9.1f} ffprobe_ms={dur:>9.1f} "
          f"diff={dur - md:>7.1f} bytes={os.path.getsize(p)}")
print("TOTAL manifest_ms =", total)

html = open(os.path.join(WORKSPACE, "courses", "differential_equations",
                         "lesson_06.html"), encoding="utf-8").read()
print("page manifest versions:", re.findall(r"manifest\.js\?v=(\d+)", html))

bad = []
for sid, s in m["sections"].items():
    for c in s["cues"]:
        if "চিত্র প্রদর্শনী" in c["text"]:
            bad.append((sid, c["index"]))
print("forbidden label hits:", bad)

# backup folder intact
bak = os.path.join(D, "_backup_before_expressive_build")
print("backup folder exists:", os.path.isdir(bak),
      "entries:", len(os.listdir(bak)) if os.path.isdir(bak) else "n/a")
