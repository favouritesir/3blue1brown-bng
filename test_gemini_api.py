import urllib.request
import urllib.error
import json
import base64

import os
API_KEY = os.environ.get("GEMINI_API_KEY", "")
# Test Gemini endpoint
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

payload = {
    "contents": [{
        "role": "user",
        "parts": [{"text": "Hello, respond with pong"}]
    }]
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("Response:", res["candidates"][0]["content"]["parts"][0]["text"])
except Exception as e:
    print("Error:", e)
