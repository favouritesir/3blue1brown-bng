# -*- coding: utf-8 -*-
"""
Extract the LIVE DOM blocks of differential_equations/lesson_04.html using
narration_engine.js's exact selector + skip rules, and the narrationEngine's
own block-type mapping. This MUST be run before writing expressive scripts so
section IDs / block types / counts come from the DOM, not from prose.

Writes governance/de04_dom_blocks.json (one-off extraction aid; the re-runnable
builder embeds its own script data and validates DOM parity at verify time).
"""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
PAGE_PATH = os.path.join(WORKSPACE, "courses", "differential_equations", "lesson_04.html")

EXTRACT_JS = r"""() => {
  const ne = window.narrationEngine;

  // Exact type mapping used by narration_engine.parseContent()/builders.
  function domType(node) {
    if (node.classList.contains('chapter-quote')) return 'chapter-quote';
    if (node.classList.contains('callout')) {
      const v = [...node.classList].find(c => c.startsWith('callout-'));
      return v || 'callout';
    }
    if (node.matches('figure.lesson-figure')) return 'figure';
    if (node.classList.contains('formula-box')) return 'formula-box';
    if (node.classList.contains('code-showcase')) return 'code-showcase';
    return node.tagName.toLowerCase();
  }

  const sectionEls = [...document.querySelectorAll('.article > section, article section')];
  const dom = [];
  for (const el of sectionEls) {
    const noNarration = el.getAttribute('data-no-narration') === 'true';
    const nodes = [...el.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box')];
    const blocks = [];
    for (const node of nodes) {
      if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) continue;
      const anns = [...node.querySelectorAll('annotation[encoding="application/x-tex"]')]
                     .map(a => a.textContent);
      blocks.push({type: domType(node), tex: anns});
    }
    dom.push({id: el.id, noNarration, types: blocks.map(b => b.type),
              tex: blocks.filter(b => b.type === 'formula-box').map(b => b.tex)});
  }

  const engine = ne ? ne.sections.map(s => ({
    id: s.id, blockCount: s.blocks.length, cueCount: s.cues.length,
    audioFile: s.audioFile, types: s.blocks.map(b => domType(b.element))
  })) : null;

  return {
    dom,
    engine,
    hasStudioAudio: !!(ne && ne.hasStudioAudio),
    manifestPresent: !!window.TEACHER_AUDIO_MANIFEST,
  };
}"""


def main():
    page_uri = Path(PAGE_PATH).as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page()
        page.goto(page_uri, wait_until="load")
        page.wait_for_function(
            "() => !!window.narrationEngine && !!window.narrationEngine.sections "
            "&& window.narrationEngine.sections.length > 0")
        data = page.evaluate(EXTRACT_JS)
        browser.close()

    out_path = os.path.join(HERE, "de04_dom_blocks.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)

    narrated = [s for s in data["dom"] if not s["noNarration"]]
    total = 0
    print(f"{'section id':<32} {'count':>5}  types")
    for s in narrated:
        total += len(s["types"])
        print(f"{s['id']:<32} {len(s['types']):>5}  {s['types']}")
    print(f"NARRATED total = {total} cues across {len(narrated)} sections")
    print("NON-NARRATED (data-no-narration=true):",
          [s["id"] for s in data["dom"] if s["noNarration"]])
    print("ENGINE sections:")
    for s in data["engine"] or []:
        print(f"  {s['id']:<32} blocks={s['blockCount']} cues={s['cueCount']} "
              f"audio={s['audioFile']} types={s['types']}")
    print(f"hasStudioAudio={data['hasStudioAudio']} manifestPresent={data['manifestPresent']}")
    print("Wrote", out_path)


if __name__ == "__main__":
    main()
