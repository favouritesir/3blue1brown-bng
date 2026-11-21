# -*- coding: utf-8 -*-
"""
Browser verification of the regenerated Fractals L01..L04 expressive teacher
audio. Headless Chrome (channel="chrome") against the LIVE lesson pages over
HTTP, one browser page per lesson.

Per lesson:
  * window.TEACHER_AUDIO_MANIFEST present, valid JSON, == manifest.json on disk
  * narrationEngine parsed exactly the narrated sections (no data-no-narration
    leak); hasStudioAudio === true; every section bound with cues > 0
  * DOM <-> manifest 1:1 per section: cue types + counts in exact order, from
    the engine's live parsed blocks (the actual rendered DOM)
  * 0 duplicate canonical cue texts (DOM) and spoken texts (manifest)
  * 0 quiz / media-tab cue types anywhere
  * NO cue text begins with / contains the artificial label "চিত্র প্রদর্শনী"
  * all spoken scripts free of Latin letters / TeX / raw hyphens
  * figure cues are genuine 2-4 sentence explanations
  * every mp3 reachable over HTTP (200) + non-zero on disk + positive ffprobe
  * cue timings positive, zero overlaps, exact 350 ms gaps, total matches
  * 0 page errors

Run with the local web server up (port 8085):
    python governance/verify_fractals_expressive_build.py
"""
import json
import os
import re
import subprocess

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
AUDIO_ROOT = os.path.join(WORKSPACE, "assets", "audio", "fractals")
BASE_URL = "http://127.0.0.1:8085/courses/fractals/lesson_{:02d}.html?v=verify"
AUDIO_BASE = "http://127.0.0.1:8085/assets/audio/fractals/lesson_{:02d}/"

# Authoritative DOM structure extracted via narration_engine selector.
EXPECTED = {
    1: {"sec-intro": 7, "sec-newton": 6, "sec-complex": 6,
        "sec-basins": 6, "sec-boundary": 6, "sec-conclusion": 3},
    2: {"sec-iteration": 6, "sec-holomorphic": 6, "sec-newton-again": 6,
        "sec-parameter": 5, "sec-mandelbrot": 6, "sec-escape": 5,
        "sec-conclusion": 3},
    3: {"sec-misconception": 5, "sec-dimension": 5, "sec-scaling": 6,
        "sec-not-selfsimilar": 6, "sec-coast": 5, "sec-conclusion": 3},
    4: {"sec-intro": 5, "sec-construction": 6, "sec-limit": 5,
        "sec-useful": 5, "sec-paradox": 5, "sec-conclusion": 3},
}
TOTAL = {1: 34, 2: 37, 3: 30, 4: 29}
FORBIDDEN = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
GAP_MS = 350.0

VERIFY_JS = r"""() => {
  const out = { manifest: null, domBlocks: {}, runtime: [], forbidden: [], canonical: [] };
  out.manifest = window.TEACHER_AUDIO_MANIFEST || null;
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
  (eng && eng.sections || []).forEach(sec => {
    const types = [];
    (sec.blocks || []).forEach(b => {
      const t = typeOf(b.element);
      types.push(t);
      out.canonical.push(b.text);
      if (['quiz-block','media-tab','quiz','media-tab-caption'].includes(t))
        out.forbidden.push(t);
    });
    out.domBlocks[sec.id] = types;
    out.runtime.push({
      id: sec.id,
      blocks: (sec.blocks || []).length,
      cues: (sec.cues || []).length,
      audioFile: sec.audioFile || ''
    });
  });
  out.hasStudioAudio = !!(eng && eng.hasStudioAudio);
  return out;
}"""


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout.strip()
    return float(out) * 1000.0


def check(cond, label, errors):
    print(("  [OK]  " if cond else "  [FAIL]") + " " + label)
    if not cond:
        errors.append(label)


