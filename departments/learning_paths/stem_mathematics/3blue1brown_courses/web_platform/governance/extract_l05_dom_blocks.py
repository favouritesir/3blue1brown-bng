# -*- coding: utf-8 -*-
"""
Extract the LIVE DOM blocks of lesson_05.html using narration_engine.js's exact
selector + skip rules, preserving KaTeX TeX via <annotation> markers.

Run with the local web_server up (port 8123):
    python governance/extract_l05_dom_blocks.py

Writes governance/l05_dom_blocks.json. This is a one-off extraction aid; the
re-runnable builder embeds its own scripts and validates DOM parity from source
AND against this browser-extracted live DOM snapshot.

Waiting is reactive (wait_for_function on the rendered narration sections and
KaTeX annotations) — no arbitrary fixed sleeps.
"""
import json
import os

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8123/courses/linear_algebra/lesson_05.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
HERE = os.path.dirname(os.path.abspath(__file__))

EXTRACT_JS = r"""() => {
  // Replicate narration_engine.parseContent() selectors and skip rules exactly.
  const sectionElements = document.querySelectorAll('.article > section, article section');
  const out = [];
  sectionElements.forEach((secEl, sIdx) => {
    if (secEl.getAttribute('data-no-narration') === 'true') return;
    const titleEl = secEl.querySelector('h2');
    // Use the component title when present (h2 innerText can include KaTeX noise).
    let sectionTitle = secEl.getAttribute('title') || (titleEl ? titleEl.innerText.trim() : '');
    const secId = secEl.id || ('sec-' + sIdx);

    const blocks = [];
    const readableNodes = secEl.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box'
    );
    readableNodes.forEach(node => {
      // skip <p> inside .callout / .chapter-quote (author/caption paragraphs)
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

      // Clone node and replace each rendered KaTeX span with a TeX marker so the
      // canonical text preserves the original LaTeX via <annotation>...</annotation>.
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
        blocks.push({ type, text, tex: '', tex_list: texList });
      }
    });

    if (blocks.length > 0) out.push({ id: secId, title: sectionTitle, blocks });
  });
  return out;
}"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page()
        page.goto(URL, wait_until="load")
        # Reactive wait: narration engine parsed >=3 sections and KaTeX rendered.
        page.wait_for_function(
            "() => window.narrationEngine && window.narrationEngine.sections && "
            "window.narrationEngine.sections.length >= 3 && "
            "document.querySelectorAll('annotation[encoding=\"application/x-tex\"]').length > 0",
            timeout=20000,
        )
        blocks = page.evaluate(EXTRACT_JS)
        browser.close()

    # Flatten tex_list -> `tex` field to match the l01-l04 dom_blocks schema,
    # while <annotation> markers in `text` preserve TeX in place.
    for sec in blocks:
        for b in sec["blocks"]:
            b["tex"] = " ".join(b.pop("tex_list", []))
    out_path = os.path.join(HERE, "l05_dom_blocks.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(blocks, fh, ensure_ascii=False, indent=2)

    total = 0
    for sec in blocks:
        types = [b["type"] for b in sec["blocks"]]
        total += len(types)
        print(f"{sec['id']:<24} {len(types):>2}  {types}")
    print(f"TOTAL {total} cues across {len(blocks)} narrated sections -> {out_path}")


if __name__ == "__main__":
    main()
