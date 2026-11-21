import json
from pathlib import Path

p_script = Path('departments/learning_paths/stem_mathematics/3blue1brown_courses/differential_equations/lesson_05_heat_equation/dubbing_pipeline/3b1b_diffeq_l05_bangla_master_script.json')
p_manifest = Path('departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/differential_equations/lesson_05/manifest.json')
p_manifest_js = Path('departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/differential_equations/lesson_05/manifest.js')
p_data = Path('departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/data/differential_equations/lesson_05.json')

for p in [p_script, p_manifest, p_manifest_js, p_data]:
    assert p.exists(), f'Missing {p}'
    print(f'Verified {p.name}: {p.stat().st_size} bytes')

with open(p_script, encoding='utf-8') as f:
    script = json.load(f)
with open(p_manifest, encoding='utf-8') as f:
    manifest = json.load(f)
with open(p_data, encoding='utf-8') as f:
    data = json.load(f)

print(f"Master script items: {len(script)}")
print(f"Manifest sections: {list(manifest['sections'].keys())}")
print(f"Lesson data quizzes: {len(data['quizzes'])}")
print(f"Lesson data sections: {len(data['sections'])}")
print("ALL CHECKS PASSED!")
