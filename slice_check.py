import soundfile as sf
import numpy as np

orig, sr = sf.read('test_intro_0_15.wav')
# Let's see what is happening from 0.0 to 3.0s
print("Sample rate:", sr)
# Is there someone speaking in 0.0 to 2.2s?
# Let's save slices to inspect
sf.write('slice_0_2.wav', orig[:int(2.2*sr)], sr)
sf.write('slice_2_4.wav', orig[int(2.0*sr):int(4.0*sr)], sr)
print("Wrote slice_0_2.wav and slice_2_4.wav")
