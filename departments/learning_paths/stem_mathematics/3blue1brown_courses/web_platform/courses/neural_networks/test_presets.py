import numpy as np

# 16x16 grid = 256 inputs
grid_size = 16

def create_preset(digit):
    grid = np.zeros((16, 16))
    if digit == 0:
        for y in range(3, 13):
            for x in range(4, 12):
                dx = (x - 7.5) / 3.5
                dy = (y - 7.5) / 4.5
                dist = dx*dx + dy*dy
                if 0.5 <= dist <= 1.2:
                    grid[y, x] = 0.95
    elif digit == 1:
        for y in range(2, 14):
            grid[y, 8] = 1.0
            grid[y, 7] = 0.4
    elif digit == 2:
        # top curve
        for x in range(5, 11): grid[3, x] = 1.0
        for y in range(4, 7): grid[y, 11] = 1.0
        # diagonal
        for i in range(6):
            grid[7 + i, 11 - i] = 1.0
        # bottom bar
        for x in range(5, 12): grid[13, x] = 1.0
    elif digit == 3:
        for x in range(5, 11): grid[3, x] = 1.0
        for y in range(4, 7): grid[y, 11] = 1.0
        for x in range(6, 11): grid[8, x] = 1.0
        for y in range(9, 13): grid[y, 11] = 1.0
        for x in range(5, 11): grid[13, x] = 1.0
    elif digit == 4:
        for y in range(3, 9): grid[y, 5] = 1.0
        for x in range(4, 12): grid[8, x] = 1.0
        for y in range(3, 14): grid[y, 10] = 1.0
    elif digit == 7:
        for x in range(4, 12): grid[3, x] = 1.0
        for i in range(10):
            grid[4 + i, 11 - int(i * 0.7)] = 1.0
    elif digit == 8:
        # top loop
        for y in range(3, 8):
            for x in range(5, 11):
                dx = (x - 7.5) / 2.5
                dy = (y - 5.5) / 2.0
                dist = dx*dx + dy*dy
                if 0.5 <= dist <= 1.2: grid[y, x] = 0.95
        # bottom loop
        for y in range(8, 14):
            for x in range(4, 12):
                dx = (x - 7.5) / 3.0
                dy = (y - 10.5) / 2.5
                dist = dx*dx + dy*dy
                if 0.5 <= dist <= 1.2: grid[y, x] = 0.95
    return grid

for d in [0, 1, 2, 3, 4, 7, 8]:
    g = create_preset(d)
    print(f"Preset {d}: {int(np.sum(g))} active pixels")
