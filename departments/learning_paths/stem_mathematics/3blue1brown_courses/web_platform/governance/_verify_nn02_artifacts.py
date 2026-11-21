# -*- coding: utf-8 -*-
"""Independent artifact check for the NN L02 expressive teacher-audio build."""
import json, os, subprocess
from pathlib import Path

WP = Path(__file__).resolve().parent.parent
A = WP / "assets" / "audio" / "neural_networks" / "lesson_02"
OLD_KEYS = ["sec-learning-paradox", "sec-cost-function",
            "sec-gradient-descent-intuition", "sec-multivariable-gradient",
            "sec-learning-rate-landscape", "sec-mini-batch-sgd"]

m = json.loads((A / "manifest.json").read_text(encoding="utf-8"))
js = (A / "manifest.js").read_text(encoding="utf-8").strip()
js_obj = json.loads(js[len("window.TEACHER_AUDIO_MANIFEST = "):-1].strip())

print("manifest.json == manifest.js:", js_obj == m)
print("section keys identical to existing keys:", list(m["sections"].keys()) == OLD_KEYS)
print("voice:", m["voice"], "| course/lesson:", m["course"], m["lesson"])

all_texts = []
total = 0
dur_total = 0
for sid, sec in m["sections"].items():
    mp3 = A / sec["audio_file"]
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(mp3)],
        capture_output=True, text=True, check=True).stdout.strip()
    real_ms = float(probe) * 1000
    declared = sec["total_duration_ms"]
    cues = sec["cues"]
    all_texts.extend(c["text"] for c in cues)
    total += len(cues)
    dur_total += declared
    print(f"  {sid:<34} {len(cues):>2} cues | manifest {declared/1000:8.2f}s | "
          f"mp3 {real_ms/1000:8.2f}s | delta {abs(real_ms-declared):6.1f}ms | "
          f"{mp3.stat().st_size} B")

print("total cues:", total, "| total duration:", round(dur_total/1000, 2), "s")
print("duplicate cue texts:", len(all_texts) - len(set(all_texts)))
print("forbidden label 'চিত্র প্রদর্শনী' occurrences:",
      sum(t.count("চিত্র প্রদর্শনী") for t in all_texts))
print("types:", {t: sum(1 for s in m['sections'].values() for c in s['cues'] if c['type'] == t)
                 for t in sorted({c['type'] for s in m['sections'].values() for c in s['cues']})})
