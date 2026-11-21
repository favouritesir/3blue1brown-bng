import soundfile as sf
import numpy as np

for name in ["test_intro_0_15.wav", "test_maggie_35_50.wav", "test_gag_78_88.wav", "test_flower_162_180.wav", "test_chili_192_210.wav"]:
    data, sr = sf.read(name)
    L = data[:, 0]
    R = data[:, 1]
    diff = L - R
    sum_m = (L + R) / 2.0
    
    # Calculate energy ratio of diff vs sum
    energy_diff = np.mean(diff**2)
    energy_sum = np.mean(sum_m**2)
    print(f"{name}: diff RMS = {np.sqrt(energy_diff):.4f}, sum RMS = {np.sqrt(energy_sum):.4f}, ratio = {energy_diff/max(1e-9, energy_sum):.4f}")
