# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Lockdown Math Lesson 04
("Complex Number Fundamentals & Geometric Multiplication", Bengali) to the
gold standard — warm, natural, fully phonetic figure phrasing, NO artificial
figure label ("চিত্র প্রদর্শনী" is NEVER used).

Deterministic, re-runnable, self-contained:
  * 37 cues in 6 narrated sections with EXACTLY the same section IDs, audio_file
    names, cue type and cue order as the live narration-engine DOM.
    Authoritative DOM extraction (governance/_extract_lock04_dom.py, via the
    narration_engine.js selector `.article > section, article section` with
    `data-no-narration` filtering and the canonical readable-node selector)
    confirmed:
        sec-number-extension        -> [h2, p, p, p, formula-box, formula-box]       (6)
        sec-rotation-meaning        -> [h2, p, p, p, formula-box, formula-box]       (6)
        sec-argand-plane            -> [h2, p, p, p, formula-box, formula-box]       (6)
        sec-polar-form              -> [h2, p, p, p, formula-box, formula-box,
                                         formula-box]                              (7)
        sec-complex-multiplication  -> [h2, p, p, p, formula-box, formula-box]       (6)
        sec-trig-connection         -> [h2, p, p, p, formula-box, formula-box]       (6)
    Total = 37 cues. All six *-study companions plus sec-interactive-lab,
    sec-quizzes and sec-formulas-glossary carry data-no-narration="true" and
    are deliberately excluded. There are NO quiz / media-tab cue types.
  * Every cue is an expressive, natural 2-4 sentence Bengali teacher
    explanation of that figure/formula, with the topic woven in naturally.
    Teacher phrasing uses "চিত্রে দেখা যাচ্ছে" or direct explanation — the
    artificial "চিত্র প্রদর্শনী" label is forbidden.
  * Fully phonetic spoken Bengali (no TeX / Latin / markup). Safeguards:
        complex -> কমপ্লেক্স, Argand -> আরগ্যান্ড, polar -> পোলার,
        Euler -> অয়লার, i -> আই (never "ই"), rotation -> ঘূর্ণন.
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
  python governance/build_expressive_teacher_audio_lock04.py
  python governance/build_expressive_teacher_audio_lock04.py --verify-only
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
                         "lockdown_math", "lesson_04")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "lockdown_math", "lesson_04.html")
