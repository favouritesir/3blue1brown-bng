import asyncio, json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, channel="chrome")
        page = await b.new_page()
        errs = []
        page.on('pageerror', lambda e: errs.append('PAGE: ' + str(e)))
        bad = []
        page.on('response', lambda r: bad.append(f'{r.status} {r.url}') if r.status >= 400 else None)
        await page.goto('http://127.0.0.1:8085/index.html', wait_until='load')
        await page.wait_for_timeout(1500)
        r = await page.evaluate("""() => {
          const links = Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href'));
          return {
            title: document.title,
            linkCount: links.length,
            boardLinks: links.filter(h=>h && h.includes('board')),
            lessonLinks: links.filter(h=>h && h.includes('lesson_')).length,
            seriesCards: document.querySelectorAll('.series-card, b1b-series-card').length,
            htmlLen: document.body.innerText.length
          };
        }""")
        print(json.dumps(r, ensure_ascii=False, indent=2))
        print('PAGE ERRORS:', errs[:10])
        print('BAD RESPONSES:', bad[:25], 'total', len(bad))
        await b.close()

asyncio.run(main())
