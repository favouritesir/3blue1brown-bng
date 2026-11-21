# -*- coding: utf-8 -*-
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _topology_all_scripts import LESSONS

BAD = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN = "চিত্র প্রদর্শনী"
GOV = os.path.dirname(os.path.abspath(__file__))
problems = []

for n in (1, 2, 3):
    lesson = LESSONS[n]
    meta, secs = lesson["meta"], lesson["sections"]
    snap = json.load(open(os.path.join(GOV, meta["dom_snapshot"]), encoding="utf-8"))
    snap_types = {s["id"]: [b["type"] for b in s["blocks"]] for s in snap["sections"]}
    total = 0
    print("=" * 70, "\nLESSON", n)
    for sid, sec in secs.items():
        types = [c["type"] for c in sec["cues"]]
        total += len(types)
        if types != meta["expected_types"][sid]:
            problems.append(f"L{n} {sid}: type mismatch\n  {types}\n  {meta['expected_types'][sid]}")
        if types != snap_types.get(sid):
            problems.append(f"L{n} {sid}: DOM snapshot type mismatch\n  {types}\n  {snap_types.get(sid)}")
        if len(types) != meta["counts"][sid]:
            problems.append(f"L{n} {sid}: count {len(types)} != {meta['counts'][sid]}")
        if [c["index"] for c in sec["cues"]] != list(range(len(types))):
            problems.append(f"L{n} {sid}: indices not 0-based")
        for c in sec["cues"]:
            bad = BAD.findall(c["tts"])
            if bad:
                problems.append(f"L{n} {sid}[{c['index']}]: BAD CHARS {bad!r} :: {c['tts']}")
            if FORBIDDEN in c["tts"]:
                problems.append(f"L{n} {sid}[{c['index']}]: forbidden label")
            if c["type"] == "figure":
                sentences = [s for s in c["tts"].split("।") if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    problems.append(f"L{n} {sid}[{c['index']}]: figure has {len(sentences)} sentences")
        print(f"  {sid:<20} {len(types):>2} cues OK")
    if total != meta["total"]:
        problems.append(f"L{n}: total {total} != {meta['total']}")
    spoken = [c["tts"] for s in secs.values() for c in s["cues"]]
    if len(spoken) != len(set(spoken)):
        problems.append(f"L{n}: duplicate scripts")
        from collections import Counter
        for t, cnt in Counter(spoken).items():
            if cnt > 1:
                problems.append(f"L{n} DUP x{cnt}: {t[:60]}")
    print(f"  TOTAL {total} cues, {len(set(spoken))} unique scripts")

print("=" * 70)
if problems:
    print(f"PROBLEMS: {len(problems)}")
    for p in problems:
        print(" -", p)
    raise SystemExit(1)
print("ALL SCRIPT CHECKS PASSED")
