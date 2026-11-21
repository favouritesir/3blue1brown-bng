# -*- coding: utf-8 -*-
"""Final verification of the gold-standard expressive teacher narration.

Headless Chrome (channel=chrome) checks DOM<->manifest 1:1, zero duplicates,
zero quiz/media-tab cue types, zero page errors, zero forbidden labels; plus
file-level checks for valid JSON, non-zero MP3s, 350 ms gaps and backups.

Writes governance/_cs_verify_expressive_summary.json and exits non-zero on any
failure. Report counts/durations for all 13 lessons.
"""
import json
import os
import re
import subprocess
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "http://127.0.0.1:8100"
FORBIDDEN = "চিত্র প্রদর্শনী"
BAD_TYPES = {"quiz-block", "media-tab"}

EVAL = r"""() => {
  const E = window.narrationEngine, M = window.TEACHER_AUDIO_MANIFEST;
  const secs = (E ? E.sections : []).map(s => ({
    id: s.id,
    dom_blocks: s.blocks.length,
    dom_cues: s.cues.length,
    types: s.blocks.map((b, i) => {
      const el = b.element;
      if (el.matches('h2')) return 'h2';
      if (el.matches('h3')) return 'h3';
      if (el.matches('figure.lesson-figure')) return 'figure';
      if (el.classList.contains('formula-box')) return 'formula-box';
      if (el.classList.contains('callout')) return 'callout';
      if (el.classList.contains('chapter-quote')) return 'chapter-quote';
      return 'p';
    }),
    mcue: (M && M.sections[s.id]) ? M.sections[s.id].cues : null,
    mfile: (M && M.sections[s.id]) ? M.sections[s.id].audio_file : null
  }));
  const bad = [], dups = [];
  Object.values((M && M.sections) || {}).forEach(s => {
    const seen = new Set();
    (s.cues || []).forEach(c => {
      if (BADTYPES.indexOf(c.type) >= 0) bad.push(c.type);
      const k = c.index + ':' + c.type;
      if (seen.has(k)) dups.push(k);
      seen.add(k);
    });
  });
  return {
    secs, bad, dups,
    manifestIds: Object.keys((M && M.sections) || {}),
    domIds: secs.map(s => s.id),
    scriptSrc: Array.from(document.querySelectorAll('head script[src]'))
      .map(s => s.getAttribute('src')),
    katex: document.querySelectorAll('annotation[encoding="application/x-tex"]').length
  };
}""".replace("BADTYPES", json.dumps(sorted(BAD_TYPES)))


