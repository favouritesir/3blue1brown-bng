"""
Nemotron 3.5 Super VL - Studio Audio Stem Separation Engine
Cartoon SFX, Bell Rings, Chimes, Foley & Dialogue Isolation
================================================================
Processes source audio into:
1. sfx_bells_isolated.wav (Pure cartoon sound effects, magic chimes, bell rings,
   comic boings, pops, sniffs, sizzles without hissing, buzz, or robotic distortion)
2. speech_isolated.wav (Pristine dialogue/speech track with smooth transitions)
"""

import json
from pathlib import Path
import numpy as np
import scipy.signal as signal
import soundfile as sf
from scipy.ndimage import gaussian_filter1d

def separate_cartoon_stems(
    source_audio_path: Path,
    script_cues_path: Path,
    output_dir: Path
):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(script_cues_path, encoding='utf-8') as f:
        cues = json.load(f)

    data, sr = sf.read(str(source_audio_path))
    n_samples = len(data)
    left = data[:, 0]
    right = data[:, 1]

    # Step 1: Accurate Speech Masking with smooth cosine ramps
    speech_mask_time = np.zeros(n_samples, dtype=np.float32)
    ramp_len = int(0.035 * sr) # 35ms ramp
    ramp_up = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, ramp_len)))
    ramp_down = 0.5 * (1.0 + np.cos(np.linspace(0, np.pi, ramp_len)))

    def apply_mask_interval(mask, s_sec, e_sec):
        s_idx = int(s_sec * sr)
        e_idx = int(e_sec * sr)
        if s_idx >= e_idx or s_idx >= n_samples:
            return
        s_ramp_start = max(0, s_idx - ramp_len)
        actual_s_len = s_idx - s_ramp_start
        if actual_s_len > 0:
            mask[s_ramp_start:s_idx] = np.maximum(mask[s_ramp_start:s_idx], ramp_up[-actual_s_len:])
        mask[s_idx:e_idx] = 1.0
        e_ramp_end = min(n_samples, e_idx + ramp_len)
        actual_e_len = e_ramp_end - e_idx
        if actual_e_len > 0:
            mask[e_idx:e_ramp_end] = np.maximum(mask[e_idx:e_ramp_end], ramp_down[:actual_e_len])

    for c in cues:
        c_id = c['id']
        s = c['start']
        e = c['end']
        
        # Refine boundaries where Foley sound effects (sniff, sizzle) occur
        if c_id == 36: # "Smell the flower. Smell." (starts after sniff at 166.45s)
            apply_mask_interval(speech_mask_time, 166.45, e)
        elif c_id == 37: # "Smell. [snorts] Smell." (sniff at 172.10s - 173.30s)
            apply_mask_interval(speech_mask_time, s, 172.10)
            apply_mask_interval(speech_mask_time, 173.30, e)
        elif c_id == 47: # Hot chili cartoon scream / sizzle
            apply_mask_interval(speech_mask_time, 207.85, e)
        else:
            apply_mask_interval(speech_mask_time, s, e)

    # Foley SFX explicitly designated for sfx_bells_isolated track
    foley_sfx_mask = np.zeros(n_samples, dtype=np.float32)
    apply_mask_interval(foley_sfx_mask, 164.20, 166.45) # Sniff 1
    apply_mask_interval(foley_sfx_mask, 172.10, 173.30) # Sniff 2
    apply_mask_interval(foley_sfx_mask, 206.25, 207.85) # Chili sizzle

    # Step 2: High-frequency bell chime filter (>3800 Hz) with envelope gating
    b_bell, a_bell = signal.butter(4, 3800 / (sr / 2), btype='highpass')
    chimes_in_dialogue_L = signal.filtfilt(b_bell, a_bell, left)
    chimes_in_dialogue_R = signal.filtfilt(b_bell, a_bell, right)

    def extract_tonal_chimes(chime_sig, sr_rate):
        analytic = signal.hilbert(chime_sig)
        env = np.abs(analytic)
        env_smooth = gaussian_filter1d(env, sigma=int(0.01 * sr_rate))
        mask = np.clip((env_smooth - 0.008) / 0.02, 0.0, 1.0)
        return chime_sig * mask

    chimes_clean_L = extract_tonal_chimes(chimes_in_dialogue_L, sr)
    chimes_clean_R = extract_tonal_chimes(chimes_in_dialogue_R, sr)

    # Step 3: Combine Stems
    sfx_mask_total = np.clip((1.0 - speech_mask_time) + foley_sfx_mask, 0.0, 1.0)
    sfx_out_L = left * sfx_mask_total + chimes_clean_L * (1.0 - sfx_mask_total)
    sfx_out_R = right * sfx_mask_total + chimes_clean_R * (1.0 - sfx_mask_total)

    speech_mask_final = np.clip(speech_mask_time * (1.0 - foley_sfx_mask), 0.0, 1.0)
    speech_out_L = left * speech_mask_final
    speech_out_R = right * speech_mask_final

    sfx_stereo = np.column_stack([sfx_out_L, sfx_out_R])
    speech_stereo = np.column_stack([speech_out_L, speech_out_R])

    # True-peak limit to -0.5 dBFS
    max_sfx = np.max(np.abs(sfx_stereo))
    if max_sfx > 0.95:
        sfx_stereo = sfx_stereo * (0.95 / max_sfx)

    max_sp = np.max(np.abs(speech_stereo))
    if max_sp > 0.95:
        speech_stereo = speech_stereo * (0.95 / max_sp)

    sfx_file = output_dir / 'sfx_bells_isolated.wav'
    speech_file = output_dir / 'speech_isolated.wav'

    sf.write(str(sfx_file), sfx_stereo, sr, subtype='PCM_16')
    sf.write(str(speech_file), speech_stereo, sr, subtype='PCM_16')

    return sfx_file, speech_file

if __name__ == '__main__':
    base = Path('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses')
    src = base / 'raw_sources' / 'original_audio.wav'
    script = base / 'scripts' / 'master_bangla_screenplay_script.json'
    dest = base / 'isolated_stems' / 'nemotron_3_5_super_vl'
    s_f, sp_f = separate_cartoon_stems(src, script, dest)
    print(f"Engine ran successfully. Outputs:\n  {s_f}\n  {sp_f}")
