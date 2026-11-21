# -*- coding: utf-8 -*-
"""Independent post-build checks for Lockdown Math Lesson 06."""
import os
import json
import subprocess

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                 "assets", "audio", "lockdown_math", "lesson_06")
D = os.path.normpath(D)
man = json.load(open(os.path.join(D, "manifest.json"), encoding="utf-8"))


def dur(p):
    o = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", p],
        capture_output=True, text=True).stdout.strip()
    return float(o) * 1000.0


print("=== on-disk MP3 vs manifest total_duration_ms ===")
all_ok = True
for sid, s in man["sections"].items():
    p = os.path.join(D, s["audio_file"])
    dd, md = dur(p), s["total_duration_ms"]
    ok = abs(dd - md) < 1500
    all_ok = all_ok and ok
    print(f"{sid:<30} disk={dd/1000:7.2f}s manifest={md/1000:7.2f}s "
          f"diff={abs(dd-md):.0f}ms size={os.path.getsize(p)} "
          f"{'OK' if ok else 'MISMATCH'}")
print("ALL_OK =", all_ok)

print("=== forbidden label in audio-dir json/js (excluding backup) ===")
bad = []
for root, dirs, files in os.walk(D):
    if "_backup_before_expressive_build" in root:
        continue
    for f in files:
        if f.endswith((".json", ".js")):
            t = open(os.path.join(root, f), encoding="utf-8", errors="ignore").read()
            if "চিত্র প্রদর্শনী" in t:
                bad.append(os.path.join(root, f))
print("forbidden hits:", bad)

print("=== backup folder contents (must be untouched) ===")
bdir = os.path.join(D, "_backup_before_expressive_build")
for f in sorted(os.listdir(bdir)):
    print(" ", f, os.path.getsize(os.path.join(bdir, f)))
