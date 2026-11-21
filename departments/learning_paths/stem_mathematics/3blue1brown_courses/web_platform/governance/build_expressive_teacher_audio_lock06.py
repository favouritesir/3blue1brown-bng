# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Lockdown Math Lesson 06
("Continuous Probabilities and Probability Density", Bengali) to the
gold standard — warm, natural, fully phonetic figure phrasing, NO artificial
figure label ("চিত্র প্রদর্শনী" is NEVER used).

Deterministic, re-runnable, self-contained:
  * 36 cues in 6 narrated sections with EXACTLY the same section IDs, audio_file
    names, cue type and cue order as the live narration-engine DOM.
    Authoritative DOM extraction (governance/_extract_lock06_dom.py, via the
    narration_engine.js selector `.article > section, article section` with
    `data-no-narration` filtering and the canonical readable-node selector)
    confirmed:
        sec-discrete-to-continuous -> [h2, p, p, p, formula-box, formula-box]  (6)
        sec-zero-prob-paradox      -> [h2, p, p, p, formula-box, formula-box]  (6)
        sec-density-concept        -> [h2, p, p, p, formula-box, formula-box]  (6)
        sec-uniform-exponential    -> [h2, p, p, p, formula-box, formula-box]  (6)
        sec-cdf-calculus           -> [h2, p, p, p, formula-box, formula-box]  (6)
        sec-clt-emergence          -> [h2, p, p, p, formula-box, formula-box]  (6)
    Total = 36 cues. The six *-study companions plus sec-interactive-lab,
    sec-quizzes and sec-formulas-glossary carry data-no-narration="true" and
    are deliberately excluded. There are NO quiz / media-tab cue types.
  * Every cue is an expressive, natural 2-4 sentence Bengali teacher
    explanation of that figure/formula, with the topic woven in naturally.
    Teacher phrasing uses "চিত্রে দেখা যাচ্ছে" or direct explanation — the
    artificial "চিত্র প্রদর্শনী" label is forbidden.
  * Fully phonetic spoken Bengali (no TeX / Latin / markup). Safeguards:
        density -> ডেনসিটি, PDF -> পি ডি এফ, CDF -> সিডিএফ,
        uniform -> ইউনিফর্ম, exponential -> এক্সপোনেনশিয়াল.
  * Per-cue prosody via edge_tts.Communicate(rate=, pitch=, volume=):
        h2 -5%/+2Hz, figure -4%, formula-box -8%, p +2%, callout +0%,
        conclusion -3%. A real 350 ms silence chunk between cues.
  * ffmpeg -c copy concat into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) + the
    per-section *_cues.json sidecars, all with exact measured ms timings.
  * Bumps the page cache-buster manifest.js?v=N -> ?v=N+1.
  * verify_in_chrome() re-checks everything headlessly with channel=chrome.
  * The _backup_before_expressive_build/ folder is NEVER touched. No other
    lesson or library is touched.

Usage:
  python governance/build_expressive_teacher_audio_lock06.py
  python governance/build_expressive_teacher_audio_lock06.py --verify-only
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
                         "lockdown_math", "lesson_06")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "lockdown_math", "lesson_06.html")
VERIFY_RESULT = os.path.join(SCRIPT_DIR, "_verify_lock06_result.json")

