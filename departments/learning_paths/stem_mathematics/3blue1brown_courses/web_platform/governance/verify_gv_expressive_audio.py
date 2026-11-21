# -*- coding: utf-8 -*-
"""
Final verification of the five Guest-Videos expressive TEACHER NARRATION AUDIO
builds, in headless Chrome (channel="chrome").

Per lesson it asserts:
  * manifest.json / manifest.js are valid and identical objects
  * DOM (narration_engine selector) <-> manifest <-> engine sections 1:1 by
    section id, cue count, cue type and cue order
  * 0 duplicate cue scripts, 0 quiz/media-tab cue types
  * 0 forbidden labels (চিত্র প্রদর্শনী), 0 markup/Latin characters in TTS text
  * figure cues are genuine 2-4 sentence explanations
  * exact-ms timing integrity (350 ms gaps, no overlap, end == total_duration_ms)
  * every section mp3 exists, is non-zero, decodes, and matches the manifest
    total duration (allowing MP3 frame padding)
  * page manifest cache-buster is ?v>=8
  * 0 console errors / page errors, preloaded manifest matches on-page object

Writes governance/_gv_expressive_verify_result.json.
"""
import json
import os
import re
import subprocess
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = "file:///" + ROOT.replace("\\", "/").replace(" ", "%20")
CHANNEL = "chrome"
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"
FORBIDDEN_TYPES = {"quiz", "media-tab"}
GAP_MS = 350.0


