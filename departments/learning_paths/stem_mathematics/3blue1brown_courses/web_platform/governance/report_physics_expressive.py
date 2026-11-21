# -*- coding: utf-8 -*-
"""Aggregate per-lesson verification logs into one final physics audio report."""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHECKPOINT = os.path.join(HERE, "_physics_expressive_checkpoint.json")
OUT = os.path.join(HERE, "_physics_expressive_final_report.md")


def main():
    cp = json.load(open(CHECKPOINT, encoding="utf-8")) if os.path.exists(CHECKPOINT) else {"verified": {}}
    lines = [
        "# Physics — Expressive Bengali Teacher Narration Audio",
        "",
        "Gold-standard rebuild of all 13 physics lesson manifests, replacing the",
        "placeholder timing manifests. Voice: `bn-BD-PradeepNeural`. 350 ms inter-cue",
        "silence, per-cue expressive prosody, real `ffprobe`-measured millisecond timings.",
        "",
        "| Lesson | Sections | Cues | Figures | Duration | MP3s | Verified |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    grand_cues = grand_fig = 0
    grand_ms = 0.0
    all_ok = True
    for n in range(1, 14):
        key = f"lesson_{n:02d}"
        adir = os.path.join(ROOT, "assets", "audio", "physics", key)
        mpath = os.path.join(adir, "manifest.json")
        if not os.path.exists(mpath):
            lines.append(f"| {key} | — | — | — | — | — | NOT BUILT |")
            all_ok = False
            continue
        m = json.load(open(mpath, encoding="utf-8"))
        secs = m["sections"]
        cues = sum(len(s["cues"]) for s in secs.values())
        figs = sum(1 for s in secs.values() for c in s["cues"] if c["type"] == "figure")
        ms = sum(s["total_duration_ms"] for s in secs.values())
        mp3s = [s["audio_file"] for s in secs.values()]
        nonzero = sum(1 for f in mp3s
                      if os.path.exists(os.path.join(adir, f)) and os.path.getsize(os.path.join(adir, f)) > 0)
        verified = key in cp["verified"]
        lines.append(f"| {key} | {len(secs)} | {cues} | {figs} | {ms / 1000.0:.2f}s | "
                     f"{nonzero}/{len(mp3s)} | {'PASS' if verified else 'PENDING'} |")
        grand_cues += cues
        grand_fig += figs
        grand_ms += ms
        if not verified or nonzero != len(mp3s):
            all_ok = False

    lines += [
        "",
        f"**Total:** {grand_cues} cues across 13 lessons, {grand_fig} figure explanations, "
        f"{grand_ms / 1000.0:.2f} s of narration.",
        "",
        f"**Verification status:** {'ALL 13 PASSED' if all_ok else 'INCOMPLETE — see per-lesson logs'}",
        "",
        "Per-lesson build/verify logs: `governance/_physicsNN_expressive_build.log` and",
        "`governance/_physicsNN_expressive_verify.log`. Placeholder manifests were copied",
        "to `assets/audio/physics/lesson_NN/_backup_before_expressive_build/` before each build.",
    ]
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
