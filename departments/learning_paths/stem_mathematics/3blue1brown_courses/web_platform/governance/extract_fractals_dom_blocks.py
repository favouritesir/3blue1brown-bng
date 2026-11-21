# -*- coding: utf-8 -*-
"""
Extract the LIVE DOM blocks of courses/fractals/lesson_01.html .. lesson_04.html
using narration_engine.js's exact selector + skip rules, preserving KaTeX TeX
via <annotation> markers. One-off extraction aid for the expressive audio build.

Run with the local web server up (port 8085):
    python governance/extract_fractals_dom_blocks.py

Writes governance/fractals_dom_blocks_L01.json .. fractals_dom_blocks_L04.json.
Also writes governance/fractals_dom_runtime_LNN.json with the narrationEngine's
live-parsed section ids / block counts, for a DOM<->engine cross check.
"""
import json
import os

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "http://127.0.0.1:8085/courses/fractals/lesson_{:02d}.html"

EXTRACT_JS = r"""() => {
  const sectionElements = document.querySelectorAll('.article > section, article section');
  const out = [];
  const runtime = [];
  sectionElements.forEach((secEl, sIdx) => {
    const titleEl = secEl.querySelector('h2');
    let sectionTitle = secEl.getAttribute('title') || (titleEl ? titleEl.innerText.trim() : '');
    const secId = secEl.id || ('sec-' + sIdx);
    const noNarration = secEl.getAttribute('data-no-narration') === 'true';
    runtime.push({ id: secId, title: sectionTitle, noNarration: noNarration });
    if (noNarration) return;

    const blocks = [];
    const readableNodes = secEl.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box'
    );
    readableNodes.forEach(node => {
      if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) return;

      let type;
      if (node.tagName === 'H2') type = 'h2';
      else if (node.tagName === 'H3') type = 'h3';
      else if (node.classList.contains('chapter-quote')) type = 'chapter-quote';
      else if (node.classList.contains('callout')) type = 'callout';
      else if (node.matches('figure.lesson-figure')) type = 'figure';
      else if (node.classList.contains('code-showcase')) type = 'code-showcase';
      else if (node.classList.contains('formula-box')) type = 'formula-box';
      else type = 'p';

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

      if (text && text.length > 2) {
        blocks.push({ type, text, tex_list: texList });
      }
    });

    if (blocks.length > 0) out.push({ id: secId, title: sectionTitle, blocks });
  });
  return { sections: out, runtime };
}"""


def main():
    grand_total = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        for n in range(1, 5):
            page = browser.new_page()
            page.goto(BASE.format(n), wait_until="load")
            # Reactive wait: DOM upgraded + narration engine parsed before extracting.
            page.wait_for_function(
                "() => window.narrationEngine && window.narrationEngine.sections && "
                "window.narrationEngine.sections.length >= 1",
                timeout=25000,
            )
            result = page.evaluate(EXTRACT_JS)
            blocks = result["sections"]
            runtime = result["runtime"]

            # Cross check extractor sections vs the engine's own parsed sections.
            eng = page.evaluate(
                "() => window.narrationEngine.sections.map(s => "
                "({id:s.id, blocks:(s.blocks||[]).length, cues:(s.cues||[]).length}))"
            )
            for sec in blocks:
                for b in sec["blocks"]:
                    b["tex"] = " ".join(b.pop("tex_list", []))
            page.close()

            tag = f"L{n:02d}"
            out_path = os.path.join(HERE, f"fractals_dom_blocks_{tag}.json")
            with open(out_path, "w", encoding="utf-8") as fh:
                json.dump(blocks, fh, ensure_ascii=False, indent=2)
            rt_path = os.path.join(HERE, f"fractals_dom_runtime_{tag}.json")
            with open(rt_path, "w", encoding="utf-8") as fh:
                json.dump({"runtime": runtime, "engine": eng}, fh, ensure_ascii=False, indent=2)

            print(f"\n=== lesson {n:02d} ===")
            total = 0
            for sec in blocks:
                types = [b["type"] for b in sec["blocks"]]
                total += len(types)
                print(f"  {sec['id']:<26} {len(types):>2}  {types}")
            print(f"  engine: {eng}")
            print(f"  TOTAL {total} cues across {len(blocks)} narrated sections -> {out_path}")
            grand_total += total
        browser.close()
    print(f"\nGRAND TOTAL {grand_total} cues across 4 lessons.")


if __name__ == "__main__":
    main()
