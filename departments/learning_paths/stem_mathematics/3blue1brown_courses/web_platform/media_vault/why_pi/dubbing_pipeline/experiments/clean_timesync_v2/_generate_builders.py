"""Generate the 8 per-lesson build_why_pi0N_clean.py files from the template."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
TPL = (HERE / "build_why_pi_clean.TEMPLATE.py").read_text(encoding="utf-8")

V = [
    ("01", "clacks", "HEfHFsfGXjs", "The most unexpected answer to a counting puzzle"),
    ("02", "colliding-blocks-v2", "6dTyOl1fmDo", "Why colliding blocks compute pi"),
    ("03", "clacks-via-light", "brU5yLm9DZM", "How colliding blocks act like a beam of light...to compute pi."),
    ("04", "basel-problem", "d-o3eB9sfls", "Why is pi here? And why is it squared? A geometric answer to the Basel problem"),
    ("05", "leibniz-formula", "NaL_Cb42WyY", "Pi hiding in prime regularities"),
    ("06", "gaussian-integral", "cy8r7WSuT1I", "Why π is in the normal distribution (beyond integral tricks)"),
    ("07", "wallis-product", "8GPy_UMV-08", "The Wallis product for pi, proved geometrically"),
    ("08", "pi-was-628", "bcPTiiiYDs8", "How pi was almost 6.283185..."),
]

for nn, slug, vid, title in V:
    code = (TPL.replace("@@NN@@", nn)
               .replace("@@SLUG@@", slug)
               .replace("@@VIDEO_ID@@", vid)
               .replace("@@OEMBED_TITLE@@", title))
    out = HERE.parent.parent.parent / f"lesson_{nn}" / "dubbing_pipeline" / "experiments" / "clean_timesync_v2" / f"build_why_pi{nn}_clean.py"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(code, encoding="utf-8")
    print("wrote", out)
