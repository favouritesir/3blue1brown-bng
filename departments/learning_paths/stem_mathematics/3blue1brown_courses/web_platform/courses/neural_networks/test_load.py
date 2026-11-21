# Python generator for lesson_01.html
import os
import json

with open("departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/neural_networks/weights_b64.txt", "r") as f:
    b64_weights = f.read().strip()

print("Base64 weights loaded:", len(b64_weights))
