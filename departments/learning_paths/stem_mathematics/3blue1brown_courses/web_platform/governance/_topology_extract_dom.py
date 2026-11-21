# -*- coding: utf-8 -*-
"""
Extract the LIVE DOM blocks of the topology lesson pages using the exact
narration_engine.js selector, preserving KaTeX <annotation> TeX markers.

Headless Chrome (channel="chrome") against the local web root at 127.0.0.1:8085.

Writes governance/topology0N_dom_blocks.json for N = 1..3.
"""
import os
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

GOV = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(GOV)
BASE_URL = "http://127.0.0.1:8085"

EXTRACT_JS = r"""() => {
  const ne = window.narrationEngine;
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
  // Render a block's text with KaTeX replaced by <annotation>...</annotation>.
  const annotatedText = (node) => {
    const clone = node.cloneNode(true);
    clone.querySelectorAll('.katex').forEach(k => {
      const ann = k.querySelector('annotation[encoding="application/x-tex"]');
      const raw = ann ? ann.textContent : (k.textContent || '');
      const marker = document.createTextNode('<annotation>' + raw + '</annotation>');
      if (k.parentNode) k.parentNode.replaceChild(marker, k);
    });
    return (clone.innerText || clone.textContent || '').replace(/\s+/g, ' ').trim();
  };

  const sections = [];
  for (const sec of (ne.sections || [])) {
    const blocks = [];
    for (const b of (sec.blocks || [])) {
      const node = b.element;
      const anns = [...node.querySelectorAll('annotation[encoding="application/x-tex"]')]
                     .map(a => a.textContent);
      blocks.push({
        type: typeOf(node),
        text: annotatedText(node),
        engine_text: b.text || '',
        tex: anns,
      });
    }
    sections.push({
      id: sec.id,
      title: sec.title,
      blocks: blocks,
      audioFile: sec.audioFile || null,
    });
  }
  return {
    sections,
    hasStudioAudio: !!ne.hasStudioAudio,
    manifest: window.TEACHER_AUDIO_MANIFEST || null,
  };
}"""


def extract(n):
    url = f"{BASE_URL}/courses/topology/lesson_{n:02d}.html?v=extract{n}"
    js_errors, console_errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page()
        page.on("pageerror", lambda e: js_errors.append(str(e)))
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.goto(url, wait_until="load")
        page.wait_for_function(
            "() => !!window.narrationEngine && !!window.narrationEngine.sections "
            "&& window.narrationEngine.sections.length > 0",
            timeout=30000,
        )
        data = page.evaluate(EXTRACT_JS)
        browser.close()

    snap = {
        "lesson": f"lesson_{n:02d}",
        "source_url": url,
        "js_errors": js_errors,
        "console_errors": console_errors,
        "hasStudioAudio": data["hasStudioAudio"],
        "sections": data["sections"],
    }
    out = os.path.join(GOV, f"topology{n:02d}_dom_blocks.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(snap, fh, ensure_ascii=False, indent=2)
    return out, snap


def main():
    for n in (1, 2, 3):
        out, snap = extract(n)
        print("=" * 70)
        print(f"lesson_{n:02d} -> {out}")
        print(f"  sections: {len(snap['sections'])}, "
              f"hasStudioAudio={snap['hasStudioAudio']}, "
              f"pageerrors={len(snap['js_errors'])}, "
              f"console_errors={len(snap['console_errors'])}")
        total = 0
        for s in snap["sections"]:
            types = [b["type"] for b in s["blocks"]]
            total += len(types)
            tex = sum(len(b["tex"]) for b in s["blocks"])
            print(f"  {s['id']:<22} {len(types):>2} blocks  tex={tex}  {types}")
        print(f"  TOTAL blocks: {total}")


if __name__ == "__main__":
    main()
