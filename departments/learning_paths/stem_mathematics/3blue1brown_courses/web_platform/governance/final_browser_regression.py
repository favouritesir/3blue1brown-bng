"""Gate 2: live browser regression across one lesson per course + mobile viewport."""
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8085/'
pages=['courses/linear_algebra/lesson_01.html','courses/calculus/lesson_01.html',
       'courses/neural_networks/lesson_01.html','courses/probability/lesson_01.html',
       'courses/differential_equations/lesson_01.html','courses/lockdown_math/lesson_01.html']
out=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,channel='chrome')
    for path in pages:
        ctx=browser.new_context(viewport={'width':1400,'height':900})
        pg=ctx.new_page(); errs=[]
        pg.on('pageerror',lambda e:errs.append('pageerror: '+str(e)))
        pg.on('console',lambda m:errs.append('console: '+m.text) if m.type=='error' and '404' not in m.text and 'Failed to load resource' not in m.text else None)
        try:
            resp=pg.goto(BASE+path,wait_until='domcontentloaded',timeout=15000)
            pg.wait_for_timeout(600)
            arts=pg.locator('article.article').count()
            quizzes=pg.locator('.b1b-quiz, b1b-quiz').count()
            stepper=pg.locator('.navbar-stepper, .stepper, [class*=stepper]').first
            stepper_txt=stepper.inner_text() if stepper.count() else 'n/a'
            out.append((path,resp.status if resp else 0,arts,quizzes,len(errs),stepper_txt[:30],errs[:2]))
        except Exception as e:
            out.append((path,'ERR',0,0,1,'', [str(e)[:80]]))
        ctx.close()
    # mobile viewport check on one page
    m=browser.new_context(viewport={'width':390,'height':844})
    mp=m.new_page(); mp.goto(BASE+pages[0],wait_until='domcontentloaded',timeout=15000)
    mp.wait_for_timeout(400)
    sw=mp.evaluate('document.documentElement.scrollWidth')
    out.append(('MOBILE 390px', 'scrollWidth='+str(sw), '', '', 0, '', []))
    m.close(); browser.close()
for row in out: print(row)
