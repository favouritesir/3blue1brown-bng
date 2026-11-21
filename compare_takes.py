import soundfile as sf
import numpy as np

def check_file(path, label):
    d, sr = sf.read(path)
    if d.ndim > 1: d = d.mean(axis=1)
    dur = len(d) / sr
    rms = np.sqrt(np.mean(d**2))
    peak = np.max(np.abs(d))
    print(f"{label:30s}: dur={dur:6.3f}s sr={sr} rms={rms:6.4f} peak={peak:6.4f}")

print("--- Cue 1: 'আরে দেখো! এটা তো একটা পেন্সিল!' ---")
check_file('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/cues_rendered_perfect/raw_cue_001_Steve.wav', "rendered_perfect raw_cue_001")
check_file('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/sliced_cues/fresh_cue_001_Steve.wav', "sliced_cues fresh_cue_001")
check_file('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_cues_v2/fitted_cue_001_Steve.wav', "v2 fitted_cue_001")

print("\n--- Cue 5: 'আরেহ্! ওরেব্বাবা!' (scream) ---")
check_file('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/cues_rendered_perfect/raw_cue_005_Steve.wav', "rendered_perfect raw_cue_005")
check_file('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/sliced_cues/fresh_cue_005_Steve.wav', "sliced_cues fresh_cue_005")
check_file('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_cues_v2/fitted_cue_005_Steve.wav', "v2 fitted_cue_005")

print("\n--- Cue 12: Maggie teasing ---")
check_file('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/cues_rendered_perfect/raw_cue_012_Maggie.wav', "rendered_perfect raw_cue_012")
check_file('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/sliced_cues/fresh_cue_012_Maggie.wav', "sliced_cues fresh_cue_012")
check_file('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_cues_v2/fitted_cue_012_Maggie.wav', "v2 fitted_cue_012")

print("\n--- Cue 47: Hot chili scream ---")
check_file('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/cues_rendered_perfect/raw_cue_047_Steve.wav', "rendered_perfect raw_cue_047")
check_file('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/sliced_cues/fresh_cue_047_Steve.wav', "sliced_cues fresh_cue_047")
check_file('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/audio_takes/google_studio_cues_v2/fitted_cue_047_Steve.wav', "v2 fitted_cue_047")