# Prosody keyed by cue type: (rate, pitch, volume) — gold-standard spec.
PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),   # warm, slightly slower opening
    "h3":            ("-3%", "+0Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),
    "p":             ("+2%", "+0Hz", "+0%"),   # natural teacher pace
    "figure":        ("-4%", "+0Hz", "+0%"),   # slower, considerate visual explanation
    "callout":       ("+0%", "+0Hz", "+0%"),
    "callout-blue":  ("+0%", "+0Hz", "+0%"),
    "callout-gold":  ("+0%", "+0Hz", "+0%"),
    "callout-green": ("+0%", "+0Hz", "+0%"),
    "code-showcase": ("-4%", "+0Hz", "+0%"),
    "formula-box":   ("-8%", "+0Hz", "+0%"),   # slow and deliberate
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")     # calm concluding prose

ALLOWED_CUE_TYPES = set(PROSODY_DEFAULT) | {"conclusion"}

# Exact DOM block-type sequence per narrated section (from narration_engine).
EXPECTED_TYPES = {
    "sec-discrete-to-continuous": ["h2", "p", "p", "p", "formula-box", "formula-box"],
    "sec-zero-prob-paradox":      ["h2", "p", "p", "p", "formula-box", "formula-box"],
    "sec-density-concept":        ["h2", "p", "p", "p", "formula-box", "formula-box"],
    "sec-uniform-exponential":    ["h2", "p", "p", "p", "formula-box", "formula-box"],
    "sec-cdf-calculus":           ["h2", "p", "p", "p", "formula-box", "formula-box"],
    "sec-clt-emergence":          ["h2", "p", "p", "p", "formula-box", "formula-box"],
}
# Audio-file names are the EXISTING manifest keys (canonical section ids).
EXPECTED_AUDIO_FILES = {sid: sid + ".mp3" for sid in EXPECTED_TYPES}
EXPECTED_COUNT = {sid: len(types) for sid, types in EXPECTED_TYPES.items()}
EXPECTED_TOTAL = 36

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (36 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-discrete-to-continuous": {
        "title": "বিচ্ছিন্ন স্তম্ভ থেকে অবিচ্ছিন্ন তরঙ্গে উত্তরণ",
        "audio_file": "sec-discrete-to-continuous.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "আমাদের প্রথম পরিচ্ছেদ, বিচ্ছিন্ন স্তম্ভ থেকে অবিচ্ছিন্ন তরঙ্গে উত্তরণ। "
             "চিত্রে দেখা যাচ্ছে ছক্কার ছয়টি আলাদা স্তম্ভ ধীরে ধীরে মিশে একটিমাত্র মসৃণ বক্ররেখায় পরিণত হচ্ছে। "
             "বিচ্ছিন্ন গণনা যেখানে শেষ হয়, সেখানেই সমাকলনের যাত্রা শুরু। "
             "এই পরিচ্ছেদে আমরা দেখব কীভাবে সমষ্টি রূপ নেয় অবিচ্ছিন্ন সমাকলনে।"},
            {"index": 1, "type": "p",
             "tts":
             "আমরা সাধারণত ছক্কার মতো বিচ্ছিন্ন ঘটনার কথা ভাবি, যেখানে প্রতিটি ফলাফলের একটি নির্দিষ্ট স্তম্ভ আছে। "
             "চিত্রে দেখা যাচ্ছে সেই স্তম্ভগুলোর প্রস্থ ক্রমাগত সংকুচিত হয়ে আসছে। "
             "বাস্তব জগতের অপেক্ষার সময় বা তাপমাত্রা কিন্তু এইরকম পৃথক ধাপে চলে না। "
             "সেগুলো একটি অবিচ্ছিন্ন ধারায় বিস্তৃত থাকে।"},
            {"index": 2, "type": "p",
             "tts":
             "হিস্টোগ্রামের প্রতিটি বারের প্রস্থ যখন শূন্যের কাছাকাছি নামানো হয়, তখন অসংখ্য সূক্ষ্ম স্তম্ভ একসাথে মিশে যায়। "
             "চিত্রে দেখা যাচ্ছে ধাপগুলোর কড়া প্রান্ত মসৃণ হয়ে একটি সুন্দর তরঙ্গ তৈরি করছে। "
             "এই রূপান্তরেই বিচ্ছিন্ন সম্ভাবনা ভর ফাংশন থেকে পি ডি এফের জন্ম হয়। "
             "পি ডি এফ মানে সম্ভাব্যতা ঘনত্ব অপেক্ষক, যা অবিচ্ছিন্ন জগতের ভাষা।"},
            {"index": 3, "type": "p",
             "tts":
             "বিচ্ছিন্ন জগতে আমরা সকল ফলাফলের সম্ভাবনা যোগ করে এক পাই, কিন্তু অবিচ্ছিন্ন জগতে সেই যোগের জায়গা নেয় সমাকলন। "
             "চিত্রে দেখা যাচ্ছে স্তম্ভগুলোর উচ্চতার যোগফল ধীরে ধীরে বক্ররেখার নিচের ক্ষেত্রফলে রূপ নিচ্ছে। "
             "সমষ্টি থেকে সমাকলনে এই উত্তরণই এই পর্বের মূল কথা। "
             "গ্রান্ট স্যান্ডারসন এই রূপান্তরটিই আমাদের দেখিয়েছেন।"},
            {"index": 4, "type": "formula-box",
             "tts":
             "এই প্রথম সূত্রটি বিচ্ছিন্ন জগতের কথা বলে, সকল সম্ভাবনার যোগফল এক। "
             "চিত্রে দেখা যাচ্ছে প্রতিটি স্তম্ভের উচ্চতা যোগ করলে ঠিক এক পাওয়া যাচ্ছে। "
             "কিন্তু অবিচ্ছিন্ন জগতে উচ্চতার বদলে ক্ষেত্রফলই আসল পরিমাপ। "
             "তাই পরের সূত্রটি আমাদের সেই নতুন নিয়ম শেখায়।"},
            {"index": 5, "type": "formula-box",
             "tts":
             "এই দ্বিতীয় সূত্রটি অবিচ্ছিন্ন জগতের স্বাভাবিকীকরণ শর্ত। "
             "বক্ররেখার নিচের মোট ক্ষেত্রফল, অর্থাৎ সমগ্র অঞ্চল জুড়ে সমাকলনের মান সর্বদা এক। "
             "চিত্রে দেখা যাচ্ছে বাঁ দিক থেকে ডান দিক পর্যন্ত পুরো এলাকা এককভাবে পূর্ণ হয়ে আছে। "
             "মনে রাখতে হবে, বিচ্ছিন্ন হোক কিংবা অবিচ্ছিন্ন, মোট সম্ভাবনা কখনো একের বেশি হয় না।"},
        ],
    },

    "sec-zero-prob-paradox": {
        "title": "একক বিন্দুর শূন্য সম্ভাব্যতা প্যারাডক্স",
        "audio_file": "sec-zero-prob-paradox.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "দ্বিতীয় পরিচ্ছেদ, একক বিন্দুর শূন্য সম্ভাব্যতা প্যারাডক্স। "
             "চিত্রে দেখা যাচ্ছে এক মিটারের রেখার ওপর একটি সূচ আঘাত করেছে একটিমাত্র সুনির্দিষ্ট বিন্দুতে। "
             "অথচ সেই বিন্দুর নিজস্ব সম্ভাবনা অবিকল শূন্য। "
             "এই আপাত বিরোধটিই আমরা আজ ভেঙে বুঝে নেব।"},
            {"index": 1, "type": "p",
             "tts":
             "ধরা যাক, শূন্য থেকে এক মিটারের একটি স্কেলে আমরা সম্পূর্ণ দৈবভাবে একটি সূচ ফেলেছি। "
             "চিত্রে দেখা যাচ্ছে সেটি অবিকল মাঝের কোনো এক বিন্দুতে বিঁধেছে। "
             "সেই নিখুঁত বিন্দুতে পড়ার সম্ভাবনা কত, এই প্রশ্নটি আমাদের প্যারাডক্সের জন্ম দেয়।"},
            {"index": 2, "type": "p",
             "tts":
             "এই স্কেলে অসীম সংখ্যক বিন্দু আছে, যার পৃথক গণনা করা সম্ভব নয়। "
             "যদি প্রতিটি বিন্দুর জন্য সামান্যতম সম্ভাবনাও বরাদ্দ করি, তবে অসীম সংখ্যক বিন্দু যোগ করে মোট সম্ভাবনা অসীম হয়ে যাবে। "
             "কিন্তু সম্ভাবনার মৌলিক নিয়ম বলে মোট একের বেশি হতে পারে না। "
             "তাই একক বিন্দুর সম্ভাবনা শূন্য ছাড়া উপায় নেই।"},
            {"index": 3, "type": "p",
             "tts":
             "তাহলে কি সূচটি কোথাও পড়বে না, এই প্রশ্ন স্বাভাবিক। "
             "অবশ্যই সেটি কোনো না কোনো বিন্দুতে নিশ্চিতভাবেই বিঁধবে। "
             "সমাধান হলো, শূন্য সম্ভাবনা মানেই অসম্ভব নয়। "
             "একটি বিন্দুর দৈর্ঘ্য যেমন শূন্য, তেমনি অসংখ্য শূন্য দৈর্ঘ্যের বিন্দু মিলেই এক মিটারের সম্পূর্ণ স্কেল তৈরি হয়।"},
            {"index": 4, "type": "formula-box",
             "tts":
             "এই সূত্রটি আমাদের প্যারাডক্সের গাণিতিক রূপ। "
             "যেকোনো নির্দিষ্ট বিন্দুতে মান পতিত হওয়ার সম্ভাবনা অবিকল শূন্য। "
             "চিত্রে দেখা যাচ্ছে বিন্দুটির চারপাশে কোনো প্রস্থ নেই, তাই কোনো ক্ষেত্রফলও নেই। "
             "অথচ সূচটি সেই বিন্দুতেই পড়েছে, এটিই বোঝাতে হয়।"},
            {"index": 5, "type": "formula-box",
             "tts":
             "এই দ্বিতীয় সূত্রটি প্রান্তবিন্দুর স্বাধীনতার কথা বলে। "
             "যেহেতু একক বিন্দুর মান শূন্য, তাই ব্যবধানের দুই প্রান্তে সমতা চিহ্ন থাকা বা না থাকায় ক্ষেত্রফল বদলায় না। "
             "চিত্রে দেখা যাচ্ছে একই এলাকা দুইভাবেই লেখা যাচ্ছে। "
             "এটি আমাদের পরবর্তী পাঠের জন্য এক ছোট্ট কিন্তু গুরুত্বপূর্ণ কৌশল শেখায়।"},
        ],
    },

    "sec-density-concept": {
        "title": "সম্ভাব্যতা ঘনত্ব f(x): উচ্চতা বনাম ক্ষেত্রফল",
        "audio_file": "sec-density-concept.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "তৃতীয় পরিচ্ছেদ, সম্ভাব্যতা ঘনত্ব বা পি ডি এফ, উচ্চতা বনাম ক্ষেত্রফল। "
             "চিত্রে দেখা যাচ্ছে একটি বক্ররেখা ওপর নিচে ওঠানামা করছে, আর তার নিচে কিছু এলাকা ছায়াবৃত আছে। "
             "বিন্দুর সম্ভাবনা শূন্য হলেও এই উচ্চতা আমাদের অনেক কিছু বলে দেয়। "
             "আজ আমরা বুঝে নেব উচ্চতা আর ক্ষেত্রফলের সেই সম্পর্ক।"},
            {"index": 1, "type": "p",
             "tts":
             "পদার্থবিজ্ঞানের ভর ঘনত্বের কথা ভাবুন, একটি পাতলা তারের কোনো এক পরমাণুর নিজস্ব ভর প্রায় শূন্য। "
             "চিত্রে দেখা যাচ্ছে তারের কোথাও কোথাও ঘনত্ব বেশি, কোথাও কম। "
             "কোনো ক্ষুদ্র অংশের ভর হয় ঘনত্ব গুণ দৈর্ঘ্য। "
             "সম্ভাব্যতা ঘনত্বও ঠিক একইভাবে কাজ করে।"},
            {"index": 2, "type": "p",
             "tts":
             "সম্ভাব্যতা ঘনত্ব মানেই প্রতি একক দৈর্ঘ্যে সম্ভাবনার ঘনত্ব, সরাসরি সম্ভাবনা নয়। "
             "চিত্রে দেখা যাচ্ছে বক্ররেখার কোনো অংশ অনেক উঁচু, কিন্তু সেটি কেবল স্থানীয় ঘনত্ব বেশি বলে জানায়। "
             "কোনো ক্ষুদ্র ব্যবধানে সম্ভাবনা পেতে হলে সেই উচ্চতাকে দৈর্ঘ্য দিয়ে গুণ করতে হয়। "
             "আসল সম্ভাবনা লুকিয়ে আছে বক্ররেখার নিচের ক্ষেত্রফলে।"},
            {"index": 3, "type": "p",
             "tts":
             "অনেকেই ভুল করে ভাবেন ঘনত্ব কখনো একের বেশি হতে পারে না, অথচ চিত্রে দেখা যাচ্ছে সংকীর্ণ এক ব্যবধানে বক্ররেখা অনেক উঁচু করে উঠেছে। "
             "যদি কোনো চলক শূন্য থেকে এক দশমাংশের মধ্যে সুষমভাবে থাকে, তবে তার ডেনসিটি হবে দশ, কারণ দশ গুণ এক দশমাংশ করে মোট ক্ষেত্রফল দাঁড়ায় এক। "
             "সম্ভাবনা কখনো এক ছাড়াতে পারে না, কিন্তু ডেনসিটি যেকোনো ধনাত্মক মান নিতে পারে।"},
            {"index": 4, "type": "formula-box",
             "tts":
             "এই সূত্রটি ব্যবধানের সম্ভাবনা কীভাবে বের করতে হয় তা শেখায়। "
             "বাঁ প্রান্ত থেকে ডান প্রান্ত পর্যন্ত বক্ররেখার নিচের অংশের সমাকলনই হলো আমাদের খোঁজা সম্ভাবনা। "
             "চিত্রে দেখা যাচ্ছে ছায়াবৃত এলাকাটি ঠিক এই দুই সীমার মধ্যেই আবদ্ধ। "
             "উচ্চতা নয়, এই ক্ষেত্রফলই আসল উত্তর।"},
            {"index": 5, "type": "formula-box",
             "tts":
             "এই শেষ সূত্রটি ঘনত্ব অপেক্ষকের দুটি মৌলিক শর্ত দেয়। "
             "প্রথমটি হলো ঘনত্ব কখনো ঋণাত্মক হতে পারে না, দ্বিতীয়টি হলো সমগ্র জগত জুড়ে মোট ক্ষেত্রফল এক। "
             "চিত্রে দেখা যাচ্ছে বক্ররেখা কখনো নিচে নামছে না আর পুরো এলাকা এককভাবে ভরে গেছে। "
             "এই দুটি শর্তই একটি বৈধ পি ডি এফকে চেনা।"},
        ],
    },

    "sec-uniform-exponential": {
        "title": "বাস্তব মডেল: সুষম বণ্টন ও এক্সপোনেনশিয়াল স্মৃতিহীনতা",
        "audio_file": "sec-uniform-exponential.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "চতুর্থ পরিচ্ছেদ, বাস্তব মডেল, সুষম বণ্টন ও এক্সপোনেনশিয়াল স্মৃতিহীনতা। "
             "চিত্রে দেখা যাচ্ছে একদিকে সমতল আয়তাকার ঘনত্ব, অন্যদিকে ধীরে ধীরে নামতে থাকা একটি বক্ররেখা। "
             "এই দুটি মডেল আমাদের দৈনন্দিন অপেক্ষার সময় বোঝায়। "
             "আজ আমরা দেখব কীভাবে একই ঘনত্বের ভাষা দুই রূপে প্রকাশ পায়।"},
            {"index": 1, "type": "p",
             "tts":
             "সবচেয়ে সরল মডেল হলো ইউনিফর্ম বা সুষম বণ্টন। "
             "ধরা যাক, একটি ট্রেন প্রতি দশ মিনিটে আসে এবং আপনি কোনো রুটিন না দেখেই স্টেশনে পৌঁছেছেন। "
             "চিত্রে দেখা যাচ্ছে অপেক্ষার সময়ের ঘনত্ব একটি সমতল অনুভূমিক রেখা, সব জায়গায় একই উচ্চতা। "
             "অর্থাৎ শূন্য থেকে দশ মিনিটের যেকোনো মুহূর্ত সমান সম্ভাবনায় আসতে পারে।"},
            {"index": 2, "type": "p",
             "tts":
             "অন্য একটি অত্যন্ত গুরুত্বপূর্ণ মডেল হলো এক্সপোনেনশিয়াল বণ্টন, যা তেজস্ক্রিয় ক্ষয় বা কলের অপেক্ষার সময় ব্যাখ্যা করে। "
             "চিত্রে দেখা যাচ্ছে ঘনত্ব শুরুতে বেশি থেকে ধীরে ধীরে নিচে নামছে, কিন্তু কখনো শূন্যে পৌঁছাচ্ছে না। "
             "এই আকৃতিই এক্সপোনেনশিয়াল মডেলের স্বাক্ষর। "
             "এটি আমাদের বলে দেয় ক্ষয় বা অপেক্ষা কতটা দ্রুত ঘটছে।"},
            {"index": 3, "type": "p",
             "tts":
             "এই মডেলের সবচেয়ে আশ্চর্য বৈশিষ্ট্য হলো স্মৃতিহীনতা। "
             "আপনি ইতিমধ্যে পাঁচ মিনিট অপেক্ষা করেছেন জেনেও আরও তিন মিনিট অপেক্ষার সম্ভাবনা ঠিক ততটাই, যতটা শুরুতে তিন মিনিটের জন্য ছিল। "
             "চিত্রে দেখা যাচ্ছে বক্ররেখা তার আগের অতীত মুছে প্রতিটি মুহূর্তে নতুন করে শুরু হয়। "
             "অতীতের অপেক্ষা ভবিষ্যতের সম্ভাবনাকে কোনোভাবেই বদলায় না।"},
            {"index": 4, "type": "formula-box",
             "tts":
             "এই সূত্রটি ইউনিফর্ম বণ্টনের ঘনত্ব দেখায়। "
             "নির্দিষ্ট ব্যবধানের দৈর্ঘ্য দিয়ে এক ভাগ করলেই সমতল ঘনত্বের সেই ধ্রুবক উচ্চতা পাওয়া যায়। "
             "চিত্রে দেখা যাচ্ছে পুরো ব্যবধান জুড়ে বক্ররেখা একই রেখায় দাঁড়িয়ে আছে। "
             "আর বাইরের যেকোনো মানের সম্ভাবনা অবিকল শূন্য।"},
            {"index": 5, "type": "formula-box",
             "tts":
             "এই সূত্রটি এক্সপোনেনশিয়াল বণ্টনের ঘনত্ব আর তার অতিক্রম সম্ভাবনা দেখায়। "
             "সময় যত বাড়তে থাকে, বেঁচে থাকার সম্ভাবনা তত কমতে থাকে, কিন্তু কখনো শূন্য হয় না। "
             "চিত্রে দেখা যাচ্ছে রেখাটি অনন্তের দিকে ধাবিত হতে হতে ক্রমাগত নিচে নামছে। "
             "এই নিরবচ্ছিন্ন ক্ষয়ই স্মৃতিহীনতার গাণিতিক রূপ।"},
        ],
    },

    "sec-cdf-calculus": {
        "title": "ক্রমযোজিত সম্ভাবনা (CDF) ও ক্যালকুলাসের মৌলিক উপপাদ্য",
        "audio_file": "sec-cdf-calculus.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "পঞ্চম পরিচ্ছেদ, ক্রমযোজিত সম্ভাবনা বা সিডিএফ ও ক্যালকুলাসের মৌলিক উপপাদ্য। "
             "চিত্রে দেখা যাচ্ছে বাঁ দিক থেকে শুরু করে বক্ররেখার নিচে ক্ষেত্রফল ধীরে ধীরে জমা হচ্ছে। "
             "এই সঞ্চিত ক্ষেত্রফলটিই আমাদের নতুন অপেক্ষক, যার নাম সিডিএফ। "
             "আজ আমরা দেখব কীভাবে এটি পি ডি এফের সাথে গাণিতিকভাবে ধরে যায়।"},
            {"index": 1, "type": "p",
             "tts":
             "ক্রমযোজিত বণ্টন অপেক্ষক আমাদের বলে দেয়, বর্তমান বিন্দু পর্যন্ত মোট কত সম্ভাবনা জমা হয়েছে। "
             "চিত্রে দেখা যাচ্ছে বাঁ প্রান্ত থেকে শুরু করে বর্তমান অবস্থান পর্যন্ত ছায়াবৃত এলাকা ক্রমে বাড়ছে। "
             "ডান দিকে এগোনোর সাথে সাথে এই সঞ্চিত মানও বেড়ে চলে। "
             "শেষ পর্যন্ত সেটি একের দিকে পৌঁছে যায়।"},
            {"index": 2, "type": "p",
             "tts":
             "এখানেই ক্যালকুলাসের মৌলিক উপপাদ্য তার সবচেয়ে সুন্দর রূপ নেয়। "
             "ক্ষেত্রফল সঞ্চয়কারী অপেক্ষককে অন্তরীকরণ করলে আমরা অবিকল আগের ঘনত্ব অপেক্ষক ফেরত পাই। "
             "চিত্রে দেখা যাচ্ছে সঞ্চিত রেখার ঢাল যত বাড়ছে, নিচের ঘনত্বের উচ্চতা তত বেশি। "
             "অর্থাৎ সিডিএফের ঢালই হলো পি ডি এফের উচ্চতা।"},
            {"index": 3, "type": "p",
             "tts":
             "এই সম্পর্কের সবচেয়ে বড় সুবিধা হলো যেকোনো ব্যবধানের সম্ভাবনা এক নিমিষে বের করা। "
             "আগে যেখানে সমাকলন করতে হতো, এখন শুধু দুই প্রান্তের সঞ্চিত মানের বিয়োগ করলেই কাজ শেষ। "
             "চিত্রে দেখা যাচ্ছে দুটি বিন্দুর মানের পার্থক্যই মাঝের ছায়াবৃত এলাকার সমান। "
             "গণনা এইভাবে অনেক সহজ হয়ে যায়।"},
            {"index": 4, "type": "formula-box",
             "tts":
             "এই প্রথম সূত্রটি সিডিএফ কী তা নিখুঁতভাবে সংজ্ঞায়িত করে। "
             "বর্তমান বিন্দু পর্যন্ত ঘনত্বের সমাকলনই হলো সঞ্চিত সম্ভাবনা। "
             "চিত্রে দেখা যাচ্ছে অনন্ত থেকে শুরু করে বর্তমান বিন্দু পর্যন্ত পুরো এলাকা একসাথে ধরা পড়েছে। "
             "এই একক অপেক্ষকই ভবিষ্যতের সকল হিসাবের ভিত্তি।"},
            {"index": 5, "type": "formula-box",
             "tts":
             "এই দ্বিতীয় সূত্রটি সিডিএফ আর পি ডি এফের মধ্যে সেই স্বর্ণ সংযোগ দেখায়। "
             "সঞ্চিত অপেক্ষকের অন্তরজ ঘনত্ব ফেরত দেয়, আর দুই প্রান্তের বিয়োগ দেয় ব্যবধানের সম্ভাবনা। "
             "চিত্রে দেখা যাচ্ছে একই চিত্রের ওপর এই দুটি দৃষ্টিভঙ্গি পাশাপাশি দাঁড়িয়ে আছে। "
             "ক্যালকুলাসের মৌলিক উপপাদ্যের এই প্রয়োগই পুরো পর্বের হৃদয়।"},
        ],
    },

    "sec-clt-emergence": {
        "title": "সেন্ট্রাল লিমিট থিওরেম: গ্যালটন বোর্ড ও বেল কার্ভ",
        "audio_file": "sec-clt-emergence.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "ষষ্ঠ ও শেষ পরিচ্ছেদ, সেন্ট্রাল লিমিট থিওরেম, গ্যালটন বোর্ড ও বেল কার্ভ। "
             "চিত্রে দেখা যাচ্ছে অসংখ্য মার্বেল পিনের ধাক্কা খেয়ে নিচে নামতে নামতে এক নিখুঁত ঘণ্টা আকৃতি তৈরি করছে। "
             "এই দৃশ্যটিই গোটা সিরিজের সবচেয়ে সুন্দর উপসংহার। "
             "আজ আমরা দেখব বিশৃঙ্খলা কীভাবে নিখুঁত শৃঙ্খলায় রূপ নেয়।"},
            {"index": 1, "type": "p",
             "tts":
             "লকডাউনে ঘরে বসে যখন আমরা মার্বেল ফেলি, তখন প্রতিটি মার্বেল একে একে পিনে ধাক্কা খায়। "
             "চিত্রে দেখা যাচ্ছে বাঁয়ে বা ডানে যাওয়ার ছোট ছোট দৈব পছন্দগুলো জমা হয়ে মাঝখানে সবচেয়ে বেশি মার্বেল জড়ো করেছে। "
             "ফলাফল হলো দুই প্রান্তে কম আর মাঝখানে উঁচু একটি বক্ররেখা। "
             "এই আকৃতিকেই আমরা বেল কার্ভ বলি।"},
            {"index": 2, "type": "p",
             "tts":
             "আদি চলকগুলোর নিজস্ব আকৃতি যাই হোক না কেন, এই নিয়ম সবার ওপর সমভাবে কার্যকর। "
             "চিত্রে দেখা যাচ্ছে কোনোটি সমতল, কোনোটি বিচিত্র আকারের হলেও তাদের সমষ্টি একই রূপ ধারণ করছে। "
             "বহু স্বাধীন প্রভাবকের যোগফল বা গড় সর্বদা এই নরমাল আকৃতির দিকে ধাবিত হয়। "
             "এটি প্রকৃতির এক সার্বজনীন নিয়ম।"},
            {"index": 3, "type": "p", "role": "conclusion",
             "tts":
             "প্রকৃতির অসংখ্য পরিমাপ ও ভৌত অস্থিরতার পেছনে রয়েছে এই গাউসিয়ান ঐকতান। "
             "মানুষের উচ্চতা হোক কিংবা পরিমাপের ত্রুটি, সবকিছুতেই একই ঘণ্টা আকৃতি ফিরে ফিরে দেখা যায়। "
             "চিত্রে দেখা যাচ্ছে কীভাবে হাজার হাজার ক্ষুদ্র স্বাধীন প্রভাবক মিলে এক সুসংহত বক্ররেখা গড়ে তুলেছে। "
             "সেন্ট্রাল লিমিট থিওরেম কোনো বাড়তি বোঝা নয়, বরং বিচ্ছিন্নতা থেকে অবিচ্ছিন্নতার এই পুরো যাত্রার এক সুন্দর উপসংহার।"},
            {"index": 4, "type": "formula-box",
             "tts":
             "এই সূত্রটি নরমাল বণ্টনের ঘনত্ব বা গাউসিয়ান বেল কার্ভের সার্বজনীন সমীকরণ। "
             "মাঝের গড় মান বিন্দুতে বক্ররেখা সবচেয়ে উঁচু, আর দূরে যেতে যেতে সমানভাবে নামতে থাকে। "
             "চিত্রে দেখা যাচ্ছে গড়ের দুই পাশে বক্ররেখা একেবারে প্রতিসম। "
             "পরিমিত ব্যবধান যত ছোট হয়, ঘণ্টাটি তত সরু ও উঁচু হয়ে ওঠে।"},
            {"index": 5, "type": "formula-box",
             "tts":
             "এই শেষ সূত্রটি সেন্ট্রাল লিমিট থিওরেমের সীমাস্থ রূপ। "
             "নমুনার আকার যত বাড়তে থাকে, গড়ের বণ্টন তত নিখুঁত আদর্শ নরমাল রূপ নেয়। "
             "চিত্রে দেখা যাচ্ছে প্রথমে কিছুটা অনিয়মিত দেখালেও শেষ পর্যন্ত সবকিছু সেই একই ঘণ্টা আকৃতিতে মিশে যাচ্ছে। "
             "এই সার্বজনীনতাই আমাদের অবিচ্ছিন্ন সম্ভাবনার পুরো পাঠকে এক সুন্দর উপসংহার দেয়।"},
        ],
    },
}

# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
# Latin letters, TeX/markup, long dashes and ASCII hyphens are forbidden.
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"
NATURAL_FIGURE = "চিত্রে দেখা যাচ্ছে"

# h2 meaning woven in: a shared key phrase from each section's displayed title.
KEY_PHRASES = {
    "sec-discrete-to-continuous": "বিচ্ছিন্ন স্তম্ভ থেকে অবিচ্ছিন্ন তরঙ্গে",
    "sec-zero-prob-paradox":      "একক বিন্দুর শূন্য সম্ভাব্যতা প্যারাডক্স",
    "sec-density-concept":        "সম্ভাব্যতা ঘনত্ব",
    "sec-uniform-exponential":    "বাস্তব মডেল",
    "sec-cdf-calculus":           "ক্রমযোজিত সম্ভাবনা",
    "sec-clt-emergence":          "সেন্ট্রাল লিমিট থিওরেম",
}

# Phonetic safeguards that must survive in the spoken text.
REQUIRED_PHRASES = {
    "sec-discrete-to-continuous": ["পি ডি এফ", "সমাকলন"],
    "sec-zero-prob-paradox":      ["শূন্য", "বিন্দু"],
    "sec-density-concept":        ["ডেনসিটি", "পি ডি এফ", "ক্ষেত্রফল"],
    "sec-uniform-exponential":    ["ইউনিফর্ম", "এক্সপোনেনশিয়াল", "স্মৃতিহীনতা"],
    "sec-cdf-calculus":           ["সিডিএফ", "পি ডি এফ", "ক্যালকুলাস"],
    "sec-clt-emergence":          ["সেন্ট্রাল লিমিট থিওরেম", "গ্যালটন", "বেল কার্ভ"],
}
GLOBAL_REQUIRED = ["ডেনসিটি", "পি ডি এফ", "সিডিএফ", "ইউনিফর্ম", "এক্সপোনেনশিয়াল"]


