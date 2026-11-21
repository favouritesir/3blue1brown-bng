# Build lesson_01.html with embedded trained weights and complete interactive modules
import json

with open("departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/neural_networks/nn_weights.json") as f:
    weights_json_str = f.read()

print("Loaded weights JSON length:", len(weights_json_str))
