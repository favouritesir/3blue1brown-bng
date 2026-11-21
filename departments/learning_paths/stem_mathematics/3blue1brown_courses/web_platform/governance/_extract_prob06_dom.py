# -*- coding: utf-8 -*-
"""Authoritative DOM extraction for Probability Lesson 06 via narration_engine selector."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

PAGE = Path(__file__).resolve().parents[1] / "courses" / "probability" / "lesson_06.html"
OUT = Path(__file__).resolve().parent / "prob06_dom_extract.json"

JS = r"""() => {
  const domType = (node) => {
    if (!node || !node.classList) return node ? node.tagName.toLowerCase() : '';
    if (node.classList.contains('chapter-quote')) return 'chapter-quote';
    if (node.classList.contains('callout')) {
      const v = [...node.classList].find(c => c.startsWith('callout-'));
      return v || 'callout';
    }
    if (node.matches && node.matches('figure.lesson-figure')) return 'figure';
    if (node.classList.contains('formula-box')) return 'formula-box';
    if (node.classList.contains('code-showcase')) return 'code-showcase';
    return node.tagName.toLowerCase();
  };
  const sectionEls = [...document.querySelectorAll('.article > section, article section')];
  const dom = [];
  for (const el of sectionEls) {
    const noNarr = el.getAttribute('data-no-narration') === 'true';
    const nodes = [...el.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box')];
    const blocks = [];
    for (const node of nodes) {
      if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) continue;
      const anns = [...node.querySelectorAll('annotation[encoding="application/x-tex"]')]
                     .map(a => a.textContent);
      blocks.push({type: domType(node), text: (node.innerText || '').trim(), tex: anns});
    }
    dom.push({id: el.id, noNarration: noNarr, blockCount: blocks.length, blocks});
  }
  const eng = window.narrationEngine;
  return {
    sectionEls: dom.map(s => ({id: s.id, noNarration: s.noNarration,
                               blockCount: s.blockCount,
                               types: s.blocks.map(b => b.type)})),
    domBlocks: dom,
    engine: (eng && eng.sections || []).map(s => ({
      id: s.id, blocks: (s.blocks||[]).length, cues: (s.cues||[]).length,
      audioFile: s.audioFile || null,
      types: (s.blocks||[]).map(b => domType(b.element)),
      texts: (s.blocks||[]).map(b => b.text)
    })),
    hasStudioAudio: !!(eng && eng.hasStudioAudio),
    manifestKeys: Object.keys((window.TEACHER_AUDIO_MANIFEST||{}).sections||{}),
    version: [...document.querySelectorAll('script')]
      .map(s => s.src).filter(s => s.includes('manifest.js'))
  };
}"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(PAGE.as_uri(), wait_until="load")
    page.wait_for_function(
        "() => !!window.narrationEngine && window.narrationEngine.sections.length > 0")
    data = page.evaluate(JS)
    browser.close()

data["page_errors"] = errs
OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps({"page_errors": errs, **data}, ensure_ascii=False, indent=2))
