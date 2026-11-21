import asyncio
import json
import urllib.request
import websockets

CDP_HTTP = "http://127.0.0.1:9222"

def get_open_tabs():
    """Fetch all open browser tabs from Brave CDP"""
    try:
        req = urllib.request.urlopen(f"{CDP_HTTP}/json")
        tabs = json.loads(req.read().decode())
        return [t for t in tabs if t.get("type") == "page"]
    except Exception as e:
        print(f"[!] Error fetching tabs: {e}")
        return []

async def execute_cdp_script(ws_url, expression):
    """Execute raw JS directly on a tab in < 50ms"""
    async with websockets.connect(ws_url) as ws:
        msg = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True
            }
        }
        await ws.send(json.dumps(msg))
        res = await ws.recv()
        data = json.loads(res)
        return data.get("result", {}).get("result", {}).get("value")

async def inject_fast_prompt(tab_id_or_title_keyword, prompt_text, selector="textarea, div[contenteditable='true']"):
    """Instantly inject a prompt and trigger submission"""
    tabs = get_open_tabs()
    target_tab = None
    for t in tabs:
        if tab_id_or_title_keyword.lower() in t.get("title", "").lower() or tab_id_or_title_keyword in t.get("id", ""):
            target_tab = t
            break
            
    if not target_tab:
        print(f"[!] Target tab matching '{tab_id_or_title_keyword}' not found.")
        return False

    ws_url = target_tab.get("webSocketDebuggerUrl")
    js_code = f"""
    (() => {{
        const el = document.querySelector("{selector}");
        if (!el) return {{ success: false, error: "Selector not found" }};
        el.focus();
        
        // Instant text injection
        if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {{
            el.value = {json.dumps(prompt_text)};
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
        }} else {{
            document.execCommand('selectAll', false, null);
            document.execCommand('insertText', false, {json.dumps(prompt_text)});
        }}
        
        // Find and click submit button
        const btn = document.querySelector("button[type='submit'], button[aria-label*='Send'], button[aria-label*='Generate'], button[data-testid*='send']");
        if (btn) {{
            btn.click();
            return {{ success: true, submitted: true }};
        }}
        return {{ success: true, submitted: false, message: "Injected, but submit button needs manual click or exact selector" }};
    }})();
    """
    res = await execute_cdp_script(ws_url, js_code)
    print(f"[*] Injected into '{target_tab.get('title')}': {res}")
    return res

async def create_new_tab(url):
    """Open a new tab in Brave via CDP and return tab info"""
    try:
        encoded_url = urllib.parse.quote(url, safe=":/?#[]@!$&'()*+,;=-_.~")
        req = urllib.request.urlopen(f"{CDP_HTTP}/json/new?{encoded_url}")
        return json.loads(req.read().decode())
    except Exception as e:
        print(f"[!] Error creating tab for {url}: {e}")
        return None

async def navigate_or_attach(url_keyword, target_url):
    """Find existing tab or open a fresh one for AI Studio / Flow Music"""
    tabs = get_open_tabs()
    for t in tabs:
        if url_keyword.lower() in t.get("url", "").lower():
            return t
    return await create_new_tab(target_url)

if __name__ == "__main__":
    tabs = get_open_tabs()
    print("Available Brave Tabs:")
    for i, t in enumerate(tabs):
        print(f" [{i}] {t.get('title')} -> {t.get('url')}")

