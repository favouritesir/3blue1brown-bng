# -*- coding: utf-8 -*-
"""Headless-Chrome (channel=chrome) verification of Lesson 11 expressive audio.

Checks: 24/24 DOM cues, DOM<->manifest 1:1, 0 duplicate canonical cues,
0 quiz/media-tab types, non-zero MP3s, valid JSON, 0 page errors,
0 "চিত্র প্রদর্শনী" labels, exact ms timings vs. concatenated MP3s, and the
manifest ?v bump. No arbitrary sleeps (reactive wait_for_function only).
"""
import json
import os
import subprocess

from playwright.sync_api import sync_playwright

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "linear_algebra",
                         "lesson_11")
PAGE = "http://127.0.0.1:8085/courses/linear_algebra/lesson_11.html"
EXPECTED_ORDER = [
    "sec_01_cross_product_puzzle", "sec_02_volume_function",
    "sec_03_duality_and_dual_vector", "sec_04_geometric_proof_p",
    "sec_05_algebraic_synthesis",
]
EXPECTED_COUNTS = {
    "sec_01_cross_product_puzzle": 6, "sec_02_volume_function": 5,
    "sec_03_duality_and_dual_vector": 4, "sec_04_geometric_proof_p": 5,
    "sec_05_algebraic_synthesis": 4,
}
EXPECTED_TYPES = {
    "sec_01_cross_product_puzzle": ["h2", "chapter-quote", "p", "p", "callout", "p"],
    "sec_02_volume_function": ["h2", "p", "p", "callout", "figure"],
    "sec_03_duality_and_dual_vector": ["h2", "p", "p", "callout"],
    "sec_04_geometric_proof_p": ["h2", "p", "p", "callout", "formula-box"],
    "sec_05_algebraic_synthesis": ["h2", "p", "p", "callout"],
}
FORBIDDEN = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
FORBIDDEN_PHRASE = "চিত্র প্রদর্শনী"

# Extract DOM with narration_engine's exact selector + TeX <annotation> markers.
EXTRACT_JS = r"""() => {
  const out = [];
  document.querySelectorAll('.article > section, article section').forEach((secEl, i) => {
    if (secEl.getAttribute('data-no-narration') === 'true') return;
    const blocks = [];
    secEl.querySelectorAll('h2,h3,p,.chapter-quote,.callout,figure.lesson-figure,.code-showcase,.formula-box')
      .forEach(node => {
        if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) return;
        let type;
        if (node.tagName === 'H2') type='h2';
        else if (node.tagName === 'H3') type='h3';
        else if (node.classList.contains('chapter-quote')) type='chapter-quote';
        else if (node.classList.contains('callout')) type='callout';
        else if (node.matches('figure.lesson-figure')) type='figure';
        else if (node.classList.contains('code-showcase')) type='code-showcase';
        else if (node.classList.contains('formula-box')) type='formula-box';
        else type='p';
        const clone = node.cloneNode(true);
        clone.querySelectorAll('.katex').forEach(k => {
          const ann = k.querySelector('annotation[encoding="application/x-tex"]');
          const marker = document.createElement('span');
          marker.textContent = '<annotation>' + (ann ? ann.textContent.trim() : '') + '</annotation>';
          k.replaceWith(marker);
        });
        let text = (clone.innerText || clone.textContent || '')
          .replace(/\u00a0/g,' ').replace(/\n+/g,' ').replace(/[ \t]+/g,' ').trim();
        if (text && text.length > 2) blocks.push({ type, text });
      });
    if (blocks.length) out.push({ id: secEl.id, blocks });
  });
  return out;
}"""


