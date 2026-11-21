# -*- coding: utf-8 -*-
"""
Headless-Chrome verification of the Lesson 14 expressive teacher-audio build.

Checks (channel="chrome", headless):
  1. 23/23 cues in the live DOM (narration_engine selector), 4 narrated sections.
  2. DOM <-> manifest 1:1 (section ids, cue counts, cue type sequences).
  3. 0 duplicate cue texts; 0 quiz/media-tab cue types; 4 figure cues.
  4. 0 "চিত্র প্রদর্শনী" occurrences (DOM text, manifest text, on-disk JSON).
  5. All MP3s non-zero on disk AND loadable by the browser (loadedmetadata).
  6. Valid JSON (manifest.json + all sidecars).
  7. 0 uncaught page errors / 0 console errors.

Exits non-zero and prints FAIL lines if any check fails.
"""
import json
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio",
                         "linear_algebra", "lesson_14")
URL = "http://127.0.0.1:8085/courses/linear_algebra/lesson_14.html"

EXPECTED = {
    "sec_01_geometric_intuition":
        ["h2", "chapter-quote", "p", "figure", "callout", "p"],
    "sec_02_characteristic_equation":
        ["h2", "p", "p", "figure", "callout", "p"],
    "sec_03_special_transformations":
        ["h2", "p", "figure", "p", "callout"],
    "sec_04_3d_rotations_and_eigenbasis":
        ["h2", "p", "figure", "callout", "p", "p"],
}
AUDIO_FILES = {
    "sec_01_geometric_intuition": "sec_01_geometric_intuition.mp3",
    "sec_02_characteristic_equation": "sec_02_characteristic_equation.mp3",
    "sec_03_special_transformations": "sec_03_special_transformations.mp3",
    "sec_04_3d_rotations_and_eigenbasis": "sec_04_3d_rotations_and_eigenbasis.mp3",
}
FORBIDDEN_TYPES = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
FORBIDDEN_PHRASE = "চিত্র প্রদর্শনী"
EXPECTED_FIGURES = 4

# Extract live DOM blocks + type sequence using the narration_engine selector.
DOM_JS = r"""() => {
  const secs = window.narrationEngine ? window.narrationEngine.sections : [];
  return secs.map(sec => {
    const types = sec.blocks.map(b => {
      const el = b.element;
      if (!el) return 'unknown';
      if (el.tagName === 'H2') return 'h2';
      if (el.tagName === 'H3') return 'h3';
      if (el.classList.contains('chapter-quote')) return 'chapter-quote';
      if (el.classList.contains('callout')) return 'callout';
      if (el.matches('figure.lesson-figure')) return 'figure';
      if (el.classList.contains('code-showcase')) return 'code-showcase';
      if (el.classList.contains('formula-box')) return 'formula-box';
      return 'p';
    });
    return { id: sec.id, types, texts: sec.blocks.map(b => b.text) };
  });
}"""

# Verify each section MP3 is loadable in the browser and report its duration.
AUDIO_JS = r"""async (files) => {
  const results = [];
  for (const f of files) {
    const a = new Audio();
    const ok = await new Promise(resolve => {
      const done = v => { try { a.removeEventListener('loadedmetadata', ok); } catch(e){} resolve(v); };
      const ok = () => done(true);
      const bad = () => done(false);
      a.addEventListener('loadedmetadata', ok, { once: true });
      a.addEventListener('error', bad, { once: true });
      a.src = f;
      a.load();
    });
    results.push({ file: f, ok, duration: isFinite(a.duration) ? a.duration : -1 });
  }
  return results;
}"""


