import numpy as np
import json
from train_tiny_mlp import get_digit_template

np.random.seed(42)

def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -15, 15)))

def d_sigmoid(a):
    return a * (1.0 - a)

def softmax(z):
    ez = np.exp(z - np.max(z, axis=-1, keepdims=True))
    return ez / np.sum(ez, axis=-1, keepdims=True)

X_list = []
y_list = []

for digit in range(10):
    tmpl = get_digit_template(digit)
    for _ in range(35):
        X_list.append(tmpl.flatten())
        y_list.append(digit)
    for _ in range(150):
        sx = np.random.choice([-1, 0, 1])
        sy = np.random.choice([-1, 0, 1])
        shifted = np.roll(np.roll(tmpl, sy, axis=0), sx, axis=1)
        scale = np.random.uniform(0.7, 1.0)
        noise = np.random.uniform(0, 0.05, (16, 16))
        sample = np.clip(shifted * scale + noise, 0.0, 1.0)
        X_list.append(sample.flatten())
        y_list.append(digit)

X = np.array(X_list)
Y = np.zeros((len(y_list), 10))
for i, d in enumerate(y_list):
    Y[i, d] = 1.0

# 256 -> 16 -> 16 -> 10 (Matching 3B1B exact hidden layer sizes 16 and 16!)
H1 = 16
H2 = 16
W1 = np.random.randn(256, H1) * 0.1
b1 = np.zeros(H1)
W2 = np.random.randn(H1, H2) * 0.15
b2 = np.zeros(H2)
W3 = np.random.randn(H2, 10) * 0.2
b3 = np.zeros(10)

lr = 0.3
for epoch in range(1500):
    z1 = np.dot(X, W1) + b1
    a1 = sigmoid(z1)
    z2 = np.dot(a1, W2) + b2
    a2 = sigmoid(z2)
    z3 = np.dot(a2, W3) + b3
    probs = softmax(z3)
    
    dz3 = (probs - Y) / len(X)
    dW3 = np.dot(a2.T, dz3)
    db3 = np.sum(dz3, axis=0)
    
    da2 = np.dot(dz3, W3.T)
    dz2 = da2 * d_sigmoid(a2)
    dW2 = np.dot(a1.T, dz2)
    db2 = np.sum(dz2, axis=0)
    
    da1 = np.dot(dz2, W2.T)
    dz1 = da1 * d_sigmoid(a1)
    dW1 = np.dot(X.T, dz1)
    db1 = np.sum(dz1, axis=0)
    
    W1 -= lr * dW1
    b1 -= lr * db1
    W2 -= lr * dW2
    b2 -= lr * db2
    W3 -= lr * dW3
    b3 -= lr * db3

preds = np.argmax(probs, axis=1)
acc = np.mean(preds == np.array(y_list)) * 100
print(f"Accuracy with H1=16, H2=16: {acc:.1f}%")

for d in range(10):
    tmpl = get_digit_template(d).flatten()
    z1 = np.dot(tmpl, W1) + b1
    a1 = sigmoid(z1)
    z2 = np.dot(a1, W2) + b2
    a2 = sigmoid(z2)
    z3 = np.dot(a2, W3) + b3
    p = softmax(z3)
    pred = np.argmax(p)
    print(f"Digit {d} -> pred {pred} ({p[pred]*100:.1f}%)")

weights_export = {
    "W1": np.round(W1, 4).tolist(),
    "b1": np.round(b1, 4).tolist(),
    "W2": np.round(W2, 4).tolist(),
    "b2": np.round(b2, 4).tolist(),
    "W3": np.round(W3, 4).tolist(),
    "b3": np.round(b3, 4).tolist(),
}
with open("departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/neural_networks/weights_16_16.json", "w") as f:
    json.dump(weights_export, f)
print("Saved weights_16_16.json!")
