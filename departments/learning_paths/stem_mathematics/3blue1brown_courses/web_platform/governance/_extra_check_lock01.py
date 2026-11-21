import json
import os
import subprocess

D = "assets/audio/lockdown_math/lesson_01"
m = json.load(open(D + "/manifest.json", encoding="utf-8"))
print("manifest section keys:", list(m["sections"]))
for line in open("courses/lockdown_math/lesson_01.html", encoding="utf-8"):
    if "manifest.js?v=" in line:
        print("page script tag:", line.strip())

ok = True
for sid, s in m["sections"].items():
    f = os.path.join(D, s["audio_file"])
    ms = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", f],
        capture_output=True, text=True, check=True).stdout) * 1000.0
    c = s["cues"][0]
    match = abs(ms - s["total_duration_ms"]) < 1500 and abs(c["end_ms"] - s["total_duration_ms"]) < 1
    ok &= match and os.path.getsize(f) > 0
    print(f"{sid:30} {os.path.getsize(f):>7}B ffprobe={ms:8.1f}ms "
          f"manifest={s['total_duration_ms']:8.1f}ms cue_end={c['end_ms']:8.1f}ms match={match}")

print("backup files:", sorted(os.listdir(D + "/_backup_before_expressive_build")))
print("all mp3 match + non-zero:", ok)

# Forbidden label must be absent from page, manifest.json, manifest.js, sidecars.
forbidden = "চিত্র প্রদর্শনী"
checks = ["courses/lockdown_math/lesson_01.html", D + "/manifest.json", D + "/manifest.js"]
checks += [os.path.join(D, f) for f in os.listdir(D) if f.endswith("_cues.json")]
hits = [p for p in checks if forbidden in open(p, encoding="utf-8").read()]
print("forbidden-label hits in page/manifests/sidecars:", hits)

# Audio actually contains speech, not silence: measure mean volume.
for sid, s in m["sections"].items():
    f = os.path.join(D, s["audio_file"])
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", f, "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True)
    means = [x.strip() for x in r.stderr.splitlines() if "mean_volume:" in x]
    print(f"  {sid:30} {means[0] if means else 'NO LEVEL'}")
