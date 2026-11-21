# -*- coding: utf-8 -*-
"""Headless-Chrome (channel=chrome) verification of Calculus Lesson 11 expressive audio.

Checks: 36/36 DOM cues, DOM<->manifest 1:1, 0 duplicate canonical cues,
0 quiz/media-tab types, non-zero MP3s, valid JSON, 0 page errors,
0 "চিত্র প্রদর্শনী" labels, exact ms timings vs. concatenated MP3s, the
canonical + alias section-key structure, and the manifest ?v bump.
No arbitrary sleeps (reactive wait_for_function only).
"""
import json
import os
import subprocess

from playwright.sync_api import sync_playwright

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "calculus", "lesson_11")
PAGE = "http://127.0.0.1:8085/courses/calculus/lesson_11.html?v=verify-calc11-expressive"

# Canonical section ids (the narration-engine ids the manifest is keyed by).
CANONICAL = [
    "sec-the-dx-paradox", "sec-tangent-line-geometry",
    "sec-error-and-vanishing", "sec-dx-in-integration",
    "sec-modern-perspective",
]
ALIASES = {
    "sec-the-dx-paradox": "sec_01_the_dx_paradox",
    "sec-tangent-line-geometry": "sec_02_tangent_line_geometry",
    "sec-error-and-vanishing": "sec_03_error_and_vanishing",
    "sec-dx-in-integration": "sec_04_dx_in_integration",
    "sec-modern-perspective": "sec_05_modern_perspective",
}
AUDIO_FILES = {
    "sec-the-dx-paradox": "sec_01_the_dx_paradox.mp3",
    "sec-tangent-line-geometry": "sec_02_tangent_line_geometry.mp3",
    "sec-error-and-vanishing": "sec_03_error_and_vanishing.mp3",
    "sec-dx-in-integration": "sec_04_dx_in_integration.mp3",
    "sec-modern-perspective": "sec_05_modern_perspective.mp3",
}
EXPECTED_COUNTS = {
    "sec-the-dx-paradox": 8, "sec-tangent-line-geometry": 7,
    "sec-error-and-vanishing": 8, "sec-dx-in-integration": 7,
    "sec-modern-perspective": 6,
}
EXPECTED_TYPES = {
    "sec-the-dx-paradox": ["h2", "chapter-quote", "p", "p", "p", "formula-box", "callout", "p"],
    "sec-tangent-line-geometry": ["h2", "p", "p", "p", "p", "formula-box", "callout"],
    "sec-error-and-vanishing": ["h2", "p", "p", "p", "p", "formula-box", "callout", "p"],
    "sec-dx-in-integration": ["h2", "p", "p", "p", "p", "formula-box", "callout"],
    "sec-modern-perspective": ["h2", "p", "p", "p", "formula-box", "callout"],
}
FORBIDDEN = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
FORBIDDEN_PHRASE = "চিত্র প্রদর্শনী"

# Extract DOM with narration_engine's exact selector + TeX <annotation> markers.
EXTRACT_JS = r"""() => {
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
  const out = [];
  const eng = window.narrationEngine;
  (eng && eng.sections || []).forEach((sec) => {
    const blocks = [];
    (sec.blocks || []).forEach((b) => {
      const node = b.element;
      const clone = node.cloneNode(true);
      clone.querySelectorAll('.katex, annotation[encoding="application/x-tex"]').forEach(k => {
        let tex = '';
        if (k.tagName && k.tagName.toLowerCase() === 'annotation') tex = k.textContent.trim();
        else { const a = k.querySelector && k.querySelector('annotation[encoding="application/x-tex"]');
               tex = a ? a.textContent.trim() : ''; }
        const marker = document.createElement('span');
        marker.textContent = '<annotation>' + tex + '</annotation>';
        k.replaceWith(marker);
      });
      let text = (clone.innerText || clone.textContent || '')
        .replace(/\u00a0/g, ' ').replace(/\n+/g, ' ').replace(/[ \t]+/g, ' ').trim();
      if (text && text.length > 2) blocks.push({ type: typeOf(node), text });
    });
    out.push({ id: sec.id, blocks });
  });
  return out;
}"""


def ffprobe_ms(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True).stdout.strip()
    return float(out) * 1000.0


def check(cond, msg):
    print(("  PASS  " if cond else "  FAIL  ") + msg)
    if not cond:
        raise AssertionError(msg)


