# -*- coding: utf-8 -*-
"""
Browser verification of the rebuilt Lesson 05 expressive teacher audio.

Checks in a real (headless Chromium) browser against the LIVE lesson page:
  * window.TEACHER_AUDIO_MANIFEST is present and parses as valid JSON
  * narrationEngine parsed exactly the 3 narrated sections (no data-no-narration)
  * DOM<->manifest 1:1 per section (cue types + counts, in order)
  * runtime binding: section ids, audio_file, cue/blocks lengths align
  * 0 duplicate canonical cue texts (DOM texts with KaTeX <annotation> markers)
  * 0 duplicate spoken cue texts in the manifest
  * 0 quiz / media-tab cue types anywhere
  * every mp3 is reachable over HTTP (200) and non-zero on disk (ffprobe)
  * cue timings: positive durations, zero overlaps, exact 350 ms gaps,
    total_duration_ms equals the last cue's end_ms

Run with the local web_server up (port 8123):
    python governance/verify_l05_browser.py
"""
import json
import os
import subprocess

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8123/courses/linear_algebra/lesson_05.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "linear_algebra", "lesson_05")
EXPECTED = {
    "sec_01_3d_space": 14,
    "sec_02_matrix3x3": 15,
    "sec_03_determinant3d": 9,
}
FORBIDDEN = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
GAP_MS = 350.0

