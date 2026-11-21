# -*- coding: utf-8 -*-
"""
Builder for Differential Equations Lesson 03: Oscillations and Harmonic Motion
Generates:
1. Master Dubbing Script (JSON) in lesson_03_oscillations/dubbing_pipeline and lesson_03_linear_systems/dubbing_pipeline
2. Audio Manifests (manifest.json and manifest.js)
3. Single-Shell Lesson Data JSON (lesson_03.json)
"""

import json
import os
from pathlib import Path

BASE_DIR = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses")

# Master script paths
SCRIPT_DIR_OSC = BASE_DIR / "differential_equations" / "lesson_03_oscillations" / "dubbing_pipeline"
SCRIPT_DIR_LIN = BASE_DIR / "differential_equations" / "lesson_03_linear_systems" / "dubbing_pipeline"
SCRIPT_DIR_OSC.mkdir(parents=True, exist_ok=True)
SCRIPT_DIR_LIN.mkdir(parents=True, exist_ok=True)

MASTER_SCRIPT_PATH_OSC = SCRIPT_DIR_OSC / "3b1b_diffeq_l03_bangla_master_script.json"
MASTER_SCRIPT_PATH_LIN = SCRIPT_DIR_LIN / "3b1b_diffeq_l03_bangla_master_script.json"

# Audio Manifest paths
AUDIO_DIR = BASE_DIR / "web_platform" / "assets" / "audio" / "differential_equations" / "lesson_03"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_JSON_PATH = AUDIO_DIR / "manifest.json"
MANIFEST_JS_PATH = AUDIO_DIR / "manifest.js"

# Lesson Data JSON path
DATA_DIR = BASE_DIR / "web_platform" / "data" / "differential_equations"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LESSON_DATA_PATH = DATA_DIR / "lesson_03.json"

print("All target directories verified.")
