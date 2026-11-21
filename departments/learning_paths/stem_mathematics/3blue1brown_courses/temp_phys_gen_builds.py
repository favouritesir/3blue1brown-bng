import json
from pathlib import Path

from temp_phys_topics import TOPICS

ROOT = Path(__file__).resolve().parent
TEMPLATE = (ROOT / "temp_phys_build_template.py").read_text(encoding="utf-8")
DATA = ROOT / "web_platform" / "data" / "physics"
AUDIO = ROOT / "web_platform" / "assets" / "audio" / "physics"

for i in range(1, 14):
    lesson = json.loads((DATA / f"lesson_{i:02d}.json").read_text(encoding="utf-8"))
    manifest = json.loads((AUDIO / f"lesson_{i:02d}" / "manifest.json").read_text(encoding="utf-8"))
    cue_count = sum(len(s["cues"]) for s in manifest["sections"].values())
    vid = lesson.get("youtube_id") or lesson.get("video_id")
    body = (TEMPLATE
            .replace("__LESSON_NO__", f"{i:02d}")
            .replace("__VIDEO_ID__", str(vid))
            .replace("__CUE_COUNT__", str(cue_count))
            .replace("__TOPIC_LINES__", repr(TOPICS[i])))
    out = (ROOT / "physics" / f"lesson_{i:02d}" / "dubbing_pipeline"
           / "experiments" / "clean_timesync_v2" / f"build_phys{i:02d}_clean.py")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    compile(body, str(out), "exec")
    print(f"wrote {out.relative_to(ROOT)} | id={vid} cues={cue_count} topic_lines={len(TOPICS[i])}")
