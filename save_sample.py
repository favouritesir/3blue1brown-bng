import soundfile as sf
import numpy as np

orig, sr = sf.read('test_intro_0_15.wav')
# Let's save 0.0 to 1.5s
sf.write('test_0_15.wav', orig[:int(1.5*sr)], sr)
print("Saved test_0_15.wav")
