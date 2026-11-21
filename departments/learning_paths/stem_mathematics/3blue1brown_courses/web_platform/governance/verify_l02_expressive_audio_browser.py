# -*- coding: utf-8 -*-
"""
Browser verification of the regenerated Lesson 02 expressive teacher audio.

Headless Chrome (channel="chrome") against the LIVE lesson page over HTTP:
  * window.TEACHER_AUDIO_MANIFEST present, valid JSON, matches manifest.json on disk
  * narrationEngine parsed exactly the 4 narrated sections (no data-no-narration)
  * DOM<->manifest 1:1 per section (cue types + counts, in order, from the engine's
    live parsed blocks, i.e. the actual rendered DOM)
  * runtime binding: section ids, audio_file, block/cue lengths align
  * 0 duplicate canonical cue texts (DOM) and spoken texts (manifest)
  * 0 quiz / media-tab cue types anywhere
  * NO cue text begins with the artificial label "চিত্র প্রদর্শনী"
  * every mp3 reachable over HTTP (200) and non-zero on disk (ffprobe)
  * cue timings: positive, zero overlaps, exact 350 ms gaps, total matches
  * 0 page errors

Run with the local web server up (port 8085):
    python governance/verify_l02_expressive_audio_browser.py
"""
import json
import os
import subprocess

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8085/courses/linear_algebra/lesson_02.html?v=verify"
HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "linear_algebra", "lesson_02")
HTTP_AUDIO_BASE = "http://127.0.0.1:8085/assets/audio/linear_algebra/lesson_02/"
# section id -> exact expected cue count
EXPECTED = {
    "sec-basis": 22,
    "sec-linear-combinations": 9,
    "sec-span": 25,
    "sec-dependence": 10,
}
FORBIDDEN = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"
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


