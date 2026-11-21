# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Calculus Lesson 05
("What's so special about Euler's number e?", Bengali) to the Lesson-01 gold
standard.

CONTENT RULE: every script mirrors the CURRENT live DOM of
courses/calculus/lesson_05.html, extracted with the narration_engine.js
section/block selector and KaTeX <annotation> preservation
(governance/calc05_dom_blocks.json). Verified 23/23 cues in 4 narrated
sections (5/6/6/6). The figure/media-tab captions are woven into the spoken
prose with natural phrasing — never the artificial label "চিত্র প্রদর্শনী".

Deterministic, re-runnable, self-contained:
  * 23 cues in 4 narrated sections with EXACTLY the same section IDs, alias
    keys, audio_file names, cue types and cue order as the existing manifest.
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Every script is clean spoken Bengali with phonetic safeguards:
    e -> ই, e^t -> ই পাওয়ার টি, e^(kt) -> ই পাওয়ার কে টি, dt -> ডি টি,
    ln -> লন, ln 2 -> লন টু, 2^t -> টু টু দ্য পাওয়ার টি, k -> কে,
    M(t) -> এম অফ টি, pi -> পাই. No TeX, LaTeX, backslashes, $, braces,
    brackets, em-dashes, raw hyphens or Latin letters.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, chapter-quote -3%, p +2%, callout +0%,
      formula-box -8%, conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with the
    exact-ms timings and the same 4 canonical section keys of the old manifest
    (each keeps its "alias" field).
  * Validates non-zero durations, zero overlap, valid JSON and non-empty mp3s.

Usage:  python governance/build_expressive_teacher_audio_calc05.py
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
                         "calculus", "lesson_05")
