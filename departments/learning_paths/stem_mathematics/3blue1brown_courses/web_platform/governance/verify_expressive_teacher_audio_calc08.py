# -*- coding: utf-8 -*-
"""
Headless-Chrome verification for the expressive teacher audio of Calculus
Lesson 08. Checks DOM<->manifest parity, cue counts, duplicates, forbidden
cue types / labels, non-empty mp3s, valid JSON, timing integrity and 0 page
errors. Uses the same channel="chrome" browser as the DOM extraction.

    python governance/verify_expressive_teacher_audio_calc08.py
"""
import os
import json
import subprocess

from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "http://127.0.0.1:8085/courses/calculus/lesson_08.html?v=verify08"
AUDIO_DIR = os.path.join(BASE, "assets", "audio", "calculus", "lesson_08")
FORBIDDEN = "চিত্র প্রদর্শনী"
EXPECTED_COUNTS = {
    "sec-accumulation-intro": 8,
    "sec-riemann-to-integral": 6,
    "sec-area-function-derivative": 6,
    "sec-fundamental-theorem": 6,
}
ALLOWED_TYPES = {"h2", "h3", "chapter-quote", "p", "figure", "callout",
                 "formula-box", "code-showcase"}
BAD_TYPES = {"quiz", "quiz-feedback", "media-tab", "media", "tab", "exercise"}

CAPTURE_JS = r"""() => {
  const eng = window.narrationEngine;
  const typeOf = (el) => {
    if (el.matches && el.matches('figure.lesson-figure')) return 'figure';
    if (el.classList && el.classList.contains('chapter-quote')) return 'chapter-quote';
    if (el.classList && el.classList.contains('callout')) return 'callout';
    if (el.classList && el.classList.contains('code-showcase')) return 'code-showcase';
    if (el.classList && el.classList.contains('formula-box')) return 'formula-box';
    if (el.tagName === 'H2') return 'h2';
    if (el.tagName === 'H3') return 'h3';
    return 'p';
  };
  const dom = (eng && eng.sections || []).map(s => ({
    id: s.id,
    types: (s.blocks || []).map(b => typeOf(b.element))
  }));
  return {
    dom,
    manifest: window.TEACHER_AUDIO_MANIFEST || null,
    articleText: (document.querySelector('b1b-article') || document.body).innerText || ''
  };
}"""


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout.strip()
    return float(out)


