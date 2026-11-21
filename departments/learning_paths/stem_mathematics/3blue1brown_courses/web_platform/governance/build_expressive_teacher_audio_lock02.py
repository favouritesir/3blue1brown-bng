# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Lockdown Math Lesson 02
("Exponential growth and epidemics", Bengali) to the gold standard —
warm, natural, fully phonetic figure phrasing, ZERO calendar-puzzle content.

Deterministic, re-runnable, self-contained:
  * 13 cues in 4 narrated sections with EXACTLY the same section IDs, audio_file
    names, cue type and cue order as the live narration-engine DOM.
    Authoritative DOM extraction (governance/_extract_lock02_dom.py, via the
    narration_engine.js selector) confirmed:
        sec-calendar-puzzle  -> ['h2', 'chapter-quote', 'p', 'p']  (4 cues)
        sec-clock-modulo     -> ['h2', 'p', 'p']                   (3 cues)
        sec-leap-years       -> ['h2', 'p', 'p']                   (3 cues)
        sec-doomsday-trick   -> ['h2', 'p', 'p']                   (3 cues)
    Total = 13 cues. The 4 section IDs and audio_file names are LEGACY keys that
    are deliberately KEPT for DOM<->manifest parity. The 5 sec-*-study /
    sec-interactive-lab / sec-quizzes / sec-formulas-glossary sections carry
    data-no-narration="true" and are excluded. There are NO quiz/media-tab types.
  * CRITICAL DISCREPANCY FIX: the OLD manifest narrated a calendar puzzle. The
    live DOM KEEPS those 4 IDs but DISPLAYS exponential-growth content. Every
    script below is written about the ACTUAL displayed topic (linear vs
    exponential, doubling time / Rule of 70, dN/dt = kN differential model and
    R0/SIR, logistic S-curve / inflection, flattening the curve). No calendar,
    weekday, modulo or leap-year narration survives anywhere in the manifest.
  * Expressive Bengali: 2-4 sentence natural explanations. The artificial label
    "চিত্র প্রদর্শনী" is NEVER used — teacher phrasing uses "চিত্রে দেখা যাচ্ছে"
    or direct explanation. Fully phonetic (no TeX / Latin / markup). Safeguards:
      exponential    -> এক্সপোনেনশিয়াল,  epidemic -> মহামারী,
      doubling time  -> দ্বিগুণ হওয়ার সময়,  logistic -> লজিস্টিক,
      SIR            -> এস আই আর,  R0 -> আর নল.
  * Per-cue prosody via edge_tts.Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, chapter-quote -3%, p +2%, figure -4%, formula-box -8%,
      callout +0%, conclusion -3%. A real 350 ms silence chunk between cues.
  * ffmpeg -c copy concat into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) + the
    per-section *_cues.json sidecars, all with exact measured ms timings.
  * Bumps the page cache-buster manifest.js?v=N -> ?v=N+1.
  * verify_in_chrome() re-checks everything headlessly with channel=chrome,
    including 0 calendar-related words and 0 "চিত্র প্রদর্শনী" labels.
  * The _backup_before_expressive_build/ folder is NEVER touched. No other
    lesson or library is touched.

Usage:
  python governance/build_expressive_teacher_audio_lock02.py
  python governance/build_expressive_teacher_audio_lock02.py --verify-only
