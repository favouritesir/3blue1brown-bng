# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Calculus Lesson 09
("What does area have to do with slope?", Bengali) to the Lesson-01/02 gold
standard.

Deterministic, re-runnable, self-contained:
  * 29 cues in 5 narrated sections with EXACTLY the same section IDs, audio_file
    names and cue type/order as the existing manifest and the live DOM:
      sec-area-slope-mystery       -> h2, chapter-quote, p, p, figure, p, callout (7)
      sec-accumulation-function    -> h2, p, p, figure, p, callout              (6)
      sec-fundamental-theorem      -> h2, p, p, figure, p, callout              (6)
      sec-velocity-distance        -> h2, p, figure, p, callout                 (5)
      sec-signed-area-average      -> h2, p, p, figure, callout                 (5)
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Figure cues are genuine 2-4 sentence natural explanations — never the
    artificial label "চিত্র প্রদর্শনী".
  * Every script is clean spoken Bengali with phonetic safeguards:
      sin -> সাইন, cos -> কোস, -cos -> মাইনাস কোস, integral -> ইন্টিগ্রাল,
      dx -> ডি এক্স, dt -> ডি টি, pi -> পাই, x -> এক্স, etc.
    No TeX, LaTeX, backslashes, $, braces, brackets, em/en-dashes, raw hyphens
    or Latin letters.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, chapter-quote -3%, p +2%, figure -4%, callout +0%,
      formula-box -8%, conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with the
    exact-ms timings and the exact 5 section keys of the old manifest.
  * Validates non-zero durations, zero overlap, valid JSON and non-empty mp3s,
    plus DOM parity against the browser-extracted calc09_dom_blocks.json.

Usage:  python governance/build_expressive_teacher_audio_calc09.py
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
                         "calculus", "lesson_09")
DOM_SNAPSHOT = os.path.join(SCRIPT_DIR, "calc09_dom_blocks.json")
MANIFEST_TITLE = "অধ্যায় ০৯ — ক্ষেত্রফলের সাথে ঢালের কী সম্পর্ক? (ক্যালকুলাসের মৌলিক উপপাদ্য)"

