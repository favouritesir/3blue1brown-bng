# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Why-Pi Lesson 04 (Bengali) to the
Lesson-01 / Calculus-02 gold standard.

Deterministic, re-runnable, self-contained:
  * 17 cues in 3 narrated sections with EXACTLY the same section
    IDs, audio_file names, cue types and cue order as the LIVE narrated DOM
    (narration_engine.parseContent selector, extracted in headless Chrome).
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Figure cues are genuine 2-4 sentence natural explanations - never the
    artificial label "চিত্র প্রদর্শনী".
  * Every script is clean spoken Bengali with phonetic safeguards:
    pi -> পাই, Basel -> বাসেল, Leibniz -> লাইবনিজ, Gaussian -> গাউসিয়ান,
    Wallis -> ওয়ালিস, integral -> ইন্টিগ্রাল, infinite -> অসীম,
    probability -> সম্ভাব্যতা, theta -> থিটা, tau -> টাউ, and so on.
    No TeX, LaTeX, backslashes, $, braces, brackets, em-dashes, raw hyphens or
    Latin letters.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
    h2 -5%/+2Hz, p +2%, figure -4%, callout +0%, formula-box -8%,
    conclusion -3%, chapter-quote -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with the
    exact-ms timings and the canonical DOM section keys.
  * Validates non-zero durations, zero overlap, valid JSON and non-empty mp3s.