"""

import os
import re
import sys
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
                         "lockdown_math", "lesson_02")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "lockdown_math", "lesson_02.html")
VERIFY_RESULT = os.path.join(SCRIPT_DIR, "_verify_lock02_result.json")
MANIFEST_TITLE = "অধ্যায় ০২ — সূচকীয় বৃদ্ধি ও মহামারী মডেলিং"

# Prosody keyed by cue type: (rate, pitch, volume) — gold-standard spec.
PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
    "h3":            ("-3%", "+0Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),
    "p":             ("+2%", "+0Hz", "+0%"),   # natural teacher pace
    "figure":        ("-4%", "+0Hz", "+0%"),   # slower, considerate visual explanation
    "callout":       ("+0%", "+0Hz", "+0%"),
    "formula-box":   ("-8%", "+0Hz", "+0%"),   # slow and deliberate
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")     # calm concluding prose

ALLOWED_CUE_TYPES = set(PROSODY_DEFAULT) | {"conclusion"}

# Exact DOM block-type sequence per narrated section (from narration_engine).
EXPECTED_TYPES = {
    "sec-calendar-puzzle": ["h2", "chapter-quote", "p", "p"],
    "sec-clock-modulo":    ["h2", "p", "p"],
    "sec-leap-years":      ["h2", "p", "p"],
    "sec-doomsday-trick":  ["h2", "p", "p"],
}
# Audio-file names are the EXISTING manifest keys (legacy names, intentionally kept).
EXPECTED_AUDIO_FILES = {
    "sec-calendar-puzzle": "sec_01_calendar_puzzle.mp3",
    "sec-clock-modulo":    "sec_02_clock_modulo.mp3",
    "sec-leap-years":      "sec_03_leap_years.mp3",
    "sec-doomsday-trick":  "sec_04_doomsday_trick.mp3",
}
# Exponential-themed aliases/titles replace the stale calendar metadata.
EXPONENTIAL_ALIASES = {
    "sec-calendar-puzzle": "sec_01_linear_vs_exponential",
    "sec-clock-modulo":    "sec_02_doubling_time",
    "sec-leap-years":      "sec_03_epidemic_model",
    "sec-doomsday-trick":  "sec_04_logistic_flattening",
}
EXPECTED_COUNT = {sid: len(t) for sid, t in EXPECTED_TYPES.items()}
EXPECTED_TOTAL = 13

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (13 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-calendar-puzzle": {
        "title": "১. রৈখিক বিভ্রম ও চালের দানার চিরন্তন ধাঁধা",
        "audio_file": "sec_01_calendar_puzzle.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "প্রথম পরিচ্ছেদ, রৈখিক বিভ্রম ও চালের দানার চিরন্তন ধাঁধা, যা আমাদের "
             "সূচকীয় বা এক্সপোনেনশিয়াল বৃদ্ধির আসল রূপ চিনতে শেখায়।"},
            {"index": 1, "type": "chapter-quote",
             "tts":
             "উদ্ধৃতি, মানবজাতির সবচেয়ে বড় সীমাবদ্ধতা হলো সূচকীয় ফাংশনের গভীর রূপটি "
             "অনুধাবন করতে আমাদের মস্তিষ্কের তীব্র অক্ষমতা। কথাটি বলেছেন গণিতবিদ "
             "আলবার্ট অ্যালেন বার্টলেট।"},
            {"index": 2, "type": "p",
             "tts":
             "মানুষের মস্তিষ্ক বিবর্তনগতভাবে রৈখিক চিন্তায় অভ্যস্ত। আমরা যখন হাঁটি, "
             "প্রতি পদক্ষেপে এক মিটার করে এগোই, তাই ত্রিশ পদক্ষেপে যাই ঠিক ত্রিশ মিটার। "
             "কিন্তু যদি প্রতিটি পদক্ষেপে দূরত্ব দ্বিগুণ হতো, প্রথম ধাপে এক মিটার, দ্বিতীয় "
             "ধাপে দুই মিটার, তৃতীয় ধাপে চার মিটার, তবে ত্রিশতম পদক্ষেপে কতটা দূর যেতাম?"},
            {"index": 3, "type": "p", "visual": True,
             "tts":
             "অনেকেই ভাবেন হয়তো কয়েক কিলোমিটার, কিন্তু বাস্তবতা হলো দুই এর ২৯ ঘাত "
             "মিটার, অর্থাৎ প্রায় তিপান্ন কোটি আটষট্টি লক্ষ মিটার, যা পৃথিবীকে তেরো বার "
             "প্রদক্ষিণ করে চাঁদে পৌঁছানোর দূরত্বেরও বেশি। চিত্রে দেখা যাচ্ছে সরলরেখার মতো "
             "রৈখিক বৃদ্ধি আর খাড়া উঠে যাওয়া এক্সপোনেনশিয়াল বক্ররেখার তুলনা। দাবার বোর্ডের "
             "প্রাচীন ধাঁধাতেও প্রথম ঘরে এক, দ্বিতীয় ঘরে দুই, তৃতীয় ঘরে চার করে ষাটতম ঘরে "
             "চালের দানা দাঁড়ায় দুই এর ৬৪ ঘাতের কাছাকাছি, যা পুরো পৃথিবীকে চালের স্তরে ঢেকে "
             "দিতে পারে।"},
        ],
    },

    "sec-clock-modulo": {
        "title": "২. দ্বিগুণের সময় ও ৭০-এর নিয়ম",
        "audio_file": "sec_02_clock_modulo.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "দ্বিতীয় পরিচ্ছেদ, দ্বিগুণ হওয়ার সময় ও সত্তরের নিয়ম, যা সূচকীয় বৃদ্ধিকে "
             "পরিমাপের সবচেয়ে কার্যকর মানদণ্ড।"},
            {"index": 1, "type": "p",
             "tts":
             "দ্বিগুণ হওয়ার সময় মানে সেই নির্দিষ্ট সময়কাল, যার মধ্যে আক্রান্ত বা যেকোনো "
             "রাশির পরিমাণ ঠিক দ্বিগুণ হয়ে যায়। যদি কোনো মহামারী প্রতি তিন দিনে দ্বিগুণ হয়, "
             "তবে আজ এক হাজার জন আক্রান্ত থাকলে তিন দিন পর দুই হাজার, ছয় দিন পর চার হাজার, "
             "নয় দিন পর আট হাজার, আর মাত্র এক মাস পর অর্থাৎ দশটি ডাবলিং পিরিয়ডে সংখ্যাটি "
             "এক হাজার থেকে প্রায় দশ লাখে পৌঁছে যায়।"},
            {"index": 2, "type": "p", "visual": True,
             "tts":
             "অর্থনীতি ও ফলিত গণিতে ব্যবহৃত সত্তরের নিয়ম বলে, কোনো রাশি প্রতিদিন পি শতাংশ "
             "হারে বাড়লে দ্বিগুণ হতে সময় লাগে প্রায় সত্তর ভাগ পি, অর্থাৎ দৈনিক দশ শতাংশ "
             "হারে সাত দিন। চিত্রে দেখা যাচ্ছে সমান সময় ব্যবধানে এক, দুই, চার, আট, ষোলো করে "
             "জ্যামিতিক ধাপে দ্বিগুণীকরণ। আর প্রতিটি নতুন ডাবলিংয়ে যে পরিমাণ বৃদ্ধি পায়, "
             "তা অতীতের সব ধাপ মিলিয়ে যা তৈরি হয়েছিল তার চেয়েও বেশি।"},
        ],
    },

    "sec-leap-years": {
        "title": "৩. সংক্রমণের গাণিতিক মেকানিক্স ও ডিফারেনশিয়াল মডেল",
        "audio_file": "sec_03_leap_years.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "তৃতীয় পরিচ্ছেদ, সংক্রমণের গাণিতিক মেকানিক্স ও ডিফারেনশিয়াল মডেল, অর্থাৎ "
             "মহামারী কেন এক্সপোনেনশিয়াল বৃদ্ধি অনুসরণ করে।"},
            {"index": 1, "type": "p",
             "tts":
             "ধরা যাক, যেকোনো মুহূর্তে মোট আক্রান্তের সংখ্যা এন। গড়ে প্রতিটি আক্রান্ত ব্যক্তি "
             "প্রতিদিন ই সংখ্যক মানুষের সংস্পর্শে আসে, আর প্রতিটি সংস্পর্শে ভাইরাস ছড়ানোর "
             "সম্ভাবনা পি। তাহলে প্রতিদিন একজন আক্রান্ত ব্যক্তি গড়ে ই গুণ পি সংখ্যক নতুন "
             "মানুষকে সংক্রামিত করে, আর এন জন আক্রান্ত মিলে দিনে নতুন আক্রান্তের সংখ্যা হয় "
             "ই গুণ পি গুণ এন, অর্থাৎ কে গুণ এন।"},
            {"index": 2, "type": "p", "visual": True,
             "tts":
             "ক্যালকুলাসের দৃষ্টিতে এটি প্রকৃতির সবচেয়ে মৌলিক সমীকরণ, কোনো রাশির পরিবর্তনের "
             "হার যখন তার বর্তমান পরিমাণের সরাসরি সমানুপাতিক হয়, তখন তার বৃদ্ধির একমাত্র পথ "
             "হয় এক্সপোনেনশিয়াল বিস্তার। এস আই আর মডেলে মৌলিক প্রজনন সংখ্যা আর নল যদি "
             "একের বেশি হয়, তবে প্রতিটি প্রজন্মে রোগীর সংখ্যা গুণিতক হারে বেড়ে মহামারী ছড়ায়, "
             "আর একের কম হলে সংক্রমণ নিভে যায়। চিত্রে দেখা যাচ্ছে সংক্রমণ বৃক্ষ, প্রতিটি "
             "নোড থেকে আর নল সংখ্যক নতুন শাখা জন্ম নিচ্ছে।"},
        ],
    },

    "sec-doomsday-trick": {
        "title": "৪. লজিস্টিক এস-কার্ভ, ইনফ্লেকশন ও কার্ভ ফ্ল্যাটেনিং",
        "audio_file": "sec_04_doomsday_trick.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "চতুর্থ ও শেষ পরিচ্ছেদ, লজিস্টিক এস কার্ভ, ইনফ্লেকশন পয়েন্ট ও কার্ভ ফ্ল্যাটেনিং, "
             "অর্থাৎ কোথায় গিয়ে মহামারী থমকে দাঁড়ায়।"},
            {"index": 1, "type": "p", "visual": True,
             "tts":
             "যদি সংক্রমণ চিরকাল এক্সপোনেনশিয়ালভাবে বাড়তে থাকত, তবে কয়েক মাসের মধ্যে "
             "আক্রান্তের সংখ্যা পৃথিবীর জনসংখ্যাকেও ছাড়িয়ে যেত, কিন্তু বাস্তবে তা ঘটে না। "
             "কারণ সুস্থ হয়ে অ্যান্টিবডি তৈরি হলে বা মৃত্যুতে সংক্রামিত হতে পারা মানুষের "
             "সংখ্যা কমতে থাকে, আর ১৮৩৮ সালে গণিতবিদ পিয়েরে ফ্রাঁসোয়া ভেরহুলস্ট এই "
             "বাস্তবতাকে লজিস্টিক সমীকরণে প্রকাশ করেন, যার বৃদ্ধির হার এন বন্ধনী এক মাইনাস "
             "এন ভাগ কে দিয়ে গুণিত হয়। চিত্রে দেখা যাচ্ছে সুন্দর এস আকৃতির বক্ররেখা, যা "
             "আক্রান্তের সংখ্যা মোট জনসংখ্যার অর্ধেক অর্থাৎ কে ভাগ দুই বিন্দুতে ইনফ্লেকশন "
             "পয়েন্টে সর্বোচ্চ বেগ পৌঁছে এরপর ধীরে ধীরে কে সীমায় স্থিতিশীল হয়।"},
            {"index": 2, "type": "p", "visual": True, "role": "conclusion",
             "tts":
             "মহামারীর সময় সবচেয়ে আলোচিত স্লোগান ছিল বক্ররেখাকে সমতল করা বা ফ্ল্যাটেন দ্য "
             "কার্ভ। স্বাস্থ্যসেবার ধারণক্ষমতা একটা অনুভূমিক সীমারেখা, আর অনিয়ন্ত্রিত "
             "মহামারীতে প্রতিদিনের নতুন আক্রান্তের খাড়া পর্বত সেই রেখাকে বহু গুণ ছাড়িয়ে যায়। "
             "কিন্তু যেহেতু সূচকীয় ফাংশনে বৃদ্ধি ধ্রুবক আর সূচকে থাকে, তাই মাস্ক, সামাজিক "
             "দূরত্ব আর দ্রুত পরীক্ষার মাধ্যমে সংস্পর্শ কমালে আর সামান্য কমলেই ফলাফল রৈখিকভাবে "
             "নয়, বরং বহুগুণে কমে যায়। চিত্রে দেখা যাচ্ছে খাড়া পর্বত আর সমতল সহনশীল কার্ভের "
             "তুলনা, আর শিক্ষা হলো এক দিন আগে নেওয়া ছোট সিদ্ধান্ত দেরিতে নেওয়া বিশাল "
             "পদক্ষেপের চেয়ে শতগুণ বেশি শক্তিশালী, এই নিয়েই শেষ হলো আমাদের যাত্রা।"},
        ],
    },
}

# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
# Latin letters, TeX/markup and long dashes/hyphens are forbidden in TTS text.
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"
NATURAL_FIGURE = "চিত্রে দেখা যাচ্ছে"

# Stale calendar-puzzle vocabulary that must NOT survive in any narration text.
# (Structural IDs/audio_file names are legacy keys kept for DOM parity and are
#  intentionally excluded from this text-only scan.)
CALENDAR_WORDS = [
    "ক্যালেন্ডার", "calendar", "সপ্তাহের বার", "সপ্তাহ নির্ণয়", "বার নির্ণয়",
    "অধিবর্ষ", "লিপ ইয়ার", "লিপ বছর", "leap year", "ডুমসডে", "doomsday",
    "মডুলো", "মডুলার", "modulo", "modular", "ঘড়ির গণিত", "তারিখের বার",
]

KEY_PHRASES = {
    "sec-calendar-puzzle": "রৈখিক বিভ্রম",
    "sec-clock-modulo":    "দ্বিগুণ হওয়ার সময়",
    "sec-leap-years":      "সংক্রমণের গাণিতিক মেকানিক্স",
    "sec-doomsday-trick":  "লজিস্টিক",
}


def narration_text_blobs():
    """All human-readable narration text (manifest title + section titles + cue texts)."""
    blobs = [MANIFEST_TITLE]
    for sec_id, sec in SECTIONS_DATA.items():
        blobs.append(sec["title"])
        for cue in sec["cues"]:
            blobs.append(cue["tts"])
    return blobs


def assert_clean_scripts():
    """Fail before any TTS work on markup, banned label, or calendar content."""
    # Prosody spec must be intact.
    expected_prosody = {
        "h2": ("-5%", "+2Hz", "+0%"),
        "h3": ("-3%", "+0Hz", "+0%"),
        "chapter-quote": ("-3%", "+0Hz", "+0%"),
        "p": ("+2%", "+0Hz", "+0%"),
        "figure": ("-4%", "+0Hz", "+0%"),
        "callout": ("+0%", "+0Hz", "+0%"),
        "formula-box": ("-8%", "+0Hz", "+0%"),
    }
    assert PROSODY_DEFAULT == expected_prosody, "prosody spec drift"

    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars {bad!r}")
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: artificial figure label present")

    # No stale calendar vocabulary in any narration text.
    for blob in narration_text_blobs():
        low = blob.lower()
        for w in CALENDAR_WORDS:
            if w.lower() in low:
                raise ValueError(f"calendar-related word {w!r} survived in narration text: {blob[:60]}")

    if len(SECTIONS_DATA) != 4:
        raise ValueError("Expected exactly 4 narrated sections")
    total = 0
    for sec_id, sec in SECTIONS_DATA.items():
        types = [c["type"] for c in sec["cues"]]
        if types != EXPECTED_TYPES[sec_id]:
            raise ValueError(f"{sec_id}: cue type/order mismatch -> {types}")
        if sec["audio_file"] != EXPECTED_AUDIO_FILES[sec_id]:
            raise ValueError(f"{sec_id}: audio_file mismatch")
        indices = [c["index"] for c in sec["cues"]]
        if indices != list(range(len(indices))):
            raise ValueError(f"{sec_id}: cue indices are not 0..n-1")
        if len(indices) != EXPECTED_COUNT[sec_id]:
            raise ValueError(f"{sec_id}: cue count mismatch")
        if KEY_PHRASES[sec_id] not in sec["cues"][0]["tts"]:
            raise ValueError(f"{sec_id}: key exponential phrase missing from h2 cue")
        # Every body cue (non-h2) is a genuine 2-4 sentence explanation.
        for cue in sec["cues"]:
            if cue["type"] == "h2":
                continue
            sentences = [s for s in cue["tts"].split("।") if s.strip()]
            if not (2 <= len(sentences) <= 4):
                raise ValueError(f"{sec_id} cue {cue['index']}: explanation has "
                                 f"{len(sentences)} sentences (need 2-4)")
        total += len(indices)
    if total != EXPECTED_TOTAL:
        raise ValueError(f"Expected {EXPECTED_TOTAL} cues, found {total}")
    return total


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
    chunk_paths = []
    durations = []

    print(f"\n[{sec_id}] {len(cues)} cues -> {sec['audio_file']}")
    for cue in cues:
        idx = cue["index"]
        chunk = os.path.join(temp, f"cue_{idx:02d}.mp3")
        rate, pitch, volume = prosody_for(cue)
        role = cue.get("role", "")
        if not valid_audio(chunk):
            print(f"  cue {idx:02d} [{cue['type']:<13}] {rate:>4} {pitch:>5} "
                  f"{role:<10} {cue['tts'][:32]}...")
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

    final_path = os.path.join(AUDIO_DIR, sec["audio_file"])
    concat_to(final_path, concat_paths)

    # Timings from measured durations + the real 350 ms silence chunks.
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

    # Per-section sidecar, kept in sync with the manifest.
    sidecar = os.path.join(AUDIO_DIR,
                           os.path.splitext(sec["audio_file"])[0] + "_cues.json")
    with open(sidecar, "w", encoding="utf-8") as fh:
        json.dump(manifest_cues, fh, ensure_ascii=False, indent=2)

    print(f"  => {sec['audio_file']}: {len(manifest_cues)} cues, "
          f"{cursor / 1000.0:.2f}s, {os.path.getsize(final_path)} bytes")
    return {
        "section_id": sec_id,
        "alias": EXPONENTIAL_ALIASES[sec_id],
        "title": sec["title"],
        "audio_file": sec["audio_file"],
        "total_duration_ms": round(cursor, 1),
        "cues": manifest_cues,
    }


def bump_page_manifest_version():
    """manifest.js?v=N -> ?v=N+1 so browsers reload the rebuilt manifest."""
    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    pattern = re.compile(r"(manifest\.js\?v=)(\d+)")
    matches = pattern.findall(html)
    if not matches:
        raise RuntimeError("Page manifest cache-buster not found")
    new_html, count = pattern.subn(lambda m: m.group(1) + str(int(m.group(2)) + 1), html)
    with open(PAGE_PATH, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_html)
    print(f"  bumped manifest cache-buster: {matches[0][1]} -> {int(matches[0][1]) + 1} "
          f"({count} occurrence(s))")


async def build_all():
    total = assert_clean_scripts()
    print(f"Validated {total} clean cues in {len(SECTIONS_DATA)} sections "
          f"(0 artificial figure labels, 0 Latin/TeX chars, 0 calendar words).")

    built = {}
    for sec_id, sec in SECTIONS_DATA.items():
        built[sec_id] = await build_section(sec_id, sec)

    manifest_sections = {sec_id: built[sec_id] for sec_id in SECTIONS_DATA}
    manifest_data = {
        "course": "lockdown_math",
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

    bump_page_manifest_version()

    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert list(loaded["sections"]) == list(SECTIONS_DATA), "manifest section keys changed"
    total_cues = 0
    total_ms = 0.0
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == EXPECTED_COUNT[sec_id]
        assert [c["type"] for c in msec["cues"]] == EXPECTED_TYPES[sec_id]
        assert msec["audio_file"] == EXPECTED_AUDIO_FILES[sec_id]
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
    assert total_cues == EXPECTED_TOTAL

    print("\n" + "=" * 70)
    print("BUILD COMPLETE - expressive teacher audio, Lockdown Math Lesson 02")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<22} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 4 sections, {total_ms / 1000.0:.2f}s.")
    print("=" * 70)


# --------------------------------------------------------------------------- #
# Headless Chrome verification (channel=chrome, self-contained file://)
# --------------------------------------------------------------------------- #
VERIFY_JS = r"""() => {
  const ne = window.narrationEngine;
  const manifest = window.TEACHER_AUDIO_MANIFEST;
  const sectionEls = [...document.querySelectorAll('.article > section, article section')];

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
  for (const el of sectionEls) {
    if (el.getAttribute('data-no-narration') === 'true') continue;
    const nodes = [...el.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box')];
    const blocks = [];
    for (const node of nodes) {
      if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) continue;
      blocks.push({type: domType(node), text: (node.innerText || '').trim()});
    }
    dom.push({id: el.id, blocks});
  }
  const engine = ne.sections.map(s => ({
    id: s.id, blockCount: s.blocks.length, cueCount: s.cues.length,
    audioFile: s.audioFile, types: s.blocks.map(b => domType(b.element))
  }));
  return {
    manifestPresent: !!manifest,
    hasStudioAudio: !!ne.hasStudioAudio,
    manifestKeys: Object.keys(manifest ? manifest.sections : {}),
    manifest: manifest,
    dom: dom.map(s => ({id: s.id, types: s.blocks.map(b => b.type),
                        texts: s.blocks.map(b => b.text)})),
    engine,
    sectionEls: sectionEls.map(s => ({id: s.id, noNarration: s.getAttribute('data-no-narration')}))
  };
}"""

AUDIO_JS = r"""async (files) => {
  const results = [];
  for (const f of files) {
    const a = new Audio();
    const ok = await new Promise(resolve => {
      const good = () => resolve(true), bad = () => resolve(false);
      a.addEventListener('loadedmetadata', good, { once: true });
      a.addEventListener('error', bad, { once: true });
      a.src = f; a.load();
    });
    results.push({ file: f, ok, duration: isFinite(a.duration) ? a.duration : -1 });
  }
  return results;
}"""


def verify_in_chrome():
    """Return a verification report dict; raises AssertionError on failure."""
    from pathlib import Path
    from playwright.sync_api import sync_playwright

    page_uri = Path(PAGE_PATH).as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page()
        page_errors, console_errors = [], []
        page.on("pageerror", lambda e: page_errors.append("pageerror: " + str(e)))
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.goto(page_uri, wait_until="load")
        page.wait_for_function(
            "() => !!window.narrationEngine && !!window.narrationEngine.sections "
            "&& window.narrationEngine.sections.length > 0 "
            "&& !!window.TEACHER_AUDIO_MANIFEST")
        data = page.evaluate(VERIFY_JS)
        manifest_local = os.path.join(AUDIO_DIR, "manifest.json")
        with open(manifest_local, encoding="utf-8") as fh:
            local_manifest = json.load(fh)
        audio_urls = ["../../assets/audio/lockdown_math/lesson_02/" +
                      local_manifest["sections"][sid]["audio_file"]
                      for sid in SECTIONS_DATA]
        audio_results = page.evaluate(AUDIO_JS, audio_urls)
        browser.close()

    benign = ("ERR_FILE_NOT_FOUND", "404 (File not found)", "Failed to load resource",
              "Permissions policy violation", "net::ERR", "youtube", "youtu.be")
    narration_console_errors = [e for e in console_errors
                                if not any(b.lower() in e.lower() for b in benign)]

    assert page_errors == [], f"JS page errors: {page_errors}"
    assert narration_console_errors == [], f"Unexpected console errors: {narration_console_errors}"
    assert data["manifestPresent"], "window.TEACHER_AUDIO_MANIFEST missing"
    assert data["hasStudioAudio"], "Studio teacher audio not bound"

    mkeys = data["manifestKeys"]
    dom_ids = [s["id"] for s in data["dom"]]
    canonical_ids = list(SECTIONS_DATA)
    assert dom_ids == canonical_ids, f"DOM ids changed: {dom_ids} vs {canonical_ids}"
    assert mkeys == canonical_ids, f"Manifest keys changed: {mkeys}"
    assert canonical_ids == [s["id"] for s in data["engine"]], "Engine ids changed"
    assert not ({"sec-quizzes", "sec-quiz", "sec-media", "sec-simulator",
                 "sec-interactive-lab"} & set(dom_ids)), "non-narrated section leaked"

    nn = [e["id"] for e in data["sectionEls"] if e["noNarration"] == "true"]
    for req in ("sec-interactive-lab", "sec-quizzes", "sec-formulas-glossary"):
        assert req in nn, f"{req} missing no-narration: {nn}"

    tsections = data["manifest"]["sections"]
    total_cues = 0
    total_ms = 0.0
    dup_check = set()
    disallowed = set()
    forbidden_hits = []
    calendar_hits = []
    natural_figure_hits = 0
    prosody_variants = set()
    for sec_id in canonical_ids:
        msec = tsections[sec_id]
        dom_sec = next(s for s in data["dom"] if s["id"] == sec_id)
        eng_sec = next(s for s in data["engine"] if s["id"] == sec_id)
        cues = msec["cues"]
        expected_types = EXPECTED_TYPES[sec_id]

        assert len(cues) == EXPECTED_COUNT[sec_id], (sec_id, len(cues))
        assert len(dom_sec["types"]) == len(cues), (sec_id, "DOM block count", dom_sec["types"])
        assert [c["type"] for c in cues] == expected_types, (sec_id, "manifest types")
        assert dom_sec["types"] == expected_types, (sec_id, "DOM types", dom_sec["types"])
        assert eng_sec["types"] == expected_types, (sec_id, "engine types", eng_sec["types"])
        assert eng_sec["blockCount"] == len(cues) == eng_sec["cueCount"], sec_id
        assert msec["audio_file"] == EXPECTED_AUDIO_FILES[sec_id], (sec_id, "audio_file")
        assert msec["audio_file"] in eng_sec["audioFile"], (sec_id, "engine audio binding")

        for cue in cues:
            total_cues += 1
            key = (sec_id, cue["index"], cue["type"], cue["text"])
            assert key not in dup_check, f"Duplicate cue: {key[:3]}"
            dup_check.add(key)
            if cue["type"] not in ALLOWED_CUE_TYPES:
                disallowed.add(cue["type"])
            if FORBIDDEN_PREFIX in cue["text"]:
                forbidden_hits.append(f"{sec_id}/{cue['index']}")
            low = cue["text"].lower()
            for w in CALENDAR_WORDS:
                if w.lower() in low:
                    calendar_hits.append(f"{sec_id}/{cue['index']}:{w}")
            if NATURAL_FIGURE in cue["text"]:
                natural_figure_hits += 1
            if cue["type"] != "h2":
                sentences = [x for x in cue["text"].split("।") if x.strip()]
                assert 2 <= len(sentences) <= 4, (sec_id, cue["index"], "sentences", len(sentences))

        assert KEY_PHRASES[sec_id] in cues[0]["text"], (sec_id, "key h2 phrase missing")
        # Prosody: every cue exercised via the embedded data (roles included).
        for cue in cues:
            prosody_variants.add(prosody_for(cue))

        cursor = 0.0
        for i, c in enumerate(cues):
            assert abs(c["start_ms"] - cursor) < 1.0, (sec_id, i, "start")
            assert c["duration_ms"] > 0, (sec_id, i, "zero duration")
            assert abs((c["end_ms"] - c["start_ms"]) - c["duration_ms"]) < 1.0, (sec_id, i)
            cursor = c["end_ms"] + (GAP_MS if i < len(cues) - 1 else 0.0)
        assert abs(msec["total_duration_ms"] - cursor) < 1.0, (sec_id, "total_duration_ms")

        af = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(af) and os.path.getsize(af) > 0, af
        total_ms += msec["total_duration_ms"]

    assert total_cues == EXPECTED_TOTAL, total_cues
    assert not disallowed, f"Disallowed cue types: {disallowed}"
    assert not forbidden_hits, f"Artificial figure label found: {forbidden_hits}"
    assert not calendar_hits, f"Calendar content survived: {calendar_hits}"
    assert natural_figure_hits == 5, natural_figure_hits
    # Required prosody rules are exercised (h2, p, chapter-quote, conclusion;
    # figure/formula-box/callout are defined in the spec mapping).
    assert ("-5%", "+2Hz", "+0%") in prosody_variants, prosody_variants
    assert ("+2%", "+0Hz", "+0%") in prosody_variants, prosody_variants
    assert ("-3%", "+0Hz", "+0%") in prosody_variants, prosody_variants
    assert CONCLUSION_PROSODY in prosody_variants, prosody_variants
    assert PROSODY_DEFAULT["figure"] == ("-4%", "+0Hz", "+0%")
    assert PROSODY_DEFAULT["formula-box"] == ("-8%", "+0Hz", "+0%")
    assert PROSODY_DEFAULT["callout"] == ("+0%", "+0Hz", "+0%")

    all_dom_types = [t for s in data["dom"] for t in s["types"]]
    assert not ({"quiz", "media-tab", "b1b-quiz", "b1b-media-tab"} & set(all_dom_types)), all_dom_types

    with open(os.path.join(AUDIO_DIR, "manifest.js"), encoding="utf-8") as fh:
        js_text = fh.read().strip()
    assert js_text.startswith("window.TEACHER_AUDIO_MANIFEST = ") and js_text.endswith(";")
    js_obj = json.loads(js_text[len("window.TEACHER_AUDIO_MANIFEST = "):-1].strip())
    assert js_obj == local_manifest, "manifest.js != manifest.json"

    disk_blobs = [json.dumps(local_manifest, ensure_ascii=False)]
    for sec_id in SECTIONS_DATA:
        side = os.path.join(AUDIO_DIR,
                            os.path.splitext(EXPECTED_AUDIO_FILES[sec_id])[0] + "_cues.json")
        with open(side, encoding="utf-8") as fh:
            side_obj = json.load(fh)
        assert side_obj == local_manifest["sections"][sec_id]["cues"], (sec_id, "sidecar out of sync")
        disk_blobs.append(json.dumps(side_obj, ensure_ascii=False))
    assert not any(FORBIDDEN_PREFIX in b for b in disk_blobs), "forbidden label on disk"
    # Note: calendar-word scans target only human-readable text fields, never the
    # structural legacy keys/audio_file names that are kept for DOM parity.
    for s in data["dom"]:
        for t in s["texts"]:
            assert FORBIDDEN_PREFIX not in t, f"forbidden label in DOM text of {s['id']}"

    # Explicit text-only calendar scan of the on-disk manifest payloads.
    for sec_id in SECTIONS_DATA:
        msec = local_manifest["sections"][sec_id]
        for blob in [msec["title"]] + [c["text"] for c in msec["cues"]]:
            low = blob.lower()
            for w in CALENDAR_WORDS:
                assert w.lower() not in low, f"calendar word {w!r} in manifest text {sec_id}"
    for w in CALENDAR_WORDS:
        assert w.lower() not in MANIFEST_TITLE.lower(), f"calendar word {w!r} in manifest title"

    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    versions = [int(v) for _, v in re.findall(r"(manifest\.js\?v=)(\d+)", html)]
    assert versions and min(versions) >= 2, f"manifest ?v not bumped: {versions}"

    for r in audio_results:
        assert r["ok"] and r["duration"] > 0, f"browser MP3 load failed: {r}"

    report = {
        "channel": "chrome (headless=True)",
        "sections": len(SECTIONS_DATA),
        "cues": total_cues,
        "per_section": {sid: EXPECTED_COUNT[sid] for sid in canonical_ids},
        "manifest_keys": len(mkeys),
        "dom_manifest_1to1": True,
        "duplicates": 0,
        "disallowed_types": 0,
        "quiz_media_tab_types": 0,
        "forbidden_label_hits": 0,
        "calendar_related_words_in_manifest_text": 0,
        "natural_figure_phrasing_cues": natural_figure_hits,
        "h2_key_phrase_woven": True,
        "prosody_h2": list(PROSODY_DEFAULT["h2"]),
        "prosody_figure": list(PROSODY_DEFAULT["figure"]),
        "prosody_formula": list(PROSODY_DEFAULT["formula-box"]),
        "prosody_p": list(PROSODY_DEFAULT["p"]),
        "prosody_callout": list(PROSODY_DEFAULT["callout"]),
        "prosody_conclusion": list(CONCLUSION_PROSODY),
        "gap_ms": GAP_MS,
        "js_page_errors": len(page_errors),
        "narration_console_errors": len(narration_console_errors),
        "preexisting_media_console_errors": len(console_errors) - len(narration_console_errors),
        "mp3_nonzero": True,
        "mp3_browser_loadable": True,
        "json_valid": True,
        "manifest_js_matches_json": True,
        "sidecars_in_sync": True,
        "manifest_version": versions,
        "total_duration_ms": round(total_ms, 1),
        "total_duration_s": round(total_ms / 1000.0, 2),
        "ok": True,
    }
    with open(VERIFY_RESULT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    return report


def main():
    if "--verify-only" not in sys.argv[1:]:
        asyncio.run(build_all())
    else:
        print("--verify-only: skipping build")
    report = verify_in_chrome()
    print("\n" + "=" * 70)
    print("VERIFICATION REPORT (headless Chrome channel=chrome)")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("=" * 70)
    print(f"VERIFIED: {report['cues']}/{report['cues']} cues, DOM<->manifest 1:1, "
          f"0 dups, 0 quiz/media-tab types, non-zero+loadable mp3s, valid JSON, "
          f"0 JS page errors, 0 'চিত্র প্রদর্শনী' labels, "
          f"0 calendar words in narration text, "
          f"{report['natural_figure_phrasing_cues']} natural figure phrasings.")
    print(f"Report written to {VERIFY_RESULT}")


if __name__ == "__main__":
    main()
