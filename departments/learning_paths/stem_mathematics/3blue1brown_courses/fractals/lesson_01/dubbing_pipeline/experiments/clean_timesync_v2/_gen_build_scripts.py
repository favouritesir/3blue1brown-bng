"""Generate build_fractalsNN_clean.py for lessons 02..04 from the lesson 01 template."""
from pathlib import Path

BASE = Path(r"D:\0PEN CODE\Dub Studio\departments\learning_paths\stem_mathematics"
            r"\3blue1brown_courses\fractals")
SRC = BASE / "lesson_01" / "dubbing_pipeline" / "experiments" / "clean_timesync_v2" / "build_fractals01_clean.py"
src = SRC.read_text(encoding="utf-8")

VIDEOS = {"02": "LqbZpur38nw", "03": "gB9n2gHsHN4", "04": "3s7h2MHQtxc"}

for nn, vid in VIDEOS.items():
    t = src
    t = t.replace("Lesson 01", "Lesson " + nn)
    t = t.replace("lesson_01", "lesson_" + nn)
    t = t.replace('NN = "01"', 'NN = "' + nn + '"')
    t = t.replace('VIDEO_ID = "-RdOwhmqP5s"', 'VIDEO_ID = "' + vid + '"')
    t = t.replace("build_fractals01_clean.py", "build_fractals" + nn + "_clean.py")
    out = (BASE / ("lesson_" + nn) / "dubbing_pipeline" / "experiments" /
           "clean_timesync_v2" / ("build_fractals" + nn + "_clean.py"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(t, encoding="utf-8")
    print("wrote", out, len(t))
