# -*- coding: utf-8 -*-
"""Independent, read-only final checks for the NN04 expressive audio build."""
import json
import os
import subprocess
from pathlib import Path

WP = Path(__file__).resolve().parent.parent
AUD = WP / "assets" / "audio" / "neural_networks" / "lesson_04"
BACKUP = AUD / "_backup_before_expressive_build"
FORBIDDEN = ("চিত্র প্রদর্শনী", "চিত্রপ্রদর্শনী")
SAFEGUARDS = ("পার্শিয়াল ডি সি বাই ডি ডাব্লিউ", "সিগময়েড", "সিগমা প্রাইম",
              "চেইন রুল", "ইটা", "তেরো হাজার দুই")
BAD_TYPES = {"quiz", "media-tab", "b1b-quiz", "b1b-media-tab"}

mj = json.loads((AUD / "manifest.json").read_text(encoding="utf-8"))
js = (AUD / "manifest.js").read_text(encoding="utf-8").strip()
jo = json.loads(js[len("window.TEACHER_AUDIO_MANIFEST = "):-1].strip())
assert jo == mj, "manifest.js != manifest.json"

all_text = []
all_types = set()
grand_total_ms = 0.0
audio_report = []
for sid, sec in mj["sections"].items():
    cues = sec["cues"]
    mp3 = AUD / sec["audio_file"]
    assert mp3.exists() and mp3.stat().st_size > 0, mp3
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(mp3)],
        capture_output=True, text=True, check=True).stdout.strip()
    mp3_ms = float(probe) * 1000.0
    manifest_ms = sec["total_duration_ms"]
    assert abs(mp3_ms - manifest_ms) < 1200.0, (sid, mp3_ms, manifest_ms)
    grand_total_ms += manifest_ms
    audio_report.append((sid, sec["audio_file"], mp3.stat().st_size,
                         round(mp3_ms / 1000.0, 2), round(manifest_ms / 1000.0, 2)))
    for c in cues:
        all_text.append(c["text"])
        all_types.add(c["type"])
        for f in FORBIDDEN:
            assert f not in c["text"], (sid, c["index"], f)

joined = "\n".join(all_text)
for s in SAFEGUARDS:
    assert s in joined, f"missing safeguard: {s}"
assert not (BAD_TYPES & all_types), BAD_TYPES & all_types
assert len(all_text) == 26, len(all_text)

# Backup untouched & distinct from the rebuilt manifest.
assert (BACKUP / "manifest.json").exists() and (BACKUP / "manifest.js").exists()
bjson = (BACKUP / "manifest.json").read_text(encoding="utf-8")
assert bjson != (AUD / "manifest.json").read_text(encoding="utf-8"), "backup == live"

print("FINAL CHECK OK")
print("cues:", len(all_text), " sections:", len(mj["sections"]))
print("cue types:", sorted(all_types))
print("total duration (manifest):", round(grand_total_ms / 1000.0, 2), "s")
for sid, af, sz, m3, mf in audio_report:
    print(f"  {sid:<34} {af:<26} {sz:>8} B  ffprobe={m3:>7.2f}s  manifest={mf:>7.2f}s")
print("forbidden-label hits in narration text:", 0)
print("phonetic safeguards present:", len(SAFEGUARDS))
print("backup exists & distinct from live:", True)
print("manifest.js == manifest.json:", True)
