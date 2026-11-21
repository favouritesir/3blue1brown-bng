from playwright.sync_api import sync_playwright
import json
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
topics=json.load(open(W+'/governance/topic_lesson_map.json',encoding='utf-8'))
BASE='http://127.0.0.1:8085/courses/topics/'
with sync_playwright() as pl:
    b=pl.chromium.launch(headless=True,channel='chrome')
    pg=b.new_page(); bad=[]
    for k,v in topics.items():
        r=pg.goto(BASE+k+'.html',wait_until='domcontentloaded',timeout=15000); pg.wait_for_timeout(100)
        n=pg.locator('.topic-lesson').count()
        ok=(r.status==200 and n==len(v['lessons']))
        print(f'{k}: HTTP {r.status} lessons {n}/{len(v["lessons"])} {"OK" if ok else "BAD"}')
        if not ok: bad.append(k)
    r=pg.goto('http://127.0.0.1:8085/index.html',wait_until='domcontentloaded'); pg.wait_for_timeout(300)
    links=pg.locator('a[href^="courses/topics/"]').count()
    print('homepage topic links:',links,'bad topics:',bad)
    b.close()
