import base64
import json
import os

with open("departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/neural_networks/weights_b64.txt", "r", encoding="utf-8") as f:
    weights_b64 = f.read().strip()

print(f"Weights Base64 loaded: {len(weights_b64)} chars")