def jload(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def dom_snapshot(n):
    return jload(os.path.join(HERE, f"gv{n:02d}_dom_blocks.json"))


def probe_ms(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout.strip()
    return float(out) * 1000.0


def verify_lesson(page, n):
    lid = "lesson_%02d" % n
    a_dir = os.path.join(ROOT, "assets", "audio", "guest_videos", lid)
    errs = []
    checks = {}
    detail = {"lesson": lid, "url": "%s/courses/guest_videos/%s.html" % (BASE, lid),
              "channel": CHANNEL + " (headless=True)"}

    # --- Static artifact checks -------------------------------------------
    try:
        manifest = jload(os.path.join(a_dir, "manifest.json"))
        checks["valid_json"] = True
    except Exception as exc:  # noqa: BLE001
        manifest = {}
        checks["valid_json"] = False
        errs.append("manifest.json invalid: %s" % exc)

    js_text = ""
    try:
        with open(os.path.join(a_dir, "manifest.js"), encoding="utf-8") as fh:
            js_text = fh.read().strip()
        js_obj = json.loads(js_text[len("window.TEACHER_AUDIO_MANIFEST = "):-1].strip())
        checks["manifest_js_equals_json"] = js_obj == manifest
    except Exception as exc:  # noqa: BLE001
        checks["manifest_js_equals_json"] = False
        errs.append("manifest.js invalid: %s" % exc)

    backup = os.path.join(a_dir, "_backup_before_expressive_build")
    checks["placeholder_backup_present"] = all(
        os.path.getsize(os.path.join(backup, f)) > 0
        for f in ("manifest.json", "manifest.js")
    ) if os.path.isdir(backup) else False

    snap = dom_snapshot(n)
    dom_ids = [s["id"] for s in snap]
    dom_types = {s["id"]: [b["type"] for b in s["blocks"]] for s in snap}
    man_sections = manifest.get("sections", {})
    checks["section_ids_match_dom"] = list(man_sections) == dom_ids

    all_texts = []
    per_sec = {}
    timing_ok = True
    mp3_ok = True
    text_ok = True
    forbidden_ok = True
    figure_ok = True
    for sid in dom_ids:
        msec = man_sections.get(sid, {})
        cues = msec.get("cues", [])
        mtypes = [c.get("type") for c in cues]
        per_sec[sid] = {
            "manifest_cues": len(cues),
            "dom_blocks": len(dom_types[sid]),
            "types_match": mtypes == dom_types[sid],
        }
        if mtypes != dom_types[sid] or len(cues) != len(dom_types[sid]):
            timing_ok = False  # reflected by narration_parity below
        if [c.get("index") for c in cues] != list(range(len(cues))):
            per_sec[sid]["indices_ok"] = False
        else:
            per_sec[sid]["indices_ok"] = True

        cursor = 0.0
        for i, c in enumerate(cues):
            t = c.get("text", "")
            all_texts.append(t)
            if BAD_CHARS.search(t) or FORBIDDEN_PREFIX in t or c.get("type") in FORBIDDEN_TYPES:
                text_ok = False
                forbidden_ok = False
            if c.get("type") == "figure":
                sents = [s for s in t.split("।") if s.strip()]
                if not (2 <= len(sents) <= 4):
                    figure_ok = False
            try:
                start, end, dur = float(c["start_ms"]), float(c["end_ms"]), float(c["duration_ms"])
            except Exception:  # noqa: BLE001
                timing_ok = False
                continue
            if dur <= 0 or end <= start or abs(start - cursor) > 1.0 or abs(end - start - dur) > 1.0:
                timing_ok = False
            if i > 0:
                prev = cues[i - 1]
                try:
                    if abs(start - float(prev["end_ms"]) - GAP_MS) > 1.0:
                        timing_ok = False
                except Exception:  # noqa: BLE001
                    timing_ok = False
            cursor = end + (GAP_MS if i < len(cues) - 1 else 0.0)
        if abs(cursor - float(msec.get("total_duration_ms", -1))) > 1.0:
            timing_ok = False

        path = os.path.join(a_dir, msec.get("audio_file", "__missing__"))
        if not (os.path.exists(path) and os.path.getsize(path) > 0):
            mp3_ok = False
            per_sec[sid]["mp3_bytes"] = 0
        else:
            per_sec[sid]["mp3_bytes"] = os.path.getsize(path)
            try:
                actual = probe_ms(path)
                per_sec[sid]["mp3_ms"] = round(actual, 1)
                if actual <= 0 or abs(actual - float(msec.get("total_duration_ms", 0))) > 1200.0:
                    mp3_ok = False
            except Exception:  # noqa: BLE001
                mp3_ok = False

    checks["cue_timings_exact"] = timing_ok
    checks["mp3_nonzero_and_matching"] = mp3_ok
    checks["no_markup_or_latin_in_tts"] = text_ok
    checks["no_forbidden_labels_or_types"] = forbidden_ok
    checks["figure_explanations_2to4"] = figure_ok
    checks["zero_duplicate_cues"] = len(all_texts) == len(set(all_texts))

    html_path = os.path.join(ROOT, "courses", "guest_videos", lid + ".html")
    with open(html_path, encoding="utf-8") as fh:
        html_src = fh.read()
    mv = re.search(r"assets/audio/guest_videos/%s/manifest\.js\?v=(\d+)" % lid, html_src)
    checks["page_manifest_version_bumped"] = bool(mv and int(mv.group(1)) >= 8)
    detail["manifest_version"] = int(mv.group(1)) if mv else None

    # --- Live browser checks ----------------------------------------------
    page.on("console", lambda m: errs.append("console: " + m.text[:200]) if m.type == "error" else None)
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)[:200]))
    page.goto(detail["url"], wait_until="domcontentloaded", timeout=60000)
    page.wait_for_function(
        "() => window.narrationEngine && window.narrationEngine.sections && "
        "window.narrationEngine.sections.length >= 4",
        timeout=30000,
    )
    live = page.evaluate("""() => {
      const eng = window.narrationEngine;
      const nm = window.TEACHER_AUDIO_MANIFEST || {};
      return {
        engine: eng.sections.map(s => ({id:s.id, blocks:s.blocks.length, cues:s.cues.length,
                                        audioFile:s.audioFile || ''})),
        manifest: nm,
        quizCount: document.querySelectorAll('b1b-quiz').length,
        mediaTabs: document.querySelectorAll('[data-narration-type=\"quiz\"], [data-narration-type=\"media-tab\"]').length
      };
    }""")

    checks["no_page_errors"] = len(errs) == 0
    checks["page_manifest_matches"] = live["manifest"] == manifest
    eng_ids = [s["id"] for s in live["engine"]]
    checks["engine_ids_match_dom"] = eng_ids == dom_ids
    parity = eng_ids == dom_ids
    for es in live["engine"]:
        sid = es["id"]
        msec = man_sections.get(sid, {})
        ok = (es["blocks"] == len(dom_types.get(sid, [])) == len(msec.get("cues", []))
              and es["cues"] == len(msec.get("cues", []))
              and msec.get("audio_file", "x") in es["audioFile"])
        per_sec[sid]["engine_blocks"] = es["blocks"]
        per_sec[sid]["engine_cues"] = es["cues"]
        per_sec[sid]["engine_ok"] = bool(ok)
        parity = parity and ok
    checks["narration_parity_1to1"] = parity
    checks["zero_quiz_media_tab_narration"] = live["mediaTabs"] == 0 and live["quizCount"] >= 0

    detail["checks"] = checks
    detail["all_ok"] = all(checks.values())
    detail["errors"] = errs
    detail["per_section"] = per_sec
    detail["totals"] = {
        "sections": len(dom_ids),
        "cues": sum(len(man_sections.get(s, {}).get("cues", [])) for s in dom_ids),
        "figures": sum(1 for s in dom_ids for c in man_sections.get(s, {}).get("cues", [])
                       if c.get("type") == "figure"),
        "audio_seconds": round(sum(float(man_sections.get(s, {}).get("total_duration_ms", 0))
                                   for s in dom_ids) / 1000.0, 2),
    }
    return detail


def main():
    reports = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel=CHANNEL)
        for n in range(1, 6):
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            try:
                reports.append(verify_lesson(page, n))
            finally:
                page.close()
        browser.close()
    ok = all(r["all_ok"] for r in reports)
    out = {"channel": CHANNEL + " (headless=True)", "all_ok": ok, "reports": reports}
    out_path = os.path.join(HERE, "_gv_expressive_verify_result.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    for r in reports:
        failed = [k for k, v in r["checks"].items() if not v]
        t = r["totals"]
        print("%s: %s | %d sections, %d cues, %d figures, %.2fs audio%s" % (
            r["lesson"], "PASS" if r["all_ok"] else "FAIL",
            t["sections"], t["cues"], t["figures"], t["audio_seconds"],
            ("  FAILING=" + ",".join(failed)) if failed else ""))
        if r["errors"]:
            print("   errors:", r["errors"][:4])
    print("OVERALL:", "PASS" if ok else "FAIL")
    print("report:", out_path)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
