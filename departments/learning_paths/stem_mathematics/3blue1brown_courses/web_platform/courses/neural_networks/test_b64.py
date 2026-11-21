import numpy as np
import json
import base64

with open("departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/neural_networks/weights_16_16.json") as f:
    data = json.load(f)

w1 = np.array(data["W1"], dtype=np.float32).flatten()
b1 = np.array(data["b1"], dtype=np.float32).flatten()
w2 = np.array(data["W2"], dtype=np.float32).flatten()
b2 = np.array(data["b2"], dtype=np.float32).flatten()
w3 = np.array(data["W3"], dtype=np.float32).flatten()
b3 = np.array(data["b3"], dtype=np.float32).flatten()

all_floats = np.concatenate([w1, b1, w2, b2, w3, b3])
b64 = base64.b64encode(all_floats.tobytes()).decode('ascii')
print(f"Total floats: {len(all_floats)}, Base64 string length: {len(b64)}")

# Verify reconstruction
decoded = np.frombuffer(base64.b64decode(b64), dtype=np.float32)
print("Max diff:", np.max(np.abs(all_floats - decoded)))
