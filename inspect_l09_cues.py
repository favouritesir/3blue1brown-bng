import json

with open("departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/calculus/lesson_09/manifest.json", "r", encoding="utf-8") as f:
    d = json.load(f)

for s_id, s_data in d["sections"].items():
    if s_id.startswith("sec-"):
        print(f"\nManifest Section {s_id}:")
        for c in s_data["cues"]:
            print(f"  [{c['index']}] {c['type']}: {c['text'][:70]}")
