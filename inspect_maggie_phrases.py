import soundfile as sf
import numpy as np

m, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_masters/maggie_master_take_google_studio.wav')

# Gaps detected earlier with gap >= 0.3s:
# [ 0.000s -  1.335s]: dur=1.335s
# [ 2.000s -  2.680s]: dur=0.680s
# [ 2.970s -  4.890s]: dur=1.920s
# [ 5.295s -  7.010s]: dur=1.715s (internal micro-gap at 5.9-6.2)
# [ 7.370s -  8.610s]: dur=1.240s
# [ 9.830s - 10.915s]: dur=1.085s
# [ 11.330s - 12.005s]: dur=0.675s
# [ 12.550s - 13.855s]: dur=1.305s
# [ 14.255s - 14.665s]: dur=0.410s
# [ 15.490s - 16.055s]: dur=0.565s
# [ 17.380s - 18.310s]: dur=0.930s
# [ 18.650s - 23.005s]: dur=4.355s

# Notice Maggie total duration is 23.56s.
# Let's see the large gaps:
# gap 1: 1.335s - 2.000s (0.665s) -> before phrase 2
# gap 2: 2.680s - 2.970s (0.290s) -> before phrase 3
# gap 3: 4.890s - 5.295s (0.405s) -> before phrase 4
# gap 4: 8.610s - 9.830s (1.220s) -> big pause!
# gap 5: 12.005s - 12.550s (0.545s) ->
# gap 6: 14.665s - 15.490s (0.825s) ->
# gap 7: 16.465s - 17.380s (0.915s) ->
# gap 8: 18.310s - 18.650s (0.340s) ->

print("Inspecting Maggie audio segments:")
for idx, (s, e) in enumerate([
    (0.0, 1.335), # Phrase 1?
    (2.0, 2.68),  # Phrase 2?
    (2.97, 4.89), # Phrase 3?
    (5.29, 8.61), # Phrase 4?
    (9.83, 12.00), # Phrase 5?
    (12.55, 14.66), # Phrase 6?
    (15.49, 18.31), # Phrase 7?
    (18.65, 23.00), # Phrase 8?
]):
    chunk = m[int(s*sr):int(e*sr)]
    rms = np.sqrt(np.mean(chunk**2))
    print(f"Phrase {idx+1}: [{s:5.2f}s - {e:5.2f}s] dur={e-s:5.2f}s rms={rms:.4f}")
