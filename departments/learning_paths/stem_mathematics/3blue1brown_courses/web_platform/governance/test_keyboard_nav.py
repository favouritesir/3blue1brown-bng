import asyncio, json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, channel="chrome")
        page = await b.new_page()
        errs=[]
        page.on('pageerror', lambda e: errs.append(str(e)))
        await page.goto('http://127.0.0.1:8085/courses/linear_algebra/lesson_01.html?v=kb', wait_until='load')
        await page.wait_for_timeout(1000)
        out={}
        # start narration
        await page.click('#btnListenFullArticle')
        await page.wait_for_timeout(300)
        st = lambda: page.evaluate("""() => {const E=window.narrationEngine; return {playing:E.isPlaying,sec:E.currentSectionIdx,item:E.currentItemIdx,vis:document.getElementById('smartAudioPill').classList.contains('is-visible')}}""")
        out['start']=await st()
        # Space toggle twice -> should return to playing state
        await page.keyboard.press('Space'); await page.wait_for_timeout(150)
        out['afterSpace1']=await st()
        await page.keyboard.press('Space'); await page.wait_for_timeout(150)
        out['afterSpace2']=await st()
        # ArrowRight / Left
        await page.keyboard.press('ArrowRight'); await page.wait_for_timeout(150)
        out['afterRight']=await st()
        await page.keyboard.press('ArrowLeft'); await page.wait_for_timeout(150)
        out['afterLeft']=await st()
        # ArrowDown section
        await page.keyboard.press('ArrowDown'); await page.wait_for_timeout(150)
        out['afterDown']=await st()
        # speed +/-
        await page.keyboard.press('+'); await page.wait_for_timeout(100)
        out['ratePlus']=await page.evaluate('window.narrationEngine.playbackRate')
        await page.keyboard.press('-'); await page.wait_for_timeout(100)
        out['rateMinus']=await page.evaluate('window.narrationEngine.playbackRate')
        # End / Home
        await page.keyboard.press('End'); await page.wait_for_timeout(150)
        out['afterEnd']=await st()
        await page.keyboard.press('Home'); await page.wait_for_timeout(150)
        out['afterHome']=await st()
        # Escape closes
        await page.keyboard.press('Escape'); await page.wait_for_timeout(150)
        out['afterEscape']=await st()
        print(json.dumps(out, ensure_ascii=False, indent=2))
        print('ERRORS:', errs[:5])
        await b.close()

asyncio.run(main())
