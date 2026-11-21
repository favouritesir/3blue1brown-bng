from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8085/courses/linear_algebra/'
with sync_playwright() as pl:
    b=pl.chromium.launch(headless=True,channel='chrome')
    pg=b.new_page(viewport={'width':1280,'height':900}); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(BASE+'lesson_01.html',wait_until='domcontentloaded',timeout=15000); pg.wait_for_timeout(600)
    print('L01 title:',pg.title()[:60])
    # click playlist item 2 (sidebar or watch drawer)
    links=pg.locator('a.playlist-item[href="lesson_02.html"]')
    print('playlist links to L02:',links.count())
    if links.count()==0:
        links=pg.locator('a[href="lesson_02.html"]')
        print('any links to L02:',links.count())
    pg.eval_on_selector('a.playlist-item[href="lesson_02.html"]','e=>e.click()')
    pg.wait_for_url('**/lesson_02.html',timeout=15000); pg.wait_for_load_state('domcontentloaded',timeout=15000); pg.wait_for_timeout(900)
    print('URL:',pg.url.split('/')[-1])
    print('title:',pg.title()[:70])
    print('stepper:',pg.locator('b1b-navbar').get_attribute('current') if pg.locator('b1b-navbar').count() else '?')
    print('video src:',pg.eval_on_selector('b1b-hero-player','e=>e.getAttribute("video-src")') if pg.locator('b1b-hero-player').count() else '?')
    print('video real src:',pg.eval_on_selector('#mainVideo','e=>e.currentSrc.split("/").pop()') if pg.locator('#mainVideo').count() else '?')
    print('duration:',pg.eval_on_selector('#mainVideo','e=>e.duration') if pg.locator('#mainVideo').count() else '?')
    print('active playlist:',pg.locator('.playlist-item.active .playlist-item-title').all_inner_texts()[:2])
    print('errors:',errs[:2])
    b.close()
