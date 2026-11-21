"""Measure speech-fill ratio inside cue windows for any lesson's dubbed master.
Detects long silent pockets caused by pad-only + timeline stretching.
Usage: python governance/measure_fill.py <course> <lesson_num>
"""
import json, sys, os, subprocess, wave
import numpy as np

course, num = sys.argv[1], sys.argv[2]
w='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
folder='linear_algebra' if course=='linear_algebra' else course
exp=f'{w}/assets/audio/{folder}/lesson_{num}'
vjson=None
import glob
cands=glob.glob(f'departments/learning_paths/stem_mathematics/3blue1brown_courses/*/lesson_{num}*/dubbing_pipeline/experiments/clean_timesync_v2/verification.json')
for c in cands:
    d=json.load(open(c,encoding='utf-8'))
    if d.get('cue_count',0)>10:
        vjson=(c,d); break
if not vjson:
    print('no verification found'); sys.exit()
c,d=vjson
# find master wav near that folder
masters=glob.glob(os.path.join(os.path.dirname(c),'master.wav'))
if not masters:
    print('no master.wav'); sys.exit()
with wave.open(masters[0],'rb') as wf:
    rate=wf.getframerate(); a=np.frombuffer(wf.readframes(wf.getnframes()),dtype='<i2').astype(np.float32)/32768
print('master',masters[0],'rate',rate,'dur',len(a)/rate)
print('verification',c,'cues',d.get('cue_count'),'scale',d.get('timeline_scale'))
# group by section audio file if present
print('keys sample', list(d.keys())[:14])
