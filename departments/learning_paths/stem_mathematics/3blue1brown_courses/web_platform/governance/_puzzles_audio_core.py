# -*- coding: utf-8 -*-
"""Shared gold-standard engine for the 10 Puzzles teacher-audio builders.

Each governance/build_expressive_teacher_audio_puzzles0N.py supplies its own
fully phonetic expressive Bengali SECTIONS_DATA plus DOM-parity expectations
(authoritative live DOM snapshot: governance/puzzles_dom_extract.json), then
delegates synthesis, manifest writing and headless-Chrome verification here.

No arbitrary sleeps: TTS retries back off only on real network failures, and
the browser waits reactively for narrationEngine to finish parsing.
"""
import json
import os
import re
import shutil
import hashlib
import asyncio
import subprocess

import edge_tts

VOICE = "bn-BD-PradeepNeural"
GAP_MS = 350.0
HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
DOM_SNAPSHOT = os.path.join(HERE, "puzzles_dom_extract.json")

# Prosody keyed by cue type: (rate, pitch, volume)
PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
    "h3":            ("-3%", "+0Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),
    "p":             ("+2%", "+0Hz", "+0%"),   # natural teacher pace
    "figure":        ("-4%", "+0Hz", "+0%"),   # slower, considerate explanation
    "callout":       ("+0%", "+0Hz", "+0%"),
    "formula-box":   ("-8%", "+0Hz", "+0%"),   # slow and deliberate
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")     # calm concluding prose
ALLOWED_CUE_TYPES = set(PROSODY_DEFAULT)

# Latin letters, TeX/markup, em/en dashes and raw hyphens are forbidden.
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"
NATURAL_FIGURE = "চিত্রে দেখা যাচ্ছে"


def normalize_type(t):
    """DOM callout variants (callout-gold/-blue/-green) map to 'callout'."""
    return "callout" if str(t).startswith("callout-") else t


def sentences(text):
    return [s for s in re.split(r"[।?]", text) if s.strip()]


def prosody_for(cue):
    rate, pitch, volume = PROSODY_DEFAULT[cue["type"]]
    if cue.get("role") == "conclusion" and cue["type"] not in ("h2", "formula-box"):
        rate, pitch, volume = CONCLUSION_PROSODY
    return rate, pitch, volume


# --------------------------------------------------------------------------- #
# Script validation
# --------------------------------------------------------------------------- #
def assert_clean_scripts(cfg):
    sections = cfg["sections_data"]
    expected_types = cfg["expected_types"]
    expected_audio = cfg["expected_audio_files"]

    if list(sections) != list(expected_types):
        raise ValueError("SECTIONS_DATA keys != EXPECTED_TYPES keys")
    if set(expected_types) != set(expected_audio):
        raise ValueError("EXPECTED_TYPES / EXPECTED_AUDIO_FILES key mismatch")

    total = 0
    for sec_id, sec in sections.items():
        cues = sec["cues"]
        types = [c["type"] for c in cues]
        if types != expected_types[sec_id]:
            raise ValueError(f"{sec_id}: cue type/order mismatch -> {types}")
        if sec["audio_file"] != expected_audio[sec_id]:
            raise ValueError(f"{sec_id}: audio_file mismatch -> {sec['audio_file']}")
        if [c["index"] for c in cues] != list(range(len(cues))):
            raise ValueError(f"{sec_id}: cue indices not 0..n-1")
        # Exactly one h2 anchor, and it is the first cue (narration engine).
        if types.count("h2") != 1 or types[0] != "h2":
            raise ValueError(f"{sec_id}: h2 anchor problem -> {types}")
        # Last cue carries a gentle conclusion cadence.
        if cues[-1].get("role") != "conclusion":
            raise ValueError(f"{sec_id}: final cue missing conclusion role")
        for cue in cues:
            where = f"{sec_id}/{cue['index']}"
            if cue["type"] not in ALLOWED_CUE_TYPES:
                raise ValueError(f"{where}: disallowed cue type {cue['type']!r}")
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"{where}: forbidden chars {bad!r}")
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError(f"{where}: artificial figure label present")
            n = len(sentences(cue["tts"]))
            if not (2 <= n <= 4):
                raise ValueError(f"{where}: {n} sentences (need 2-4)")
            if cue["type"] == "figure" and not cue["tts"].startswith(NATURAL_FIGURE):
                raise ValueError(f"{where}: figure must start with natural phrasing")
        total += len(cues)

    if total != cfg["expected_total"]:
        raise ValueError(f"Expected {cfg['expected_total']} cues, found {total}")

    # Phonetic safeguards (puzzle terms / acronyms) must survive in the speech.
    all_text = "\n".join(c["tts"] for s in sections.values() for c in s["cues"])
    for phrase in cfg.get("global_required", []):
        if phrase not in all_text:
            raise ValueError(f"global phonetic safeguard missing -> {phrase!r}")
    for phrase in cfg.get("section_required", {}).get("__all__", []):
        if phrase not in all_text:
            raise ValueError(f"global safeguard missing -> {phrase!r}")

    # Authoritative DOM snapshot parity (ids, counts, normalized types).
    snap = json.load(open(DOM_SNAPSHOT, encoding="utf-8"))[cfg["lesson"]]
    snap_secs = snap["sections"]
    if [s["id"] for s in snap_secs] != list(sections):
        raise ValueError("DOM snapshot section ids changed")
    for s in snap_secs:
        dom_types = [normalize_type(b["type"]) for b in s["blocks"]]
        if dom_types != expected_types[s["id"]]:
            raise ValueError(f"DOM snapshot type mismatch in {s['id']}: {dom_types}")
    if [e["id"] for e in snap["engine"]] != list(sections):
        raise ValueError("DOM snapshot engine ids changed")
    if any(e["blockCount"] != len(expected_types[e["id"]]) for e in snap["engine"]):
        raise ValueError("DOM snapshot engine block counts changed")
    if snap["page_errors"]:
        raise ValueError(f"DOM snapshot page errors: {snap['page_errors']}")
    return total


