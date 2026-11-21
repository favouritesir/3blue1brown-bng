"""Run the 8 (remaining) Why-Pi dub builds sequentially with per-lesson logs."""
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WHYPI = HERE.parent.parent.parent
ROOT = WHYPI.parents[6]  # workspace root (Dub Studio)

only = sys.argv[1:] or ["02", "03", "04", "05", "06", "07", "08"]
for nn in only:
    script = WHYPI / f"lesson_{nn}" / "dubbing_pipeline" / "experiments" / "clean_timesync_v2" / f"build_why_pi{nn}_clean.py"
    log = script.parent / "_build.log"
    print(f"=== BUILD L{nn} start {time.strftime('%H:%M:%S')} ===", flush=True)
    with open(log, "w", encoding="utf-8") as fh:
        r = subprocess.run([sys.executable, str(script)], cwd=str(ROOT),
                           stdout=fh, stderr=subprocess.STDOUT)
    tail = log.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
    print(f"=== BUILD L{nn} rc={r.returncode} end {time.strftime('%H:%M:%S')} ===", flush=True)
    for line in tail[-6:]:
        print("   " + line, flush=True)
