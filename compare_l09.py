import json

with open("departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/data/calculus/lesson_09.json", "r", encoding="utf-8") as f:
    d = json.load(f)

for s in d["sections"]:
    print(f"\nSection {s['id']}:")
    print("  title:", s.get("title_bn"))
    if 'paragraphs' in s:
        for idx, p in enumerate(s['paragraphs']):
            print(f"  p{idx}:", p[:70])
