# -*- coding: utf-8 -*-
"""
Browser verification for Lesson 04 expressive teacher audio.

Renders courses/linear_algebra/lesson_04.html in headless Chromium and checks,
directly against the live narration engine, that:
  * window.TEACHER_AUDIO_MANIFEST is loaded (manifest.js) and valid
  * the manifest has 6 narrated sections / 52 cues
  * narrationEngine.sections maps 1:1 to manifest sections (blocks == cues)
  * no quiz / media-tab cue types; no duplicate cue texts
  * every section audio src resolves to a non-zero, playable MP3
  * DOM cue type sequences match the manifest exactly
Also validates manifest.json on disk and every MP3 via ffprobe.

Usage:  python governance/verify_l04_audio_browser.py
"""
import json
import os
import subprocess

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8123/courses/linear_algebra/lesson_04.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "linear_algebra",
                         "lesson_04")
DOM_BLOCKS = os.path.join(HERE, "l04_dom_blocks.json")

FORBIDDEN = {"quiz-block", "media-tab", "quiz", "b1b-quiz", "b1b-media-tab"}
EXPECTED_COUNTS = {
    "sec-composition": 10, "sec-matrix-multiplication": 8, "sec-tracking": 8,
    "sec-algebraic-view": 9, "sec-derivation": 9, "sec-associativity": 8,
}

failures = []


def check(cond, msg):
    if cond:
        print("  PASS", msg)
    else:
        print("  FAIL", msg)
        failures.append(msg)


def ffprobe_ms(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout.strip()
    return float(out) * 1000.0


def main():
    print("=" * 72)
    print("LESSON 04 - EXPRESSIVE TEACHER AUDIO : BROWSER VERIFICATION")
    print("=" * 72)

    # ---- On-disk JSON + MP3 checks ----
    mpath = os.path.join(AUDIO_DIR, "manifest.json")
    check(os.path.exists(mpath), "manifest.json exists")
    with open(mpath, encoding="utf-8") as fh:
        manifest = json.load(fh)  # raises if invalid
    check(True, "manifest.json is valid JSON")
    # manifest.js must parse as the same object
    jpath = os.path.join(AUDIO_DIR, "manifest.js")
    with open(jpath, encoding="utf-8") as fh:
        jtxt = fh.read()
    check(jtxt.startswith("window.TEACHER_AUDIO_MANIFEST = "),
          "manifest.js assigns window.TEACHER_AUDIO_MANIFEST")
    js_obj = json.loads(jtxt[len("window.TEACHER_AUDIO_MANIFEST = "):].rstrip().rstrip(";"))
    check(js_obj == manifest, "manifest.js === manifest.json")

    secs = manifest["sections"]
    check(len(secs) == 6, "manifest has 6 narrated sections")
    check(set(secs) == set(EXPECTED_COUNTS), "manifest section IDs match DOM")

    with open(DOM_BLOCKS, encoding="utf-8") as fh:
        dom_blocks = json.load(fh)
    dom_map = {s["id"]: [b["type"] for b in s["blocks"]] for s in dom_blocks}

    all_texts = []
    audio_files = []
    total_cues = 0
    total_ms = 0.0
    figures = 0
    for sid, msec in secs.items():
        cues = msec["cues"]
        types = [c["type"] for c in cues]
        check(len(cues) == EXPECTED_COUNTS[sid],
              f"{sid}: {len(cues)} cues (expected {EXPECTED_COUNTS[sid]})")
        check(types == dom_map.get(sid),
              f"{sid}: cue type sequence 1:1 with live DOM")
        check(not (set(types) & FORBIDDEN), f"{sid}: no quiz/media cue types")
        texts = [c["text"] for c in cues]
        check(len(texts) == len(set(texts)), f"{sid}: no duplicate cue texts")
        all_texts.extend(texts)
        af = msec["audio_file"]
        audio_files.append(af)
        apath = os.path.join(AUDIO_DIR, af)
        check(os.path.exists(apath) and os.path.getsize(apath) > 0,
              f"{sid}: {af} exists and non-zero")
        dur = ffprobe_ms(apath)
        check(dur > 0, f"{sid}: {af} probe duration > 0 ({dur/1000:.2f}s)")
        # zero overlap / exact 350ms gaps
        ok = True
        for i, c in enumerate(cues):
            if c["duration_ms"] <= 0 or c["end_ms"] <= c["start_ms"]:
                ok = False
            if i > 0:
                prev = cues[i - 1]
                gap = c["start_ms"] - prev["end_ms"]
                if gap < 0 or abs(gap - 350.0) > 1.0:
                    ok = False
        check(ok, f"{sid}: zero overlaps and exact 350 ms gaps")
        total_cues += len(cues)
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in cues if c["type"] == "figure")

    check(len(all_texts) == len(set(all_texts)), "no duplicate cue texts globally")
    check(len(audio_files) == len(set(audio_files)), "6 distinct audio files")
    check(total_cues == 52, "52 cues total")
    check(figures == 9, "9 figure explanations")
    print(f"  INFO total duration: {total_ms/1000:.2f}s across 6 sections")

    # ---- Live browser checks ----
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        page = browser.new_page()
        page.goto(URL, wait_until="load")
        page.wait_for_function(
            "() => window.narrationEngine && window.narrationEngine.sections && "
            "window.narrationEngine.sections.length > 0 && "
            "window.narrationEngine.hasStudioAudio === true",
            timeout=15000,
        )
        data = page.evaluate("""() => {
          const ne = window.narrationEngine;
          return {
            hasStudioAudio: ne.hasStudioAudio,
            sections: ne.sections.map(s => ({
              id: s.id,
              title: s.title,
              blocks: s.blocks.length,
              cues: s.cues.length,
              audioFile: s.audioFile,
              types: s.cues.map(c => c.type),
              firstText: s.cues[0] ? s.cues[0].text : null,
            })),
          };
        }""")
        browser.close()

    check(data["hasStudioAudio"] is True, "browser: studio audio active")
    check(len(data["sections"]) == 6, "browser: 6 sections parsed from live DOM")
    for s in data["sections"]:
        sid = s["id"]
        check(sid in secs, f"browser: {sid} is in manifest")
        if sid not in secs:
            continue
        check(s["blocks"] == s["cues"],
              f"browser: {sid} DOM blocks == manifest cues (1:1) "
              f"({s['blocks']}=={s['cues']})")
        check(s["cues"] == EXPECTED_COUNTS[sid],
              f"browser: {sid} {s['cues']} cues")
        check(s["types"] == [c["type"] for c in secs[sid]["cues"]],
              f"browser: {sid} cue types match manifest")
        check(s["audioFile"] and s["audioFile"].endswith(secs[sid]["audio_file"]),
              f"browser: {sid} audio src bound to {secs[sid]['audio_file']}")
        check(s["firstText"] == secs[sid]["cues"][0]["text"],
              f"browser: {sid} first cue text matches manifest")

    print("=" * 72)
    if failures:
        print(f"VERIFICATION FAILED: {len(failures)} check(s) failed")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("VERIFICATION PASSED: DOM<->manifest 1:1, no duplicate/quiz/media cues,")
    print("zero overlaps, exact 350 ms gaps, 6 non-zero MP3s, valid JSON, live browser OK.")
    print("=" * 72)


if __name__ == "__main__":
    main()
