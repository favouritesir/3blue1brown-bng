"""Final L05 live check after stale-agent page overwrite."""
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,channel='chrome')
    pg=b.new_page(); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    r=pg.goto('http://127.0.0.1:8085/courses/lockdown_math/lesson_05.html',wait_until='domcontentloaded',timeout=15000)
    pg.wait_for_timeout(800)
    arts=pg.locator('article.article').count()
    quizzes=pg.locator('b1b-quiz').count()
    # narration engine status
    try:
        ne=pg.evaluate("() => window.narrationEngine ? 'present' : (window.narrationEngine ? 'ok' : 'missing')")
    except Exception as e:
        ne='err:'+str(e)[:40]
    manifest_v=pg.evaluate("() => document.querySelector('script[src*=manifest]')?.getAttribute('src')")
    print('HTTP',r.status if r else 0,'article',arts,'quizzes',quizzes,'narrationEngine',ne,'manifest',manifest_v,'pageerrors',errs)
    b.close()
