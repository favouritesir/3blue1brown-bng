# -*- coding: utf-8 -*-
"""
Shared engine for the gold-standard TEACHER NARRATION AUDIO rebuilds of the
new Number Theory lessons (01..03).

Deterministic, re-runnable and self-contained with respect to input data: every
spoken script lives in the matching build_expressive_teacher_audio_nt0N.py.

Pipeline (identical to the calc02 / nn01 gold builders):
  * embedded expressive Bengali scripts, one per live DOM narration block
  * figure cues are genuine 2-4 sentence explanations, never "চিত্র প্রদর্শনী"
  * phonetic safeguards; no TeX, Latin letters, dashes or markup
  * per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=)
  * real 350 ms silence between cues; ffmpeg -c copy concatenation
  * exact-ms manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST)
  * page manifest.js cache-buster bumped (1 -> 2)
  * headless Chrome (channel=chrome) verification against the live DOM
"""
import os
import re
import json
import sys
import hashlib
import asyncio
import subprocess

import edge_tts

VOICE = "bn-BD-PradeepNeural"
GAP_MS = 350.0
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))            # .../governance
WORKSPACE = os.path.dirname(SCRIPT_DIR)                             # .../web_platform

PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),
    "h3":            ("-3%", "+0Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),
    "p":             ("+2%", "+0Hz", "+0%"),
    "figure":        ("-4%", "+0Hz", "+0%"),
    "callout":       ("+0%", "+0Hz", "+0%"),
    "formula-box":   ("-8%", "+0Hz", "+0%"),
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")
ALLOWED_CUE_TYPES = set(PROSODY_DEFAULT) | {"conclusion"}

BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"
DISALLOWED_TYPES = {"quiz", "media-tab", "b1b-quiz", "b1b-media-tab"}


class LessonConfig:
    def __init__(self, number, course, title, sections_data, expected_types,
                 expected_audio_files, expected_count, total_cues,
                 required_phonetic):
        self.number = number
        self.lesson = f"lesson_{number:02d}"
        self.course = course
        self.title = title
        self.sections_data = sections_data
        self.expected_types = expected_types
        self.expected_audio_files = expected_audio_files
        self.expected_count = expected_count
        self.total_cues = total_cues
        self.required_phonetic = required_phonetic
        self.audio_dir = os.path.join(WORKSPACE, "assets", "audio", course, self.lesson)
        self.page_path = os.path.join(WORKSPACE, "courses", course, self.lesson + ".html")


# --------------------------------------------------------------------------- #
# Script validation
# --------------------------------------------------------------------------- #
def assert_clean_scripts(cfg):
    for sec_id, sec in cfg.sections_data.items():
        for cue in sec["cues"]:
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars {bad!r} in {cue['tts']!r}")
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: artificial figure label present")
            if cue["type"] not in PROSODY_DEFAULT:
                raise ValueError(f"{sec_id} cue {cue['index']}: unknown cue type {cue['type']!r}")
            # Only p / callout cues carry the concluding role so figure (-4%)
            # and formula-box (-8%) prosody is never overridden.
            if cue.get("role") == "conclusion" and cue["type"] not in ("p", "callout"):
                raise ValueError(f"{sec_id} cue {cue['index']}: invalid conclusion role")

    joined = "\n".join(c["tts"] for s in cfg.sections_data.values() for c in s["cues"])
    for token, label in cfg.required_phonetic.items():
        if token not in joined:
            raise ValueError(f"Missing phonetic {label}: {token!r}")

    if set(cfg.sections_data) != set(cfg.expected_types):
        raise ValueError("Section keys do not match EXPECTED_TYPES")
    total = 0
    for sec_id, sec in cfg.sections_data.items():
        types = [c["type"] for c in sec["cues"]]
        if types != cfg.expected_types[sec_id]:
            raise ValueError(f"{sec_id}: cue type/order mismatch -> {types}")
        if sec["audio_file"] != cfg.expected_audio_files[sec_id]:
            raise ValueError(f"{sec_id}: audio_file mismatch")
        if [c["index"] for c in sec["cues"]] != list(range(len(sec["cues"]))):
            raise ValueError(f"{sec_id}: cue indices not 0..n-1")
        if len(sec["cues"]) != cfg.expected_count[sec_id]:
            raise ValueError(f"{sec_id}: expected {cfg.expected_count[sec_id]} cues")
        total += len(sec["cues"])
    if total != cfg.total_cues:
        raise ValueError(f"Expected {cfg.total_cues} cues, found {total}")

    for sec_id, sec in cfg.sections_data.items():
        for cue in sec["cues"]:
            if cue["type"] == "figure":
                sentences = [s for s in cue["tts"].split("।") if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(f"{sec_id} cue {cue['index']}: figure has {len(sentences)} sentences")


# --------------------------------------------------------------------------- #
# Audio primitives
# --------------------------------------------------------------------------- #
def get_duration_ms(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout.strip()
    ms = float(out) * 1000.0
    if ms <= 0:
        raise RuntimeError(f"Non-positive duration for {path}: {ms}")
    return ms


def probe_stream(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=sample_rate,channels", "-of", "json", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout
    st = json.loads(out)["streams"][0]
    return int(st["sample_rate"]), int(st["channels"])


def prosody_for(cue):
    rate, pitch, volume = PROSODY_DEFAULT[cue["type"]]
    if cue.get("role") == "conclusion" and cue["type"] not in ("h2", "formula-box"):
        rate, pitch, volume = CONCLUSION_PROSODY
    return rate, pitch, volume


def valid_audio(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    try:
        return get_duration_ms(path) > 0
    except Exception:  # noqa: BLE001 - corrupt / partial download
        return False


async def synth_cue(text, path, rate, pitch, volume):
    # Edge TTS occasionally replies with an empty stream. Back off and retry;
    # this is a network-response wait, not an arbitrary fixed delay.
    for attempt in range(10):
        try:
            comm = edge_tts.Communicate(text, VOICE,
                                        rate=rate, pitch=pitch, volume=volume)
            await comm.save(path)
            if valid_audio(path):
                return
        except Exception as exc:  # noqa: BLE001 - transient network hiccup
            print(f"    attempt {attempt + 1} failed: {exc}")
        await asyncio.sleep(min(0.5 * (2 ** attempt), 8.0))
    raise RuntimeError(f"Failed to synthesise cue: {text[:40]}...")


def make_silence(path, sample_rate, channels, seconds=GAP_MS / 1000.0):
    layout = "mono" if channels == 1 else "stereo"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-f", "lavfi", "-i", f"anullsrc=r={sample_rate}:cl={layout}",
         "-t", f"{seconds:.3f}",
         "-c:a", "libmp3lame", "-b:a", "64k", path],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True,
    )
    if os.path.getsize(path) == 0:
        raise RuntimeError("Failed to create silence chunk")


def concat_to(final_path, chunk_paths):
    list_path = os.path.splitext(final_path)[0] + "_expressive_concat.txt"
    with open(list_path, "w", encoding="utf-8") as fh:
        for p in chunk_paths:
            fh.write("file '" + p.replace(os.sep, "/") + "'\n")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", list_path, "-c", "copy", final_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True,
    )
    os.remove(list_path)


async def build_section(cfg, sec_id, sec):
    temp = os.path.join(cfg.audio_dir, f"_expressive_tmp_{sec_id}")
    os.makedirs(temp, exist_ok=True)

    sig = hashlib.sha256(
        json.dumps(sec, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    sig_path = os.path.join(temp, "scripts.sha256")
    old = ""
    if os.path.exists(sig_path):
        with open(sig_path, encoding="utf-8") as fh:
            old = fh.read().strip()
    if old != sig:
        for name in os.listdir(temp):
            if name.endswith(".mp3"):
                os.remove(os.path.join(temp, name))
        with open(sig_path, "w", encoding="utf-8") as fh:
            fh.write(sig)

    cues = sec["cues"]
    chunk_paths, durations = [], []
    print(f"\n[{sec_id}] {len(cues)} cues -> {sec['audio_file']}")
    for cue in cues:
        idx = cue["index"]
        chunk = os.path.join(temp, f"cue_{idx:02d}.mp3")
        rate, pitch, volume = prosody_for(cue)
        if not valid_audio(chunk):
            print(f"  cue {idx:02d} [{cue['type']:<13}] {rate:>4} {pitch:>5}  {cue['tts'][:30]}...")
            await synth_cue(cue["tts"], chunk, rate, pitch, volume)
        else:
            print(f"  cue {idx:02d} [{cue['type']:<13}] cached")
        chunk_paths.append(chunk)
        durations.append(get_duration_ms(chunk))

    sample_rate, channels = probe_stream(chunk_paths[0])
    silence = os.path.join(temp, "silence_350ms.mp3")
    make_silence(silence, sample_rate, channels)

    concat_paths = []
    for i, chunk in enumerate(chunk_paths):
        concat_paths.append(chunk)
        if i < len(chunk_paths) - 1:
            concat_paths.append(silence)

    final_path = os.path.join(cfg.audio_dir, sec["audio_file"])
    concat_to(final_path, concat_paths)

    manifest_cues, cursor = [], 0.0
    for i, (cue, dur) in enumerate(zip(cues, durations)):
        start = cursor
        end = start + dur
        manifest_cues.append({
            "index": cue["index"],
            "type": cue["type"],
            "text": cue["tts"],
            "start_ms": round(start, 1),
            "end_ms": round(end, 1),
            "duration_ms": round(dur, 1),
        })
        cursor = end + (GAP_MS if i < len(cues) - 1 else 0.0)

    for i, mc in enumerate(manifest_cues):
        if mc["duration_ms"] <= 0:
            raise RuntimeError(f"{sec_id} cue {i}: zero duration")
        if mc["end_ms"] <= mc["start_ms"]:
            raise RuntimeError(f"{sec_id} cue {i}: non-positive span")
        if i > 0:
            prev = manifest_cues[i - 1]
            if mc["start_ms"] < prev["end_ms"]:
                raise RuntimeError(f"{sec_id} cue {i}: overlaps previous cue")
            if abs((mc["start_ms"] - prev["end_ms"]) - GAP_MS) > 1.0:
                raise RuntimeError(f"{sec_id} cue {i}: gap is not {GAP_MS} ms")

    if not os.path.exists(final_path) or os.path.getsize(final_path) == 0:
        raise RuntimeError(f"{sec_id}: missing/empty output {final_path}")
    print(f"  => {sec['audio_file']}: {len(manifest_cues)} cues, "
          f"{cursor / 1000.0:.2f}s, {os.path.getsize(final_path)} bytes")

    return {
        "section_id": sec_id,
        "title": sec["title"],
        "audio_file": sec["audio_file"],
        "total_duration_ms": round(cursor, 1),
        "cues": manifest_cues,
    }


def bump_page_manifest_version(cfg):
    with open(cfg.page_path, encoding="utf-8") as fh:
        html = fh.read()
    pattern = re.compile(r"(manifest\.js\?v=)(\d+)")
    matches = pattern.findall(html)
    if not matches:
        raise RuntimeError("Page manifest cache-buster not found")
    new_html, count = pattern.subn(
        lambda m: m.group(1) + str(int(m.group(2)) + 1), html)
    with open(cfg.page_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_html)
    print(f"  bumped manifest cache-buster: {matches[0][1]} -> {int(matches[0][1]) + 1} "
          f"({count} occurrence(s))")


async def build_all(cfg):
    assert_clean_scripts(cfg)
    print(f"Validated {sum(len(s['cues']) for s in cfg.sections_data.values())} clean cues "
          f"in {len(cfg.sections_data)} sections.")

    manifest_sections = {}
    for sec_id, sec in cfg.sections_data.items():
        manifest_sections[sec_id] = await build_section(cfg, sec_id, sec)

    manifest_data = {
        "course": cfg.course,
        "lesson": cfg.lesson,
        "title": cfg.title,
        "voice": VOICE,
        "mode": "authentic_teacher",
        "sections": manifest_sections,
    }
    json_text = json.dumps(manifest_data, ensure_ascii=False, indent=2)
    with open(os.path.join(cfg.audio_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        fh.write(json_text)
    with open(os.path.join(cfg.audio_dir, "manifest.js"), "w", encoding="utf-8") as fh:
        fh.write("window.TEACHER_AUDIO_MANIFEST = " + json_text + ";\n")

    bump_page_manifest_version(cfg)

    with open(os.path.join(cfg.audio_dir, "manifest.json"), encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert set(loaded["sections"]) == set(cfg.sections_data)
    total_cues, total_ms, figures = 0, 0.0, 0
    for sec_id in cfg.sections_data:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == len(cfg.expected_types[sec_id])
        assert [c["type"] for c in msec["cues"]] == cfg.expected_types[sec_id]
        path = os.path.join(cfg.audio_dir, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    assert total_cues == cfg.total_cues

    print("\n" + "=" * 66)
    print(f"BUILD COMPLETE - expressive teacher audio, Number Theory Lesson {cfg.number:02d}")
    for sec_id in cfg.sections_data:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<24} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(cfg.sections_data)} sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json is valid JSON; all mp3 files exist and are non-empty.")
    print("=" * 66)


# --------------------------------------------------------------------------- #
# Headless Chrome verification (channel=chrome)
# --------------------------------------------------------------------------- #
VERIFY_JS = r"""() => {
  const ne = window.narrationEngine;
  const manifest = window.TEACHER_AUDIO_MANIFEST;
  const sectionEls = [...document.querySelectorAll('.article > section, article section')];

  function domType(node) {
    if (node.classList.contains('chapter-quote')) return 'chapter-quote';
    if (node.classList.contains('callout')) return 'callout';
    if (node.matches('figure.lesson-figure')) return 'figure';
    if (node.classList.contains('formula-box')) return 'formula-box';
    if (node.classList.contains('code-showcase')) return 'code-showcase';
    return node.tagName.toLowerCase();
  }

  const dom = [];
  for (const el of sectionEls) {
    if (el.getAttribute('data-no-narration') === 'true') continue;
    const nodes = [...el.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box')];
    const blocks = [];
    for (const node of nodes) {
      if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) continue;
      const anns = [...node.querySelectorAll('annotation[encoding="application/x-tex"]')]
                     .map(a => a.textContent);
      blocks.push({type: domType(node), tex: anns, text: node.innerText || ''});
    }
    dom.push({id: el.id, blocks});
  }

  const engine = ne.sections.map(s => ({
    id: s.id, blockCount: s.blocks.length, cueCount: s.cues.length,
    types: s.blocks.map(b => domType(b.element))
  }));

  return {
    manifestPresent: !!manifest,
    hasStudioAudio: !!ne.hasStudioAudio,
    manifestKeys: Object.keys(manifest ? manifest.sections : {}),
    manifest: manifest,
    dom: dom.map(s => ({id: s.id, types: s.blocks.map(b => b.type),
                        tex: s.blocks.filter(b => b.type === 'formula-box').map(b => b.tex)})),
    engine,
    sectionEls: sectionEls.map(s => ({id: s.id, noNarration: s.getAttribute('data-no-narration')}))
  };
}"""


def verify_in_chrome(cfg):
    from pathlib import Path
    from playwright.sync_api import sync_playwright

    page_uri = Path(cfg.page_path).as_uri()
    report = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page()
        page_errors = []
        page.on("pageerror", lambda e: page_errors.append("pageerror: " + str(e)))
        page.on("console", lambda m: page_errors.append("console.error: " + m.text)
                if m.type == "error" else None)
        page.goto(page_uri, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_function(
            "() => !!window.narrationEngine && !!window.narrationEngine.sections "
            "&& window.narrationEngine.sections.length > 0 "
            "&& !!window.TEACHER_AUDIO_MANIFEST",
            timeout=20000)
        data = page.evaluate(VERIFY_JS)
        browser.close()

    report["page_errors"] = page_errors
    assert page_errors == [], f"Page errors: {page_errors}"
    assert data["manifestPresent"], "window.TEACHER_AUDIO_MANIFEST missing"
    assert data["hasStudioAudio"], "Studio teacher audio not bound"

    mkeys = data["manifestKeys"]
    dom_ids = [s["id"] for s in data["dom"]]
    assert mkeys == dom_ids, f"Manifest/DOM section mismatch: {mkeys} vs {dom_ids}"
    assert mkeys == list(cfg.expected_types.keys()), f"Unexpected section keys: {mkeys}"
    assert "sec-lab" not in mkeys, "Non-narrated lab leaked into manifest"
    lab = [s for s in data["sectionEls"] if s["id"] == "sec-lab"]
    if lab:
        assert lab[0]["noNarration"] == "true", "Lab section lost data-no-narration"

    tsections = data["manifest"]["sections"]
    total_cues, dup_check, disallowed, forbidden_hits = 0, set(), set(), []
    total_ms, figure_count, ann_count = 0.0, 0, 0
    for sec_id in cfg.expected_types:
        msec = tsections[sec_id]
        dom_sec = next(s for s in data["dom"] if s["id"] == sec_id)
        eng_sec = next(s for s in data["engine"] if s["id"] == sec_id)
        cues = msec["cues"]
        expected_types = cfg.expected_types[sec_id]

        assert len(cues) == cfg.expected_count[sec_id], (sec_id, len(cues))
        assert len(dom_sec["types"]) == len(cues), (sec_id, "DOM block count", dom_sec["types"])
        assert [c["type"] for c in cues] == expected_types, (sec_id, "manifest types")
        assert dom_sec["types"] == expected_types, (sec_id, "DOM types", dom_sec["types"])
        assert eng_sec["types"] == expected_types, (sec_id, "engine types", eng_sec["types"])
        assert eng_sec["blockCount"] == len(cues) == eng_sec["cueCount"], sec_id

        for anns in dom_sec["tex"]:
            assert isinstance(anns, list) and any(t.strip() for t in anns), (sec_id, "missing TeX annotation")
            ann_count += len(anns)

        for c in cues:
            total_cues += 1
            key = (sec_id, c["index"], c["type"], c["text"])
            assert key not in dup_check, f"Duplicate cue: {key[:3]}"
            dup_check.add(key)
            if c["type"] not in ALLOWED_CUE_TYPES:
                disallowed.add(c["type"])
            if FORBIDDEN_PREFIX in c["text"]:
                forbidden_hits.append(f"{sec_id}/{c['index']}")
            if c["type"] == "figure":
                figure_count += 1
                sentences = [x for x in c["text"].split("।") if x.strip()]
                assert 2 <= len(sentences) <= 4, (sec_id, c["index"], len(sentences))

        cursor = 0.0
        for i, c in enumerate(cues):
            assert abs(c["start_ms"] - cursor) < 1.0, (sec_id, i, "start", c["start_ms"], cursor)
            assert c["duration_ms"] > 0, (sec_id, i, "zero duration")
            assert abs((c["end_ms"] - c["start_ms"]) - c["duration_ms"]) < 1.0, (sec_id, i)
            cursor = c["end_ms"] + (GAP_MS if i < len(cues) - 1 else 0.0)
        assert abs(msec["total_duration_ms"] - cursor) < 1.0, (sec_id, "total_duration_ms")

        af = os.path.join(cfg.audio_dir, msec["audio_file"])
        assert os.path.exists(af) and os.path.getsize(af) > 0, af
        total_ms += msec["total_duration_ms"]

    assert total_cues == cfg.total_cues, total_cues
    assert not disallowed, f"Disallowed cue types: {disallowed}"
    assert not forbidden_hits, f"Artificial figure label found: {forbidden_hits}"

    all_dom_types = [t for s in data["dom"] for t in s["types"]]
    assert not (DISALLOWED_TYPES & set(all_dom_types)), all_dom_types

    with open(os.path.join(cfg.audio_dir, "manifest.json"), encoding="utf-8") as fh:
        json_obj = json.load(fh)
    with open(os.path.join(cfg.audio_dir, "manifest.js"), encoding="utf-8") as fh:
        js_text = fh.read().strip()
    assert js_text.startswith("window.TEACHER_AUDIO_MANIFEST = ") and js_text.endswith(";")
    js_obj = json.loads(js_text[len("window.TEACHER_AUDIO_MANIFEST = "):-1].strip())
    assert js_obj == json_obj, "manifest.js != manifest.json"

    with open(cfg.page_path, encoding="utf-8") as fh:
        html = fh.read()
    versions = [int(v) for _, v in re.findall(r"(manifest\.js\?v=)(\d+)", html)]
    assert versions and min(versions) >= 2, f"manifest ?v not bumped: {versions}"

    report.update({
        "browser": "headless Chrome channel=chrome",
        "lesson": cfg.lesson,
        "sections": len(cfg.expected_types),
        "cues": total_cues,
        "per_section": {sid: cfg.expected_count[sid] for sid in cfg.expected_types},
        "figures": figure_count,
        "duplicates": 0,
        "disallowed_types": 0,
        "quiz_media_tab_types": 0,
        "forbidden_label_hits": 0,
        "page_errors": len(page_errors),
        "total_duration_ms": round(total_ms, 1),
        "total_duration_s": round(total_ms / 1000.0, 2),
        "katex_annotations": ann_count,
        "manifest_js_matches_json": True,
        "manifest_version": versions,
        "mp3s_nonzero": True,
        "json_valid": True,
        "ok": True,
    })
    return report


def main(cfg):
    verify_only = "--verify-only" in sys.argv[1:]
    if verify_only:
        print("Running headless Chrome verification only...")
    else:
        asyncio.run(build_all(cfg))
    report = verify_in_chrome(cfg)
    print("\n" + "=" * 66)
    print("VERIFICATION REPORT (headless Chrome channel=chrome)")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("=" * 66)
    if not report.get("ok"):
        raise SystemExit("VERIFICATION FAILED")
    print(f"VERIFIED: {cfg.total_cues}/{cfg.total_cues} cues, DOM<->manifest 1:1, "
          "0 dups, 0 quiz/media-tab types, non-zero mp3s, valid JSON, 0 page errors, "
          "0 'চিত্র প্রদর্শনী'.")