MANIFEST_TITLE = "অধ্যায় ০৫ — অয়লার সংখ্যা e কেন এত বিশেষ? | ৩ব্লু১ব্রাউন বাংলা"

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
# (from the live DOM extraction, 23 cues total: 5 / 6 / 6 / 6).
EXPECTED_TYPES = {
    "sec-mystery":            ["h2", "chapter-quote", "p", "formula-box", "callout"],
    "sec-proportional-growth": ["h2", "p", "formula-box", "p", "p", "callout"],
    "sec-compound-interest":  ["h2", "p", "p", "p", "formula-box", "callout"],
    "sec-chain-rule-growth":  ["h2", "p", "formula-box", "p", "p", "callout"],
}
EXPECTED_AUDIO_FILES = {
    "sec-mystery":            "sec_01_mystery.mp3",
    "sec-proportional-growth": "sec_02_proportional_growth.mp3",
    "sec-compound-interest":  "sec_03_compound_interest.mp3",
    "sec-chain-rule-growth":  "sec_04_chain_rule_growth.mp3",
}
# Canonical DOM section id -> legacy alias field kept in the manifest.
ALIASES = {
    "sec-mystery":            "sec_01_mystery",
    "sec-proportional-growth": "sec_02_proportional_growth",
    "sec-compound-interest":  "sec_03_compound_interest",
    "sec-chain-rule-growth":  "sec_04_chain_rule_growth",
}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (23 cues)
# Every line mirrors the CURRENT live DOM block of the same type/index.
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-mystery": {
        "title": "১. অয়লার সংখ্যা 'ই' এবং ক্যালকুলাসের অমীমাংসিত প্রশ্ন (The Mystery of e)",
        "audio_file": "sec_01_mystery.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, অয়লার সংখ্যা ই এবং ক্যালকুলাসের অমীমাংসিত প্রশ্ন।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, কে না অবাক হয়েছেন যে ই পাওয়ার এক্স ফাংশনটি নিজের ছাই থেকে পুনর্জন্ম নেওয়া ফিনিক্স পাখির মতো নিজেরই ডেরিভেটিভ? বলেছেন ফ্রাঁসোয়া লে লিওনোয়া।"},
            {"index": 2, "type": "p",
             "tts": "ক্যালকুলাস কোর্সে প্রায় প্রতিটি শিক্ষার্থীকেই একটা অদ্ভুত সংখ্যার সাথে পরিচিত হতে হয়, অয়লারের ধ্রুবক ই, যার মান প্রায় দুই দশমিক সাত এক আট দুই আট। কিন্তু শুরুতেই শিক্ষার্থীদের শেখানো হয় একটা শুষ্ক সূত্র, ই পাওয়ার টি ফাংশনের ডেরিভেটিভ নাকি হুবহু সে নিজেই, আর সূচকে ধ্রুবক কে থাকলে চেইন রুল অনুযায়ী দাঁড়ায় কে গুণ ই পাওয়ার কে টি। গণিত কোনো অন্ধ মুখস্থবিদ্যার নাম নয়। তবে প্রশ্ন হলো, মহাবিশ্বে এমন কোনো চমৎকার সংখ্যা কেন থাকবে যার বক্ররেখার প্রতিটি বিন্দুতে স্পর্শকের ঢাল তার তৎকালীন উচ্চতার হুবহু সমান? ই পাওয়ার টি ফাংশনের পরিবর্তনের হার সে নিজেই, কিন্তু প্রকৃতির এই পরম ভিত্তিটি কেন অন্য কোনো সংখ্যা না হয়ে দুই দশমিক সাত এক আট দুই আট হলো?"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ডি বাই ডি টি অফ ই পাওয়ার টি সমান ই পাওয়ার টি।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, অনুসন্ধানের পথ। এই রহস্য উন্মোচন করতে হলে আমাদের ফিরে যেতে হবে ডেরিভেটিভের একেবারে মৌলিক সংজ্ঞায় এবং পরীক্ষা করতে হবে সাধারণ সূচকীয় ফাংশনগুলোকে, যেমন টু টু দ্য পাওয়ার টি আর সেভেন টু দ্য পাওয়ার টি। প্রথমে সরাসরি ই সংখ্যাটির দিকে না তাকিয়ে টু টু দ্য পাওয়ার টি ফাংশনের মতো একটি সহজ ভিত্তি নিয়ে কাজ করাই হবে বুদ্ধিমানের কাজ। সেখান থেকে ধীরে ধীরে উঠে আসবে সেই বিশেষ ভিত্তিটি, যার জন্য এই অদ্ভুত সুন্দর সত্যটি প্রথমবারের মতো সত্য হয়ে দাঁড়ায়।"},
        ],
    },

    "sec-proportional-growth": {
        "title": "২. Population Mass ও সূচকীয় ডেরিভেটিভ: 2^t থেকে 8^t",
        "audio_file": "sec_02_proportional_growth.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, টু টু দ্য পাওয়ার টি আর এইট টু দ্য পাওয়ার টি ফাংশনের ডেরিভেটিভ।"},
            {"index": 1, "type": "p",
             "tts": "প্রথমে টু টু দ্য পাওয়ার টি ফাংশনটিকে একটু আলাদা চোখে দেখি। ইনপুট টি কে সময়, অর্থাৎ দিন হিসেবে এবং আউটপুট টু টু দ্য পাওয়ার টি কে একদল অতি উর্বর পাই জীবের মোট ভর হিসেবে কল্পনা করি, জনসংখ্যা নয়, কারণ ভর সরলভাবে ক্রমাগত বাড়ে। চিত্রে দেখা যাচ্ছে দিন শূন্যে ভর এক, একদিন পর দুই, দুই দিনে চার, তিন দিনে আট, প্রতিটি স্তম্ভ আগেরটির ঠিক দ্বিগুণ, তাই বৃদ্ধি রেখা সোজা নয়, বরং একটি বক্ররেখা। এখন ডেরিভেটিভ ডি এম বাই ডি টি মানে একই দিনের ভেতরে ভর বৃদ্ধির হার। দিন দুই থেকে তিনে ভর চার থেকে আট হয়, অর্থাৎ যোগ হয় চার, ঠিক সেই দিনের শুরুর ভরের সমান! দিন তিন থেকে চারে যোগ হয় আট, আবার শুরুর ভরের সমান। সাধারণভাবে একটি পূর্ণ দিনের বৃদ্ধি তার শুরুর ভরের সমান, তাই মনে হতে পারে টু টু দ্য পাওয়ার টি ফাংশনের ডেরিভেটিভও সে নিজেই। কিন্তু ডেরিভেটিভের জন্য আমাদের এক পূর্ণ দিন নয়, বরং অতিক্ষুদ্র ডি টি সময়ের ব্যবধান নিয়ে প্রশ্ন করতে হবে, এক দশমাংশ, এক শতাংশ, এক বিলিয়নভাগ দিন।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এম অফ টি সমান টু টু দ্য পাওয়ার টি, আর ডি এম বাই ডি টি সমান, ডি টি শূন্যের দিকে গেলে টু টু দ্য পাওয়ার টি প্লাস ডি টি বিয়োগ টু টু দ্য পাওয়ার টি, ভাগ ডি টির লিমিট।"},
            {"index": 3, "type": "p",
             "tts": "এখানেই সূচকের সবচেয়ে গুরুত্বপূর্ণ ধর্মটি কাজে আসে, টু টু দ্য পাওয়ার টি প্লাস ডি টি সমান টু টু দ্য পাওয়ার টি গুণ টু টু দ্য পাওয়ার ডি টি। যোগজ সূচককে ভাগজ রূপে ভেঙে লবের দুটি পদেই টু টু দ্য পাওয়ার টি পাওয়া যায়, তাই একে সাধারণ উৎপাদক হিসেবে বাইরে নিয়ে আসা যায়। ফলে ডি বাই ডি টি অফ টু টু দ্য পাওয়ার টি সমান টু টু দ্য পাওয়ার টি গুণ, ডি টি শূন্যের দিকে গেলে টু টু দ্য পাওয়ার ডি টি বিয়োগ এক, ভাগ ডি টির লিমিট। অর্থাৎ ডেরিভেটিটি আবার একটি এক্সপোনেনশিয়াল, শুধু একটি ধ্রুবক দিয়ে গুণিত।"},
            {"index": 4, "type": "p",
             "tts": "আশ্চর্যের বিষয় হলো বন্ধনীর ভেতরের অংশে সময়ের চলক টি সম্পূর্ণ অনুপস্থিত, এটি কেবল ডি টির ওপর নির্ভর করে। ডি টি অতি ক্ষুদ্র হলে এর মান দাঁড়ায় প্রায় শূন্য দশমিক ছয় নয় তিন, যা লন টু নামে পরিচিত। একই হিসাবে ভিত্তি তিনের জন্য ধ্রুবক প্রায় এক দশমিক শূন্য নয় আট, আর ভিত্তি আটের জন্য প্রায় দুই দশমিক শূন্য সাত নয়, ঠিক শূন্য দশমিক ছয় নয় তিনের তিনগুণ! চিত্রে স্পর্শক আর উচ্চতা পাশাপাশি তাকালে দেখা যায়, ভিত্তি দুইয়ের ক্ষেত্রে বক্ররেখার যেকোনো বিন্দুতে প্রকৃত ডেরিভেটিভ আউটপুটের চেয়ে কিছুটা ছোট, কারণ গুণকটি একের চেয়ে কম।"},
            {"index": 5, "type": "callout", "role": "conclusion",
             "tts": "বিশেষ নোট, মাইলফলক, ধ্রুবকটির সন্ধান। ভিত্তি দুইয়ের সমানুপাতিক ধ্রুবক শূন্য দশমিক ছয় নয় তিন, যা একের চেয়ে ছোট, আর ভিত্তি তিনের এক দশমিক শূন্য নয় আট, যা একের চেয়ে বড়। সুতরাং দুই ও তিনের মাঝে অবশ্যই এমন একটি ভিত্তি আছে যার সমানুপাতিক ধ্রুবক ঠিক এক, সেই ভিত্তিটিই হলো অয়লারের সংখ্যা ই। বন্ধনীর মান বের করতে ডি টিতে খুব ছোট সংখ্যা বসিয়ে ক্যালকুলেটরে হিসাব করলেই শূন্য দশমিক ছয় নয় তিন ফিরে আসে, এই ছোট্ট উন্মোচনটিই পুরো রহস্যের চাবিকাঠি।"},
        ],
    },

    "sec-compound-interest": {
        "title": "৩. বার্নোলির চক্রবৃদ্ধি সুদ ও অবিচ্ছিন্ন সীমা (Bernoulli's Compound Interest)",
        "audio_file": "sec_03_compound_interest.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, বার্নোলির ব্যাংক সুদ ও অবিচ্ছিন্ন চক্রবৃদ্ধি।"},
            {"index": 1, "type": "p",
             "tts": "এই রহস্যময় ধ্রুবকের উৎপত্তি লক্ষ্য করা যায় ১৬৮৩ সালে জ্যাকব বার্নোলির একটি চক্রবৃদ্ধি সুদের চিন্তন পরীক্ষায়। কল্পনা করুন একটি ব্যাংক বার্ষিক একশত শতাংশ সুদের অফার দিল এবং মূলধন ঠিক এক ডলার। প্রশ্ন হলো, বছর শেষে কত টাকা পাওয়া যাবে, যদি সুদকে বারবার ভাগ করে ক্রমাগত যোগ করা হয়?"},
            {"index": 2, "type": "p",
             "tts": "বছরে একবার চক্রবৃদ্ধি করলে পাওয়া যায় দুই ডলার, দুইবার করলে দুই দশমিক দুই পাঁচ ডলার, চারবার অর্থাৎ ত্রৈমাসিক করলে প্রায় দুই দশমিক চার চার এক চার ডলার, আর বারোবার অর্থাৎ মাসিক করলে প্রায় দুই দশমিক ছয় এক তিন ডলার। প্রতিবার ভাগ বাড়ানোর সাথে সাথে অর্থের পরিমাণও বাড়ছে, কিন্তু কি কখনো অসীমে পৌঁছাবে?"},
            {"index": 3, "type": "p",
             "tts": "প্রতিদিন চক্রবৃদ্ধি করলে মেলে প্রায় দুই দশমিক সাত এক চার পাঁচ ডলার, প্রতি ঘণ্টা, প্রতি মিনিট বা প্রতি ন্যানোসেকেন্ডে করলেও সংখ্যাটি আর বেশি বাড়ে না। চিত্রে দেখা যাচ্ছে বক্ররেখাটি নিচ থেকে ধীরে ধীরে সীমারেখার কাছে এসে পৌঁছাচ্ছে, কখনোই তার ওপরে যাচ্ছে না। এটি এক নির্দিষ্ট সীমায় এসে থিতু হয়, হয়ে ওঠে সেই বিখ্যাত সংখ্যা যাকে আমরা অয়লারের সংখ্যা বলি। এই অবিচ্ছিন্ন সীমাটিই আসলে ই সংখ্যার যোগবিহীন ও আবিষ্কারমূলক সংজ্ঞা।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ই সমান, এন অসীমের দিকে গেলে এক প্লাস এক বাই এন, হোল টু দ্য পাওয়ার এনের লিমিট, যার মান প্রায় দুই দশমিক সাত এক আট দুই আট এক আট দুই আট।"},
            {"index": 5, "type": "callout", "role": "conclusion",
             "tts": "বিশেষ নোট, প্রকৃতির গতিসীমা। অবিরাম প্রতি মুহূর্তে চক্রবৃদ্ধি করলেও অর্থ কখনোই বিস্ফোরিত হয়ে অসীমে যায় না, বরং এটি মহাবিশ্বের এক অনন্য গাণিতিক সীমায় থিতু হয়, অয়লার সংখ্যা ই। এই একই সীমা পরে এক্সপোনেনশিয়াল ফাংশনের ডেরিভেটিভের ক্ষেত্রেও ফিরে আসে, যা দেখায় যে ব্যাংকিং হিসাব আর ক্যালকুলাসের ঢাল একই গাণিতিক বস্তুর দুটি ভিন্ন মুখ।"},
        ],
    },

    "sec-chain-rule-growth": {
        "title": "৪. চেইন রুল ও অবিচ্ছিন্ন মডেলিং d/dt(e^(kt)) = k e^(kt) (The Universal Growth Formula)",
        "audio_file": "sec_04_chain_rule_growth.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, চেইন রুল, প্রাকৃতিক লগ ও ই পাওয়ার কে টির মহিমা।"},
            {"index": 1, "type": "p",
             "tts": "বাস্তব জগতে বৃদ্ধির হার সবসময় একশত শতাংশ হয় না, হতে পারে শতকরা পাঁচ ভাগ কিংবা পঞ্চাশ ভাগ। যদি কোনো ব্যবস্থার অবিচ্ছিন্ন শতকরা হার হয় কে, তবে এন ভাগে ভাগ করে অবিচ্ছিন্ন সীমা নিলে টি সময় পর তার রূপ হয় ই পাওয়ার কে টি। আর ই পাওয়ার সি টি ফর্মটিই প্রাকৃতিক প্রক্রিয়ার সার্বজনীন ভাষা, জনসংখ্যা বৃদ্ধি, গরম পানির ঠান্ডা হওয়া, অর্থাৎ নিউটনের সূত্রে তাপমাত্রার পার্থক্যের হার সেই পার্থক্যের সমানুপাতিক, এবং ব্যাংকে টাকার চক্রবৃদ্ধি, এই তিনটিতেই কোনো একটির পরিবর্তনের হার তার বর্তমান পরিমাণের সমানুপাতিক।"},
            {"index": 2, "type": "formula-box",
             "tts": "চেইন রুল সমীকরণ, ডি বাই ডি টি অফ ই পাওয়ার কে টি সমান কে গুণ ই পাওয়ার কে টি।"},
            {"index": 3, "type": "p",
             "tts": "চেইন রুল অনুযায়ী ভেতরের ফাংশন ইউ সমান কে টির ডেরিভেটিভ কে সামনে এসে গুণ হয়, অর্থাৎ এখানে কে হলো সরাসরি অবিচ্ছিন্ন শতকরা বৃদ্ধির হার। তাই ডি এন বাই ডি টি সমান কে গুণ এন রূপের যেকোনো ডিফারেনশিয়াল সমীকরণের সমাধান হলো, এন অফ টি সমান এন শূন্য গুণ ই পাওয়ার কে টি। ব্যাকটেরিয়ার বংশবৃদ্ধি, তেজস্ক্রিয় পরমাণুর ক্ষয়, মহামারীর বিস্তার কিংবা ব্যাংক ব্যালেন্স, সবখানেই অয়লারের সংখ্যা ই স্বয়ংক্রিয়ভাবে প্রধান চরিত্র হয়ে ওঠে।"},
            {"index": 4, "type": "p",
             "tts": "ভিন্ন ভিত্তিগুলো আসলে একে অপরের অনুভূমিকভাবে স্কেল করা রূপ, যেমন টু পাওয়ার এক্স সমান ফোর পাওয়ার এক্স বাই টু। চিত্রে দেখা যাচ্ছে দুটি বক্ররেখা একই রেখার ওপর চাপ দিয়ে আছে, ভিত্তি বদলে শুধু অনুভূমিক স্কেলিং হয়, আকার বদলায় না। একইভাবে ই পাওয়ার সি গুণ টি সমান টু পাওয়ার টি লেখা যায় যখন সি প্রায় শূন্য দশমিক ছয় নয় তিন, অর্থাৎ ই পাওয়ার শূন্য দশমিক ছয় নয় তিন গুণ টি সমান টু পাওয়ার টি। এই সি চলকটি ঠিক সেই রহস্যময় ধ্রুবক, যা লেখা হয় লন টু। সাধারণভাবে থ্রি পাওয়ার টি সমান ই পাওয়ার লন থ্রি গুণ টি, যেখানে লন থ্রি প্রায় এক দশমিক শূন্য নয় আট, আর যেকোনো ভিত্তির জন্য ডি বাই ডি টি অফ এ পাওয়ার টি সমান এ পাওয়ার টি গুণ লন এ। প্রতিটি ভিত্তির সাথে একটি করে প্রাকৃতিক লগ যুক্ত, এই বোঝাপড়াটিই রহস্যময় ধ্রুবকগুলোর পর্দা উন্মোচন করে।"},
            {"index": 5, "type": "callout", "role": "conclusion",
             "tts": "বিশেষ নোট, চূড়ান্ত দর্শন। চিত্রে ই পাওয়ার টি বক্ররেখার তিনটি বিন্দুতে আঁকা স্পর্শক দেখে বুঝতে পারি, প্রতিটি ক্ষেত্রেই স্পর্শকের ঢাল তার বিন্দুর উচ্চতার হুবহু সমান, আর ছোট ত্রিভুজগুলো দেখায় যে ঢাল আর উচ্চতার অনুপাত ঠিক এক। অয়লার সংখ্যা ই মানুষের চাপিয়ে দেওয়া কোনো কৃত্রিম ধ্রুবক নয়, এটি মসৃণ, অবিচ্ছিন্ন পরিবর্তনের নিখুঁত প্রাকৃতিক ভাষা। সব এক্সপোনেনশিয়াল নিজের ডেরিভেটিভের সমানুপাতিক, কিন্তু শুধু ই ভিত্তিক ফাংশনটির ক্ষেত্রেই সেই সমানুপাতিক ধ্রুবক ঠিক এক, তাই ডি বাই ডি টি অফ ই পাওয়ার টি সমান ই পাওয়ার টি। যেকোনো এ পাওয়ার টি কে ই পাওয়ার সি টি আকারে লিখলে ডেরিভেটিভ নেওয়া সহজ হয়, আর সি চলকটি তখন সরাসরি বোঝায় পরিবর্তনের তাৎক্ষণিক শতকরা হার।"},
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
    if total != 23:
        raise ValueError(f"Expected 23 cues, found {total}")

    # Figure cues must be genuine 2-4 sentence explanations (none in this lesson,
    # but the guard is kept for the gold standard).
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
        "lesson": "lesson_05",
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
    assert total_cues == 23

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Calculus Lesson 05")
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
