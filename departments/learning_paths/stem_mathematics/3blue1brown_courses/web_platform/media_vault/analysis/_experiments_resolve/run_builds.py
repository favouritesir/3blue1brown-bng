# -*- coding: utf-8 -*-
"""Run lesson build scripts sequentially; log each to its experiment folder."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WEB = HERE.parents[2]
VAULT = WEB / "media_vault" / "analysis"

for nn in sys.argv[1:]:
    script = (VAULT / f"lesson_{nn}" / "dubbing_pipeline" / "experiments"
              / "clean_timesync_v2" / f"build_an{nn}_clean.py")
    log = script.parent / "build.log"
    print(f"BUILD L{nn} -> {log}", flush=True)
    with open(log, "w", encoding="utf-8") as fh:
        rc = subprocess.run([sys.executable, str(script)], stdout=fh,
                            stderr=subprocess.STDOUT).returncode
    print(f"BUILD L{nn} rc={rc}", flush=True)
