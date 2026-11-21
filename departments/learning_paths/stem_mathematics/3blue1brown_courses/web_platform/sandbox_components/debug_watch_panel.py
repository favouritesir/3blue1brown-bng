from playwright.sync_api import sync_playwright
import pprint

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page()
    page.goto('http://localhost:8085/sandbox_components/demo_components.html')
    
    info = page.evaluate("""() => {
        const watchPanel = document.querySelector('b1b-watch-panel');
        const watchModePanel = watchPanel ? watchPanel.querySelector('.watch-mode-panel') : null;
        const slotted = watchPanel ? watchPanel.querySelector('[slot="playlist"]') : null;
        
        return {
            watchPanelDisplay: watchPanel ? getComputedStyle(watchPanel).display : null,
            watchModePanelDisplay: watchModePanel ? getComputedStyle(watchModePanel).display : null,
            slottedDisplay: slotted ? getComputedStyle(slotted).display : null,
            slottedParent: slotted ? slotted.parentElement.tagName : null,
            watchPanelChildren: watchPanel ? Array.from(watchPanel.children).map(c => ({
                tag: c.tagName,
                class: c.className,
                display: getComputedStyle(c).display
            })) : []
        };
    }""")
    pprint.pprint(info)
    browser.close()
