import soundfile as sf
import numpy as np

for stem in ['vocals', 'other', 'drums', 'bass']:
    data, sr = sf.read(f'demucs_4stems/htdemucs/test_intro_0_15/{stem}.wav')
    print(f"{stem:8s}: max = {np.max(np.abs(data)):.4f}, RMS = {np.sqrt(np.mean(data**2)):.4f}")
