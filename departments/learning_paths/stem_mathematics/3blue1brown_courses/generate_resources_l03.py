# -*- coding: utf-8 -*-
import json
import os
from pathlib import Path

BASE_DIR = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses")

# 1. Master Script Path
MASTER_SCRIPT_PATH = BASE_DIR / "differential_equations" / "lesson_03_linear_systems" / "dubbing_pipeline" / "3b1b_diffeq_l03_bangla_master_script.json"
MASTER_SCRIPT_PATH.parent.mkdir(parents=True, exist_ok=True)

# 2. Audio Manifest Paths
AUDIO_DIR = BASE_DIR / "web_platform" / "assets" / "audio" / "differential_equations" / "lesson_03"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_JSON_PATH = AUDIO_DIR / "manifest.json"
MANIFEST_JS_PATH = AUDIO_DIR / "manifest.js"

# 3. Lesson Data JSON Path
DATA_DIR = BASE_DIR / "web_platform" / "data" / "differential_equations"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LESSON_DATA_PATH = DATA_DIR / "lesson_03.json"

print("Paths configured.")
