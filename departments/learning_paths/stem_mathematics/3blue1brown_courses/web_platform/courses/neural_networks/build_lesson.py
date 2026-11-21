import json

# Read the trained weights
with open("departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/neural_networks/nn_weights.json", "r", encoding="utf-8") as f:
    weights_json = f.read().strip()

print("Loaded weights JSON:", len(weights_json), "bytes")
