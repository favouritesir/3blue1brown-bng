from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page()
    errs = []
    cons = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: cons.append(m.text) if m.type == "error" else None)
    pg.goto("http://127.0.0.1:8085/courses/fractals/index.html", wait_until="load")
    pg.wait_for_timeout(600)
    rows = pg.evaluate("document.querySelectorAll('a.chapter-row').length")
    hrefs = pg.evaluate("Array.from(document.querySelectorAll('a.chapter-row')).map(a=>a.getAttribute('href'))")
    print("TITLE", pg.title())
    print("rows", rows, "hrefs", hrefs)
    print("page_errors", errs)
    print("console_errors", cons)
    print("RESULT", "PASS" if (rows == 4 and not errs and not cons) else "FAIL")
    b.close()
