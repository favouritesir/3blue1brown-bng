from pathlib import Path
p = Path("temp_phys_topics.py")
s = p.read_text(encoding="utf-8")
fixes = {
    "望远镜": "দূরবীন",
    "superposition": "অধিক্রম",
    "日常 उदाहरण": "দৈনন্দিন উদাহরণ",
    "বল্লমিক্স": "মেকানিক্স",
    "turbulens বা ": "",
    "কোলmogorov": "কোলমোগোরভ",
    "কোলমোগোরভ স্কেলিং ল": "কোলমোগোরভ স্কেলিং নিয়ম",
    "আपेক্ষিকতার": "আপেক্ষিকতার",
    "আपেক্ষিকতার": "আপেক্ষিকতার",
    "আपেक्षिकतার": "আপেক্ষিকতার",
    "这个小": "এই ছোট ",
    "प्रतिक्रिया": "প্রতিক্রিয়া",
}
for a, b in fixes.items():
    s = s.replace(a, b)
p.write_text(s, encoding="utf-8")
# Report any remaining non-Bengali word characters (excluding Python syntax identifiers).
import re
for i, line in enumerate(s.splitlines(), 1):
    words = re.findall(r"[A-Za-z\u0900-\u097F\u4e00-\u9fff]+", line)
    bad = [w for w in words if re.search(r"[\u0900-\u097F\u4e00-\u9fff]", w)]
    if bad:
        print(i, bad)
print("fixed")