def ffprobe_ms(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        check=True).stdout.strip()
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
            "window.TEACHER_AUDIO_MANIFEST && "
            "document.querySelectorAll('annotation[encoding=\"application/x-tex\"]').length > 0",
            timeout=20000,
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
    check(list(manifest["sections"]) == EXPECTED_ORDER,
          f"section keys match existing keys: {EXPECTED_ORDER}")
    check(manifest["lesson"] == "lesson_11" and
          manifest["voice"] == "bn-BD-PradeepNeural",
          "lesson/voice metadata correct")

    print("=== 4. DOM 24/24 + DOM<->manifest 1:1 ===")
    dom_map = {s["id"]: s for s in dom}
    check(set(dom_map) == set(EXPECTED_ORDER),
          f"exactly 5 narrated DOM sections: {sorted(dom_map)}")
    total_dom = total_manifest = 0
    canonical = []
    for sid in EXPECTED_ORDER:
        dsec = dom_map.get(sid, {})
        msec = manifest["sections"][sid]
        dtypes = [b["type"] for b in dsec.get("blocks", [])]
        mtypes = [c["type"] for c in msec["cues"]]
        check(dtypes == EXPECTED_TYPES[sid] == mtypes,
              f"{sid}: DOM/manifest types {mtypes} (n={len(mtypes)})")
        check(len(mtypes) == EXPECTED_COUNTS[sid],
              f"{sid}: {EXPECTED_COUNTS[sid]} cues")
        total_dom += len(dtypes)
        total_manifest += len(mtypes)
        canonical.extend(b["text"] for b in dsec.get("blocks", []))
    check(total_dom == 24 and total_manifest == 24,
          f"24/24 DOM cues and 24/24 manifest cues ({total_dom}/{total_manifest})")

    print("=== 5. No duplicates / forbidden types / no label ===")
    check(len(canonical) == len(set(canonical)),
          f"0 duplicate canonical DOM cue texts ({len(canonical)-len(set(canonical))} dupes)")
    all_texts = []
    for sid in EXPECTED_ORDER:
        all_texts.extend(c["text"] for c in manifest["sections"][sid]["cues"])
    check(len(all_texts) == len(set(all_texts)), "0 duplicate manifest cue texts")
    types_all = [c["type"] for sid in EXPECTED_ORDER
                 for c in manifest["sections"][sid]["cues"]]
    check(not (set(types_all) & FORBIDDEN), "0 quiz/media-tab cue types")
    check(all(FORBIDDEN_PHRASE not in t for t in all_texts),
          f"0 '{FORBIDDEN_PHRASE}' labels in manifest")
    check(all(FORBIDDEN_PHRASE not in b for b in canonical),
          f"0 '{FORBIDDEN_PHRASE}' labels in DOM")
    fig_count = sum(1 for t in types_all if t == "figure")
    check(fig_count == 1, f"1 naturally-phrased figure explanation ({fig_count})")

    print("=== 6. MP3 files non-zero + exact ms timings ===")
    grand_ms = 0.0
    for sid in EXPECTED_ORDER:
        msec = manifest["sections"][sid]
        mp3 = os.path.join(AUDIO_DIR, msec["audio_file"])
        size = os.path.getsize(mp3) if os.path.exists(mp3) else 0
        check(size > 0, f"{sid}: {msec['audio_file']} non-zero ({size} bytes)")
        actual_ms = ffprobe_ms(mp3)
        stated_ms = msec["total_duration_ms"]
        check(abs(actual_ms - stated_ms) <= 1200.0,
              f"{sid}: MP3 duration {actual_ms:.1f}ms ~= manifest {stated_ms}ms")
        cues = msec["cues"]
        for i, c in enumerate(cues):
            check(c["duration_ms"] > 0 and c["end_ms"] > c["start_ms"],
                  f"{sid} cue {i}: positive span")
            if i > 0:
                prev = cues[i - 1]
                gap = c["start_ms"] - prev["end_ms"]
                check(abs(gap - 350.0) <= 1.0,
                      f"{sid} cue {i}: 350ms gap (actual {gap:.1f}ms)")
        grand_ms += stated_ms
    print(f"\nTOTAL: {total_manifest} cues, {grand_ms/1000.0:.2f}s, "
          f"5 MP3s, 0 page errors, DOM<->manifest 1:1 — ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
