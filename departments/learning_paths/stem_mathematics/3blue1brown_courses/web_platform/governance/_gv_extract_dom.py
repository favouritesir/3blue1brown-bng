# -*- coding: utf-8 -*-
"""
One-off live-DOM extraction for the NEW guest_videos course (lessons 01..05).

Uses narration_engine.js's EXACT selector + skip rules, headless Chrome
(channel="chrome"), and preserves KaTeX TeX via <annotation> markers.
Writes governance/gv0N_dom_blocks.json for lessons 01..05.
"""
import json
import os

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "file:///" + ROOT.replace("\\", "/").replace(" ", "%20")

EXTRACT_JS = r"""() => {
  const sectionElements = document.querySelectorAll('.article > section, article section');
  const out = [];
  sectionElements.forEach((secEl, sIdx) => {
    if (secEl.getAttribute('data-no-narration') === 'true') return;
    const titleEl = secEl.querySelector('h2');
    const sectionTitle = titleEl ? titleEl.innerText.trim() : 'section-' + sIdx;
    const secId = secEl.id || ('sec-' + sIdx);

    const blocks = [];
    const readableNodes = secEl.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box'
    );
    readableNodes.forEach(node => {
      if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) return;

      let type;
      if (node.tagName === 'H2') type = 'h2';
      else if (node.tagName === 'H3') type = 'h3';
      else if (node.classList.contains('chapter-quote')) type = 'quote';
      else if (node.classList.contains('callout')) type = 'callout';
      else if (node.matches('figure.lesson-figure')) type = 'figure';
      else if (node.classList.contains('code-showcase')) type = 'code-showcase';
      else if (node.classList.contains('formula-box')) type = 'formula';
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
  return out;
}"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        for n in range(1, 6):
            lid = "lesson_%02d" % n
            url = "%s/courses/guest_videos/%s.html" % (BASE, lid)
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_function(
                "() => window.narrationEngine && window.narrationEngine.sections && "
                "window.narrationEngine.sections.length >= 4",
                timeout=30000,
            )
            blocks = page.evaluate(EXTRACT_JS)
            for sec in blocks:
                for b in sec["blocks"]:
                    b["tex"] = " ".join(b.pop("tex_list", []))
            out_path = os.path.join(HERE, "gv%02d_dom_blocks.json" % n)
            with open(out_path, "w", encoding="utf-8") as fh:
                json.dump(blocks, fh, ensure_ascii=False, indent=2)
            total = 0
            print("=== %s ===" % lid)
            for sec in blocks:
                types = [b["type"] for b in sec["blocks"]]
                total += len(types)
                print("  %-20s %2d  %s" % (sec["id"], len(types), types))
            print("  TOTAL %d cues across %d sections -> %s" % (total, len(blocks), out_path))
        browser.close()


if __name__ == "__main__":
    main()
