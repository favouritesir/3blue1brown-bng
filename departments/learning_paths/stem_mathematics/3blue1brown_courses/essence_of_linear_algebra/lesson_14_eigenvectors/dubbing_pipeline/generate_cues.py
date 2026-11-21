import json
import os

out_dir = "departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/linear_algebra/lesson_14"
os.makedirs(out_dir, exist_ok=True)

with open("departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_linear_algebra/lesson_14_eigenvectors/dubbing_pipeline/3b1b_lesson_14_bangla_master_script.json", "r", encoding="utf-8") as f:
    data = json.load(f)

manifest_sections = {}

for sec in data["sections"]:
    sec_id = sec["section_id"]
    title = sec["title"]
    audio_file = f"{sec_id}.mp3"
    cues_file = f"{sec_id}_cues.json"
    
    current_ms = 0.0
    cues_list = []
    
    for i, cue in enumerate(sec["cues"]):
        start_ms = current_ms
        dur_ms = cue["duration_ms"]
        end_ms = start_ms + dur_ms
        
        cue_obj = {
            "index": cue["index"],
            "type": cue["type"],
            "text": cue["text"],
            "start_ms": round(start_ms, 1),
            "end_ms": round(end_ms, 1),
            "duration_ms": round(dur_ms, 1)
        }
        if cue.get("formula"):
            cue_obj["formula"] = cue["formula"]
            
        cues_list.append(cue_obj)
        # 350ms pause between cues
        current_ms = end_ms + 350.0

    total_duration_ms = cues_list[-1]["end_ms"] if cues_list else 0.0

    manifest_sections[sec_id] = {
        "title": title,
        "audio_file": audio_file,
        "cues_file": cues_file,
        "total_duration_ms": total_duration_ms,
        "cues": cues_list
    }

    # Write individual cues file
    cues_data = {
        "section_id": sec_id,
        "title": title,
        "audio_file": audio_file,
        "total_duration_ms": total_duration_ms,
        "cues": cues_list
    }
    with open(f"{out_dir}/{cues_file}", "w", encoding="utf-8") as cf:
        json.dump(cues_data, cf, ensure_ascii=False, indent=2)

manifest_data = {
    "course": "linear_algebra",
    "lesson": "lesson_14",
    "voice": "bn-BD-PradeepNeural",
    "mode": "authentic_teacher",
    "sections": manifest_sections
}

with open(f"{out_dir}/manifest.json", "w", encoding="utf-8") as mf:
    json.dump(manifest_data, mf, ensure_ascii=False, indent=2)

with open(f"{out_dir}/manifest.js", "w", encoding="utf-8") as mjf:
    mjf.write("window.TEACHER_AUDIO_MANIFEST = " + json.dumps(manifest_data, ensure_ascii=False, indent=2) + ";\n")

print("Generated manifest and cues files successfully.")
