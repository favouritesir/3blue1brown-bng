import json

path = r'departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_linear_algebra/lesson_01_vectors/dubbing_pipeline/3b1b_lesson_01_bangla_master_script.json'
with open(path, 'r', encoding='utf-8') as f:
    cues = json.load(f)

high_density = []
for c in cues:
    dur = c['end'] - c['start']
    words = len(c['bn'].split())
    wps = words / dur if dur > 0 else 0
    if wps > 3.0:
        high_density.append((c['id'], dur, words, wps, c['bn'], c['en']))

print(f"Total cues exceeding 3.0 WPS (Words Per Second): {len(high_density)} out of {len(cues)}")
for cid, dur, words, wps, bn, en in high_density[:15]:
    print(f"\nCue #{cid:02d} ({dur:.2f}s, {words} words, {wps:.1f} WPS):")
    print(f"  EN: {en}")
    print(f"  BN: {bn}")
