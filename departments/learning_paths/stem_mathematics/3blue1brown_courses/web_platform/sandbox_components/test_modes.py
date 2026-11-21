from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page()
    page.goto('http://localhost:8085/sandbox_components/demo_components.html')

    # Read mode state
    read_state = page.evaluate('''() => {
        const bodyClass = document.body.className;
        const watchPanel = document.querySelector('b1b-watch-panel');
        const watchPanelInner = watchPanel ? watchPanel.querySelector('.watch-mode-panel') : null;
        const chapterList = document.querySelector('b1b-chapter-list');
        const chapterNav = document.querySelector('b1b-chapter-nav');
        const readMode = document.querySelector('.read-mode');
        const heroPlayer = document.querySelector('b1b-hero-player');

        return {
            mode: bodyClass,
            heroPlayerDisplay: heroPlayer ? getComputedStyle(heroPlayer).display : 'none',
            readModeDisplay: readMode ? getComputedStyle(readMode).display : 'none',
            watchPanelDisplay: watchPanel ? getComputedStyle(watchPanel).display : 'none',
            watchPanelInnerDisplay: watchPanelInner ? getComputedStyle(watchPanelInner).display : 'none',
            chapterNavDisplay: chapterNav ? getComputedStyle(chapterNav).display : 'none',
            chapterListDisplay: chapterList ? getComputedStyle(chapterList).display : 'none',
        };
    }''')
    print('Read mode state:', read_state)

    # Click watch mode button via JS click
    page.evaluate('''() => {
        const btn = document.querySelector('button[data-mode="watch"]');
        if (btn) btn.click();
    }''')
    page.wait_for_timeout(200)

    watch_state = page.evaluate('''() => {
        const bodyClass = document.body.className;
        const watchPanel = document.querySelector('b1b-watch-panel');
        const watchPanelInner = watchPanel ? watchPanel.querySelector('.watch-mode-panel') : null;
        const chapterList = document.querySelector('b1b-chapter-list');
        const chapterNav = document.querySelector('b1b-chapter-nav');
        const readMode = document.querySelector('.read-mode');
        const heroPlayer = document.querySelector('b1b-hero-player');

        return {
            mode: bodyClass,
            heroPlayerDisplay: heroPlayer ? getComputedStyle(heroPlayer).display : 'none',
            readModeDisplay: readMode ? getComputedStyle(readMode).display : 'none',
            watchPanelDisplay: watchPanel ? getComputedStyle(watchPanel).display : 'none',
            watchPanelInnerDisplay: watchPanelInner ? getComputedStyle(watchPanelInner).display : 'none',
            chapterNavDisplay: chapterNav ? getComputedStyle(chapterNav).display : 'none',
            chapterListDisplay: chapterList ? getComputedStyle(chapterList).display : 'none',
        };
    }''')
    print('Watch mode state:', watch_state)
    browser.close()