def verify_lesson(lesson, browser):
    errors = []
    page_errors = []
    expected = EXPECTED[lesson]
    audio_dir = os.path.join(AUDIO_ROOT, f"lesson_{lesson:02d}")
    page = browser.new_page()
    page.on("pageerror", lambda e: page_errors.append(str(e)))
    page.goto(BASE_URL.format(lesson), wait_until="load")
    page.wait_for_function(
        "() => window.narrationEngine && window.narrationEngine.sections && "
        f"window.narrationEngine.sections.length >= {len(expected)} && "
        "window.narrationEngine.hasStudioAudio === true && "
        "window.narrationEngine.sections.every(s => (s.cues || []).length > 0) && "
        "window.TEACHER_AUDIO_MANIFEST",
        timeout=25000,
    )
    data = page.evaluate(VERIFY_JS)
    mf = data["manifest"] or {}
    audio_http = {}
    for sec in mf.get("sections", {}).values():
        af = sec["audio_file"]
        resp = page.request.get(AUDIO_BASE.format(lesson) + af)
        audio_http[af] = (resp.status, len(resp.body()))
    page.close()

    print("\n" + "=" * 78)
    print(f"FRACTALS L{lesson:02d} BROWSER VERIFICATION (headless Chrome, channel='chrome')")
    print("=" * 78)
    check(isinstance(mf, dict) and isinstance(mf.get("sections"), dict),
          "window.TEACHER_AUDIO_MANIFEST parsed as valid JSON object", errors)
    check(not page_errors, f"0 page errors (got {len(page_errors)})", errors)
    for pe in page_errors:
        print("      PAGE ERROR: " + pe)
    check(data.get("hasStudioAudio") is True,
          "narrationEngine successfully fetched/bound the studio manifest", errors)
    sections = mf["sections"] if mf else {}

    # Exact section keys (canonical DOM ids only — this course has no aliases).
    check(set(sections) == set(expected),
          f"manifest sections exactly {len(expected)} canonical DOM keys "
          f"(got {len(sections)})", errors)
    for sid in expected:
        check(sections.get(sid, {}).get("section_id") == sid,
              f"{sid}: section_id field correct", errors)

    # DOM <-> manifest 1:1 per narrated section (types + counts, in order).
    print("\nDOM <-> manifest 1:1 per narrated section:")
    for sid, expected_n in expected.items():
        dom_types = data["domBlocks"].get(sid, [])
        man_types = [c["type"] for c in sections.get(sid, {}).get("cues", [])]
        ok = (len(dom_types) == expected_n and len(man_types) == expected_n
              and dom_types == man_types)
        check(ok, f"{sid}: DOM {len(dom_types)} == manifest {len(man_types)} "
                  f"== {expected_n}, cue types identical", errors)
        if not ok:
            print(f"      DOM={dom_types}\n      MAN={man_types}")

    total_canonical = sum(len(sections[s]["cues"]) for s in expected if s in sections)
    check(total_canonical == TOTAL[lesson],
          f"{TOTAL[lesson]}/{TOTAL[lesson]} canonical cues (got {total_canonical})", errors)

    leaked = set(data["domBlocks"]) - set(expected)
    check(not leaked, f"no non-narrated section leaked into DOM blocks "
                      f"(leaked={sorted(leaked)})", errors)

    print("\nRuntime narration-engine binding:")
    rt = {r["id"]: r for r in data["runtime"]}
    for sid, expected_n in expected.items():
        r = rt.get(sid)
        ok = bool(r) and r["blocks"] == expected_n and r["cues"] == expected_n
        check(ok, f"{sid}: engine blocks={r and r['blocks']}, "
                  f"cues={r and r['cues']}, expected {expected_n}", errors)
        af = sections.get(sid, {}).get("audio_file", "")
        check(bool(r) and af and r["audioFile"].endswith(af),
              f"{sid}: engine audioFile points to {af}", errors)

    canonical = data["canonical"]
    spoken = [c["text"] for s in expected for c in sections.get(s, {}).get("cues", [])]
    check(len(canonical) == len(set(canonical)),
          f"0 duplicate canonical cue texts (DOM {len(canonical)} cues, "
          f"{len(canonical) - len(set(canonical))} dupes)", errors)
    check(len(spoken) == len(set(spoken)),
          f"0 duplicate spoken cue texts (manifest {len(spoken)} canonical cues, "
          f"{len(spoken) - len(set(spoken))} dupes)", errors)

    man_types_all = [c["type"] for s in sections.values() for c in s.get("cues", [])]
    check(not data["forbidden"] and not any(t in FORBIDDEN for t in man_types_all),
          "0 quiz/media-tab cue types (DOM and manifest)", errors)

    bad_spoken = [c for c in spoken if c.lstrip().startswith(FORBIDDEN_PREFIX)]
    bad_dom = [t for t in canonical if t.lstrip().startswith(FORBIDDEN_PREFIX)]
    anywhere = [c["text"] for s in sections.values() for c in s.get("cues", [])
                if FORBIDDEN_PREFIX in c["text"]]
    check(not bad_spoken and not bad_dom and not anywhere,
          f'0 cue texts begin with/contain "চিত্র প্রদর্শনী" '
          f'(spoken={len(bad_spoken)}, dom={len(bad_dom)}, anywhere={len(anywhere)})', errors)

    bad_chars = [c for c in spoken if BAD_CHARS.search(c)]
    check(not bad_chars, f"0 spoken scripts with Latin/TeX/raw-hyphen characters "
                         f"(got {len(bad_chars)})", errors)
    bad_figs = []
    for sid in expected:
        for c in sections.get(sid, {}).get("cues", []):
            if c["type"] == "figure":
                n = len([s for s in c["text"].split("।") if s.strip()])
                if not (2 <= n <= 4):
                    bad_figs.append((sid, c["index"], n))
    check(not bad_figs, f"all figure cues are 2-4 sentence explanations "
                        f"(bad={bad_figs})", errors)

    print("\nMP3 files (HTTP + on-disk ffprobe):")
    for sid in expected:
        sec = sections[sid]
        af = sec["audio_file"]
        path = os.path.join(audio_dir, af)
        status, served_bytes = audio_http.get(af, (None, 0))
        on_disk = os.path.exists(path) and os.path.getsize(path) > 0
        disk_bytes = os.path.getsize(path) if on_disk else 0
        dur = 0.0
        if on_disk:
            try:
                dur = probe_duration(path)
            except Exception:  # noqa: BLE001
                dur = 0.0
        ok = status == 200 and served_bytes > 0 and on_disk and dur > 0
        check(ok, f"{af}: HTTP {status} ({served_bytes} served B), "
                  f"{disk_bytes} disk B, {dur / 1000.0:.2f}s", errors)
        check(abs(dur - sec["total_duration_ms"]) <= 2500.0,
              f"{af}: ffprobe {dur:.1f} ms ~ manifest {sec['total_duration_ms']:.1f} ms", errors)

    print("\nCue timings (positive / no overlap / exact 350 ms gaps / total):")
    for sid in expected:
        sec = sections[sid]
        cues = sec.get("cues", [])
        ok = True
        prev_end = None
        for i, c in enumerate(cues):
            if c["duration_ms"] <= 0 or c["end_ms"] <= c["start_ms"]:
                ok = False
                break
            if i > 0:
                if c["start_ms"] < prev_end:
                    ok = False
                    break
                if abs((c["start_ms"] - prev_end) - GAP_MS) > 1.0:
                    ok = False
                    break
            prev_end = c["end_ms"]
        total_ok = bool(cues) and abs(sec["total_duration_ms"] - cues[-1]["end_ms"]) <= 1.0
        check(ok and total_ok, f"{sid}: {len(cues)} cues, total "
                               f"{sec['total_duration_ms']:.1f} ms "
                               f"(last end {cues[-1]['end_ms']:.1f})", errors)

    with open(os.path.join(audio_dir, "manifest.json"), encoding="utf-8") as fh:
        disk_mf = json.load(fh)
    check(disk_mf == mf, "manifest.json on disk == window.TEACHER_AUDIO_MANIFEST", errors)

    total_ms = sum(sections[s]["total_duration_ms"] for s in expected)
    figures = sum(1 for s in expected for c in sections[s]["cues"] if c["type"] == "figure")
    print("\n" + "-" * 78)
    print(f"L{lesson:02d} TOTALS: {total_canonical}/{TOTAL[lesson]} canonical cues, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations, "
          f"{len(sections)} manifest keys")
    print("-" * 78)
    return errors, total_canonical, total_ms, figures


