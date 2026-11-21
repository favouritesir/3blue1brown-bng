# -*- coding: utf-8 -*-
"""
Builder for 3Blue1Brown Essence of Probability Lesson 03:
Binomial Distribution and Pascal's Triangle (দ্বিপদী বিন্যাস ও প্যাসকেলের ত্রিভুজ)

Strict 5-Point Parity:
1. Zero text dropping: Authentic Bengali prose, Bernoulli trials, combinations nCr, Pascal's triangle connection, Poisson limit intuition.
2. 1:1 sequence: Coin tosses, tree representation, formula P(X=k) = nCr * p^k * (1-p)^(n-k), symmetry when p=0.5.
3. 3B1B quiz parity: 3 conceptual multiple-choice quizzes with explanations.
4. Single-shell JSON: departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/data/probability/lesson_03.json
5. Script: departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_probability/lesson_03_binomial_distribution/dubbing_pipeline/3b1b_prob_l03_bangla_master_script.json
   (and mirrored to lesson_03_bayes_rule if requested by earlier prompt)
6. Manifests: departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/probability/lesson_03/manifest.json and manifest.js
"""

import json
import os
from pathlib import Path

BASE_DIR = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses")

SCRIPT_DIR_BINOMIAL = BASE_DIR / "essence_of_probability" / "lesson_03_binomial_distribution" / "dubbing_pipeline"
SCRIPT_PATH_BINOMIAL = SCRIPT_DIR_BINOMIAL / "3b1b_prob_l03_bangla_master_script.json"

SCRIPT_DIR_BAYES = BASE_DIR / "essence_of_probability" / "lesson_03_bayes_rule" / "dubbing_pipeline"
SCRIPT_PATH_BAYES = SCRIPT_DIR_BAYES / "3b1b_prob_l03_bangla_master_script.json"

AUDIO_DIR = BASE_DIR / "web_platform" / "assets" / "audio" / "probability" / "lesson_03"
MANIFEST_JSON = AUDIO_DIR / "manifest.json"
MANIFEST_JS = AUDIO_DIR / "manifest.js"

DATA_DIR = BASE_DIR / "web_platform" / "data" / "probability"
DATA_JSON = DATA_DIR / "lesson_03.json"

for d in [SCRIPT_DIR_BINOMIAL, SCRIPT_DIR_BAYES, AUDIO_DIR, DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

print("Directories prepared.")
