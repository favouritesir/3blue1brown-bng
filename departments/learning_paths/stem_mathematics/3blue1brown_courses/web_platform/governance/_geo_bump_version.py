# -*- coding: utf-8 -*-
"""Bump geometry lesson page manifest.js cache-busting version 7 -> 8."""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.abspath(os.path.join(HERE, '..', 'courses', 'geometry'))
for n in range(1, 7):
    path = os.path.join(PAGES, f'lesson_{n:02d}.html')
    with open(path, encoding='utf-8', newline='') as fh:
        text = fh.read()
    new, count = re.subn(r'(manifest\.js\?v=)7\b', r'\g<1>8', text)
    if count != 1:
        raise SystemExit(f'lesson_{n:02d}: expected 1 version bump, got {count}')
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(new)
    print(f'lesson_{n:02d}: manifest.js?v=7 -> ?v=8')