Usage:  python governance/build_expressive_teacher_audio_why_pi004.py
"""

import os
import re
import json
import hashlib
import asyncio
import subprocess

import edge_tts

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
VOICE = "bn-BD-PradeepNeural"
GAP_MS = 350.0
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))            # .../governance
WORKSPACE = os.path.dirname(SCRIPT_DIR)                             # .../web_platform
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio",
                         "why_pi", "lesson_04")
MANIFEST_TITLE = "অধ্যায় ০৪ — ব্যাসেল সমস্যা ও পাই বর্গ"

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

# Parity guards: exact cue-type sequence expected for each narrated section,
# derived from the live narrated DOM via the narration_engine selector.
EXPECTED_TYPES = {'sec-basel-series': ['h2', 'p', 'p', 'figure', 'formula-box'],
 'sec-inverse-squares': ['h2', 'p', 'figure', 'p', 'callout', 'formula-box', 'formula-box'],
 'sec-result': ['h2', 'p', 'figure', 'p', 'formula-box']}
EXPECTED_AUDIO_FILES = {'sec-basel-series': 'sec_01_sec-basel-series.mp3',
 'sec-inverse-squares': 'sec_02_sec-inverse-squares.mp3',
 'sec-result': 'sec_03_sec-result.mp3'}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (17 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {'sec-basel-series': {'title': '',
                      'audio_file': 'sec_01_sec-basel-series.mp3',
                      'cues': [{'index': 0,
                                'type': 'h2',
                                'tts': 'চতুর্থ পরিচ্ছেদ, ব্যাসেল সমস্যা। গণিতবিদরা দীর্ঘদিন ধরে এই একটা '
                                       'প্রশ্নের উত্তর খুঁজছিলেন।'},
                               {'index': 1,
                                'type': 'p',
                                'tts': 'সতেরো শো চল্লিশ সাল থেকে গণিতবিদরা একটা প্রশ্ন নিয়ে কাজ করছিলেন, এক '
                                       'প্লাস এক ভাগ চার প্লাস এক ভাগ নয় প্লাস এক ভাগ ষোলো, এইভাবে চলতে থাকা '
                                       'ধারার মান কত। প্রতিটি পদ একের পর এক ছোট হয়ে যাচ্ছে, কিন্তু যোগফল '
                                       'কোথায় গিয়ে থামে তা কেউ জানতেন না। এই প্রশ্নটাই ব্যাসেল সমস্যা নামে '
                                       'পরিচিত।'},
                               {'index': 2,
                                'type': 'p',
                                'tts': 'সতেরো শো চৌত্রিশ সালে অয়লার দেখালেন মানটা পাই বর্গ ভাগ ছয়। কিন্তু '
                                       'কেন পাই, আর তাও আবার পাইয়ের বর্গ। প্রচলিত বীজগাণিতিক প্রমাণে এটা '
                                       'বোঝা কঠিন, তাই আমরা একটা জ্যামিতিক প্রমাণ দেখব যেখানে পাইটা '
                                       'সামনাসামনি দেখা যায়।'},
                               {'index': 3,
                                'type': 'figure',
                                'tts': 'এই চিত্রে বর্গের ব্যস্তনের যোগফল পাই বর্গ ভাগ ছয় দেখানো হয়েছে। '
                                       'প্রতিটি ছোট বর্গক্ষেত্রের ব্যস্তন ধারার একটা পদ নির্দেশ করে। অসীম '
                                       'সংখ্যক বর্গের এই যোগফলেই পাই বর্গাকৃত হয়ে ফুটে ওঠে।'},
                               {'index': 4,
                                'type': 'formula-box',
                                'tts': 'গাণিতিক সূত্র, এক থেকে অসীম পর্যন্ত এন বর্গের ব্যস্তনের যোগফল সমান '
                                       'পাই বর্গ ভাগ ছয়। অর্থাৎ এক প্লাস এক ভাগ চার প্লাস এক ভাগ নয় এবং পরের '
                                       'পদগুলো যোগ করলে ঠিক পাই বর্গ ভাগ ছয় পাওয়া যায়।'}]},
 'sec-inverse-squares': {'title': '',
                         'audio_file': 'sec_02_sec-inverse-squares.mp3',
                         'cues': [{'index': 0,
                                   'type': 'h2',
                                   'tts': 'পঞ্চম পরিচ্ছেদ, ব্যস্ত বর্গ ও জ্যামিতি। ব্যাসেল ধারার পদগুলোর '
                                          'সাথে প্রকৃতির একটা সুন্দর মিল আছে।'},
                                  {'index': 1,
                                   'type': 'p',
                                   'tts': 'ব্যাসেল ধারার পদগুলো ব্যস্ত বর্গের। প্রকৃতিতেও ব্যস্ত বর্গ সূত্র '
                                          'দেখা যায়, কোনো উৎস থেকে আর দূরত্বে গেলে তার তীব্রতা এক ভাগ আর '
                                          'বর্গ হারে কমে। কারণ শক্তি একটা বৃত্তের পরিধি দুই পাই আর জুড়ে '
                                          'ছড়িয়ে পড়ে, আর সেক্টরের ক্ষেত্রফল আধা আর বর্গ গুণ থিটা।'},
                                  {'index': 2,
                                   'type': 'figure',
                                   'tts': 'এই চিত্রে বৃত্তাকার ছড়ানোর হিসাবেই পাই কীভাবে আসে তা দেখানো '
                                          'হয়েছে। কেন্দ্র থেকে বাইরের দিকে শক্তি ছড়িয়ে পড়ে একটা বৃত্তের '
                                          'পরিধি বরাবর। যত দূরে যাই, একই শক্তি তত বেশি এলাকায় বিভক্ত হয়।'},
                                  {'index': 3,
                                   'type': 'p',
                                   'tts': 'আর বর্গ আর পাইয়ের এই সংমিশ্রণই ইঙ্গিত দেয় যে ধারার উত্তরে পাই '
                                          'বর্গ থাকতে পারে। কিন্তু এটা ইঙ্গিত মাত্র, আমাদের চাই একটা নিখুঁত '
                                          'প্রমাণ। সেই প্রমাণে প্রতিটি পদ একটা জ্যামিতিক বস্তুর সাথে মেলে।'},
                                  {'index': 4,
                                   'type': 'callout',
                                   'tts': 'বিশেষ নোট, জ্যামিতিক দৃষ্টিভঙ্গি। সরাসরি যোগ করার বদলে আমরা '
                                          'প্রতিটি এন বর্গের ব্যস্ত কে একটা উপবৃত্ত বা বৃত্তের ক্ষেত্রফলের '
                                          'সাথে মিলিয়ে দেখি। তখন অসীম যোগটা হয়ে যায় একটা মসৃণ বক্ররেখার '
                                          'নিচের ক্ষেত্রফল, আর সেই ক্ষেত্রফলেই লুকিয়ে আছে পাই বর্গ ভাগ ছয়।'},
                                  {'index': 5,
                                   'type': 'formula-box',
                                   'tts': 'গাণিতিক সূত্র, আর দূরত্বে তীব্রতা আই অফ আর সমানুপাতিক এক ভাগ আর '
                                          'বর্গ। অর্থাৎ দূরত্ব দ্বিগুণ হলে তীব্রতা চার ভাগের এক ভাগ হয়ে '
                                          'যায়।'},
                                  {'index': 6,
                                   'type': 'formula-box',
                                   'tts': 'গাণিতিক সূত্র, বৃত্তের পরিধি সি সমান দুই পাই আর। এই দুই পাই আর '
                                          'থাকাই ব্যস্ত বর্গ সূত্রে পাইয়ের উপস্থিতির ইঙ্গিত দেয়।'}]},
 'sec-result': {'title': '',
                'audio_file': 'sec_03_sec-result.mp3',
                'cues': [{'index': 0,
                          'type': 'h2',
                          'tts': 'ষষ্ঠ পরিচ্ছেদ, উত্তর পাই বর্গ ভাগ ছয়। জ্যামিতিক ছবিটা এগিয়ে নিয়ে গেলেই '
                                 'উত্তরটা সামনে চলে আসে।'},
                         {'index': 1,
                          'type': 'p',
                          'tts': 'জ্যামিতিক ছবিটিকে যতক্ষণ কাগজে কলমে এগিয়ে নিয়ে যাই, ততক্ষণে দেখা যায় অসীম '
                                 'পদগুলোর যোগফল ঠিক পাই বর্গ ভাগ ছয়। পাইটা এসেছে বৃত্ত থেকে, আর তার বর্গ '
                                 'এসেছে দুই মাত্রার ক্ষেত্রফলের হিসাব থেকে। এই দুটো কারণ মিলেই উত্তরটা গঠিত '
                                 'হয়।'},
                         {'index': 2,
                          'type': 'figure',
                          'tts': 'এই চিত্রে ধারার মান পাই বর্গ ভাগ ছয় দেখানো হয়েছে, পাই বর্গাকৃত হয়ে আছে। '
                                 'একের পর এক ছোট বর্গের ব্যস্তন যোগ হয়ে এই মান গড়ে তুলেছে। ছবিটা আমাদের মনে '
                                 'করিয়ে দেয় উত্তরের পেছনে একটা বৃত্ত আছে।'},
                         {'index': 3,
                          'type': 'p',
                          'tts': 'এই প্রমাণের সৌন্দর্য হলো এটা শুধু উত্তর কী বলেই থামে না, বরং কেন পাই '
                                 'প্রশ্নেরও সরাসরি জবাব দেয়। পরবর্তী পাঠে আমরা আরেকটি বিখ্যাত ধারা দেখব, '
                                 'লাইবনিজের সূত্র, যেখানে পাই আবারও অপ্রত্যাশিতভাবে আবির্ভূত হয়।',
                          'role': 'conclusion'},
                         {'index': 4,
                          'type': 'formula-box',
                          'tts': 'গাণিতিক সূত্র, এক থেকে অসীম পর্যন্ত এন বর্গের ব্যস্তনের যোগফল সমান পাই '
                                 'বর্গ ভাগ ছয়, যার মান প্রায় এক দশমিক ছয় চার চার নয়। ছোট ছোট ভগ্নাংশের এই '
                                 'অসীম যোগফলেই পাই লুকিয়ে আছে।'}]}}

# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
DEVANAGARI = re.compile(r"[\u0900-\u097f]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"


def assert_clean_scripts():
    """Fail before any TTS work if a script still contains markup or Latin text."""
    total = 0
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars {bad!r}")
            if DEVANAGARI.search(cue["tts"].replace("।", "")):
                raise ValueError(f"{sec_id} cue {cue['index']}: Devanagari char present")
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: artificial figure label present")
            sentences = [s for s in cue["tts"].split("।") if s.strip()]
            if not (2 <= len(sentences) <= 4):
                raise ValueError(f"{sec_id} cue {cue['index']}: {len(sentences)} sentences")
        types = [c["type"] for c in sec["cues"]]
        if types != EXPECTED_TYPES[sec_id]:
            raise ValueError(f"{sec_id}: cue type/order mismatch -> {types}")
        if sec["audio_file"] != EXPECTED_AUDIO_FILES[sec_id]:
            raise ValueError(f"{sec_id}: audio_file mismatch")
        indices = [c["index"] for c in sec["cues"]]
        if indices != list(range(len(indices))):
            raise ValueError(f"{sec_id}: cue indices are not 0..n-1")
        total += len(indices)
    if set(SECTIONS_DATA) != set(EXPECTED_TYPES):
        raise ValueError("section key mismatch vs live DOM")
    if total != 17:
        raise ValueError(f"Expected 17 cues, found {total}")


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
    """A cached chunk counts only if ffprobe can read a positive duration."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    try:
        return get_duration_ms(path) > 0
    except Exception:  # noqa: BLE001 - corrupt / partial download
        return False