VERIFY_JS = r"""() => {
  const out = { manifest: null, domBlocks: {}, runtime: [], forbidden: [], canonical: [] };

  out.manifest = window.TEACHER_AUDIO_MANIFEST || null;

  // Replicate narration_engine.parseContent() to get DOM blocks + canonical text.
  const sectionElements = document.querySelectorAll('.article > section, article section');
  sectionElements.forEach((secEl, sIdx) => {
    if (secEl.getAttribute('data-no-narration') === 'true') return;
    const secId = secEl.id || ('sec-' + sIdx);
    const blocks = [];
    const nodes = secEl.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box');
    nodes.forEach(node => {
      if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) return;
      let type;
      if (node.tagName === 'H2') type = 'h2';
      else if (node.tagName === 'H3') type = 'h3';
      else if (node.classList.contains('chapter-quote')) type = 'chapter-quote';
      else if (node.classList.contains('callout')) type = 'callout';
      else if (node.matches('figure.lesson-figure')) type = 'figure';
      else if (node.classList.contains('code-showcase')) type = 'code-showcase';
      else if (node.classList.contains('formula-box')) type = 'formula-box';
      else type = 'p';

      const clone = node.cloneNode(true);
      clone.querySelectorAll('.katex').forEach(k => {
        const ann = k.querySelector('annotation[encoding="application/x-tex"]');
        const tex = ann ? ann.textContent.trim() : '';
        const marker = document.createElement('span');
        marker.textContent = '<annotation>' + tex + '</annotation>';
        k.replaceWith(marker);
      });
      let text = clone.innerText || clone.textContent || '';
      text = text.replace(/\u00a0/g, ' ').replace(/\n+/g, ' ').replace(/[ \t]+/g, ' ').trim();
      if (text && text.length > 2) {
        blocks.push({ type, text });
        out.canonical.push(text);
        if (['quiz-block','media-tab','quiz','media-tab-caption'].includes(type))
          out.forbidden.push(type);
      }
    });
    out.domBlocks[secId] = blocks;
  });

  // Runtime narration-engine state (how the page actually binds the manifest).
  (window.narrationEngine && window.narrationEngine.sections || []).forEach(sec => {
    out.runtime.push({
      id: sec.id,
      blocks: (sec.blocks || []).length,
      cues: (sec.cues || []).length,
      audioFile: sec.audioFile || ''
    });
  });
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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page()
        page.goto(URL, wait_until="load")
        page.wait_for_function(
            "() => window.narrationEngine && window.narrationEngine.sections && "
            "window.narrationEngine.sections.length >= 3 && window.TEACHER_AUDIO_MANIFEST",
            timeout=20000,
        )
        data = page.evaluate(VERIFY_JS)
        # The page does not auto-fetch MP3s on load (Audio loads on playback),
        # so actively request each one over HTTP from the browser context.
        audio_http = {}
        for sec in (data["manifest"] or {}).get("sections", {}).values():
            af = sec["audio_file"]
            resp = page.request.get(
                "http://127.0.0.1:8123/assets/audio/linear_algebra/lesson_05/" + af)
            audio_http[af] = (resp.status, len(resp.body()))
        browser.close()

    print("=" * 70)
    print("L05 BROWSER VERIFICATION")
    print("=" * 70)

    # 1. Valid manifest object.
    mf = data["manifest"]
    check(isinstance(mf, dict) and isinstance(mf.get("sections"), dict),
          "window.TEACHER_AUDIO_MANIFEST parsed as valid JSON object", errors)
    sections = mf["sections"] if mf else {}

    # 2. Exact section keys.
    check(set(sections) == set(EXPECTED),
          f"manifest sections exactly {sorted(EXPECTED)} (got {sorted(sections)})", errors)

    # 3. DOM<->manifest 1:1 per narrated section.
    print("\nDOM <-> manifest 1:1 per narrated section:")
    for sid, expected_n in EXPECTED.items():
        dom_types = [b["type"] for b in data["domBlocks"].get(sid, [])]
        man_types = [c["type"] for c in sections.get(sid, {}).get("cues", [])]
        ok = (len(dom_types) == expected_n and len(man_types) == expected_n
              and dom_types == man_types)
        check(ok, f"{sid}: DOM {len(dom_types)} == manifest {len(man_types)} "
                  f"== {expected_n}, types identical", errors)
        if not ok:
            print(f"      DOM={dom_types}\n      MAN={man_types}")

    # 4. Non-narrated sections must not leak into DOM blocks.
    leaked = set(data["domBlocks"]) - set(EXPECTED)
    check(not leaked, f"no non-narrated section leaked into DOM blocks "
                      f"(leaked={sorted(leaked)})", errors)

    # 5. Runtime engine binding.
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

    # 6. Duplicate canonical texts (DOM) and spoken texts (manifest).
    canonical = data["canonical"]
    spoken = [c["text"] for s in sections.values() for c in s.get("cues", [])]
    check(len(canonical) == len(set(canonical)),
          f"0 duplicate canonical cue texts (DOM {len(canonical)} cues, "
          f"{len(canonical)-len(set(canonical))} dupes)", errors)
    check(len(spoken) == len(set(spoken)),
          f"0 duplicate spoken cue texts (manifest {len(spoken)} cues, "
          f"{len(spoken)-len(set(spoken))} dupes)", errors)

    # 7. No quiz / media-tab cue types.
    man_types_all = [c["type"] for s in sections.values() for c in s.get("cues", [])]
    check(not data["forbidden"] and not any(t in FORBIDDEN for t in man_types_all),
          "0 quiz/media-tab cue types (DOM and manifest)", errors)

    # 8. MP3 reachable (HTTP 200) + non-zero on disk.
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

    # 9. Cue timings: positive, no overlap, exact gaps, total matches.
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

    # 10. manifest.json on disk is valid JSON and matches window object.
    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        disk_mf = json.load(fh)
    check(disk_mf == mf, "manifest.json on disk == window.TEACHER_AUDIO_MANIFEST", errors)

    total_cues = sum(len(s["cues"]) for s in sections.values())
    total_ms = sum(s["total_duration_ms"] for s in sections.values())
    figures = sum(1 for s in sections.values() for c in s["cues"] if c["type"] == "figure")
    print("\n" + "=" * 70)
    print(f"TOTALS: {total_cues} cues, {total_ms/1000.0:.2f}s, {figures} figure explanations")
    if errors:
        print(f"VERIFICATION FAILED ({len(errors)} issue(s)):")
        for e in errors:
            print("  - " + e)
    else:
        print("VERIFICATION PASSED: all checks green.")
    print("=" * 70)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
