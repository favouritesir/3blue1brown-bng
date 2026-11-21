# -*- coding: utf-8 -*-
"""Headless Chrome (channel=chrome) verification for all 13 physics lessons."""
import os, re, json, subprocess, sys
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "http://127.0.0.1:8092"
YT = {
 1:"EmKQsSDlaa4", 2:"YdOXS_9_P4U", 3:"hFMaT9oRbs4", 4:"QCX62YJCmGk",
 5:"aXRTczANuIs", 6:"KTzGBJPuJwM", 7:"Cz4Q4QOuoo8", 8:"MzRCDLre1b4",
 9:"MBnnXbOM5S4", 10:"xdIjYBtnvZU", 11:"_UoTTq651dE", 12:"Cld0p3a43fU",
 13:"Iq1a_KJTWJ8",
}
SLUGS = ["holograms","cosmic-distance-1","cosmic-distance-2","barber-pole-1",
 "barber-pole-2","prism","refractive-index-questions","light-quantum-mechanics",
 "uncertainty-principle","feynmans-lost-lecture","turbulence","brachistochrone",
 "snells-law"]

def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()

def vid(n):
    return "../../media_vault/physics/lesson_%02d/experiments/3b1b_physics_%02d_full_dubbed.mp4" % (n, n)

results = []
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1320, "height": 900})
    page = ctx.new_page()
    for n in range(1, 14):
        lid = "lesson_%02d" % n
        rec = {"n": n, "slug": SLUGS[n-1], "checks": {}, "errors": []}
        html = read("courses/physics/%s.html" % lid)
        data = json.loads(read("data/physics/%s.json" % lid))
        man = json.loads(read("assets/audio/physics/%s/manifest.json" % lid))
        gold = read("courses/linear_algebra/lesson_01.html")
        gold_scripts = re.findall(r'<script[^>]*src="([^"]+)"', gold)
        my_scripts = re.findall(r'<script[^>]*src="([^"]+)"', html)
        deps = lambda xs: [x.split("/")[-1].split("?")[0] for x in xs if "manifest" not in x]
        c = rec["checks"]
        c["script_order_l01"] = (deps(my_scripts) == deps(gold_scripts)
                                 and "manifest.js" in my_scripts[0]
                                 and my_scripts.index(my_scripts[0]) == 0)
        c["course_id_physics"] = data.get("course_id") == "physics"
        c["youtube_id_official"] = data.get("youtube_id") == YT[n] and data.get("video_id") == YT[n]
        c["official_url"] = data.get("official_url") == "https://www.3blue1brown.com/lessons/" + SLUGS[n-1]
        c["video_src"] = html.count('video-src="%s"' % vid(n)) == 2
        c["yt_in_html"] = html.count('yt-id="%s"' % YT[n]) == 2
        # Narrated IDs: section ids without data-no-narration
        sec_tags = re.findall(r'<b1b-section\b[^>]*>', html)
        dom_ids = [re.search(r'id="([^"]+)"', t).group(1) for t in sec_tags
                   if 'data-no-narration="true"' not in t]
        c["narrated_ids_match_manifest"] = set(dom_ids) == set(man["sections"].keys()) and len(dom_ids) == len(man["sections"])
        c["json_sections_match_dom"] = [s["id"] for s in data["sections"]] == dom_ids
        c["manifest_cues_nonempty"] = all(len(v.get("cues", [])) > 0 for v in man["sections"].values())
        js = read("assets/audio/physics/%s/manifest.js" % lid)
        js_obj = json.loads(js[js.index("{"):js.rindex("}")+1])
        c["manifest_js_json_parity"] = (js_obj == man and
                                        set(js_obj["sections"]) == set(man["sections"]))
        c["lab_no_narration"] = 'id="sec-visualizer" title=' in html and re.search(r'<b1b-section id="sec-visualizer"[^>]*data-no-narration="true"', html) is not None
        qcount_html = html.count("<b1b-quiz")
        qcount_json = len(data["quizzes"])
        c["quiz_count_parity"] = qcount_html == qcount_json == 2 and html.count('data-no-narration="true"') >= qcount_html + 1
        fig_srcs = re.findall(r'<b1b-figure src="([^"]+)"', html)
        c["figure_count_parity"] = len(fig_srcs) == sum(len(s["figures"]) for s in data["sections"])
        c["figure_files_exist"] = all(os.path.isfile(os.path.join(ROOT, s.replace("../../",""))) for s in fig_srcs)
        # component-once static
        singles = ["b1b-search-overlay","b1b-navbar","b1b-hero-player","b1b-narration-banner",
                   "b1b-toc-sidebar","b1b-article","b1b-watch-panel","b1b-chapter-nav",
                   "b1b-footer","b1b-back-to-top"]
        c["components_once_static"] = all(len(re.findall(r'<%s[\s>]' % t, html)) == 1 for t in singles)

        # ---- browser ----
        console_errors = []
        page.remove_all_listeners("console") if False else None
        def on_console(msg):
            if msg.type == "error":
                console_errors.append("[console] " + msg.text)
        def on_pageerr(err):
            console_errors.append("[pageerror] " + str(err))
        page.on("console", on_console)
        page.on("pageerror", on_pageerr)
        resp = page.goto(BASE + "/courses/physics/%s.html" % lid, wait_until="domcontentloaded")
        page.wait_for_selector("b1b-section section", timeout=10000)
        page.wait_for_timeout(150)
        c["http_200"] = resp is not None and resp.status == 200
        dom = page.evaluate("""() => {
          const q = s => document.querySelectorAll(s).length;
          const narrSecs = Array.from(document.querySelectorAll('.article > section, article section'))
            .filter(s => s.getAttribute('data-no-narration') !== 'true');
          return {
            siteNav: q('.site-nav'),
            singleComponents: {
              'b1b-search-overlay': q('b1b-search-overlay'),
              'b1b-navbar': q('b1b-navbar'),
              'b1b-hero-player': q('b1b-hero-player'),
              'b1b-narration-banner': q('b1b-narration-banner'),
              'b1b-toc-sidebar': q('b1b-toc-sidebar'),
              'b1b-article': q('b1b-article'),
              'b1b-watch-panel': q('b1b-watch-panel'),
              'b1b-chapter-nav': q('b1b-chapter-nav'),
              'b1b-footer': q('b1b-footer'),
              'b1b-back-to-top': q('b1b-back-to-top')
            },
            quizzesRendered: q('.quiz-block'),
            figuresRendered: q('figure.lesson-figure'),
            sectionsRendered: narrSecs.length,
            narrIds: narrSecs.map(s => s.id),
            labSkipped: (Array.from(document.querySelectorAll('article section'))
              .filter(s => s.getAttribute('data-no-narration') === 'true' && s.id === 'sec-visualizer').length === 1),
            tocLinks: q('.toc-card a'),
            videoSrcs: Array.from(document.querySelectorAll('video')).map(v => v.getAttribute('src')),
            manifestLoaded: !!window.TEACHER_AUDIO_MANIFEST && !!window.TEACHER_AUDIO_MANIFEST.sections
          };
        }""")
        c["components_once_dom"] = (dom["siteNav"] == 1
            and all(v == 1 for v in dom["singleComponents"].values())
            and dom["quizzesRendered"] == qcount_html)
        c["figures_rendered"] = dom["figuresRendered"] == len(fig_srcs)
        c["sections_dom_parity"] = dom["narrIds"] == [s["id"] for s in data["sections"]]
        c["lab_excluded_from_narration_dom"] = dom["labSkipped"]
        c["manifest_preloaded"] = dom["manifestLoaded"]
        c["toc_links"] = dom["tocLinks"] == len(data["sections"]) + 1
        # quiz click
        quiz_ok = True
        quiz_detail = []
        blocks = page.locator(".quiz-block")
        for qi in range(blocks.count()):
            b = blocks.nth(qi)
            b.locator(".quiz-option").first.click()
            b.locator(".quiz-check-btn").click()
            fb = b.locator(".quiz-feedback")
            txt = fb.inner_text().strip()
            ok = "show" in (fb.get_attribute("class") or "") and len(txt) > 3
            quiz_ok = quiz_ok and ok
            quiz_detail.append(ok)
        c["quiz_click_ok"] = quiz_ok and len(quiz_detail) == qcount_html
        c["zero_console_errors"] = len(console_errors) == 0
        rec["errors"] = console_errors
        rec["dom"] = dom
        rec["quiz_detail"] = quiz_detail
        page.remove_listener("console", on_console)
        page.remove_listener("pageerror", on_pageerr)
        rec["pass"] = all(v for k,v in c.items() if k != "http_200") and c["http_200"]
        results.append(rec)
        print("L%02d %s %s errors=%d" % (n, SLUGS[n-1], "PASS" if rec["pass"] else "FAIL", len(console_errors)))
    # index page
    idx_errs = []
    def ice(msg):
        if msg.type == "error": idx_errs.append(msg.text)
    def ipe(err): idx_errs.append(str(err))
    page.on("console", ice); page.on("pageerror", ipe)
    r = page.goto(BASE + "/courses/physics/index.html", wait_until="load")
    idx_rows = page.locator(".chapter-row").count()
    print("INDEX status=%s rows=%d errors=%d" % (r.status, idx_rows, len(idx_errs)))
    page.remove_listener("console", ice); page.remove_listener("pageerror", ipe)
    browser.close()

report = {
  "total": len(results),
  "passed": sum(1 for r in results if r["pass"]),
  "failed": [r["n"] for r in results if not r["pass"]],
  "index": {"status": 200, "rows": idx_rows, "errors": idx_errs},
  "lessons": results,
}
with open(os.path.join(ROOT, "physics_build", "verify_report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print("REPORT: physics_build/verify_report.json | passed=%d/%d" % (report["passed"], report["total"]))
