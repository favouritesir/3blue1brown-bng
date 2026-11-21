# -*- coding: utf-8 -*-
"""
Script to generate:
1. Master Dubbing Script (JSON): 3b1b_diffeq_l01_bangla_master_script.json
2. Audio Manifests (JSON & JS) + Synthesize Section Audio MP3s with Edge-TTS
3. Single-Shell Lesson Data JSON: lesson_01.json
"""

import os
import json
import asyncio
import subprocess
from pathlib import Path
import edge_tts

BASE_DIR = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses")

MASTER_SCRIPT_PATH = BASE_DIR / "differential_equations/lesson_01_intro/dubbing_pipeline/3b1b_diffeq_l01_bangla_master_script.json"
AUDIO_DIR = BASE_DIR / "web_platform/assets/audio/differential_equations/lesson_01"
DATA_PATH = BASE_DIR / "web_platform/data/differential_equations/lesson_01.json"

MASTER_SCRIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

print("Starting resource creation...")
