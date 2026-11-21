import asyncio, json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, channel="chrome")
        for n in ['11','12']:
            page = await b.new_page()
            errs=[]
            page.on('pageerror', lambda e, errs=errs: errs.append(str(e)))
            await page.goto(f'http://127.0.0.1:8085/courses/linear_algebra/lesson_{n}.html?v=verify', wait_until='domcontentloaded')
            await page.wait_for_timeout(900)
            r = await page.evaluate("""() => {
              const E=window.narrationEngine;
              const secs=E?.sections?.map(s=>({id:s.id,d:s.blocks.length,c:s.cues.length,ok:s.blocks.length===s.cues.length}));
              return {title:document.title.slice(0,55), secs, total:E?.sections?.reduce((a,s)=>a+s.cues.length,0),
               allMatch:secs?.every(s=>s.ok), step:document.querySelector('b1b-stepper .nav-step-label')?.textContent.trim(),
               figs:document.querySelectorAll('.lesson-figure').length, quizzes:document.querySelectorAll('.quiz-block').length,
               imagesOk:Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)};
            }""")
            print(n, json.dumps(r, ensure_ascii=False), 'ERRS', errs[:2])
            await page.close()
        await b.close()

asyncio.run(main())