VERIFY_RESULT = os.path.join(SCRIPT_DIR, "_verify_lock04_result.json")

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
    "sec-number-extension":       ["h2", "p", "p", "p", "formula-box", "formula-box"],
    "sec-rotation-meaning":       ["h2", "p", "p", "p", "formula-box", "formula-box"],
    "sec-argand-plane":           ["h2", "p", "p", "p", "formula-box", "formula-box"],
    "sec-polar-form":             ["h2", "p", "p", "p", "formula-box", "formula-box", "formula-box"],
    "sec-complex-multiplication": ["h2", "p", "p", "p", "formula-box", "formula-box"],
    "sec-trig-connection":        ["h2", "p", "p", "p", "formula-box", "formula-box"],
}
# Audio-file names are the EXISTING manifest keys (canonical section ids).
EXPECTED_AUDIO_FILES = {sid: sid + ".mp3" for sid in EXPECTED_TYPES}
EXPECTED_COUNT = {sid: len(types) for sid, types in EXPECTED_TYPES.items()}
EXPECTED_TOTAL = 37

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (37 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-number-extension": {
        "title": "সংখ্যা ধারণার বিস্তৃতি: ঋণাত্মক সংখ্যা থেকে দ্বিমাত্রিক জগতে",
        "audio_file": "sec-number-extension.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "আমাদের প্রথম পরিচ্ছেদ, সংখ্যা ধারণার বিস্তৃতি, ঋণাত্মক সংখ্যা থেকে দ্বিমাত্রিক জগতে। "
             "চিত্রে দেখা যাচ্ছে একমাত্রিক সংখ্যারেখা ধীরে ধীরে প্রসারিত হয়ে একটি সম্পূর্ণ সমতলের জন্ম দিচ্ছে। "
             "সংখ্যা কেবল পরিমাপের একক নয়, প্রতিটি সংখ্যা এক একটি জ্যামিতিক রূপান্তর। "
             "এই যাত্রায় আমরা দেখব কীভাবে ঋণাত্মক সংখ্যা এবং কাল্পনিক একক আমাদের দৃষ্টিকে এক মাত্রা থেকে দুই মাত্রায় নিয়ে যায়।"},
            {"index": 1, "type": "p",
             "tts":
             "সংখ্যাকে আমরা সাধারণত পরিমাপের একক হিসেবে ভাবি, কিন্তু এখানে দেখা যাচ্ছে সংখ্যার আরেকটি রূপ। "
             "চিত্রে দেখা যাচ্ছে ধনাত্মক দিকে থাকা এক বিন্দু ঋণাত্মক দিকে সরে যাচ্ছে, ঠিক যেন কোনো দিক পরিবর্তন ঘটেছে। "
             "অর্থাৎ গুণের ক্রিয়া কেবল মান বদলায় না, সেটি সমতলে একটি নির্দিষ্ট রূপান্তরও সম্পাদন করে। "
             "দেকার্তের সংখ্যারেখা এই ধারণাটিকেই সুন্দরভাবে ধরে রেখেছে।"},
            {"index": 2, "type": "p",
             "tts":
             "সংখ্যারেখায় ধনাত্মক ১ কে ঋণাত্মক ১ দিয়ে গুণ করার অর্থ কী? "
             "চিত্রে দেখা যাচ্ছে বিন্দুটি মূলবিন্দুকে কেন্দ্র করে ঠিক ১৮০ ডিগ্রি ঘুরে বিপরীত দিকে পৌঁছে যাচ্ছে। "
             "আবার ঋণাত্মক ১ দিয়ে একই কাজ করলে সেটি ৩৬০ ডিগ্রি ঘুরে আবার ১ এ ফিরে আসে। "
             "এই বিপরীতকরণ বা প্রতিফলনই হলো ঋণাত্মক সংখ্যার জ্যামিতিক অর্থ।"},
            {"index": 3, "type": "p",
             "tts":
             "রেনেসাঁ যুগের গণিতবিদরা ঋণাত্মক সংখ্যার বর্গমূল নিয়ে ভাবতে গিয়ে এক নতুন ধাঁধার মুখোমুখি হয়েছিলেন। "
             "উত্তরটি ছিল একমাত্রিক রেখার বাইরে পা দেওয়া, অর্থাৎ কমপ্লেক্স সংখ্যার জগৎ। "
             "চিত্রে দেখা যাচ্ছে সেই রেখা এখন একটি দ্বিমাত্রিক সমতলে রূপ নিচ্ছে, যার প্রতিটি বিন্দু একটিমাত্র সংখ্যা। "
             "কাল্পনিক বলে উপহাসিত এই সংখ্যাগুলো আসলে জ্যামিতির এক অপূর্ব উপহার।"},
            {"index": 4, "type": "formula-box",
             "tts":
             "এই সূত্রের প্রথম অংশ বলছে, ১ কে ঋণাত্মক ১ দিয়ে গুণ করলে ফলাফল ঋণাত্মক ১, অর্থাৎ ১৮০ ডিগ্রির এক ধাপ ঘূর্ণন। "
             "দ্বিতীয় অংশে ঋণাত্মক ১ কে আবার ঋণাত্মক ১ দিয়ে গুণ করলে ৩৬০ ডিগ্রি ঘুরে ফলাফল দাঁড়ায় ধনাত্মক ১। "
             "চিত্রে দেখা যাচ্ছে দুটি ধাপের এই চক্র ঠিক এক পূর্ণ বৃত্ত বানায়। "
             "মনে রাখতে হবে, এখানে গুণ মানেই ঘুরে যাওয়া।"},
            {"index": 5, "type": "formula-box",
             "tts":
             "এখানে আই হলো সেই কাল্পনিক একক যার বর্গ ঋণাত্মক ১, আর তাই একে ঋণাত্মক ১ এর বর্গমূল হিসেবেও লেখা যায়। "
             "চিত্রে দেখা যাচ্ছে আই প্রয়োগ করলে ৯০ ডিগ্রি করে ঘুরে একটি নতুন মাত্রায় পৌঁছানো যায়। "
             "দুইবার প্রয়োগ করলেই মিলে যায় সেই ১৮০ ডিগ্রি, যা আমরা ঋণাত্মক ১ এ দেখেছি। "
             "এই ছোট্ট সমীকরণটিই পুরো কমপ্লেক্স সংখ্যা তত্ত্বের ভিত্তি।"},
        ],
    },

    "sec-rotation-meaning": {
        "title": "i-এর আসল অর্থ: সমতলে ৯০ ডিগ্রি ঘূর্ণন",
        "audio_file": "sec-rotation-meaning.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "দ্বিতীয় পরিচ্ছেদে আমরা দেখব আই এর আসল অর্থ, সমতলে ৯০ ডিগ্রি ঘূর্ণন। "
             "চিত্রে দেখা যাচ্ছে বাস্তব অক্ষ থেকে একটি ভেক্টর উল্লম্ব অক্ষের দিকে কাত হয়ে যাচ্ছে। "
             "আই কোনো সাধারণ সংখ্যা নয়, সেটি একটি ক্রিয়াশীল ঘূর্ণনের নির্দেশক। "
             "এই পরিচ্ছেদে আমরা সেই ঘূর্ণনের চক্র ও এর সমতলিক অর্থ নিখুঁতভাবে বুঝে নেব।"},
            {"index": 1, "type": "p",
             "tts":
             "বীজগণিতে আই কে এমন সংখ্যা হিসেবে চেনা যায় যার বর্গ ঋণাত্মক ১, কিন্তু জ্যামিতিতে এর মান অনেক বেশি গভীর। "
             "চিত্রে দেখা যাচ্ছে কোনো ভেক্টরকে আই দিয়ে গুণ করার সাথে সাথে সেটি মূলবিন্দুকে কেন্দ্র করে ঘড়ির কাঁটার বিপরীতে ৯০ ডিগ্রি ঘুরে যাচ্ছে। "
             "এর দৈর্ঘ্য কিন্তু একই থাকে, শুধু দিক বদলায়। "
             "তাই আই কে আমরা একটি বিশুদ্ধ ঘূর্ণন অপারেটর বলে ভাবতে পারি।"},
            {"index": 2, "type": "p",
             "tts":
             "একবার আই প্রয়োগ করলে ৯০ ডিগ্রি, দুইবার করলে ১৮০ ডিগ্রি। "
             "তিনবারে ২৭০ ডিগ্রি আর চারবারে পূর্ণ ৩৬০ ডিগ্রি ঘুরে আমরা আবার মূল অবস্থানে ফিরে আসি। "
             "চিত্রে দেখা যাচ্ছে এই চারটি ধাপ ঠিক একটি বৃত্তের চারটি কোণাকে চিহ্নিত করছে। "
             "এই চক্রাকার প্রতিসাম্যই আই এর শক্তির মূল কথা।"},
            {"index": 3, "type": "p",
             "tts":
             "আই এর ঘাত বের করার কৌশল মূলত চার দিয়ে ভাগের ভাগশেষের ওপর নির্ভরশীল। "
             "যেকোনো বড় ঘাতকে চার দিয়ে ভাগ করে ভাগশেষ দেখে সেটির অবস্থান নির্ধারণ করা যায়। "
             "চিত্রে দেখা যাচ্ছে ভাগশেষ শূন্য, এক, দুই বা তিনের সাথে মিল রেখে বিন্দুটি আবার সেই চার কোণায় ফিরে যাচ্ছে। "
             "বীজগণিত আর জ্যামিতি এখানে একই কথা বলছে আলাদা ভাষায়।"},
            {"index": 4, "type": "formula-box",
             "tts":
             "এই সারিটি ঘূর্ণনের চার ধাপকে এক নজরে দেখায়। "
             "প্রথম ধাপে আই, দ্বিতীয়তে ঋণাত্মক ১, তৃতীয়তে ঋণাত্মক আই আর চতুর্থতে আবার ধনাত্মক ১। "
             "চিত্রে দেখা যাচ্ছে প্রতিটি ধাপে মাত্র ৯০ ডিগ্রি করে ঘুরে পুরো চক্র সম্পন্ন হয়। "
             "এই ক্রম মুখস্থ না করলেও চলে, কারণ চিত্রটি নিজেই ক্রমটি বলে দিচ্ছে।"},
            {"index": 5, "type": "formula-box",
             "tts":
             "এই সাধারণ সূত্রটি বলে, আই এর যেকোনো ঘাতকে চার দিয়ে ভাগ করে ভাগশেষ র দ্বারা তার মান নির্ধারণ করা যায়। "
             "র এর মান শূন্য, এক, দুই বা তিন হতে পারে, আর প্রতিটির সাথে একটি নির্দিষ্ট কোণা মিলে যায়। "
             "চিত্রে দেখা যাচ্ছে কত বড় ঘাত হোক না কেন, শেষ পর্যন্ত বিন্দুটি ওই চার কোণার মধ্যেই কোথাও দাঁড়ায়। "
             "এটি ঘূর্ণনের পুনরাবৃত্তিকে বীজগণিতের ভাষায় প্রকাশ করে।"},
        ],
    },

    "sec-argand-plane": {
        "title": "আর্গাঁ চিত্র ও কার্তেসীয় স্থানাঙ্ক রূপ (a + bi)",
        "audio_file": "sec-argand-plane.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "তৃতীয় পরিচ্ছেদে আমরা দেখব আরগ্যান্ড চিত্র ও কার্তেসীয় স্থানাঙ্ক রূপ। "
             "চিত্রে দেখা যাচ্ছে একটি সমতল, যার অনুভূমিক অক্ষ বাস্তব আর উল্লম্ব অক্ষ কাল্পনিক অংশকে নির্দেশ করে। "
             "জিন রবার্ট আরগ্যান্ড আর গাউসের এই অঙ্কন জটিল সংখ্যাকে একটি নির্দিষ্ট ঠিকানা দেয়। "
             "এখান থেকে বীজগণিত ও জ্যামিতি একই ভাষায় কথা বলতে শুরু করে।"},
            {"index": 1, "type": "p",
             "tts":
             "জটিল সমতলে অনুভূমিক অক্ষকে বলা হয় বাস্তব অক্ষ আর উল্লম্ব অক্ষকে কাল্পনিক অক্ষ। "
             "চিত্রে দেখা যাচ্ছে বাস্তব অংশ ডানে বা বাঁয়ে দূরত্ব নির্ধারণ করছে, আর কাল্পনিক অংশ ওপর বা নিচে অবস্থান ঠিক করছে। "
             "এই দুটি অক্ষের ছেদবিন্দু হলো মূলবিন্দু, যার মান শূন্য। "
             "সাধারণ কার্তেসীয় স্থানাঙ্কের মতোই এখানেও প্রতিটি বিন্দুর একটি নির্দিষ্ট ঠিকানা থাকে।"},
            {"index": 2, "type": "p",
             "tts":
             "দুটি জটিল সংখ্যার যোগফল জ্যামিতিকভাবে ঠিক ভেক্টর যোগের মতোই কাজ করে। "
             "চিত্রে দেখা যাচ্ছে প্রথম ভেক্টরের অগ্রভাগ থেকে দ্বিতীয় ভেক্টরটি টেনে আঁকা হয়েছে, আর শেষ বিন্দুটিই যোগফল। "
             "বাস্তব অংশ বাস্তব অংশের সাথে আর কাল্পনিক অংশ কাল্পনিক অংশের সাথে স্বাধীনভাবে যুক্ত হয়। "
             "এই সরল নিয়মটি হিসাবকে অনেক সহজ করে দেয়।"},
            {"index": 3, "type": "p",
             "tts":
             "আরগ্যান্ড চিত্রের সবচেয়ে আশ্চর্য দিক হলো, প্রতিটি জটিল সংখ্যা একই সাথে একটি বিন্দু ও একটি ভেক্টর। "
             "চিত্রে দেখা যাচ্ছে মূলবিন্দু থেকে বিন্দুটিতে টানা একটি রেখা, যার দৈর্ঘ্য ও দিক সংখ্যাটির সম্পূর্ণ পরিচয় বহন করছে। "
             "সাধারণ স্থানাঙ্কে দুটি সংখ্যার জোড়া থাকলেও এখানে পুরো বিন্দুটিই একটিমাত্র সংখ্যা। "
             "বীজগণিত আর জ্যামিতির এই মিলনই কমপ্লেক্স সংখ্যার সৌন্দর্য।"},
            {"index": 4, "type": "formula-box",
             "tts":
             "এই রূপে জটিল সংখ্যা জেড কে দুটি অংশে ভাগ করা হয়েছে। "
             "বাস্তব অংশ এ আর কাল্পনিক অংশ বি ঘাত আই, আর দুজনই বাস্তব সংখ্যা। "
             "চিত্রে দেখা যাচ্ছে এ বলছে কতটা ডানে বা বাঁয়ে যেতে হবে, আর বি বলছে কতটা ওপর বা নিচে। "
             "এই সহজ রূপটিই যোগের জন্য সবচেয়ে সুবিধাজনক, আর এখানে কাল্পনিক এককটি হলো আই, যা সমতলে ৯০ ডিগ্রি ঘূর্ণনের কথা মনে করিয়ে দেয়।"},
            {"index": 5, "type": "formula-box",
             "tts":
             "এই সূত্রটি যোগের নিয়মকে স্পষ্ট করে তোলে। "
             "প্রথম জটিল সংখ্যার বাস্তব অংশের সাথে দ্বিতীয়টির বাস্তব অংশ যোগ হচ্ছে, আর একইভাবে কাল্পনিক অংশ দুটিও যোগ হচ্ছে। "
             "চিত্রে দেখা যাচ্ছে দুটি ভেক্টরের সমান্তরালভাগ অনুসরণ করে শেষ বিন্দুটি ঠিক ওই যোগফলে পৌঁছে যাচ্ছে। "
             "ফলাফলটি আবার একটিমাত্র জটিল সংখ্যা, ঠিক যেমনটি আমরা আশা করেছিলাম।"},
        ],
    },

    "sec-polar-form": {
        "title": "পোলার রূপ: দূরত্ব ও কোণের ভাষা (r, θ)",
        "audio_file": "sec-polar-form.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "চতুর্থ পরিচ্ছেদে আমরা দেখব পোলার রূপ, দূরত্ব ও কোণের ভাষা। "
             "এখনো পর্যন্ত আমরা বিন্দুকে বাস্তব ও কাল্পনিক অংশ দিয়ে চিহ্নিত করেছি, কিন্তু গুণের ক্ষেত্রে এই রূপ সবচেয়ে স্বাভাবিক নয়। "
             "চিত্রে দেখা যাচ্ছে একই বিন্দুকে এখন মূলবিন্দু থেকে তার দূরত্ব আর একটি কোণ দিয়ে প্রকাশ করা হচ্ছে। "
             "এই দুটি সংখ্যা জটিল সংখ্যার গুণের আসল চিত্র উন্মোচন করবে।"},
            {"index": 1, "type": "p",
             "tts":
             "পোলার স্থানাঙ্কে কোনো জটিল সংখ্যাকে দুটি কথা দিয়ে বোঝা হয়। "
             "প্রথমটি হলো মূলবিন্দু থেকে বিন্দুর সরাসরি দূরত্ব, যার নাম আর, দ্বিতীয়টি হলো বাস্তব অক্ষের সাথে তার তৈরি কোণ, যার নাম থিটা। "
             "চিত্রে দেখা যাচ্ছে ভেক্টরটি ঘুরে সেই কোণটিকে চিহ্নিত করছে, আর তার দৈর্ঘ্য দূরত্বটি নির্ধারণ করছে। "
             "বাস্তব ও উল্লম্ব দূরত্বের বদলে এই দুটি তথ্যই যথেষ্ট।"},
            {"index": 2, "type": "p",
             "tts":
             "মডুলাস হলো সমতলে ভেক্টরের দৈর্ঘ্য বা পরমমান, আর আর্গুমেন্ট হলো তার ঘূর্ণন কোণ। "
             "চিত্রে দেখা যাচ্ছে ভেক্টরের দৈর্ঘ্য যত বাড়ছে, মডুলাসের মানও তত বাড়ছে, আর কোণের পরিবর্তনের সাথে সাথে আর্গুমেন্টও বদলাচ্ছে। "
             "স্কেলিং আর ঘূর্ণন, এই দুটোই যেন জটিল সংখ্যার গুণের ভাষা। "
             "তাই পোলার রূপ আমাদের সেই ভাষাটি সরাসরি পড়তে শেখায়।"},
            {"index": 3, "type": "p",
             "tts":
             "যোগের জন্য কার্তেসীয় রূপ সুবিধাজনক হলেও গুণ ও ভাগের আসল সৌন্দর্য প্রকাশ পায় পোলার রূপে। "
             "চিত্রে দেখা যাচ্ছে দুটি ভেক্টরের দৈর্ঘ্য গুণ হচ্ছে আর কোণদুটি যোগ হচ্ছে, ঠিক যেন একটি সুন্দর নৃত্য। "
             "এই একক ধারণাটিই পরবর্তীতে গুণের মূল উপপাদ্য আর অয়লারের সূত্রের দিকে আমাদের নিয়ে যাবে। "
             "পোলার রূপ কেবল একটি লেখার ভঙ্গি নয়, সেটি এক নতুন দৃষ্টিভঙ্গি।"},
            {"index": 4, "type": "formula-box",
             "tts":
             "মডুলাস বা পরমমানের এই সূত্রটি পিথাগোরাসের উপপাদ্য থেকে সরাসরি আসে। "
             "বাস্তব অংশ এ এর বর্গ আর কাল্পনিক অংশ বি এর বর্গ যোগ করে তার বর্গমূল নিলেই মূলবিন্দু থেকে দূরত্ব পাওয়া যায়। "
             "চিত্রে দেখা যাচ্ছে ভেক্টরটি একটি ডানকোণী ত্রিভুজের কর্ণ, আর কর্ণের দৈর্ঘ্যই মডুলাস। "
             "মডুলাস আমাদের বলে দেয় জটিল সংখ্যাটি কতটা বড় বা ছোট।"},
            {"index": 5, "type": "formula-box",
             "tts":
             "আর্গুমেন্ট বা কোণের সূত্রটি ত্রিকোণমিতির বিপরীত স্পর্শাংক থেকে আসে। "
             "কাল্পনিক অংশ বি কে বাস্তব অংশ এ দিয়ে ভাগ করে সেই ভাগফলের বিপরীত স্পর্শাংক নিলেই কোণ থিটা পাওয়া যায়। "
             "চিত্রে দেখা যাচ্ছে ভেক্টরটি বাস্তব অক্ষের সাথে যে কোণ তৈরি করছে, সেটিই আর্গুমেন্ট। "
             "তবে কোণের সঠিক চতুর্ভাগ বেছে নিতে চিত্রের দিকে লক্ষ্য রাখতে হবে।"},
            {"index": 6, "type": "formula-box",
             "tts":
             "পোলার ত্রিকোণমিতিক রূপে জটিল সংখ্যা জেড কে লেখা হয় দূরত্ব আর কোণের মাধ্যমে। "
             "কোসাইন থিটা বাস্তব অক্ষে অবস্থান নির্ধারণ করে আর সাইন থিটা কাল্পনিক অক্ষে, আর সেই সাথে আই ঘূর্ণনের কথা মনে করিয়ে দেয়। "
             "চিত্রে দেখা যাচ্ছে ভেক্টরটি তার দৈর্ঘ্য ও কোণ বজায় রেখে সমতলে নিজের জায়গা করে নিচ্ছে। "
             "এই রূপটিই গুণনকে এত সুন্দর করে তোলে।"},
        ],
    },

    "sec-complex-multiplication": {
        "title": "জটিল সংখ্যার গুণন: স্কেলিং ও রোটেশনের দ্বৈত নৃত্য",
        "audio_file": "sec-complex-multiplication.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "পঞ্চম পরিচ্ছেদে আমরা দেখব জটিল সংখ্যার গুণন, স্কেলিং ও ঘূর্ণনের দ্বৈত নৃত্য। "
             "লকডাউন ম্যাথের এই অংশটি পুরো ধারার হৃদয়, যেখানে বীজগণিত আর জ্যামিতি এক জায়গায় মিলে যায়। "
             "চিত্রে দেখা যাচ্ছে একটি বিন্দু একই সাথে প্রসারিত ও ঘুরে যাচ্ছে। "
             "এই দুই ক্রিয়ার মিলনই জটিল গুণনের আসল পরিচয়।"},
            {"index": 1, "type": "p",
             "tts":
             "দুটি জটিল সংখ্যা গুণ করলে তাদের দৈর্ঘ্য বা মডুলাস সাধারণ সংখ্যার মতো গুণ হয়, আর কোণ বা আর্গুমেন্ট পরস্পরের সাথে যোগ হয়। "
             "চিত্রে দেখা যাচ্ছে প্রথম ভেক্টরের দৈর্ঘ্য দ্বিতীয়টির দৈর্ঘ্য দ্বারা বাড়ছে, আর কোণ দুটো একসাথে মিলে নতুন দিক নির্ধারণ করছে। "
             "মনে হতে পারে এটি জটিল হিসাব, কিন্তু চিত্রটি দেখলে সব কিছু সহজ হয়ে যায়। "
             "স্কেলিং আর ঘূর্ণন, এই দুটোই ঘটছে একসাথে।"},
            {"index": 2, "type": "p",
             "tts":
             "যখন কোনো জটিল সংখ্যার মডুলাস ১ হয়, অর্থাৎ সেটি একক বৃত্তের ওপর থাকে, তখন গুণ করা মানে কেবল ঘুরে যাওয়া। "
             "চিত্রে দেখা যাচ্ছে ভেক্টরের দৈর্ঘ্য একই রইল, শুধু দিকটি নির্দিষ্ট কোণে কাত হলো। "
             "আই দিয়ে গুণ করলে যেমন ৯০ ডিগ্রি ঘুরে, ঠিক তেমনি অন্য কোনো কোণের সংখ্যা দিয়ে গুণ করলে সেই কোণেই ঘুরে যায়। "
             "দৈর্ঘ্য অপরিবর্তিত রেখে শুধু দিক বদলানোই হলো খাঁটি ঘূর্ণন।"},
            {"index": 3, "type": "p",
             "tts":
             "দ্য মোয়াভ্রের উপপাদ্য এই ঘূর্ণন নীতিরই এক স্বাভাবিক অনুসিদ্ধান্ত। "
             "একই জটিল সংখ্যাকে বারবার গুণ করলে তার কোণ বারবার যোগ হয়, আর দৈর্ঘ্য বারবার গুণ হয়। "
             "চিত্রে দেখা যাচ্ছে প্রতিটি পুনরাবৃত্তিতে ভেক্টরটি একই কোণে আরেক ধাপ ঘুরে যাচ্ছে। "
             "এই সরল পর্যবেক্ষণ থেকেই শক্তিশালী ত্রিকোণমিতিক সূত্র জন্ম নেয়।"},
            {"index": 4, "type": "formula-box",
             "tts":
             "এই মূল উপপাদ্যটি জটিল গুণনের পুরো কথা এক লাইনে বলে দেয়। "
             "বাঁ পাশের প্রথম অংশ বলছে, গুণফলের মডুলাস দুটি মডুলাসের গুণফল, আর দ্বিতীয় অংশ বলছে গুণফলের আর্গুমেন্ট দুটি আর্গুমেন্টের যোগফল। "
             "চিত্রে দেখা যাচ্ছে দুটি ভেক্টরের দৈর্ঘ্য গুণ হয়ে নতুন দৈর্ঘ্য তৈরি করছে, আর কোণ দুটি যোগ হয়ে নতুন দিক বানাচ্ছে। "
             "জ্যামিতির এই সরলতাকেই বীজগণিত এত সুন্দরভাবে প্রকাশ করেছে।"},
            {"index": 5, "type": "formula-box",
             "tts":
             "একক বৃত্তে খাঁটি ঘূর্ণনের এই সূত্রটি আমাদের কোণকে বহুগুণ করতে শেখায়। "
             "ভেতরে কোণ থিটা আর বাইরে এন গুণ থিটা, মানে কতবার ঘুরবে সেটিই এন দিয়ে নির্ধারিত। "
             "চিত্রে দেখা যাচ্ছে একই ভেক্টর বারবার ঘুরে শেষ পর্যন্ত এন গুণ কোণে পৌঁছে যাচ্ছে, আর তার দৈর্ঘ্য একই রয়ে গেছে। "
             "দ্য মোয়াভ্রের উপপাদ্য নামে পরিচিত এই ফলাফল থেকে ত্রিকোণমিতির অনেক সূত্র সহজে বেরিয়ে আসে।"},
        ],
    },

    "sec-trig-connection": {
        "title": "ত্রিকোণমিতির সূত্রাবলি: মুখস্থহীন জ্যামিতিক আবিষ্কার",
        "audio_file": "sec-trig-connection.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "ষষ্ঠ ও শেষ পরিচ্ছেদে আমরা দেখব ত্রিকোণমিতির সূত্রাবলি, মুখস্থহীন জ্যামিতিক আবিষ্কার। "
             "স্কুলে কোণ যোগের সূত্রগুলো মুখস্থ করতে গিয়ে অনেকেই বিভ্রান্ত হয়েছিলেন, কিন্তু কমপ্লেক্স সংখ্যা জানলে সেই ভয় দূর হয়। "
             "চিত্রে দেখা যাচ্ছে একক বৃত্তের দুটি সংখ্যা গুণ হচ্ছে, আর সেই গুণফল থেকে সূত্রগুলো নিজেই বেরিয়ে আসছে। "
             "এই পরিচ্ছেদে আমরা দেখব জ্ঞান মুখস্থ করা নয়, আবিষ্কার করা যায়।"},
            {"index": 1, "type": "p",
             "tts":
             "ত্রিকোণমিতির সমস্ত যৌগিক কোণের সূত্র জটিল সংখ্যার স্বাভাবিক গুণফল থেকেই সরাসরি উদ্ভূত হয়। "
             "চিত্রে দেখা যাচ্ছে দুটি কোণের ভেক্টর গুণ হয়ে একটি নতুন ভেক্টর তৈরি করছে, যার কোণ আগের দুটির যোগফল। "
             "একদিকে বীজগণিতিক গুণ, অন্যদিকে জ্যামিতিক কোণ যোগ, দুটি পদ্ধতি একই ফল দিচ্ছে। "
             "এই মিলন আমাদের কাছে এক অলৌকিক উপহার।"},
            {"index": 2, "type": "p",
             "tts":
             "গুণফলের বাস্তব অংশ কোসাইনের পরিবর্তন প্রকাশ করে আর কাল্পনিক অংশ সাইনের পরিবর্তন। "
             "চিত্রে দেখা যাচ্ছে অনুভূমিক অক্ষে যে অংশ পড়েছে তা কোসাইন, আর উল্লম্ব অক্ষে যে অংশ পড়েছে তা সাইন। "
             "কোণ দুটো যোগ হওয়ার সাথে সাথে এই দুটি অংশ নিজেদের মান বদলে নিচ্ছে। "
             "এই পর্যবেক্ষণটিই পরের দুটি সূত্রের জন্ম দেবে।"},
            {"index": 3, "type": "p", "role": "conclusion",
             "tts":
             "জটিল সংখ্যায় কোণ যোগ হওয়া আর বীজগণিতে পদগুলোর গুণফল, দুটি আসলে একই প্রক্রিয়ার দুটি রূপ। "
             "যেহেতু একই গুণফলকে দুইভাবে লেখা যায়, তাই দুই পক্ষের বাস্তব ও কাল্পনিক অংশ তুলনা করলেই সূত্রগুলো স্বতঃস্ফূর্তভাবে বেরিয়ে আসে। "
             "চিত্রে দেখা যাচ্ছে কীভাবে একটি সরল গুণের চিত্র থেকে পুরো ত্রিকোণমিতি নতুন করে আবিষ্কৃত হচ্ছে। "
             "এই কমপ্লেক্স সংখ্যা তত্ত্ব কোনো বাড়তি বোঝা নয়, বরং বীজগণিত, জ্যামিতি ও ত্রিকোণমিতিকে একসাথে মিলিয়ে দেওয়া এক সুসংহত ভাষা।"},
            {"index": 4, "type": "formula-box",
             "tts":
             "কোসাইন যোগফল সূত্রটি বাস্তব অংশের সমতা থেকে সরাসরি পাওয়া যায়। "
             "প্রথম কোণের কোসাইন ও দ্বিতীয় কোণের কোসাইনের গুণফল থেকে দুটি সাইনের গুণফল বাদ দিলেই ডান পাশের মান দাঁড়ায়। "
             "চিত্রে দেখা যাচ্ছে বাস্তব অক্ষের অংশটি ঠিক এইভাবেই গঠিত হচ্ছে। "
             "মুখস্থ করার বদলে এখন আমরা বুঝে পাচ্ছি কেন বিয়োগ চিহ্নটি এখানে আসে।"},
            {"index": 5, "type": "formula-box",
             "tts":
             "সাইন যোগফল সূত্রটি কাল্পনিক অংশের সমতা থেকে একইভাবে বেরিয়ে আসে। "
             "প্রথম কোণের সাইন ও দ্বিতীয় কোণের কোসাইনের গুণফলের সাথে প্রথম কোণের কোসাইন ও দ্বিতীয় কোণের সাইনের গুণফল যোগ করলেই ফলাফল পাওয়া যায়। "
             "চিত্রে দেখা যাচ্ছে উল্লম্ব অক্ষের অংশটি এই যোগফল থেকে তৈরি হচ্ছে। "
             "এই দুটি সূত্র নিয়ে কমপ্লেক্স সংখ্যার এই যাত্রা এক সুন্দর উপসংহারে পৌঁছে যায়।"},
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
    "sec-number-extension":       "সংখ্যা ধারণার বিস্তৃতি",
    "sec-rotation-meaning":       "আই এর আসল অর্থ",
    "sec-argand-plane":           "আরগ্যান্ড চিত্র",
    "sec-polar-form":             "পোলার রূপ",
    "sec-complex-multiplication": "জটিল সংখ্যার গুণন",
    "sec-trig-connection":        "ত্রিকোণমিতির সূত্রাবলি",
}

