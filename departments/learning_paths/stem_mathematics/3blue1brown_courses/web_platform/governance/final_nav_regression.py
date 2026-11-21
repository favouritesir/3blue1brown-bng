from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8085/courses/'
checks=[('linear_algebra',2,15),('calculus',3,12),('neural_networks',2,4),('probability',3,6),('differential_equations',2,6),('lockdown_math',3,10)]
with sync_playwright() as pl:
    b=pl.chromium.launch(headless=True,channel='chrome')
    pg=b.new_page(); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    for course,n,total in checks:
        pg.goto(BASE+f'{course}/lesson_{n:02d}.html',wait_until='domcontentloaded',timeout=15000); pg.wait_for_timeout(500)
        items=pg.locator('.playlist-item').count()
        active=pg.locator('.playlist-item.active').count()
        act_title=pg.locator('.playlist-item.active .playlist-item-title').all_inner_texts()[:1]
        step=pg.locator('.stepper-current, .nav-stepper, [class*=step] ').first
        print(f'{course} L{n}: playlist items={items}/{total} active={active} {act_title}')
    print('errors:',errs[:3])
    b.close()
