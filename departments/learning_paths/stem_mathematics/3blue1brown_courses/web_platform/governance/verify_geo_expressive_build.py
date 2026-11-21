# -*- coding: utf-8 -*-
"""
Browser verification of the regenerated Geometry lessons 01..06 expressive
teacher audio. Headless Chrome (channel="chrome") against the LIVE lesson pages
over HTTP (local range server on port 8085).

For every lesson:
  * window.TEACHER_AUDIO_MANIFEST present, valid JSON, == manifest.json on disk
  * manifest sections exactly the 6 canonical DOM section ids
  * narrationEngine parsed exactly those 6 narrated sections
  * DOM <-> manifest 1:1 per section (cue types + counts, in order)
  * runtime binding: section ids, audio_file, block/cue lengths align
  * 0 duplicate canonical DOM cue texts and 0 duplicate spoken manifest texts
  * 0 quiz / media-tab cue types anywhere
  * NO cue text contains the artificial label "চিত্র প্রদর্শনী"
  * NO cue text contains markup / Latin letters / em-dash (phonetic safeguard)
  * every mp3 reachable over HTTP (200), non-zero on disk, positive ffprobe dur
  * cue timings positive, zero overlaps, exact 350 ms gaps, totals consistent
  * placeholder backup folder present
  * 0 page errors

Usage:  python governance/verify_geo_expressive_build.py
"""
import json
import os
import re
import subprocess

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
PAGES = os.path.join(WORKSPACE, "courses", "geometry")
AUDIO_ROOT = os.path.join(WORKSPACE, "assets", "audio", "geometry")

EXPECTED_TOTALS = {1: 37, 2: 29, 3: 26, 4: 27, 5: 25, 6: 26}
FORBIDDEN = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
GAP_MS = 350.0

