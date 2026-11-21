import asyncio
import json
import websockets

async def get_transcript():
    ws_url = "ws://127.0.0.1:9222/devtools/page/926EA96618E8B4F20649CE4AB3BE4A34"
    async with websockets.connect(ws_url) as ws:
        expr = """
        (async () => {
            const tracks = ytInitialPlayerResponse.captions.playerCaptionsTracklistRenderer.captionTracks;
            const enTrack = tracks.find(t => t.languageCode === 'en');
            const res = await fetch(enTrack.baseUrl);
            const text = await res.text();
            return {
                url: enTrack.baseUrl,
                status: res.status,
                headers: Array.from(res.headers.entries()),
                textLen: text.length,
                textSample: text.slice(0, 500)
            };
        })()
        """
        msg = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {"expression": expr, "returnByValue": True, "awaitPromise": True}
        }
        await ws.send(json.dumps(msg))
        res = json.loads(await ws.recv())
        val = res.get("result", {}).get("result", {}).get("value", {})
        print(json.dumps(val, indent=2))

if __name__ == "__main__":
    asyncio.run(get_transcript())
