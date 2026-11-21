from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8085/courses/topics/'
with sync_playwright() as pl:
    b=pl.chromium.launch(headless=True,channel='chrome')
    pg=b.new_page(); bad=[]
    for topic in ['fractals','group-theory','number-theory','geometry','puzzles','why-pi','topology','analysis']:
        pg.goto(BASE+topic+'.html',wait_until='domcontentloaded',timeout=15000); pg.wait_for_timeout(150)
        links=pg.locator('a.topic-lesson').evaluate_all('els=>els.map(e=>e.getAttribute("href"))')
        local=[l for l in links if l and l.startswith('../')]
        print(f'{topic}: {len(local)} local of {len(links)}')
        if local:
            pg.goto('http://127.0.0.1:8085/courses/topics/'+local[0].replace('../',''),wait_until='domcontentloaded',timeout=15000)
            # resolve properly: local[0] is ../<course>/lesson... from /courses/topics/
            b2=1
    # direct check one link
    pg.goto(BASE+'fractals.html',wait_until='domcontentloaded')
    href=pg.locator('a.topic-lesson').first.get_attribute('href')
    r=pg.goto('http://127.0.0.1:8085/courses/topics/'+href.replace('../',''),wait_until='domcontentloaded',timeout=15000)
    print('first fractal local link resolved:',href,'HTTP',r.status if r else 0,'title',pg.title()[:50])
    b.close()