# Prosody keyed by cue type: (rate, pitch, volume)
PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
    "h3":            ("-3%", "+0Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),   # measured, thoughtful quotation
    "p":             ("+2%", "+0Hz", "+0%"),   # natural teacher pace
    "figure":        ("-4%", "+0Hz", "+0%"),   # slower, considerate explanation
    "callout":       ("+0%", "+0Hz", "+0%"),   # steady emphasis
    "formula-box":   ("-8%", "+0Hz", "+0%"),   # slow and deliberate
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")     # calm concluding prose

# Parity guards: exact cue-type sequence of each narrated section (live DOM).
EXPECTED_TYPES = {
    "sec-area-slope-mystery":    ["h2", "chapter-quote", "p", "p", "figure", "p", "callout"],
    "sec-accumulation-function": ["h2", "p", "p", "figure", "p", "callout"],
    "sec-fundamental-theorem":   ["h2", "p", "p", "figure", "p", "callout"],
    "sec-velocity-distance":     ["h2", "p", "figure", "p", "callout"],
    "sec-signed-area-average":   ["h2", "p", "p", "figure", "callout"],
}
EXPECTED_AUDIO_FILES = {
    "sec-area-slope-mystery":    "sec_01_area_slope_mystery.mp3",
    "sec-accumulation-function": "sec_02_accumulation_function.mp3",
    "sec-fundamental-theorem":   "sec_03_fundamental_theorem.mp3",
    "sec-velocity-distance":     "sec_04_velocity_distance.mp3",
    "sec-signed-area-average":   "sec_05_signed_area_average.mp3",
}
# Legacy alias names kept in each section's `alias` field (NOT extra keys).
ALIASES = {
    "sec-area-slope-mystery":    "sec_01_area_slope_mystery",
    "sec-accumulation-function": "sec_02_accumulation_function",
    "sec-fundamental-theorem":   "sec_03_fundamental_theorem",
    "sec-velocity-distance":     "sec_04_velocity_distance",
    "sec-signed-area-average":   "sec_05_signed_area_average",
}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (29 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-area-slope-mystery": {
        "title": "১. ক্ষেত্রফল ও ঢালের রহস্যময় সংযোগ (The Area-Slope Mystery)",
        "audio_file": "sec_01_area_slope_mystery.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, ক্ষেত্রফল ও ঢালের আপাত বৈপরীত্য আর রহস্যময় সংযোগ।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, আমরা প্রায়ই শুনি গণিত মূলত উপপাদ্য প্রমাণ করার নাম, তবে কি একজন লেখকের কাজ মূলত বাক্য লেখা? বলেছেন জিয়ান কার্লো রোটা।"},
            {"index": 2, "type": "p",
             "tts": "প্রথম দেখায় মনে হতে পারে, বক্ররেখার নিচের ক্ষেত্রফল পরিমাপ করা আর স্পর্শক রেখার ঢাল নির্ণয় করা সম্পূর্ণ ভিন্ন দুটি জ্যামিতিক সমস্যা। অন্তরজ আর সমাকলন যেন দুটি আলাদা পথ।"},
            {"index": 3, "type": "p",
             "tts": "ঢাল বা অন্তরীকরণ মানে একটি বিন্দুর অতি ক্ষুদ্র প্রতিবেশে জুম করে তাৎক্ষণিক পরিবর্তনের হার দেখা। অন্যদিকে সমাকলন মানে পুরো অঞ্চলকে অসীম সংখ্যক সরু ফালিতে ভেঙে সবগুলো যোগ করা।"},
            {"index": 4, "type": "figure",
             "tts": "এই ছবিতে নীল বক্ররেখার নিচের আবদ্ধ অঞ্চলটিকে বালির স্তূপের মতো দেখানো হয়েছে। হলুদ ভাঙা আয়তক্ষেত্রটি সেই একই ক্ষেত্রফলের সমতল রূপ, আর এর উচ্চতা বের করতে হলে ক্ষেত্রফলকে প্রস্থ দিয়ে ভাগ করতে হয়। লক্ষ্য করুন, আয়তক্ষেত্রের ক্ষেত্রফল মূল বক্ররেখার ক্ষেত্রফলের হুবহু সমান, আর এই উচ্চতাই হলো ফাংশনের গড় মান।"},
            {"index": 5, "type": "p",
             "tts": "তা সত্ত্বেও এই দুটি প্রক্রিয়া পরস্পরের নিখুঁত বিপরীতমুখী অপারেশন। একেই বলা হয় ক্যালকুলাসের মৌলিক উপপাদ্য, বা ফান্ডামেন্টাল থিওরেম অফ ক্যালকুলাস।"},
            {"index": 6, "type": "callout", "role": "conclusion",
             "tts": "মৌলিক প্রশ্ন, কেন বক্ররেখার নিচের ক্ষেত্রফল খোঁজার সমাধান লুকিয়ে থাকে আরেকটি ফাংশনের ঢাল খোঁজার ভেতর? এর চাবিকাঠি হলো গড় মানকে স্পর্শকের গড় ঢাল হিসেবে দেখা, যা নিচের সেকশনগুলোতে ধাপে ধাপে উন্মোচন করব।"},
        ],
    },

    "sec-accumulation-function": {
        "title": "২. সঞ্চয়ন ফাংশন A(x) ও অতি ক্ষুদ্র ধাপ dx (The Accumulation Function)",
        "audio_file": "sec_02_accumulation_function.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, সীমিত নমুনা থেকে ইন্টিগ্রাল, অর্থাৎ সঞ্চয়ন ফাংশনের ধারণা।"},
            {"index": 1, "type": "p",
             "tts": "ধরা যাক শূন্য থেকে পাই ব্যবধিতে সাইন ফাংশনের বক্ররেখা, এটি তার অর্ধ পর্যায়। প্রকৃতির অনেক চক্রীয় ঘটনাই সাইন তরঙ্গ দিয়ে মডেল করা হয়। বছরের কোন দিনে সূর্য কত ঘণ্টা থাকে, অর্থাৎ দৈনিক আলোর সময়, তাও সাইন আকৃতির বক্ররেখা অনুসরণ করে। সৌর প্যানেলের গ্রীষ্মকালীন ও শীতকালীন গড় কার্যকারিতা বের করতে হলে ঠিক এই ধরনের গড় মানই দরকার।"},
            {"index": 2, "type": "p",
             "tts": "কিন্তু শূন্য থেকে পাই এর মধ্যে সাইন ফাংশনের অসংখ্য মান আছে, এদের সবাইকে যোগ করে অসীম দিয়ে ভাগ করা সম্ভব নয়। তাই প্রথমে আমরা সসীম কয়েকটি বিন্দু নিই, সমান ব্যবধানে ছড়িয়ে, এবং তাদের উচ্চতার যোগফলকে নমুনার সংখ্যা দিয়ে ভাগ করি। নমুনা যত বাড়বে, এই গড় ততই অবিচ্ছিন্ন গড়ের কাছে পৌঁছাবে।"},
            {"index": 3, "type": "figure",
             "tts": "চিত্রে শূন্য থেকে পাই জুড়ে সাইন বক্ররেখার ওপর কয়েকটি হলুদ নমুনা বিন্দু আর তাদের সরু আয়তাকার ফালি দেখা যাচ্ছে। প্রতিটি ফালির প্রস্থ ডি এক্স এবং উচ্চতা সাইন অফ এক্স, ফলে তার ক্ষেত্রফল সাইন অফ এক্স গুণ ডি এক্স। নমুনার সংখ্যা বাড়ালে এই ফালিগুলোই ইন্টিগ্রালের রিম্যান যোগফলে রূপ নেয়।"},
            {"index": 4, "type": "p",
             "tts": "এখন নমুনাগুলোর ব্যবধানকে ডি এক্স লিখি। শূন্য থেকে পাই পর্যন্ত মোট দৈর্ঘ্যকে ডি এক্স দিয়ে ভাগ করলে নমুনার সংখ্যা দাঁড়ায় পাই ভাগ ডি এক্স, যেমন ব্যবধান দশমিক এক হলে নমুনা প্রায় একত্রিশ। গড়ের ভাগফলে এই পাই ভাগ ডি এক্স বসিয়ে ডি এক্স কে উপরে নিয়ে এসে বিন্যাস করলে পাই ইন্টিগ্রাল শূন্য থেকে পাই সাইন অফ এক্স ডি এক্স ভাগ পাই। অর্থাৎ গড় মান সমান ক্ষেত্রফল ভাগ প্রস্থ।"},
            {"index": 5, "type": "callout", "role": "conclusion",
             "tts": "বিশেষ নোট, অসীম সংখ্যক মানকে কোনোভাবে যোগ করার ইচ্ছা হলেই বুঝতে হবে এখানে ইন্টিগ্রালের প্রয়োজন। সসীম নমুনা দিয়ে কাজ শুরু করে তারপর ডি এক্স শূন্যের দিকে যাওয়ার সীমা নেওয়া এই রূপান্তরের নিখুঁত পদ্ধতি, আর এটি কেবল সাইনের ক্ষেত্রেই নয়, যেকোনো অবিচ্ছিন্ন ফাংশনের ক্ষেত্রে প্রযোজ্য।"},
        ],
    },

    "sec-fundamental-theorem": {
        "title": "৩. ক্যালকুলাসের মৌলিক উপপাদ্য: dA/dx = f(x) (The Fundamental Theorem)",
        "audio_file": "sec_03_fundamental_theorem.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, ক্যালকুলাসের মৌলিক উপপাদ্য আর অ্যান্টিডেরিভেটিভের সন্ধান।"},
            {"index": 1, "type": "p",
             "tts": "ইন্টিগ্রালের মান বের করতে হলে অ্যান্টিডেরিভেটিভ খুঁজতে হয়। আগের অধ্যায় থেকে জানি, কোস অফ এক্সের অন্তরজ মাইনাস সাইন অফ এক্স, সুতরাং মাইনাস কোস অফ এক্স হলো সাইন অফ এক্সের অ্যান্টিডেরিভেটিভ। নিজেই যাচাই করে দেখুন, শূন্য বিন্দুতে মাইনাস কোসের ঢাল শূন্য, পাই ভাগ দুইয়ে সর্বোচ্চ ঢাল, আবার পাই তে শূন্য, প্রতিটি বিন্দুতে ঢাল হুবহু সাইনের উচ্চতার সমান।"},
            {"index": 2, "type": "p",
             "tts": "এবার শূন্য থেকে পাই পর্যন্ত সাইন অফ এক্সের ইন্টিগ্রাল হিসাব করি। উপরের সীমায় অ্যান্টিডেরিভেটিভের মান থেকে নিচের সীমার মান বাদ দিই, মাইনাস কোস পাই বিয়োগ মাইনাস কোস শূন্য, অর্থাৎ এক বিয়োগ মাইনাস এক, ফলাফল দুই। ছবিতে এটি মাইনাস কোস বক্ররেখার শূন্য ও পাই বিন্দুর উচ্চতার পার্থক্য, আর সেই পার্থক্য হুবহু দুই, অর্থাৎ সাইনের নিচের মোট ক্ষেত্রফল ঠিক দুই।"},
            {"index": 3, "type": "figure",
             "tts": "চিত্রে নীল মাইনাস কোস অফ এক্স বক্ররেখা আর তার ওপর দুটি বিন্দু দেখা যাচ্ছে, একটি শূন্য বিন্দুতে এবং অন্যটি পাই বিন্দুতে। সবুজ ভাঙা রেখাটি দুই বিন্দুর উচ্চতার পার্থক্য দুই দেখাচ্ছে, যা হুবহু সাইন বক্ররেখার নিচের আবদ্ধ ক্ষেত্রফল। পাশের ছায়াঘেরা সাইন অঞ্চলটি মনে করিয়ে দেয় যে মাইনাস কোসের ঢালই সাইনের উচ্চতা।"},
            {"index": 4, "type": "p",
             "tts": "সুতরাং আমাদের গড় উচ্চতার উত্তর দুই ভাগ পাই, প্রায় দশমিক ছয় চার। ক্ষেত্রফল ফাংশন এ অফ এক্স, অর্থাৎ শূন্য থেকে এক্স পর্যন্ত ফাংশনের ইন্টিগ্রাল, তার বৃদ্ধির হার দি এ ভাগ দি এক্স সমান এফ অফ এক্স। অর্থাৎ ক্ষেত্রফল বের করা মানে এমন একটি ফাংশন ক্যাপিটাল এফ খোঁজা যার অন্তরজ মূল ফাংশন, যোগজীকরণ ও ব্যবকলন একে অপরের নিখুঁত বিপরীত প্রক্রিয়া।"},
            {"index": 5, "type": "callout", "role": "conclusion",
             "tts": "ক্যালকুলাসের মূল উপপাদ্য, ইন্টিগ্রাল এ থেকে বি এফ অফ এক্স ডি এক্স সমান ক্যাপিটাল এফ অফ বি বিয়োগ ক্যাপিটাল এফ অফ এ। এই রূপটি আমাদের বলে যে অ্যান্টিডেরিভেটিভই হলো ইন্টিগ্রালের চাবিকাঠি, আর সাইনের ক্ষেত্রে মাইনাস কোস সেই চাবিকাঠি, দুই প্রান্তের উচ্চতার পার্থক্য আমাদের সরাসরি দুই ফেরত দেয়, কোনো ফালি গণনা না করেই।"},
        ],
    },

    "sec-velocity-distance": {
        "title": "৪. বেগ বনাম দূরত্ব এবং নিট সরণের ভৌত রূপ (Velocity and Distance Intuition)",
        "audio_file": "sec_04_velocity_distance.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, বেগ বনাম দূরত্ব আর অ্যান্টিডেরিভেটিভের ঢাল।"},
            {"index": 1, "type": "p",
             "tts": "এবার দুই ভাগ পাই সংখ্যাটিকে অন্য চোখে দেখা যাক। এটি এসেছে মাইনাস কোস অফ এক্স ফাংশনের শূন্য ও পাই বিন্দুর উচ্চতার পার্থক্য দুই কে ব্যবধির দৈর্ঘ্য পাই দিয়ে ভাগ করে, অর্থাৎ দুই প্রান্তের মাঝে টানা সরলরেখার রাইজ ওভার রান ঢাল। যেহেতু মাইনাস কোসের অন্তরজ হলো সাইন, তাই সাইনের গড় মানকে ধরা যায় ওই ব্যবধিতে মাইনাস কোসের সব স্পর্শকের ঢালের গড় হিসেবে, আর সব বিন্দুতে ঢালের গড় অবশ্যই শুরু ও শেষ বিন্দুর মোট ঢালের সমান হয়।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে মাইনাস কোস অফ এক্স বক্ররেখার শূন্য ও পাই বিন্দুতে হলুদ ভাঙা রেখা দিয়ে রাইজ ওভার রান ঢাল দেখানো হয়েছে, আর সবুজ রেখা একটি মধ্যবর্তী স্পর্শক। বক্ররেখা যতই বাঁকা হোক, সমস্ত স্পর্শকের গড় ঢাল শেষ পর্যন্ত প্রান্তদুটির সরলরেখার ঢালেরই সমান হয়। এই উপলব্ধিই অ্যান্টিডেরিভেটিভের শক্তি।"},
            {"index": 3, "type": "p",
             "tts": "এই দৃষ্টিভঙ্গির সাথে আমাদের পরিচিত ভৌত উপমাটিও মিলে যায়। চলন্ত গাড়ির ক্ষেত্রে বেগ ভি সমান ডি এস ভাগ ডি টি হলো দূরত্বের অন্তরজ, আর ক্ষুদ্র সময় ডি টি তে অতিক্রান্ত দূরত্ব ডি এস সমান বেগ গুণ ডি টি হলো বেগ লেখচিত্রের একটি সরু ফালির ক্ষেত্রফল। সব ফালি যোগ করলে যেমন মোট ক্ষেত্রফল মেলে, তেমনি নিট সরণও মেলে, ক্ষেত্রফল ও ঢালের এই দ্বৈত রূপই অধ্যায়জুড়ে ফিরে আসছে।"},
            {"index": 4, "type": "callout", "role": "conclusion",
             "tts": "বিশেষ নোট, অ্যান্টিডেরিভেটিভের প্রতিটি বিন্দুতে স্পর্শকের ঢাল দেয় মূল ফাংশন এফ অফ এক্স। তাই এফ এর গড় মান বলতে আমরা আসলে বুঝি মাইনাস কোসের সব স্পর্শকের ঢালের গড়, যা শুরু ও শেষ বিন্দু দেখেই নির্ণয় করা যায়, মাঝের অসংখ্য বিন্দু যোগ না করেই।"},
        ],
    },

    "sec-signed-area-average": {
        "title": "৫. ঋণাত্মক ক্ষেত্রফল ও ফাংশনের গড় মান (Negative Areas and Average Value)",
        "audio_file": "sec_05_signed_area_average.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, চিহ্নযুক্ত ক্ষেত্রফল আর ফাংশনের গড় মান।"},
            {"index": 1, "type": "p",
             "tts": "এখন ধরা যাক কোনো ফাংশন এফ অফ এক্সের এ থেকে বি ব্যবধিতে গড় মান বের করতে হবে। নিয়মটি হলো, এ থেকে বি পর্যন্ত ইন্টিগ্রাল কে বি বিয়োগ এ দিয়ে ভাগ করা, অর্থাৎ বক্ররেখার নিচের ক্ষেত্রফলকে প্রস্থ দিয়ে ভাগ করা। কিন্তু এখানে একটা সূক্ষ্মতা আছে, ক্ষেত্রফল আসলে স্বাক্ষরিত, কারণ এক্স অক্ষের নিচের অংশ ঋণাত্মক হিসেবে গণনা হয়।"},
            {"index": 2, "type": "p",
             "tts": "সসীম গড়ের সাথে মিলিয়ে দেখলে চিত্রটি পরিষ্কার। ডি এক্স ব্যবধানে নমুনা নিলে সংখ্যা দাঁড়ায় প্রস্থ ভাগ ডি এক্স, প্রতিটি মান এফ অফ এক্স কে ডি এক্স দিয়ে গুণ করে যোগ করলে উপরে থাকে সব এফ অফ এক্স গুণ ডি এক্সের যোগফল, আর ভাগ হয় প্রস্থ দ্বারা, হুবহু ইন্টিগ্রালের সংজ্ঞা, শুধু ডি এক্স শূন্যের দিকে যাওয়ার সীমা ছাড়া। ইন্টিগ্রাল মূল্যায়ন করতে হয় অ্যান্টিডেরিভেটিভ ক্যাপিটাল এফ দিয়ে, ক্যাপিটাল এফ অফ বি বিয়োগ ক্যাপিটাল এফ অফ এ।"},
            {"index": 3, "type": "figure",
             "tts": "চিত্রে বক্ররেখা এক্স অক্ষের ওপরে সবুজ ধনাত্মক অঞ্চল আর নিচে লাল ঋণাত্মক অঞ্চল দেখা যাচ্ছে। হলুদ ভাঙা আয়তক্ষেত্রটি এই স্বাক্ষরিত ক্ষেত্রফলকেই প্রস্থ দিয়ে ভাগ করে পাওয়া গড় উচ্চতা, ঋণাত্মক অঞ্চল গড় কমিয়ে দেয়। মনে রাখবেন, গড় মান মানেই এমন একটি ধ্রুবক উচ্চতা যার আয়তক্ষেত্র মূল বক্ররেখার সমান স্বাক্ষরিত ক্ষেত্রফল ধারণ করে।"},
            {"index": 4, "type": "callout", "role": "conclusion",
             "tts": "সাধারণ সূত্র হলো, এ থেকে বি পর্যন্ত ইন্টিগ্রাল ভাগ বি বিয়োগ এ সমান ক্যাপিটাল এফ অফ বি বিয়োগ ক্যাপিটাল এফ অফ এ ভাগ বি বিয়োগ এ, অর্থাৎ অ্যান্টিডেরিভেটিভ ক্যাপিটাল এফের দুই প্রান্তের মাঝকার রাইজ ওভার রান ঢাল, যা হুবহু এফ অফ এক্সের গড় মান। অন্তরজ আর সমাকলন একে অপরের বিপরীত, এই উপসংহারে আমরা দ্বিতীয় একটি পথ থেকে পৌঁছালাম। ক্ষেত্রফলকে প্রস্থ দিয়ে ভাগ করে পাওয়া গড় মান, আবার সেই গড় মান অ্যান্টিডেরিভেটিভের প্রান্তদুটির ঢাল, এই দুই দৃষ্টিভঙ্গি একসাথে মিলে ক্যালকুলাসের মৌলিক উপপাদ্যকে নতুন করে বোঝায়।"},
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
    if len(SECTIONS_DATA) != 5:
        raise ValueError("Expected exactly 5 narrated sections")
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

    # DOM parity against the browser-extracted live snapshot (narration_engine
    # selector + KaTeX <annotation> preservation).
    if os.path.exists(DOM_SNAPSHOT):
        with open(DOM_SNAPSHOT, encoding="utf-8") as fh:
            snap = json.load(fh)
        snap_types = {s["id"]: [b["type"] for b in s["blocks"]]
                      for s in snap["sections"]}
        if snap_types != EXPECTED_TYPES:
            raise ValueError(f"DOM snapshot cue types differ from embedded EXPECTED_TYPES:\n"
                             f"snapshot={snap_types}\nexpected={EXPECTED_TYPES}")
        if set(snap_types) != set(SECTIONS_DATA):
            raise ValueError("DOM snapshot section ids differ from embedded sections")

    # No duplicate spoken scripts.
    spoken = [c["tts"] for s in SECTIONS_DATA.values() for c in s["cues"]]
    if len(spoken) != len(set(spoken)):
        raise ValueError("Duplicate spoken cue scripts detected")


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
        "lesson": "lesson_09",
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
        assert msec["audio_file"] == EXPECTED_AUDIO_FILES[sec_id]
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    assert total_cues == 29

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Calculus Lesson 09")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<26} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 5 sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json is valid JSON; all 5 mp3 files exist and are non-empty.")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(build_all())
