import soundfile as sf
import numpy as np

orig, sr = sf.read('check_36_40.wav')
vocals, sr = sf.read('chime_test/htdemucs/check_36_40/vocals.wav')
no_vocals, sr = sf.read('chime_test/htdemucs/check_36_40/no_vocals.wav')

print("Orig RMS:", np.sqrt(np.mean(orig**2)))
print("Vocals RMS:", np.sqrt(np.mean(vocals**2)))
print("No_vocals RMS:", np.sqrt(np.mean(no_vocals**2)))
