# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Calculus Lesson 07
("Limits and the definition of derivatives", Bengali) to the Lesson-01
gold standard.

CRITICAL CONTENT RULE: the OLD manifest narrated an outdated L'Hôpital-topic
script. This rebuild uses ONLY the CURRENT live DOM text of
courses/calculus/lesson_07.html (limits, df/dx -> f'(x), finite nudge h,
infinitesimal misconception, zoom/eps-delta), extracted via the
narration_engine.js selector with KaTeX <annotation> preservation
(governance/calc07_dom_blocks.json).

Deterministic, re-runnable, self-contained:
  * 30 cues in 4 narrated sections with EXACTLY the same section IDs, alias
    keys, audio_file names, cue types and cue order as the existing manifest
    (verified 30/30 against the LIVE DOM: 7/7/8/8).
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Figure cues are genuine 3-4 sentence natural explanations — never the
    artificial label "চিত্র প্রদর্শনী" — and read naturally about what is on
    screen (secant -> tangent, rise-over-run triangle, finite nudge on the
    number line, zooming in on e^x).
  * Every script is clean spoken Bengali with phonetic safeguards:
    x -> এক্স, dx -> ডি এক্স, df/dx -> ডি এফ বাই ডি এক্স, h -> এইচ,
    Δx -> ডেল্টা এক্স, f(x) -> এফ অফ এক্স, f'(x) -> এফ প্রাইম অফ এক্স,
    e^x -> ই পাওয়ার এক্স, ε -> এপসিলন, δ -> ডেল্টা, 0.001 ->
    শূন্য দশমিক শূন্য শূন্য এক. No TeX, LaTeX, backslashes, $, braces,
    brackets, em-dashes, raw hyphens or Latin letters.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, chapter-quote -3%, p +2%, figure -4%, callout +0%,
      formula-box -8%, conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with
    the exact-ms timings and the same 4 canonical section keys of the old
    manifest (each keeps its "alias" field).
  * Validates non-zero durations, zero overlap, valid JSON and non-empty mp3s.

Usage:  python governance/build_expressive_teacher_audio_calc07.py
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
                         "calculus", "lesson_07")
MANIFEST_TITLE = "অধ্যায় ০৭ — সীমা ও অন্তরজের সংজ্ঞা (Limits and the definition of derivatives)"

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

