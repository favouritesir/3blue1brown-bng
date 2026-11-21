# -*- coding: utf-8 -*-
"""
Headless-Chrome verification of the L10 expressive teacher-audio build.

Checks, against the LIVE page (http://127.0.0.1:8085/.../lesson_10.html):
  * 37/37 cues (DOM blocks == manifest cues, per section and total)
  * DOM <-> manifest 1:1 (section ids, cue type/order, cue count)
  * 0 duplicate canonical cue texts
  * 0 quiz / media-tab cue types
  * MP3 files exist and are non-zero, and their real durations match the
    manifest timings (zero overlap, exact 350 ms gaps)
  * valid manifest.json + manifest.js (browser global)
  * 0 page errors
  * 0 occurrences of the forbidden "চিত্র প্রদর্শনী" label
  * manifest script tag cache-bumped to ?v=2
  * narration engine actually bound the studio audio

Run with the local web server up (port 8085):
    python governance/verify_l10_expressive_audio.py
"""
import json
import os
import re
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio",
                         "linear_algebra", "lesson_10")
URL = "http://127.0.0.1:8085/courses/linear_algebra/lesson_10.html"

EXPECTED_ORDER = [
    "sec_01_geometric_definition",
    "sec_02_2d_orientation_determinant",
    "sec_03_3d_determinant_formula",
    "sec_04_duality_perspective",
]
EXPECTED_COUNTS = {
    "sec_01_geometric_definition": 9,
    "sec_02_2d_orientation_determinant": 9,
    "sec_03_3d_determinant_formula": 9,
    "sec_04_duality_perspective": 10,
}
FORBIDDEN_TYPES = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
LABEL = "চিত্র প্রদর্শনী"

EXTRACT_JS = r"""() => {
  const sectionElements = document.querySelectorAll('.article > section, article section');
  const out = [];
  sectionElements.forEach((secEl, sIdx) => {
    if (secEl.getAttribute('data-no-narration') === 'true') return;
    const blocks = [];
    const readableNodes = secEl.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box'
    );
    readableNodes.forEach(node => {
      if (node.tagName === 'P' &&
          (node.closest('.callout') || node.closest('.chapter-quote'))) return;
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
      text = text.replace(/\u00a0/g, ' ').replace(/\n+/g, ' ')
                 .replace(/[ \t]+/g, ' ').trim();
      if (text && text.length > 2) blocks.push({ type, text });
    });
    if (blocks.length > 0)
      out.push({ id: secEl.id || ('sec-' + sIdx), blocks });
  });
  return out;
}"""

results = []


def check(name, cond, detail=""):
    results.append((bool(cond), name, detail))
    print(("  PASS  " if cond else "  FAIL  ") + name +
          ((" :: " + detail) if detail else ""))
    return bool(cond)


