# -*- coding: utf-8 -*-
"""Run the remaining puzzle build scripts strictly SEQUentially.

edge_tts retries are more reliable without concurrent TTS traffic, so each
build runs to completion before the next one starts. Lesson 10 is excluded
because it is run first as the smoke test.
"""
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSES = HERE.parent.parent
LESSONS = [int(x) for x in sys.argv[1:]] or [1, 2, 3, 4, 5, 6, 7, 8, 9]
PY = sys.executable

for n in LESSONS:
    nn = f"{n:02d}"
    script = (COURSES / "puzzles" / f"lesson_{nn}" / "dubbing_pipeline" /
              "experiments" / "clean_timesync_v2" / f"build_puz{nn}_clean.py")
    log = script.parent / "_build.log"
    if not script.exists():
        print(f"L{nn}: MISSING SCRIPT {script}", flush=True)
        continue
    print(f"\n===== START L{nn} {time.strftime('%H:%M:%S')} =====", flush=True)
    t0 = time.time()
    with open(log, "w", encoding="utf-8") as fh:
        r = subprocess.run([PY, str(script)], stdout=fh, stderr=subprocess.STDOUT)
    dt = time.time() - t0
    print(f"===== END L{nn} rc={r.returncode} {dt:.1f}s =====", flush=True)
    tail = log.read_text(encoding="utf-8", errors="ignore").splitlines()[-8:]
    for line in tail:
        print(f"  L{nn}| {line}", flush=True)

print("\nALL BUILDS FINISHED", flush=True)
