import json, os, glob
ROOT='departments/learning_paths/stem_mathematics/3blue1brown_courses'
p=f'{ROOT}/differential_equations/lesson_01_intro/dubbing_pipeline/experiments/clean_timesync_v2/verification.json'
if not os.path.isfile(p):
    print('no verification.json yet'); raise SystemExit
d=json.load(open(p,encoding='utf-8'))
for k in ('cue_count','duration','timeline_scale','median_fill','max_internal_gap_s','fill_policy_met','max_measured_drift_ms','failed_tts_cues','overrun_cues'):
    print(f'{k}: {d.get(k)}')
mp4=f'{ROOT}/web_platform/media_vault/differential_equations/lesson_01/experiments/3b1b_de_01_full_dubbed.mp4'
print('mp4 exists:',os.path.isfile(mp4), os.path.getsize(mp4) if os.path.isfile(mp4) else 0)
