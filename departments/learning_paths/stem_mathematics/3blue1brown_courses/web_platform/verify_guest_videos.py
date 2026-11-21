# -*- coding: utf-8 -*-
"""
Verify the NEW guest_videos course in headless Chrome (channel=chrome).

Checks per lesson:
  * 0 console errors / page errors
  * every singleton component rendered exactly once; no double-render
  * exact component + script order identical to gold linear_algebra/lesson_01
  * DOM narration sections <-> manifest <-> narration engine 1:1 parity
  * data JSON fields (course_id, youtube/author, quizzes, figures)
  * non-narrated lab/quiz carry data-no-narration="true"
  * exact video-src path
  * quiz click interaction produces visible feedback
  * figure images load (no broken images)
  * manifest.js == manifest.json
"""
import asyncio
import json
import os
import sys

from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "file:///" + ROOT.replace("\\", "/").replace(" ", "%20")
CHANNEL = "chrome"

EXPECTED_SCRIPTS = [
    "../../assets/libs/katex/katex.min.js",
    "../../assets/libs/katex/auto-render.min.js",
    "../../assets/libs/katex-stub.js",
    "../../assets/js/lesson_components.js",
    "../../assets/js/lesson_components_extended.js",
    "../../assets/js/main.js",
    "../../assets/js/lesson.js",
    "../../assets/js/narration_engine.js",
]
SINGLETONS = [
    "b1b-search-overlay", "b1b-navbar", "b1b-hero-player", "b1b-narration-banner",
    "b1b-bookmarks", "b1b-toc-sidebar", "b1b-article", "b1b-watch-panel",
    "b1b-chapter-nav", "b1b-footer", "b1b-back-to-top",
]
AUTHORS = {
    "lesson_01": "Stephen Welch", "lesson_02": "Paul Dancstep",
    "lesson_03": "Vilas Winstein", "lesson_04": "Adithya Chakravarthy",
    "lesson_05": "Ben Syversen",
}
YT_IDS = {
    "lesson_01": "iv-5mZ_9CPY", "lesson_02": "_BrFKp-U8GI",
    "lesson_03": "itRV2jEtV8Q", "lesson_04": "4NlrfOl0l8U",
    "lesson_05": "M-MgQC6z3VU",
}


