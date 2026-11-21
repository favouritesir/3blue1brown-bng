# -*- coding: utf-8 -*-
"""
Headless-Chrome (channel="chrome") verification of the expressive teacher
audio for ALL THREE topology lessons. One fresh browser session per lesson.

    python governance/verify_expressive_teacher_audio_topology.py
"""
import os, json, subprocess
from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORBIDDEN = "চিত্র প্রদর্শনী"
ALLOWED = {"h2", "h3", "chapter-quote", "p", "figure", "callout",
           "formula-box", "code-showcase"}
BAD_TYPES = {"quiz", "quiz-feedback", "media-tab", "media", "tab", "exercise"}
EXPECTED = {
    1: {"sec-intro": ["h2", "p", "p", "p", "figure", "callout", "p"],
        "sec-square": ["h2", "chapter-quote", "p", "p", "p", "figure", "figure",
                       "formula-box", "p", "callout", "p"],
        "sec-rectangle": ["h2", "p", "p", "p", "p"] + ["figure"] * 7 +
                         ["formula-box", "p", "formula-box", "p", "callout", "p"],
        "sec-pairs": ["h2", "p", "p", "p", "p"] + ["figure"] * 13 +
                     ["formula-box", "p", "formula-box", "p", "callout", "p"],
        "sec-topology": ["h2", "p", "p", "p", "p", "figure", "formula-box", "p",
                         "formula-box", "p", "callout", "p"]},
    2: {"sec-intro": ["h2", "p", "p", "p", "figure", "figure", "formula-box",
                      "p", "formula-box", "p", "callout", "p"],
        "sec-applications": ["h2", "p", "p", "p", "figure", "formula-box", "p",
                             "formula-box", "p", "callout", "p"],
        "sec-proof": ["h2", "p", "p", "p", "p", "figure", "formula-box", "p",
                      "formula-box", "p", "formula-box", "p", "callout", "p"],
        "sec-dimensions": ["h2", "p", "p", "p", "figure", "formula-box", "p",
                           "formula-box", "p", "callout", "p"]},
    3: {"sec-intro": ["h2", "p", "p", "p", "figure", "figure", "formula-box",
                      "p", "formula-box", "p", "callout", "p"],
        "sec-necklace": ["h2", "p", "p", "p", "figure", "formula-box", "p",
                         "callout", "p"],
        "sec-proof": ["h2", "p", "p", "p", "figure", "formula-box", "p",
                      "formula-box", "p", "formula-box", "p", "callout", "p"],
        "sec-meaning": ["h2", "p", "p", "p", "figure", "formula-box", "p",
                        "callout", "p"]},
}

CAPTURE_JS = r"""() => {
  const ne = window.narrationEngine;
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
  const secEls = [...document.querySelectorAll('.article > section, article section')];
  const dom = [];
  for (const el of secEls) {
    if (el.getAttribute('data-no-narration') === 'true') continue;
    const nodes = [...el.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box')];
    const types = [], tex = [];
    for (const node of nodes) {
      if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) continue;
      types.push(typeOf(node));
      if (typeOf(node) === 'formula-box') {
        tex.push([...node.querySelectorAll('annotation[encoding="application/x-tex"]')]
                   .map(a => a.textContent));
      }
    }
    dom.push({id: el.id, types, tex});
  }
  return {
    dom,
    manifest: window.TEACHER_AUDIO_MANIFEST || null,
    hasStudioAudio: !!ne.hasStudioAudio,
    engineCount: (ne.sections || []).map(s => ({id: s.id, n: s.blocks.length})),
    articleText: (document.querySelector('b1b-article') || document.body).innerText || '',
    pageManifestVersion: (performance.getEntriesByType('resource')
      .map(r => r.name).find(n => n.includes('manifest.js')) || ''),
  };
}"""


def dur(path):
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout.strip())


