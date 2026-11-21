import json

with open("departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/neural_networks/nn_weights.json", "r", encoding="utf-8") as f:
    weights_raw = f.read().strip()

# Let's inspect gen_full_html.py logic
print("Weights length:", len(weights_raw))
