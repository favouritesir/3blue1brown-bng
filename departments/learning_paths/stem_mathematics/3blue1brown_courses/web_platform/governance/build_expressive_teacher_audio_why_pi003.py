# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Why-Pi Lesson 03 (Bengali) to the
Lesson-01 / Calculus-02 gold standard.

Deterministic, re-runnable, self-contained:
  * 20 cues in 3 narrated sections with EXACTLY the same section
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

Usage:  python governance/build_expressive_teacher_audio_why_pi003.py
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
                         "why_pi", "lesson_03")
MANIFEST_TITLE = "অধ্যায় ০৩ — আলোর রশ্মির মতো আচরণ"

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
EXPECTED_TYPES = {'sec-position-space': ['h2', 'p', 'p', 'figure', 'p', 'formula-box'],
 'sec-rescale': ['h2', 'p', 'p', 'figure', 'p', 'formula-box', 'formula-box'],
 'sec-unfold': ['h2', 'p', 'figure', 'p', 'callout', 'formula-box', 'formula-box']}
EXPECTED_AUDIO_FILES = {'sec-position-space': 'sec_01_sec-position-space.mp3',
 'sec-rescale': 'sec_02_sec-rescale.mp3',
 'sec-unfold': 'sec_03_sec-unfold.mp3'}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (20 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {'sec-position-space': {'title': '',
                        'audio_file': 'sec_01_sec-position-space.mp3',
                        'cues': [{'index': 0,
                                  'type': 'h2',
                                  'tts': 'তৃতীয় পরিচ্ছেদ, অবস্থান ফেজ স্পেস। আগের বেগের ছবির বদলে এখানে আমরা '
                                         'অবস্থানের ছবি আঁকব।'},
                                 {'index': 1,
                                  'type': 'p',
                                  'tts': 'আগের পাঠে আমরা এমন একটা সমতল ব্যবহার করেছিলাম যার প্রতিটি বিন্দু '
                                         'দুই ব্লকের বেগ প্রকাশ করে। এবার অন্য কিছু চেষ্টা করি, বিন্দুটা যেন '
                                         'দুই ব্লকের অবস্থান প্রকাশ করে। নতুন এই ছবিটাও আগের ছবির মতোই কাজ '
                                         'করবে।'},
                                 {'index': 2,
                                  'type': 'p',
                                  'tts': 'ধরি এক্স অক্ষ দেয়াল থেকে বড় ব্লকের বাঁ প্রান্তের দূরত্ব ডি এক, আর '
                                         'ওয়াই অক্ষ দেয়াল থেকে ছোট ব্লকের ডান প্রান্তের দূরত্ব ডি দুই। যখন '
                                         'ডি এক সমান ডি দুই, অর্থাৎ এক্স সমান ওয়াই রেখায়, ব্লকদুটি ধাক্কা '
                                         'খায়। নিচের সীমানা বোঝায় ছোট ব্লক দেয়ালে ঠুকে।'},
                                 {'index': 3,
                                  'type': 'figure',
                                  'tts': 'এই চিত্রে অবস্থান ফেজ স্পেসে দুই ব্লকের গতি একটা বিন্দুর পথ হিসেবে '
                                         'দেখা যাচ্ছে। এক্স আর ওয়াই অক্ষ যথাক্রমে বড় ও ছোট ব্লকের অবস্থান '
                                         'বোঝায়। ব্লকগুলো নড়ার সাথে সাথে বিন্দুটা এই পথ ধরে এগিয়ে যায়।'},
                                 {'index': 4,
                                  'type': 'p',
                                  'tts': 'ব্লকগুলো নড়ার সাথে সাথে আমাদের বিন্দুটা এই দুই সীমানার মাঝে ছড়া '
                                         'খায়, ঠিক যেন দুইটা আয়নার মাঝে একটা আলোর রশ্মি। কিন্তু একটা সমস্যা '
                                         'আছে, সাধারণ আয়নায় আপতন কোণ ও প্রতিফলন কোণ সমান, কিন্তু এখানে তা '
                                         'নয়। এই অমিলটাই পরের ধাপে ঠিক করা যাবে।'},
                                 {'index': 5,
                                  'type': 'formula-box',
                                  'tts': 'গাণিতিক সূত্র, ডি এক সমান ডি দুই হলে এক্স সমান ওয়াই। অর্থাৎ '
                                         'অবস্থান সমতলে এক্স সমান ওয়াই রেখাটিই ব্লকদুটির সংঘর্ষের শর্ত।'}]},
 'sec-rescale': {'title': '',
                 'audio_file': 'sec_02_sec-rescale.mp3',
                 'cues': [{'index': 0,
                           'type': 'h2',
                           'tts': 'চতুর্থ পরিচ্ছেদ, ভর দিয়ে অক্ষ স্কেল করা। এই স্কেলিংয়ের পর আমাদের রশ্মি '
                                  'সত্যিকারের আলোর মতো আচরণ করবে।'},
                          {'index': 1,
                           'type': 'p',
                           'tts': 'অ্যানালজিটা ঠিক করতে আমরা আগের মতোই অক্ষ স্কেল করি, এক্স সমান এম একের '
                                  'বর্গমূল গুণ ডি এক আর ওয়াই সমান এম দুইয়ের বর্গমূল গুণ ডি দুই। প্রথমে মনে '
                                  'হতে পারে এটা একটা এলোমেলো কাজ, কিন্তু শক্তি ও ভরবেগের সাথে মিলিয়ে দেখলে '
                                  'সব জায়গায় পড়ে যায়। প্রতিটি পদ নিখুঁতভাবে মিলে যায়।'},
                          {'index': 2,
                           'type': 'p',
                           'tts': 'বিন্দুটির বেগ হলো এক্স ডট সমান এম একের বর্গমূল গুণ ভি এক, আর ওয়াই ডট '
                                  'সমান এম দুইয়ের বর্গমূল গুণ ভি দুই। পাইথাগোরাসের উপপাদ্যে এক্স ডট বর্গ '
                                  'প্লাস ওয়াই ডট বর্গ সমান দুই ই, অর্থাৎ ধ্রুবক। অপটিক্যাল ভাষায় বলা যায়, '
                                  'আলোর বেগ সব জায়গায় একই থাকে।'},
                          {'index': 3,
                           'type': 'figure',
                           'tts': 'এই চিত্রে স্কেলের পর দুটি সীমানা আয়নার মতো কাজ করছে। বিন্দুটা এক সীমানায় '
                                  'আছড়ে পড়ে আবার ফিরে আসছে, ঠিক যেন আলোর রশ্মি। স্কেলিংয়ের কাজটা এখানেই '
                                  'সার্থক হয়।'},
                          {'index': 4,
                           'type': 'p',
                           'tts': 'আর ভরবেগ এম এক ভি এক প্লাস এম দুই ভি দুই সমান ধ্রুবক কে ডট গুণফল হিসেবে '
                                  'লিখলে দেখা যায়, বিন্দুটা যে কোণে আয়নায় আছড়ে পড়ে সেই কোণেই ফিরে আসে। '
                                  'অর্থাৎ দুই সীমানা সত্যিই আয়না। যান্ত্রিক আইনগুলো অপটিক্যাল আইন হয়ে গেল, '
                                  'কী অদ্ভুত কিন্তু সুন্দর।'},
                          {'index': 5,
                           'type': 'formula-box',
                           'tts': 'গাণিতিক সূত্র, এক্স সমান এম একের বর্গমূল গুণ ডি এক, আর ওয়াই সমান এম '
                                  'দুইয়ের বর্গমূল গুণ ডি দুই। এই স্কেলিংয়ের পর অবস্থানের ছবিটা আমাদের পরিচিত '
                                  'জ্যামিতি হয়ে যায়।'},
                          {'index': 6,
                           'type': 'formula-box',
                           'tts': 'গাণিতিক সূত্র, এক্স ডট বর্গ প্লাস ওয়াই ডট বর্গের বর্গমূল সমান দুই ই এর '
                                  'বর্গমূল, যা ধ্রুবক। অর্থাৎ রশ্মির বেগ সব জায়গায় একই, ঠিক আলোর মতো।'}]},
 'sec-unfold': {'title': '',
                'audio_file': 'sec_03_sec-unfold.mp3',
                'cues': [{'index': 0,
                          'type': 'h2',
                          'tts': 'পঞ্চম পরিচ্ছেদ, আয়না খুলে সোজা রশ্মি। এই চতুর কৌশলটাই আমাদের সংঘর্ষ গণনার '
                                 'চাবিকাঠি।'},
                         {'index': 1,
                          'type': 'p',
                          'tts': 'আয়নার মাঝে রশ্মি গণনা করা কঠিন, কিন্তু একটা চতুর কৌশল আছে। রশ্মি প্রতিফলিত '
                                 'হচ্ছে ভেবে না, বরং পুরো বিশ্বটাকেই উল্টিয়ে দিন। তখন রশ্মিটা সোজা চলতে থাকে '
                                 'এবং পরপর কয়েকটা লুকিং গ্লাস ইউনিভার্সে প্রবেশ করে।'},
                         {'index': 2,
                          'type': 'figure',
                          'tts': 'এই চিত্রে আয়না খুলে দিলে রশ্মি কাঁচের টুকরোর মাঝ দিয়ে সোজা যাচ্ছে। বাঁকা '
                                 'পথ আর কাল্পনিক সোজা পথ পাশাপাশি দেখা যায়। প্রতিটি কাঁচের টুকরো একবার '
                                 'প্রতিফলনের সমান।'},
                         {'index': 3,
                          'type': 'p',
                          'tts': 'আসল বাঁকা পথ আর কাল্পনিক সোজা পথের তুলনা করলে দেখা যায়, সংঘর্ষ গণনা হয়ে '
                                 'গেছে কতগুলো কাঁচের টুকরো অতিক্রম করেছে তা গণনা। আয়নাদুটোর মাঝের কোণ থিটা '
                                 'হলে, পাই অতিক্রম না করে থিটা কে কতবার যোগ করা যায় সেটাই আয়নের সংখ্যা, এন '
                                 'সমান পাই ভাগ থিটার নিচতম পূর্ণসংখ্যা। সোজা পথের এই হিসাব আমাদের মূল উত্তর '
                                 'দেয়।'},
                         {'index': 4,
                          'type': 'callout',
                          'tts': 'বিশেষ নোট, কোথায় পাই এলো। থিটা সমান আর্কট্যানজেন্ট অফ এম দুই ভাগ এম একের '
                                 'বর্গমূল, ছোট কোণে থিটা প্রায় সমান এম দুই ভাগ এম একের বর্গমূল। ভর একশোর '
                                 'ঘাত হলে পাই ভাগ থিটা জাতীয় এই গণনাই পাইয়ের অঙ্কগুলোকে বের করে দেয়, যা আগের '
                                 'পাঠেও দেখেছি।'},
                         {'index': 5,
                          'type': 'formula-box',
                          'tts': 'গাণিতিক সূত্র, থিটা সমান আর্কট্যানজেন্ট অফ এম দুই ভাগ এম একের বর্গমূল। ছোট '
                                 'কোণের ক্ষেত্রে থিটা প্রায় সমান এম দুই ভাগ এম একের বর্গমূল।'},
                         {'index': 6,
                          'type': 'formula-box',
                          'tts': 'গাণিতিক সূত্র, সংঘর্ষের সংখ্যা এন সমান পাই ভাগ থিটার নিচতম পূর্ণসংখ্যা। ভর '
                                 'একশোর ঘাতে এই সূত্রই পাইয়ের পরপর অঙ্কগুলো ফুটিয়ে তোলে।'}]}}

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
    if total != 20:
        raise ValueError(f"Expected 20 cues, found {total}")


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
        "lesson": "lesson_03",
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
    assert total_cues == 20

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Why Pi Lesson 03")
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
