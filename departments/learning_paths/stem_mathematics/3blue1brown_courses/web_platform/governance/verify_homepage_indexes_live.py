from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8085/'
courses=[('linear_algebra',15),('calculus',12),('neural_networks',4),('probability',6),('differential_equations',6),('lockdown_math',10)]
with sync_playwright() as pl:
    b=pl.chromium.launch(headless=True,channel='chrome')
    pg=b.new_page(); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    r=pg.goto(BASE+'index.html',wait_until='domcontentloaded',timeout=15000); pg.wait_for_timeout(500)
    print('HOME HTTP',r.status,'cards:',pg.locator('[data-href*="index.html"]').count(),'errors:',len(errs))
    for c,n in courses:
        p=pg.goto(BASE+f'courses/{c}/index.html',wait_until='domcontentloaded',timeout=15000); pg.wait_for_timeout(200)
        links=pg.locator('a.chapter-row').count()
        print(f'  {c}: HTTP {p.status} chapter-rows {links}/{n} {"OK" if links==n else "MISMATCH"}')
    b.close()