# Phonetic safeguards that must survive in the spoken text.
REQUIRED_PHRASES = {
    "sec-number-extension":       ["কমপ্লেক্স", "আই", "ঘূর্ণন"],
    "sec-rotation-meaning":       ["আই", "ঘূর্ণন"],
    "sec-argand-plane":           ["আরগ্যান্ড", "কমপ্লেক্স", "আই"],
    "sec-polar-form":             ["পোলার", "অয়লার", "থিটা"],
    "sec-complex-multiplication": ["মডুলাস", "ঘূর্ণন", "আই"],
    "sec-trig-connection":        ["কমপ্লেক্স", "কোসাইন", "সাইন"],
}
GLOBAL_REQUIRED = ["কমপ্লেক্স", "আরগ্যান্ড", "পোলার", "অয়লার", "আই", "ঘূর্ণন"]


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
        "lesson": "lesson_04",
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
    print("BUILD COMPLETE - expressive teacher audio, Lockdown Math Lesson 04")
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
        audio_urls = ["../../assets/audio/lockdown_math/lesson_04/" +
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
    for req in ("sec-number-extension-study", "sec-rotation-meaning-study",
                "sec-argand-plane-study", "sec-polar-form-study",
                "sec-complex-multiplication-study", "sec-trig-connection-study",
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

    # Page cache-buster bumped.
    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    versions = [int(v) for _, v in re.findall(r"(manifest\.js\?v=)(\d+)", html)]
    assert versions and min(versions) >= 3, f"manifest ?v not bumped: {versions}"

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
