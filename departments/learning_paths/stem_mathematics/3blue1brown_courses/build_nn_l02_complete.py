import json
import os
from pathlib import Path

# Base paths
BASE_DIR = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses")

MASTER_SCRIPT_PATH = BASE_DIR / "neural_networks" / "lesson_02_gradient_descent" / "dubbing_pipeline" / "3b1b_nn_l02_bangla_master_script.json"
AUDIO_DIR = BASE_DIR / "web_platform" / "assets" / "audio" / "neural_networks" / "lesson_02"
MANIFEST_JSON_PATH = AUDIO_DIR / "manifest.json"
MANIFEST_JS_PATH = AUDIO_DIR / "manifest.js"
LESSON_DATA_PATH = BASE_DIR / "web_platform" / "data" / "neural_networks" / "lesson_02.json"

MASTER_SCRIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
LESSON_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

print("Writing generator script for complete Neural Networks Lesson 02 resources...")
