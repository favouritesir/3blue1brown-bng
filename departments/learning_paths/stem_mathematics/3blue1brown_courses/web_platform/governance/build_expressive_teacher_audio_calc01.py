# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Calculus Lesson 01
("The Essence of Calculus", Bengali) to the Lesson-01 gold standard.

Deterministic, re-runnable, self-contained:
  * 29 cues in 4 narrated sections with EXACTLY the same section IDs, alias keys,
    audio_file names, cue types and cue order as the live DOM
    (governance/calc01_dom_blocks.json) and the existing manifest.
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Figure cues are genuine 2-4 sentence natural explanations — never the
    artificial label "চিত্র প্রদর্শনী".
  * Every script is clean spoken Bengali with phonetic safeguards:
    x -> এক্স, R -> আর, dr -> ডি আর, pi -> পাই, dx -> ডি এক্স, dA -> ডি এ.
    No TeX, LaTeX, backslashes, $, braces, brackets, em-dashes, raw hyphens or
    Latin letters.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, chapter-quote -3%, p +2%, figure -4%, callout +0%,
      formula-box -8%, conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with the
    exact-ms timings and both canonical + alias section keys of the old manifest.
  * Validates non-zero durations, zero overlap, valid JSON and non-empty mp3s.

Usage:  python governance/build_expressive_teacher_audio_calc01.py
"""

import os
import re
import json
import copy
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
                         "calculus", "lesson_01")
MANIFEST_TITLE = "অধ্যায় ০১ — ক্যালকুলাসের সারমর্ম: ভাঙো, অনুমান করো, জুড়ে দাও"

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

# Parity guards: exact cue-type sequence expected for each narrated section.
EXPECTED_TYPES = {
    "sec-intro":        ["h2", "chapter-quote", "p", "p", "callout", "p"],
    "sec-circle-rings": ["h2", "p", "formula-box", "p", "p", "figure", "p",
                          "callout", "formula-box", "p"],
    "sec-slope-rate":   ["h2", "p", "chapter-quote", "p", "p", "formula-box", "p", "p"],
    "sec-connection":   ["h2", "p", "formula-box", "p", "callout"],
}
EXPECTED_AUDIO_FILES = {
    "sec-intro":        "sec_01_intro.mp3",
    "sec-circle-rings": "sec_02_circle_area.mp3",
    "sec-slope-rate":   "sec_03_derivative.mp3",
    "sec-connection":   "sec_04_connection.mp3",
}
# Canonical DOM section id -> legacy alias key kept in the manifest.
ALIASES = {
    "sec-intro":        "sec_01_intro",
    "sec-circle-rings": "sec_02_circle_area",
    "sec-slope-rate":   "sec_03_derivative",
    "sec-connection":   "sec_04_connection",
}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (29 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-intro": {
        "title": "ক্যালকুলাসের সারমর্ম, হিলবার্টের বিশেষ উদাহরণ ও মহাকৌশল",
        "audio_file": "sec_01_intro.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, ক্যালকুলাসের সারমর্ম, হিলবার্টের বিশেষ উদাহরণ ও মহাকৌশল।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, গণিত চর্চার শিল্প হলো এমন এক বিশেষ ক্ষেত্র খুঁজে বের করা, যার ভেতরে সার্বজনীনতার সমস্ত বীজ সুপ্ত থাকে। বলেছেন ডেভিড হিলবার্ট।"},
            {"index": 2, "type": "p",
             "tts": "যে সত্যটি এতই চেনা, তার ব্যাপারে প্রশ্ন তোলার ইচ্ছেই আমাদের কখনো জন্মেনি। বৃত্তের ক্ষেত্রফল সমান পাই আর স্কয়ার। ছোটবেলা থেকে সূত্রটি মুখস্থ হলেও কেউ কোনোদিন জিজ্ঞেস করেনি, পাই তো পরিধি আর ব্যাসের অনুপাত, তাহলে পরিধির ধ্রুবকটি ক্ষেত্রফলের ভেতরে ব্যাসার্ধের বর্গের সাথে জড়িয়ে গেল কীভাবে। সাধারণত কলেজ বা বিশ্ববিদ্যালয়ে ক্যালকুলাস শেখানোর সময় শিক্ষার্থীদের একগাদা কঠিন সূত্র মুখস্থ করতে দেওয়া হয়, যেমন এক্স স্কয়ারের ডেরিভেটিভ দুই এক্স, চেইন রুল, প্রোডাক্ট রুল কিংবা সমাকলনের তালিকা। কিন্তু এই সূত্রগুলোর পেছনে মূল যে প্রাণবন্ত ভাবনা লুকিয়ে আছে, তা বেশিরভাগ সময় আলোচনায় আসে না।"},
            {"index": 3, "type": "p",
             "tts": "ক্যালকুলাসের মূল সারমর্ম বুঝতে হলে আমাদের জানতে হবে গণিতবিদদের সবচেয়ে শক্তিশালী কৌশলটি। হিলবার্টের উপদেশ মেনে আমরা সাধারণ বৃত্তের বদলে একটি বিশেষ নির্দিষ্ট বৃত্ত দিয়েই শুরু করব, যার ভেতরে লুকিয়ে আছে সমগ্র ক্যালকুলাসের সর্বজনীন বীজ।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, কেন্দ্রীয় দর্শন, ভাঙো, অনুমান করো, জুড়ে দাও। যেকোনো জটিল ও দুর্বোধ্য সমস্যাকে অসংখ্য ক্ষুদ্রাতিক্ষুদ্র এবং সহজ অংশে ভাগ করা, প্রতিটির জন্য একটি ভালো আসন্নায়ন তৈরি করা, এবং তারপর সীমাস্থ অবস্থায় ডি আর শূন্যের দিকে ধাবিত হলে সেগুলোকে পুনরায় একত্রিত করে নিখুঁত সমাধানে পৌঁছানো। এই তিন ধাপই ক্যালকুলাসের হৃৎস্পন্দন।"},
            {"index": 5, "type": "p", "role": "conclusion",
             "tts": "এই পুরো যাত্রায় দুটি প্রধান অস্ত্র বারবার ঘুরে ফিরে আসবে। সমাকলন বা ইন্টিগ্রাল, যার মাধ্যমে অসংখ্য ক্ষুদ্র অংশের যোগফল থেকে মোট ক্ষেত্রফল বের করা হয়। আর অন্তরীকরণ বা ডেরিভেটিভ, যার মাধ্যমে কোনো পরিবর্তনের তাৎক্ষণিক হার পরিমাপ করা হয়।"},
        ],
    },

    "sec-circle-rings": {
        "title": "বৃত্তের ক্ষেত্রফল: বলয় কাটা, আনরোলিং ও রিমান সমষ্টি",
        "audio_file": "sec_02_circle_area.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, বৃত্তের ক্ষেত্রফল, বলয় কাটা, আনরোলিং আর রিমান সমষ্টি।"},
            {"index": 1, "type": "p",
             "tts": "ছোটবেলা থেকেই আমরা জানি যে আর ব্যাসার্ধবিশিষ্ট একটি বৃত্তের ক্ষেত্রফল হলো।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। বৃত্তের ক্ষেত্রফল সমান পাই আর স্কয়ার।"},
            {"index": 3, "type": "p",
             "tts": "কিন্তু কখনো কি ভেবে দেখেছেন, কেন এই সূত্রটি সত্য। পাই তো মূলত একটি বৃত্তের পরিধি আর তার ব্যাসের অনুপাত, অর্থাৎ পাই সমান সি বাই দুই আর, আর সেই সুতোয় বলা যায় সি সমান দুই পাই আর। তাহলে পরিধির ধ্রুবকটি ক্ষেত্রফলের ভেতরে ব্যাসার্ধের বর্গের সাথে কীভাবে এমন নিখুঁতভাবে জড়িয়ে গেল।"},
            {"index": 4, "type": "p",
             "tts": "চলুন গ্রান্ট স্যান্ডারসনের মতো করে ভাবা যাক। ধরা যাক আমাদের কাছে একটি বৃত্ত আছে। আমরা যদি একে সোজা গ্রিড দিয়ে মাপতে যাই, তবে বৃত্তের বাঁকা সীমানা কখনোই সরল বর্গাকৃতির সাথে খাপ খাবে না। কিন্তু যদি আমরা বৃত্তটিকে কয়েকটি সমকেন্দ্রিক পাতলা বলয়ে কেটে ফেলি, তখন প্রতিটি অংশের আসন্নায়ন করা সহজ হয়ে যায়।"},
            {"index": 5, "type": "figure",
             "tts": "লক্ষ্য করুন, বৃত্তটিকে অসংখ্য সমকেন্দ্রিক পাতলা বলয়ে ভাগ করা হয়েছে। হলুদ রেখাটি ব্যাসার্ধ আর, আর গোলাপি রেখাটি সবচেয়ে বাইরের বলয়ের অতিক্ষুদ্র বেধ ডি আর নির্দেশ করছে। প্রতিটি বলয়ের ব্যাসার্ধ ক্রমে বাড়ছে, কিন্তু বেধ একই থাকছে। এই সুসমতাই পরে সব বলয়ের ক্ষেত্রফল যোগ করার কাজটিকে সহজ করে দেবে।"},
            {"index": 6, "type": "p",
             "tts": "মনে করি মূল বৃত্তটির কেন্দ্র থেকে আর দূরত্বে অবস্থিত যেকোনো একটি নির্দিষ্ট বলয় নেওয়া হলো। এই বলয়টির বেধ অত্যন্ত পাতলা, যাকে ক্যালকুলাসের ভাষায় আমরা বলি ডি আর, অর্থাৎ ব্যাসার্ধের একটি অতিক্ষুদ্র পরিবর্তন।"},
            {"index": 7, "type": "callout",
             "tts": "বিশেষ নোট, একটি বলয়কে সোজা করা। যদি আমরা এই পাতলা বলয়টিকে এক জায়গায় কাঁচি দিয়ে কেটে সোজা লম্বা ফিতার মতো বিছিয়ে দিই, তবে সেটি প্রায় একটি নিখুঁত আয়তক্ষেত্র তৈরি করবে। এই আয়তক্ষেত্রের দৈর্ঘ্য হবে মূল বলয়ের পরিধির সমান দুই পাই আর, আর এর প্রস্থ বা উচ্চতা হবে বলয়টির পাতলা বেধ ডি আর। অতএব এই একক বলয়ের অতিক্ষুদ্র ক্ষেত্রফল ডি এ হবে দৈর্ঘ্য আর প্রস্থের গুণফল, অর্থাৎ ডি এ প্রায় সমান দুই পাই আর গুণ ডি আর।"},
            {"index": 8, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। অতিক্ষুদ্র ক্ষেত্রফল ডি এ প্রায় সমান দুই পাই আর গুণ ডি আর।"},
            {"index": 9, "type": "p", "role": "conclusion",
             "tts": "অবশ্যই, যেহেতু বলয়টির ভেতরের পরিধি দুই পাই আর আর বাইরের পরিধি দুই পাই ইনটু আর যোগ ডি আর সামান্য ভিন্ন, তাই এটি পুরোপুরি সোজা আয়তক্ষেত্র না হয়ে সামান্য ট্রাপিজয়েড হয়। কিন্তু ডি আরের মান যত ক্ষুদ্র থেকে ক্ষুদ্রতর হবে, এই পার্থক্য ততই অদৃশ্য হয়ে যাবে আর আয়তক্ষেত্রের আসন্নায়নটি পরম নির্ভুলতার দিকে ধাবিত হবে।"},
        ],
    },

    "sec-slope-rate": {
        "title": "পরিবর্তনের হার ও ঢাল: ডেরিভেটিভের প্রথম সাক্ষাৎ",
        "audio_file": "sec_03_derivative.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, পরিবর্তনের হার ও ঢাল, ডেরিভেটিভের প্রথম সাক্ষাৎ।"},
            {"index": 1, "type": "p",
             "tts": "ক্যালকুলাসের অপর পিঠ হলো পরিবর্তনের হার অনুসন্ধান করা। বৃত্তের ক্ষেত্রফলের উদাহরণটিতেই যদি আমরা প্রশ্ন করি।"},
            {"index": 2, "type": "chapter-quote",
             "tts": "যদি বৃত্তের ব্যাসার্ধ আর কে খুব সামান্য পরিমাণ ডি আর বৃদ্ধি করা হয়, তবে ক্ষেত্রফল এ ঠিক কতটুকু বৃদ্ধি পাবে।"},
            {"index": 3, "type": "p",
             "tts": "বৃত্তের পরিধিতে যুক্ত হওয়া নতুন অংশের ক্ষেত্রফলই হলো সেই বৃদ্ধি ডি এ। আমরা আগেই দেখেছি, এই বৃদ্ধি হলো একদম বাইরের বলয়টির ক্ষেত্রফল, যার মান দুই পাই আর গুণ ডি আর।"},
            {"index": 4, "type": "p",
             "tts": "উভয়পক্ষকে ডি আর দিয়ে ভাগ করলে আমরা পাই, ক্ষেত্রফলের পরিবর্তনের হার হুবহু পরিধির সমান।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। ডি এ বাই ডি আর সমান দুই পাই আর।"},
            {"index": 6, "type": "p",
             "tts": "এটি এক পরম জাদুকরী উপলব্ধি। বৃত্তের ক্ষেত্রফলের পরিবর্তনের হার, অর্থাৎ ডি এ বাই ডি আর, হুবহু তার পরিধির দুই পাই আরের সমান। কারণ ব্যাসার্ধ সামান্য একটু বাড়ালে বৃত্তের ক্ষেত্রফল কেবল তার পরিধি বরাবরই নতুন স্তর হিসেবে বিস্তৃত হতে পারে। পরিবর্তনের হার নিজেরাই এক পরিচিত জ্যামিতিক রাশিকে, পরিধিকে, ছুঁয়ে যায়।"},
            {"index": 7, "type": "p", "role": "conclusion",
             "tts": "সাধারণভাবে, যেকোনো ফাংশন এফ অফ এক্সের জন্য ইনপুটের ক্ষুদ্র পরিবর্তন হলো ডি এক্স, আউটপুটের সংশ্লিষ্ট বৃদ্ধি হলো ডি এফ, আর লেখচিত্রের স্পর্শকের ঢাল হলো ডি এফ বাই ডি এক্স। যেমন এফ অফ এক্স সমান এক্স স্কয়ারের ক্ষেত্রে ডি এফ বাই ডি এক্স সমান দুই এক্স, মূলবিন্দুতে ঢাল প্রায় শূন্য, দূরে গেলে ক্রমেই খাড়া।"},
        ],
    },

    "sec-connection": {
        "title": "ক্ষেত্রফল ও ঢালের সংযোগ: ক্যালকুলাসের মৌলিক উপপাদ্য",
        "audio_file": "sec_04_connection.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, ক্ষেত্রফল ও ঢালের সংযোগ, ক্যালকুলাসের মৌলিক উপপাদ্য।"},
            {"index": 1, "type": "p",
             "tts": "এ পর্যন্ত ক্ষেত্রফল আর পরিবর্তনের হারকে আমরা ভেবেছি দুটি আলাদা গল্প, কিন্তু ক্যালকুলাসের প্রাণবন্ত রহস্য হলো, এরা পরস্পরের দর্পণ, একটির ভেতরে অন্যটির প্রতিবিম্ব ঘুরে আসে।"},
            {"index": 2, "type": "formula-box",
             "tts": "মৌলিক উপপাদ্যের সূত্র। ডি বাই ডি এক্স অফ এ অফ এক্স সমান এফ অফ এক্স।"},
            {"index": 3, "type": "p",
             "tts": "একটি নতুন ফাংশন সংজ্ঞায়িত করুন, এ অফ এক্স, অর্থাৎ লেখচিত্রের নিচে জমা হওয়া ক্ষেত্রফল। ডান দিকে অতি ক্ষুদ্র ডি এক্স পদক্ষেপে যোগ হয় অতি ক্ষুদ্র এক টুকরো ক্ষেত্রফল, মূলত উচ্চতা এফ অফ এক্স গুণ ডি এক্স। ফলে এ অফ এক্সের পরিবর্তনের হার ফিরিয়ে দেয় ঢাল এফ অফ এক্স নিজেকেই। বৃত্তে এসে গল্পটি পূর্ণতা পায়, পাই আর স্কয়ারের ঢাল দুই পাই আর, ঠিক পরিধি।"},
            {"index": 4, "type": "callout", "role": "conclusion",
             "tts": "মূল অন্তর্দৃষ্টি। ক্ষুদ্রাতিক্ষুদ্র বলয়ের যোগফল, অর্থাৎ সমাকলন, দেয় ক্ষেত্রফল, আর ক্ষেত্রফলের ঢাল, অর্থাৎ অন্তরীকরণ, ফিরিয়ে দেয় পরিধিকে। যেমন গুণ আর ভাগ বিপরীত দুই ক্রিয়া, ক্যালকুলাসের এই দুই স্তম্ভও ঠিক তেমনি। বৃত্তের বিশেষ এই উদাহরণের ভেতরেই লুকায় ক্যালকুলাসের সর্বজনীন বীজ। অতএব ক্যালকুলাস মুখস্থ সূত্রের ঝোলা নয়, এটি সেই শিল্প যেখানে সমষ্টি রূপ নেয় সীমায়, আর ক্ষেত্রফল ও ঢাল বলে যায় পরস্পরের গল্প।"},
        ],
    },
}

# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"


def assert_clean_scripts():
    """Fail before any TTS work if a script still contains markup or Latin text."""
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars {bad!r} in {cue['tts']!r}")
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: artificial figure label present")

    # Structural parity guards.
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
        total += len(indices)
    if total != 29:
        raise ValueError(f"Expected 29 cues, found {total}")

    # Figure cues must be genuine 2-4 sentence explanations.
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            if cue["type"] == "figure":
                sentences = [s for s in cue["tts"].split("।") if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(f"{sec_id} cue {cue['index']}: figure has {len(sentences)} sentences")


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
        "alias": ALIASES[sec_id],
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
        built = await build_section(sec_id, sec)
        manifest_sections[sec_id] = built
        # Legacy alias key mirrors the canonical section exactly (same fields).
        manifest_sections[ALIASES[sec_id]] = copy.deepcopy(built)

    manifest_data = {
        "course": "calculus",
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
    expected_keys = set(SECTIONS_DATA) | set(ALIASES.values())
    assert set(loaded["sections"]) == expected_keys
    total_cues = 0
    total_ms = 0.0
    figures = 0
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == len(EXPECTED_TYPES[sec_id])
        assert loaded["sections"][ALIASES[sec_id]] == msec
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    assert total_cues == 29

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Calculus Lesson 01")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<20} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 4 sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json is valid JSON; all 4 mp3 files exist and are non-empty.")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(build_all())
