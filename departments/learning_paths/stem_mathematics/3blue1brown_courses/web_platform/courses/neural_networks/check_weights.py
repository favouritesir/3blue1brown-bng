import json

with open("departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/neural_networks/nn_weights.json") as f:
    weights = json.load(f)

print("Keys in weights:", weights.keys())
print("W1 len:", len(weights["W1"]), "cols:", len(weights["W1"][0]))
print("b1 len:", len(weights["b1"]))
print("W2 len:", len(weights["W2"]), "cols:", len(weights["W2"][0]))
print("b2 len:", len(weights["b2"]))
print("W3 len:", len(weights["W3"]), "cols:", len(weights["W3"][0]))
print("b3 len:", len(weights["b3"]))
