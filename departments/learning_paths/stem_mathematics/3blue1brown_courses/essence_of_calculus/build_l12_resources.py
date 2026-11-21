# -*- coding: utf-8 -*-
"""
Builder for 3Blue1Brown Essence of Calculus - Lesson 12:
"What is a function really? / ফাংশন আসলে কী?"

Generates:
1. Authentic Bengali master script:
   departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_calculus/lesson_12_what_is_a_function/dubbing_pipeline/3b1b_calc_l12_bangla_master_script.json
2. Audio cues manifest:
   departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/calculus/lesson_12/manifest.json
   departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/calculus/lesson_12/manifest.js
3. Single-Shell Lesson Data JSON:
   departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/data/calculus/lesson_12.json
"""

import os
import json

base_dir = os.path.abspath(r"departments/learning_paths/stem_mathematics/3blue1brown_courses")

script_dir = os.path.join(base_dir, r"essence_of_calculus/lesson_12_what_is_a_function/dubbing_pipeline")
audio_dir = os.path.join(base_dir, r"web_platform/assets/audio/calculus/lesson_12")
data_dir = os.path.join(base_dir, r"web_platform/data/calculus")

os.makedirs(script_dir, exist_ok=True)
os.makedirs(audio_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

print("Directories ensured.")