def dur_ms(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout.strip()
    return float(out) * 1000.0


def check(cond, results, lesson, name, detail=""):
    ok = bool(cond)
    results.append({"lesson": lesson, "check": name, "ok": ok, "detail": detail})
    return ok


def main():
    results = []
    summary = []
    audio_root = os.path.join(ROOT, "assets", "audio", "computer_science")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        for n in range(1, 14):
            lesson = "lesson_%02d" % n
            errors = []
            page = browser.new_page()
            page.on("pageerror", lambda e, a=errors: a.append("pageerror:" + str(e)))
            page.on("console", lambda m, a=errors: a.append("console:" + m.text)
                    if m.type == "error" else None)
            page.on("response", lambda r, a=errors: a.append("http%d:%s" % (r.status, r.url))
                    if r.status >= 400 else None)
            try:
                page.goto("%s/courses/computer_science/lesson_%02d.html?v=verify"
                          % (BASE, n), wait_until="domcontentloaded", timeout=30000)
                page.wait_for_function(
                    "() => window.narrationEngine && window.narrationEngine.sections.length > 0",
                    timeout=20000)
                r = page.evaluate(EVAL)
            except Exception as e:  # noqa: BLE001
                check(False, results, lesson, "navigation/eval", str(e).split("\n")[0])
                page.close()
                continue
            page.close()

            check(len(errors) == 0, results, lesson, "0 page/console/http errors",
                  str(errors[:3]))
            check(len(r["secs"]) == 5, results, lesson, "5 narrated DOM sections",
                  str(len(r["secs"])))
            check(r["manifestIds"] == r["domIds"], results, lesson,
                  "manifest section IDs == DOM IDs (order)")
            check(len(set(r["manifestIds"])) == len(r["manifestIds"]), results,
                  lesson, "0 duplicate section IDs")
            parity = all(s["dom_blocks"] == s["dom_cues"] == len(s["mcue"] or [])
                         for s in r["secs"])
            check(parity, results, lesson, "DOM blocks == cues == manifest cues")
            types_ok = all([c["type"] for c in (s["mcue"] or [])] == s["types"]
                           for s in r["secs"])
            check(types_ok, results, lesson, "manifest cue types == DOM block types")
            indices_ok = all([c["index"] for c in (s["mcue"] or [])] ==
                             list(range(len(s["mcue"] or []))) for s in r["secs"])
            check(indices_ok, results, lesson, "cue indices contiguous 0..n-1")
            check(len(r["bad"]) == 0, results, lesson, "0 quiz/media-tab cue types",
                  str(r["bad"]))
            check(len(r["dups"]) == 0, results, lesson, "0 duplicate cue ids",
                  str(r["dups"][:5]))
            check(r["katex"] > 0, results, lesson, "KaTeX annotations rendered",
                  str(r["katex"]))
            manifest_href = [s for s in r["scriptSrc"] if "manifest.js" in s]
            check(len(manifest_href) == 1 and "?v=2" in manifest_href[0], results,
                  lesson, "page manifest bumped to ?v=2", str(manifest_href))

            # File-level checks.
            adir = os.path.join(audio_root, lesson)
            mjson = os.path.join(adir, "manifest.json")
            mjs = os.path.join(adir, "manifest.js")
            try:
                m = json.load(open(mjson, encoding="utf-8"))
                js = open(mjs, encoding="utf-8").read()
                assert js.startswith("window.TEACHER_AUDIO_MANIFEST = ")
                assert json.loads(js[len("window.TEACHER_AUDIO_MANIFEST = "):].rstrip(";\n"))
                check(True, results, lesson, "valid manifest.json + manifest.js")
            except Exception as e:  # noqa: BLE001
                check(False, results, lesson, "valid manifest.json + manifest.js", str(e))
                continue

            texts = [c["text"] for s in m["sections"].values() for c in s["cues"]]
            check(not any(FORBIDDEN in t for t in texts), results, lesson,
                  "0 forbidden figure labels")
            badchars = [t for t in texts if re.search(r"[A-Za-z\\$⟦⟧{}\[\]—–\-=+/^]", t)]
            check(len(badchars) == 0, results, lesson, "0 Latin/markup artifacts",
                  str(badchars[:2]))
            backup = os.path.join(adir, "_backup_before_expressive_build")
            check(os.path.exists(os.path.join(backup, "manifest.json")) and
                  os.path.exists(os.path.join(backup, "manifest.js")), results,
                  lesson, "placeholder manifest backed up")

            total_cues = 0
            total_ms = 0.0
            mp3_ok = True
            gaps_ok = True
            for sid, sec in m["sections"].items():
                mp3 = os.path.join(adir, sec["audio_file"])
                if not (os.path.exists(mp3) and os.path.getsize(mp3) > 0 and dur_ms(mp3) > 0):
                    mp3_ok = False
                cues = sec["cues"]
                total_cues += len(cues)
                total_ms += sec["total_duration_ms"]
                for i in range(1, len(cues)):
                    gap = cues[i]["start_ms"] - cues[i - 1]["end_ms"]
                    if abs(gap - 350.0) > 1.0:
                        gaps_ok = False
                for c in cues:
                    if c["end_ms"] <= c["start_ms"] or c["duration_ms"] <= 0:
                        gaps_ok = False
            check(mp3_ok, results, lesson, "all section MP3s non-zero & decodable")
            check(gaps_ok, results, lesson, "350 ms gaps, positive spans")
            summary.append({"lesson": lesson, "sections": len(m["sections"]),
                            "cues": total_cues, "duration_s": round(total_ms / 1000.0, 2),
                            "figures": sum(1 for s in m["sections"].values()
                                           for c in s["cues"] if c["type"] == "figure")})
            print("%s: %d sections, %d cues, %.2fs, %d figures"
                  % (lesson, len(m["sections"]), total_cues, total_ms / 1000.0,
                     summary[-1]["figures"]))
        browser.close()

    failed = [x for x in results if not x["ok"]]
    report = {"lessons": summary, "total_checks": len(results),
              "passed": len(results) - len(failed), "failed": len(failed),
              "failures": failed, "channel": "chrome", "headless": True}
    dst = os.path.join(ROOT, "governance", "_cs_verify_expressive_summary.json")
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("\nTOTAL CHECKS %d  PASSED %d  FAILED %d" %
          (len(results), report["passed"], report["failed"]))
    for f in failed:
        print("FAIL", f["lesson"], f["check"], f["detail"][:160])
    print("report:", dst)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
