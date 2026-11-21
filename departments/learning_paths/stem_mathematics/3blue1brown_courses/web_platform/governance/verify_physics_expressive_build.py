# -*- coding: utf-8 -*-
"""
Headless-Chrome (channel="chrome") verification of a PHYSICS expressive
teacher-audio build. Usage: python governance/verify_physics_expressive_build.py NN

Checks:
  1. Live DOM (narration_engine selector) section ids/counts/types <-> manifest 1:1
  2. 0 duplicate cue texts; 0 quiz/media-tab cue types
  3. All section MP3s non-zero on disk AND loadable in-browser (positive duration)
  4. Valid JSON (manifest.json + window.TEACHER_AUDIO_MANIFEST in manifest.js)
  5. 0 uncaught page errors
  6. 0 forbidden labels ("চিত্র প্রদর্শনী") in DOM / manifest / on-disk JSON
  7. Exact 350 ms gaps, zero overlap, positive spans
  8. Page manifest script has a ?v cache-buster; placeholder backup exists
Exits non-zero on any failure.
"""
import json
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
NN = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LESSON = f"lesson_{NN:02d}"
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "physics", LESSON)
PAGE = os.path.join(WORKSPACE, "courses", "physics", f"{LESSON}.html")
URL = f"http://127.0.0.1:8085/courses/physics/{LESSON}.html?v=verify{NN}"

FORBIDDEN_TYPES = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
FORBIDDEN_PHRASE = "চিত্র প্রদর্শনী"

DOM_JS = r"""() => {
  const secs = window.narrationEngine ? window.narrationEngine.sections : [];
  const typeOf = el => {
    if (!el) return 'unknown';
    if (el.tagName === 'H2') return 'h2';
    if (el.tagName === 'H3') return 'h3';
    if (el.classList.contains('chapter-quote')) return 'chapter-quote';
    if (el.classList.contains('callout')) return 'callout';
    if (el.matches('figure.lesson-figure')) return 'figure';
    if (el.classList.contains('code-showcase')) return 'code-showcase';
    if (el.classList.contains('formula-box')) return 'formula-box';
    return 'p';
  };
  return secs.map(sec => ({
    id: sec.id,
    types: sec.blocks.map(b => typeOf(b.element)),
    texts: sec.blocks.map(b => b.text),
  }));
}"""

AUDIO_JS = r"""async (files) => {
  const results = [];
  for (const f of files) {
    const a = new Audio();
    const ok = await new Promise(resolve => {
      const done = v => resolve(v);
      a.addEventListener('loadedmetadata', () => done(true), { once: true });
      a.addEventListener('error', () => done(false), { once: true });
      a.src = f;
      a.load();
    });
    results.push({ file: f, ok, duration: isFinite(a.duration) ? a.duration : -1 });
  }
  return results;
}"""