VERIFY_JS = r"""() => {
  const out = { manifest: null, domBlocks: {}, runtime: [], forbidden: [],
                canonical: [], hasStudioAudio: false };
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


def verify_lesson(page, n):
    errors, page_errors = [], []
    url = f"http://127.0.0.1:8085/courses/geometry/lesson_{n:02d}.html?v=verify-geo{n:02d}"
    a_dir = os.path.join(AUDIO_ROOT, f"lesson_{n:02d}")
    http_base = f"http://127.0.0.1:8085/assets/audio/geometry/lesson_{n:02d}/"
    handler = lambda e: page_errors.append(str(e))
    page.on('pageerror', handler)
    page.route("**/*.mp4", lambda route: route.abort())
    page.set_default_navigation_timeout(60000)
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_function(
        "() => window.narrationEngine && window.narrationEngine.sections && "
        "window.narrationEngine.sections.length >= 6 && "
        "window.narrationEngine.hasStudioAudio === true && "
        "window.narrationEngine.sections.every(s => (s.cues || []).length > 0) && "
        "window.TEACHER_AUDIO_MANIFEST",
        timeout=30000,
    )
    data = page.evaluate(VERIFY_JS)
    mf = data["manifest"] or {}
    audio_http = {}
    for sec in mf.get("sections", {}).values():
        af = sec["audio_file"]
        resp = page.request.get(http_base + af)
        audio_http[af] = (resp.status, len(resp.body()))
    page.remove_listener('pageerror', handler)

    print("\n" + "=" * 82)
    print(f"GEOMETRY L{n:02d} BROWSER VERIFICATION (headless Chrome, channel='chrome')")
    print("=" * 82)
    check(isinstance(mf, dict) and isinstance(mf.get("sections"), dict),
          "window.TEACHER_AUDIO_MANIFEST is a valid JSON object", errors)
    check(not page_errors, f"0 page errors (got {len(page_errors)})", errors)
    for pe in page_errors:
        print("      PAGE ERROR: " + pe)
    check(data.get("hasStudioAudio") is True,
          "narrationEngine fetched/bound the studio manifest", errors)

    sections = mf.get("sections", {})
    dom_ids = set(data["domBlocks"])
    check(len(dom_ids) == 6 and set(sections) == dom_ids,
          f"manifest sections exactly the {len(dom_ids)} canonical DOM ids; "
          f"got {len(sections)} manifest keys", errors)

    check(mf.get("course") == "geometry" and mf.get("lesson") == f"lesson_{n:02d}"
          and mf.get("voice") == "bn-BD-PradeepNeural"
          and mf.get("mode") == "authentic_teacher" and bool(mf.get("title")),
          "manifest metadata (course/lesson/voice/mode/title) correct", errors)

    # DOM <-> manifest 1:1 per narrated section.
    print("\nDOM <-> manifest 1:1 per narrated section:")
    total_canonical = 0
    for sid in sorted(dom_ids):
        dom_types = data["domBlocks"].get(sid, [])
        man_types = [c["type"] for c in sections.get(sid, {}).get("cues", [])]
        ok = bool(dom_types) and dom_types == man_types
        check(ok, f"{sid}: DOM {len(dom_types)} == manifest {len(man_types)}, "
                  f"cue types identical", errors)
        if not ok:
            print(f"      DOM={dom_types}\n      MAN={man_types}")
        total_canonical += len(man_types)
    check(total_canonical == EXPECTED_TOTALS[n],
          f"{EXPECTED_TOTALS[n]}/{EXPECTED_TOTALS[n]} canonical cues "
          f"(got {total_canonical})", errors)

    # Runtime engine binding.
    print("\nRuntime narration-engine binding:")
    rt = {r["id"]: r for r in data["runtime"]}
    for sid in sorted(dom_ids):
        r = rt.get(sid)
        expected_n = len(data["domBlocks"][sid])
        ok = bool(r) and r["blocks"] == expected_n and r["cues"] == expected_n
        check(ok, f"{sid}: engine blocks={r and r['blocks']}, "
                  f"cues={r and r['cues']}, expected {expected_n}", errors)
        af = sections.get(sid, {}).get("audio_file", "")
        check(bool(r) and af and r["audioFile"].endswith(af),
              f"{sid}: engine audioFile points to {af}", errors)

    # Duplicate texts (canonical DOM + spoken manifest).
    canonical = data["canonical"]
    spoken = [c["text"] for sid in dom_ids for c in sections[sid].get("cues", [])]
    check(len(canonical) == len(set(canonical)),
          f"0 duplicate canonical DOM cue texts ({len(canonical)} cues, "
          f"{len(canonical) - len(set(canonical))} dupes)", errors)
    check(len(spoken) == len(set(spoken)),
          f"0 duplicate spoken manifest texts ({len(spoken)} cues, "
          f"{len(spoken) - len(set(spoken))} dupes)", errors)

    # No quiz / media-tab types anywhere.
    man_types_all = [c["type"] for s in sections.values() for c in s.get("cues", [])]
    check(not data["forbidden"] and not any(t in FORBIDDEN for t in man_types_all),
          "0 quiz/media-tab cue types (DOM and manifest)", errors)

    # No artificial label / forbidden markup anywhere in spoken text.
    bad_label = [t for t in spoken if FORBIDDEN_PREFIX in t]
    bad_chars = [t for t in spoken if BAD_CHARS.search(t)]
    check(not bad_label,
          f'0 "চিত্র প্রদর্শনী" labels (got {len(bad_label)})', errors)
    check(not bad_chars,
          f"0 forbidden chars in spoken text (markup/Latin/em-dash; "
          f"got {len(bad_chars)})", errors)

    # MP3 reachable + non-zero + ffprobe positive + duration ~ manifest.
    print("\nMP3 files (HTTP + on-disk ffprobe):")
    for sid in sorted(dom_ids):
        sec = sections[sid]
        af = sec["audio_file"]
        path = os.path.join(a_dir, af)
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
        check(ok, f"{af}: HTTP {status} ({served_bytes} B), "
                  f"{disk_bytes} disk B, {dur / 1000.0:.2f}s", errors)
        check(abs(dur - sec["total_duration_ms"]) <= 2500.0,
              f"{af}: ffprobe {dur:.1f} ms ~ manifest "
              f"{sec['total_duration_ms']:.1f} ms", errors)

    # Cue timings.
    print("\nCue timings (positive / no overlap / exact 350 ms gaps / total):")
    for sid in sorted(dom_ids):
        sec = sections[sid]
        cues = sec.get("cues", [])
        ok, prev_end = True, None
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

    # Disk manifest matches window object + backup present.
    with open(os.path.join(a_dir, "manifest.json"), encoding="utf-8") as fh:
        disk_mf = json.load(fh)
    check(disk_mf == mf, "manifest.json on disk == window.TEACHER_AUDIO_MANIFEST", errors)
    backup = os.path.join(a_dir, "_backup_before_expressive_build")
    check(os.path.isfile(os.path.join(backup, "manifest.json")) and
          os.path.isfile(os.path.join(backup, "manifest.js")),
          "placeholder backup (_backup_before_expressive_build/) present", errors)

    total_ms = sum(sections[s]["total_duration_ms"] for s in dom_ids)
    figures = sum(1 for s in dom_ids for c in sections[s]["cues"] if c["type"] == "figure")
    print("\n" + "-" * 82)
    print(f"L{n:02d} TOTALS: {total_canonical}/{EXPECTED_TOTALS[n]} cues, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations, "
          f"{len(sections)} manifest keys")
    print("PER SECTION: " + ", ".join(
        f"{sid}={len(sections[sid]['cues'])}" for sid in sorted(dom_ids)))
    if errors:
        print(f"L{n:02d} VERIFICATION FAILED ({len(errors)} issue(s)):")
        for e in errors:
            print("  - " + e)
    else:
        print(f"L{n:02d} VERIFICATION PASSED: all checks green.")
    return errors, total_canonical, total_ms, figures


def main():
    all_errors = []
    grand_cues = grand_ms = grand_figs = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page()
        for n in range(1, 7):
            errs, cues, ms, figs = verify_lesson(page, n)
            all_errors.extend(errs)
            grand_cues += cues
            grand_ms += ms
            grand_figs += figs
        browser.close()
    print("\n" + "=" * 82)
    print(f"GEOMETRY COURSE TOTAL: {grand_cues}/170 cues, {grand_ms / 1000.0:.2f}s, "
          f"{grand_figs} figure explanations, 6 lessons")
    print("FINAL: " + ("ALL 6 LESSONS VERIFIED - ALL CHECKS GREEN"
                       if not all_errors else
                       f"FAILED: {len(all_errors)} issue(s) across the course"))
    print("=" * 82)
    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
