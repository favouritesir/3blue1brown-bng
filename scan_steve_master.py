import soundfile as sf
import numpy as np

x, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/steve_master_take_google_studio.wav')

def inspect_exact(t0, t1, name):
    s0 = int(t0 * sr)
    s1 = int(t1 * sr)
    seg = x[s0:s1]
    rms = np.sqrt(np.mean(seg**2))
    peak = np.max(np.abs(seg))
    print(f"{name:15s} [{t0:6.3f}s - {t1:6.3f}s]: dur={t1-t0:.3f}s, rms={rms:.4f}, peak={peak:.4f}")

for t in np.arange(0, 15, 0.5):
    inspect_exact(t, t+0.5, f"t={t:.1f}")
