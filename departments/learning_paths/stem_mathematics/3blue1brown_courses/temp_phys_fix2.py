import re
from pathlib import Path
p = Path("temp_phys_topics.py")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
for i, line in enumerate(lines):
    # Replace any Devanagari/Greek/CJK mixed token in the "বেগ সব দর্শকের" line.
    if "বেগ সব দর্শকের" in line:
        lines[i] = "    \"আলোর বেগ সব দর্শকের কাছে একই—এই আপেক্ষিকতার মূল নীম থেকে বিষয়টি বোঝা যায়।\",\n"
        print("patched line", i + 1)
p.write_text("".join(lines), encoding="utf-8")
# final scan
s = p.read_text(encoding="utf-8")
for i, line in enumerate(s.splitlines(), 1):
    for w in re.findall(r"[A-Za-z\u0900-\u097F\u4e00-\u9fff]+", line):
        if re.search(r"[\u0900-\u097F\u4e00-\u9fff]", w) and w not in ("।", "之急"):
            print("REMAIN", i, repr(w))
