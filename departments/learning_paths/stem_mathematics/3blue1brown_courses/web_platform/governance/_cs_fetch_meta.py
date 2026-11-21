import json, re, urllib.request

SLUGS = [
    "entropy","cross-entropy","arithmetic-codes","wordle","wordle-2","bitcoin",
    "256-bit-security","epidemic-simulations","hamming-codes","hamming-codes-2",
    "grover","grover-clarification","hanoi-and-sierpinski",
]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")

out = {}
for slug in SLUGS:
    url = "https://www.3blue1brown.com/lessons/" + slug
    try:
        html = fetch(url)
    except Exception as e:
        out[slug] = {"error": str(e)}
        print("ERR", slug, e)
        continue
    info = {"url": url}
    # JSON-LD blocks
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            data = json.loads(m.group(1))
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            t = it.get("@type")
            if t == "VideoObject":
                eu = it.get("embedUrl", "")
                vid = ""
                mm = re.search(r"/embed/([A-Za-z0-9_-]{11})", eu)
                if mm:
                    vid = mm.group(1)
                if not vid:
                    tu = it.get("thumbnailUrl", "")
                    mm = re.search(r"/vi/([A-Za-z0-9_-]{11})", tu)
                    if mm:
                        vid = mm.group(1)
                info["youtube_id"] = vid
                info["title_en"] = it.get("name", "")
                info["description_en"] = it.get("description", "")
                info["date"] = it.get("uploadDate", "")
            elif t == "Article":
                info["article_title"] = it.get("headline", "")
                info["article_desc"] = it.get("description", "")
    # <!--$--> streamed data sometimes carries the real lesson payload; grab source link
    src = re.findall(r'href="(https://github\.com/3b1b/videos/blob/master/[^"]+)"', html)
    if src:
        info["github"] = src[0]
    # first h1 text (strip tags/spans) as fallback title
    out[slug] = info
    print("OK", slug, info.get("youtube_id"), "|", info.get("title_en", "")[:70])

with open("governance/_cs_meta.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("WROTE governance/_cs_meta.json")
