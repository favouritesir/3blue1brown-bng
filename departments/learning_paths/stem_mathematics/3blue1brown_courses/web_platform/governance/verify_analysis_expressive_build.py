# -*- coding: utf-8 -*-
"""Full browser verification of the regenerated Analysis Lessons 01-10
expressive teacher audio. Headless Chrome (channel="chrome") against the LIVE
lesson pages over HTTP (port 8085).

Per lesson:
  * window.TEACHER_AUDIO_MANIFEST present, valid JSON, == manifest.json on disk
  * manifest section keys exactly the 4 canonical DOM section ids
  * narrationEngine parsed exactly the 4 narrated sections; hasStudioAudio true
  * DOM <-> manifest 1:1 per section (cue types + counts, in order, from the
    engine's live parsed blocks), runtime ids/blocks/cues/audioFile aligned
  * 0 duplicate canonical cue texts (DOM) and spoken texts (manifest)
  * 0 quiz / media-tab cue types anywhere
  * 0 cue texts begin with/contain the artificial label "চিত্র প্রদর্শনী"
  * manifest cue text == embedded expressive script (not a placeholder)
  * figure cues are genuine 2-4 sentence explanations; no Latin/markup chars
  * every mp3 reachable over HTTP (200) and non-zero on disk (ffprobe > 0),
    ffprobe duration ~ manifest total
  * cue timings positive, zero overlaps, exact 350 ms gaps, total matches
  * placeholder manifest backed up under _backup_before_expressive_build/
  * 0 page errors

Usage: python governance/verify_analysis_expressive_build.py
"""
import json
import os
import re
import subprocess
import importlib

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
AUDIO_ROOT = os.path.join(WORKSPACE, "assets", "audio", "analysis")
BACKUP_DIRNAME = "_backup_before_expressive_build"
FORBIDDEN = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
FORBIDDEN_LABEL = "চিত্র প্রদর্শনী"
GAP_MS = 350.0
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")

