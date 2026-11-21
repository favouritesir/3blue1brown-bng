import json

for num in [7, 8, 9]:
    p = f"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/calculus/lesson_{num:02d}/manifest.json"
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    print(f"\n=================== LESSON {num:02d} MANIFEST ===================")
    print("Course:", d.get("course"), "Lesson:", d.get("lesson"), "Voice:", d.get("voice"))
    print("Title:", d.get("title"))
    for s_key, s_data in d.get("sections", {}).items():
        if isinstance(s_data, dict) and "cues" in s_data:
            print(f"  Section key: {s_key} | audio_file: {s_data.get('audio_file')} | cues: {len(s_data['cues'])}")
            for c in s_data["cues"][:3]:
                print(f"    [{c['index']}] ({c['type']}): {c['text'][:50]}")
