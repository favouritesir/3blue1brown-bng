# -*- coding: utf-8 -*-
"""
Production Resource Builder for Differential Equations Lesson 05:
Harmonic Oscillators, Damping, and Resonance (সরল স্পন্দন গতি, অবমন্দিত দোলন ও অনুরণন)
"""

import json
import os
from pathlib import Path

# Paths
BASE_DIR = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses")

MASTER_SCRIPT_DIR = BASE_DIR / "differential_equations" / "lesson_05_harmonic_oscillator" / "dubbing_pipeline"
MASTER_SCRIPT_FILE = MASTER_SCRIPT_DIR / "3b1b_diffeq_l05_bangla_master_script.json"

AUDIO_ASSETS_DIR = BASE_DIR / "web_platform" / "assets" / "audio" / "differential_equations" / "lesson_05"
AUDIO_MANIFEST_JSON = AUDIO_ASSETS_DIR / "manifest.json"
AUDIO_MANIFEST_JS = AUDIO_ASSETS_DIR / "manifest.js"

DATA_DIR = BASE_DIR / "web_platform" / "data" / "differential_equations"
DATA_JSON_FILE = DATA_DIR / "lesson_05.json"

for d in [MASTER_SCRIPT_DIR, AUDIO_ASSETS_DIR, DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

print("Directories verified.")
