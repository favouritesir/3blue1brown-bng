import soundfile as sf
import numpy as np

x, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/steve_master_take_google_studio.wav')

def inspect_range(t0, t1, label):
    s0 = int(t0 * sr)
    s1 = int(t1 * sr)
    chunk = x[s0:s1]
    rms = np.sqrt(np.mean(chunk**2))
    peak = np.max(np.abs(chunk))
    print(f"{label} [{t0:.2f}s - {t1:.2f}s]: dur={t1-t0:.2f}s, rms={rms:.4f}, peak={peak:.4f}")

inspect_range(0.0, 0.9, "Utterance 1")
inspect_range(1.0, 2.9, "Utterance 2")
inspect_range(3.4, 6.0, "Utterance 3")
inspect_range(6.3, 8.8, "Utterance 4")
inspect_range(9.0, 10.5, "Utterance 5")
inspect_range(10.8, 12.0, "Utterance 6")
inspect_range(15.0, 17.0, "Utterance 7")
inspect_range(18.0, 21.3, "Utterance 8")
inspect_range(21.4, 24.5, "Utterance 9")