VERIFY_JS = r"""() => {
  const out = { manifest: null, domBlocks: {}, runtime: [], forbidden: [], canonical: [] };
  out.manifest = window.TEACHER_AUDIO_MANIFEST || null;
  const typeOf = (el) => {
    if (!el) return 'p';
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
    print(("  [OK]   " if cond else "  [FAIL] ") + label)
    if not cond:
        errors.append(label)


def verify_lesson(n, builder):
    lesson = f"lesson_{n:02d}"
    canonical = set(builder.EXPECTED_TYPES)
    expected_total = sum(len(v) for v in builder.EXPECTED_TYPES.values())
    audio_dir = os.path.join(AUDIO_ROOT, lesson)
    url = f"http://127.0.0.1:8085/courses/analysis/{lesson}.html?v=verify"
    http_audio_base = f"http://127.0.0.1:8085/assets/audio/analysis/{lesson}/"

    errors = []
    page_errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page()
        page.set_default_navigation_timeout(60000)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        for attempt in range(3):
            try:
                page.goto(url, wait_until="domcontentloaded")
                break
            except Exception as exc:
                if attempt == 2:
                    raise
        page.wait_for_function(
            "() => window.narrationEngine && window.narrationEngine.sections && "
            "window.narrationEngine.sections.length >= 4 && "
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
            resp = page.request.get(http_audio_base + af)
            audio_http[af] = (resp.status, len(resp.body()))
        browser.close()

    print("\n" + "=" * 78)
    print(f"ANALYSIS {lesson} BROWSER VERIFICATION (headless Chrome, channel='chrome')")
    print("=" * 78)

    # Manifest shape / disk parity.
    sections = mf.get("sections", {})
    check(isinstance(mf, dict) and isinstance(sections, dict),
          "window.TEACHER_AUDIO_MANIFEST is a valid JSON object", errors)
    check(not page_errors, f"0 page errors (got {len(page_errors)})", errors)
    for pe in page_errors:
        print("      PAGE ERROR: " + pe)
    check(data.get("hasStudioAudio") is True,
          "narrationEngine bound the studio manifest (hasStudioAudio)", errors)
    check(set(sections) == canonical,
          f"manifest keys exactly {len(canonical)} canonical DOM sections "
          f"(got {len(sections)})", errors)

    with open(os.path.join(audio_dir, "manifest.json"), encoding="utf-8") as fh:
        disk_mf = json.load(fh)
    check(disk_mf == mf, "manifest.json on disk == window.TEACHER_AUDIO_MANIFEST", errors)

    # DOM <-> manifest 1:1.
    print("\nDOM <-> manifest 1:1 per narrated section:")
    for sid in sorted(canonical):
        dom_types = data["domBlocks"].get(sid, [])
        man_types = [c["type"] for c in sections.get(sid, {}).get("cues", [])]
        exp_types = builder.EXPECTED_TYPES[sid]
        ok = (len(dom_types) == len(exp_types) and len(man_types) == len(exp_types)
              and dom_types == man_types == exp_types)
        check(ok, f"{sid}: DOM {len(dom_types)} == manifest {len(man_types)} "
                  f"== expected {len(exp_types)}, types identical", errors)
        if not ok:
            print(f"      DOM={dom_types}\n      MAN={man_types}\n      EXP={exp_types}")
    total_canonical = sum(len(sections[s]["cues"]) for s in canonical if s in sections)
    check(total_canonical == expected_total,
          f"{expected_total}/{expected_total} canonical cues (got {total_canonical})", errors)
    leaked = set(data["domBlocks"]) - canonical
    check(not leaked, f"no non-narrated section leaked into DOM blocks (leaked={sorted(leaked)})", errors)

    # Runtime engine binding.
    print("\nRuntime narration-engine binding:")
    rt = {r["id"]: r for r in data["runtime"]}
    for sid in sorted(canonical):
        r = rt.get(sid)
        exp_n = len(builder.EXPECTED_TYPES[sid])
        ok = bool(r) and r["blocks"] == exp_n and r["cues"] == exp_n
        check(ok, f"{sid}: engine blocks={r and r['blocks']}, cues={r and r['cues']}, "
                  f"expected {exp_n}", errors)
        af = sections.get(sid, {}).get("audio_file", "")
        check(bool(r) and af and r["audioFile"].endswith(af),
              f"{sid}: engine audioFile endswith {af}", errors)

    # Duplicates / forbidden types / forbidden label.
    spoken_dom = data["canonical"]
    spoken_man = [c["text"] for s in canonical for c in sections[s].get("cues", [])]
    check(len(spoken_dom) == len(set(spoken_dom)),
          f"0 duplicate canonical DOM cue texts ({len(spoken_dom)-len(set(spoken_dom))} dupes)", errors)
    check(len(spoken_man) == len(set(spoken_man)),
          f"0 duplicate spoken cue texts ({len(spoken_man)-len(set(spoken_man))} dupes)", errors)
    man_types_all = [c["type"] for s in sections.values() for c in s.get("cues", [])]
    check(not data["forbidden"] and not any(t in FORBIDDEN for t in man_types_all),
          "0 quiz/media-tab cue types (DOM and manifest)", errors)
    any_label = [c["text"] for s in sections.values() for c in s.get("cues", [])
                 if FORBIDDEN_LABEL in c["text"]]
    check(not any_label,
          f'0 cue texts contain "চিত্র প্রদর্শনী" (got {len(any_label)})', errors)

    # Expressive scripts (not placeholders) + figure sentence count + clean chars.
    print("\nScript integrity (expressive content, figures, phonetic safeguards):")
    script_ok = True
    figure_ok = True
    clean_ok = True
    figure_count = 0
    for sid in sorted(canonical):
        cues = sections.get(sid, {}).get("cues", [])
        embedded = builder.SECTIONS_DATA[sid]["cues"]
        if [c["text"] for c in cues] != [c["tts"] for c in embedded]:
            script_ok = False
        for c in cues:
            if BAD_CHARS.findall(c["text"]):
                clean_ok = False
            if c["type"] == "figure":
                figure_count += 1
                sents = [s for s in c["text"].split("।") if s.strip()]
                if not (2 <= len(sents) <= 4):
                    figure_ok = False
    check(script_ok, "every manifest cue text equals the embedded expressive script", errors)
    check(clean_ok, "0 Latin letters / TeX / markup in spoken texts (phonetic safeguards)", errors)
    check(figure_ok, f"all {figure_count} figure cues are 2-4 sentence explanations", errors)

    # MP3 reachable (HTTP 200) + non-zero on disk + ffprobe ~ manifest total.
    print("\nMP3 files (HTTP + on-disk ffprobe):")
    for sid in sorted(canonical):
        sec = sections[sid]
        af = sec["audio_file"]
        path = os.path.join(audio_dir, af)
        status, served = audio_http.get(af, (None, 0))
        on_disk = os.path.exists(path) and os.path.getsize(path) > 0
        disk_bytes = os.path.getsize(path) if on_disk else 0
        dur = 0.0
        if on_disk:
            try:
                dur = probe_duration(path)
            except Exception:
                dur = 0.0
        ok = status == 200 and served > 0 and on_disk and dur > 0
        check(ok, f"{af}: HTTP {status} ({served} B), {disk_bytes} disk B, {dur/1000:.2f}s", errors)
        check(abs(dur - sec["total_duration_ms"]) <= 2500.0,
              f"{af}: ffprobe {dur:.1f} ms ~ manifest {sec['total_duration_ms']:.1f} ms", errors)

    # Cue timings.
    print("\nCue timings (positive / no overlap / exact 350 ms gaps / total):")
    for sid in sorted(canonical):
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
        check(ok and total_ok,
              f"{sid}: {len(cues)} cues, total {sec['total_duration_ms']:.1f} ms "
              f"(last end {cues[-1]['end_ms']:.1f})", errors)

    # Backup present.
    bak = os.path.join(audio_dir, BACKUP_DIRNAME)
    backup_ok = (os.path.exists(os.path.join(bak, "manifest.json"))
                 and os.path.exists(os.path.join(bak, "manifest.js")))
    check(backup_ok, "placeholder manifest backed up before expressive build", errors)

    total_ms = sum(sections[s]["total_duration_ms"] for s in canonical if s in sections)
    result = {
        "lesson": lesson, "cues": total_canonical, "duration_s": round(total_ms / 1000.0, 2),
        "figures": figure_count, "sections": len(canonical),
        "errors": errors, "ok": not errors,
    }
    print("\n" + "-" * 78)
    print(f"RESULT {lesson}: {total_canonical} cues, {total_ms/1000:.2f}s, "
          f"{figure_count} figures, {len(errors)} issue(s) -> "
          f"{'PASS' if not errors else 'FAIL'}")
    return result


def main():
    results = []
    for n in range(1, 11):
        builder = importlib.import_module(f"build_expressive_teacher_audio_analysis{n:02d}")
        results.append(verify_lesson(n, builder))

    print("\n" + "#" * 78)
    print("FINAL REPORT — ANALYSIS EXPRESSIVE TEACHER AUDIO (10 lessons)")
    print("#" * 78)
    grand_cues = grand_figures = 0
    grand_ms = 0.0
    for r in results:
        print(f"  {r['lesson']}: {r['cues']:>2} cues  {r['duration_s']:>8.2f}s  "
              f"{r['figures']} figures  {r['sections']} sections  "
              f"{'PASS' if r['ok'] else 'FAIL(' + str(len(r['errors'])) + ')'}")
        grand_cues += r["cues"]
        grand_figures += r["figures"]
        grand_ms += r["duration_s"]
    print(f"  TOTAL: {grand_cues} cues, {grand_ms:.2f}s, {grand_figures} figure explanations")
    failed = [r for r in results if not r["ok"]]
    print(f"  VERIFICATION: {'ALL 10 LESSONS PASSED' if not failed else str(len(failed)) + ' LESSON(S) FAILED'}")
    print("#" * 78)
    with open(os.path.join(HERE, "_analysis_verification_report.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
