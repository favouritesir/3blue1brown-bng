from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8085/courses/physics/'
with sync_playwright() as pl:
    b=pl.chromium.launch(headless=True,channel='chrome'); pg=b.new_page(); bad=[]
    for n in range(1,14):
        r=pg.goto(BASE+f'lesson_{n:02d}.html',wait_until='domcontentloaded',timeout=15000); pg.wait_for_timeout(80)
        arts=pg.locator('article.article').count(); q=pg.locator('b1b-quiz').count()
        ok=r.status==200 and arts==1 and q>=1
        print(f'L{n:02d}: HTTP {r.status} article={arts} quizzes={q} {"OK" if ok else "BAD"}')
        if not ok: bad.append(n)
    print('BAD:',bad)
    b.close()