def main():
    all_errors = []
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        for lesson in range(1, 5):
            try:
                errs, cues, ms, figs = verify_lesson(lesson, browser)
            except Exception as exc:  # noqa: BLE001 - a failed lesson must not hide others
                print(f"\nL{lesson:02d} VERIFICATION EXCEPTION: {exc}")
                errs, cues, ms, figs = [f"L{lesson:02d} exception: {exc}"], 0, 0.0, 0
            all_errors.extend(errs)
            results.append((lesson, cues, ms, figs, len(errs)))
        browser.close()

    print("\n" + "=" * 78)
    print("FRACTALS COURSE — FINAL VERIFICATION SUMMARY")
    print("=" * 78)
    grand_cues = grand_figs = 0
    grand_ms = 0.0
    for lesson, cues, ms, figs, nerr in results:
        grand_cues += cues
        grand_ms += ms
        grand_figs += figs
        print(f"  Lesson {lesson:02d}: {cues:>2} cues, {ms / 1000.0:>7.2f}s, "
              f"{figs} figures, {nerr} issue(s)")
    print(f"  TOTAL: {grand_cues}/130 cues, {grand_ms / 1000.0:.2f}s, "
          f"{grand_figs} figure explanations")
    if all_errors:
        print(f"VERIFICATION FAILED ({len(all_errors)} issue(s)):")
        for e in all_errors:
            print("  - " + e)
        return 1
    print("VERIFICATION PASSED: all checks green for all 4 lessons.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