def main():
    failures = []

    # ---- On-disk JSON / files / backup -------------------------------------
    mpath = os.path.join(AUDIO_DIR, "manifest.json")
    jpath = os.path.join(AUDIO_DIR, "manifest.js")
    try:
        on_disk = json.load(open(mpath, encoding="utf-8"))
        print("PASS  manifest.json is valid JSON")
    except Exception as e:  # noqa: BLE001
        failures.append(f"manifest.json invalid JSON: {e}")
        on_disk = {}
    js_text = open(jpath, encoding="utf-8").read()
    if not js_text.startswith("window.TEACHER_AUDIO_MANIFEST = "):
        failures.append("manifest.js does not assign window.TEACHER_AUDIO_MANIFEST")
    else:
        print("PASS  manifest.js assigns window.TEACHER_AUDIO_MANIFEST")

    backup = os.path.join(AUDIO_DIR, "_backup_before_expressive_build")
    for f in ("manifest.json", "manifest.js"):
        if not os.path.exists(os.path.join(backup, f)):
            failures.append(f"missing placeholder backup: {f}")

    # ---- Browser -----------------------------------------------------------
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page()
        page_errors, console_errors = [], []
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_function(
            "() => window.narrationEngine && window.narrationEngine.sections && "
            "window.narrationEngine.sections.length > 0 && "
            "window.TEACHER_AUDIO_MANIFEST && window.TEACHER_AUDIO_MANIFEST.sections",
            timeout=20000,
        )
        dom = page.evaluate(DOM_JS)
        manifest = page.evaluate("() => window.TEACHER_AUDIO_MANIFEST")
        manifest_scripts = page.eval_on_selector_all(
            "script", "(els) => els.map(e => e.src).filter(s => s.includes('manifest.js'))")
        audio_files = [manifest["sections"][s["id"]]["audio_file"] for s in dom]
        audio_urls = [f"../../assets/audio/physics/{LESSON}/{f}" for f in audio_files]
        audio_results = page.evaluate(AUDIO_JS, audio_urls)
        browser.close()

    if page_errors:
        failures.append(f"uncaught page errors: {page_errors[:5]}")
    else:
        print("PASS  0 uncaught page errors")
    benign = [c for c in console_errors if "compute-pressure" not in c]
    if benign:
        failures.append(f"console errors: {benign[:5]}")
    else:
        print(f"PASS  0 unexpected console errors "
              f"({len(console_errors) - len(benign)} benign permission-policy notices ignored)")

    # Cache-buster.
    if not any("manifest.js?v=" in s for s in manifest_scripts):
        failures.append("page manifest.js script has no ?v cache-buster")
    else:
        print("PASS  page manifest.js carries ?v cache-buster")

    # ---- DOM <-> manifest 1:1 ---------------------------------------------
    dom_map = {s["id"]: s for s in dom}
    msec = manifest.get("sections", {})
    total_dom = sum(len(s["types"]) for s in dom)
    if set(dom_map) != set(msec):
        failures.append(f"DOM/manifest section ids mismatch: DOM={sorted(dom_map)} MAN={sorted(msec)}")
    if set(msec) != set(on_disk.get("sections", {})):
        failures.append("browser manifest sections != on-disk manifest sections")
    else:
        print("PASS  browser manifest matches on-disk manifest sections")
    for sid in set(dom_map) | set(msec):
        dtypes = dom_map.get(sid, {}).get("types", [])
        mtypes = [c["type"] for c in msec.get(sid, {}).get("cues", [])]
        if dtypes != mtypes:
            failures.append(f"{sid}: DOM types {dtypes} != manifest types {mtypes}")
    if not any("types" in f for f in failures):
        print(f"PASS  DOM <-> manifest 1:1 ({total_dom} cues across {len(dom)} sections)")

    # ---- Manifest integrity ------------------------------------------------
    all_texts, total_dur, figures = [], 0.0, 0
    for sid, sec in msec.items():
        cues = sec.get("cues", [])
        total_dur += sec.get("total_duration_ms", 0)
        for c in cues:
            all_texts.append(c.get("text", ""))
            if c.get("type") in FORBIDDEN_TYPES:
                failures.append(f"{sid}: forbidden cue type {c['type']}")
            if FORBIDDEN_PHRASE in c.get("text", ""):
                failures.append(f"{sid}: forbidden phrase in cue text")
        figures += sum(1 for c in cues if c.get("type") == "figure")
        for i, c in enumerate(cues):
            if c.get("duration_ms", 0) <= 0 or c.get("end_ms", 0) <= c.get("start_ms", 0):
                failures.append(f"{sid} cue {i}: non-positive span")
            if i > 0:
                prev = cues[i - 1]
                if c["start_ms"] < prev["end_ms"]:
                    failures.append(f"{sid} cue {i}: overlap")
                if abs((c["start_ms"] - prev["end_ms"]) - 350.0) > 1.0:
                    failures.append(f"{sid} cue {i}: gap != 350ms")
    dups = len(all_texts) - len(set(all_texts))
    if dups:
        failures.append(f"duplicate cue texts: {dups}")
    else:
        print("PASS  0 duplicate cue texts")
    if not any("forbidden cue type" in f for f in failures):
        print("PASS  0 quiz/media-tab cue types")
    if not any("overlap" in f or "gap !=" in f or "non-positive" in f for f in failures):
        print("PASS  exact 350ms gaps, zero overlaps, positive spans")

    # Forbidden phrase across DOM + on-disk JSON.
    if FORBIDDEN_PHRASE in json.dumps(on_disk, ensure_ascii=False):
        failures.append("forbidden phrase in on-disk manifest.json")
    for s in dom:
        for t in s["texts"]:
            if FORBIDDEN_PHRASE in t:
                failures.append(f"forbidden phrase in DOM text of {s['id']}")
    if not any("forbidden phrase" in f for f in failures):
        print("PASS  0 forbidden 'চিত্র প্রদর্শনী' labels")

    # ---- MP3s --------------------------------------------------------------
    for f in audio_files:
        fp = os.path.join(AUDIO_DIR, f)
        if not os.path.exists(fp) or os.path.getsize(fp) == 0:
            failures.append(f"{f}: missing/empty on disk")
    if not any(".mp3 missing" in f or "empty on disk" in f for f in failures):
        print(f"PASS  all {len(audio_files)} section MP3s non-zero on disk")
    for r in audio_results:
        if not r["ok"] or r["duration"] <= 0:
            failures.append(f"browser MP3 load failed: {r['file']} ok={r['ok']} dur={r['duration']}")
    if not any("browser MP3 load failed" in f for f in failures):
        print(f"PASS  all {len(audio_results)} MP3s load in browser with positive duration")
    for r in audio_results:
        print(f"        {os.path.basename(r['file'])}  {r['duration']:.2f}s  ok={r['ok']}")

    print(f"\n{LESSON}: {total_dom} cues, {len(dom)} sections, {figures} figures, "
          f"{total_dur / 1000.0:.2f}s total manifest duration")

    if failures:
        print("\nFAILURES:")
        for f in dict.fromkeys(failures):
            print("  FAIL ", f)
        sys.exit(1)
    print(f"\nALL CHECKS PASSED — Physics {LESSON} expressive teacher audio verified.")


if __name__ == "__main__":
    main()
