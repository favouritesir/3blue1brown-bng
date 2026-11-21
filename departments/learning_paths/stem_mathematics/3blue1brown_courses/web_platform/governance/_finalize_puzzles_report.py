# -*- coding: utf-8 -*-
"""Aggregate the 10 per-lesson Chrome verification reports + backup checks."""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)

rows = []
for n in range(1, 11):
    nn = f"lesson_{n:02d}"
    report = json.load(open(os.path.join(HERE, f"_verify_puzzles{n:02d}_result.json"),
                            encoding="utf-8"))
    audio_dir = os.path.join(WORKSPACE, "assets", "audio", "puzzles", nn)
    backup_dir = os.path.join(audio_dir, "_backup_before_expressive_build")
    backups = sorted(os.listdir(backup_dir)) if os.path.isdir(backup_dir) else []
    page = os.path.join(WORKSPACE, "courses", "puzzles", nn + ".html")
    html = open(page, encoding="utf-8").read()
    versions = [int(v) for _, v in re.findall(r"(manifest\.js\?v=)(\d+)", html)]
    manifest = json.load(open(os.path.join(audio_dir, "manifest.json"), encoding="utf-8"))
    mp3s = sorted(os.listdir(audio_dir))
    mp3s = [m for m in mp3s if m.endswith(".mp3")]
    assert report["ok"] and report["dom_manifest_1to1"]
    assert report["duplicates"] == 0 and report["disallowed_types"] == 0
    assert report["quiz_media_tab_types"] == 0 and report["forbidden_label_hits"] == 0
    assert report["js_page_errors"] == 0 and report["console_errors_narration"] == 0
    assert report["mp3_nonzero"] and report["mp3_browser_loadable"] and report["json_valid"]
    assert "manifest.json" in backups and "manifest.js" in backups
    assert versions == [2]
    assert len(mp3s) == 5 and all(os.path.getsize(os.path.join(audio_dir, m)) > 0
                                 for m in mp3s)
    assert sum(len(s["cues"]) for s in manifest["sections"].values()) == report["cues"]
    rows.append({
        "lesson": nn,
        "sections": report["sections"],
        "cues": report["cues"],
        "per_section": report["per_section"],
        "figure_cues": report["figure_cues"],
        "katex_annotations": report["katex_annotations"],
        "duration_s": report["total_duration_s"],
        "mp3_files": len(mp3s),
        "backup": backups,
        "manifest_version": versions,
        "dom_manifest_1to1": report["dom_manifest_1to1"],
        "duplicates": report["duplicates"],
        "quiz_media_tab_types": report["quiz_media_tab_types"],
        "forbidden_label_hits": report["forbidden_label_hits"],
        "js_page_errors": report["js_page_errors"],
        "console_errors_narration": report["console_errors_narration"],
        "mp3_nonzero": report["mp3_nonzero"],
        "mp3_browser_loadable": report["mp3_browser_loadable"],
        "json_valid": report["json_valid"],
        "manifest_js_matches_json": report["manifest_js_matches_json"],
        "no_narration_sections": report["no_narration_sections"],
        "verified": True,
    })

final = {
    "course": "puzzles",
    "build": "expressive_teacher_audio",
    "voice": "bn-BD-PradeepNeural",
    "verification_browser": "headless Chrome channel=chrome",
    "lessons": rows,
    "totals": {
        "lessons": len(rows),
        "sections": sum(r["sections"] for r in rows),
        "cues": sum(r["cues"] for r in rows),
        "figure_cues": sum(r["figure_cues"] for r in rows),
        "katex_annotations": sum(r["katex_annotations"] for r in rows),
        "duration_s": round(sum(r["duration_s"] for r in rows), 2),
        "mp3_files": sum(r["mp3_files"] for r in rows),
        "duplicates": 0,
        "quiz_media_tab_types": 0,
        "forbidden_label_hits": 0,
        "js_page_errors": 0,
        "narration_console_errors": 0,
        "all_verified": all(r["verified"] for r in rows),
    },
}
out = os.path.join(HERE, "puzzles_teacher_audio_final_report.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(final, fh, ensure_ascii=False, indent=2)

print(f"{'lesson':<12}{'secs':>5}{'cues':>6}{'fig':>5}{'TeX':>5}{'dur(s)':>10}  verify")
for r in rows:
    print(f"{r['lesson']:<12}{r['sections']:>5}{r['cues']:>6}{r['figure_cues']:>5}"
          f"{r['katex_annotations']:>5}{r['duration_s']:>10.2f}  "
          f"{'OK' if r['verified'] else 'FAIL'}")
t = final["totals"]
print(f"TOTAL: {t['lessons']} lessons, {t['sections']} sections, {t['cues']} cues, "
      f"{t['figure_cues']} figures, {t['katex_annotations']} KaTeX annotations, "
      f"{t['duration_s']:.2f}s, {t['mp3_files']} mp3 files")
print("0 dups / 0 quiz-media-tab / 0 forbidden labels / 0 page errors / all verified")
print("Final report ->", out)
