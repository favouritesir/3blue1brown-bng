# -*- coding: utf-8 -*-
"""
Generator for Essence of Probability Lesson 06:
Central Limit Theorem, Hypothesis Testing and p-Values
(কেন্দ্রীয় সীমা উপপাদ্য, অনুমিতি পরীক্ষা ও পি-ভ্যালুর রহস্য)

Generates:
1. Master Dubbing Script (JSON):
   departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_probability/lesson_06_hypothesis_testing/dubbing_pipeline/3b1b_prob_l06_bangla_master_script.json
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
    / "lesson_06_hypothesis_testing"
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

print(f"Target Master Script: {MASTER_SCRIPT_PATH}")
print(f"Target Audio Manifest: {MANIFEST_JSON_PATH}")
print(f"Target Lesson Data: {DATA_JSON_PATH}")
