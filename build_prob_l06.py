# -*- coding: utf-8 -*-
"""
Builder for 3Blue1Brown Essence of Probability Lesson 06:
Bayes' Rule and the False Positive Dilemma (বেইজের নিয়ম ও মেডিকেল টেস্টের প্যারাডক্স)

Delivers:
1. Authentic Bengali Master Dubbing Script (JSON):
   departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_probability/lesson_06_bayes_dilemma/dubbing_pipeline/3b1b_prob_l06_bangla_master_script.json
2. Audio Manifests (JSON & JS):
   departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/probability/lesson_06/manifest.json
   departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/probability/lesson_06/manifest.js
3. Single-Shell Lesson Data JSON:
   departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/data/probability/lesson_06.json
"""

import json
import os
from pathlib import Path

BASE_DIR = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses")

# Target Paths
MASTER_SCRIPT_DIR = (
    BASE_DIR
    / "essence_of_probability"
    / "lesson_06_bayes_dilemma"
    / "dubbing_pipeline"
)
MASTER_SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
MASTER_SCRIPT_PATH = MASTER_SCRIPT_DIR / "3b1b_prob_l06_bangla_master_script.json"

AUDIO_DIR = BASE_DIR / "web_platform" / "assets" / "audio" / "probability" / "lesson_06"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_JSON_PATH = AUDIO_DIR / "manifest.json"
MANIFEST_JS_PATH = AUDIO_DIR / "manifest.js"

DATA_DIR = BASE_DIR / "web_platform" / "data" / "probability"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_JSON_PATH = DATA_DIR / "lesson_06.json"

print(f"Master script target: {MASTER_SCRIPT_PATH}")
print(f"Manifest JSON target: {MANIFEST_JSON_PATH}")
print(f"Manifest JS target:   {MANIFEST_JS_PATH}")
print(f"Lesson Data JSON:     {DATA_JSON_PATH}")