async def synth_cue(text, path, rate, pitch, volume):
    # Edge TTS occasionally replies with an empty audio stream. Back off and
    # retry; this is a network-response wait, not an arbitrary fixed delay.
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


async def build_section(sec_id, sec):
    temp = os.path.join(AUDIO_DIR, f"_expressive_tmp_{sec_id}")
    os.makedirs(temp, exist_ok=True)

    # Version-based cache: changing the embedded scripts invalidates old chunks.
    sig = hashlib.sha256(
        json.dumps(sec, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    sig_path = os.path.join(temp, "scripts.sha256")
    if os.path.exists(sig_path):
        with open(sig_path, encoding="utf-8") as fh:
            old = fh.read().strip()
    else:
        old = ""
    if old != sig:
        for name in os.listdir(temp):
            if name.endswith(".mp3"):
                os.remove(os.path.join(temp, name))
        with open(sig_path, "w", encoding="utf-8") as fh:
            fh.write(sig)

    cues = sec["cues"]
    chunk_paths = []
    durations = []

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

    # Real 350 ms silence between cues, encoded to match the TTS chunks.
    sample_rate, channels = probe_stream(chunk_paths[0])
    silence = os.path.join(temp, "silence_350ms.mp3")
    make_silence(silence, sample_rate, channels)

    concat_paths = []
    for i, chunk in enumerate(chunk_paths):
        concat_paths.append(chunk)
        if i < len(chunk_paths) - 1:
            concat_paths.append(silence)

    final_path = os.path.join(AUDIO_DIR, sec["audio_file"])
    concat_to(final_path, concat_paths)

    # Build timings from measured durations + the real silence chunks.
    manifest_cues = []
    cursor = 0.0
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

    # Per-cue validation: non-zero duration, no overlap, exact gap.
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


async def build_all():
    assert_clean_scripts()
    print(f"Validated {sum(len(s['cues']) for s in SECTIONS_DATA.values())} clean cues "
          f"in {len(SECTIONS_DATA)} sections.")

    manifest_sections = {}
    for sec_id, sec in SECTIONS_DATA.items():
        manifest_sections[sec_id] = await build_section(sec_id, sec)

    manifest_data = {
        "course": "why_pi",
        "lesson": "lesson_04",
        "title": MANIFEST_TITLE,
        "voice": VOICE,
        "mode": "authentic_teacher",
        "sections": manifest_sections,
    }

    json_text = json.dumps(manifest_data, ensure_ascii=False, indent=2)
    with open(os.path.join(AUDIO_DIR, "manifest.json"), "w", encoding="utf-8") as fh:
        fh.write(json_text)
    with open(os.path.join(AUDIO_DIR, "manifest.js"), "w", encoding="utf-8") as fh:
        fh.write("window.TEACHER_AUDIO_MANIFEST = " + json_text + ";\n")

    # Final integrity checks.
    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert set(loaded["sections"]) == set(SECTIONS_DATA)
    total_cues = 0
    total_ms = 0.0
    figures = 0
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == len(EXPECTED_TYPES[sec_id])
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    assert total_cues == 17

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Why Pi Lesson 04")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<24} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTIONS_DATA)} sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json is valid JSON; all mp3 files exist and are non-empty.")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(build_all())