def narration_text_blobs():
    blobs = []
    for sec_id, sec in SECTIONS_DATA.items():
        blobs.append(sec["title"])
        for cue in sec["cues"]:
            blobs.append(cue["tts"])
    return blobs


def assert_clean_scripts():
    """Fail before any TTS work if a script has markup/Latin/the banned label."""
    expected_prosody = {
        "h2":            ("-5%", "+2Hz", "+0%"),
        "h3":            ("-3%", "+0Hz", "+0%"),
        "chapter-quote": ("-3%", "+0Hz", "+0%"),
        "p":             ("+2%", "+0Hz", "+0%"),
        "figure":        ("-4%", "+0Hz", "+0%"),
        "callout":       ("+0%", "+0Hz", "+0%"),
        "callout-blue":  ("+0%", "+0Hz", "+0%"),
        "callout-gold":  ("+0%", "+0Hz", "+0%"),
        "callout-green": ("+0%", "+0Hz", "+0%"),
        "code-showcase": ("-4%", "+0Hz", "+0%"),
        "formula-box":   ("-8%", "+0Hz", "+0%"),
    }
    assert PROSODY_DEFAULT == expected_prosody, "prosody spec drift"
    assert CONCLUSION_PROSODY == ("-3%", "+0Hz", "+0%"), "conclusion prosody drift"

    for sec_id, sec in SECTIONS_DATA.items():
        sec_text = " ".join(c["tts"] for c in sec["cues"])
        if NATURAL_FIGURE not in sec_text:
            raise ValueError(f"{sec_id}: no natural figure phrasing")
        for cue in sec["cues"]:
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars {bad!r}")
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: artificial figure label present")
            sentences = [s for s in re.split(r"[।?]", cue["tts"]) if s.strip()]
            if not (2 <= len(sentences) <= 4):
                raise ValueError(f"{sec_id} cue {cue['index']}: {len(sentences)} sentences (need 2-4)")

    if len(SECTIONS_DATA) != 6:
        raise ValueError("Expected exactly 6 narrated sections")
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
            raise ValueError(f"{sec_id}: key h2 phrase missing")
        sec_text = " ".join(c["tts"] for c in sec["cues"])
        for phrase in REQUIRED_PHRASES.get(sec_id, []):
            if phrase not in sec_text:
                raise ValueError(f"{sec_id}: phonetic safeguard missing -> {phrase}")
        total += len(indices)

    all_text = "\n".join(narration_text_blobs())
    for phrase in GLOBAL_REQUIRED:
        if phrase not in all_text:
            raise ValueError(f"global phonetic safeguard missing -> {phrase}")
    if FORBIDDEN_PREFIX in all_text:
        raise ValueError("artificial figure label present in scripts")
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
            print(f"  cue {idx:02d} [{cue['type']:<11}] {rate:>4} {pitch:>5} "
                  f"{role:<10} {cue['tts'][:30]}...")
            await synth_cue(cue["tts"], chunk, rate, pitch, volume)
        else:
            print(f"  cue {idx:02d} [{cue['type']:<11}] cached")
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
          f"(0 artificial figure labels, 0 Latin/TeX chars).")

    built = {}
    for sec_id, sec in SECTIONS_DATA.items():
        built[sec_id] = await build_section(sec_id, sec)

    # Manifest keys are exactly the 6 canonical DOM section ids (in DOM order).
    manifest_sections = {sec_id: built[sec_id] for sec_id in SECTIONS_DATA}
    manifest_data = {
        "course": "lockdown_math",
        "lesson": "lesson_06",
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

    # Final integrity checks.
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
    print("BUILD COMPLETE - expressive teacher audio, Lockdown Math Lesson 06")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<30} {len(msec['cues']):>2} cues "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 6 sections, {total_ms / 1000.0:.2f}s.")
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
        audio_urls = ["../../assets/audio/lockdown_math/lesson_06/" +
                      local_manifest["sections"][sid]["audio_file"]
                      for sid in SECTIONS_DATA]
        audio_results = page.evaluate(AUDIO_JS, audio_urls)
        browser.close()

    # Benign, pre-existing, non-narration noise from the offline file:// page:
    # hero/watch-panel mp4 + YouTube embeds are unavailable offline.
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

    # All no-narration sections really carry the attribute.
    nn = [e["id"] for e in data["sectionEls"] if e["noNarration"] == "true"]
    for req in ("sec-discrete-to-continuous-study", "sec-zero-prob-paradox-study",
                "sec-density-concept-study", "sec-uniform-exponential-study",
                "sec-cdf-calculus-study", "sec-clt-emergence-study",
                "sec-interactive-lab", "sec-quizzes", "sec-formulas-glossary"):
        assert req in nn, f"{req} missing no-narration: {nn}"

    tsections = data["manifest"]["sections"]
    total_cues = 0
    total_ms = 0.0
    dup_check = set()
    disallowed = set()
    forbidden_hits = []
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

        sec_text = " ".join(c["text"] for c in cues)
        for phrase in REQUIRED_PHRASES.get(sec_id, []):
            assert phrase in sec_text, (sec_id, "safeguard missing", phrase)

        for cue in cues:
            total_cues += 1
            key = (sec_id, cue["index"], cue["type"], cue["text"])
            assert key not in dup_check, f"Duplicate cue: {key[:3]}"
            dup_check.add(key)
            if cue["type"] not in ALLOWED_CUE_TYPES:
                disallowed.add(cue["type"])
            if FORBIDDEN_PREFIX in cue["text"]:
                forbidden_hits.append(f"{sec_id}/{cue['index']}")
            if NATURAL_FIGURE in cue["text"]:
                natural_figure_hits += 1
            sentences = [x for x in re.split(r"[।?]", cue["text"]) if x.strip()]
            assert 2 <= len(sentences) <= 4, (sec_id, cue["index"], "sentences", len(sentences))
            bad = BAD_CHARS.findall(cue["text"])
            assert not bad, (sec_id, cue["index"], "latin/tex chars", bad)

        assert KEY_PHRASES[sec_id] in cues[0]["text"], (sec_id, "key h2 phrase missing")
        for cue in SECTIONS_DATA[sec_id]["cues"]:
            prosody_variants.add(prosody_for(cue))

        # Timing integrity: exact 350 ms gaps, no overlaps, duration agrees.
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
    assert natural_figure_hits >= 6, natural_figure_hits
    # Required prosody rules exercised; figure/formula/callout defined in spec.
    assert ("-5%", "+2Hz", "+0%") in prosody_variants, prosody_variants
    assert ("+2%", "+0Hz", "+0%") in prosody_variants, prosody_variants
    assert ("-8%", "+0Hz", "+0%") in prosody_variants, prosody_variants
    assert CONCLUSION_PROSODY in prosody_variants, prosody_variants
    assert PROSODY_DEFAULT["figure"] == ("-4%", "+0Hz", "+0%")
    assert PROSODY_DEFAULT["callout"] == ("+0%", "+0Hz", "+0%")
    # Global phonetic safeguards.
    all_text = json.dumps(local_manifest, ensure_ascii=False)
    for phrase in GLOBAL_REQUIRED:
        assert phrase in all_text, ("global phonetic safeguard missing", phrase)

    # No quiz / media-tab anywhere in the narrated DOM cue types.
    all_dom_types = [t for s in data["dom"] for t in s["types"]]
    assert not ({"quiz", "media-tab", "b1b-quiz", "b1b-media-tab"} & set(all_dom_types)), all_dom_types

    # manifest.js payload must equal manifest.json; sidecars valid and in sync.
    with open(os.path.join(AUDIO_DIR, "manifest.js"), encoding="utf-8") as fh:
        js_text = fh.read().strip()
    assert js_text.startswith("window.TEACHER_AUDIO_MANIFEST = ") and js_text.endswith(";")
    js_obj = json.loads(js_text[len("window.TEACHER_AUDIO_MANIFEST = "):-1].strip())
    assert js_obj == local_manifest, "manifest.js != manifest.json"
    for sec_id in SECTIONS_DATA:
        side = os.path.join(AUDIO_DIR,
                            os.path.splitext(EXPECTED_AUDIO_FILES[sec_id])[0] + "_cues.json")
        with open(side, encoding="utf-8") as fh:
            side_obj = json.load(fh)
        assert side_obj == local_manifest["sections"][sec_id]["cues"], (sec_id, "sidecar out of sync")

    # On-disk forbidden phrase scan (manifest + sidecars).
    disk_blobs = [json.dumps(local_manifest, ensure_ascii=False)]
    for sec_id in SECTIONS_DATA:
        side = os.path.join(AUDIO_DIR,
                            os.path.splitext(EXPECTED_AUDIO_FILES[sec_id])[0] + "_cues.json")
        with open(side, encoding="utf-8") as fh:
            disk_blobs.append(fh.read())
    assert not any(FORBIDDEN_PREFIX in b for b in disk_blobs), "forbidden label on disk"
    # DOM text forbidden phrase scan.
    for s in data["dom"]:
        for t in s["texts"]:
            assert FORBIDDEN_PREFIX not in t, f"forbidden label in DOM text of {s['id']}"

    # Page cache-buster bumped (original ?v=1 -> rebuilt ?v=2).
    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    versions = [int(v) for _, v in re.findall(r"(manifest\.js\?v=)(\d+)", html)]
    assert versions and min(versions) >= 2, f"manifest ?v not bumped: {versions}"

    # Browser MP3 loadability.
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
        "natural_figure_phrasing_cues": natural_figure_hits,
        "h2_key_phrase_woven": True,
        "phonetic_safeguards_ok": True,
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
          f"{report['natural_figure_phrasing_cues']} natural figure phrasings.")
    print(f"Report written to {VERIFY_RESULT}")


if __name__ == "__main__":
    main()
