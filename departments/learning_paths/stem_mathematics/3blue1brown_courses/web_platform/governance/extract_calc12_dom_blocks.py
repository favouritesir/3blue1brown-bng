# -*- coding: utf-8 -*-
"""
Extract the LIVE DOM blocks of courses/calculus/lesson_12.html using
narration_engine.js's exact selector + skip rules, preserving KaTeX TeX via
<annotation> markers.

Run with the local web server up (port 8085):
    python governance/extract_calc12_dom_blocks.py

Writes governance/calc12_dom_blocks.json. The re-runnable expressive builder
validates its embedded scripts against both the HTML source and this
browser-extracted live DOM snapshot.

Browser: headless Chrome via channel="chrome".
Waiting is reactive (wait_for_function on rendered narration sections and KaTeX
annotations) - no arbitrary fixed sleeps.
"""
import json
import os

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8085/courses/calculus/lesson_12.html?v=extract-dom-calc12"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "calc12_dom_blocks.json")

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
        if (k.tagName && k.tagName.toLowerCase() === 'annotation') {
          tex = k.textContent.trim();
        } else {
          const ann = k.querySelector && k.querySelector('annotation[encoding="application/x-tex"]');
          tex = ann ? ann.textContent.trim() : '';
        }
        const marker = document.createElement('span');
        marker.textContent = '<annotation>' + tex + '</annotation>';
        k.replaceWith(marker);
      });
      let text = clone.innerText || clone.textContent || '';
      text = text.replace(/\u00a0/g, ' ').replace(/\n+/g, ' ')
                 .replace(/[ \t]+/g, ' ').trim();
      const texList = [...(node.querySelectorAll ?
        node.querySelectorAll('annotation[encoding="application/x-tex"]') : [])]
        .map(a => a.textContent.trim());
      if (text && text.length > 2) {
        blocks.push({ type: typeOf(node), text, tex_list: texList,
                      engine_text: b.text || '' });
      }
    });
    out.push({ id: sec.id, title: sec.title, blocks,
               audioFile: sec.audioFile || '', cues: (sec.cues || []).length });
  });

  // Raw-DOM pass using the exact parseContent selector as a cross-check.
  const raw = [];
  document.querySelectorAll('.article > section, article section').forEach((secEl, sIdx) => {
    if (secEl.getAttribute('data-no-narration') === 'true') return;
    const types = [];
    secEl.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box'
    ).forEach(node => {
      if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) return;
      types.push(typeOf(node));
    });
    raw.push({ id: secEl.id || ('sec-' + sIdx), types });
  });
  return { sections: out, rawDom: raw };
}"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page()
        errs = []
        page.on('pageerror', lambda e: errs.append(str(e)))
        page.goto(URL, wait_until="load")
        page.wait_for_function(
            "() => window.narrationEngine && window.narrationEngine.sections && "
            "window.narrationEngine.sections.length >= 5 && "
            "window.narrationEngine.hasStudioAudio === true && "
            "document.querySelectorAll('annotation[encoding=\"application/x-tex\"]').length > 0",
            timeout=25000,
        )
        data = page.evaluate(EXTRACT_JS)
        browser.close()

    print("PAGE ERRORS:", errs[:5] if errs else "none")

    for sec in data["sections"]:
        for b in sec["blocks"]:
            b["tex"] = " ".join(b.pop("tex_list", []))

    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)

    total = 0
    print("\nEngine sections (canonical DOM):")
    for sec in data["sections"]:
        types = [b["type"] for b in sec["blocks"]]
        total += len(types)
        print(f"  {sec['id']:<40} {len(types):>2}  {types}")
    print("\nRaw-DOM cross-check:")
    for sec in data["rawDom"]:
        print(f"  {sec['id']:<40} {len(sec['types']):>2}  {sec['types']}")
    print(f"\nTOTAL {total} cues across {len(data['sections'])} narrated sections "
          f"-> {OUT_PATH}")


if __name__ == "__main__":
    main()