# Parity guards: exact cue-type sequence expected for each narrated section
# (from the live DOM extraction, 30 cues total).
EXPECTED_TYPES = {
    "sec-limits-intro":      ["h2", "chapter-quote", "p", "p", "figure", "p", "callout"],
    "sec-zero-over-zero":    ["h2", "p", "p", "figure", "formula-box", "p", "callout"],
    "sec-lhopital-geometry": ["h2", "chapter-quote", "p", "p", "figure", "formula-box", "p", "callout"],
    "sec-epsilon-delta":     ["h2", "chapter-quote", "p", "p", "figure", "formula-box", "p", "callout"],
}
EXPECTED_AUDIO_FILES = {
    "sec-limits-intro":      "sec_01_limits_intro.mp3",
    "sec-zero-over-zero":    "sec_02_zero_over_zero.mp3",
    "sec-lhopital-geometry": "sec_03_lhopital_geometry.mp3",
    "sec-epsilon-delta":     "sec_04_epsilon_delta.mp3",
}
# Canonical DOM section id -> legacy alias field kept in the manifest.
ALIASES = {
    "sec-limits-intro":      "sec_01_limits_intro",
    "sec-zero-over-zero":    "sec_02_zero_over_zero",
    "sec-lhopital-geometry": "sec_03_lhopital_geometry",
    "sec-epsilon-delta":     "sec_04_epsilon_delta",
}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (30 cues)
# Every line mirrors the CURRENT live DOM block of the same type/index.
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-limits-intro": {
        "title": "১. অন্তরজের সংজ্ঞা ও সীমার প্রয়োজনীয়তা",
        "audio_file": "sec_01_limits_intro.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, অন্তরজের সংজ্ঞা ও সীমার প্রয়োজনীয়তা।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, ক্যালকুলাসের কাজই হলো বাঁকা জিনিসকে সোজা দেখানো, বলেছেন এক অজ্ঞাত অধ্যাপক।"},
            {"index": 2, "type": "p",
             "tts": "আগের অধ্যায়গুলোতে আমরা অন্তরজকে একটিমাত্র ক্রিয়ার মাধ্যমে চিনেছি। কোনো বিন্দুতে, যেমন এক্স সমান দুই, ফাংশনের ইনপুটে ডি এক্স পরিমাণ একটু নাড়া দিই, তারপর ঢালের অনুপাত ডি এফ বাই ডি এক্স বের করি। ছবির মতোই এই অনুপাতটা আসলে রাইজ ওভার রান, অর্থাৎ উপরের পরিবর্তন ডেল্টা এফ আর পাশের পরিবর্তন ডেল্টা এক্সের ভাগ।"},
            {"index": 3, "type": "p",
             "tts": "কিন্তু এখানেই একটা গভীর অস্বস্তি লুকিয়ে আছে। যদি ডি এক্স সত্যিই শূন্য হয়, তবে ডি এফ বাই ডি এক্স দাঁড়ায় শূন্য ভাগ শূন্য, সম্পূর্ণ অনির্ণেয়। আবার যদি ডি এক্স শূন্য না হয়, তবে হিসাবের শেষ ধাপে আমরা বাড়তি ডি এক্স পদগুলো কীভাবে মুছে ফেলি? এই প্রশ্নটিই ক্যালকুলাসের ভিত্তিকে নাড়া দেয়।"},
            {"index": 4, "type": "figure",
             "tts": "এই চিত্রে এক্স সমান দুই বিন্দুতে বক্ররেখার ওপর একটি লাল বিন্দু দেখা যাচ্ছে। হলুদ ভাঙা রেখাটি একটি সসীম নাড়া ডি এক্স নিয়ে টানা ছেদক আর সবুজ রেখাটি তার সীমাস্থ অবস্থা, অর্থাৎ স্পর্শক। ডি এক্স কে যত ছোট করা হয়, ছেদক ততই স্পর্শকের ওপর এসে পড়ে, কিন্তু কখনোই শূন্য করা হয় না। এই কাছে এসে পৌঁছানোর প্রক্রিয়াটিই আসলে লিমিটের কাজ।"},
            {"index": 5, "type": "p",
             "tts": "সমাধান হলো লিমিট। আমরা ডি এক্সকে শূন্য করে দিই না, বরং তাকে শূন্যের যত ইচ্ছা কাছে নিয়ে যাই এবং দেখি অনুপাতটি কোন একক, অপরিবর্তনীয় মানের দিকে এগিয়ে যাচ্ছে। লেখা হয়, ডি এক্স শূন্যের দিকে গেলে ডি এফ বাই ডি এক্সের লিমিট। অর্থাৎ ডি এক্স শূন্যের দিকে গেলে অনুপাতের গন্তব্য কী, সেটাই আমরা খুঁজি।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, মৌলিক অন্তর্দৃষ্টি। লিমিট কখনোই বিন্দুতে কী আছে তা জিজ্ঞেস করে না, সে জিজ্ঞেস করে বিন্দুর অতি কাছে আউটপুট কোন ঠিকানার দিকে ছুটছে। এই ছোট্ট বদলেই ক্যালকুলাস অযৌক্তিকতা থেকে মুক্তি পায়।"},
        ],
    },

    "sec-zero-over-zero": {
        "title": "২. df/dx থেকে f'(x)-এর আনুষ্ঠানিক সংজ্ঞা",
        "audio_file": "sec_02_zero_over_zero.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, ডি এফ বাই ডি এক্স থেকে এফ প্রাইম অফ এক্সের আনুষ্ঠানিক সংজ্ঞা।"},
            {"index": 1, "type": "p",
             "tts": "ধরা যাক আমরা এক্স বিন্দুতে আছি। ইনপুটে একটু নাড়া দিয়ে এক্স প্লাস এইচ বিন্দুতে পৌঁছালাম, যেখানে এইচ একটি সসীম সংখ্যা। ফাংশনের মান বদল হয়ে হলো এফ অফ এক্স প্লাস এইচ। তাই ঢালের আসন্ন অনুপাত দাঁড়ায়, এফ অফ এক্স প্লাস এইচ বিয়োগ এফ অফ এক্স, ভাগ এইচ। উপরে উচ্চতার পরিবর্তন, নিচে অনুভূমিক দূরত্ব।"},
            {"index": 2, "type": "p",
             "tts": "ঐতিহাসিকভাবে লেখকেরা ডি এক্স লেখেন, কিন্তু আনুষ্ঠানিক সংজ্ঞায় একই কথা ডেল্টা এক্স বা কেবল এইচ দিয়ে লেখা হয়। কারণ ডি অক্ষরটিকে অসীম ক্ষুদ্রের রহস্যময় অর্থ দেওয়ার প্রয়োজন নেই। গুরুত্বপূর্ণ হলো এইচ শূন্য নয়, বরং শূন্যের দিকে যাচ্ছে।"},
            {"index": 3, "type": "figure",
             "tts": "এই ছবিতে সবুজ বিন্দু দুটির মাঝে হলুদ অনুভূমিক রেখা এইচ, অর্থাৎ ডেল্টা এক্স, আর খাড়া রেখা এফ অফ এক্স প্লাস এইচ বিয়োগ এফ অফ এক্স দেখানো হয়েছে। সাদা তির্যক রেখাটি একই দুই বিন্দু দিয়ে যাওয়া ছেদক, যার ঢাল ঠিক ঐ অনুপাত। এইচ ছোট হলে ত্রিভুজটি সঙ্কুচিত হয়, কিন্তু তার ঢাল স্থির থাকে। এই স্থিরত্বই আমাদের অন্তরজ।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এফ প্রাইম অফ এক্স সমান, এইচ শূন্যের দিকে গেলে এফ অফ এক্স প্লাস এইচ বিয়োগ এফ অফ এক্স, ভাগ এইচের লিমিট।"},
            {"index": 5, "type": "p",
             "tts": "এই সমীকরণটিই অন্তরজের আনুষ্ঠানিক সংজ্ঞা। এখানে কোথাও অসীম ক্ষুদ্র বলা নেই, শুধু বলা আছে এইচকে শূন্যের কাছে পাঠালে ভাগফল যে মানে স্থিতিশীল হয়, তাই এফ প্রাইম অফ এক্স। যেমন এফ অফ টি সমান টি কিউবের টি সমান দুই বিন্দুতে এই সীমা দেয় তিন গুণ দুই স্কয়ার, অর্থাৎ বারো, আগের অধ্যায়ের সেই পরিচিত বারো।"},
            {"index": 6, "type": "callout", "role": "conclusion",
             "tts": "বিশেষ নোট, ডেল্টা এক্স, এইচ আর ডি এক্স, একই কথার তিন রূপ। এগুলো সবই একই ধারণার ভিন্ন পোশাক। পার্থক্য শুধু ঐতিহ্য ও লেখার সুবিধার, গাণিতিক সারমর্ম অপরিবর্তিত, একটি সসীম নাড়া, তারপর সীমা।"},
        ],
    },

    "sec-lhopital-geometry": {
        "title": "৩. ‘অসীম ক্ষুদ্র’ নিয়ে ভুল বোঝাবুঝি",
        "audio_file": "sec_03_lhopital_geometry.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, অসীম ক্ষুদ্র নিয়ে ভুল বোঝাবুঝি।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, বিদায়ী রাশির প্রেতাত্মা, ক্যালকুলাসের ওপর এক তীক্ষ্ণ ঐতিহাসিক কটাক্ষ, যার উত্তর লিমিট, বলেছেন বিশপ জর্জ বার্কলে।"},
            {"index": 2, "type": "p",
             "tts": "অনেকেই মনে করেন ক্যালকুলাস অসীম ক্ষুদ্র নামক কোনো রহস্যময় সংখ্যার ওপর দাঁড়িয়ে। কিন্তু আনুষ্ঠানিক সংজ্ঞায় এমন কোনো জিনিস নেই। এইচ হলো একেবারে সাধারণ, বাস্তব সংখ্যা, যেমন শূন্য দশমিক শূন্য শূন্য এক। আপনি ক্যালকুলেটরে বসিয়ে দেখতে পারেন, এফ অফ এক্স প্লাস শূন্য দশমিক শূন্য শূন্য এক বিয়োগ এফ অফ এক্স, ভাগ শূন্য দশমিক শূন্য শূন্য এক, সত্যিই এফ প্রাইম অফ এক্সের কাছাকাছি।"},
            {"index": 3, "type": "p",
             "tts": "ভুলটা হয় যখন আমরা ডি এক্সকে একই সাথে শূন্য ও অশূন্য ভাবি, আগে ভাগের জন্য ধরে রাখি, পরে মুছে দিই। লিমিট এই দ্বিচারিতা দূর করে। প্রথমে এইচকে সসীম রেখে হিসাব করি, তারপর এইচ শূন্যের দিকে যাচ্ছে বলে সীমা নিই। কোনো ধাপেই শূন্য দিয়ে ভাগ করা হয় না।"},
            {"index": 4, "type": "figure",
             "tts": "ছবিতে সংখ্যারেখায় এক্স ও এক্স প্লাস শূন্য দশমিক শূন্য শূন্য এক, এই দুটি বিন্দু দেখানো হয়েছে। এগুলো আলাদা, পরিমাপযোগ্য দূরত্ব। বড় বিবর্ধক কাঁচটি স্মরণ করিয়ে দেয় যে আমরা শুধু কাছ থেকে দেখছি, কোনো অদৃশ্য অণু সংখ্যা ব্যবহার করছি না। এইচ সমান শূন্য দশমিক শূন্য শূন্য এক একটি নির্দিষ্ট, নিরাপদ সংখ্যা, আর সীমা তারপর আসে।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এফ অফ এক্স প্লাস শূন্য দশমিক শূন্য শূন্য এক বিয়োগ এফ অফ এক্স, ভাগ শূন্য দশমিক শূন্য শূন্য এক, প্রায় সমান এফ প্রাইম অফ এক্স। আর এফ প্রাইম অফ এক্স সমান, এইচ শূন্যের দিকে গেলে এফ অফ এক্স প্লাস এইচ বিয়োগ এফ অফ এক্স, ভাগ এইচের লিমিট।"},
            {"index": 6, "type": "p",
             "tts": "এই পদ্ধতির সুন্দর দিক হলো ত্রুটিও পরিমাপ করা যায়। এইচ যত ছোট, আসন্ন ঢালের শতাংশ ত্রুটি তত কমে। তাই অসীম ক্ষুদ্রের রহস্য না বেঁধেই কাজ চলে, সসীম নাড়া আর সীমা, এই দুটিই যথেষ্ট।"},
            {"index": 7, "type": "callout",
             "tts": "বিশেষ নোট, পাদটীকা, ইনফিনিটেসিমাল নিয়ে। আধুনিক গণিতে হাইপাররিয়েল সংখ্যা ব্যবহার করে ইনফিনিটেসিমালকেও সুসংজ্ঞায়িত করা যায়, বলেছেন অ্যাব্রাহাম রবিনসন। কিন্তু সেটি একটিমাত্র বিকল্প ভাষা, আমাদের জন্য এপসিলন ডেল্টা ভাষাই যথেষ্ট ও ঝামেলামুক্ত।"},
        ],
    },

    "sec-epsilon-delta": {
        "title": "৪. কেন আমরা এ নিয়ে ভাবব — পরবর্তী অধ্যায়",
        "audio_file": "sec_04_epsilon_delta.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, কেন আমরা এ নিয়ে ভাবব, পরবর্তী অধ্যায়।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, যথেষ্ট কাছ থেকে দেখলে বক্ররেখা সোজা লাগে, অন্তরজ আপনাকে বলে দেয় বক্ররেখাটি ঠিক কেমন দেখায় যখন আপনি তা যথেষ্ট কাছ থেকে দেখেন, বলেছেন গ্রান্ট স্যান্ডারসন।"},
            {"index": 2, "type": "p",
             "tts": "কেন আমরা এত খাটাখাটুনি করছি? কারণ অন্তরজের কাজই হলো বাঁকা জিনিসকে সোজা দেখানো। ই পাওয়ার এক্স বক্ররেখার এক্স সমান শূন্য বিন্দুতে যদি আপনি বারবার জুম করেন, দেখবেন বক্রতা কমে যাচ্ছে এবং স্পর্শকের ঢাল আসছে একের কাছে, ঠিক সেখানকার ফাংশনের মানের মতোই।"},
            {"index": 3, "type": "p",
             "tts": "কতদূর জুম করা দরকার? ব্যবহারিক প্রকৌশলী বলবেন, যতক্ষণ ত্রুটি সহনশীলতার ভেতরে থাকে, ততক্ষণই যথেষ্ট, এটা যথার্থতার খেলা। গণিতবিদ চাইবেন এক নিখুঁত উত্তর, প্রতিটি চ্যালেঞ্জের ব্যবধান এপসিলনের জন্য এমন এক ডেল্টা আছে কি? এই প্রশ্নের উত্তরই পরবর্তী অধ্যায়ের এপসিলন ডেল্টা সংজ্ঞা।"},
            {"index": 4, "type": "figure",
             "tts": "চিত্রে ই পাওয়ার এক্স বক্ররেখার এক্স সমান শূন্য বিন্দুটিকে ঘিরে দুটি জুম বক্স দেখা যাচ্ছে। সবুজ স্পর্শকের ঢাল এক, আর হলুদ বৃত্তাকার অংশ বাড়ালে বক্ররেখা সরলরেখার মতো দেখায়। মনে রাখবেন জুম কেবল দৃশ্যমান সাহায্য, আর সীমা হলো তার নিখুঁত গাণিতিক রূপ।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এইচ শূন্যের দিকে গেলে ই পাওয়ার এইচ বিয়োগ এক, ভাগ এইচের লিমিট সমান এক।"},
            {"index": 6, "type": "p",
             "tts": "পরবর্তী পর্বে আমরা এই কাছে আসাকে সংখ্যায় বাঁধব। এক্স মাইনাস এ এর পরিমাপ ডেল্টার চেয়ে ছোট হলে, এফ অফ এক্স মাইনাস এলের পরিমাপ এপসিলনের চেয়ে ছোট হবে। অর্থাৎ ইনপুট যত কাছে আসবে, আউটপুট তত নির্দিষ্ট লক্ষ্যের ভেতরে পড়বে। সেখানেই লিমিটের পূর্ণ কঠোরতা জন্ম নেবে।"},
            {"index": 7, "type": "callout", "role": "conclusion",
             "tts": "বিশেষ নোট, শেষ কথা। লিমিট কোনো অতিরিক্ত যন্ত্রপাতি নয়, এটি আমাদের সাধারণ বুদ্ধিকেই লিখিত রূপ দেয়। আপনি ইতিমধ্যেই বুঝেছেন বক্ররেখা কাছ থেকে সোজা হয়, এপসিলন ডেল্টা শুধু সেই বোঝাপড়ার হিসাববই।"},
        ],
    },
}

# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"
OLD_TOPIC_TERMS = ["ল'হোপিতাল", "ল’হোপিতাল", "ল'হোপিটাল", "এল'হোপিতাল", "L'Hôpital"]


def assert_clean_scripts():
    """Fail before any TTS work if a script still contains markup or Latin text."""
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars {bad!r} in {cue['tts']!r}")
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: artificial figure label present")
            if any(term in cue["tts"] for term in OLD_TOPIC_TERMS):
                raise ValueError(f"{sec_id} cue {cue['index']}: outdated L'Hopital topic text present")

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
    if total != 30:
        raise ValueError(f"Expected 30 cues, found {total}")

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
        manifest_sections[sec_id] = await build_section(sec_id, sec)

    manifest_data = {
        "course": "calculus",
        "lesson": "lesson_07",
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
    expected_keys = set(SECTIONS_DATA)
    assert set(loaded["sections"]) == expected_keys
    total_cues = 0
    total_ms = 0.0
    figures = 0
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == len(EXPECTED_TYPES[sec_id])
        assert msec["section_id"] == sec_id
        assert msec["alias"] == ALIASES[sec_id]
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    assert total_cues == 30

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Calculus Lesson 07")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<26} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 4 sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json is valid JSON; all 4 mp3 files exist and are non-empty.")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(build_all())
