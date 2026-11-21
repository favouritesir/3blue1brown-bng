# -*- coding: utf-8 -*-
"""Headless-Chrome verification for the NEW number_theory course."""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8085/courses/number_theory/lesson_%s.html"

SINGLETONS = [
    "b1b-search-overlay", "b1b-navbar", "b1b-hero-player",
    "b1b-narration-banner", "b1b-bookmarks", "b1b-toc-sidebar",
    "b1b-article", "b1b-watch-panel", "b1b-chapter-nav",
    "b1b-footer", "b1b-back-to-top", "nt-math-lab",
]


def verify(page, nn):
    result = {"lesson": nn, "checks": {}, "errors": []}
    page.set_default_timeout(20000)

    # ---- 1. page errors -------------------------------------------------- #
    js_errors, console_errors = [], []
    page.on("pageerror", lambda e: js_errors.append(str(e)))
    page.on("console", lambda m: console_errors.append(m.text)
            if m.type == "error" else None)

    resp = page.goto(BASE % nn, wait_until="networkidle")
    result["checks"]["http_200"] = resp is not None and resp.status == 200
    page.wait_for_function(
        "() => window.narrationEngine && window.narrationEngine.sections.length > 0"
        " && !!window.TEACHER_AUDIO_MANIFEST",
        timeout=20000,
    )

    result["checks"]["no_page_errors"] = len(js_errors) == 0
    result["errors"].extend("pageerror: " + e for e in js_errors)
    # Media decode failures for placeholder dubbed video are not JS errors,
    # but report console errors for transparency.
    result["console_errors"] = console_errors

    # ---- 2. components rendered once ------------------------------------ #
    comp = page.evaluate("""() => {
      const singles = %s.map(t => [t, document.querySelectorAll(t).length]);
      const structural = {
        sections: document.querySelectorAll('article.article > b1b-section > section').length,
        sectionHosts: document.querySelectorAll('b1b-section').length,
        figureOk: [...document.querySelectorAll('b1b-figure')].every(f =>
          f.querySelectorAll('figure.lesson-figure').length === 1),
        figureCount: document.querySelectorAll('b1b-figure figure.lesson-figure').length,
        figureHosts: document.querySelectorAll('b1b-figure').length,
        quizOk: [...document.querySelectorAll('b1b-quiz')].every(q =>
          q.querySelectorAll('.quiz-block').length === 1),
        quizCount: document.querySelectorAll('b1b-quiz .quiz-block').length,
        quizHosts: document.querySelectorAll('b1b-quiz').length,
        calloutOk: [...document.querySelectorAll('b1b-callout')].every(c =>
          c.querySelectorAll('.callout').length === 1),
        formulaOk: [...document.querySelectorAll('b1b-formula')].every(f =>
          f.querySelectorAll('.formula-box').length === 1),
        quoteOk: [...document.querySelectorAll('b1b-quote')].every(q =>
          q.querySelectorAll('.chapter-quote').length === 1),
        bookmarks: document.querySelectorAll('.bookmark-chip').length,
        tocLinks: document.querySelectorAll('b1b-toc-sidebar a').length,
        duplicateIds: (() => {
          const ids = [...document.querySelectorAll('[id]')].map(e => e.id);
          return ids.filter((v, i) => ids.indexOf(v) !== i);
        })(),
        labNoNarration: document.querySelector('#sec-lab')?.getAttribute('data-no-narration'),
        videoSrc: document.querySelector('#mainVideo')?.getAttribute('src'),
      };
      return {singles, structural};
    }""" % repr(SINGLETONS).replace("'", '"'))

    counts = dict(comp["singles"])
    st = comp["structural"]
    result["component_counts"] = counts
    result["structural"] = st
    result["checks"]["singletons_once"] = all(v == 1 for v in counts.values())
    result["checks"]["sections_once"] = (
        st["sections"] == st["sectionHosts"] and st["sections"] >= 5
    )
    result["checks"]["nested_components_once"] = all([
        st["figureOk"], st["quizOk"], st["calloutOk"],
        st["formulaOk"], st["quoteOk"],
        st["figureCount"] == st["figureHosts"],
        st["quizCount"] == st["quizHosts"],
    ])
    result["checks"]["no_duplicate_ids"] = len(st["duplicateIds"]) == 0
    result["checks"]["lab_no_narration"] = st["labNoNarration"] == "true"
    result["checks"]["video_src_ok"] = bool(
        st["videoSrc"] and
        st["videoSrc"].endswith("3b1b_number_theory_%s_full_dubbed.mp4" % nn)
    )
    result["checks"]["bookmarks_and_toc"] = st["bookmarks"] >= 5 and st["tocLinks"] >= 5

    # ---- 3. quiz click --------------------------------------------------- #
    q = page.evaluate("""() => {
      const host = document.querySelector('b1b-quiz');
      if (!host) return {ok:false, reason:'no quiz'};
      const opt = host.querySelector('.quiz-option');
      const btn = host.querySelector('.quiz-check-btn');
      const before = btn.disabled;
      opt.click();
      const afterSelect = btn.disabled;
      btn.click();
      const fb = host.querySelector('.quiz-feedback');
      return {
        ok: true,
        before, afterSelect,
        feedbackShown: fb.classList.contains('show'),
        feedbackText: fb.textContent.trim().slice(0, 90),
        lockedCount: host.querySelectorAll('.quiz-option.locked').length,
      };
    }""")
    result["quiz"] = q
    result["checks"]["quiz_click"] = bool(
        q.get("ok") and q.get("before") is True and q.get("afterSelect") is False
        and q.get("feedbackShown") and q.get("lockedCount", 0) >= 1
        and len(q.get("feedbackText", "")) > 3
    )

    # ---- 4. DOM <-> manifest parity ------------------------------------- #
    parity = page.evaluate("""() => {
      const typeOf = (el) => {
        if (el.tagName === 'H2') return 'h2';
        if (el.tagName === 'H3') return 'h3';
        if (el.tagName === 'P') return 'p';
        if (el.classList.contains('chapter-quote')) return 'chapter-quote';
        if (el.classList.contains('callout')) return 'callout';
        if (el.tagName === 'FIGURE') return 'figure';
        if (el.classList.contains('formula-box')) return 'formula-box';
        return el.tagName.toLowerCase();
      };
      const eng = window.narrationEngine;
      const man = window.TEACHER_AUDIO_MANIFEST;
      const dom = eng.sections.map(s => ({
        id: s.id,
        types: s.blocks.map(b => typeOf(b.element)),
        cuesLoaded: s.cues.length,
        audioFile: s.audioFile || null,
      }));
      const manifest = Object.keys(man.sections).map(id => ({
        id,
        types: man.sections[id].cues.map(c => c.type),
        cues: man.sections[id].cues.length,
        audioFile: man.sections[id].audio_file,
      }));
      const labLeaked = dom.some(s => s.id === 'sec-lab') ||
                        Object.keys(man.sections).includes('sec-lab');
      return {
        dom, manifest, labLeaked,
        hasStudioAudio: eng.hasStudioAudio,
        manifestCourse: man.course,
        manifestLesson: man.lesson,
      };
    }""")
    result["parity"] = parity
    dom_map = {s["id"]: s for s in parity["dom"]}
    man_map = {s["id"]: s for s in parity["manifest"]}
    same_ids = set(dom_map) == set(man_map)
    same_types = same_ids and all(
        dom_map[i]["types"] == man_map[i]["types"] for i in dom_map
    )
    same_cues = same_ids and all(
        dom_map[i]["cuesLoaded"] == man_map[i]["cues"] for i in dom_map
    )
    audio_ok = same_ids and all(
        dom_map[i]["audioFile"] and
        dom_map[i]["audioFile"].endswith(man_map[i]["audioFile"]) for i in dom_map
    )
    result["checks"]["dom_manifest_ids"] = same_ids
    result["checks"]["dom_manifest_cue_types"] = same_types
    result["checks"]["dom_manifest_cue_counts"] = same_cues
    result["checks"]["manifest_audio_binding"] = audio_ok
    result["checks"]["manifest_metadata"] = (
        parity["manifestCourse"] == "number_theory" and
        parity["manifestLesson"] == "lesson_" + nn
    )
    result["checks"]["lab_excluded_from_manifest"] = not parity["labLeaked"]
    # "Page errors" are uncaught JS exceptions. Console messages emitted by the
    # browser itself about iframe permission policy (e.g. compute-pressure from
    # the YouTube embed) are not page errors and are only reported, not failed.
    benign_console = [
        m for m in console_errors
        if "Permissions policy violation" in m or "compute-pressure" in m
    ]
    real_console = [m for m in console_errors if m not in benign_console]
    result["benign_console"] = benign_console
    result["checks"]["no_page_errors"] = (
        result["checks"]["no_page_errors"] and len(real_console) == 0
    )
    result["all_passed"] = all(result["checks"].values())
    return result


def main():
    all_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        for nn in ("01", "02", "03"):
            r = verify(page, nn)
            all_results.append(r)
            print("=" * 70)
            print("lesson_%s : %s" % (nn, "PASS" if r["all_passed"] else "FAIL"))
            for k, v in r["checks"].items():
                print("  %-32s %s" % (k, "OK" if v else "FAIL"))
            if r["errors"]:
                print("  ERRORS:", r["errors"][:5])
            if r["console_errors"]:
                print("  CONSOLE:", r["console_errors"][:5])
            failed = [k for k, v in r["checks"].items() if not v]
            if failed:
                print("  FAILED CHECKS:", failed)
                if "parity" in r:
                    print("  DOM:", r["parity"]["dom"])
                    print("  MAN:", r["parity"]["manifest"])
        browser.close()
    print("=" * 70)
    print("OVERALL:", "ALL PASS" if all(r["all_passed"] for r in all_results) else "FAILURES")
    return 0 if all(r["all_passed"] for r in all_results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
