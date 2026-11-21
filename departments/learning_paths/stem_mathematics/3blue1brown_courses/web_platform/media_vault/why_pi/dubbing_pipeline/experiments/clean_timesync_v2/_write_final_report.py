"""Aggregate every lesson's verification.json into one Markdown report."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WHYPI = HERE.parent.parent.parent
REPORT = HERE / "FINAL_VERIFICATION_REPORT.md"

rows = []
all_ok = True
for nn in ["01", "02", "03", "04", "05", "06", "07", "08"]:
    vf = WHYPI / f"lesson_{nn}" / "dubbing_pipeline" / "experiments" / "clean_timesync_v2" / "verification.json"
    if not vf.exists():
        rows.append(f"| {nn} | — | — | — | — | — | — | — | NO VERIFICATION |")
        all_ok = False
        continue
    d = json.loads(vf.read_text(encoding="utf-8"))
    iv = d.get("independent_verification", {})
    g = d.get("gates", {})
    ok = bool(d.get("success"))
    all_ok = all_ok and ok
    rows.append(
        f"| {nn} | `{d.get('video_id')}` | {d.get('cue_count')} | "
        f"{d.get('video_duration_sec')}s | {iv.get('output_duration_sec')}s | "
        f"{iv.get('duration_delta_sec')}s | {d.get('median_fill')} | "
        f"{d.get('max_internal_gap_s')}s | {iv.get('internal_runs_gt_2s_count')} | "
        f"{'PASS' if ok else 'FAIL'} |"
    )

lines = [
    "# Why-Pi — Full-length Bengali dub verification",
    "",
    "## Resolved official 3Blue1Brown YouTube IDs",
    "",
    "| Lesson | Slug | YouTube ID | oEmbed author | oEmbed title |",
    "|---|---|---|---|---|",
]
ids = [
    ("01", "clacks", "HEfHFsfGXjs", "The most unexpected answer to a counting puzzle"),
    ("02", "colliding-blocks-v2", "6dTyOl1fmDo", "Why colliding blocks compute pi"),
    ("03", "clacks-via-light", "brU5yLm9DZM", "How colliding blocks act like a beam of light...to compute pi."),
    ("04", "basel-problem", "d-o3eB9sfls", "Why is pi here? And why is it squared? A geometric answer to the Basel problem"),
    ("05", "leibniz-formula", "NaL_Cb42WyY", "Pi hiding in prime regularities"),
    ("06", "gaussian-integral", "cy8r7WSuT1I", "Why π is in the normal distribution (beyond integral tricks)"),
    ("07", "wallis-product", "8GPy_UMV-08", "The Wallis product for pi, proved geometrically"),
    ("08", "pi-was-628", "bcPTiiiYDs8", "How pi was almost 6.283185..."),
]
for nn, slug, vid, title in ids:
    lines.append(f"| {nn} | {slug} | `{vid}` | 3Blue1Brown | {title} |")

lines += [
    "",
    "ID source: `https://www.3blue1brown.com/lessons/<slug>` `VideoObject.embedUrl`; "
    "each verified with `https://www.youtube.com/oembed` (`author_name = 3Blue1Brown`).",
    "",
    "## Quality gates (independent verification on final MP4)",
    "",
    "Gates: duration delta ≤ 1.0 s; zero internal silence runs > 2 s "
    "(lead-in/tail excluded); median_fill ≥ 0.72; max_internal_gap_s ≤ 1.5.",
    "",
    "| Lesson | ID | Cues | Original | Output | Δ dur | median_fill | max_gap | internal>2s | Result |",
    "|---|---|---|---|---|---|---|---|---|---|",
]
lines.extend(rows)
lines += [
    "",
    f"**ALL LESSONS PASS: {all_ok}**",
    "",
    "## Method",
    "",
    "- Cue texts: gold manifests under `web_platform/assets/audio/why_pi/lesson_NN/manifest.json` (read-only).",
    "- TTS: edge-tts `bn-BD-PradeepNeural`, robust retries + half/sentence fallbacks.",
    "- Scale recomputed from *measured rendered speech*; auto re-render (contextual Bengali "
    "pedagogical expansion) when the required tempo would fall below the 0.82 floor.",
    "- Absolute sample placement `start*44100` (zero cumulative drift); atempo in [0.82, 2.2]; "
    "pad only, never truncate; NO SFX.",
    "- Full-length canvas before `-shortest`; `loudnorm=I=-14:LRA=7:TP=-1`; `-c:v copy`.",
    "- Independent check: ffprobe duration + ffmpeg `silencedetect` on the final MP4.",
    "",
]

REPORT.write_text("\n".join(lines), encoding="utf-8")
print("wrote", REPORT)
print("ALL_OK", all_ok)
