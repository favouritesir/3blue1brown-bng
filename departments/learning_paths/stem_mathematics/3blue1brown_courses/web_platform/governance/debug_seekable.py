from playwright.sync_api import sync_playwright
with sync_playwright() as pl:
    b=pl.chromium.launch(headless=True,channel='chrome')
    pg=b.new_page()
    pg.goto('http://127.0.0.1:8085/courses/linear_algebra/lesson_01.html',wait_until='domcontentloaded'); pg.wait_for_timeout(500)
    pg.eval_on_selector('#mainVideo','e=>e.play().catch(()=>{})'); pg.wait_for_timeout(1200)
    print(pg.evaluate("""() => { const v=document.getElementById('mainVideo');
      const rng=(r)=>{let o=[];for(let i=0;i<r.length;i++)o.push([r.start(i),r.end(i)]);return o};
      return {src:v.currentSrc.split('/').pop(),readyState:v.readyState,duration:v.duration,
              seekable:rng(v.seekable), buffered:rng(v.buffered), networkState:v.networkState};
    }"""))
    b.close()
