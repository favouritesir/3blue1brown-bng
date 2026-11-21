import urllib.request
import urllib.error
import json

import os
API_KEY = os.environ.get("GEMINI_API_KEY", "")

for m in ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-2.5-flash"]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={API_KEY}"
    payload = {"contents": [{"role": "user", "parts": [{"text": "say hi"}]}]}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            print(f"{m}: OK ->", res["candidates"][0]["content"]["parts"][0]["text"].strip())
            break
    except urllib.error.HTTPError as e:
        print(f"{m}: {e.code} {e.reason}")
    except Exception as e:
        print(f"{m}: {e}")
