import json
import wave
import numpy as np
import scipy.signal as signal

base_path = 'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses'
orig_wav = f'{base_path}/raw_sources/original_audio.wav'

with wave.open(orig_wav, 'rb') as wf:
    sr = wf.getframerate()
    nframes = wf.getnframes()
    raw = np.frombuffer(wf.readframes(nframes), dtype=np.int16).reshape(-1, 2)

mono = 0.5 * (raw[:, 0].astype(np.float32) + raw[:, 1].astype(np.float32))

with open(f'{base_path}/scripts/master_bangla_screenplay_script.json', encoding='utf-8') as f:
    cues = json.load(f)

# For each cue, let's find if there are high-frequency bell chimes (>3000Hz with high Q peakiness)
print("Scanning cues for prominent bell rings or high-frequency chimes:")
for c in cues:
    s = int(c['start'] * sr)
    e = int(c['end'] * sr)
    cue_audio = mono[s:e]
    
    # STFT to inspect narrow-band peaks
    f, t, Zxx = signal.stft(cue_audio, sr, nperseg=2048, noverlap=1024)
    mag = np.abs(Zxx)
    
    # Look for sharp isolated spectral peaks in 2500 - 9000 Hz
    band = (f >= 2500) & (f <= 9000)
    mag_band = mag[band, :]
    
    # Peakiness / Kurtosis: ratio of max to mean across frequencies
    peak_ratio = np.max(mag_band, axis=0) / (np.mean(mag_band, axis=0) + 1e-6)
    prominent_peaks = np.where(peak_ratio > 12.0)[0]
    
    if len(prominent_peaks) > 3:
        peak_times = t[prominent_peaks] + c['start']
        print(f"Cue #{c['id']:02d} [{c['start']:5.2f} - {c['end']:5.2f}s] ({c['speaker']}): Detected {len(prominent_peaks)} chime/bell partials at {peak_times[:4]}")
