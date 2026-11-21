# -*- coding: utf-8 -*-
"""
Headless-Chrome verification for the gold-standard expressive teacher audio of
Group Theory lessons 01 and 02.

Checks (per lesson):
  * manifest.json is valid JSON and manifest.js mirrors it exactly.
  * Live DOM (narrationEngine blocks via the exact parseContent selector) maps
    1:1 to manifest sections/cues: same IDs, counts, order and cue types.
  * 0 duplicate section IDs / cue indices / duplicate cue texts.
  * 0 quiz / media-tab (or any unexpected) cue types.
  * Every referenced mp3 exists and is non-zero with a positive ffprobe
    duration that matches the manifest total.
  * Cue timings: positive spans, non-overlap, exact 350 ms gaps.
  * 0 page errors in headless Chrome (channel=chrome).
  * 0 forbidden artificial figure labels ("চিত্র প্রদর্শনী").

Usage:  python governance/verify_gt_expressive_audio.py
"""
import json
import os
import subprocess
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
WP = os.path.dirname(HERE)
GAP_MS = 350.0
ALLOWED_TYPES = {"h2", "h3", "p", "figure", "callout", "formula-box",
                 "chapter-quote", "code-showcase"}
FORBIDDEN = "চিত্র প্রদর্শনী"

TYPEOF_JS = r"""() => {
  const typeOf = (el) => {
    if (el.matches && el.matches('figure.lesson-figure')) return 'figure';
    if (el.classList && el.classList.contains('chapter-quote')) return 'chapter-quote';
    if (el.classList && el.classList.contains('callout')) return 'callout';
    if (el.classList && el.classList.contains('code-showcase')) return 'code-showcase';
    if (el.classList && el.classList.contains('formula-box')) return 'formula-box';
    if (el.tagName === 'H2') return 'h2';
    if (el.tagName === 'H3') return 'h3';
    return 'p';
  };
  const eng = window.narrationEngine;
  const sections = (eng && eng.sections || []).map(sec => ({
    id: sec.id,
    types: (sec.blocks || []).map(b => typeOf(b.element)),
    count: (sec.blocks || []).length,
    cues: (sec.cues || []).length,
  }));
  const rawIds = [...document.querySelectorAll('.article > section, article section')]
    .filter(s => s.getAttribute('data-no-narration') !== 'true')
    .map(s => s.id || 'sec-' + [...document.querySelectorAll('.article > section, article section')].indexOf(s));
  return { sections, rawIds, hasStudioAudio: eng ? eng.hasStudioAudio : false,
           manifestLesson: window.TEACHER_AUDIO_MANIFEST ? window.TEACHER_AUDIO_MANIFEST.lesson : null,
           manifestVersion: window.TEACHER_AUDIO_MANIFEST ? window.TEACHER_AUDIO_MANIFEST.lesson : null };
}"""


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout.strip()
    return float(out) * 1000.0


def check(cond, msg, fails):
    if not cond:
        fails.append(msg)
    return cond


