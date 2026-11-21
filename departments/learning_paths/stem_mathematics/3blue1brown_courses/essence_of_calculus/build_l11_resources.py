# -*- coding: utf-8 -*-
"""
Builder for 3Blue1Brown Essence of Calculus - Lesson 11:
"What is pi, and why does it appear in calculus? / পাই আসলে কী এবং ক্যালকুলাসে এটি কেন দেখা যায়?"

Generates:
1. 3b1b_calculus_l11_bangla_master_script.json
2. manifest.json, manifest.js and section cue json files
3. lesson_11.json (Single-shell structured lesson data with full KaTeX formulas and quizzes)
"""

import os
import json

base_dir = os.path.abspath(r"departments/learning_paths/stem_mathematics/3blue1brown_courses")

script_dir = os.path.join(base_dir, r"essence_of_calculus/lesson_11_what_is_pi/dubbing_pipeline")
audio_dir = os.path.join(base_dir, r"web_platform/assets/audio/calculus/lesson_11")
data_dir = os.path.join(base_dir, r"web_platform/data/calculus")

os.makedirs(script_dir, exist_ok=True)
os.makedirs(audio_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

print("Directories ensured.")
