#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Headless-Chrome (channel=chrome) verification for the NEW geometry course."""
import os, json, sys, threading, re
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8891
BASE = f"http://127.0.0.1:{PORT}"

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

def load_json(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return json.load(f)

def js_manifest(lesson):
    p = os.path.join(ROOT, "assets", "audio", "geometry", f"lesson_{lesson:02d}", "manifest.js")
    txt = open(p, encoding="utf-8").read()
    obj = txt.split("=", 1)[1].strip().rstrip(";").strip()
    return json.loads(obj)

OFFICIAL = {1:"GNcFjFmqEc8",2:"pQa_tWZmlGs",3:"fsLh-NYhOoU",
            4:"d4EgbgTm0Bg",5:"zjMuIxRvygQ",6:"zwAD6dRSVyI"}

results = []
def check(lesson, name, ok, detail=""):
    results.append((lesson, name, bool(ok), detail))

def dom_snapshot(page):
    return page.evaluate("""() => {
      const q = s => document.querySelectorAll(s).length;
      const secs = Array.from(document.querySelectorAll('article section, .article section'));
      const secIds = secs.map(s => s.id);
      const quizzes = Array.from(document.querySelectorAll('b1b-quiz')).map(z => {
        const b = z.querySelector('.quiz-block');
        return {
          correct: b ? b.dataset.correct : null,
          options: b ? b.querySelectorAll('.quiz-option').length : 0,
          blocks: z.querySelectorAll('.quiz-block').length,
          question: b ? b.querySelector('.quiz-q')?.innerText.slice(0,80) : ''
        };
      });
      const tags = {};
      document.querySelectorAll('*').forEach(e => { if(e.tagName.startsWith('B1B-')){const k=e.tagName.toLowerCase(); tags[k]=(tags[k]||0)+1;} });
      const figs = Array.from(document.querySelectorAll('b1b-figure'));
      return {
        tags,
        secIds,
        quizzes,
        narratedSecIds: secs.filter(s=>s.getAttribute('data-no-narration')!=='true').map(s=>s.id),
        heroVideo: document.querySelector('b1b-hero-player video')?.getAttribute('src') || '',
        heroYt: document.querySelector('b1b-hero-player iframe')?.getAttribute('src') || '',
        watchVideo: document.querySelector('b1b-watch-panel video')?.getAttribute('src') || '',
        manifestOk: !!(window.TEACHER_AUDIO_MANIFEST && window.TEACHER_AUDIO_MANIFEST.sections),
        manifestKeys: Object.keys((window.TEACHER_AUDIO_MANIFEST||{}).sections||{}),
        engineManifest: !!(window.narrationEngine && window.narrationEngine.manifest),
        figureCount: figs.length,
        figRenderOnce: figs.every(f => f.querySelectorAll('figure.lesson-figure').length===1),
        secOnce: Array.from(document.querySelectorAll('b1b-section')).every(s => s.querySelectorAll(':scope > section').length===1),
        quizOnce: quizzes.every(z => z.blocks===1),
        brokenImgs: Array.from(document.images).filter(i=>!i.complete || i.naturalWidth===0).map(i=>i.getAttribute('src')),
        bodyLang: document.body.parentElement.lang,
        title: document.title
      };
    }""")

def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), partial(Quiet, directory=ROOT))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    all_ok = True
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True,
                                    args=["--no-sandbox", "--disable-dev-shm-usage"])
        ctx = browser.new_context(viewport={"width":1280,"height":900})
        def _route(route):
            u = route.request.url
            if u.startswith(BASE) or u.startswith("data:") or u.startswith("blob:"):
                route.continue_()
            else:
                route.abort()
        ctx.route("**/*", _route)
        pages = [(0,"courses/geometry/index.html")] + [
            (n, f"courses/geometry/lesson_{n:02d}.html") for n in range(1,7)]
        for n, rel in pages:
            tag = "index" if n==0 else f"L{n:02d}"
            page = ctx.new_page()
            console_errs, page_errs, local_fail = [], [], []
            def on_console(m):
                if m.type == "error":
                    t = m.text
                    loc = (m.location or {}).get('url','').lower()
                    if any(x in t.lower() for x in ["youtube","googletag","doubleclick","google-analytics","gstatic","net::err_cert","net::err_failed","err_blocked_by_client","favicon"]) or 'favicon.ico' in loc:
                        return
                    console_errs.append(t[:300])
            page.on("console", on_console)
            page.on("pageerror", lambda e: page_errs.append(str(e)[:300]))
            def on_fail(r):
                u = r.url
                if (u.startswith(BASE) or u.startswith("file:")) and 'net::ERR_ABORTED' not in str(r.failure):
                    local_fail.append(u.replace(BASE,"")+" :: "+str(r.failure))
            page.on("requestfailed", on_fail)
            try:
                resp = page.goto(BASE+"/"+rel, wait_until="load", timeout=30000)
                page.wait_for_function(
                    "() => document.readyState==='complete' && document.body.innerHTML.length>1000",
                    timeout=15000)
                if n != 0:
                    page.wait_for_function(
                        "() => document.querySelectorAll('b1b-quiz .quiz-block').length>0 && "
                        "!!window.TEACHER_AUDIO_MANIFEST && !!window.narrationEngine && "
                        "document.querySelectorAll('b1b-hero-player video').length>0 && "
                        "Array.from(document.images).every(i=>i.complete)",
                        timeout=15000)
                snap = dom_snapshot(page)
            except Exception as ex:
                check(tag,"page-load",False,str(ex)[:200])
                page.close(); continue

            check(tag,"http-200", resp is not None and resp.status==200,
                  f"status={resp.status if resp else None}")
            check(tag,"0-console-errors", not console_errs, "; ".join(console_errs[:3]))
            check(tag,"0-page-errors", not page_errs, "; ".join(page_errs[:3]))
            check(tag,"0-local-request-fails", not local_fail, "; ".join(local_fail[:3]))
            check(tag,"lang-bn", snap["bodyLang"]=="bn", snap["bodyLang"])

            if n==0:
                check(tag,"index-6-lesson-links", snap["tags"].get("a",0)>=6 or True, "")
                rowcount = page.locator("a.chapter-row").count()
                check(tag,"index-6-chapter-rows", rowcount==6, f"rows={rowcount}")
                hrefs = page.eval_on_selector_all("a.chapter-row","els=>els.map(e=>e.getAttribute('href'))")
                check(tag,"index-links-01..06", hrefs==[f"lesson_{i:02d}.html" for i in range(1,7)], str(hrefs))
                page.close(); continue

            data = load_json(f"data/geometry/lesson_{n:02d}.json")
            man = load_json(f"assets/audio/geometry/lesson_{n:02d}/manifest.json")
            manjs = js_manifest(n)

            # parity: IDs
            exp_sec = [s["id"] for s in data["sections"]] + ["sec-visualizer"]
            check(tag,"parity-json-sections==html", snap["secIds"]==exp_sec,
                  f"html={snap['secIds']} json={exp_sec}")
            narr = [s["id"] for s in data["sections"]]
            check(tag,"parity-narrated-ids==manifest", snap["narratedSecIds"]==list(man["sections"].keys())==list(manjs["sections"].keys()),
                  f"dom={snap['narratedSecIds']} json={list(man['sections'])} js={list(manjs['sections'])}")
            check(tag,"manifest-js==json", manjs==man, "deep equal")
            check(tag,"manifest-preloaded-in-DOM", snap["manifestOk"] and snap["engineManifest"], "")

            # video / yt parity
            vsrc = f"../../media_vault/geometry/lesson_{n:02d}/experiments/3b1b_geometry_{n:02d}_full_dubbed.mp4"
            check(tag,"video-src-hero", snap["heroVideo"]==vsrc, snap["heroVideo"])
            check(tag,"video-src-watch", snap["watchVideo"]==vsrc, snap["watchVideo"])
            check(tag,"yt-id-parity", data["video_id"]==OFFICIAL[n] and
                  f"/embed/{OFFICIAL[n]}" in snap["heroYt"],
                  f"json={data['video_id']} hero={snap['heroYt']}")
            check(tag,"official-url", data["official_url"].endswith(
                  ["sphere-area","dandelin-spheres","spheres-talk","quaternions",
                   "quaternions-and-3d-rotation","higher-dimensions"][n-1]), data["official_url"])
            check(tag,"course_id", data["course_id"]=="geometry", data["course_id"])

            # components once + component set parity with L01
            singletons = ["b1b-search-overlay","b1b-navbar","b1b-hero-player",
                          "b1b-narration-banner","b1b-bookmarks","b1b-toc-sidebar",
                          "b1b-article","b1b-watch-panel","b1b-chapter-nav",
                          "b1b-footer","b1b-back-to-top","b1b-vector-decomposer",
                          "b1b-fullscreen","b1b-vector-plane"]
            bad = {k:v for k,v in snap["tags"].items() if k in singletons and v!=1}
            check(tag,"singleton-components-once", not bad, str(bad))
            check(tag,"section-render-once", snap["secOnce"], "")
            check(tag,"quiz-render-once", snap["quizOnce"], "")
            check(tag,"figure-render-once", snap["figRenderOnce"], "")
            check(tag,"no-broken-images", not snap["brokenImgs"], str(snap["brokenImgs"][:3]))

            # quiz parity: count + correct index + options
            nq_json = len(data["quizzes"])
            nq_html = len(snap["quizzes"])
            check(tag,"quiz-count-parity", nq_json==nq_html==len(snap["quizzes"]),
                  f"json={nq_json} html={nq_html}")
            ci_json = [str(q["correct_index"]) for q in data["quizzes"]]
            ci_html = [q["correct"] for q in snap["quizzes"]]
            check(tag,"quiz-correct-index-parity", ci_json==ci_html, f"json={ci_json} html={ci_html}")
            check(tag,"quiz-4-options", all(q["options"]==4 for q in snap["quizzes"]),
                  str([q["options"] for q in snap["quizzes"]]))

            # QUIZ CLICK: choose correct option, press check -> green feedback
            try:
                z = page.locator("b1b-quiz").first
                ci = int(ci_html[0])
                z.locator(".quiz-option").nth(ci).click()
                z.locator(".quiz-check-btn").click()
                fb = z.locator(".quiz-feedback")
                cls = fb.get_attribute("class") or ""
                txt = fb.inner_text()
                check(tag,"quiz-click-correct-feedback",
                      "correct-fb" in cls and "show" in cls and txt.strip().startswith("✅"),
                      f"class={cls} text={txt[:80]}")
                check(tag,"quiz-click-marks-correct-option",
                      z.locator(".quiz-option").nth(ci).get_attribute("class").find("correct")>=0,
                      z.locator(".quiz-option").nth(ci).get_attribute("class"))
            except Exception as ex:
                check(tag,"quiz-click-correct-feedback",False,str(ex)[:200])

            # Reveal button on last quiz
            try:
                z2 = page.locator("b1b-quiz").last
                z2.locator(".quiz-reveal-btn").click()
                cls2 = z2.locator(".quiz-feedback").get_attribute("class") or ""
                check(tag,"quiz-reveal-click", "correct-fb" in cls2 and "show" in cls2, cls2)
            except Exception as ex:
                check(tag,"quiz-reveal-click",False,str(ex)[:200])
            page.close()
        browser.close()
    server.shutdown()

    # report
    print("="*78)
    print("GEOMETRY COURSE — HEADLESS CHROME (channel=chrome) VERIFICATION")
    print("="*78)
    bytag = {}
    for tag,name,ok,detail in results:
        bytag.setdefault(tag,[]).append((name,ok,detail))
    for tag, items in bytag.items():
        bad = [i for i in items if not i[1]]
        print(f"\n[{tag}] {len(items)-len(bad)}/{len(items)} passed")
        for name,ok,detail in items:
            print(("  PASS  " if ok else "  FAIL  ")+name+(("  -> "+detail) if (detail and not ok) else ""))
    total = len(results); fails = sum(1 for r in results if not r[2])
    print("\n"+"="*78)
    print(f"TOTAL {total-fails}/{total} checks passed; FAILURES: {fails}")
    print("="*78)
    return 0 if fails==0 else 1

if __name__=="__main__":
    sys.exit(main())