def main():
    errors = []
    console_errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page()
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.on("console", lambda msg: console_errors.append(msg.text)
                if msg.type == "error" else None)
        page.goto(URL, wait_until="load")
        page.wait_for_function(
            "() => window.narrationEngine && window.narrationEngine.sections && "
            "window.narrationEngine.sections.length >= 4 && "
            "window.narrationEngine.hasStudioAudio === true && "
            "!!window.TEACHER_AUDIO_MANIFEST",
            timeout=25000,
        )
        data = page.evaluate(CAPTURE_JS)
        browser.close()

    checks = []

    def check(name, ok, detail=""):
        checks.append((name, bool(ok), detail))

    dom = data["dom"]
    manifest = data["manifest"]
    sections = manifest["sections"] if manifest else {}

    # 1. Live DOM cue count per narrated section.
    dom_counts = {s["id"]: len(s["types"]) for s in dom}
    check("DOM sections == 4", len(dom) == 4, str(list(dom_counts)))
    check("DOM counts 8/6/6/6", dom_counts == EXPECTED_COUNTS, str(dom_counts))
    check("DOM total cues == 26", sum(dom_counts.values()) == 26,
          str(sum(dom_counts.values())))

    # 2. Manifest JSON valid + structure.
    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        disk_manifest = json.load(fh)
    check("manifest.json valid JSON", isinstance(disk_manifest, dict))
    js_path = os.path.join(AUDIO_DIR, "manifest.js")
    with open(js_path, encoding="utf-8") as fh:
        js_head = fh.read(40)
    check("manifest.js exports window.TEACHER_AUDIO_MANIFEST",
          js_head.startswith("window.TEACHER_AUDIO_MANIFEST"))
    check("preloaded manifest == disk manifest", manifest == disk_manifest)
    check("manifest has exactly 4 sections", len(sections) == 4,
          str(list(sections)))

    # 3. Manifest counts + DOM<->manifest 1:1 (ids, counts, type order).
    man_counts = {sid: len(sec["cues"]) for sid, sec in sections.items()}
    check("Manifest counts 8/6/6/6", man_counts == EXPECTED_COUNTS, str(man_counts))
    check("Manifest total cues == 26", sum(man_counts.values()) == 26,
          str(sum(man_counts.values())))
    check("DOM section ids == manifest section ids",
          sorted(dom_counts) == sorted(man_counts),
          f"DOM={sorted(dom_counts)} MAN={sorted(man_counts)}")
    parity = []
    for s in dom:
        sid = s["id"]
        msec = sections.get(sid, {})
        mtypes = [c["type"] for c in msec.get("cues", [])]
        parity.append((sid, s["types"] == mtypes, s["types"], mtypes))
    check("DOM<->manifest 1:1 type order (every section)",
          all(ok for _, ok, _, _ in parity),
          "; ".join(f"{sid}:{'OK' if ok else 'MISMATCH'}" for sid, ok, _, _ in parity))

    # 4. Zero duplicates.
    section_ids = list(sections)
    check("0 duplicate section ids", len(section_ids) == len(set(section_ids)))
    audio_files = [sec["audio_file"] for sec in sections.values()]
    check("0 duplicate audio_file names", len(audio_files) == len(set(audio_files)))
    idx_dups = []
    all_texts = []
    for sid, sec in sections.items():
        idxs = [c["index"] for c in sec["cues"]]
        if len(idxs) != len(set(idxs)):
            idx_dups.append(sid)
        if idxs != list(range(len(idxs))):
            idx_dups.append(sid + ":not-0-based")
        all_texts.extend(c["text"] for c in sec["cues"])
    check("0 duplicate cue indices (0-based)", not idx_dups, str(idx_dups))
    check("0 duplicate cue texts", len(all_texts) == len(set(all_texts)),
          f"{len(all_texts)} texts, {len(set(all_texts))} unique")

    # 5. No quiz / media-tab / forbidden cue types.
    used_types = {c["type"] for sec in sections.values() for c in sec["cues"]}
    check("0 quiz/media-tab cue types", not (used_types & BAD_TYPES),
          str(sorted(used_types)))
    check("all cue types in allowed set", used_types <= ALLOWED_TYPES,
          str(sorted(used_types - ALLOWED_TYPES)))

    # 6. Zero "চিত্র প্রদর্শনী" label anywhere in narration or DOM.
    check('0 "চিত্র প্রদর্শনী" in manifest cue texts',
          all(FORBIDDEN not in t for t in all_texts))
    check('0 "চিত্র প্রদর্শনী" in live DOM text',
          FORBIDDEN not in data["articleText"])

    # 7. MP3 files non-zero + positive ffprobe duration.
    mp3_info = []
    for sec in sections.values():
        path = os.path.join(AUDIO_DIR, sec["audio_file"])
        size = os.path.getsize(path) if os.path.exists(path) else 0
        dur = probe_duration(path) if size > 0 else 0.0
        mp3_info.append((sec["audio_file"], size, dur))
    check("4 mp3 files present non-zero",
          len(mp3_info) == 4 and all(s > 0 for _, s, _ in mp3_info),
          "; ".join(f"{n}:{s}B" for n, s, _ in mp3_info))
    check("4 mp3 durations > 0",
          all(d > 0 for _, _, d in mp3_info),
          "; ".join(f"{n}:{d:.2f}s" for n, _, d in mp3_info))

    # 8. Timing integrity: monotonic, 350ms gaps, total == last end.
    timing_bad = []
    total_ms = 0.0
    for sid, sec in sections.items():
        cues = sec["cues"]
        total_ms += sec["total_duration_ms"]
        for i, c in enumerate(cues):
            if c["duration_ms"] <= 0 or c["end_ms"] <= c["start_ms"]:
                timing_bad.append(f"{sid}:{i}:span")
            if i > 0:
                prev = cues[i - 1]
                gap = c["start_ms"] - prev["end_ms"]
                if abs(gap - 350.0) > 1.0:
                    timing_bad.append(f"{sid}:{i}:gap={gap}")
        if abs(cues[-1]["end_ms"] - sec["total_duration_ms"]) > 1.0:
            timing_bad.append(f"{sid}:total-mismatch")
    check("timings monotonic + 350ms gaps + totals", not timing_bad,
          str(timing_bad))

    # 9. Zero page errors.
    check("0 page errors (pageerror)", not errors, str(errors))
    check("0 console errors", not console_errors, str(console_errors[:5]))

    # Report.
    print("=" * 70)
    print("CALCULUS L08 — EXPRESSIVE TEACHER AUDIO — HEADLESS VERIFICATION")
    print("=" * 70)
    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  :: {detail}" if detail else ""))
    passed = sum(1 for _, ok, _ in checks if ok)
    print("-" * 70)
    print(f"RESULT: {passed}/{len(checks)} checks passed")
    print(f"CUES: 26 (8/6/6/6)   FIGURES: 4   "
          f"TOTAL AUDIO: {total_ms / 1000.0:.2f}s")
    print(f"PAGE ERRORS: {len(errors)}   CONSOLE ERRORS: {len(console_errors)}")
    print("=" * 70)
    if passed != len(checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
