import wave
import numpy as np

base_path = 'departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses'
orig_wav = f'{base_path}/raw_sources/original_audio.wav'

with wave.open(orig_wav, 'rb') as wf:
    sr = wf.getframerate()
    nframes = wf.getnframes()
    raw = np.frombuffer(wf.readframes(nframes), dtype=np.int16).reshape(-1, 2)

# Function to save wav
def save_wav(filename, samples, sr=44100):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        data = np.clip(samples, -32768, 32767).astype(np.int16)
        wf.writeframes(data.tobytes())

# Let's save a 10-second snippet (0s - 15s) to test
clip = raw[0:int(15*sr)]
save_wav('test_snippet_0_15s.wav', clip)
print("Saved snippet 0-15s")
