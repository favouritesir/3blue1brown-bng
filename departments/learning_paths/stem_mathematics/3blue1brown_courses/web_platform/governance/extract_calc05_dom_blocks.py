# -*- coding: utf-8 -*-
"""
Extract the LIVE DOM blocks of courses/calculus/lesson_05.html using the exact
narration_engine.js section/block selection, preserving KaTeX TeX via
<annotation> markers. One-off extraction aid for the expressive audio build.

Reads the ALREADY-PARSED blocks straight from window.narrationEngine.sections —
literally the DOM the narration engine selects at runtime. Each block's
`element` is cloned and every rendered .katex node is replaced by an
<annotation>tex</annotation> marker so the underlying TeX survives (the
engine's own `b.text` is phonetically cleaned and mangles it).

Run with the local web server up (port 8085):
    python governance/extract_calc05_dom_blocks.py

Writes governance/calc05_dom_blocks.json.
"""
import json
import os

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8085/courses/calculus/lesson_05.html?v=extract"
HERE = os.path.dirname(os.path.abspath(__file__))

EXTRACT_JS = r"""() => {
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
  const out = [];
  (eng && eng.sections || []).forEach(sec => {
    const blocks = [];
    (sec.blocks || []).forEach(b => {
      const node = b.element;
      const clone = node.cloneNode(true);
      clone.querySelectorAll('.katex').forEach(k => {
        const ann = k.querySelector('annotation[encoding="application/x-tex"]');
        const tex = ann ? ann.textContent.trim() : '';
        const marker = document.createElement('span');
        marker.textContent = '<annotation>' + tex + '</annotation>';
        k.replaceWith(marker);
      });
      let text = clone.innerText || clone.textContent || '';
      text = text.replace(/\u00a0/g, ' ').replace(/\n+/g, ' ').replace(/[ \t]+/g, ' ').trim();
      const texList = [...node.querySelectorAll('.katex annotation[encoding="application/x-tex"]')]
        .map(a => a.textContent.trim());
      const mathAttr = node.getAttribute && node.getAttribute('math');
      blocks.push({ type: typeOf(node), text, tex_list: texList,
                    math_attr: mathAttr || '' });
    });
    if (blocks.length) out.push({ id: sec.id, title: sec.title, blocks });
  });
  return out;
}"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page()
        page.goto(URL, wait_until="load")
        page.wait_for_function(
            "() => window.narrationEngine && window.narrationEngine.sections && "
            "window.narrationEngine.sections.length >= 4 && "
            "window.narrationEngine.hasStudioAudio === true",
            timeout=25000,
        )
        blocks = page.evaluate(EXTRACT_JS)
        browser.close()

    for sec in blocks:
        for b in sec["blocks"]:
            b["tex"] = " ".join(b.pop("tex_list", []))
    out_path = os.path.join(HERE, "calc05_dom_blocks.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(blocks, fh, ensure_ascii=False, indent=2)

    total = 0
    for sec in blocks:
        types = [b["type"] for b in sec["blocks"]]
        total += len(types)
        print(f"{sec['id']:<28} {len(types):>2}  {types}")
    print(f"TOTAL {total} cues across {len(blocks)} narrated sections -> {out_path}")


if __name__ == "__main__":
    main()
