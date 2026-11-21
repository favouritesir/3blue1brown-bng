from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8085/courses/linear_algebra/lesson_01.html"

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page()
    errs = []
    cons = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: cons.append((m.type, m.text)) if m.type in ("error", "warning") else None)
    pg.goto(URL, wait_until="domcontentloaded")
    pg.wait_for_timeout(1500)
    print("TITLE", pg.title())
    print("PAGEERRORS", errs)
    print("CONSOLE_ERR_WARN", cons[:15])
    print("SECTIONS", pg.evaluate("window.narrationEngine && window.narrationEngine.sections.map(s=>[s.id,s.blocks.length,s.cues.length])"))
    print("NAVBARS", pg.evaluate("document.querySelectorAll('b1b-navbar').length"), pg.evaluate("document.querySelectorAll('.site-nav').length"))
    print("PILLS", pg.evaluate("document.querySelectorAll('#smartAudioPill').length"))
    b.close()
