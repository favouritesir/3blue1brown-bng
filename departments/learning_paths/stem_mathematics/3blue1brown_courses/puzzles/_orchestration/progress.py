import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSES = HERE.parent.parent
WEB = COURSES / "web_platform"

for n in range(1, 11):
    nn = f"{n:02d}"
    log = COURSES / "puzzles" / f"lesson_{nn}" / "dubbing_pipeline" / "experiments" / "clean_timesync_v2" / "_build.log"
    last = ""
    if log.exists():
        lines = [x for x in log.read_text(encoding="utf-8", errors="ignore").splitlines() if x.strip()]
        last = lines[-1] if lines else ""
    vpath = WEB / "media_vault" / "puzzles" / f"lesson_{nn}" / "experiments" / "verification.json"
    status = "PENDING"
    if vpath.exists():
        d = json.loads(vpath.read_text(encoding="utf-8"))
        g = d.get("gates", {})
        status = (f"PASS fill={d['median_fill']} gap={d['max_internal_gap_s']} "
                  f"dur={d['output_duration_sec']}/{d['video_duration_sec']} "
                  f"int>2s={d['independent_verification']['internal_runs_gt_2s_count']} "
                  f"cues={d['cue_count']} id={d['video_id']}")
    print(f"L{nn}: {status} | {last[-95:]}")
