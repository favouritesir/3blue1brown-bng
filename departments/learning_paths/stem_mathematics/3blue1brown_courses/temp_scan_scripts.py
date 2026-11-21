import re
from pathlib import Path
ROOT = Path(".")
hits = 0
for i in range(1, 14):
    p = (ROOT / "physics" / f"lesson_{i:02d}" / "dubbing_pipeline" / "experiments"
         / "clean_timesync_v2" / f"build_phys{i:02d}_clean.py")
    s = p.read_text(encoding="utf-8")
    for n, line in enumerate(s.splitlines(), 1):
        for ch in line:
            cp = ord(ch)
            if (0x4E00 <= cp <= 0x9FFF) or (0x0900 <= cp <= 0x097F and cp not in (0x0964, 0x0965)):
                print(f"{p.name}:{n}: U+{cp:04X} {ch!r}")
                hits += 1
print(f"foreign-script chars found: {hits}")
