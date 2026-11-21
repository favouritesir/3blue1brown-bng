import soundfile as sf
import numpy as np

orig, sr = sf.read('test_intro_0_15.wav')
vocals, sr = sf.read('demucs_test/htdemucs/test_intro_0_15/vocals.wav')
no_vocals, sr = sf.read('demucs_test/htdemucs/test_intro_0_15/no_vocals.wav')

print(f"Orig length: {len(orig)/sr:.2f}s, Vocals: {len(vocals)/sr:.2f}s, No_vocals: {len(no_vocals)/sr:.2f}s")
# 0 to 2.2s is pure intro music & bell chime!
intro_orig = orig[:int(2.2*sr)]
intro_no_vocals = no_vocals[:int(2.2*sr)]
intro_vocals = vocals[:int(2.2*sr)]

print(f"0-2.2s Orig RMS: {np.sqrt(np.mean(intro_orig**2)):.4f}")
print(f"0-2.2s No_vocals RMS: {np.sqrt(np.mean(intro_no_vocals**2)):.4f}")
print(f"0-2.2s Vocals RMS (leakage during non-vocal): {np.sqrt(np.mean(intro_vocals**2)):.4f}")

# 2.2 to 6.3s is Steve saying "Look, it's a pencil."
# During this, what is in no_vocals vs vocals?
speech_orig = orig[int(2.2*sr):int(6.3*sr)]
speech_no_vocals = no_vocals[int(2.2*sr):int(6.3*sr)]
speech_vocals = vocals[int(2.2*sr):int(6.3*sr)]

print(f"2.2-6.3s Orig RMS: {np.sqrt(np.mean(speech_orig**2)):.4f}")
print(f"2.2-6.3s Vocals RMS: {np.sqrt(np.mean(speech_vocals**2)):.4f}")
print(f"2.2-6.3s No_vocals RMS: {np.sqrt(np.mean(speech_no_vocals**2)):.4f}")

# 12.0 to 14.0s is pencil comic sound and screaming
sfx_orig = orig[int(12.0*sr):int(14.0*sr)]
sfx_no_vocals = no_vocals[int(12.0*sr):int(14.0*sr)]
sfx_vocals = vocals[int(12.0*sr):int(14.0*sr)]
print(f"12-14s Orig RMS: {np.sqrt(np.mean(sfx_orig**2)):.4f}")
print(f"12-14s Vocals RMS: {np.sqrt(np.mean(sfx_vocals**2)):.4f}")
print(f"12-14s No_vocals RMS: {np.sqrt(np.mean(sfx_no_vocals**2)):.4f}")
