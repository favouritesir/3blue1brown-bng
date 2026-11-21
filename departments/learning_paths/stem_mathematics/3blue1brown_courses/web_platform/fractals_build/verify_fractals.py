# -*- coding: utf-8 -*-
"""Headless-Chrome verification for the 4 new fractals lesson pages."""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8085/courses/fractals/lesson_{}.html"

# expected narratable block counts come from the manifest itself; parity is
# computed live from narrationEngine DOM parse vs preloaded manifest.
EXPECTED_QUIZZES = 3
EXPECTED_COMPONENTS = [
    ("b1b-search-overlay", 1), ("b1b-navbar", 1), (".site-nav", 1),
    ("b1b-hero-player", 1), ("#mainVideo", 1),
    ("b1b-narration-banner", 1), ("b1b-bookmarks", 1), ("b1b-toc-sidebar", 1),
    ("b1b-article", 1), ("article.article", 1),
    ("b1b-watch-panel", 1), ("b1b-chapter-nav", 1), ("b1b-footer", 1),
    ("b1b-back-to-top", 1), ("#smartAudioPill", 1),
    ("b1b-fullscreen", 1), ("b1b-vector-plane", 1),
]

ok_all = True

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    for num in range(1, 5):
        n = str(num).zfill(2)
        url = BASE.format(n)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page_errors = []
        console_errors = []
        bad_responses = []
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("response", lambda r: bad_responses.append((r.status, r.url)) if r.status >= 400 else None)

        page.goto(url, wait_until="load")
        page.wait_for_function(
            "window.narrationEngine && window.narrationEngine.sections && "
            "window.narrationEngine.sections.length > 0 && window.TEACHER_AUDIO_MANIFEST",
            timeout=15000)

        fails = []

        # 1) page errors
        if page_errors:
            fails.append("page errors: " + repr(page_errors))

        # 2) components rendered exactly once
        for sel, want in EXPECTED_COMPONENTS:
            got = page.evaluate("s => document.querySelectorAll(s).length", sel)
            if got != want:
                fails.append(f"component count {sel}: got {got}, want {want}")
        quiz_count = page.evaluate("document.querySelectorAll('b1b-quiz .quiz-block').length")
        if quiz_count != EXPECTED_QUIZZES:
            fails.append(f"quiz render count: got {quiz_count}, want {EXPECTED_QUIZZES}")
        section_count = page.evaluate("document.querySelectorAll('article.article > b1b-section > section').length")
        if section_count < 6:
            fails.append(f"section count too low: {section_count}")
        no_narr = page.evaluate("document.querySelectorAll('section[data-no-narration=\"true\"]').length")
        if no_narr != 1:
            fails.append(f"data-no-narration sections: {no_narr}")

        # 3) DOM <-> manifest parity
        parity = page.evaluate("""() => {
          const m = window.TEACHER_AUDIO_MANIFEST;
          return window.narrationEngine.sections.map(s => ({
            id: s.id,
            blocks: s.blocks.length,
            cues: (m.sections[s.id] ? m.sections[s.id].cues : []).length,
            titleMatch: !!(m.sections[s.id] && m.sections[s.id].title === s.title)
          }));
        }""")
        for row in parity:
            if row["blocks"] != row["cues"] or not row["titleMatch"]:
                fails.append("parity mismatch: " + repr(row))
        if any(r["id"] == "sec-lab" for r in parity):
            fails.append("lab section incorrectly narrated")
        manifest_keys = page.evaluate("Object.keys(window.TEACHER_AUDIO_MANIFEST.sections)")
        dom_ids = [r["id"] for r in parity]
        if set(manifest_keys) != set(dom_ids):
            fails.append(f"manifest/DOM section keys differ: {manifest_keys} vs {dom_ids}")

        # 4) quiz click interaction (every quiz: select correct option + check)
        quiz_results = page.evaluate("""() => {
          const out = [];
          document.querySelectorAll('b1b-quiz .quiz-block').forEach((b, i) => {
            const correct = parseInt(b.dataset.correct, 10);
            const opts = b.querySelectorAll('.quiz-option');
            if (!opts[correct]) { out.push({i, ok:false, why:'missing option'}); return; }
            opts[correct].click();
            const chk = b.querySelector('.quiz-check-btn');
            if (!chk || chk.disabled) { out.push({i, ok:false, why:'check disabled'}); return; }
            chk.click();
            const fb = b.querySelector('.quiz-feedback');
            out.push({i, ok: !!(fb && fb.classList.contains('show') && fb.classList.contains('correct-fb')),
                      why: (fb ? fb.textContent.trim().slice(0,60) : 'no feedback')});
          });
          return out;
        }""")
        for qr in quiz_results:
            if not qr["ok"]:
                fails.append(f"quiz {qr['i']} click failed: {qr['why']}")

        # reveal button check on first quiz
        reveal_ok = page.evaluate("""() => {
          const b = document.querySelector('b1b-quiz .quiz-block');
          const r = b && b.querySelector('.quiz-reveal-btn');
          if (!r) return false;
          r.click();
          const fb = b.querySelector('.quiz-feedback');
          return !!(fb && fb.classList.contains('show') && fb.classList.contains('correct-fb'));
        }""")
        if not reveal_ok:
            fails.append("quiz reveal button failed")

        # 5) video src + load
        vsrc = page.get_attribute("#mainVideo", "src")
        want_src = f"../../media_vault/fractals/lesson_{n}/experiments/3b1b_fractals_{n}_full_dubbed.mp4"
        if vsrc != want_src:
            fails.append(f"video src mismatch: {vsrc}")
        vready = page.evaluate("document.querySelector('#mainVideo').readyState")
        if vready < 1:
            fails.append(f"video not loadable, readyState={vready}")

        # console / network diagnostics (reported, not fatal)
        net_4xx = [x for x in bad_responses if x[0] >= 400]

        status = "PASS" if not fails else "FAIL"
        if fails:
            ok_all = False
        print(f"\n===== lesson_{n} : {status} =====")
        print("URL:", url)
        print("page_errors:", page_errors)
        print("console_errors:", console_errors[:8])
        print("http>=400:", net_4xx[:8])
        print("components: OK" if not any("component" in f or "quiz render" in f or "section count" in f or "no-narration" in f for f in fails) else "components: FAIL")
        print("parity:", parity)
        print("quiz_clicks:", quiz_results, "reveal:", reveal_ok)
        print("video:", vsrc, "readyState:", vready)
        if fails:
            print("FAILURES:")
            for f in fails:
                print("  -", f)
        page.close()

    browser.close()

print("\n===== OVERALL:", "PASS" if ok_all else "FAIL", "=====")
sys.exit(0 if ok_all else 1)
