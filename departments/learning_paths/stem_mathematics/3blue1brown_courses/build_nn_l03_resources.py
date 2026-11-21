# -*- coding: utf-8 -*-
"""
Builder script for 3Blue1Brown Neural Networks Lesson 03:
"What is backpropagation really doing?" / "ব্যাকপ্রপাগেশন আসলে কী করে?"

Produces:
1. Master Dubbing Script JSON:
   departments/learning_paths/stem_mathematics/3blue1brown_courses/neural_networks/lesson_03_backpropagation/dubbing_pipeline/3b1b_nn_l03_bangla_master_script.json
2. Audio Manifest JSON & JS:
   departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/neural_networks/lesson_03/manifest.json
   departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/neural_networks/lesson_03/manifest.js
3. Single-Shell Lesson Data JSON:
   departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/data/neural_networks/lesson_03.json
"""

import json
import os
from pathlib import Path

BASE_DIR = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses")

# Target Paths
MASTER_SCRIPT_DIR = BASE_DIR / "neural_networks" / "lesson_03_backpropagation" / "dubbing_pipeline"
MASTER_SCRIPT_PATH = MASTER_SCRIPT_DIR / "3b1b_nn_l03_bangla_master_script.json"

AUDIO_MANIFEST_DIR = BASE_DIR / "web_platform" / "assets" / "audio" / "neural_networks" / "lesson_03"
AUDIO_MANIFEST_JSON = AUDIO_MANIFEST_DIR / "manifest.json"
AUDIO_MANIFEST_JS = AUDIO_MANIFEST_DIR / "manifest.js"

DATA_DIR = BASE_DIR / "web_platform" / "data" / "neural_networks"
DATA_JSON_PATH = DATA_DIR / "lesson_03.json"

for d in [MASTER_SCRIPT_DIR, AUDIO_MANIFEST_DIR, DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

print("Target directories verified.")
