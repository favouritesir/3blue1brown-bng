# -*- coding: utf-8 -*-
"""Back up the number-theory placeholder manifests BEFORE the expressive build.
Idempotent: never overwrites an existing backup (so the original placeholder
survives even if this script is re-run after a build)."""
import os, shutil, json, hashlib

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for n in (1, 2, 3):
    src = os.path.join(BASE, "assets", "audio", "number_theory", f"lesson_{n:02d}")
    dst = os.path.join(src, "_backup_before_expressive_build")
    os.makedirs(dst, exist_ok=True)
    for name in ("manifest.json", "manifest.js"):
        s = os.path.join(src, name)
        d = os.path.join(dst, name)
        if not os.path.exists(d):
            shutil.copy2(s, d)
    # Also preserve any pre-existing audio, if present.
    for s in os.listdir(src):
        if s.endswith(".mp3") and not s.startswith("_expressive"):
            d = os.path.join(dst, s)
            if not os.path.exists(d):
                shutil.copy2(os.path.join(src, s), d)
    with open(os.path.join(dst, "manifest.json"), encoding="utf-8") as fh:
        obj = json.load(fh)
    digest = hashlib.sha256(open(os.path.join(dst, "manifest.json"), "rb").read()).hexdigest()[:12]
    print(f"lesson_{n:02d}: backup ready, sections={len(obj['sections'])}, "
          f"cues={sum(len(s['cues']) for s in obj['sections'].values())}, sha256={digest}")
