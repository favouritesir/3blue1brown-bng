import numpy as np

def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -15, 15)))

def relu(z):
    return np.maximum(0.0, z)

def softmax(z, temp=1.0):
    ex = np.exp((z - np.max(z)) / temp)
    return ex / np.sum(ex)

# Test the architecture
def get_weights():
    # W1: 16 x 256
    W1 = np.zeros((16, 16, 16))
    b1 = np.zeros(16)
    
    # 0: Top horiz
    W1[0, 2:5, 3:13] = 0.8
    b1[0] = -1.5
    # 1: Mid horiz
    W1[1, 7:10, 3:13] = 0.8
    b1[1] = -1.5
    # 2: Bot horiz
    W1[2, 12:15, 3:13] = 0.8
    b1[2] = -1.5
    # 3: Center vertical
    W1[3, 2:14, 7:10] = 0.9
    b1[3] = -2.0
    # 4: Left upper vert
    W1[4, 2:8, 2:6] = 0.9
    b1[4] = -1.2
    # 5: Left lower vert
    W1[5, 8:14, 2:6] = 0.9
    b1[5] = -1.2
    # 6: Right upper vert
    W1[6, 2:8, 10:14] = 0.9
    b1[6] = -1.2
    # 7: Right lower vert
    W1[7, 8:14, 10:14] = 0.9
    b1[7] = -1.2
    # 8: Diagonal slash (top right to bot left)
    for i in range(12):
        y = 2 + i
        x = 13 - int(i * 0.8)
        if 0 <= x < 16 and 0 <= y < 16:
            W1[8, y, max(0, x-1):min(16, x+2)] = 0.8
    b1[8] = -2.0
    # 9: Diagonal backslash
    for i in range(12):
        y = 2 + i
        x = 2 + int(i * 0.8)
        if 0 <= x < 16 and 0 <= y < 16:
            W1[9, y, max(0, x-1):min(16, x+2)] = 0.8
    b1[9] = -2.0
    # 10: Top loop
    for y in range(2, 8):
        for x in range(4, 12):
            dx = (x - 7.5) / 2.8
            dy = (y - 5.0) / 2.2
            r2 = dx*dx + dy*dy
            if 0.5 <= r2 <= 1.3:
                W1[10, y, x] = 0.8
            elif r2 < 0.3:
                W1[10, y, x] = -0.6
    b1[10] = -1.5
    # 11: Bottom loop
    for y in range(8, 14):
        for x in range(4, 12):
            dx = (x - 7.5) / 3.0
            dy = (y - 11.0) / 2.5
            r2 = dx*dx + dy*dy
            if 0.5 <= r2 <= 1.3:
                W1[11, y, x] = 0.8
            elif r2 < 0.3:
                W1[11, y, x] = -0.6
    b1[11] = -1.5
    # 12: Upper-right curve
    W1[12, 2:5, 8:13] = 0.7
    W1[12, 4:8, 10:13] = 0.7
    b1[12] = -1.5
    # 13: Lower-left curve
    W1[13, 8:12, 3:6] = 0.7
    W1[13, 11:14, 4:9] = 0.7
    b1[13] = -1.5
    # 14: Center stem
    W1[14, 4:13, 9:12] = 0.9
    b1[14] = -1.8
    # 15: Hollow center
    W1[15, 6:10, 6:10] = -1.2
    W1[15, 3:13, 3:13] += 0.3
    b1[15] = 0.5

    # W2: 16 x 16
    W2 = np.zeros((16, 16))
    b2 = np.zeros(16)
    
    # Pattern 0: Loop 0
    W2[0, [0, 2, 4, 5, 6, 7, 15]] = [1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.5]
    W2[0, [1, 3]] = [-1.5, -1.0]
    b2[0] = -2.0

    # Pattern 1: Vert 1
    W2[1, [3, 14]] = [2.5, 1.5]
    W2[1, [0, 1, 2, 4, 5, 6, 7, 10, 11]] = -1.2
    b2[1] = -1.0

    # Pattern 2: Digit 2
    W2[2, [0, 6, 1, 5, 2, 8]] = [1.2, 1.0, 1.1, 1.0, 1.4, 1.2]
    W2[2, [3, 15, 11]] = [-1.0, -1.0, -1.0]
    b2[2] = -2.0

    # Pattern 3: Digit 3
    W2[3, [0, 1, 2, 6, 7]] = [1.3, 1.5, 1.3, 1.2, 1.2]
    W2[3, [4, 5, 3]] = [-1.5, -1.5, -1.0]
    b2[3] = -2.0

    # Pattern 4: Digit 4
    W2[4, [4, 1, 6, 7, 14]] = [1.5, 1.5, 1.2, 1.2, 1.0]
    W2[4, [0, 2, 5]] = [-1.2, -1.2, -1.2]
    b2[4] = -1.5

    # Pattern 5: Digit 5
    W2[5, [0, 4, 1, 7, 2]] = [1.3, 1.3, 1.4, 1.3, 1.3]
    W2[5, [6, 5]] = [-1.2, -1.2]
    b2[5] = -2.0

    # Pattern 6: Digit 6
    W2[6, [0, 4, 5, 1, 2, 7, 11]] = [0.8, 1.5, 1.5, 1.3, 1.3, 1.0, 1.5]
    W2[6, [6]] = [-1.5]
    b2[6] = -2.0

    # Pattern 7: Digit 7
    W2[7, [0, 8, 6]] = [1.8, 2.0, 1.0]
    W2[7, [1, 2, 4, 5]] = [-1.5, -1.5, -1.2, -1.2]
    b2[7] = -1.5

    # Pattern 8: Digit 8
    W2[8, [10, 11, 1, 4, 5, 6, 7]] = [1.8, 1.8, 1.0, 1.0, 1.0, 1.0, 1.0]
    W2[8, [3]] = [-1.0]
    b2[8] = -2.5

    # Pattern 9: Digit 9
    W2[9, [10, 6, 7, 0, 1]] = [1.8, 1.2, 1.2, 1.0, 1.0]
    W2[9, [5, 2]] = [-1.5, -1.0]
    b2[9] = -1.8

    # Patterns 10-15: extra helper features
    for k in range(10, 16):
        W2[k] = np.random.randn(16) * 0.1
        b2[k] = -0.5

    # W3: 10 x 16 (Output layer)
    W3 = np.zeros((10, 16))
    b3 = np.zeros(10)
    for d in range(10):
        W3[d, d] = 3.0
        # slight cross inhibition
        for other in range(10):
            if other != d:
                W3[d, other] = -0.5
        b3[d] = 0.0
    
    return W1, b1, W2, b2, W3, b3

from test_presets import create_preset

W1, b1, W2, b2, W3, b3 = get_weights()

print("Evaluating presets:")
for d in [0, 1, 2, 3, 4, 7, 8]:
    grid = create_preset(d) # 16x16
    
    # Layer 1
    z1 = np.zeros(16)
    for j in range(16):
        z1[j] = np.sum(grid * W1[j]) + b1[j]
    a1 = sigmoid(z1)
    
    # Layer 2
    z2 = np.dot(W2, a1) + b2
    a2 = sigmoid(z2)
    
    # Layer 3 (Output)
    z3 = np.dot(W3, a2) + b3
    probs = softmax(z3, temp=0.8)
    
    top_pred = np.argmax(probs)
    conf = probs[top_pred] * 100
    print(f"Preset {d} -> Predicted: {top_pred} ({conf:.1f}%) | target prob: {probs[d]*100:.1f}%")
