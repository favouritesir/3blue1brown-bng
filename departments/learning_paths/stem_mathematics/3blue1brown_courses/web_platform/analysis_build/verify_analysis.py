# -*- coding: utf-8 -*-
"""Headless Chrome (channel='chrome') verification for all 10 analysis lessons.

Checks per lesson:
  1. zero page errors and zero console/network errors
  2. every component rendered exactly once (no duplicate wrappers)
  3. each quiz: correct + wrong click produces feedback
  4. full DOM <-> manifest parity (section IDs 1:1, cue types/order 1:1)
  5. manifest.js == manifest.json; data JSON valid with course_id='analysis'
  6. video-src / narrated ids / index links
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BASE = "http://127.0.0.1:8085"
SLUGS = ["zeta", "print-gallery", "fourier-transforms", "uncertainty-principle",
         "fourier-series", "borwein", "convolutions", "winding-numbers",
         "inventing-math", "music-and-measure-theory"]

DOM_JS = r"""() => {
  const secs = Array.from(document.querySelectorAll('article.article section'));
  const seqFor = (sec) => Array.from(sec.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box'))
    .filter(n => !(n.tagName === 'P' && (n.closest('.callout') || n.closest('.chapter-quote'))))
    .map(n => {
      if (n.matches('h2')) return 'h2';
      if (n.classList.contains('chapter-quote')) return 'chapter-quote';
      if (n.classList.contains('callout')) return 'callout';
      if (n.matches('figure.lesson-figure')) return 'figure';
      if (n.classList.contains('formula-box')) return 'formula-box';
      return n.tagName.toLowerCase();
    });
  const count = (sel) => document.querySelectorAll(sel).length;
  return {
    sections: secs.map(s => ({id: s.id, seq: seqFor(s)})),
    counts: {
      article: count('article.article'),
      b1bArticle: count('b1b-article'),
      section: count('article.article section'),
      b1bSection: count('b1b-section'),
      quizBlock: count('b1b-quiz .quiz-block'),
      b1bQuiz: count('b1b-quiz'),
      callout: count('b1b-callout .callout'),
      b1bCallout: count('b1b-callout'),
      figure: count('b1b-figure figure.lesson-figure'),
      b1bFigure: count('b1b-figure'),
      formula: count('b1b-formula .formula-box'),
      b1bFormula: count('b1b-formula'),
      quote: count('b1b-quote .chapter-quote'),
      b1bQuote: count('b1b-quote'),
      toc: count('b1b-toc-sidebar'),
      navbar: count('b1b-navbar'),
      hero: count('b1b-hero-player'),
      watch: count('b1b-watch-panel'),
      footer: count('b1b-footer'),
    },
    engine: window.narrationEngine ? {
      present: true,
      sections: window.narrationEngine.sections.length,
      ids: window.narrationEngine.sections.map(s => s.id),
      cueCounts: window.narrationEngine.sections.map(s => s.cues.length),
      blockCounts: window.narrationEngine.sections.map(s => s.blocks.length),
    } : {present: false},
    manifestIds: Object.keys((window.TEACHER_AUDIO_MANIFEST || {}).sections || {}),
    manifestSeq: Object.fromEntries(Object.entries((window.TEACHER_AUDIO_MANIFEST || {}).sections || {})
      .map(([k, v]) => [k, v.cues.map(c => c.type)])),
    manifestJson: !!window.TEACHER_AUDIO_MANIFEST,
    videoSrc: document.querySelector('b1b-hero-player')?.getAttribute('video-src'),
    watchSrc: document.querySelector('b1b-watch-panel')?.getAttribute('video-src'),
  };
}"""


def check_quizzes(page, report):
    quizzes = page.locator("b1b-quiz")
    n = quizzes.count()
    results = []
    for i in range(n):
        q = quizzes.nth(i)
        block = q.locator(".quiz-block")
        correct = int(block.get_attribute("data-correct"))
        # correct path
        q.locator(f'.quiz-option[data-idx="{correct}"]').click()
        q.locator(".quiz-check-btn").click()
        fb = q.locator(".quiz-feedback.show.correct-fb")
        ok_correct = fb.count() == 1 and "✅" in (fb.inner_text() or "")
        # wrong path on a freshly rendered instance (options lock after checking)
        page.reload(wait_until="domcontentloaded")
        page.wait_for_selector("b1b-quiz .quiz-block", timeout=10000)
        fresh = page.locator("b1b-quiz").nth(i)
        wrong = (correct + 1) % fresh.locator(".quiz-option").count()
        fresh.locator(f'.quiz-option[data-idx="{wrong}"]').click()
        fresh.locator(".quiz-check-btn").click()
        fbw = fresh.locator(".quiz-feedback.show.wrong-fb")
        ok_wrong = fbw.count() == 1 and "❌" in (fbw.inner_text() or "")
        results.append({"i": i, "correct": ok_correct, "wrong": ok_wrong})
    report["quiz_clicks"] = results


def verify_lesson(pw, nn):
    rep = {"lesson": nn, "slug": SLUGS[nn - 1]}
    browser = pw.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page_errors, console_errors, bad_responses = [], [], []
    page.on("pageerror", lambda e: page_errors.append(str(e)))
    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    page.on("response", lambda r: bad_responses.append(f"{r.status} {r.url}")
            if r.status >= 400 else None)

    url = f"{BASE}/courses/analysis/lesson_{nn:02d}.html"
    resp = page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("article.article section", state="attached", timeout=10000)
    page.wait_for_selector("b1b-quiz .quiz-block", timeout=10000)
    page.wait_for_function(
        "() => window.narrationEngine && window.narrationEngine.sections && "
        "window.narrationEngine.sections.length > 0", timeout=10000)
    page.wait_for_function(
        "() => Array.from(document.querySelectorAll('.formula-box')).every("
        "e => e.querySelector('.katex') || e.textContent.trim().length < 4)", timeout=10000)

    dom = page.evaluate(DOM_JS)
    rep["http"] = resp.status if resp else 0

    # --- data JSON ---
    data = json.loads((ROOT / f"data/analysis/lesson_{nn:02d}.json").read_text(encoding="utf-8"))
    man = json.loads((ROOT / f"assets/audio/analysis/lesson_{nn:02d}/manifest.json").read_text(encoding="utf-8"))
    rep["data"] = {
        "course_id": data.get("course_id"),
        "official": data.get("official_url") == f"https://www.3blue1brown.com/lessons/{SLUGS[nn-1]}",
        "quizzes": len(data.get("quizzes", [])),
    }

    # --- parity ---
    sec_ids = [s["id"] for s in dom["sections"]]
    mids = dom["manifestIds"]
    rep["parity"] = {
        "dom_sections": len(sec_ids),
        "manifest_keys": len(mids),
        "ids_1to1": sec_ids == mids,
        "cues_1to1": all(dom["manifestSeq"].get(s["id"]) == s["seq"] for s in dom["sections"]),
        "engine_ids_match": dom["engine"].get("ids") == sec_ids,
        "engine_cues_nonzero": all(c > 0 for c in dom["engine"].get("cueCounts", [])),
        "engine_block_cue_equal": all(
            b == c for b, c in zip(dom["engine"].get("blockCounts", []),
                                   dom["engine"].get("cueCounts", []))),
        "json_js_same": man == page.evaluate(
            "() => JSON.parse(JSON.stringify(window.TEACHER_AUDIO_MANIFEST))"),
    }

    # --- components once ---
    c = dom["counts"]
    once_pairs = {
        "article": c["article"] == 1,
        "b1bArticle": c["b1bArticle"] == 1,
        "section": c["section"] == len(sec_ids),
        "quiz": c["b1bQuiz"] == c["quizBlock"] == 2,
        "callout": c["b1bCallout"] == c["callout"] > 0,
        "figure": c["b1bFigure"] == c["figure"] > 0,
        "formula": c["b1bFormula"] == c["formula"] > 0,
        "quote": c["b1bQuote"] == c["quote"] == 1,
        "toc/navbar/hero/watch/footer": all(
            c[k] == 1 for k in ("toc", "navbar", "hero", "watch", "footer")),
    }
    rep["components_once"] = once_pairs

    expected = (f"../../media_vault/analysis/lesson_{nn:02d}/experiments/"
                f"3b1b_analysis_{nn:02d}_full_dubbed.mp4")
    rep["video_src_ok"] = dom["videoSrc"] == expected == dom["watchSrc"]

    check_quizzes(page, rep)

    rep["errors"] = {
        "page": page_errors,
        "console": console_errors,
        "bad_responses": bad_responses,
    }
    browser.close()
    rep["ok"] = (rep["http"] == 200 and rep["data"]["course_id"] == "analysis" and
                 rep["data"]["official"] and rep["data"]["quizzes"] == 2 and
                 all(rep["parity"].values()) and all(rep["components_once"].values()) and
                 rep["video_src_ok"] and
                 all(x["correct"] and x["wrong"] for x in rep["quiz_clicks"]) and
                 not page_errors and not console_errors and not bad_responses)
    return rep


def main():
    reports = []
    with sync_playwright() as pw:
        for nn in range(1, 11):
            try:
                r = verify_lesson(pw, nn)
            except Exception as exc:
                r = {"lesson": nn, "ok": False, "exception": repr(exc)}
            reports.append(r)
            print(f"L{nn:02d} {'OK' if r.get('ok') else 'FAIL'} "
                  f"(pages={len(r.get('errors',{}).get('page',[]))} "
                  f"console={len(r.get('errors',{}).get('console',[]))} "
                  f"http404={len(r.get('errors',{}).get('bad_responses',[]))})")
            if not r.get("ok"):
                print(json.dumps(r, ensure_ascii=False, indent=2)[:4000])

    # index page verification
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True)
        pg = b.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        r = pg.goto(f"{BASE}/courses/analysis/index.html", wait_until="domcontentloaded")
        rows = pg.locator("a.chapter-row").count()
        hrefs = pg.eval_on_selector_all("a.chapter-row", "els => els.map(e => e.getAttribute('href'))")
        b.close()
    index_ok = r.status == 200 and rows == 10 and not errs and all(
        hrefs[i] == f"lesson_{i+1:02d}.html" for i in range(10))
    print(f"INDEX {'OK' if index_ok else 'FAIL'} rows={rows} errs={errs}")

    out = ROOT / "analysis_build/verify_result.json"
    out.write_text(json.dumps({
        "browser": "chrome (headless=True, channel=chrome)",
        "lessons_ok": sum(1 for r in reports if r.get("ok")),
        "lessons_total": 10,
        "index_ok": index_ok,
        "reports": reports,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out)
    return 0 if all(r.get("ok") for r in reports) and index_ok else 1


if __name__ == "__main__":
    sys.exit(main())