def verify(n):
    audio_dir = os.path.join(BASE, "assets", "audio", "topology", f"lesson_{n:02d}")
    url = f"http://127.0.0.1:8085/courses/topology/lesson_{n:02d}.html?v=finalverify{n}"
    page_errors, console_errors = [], []
    benign = ("404 (File not found)", "Failed to load resource",
              "ERR_FILE_NOT_FOUND", "net::ERR", "ERR_BLOCKED",
              "Permissions policy violation")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page()
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.goto(url, wait_until="load")
        page.wait_for_function(
            "() => !!window.narrationEngine && window.narrationEngine.sections.length>0 "
            "&& !!window.TEACHER_AUDIO_MANIFEST", timeout=30000)
        data = page.evaluate(CAPTURE_JS)
        browser.close()

    checks = []
    def chk(name, ok, detail=""):
        checks.append((name, bool(ok), detail))

    manifest = data["manifest"]
    sections = manifest["sections"] if manifest else {}
    dom = data["dom"]
    expected = EXPECTED[n]
    canonical = list(expected)

    chk("0 JS page errors", not page_errors, str(page_errors))
    chk("0 unexpected console errors",
        not [e for e in console_errors if not any(b in e for b in benign)],
        f"{len(console_errors)} benign video-404s")
    chk("manifest present + studio audio bound",
        data["manifest"] is not None and data["hasStudioAudio"])
    chk("page manifest.js?v=2 loaded", "manifest.js?v=2" in data["pageManifestVersion"],
        data["pageManifestVersion"])

    disk = json.load(open(os.path.join(audio_dir, "manifest.json"), encoding="utf-8"))
    chk("manifest.json valid JSON", isinstance(disk, dict))
    chk("preloaded manifest == disk", manifest == disk)
    chk("mode is authentic_teacher (not placeholder)", disk.get("mode") == "authentic_teacher")
    chk("manifest.js exports global",
        open(os.path.join(audio_dir, "manifest.js"), encoding="utf-8").read(30)
        .startswith("window.TEACHER_AUDIO_MANIFEST"))

    chk("DOM section ids == expected", [s["id"] for s in dom] == canonical,
        str([s["id"] for s in dom]))
    chk("manifest section ids == expected", list(sections) == canonical)
    chk("engine counts match",
        all(e["n"] == sum(len(v) for v in [expected[e["id"]]]) for e in data["engineCount"]))

    parity = True
    total_cues = 0
    texts = []
    used_types = set()
    mp3s = []
    for sid in canonical:
        cues = sections[sid]["cues"]
        dsec = next(s for s in dom if s["id"] == sid)
        total_cues += len(cues)
        texts += [c["text"] for c in cues]
        used_types |= {c["type"] for c in cues}
        parity &= ([c["type"] for c in cues] == expected[sid] and
                   dsec["types"] == expected[sid])
        for bt in dsec["tex"]:
            parity &= any(t.strip() for t in bt)
        path = os.path.join(audio_dir, sections[sid]["audio_file"])
        mp3s.append((sections[sid]["audio_file"], os.path.getsize(path) if os.path.exists(path) else 0,
                     dur(path) if os.path.exists(path) else 0.0))
    chk("DOM <-> manifest 1:1 (ids/counts/types) + KaTeX annotations", parity)
    chk(f"DOM total cues == {sum(len(v) for v in expected.values())}",
        total_cues == sum(len(v) for v in expected.values()), str(total_cues))
    chk("0 duplicate section ids / audio files",
        len(set(sections)) == len(sections) and
        len({s["audio_file"] for s in sections.values()}) == len(sections))
    chk("0 duplicate cue indices (0-based) / texts",
        all([c["index"] for c in s["cues"]] == list(range(len(s["cues"]))) for s in sections.values())
        and len(texts) == len(set(texts)))
    chk("0 quiz/media-tab types", not (used_types & BAD_TYPES), str(sorted(used_types)))
    chk("all cue types allowed", used_types <= ALLOWED, str(sorted(used_types - ALLOWED)))
    chk('0 "চিত্র প্রদর্শনী" labels',
        not any(FORBIDDEN in t for t in texts) and FORBIDDEN not in data["articleText"])
    chk("mp3s non-zero + positive duration",
        len(mp3s) == len(canonical) and all(s > 0 and d > 0 for _, s, d in mp3s),
        "; ".join(f"{n}:{s}B/{d:.1f}s" for n, s, d in mp3s))
    total_ms = sum(s["total_duration_ms"] for s in sections.values())
    timing_ok = True
    for s in sections.values():
        cues = s["cues"]
        for i, c in enumerate(cues):
            timing_ok &= c["duration_ms"] > 0 and c["end_ms"] > c["start_ms"]
            if i:
                timing_ok &= abs(c["start_ms"] - cues[i-1]["end_ms"] - 350.0) <= 1.0
        timing_ok &= abs(cues[-1]["end_ms"] - s["total_duration_ms"]) <= 1.0
    chk("timings monotonic + 350ms gaps + totals", timing_ok)
    return checks, total_cues, total_ms, page_errors, [e for e in console_errors
                                                       if not any(b in e for b in benign)]


def main():
    grand = 0
    grand_ms = 0.0
    failed = False
    for n in (1, 2, 3):
        checks, cues, ms, pe, ce = verify(n)
        grand += cues
        grand_ms += ms
        print("=" * 72)
        print(f"TOPOLOGY LESSON {n:02d} — FINAL HEADLESS CHROME VERIFICATION")
        print("=" * 72)
        for name, ok, detail in checks:
            print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  :: {detail}" if detail else ""))
        print(f"CUES: {cues}   DURATION: {ms/1000:.2f}s   PAGE ERRORS: {len(pe)}   "
              f"UNEXPECTED CONSOLE ERRORS: {len(ce)}")
        failed |= not all(ok for _, ok, _ in checks)
    print("=" * 72)
    print(f"GRAND TOTAL: {grand} cues across 3 lessons, {grand_ms/1000:.2f}s audio")
    print("RESULT:", "ALL CHECKS PASSED" if not failed else "FAILURES PRESENT")
    print("=" * 72)
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
