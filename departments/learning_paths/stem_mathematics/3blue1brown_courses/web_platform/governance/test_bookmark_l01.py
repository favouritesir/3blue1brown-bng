from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8085/courses/linear_algebra/lesson_01.html'
with sync_playwright() as pl:
    b=pl.chromium.launch(headless=True,channel='chrome')
    pg=b.new_page(viewport={'width':1280,'height':900}); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(BASE,wait_until='domcontentloaded',timeout=15000); pg.wait_for_timeout(1000)
    print('body class:',pg.eval_on_selector('body','e=>e.className'))
    print('hero video visible:',pg.locator('#mainVideo').is_visible())
    print('video readyState:',pg.eval_on_selector('#mainVideo','e=>e.readyState'))
    print('video src:',pg.eval_on_selector('#mainVideo','e=>e.currentSrc.split("/").pop()'))
    print('video duration:',pg.eval_on_selector('#mainVideo','e=>e.duration'))
    chips=pg.locator('.bookmark-chip'); print('chips:',chips.count())
    for i in [1,2,3]:
        attr=chips.nth(i).get_attribute('onclick')
        chips.nth(i).click(); pg.wait_for_timeout(400)
        t=pg.eval_on_selector('#mainVideo','e=>e.currentTime')
        print(f'  chip{i} onclick={attr} -> currentTime={t:.2f}')
    print('errors:',errs[:3])
    b.close()
