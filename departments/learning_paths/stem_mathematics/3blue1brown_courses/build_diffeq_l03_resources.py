import json
import os
from pathlib import Path

# Base directories
BASE_DIR = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses")

MASTER_SCRIPT_DIR = BASE_DIR / "differential_equations" / "lesson_03_linear_systems" / "dubbing_pipeline"
AUDIO_DIR = BASE_DIR / "web_platform" / "assets" / "audio" / "differential_equations" / "lesson_03"
DATA_DIR = BASE_DIR / "web_platform" / "data" / "differential_equations"

MASTER_SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

print("Directories prepared successfully.")
