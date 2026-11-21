# -*- coding: utf-8 -*-
"""Supplementary L05 checks: headless Chrome (channel=chrome) page errors,
manifest script version, and the forbidden artificial figure-label prefix."""
import json
import os

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
URL = "http://127.0.0.1:8123/courses/linear_algebra/lesson_05.html"
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "linear_algebra", "lesson_05")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"

page_errors = []
console_errors = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel="chrome")
    page = browser.new_page()
    page.on("pageerror", lambda exc: page_errors.append(str(exc)))
    page.on("console", lambda msg: console_errors.append(msg.text)
            if msg.type == "error" else None)
    resp = page.goto(URL, wait_until="load")
    page.wait_for_function(
        "() => window.narrationEngine && window.narrationEngine.sections && "
        "window.TEACHER_AUDIO_MANIFEST", timeout=20000)
    result = page.evaluate("""(prefix) => {
      const sections = Object.entries(window.TEACHER_AUDIO_MANIFEST.sections);
      const texts = sections.flatMap(([k, v]) => v.cues.map(c => c.text));
      return {
        scriptSrc: Array.from(document.scripts).map(s => s.src)
                         .filter(s => s.includes('lesson_05/manifest.js')),
        sections: Object.fromEntries(sections.map(([k, v]) => [k, v.cues.length])),
        total: texts.length,
        startsWithForbidden: texts.filter(t => t.startsWith(prefix)),
        containsForbidden: texts.filter(t => t.includes(prefix)),
      };
    }""", FORBIDDEN_PREFIX)
    browser.close()

with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
    disk = json.load(fh)
disk_texts = [c["text"] for s in disk["sections"].values() for c in s["cues"]]

print("EXTRA L05 CHECKS (headless Chrome, channel=chrome)")
print("  HTTP status:", resp.status)
print("  Manifest script src:", result["scriptSrc"])
print("  Section cue counts:", result["sections"], "total:", result["total"])
print("  Page errors (uncaught):", len(page_errors), page_errors)
print("  Console errors:", len(console_errors), console_errors)
print("  Cues starting with forbidden label:", len(result["startsWithForbidden"]))
print("  Cues containing forbidden label:", len(result["containsForbidden"]))
print("  Disk manifest cues with forbidden label:",
      sum(1 for t in disk_texts if FORBIDDEN_PREFIX in t))
ok = (resp.status == 200
      and all("?v=8" in s for s in result["scriptSrc"])
      and result["total"] == 38
      and result["sections"] == {"sec_01_3d_space": 14,
                                  "sec_02_matrix3x3": 15,
                                  "sec_03_determinant3d": 9}
      and not page_errors and not console_errors
      and not result["startsWithForbidden"] and not result["containsForbidden"]
      and not any(FORBIDDEN_PREFIX in t for t in disk_texts))
print("EXTRA CHECKS:", "PASSED" if ok else "FAILED")
raise SystemExit(0 if ok else 1)
