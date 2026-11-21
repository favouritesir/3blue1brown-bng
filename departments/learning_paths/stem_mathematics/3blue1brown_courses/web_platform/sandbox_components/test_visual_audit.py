from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    page.goto('http://localhost:8085/sandbox_components/demo_components.html')

    # Dark mode read mode
    page.screenshot(path='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/sandbox_components/ss_read_dark.png')

    # Switch to Watch Mode
    page.evaluate("() => document.querySelector('button[data-mode=\"watch\"]').click()")
    page.wait_for_timeout(200)
    page.screenshot(path='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/sandbox_components/ss_watch_dark.png')

    # Switch to Light Mode
    page.evaluate("() => document.getElementById('themeBtn').click()")
    page.wait_for_timeout(200)
    page.screenshot(path='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/sandbox_components/ss_watch_light.png')

    # Switch back to Read Mode in Light
    page.evaluate("() => document.querySelector('button[data-mode=\"read\"]').click()")
    page.wait_for_timeout(200)
    page.screenshot(path='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/sandbox_components/ss_read_light.png')

    # Check components
    comp_checks = page.evaluate('''() => {
        const mediaTab = document.querySelector('b1b-media-tab');
        const quote = document.querySelector('b1b-quote');
        const callouts = document.querySelectorAll('b1b-callout');
        const quizzes = document.querySelectorAll('b1b-quiz');
        const lab = document.querySelector('b1b-interactive-lab');

        return {
            mediaTabHtml: mediaTab ? mediaTab.outerHTML.substring(0, 300) : null,
            quoteHtml: quote ? quote.outerHTML : null,
            callout0Html: callouts[0] ? callouts[0].outerHTML.substring(0, 300) : null,
            quiz0Options: quizzes[0] ? Array.from(quizzes[0].querySelectorAll('.quiz-option')).map(o => o.innerText.trim()) : [],
            labHtml: lab ? lab.outerHTML.substring(0, 400) : null
        };
    }''')
    import pprint
    pprint.pprint(comp_checks)
    browser.close()
