# -*- coding: utf-8 -*-
"""One-off: print all section elements (incl. sec-video-note) as seen by the browser."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
PAGE = os.path.join(WORKSPACE, "courses", "differential_equations", "lesson_06.html")

JS = r"""() => {
  const all = [...document.querySelectorAll('section, b1b-section')].map(s => ({
    tag: s.tagName.toLowerCase(), id: s.id,
    noNarration: s.getAttribute('data-no-narration'),
    isArticleChild: !!s.closest('.article, article')
  }));
  return all;
}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page()
    pg.goto(Path(PAGE).as_uri(), wait_until="load")
    pg.wait_for_function("() => !!window.narrationEngine && window.narrationEngine.sections.length > 0")
    for row in pg.evaluate(JS):
        print(row)
    b.close()
