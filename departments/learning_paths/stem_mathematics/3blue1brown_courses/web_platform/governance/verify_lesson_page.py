import asyncio, json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, channel="chrome")
        page = await b.new_page()
        errs = []
        page.on('pageerror', lambda e: errs.append(str(e)))
        await page.goto('http://127.0.0.1:8085/courses/linear_algebra/lesson_05.html?v=verify', wait_until='load')
        await page.wait_for_timeout(1500)
        r = await page.evaluate("""() => {
          const E=window.narrationEngine, M=window.TEACHER_AUDIO_MANIFEST;
          const q=s=>document.querySelectorAll(s).length;
          const secs=E?.sections?.map(s=>({id:s.id,d:s.blocks.length,c:s.cues.length,ok:s.blocks.length===s.cues.length}));
          return {title:document.title, secs, total:E?.sections?.reduce((a,s)=>a+s.cues.length,0),
           allMatch:secs?.every(s=>s.ok), badTypes:(()=>{let n=0;Object.values(M?.sections||{}).forEach(s=>s.cues.forEach(c=>{if(['quiz-block','media-tab'].includes(c.type))n++}));return n})(),
           components:{navbar:q('b1b-navbar .site-nav'),hero:q('b1b-hero-player video'),banner:q('b1b-narration-banner .narration-card'),bookmarks:q('b1b-bookmarks .bookmark-chip'),figures:q('figure.lesson-figure'),quizzes:q('b1b-quiz .quiz-block'),fullscreen:q('b1b-fullscreen .b1b-fs-btn')},
           imagesOk:Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)};
        }""")
        print(json.dumps(r, ensure_ascii=False, indent=2))
        print('PAGE ERRORS:', errs[:5])
        await b.close()

asyncio.run(main())
