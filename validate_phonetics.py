#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from pathlib import Path

base = Path(r"D:\0PEN CODE\Dub Studio\departments\learning_paths\stem_mathematics\3blue1brown_courses\essence_of_linear_algebra")
scripts = {
    "L01": base / "lesson_01_vectors/dubbing_pipeline/3b1b_lesson_01_bangla_master_script.json",
    "L02": base / "lesson_02_span/dubbing_pipeline/3b1b_lesson_02_bangla_master_script.json",
    "L03": base / "lesson_03_linear_transformations/dubbing_pipeline/3b1b_lesson_03_bangla_master_script.json",
    "L04": base / "lesson_04_matrix_multiplication/dubbing_pipeline/3b1b_lesson_04_bangla_master_script.json",
    "L05": base / "lesson_05_3d_transformations/dubbing_pipeline/3b1b_lesson_05_bangla_master_script.json",
}

bad_patterns = [
    "x-\u0985\u0995\u09cd\u09b7",  # x-অক্ষ
    "y-\u0985\u0995\u09cd\u09b7",  # y-অক্ষ
    "z-\u0985\u0995\u09cd\u09b7",  # z-অক্ষ
    "i-hat", "j-hat", "k-hat",
    "i_hat", "j_hat", "k_hat",
    "xy-\u09aa\u09cd\u09b2\u09c7\u09a8",  # xy-প্লেন
    "2D", "3D"
]

print("=" * 60)
print("POST-FIX VALIDATION REPORT")
print("=" * 60)
all_pass = True
for label, path in scripts.items():
    data = json.loads(path.read_text(encoding="utf-8"))
    issues = []
    for cue in data:
        bn = cue.get("bn", "")
        for pat in bad_patterns:
            if pat in bn:
                issues.append("  Cue %d: %r in: %s" % (cue["id"], pat, bn[:80]))
    if issues:
        all_pass = False
        print("FAIL %s:" % label)
        for i in issues:
            print(i)
    else:
        print("PASS %s: ALL CLEAN" % label)

print("=" * 60)
if all_pass:
    print("ALL SCRIPTS PHONETICALLY CLEAN!")
else:
    print("ISSUES FOUND - see above")
