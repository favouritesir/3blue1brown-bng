import soundfile as sf
import numpy as np

orig, sr = sf.read('test_intro_0_15.wav')

# Let's inspect small slices of test_intro_0_15.wav
# 0.0 - 0.5s: What is there?
# 0.5 - 1.0s:
# 1.0 - 2.0s:
for t in np.arange(0, 15, 1.0):
    chunk = orig[int(t*sr):int((t+1)*sr)]
    rms = np.sqrt(np.mean(chunk**2))
    print(f"{t:4.1f} - {t+1:4.1f}s: RMS = {rms:.4f}")
