import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
script = HERE / "build_lock04_clean.py"
extra = json.loads((HERE / "_extra_pool.json").read_text(encoding="utf-8"))
src = script.read_text(encoding="utf-8")

for sec, sentences in extra.items():
    pat = re.compile(r'("' + re.escape(sec) + r'": \[\n)(.*?)(\n    \],)', re.S)
    m = pat.search(src)
    if not m:
        raise SystemExit(f"pool not found: {sec}")
    added = "".join('        ' + json.dumps(s, ensure_ascii=False) + ',\n' for s in sentences)
    src = src[:m.start(2)] + m.group(2) + added + src[m.end(2):]

script.write_text(src, encoding="utf-8")
print("inserted", {k: len(v) for k, v in extra.items()})