def jload(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


async def verify_lesson(page, n):
    lid = "lesson_%02d" % n
    url = "%s/courses/guest_videos/%s.html" % (BASE, lid)

    data = jload(os.path.join(ROOT, "data", "guest_videos", lid + ".json"))
    manifest = jload(os.path.join(ROOT, "assets", "audio", "guest_videos", lid, "manifest.json"))
    with open(os.path.join(ROOT, "assets", "audio", "guest_videos", lid, "manifest.js"),
              encoding="utf-8") as fh:
        js_text = fh.read().strip()
    js_obj = json.loads(js_text[len("window.TEACHER_AUDIO_MANIFEST = "):-1].strip())

    with open(os.path.join(ROOT, "courses", "guest_videos", lid + ".html"), encoding="utf-8") as fh:
        html_src = fh.read()
    script_srcs = [line.split('src="')[1].split('"')[0]
                   for line in html_src.splitlines() if "<script defer src=" in line]
    order_ok = script_srcs == EXPECTED_SCRIPTS
    # Cache-buster is bumped by each expressive-audio build (v=7 -> v=8, ...).
    import re as _re
    _mv = _re.search(r'assets/audio/guest_videos/%s/manifest\.js\?v=(\d+)' % lid, html_src)
    manifest_ref_ok = bool(_mv and int(_mv.group(1)) >= 8)
    video_src = ("../../media_vault/guest_videos/%s/experiments/"
                 "3b1b_guest_videos_%02d_full_dubbed.mp4" % (lid, n))
    video_ok = html_src.count(video_src) == 2  # hero + watch panel

    errs = []

    def on_console(m):
        if m.type == "error":
            errs.append("console: " + m.text[:200])

    page.on("console", on_console)
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)[:200]))
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(1200)

    dom = await page.evaluate("""() => {
      const nm = window.TEACHER_AUDIO_MANIFEST || {};
      const art = document.querySelectorAll('article.article').length;
      const allSec = [...document.querySelectorAll('article section')];
      const narrSec = allSec.filter(s => s.getAttribute('data-no-narration') !== 'true');
      const labSec = allSec.filter(s => s.getAttribute('data-no-narration') === 'true');
      const eng = window.narrationEngine || null;
      const engSecs = (eng && eng.sections) ? eng.sections.map(s => ({
        id: s.id,
        blocks: s.blocks.length,
        cues: s.cues.length,
        audioFile: s.audioFile || ''
      })) : [];
      const singletons = {};
      return {
        manifest: nm,
        articleCount: art,
        sectionIds: narrSec.map(s => s.id),
        sectionBlockTypes: narrSec.map(s => {
          const nodes = [...s.querySelectorAll('h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box')]
            .filter(nd => !(nd.tagName === 'P' && (nd.closest('.callout') || nd.closest('.chapter-quote'))));
          return nodes.map(nd => nd.tagName === 'H2' ? 'h2' : nd.tagName === 'H3' ? 'h3'
            : nd.tagName === 'P' ? 'p' : nd.classList.contains('chapter-quote') ? 'quote'
            : nd.classList.contains('callout') ? 'callout'
            : nd.matches('figure.lesson-figure') ? 'figure'
            : nd.classList.contains('formula-box') ? 'formula' : 'other');
        }),
        labSectionIds: labSec.map(s => s.id),
        engSecs,
        quizzes: document.querySelectorAll('b1b-quiz').length,
        quizBlocks: document.querySelectorAll('.quiz-block').length,
        quizNoNarration: [...document.querySelectorAll('b1b-quiz')]
          .every(q => q.getAttribute('data-no-narration') === 'true'),
        brokenImages: [...document.images].filter(i => !i.complete || i.naturalWidth === 0)
          .map(i => i.getAttribute('src')),
        singletonCounts: (function(){
          const o = {};
          return o;
        })()
      };
    }""")

    # Component-once checks (run separately so we can pass the tag list in)
    comp_counts = await page.evaluate(
        """(tags) => {
          const o = {};
          tags.forEach(t => o[t] = document.querySelectorAll(t).length);
          const figs = document.querySelectorAll('b1b-figure').length;
          const renderedFigs = document.querySelectorAll('b1b-figure figure.lesson-figure').length;
          const secs = document.querySelectorAll('b1b-section').length;
          const renderedSecs = document.querySelectorAll('b1b-section > section').length;
          const quizzes = document.querySelectorAll('b1b-quiz').length;
          const renderedQuizzes = document.querySelectorAll('b1b-quiz .quiz-block').length;
          return {o, figs, renderedFigs, secs, renderedSecs, quizzes, renderedQuizzes};
        }""", SINGLETONS)

    # Parity maths
    man_secs = manifest["sections"]
    man_ids = list(man_secs.keys())
    dom_ids = dom["sectionIds"]
    id_match = dom_ids == man_ids
    per_sec = {}
    parity = id_match
    for sid in man_ids:
        cues = man_secs[sid]["cues"]
        es = next((x for x in dom["engSecs"] if x["id"] == sid), None)
        dom_types = dom["sectionBlockTypes"][dom_ids.index(sid)] if sid in dom_ids else []
        man_types = [c["type"] for c in cues]
        ok = (es is not None and es["blocks"] == len(cues) == len(dom_types)
              and es["cues"] == len(cues) and man_types == dom_types
              and man_secs[sid]["audio_file"] in es["audioFile"])
        per_sec[sid] = {"manifest_cues": len(cues), "engine_blocks": es["blocks"] if es else -1,
                        "engine_cues": es["cues"] if es else -1, "dom_blocks": len(dom_types),
                        "types_match": man_types == dom_types, "ok": bool(ok)}
        parity = parity and bool(ok)

    # Quiz interaction: click first option, then the check button
    quiz_result = {"ok": False, "clicked": False, "feedback": ""}
    try:
        first_opt = page.locator("b1b-quiz .quiz-option").first
        await first_opt.click(timeout=5000)
        check = page.locator("b1b-quiz .quiz-check-btn").first
        await check.click(timeout=5000)
        fb = page.locator("b1b-quiz .quiz-feedback.show").first
        txt = (await fb.inner_text(timeout=5000)).strip()
        quiz_result = {"ok": bool(txt), "clicked": True, "feedback": txt[:120]}
    except Exception as exc:
        quiz_result = {"ok": False, "clicked": False, "error": str(exc)[:180]}

    data_ok = (
        data.get("course_id") == "guest_videos"
        and data.get("video_id") == YT_IDS[lid]
        and data.get("youtube_id") == YT_IDS[lid]
        and data.get("author") == AUTHORS[lid]
        and data.get("meta", {}).get("author") == AUTHORS[lid]
        and len(data.get("sections", [])) == len(dom["sectionIds"])
        and len(data.get("sections", [])) >= 4
        and len(data.get("quizzes", [])) >= 2
        and [s["id"] for s in data.get("sections", [])] == dom["sectionIds"]
        and all(len(s.get("figures", [])) >= 1 for s in data.get("sections", []))
        and data.get("oembed", {}).get("verified") is True
    )

    singletons_ok = all(v == 1 for v in comp_counts["o"].values())
    render_ok = (comp_counts["figs"] == comp_counts["renderedFigs"]
                 and comp_counts["secs"] == comp_counts["renderedSecs"]
                 and comp_counts["quizzes"] == comp_counts["renderedQuizzes"])

    checks = {
        "no_console_or_page_errors": len(errs) == 0,
        "component_order_like_gold": order_ok,
        "manifest_preload_ref": manifest_ref_ok,
        "video_src_exact_twice": video_ok,
        "all_singletons_once": singletons_ok,
        "no_double_render": render_ok,
        "id_match_dom_manifest": id_match,
        "narration_parity": parity,
        "manifest_js_equals_json": js_obj == manifest,
        "quizzes_present": dom["quizzes"] >= 2 and dom["quizzes"] == dom["quizBlocks"],
        "quizzes_no_narration": dom["quizNoNarration"],
        "lab_no_narration": len(dom["labSectionIds"]) == 1 and dom["labSectionIds"][0] == "sec-06-lab",
        "figures_load": len(dom["brokenImages"]) == 0,
        "quiz_click_works": quiz_result["ok"],
        "data_json_fields": data_ok,
        "one_article": dom["articleCount"] == 1,
    }
    report = {
        "lesson": lid, "url": url, "channel": CHANNEL + " (headless=True)",
        "checks": checks, "all_ok": all(checks.values()),
        "errors": errs, "singleton_counts": comp_counts["o"],
        "section_ids": dom_ids, "per_section_parity": per_sec,
        "quiz_click": quiz_result,
        "broken_images": dom["brokenImages"],
    }
    return report


