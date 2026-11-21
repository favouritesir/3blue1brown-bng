from playwright.sync_api import sync_playwright
with sync_playwright() as pl:
    b=pl.chromium.launch(headless=True,channel='chrome')
    pg=b.new_page(); logs=[]
    pg.on('console',lambda m:logs.append(m.text) if m.type=='error' else None)
    pg.goto('http://127.0.0.1:8085/courses/linear_algebra/lesson_01.html',wait_until='domcontentloaded'); pg.wait_for_timeout(600)
    pg.eval_on_selector('#mainVideo','e=>{e.addEventListener("seeking",()=>console.log("SEEKING",e.currentTime)); e.addEventListener("seeked",()=>console.log("SEEKED",e.currentTime)); e.addEventListener("loadedmetadata",()=>console.log("META",e.duration));}')
    pg.on('console',lambda m:logs.append(m.text) if m.text.startswith(('SEEK','META')) else None)
    pg.eval_on_selector('#mainVideo','e=>e.play().catch(()=>{})'); pg.wait_for_timeout(1200)
    print('BEFORE click: video',pg.eval_on_selector('#mainVideo','e=>e.currentTime'),'audio?',pg.eval_on_selector('#bgAudio','e=>e?e.currentTime:"none"') if pg.locator('#bgAudio').count() else 'no bgAudio')
    pg.locator('.bookmark-chip').nth(2).click()
    for t in [100,300,600,1000,1500]:
        pg.wait_for_timeout(t if t==100 else t-[100,300,600,1000,1500][[100,300,600,1000,1500].index(t)-1])
        print(f'  +{t}ms video',pg.eval_on_selector('#mainVideo','e=>e.currentTime'),'paused',pg.eval_on_selector('#mainVideo','e=>e.paused'))
    print('logs:',logs[-10:])
    b.close()