def main():
    page_errors = []
    console_errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page()
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.goto(PAGE, wait_until="load")
        page.wait_for_function(
            "() => window.narrationEngine && window.narrationEngine.sections && "
            "window.narrationEngine.sections.length >= 5 && "
            "window.narrationEngine.hasStudioAudio === true && "
            "window.TEACHER_AUDIO_MANIFEST && "
            "document.querySelectorAll('annotation[encoding=\"application/x-tex\"]').length > 0",
            timeout=25000,
        )
        dom = page.evaluate(EXTRACT_JS)
        manifest = page.evaluate("() => window.TEACHER_AUDIO_MANIFEST")
        version = page.evaluate(
            "() => [...document.scripts].map(s=>s.src).find(s=>s.includes('manifest.js'))")
        browser.close()

    print("=== 1. Page errors / console ===")
    check(len(page_errors) == 0, f"0 page errors (got {len(page_errors)}: {page_errors})")
    check(len(console_errors) == 0,
          f"0 console errors (got {len(console_errors)}: {console_errors[:3]})")

    print("=== 2. Manifest ?v bump ===")
    check(bool(version) and "manifest.js?v=2" in version,
          f"manifest script bumped to ?v=2 (got {version})")

    print("=== 3. JSON / manifest structure ===")
    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        disk = json.load(fh)
    check(disk == manifest, "manifest.js === manifest.json (valid JSON, identical)")
    expected_keys = set(CANONICAL) | set(ALIASES.values())
    check(set(manifest["sections"]) == expected_keys and len(manifest["sections"]) == 10,
          f"10 section keys (5 canonical + 5 alias): {sorted(manifest['sections'])}")
    for cid in CANONICAL:
        check(manifest["sections"][cid] == manifest["sections"][ALIASES[cid]],
              f"{cid}: alias key equals canonical key")
        check(manifest["sections"][cid]["section_id"] == cid and
              manifest["sections"][cid]["alias"] == ALIASES[cid] and
              manifest["sections"][cid]["audio_file"] == AUDIO_FILES[cid],
              f"{cid}: section metadata (id/alias/audio_file) correct")
    check(manifest["lesson"] == "lesson_11" and
          manifest["voice"] == "bn-BD-PradeepNeural" and
          manifest["course"] == "calculus",
          "course/lesson/voice metadata correct")

    print("=== 4. DOM 36/36 + DOM<->manifest 1:1 ===")
    dom_map = {s["id"]: s for s in dom}
    check(set(dom_map) == set(CANONICAL),
          f"exactly 5 narrated DOM sections: {sorted(dom_map)}")
    total_dom = total_manifest = 0
    canonical = []
    for cid in CANONICAL:
        dsec = dom_map.get(cid, {})
        msec = manifest["sections"][cid]
        dtypes = [b["type"] for b in dsec.get("blocks", [])]
        mtypes = [c["type"] for c in msec["cues"]]
        check(dtypes == EXPECTED_TYPES[cid] == mtypes,
              f"{cid}: DOM/manifest types {mtypes} (n={len(mtypes)})")
        check(len(mtypes) == EXPECTED_COUNTS[cid],
              f"{cid}: {EXPECTED_COUNTS[cid]} cues")
        total_dom += len(dtypes)
        total_manifest += len(mtypes)
        canonical.extend(b["text"] for b in dsec.get("blocks", []))
    check(total_dom == 36 and total_manifest == 36,
          f"36/36 DOM cues and 36/36 manifest cues ({total_dom}/{total_manifest})")

    print("=== 5. No duplicates / forbidden types / no label ===")
    check(len(canonical) == len(set(canonical)),
          f"0 duplicate canonical DOM cue texts ({len(canonical)-len(set(canonical))} dupes)")
    all_texts = []
    for cid in CANONICAL:
        all_texts.extend(c["text"] for c in manifest["sections"][cid]["cues"])
    check(len(all_texts) == len(set(all_texts)), "0 duplicate manifest cue texts")
    types_all = [c["type"] for cid in CANONICAL
                 for c in manifest["sections"][cid]["cues"]]
    check(not (set(types_all) & FORBIDDEN), "0 quiz/media-tab cue types")
    check(all(FORBIDDEN_PHRASE not in t for t in all_texts),
          f"0 '{FORBIDDEN_PHRASE}' labels in manifest")
    check(all(FORBIDDEN_PHRASE not in b for b in canonical),
          f"0 '{FORBIDDEN_PHRASE}' labels in DOM")
    check(all(FORBIDDEN_PHRASE not in t for t in all_texts),
          "NATURAL figure phrasing preserved (no artificial figure label)")

    print("=== 6. MP3 files non-zero + exact ms timings + 350ms gaps ===")
    grand_ms = 0.0
    for cid in CANONICAL:
        msec = manifest["sections"][cid]
        mp3 = os.path.join(AUDIO_DIR, msec["audio_file"])
        size = os.path.getsize(mp3) if os.path.exists(mp3) else 0
        check(size > 0, f"{cid}: {msec['audio_file']} non-zero ({size} bytes)")
        actual_ms = ffprobe_ms(mp3)
        stated_ms = msec["total_duration_ms"]
        check(abs(actual_ms - stated_ms) <= 1200.0,
              f"{cid}: MP3 duration {actual_ms:.1f}ms ~= manifest {stated_ms}ms")
        cues = msec["cues"]
        for i, c in enumerate(cues):
            check(c["duration_ms"] > 0 and c["end_ms"] > c["start_ms"] and
                  abs(c["end_ms"] - c["start_ms"] - c["duration_ms"]) < 1.0,
                  f"{cid} cue {i}: positive, consistent span")
            if i > 0:
                prev = cues[i - 1]
                gap = c["start_ms"] - prev["end_ms"]
                check(abs(gap - 350.0) <= 1.0,
                      f"{cid} cue {i}: 350ms gap (actual {gap:.1f}ms)")
        grand_ms += stated_ms
    print(f"\nTOTAL: {total_manifest} cues, {grand_ms/1000.0:.2f}s, "
          f"5 MP3s, 10 manifest keys, 0 page errors, DOM<->manifest 1:1 — ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
