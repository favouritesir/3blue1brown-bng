import json
from playwright.sync_api import sync_playwright

def run_audit():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ['error', 'warn'] else None)
        page.on("pageerror", lambda err: console_errors.append(f"[pageerror] {err}"))

        page.goto('http://localhost:8085/sandbox_components/demo_components.html', wait_until='networkidle')

        audit_results = {}
        audit_results['console_logs'] = console_errors

        # 1. Duplication check
        dup_info = page.evaluate("""() => {
            const watchPanel = document.querySelector('b1b-watch-panel');
            const chapterList = document.querySelector('b1b-chapter-list');
            const chapterNav = document.querySelector('b1b-chapter-nav');
            const backToTop = document.querySelectorAll('.jump-to-top-btn, b1b-back-to-top button');
            const searchOverlays = document.querySelectorAll('#searchOverlay, b1b-search-overlay');
            
            return {
                hasWatchPanel: !!watchPanel,
                watchPanelVisible: watchPanel ? getComputedStyle(watchPanel).display : 'none',
                watchPanelDrawerItems: watchPanel ? watchPanel.querySelectorAll('.playlist-item').length : 0,
                hasChapterList: !!chapterList,
                chapterListVisible: chapterList ? getComputedStyle(chapterList).display : 'none',
                chapterListItems: chapterList ? chapterList.querySelectorAll('.playlist-item').length : 0,
                hasChapterNav: !!chapterNav,
                chapterNavRect: chapterNav ? chapterNav.getBoundingClientRect() : null,
                chapterListRect: chapterList ? chapterList.getBoundingClientRect() : null,
                backToTopCount: backToTop.length,
                searchOverlaysCount: searchOverlays.length
            };
        }""")
        audit_results['duplications'] = dup_info

        # 2. Component inspection
        comp_info = page.evaluate("""() => {
            // b1b-media-tab
            const mediaTab = document.querySelector('b1b-media-tab');
            const imgBtn = mediaTab ? mediaTab.querySelector('.tab-btn-img') : null;
            const vidBtn = mediaTab ? mediaTab.querySelector('.tab-btn-vid') : null;
            const imgPane = mediaTab ? mediaTab.querySelector('.pane-image') : null;
            const vidPane = mediaTab ? mediaTab.querySelector('.pane-video') : null;
            const mediaTabInfo = {
                exists: !!mediaTab,
                imgBtnText: imgBtn ? imgBtn.innerText.trim() : null,
                vidBtnText: vidBtn ? vidBtn.innerText.trim() : null,
                imgPaneVisible: imgPane ? getComputedStyle(imgPane).display : null,
                vidPaneVisible: vidPane ? getComputedStyle(vidPane).display : null,
            };

            // b1b-quote
            const quote = document.querySelector('b1b-quote');
            const quoteBox = quote ? quote.querySelector('.chapter-quote') : null;
            const quoteInfo = {
                exists: !!quote,
                hasChapterQuote: !!quoteBox,
                author: quote ? quote.getAttribute('author') : null,
                attribText: quote && quote.querySelector('.attrib') ? quote.querySelector('.attrib').innerText.trim() : null,
                text: quoteBox ? quoteBox.querySelector('p:not(.attrib)').innerText.trim() : null,
                styles: quoteBox ? {
                    fontStyle: getComputedStyle(quoteBox.querySelector('p')).fontStyle,
                    display: getComputedStyle(quoteBox).display,
                    border: getComputedStyle(quoteBox).borderLeft
                } : null
            };

            // b1b-callout contrast & overflow
            const callouts = Array.from(document.querySelectorAll('b1b-callout')).map(c => {
                const inner = c.querySelector('.callout');
                const title = c.querySelector('.callout-title');
                const body = c.querySelector('.callout-body');
                return {
                    type: c.getAttribute('type'),
                    title: title ? title.innerText.trim() : '',
                    bg: inner ? getComputedStyle(inner).backgroundColor : null,
                    borderColor: inner ? getComputedStyle(inner).borderLeftColor : null,
                    titleColor: title ? getComputedStyle(title).color : null,
                    bodyColor: body ? getComputedStyle(body).color : null,
                    hasBody: !!body,
                    isBodyInside: inner && body ? inner.contains(body) : false,
                    innerScrollWidth: inner ? inner.scrollWidth : 0,
                    innerClientWidth: inner ? inner.clientWidth : 0
                };
            });

            // b1b-quiz
            const quizzes = Array.from(document.querySelectorAll('b1b-quiz')).map(q => {
                const block = q.querySelector('.quiz-block');
                const options = Array.from(q.querySelectorAll('.quiz-option')).map(opt => ({
                    text: opt.innerText.trim(),
                    hasKatex: !!opt.querySelector('.katex')
                }));
                const feedback = q.querySelector('.quiz-feedback');
                return {
                    question: q.getAttribute('question'),
                    optionsCount: options.length,
                    options: options,
                    feedbackExists: !!feedback
                };
            });

            // b1b-interactive-lab
            const lab = document.querySelector('b1b-interactive-lab');
            const vizWrapper = lab ? lab.querySelector('.viz-wrapper') : null;
            const svgContainer = lab ? lab.querySelector('.viz-svg-container') : null;
            const svgPlane = lab ? lab.querySelector('#interactiveSvgPlane') : null;
            const controls = lab ? lab.querySelector('.viz-controls') : null;
            const info = lab ? lab.querySelector('.viz-info') : null;
            const labInfo = {
                exists: !!lab,
                hasVizWrapper: !!vizWrapper,
                isEverythingInsideVizWrapper: vizWrapper ? (
                    vizWrapper.contains(svgContainer) && 
                    vizWrapper.contains(controls) && 
                    vizWrapper.contains(info)
                ) : false,
                svgPlaneRect: svgPlane ? svgPlane.getBoundingClientRect() : null,
                wrapperRect: vizWrapper ? vizWrapper.getBoundingClientRect() : null
            };

            return {
                mediaTab: mediaTabInfo,
                quote: quoteInfo,
                callouts: callouts,
                quizzes: quizzes,
                lab: labInfo
            };
        }""")
        audit_results['components_dark'] = comp_info

        # Toggle to light mode and check contrast again
        page.evaluate("""() => {
            document.documentElement.setAttribute('data-theme', 'light');
            document.documentElement.classList.remove('dark');
        }""")
        page.wait_for_timeout(200)

        light_callouts = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('b1b-callout')).map(c => {
                const inner = c.querySelector('.callout');
                const title = c.querySelector('.callout-title');
                const body = c.querySelector('.callout-body');
                return {
                    type: c.getAttribute('type'),
                    title: title ? title.innerText.trim() : '',
                    bg: inner ? getComputedStyle(inner).backgroundColor : null,
                    borderColor: inner ? getComputedStyle(inner).borderLeftColor : null,
                    titleColor: title ? getComputedStyle(title).color : null,
                    bodyColor: body ? getComputedStyle(body).color : null
                };
            });
        }""")
        audit_results['components_light_callouts'] = light_callouts

        # Test media tab toggle
        page.evaluate("""() => {
            document.documentElement.setAttribute('data-theme', 'dark');
        }""")
        page.locator('b1b-media-tab .tab-btn-vid').click()
        page.wait_for_timeout(200)

        media_tab_toggle_test = page.evaluate("""() => {
            const mediaTab = document.querySelector('b1b-media-tab');
            const imgPane = mediaTab ? mediaTab.querySelector('.pane-image') : null;
            const vidPane = mediaTab ? mediaTab.querySelector('.pane-video') : null;
            return {
                imgPaneDisplay: imgPane ? getComputedStyle(imgPane).display : null,
                vidPaneDisplay: vidPane ? getComputedStyle(vidPane).display : null,
                vidHasSrc: vidPane && vidPane.querySelector('video') ? vidPane.querySelector('video').src : null
            };
        }""")
        audit_results['media_tab_toggle_test'] = media_tab_toggle_test

        # Test Quiz interaction and KaTeX render in feedback
        quiz_test = page.evaluate("""() => {
            const q = document.querySelector('b1b-quiz');
            const checkBtn = q.querySelector('.quiz-check-btn');
            const revealBtn = q.querySelector('.quiz-reveal-btn');
            const opt = q.querySelectorAll('.quiz-option')[2]; // correct is 2
            opt.click();
            checkBtn.click();
            const feedback = q.querySelector('.quiz-feedback');
            return {
                checkBtnDisabled: checkBtn.disabled,
                feedbackVisible: feedback.classList.contains('show'),
                feedbackText: feedback.innerText,
                feedbackKatexRendered: !!feedback.querySelector('.katex'),
                feedbackHtml: feedback.innerHTML
            };
        }""")
        audit_results['quiz_test'] = quiz_test

        # Mobile responsiveness check at 375px
        page.set_viewport_size({'width': 375, 'height': 812})
        page.wait_for_timeout(200)

        mobile_audit = page.evaluate("""() => {
            const docWidth = document.documentElement.offsetWidth;
            const scrollWidth = document.documentElement.scrollWidth;
            const elementsOverflowing = [];
            document.querySelectorAll('*').forEach(el => {
                if (el.scrollWidth > docWidth + 5) {
                    elementsOverflowing.push({
                        tag: el.tagName,
                        id: el.id,
                        className: el.className,
                        scrollWidth: el.scrollWidth,
                        clientWidth: el.clientWidth
                    });
                }
            });
            return {
                docWidth,
                scrollWidth,
                hasHorizontalOverflow: scrollWidth > docWidth,
                overflowingElements: elementsOverflowing.slice(0, 10)
            };
        }""")
        audit_results['mobile_audit'] = mobile_audit

        # Screenshots
        page.screenshot(path='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/sandbox_components/audit_mobile_dark.png')
        
        page.set_viewport_size({'width': 1280, 'height': 900})
        page.screenshot(path='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/sandbox_components/audit_desktop_dark.png')

        page.evaluate("""() => {
            document.documentElement.setAttribute('data-theme', 'light');
            document.documentElement.classList.remove('dark');
        }""")
        page.wait_for_timeout(200)
        page.screenshot(path='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/sandbox_components/audit_desktop_light.png')

        browser.close()

    with open('departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/sandbox_components/audit_results.json', 'w', encoding='utf-8') as f:
        json.dump(audit_results, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    run_audit()
