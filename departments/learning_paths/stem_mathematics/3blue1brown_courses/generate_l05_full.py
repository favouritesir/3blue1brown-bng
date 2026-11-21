# -*- coding: utf-8 -*-
"""
Generator for:
1. 3b1b_diffeq_l05_bangla_master_script.json (45+ timed cues)
2. Audio Manifest (manifest.json, manifest.js, and sec_01..05_cues.json)
3. Single-Shell Lesson Data JSON (lesson_05.json)
"""

import json
from pathlib import Path

BASE_DIR = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses")

# Target Paths
MASTER_SCRIPT_DIR = BASE_DIR / "differential_equations" / "lesson_05_harmonic_oscillator" / "dubbing_pipeline"
MASTER_SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
MASTER_SCRIPT_FILE = MASTER_SCRIPT_DIR / "3b1b_diffeq_l05_bangla_master_script.json"

AUDIO_DIR = BASE_DIR / "web_platform" / "assets" / "audio" / "differential_equations" / "lesson_05"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = BASE_DIR / "web_platform" / "data" / "differential_equations"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / "lesson_05.json"

print("Building Lesson 05 resources...")
