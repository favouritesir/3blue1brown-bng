# -*- coding: utf-8 -*-
"""One-off cleanup of mixed-script drafting artifacts in the generator."""
from pathlib import Path

P = Path(__file__).with_name("build_number_theory.py")
s = P.read_text(encoding="utf-8")

REPLACEMENTS = {
    "মডulo": "মডুলো",
    "মডুলো ১₀": "মডুলো ১০",
    "হ্যाँ": "হ্যাঁ",
    "গ্যালakty": "গ্যালাক্সি",
    "সংখ্যা grouping করার": "সংখ্যা ভাগ করার",
    "অনুপাত becomes ১/φ(N)": "অনুপাত হয় ১/φ(N)",
    "π(chiff)": "π(x)",
    "মিল无可 Nash": "মিলে না",
    "আছে와": "আছে আর",
    "আঁका": "আঁকা",
    "ভগ্নাংশ_clear করে": "ভগ্নাংশ সরল করে",
    "একই সম chwrt হলে": "একই সম হলে",
    "প্রতিটি শাখার চর্বি বাড়তে": "প্রতিটি শাখার আকার বাড়তে",
    "কোনো কি Sharma-অনুমান": "কোনো অনুমান",
    "অল্ফান্ন অধ্যায়": "অন্য অধ্যায়",
    "ধারারhoot": "ধারার",
    "অসীম schw ধারা": "অসীম ধারা",
    "অসীম many মৌলিকের": "অসীম সংখ্যক মৌলিকের",
    "চিহ্নেরalternation": "চিহ্নের পর্যায়ক্রম",
    "আরτικ étude arctan-এর": "আর arctan-এর",
    "এক共同推动 করে": "একসাথে এগিয়ে গিয়ে",
    "আরও一顿一笔": "আরও এক কথা",
    "মূলবिन्दু": "মূলবিন্দু",
    "বिन्दু": "বিন্দু",
    "পরিমeyer": "পরিমেয়",
    "জMatching": "মিলছে",
    "যোগfade দিতে": "যোগ দিতে",
    "गাউসিয়ান": "গাউসিয়ান",
    " tooth ": " দাঁত ",
    "একটি tooth": "একটি দাঁত",
}

applied = []
for old, new in REPLACEMENTS.items():
    if old in s:
        n = s.count(old)
        s = s.replace(old, new)
        applied.append((old, new, n))

P.write_text(s, encoding="utf-8")
print("applied %d replacements" % len(applied))
for old, new, n in applied:
    print("  %-28s -> %-24s x%d" % (old[:28], new[:24], n))
