# -*- coding: utf-8 -*-
import json
import os
from pathlib import Path

BASE_DIR = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses")

# Paths
MASTER_SCRIPT_PATH = BASE_DIR / "differential_equations" / "lesson_03_linear_systems" / "dubbing_pipeline" / "3b1b_diffeq_l03_bangla_master_script.json"
AUDIO_DIR = BASE_DIR / "web_platform" / "assets" / "audio" / "differential_equations" / "lesson_03"
MANIFEST_JSON_PATH = AUDIO_DIR / "manifest.json"
MANIFEST_JS_PATH = AUDIO_DIR / "manifest.js"
LESSON_DATA_PATH = BASE_DIR / "web_platform" / "data" / "differential_equations" / "lesson_03.json"

MASTER_SCRIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
LESSON_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

print("Writing generator script...")
