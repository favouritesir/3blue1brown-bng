# -*- coding: utf-8 -*-
"""Headless Chrome (channel=chrome) verification for the NEW CS course."""
import json, os, sys
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "http://127.0.0.1:8100"
ORDER = ["entropy","cross-entropy","arithmetic-codes","wordle","wordle-2","bitcoin",
         "256-bit-security","epidemic-simulations","hamming-codes","hamming-codes-2",
         "grover","grover-clarification","hanoi-and-sierpinski"]
META = json.load(open(os.path.join(ROOT,"governance","_cs_meta.json"), encoding="utf-8"))

NARRATION_SCRIPTS = [
 "assets/libs/katex/katex.min.js","assets/libs/katex/auto-render.min.js",
 "assets/libs/katex-stub.js","assets/js/lesson_components.js",
 "assets/js/lesson_components_extended.js","assets/js/main.js",
 "assets/js/lesson.js","assets/js/narration_engine.js",
]

results, fatal = [], []
def check(cond, msg, n, label):
    ok = bool(cond)
    results.append({"lesson":label,"check":msg,"ok":ok})
    if not ok: fatal.append("%s [%s]: %s" % (label,n,msg))
    return ok

EVAL = """() => {
  const E=window.narrationEngine, M=window.TEACHER_AUDIO_MANIFEST;
  const q=s=>document.querySelectorAll(s).length;
  const secs=E?E.sections.map(s=>({id:s.id,d:s.blocks.length,c:s.cues.length,
      ok:s.blocks.length===s.cues.length,
      mcue:(M&&M.sections[s.id])?M.sections[s.id].cues.length:-1,
      mid:!!(M&&M.sections[s.id])})):[];
  const bad=(()=>{let c=0;Object.values(M?.sections||{}).forEach(s=>(s.cues||[])
      .forEach(k=>{if(['quiz-block','media-tab'].includes(k.type))c++;}));return c;})();
  const imgs=Array.from(document.images);
  return {
    title:document.title, sections:secs,
    allMatch:secs.length>0&&secs.every(s=>s.ok&&s.c===s.mcue),
    manifestIds:Object.keys(M?.sections||{}), badTypes:bad,
    components:{
      navbar:q('b1b-navbar .site-nav'),heroVideo:q('b1b-hero-player video'),
      banner:q('b1b-narration-banner .narration-card'),
      bookmarks:q('b1b-bookmarks .bookmark-chip'),
      article:q('b1b-article article.article'),figures:q('figure.lesson-figure'),
      quizzes:q('b1b-quiz .quiz-block'),fullscreen:q('b1b-fullscreen .b1b-fs-btn'),
      watch:q('b1b-watch-panel .watch-mode-panel'),footer:q('b1b-footer .site-footer'),
      nolarr:q('section[data-no-narration="true"]')
    },
    imagesOk:imgs.length>0&&imgs.every(i=>i.complete&&i.naturalWidth>0),imgCount:imgs.length,
    heroSrc:document.querySelector('b1b-hero-player')?.getAttribute('video-src')||'',
    heroYt:document.querySelector('b1b-hero-player')?.getAttribute('yt-id')||'',
    watchSrc:document.querySelector('b1b-watch-panel')?.getAttribute('video-src')||'',
    watchYt:document.querySelector('b1b-watch-panel')?.getAttribute('yt-id')||'',
    scripts:Array.from(document.querySelectorAll('head script[src]')).map(s=>s.getAttribute('src'))
  };
}"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel="chrome")
    for n, slug in enumerate(ORDER, 1):
        label = "lesson_%02d (%s)" % (n, slug)
        page = browser.new_page()
        pageerrors, console_errors, notfound = [], [], []
        page.on("pageerror", lambda e, a=pageerrors: a.append(str(e)))
        page.on("console", lambda m, a=console_errors: a.append(m.text)
                if m.type == "error" else None)
        page.on("response", lambda r, a=notfound: a.append(r.url)
                if r.status >= 400 else None)
        url = "%s/courses/computer_science/lesson_%02d.html?v=verify" % (BASE, n)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(1100)
            r = page.evaluate(EVAL)
        except Exception as e:
            check(False, "navigation/eval failed: %s" % str(e).split("\n")[0], n, label)
            page.close()
            continue

        check(len(pageerrors)==0, "0 page errors (got %d: %s)" % (len(pageerrors), pageerrors[:2]), n, label)
        c = r["components"]
        for key in ["navbar","heroVideo","banner","article","fullscreen","watch","footer"]:
            check(c[key]==1, "%s rendered exactly once (got %d)" % (key,c[key]), n, label)
        check(c["bookmarks"]>=1, "bookmarks rendered (%d)" % c["bookmarks"], n, label)
        check(c["figures"]>=5, "figures rendered (%d)" % c["figures"], n, label)
        check(c["quizzes"]>=2, "quizzes rendered (%d)" % c["quizzes"], n, label)
        check(c["nolarr"]==1, "one data-no-narration lab section (got %d)" % c["nolarr"], n, label)
        check(len(r["sections"])==5, "5 narrated sections (got %d)" % len(r["sections"]), n, label)
        check(r["allMatch"], "DOM cue parity blocks==cues==manifest per section", n, label)
        check(r["badTypes"]==0, "no quiz/media cue types (%d)" % r["badTypes"], n, label)
        check(r["manifestIds"]==[s["id"] for s in r["sections"]],
              "manifest narrated IDs match DOM section IDs", n, label)
        check(r["imagesOk"], "all %d images loaded" % r["imgCount"], n, label)
        want_src = "../../media_vault/computer_science/lesson_%02d/experiments/3b1b_computer_science_%02d_full_dubbed.mp4" % (n,n)
        yt = META[slug]["youtube_id"]
        check(r["heroSrc"]==want_src, "hero video-src exact", n, label)
        check(r["watchSrc"]==want_src, "watch video-src exact", n, label)
        check(r["heroYt"]==yt and r["watchYt"]==yt, "official youtube_id on hero+watch", n, label)
        expected = ["../../assets/audio/computer_science/lesson_%02d/manifest.js" % n] + ["../../"+s for s in NARRATION_SCRIPTS]
        got = [s.split("?")[0] for s in r["scripts"]]
        check(got==expected, "script load order == L01 (incl. manifest)", n, label)

        try:
            qi = page.evaluate("""() => {const b=document.querySelector('b1b-quiz .quiz-block');
                return b?{correct:parseInt(b.dataset.correct||'0',10),
                opts:b.querySelectorAll('.quiz-option').length}:null;}""")
            ok = False
            if qi and qi["opts"] > qi["correct"]:
                q = page.locator("b1b-quiz .quiz-block").first
                q.locator(".quiz-option").nth(qi["correct"]).click()
                q.locator(".quiz-check-btn").click()
                page.wait_for_timeout(100)
                ok = page.evaluate("""() => {const f=document.querySelector('b1b-quiz .quiz-feedback');
                    return !!(f&&f.classList.contains('show')&&f.classList.contains('correct-fb'));}""")
            check(ok, "quiz click -> correct feedback", n, label)
        except Exception as e:
            check(False, "quiz click error: %s" % e, n, label)

        check(len(console_errors)==0, "0 console errors (got %d: %s)" % (len(console_errors),console_errors[:2]), n, label)
        check(len(notfound)==0, "0 HTTP 4xx/5xx (got %d: %s)" % (len(notfound),notfound[:3]), n, label)
        page.close()

    # index page
    page = browser.new_page()
    idx_errors, idx_404 = [], []
    page.on("pageerror", lambda e: idx_errors.append(str(e)))
    page.on("response", lambda r, a=idx_404: a.append(r.url) if r.status >= 400 else None)
    try:
        page.goto("%s/courses/computer_science/index.html?v=verify" % BASE,
                  wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(300)
        rows = page.evaluate("() => document.querySelectorAll('.chapter-row').length")
        check(len(idx_errors)==0, "index: 0 page errors (got %s)" % idx_errors[:2], 0, "index")
        check(len(idx_404)==0, "index: 0 HTTP 4xx/5xx (got %s)" % idx_404[:3], 0, "index")
        check(rows==13, "index: 13 lesson rows (got %d)" % rows, 0, "index")
    except Exception as e:
        check(False, "index verification failed: %s" % str(e).split("\n")[0], 0, "index")
    browser.close()

report = {"results":results,"fatal":fatal,"total_checks":len(results),
          "passed":len(results)-len(fatal),"failed":len(fatal)}
with open(os.path.join(ROOT,"governance","_cs_verify_summary.json"),"w",encoding="utf-8") as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps({"total_checks":report["total_checks"],"passed":report["passed"],
                  "failed":report["failed"],"fatal":fatal},ensure_ascii=False,indent=2))
sys.exit(1 if fatal else 0)
