import soundfile as sf
import numpy as np

other, sr = sf.read('demucs_4stems/htdemucs/test_intro_0_15/other.wav')
drums, sr = sf.read('demucs_4stems/htdemucs/test_intro_0_15/drums.wav')
vocals, sr = sf.read('demucs_4stems/htdemucs/test_intro_0_15/vocals.wav')

# Look at 12-14s (the pencil reaction / gag)
sfx_other = other[int(12.0*sr):int(14.0*sr)]
sfx_drums = drums[int(12.0*sr):int(14.0*sr)]
print("12-14s other max:", np.max(np.abs(sfx_other)))
print("12-14s drums max:", np.max(np.abs(sfx_drums)))

# Look at 0-2.2s (the intro)
intro_other = other[:int(2.2*sr)]
intro_drums = drums[:int(2.2*sr)]
print("0-2.2s other max:", np.max(np.abs(intro_other)))
print("0-2.2s drums max:", np.max(np.abs(intro_drums)))