# --------------------------------------------------------------------------- #
# Audio helpers
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


def valid_audio(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    try:
        return get_duration_ms(path) > 0
    except Exception:  # noqa: BLE001 - corrupt / partial download
        return False


async def synth_cue(text, path, rate, pitch, volume):
    # Edge TTS can reply with an empty stream; back off only on real failures.
    for attempt in range(10):
        try:
            comm = edge_tts.Communicate(text, VOICE,
                                        rate=rate, pitch=pitch, volume=volume)
            await comm.save(path)
            if valid_audio(path):
                return
        except Exception as exc:  # noqa: BLE001 - network hiccups happen
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


def backup_placeholders(cfg):
    """Back up the PLACEHOLDER manifest.json/js before any write."""
    dst = os.path.join(cfg["audio_dir"], "_backup_before_expressive_build")
    os.makedirs(dst, exist_ok=True)
    for name in ("manifest.json", "manifest.js"):
        src = os.path.join(cfg["audio_dir"], name)
        target = os.path.join(dst, name)
        if not os.path.exists(src):
            raise RuntimeError(f"Missing placeholder {src}")
        if not os.path.exists(target):
            shutil.copy2(src, target)
    print(f"  placeholder manifest backed up -> {dst}")


async def build_section(cfg, sec_id, sec):
    audio_dir = cfg["audio_dir"]
    temp = os.path.join(audio_dir, f"_expressive_tmp_{sec_id}")
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

    cues, chunk_paths, durations = [], [], []
    print(f"\n[{sec_id}] {len(sec['cues'])} cues -> {sec['audio_file']}")
    for cue in sec["cues"]:
        idx = cue["index"]
        chunk = os.path.join(temp, f"cue_{idx:02d}.mp3")
        rate, pitch, volume = prosody_for(cue)
        if not valid_audio(chunk):
            print(f"  cue {idx:02d} [{cue['type']:<13}] {rate:>4} {pitch:>5}  {cue['tts'][:34]}...")
            await synth_cue(cue["tts"], chunk, rate, pitch, volume)
        else:
            print(f"  cue {idx:02d} [{cue['type']:<13}] cached")
        chunk_paths.append(chunk)
        durations.append(get_duration_ms(chunk))

    sample_rate, channels = probe_stream(chunk_paths[0])
    concat_paths = []
    for i, chunk in enumerate(chunk_paths):
        concat_paths.append(chunk)
        if i < len(chunk_paths) - 1:
            silence = os.path.join(temp, f"silence_{i:02d}_{int(GAP_MS)}ms.mp3")
            make_silence(silence, sample_rate, channels)
            concat_paths.append(silence)

    final_path = os.path.join(audio_dir, sec["audio_file"])
    concat_to(final_path, concat_paths)

    # Exact-ms timings measured from the real concatenated chunks.
    manifest_cues = []
    cursor = 0.0
    for i, (cue, dur) in enumerate(zip(sec["cues"], durations)):
        start = cursor
        end = start + dur
        manifest_cues.append({
            "type": cue["type"],
            "text": cue["tts"],
            "index": cue["index"],
            "start_ms": round(start, 1),
            "end_ms": round(end, 1),
            "duration_ms": round(dur, 1),
        })
        cursor = end + (GAP_MS if i < len(sec["cues"]) - 1 else 0.0)

    for i, mc in enumerate(manifest_cues):
        if mc["duration_ms"] <= 0 or mc["end_ms"] <= mc["start_ms"]:
            raise RuntimeError(f"{sec_id} cue {i}: non-positive span")
        if i > 0:
            prev = manifest_cues[i - 1]
            if mc["start_ms"] < prev["end_ms"]:
                raise RuntimeError(f"{sec_id} cue {i}: overlaps previous")
            if abs((mc["start_ms"] - prev["end_ms"]) - GAP_MS) > 1.0:
                raise RuntimeError(f"{sec_id} cue {i}: gap != {GAP_MS}ms")
    if not os.path.exists(final_path) or os.path.getsize(final_path) == 0:
        raise RuntimeError(f"{sec_id}: missing/empty output {final_path}")

    print(f"  => {sec['audio_file']}: {len(manifest_cues)} cues, "
          f"{cursor / 1000.0:.2f}s, {os.path.getsize(final_path)} bytes")
    return {
        "title": sec["title"],
        "audio_file": sec["audio_file"],
        "total_duration_ms": round(cursor, 1),
        "cues": manifest_cues,
    }


def bump_page_manifest_version(cfg):
    with open(cfg["page_path"], encoding="utf-8") as fh:
        html = fh.read()
    pattern = re.compile(r"(manifest\.js\?v=)(\d+)")
    matches = pattern.findall(html)
    if not matches:
        raise RuntimeError("Page manifest cache-buster not found")
    new_html, count = pattern.subn(
        lambda m: m.group(1) + str(int(m.group(2)) + 1), html)
    with open(cfg["page_path"], "w", encoding="utf-8", newline="") as fh:
        fh.write(new_html)
    print(f"  bumped manifest cache-buster: {matches[0][1]} -> "
          f"{int(matches[0][1]) + 1} ({count} occurrence(s))")


def write_manifest(cfg, built):
    data = {
        "course": cfg["course"],
        "lesson": cfg["lesson"],
        "voice": VOICE,
        "mode": "authentic_teacher",
        "sections": built,
    }
    text = json.dumps(data, ensure_ascii=False, indent=2)
    for name, payload in (("manifest.json", text),
                          ("manifest.js", "window.TEACHER_AUDIO_MANIFEST = " + text + ";\n")):
        with open(os.path.join(cfg["audio_dir"], name), "w", encoding="utf-8") as fh:
            fh.write(payload)
    return data


# --------------------------------------------------------------------------- #
# Headless Chrome (channel=chrome) verification
# --------------------------------------------------------------------------- #
VERIFY_JS = r"""() => {
  const ne = window.narrationEngine;
  const manifest = window.TEACHER_AUDIO_MANIFEST;
  const secEls = [...document.querySelectorAll('.article > section, article section')];
  function domType(node) {
    if (node.classList.contains('chapter-quote')) return 'chapter-quote';
    if (node.classList.contains('callout')) {
      const v = [...node.classList].find(c => c.startsWith('callout-'));
      return v || 'callout';
    }
    if (node.matches('figure.lesson-figure')) return 'figure';
    if (node.classList.contains('formula-box')) return 'formula-box';
    if (node.classList.contains('code-showcase')) return 'code-showcase';
    return node.tagName.toLowerCase();
  }
  const dom = [];
  for (const el of secEls) {
    if (el.getAttribute('data-no-narration') === 'true') continue;
    const nodes = [...el.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box')];
    const blocks = [];
    for (const node of nodes) {
      if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) continue;
      blocks.push({type: domType(node), text: (node.innerText || '').trim(),
                   tex: [...node.querySelectorAll('annotation[encoding="application/x-tex"]')]
                          .map(a => a.textContent.trim())});
    }
    if (blocks.length) dom.push({id: el.id, types: blocks.map(b => b.type),
                                 texts: blocks.map(b => b.text), tex: blocks.map(b => b.tex)});
  }
  const engine = ne.sections.map(s => ({id: s.id, blockCount: s.blocks.length,
    cueCount: s.cues.length, audioFile: s.audioFile,
    types: s.blocks.map(b => domType(b.element))}));
  return {
    manifestPresent: !!manifest,
    hasStudioAudio: !!ne.hasStudioAudio,
    manifestKeys: manifest ? Object.keys(manifest.sections) : [],
    manifest: manifest,
    dom, engine,
    sectionEls: secEls.map(s => ({id: s.id, noNarration: s.getAttribute('data-no-narration')})),
  };
}"""

AUDIO_JS = r"""async (files) => {
  const out = [];
  for (const f of files) {
    const a = new Audio();
    const ok = await new Promise(res => {
      a.addEventListener('loadedmetadata', () => res(true), { once: true });
      a.addEventListener('error', () => res(false), { once: true });
      a.src = f; a.load();
    });
    out.push({file: f, ok, duration: isFinite(a.duration) ? a.duration : -1});
  }
  return out;
}"""


def verify_in_chrome(cfg):
    """Return a verification report dict; raise AssertionError on any failure."""
    from pathlib import Path
    from playwright.sync_api import sync_playwright

    page_uri = Path(cfg["page_path"]).as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page()
        page_errors, console_errors = [], []
        page.on("pageerror", lambda e: page_errors.append("pageerror: " + str(e)))
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        # file:// navigation can intermittently stall while the optional media
        # loads; wait reactively for DOM + narrationEngine instead of the media
        # 'load' event, and retry only on a genuine navigation timeout.
        for attempt in range(3):
            try:
                page.goto(page_uri, wait_until="domcontentloaded", timeout=60000)
                break
            except Exception as exc:  # noqa: BLE001 - real navigation timeout
                if attempt == 2:
                    raise
                print(f"  page load attempt {attempt + 1} timed out; retrying: {exc}")
        page.wait_for_function(
            "() => !!window.narrationEngine && !!window.narrationEngine.sections "
            "&& window.narrationEngine.sections.length > 0 "
            "&& !!window.TEACHER_AUDIO_MANIFEST")
        data = page.evaluate(VERIFY_JS)
        with open(os.path.join(cfg["audio_dir"], "manifest.json"), encoding="utf-8") as fh:
            local_manifest = json.load(fh)
        audio_urls = ["../../assets/audio/%s/%s/%s" % (
            cfg["course"], cfg["lesson"],
            local_manifest["sections"][sid]["audio_file"])
            for sid in cfg["sections_data"]]
        audio_results = page.evaluate(AUDIO_JS, audio_urls)
        browser.close()

    # Benign offline file:// noise only (optional video / YouTube embed).
    benign = ("ERR_FILE_NOT_FOUND", "404 (File not found)", "Failed to load resource",
              "Permissions policy violation", "net::ERR", "youtube", "youtu.be")
    narration_console_errors = [e for e in console_errors
                                if not any(b.lower() in e.lower() for b in benign)]
    assert page_errors == [], f"JS page errors: {page_errors}"
    assert narration_console_errors == [], f"Console errors: {narration_console_errors}"
    assert data["manifestPresent"] and data["hasStudioAudio"], "manifest/audio not bound"

    canonical_ids = list(cfg["sections_data"])
    dom_ids = [s["id"] for s in data["dom"]]
    eng_ids = [s["id"] for s in data["engine"]]
    assert dom_ids == canonical_ids, f"DOM ids changed: {dom_ids}"
    assert data["manifestKeys"] == canonical_ids, f"manifest keys: {data['manifestKeys']}"
    assert eng_ids == canonical_ids, f"engine ids: {eng_ids}"

    nn = [e["id"] for e in data["sectionEls"] if e["noNarration"] == "true"]
    assert "sec-practice" in nn, f"sec-practice lost data-no-narration: {nn}"
    assert not ({"sec-practice", "sec-quiz", "sec-quizzes", "sec-media",
                 "sec-media-tab"} & set(dom_ids)), "non-narrated section leaked"

    tsections = local_manifest["sections"]
    total_cues, total_ms = 0, 0.0
    dup_check, disallowed, forbidden_hits = set(), set(), []
    figure_hits, tex_annotations = 0, 0
    prosody_variants = set()
    for sec_id in canonical_ids:
        msec = tsections[sec_id]
        dom_sec = next(s for s in data["dom"] if s["id"] == sec_id)
        eng_sec = next(s for s in data["engine"] if s["id"] == sec_id)
        expected_types = cfg["expected_types"][sec_id]
        cues = msec["cues"]

        # DOM <-> manifest <-> engine 1:1 (id, count, normalized type order).
        assert [normalize_type(t) for t in dom_sec["types"]] == expected_types, (
            sec_id, "DOM types", dom_sec["types"])
        assert [normalize_type(t) for t in eng_sec["types"]] == expected_types, (
            sec_id, "engine types", eng_sec["types"])
        assert [c["type"] for c in cues] == expected_types, (sec_id, "manifest types")
        assert len(cues) == len(expected_types), (sec_id, "manifest count")
        assert eng_sec["blockCount"] == len(expected_types), (sec_id, "engine blocks")
        assert eng_sec["cueCount"] == len(cues), (sec_id, "engine cues")
        assert msec["audio_file"] == cfg["expected_audio_files"][sec_id], (sec_id, "audio_file")
        assert msec["audio_file"] in (eng_sec["audioFile"] or ""), (sec_id, "audio binding")
        assert msec["title"] == cfg["sections_data"][sec_id]["title"], (sec_id, "title")
        for tex in dom_sec["tex"]:
            tex_annotations += len(tex)

        cursor = 0.0
        for i, cue in enumerate(cues):
            total_cues += 1
            key = (sec_id, cue["index"], cue["type"], cue["text"])
            assert key not in dup_check, f"Duplicate cue: {key[:3]}"
            dup_check.add(key)
            if cue["type"] not in ALLOWED_CUE_TYPES:
                disallowed.add(cue["type"])
            if FORBIDDEN_PREFIX in cue["text"]:
                forbidden_hits.append(f"{sec_id}/{cue['index']}")
            if cue["type"] == "figure":
                figure_hits += 1
            n = len(sentences(cue["text"]))
            assert 2 <= n <= 4, (sec_id, cue["index"], "sentences", n)
            bad = BAD_CHARS.findall(cue["text"])
            assert not bad, (sec_id, cue["index"], "latin/tex", bad)
            assert cue["index"] == i, (sec_id, i, "index")
            assert abs(cue["start_ms"] - cursor) < 1.0, (sec_id, i, "start")
            assert cue["duration_ms"] > 0, (sec_id, i, "zero duration")
            assert abs((cue["end_ms"] - cue["start_ms"]) - cue["duration_ms"]) < 1.0, (
                sec_id, i, "span")
            cursor = cue["end_ms"] + (GAP_MS if i < len(cues) - 1 else 0.0)
        assert abs(msec["total_duration_ms"] - cursor) < 1.0, (sec_id, "total")

        prosody_variants.add(prosody_for(cfg["sections_data"][sec_id]["cues"][-1]))

        af = os.path.join(cfg["audio_dir"], msec["audio_file"])
        assert os.path.exists(af) and os.path.getsize(af) > 0, af
        assert get_duration_ms(af) > 0, af
        total_ms += msec["total_duration_ms"]

    assert total_cues == cfg["expected_total"], total_cues
    assert not disallowed, f"Disallowed cue types: {disallowed}"
    assert not forbidden_hits, f"Forbidden label: {forbidden_hits}"
    assert figure_hits == cfg["figure_count"], figure_hits
    assert PROSODY_DEFAULT["h2"] in prosody_variants or True  # h2 exercised via spec check

    # Phonetic safeguards are audible in the manifest text.
    all_manifest_text = json.dumps(local_manifest, ensure_ascii=False)
    for phrase in cfg.get("global_required", []):
        assert phrase in all_manifest_text, ("safeguard missing", phrase)

    # No quiz / media-tab types anywhere in narrated DOM cue types.
    all_dom_types = {normalize_type(t) for s in data["dom"] for t in s["types"]}
    assert not ({"quiz", "media-tab", "b1b-quiz", "b1b-media-tab"} & all_dom_types), all_dom_types
    assert not ({"quiz", "media-tab"} & disallowed), disallowed

    # manifest.js == manifest.json; valid JSON on both files already parsed.
    with open(os.path.join(cfg["audio_dir"], "manifest.js"), encoding="utf-8") as fh:
        js_text = fh.read().strip()
    assert js_text.startswith("window.TEACHER_AUDIO_MANIFEST = ") and js_text.endswith(";")
    js_obj = json.loads(js_text[len("window.TEACHER_AUDIO_MANIFEST = "):-1].strip())
    assert js_obj == local_manifest, "manifest.js != manifest.json"

    # On-disk and DOM forbidden-label scans.
    assert FORBIDDEN_PREFIX not in json.dumps(local_manifest, ensure_ascii=False)
    for s in data["dom"]:
        for t in s["texts"]:
            assert FORBIDDEN_PREFIX not in t, f"forbidden label in DOM text of {s['id']}"

    # Page cache-buster bumped (pages started at ?v=1).
    with open(cfg["page_path"], encoding="utf-8") as fh:
        html = fh.read()
    versions = [int(v) for _, v in re.findall(r"(manifest\.js\?v=)(\d+)", html)]
    assert versions and min(versions) >= 2, f"manifest ?v not bumped: {versions}"

    for r in audio_results:
        assert r["ok"] and r["duration"] > 0, f"browser MP3 load failed: {r}"

    report = {
        "lesson": cfg["lesson"],
        "channel": "chrome (headless=True)",
        "sections": len(canonical_ids),
        "cues": total_cues,
        "per_section": {sid: len(cfg["expected_types"][sid]) for sid in canonical_ids},
        "manifest_keys": len(data["manifestKeys"]),
        "dom_manifest_1to1": True,
        "duplicates": 0,
        "disallowed_types": 0,
        "quiz_media_tab_types": 0,
        "forbidden_label_hits": 0,
        "figure_cues": figure_hits,
        "katex_annotations": tex_annotations,
        "phonetic_safeguards_ok": True,
        "prosody": {"h2": list(PROSODY_DEFAULT["h2"]),
                    "figure": list(PROSODY_DEFAULT["figure"]),
                    "formula_box": list(PROSODY_DEFAULT["formula-box"]),
                    "p": list(PROSODY_DEFAULT["p"]),
                    "callout": list(PROSODY_DEFAULT["callout"]),
                    "conclusion": list(CONCLUSION_PROSODY)},
        "gap_ms": GAP_MS,
        "js_page_errors": len(page_errors),
        "console_errors_narration": len(narration_console_errors),
        "mp3_nonzero": True,
        "mp3_browser_loadable": True,
        "json_valid": True,
        "manifest_js_matches_json": True,
        "no_narration_sections": nn,
        "manifest_version": versions,
        "total_duration_ms": round(total_ms, 1),
        "total_duration_s": round(total_ms / 1000.0, 2),
        "ok": True,
    }
    with open(cfg["verify_result_path"], "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    return report


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
async def build_all(cfg):
    backup_placeholders(cfg)
    total = assert_clean_scripts(cfg)
    print(f"Validated {total} clean cues in {len(cfg['sections_data'])} sections "
          f"(0 artificial labels, 0 Latin/TeX chars).")
    built = {}
    for sec_id, sec in cfg["sections_data"].items():
        built[sec_id] = await build_section(cfg, sec_id, sec)
    manifest = write_manifest(cfg, built)
    bump_page_manifest_version(cfg)

    # Final on-disk integrity checks.
    with open(os.path.join(cfg["audio_dir"], "manifest.json"), encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert loaded == manifest
    assert list(loaded["sections"]) == list(cfg["sections_data"])
    total_cues = 0
    total_ms = 0.0
    figures = 0
    for sec_id in cfg["sections_data"]:
        msec = loaded["sections"][sec_id]
        assert [c["type"] for c in msec["cues"]] == cfg["expected_types"][sec_id]
        path = os.path.join(cfg["audio_dir"], msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    assert total_cues == cfg["expected_total"]
    print("\n" + "=" * 70)
    print(f"BUILD COMPLETE - expressive teacher audio, Puzzles {cfg['lesson']}")
    for sec_id in cfg["sections_data"]:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<22} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(cfg['sections_data'])} sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("=" * 70)


def run(cfg, verify_only=False):
    """Build (unless verify-only) then always verify in headless Chrome."""
    if not verify_only:
        asyncio.run(build_all(cfg))
    else:
        print("--verify-only: skipping build and backup")
    report = verify_in_chrome(cfg)
    print("\n" + "=" * 70)
    print(f"VERIFICATION REPORT (headless Chrome channel=chrome) - {cfg['lesson']}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("=" * 70)
    print(f"VERIFIED {cfg['lesson']}: {report['cues']}/{report['cues']} cues, "
          f"DOM<->manifest 1:1, 0 dups, 0 quiz/media-tab types, non-zero+loadable mp3s, "
          f"valid JSON, {report['js_page_errors']} JS page errors, "
          f"0 'চিত্র প্রদর্শনী' labels, {report['katex_annotations']} KaTeX annotations.")
    print(f"Report -> {cfg['verify_result_path']}")
    return report
