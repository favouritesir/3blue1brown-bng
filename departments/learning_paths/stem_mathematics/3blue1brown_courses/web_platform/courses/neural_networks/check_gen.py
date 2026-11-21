import json
import base64

with open("departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/neural_networks/weights_b64.txt") as f:
    weights_b64 = f.read().strip()

print(f"Loaded b64 weights: {len(weights_b64)} chars")
