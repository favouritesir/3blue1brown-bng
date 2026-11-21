# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Why-Pi Lesson 01 (Bengali) to the
Lesson-01 / Calculus-02 gold standard.

Deterministic, re-runnable, self-contained:
  * 22 cues in 3 narrated sections with EXACTLY the same section
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

Usage:  python governance/build_expressive_teacher_audio_why_pi001.py
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
                         "why_pi", "lesson_01")
MANIFEST_TITLE = "অধ্যায় ০১ — একটি গণনার ধাঁধার সবচেয়ে অপ্রত্যাশিত উত্তর"

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
EXPECTED_TYPES = {'sec-setup': ['h2', 'p', 'figure', 'p', 'figure', 'p', 'formula-box'],
 'sec-pattern': ['h2', 'p', 'figure', 'p', 'callout', 'p', 'formula-box'],
 'sec-hidden-circle': ['h2', 'p', 'p', 'figure', 'callout', 'p', 'formula-box', 'formula-box']}
EXPECTED_AUDIO_FILES = {'sec-setup': 'sec_01_sec-setup.mp3',
 'sec-pattern': 'sec_02_sec-pattern.mp3',
 'sec-hidden-circle': 'sec_03_sec-hidden-circle.mp3'}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (22 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {'sec-setup': {'title': '',
               'audio_file': 'sec_01_sec-setup.mp3',
               'cues': [{'index': 0,
                         'type': 'h2',
                         'tts': 'প্রথম পরিচ্ছেদ, ধাঁধাটির সেটআপ। আসুন দেখি একটা সাদামাটা ব্যবস্থা থেকে '
                                'কীভাবে একটা অবিশ্বাস্য উত্তর বেরিয়ে আসে।'},
                        {'index': 1,
                         'type': 'p',
                         'tts': 'কল্পনা করুন একদিকে একটি দেয়াল, তার সামনে ছোট একটি ব্লক এবং তার ডানে অনেক বড় '
                                'একটি ব্লক। বড় ব্লকটি বাঁ দিকে ধেয়ে আসছে, আর ছোট ব্লকটি প্রথমে সম্পূর্ণ '
                                'স্থির আছে। আমরা একধরনের আদর্শ পদার্থবিদ, মেঝেতে কোনো ঘর্ষণ নেই, আর প্রতিটি '
                                'সংঘর্ষ সম্পূর্ণ স্থিতিস্থাপক, অর্থাৎ সংঘর্ষে কোনো শক্তি নষ্ট হয় না।'},
                        {'index': 2,
                         'type': 'figure',
                         'tts': 'এই চিত্রে বাঁ দিকে দেয়াল, তার ঠিক সামনে ছোট ব্লকটি আর একটু দূরে বড় ব্লকটি '
                                'দেখা যাচ্ছে। বড় ব্লকটি বাঁ দিকে তীব্র বেগে এগিয়ে আসছে, ছোটটি এখনো নড়ছে না। '
                                'চিত্রের এই আদি অবস্থাটিই পুরো ধাঁধার শুরু, পরে প্রতিটি সংঘর্ষের সাথে সাথে '
                                'আমরা এই ছবিটারই পরিবর্তন দেখব।'},
                        {'index': 3,
                         'type': 'p',
                         'tts': 'সবচেয়ে সোজা ক্ষেত্রটি হলো দুই ব্লকের ভর সমান হওয়া। প্রথম ব্লকটি তার '
                                'সম্পূর্ণ ভরবেগ দ্বিতীয়টিকে দিয়ে দেয়, দ্বিতীয়টি দেয়ালে ঠুকে ফিরে আসে, আবার '
                                'প্রথমটির সাথে ধাক্কা খায়, আর প্রথমটি সোজা অসীমের দিকে চলে যায়। শেষে মোট '
                                'তিনটি ক্ল্যাক শোনা যায়।'},
                        {'index': 4,
                         'type': 'figure',
                         'tts': 'এই চিত্রে দুটি সমান ভরের ব্লকের সংঘর্ষের তিনটি ধাপ দেখানো হয়েছে। প্রথম ধাপে '
                                'বড় ব্লকটি ছোটটিকে ধাক্কা দেয়, দ্বিতীয় ধাপে ছোটটি দেয়ালে ঠুকে ফিরে আসে, '
                                'তৃতীয় ধাপে আবার দুই ব্লকের সংঘর্ষ হয়। তিনটি ধাপ মিলিয়ে মোট তিনটি ক্ল্যাক, '
                                'আর এরপর দুই ব্লক আলাদা দিকে চলে যায়।'},
                        {'index': 5,
                         'type': 'p',
                         'tts': 'কিন্তু যদি প্রথম ব্লকের ভর দ্বিতীয়টির চেয়ে একশো গুণ হয়, তখন পরিস্থিতি অনেক '
                                'জটিল হয়ে যায়। ছোট ব্লকটি দেয়াল আর বড় ব্লকের মাঝে বারবার ছড়া খেয়ে ধীরে ধীরে '
                                'বড় ব্লকের ভরবেগকে উল্টে দেয়। কতবার সংঘর্ষ হবে, উত্তরটা সহজে অনুমেয় নয়।'},
                        {'index': 6,
                         'type': 'formula-box',
                         'tts': 'গাণিতিক সূত্র, সমান ভরের ক্ষেত্রে মোট সংঘর্ষের সংখ্যা এন সমান তিন, যখন এম '
                                'এক সমান এম দুই। অর্থাৎ দুই ব্লকের ভর ঠিক সমান হলে আমরা তিনটির বেশি সংঘর্ষ '
                                'পাই না।'}]},
 'sec-pattern': {'title': '',
                 'audio_file': 'sec_02_sec-pattern.mp3',
                 'cues': [{'index': 0,
                           'type': 'h2',
                           'tts': 'দ্বিতীয় পরিচ্ছেদ, অঙ্কগুলোর অপ্রত্যাশিত প্যাটার্ন। ভরের অনুপাত বদলিয়ে '
                                  'দেখা যাক সংঘর্ষের সংখ্যা কীভাবে বদলায়।'},
                          {'index': 1,
                           'type': 'p',
                           'tts': 'আসুন ভরের অনুপাতটা বাড়িয়ে দেখি। একশো গুণ হলে একত্রিশটি সংঘর্ষ, দশ হাজার '
                                  'গুণ হলে তিনশো চৌদ্দটি, আর দশ লক্ষ গুণ হলে তিন হাজার একশো একচল্লিশটি। '
                                  'প্যাটার্নটা কি ধরা পড়ছে, একটু ভেবে দেখুন।'},
                          {'index': 2,
                           'type': 'figure',
                           'tts': 'এই চিত্রে ভরের অনুপাত বাড়ার সাথে সংঘর্ষের সংখ্যা কীভাবে বাড়ছে তা দেখানো '
                                  'হয়েছে। একশো গুণে একত্রিশ, দশ হাজার গুণে তিনশো চৌদ্দ, আর দশ লক্ষ গুণে তিন '
                                  'হাজার একশো একচল্লিশ। এই সংখ্যাগুলো টানা সাজালে পাইয়ের অঙ্কের মতোই মনে '
                                  'হয়।'},
                          {'index': 3,
                           'type': 'p',
                           'tts': 'যখনই বড় ব্লকের ভর ছোটটির একশোর কোনো ঘাত, তখনই মোট সংঘর্ষের সংখ্যা পাইয়ের '
                                  'প্রথম অঙ্কগুলোর মতো হয়। প্রথম শুনে আমাকেও এটা হতবাক করে দিয়েছিল, এই '
                                  'তথ্যটি শেয়ার করার জন্য ধন্যবাদ ভিউয়ার হেনরি ক্যাভলিকে। মূল আবিষ্কারটা '
                                  'গণিতবিদ গ্রেগরি গ্যালপেরিনের, উনিশ শো পঁচানব্বই সালে তিনি এটা আবিষ্কার '
                                  'করেন এবং দুই হাজার তিনে প্রকাশ করেন।'},
                          {'index': 4,
                           'type': 'callout',
                           'tts': 'বিশেষ নোট, কেন এটা বিস্ময়কর। পাই সাধারণত কোনো অবিচ্ছিন্ন জ্যামিতিক '
                                  'পরিমাণ, অর্থাৎ বৃত্তের পরিধি আর ব্যাসের অনুপাত বর্ণনা করে। কিন্তু এখানে '
                                  'এর দশমিক অঙ্কগুলো একটা পূর্ণসংখ্যা গণনা করছে, পাইয়ের আবির্ভাবের এই অদ্ভুত '
                                  'উপায় সত্যিই মানুষকে অবাক করে।'},
                          {'index': 5,
                           'type': 'p',
                           'tts': 'অবশ্যই এটা পাই হিসাব করার ব্যবহারিক উপায় নয়। কুড়িটি অঙ্ক পেতে বড় ব্লকের '
                                  'ভর ছোটটির একশো কোটি কোটি কোটি কোটি গুণ হতে হবে, যা আমাদের ছায়াপথের '
                                  'কেন্দ্রের অতিপ্রকৃত কৃষ্ণগহ্বরের চেয়েও অনেক বেশি। তবু প্রশ্নটা থেকে যায়, '
                                  'এখানে পাই আসছে কেন।',
                           'role': 'conclusion'},
                          {'index': 6,
                           'type': 'formula-box',
                           'tts': 'গাণিতিক সূত্র, ভরের অনুপাত এম এক ভাগ এম দুই সমান একশোর ডি বিয়োগ এক ঘাত '
                                  'হলে, সংঘর্ষের সংখ্যা এন প্রায় সমান দশের ডি ঘাত গুণ পাইয়ের নিচতম '
                                  'পূর্ণসংখ্যা। সহজ কথায়, একশোর ঘাত যত বাড়াই, পাইয়ের তত বেশি অঙ্ক সামনে চলে '
                                  'আসে।'}]},
 'sec-hidden-circle': {'title': '',
                       'audio_file': 'sec_03_sec-hidden-circle.mp3',
                       'cues': [{'index': 0,
                                 'type': 'h2',
                                 'tts': 'তৃতীয় পরিচ্ছেদ, লুকোনো বৃত্ত ও শক্তির সংরক্ষণ। এবার আমরা দেখব পাইটা '
                                        'আসলে কোথা থেকে এল।'},
                                {'index': 1,
                                 'type': 'p',
                                 'tts': 'এই ধাঁধার মূল কথা হলো, যেখানে পাই আছে সেখানে একটা লুকোনো বৃত্ত আছে। '
                                        'এই ক্ষেত্রে সেই বৃত্তটা লুকিয়ে আছে শক্তির সংরক্ষণের ভেতরে। আমরা এখন '
                                        'সেই লুকোনো বৃত্তটিকে খুঁজে বের করব।'},
                                {'index': 2,
                                 'type': 'p',
                                 'tts': 'যেকোনো মুহূর্তে দুই ব্লকের মোট গতিশক্তি হলো আধা এম এক ভি এক বর্গ '
                                        'প্লাস আধা এম দুই ভি দুই বর্গ, আর সংঘর্ষের পরও এই মান অপরিবর্তিত '
                                        'থাকে। এখন যদি অক্ষদুটিকে এভাবে স্কেল করি, এক্স সমান এম একের বর্গমূল '
                                        'গুণ ভি এক এবং ওয়াই সমান এম দুইয়ের বর্গমূল গুণ ভি দুই, তবে সমীকরণটা '
                                        'দাঁড়ায় আধা এক্স বর্গ প্লাস আধা ওয়াই বর্গ সমান ধ্রুবক। আর এটা তো '
                                        'একটা বৃত্তের সমীকরণ।'},
                                {'index': 3,
                                 'type': 'figure',
                                 'tts': 'এই চিত্রে বেগ ফেজ স্পেসে শক্তির সংরক্ষণ একটা বৃত্ত তৈরি করেছে। '
                                        'বৃত্তের প্রতিটি বিন্দু দুই ব্লকের এমন এক জোড়া বেগ নির্দেশ করে যাদের '
                                        'মোট শক্তি একই। ব্লকগুলো সংঘর্ষ করার সাথে সাথে আমাদের প্রতীকী '
                                        'বিন্দুটা এই বৃত্তের ওপরেই নড়াচড়া করে।'},
                                {'index': 4,
                                 'type': 'callout',
                                 'tts': 'বিশেষ নোট, পরবর্তী দুটি পাঠে। এই বৃত্তের ওপর দুটি ভিন্ন উপায়ে চলন '
                                        'করে দেখা যাবে কেন সংঘর্ষের সংখ্যা পাইয়ের অঙ্ক দেয়। পরবর্তী পাঠে '
                                        'আমরা বেগ ফেজ স্পেস ব্যবহার করব, আর তারপরের পাঠে দেখব একই সমস্যা '
                                        'আলোর রশ্মির মতো আচরণ করে, দুটিই সমান সুন্দর।'},
                                {'index': 5,
                                 'type': 'p',
                                 'tts': 'সংক্ষেপে বলতে গেলে, ব্লকগুলোর গতি নির্ধারণ করে শক্তি ও ভরবেগ, এই '
                                        'দুটি সংরক্ষণ আইন। এই আইনগুলোকেই একটা জ্যামিতিক ছবিতে রূপ দিয়েই '
                                        'পাইয়ের রহস্যের উত্তর মিলবে।',
                                 'role': 'conclusion'},
                                {'index': 6,
                                 'type': 'formula-box',
                                 'tts': 'গাণিতিক সূত্র, আধা এম এক ভি এক বর্গ প্লাস আধা এম দুই ভি দুই বর্গ '
                                        'সমান ধ্রুবক হলে, আধা এক্স বর্গ প্লাস আধা ওয়াই বর্গও ধ্রুবক হয়। '
                                        'অর্থাৎ শক্তির সংরক্ষণ সরাসরি একটা বৃত্তের সমীকরণে রূপ নেয়।'},
                                {'index': 7,
                                 'type': 'formula-box',
                                 'tts': 'গাণিতিক সূত্র, স্কেল করা স্থানাঙ্ক হলো এক্স সমান এম একের বর্গমূল '
                                        'গুণ ভি এক, আর ওয়াই সমান এম দুইয়ের বর্গমূল গুণ ভি দুই। এই দুটি '
                                        'স্থানাঙ্কই আমাদের সেই লুকোনো বৃত্তের সমতল আঁকতে সাহায্য করে।'}]}}

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
    if total != 22:
        raise ValueError(f"Expected 22 cues, found {total}")


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
        "lesson": "lesson_01",
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
    assert total_cues == 22

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Why Pi Lesson 01")
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
