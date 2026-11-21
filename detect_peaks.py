import soundfile as sf
import numpy as np

orig, sr = sf.read('test_intro_0_15.wav')

# Let's inspect small slices of test_intro_0_15.wav
# In 0 - 2.2s, let's see what sounds exist:
# Is there a bell chime? When does it ring?
# Let's do an envelope / peak detection in 0-15s
frame_len = int(0.05 * sr)
hop_len = int(0.02 * sr)
times = []
rms_list = []
for i in range(0, len(orig) - frame_len, hop_len):
    t = i / sr
    chunk = orig[i:i+frame_len]
    rms = np.sqrt(np.mean(chunk**2))
    times.append(t)
    rms_list.append(rms)

# Find peaks
for t, rms in zip(times, rms_list):
    if rms > 0.15:
        # check if it's near speech cues
        pass
