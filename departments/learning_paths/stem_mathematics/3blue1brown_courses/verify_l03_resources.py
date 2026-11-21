# -*- coding: utf-8 -*-
"""
Verification Script for Differential Equations Lesson 03 Resources
"""

import json
from pathlib import Path

BASE_DIR = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses")

files_to_check = [
    BASE_DIR / "differential_equations" / "lesson_03_oscillations" / "dubbing_pipeline" / "3b1b_diffeq_l03_bangla_master_script.json",
    BASE_DIR / "differential_equations" / "lesson_03_linear_systems" / "dubbing_pipeline" / "3b1b_diffeq_l03_bangla_master_script.json",
    BASE_DIR / "web_platform" / "assets" / "audio" / "differential_equations" / "lesson_03" / "manifest.json",
    BASE_DIR / "web_platform" / "assets" / "audio" / "differential_equations" / "lesson_03" / "manifest.js",
    BASE_DIR / "web_platform" / "data" / "differential_equations" / "lesson_03.json"
]

all_ok = True
for f in files_to_check:
    if f.exists():
        size = f.stat().st_size
        print(f"[OK] {f} exists ({size:,} bytes)")
    else:
        print(f"[FAIL] {f} missing!")
        all_ok = False

# Validate JSON files
json_files = [f for f in files_to_check if f.suffix == ".json"]
for jf in json_files:
    try:
        with open(jf, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                print(f"     -> Valid JSON array with {len(data)} items")
            elif isinstance(data, dict):
                print(f"     -> Valid JSON object with keys: {list(data.keys())[:5]}")
    except Exception as e:
        print(f"     -> [JSON ERROR] {jf}: {e}")
        all_ok = False

# Validate JS manifest
js_file = BASE_DIR / "web_platform" / "assets" / "audio" / "differential_equations" / "lesson_03" / "manifest.js"
with open(js_file, "r", encoding="utf-8") as f:
    js_content = f.read()
    if js_content.startswith("window.TEACHER_AUDIO_MANIFEST =") and js_content.strip().endswith(";"):
        print("[OK] manifest.js has valid window.TEACHER_AUDIO_MANIFEST assignment.")
    else:
        print("[FAIL] manifest.js structure invalid!")
        all_ok = False

print("\nResource verification completed. All tests passed:", all_ok)
