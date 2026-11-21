from pathlib import Path

HERE = Path(__file__).resolve().parent
tpl = (HERE / "_build_template.py").read_text(encoding="utf-8")

LESSONS = {
    1: "iv-5mZ_9CPY",
    2: "_BrFKp-U8GI",
    3: "itRV2jEtV8Q",
    4: "4NlrfOl0l8U",
    5: "M-MgQC6z3VU",
}

for n, vid in LESSONS.items():
    txt = tpl.replace("__NN__", f"{n:02d}").replace("__VID__", vid)
    out = HERE / f"lesson_{n:02d}" / "dubbing_pipeline" / "experiments" / "clean_timesync_v2" / f"build_gv{n:02d}_clean.py"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(txt, encoding="utf-8")
    print(out)