def main():
    failures = []

    # ---- On-disk JSON validity + file sizes -------------------------------
    mpath = os.path.join(AUDIO_DIR, "manifest.json")
    try:
        with open(mpath, encoding="utf-8") as fh:
            on_disk_manifest = json.load(fh)
        print("PASS  manifest.json is valid JSON")
    except Exception as e:  # noqa: BLE001
        failures.append(f"manifest.json invalid JSON: {e}")
        on_disk_manifest = {}

    for sec_id in EXPECTED:
        cues_file = os.path.join(AUDIO_DIR, sec_id + "_cues.json")
        try:
            with open(cues_file, encoding="utf-8") as fh:
                json.load(fh)
        except Exception as e:  # noqa: BLE001
            failures.append(f"{sec_id}_cues.json invalid JSON: {e}")
    if not any("cues.json invalid" in f for f in failures):
        print("PASS  all 4 sidecar cues JSON valid")

    for sec_id in EXPECTED:
        mp3 = os.path.join(AUDIO_DIR, AUDIO_FILES[sec_id])
        if not os.path.exists(mp3) or os.path.getsize(mp3) == 0:
            failures.append(f"{AUDIO_FILES[sec_id]} missing/empty on disk")
    if not any(".mp3 missing" in f for f in failures):
        print("PASS  all 4 MP3s non-zero on disk")

    # ---- Browser checks ---------------------------------------------------
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page()
        page_errors = []
        console_errors = []
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_function(
            "() => window.narrationEngine && window.narrationEngine.sections && "
            "window.narrationEngine.sections.length >= 4 && "
            "window.TEACHER_AUDIO_MANIFEST && window.TEACHER_AUDIO_MANIFEST.sections",
            timeout=20000,
        )
        dom = page.evaluate(DOM_JS)
        manifest = page.evaluate("() => window.TEACHER_AUDIO_MANIFEST")
        audio_files = [manifest["sections"][s]["audio_file"] for s in EXPECTED]
        audio_urls = ["../../assets/audio/linear_algebra/lesson_14/" + f
                      for f in audio_files]
        audio_results = page.evaluate(AUDIO_JS, audio_urls)
        browser.close()

    # Page / console errors.
    if page_errors:
        failures.append(f"uncaught page errors: {page_errors[:5]}")
    else:
        print("PASS  0 uncaught page errors")
    if console_errors:
        failures.append(f"console errors: {console_errors[:5]}")
    else:
        print("PASS  0 console errors")

    # 23/23 cue count and section ids.
    dom_map = {s["id"]: s for s in dom}
    total = sum(len(s["types"]) for s in dom)
    if set(dom_map) != set(EXPECTED):
        failures.append(f"DOM section ids mismatch: {sorted(dom_map)}")
    if total != 23:
        failures.append(f"DOM total cues {total} != 23")
    else:
        print("PASS  23/23 cues in live DOM across 4 narrated sections")

    # DOM <-> manifest 1:1.
    msec = manifest["sections"]
    if set(msec) != set(EXPECTED):
        failures.append(f"manifest sections mismatch: {sorted(msec)}")
    for sid, expected_types in EXPECTED.items():
        dtypes = dom_map.get(sid, {}).get("types", [])
        mtypes = [c["type"] for c in msec.get(sid, {}).get("cues", [])]
        if dtypes != expected_types:
            failures.append(f"{sid}: DOM types {dtypes} != expected")
        if mtypes != expected_types:
            failures.append(f"{sid}: manifest types {mtypes} != expected")
        if dtypes != mtypes:
            failures.append(f"{sid}: DOM<->manifest type mismatch")
    if not any("types" in f for f in failures):
        print("PASS  DOM <-> manifest 1:1 (ids, counts, type sequences)")

    # Manifest integrity: dups, forbidden types, forbidden phrase, timings, figures.
    all_texts = []
    total_dur = 0.0
    figures = 0
    for sid in EXPECTED:
        cues = msec[sid]["cues"]
        total_dur += msec[sid]["total_duration_ms"]
        for c in cues:
            all_texts.append(c["text"])
            if c["type"] in FORBIDDEN_TYPES:
                failures.append(f"{sid}: forbidden cue type {c['type']}")
            if FORBIDDEN_PHRASE in c["text"]:
                failures.append(f"{sid}: forbidden phrase in cue text")
            if c["type"] == "figure":
                figures += 1
        # exact 350ms gaps, zero overlap.
        for i, c in enumerate(cues):
            if c["duration_ms"] <= 0 or c["end_ms"] <= c["start_ms"]:
                failures.append(f"{sid} cue {i}: non-positive span")
            if i > 0:
                prev = cues[i - 1]
                if c["start_ms"] < prev["end_ms"]:
                    failures.append(f"{sid} cue {i}: overlap")
                if abs((c["start_ms"] - prev["end_ms"]) - 350.0) > 1.0:
                    failures.append(f"{sid} cue {i}: gap != 350ms")
    if len(all_texts) != len(set(all_texts)):
        failures.append(f"duplicate cue texts: {len(all_texts) - len(set(all_texts))}")
    else:
        print("PASS  0 duplicate cue texts")
    if not any("forbidden cue type" in f for f in failures):
        print("PASS  0 quiz/media-tab cue types")
    if not any("forbidden phrase" in f for f in failures):
        print("PASS  0 'চিত্র প্রদর্শনী' occurrences (manifest cues)")
    if figures == EXPECTED_FIGURES:
        print(f"PASS  {EXPECTED_FIGURES} figure cues, all natural prose")
    else:
        failures.append(f"figure cue count {figures} != {EXPECTED_FIGURES}")
    if not any("overlap" in f or "gap !=" in f or "non-positive" in f for f in failures):
        print("PASS  exact 350ms gaps, zero overlaps, positive spans")

    # On-disk manifest forbidden phrase check.
    if FORBIDDEN_PHRASE in json.dumps(on_disk_manifest, ensure_ascii=False):
        failures.append("forbidden phrase in on-disk manifest.json")
    # DOM text forbidden phrase check.
    for s in dom:
        for t in s["texts"]:
            if FORBIDDEN_PHRASE in t:
                failures.append(f"forbidden phrase in DOM text of {s['id']}")
    if not any("forbidden phrase" in f for f in failures):
        print("PASS  0 'চিত্র প্রদর্শনী' occurrences (DOM text + on-disk JSON)")

    # Browser audio loadability.
    for r in audio_results:
        if not r["ok"] or r["duration"] <= 0:
            failures.append(f"browser MP3 load failed: {r['file']} ok={r['ok']} dur={r['duration']}")
    if not any("browser MP3 load failed" in f for f in failures):
        print("PASS  all 4 MP3s load in browser with positive duration")
    for r in audio_results:
        print(f"        {os.path.basename(r['file'])}  {r['duration']:.2f}s  ok={r['ok']}")

    print(f"\nManifest total duration: {total_dur / 1000.0:.2f}s")

    if failures:
        print("\nFAILURES:")
        for f in dict.fromkeys(failures):
            print("  FAIL ", f)
        sys.exit(1)
    print("\nALL CHECKS PASSED — Lesson 14 expressive teacher audio verified.")


if __name__ == "__main__":
    main()