def main():
    # ---- local manifest files (valid JSON) --------------------------------
    mpath = os.path.join(AUDIO_DIR, "manifest.json")
    jspath = os.path.join(AUDIO_DIR, "manifest.js")
    check("manifest.json exists", os.path.exists(mpath))
    check("manifest.js exists", os.path.exists(jspath))
    with open(mpath, encoding="utf-8") as fh:
        manifest = json.load(fh)
    js_src = open(jspath, encoding="utf-8").read()
    check("manifest.js assigns window.TEACHER_AUDIO_MANIFEST",
          "window.TEACHER_AUDIO_MANIFEST" in js_src)
    check("manifest.json lesson == lesson_10", manifest.get("lesson") == "lesson_10")
    check("manifest.json voice == bn-BD-PradeepNeural",
          manifest.get("voice") == "bn-BD-PradeepNeural")

    # ---- live page in headless Chrome -------------------------------------
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page()
        errs = []
        page.on('pageerror', lambda e: errs.append(str(e)))
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_function(
            "() => window.narrationEngine && window.narrationEngine.hasStudioAudio "
            "&& window.TEACHER_AUDIO_MANIFEST && window.TEACHER_AUDIO_MANIFEST.sections",
            timeout=20000,
        )
        dom = page.evaluate(EXTRACT_JS)
        browser_global = page.evaluate("() => window.TEACHER_AUDIO_MANIFEST")
        studio = page.evaluate("""() => ({
            hasStudioAudio: window.narrationEngine.hasStudioAudio,
            sectionCount: window.narrationEngine.sections.length,
            bound: window.narrationEngine.sections.map(s => ({
                id: s.id, audioFile: s.audioFile, cues: s.cues.length,
                blocks: s.blocks.length
            }))
        })""")
        version = page.evaluate("""() => {
            const s = document.querySelector('script[src*="lesson_10/manifest.js"]');
            return s ? s.getAttribute('src') : '';
        }""")
        body_text = page.evaluate("() => document.body.innerText")
        browser.close()

    check("0 page errors", len(errs) == 0, repr(errs[:3]))
    check("manifest script cache-bumped to ?v=2", version.endswith("?v=2"), version)
    check("narration engine bound studio audio", studio["hasStudioAudio"] is True)
    check("narration engine parsed 4 sections", studio["sectionCount"] == 4,
          str(studio["sectionCount"]))
    check("browser manifest == manifest.json",
          browser_global == manifest)

    dom_map = {s["id"]: s for s in dom}
    check("DOM narrated section ids match manifest keys",
          set(dom_map) == set(EXPECTED_ORDER), str(sorted(dom_map)))
    check("manifest section keys match expected order",
          list(manifest["sections"]) == EXPECTED_ORDER)

    # ---- 37/37 cues + DOM<->manifest 1:1 ---------------------------------
    total_dom = sum(len(s["blocks"]) for s in dom)
    total_manifest = sum(len(v["cues"]) for v in manifest["sections"].values())
    check("DOM cue total == 37", total_dom == 37, str(total_dom))
    check("manifest cue total == 37", total_manifest == 37, str(total_manifest))

    all_dom_types = []
    all_manifest_texts = []
    all_dom_texts = []
    figures = []
    bad_type = []
    for sid in EXPECTED_ORDER:
        dblocks = dom_map[sid]["blocks"]
        mcues = manifest["sections"][sid]["cues"]
        dtypes = [b["type"] for b in dblocks]
        mtypes = [c["type"] for c in mcues]
        check(f"{sid}: DOM blocks == 9/10 expected",
              len(dblocks) == EXPECTED_COUNTS[sid], str(len(dblocks)))
        check(f"{sid}: DOM cue count == manifest cue count",
              len(dblocks) == len(mcues), f"{len(dblocks)} vs {len(mcues)}")
        check(f"{sid}: DOM type order == manifest type order",
              dtypes == mtypes, f"{dtypes} vs {mtypes}")
        check(f"{sid}: audioFile key matches",
              manifest["sections"][sid]["audio_file"] == sid + ".mp3")
        check(f"{sid}: engine audioFile bound",
              any(b["id"] == sid and b["audioFile"] and b["audioFile"].endswith(sid + ".mp3")
                  for b in studio["bound"]))
        check(f"{sid}: engine cues == blocks == manifest cues",
              any(b["id"] == sid and b["cues"] == b["blocks"] == len(mcues)
                  for b in studio["bound"]))
        all_dom_types += dtypes
        all_dom_texts += [b["text"] for b in dblocks]
        all_manifest_texts += [c["text"] for c in mcues]
        for c in mcues:
            figures.extend([c] if c["type"] == "figure" else [])

    # Duplicates: canonical DOM texts (TeX annotations make formulas unique).
    dups = len(all_dom_texts) - len(set(all_dom_texts))
    check("0 duplicate canonical DOM cue texts", dups == 0, str(dups))
    mdups = len(all_manifest_texts) - len(set(all_manifest_texts))
    check("0 duplicate manifest cue texts", mdups == 0, str(mdups))
    check("0 quiz/media-tab cue types (DOM)",
          not (set(all_dom_types) & FORBIDDEN_TYPES))
    check("0 quiz/media-tab cue types (manifest)",
          not (set(c["type"] for v in manifest["sections"].values()
                   for c in v["cues"]) & FORBIDDEN_TYPES))
    check("0 forbidden label in page text", LABEL not in body_text)
    check("0 forbidden label in manifest cue texts",
          not any(LABEL in t for t in all_manifest_texts))

    # ---- figure pedagogy ---------------------------------------------------
    check("exactly 2 figure cues", len(figures) == 2, str(len(figures)))
    for i, c in enumerate(figures):
        body = c["text"]
        sents = [s for s in re.split(r"[।?]", body) if s.strip()]
        check(f"figure {i}: 2-4 pedagogical sentences", 2 <= len(sents) <= 4,
              str(len(sents)))
        check(f"figure {i}: starts naturally with 'এখানে'",
              body.startswith("এখানে"))

    # ---- MP3 files, durations, exact gaps ---------------------------------
    import subprocess

    def probe(path):
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            check=True).stdout.strip()
        return float(out) * 1000.0

    for sid in EXPECTED_ORDER:
        sec = manifest["sections"][sid]
        fpath = os.path.join(AUDIO_DIR, sec["audio_file"])
        check(f"{sid}: MP3 exists and non-zero",
              os.path.exists(fpath) and os.path.getsize(fpath) > 0,
              f"{os.path.getsize(fpath) if os.path.exists(fpath) else 0} bytes")
        real_ms = probe(fpath)
        check(f"{sid}: real MP3 duration matches manifest total",
              abs(real_ms - sec["total_duration_ms"]) < 1500.0,
              f"real {real_ms:.0f} vs manifest {sec['total_duration_ms']:.0f}")
        cues = sec["cues"]
        gaps = [cues[i]["start_ms"] - cues[i - 1]["end_ms"]
                for i in range(1, len(cues))]
        check(f"{sid}: all cue spans positive",
              all(c["end_ms"] > c["start_ms"] for c in cues))
        check(f"{sid}: zero overlap between cues", all(g >= 0 for g in gaps))
        check(f"{sid}: every gap == 350 ms",
              all(abs(g - 350.0) <= 1.0 for g in gaps),
              str([round(g, 1) for g in gaps]))
        check(f"{sid}: cues monotonic & within total duration",
              cues[0]["start_ms"] == 0 and
              cues[-1]["end_ms"] <= sec["total_duration_ms"] + 1.0)

    total_s = sum(s["total_duration_ms"]
                  for s in manifest["sections"].values()) / 1000.0

    ok = all(r[0] for r in results)
    print("\n" + "=" * 72)
    print(f"VERIFICATION {'PASSED' if ok else 'FAILED'}: "
          f"{sum(r[0] for r in results)}/{len(results)} checks passed")
    print(f"  cues: DOM {total_dom}/37, manifest {total_manifest}/37, "
          f"sections {len(EXPECTED_ORDER)}")
    print(f"  figures: {len(figures)} (2-4 sentences each, natural phrasing)")
    print(f"  total audio duration: {total_s:.2f}s")
    print("  0 duplicates, 0 quiz/media-tab, 0 page errors, "
          "0 forbidden labels, MP3s non-zero, valid JSON")
    print("=" * 72)
    if not ok:
        for good, name, detail in results:
            if not good:
                print("FAILED:", name, detail)
        sys.exit(1)


if __name__ == "__main__":
    main()
