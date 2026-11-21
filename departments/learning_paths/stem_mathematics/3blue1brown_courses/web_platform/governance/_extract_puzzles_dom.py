# -*- coding: utf-8 -*-
"""Authoritative LIVE DOM extraction for all 10 Puzzles lessons.

Uses narration_engine.js's exact selector + skip rules in headless Chrome
(channel=chrome, file://), preserving KaTeX TeX via <annotation> markers.
Writes governance/puzzles_dom_extract.json (one entry per lesson).
"""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
OUT = os.path.join(HERE, "puzzles_dom_extract.json")

EXTRACT_JS = r"""() => {
  const secEls = [...document.querySelectorAll('.article > section, article section')];
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
  const sections = [];
  for (const el of secEls) {
    if (el.getAttribute('data-no-narration') === 'true') continue;
    const nodes = [...el.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box')];
    const blocks = [];
    for (const node of nodes) {
      if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) continue;
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
      const tex_list = [...node.querySelectorAll('.katex annotation[encoding="application/x-tex"]')]
        .map(a => a.textContent.trim());
      if (text && text.length > 2) blocks.push({type: domType(node), text, tex_list});
    }
    if (blocks.length > 0) {
      const h2 = el.querySelector('h2');
      sections.push({id: el.id, title: h2 ? h2.innerText.trim() : (el.getAttribute('title') || ''), blocks});
    }
  }
  const eng = window.narrationEngine ? window.narrationEngine.sections.map(s => ({
    id: s.id, blockCount: s.blocks.length, cueCount: s.cues.length,
    types: s.blocks.map(b => domType(b.element))
  })) : [];
  const manifest = window.TEACHER_AUDIO_MANIFEST;
  return {
    sectionEls: secEls.map(s => ({id: s.id, noNarration: s.getAttribute('data-no-narration')})),
    sections, engine: eng,
    manifestPresent: !!manifest,
    manifestKeys: manifest ? Object.keys(manifest.sections) : [],
    engineHasStudioAudio: window.narrationEngine ? window.narrationEngine.hasStudioAudio : null,
  };
}"""


def main():
    result = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        for n in range(1, 11):
            nn = f"{n:02d}"
            page_uri = Path(os.path.join(
                WORKSPACE, "courses", "puzzles", f"lesson_{nn}.html")).as_uri()
            page = browser.new_page()
            page_errors, console_errors = [], []
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            page.on("console", lambda m: console_errors.append(m.text)
                    if m.type == "error" else None)
            page.goto(page_uri, wait_until="load")
            page.wait_for_function(
                "() => !!window.narrationEngine && !!window.narrationEngine.sections "
                "&& window.narrationEngine.sections.length > 0 && !!window.TEACHER_AUDIO_MANIFEST",
                timeout=30000)
            data = page.evaluate(EXTRACT_JS)
            data["page_errors"] = page_errors
            data["console_errors"] = console_errors
            result[f"lesson_{nn}"] = data
            page.close()
        browser.close()

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    for nn, d in result.items():
        total = sum(len(s["blocks"]) for s in d["sections"])
        print(f"=== {nn}: {len(d['sections'])} narrated sections, {total} cues, "
              f"engine={[ (e['id'], len(e['types'])) for e in d['engine'] ]}")
        for s in d["sections"]:
            print(f"   {s['id']:<20} {len(s['blocks']):>2} {[b['type'] for b in s['blocks']]}")
        print("   sectionEls:", [(e["id"], e["noNarration"]) for e in d["sectionEls"]])
        print("   page_errors:", d["page_errors"][:3], "console_errors:", len(d["console_errors"]))
    print("Saved ->", OUT)


if __name__ == "__main__":
    main()
