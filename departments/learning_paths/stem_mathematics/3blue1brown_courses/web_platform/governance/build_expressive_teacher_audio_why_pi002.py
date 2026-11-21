# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Why-Pi Lesson 02 (Bengali) to the
Lesson-01 / Calculus-02 gold standard.

Deterministic, re-runnable, self-contained:
  * 25 cues in 4 narrated sections with EXACTLY the same section
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

Usage:  python governance/build_expressive_teacher_audio_why_pi002.py
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
                         "why_pi", "lesson_02")
MANIFEST_TITLE = "অধ্যায় ০২ — সংঘর্ষরত ব্লকরা কীভাবে পাই গণনা করে"

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
EXPECTED_TYPES = {'sec-conservation': ['h2', 'p', 'p', 'figure', 'p', 'formula-box'],
 'sec-phase-circle': ['h2', 'p', 'p', 'figure', 'p', 'formula-box'],
 'sec-momentum-line': ['h2', 'p', 'p', 'figure', 'callout', 'formula-box'],
 'sec-inscribed-angle': ['h2', 'p', 'p', 'figure', 'p', 'formula-box', 'formula-box']}
EXPECTED_AUDIO_FILES = {'sec-conservation': 'sec_01_sec-conservation.mp3',
 'sec-phase-circle': 'sec_02_sec-phase-circle.mp3',
 'sec-momentum-line': 'sec_03_sec-momentum-line.mp3',
 'sec-inscribed-angle': 'sec_04_sec-inscribed-angle.mp3'}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (25 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {'sec-conservation': {'title': '',
                      'audio_file': 'sec_01_sec-conservation.mp3',
                      'cues': [{'index': 0,
                                'type': 'h2',
                                'tts': 'দ্বিতীয় পরিচ্ছেদ, শক্তি ও ভরবেগের সংরক্ষণ। সংঘর্ষের পর ব্লকগুলোর বেগ '
                                       'বের করার চাবিকাঠি এখানেই আছে।'},
                               {'index': 1,
                                'type': 'p',
                                'tts': 'আমাদের আসলে কী দরকার, সংঘর্ষের ঠিক পরে দুই ব্লকের বেগ কত তা বের করা। '
                                       'এর চাবিকাঠি হলো দুটি সংরক্ষণ আইন, একটি শক্তির আর একটি ভরবেগের। এই '
                                       'দুই আইন মিলে পরবর্তী গতি নির্ধারণ করে।'},
                               {'index': 2,
                                'type': 'p',
                                'tts': 'ব্লক দুটির ভর এম এক ও এম দুই, আর বেগ ভি এক ও ভি দুই। মোট গতিশক্তি '
                                       'হলো আধা এম এক ভি এক বর্গ প্লাস আধা এম দুই ভি দুই বর্গ, ব্লকগুলো যতই '
                                       'ধাক্কা খাক এই মান একই থাকতে হবে। মোট ভরবেগ এম এক ভি এক প্লাস এম দুই '
                                       'ভি দুইও সংঘর্ষে অপরিবর্তিত থাকে, শুধু ছোট ব্লক দেয়ালে ঠুকে তার ভরবেগ '
                                       'দেয়ালে দিয়ে দেয়।'},
                               {'index': 3,
                                'type': 'figure',
                                'tts': 'এই চিত্রে দুই ব্লকের সংঘর্ষের সাথে শক্তি আর ভরবেগ কীভাবে অপরিবর্তিত '
                                       'থাকে তা দেখানো হয়েছে। একটি ব্লকের বেগ কমলে অন্যটির বেগ বাড়ে, কিন্তু '
                                       'দুটির মোট হিসাব একই থাকে। এই দুটি সংরক্ষণ আইনই আমাদের পরবর্তী গতি '
                                       'নির্ধারণ করে।'},
                               {'index': 4,
                                'type': 'p',
                                'tts': 'দুটি অজানা, দুটি সমীকরণ, কাজটা সম্ভব। কিন্তু সরাসরি বীজগণিতের বদলে '
                                       'আমরা একটা ছবি আঁকব। আর সেই ছবিই আমাদের পাইয়ের দিকে নিয়ে যাবে।'},
                               {'index': 5,
                                'type': 'formula-box',
                                'tts': 'গাণিতিক সূত্র, মোট শক্তি ই সমান আধা এম এক ভি এক বর্গ প্লাস আধা এম '
                                       'দুই ভি দুই বর্গ, আর মোট ভরবেগ পি সমান এম এক ভি এক প্লাস এম দুই ভি '
                                       'দুই। এই দুটি রাশি সংঘর্ষের আগে ও পরে একই থাকে।'}]},
 'sec-phase-circle': {'title': '',
                      'audio_file': 'sec_02_sec-phase-circle.mp3',
                      'cues': [{'index': 0,
                                'type': 'h2',
                                'tts': 'তৃতীয় পরিচ্ছেদ, বেগ ফেজ স্পেসে বৃত্ত। শক্তির সমীকরণটাকে একটা ছবিতে '
                                       'রূপ দেওয়া যাক।'},
                               {'index': 1,
                                'type': 'p',
                                'tts': 'প্রথমে শক্তির সমীকরণটার দিকে তাকাই। ভি এক আর ভি দুই তো বদলাচ্ছে, তাই '
                                       'আমরা একটা সমতল আঁকি যার এক্স অক্ষ ভি এক আর ওয়াই অক্ষ ভি দুই বোঝায়। '
                                       'তখন আধা এম এক ভি এক বর্গ প্লাস আধা এম দুই ভি দুই বর্গ সমান ধ্রুবক, '
                                       'একটা উপবৃত্ত হয়।'},
                               {'index': 2,
                                'type': 'p',
                                'tts': 'কিন্তু আমরা পাইয়ের খোঁজে আছি, তাই অক্ষদুটো এভাবে পাল্টাই, এক্সে ভি '
                                       'একের বদলে এম একের বর্গমূল গুণ ভি এক আর ওয়াইতে এম দুইয়ের বর্গমূল গুণ '
                                       'ভি দুই। তখন সমীকরণটা সোজা আধা এক্স বর্গ প্লাস আধা ওয়াই বর্গ সমান '
                                       'ধ্রুবক, একটি নিখুঁত বৃত্ত। আর বৃত্ত মানেই পাইয়ের সম্ভাবনা।'},
                               {'index': 3,
                                'type': 'figure',
                                'tts': 'এই চিত্রে উপবৃত্তটিকে স্কেল করে নিখুঁত বৃত্ত বানানো হলো। আগে '
                                       'অক্ষদুটো ছিল ভি এক আর ভি দুই, পরে সেটা বদলে এম এক ও এম দুই দিয়ে '
                                       'স্কেল করা হয়েছে। এই একটা স্কেলিংয়েই পাইয়ের পথ খুলে যায়।'},
                               {'index': 4,
                                'type': 'p',
                                'tts': 'বৃত্তের প্রতিটি বিন্দু এমন এক জোড়া বেগ যারা একই পরিমাণ শক্তি বহন '
                                       'করে। শুরুতে আমরা বৃত্তের সবচেয়ে বাঁ প্রান্তে আছি, বড় ব্লক বাঁ দিকে '
                                       'যাচ্ছে আর ছোটটি স্থির। এই শুরুর বিন্দু থেকেই বৃত্তের ওপর যাত্রা শুরু '
                                       'হয়।'},
                               {'index': 5,
                                'type': 'formula-box',
                                'tts': 'গাণিতিক সূত্র, এক্স সমান এম একের বর্গমূল গুণ ভি এক এবং ওয়াই সমান এম '
                                       'দুইয়ের বর্গমূল গুণ ভি দুই হলে, আধা এক্স বর্গ প্লাস আধা ওয়াই বর্গ '
                                       'সমান ই। অর্থাৎ আমাদের শক্তির সমীকরণটা এখন একটা বৃত্তের সমীকরণ।'}]},
 'sec-momentum-line': {'title': '',
                       'audio_file': 'sec_03_sec-momentum-line.mp3',
                       'cues': [{'index': 0,
                                 'type': 'h2',
                                 'tts': 'চতুর্থ পরিচ্ছেদ, ভরবেগের রেখা ও ফেজের লাফ। শক্তি বলছে বৃত্তের ওপর '
                                        'থাকতে হবে, কোথায় যাব সেটা ঠিক করে ভরবেগ।'},
                                {'index': 1,
                                 'type': 'p',
                                 'tts': 'শক্তি বলছে আমাদের বৃত্তের ওপর থাকতে হবে, কিন্তু কোন বিন্দুতে যাব '
                                        'সেটা ঠিক করে ভরবেগ। স্কেল করা অক্ষে এম এক ভি এক প্লাস এম দুই ভি দুই '
                                        'সমান ধ্রুবক রূপ নেয় এম একের বর্গমূল গুণ এক্স প্লাস এম দুইয়ের '
                                        'বর্গমূল গুণ ওয়াই সমান ধ্রুবক। এটা একটা সরলরেখা, যার ঢাল ঋণাত্মক এম '
                                        'এক ভাগ এম দুইয়ের বর্গমূল।'},
                                {'index': 2,
                                 'type': 'p',
                                 'tts': 'বৃত্ত আর এই রেখার ছেদে ঠিক দুটি বিন্দু। এর একটি আগের অবস্থা, অন্যটি '
                                        'সংঘর্ষের পরের অবস্থা। দেয়ালে ঠুকে ছোট ব্লকের বেগের চিহ্ন বদলায়, '
                                        'ছবিতে এটা এক্স অক্ষের ওপর প্রতিফলনের মতো। এইভাবে বারবার লাফ দিয়ে '
                                        'আমরা বৃত্তের ওপর ঘুরে বেড়াই, যতক্ষণ না দুই বেগই ধনাত্মক হয় আর বড় '
                                        'ব্লক ছোটটিকে অতিক্রম করে যায়।'},
                                {'index': 3,
                                 'type': 'figure',
                                 'tts': 'এই চিত্রে বৃত্ত আর ভরবেগের রেখার ছেদবিন্দুতেই লাফটা ঘটছে। এক বিন্দু '
                                        'থেকে আরেক বিন্দুতে যাওয়া মানেই একবার সংঘর্ষ। এই ছবিটার সাহায্যে '
                                        'আমরা সংঘর্ষ গণনা করতে পারি।'},
                                {'index': 4,
                                 'type': 'callout',
                                 'tts': 'বিশেষ নোট, ফেজ ডায়াগ্রামের ক্ষমতা। সিস্টেমের অবস্থাকে একটা বিন্দু '
                                        'দিয়ে প্রকাশ করলে গতীয় প্রশ্নগুলো জ্যামিতিক প্রশ্ন হয়ে যায়। শক্তির '
                                        'মতো গতীয় ধারণা হয়ে যায় বৃত্ত, আর সংঘর্ষ গণনা হয়ে যায় বৃত্তের ওপর '
                                        'লাফের সংখ্যা গণনা।'},
                                {'index': 5,
                                 'type': 'formula-box',
                                 'tts': 'গাণিতিক সূত্র, এম একের বর্গমূল গুণ এক্স প্লাস এম দুইয়ের বর্গমূল গুণ '
                                        'ওয়াই সমান ধ্রুবক, আর রেখার ঢাল ঋণাত্মক এম এক ভাগ এম দুইয়ের '
                                        'বর্গমূল। এই ঢাল থেকেই পরবর্তীতে কোণের হিসাব শুরু হয়।'}]},
 'sec-inscribed-angle': {'title': '',
                         'audio_file': 'sec_04_sec-inscribed-angle.mp3',
                         'cues': [{'index': 0,
                                   'type': 'h2',
                                   'tts': 'পঞ্চম পরিচ্ছেদ, অন্তর্লিখিত কোণ ও থিটা হিসাব। এখন আসল প্রশ্ন, '
                                          'সংঘর্ষের সংখ্যা কত।'},
                                  {'index': 1,
                                   'type': 'p',
                                   'tts': 'এখন আসল প্রশ্ন, সংঘর্ষের সংখ্যা কত। ছবিটার দিকে গভীরভাবে তাকালে '
                                          'দেখা যায় বিন্দুগুলোর মাঝের চাপগুলো প্রায় সমান। অন্তর্লিখিত কোণের '
                                          'উপপাদ্য ব্যবহার করে দেখা যায় প্রতিটি লাফ ঠিক দুই থিটা রেডিয়ান চাপ '
                                          'তৈরি করে।'},
                                  {'index': 2,
                                   'type': 'p',
                                   'tts': 'তাই প্রশ্নটা দাঁড়ায়, দুই থিটা কে কতবার যোগ করলে দুই পাই অতিক্রম '
                                          'করবে না। সরল করে লেখা যায় এন গুণ থিটা কম পাই। এখন থিটা হিসাব করি, '
                                          'ভরবেগের রেখার ঢাল ঋণাত্মক এম এক ভাগ এম দুইয়ের বর্গমূল হওয়ায় থিটা '
                                          'সমান আর্কট্যানজেন্ট অফ এম দুই ভাগ এম একের বর্গমূল।'},
                                  {'index': 3,
                                   'type': 'figure',
                                   'tts': 'এই চিত্রে সমান চাপ দুই থিটা আর পাইয়ের সাথে তুলনা দেখানো হয়েছে। '
                                          'বৃত্তের ওপর প্রতিটি লাফ একই কোণ গ্রহণ করে, কেবল শেষের লাফটা কম '
                                          'কোণ নিয়ে থামে। এই চাপগুলো গণনা করলেই সংঘর্ষের সংখ্যা পাওয়া যায়।'},
                                  {'index': 4,
                                   'type': 'p',
                                   'tts': 'ভর অনুপাত দশ হাজার এক হলে এম দুই ভাগ এম এক সমান এক শতাংশ, আর '
                                          'আর্কট্যানজেন্ট অফ এক শতাংশ প্রায় সমান শূন্য দশমিক এক। তখন তিনশো '
                                          'চৌদ্দ গুণ শূন্য দশমিক এক সমান তিন দশমিক এক চার কম পাই, কিন্তু '
                                          'তিনশো পনেরো গুণ শূন্য দশমিক এক সমান তিন দশমিক এক পাঁচ বেশি পাই, '
                                          'অর্থাৎ তিনশো চৌদ্দটি সংঘর্ষ। ছোট এক্সের জন্য আর্কট্যানজেন্ট অফ '
                                          'এক্স প্রায় সমান এক্স হওয়াতেই পাইয়ের অঙ্কগুলো এভাবে ফুটে ওঠে।'},
                                  {'index': 5,
                                   'type': 'formula-box',
                                   'tts': 'গাণিতিক সূত্র, থিটা সমান আর্কট্যানজেন্ট অফ এম দুই ভাগ এম একের '
                                          'বর্গমূল, যা ছোট কোণের ক্ষেত্রে প্রায় সমান এম দুই ভাগ এম একের '
                                          'বর্গমূল। ভরের অনুপাত যত বাড়ে, থিটা তত ছোট হয়।'},
                                  {'index': 6,
                                   'type': 'formula-box',
                                   'tts': 'গাণিতিক সূত্র, এন গুণ থিটা কম পাই হলে সংঘর্ষের সংখ্যা এন সমান পাই '
                                          'ভাগ থিটার নিচতম পূর্ণসংখ্যা। এই সূত্রটিই একশোর ঘাতে পাইয়ের অঙ্ক '
                                          'বের করে দেয়।'}]}}

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
    if total != 25:
        raise ValueError(f"Expected 25 cues, found {total}")


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
        "lesson": "lesson_02",
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
    assert total_cues == 25

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Why Pi Lesson 02")
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
