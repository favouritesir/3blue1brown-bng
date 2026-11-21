# -*- coding: utf-8 -*-
"""Run puzzle builds with a small bounded worker pool (3 concurrent builds).

Each build is independent and writes only into its own NEW experiment folder.
edge_tts transient errors are handled inside each build script (12 attempts +
half/sentence split fallbacks).
"""
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSES = HERE.parent.parent
PY = sys.executable
WORKERS = 4
LESSONS = [int(x) for x in sys.argv[1:]] or [1, 2, 3, 4, 5, 6, 7, 8, 9]


def run_one(n):
    nn = f"{n:02d}"
    script = (COURSES / "puzzles" / f"lesson_{nn}" / "dubbing_pipeline" /
              "experiments" / "clean_timesync_v2" / f"build_puz{nn}_clean.py")
    log = script.parent / "_build.log"
    t0 = time.time()
    with open(log, "w", encoding="utf-8") as fh:
        r = subprocess.run([PY, str(script)], stdout=fh, stderr=subprocess.STDOUT)
    tail = log.read_text(encoding="utf-8", errors="ignore").splitlines()[-7:]
    return n, r.returncode, time.time() - t0, tail


def main():
    results = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(run_one, n): n for n in LESSONS}
        for fut in as_completed(futs):
            n, rc, dt, tail = fut.result()
            results.append((n, rc, dt))
            print(f"\n===== L{n:02d} DONE rc={rc} {dt:.1f}s =====", flush=True)
            for line in tail:
                print(f"  L{n:02d}| {line}", flush=True)
    results.sort()
    print("\nSUMMARY", [(f"L{n:02d}", rc, round(dt)) for n, rc, dt in results], flush=True)


if __name__ == "__main__":
    main()
