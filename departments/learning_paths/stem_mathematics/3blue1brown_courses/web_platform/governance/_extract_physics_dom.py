# -*- coding: utf-8 -*-
"""
Authoritative DOM extraction for all 13 PHYSICS lesson pages via the exact
narration_engine.js selector, preserving KaTeX <annotation> TeX markers.

Headless Chrome (channel="chrome") against the local web root at 127.0.0.1:8085.
Writes governance/physicsNN_dom_blocks.json for NN = 01..13.
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
    if (!el) return 'unknown';
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

  // Also enumerate every <b1b-section> to confirm no-narration exclusions.
  const allSections = [...document.querySelectorAll(
    '.article > section, article section, b1b-section')].map(s => ({
      id: s.id || null,
      noNarration: s.getAttribute('data-no-narration') === 'true',
    }));

  return {
    sections,
    allSections,
    hasStudioAudio: !!ne.hasStudioAudio,
    manifest: window.TEACHER_AUDIO_MANIFEST || null,
    manifestScripts: [...document.querySelectorAll('script')]
      .map(s => s.src).filter(s => s.includes('manifest.js')),
  };
}"""


def extract(n):
    url = f"{BASE_URL}/courses/physics/lesson_{n:02d}.html?v=extract{n}"
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
        "manifestScripts": data["manifestScripts"],
        "allSections": data["allSections"],
        "sections": data["sections"],
    }
    out = os.path.join(GOV, f"physics{n:02d}_dom_blocks.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(snap, fh, ensure_ascii=False, indent=2)
    return out, snap


def main():
    grand = 0
    for n in range(1, 14):
        out, snap = extract(n)
        print("=" * 74)
        print(f"lesson_{n:02d} -> {os.path.basename(out)}")
        print(f"  sections={len(snap['sections'])} hasStudioAudio={snap['hasStudioAudio']}"
              f" pageerrors={len(snap['js_errors'])} console_errors={len(snap['console_errors'])}")
        total = 0
        for s in snap["sections"]:
            types = [b["type"] for b in s["blocks"]]
            total += len(types)
            tex = sum(len(b["tex"]) for b in s["blocks"])
            print(f"  {s['id']:<26} {len(types):>2} blocks  tex={tex}  {types}")
        grand += total
        print(f"  TOTAL cues: {total}")
        if snap["js_errors"]:
            print("  JS ERRORS:", snap["js_errors"][:3])
    print("=" * 74)
    print(f"GRAND TOTAL cues across 13 lessons: {grand}")


if __name__ == "__main__":
    main()
