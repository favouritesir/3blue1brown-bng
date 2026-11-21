# -*- coding: utf-8 -*-
"""Extract the authoritative LIVE narration-engine DOM blocks for all 10
Analysis lessons (headless Chrome, channel=chrome). Reads directly from
window.narrationEngine.sections (the exact engine the verifier inspects),
preserving KaTeX TeX via <annotation> markers. Writes
governance/analysis_dom/lesson_NN.json.
"""
import json
import os

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "analysis_dom")
os.makedirs(OUT_DIR, exist_ok=True)

EXTRACT_JS = r"""() => {
  const eng = window.narrationEngine;
  const typeOf = (el) => {
    if (!el) return 'p';
    if (el.matches && el.matches('figure.lesson-figure')) return 'figure';
    if (el.classList && el.classList.contains('chapter-quote')) return 'chapter-quote';
    if (el.classList && el.classList.contains('callout')) return 'callout';
    if (el.classList && el.classList.contains('code-showcase')) return 'code-showcase';
    if (el.classList && el.classList.contains('formula-box')) return 'formula-box';
    if (el.tagName === 'H2') return 'h2';
    if (el.tagName === 'H3') return 'h3';
    return 'p';
  };
  const sections = [];
  (eng && eng.sections || []).forEach(sec => {
    const cues = [];
    (sec.blocks || []).forEach((b, i) => {
      const el = b.element;
      const annotations = [...(el ? el.querySelectorAll('.katex annotation[encoding="application/x-tex"]') : [])]
        .map(a => a.textContent.trim());
      // raw innerText with KaTeX replaced by <annotation>tex</annotation> markers
      let raw = '';
      if (el) {
        const clone = el.cloneNode(true);
        clone.querySelectorAll('.katex').forEach(k => {
          const ann = k.querySelector('annotation[encoding="application/x-tex"]');
          const tex = ann ? ann.textContent.trim() : '';
          const marker = document.createElement('span');
          marker.textContent = '<annotation>' + tex + '</annotation>';
          k.replaceWith(marker);
        });
        raw = (clone.innerText || clone.textContent || '')
          .replace(/\u00a0/g, ' ').replace(/\n+/g, ' ').replace(/[ \t]+/g, ' ').trim();
      }
      cues.push({
        index: i,
        type: typeOf(el),
        text: b.text || '',
        annotations,
        raw
      });
    });
    sections.push({
      id: sec.id,
      title: sec.title || '',
      audio_file: sec.audioFile || '',
      cues
    });
  });
  return {
    hasStudioAudio: !!(eng && eng.hasStudioAudio),
    sections
  };
}"""


def main():
    grand_total = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        for n in range(1, 11):
            url = f"http://127.0.0.1:8085/courses/analysis/lesson_{n:02d}.html"
            page = browser.new_page()
            page.set_default_navigation_timeout(60000)
            page_errors = []
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            for attempt in range(3):
                try:
                    page.goto(url, wait_until="domcontentloaded")
                    break
                except Exception as exc:  # transient server hiccup
                    print(f"  lesson_{n:02d} goto attempt {attempt + 1} failed: {exc}")
                    if attempt == 2:
                        raise
            page.wait_for_function(
                "() => window.narrationEngine && window.narrationEngine.sections && "
                "window.narrationEngine.sections.length >= 1 && "
                "window.narrationEngine.sections.every(s => (s.cues || []).length > 0) && "
                "window.narrationEngine.hasStudioAudio === true",
                timeout=25000,
            )
            data = page.evaluate(EXTRACT_JS)
            page.close()

            out = {
                "lesson": f"lesson_{n:02d}",
                "hasStudioAudio": data["hasStudioAudio"],
                "sections": data["sections"],
                "page_errors": page_errors,
            }
            out_path = os.path.join(OUT_DIR, f"lesson_{n:02d}.json")
            with open(out_path, "w", encoding="utf-8") as fh:
                json.dump(out, fh, ensure_ascii=False, indent=2)

            total = sum(len(s["cues"]) for s in data["sections"])
            grand_total += total
            print(f"\n=== lesson_{n:02d}  cues={total}  sections={len(data['sections'])}  "
                  f"hasStudioAudio={data['hasStudioAudio']}  page_errors={len(page_errors)}")
            for s in data["sections"]:
                types = [c["type"] for c in s["cues"]]
                print(f"  {s['id']:<28} {len(types):>2}  {types}")
                print(f"      audio_file={s['audio_file']}")
        browser.close()
    print(f"\nGRAND TOTAL CUES = {grand_total}")


if __name__ == "__main__":
    main()
