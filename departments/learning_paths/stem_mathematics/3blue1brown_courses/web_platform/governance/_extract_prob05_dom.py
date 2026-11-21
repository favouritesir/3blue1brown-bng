# -*- coding: utf-8 -*-
"""Authoritative DOM extraction for Probability Lesson 05 via narration_engine selector."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

PAGE = Path(__file__).resolve().parents[1] / "courses" / "probability" / "lesson_05.html"

JS = r"""() => {
  const domType = (node) => {
    if (node.classList && node.classList.contains('chapter-quote')) return 'chapter-quote';
    if (node.classList && node.classList.contains('callout')) {
      const v = [...node.classList].find(c => c.startsWith('callout-'));
      return v || 'callout';
    }
    if (node.matches && node.matches('figure.lesson-figure')) return 'figure';
    if (node.classList && node.classList.contains('formula-box')) return 'formula-box';
    if (node.classList && node.classList.contains('code-showcase')) return 'code-showcase';
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
      blocks.push(domType(node));
    }
    dom.push({id: el.id, noNarration: noNarr, blockCount: blocks.length, types: blocks});
  }
  const eng = window.narrationEngine;
  return {
    sectionEls: dom,
    engine: (eng && eng.sections || []).map(s => ({
      id: s.id, blocks: (s.blocks||[]).length, cues: (s.cues||[]).length,
      audioFile: s.audioFile || null,
      types: (s.blocks||[]).map(b => domType(b.element))
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
    page.wait_for_function("() => !!window.narrationEngine && window.narrationEngine.sections.length > 0")
    data = page.evaluate(JS)
    browser.close()

print(json.dumps({"page_errors": errs, **data}, ensure_ascii=False, indent=2))
