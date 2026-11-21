# -*- coding: utf-8 -*-
"""Scan every analysis builder cue text for any character outside the allowed
Bengali/ASCII/punctuation set (catches stray Devanagari/Arabic/etc.)."""
import importlib

ALLOWED_RANGES = [(0x0980, 0x09FF), (0x0020, 0x007E)]  # Bengali block, ASCII printable
ALLOWED_EXTRA = set("।্\n\t东盟")  # danda + virama already in Bengali block; newline/tab

for n in range(1, 11):
    mod = importlib.import_module(f"build_expressive_teacher_audio_analysis{n:02d}")
    bad = {}
    for sid, sec in mod.SECTIONS_DATA.items():
        for cue in sec["cues"]:
            for ch in cue["tts"]:
                cp = ord(ch)
                if ch in ALLOWED_EXTRA:
                    continue
                if any(a <= cp <= b for a, b in ALLOWED_RANGES):
                    continue
                bad.setdefault(ch, []).append(f"{sid}/{cue['index']}")
    if bad:
        for ch, locs in bad.items():
            print(f"lesson_{n:02d}: U+{ord(ch):04X} {ch!r} at {locs[:6]} (x{len(locs)})")
    else:
        print(f"lesson_{n:02d}: clean")
