# -*- coding: utf-8 -*-
"""
Generator for Differential Equations Lesson 03 Resources:
1. Master Dubbing Script (JSON)
2. Audio Manifest (JSON & JS)
3. Lesson Data JSON (with full KaTeX & Quizzes)
"""

import json
import os
from pathlib import Path

BASE_DIR = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses")

# 1. Master Script
MASTER_SCRIPT_PATH = BASE_DIR / "differential_equations" / "lesson_03_linear_systems" / "dubbing_pipeline" / "3b1b_diffeq_l03_bangla_master_script.json"
MASTER_SCRIPT_PATH.parent.mkdir(parents=True, exist_ok=True)

# 2. Audio Manifest
AUDIO_MANIFEST_DIR = BASE_DIR / "web_platform" / "assets" / "audio" / "differential_equations" / "lesson_03"
AUDIO_MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_MANIFEST_JSON = AUDIO_MANIFEST_DIR / "manifest.json"
AUDIO_MANIFEST_JS = AUDIO_MANIFEST_DIR / "manifest.js"

# 3. Lesson Data JSON
DATA_DIR = BASE_DIR / "web_platform" / "data" / "differential_equations"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_JSON_PATH = DATA_DIR / "lesson_03.json"

print("Setup paths complete.")
