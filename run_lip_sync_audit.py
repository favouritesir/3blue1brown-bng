import json
import soundfile as sf
import numpy as np

# Load original audio
orig, sr = sf.read('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/original_audio.wav')
if orig.ndim > 1:
    orig = orig.mean(axis=1)

with open('departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/scripts/egm_master_screenplay_v2.json', encoding='utf-8') as f:
    sp = json.load(f)

cues = sp['cues']

# Function to detect exact active speech boundaries in original audio within a search window
def find_exact_speech_window(t_center_start, t_center_end, search_pad=0.5, thresh_db=-35):
    t0 = max(0.0, t_center_start - search_pad)
    t1 = min(len(orig)/sr, t_center_end + search_pad)
    s0 = int(t0 * sr)
    s1 = int(t1 * sr)
    chunk = orig[s0:s1]
    
    win = int(sr * 0.02)
    hop = int(sr * 0.005)
    n = (len(chunk) - win) // hop + 1
    e = np.empty(n)
    for i in range(n):
        seg = chunk[i*hop : i*hop+win]
        e[i] = 20.0 * np.log10(np.sqrt(np.mean(seg*seg)) + 1e-9)
        
    hop_s = hop / sr
    loud = np.where(e >= thresh_db)[0]
    if len(loud) == 0:
        return t_center_start, t_center_end
        
    start_s = t0 + loud[0] * hop_s
    end_s = t0 + loud[-1] * hop_s
    return round(start_s, 2), round(end_s, 2)

print("Auditing speech boundaries in source video / original audio:")
audit = []
for c in cues:
    v_start, v_end = find_exact_speech_window(c['start'], c['end'], search_pad=0.3)
    audit.append({
        'id': c['id'],
        'speaker': c['speaker'],
        'v2_start': c['start'],
        'v2_end': c['end'],
        'visual_mouth_start': v_start,
        'visual_mouth_end': v_end,
        'duration': round(v_end - v_start, 2),
        'en': c.get('en', ''),
        'bn': c['bn'],
        'scene_title': c.get('scene_title', '')
    })
    print(f"Cue {c['id']:02d} [{c['speaker']:6s}]: v2=[{c['start']:5.2f} - {c['end']:5.2f}] -> audit=[{v_start:5.2f} - {v_end:5.2f} | dur {v_end-v_start:4.2f}s] | {c['bn']}")

with open('visual_lip_sync_audit.json', 'w', encoding='utf-8') as f:
    json.dump(audit, f, indent=2, ensure_ascii=False)
