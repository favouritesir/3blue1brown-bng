# -*- coding: utf-8 -*-
"""Authoritative DOM extraction for Lockdown Math Lesson 04 via the
narration_engine.js selector — exact section IDs / block types / counts."""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
URL = Path(os.path.join(WORKSPACE, "courses", "lockdown_math", "lesson_04.html")).as_uri()
OUT = os.path.join(HERE, "_lock04_dom_extract.json")

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
      blocks.push({type: domType(node), text: (node.innerText || '').trim()});
    }
    sections.push({id: el.id, title: (el.querySelector('h2') ? el.querySelector('h2').innerText.trim() : ''), blocks});
  }
  const engine = window.narrationEngine ? window.narrationEngine.sections.map(s => ({
    id: s.id,
    blockCount: s.blocks.length,
    types: s.blocks.map(b => {
      const el = b.element;
      if (el.tagName === 'H2') return 'h2';
      if (el.tagName === 'H3') return 'h3';
      if (el.classList.contains('chapter-quote')) return 'chapter-quote';
      if (el.classList.contains('callout')) return 'callout';
      if (el.matches('figure.lesson-figure')) return 'figure';
      if (el.classList.contains('formula-box')) return 'formula-box';
      if (el.classList.contains('code-showcase')) return 'code-showcase';
      return 'p';
    }),
  })) : [];
  return {
    sectionEls: secEls.map(s => ({id: s.id, noNarration: s.getAttribute('data-no-narration')})),
    sections, engine,
    manifestPresent: !!window.TEACHER_AUDIO_MANIFEST,
    manifestKeys: window.TEACHER_AUDIO_MANIFEST ? Object.keys(window.TEACHER_AUDIO_MANIFEST.sections) : [],
  };
}"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page()
        page_errors, console_errors = [], []
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.goto(URL, wait_until="load")
        page.wait_for_function(
            "() => !!window.narrationEngine && !!window.narrationEngine.sections "
            "&& window.narrationEngine.sections.length > 0 && !!window.TEACHER_AUDIO_MANIFEST")
        data = page.evaluate(EXTRACT_JS)
        browser.close()
    data["page_errors"] = page_errors
    data["console_errors"] = console_errors
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    print("Narrated DOM sections (narration_engine selector):", len(data["sections"]))
    for s in data["sections"]:
        print("  ", s["id"], "title=", s["title"])
        print("       types=", [b["type"] for b in s["blocks"]], "count=", len(s["blocks"]))
    print("Engine sections:", [(e["id"], e["blockCount"], e["types"]) for e in data["engine"]])
    print("Manifest keys:", data["manifestKeys"])
    print("Section elements (incl. no-narration):", [(e["id"], e["noNarration"]) for e in data["sectionEls"]])
    print("page_errors:", page_errors)
    print("console_errors:", console_errors)
    print("Saved ->", OUT)


if __name__ == "__main__":
    main()
