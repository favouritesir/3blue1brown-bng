from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    page.goto('http://localhost:8085/sandbox_components/demo_components.html')
    
    # Scroll with offset so it's not hidden by navbar
    page.evaluate('''() => {
        const el = document.querySelector('b1b-interactive-lab');
        const y = el.getBoundingClientRect().top + window.pageYOffset - 80;
        window.scrollTo({top: y, behavior: 'instant'});
    }''')
    page.wait_for_timeout(100)
    page.screenshot(path='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/sandbox_components/ss_interactive_lab_with_header.png')
    
    # Also inspect quote with offset
    page.evaluate('''() => {
        const el = document.querySelector('b1b-quote');
        const y = el.getBoundingClientRect().top + window.pageYOffset - 80;
        window.scrollTo({top: y, behavior: 'instant'});
    }''')
    page.wait_for_timeout(100)
    page.screenshot(path='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/sandbox_components/ss_quote_with_offset.png')

    # Also inspect callouts in light mode
    page.evaluate('''() => {
        document.documentElement.setAttribute('data-theme', 'light');
        document.documentElement.classList.remove('dark');
        const el = document.querySelector('b1b-callout');
        const y = el.getBoundingClientRect().top + window.pageYOffset - 80;
        window.scrollTo({top: y, behavior: 'instant'});
    }''')
    page.wait_for_timeout(100)
    page.screenshot(path='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/sandbox_components/ss_callout_light.png')

    browser.close()
