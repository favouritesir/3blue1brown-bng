from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
BASE='http://127.0.0.1:8085/courses/topics/'
with sync_playwright() as pl:
    b=pl.chromium.launch(headless=True,channel='chrome')
    pg=b.new_page(); bad=[]
    for topic in ['fractals','group-theory','number-theory','geometry','puzzles','why-pi','topology','analysis']:
        pg.goto(BASE+topic+'.html',wait_until='domcontentloaded',timeout=15000); pg.wait_for_timeout(100)
        links=pg.locator('a.topic-lesson').evaluate_all('els=>els.map(e=>e.getAttribute("href"))')
        local=[l for l in links if l and l.startswith('../')]
        # click first local link via playwright (proper resolution)
        if local:
            pg.locator('a.topic-lesson').first.click(); pg.wait_for_load_state('domcontentloaded',timeout=15000)
            print(f'{topic}: {len(local)} local links -> first click URL {pg.url.split("/")[-2:]}, title {pg.title()[:45]}')
            pg.goto(BASE+topic+'.html',wait_until='domcontentloaded')
    b.close()
