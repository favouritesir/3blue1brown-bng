import json

with open(r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/calculus/lesson_02/sec_01_paradox_cues.json", "r", encoding="utf-8") as f:
    d = json.load(f)

for c in d["cues"]:
    print(c["index"], c["type"], c["start_ms"], c["end_ms"], c["duration_ms"])
    print("  ", c["text"][:60])
