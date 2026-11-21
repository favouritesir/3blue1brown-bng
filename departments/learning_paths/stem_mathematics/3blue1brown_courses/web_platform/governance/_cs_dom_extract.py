# -*- coding: utf-8 -*-
"""Extract the LIVE narration-engine DOM (cue id/count/type + KaTeX annotations)
for the NEW Computer Science course using headless Chrome (channel=chrome).

Reads only the rendered DOM -- nothing is inferred from the source data files.
Writes governance/_cs_dom_dump.json, consumed by the per-lesson builders.
"""
import json
import os
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "http://127.0.0.1:8100"

NARRATION_SCRIPTS = [
    "assets/libs/katex/katex.min.js", "assets/libs/katex/auto-render.min.js",
    "assets/libs/katex-stub.js", "assets/js/lesson_components.js",
    "assets/js/lesson_components_extended.js", "assets/js/main.js",
    "assets/js/lesson.js", "assets/js/narration_engine.js",
]

EVAL = r"""() => {
  const E = window.narrationEngine, M = window.TEACHER_AUDIO_MANIFEST;
  const typeOf = (el) => {
    if (el.matches('h2')) return 'h2';
    if (el.matches('h3')) return 'h3';
    if (el.matches('figure.lesson-figure')) return 'figure';
    if (el.classList.contains('formula-box')) return 'formula-box';
    if (el.classList.contains('callout')) return 'callout';
    if (el.classList.contains('chapter-quote')) return 'chapter-quote';
    if (el.classList.contains('code-showcase')) return 'code-showcase';
    return 'p';
  };
  const texOf = (el) => Array.from(el.querySelectorAll(
      'annotation[encoding="application/x-tex"], .katex-mathml annotation'
    )).map(a => (a.textContent || '').trim()).filter(Boolean);
  const sections = (E ? E.sections : []).map(s => ({
    id: s.id,
    title: s.title,
    audio_file: (M && M.sections[s.id]) ? M.sections[s.id].audio_file : null,
    dom_section_id: s.element ? s.element.id : null,
    blocks: s.blocks.map((b, i) => ({
      index: i,
      type: typeOf(b.element),
      engine_text: b.text || '',
      raw_text: (b.element.innerText || '').trim(),
      tag: b.element.tagName,
      classes: b.element.className || '',
      katex_src: texOf(b.element)
    }))
  }));
  return {
    title: document.title,
    sections: sections,
    manifest_section_ids: Object.keys((M && M.sections) || {}),
    scripts: Array.from(document.querySelectorAll('head script[src]'))
              .map(s => s.getAttribute('src'))
  };
}"""


def main():
    out = {}
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        for n in range(1, 14):
            page = browser.new_page()
            perr = []
            page.on("pageerror", lambda e, a=perr: a.append(str(e)))
            url = "%s/courses/computer_science/lesson_%02d.html?v=dom" % (BASE, n)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_function(
                    "() => window.narrationEngine && window.narrationEngine.sections.length > 0",
                    timeout=20000,
                )
                page.wait_for_function(
                    "() => document.querySelectorAll('annotation[encoding=\"application/x-tex\"]').length > 0",
                    timeout=10000,
                )
                data = page.evaluate(EVAL)
                data["pageerrors"] = perr
                out["lesson_%02d" % n] = data
                print("lesson_%02d: %d sections, %d cues, %d KaTeX, %d page errors" % (
                    n, len(data["sections"]),
                    sum(len(s["blocks"]) for s in data["sections"]),
                    sum(len(b["katex_src"]) for s in data["sections"] for b in s["blocks"]),
                    len(perr)))
            except Exception as e:  # noqa: BLE001
                errors.append("lesson_%02d: %s" % (n, str(e).split("\n")[0]))
                print("lesson_%02d FAILED: %s" % (n, errors[-1]))
            page.close()
        browser.close()
    out["_meta"] = {"errors": errors, "channel": "chrome", "headless": True}
    dst = os.path.join(ROOT, "governance", "_cs_dom_dump.json")
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print("\nWrote %s (errors=%d)" % (dst, len(errors)))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