def main():
    errors = []
    page_errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page()
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(URL, wait_until="load")
        # Wait for the engine to parse the DOM AND finish binding the fetched
        # manifest (hasStudioAudio + cues populated) — reactive, no fixed sleep.
        page.wait_for_function(
            "() => window.narrationEngine && window.narrationEngine.sections && "
            "window.narrationEngine.sections.length >= 4 && "
            "window.narrationEngine.hasStudioAudio === true && "
            "window.narrationEngine.sections.every(s => (s.cues || []).length > 0) && "
            "window.TEACHER_AUDIO_MANIFEST",
            timeout=25000,
        )
        data = page.evaluate(VERIFY_JS)
        audio_http = {}
        for sec in (data["manifest"] or {}).get("sections", {}).values():
            af = sec["audio_file"]
            resp = page.request.get(HTTP_AUDIO_BASE + af)
            audio_http[af] = (resp.status, len(resp.body()))
        browser.close()

    print("=" * 76)
    print("L02 BROWSER VERIFICATION (headless Chrome, channel='chrome')")
    print("=" * 76)

    mf = data["manifest"]
    check(isinstance(mf, dict) and isinstance(mf.get("sections"), dict),
          "window.TEACHER_AUDIO_MANIFEST parsed as valid JSON object", errors)
    check(not page_errors, f"0 page errors (got {len(page_errors)})", errors)
    for pe in page_errors:
        print("      PAGE ERROR: " + pe)
    check(data.get("hasStudioAudio") is True,
          "narrationEngine successfully fetched/bound the studio manifest", errors)
    sections = mf["sections"] if mf else {}

    # Exact section keys.
    check(set(sections) == set(EXPECTED),
          f"manifest sections exactly {sorted(EXPECTED)} (got {sorted(sections)})", errors)

    # DOM <-> manifest 1:1 per narrated section (types + counts, in order).
    print("\nDOM <-> manifest 1:1 per narrated section:")
    for sid, expected_n in EXPECTED.items():
        dom_types = data["domBlocks"].get(sid, [])
        man_types = [c["type"] for c in sections.get(sid, {}).get("cues", [])]
        ok = (len(dom_types) == expected_n and len(man_types) == expected_n
              and dom_types == man_types)
        check(ok, f"{sid}: DOM {len(dom_types)} == manifest {len(man_types)} "
                  f"== {expected_n}, cue types identical", errors)
        if not ok:
            print(f"      DOM={dom_types}\n      MAN={man_types}")

    # Non-narrated sections must not leak into DOM blocks.
    leaked = set(data["domBlocks"]) - set(EXPECTED)
    check(not leaked, f"no non-narrated section leaked into DOM blocks "
                      f"(leaked={sorted(leaked)})", errors)

    # Runtime engine binding.
    print("\nRuntime narration-engine binding:")
    rt = {r["id"]: r for r in data["runtime"]}
    for sid, expected_n in EXPECTED.items():
        r = rt.get(sid)
        ok = bool(r) and r["blocks"] == expected_n and r["cues"] == expected_n
        check(ok, f"{sid}: engine blocks={r and r['blocks']}, "
                  f"cues={r and r['cues']}, expected {expected_n}", errors)
        af = sections.get(sid, {}).get("audio_file", "")
        check(bool(r) and af and r["audioFile"].endswith(af),
              f"{sid}: engine audioFile points to {af}", errors)

    # Duplicate texts (DOM canonical + manifest spoken).
    canonical = data["canonical"]
    spoken = [c["text"] for s in sections.values() for c in s.get("cues", [])]
    check(len(canonical) == len(set(canonical)),
          f"0 duplicate canonical cue texts (DOM {len(canonical)} cues, "
          f"{len(canonical)-len(set(canonical))} dupes)", errors)
    check(len(spoken) == len(set(spoken)),
          f"0 duplicate spoken cue texts (manifest {len(spoken)} cues, "
          f"{len(spoken)-len(set(spoken))} dupes)", errors)

    # No quiz / media-tab cue types.
    man_types_all = [c["type"] for s in sections.values() for c in s.get("cues", [])]
    check(not data["forbidden"] and not any(t in FORBIDDEN for t in man_types_all),
          "0 quiz/media-tab cue types (DOM and manifest)", errors)

    # NO artificial "চিত্র প্রদর্শনী" label at the start of any cue.
    bad_prefix_spoken = [c["text"] for c in spoken if c.lstrip().startswith(FORBIDDEN_PREFIX)]
    bad_prefix_dom = [t for t in canonical if t.lstrip().startswith(FORBIDDEN_PREFIX)]
    any_prefix = [t for s in sections.values() for c in s.get("cues", [])
                  if FORBIDDEN_PREFIX in c["text"]]
    check(not bad_prefix_spoken and not bad_prefix_dom and not any_prefix,
          f'0 cue texts begin with/contain "চিত্র প্রদর্শনী" '
          f'(spoken={len(bad_prefix_spoken)}, dom={len(bad_prefix_dom)}, '
          f'anywhere={len(any_prefix)})', errors)

    # MP3 reachable (HTTP 200) + non-zero on disk.
    print("\nMP3 files (HTTP + on-disk ffprobe):")
    for sid, sec in sections.items():
        af = sec["audio_file"]
        path = os.path.join(AUDIO_DIR, af)
        status, served_bytes = audio_http.get(af, (None, 0))
        on_disk = os.path.exists(path) and os.path.getsize(path) > 0
        disk_bytes = os.path.getsize(path) if on_disk else 0
        dur = 0.0
        if on_disk:
            try:
                dur = probe_duration(path)
            except Exception:
                dur = 0.0
        ok = status == 200 and served_bytes > 0 and on_disk and dur > 0
        check(ok, f"{af}: HTTP {status} ({served_bytes} served B), "
                  f"{disk_bytes} disk B, {dur/1000.0:.2f}s", errors)

    # Cue timings: positive, no overlap, exact gaps, total matches.
    print("\nCue timings (positive / no overlap / exact 350 ms gaps / total):")
    for sid, sec in sections.items():
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
        check(ok and total_ok,
              f"{sid}: {len(cues)} cues, total {sec['total_duration_ms']:.1f} ms "
              f"(last end {cues[-1]['end_ms']:.1f})", errors)

    # manifest.json on disk is valid JSON and matches window object.
    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        disk_mf = json.load(fh)
    check(disk_mf == mf, "manifest.json on disk == window.TEACHER_AUDIO_MANIFEST", errors)

    total_cues = sum(len(s["cues"]) for s in sections.values())
    total_ms = sum(s["total_duration_ms"] for s in sections.values())
    figures = sum(1 for s in sections.values() for c in s["cues"] if c["type"] == "figure")
    print("\n" + "=" * 76)
    print(f"TOTALS: {total_cues}/66 cues, {total_ms/1000.0:.2f}s, "
          f"{figures} figure explanations")
    print(f"PER SECTION: " + ", ".join(
        f"{sid}={len(sections[sid]['cues'])}" for sid in EXPECTED))
    if errors:
        print(f"VERIFICATION FAILED ({len(errors)} issue(s)):")
        for e in errors:
            print("  - " + e)
    else:
        print("VERIFICATION PASSED: all checks green.")
    print("=" * 76)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
