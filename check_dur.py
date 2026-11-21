import json, subprocess
p = r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/calculus/lesson_02/sec_01_paradox.mp3"
cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{p}"'
res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print("Actual mp3 duration (ms):", float(res.stdout.strip()) * 1000)
with open(r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/calculus/lesson_02/sec_01_paradox_cues.json", "r", encoding="utf-8") as f:
    d = json.load(f)
print("Cues duration (ms):", d["total_duration_ms"])
