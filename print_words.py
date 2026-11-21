import json

with open("word_level_vocal_timeline.json", "r", encoding="utf-8") as f:
    words = json.load(f)

for w in words[:30]:
    print(f"[{w['start']:6.2f} - {w['end']:6.2f}] (p={w['prob']:.2f}): {w['word']}")
