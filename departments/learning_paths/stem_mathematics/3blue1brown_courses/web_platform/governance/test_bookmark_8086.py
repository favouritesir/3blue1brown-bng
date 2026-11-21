from playwright.sync_api import sync_playwright
with sync_playwright() as pl:
    b=pl.chromium.launch(headless=True,channel='chrome')
    pg=b.new_page()
    pg.goto('http://127.0.0.1:8086/courses/linear_algebra/lesson_01.html',wait_until='domcontentloaded')
    pg.wait_for_timeout(500)
    pg.eval_on_selector('#mainVideo','e=>e.play().catch(()=>{})')
    pg.wait_for_timeout(1000)
    rng=pg.evaluate("""() => { const v=document.getElementById('mainVideo');
      let r=[]; for(let i=0;i<v.seekable.length;i++) r.push([v.seekable.start(i),v.seekable.end(i)]); return r; }""")
    print('seekable:',rng)
    pg.locator('.bookmark-chip').nth(2).click()
    pg.wait_for_timeout(900)
    print('after click currentTime:',pg.eval_on_selector('#mainVideo','e=>e.currentTime'))
    b.close()