async def verify_index(page):
    url = "%s/courses/guest_videos/index.html" % BASE
    errs = []

    def on_console(m):
        if m.type == "error":
            errs.append("console: " + m.text[:200])

    page.on("console", on_console)
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)[:200]))
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(600)
    links = await page.eval_on_selector_all(
        "a.chapter-row", "els => els.map(e => e.getAttribute('href'))")
    checks = {
        "no_errors": len(errs) == 0,
        "five_links": links == ["lesson_%02d.html" % i for i in range(1, 6)],
    }
    return {"index": True, "checks": checks, "all_ok": all(checks.values()),
            "errors": errs, "links": links}


async def main():
    all_reports = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel=CHANNEL, headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        try:
            all_reports.append(await verify_index(page))
        finally:
            await page.close()
        for n in range(1, 6):
            page = await browser.new_page(viewport={"width": 1280, "height": 900})
            try:
                all_reports.append(await verify_lesson(page, n))
            finally:
                await page.close()
        await browser.close()

    ok = all(r["all_ok"] for r in all_reports)
    out = {"channel": CHANNEL + " (headless=True)", "all_ok": ok, "reports": all_reports}
    out_path = os.path.join(ROOT, "governance", "_verify_guest_videos_result.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    # Human-readable summary
    for r in all_reports:
        label = r.get("lesson") or "index"
        failed = [k for k, v in r["checks"].items() if not v]
        print("%s: %s%s" % (label, "PASS" if r["all_ok"] else "FAIL",
                            ("  failing=" + ",".join(failed)) if failed else ""))
        if r["errors"]:
            print("   errors:", r["errors"][:4])
        if label != "index" and not r["all_ok"]:
            for sid, pp in r["per_section_parity"].items():
                if not pp["ok"]:
                    print("   parity", sid, pp)
    print("OVERALL:", "PASS" if ok else "FAIL")
    print("report:", out_path)
    sys.exit(0 if ok else 1)


asyncio.run(main())
