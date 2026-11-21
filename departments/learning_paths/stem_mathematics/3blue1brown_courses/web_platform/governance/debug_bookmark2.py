from playwright.sync_api import sync_playwright
with sync_playwright() as pl:
    b=pl.chromium.launch(headless=True,channel='chrome')
    pg=b.new_page(); logs=[]
    pg.on('console',lambda m:logs.append(m.text) if ('SET' in m.text or 'SEEK' in m.text) else None)
    pg.goto('http://127.0.0.1:8085/courses/linear_algebra/lesson_01.html',wait_until='domcontentloaded'); pg.wait_for_timeout(700)
    chips=pg.locator('.bookmark-chip')
    print('chip onclicks:',[chips.nth(i).get_attribute('onclick') for i in range(chips.count())])
    # monkeypatch currentTime setter with stack
    pg.evaluate("""() => {
      const v=document.getElementById('mainVideo');
      const d=Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype,'currentTime');
      Object.defineProperty(v,'currentTime',{
        get(){return d.get.call(v)},
        set(x){ console.log('SET currentTime',x,'stack',new Error().stack.split('\\n').slice(1,4).join(' | ')); d.set.call(v,x); }
      });
      v.addEventListener('seeking',()=>console.log('SEEKING event '+v.currentTime));
    }""")
    pg.eval_on_selector('#mainVideo','e=>e.play().catch(()=>{})'); pg.wait_for_timeout(800)
    print('--- clicking chip 2 (should be 160) ---')
    chips.nth(2).click(); pg.wait_for_timeout(1200)
    print('final video time:',pg.eval_on_selector('#mainVideo','e=>e.currentTime'))
    for l in logs[-15:]: print(' ',l)
    b.close()
