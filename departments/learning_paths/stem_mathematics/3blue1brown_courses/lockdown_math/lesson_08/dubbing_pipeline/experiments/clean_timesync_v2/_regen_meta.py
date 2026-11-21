import importlib.util
import json
from pathlib import Path

P = Path(__file__).resolve().parent / "build_lock08_clean.py"
s = importlib.util.spec_from_file_location("b", str(P))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

vend = m.video_duration(m.ORIGINAL_VIDEO)
usable = vend - m.LEAD_IN_SEC - m.TAIL_MARGIN_SEC
target = (usable / 4) / m.TARGET_NATURAL_SCALE
src, _ = m.load_source_cues()
befores = [105.0, 99.9, 100.0, 106.3]

for idx, (c, bf) in enumerate(zip(src, befores), start=1):
    base = m.sanitize(c["text"])
    pool = m.EXPANSION_POOL.get(c["section"], m.DEFAULT_EXPANSIONS)
    rate = bf / max(len(base), 1)
    need = max(250, int((target - bf) / max(rate, 0.01)))
    txt, n = m.pick_append(pool, 0, need, m.MAX_APPENDED_SENTENCES)
    final = m.sanitize(base + " " + txt)
    entry = {
        "id": idx,
        "section": c["section"],
        "natural_before": bf,
        "sentences_added": n,
        "final_chars": len(final),
        "target_sec": round(target, 3),
    }
    meta = m.RAW_DIR / f"expand_meta_{idx:03d}.json"
    meta.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    print(idx, "sent", n, "chars", len(final), "->", meta.name)
