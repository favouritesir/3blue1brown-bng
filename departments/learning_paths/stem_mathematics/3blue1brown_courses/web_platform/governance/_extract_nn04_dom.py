# -*- coding: utf-8 -*-
"""One-off: extract the LIVE narrated DOM of neural_networks/lesson_04.html
using the narration engine's exact selector, including KaTeX <annotation>
text, callout variants and figure captions. Never guess section IDs/counts.

TeX `<annotation>` nodes are collected FIRST, so we prove the DOM was read with
annotation support. Callout variants are recorded verbatim (callout-purple etc.)
AND normalised to the DOM's `.callout` base class.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
WP = HERE.parent
PAGE = WP / "courses" / "neural_networks" / "lesson_04.html"
OUT = HERE / "_nn04_dom_extract.json"

EXTRACT_JS = r"""() => {
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
  // Manifest-style normalisation: callout-purple/blue/gold -> DOM .callout
  function normType(t) {
    return (typeof t === 'string' && t.indexOf('callout-') === 0) ? 'callout' : t;
  }
  const sectionEls = [...document.querySelectorAll('.article > section, article section')];
  const dom = [];
  for (const el of sectionEls) {
    if (el.getAttribute('data-no-narration') === 'true') continue;
    const nodes = [...el.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box')];
    const blocks = [];
    for (const node of nodes) {
      if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) continue;
      // TeX <annotation> FIRST
      const anns = [...node.querySelectorAll('annotation[encoding="application/x-tex"]')]
                     .map(a => a.textContent);
      const t = domType(node);
      blocks.push({
        type: t,
        normType: normType(t),
        calloutClasses: node.classList.contains('callout')
          ? [...node.classList].filter(c => c.startsWith('callout-')) : [],
        tex: anns,
        text: (node.innerText || '').trim().slice(0, 800)
      });
    }
    dom.push({id: el.id, title: (el.querySelector('h2')||{}).innerText||null, blocks});
  }

  const eng = window.narrationEngine;
  const engine = (eng ? eng.sections : []).map(s => ({
    id: s.id,
    blockCount: s.blocks.length,
    cueCount: s.cues.length,
    audioFile: s.audioFile || null,
    types: s.blocks.map(b => normType(domType(b.element))),
    rawTypes: s.blocks.map(b => domType(b.element))
  }));
  return {
    hasStudioAudio: !!(eng && eng.hasStudioAudio),
    manifestPresent: !!window.TEACHER_AUDIO_MANIFEST,
    sectionEls: sectionEls.map(s => ({id: s.id, noNarration: s.getAttribute('data-no-narration')})),
    dom, engine
  };
}"""

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page()
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.goto(PAGE.as_uri(), wait_until="load")
        page.wait_for_function(
            "() => !!window.narrationEngine && !!window.narrationEngine.sections "
            "&& window.narrationEngine.sections.length > 0", timeout=25000)
        data = page.evaluate(EXTRACT_JS)
        browser.close()
    data["page_errors"] = errs
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("page_errors:", errs)
    print("hasStudioAudio:", data["hasStudioAudio"], "manifestPresent:", data["manifestPresent"])
    print("\nALL <section> elements:")
    for s in data["sectionEls"]:
        print("  ", s)
    print("\nNARRATED DOM SECTIONS (exact selector):")
    for s in data["dom"]:
        types = [b["type"] for b in s["blocks"]]
        norms = [b["normType"] for b in s["blocks"]]
        tex = sum(len(b["tex"]) for b in s["blocks"])
        print(f"  {s['id']}  ({len(types)} blocks, {tex} tex)  raw={types}")
        print(f"      norm={norms}")
    print("\nENGINE SECTIONS:")
    for s in data["engine"]:
        print(f"  {s['id']}  blocks={s['blockCount']} cues={s['cueCount']} "
              f"audio={s['audioFile']}  types={s['types']}")
    print(f"\nSaved full extraction -> {OUT}")

if __name__ == "__main__":
    main()
