import numpy as np
import json

# Optimize training for 100% prototype accuracy and high noise resilience
np.random.seed(42)

def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -25, 25)))

def d_sigmoid(a):
    return a * (1.0 - a)

def softmax(z):
    e = np.exp(z - np.max(z, axis=-1, keepdims=True))
    return e / np.sum(e, axis=-1, keepdims=True)

def make_digit(d):
    grid = np.zeros((16, 16))
    if d == 0:
        for y in range(2, 14):
            for x in range(3, 13):
                dx = (x - 7.5) / 3.6
                dy = (y - 7.5) / 4.6
                r2 = dx*dx + dy*dy
                if 0.5 <= r2 <= 1.25: grid[y, x] = 1.0
    elif d == 1:
        for y in range(2, 14):
            grid[y, 8] = 1.0
            grid[y, 7] = 0.5
        for x in range(5, 12): grid[13, x] = 1.0
        for i in range(3): grid[2 + i, 8 - i] = 0.8
    elif d == 2:
        for x in range(4, 12): grid[2, x] = 1.0
        for y in range(3, 7): grid[y, 11] = 1.0
        for x in range(5, 11): grid[7, x] = 1.0
        for i in range(6): grid[8 + i, 10 - int(i * 1.1)] = 1.0
        for x in range(3, 13): grid[13, x] = 1.0
    elif d == 3:
        for x in range(4, 12):
            grid[2, x] = 1.0; grid[7, x] = 1.0; grid[13, x] = 1.0
        for y in range(3, 7): grid[y, 11] = 1.0
        for y in range(8, 13): grid[y, 11] = 1.0
    elif d == 4:
        for y in range(2, 9): grid[y, 4] = 1.0
        for x in range(3, 13): grid[8, x] = 1.0
        for y in range(2, 14): grid[y, 10] = 1.0
    elif d == 5:
        for x in range(4, 12):
            grid[2, x] = 1.0; grid[7, x] = 1.0; grid[13, x] = 1.0
        for y in range(3, 7): grid[y, 4] = 1.0
        for y in range(8, 13): grid[y, 11] = 1.0
    elif d == 6:
        for y in range(2, 14): grid[y, 4] = 1.0
        for x in range(4, 12):
            grid[2, x] = 1.0; grid[7, x] = 1.0; grid[13, x] = 1.0
        for y in range(8, 13): grid[y, 11] = 1.0
    elif d == 7:
        for x in range(3, 13): grid[2, x] = 1.0
        for i in range(11): grid[3 + i, 12 - int(i * 0.7)] = 1.0
    elif d == 8:
        for y in range(2, 8):
            for x in range(4, 12):
                dx = (x - 7.5) / 2.8; dy = (y - 4.8) / 2.2
                if 0.5 <= dx*dx + dy*dy <= 1.25: grid[y, x] = 1.0
        for y in range(8, 14):
            for x in range(3, 13):
                dx = (x - 7.5) / 3.6; dy = (y - 10.5) / 2.4
                if 0.5 <= dx*dx + dy*dy <= 1.25: grid[y, x] = 1.0
    elif d == 9:
        for y in range(2, 8):
            for x in range(4, 12):
                dx = (x - 7.5) / 3.0; dy = (y - 4.8) / 2.2
                if 0.5 <= dx*dx + dy*dy <= 1.25: grid[y, x] = 1.0
        for y in range(3, 14): grid[y, 11] = 1.0
        for x in range(5, 11): grid[13, x] = 0.8
    return grid

X_train, y_train = [], []
for d in range(10):
    base = make_digit(d)
    # Give higher weight to clean prototypes
    for _ in range(50):
        X_train.append(base.flatten())
        y_train.append(d)
    for _ in range(100):
        sx = np.random.choice([-1, 0, 1])
        sy = np.random.choice([-1, 0, 1])
        shifted = np.roll(np.roll(base, sy, axis=0), sx, axis=1)
        noise = np.random.normal(0, 0.04, (16, 16))
        sample = np.clip(shifted * np.random.uniform(0.85, 1.1) + noise, 0.0, 1.0)
        X_train.append(sample.flatten())
        y_train.append(d)

X = np.array(X_train)
Y = np.zeros((len(y_train), 10))
for i, d in enumerate(y_train): Y[i, d] = 1.0

W1 = np.random.randn(256, 16) * 0.1
b1 = np.zeros(16)
W2 = np.random.randn(16, 16) * 0.2
b2 = np.zeros(16)
W3 = np.random.randn(16, 10) * 0.3
b3 = np.zeros(10)

lr = 0.015
vW1, vb1 = np.zeros_like(W1), np.zeros_like(b1)
vW2, vb2 = np.zeros_like(W2), np.zeros_like(b2)
vW3, vb3 = np.zeros_like(W3), np.zeros_like(b3)

for epoch in range(1600):
    z1 = np.dot(X, W1) + b1; a1 = sigmoid(z1)
    z2 = np.dot(a1, W2) + b2; a2 = sigmoid(z2)
    z3 = np.dot(a2, W3) + b3; probs = softmax(z3)

    dz3 = (probs - Y) / len(X)
    dW3 = np.dot(a2.T, dz3); db3 = np.sum(dz3, axis=0)

    da2 = np.dot(dz3, W3.T); dz2 = da2 * d_sigmoid(a2)
    dW2 = np.dot(a1.T, dz2); db2 = np.sum(dz2, axis=0)

    da1 = np.dot(dz2, W2.T); dz1 = da1 * d_sigmoid(a1)
    dW1 = np.dot(X.T, dz1); db1 = np.sum(dz1, axis=0)

    mu = 0.9
    vW3 = mu * vW3 - lr * dW3 * 20; W3 += vW3
    vb3 = mu * vb3 - lr * db3 * 20; b3 += vb3
    vW2 = mu * vW2 - lr * dW2 * 20; W2 += vW2
    vb2 = mu * vb2 - lr * db2 * 20; b2 += vb2
    vW1 = mu * vW1 - lr * dW1 * 20; W1 += vW1
    vb1 = mu * vb1 - lr * db1 * 20; b1 += vb1

correct = 0
for d in range(10):
    t = make_digit(d).flatten()
    z1 = np.dot(t, W1) + b1; a1 = sigmoid(z1)
    z2 = np.dot(a1, W2) + b2; a2 = sigmoid(z2)
    z3 = np.dot(a2, W3) + b3; p = softmax(z3)
    pred = np.argmax(p)
    if pred == d: correct += 1
    print(f"Digit {d} -> pred {pred} ({p[pred]*100:.1f}%)")

print(f"Prototypes accuracy: {correct}/10")

weights_data = {
    "W1": np.round(W1, 3).tolist(),
    "b1": np.round(b1, 3).tolist(),
    "W2": np.round(W2, 3).tolist(),
    "b2": np.round(b2, 3).tolist(),
    "W3": np.round(W3, 3).tolist(),
    "b3": np.round(b3, 3).tolist(),
}
with open("departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/neural_networks/nn_weights.json", "w") as f:
    json.dump(weights_data, f)
