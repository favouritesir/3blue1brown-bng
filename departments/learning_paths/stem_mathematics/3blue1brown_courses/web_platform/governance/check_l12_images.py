import asyncio, json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, channel="chrome")
        page = await b.new_page()
        bad=[]
        page.on('response', lambda r: bad.append(f'{r.status} {r.url}') if r.status>=400 else None)
        await page.goto('http://127.0.0.1:8085/courses/linear_algebra/lesson_12.html?v=img', wait_until='load')
        await page.wait_for_timeout(1200)
        r = await page.evaluate("""() => Array.from(document.images).filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.getAttribute('src'))""")
        print('BROKEN IMAGES:', json.dumps(r, ensure_ascii=False, indent=2))
        print('BAD RESPONSES:', json.dumps(bad[:20], ensure_ascii=False, indent=2))
        await b.close()

asyncio.run(main())
