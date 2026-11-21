# -*- coding: utf-8 -*-
"""Dry-run: validate all 4 Fractals builder scripts without any TTS/network."""
import importlib
from fractals_audio_common import assert_clean_scripts

TOTALS = {1: 34, 2: 37, 3: 30, 4: 29}
for n in range(1, 5):
    mod = importlib.import_module(f"build_expressive_teacher_audio_fractals_{n:02d}")
    count = assert_clean_scripts(mod.SECTIONS_DATA, mod.EXPECTED_TYPES,
                                 mod.EXPECTED_FILES, TOTALS[n])
    figures = sum(1 for s in mod.SECTIONS_DATA.values() for c in s["cues"]
                  if c["type"] == "figure")
    print(f"lesson_{n:02d}: OK  {count} cues, {figures} figure explanations, "
          f"{len(mod.SECTIONS_DATA)} sections")
print("ALL SCRIPT VALIDATIONS PASSED")
