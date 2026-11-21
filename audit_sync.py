import json

path = r'departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_linear_algebra/lesson_01_vectors/dubbing_pipeline/3b1b_lesson_01_bangla_master_script.json'
with open(path, 'r', encoding='utf-8') as f:
    cues = json.load(f)

for i in range(15):
    c = cues[i]
    dur = c['end'] - c['start']
    words = len(c['bn'].split())
    wps = words / dur if dur > 0 else 0
    cid = c['id']
    bn = c['bn'][:45]
    print(f"Cue #{cid:02d} | Win: {dur:4.2f}s | Words: {words:2d} | WPS: {wps:3.1f} | {bn}")
