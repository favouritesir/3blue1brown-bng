import numpy as np

# Let's train a real tiny MLP on synthetic 16x16 digit exemplars
# Inputs: 256
# Hidden 1: 16
# Hidden 2: 16
# Output: 10

np.random.seed(42)

def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -15, 15)))

def d_sigmoid(a):
    return a * (1.0 - a)

def relu(z):
    return np.maximum(0.0, z)

def d_relu(z):
    return (z > 0).astype(float)

def softmax(z):
    ez = np.exp(z - np.max(z, axis=-1, keepdims=True))
    return ez / np.sum(ez, axis=-1, keepdims=True)

# Generate prototypes for 0-9 on 16x16
def get_digit_template(d):
    grid = np.zeros((16, 16))
    if d == 0:
        for y in range(2, 14):
            for x in range(3, 13):
                dx = (x - 7.5) / 3.8
                dy = (y - 7.5) / 4.8
                dist = dx*dx + dy*dy
                if 0.5 <= dist <= 1.3: grid[y, x] = 1.0
    elif d == 1:
        for y in range(2, 14):
            grid[y, 8] = 1.0
            grid[y, 7] = 0.5
        for x in range(5, 12): grid[13, x] = 1.0
        for i in range(3): grid[2+i, 8-i] = 0.8
    elif d == 2:
        for x in range(4, 12): grid[2, x] = 1.0
        for y in range(3, 7): grid[y, 11] = 1.0
        for x in range(5, 11): grid[7, x] = 1.0
        for i in range(6):
            grid[8+i, 9-int(i*1.1)] = 1.0
        for x in range(3, 13): grid[13, x] = 1.0
    elif d == 3:
        for x in range(4, 12): grid[2, x] = 1.0; grid[7, x] = 0.9; grid[13, x] = 1.0
        for y in range(3, 7): grid[y, 11] = 1.0
        for y in range(8, 13): grid[y, 11] = 1.0
    elif d == 4:
        for y in range(2, 9): grid[y, 4] = 1.0
        for x in range(3, 13): grid[8, x] = 1.0
        for y in range(2, 14): grid[y, 10] = 1.0
    elif d == 5:
        for x in range(4, 12): grid[2, x] = 1.0; grid[7, x] = 1.0; grid[13, x] = 1.0
        for y in range(3, 8): grid[y, 4] = 1.0
        for y in range(8, 13): grid[y, 11] = 1.0
    elif d == 6:
        for y in range(2, 14): grid[y, 4] = 1.0
        for x in range(4, 12): grid[2, x] = 0.9; grid[7, x] = 1.0; grid[13, x] = 1.0
        for y in range(8, 13): grid[y, 11] = 1.0
    elif d == 7:
        for x in range(3, 13): grid[2, x] = 1.0
        for i in range(12):
            grid[2+i, 12-int(i*0.75)] = 1.0
    elif d == 8:
        for y in range(2, 8):
            for x in range(4, 12):
                dx = (x - 7.5)/3.0; dy = (y - 4.5)/2.2
                if 0.5 <= dx*dx + dy*dy <= 1.3: grid[y, x] = 1.0
        for y in range(8, 14):
            for x in range(3, 13):
                dx = (x - 7.5)/3.8; dy = (y - 10.5)/2.5
                if 0.5 <= dx*dx + dy*dy <= 1.3: grid[y, x] = 1.0
    elif d == 9:
        for y in range(2, 9):
            for x in range(4, 12):
                dx = (x - 7.5)/3.2; dy = (y - 5.0)/2.5
                if 0.5 <= dx*dx + dy*dy <= 1.3: grid[y, x] = 1.0
        for y in range(4, 14): grid[y, 11] = 1.0
        for x in range(5, 11): grid[13, x] = 0.8
    return grid

# Generate training samples with random shifts and noise
X_list = []
y_list = []

for digit in range(10):
    tmpl = get_digit_template(digit)
    for _ in range(80):
        # shift
        sx = np.random.randint(-1, 2)
        sy = np.random.randint(-1, 2)
        shifted = np.roll(np.roll(tmpl, sy, axis=0), sx, axis=1)
        # noise & dilation
        noise = np.random.uniform(0, 0.15, (16, 16))
        sample = np.clip(shifted + noise, 0.0, 1.0)
        X_list.append(sample.flatten())
        y_list.append(digit)

X = np.array(X_list)
Y = np.zeros((len(y_list), 10))
for i, d in enumerate(y_list):
    Y[i, d] = 1.0

# Initialize weights (Xavier)
W1 = np.random.randn(256, 16) * np.sqrt(2.0 / 256)
b1 = np.zeros(16)
W2 = np.random.randn(16, 16) * np.sqrt(2.0 / 16)
b2 = np.zeros(16)
W3 = np.random.randn(16, 10) * np.sqrt(2.0 / 16)
b3 = np.zeros(10)

lr = 0.1
for epoch in range(400):
    # Forward
    z1 = np.dot(X, W1) + b1
    a1 = sigmoid(z1)
    
    z2 = np.dot(a1, W2) + b2
    a2 = sigmoid(z2)
    
    z3 = np.dot(a2, W3) + b3
    probs = softmax(z3)
    
    # Backprop
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
print(f"Trained accuracy: {acc:.1f}%")

# Test prototypes
print("Prototypes evaluation:")
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

# Output compact weights as JSON/JS
import json
weights_export = {
    "W1": np.round(W1, 4).tolist(),
    "b1": np.round(b1, 4).tolist(),
    "W2": np.round(W2, 4).tolist(),
    "b2": np.round(b2, 4).tolist(),
    "W3": np.round(W3, 4).tolist(),
    "b3": np.round(b3, 4).tolist(),
}
with open("departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/neural_networks/trained_weights.json", "w") as f:
    json.dump(weights_export, f)
print("Saved trained weights to JSON!")
