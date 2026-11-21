# -*- coding: utf-8 -*-
"""
Extract the LIVE narrated DOM of all 8 Why-Pi lessons via headless Chrome
(channel='chrome'), using the exact narration_engine.parseContent() selector.

Output: governance/why_pi_dom_extract.json

For every narrated section (skipping data-no-narration="true") we record the
readable nodes in DOM order, with their cue type mapped exactly the way the
narration engine classifies them:

  h2 -> h2, h3 -> h3, .chapter-quote -> chapter-quote, .callout -> callout,
  figure.lesson-figure -> figure, .formula-box -> formula-box,
  .code-showcase -> code-showcase, plain p -> p

Quiz / media-tab nodes are NOT in the selector, so they never appear.
KaTeX annotation: for formula-box nodes we also capture the rendered .katex
text and the source `math` attribute from the host element.
"""
import json
import os
import sys
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # web_platform
BASE = 'http://localhost:8085'
OUT = os.path.join(ROOT, 'governance', 'why_pi_dom_extract.json')

READABLE_SELECTOR = ('h2, h3, p, .chapter-quote, .callout, '
                     'figure.lesson-figure, .code-showcase, .formula-box')

EXTRACT_JS = r"""() => {
  const SEL = 'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box';
  const sections = [];
  document.querySelectorAll('b1b-article section').forEach((secEl) => {
    if (secEl.getAttribute('data-no-narration') === 'true') return;
    const nodes = [];
    secEl.querySelectorAll(SEL).forEach((node) => {
      if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) return;
      let type;
      if (node.matches('h2')) type = 'h2';
      else if (node.matches('h3')) type = 'h3';
      else if (node.classList.contains('chapter-quote')) type = 'chapter-quote';
      else if (node.classList.contains('callout')) type = 'callout';
      else if (node.matches('figure.lesson-figure')) type = 'figure';
      else if (node.classList.contains('code-showcase')) type = 'code-showcase';
      else if (node.classList.contains('formula-box')) type = 'formula-box';
      else type = 'p';
      let text = (node.innerText || '').trim();
      // KaTeX annotation: capture rendered formula text + source math attr.
      let katex = null, math = null;
      if (type === 'formula-box') {
        const host = node.closest('b1b-formula');
        if (host) math = host.getAttribute('math');
        const k = node.querySelector('.katex');
        if (k) katex = (k.innerText || k.textContent || '').trim();
      }
      let caption = null;
      if (type === 'figure') {
        const cap = node.querySelector('figcaption');
        if (cap) caption = (cap.innerText || '').trim();
      }
      if (text.length > 2) nodes.push({type, text, katex, math, caption});
    });
    const h2 = secEl.querySelector('h2');
    sections.push({
      id: secEl.id || '',
      title: h2 ? h2.innerText.trim() : '',
      nodes
    });
  });
  return {
    sections,
    katexCount: document.querySelectorAll('.katex').length,
    manifestLoaded: !!(window.TEACHER_AUDIO_MANIFEST && window.TEACHER_AUDIO_MANIFEST.sections)
  };
}"""


def goto_ready(page, url):
    page.goto(url, wait_until='domcontentloaded', timeout=60000)
    page.wait_for_function(
        "() => !!customElements.get('b1b-hero-player') && "
        "!!document.querySelector('b1b-article section')",
        timeout=20000)
    page.wait_for_function(
        "() => document.querySelectorAll('.katex').length > 0",
        timeout=20000)


def main():
    out = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        for nn in ['01', '02', '03', '04', '05', '06', '07', '08']:
            page = ctx.new_page()
            errors = []
            page.on('console', lambda m: errors.append('[console] ' + m.text)
                    if m.type == 'error' else None)
            page.on('pageerror', lambda e: errors.append('[pageerror] ' + str(e)))
            goto_ready(page, BASE + '/courses/why_pi/lesson_%s.html' % nn)
            data = page.evaluate(EXTRACT_JS)
            data['errors'] = errors
            out['lesson_' + nn] = data
            total = sum(len(s['nodes']) for s in data['sections'])
            print('lesson_%s: %d sections, %d cues, katex=%d, errors=%d' % (
                nn, len(data['sections']), total, data['katexCount'], len(errors)))
            for s in data['sections']:
                types = [n['type'] for n in s['nodes']]
                print('   %-24s %2d  %s' % (s['id'], len(types), ', '.join(types)))
            page.close()
        browser.close()
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print('\nWrote', OUT)


if __name__ == '__main__':
    sys.exit(main())
