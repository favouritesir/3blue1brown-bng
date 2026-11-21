import asyncio, json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, channel="chrome")
        page = await b.new_page()
        for n in ['01','05','09','15']:
            await page.goto(f'http://127.0.0.1:8085/courses/linear_algebra/lesson_{n}.html?v=step', wait_until='domcontentloaded')
            await page.wait_for_timeout(500)
            r = await page.evaluate("""() => ({
              step: document.querySelector('b1b-stepper .nav-step-label')?.textContent.trim(),
              links: Array.from(document.querySelectorAll('b1b-stepper a.nav-step-btn')).map(a=>a.getAttribute('href')),
              bottomPrev: document.querySelector('b1b-chapter-nav .prev-card')?.getAttribute('href'),
              bottomNext: document.querySelector('b1b-chapter-nav .next-card')?.getAttribute('href')
            })""")
            print(n, json.dumps(r, ensure_ascii=False))
        await b.close()

asyncio.run(main())