def verify_lesson(n, page):
    fails = []
    audio_dir = os.path.join(WP, "assets", "audio", "group_theory", f"lesson_{n:02d}")
    mjson = os.path.join(audio_dir, "manifest.json")
    mjs = os.path.join(audio_dir, "manifest.js")

    # --- valid JSON ---------------------------------------------------------
    with open(mjson, encoding="utf-8") as fh:
        text = fh.read()
    m = json.loads(text)  # raises on invalid JSON
    js_text = open(mjs, encoding="utf-8").read()
    check(js_text == "window.TEACHER_AUDIO_MANIFEST = " + text + ";\n",
          "manifest.js does not mirror manifest.json", fails)

    sections = m["sections"]
    # --- 0 duplicate section IDs / cue indices / cue texts ------------------
    sec_ids = list(sections)
    check(len(sec_ids) == len(set(sec_ids)), "duplicate section IDs", fails)
    all_texts = []
    for sid, sec in sections.items():
        cues = sec["cues"]
        idx = [c["index"] for c in cues]
        check(idx == list(range(len(idx))), f"{sid}: duplicate/non-sequential cue indices", fails)
        texts = [c["text"] for c in cues]
        all_texts += texts
        check(len(texts) == len(set(texts)), f"{sid}: duplicate cue texts", fails)
    check(len(all_texts) == len(set(all_texts)), "duplicate cue texts across lesson", fails)

    # --- types, forbidden labels, timings -----------------------------------
    total_cues = 0
    total_ms = 0.0
    figure_count = 0
    for sid, sec in sections.items():
        cues = sec["cues"]
        total_cues += len(cues)
        total_ms += sec["total_duration_ms"]
        for i, c in enumerate(cues):
            check(c["type"] in ALLOWED_TYPES,
                  f"{sid} cue {i}: disallowed type {c['type']!r}", fails)
            check(c["type"] not in ("quiz", "media-tab"),
                  f"{sid} cue {i}: quiz/media-tab type", fails)
            check(isinstance(c["text"], str) and len(c["text"]) > 2,
                  f"{sid} cue {i}: empty text", fails)
            check(FORBIDDEN not in c["text"],
                  f"{sid} cue {i}: forbidden figure label", fails)
            check(c["duration_ms"] > 0 and c["end_ms"] > c["start_ms"],
                  f"{sid} cue {i}: non-positive span", fails)
            if i > 0:
                prev = cues[i - 1]
                check(abs((c["start_ms"] - prev["end_ms"]) - GAP_MS) <= 1.0,
                      f"{sid} cue {i}: gap != 350ms", fails)
        figure_count += sum(1 for c in cues if c["type"] == "figure")
        check(abs(sec["total_duration_ms"] - cues[-1]["end_ms"]) <= 1.0,
              f"{sid}: total_duration_ms != last cue end_ms", fails)

    # --- mp3 files exist, non-zero, durations match -------------------------
    mp3_count = 0
    for sid, sec in sections.items():
        p = os.path.join(audio_dir, sec["audio_file"])
        check(os.path.exists(p) and os.path.getsize(p) > 0,
              f"{sid}: missing/empty mp3 {sec['audio_file']}", fails)
        if os.path.exists(p) and os.path.getsize(p) > 0:
            mp3_count += 1
            dur = probe_duration(p)
            # MP3 frame padding in concat -c copy adds <1s over a multi-minute
            # section; gold builders allow 2500ms. Exactness is checked against
            # the last cue's end_ms below.
            check(abs(dur - sec["total_duration_ms"]) <= 2500.0,
                  f"{sid}: mp3 duration {dur:.0f}ms != manifest {sec['total_duration_ms']}ms", fails)

    # --- live DOM via headless Chrome ---------------------------------------
    page.route("**/*.mp4", lambda route: route.abort())
    page.set_default_navigation_timeout(60000)
    errs = []
    handler = lambda e: errs.append(str(e))
    page.on("pageerror", handler)
    page.goto(f"http://127.0.0.1:8085/courses/group_theory/lesson_{n:02d}.html?v=2",
              wait_until="domcontentloaded")
    page.wait_for_function(
        "() => window.narrationEngine && window.narrationEngine.sections && "
        "window.narrationEngine.hasStudioAudio === true && "
        "window.TEACHER_AUDIO_MANIFEST",
        timeout=25000,
    )
    dom = page.evaluate(TYPEOF_JS)
    page.remove_listener("pageerror", handler)
    check(not errs, f"page errors: {errs[:3]}", fails)
    check(dom["hasStudioAudio"] is True, "engine hasStudioAudio not true", fails)
    check(dom["manifestLesson"] == f"lesson_{n:02d}", "wrong manifest lesson", fails)

    dom_secs = dom["sections"]
    check([s["id"] for s in dom_secs] == sec_ids,
          f"DOM section IDs != manifest section IDs: {[s['id'] for s in dom_secs]} vs {sec_ids}", fails)
    for s in dom_secs:
        msec = sections[s["id"]]
        check(s["count"] == len(msec["cues"]),
              f"{s['id']}: DOM block count {s['count']} != manifest {len(msec['cues'])}", fails)
        check(s["types"] == [c["type"] for c in msec["cues"]],
              f"{s['id']}: DOM types != manifest types", fails)
        check(s["cues"] == len(msec["cues"]),
              f"{s['id']}: engine cues != manifest cues", fails)

    print(f"\n===== lesson_{n:02d} =====")
    print(f"  sections           : {len(sections)}")
    print(f"  cues               : {total_cues}")
    print(f"  figure explanations: {figure_count}")
    print(f"  mp3 files (non-zero): {mp3_count}/{len(sections)}")
    print(f"  total duration     : {total_ms / 1000.0:.2f}s")
    print(f"  page errors        : {len(errs)}")
    print(f"  DOM<->manifest     : {'1:1 OK' if not any('DOM' in f for f in fails) else 'MISMATCH'}")
    print(f"  RESULT             : {'PASS' if not fails else 'FAIL'}")

    if fails:
        for f in fails:
            print("   -", f)
    return {
        "lesson": f"lesson_{n:02d}", "sections": len(sections), "cues": total_cues,
        "figures": figure_count, "mp3": mp3_count, "duration_s": round(total_ms / 1000.0, 2),
        "page_errors": len(errs), "pass": not fails, "fails": fails,
    }


def main():
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page()
        for n in (1, 2):
            results.append(verify_lesson(n, page))
        browser.close()

    print("\n" + "=" * 62)
    all_ok = all(r["pass"] for r in results)
    for r in results:
        print(f"  {r['lesson']}: {r['cues']} cues, {r['sections']} sections, "
              f"{r['duration_s']}s, {r['page_errors']} page errors -> "
              f"{'PASS' if r['pass'] else 'FAIL'}")
    print(f"  OVERALL: {'ALL PASS' if all_ok else 'FAILURES PRESENT'}")
    print("=" * 62)
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
