"""Run the generated per-lesson build scripts sequentially and log each one."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
lessons = [int(x) for x in sys.argv[1:]] or list(range(2, 14))
results = {}
for i in lessons:
    script = (ROOT / "physics" / f"lesson_{i:02d}" / "dubbing_pipeline" / "experiments"
              / "clean_timesync_v2" / f"build_phys{i:02d}_clean.py")
    log = ROOT / f"temp_build_{i:02d}.log"
    print(f"[runner] starting lesson {i:02d} -> {log.name}", flush=True)
    with open(log, "w", encoding="utf-8") as fh:
        r = subprocess.run([sys.executable, str(script)], stdout=fh, stderr=subprocess.STDOUT,
                           cwd=str(ROOT))
    results[f"lesson_{i:02d}"] = r.returncode
    print(f"[runner] lesson {i:02d} exit={r.returncode}", flush=True)
print("BUILD_RESULTS:", results, flush=True)
