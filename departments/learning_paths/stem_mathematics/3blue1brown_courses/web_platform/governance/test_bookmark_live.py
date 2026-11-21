from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8085/'
# find a page with bookmarks
import glob, os, re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
for p in sorted(glob.glob(W+'/courses/*/lesson_*.html')):
    s=open(p,encoding='utf-8',errors='ignore').read()
    if 'bookmark-chip' in s or '<b1b-bookmark ' in s:
        rel=os.path.relpath(p,W).replace('\\','/')
        break
print('testing:',rel)
with sync_playwright() as pl:
    b=pl.chromium.launch(headless=True,channel='chrome')
    pg=b.new_page(); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(BASE+rel,wait_until='domcontentloaded',timeout=15000); pg.wait_for_timeout(700)
    print('chips:',pg.locator('.bookmark-chip').count())
    print('videos:',pg.locator('video').count(),'ids:',pg.eval_on_selector_all('video','els=>els.map(e=>e.id)'))
    print('mainVideo?',pg.locator('#mainVideo').count(),'heroLocalBox?',pg.locator('#heroLocalBox video').count())
    chips=pg.locator('.bookmark-chip')
    if chips.count()>1:
        before=pg.eval_on_selector_all('video','els=>els.map(e=>e.currentTime)')
        chips.nth(1).click(); pg.wait_for_timeout(600)
        after=pg.eval_on_selector_all('video','els=>els.map(e=>e.currentTime)')
        print('onclick:',chips.nth(1).get_attribute('onclick'))
        print('before:',before,'after:',after)
    print('errors:',errs[:3])
    b.close()
