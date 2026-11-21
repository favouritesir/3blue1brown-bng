# -*- coding: utf-8 -*-
"""One-off: back up all six geometry placeholder manifests before build."""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', 'assets', 'audio', 'geometry'))

for n in range(1, 7):
    d = os.path.join(ROOT, f'lesson_{n:02d}')
    bak = os.path.join(d, '_backup_before_expressive_build')
    os.makedirs(bak, exist_ok=True)
    for name in ('manifest.json', 'manifest.js'):
        src = os.path.join(d, name)
        dst = os.path.join(bak, name)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
            print(f'lesson_{n:02d}: backed up {name}')
        else:
            print(f'lesson_{n:02d}: backup already present for {name}')
