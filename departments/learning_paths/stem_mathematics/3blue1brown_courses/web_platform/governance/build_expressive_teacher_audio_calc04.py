# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Calculus Lesson 04
("Visualizing the Chain Rule and Product Rule", Bengali) to the Lesson-01/02 gold standard.

Deterministic, re-runnable, self-contained:
  * 34 cues in 4 narrated sections with EXACTLY the same section IDs, alias keys,
    audio_file names, cue types and cue order as the existing manifest.
  * Source of truth: narration_engine.js DOM selector
        sections -> '.article > section, article section'  (data-no-narration skipped)
        blocks   -> 'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
                     .code-showcase, .formula-box'
    The rendered DOM is driven by <b1b-article>/<b1b-section>/<b1b-quote>/
    <b1b-callout>/<b1b-figure>/<b1b-formula> components; the figure/formula TeX
    (KaTeX <annotation encoding="application/x-tex"> / math= / caption=) was used
    to make every spoken formula phonetically accurate.
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Figure cues are genuine 2-4 sentence natural explanations — never the
    artificial label "চিত্র প্রদর্শনী".
  * Every script is clean spoken Bengali with phonetic safeguards:
    x -> এক্স, x^2 -> এক্স স্কয়ার, dx -> ডি এক্স, df -> ডি এফ,
    dg -> ডি জি, dh -> ডি এইচ, f -> এফ, g -> জি, h -> এইচ,
    sin -> সাইন, cos -> কোসাইন, f' -> এফ প্রাইম, etc.
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

Usage:  python governance/build_expressive_teacher_audio_calc04.py
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
                         "calculus", "lesson_04")
MANIFEST_TITLE = "অধ্যায় ০৪ — চেইন রুল ও প্রোডাক্ট রুলের চাক্ষুষ রূপ (Visualizing the Chain Rule and Product Rule)"

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
# Derived 1:1 from the rendered DOM (media tabs / quizzes are not narrated).
EXPECTED_TYPES = {
    "sec-product-intro":      ["h2", "chapter-quote", "p", "p", "callout", "p"],
    "sec-rectangle-geometry": ["h2", "p", "figure", "p", "p", "callout",
                               "formula-box", "p", "p", "formula-box", "p"],
    "sec-chain-intro":        ["h2", "p", "p", "figure", "p", "callout",
                               "formula-box", "p", "p"],
    "sec-gears-examples":     ["h2", "chapter-quote", "p", "figure", "p",
                               "formula-box", "callout", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-product-intro":      "sec_01_product_intro.mp3",
    "sec-rectangle-geometry": "sec_02_rectangle_geometry.mp3",
    "sec-chain-intro":        "sec_03_chain_rule.mp3",
    "sec-gears-examples":     "sec_04_gears_examples.mp3",
}
# Canonical DOM section id -> legacy alias key kept in the manifest.
ALIASES = {
    "sec-product-intro":      "sec_01_product_intro",
    "sec-rectangle-geometry": "sec_02_rectangle_geometry",
    "sec-chain-intro":        "sec_03_chain_rule",
    "sec-gears-examples":     "sec_04_gears_examples",
}
EXPECTED_TITLES = {
    "sec-product-intro":      "১. প্রোডাক্ট রুল ও সাধারণ ভুল ধারণা (The Product Rule & Common Misconceptions)",
    "sec-rectangle-geometry": "২. আয়তক্ষেত্রের বৃদ্ধি ও প্রোডাক্ট রুলের জ্যামিতিক প্রমাণ (Geometric Proof via Rectangle Expansion)",
    "sec-chain-intro":        "৩. চেইন রুল ও তিনটি সংখ্যা রেখা (The Chain Rule & Three Number Lines)",
    "sec-gears-examples":     "৪. গিয়ার অ্যানালজি ও সমন্বিত প্রয়োগ (Gear Ratio Analogy & Real Examples)",
}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (34 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-product-intro": {
        "title": EXPECTED_TITLES["sec-product-intro"],
        "audio_file": "sec_01_product_intro.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, প্রোডাক্ট রুল ও গুণফলের অন্তরজের সাধারণ বিভ্রান্তি।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, চেইন রুল ব্যবহার করা পেঁয়াজের খোসা ছাড়ানোর মতো, একবারে এক স্তর মোকাবেলা করতে হয়, আর পেঁয়াজটি বড় হলে চোখে পানি আসতে থাকে। বলেছেন অজ্ঞাতনামা অধ্যাপক।"},
            {"index": 2, "type": "p",
             "tts": "আগের ভিডিওগুলোতে আমরা সরল ফাংশনের ডেরিভেটিভ নিয়ে কথা বলেছি, যেমন এক্স এর ঘাত, সাইন অফ এক্স আর সূচক ফাংশন। লক্ষ্য ছিল এই সূত্রগুলোর পেছনে একটা পরিচ্ছন্ন ছবি মনে রাখা। কিন্তু বাস্তব জগৎকে মডেল করতে ব্যবহৃত বেশিরভাগ ফাংশনই এই সরল ধাপগুলোকে মিশিয়ে, গুণ করে বা একটির ভেতরে আরেকটিকে ঢুকিয়ে তৈরি। তাই আজকের প্রশ্ন, দুটি ফাংশনের ডেরিভেটিভ জানা থাকলে তাদের যোগফল, গুণফল ও সংযোজন, এই তিনটি মিশ্রণের ডেরিভেটিভ কী হবে।"},
            {"index": 3, "type": "p",
             "tts": "সবচেয়ে সহজ হলো যোগের নিয়ম, দুটি ফাংশনের যোগফলের ডেরিভেটিভ হলো তাদের ডেরিভেটিভের যোগফল। ধরা যাক, এফ অফ এক্স সমান সাইন অফ এক্স প্লাস এক্স স্কয়ার। প্রতি ইনপুটে সাইনের মানের সাথে এক্স স্কয়ারের মান যোগ করা হচ্ছে। এক্স সমান দশমিক পাঁচ থেকে শুরু করে কিছুটা এগিয়ে নিলে এফ এর যে পরিবর্তন ডি এফ ঘটে, তা আসলে সাইন বক্রের পরিবর্তন আর পরাবৃত্তের পরিবর্তন, এই দুটির যোগফল। সাইনের ডেরিভেটিভ কোসাইন আর এক্স স্কয়ারের ডেরিভেটিভ দুই এক্স হওয়ায় ডি এফ বাই ডি এক্স সমান কোসাইন অফ এক্স প্লাস দুই এক্স।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, সতর্কবার্তা, গুণনের সাধারণ বিভ্রান্তি। যোগের নিয়ম দেখে মনে হতে পারে গুণফলের ক্ষেত্রেও একই রকম প্রতিসম সূত্র চলে আসবে, এফ প্রাইম গুণ জি প্রাইম। কিন্তু এটি ক্যালকুলাসের সবচেয়ে বিপজ্জনক ফাঁদ। উদাহরণস্বরূপ এফ অফ এক্স সমান এক্স ও জি অফ এক্স সমান এক্স নিলে গুণফল এক্স স্কয়ার, যার ডেরিভেটিভ দুই এক্স, অথচ ভুল নিয়মে পাওয়া যাবে এক গুণ এক, অর্থাৎ এক। সুতরাং গুণফলের অন্তরজ কখনোই শুধু অন্তরজ দুটির গুণফল নয়, এর পেছনে আছে একটা জ্যামিতিক গল্প।"},
            {"index": 5, "type": "p", "role": "conclusion",
             "tts": "পাঠ্যবইয়ে প্রোডাক্ট রুল মুখস্থ করার কথা বলা হয়, বাম গুণ ডানের ডেরিভেটিভ, যোগ ডান গুণ বামের ডেরিভেটিভ। কিন্তু কেন এই অদ্ভুত অপ্রতিসম সূত্র? এর উত্তর পেতে হলে বক্ররেখা ছেড়ে আয়তক্ষেত্রের দিকে যেতে হবে। গুণফলকে ক্ষেত্রফল হিসেবে দেখলে ওই দুটি পদ কেবল দুটি সরু ফালির ক্ষেত্রফল ছাড়া আর কিছু নয়। পরবর্তী পরিচ্ছেদে ঠিক সেটাই আমরা দেখব।"},
        ],
    },

    "sec-rectangle-geometry": {
        "title": EXPECTED_TITLES["sec-rectangle-geometry"],
        "audio_file": "sec_02_rectangle_geometry.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, আয়তক্ষেত্রের সম্প্রসারণ ও প্রোডাক্ট রুলের প্রমাণ।"},
            {"index": 1, "type": "p",
             "tts": "দুটি রাশির গুণফল বোঝার সবচেয়ে প্রাকৃতিক উপায় হলো একটি আয়তক্ষেত্র কল্পনা করা। সাইন অফ এক্স গুণ এক্স স্কয়ার ফাংশনের ক্ষেত্রে ধরা যাক একটি আয়তক্ষেত্র, যার উপরের বাহু সাইন অফ এক্স আর উচ্চতা এক্স স্কয়ার, তাহলে এফ অফ এক্স হলো ঐ বক্সের মোট ক্ষেত্রফল। যেহেতু এরা ফাংশন, তাই এক্স বদলালে বাহু দুটিও বদলাবে। এক্স বাড়লে সাইন অফ এক্স প্রথমে এক পর্যন্ত বাড়ে, তারপর নামতে থাকে, আর এক্স স্কয়ার ক্রমাগত লম্বা হয়। এই অ্যাডজাস্টেবল বক্সটিই প্রোডাক্ট রুলের চাবিকাঠি।"},
            {"index": 2, "type": "figure",
             "tts": "এই আয়তক্ষেত্রের উপরের বাহু সাইন অফ এক্স আর ডান বাহু এক্স স্কয়ার, আর এর ক্ষেত্রফলই আমাদের ফাংশন এফ অফ এক্স। যখন এক্স এর সাথে সাইন অফ এক্স কে টেনে বাড়ানো হয়, দেখা যায় এটি এক পর্যন্ত উঠে আবার নামে, আর ডান বাহু ক্রমশ লম্বা হয়। বক্ররেখার বদলে এই বক্স ব্যবহার করার কারণ হলো গুণফলের ছোট পরিবর্তনগুলো ক্ষেত্রফল হিসেবে সরাসরি আঁকা যায়। মনে রাখবেন বাহু দুটো স্বাধীন নয়, দুটোই একই এক্স এর ওপর নির্ভরশীল।"},
            {"index": 3, "type": "p",
             "tts": "এবার ইনপুট এক্স কে সামান্য ডি এক্স পরিমাণ বাড়ানো যাক। এর ফলে প্রস্থের পরিবর্তন ডি অফ সাইন অফ এক্স আর উচ্চতার পরিবর্তন ডি অফ এক্স স্কয়ার, দুটোই খুব ছোট, কিন্তু শূন্য নয়। আগের অধ্যায়ের এক্স স্কয়ার চিত্রের সাথে মিল রেখে মনে রাখবেন এখানে মোটা করে আঁকা ফালিগুলো আসলে অতি ক্ষুদ্র, ছবির সুবিধার্থেই এত বড় দেখানো হয়েছে। নতুন ক্ষেত্রফলের পুরোটাই এই দুই ছোট বাহুর বৃদ্ধি থেকে আসে।"},
            {"index": 4, "type": "p",
             "tts": "নতুন ক্ষেত্রফলটি ভেঙে দেখলে তিনটি অংশ পাওয়া যায়। নিচের সরু আয়তক্ষেত্রটি সাইন অফ এক্স গুণ ডি অফ এক্স স্কয়ার, ডানপাশের খাড়া ফালিটি এক্স স্কয়ার গুণ ডি অফ সাইন অফ এক্স, আর ওপরের ডান কোণার ছোট্ট বর্গটি ডি অফ সাইন অফ এক্স গুণ ডি অফ এক্স স্কয়ার। প্রথম দুটি ফালি আমাদের পরিচিত, একটি বাহু স্থির রেখে অন্য বাহুর প্রসারণ। তৃতীয়টি কিন্তু দুটি অতিক্ষুদ্রের গুণফল, তাই ডি এক্স শূন্যের দিকে গেলে সেটি ফালি দুটির তুলনায় সীমাহীন ছোট হয়ে বিলীন হয়ে যায়।"},
            {"index": 5, "type": "callout",
             "tts": "বিশেষ নোট, মনে রাখার কৌশল, বাঁয়ে ডান আর ডানে বাঁ, ও সাধারণ প্রোডাক্ট রুল। এই ছবিটিই ব্যাখ্যা করে থ্রি ব্লু ওয়ান ব্রাউনের বিখ্যাত শব্দ কৌশল, বাঁয়ে ডান আর ডানে বাঁ। সাইন অফ এক্স গুণ এক্স স্কয়ারে বাঁয়ে ডান মানে বাঁ পাশের সাইন অফ এক্স কে গুণ করতে হবে ডান পাশের এক্স স্কয়ারের ডেরিভেটিভ দুই এক্স দিয়ে, আর ডানে বাঁ মানে ডান পাশের এক্স স্কয়ার কে গুণ করতে হবে বাঁ পাশের সাইন অফ এক্সের ডেরিভেটিভ কোসাইন অফ এক্স দিয়ে। জ্যামিতিকভাবে প্রথম পদটি নিচের ফালির ক্ষেত্রফল, দ্বিতীয় পদটি ডান ফালির ক্ষেত্রফল। যেকোনো দুটি ফাংশনের জন্য লেখা যায়, জি গুণ এইচের ডেরিভেটিভ সমান জি প্রাইম গুণ এইচ প্লাস জি গুণ এইচ প্রাইম, অর্থাৎ বাঁ গুণ ডানের অন্তরজ, যোগ ডান গুণ বাঁয়ের অন্তরজ।"},
            {"index": 6, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ডি অফ এফ জি সমান এফ ডি জি প্লাস জি ডি এফ প্লাস ডি এফ গুণ ডি জি।"},
            {"index": 7, "type": "p",
             "tts": "এখন পুরো সমীকরণটিকে ডি এক্স দিয়ে ভাগ করা যাক। প্রথম পদ হয় এফ গুণ ডি জি বাই ডি এক্স, দ্বিতীয় পদ জি গুণ ডি এফ বাই ডি এক্স, এগুলো পরিচিত। কিন্তু কোণার পদটি দাঁড়ায় ডি এফ গুণ ডি জি ভাগ ডি এক্স, অর্থাৎ ডি এফ বাই ডি এক্স গুণ ডি জি। এখানে ডি এফ বাই ডি এক্স একটি সসীম সংখ্যা, কিন্তু ডি জি নিজেই ডি এক্স এর সাথে শূন্যের দিকে ধাবিত হয়। তাই এই পদটি শূন্যে মিলিয়ে যায়, কোনো কৃত্রিম বাদ দেওয়া নয়, বরং সীমার স্বাভাবিক ফলাফল।"},
            {"index": 8, "type": "p",
             "tts": "ডি এক্স যত শূন্যের কাছে আসবে, ডি অফ সাইন অফ এক্স আর ডি অফ এক্স স্কয়ার ততই ছোট হবে। ফলে তাদের গুণফল ফালি দুটির চেয়ে অনেক বেশি দ্রুত কমবে। পাশের ভিডিও চিত্রে ডি এক্স ক্রমশ ছোট করে দেখানো হয়েছে কীভাবে কোণার টুকরোটি অদৃশ্য হয়ে যায় আর কেবল দুটি সরু ফালিই অবশিষ্ট থাকে। এই কারণেই প্রোডাক্ট রুলে কেবল দুটি পদ থাকে, তৃতীয় পদটির অস্তিত্ব ছিল ছবি আঁকার সুবিধার্থে মাত্র।"},
            {"index": 9, "type": "formula-box",
             "tts": "চূড়ান্ত প্রোডাক্ট রুল, ডি বাই ডি এক্স অফ এফ অফ এক্স গুণ জি অফ এক্স সমান এফ অফ এক্স গুণ জি প্রাইম অফ এক্স প্লাস জি অফ এক্স গুণ এফ প্রাইম অফ এক্স।"},
            {"index": 10, "type": "p", "role": "conclusion",
             "tts": "অতএব মুখস্থ করার কোনো প্রয়োজন নেই। একটি বাহু স্থির রেখে অন্য বাহুর প্রসারণই দুটি আয়তাকার ফালি তৈরি করে, আর সেই ফালি দুটিই প্রোডাক্ট রুলের দুটি পদ। একই চিন্তা ত্রিমাত্রিক ঘনকেও প্রয়োগ করা যায়, তিনটি ফাংশনের গুণফল কে আয়তন হিসেবে দেখলে বাহু বাড়ালে তিনটি মূল তল বৃদ্ধি পায়, আর ডি বাই ডি এক্স অফ এফ জি এইচ সমান এফ প্রাইম জি এইচ প্লাস এফ জি প্রাইম এইচ প্লাস এফ জি এইচ প্রাইম।"},
        ],
    },

    "sec-chain-intro": {
        "title": EXPECTED_TITLES["sec-chain-intro"],
        "audio_file": "sec_03_chain_rule.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, চেইন রুল ও তিনটি সংখ্যা রেখা।"},
            {"index": 1, "type": "p",
             "tts": "যোগ ও গুণ ছাড়া ফাংশন মিশ্রণের তৃতীয় প্রধান উপায় হলো সংযোজন, একটি ফাংশনের ফলাফল সরাসরি আরেকটির ভেতরে ইনপুট হিসেবে পাঠানো। উদাহরণস্বরূপ এক্স স্কয়ার কে সাইন অফ এক্সের ভেতরে ঢুকিয়ে পাই নতুন ফাংশন সাইন অফ এক্স স্কয়ার, ভেতরের ফাংশন জি অফ এক্স সমান এক্স স্কয়ার, বাইরের ফাংশন এফ অফ জি সমান সাইন অফ জি। প্রশ্ন হলো, এই নতুন ফাংশনের ডেরিভেটিভ কী? এখানে আমরা আরেকটি ভিন্ন দৃশ্য বেছে নেব, লেখচিত্রের বদলে তিনটি সমান্তরাল সংখ্যা রেখা।"},
            {"index": 2, "type": "p",
             "tts": "প্রথম রেখায় বসবে এক্স, দ্বিতীয় রেখায় এক্স স্কয়ার, আর তৃতীয় রেখায় সাইন অফ এক্স স্কয়ার। এক্স স্কয়ার ফাংশনটি প্রথম রেখা থেকে দ্বিতীয় রেখায় নিয়ে যায়, আর সাইন দ্বিতীয় থেকে তৃতীয় রেখায়। এক্স সমান দশমিক পাঁচ দেখানো হয়েছে, দ্বিতীয় রেখায় এক্স স্কয়ার সমান দশমিক দুই পাঁচ, আর তৃতীয় রেখায় সাইন অফ দশমিক দুই পাঁচ প্রায় দশমিক দুই চার সাত। এক্স কে বদলে তিন করলে দ্বিতীয় রেখায় নয় আর তৃতীয় রেখায় সাইন অফ নয়, এই ভাবে এক রেখা থেকে পরের রেখায় মান প্রবাহিত হয়।"},
            {"index": 3, "type": "figure",
             "tts": "এই চিত্রে তিনটি সমান্তরাল সংখ্যারেখা দেখানো হয়েছে, উপরে এক্স, মাঝখানে এক্স স্কয়ার, নিচে সাইন অফ এক্স স্কয়ার। এক্স সমান দশমিক পাঁচ বিন্দু থেকে শুরু করে ভেতরের ফাংশন এক্স স্কয়ার সেটিকে দশমিক দুই পাঁচে পাঠায়, আর সাইন সেই দশমিক দুই পাঁচ কে দশমিক দুই চার সাতে রূপ দেয়। রেখা তিনটির মাঝে আঁকা ধনুক রেখাগুলো দেখায় কোন মান কোন ধাপে রূপান্তরিত হচ্ছে। এই দৃশ্যটি মনে রাখলে ফাংশনের ভেতরে ফাংশন ধারণাটি আর বিমূর্ত থাকে না, এটি হয়ে যায় এক প্রবাহিত যাত্রা।"},
            {"index": 4, "type": "p",
             "tts": "ডেরিভেটিভের জন্য আবার সেই পুরনো কৌশল, এক্স কে সামান্য ডি এক্স ধাক্কা দেওয়া। মানসিক ছবির জন্য এক্স সমান এক দশমিক পাঁচ আর ডি এক্স প্রায় দশমিক এক ধরা যাক। প্রথম রেখার এই ছোট সরণ দ্বিতীয় রেখায় ডি অফ এক্স স্কয়ার পরিমাণ সরণ ঘটায়, যা আমরা জানি দুই এক্স গুণ ডি এক্স। এখন এক ধাপ এগিয়ে এই এক্স স্কয়ার কে একটি নতুন নাম এইচ দেওয়া যাক, তাহলে দ্বিতীয় রেখার সরণটি হলো ডি এইচ। নাম বদলালে সমস্যা সহজ হয়, কারণ এখন আমরা শুধু বলছি এইচ এর ওপর ভিত্তি করে সাইন অফ এইচ কতটা নড়ছে।"},
            {"index": 5, "type": "callout",
             "tts": "বিশেষ নোট, চেইন বিক্রিয়ার চাবিকাঠি, ডি এইচ ই পরবর্তী ফাংশনের ইনপুট। এখানেই চেইন রুলের হৃদয়স্পন্দন, এইচ রেখার এই অতিক্ষুদ্র সরণ ডি এইচ সরাসরি পরবর্তী সাইন অফ এইচ ফাংশনের ইনপুট বৃদ্ধি হিসেবে কাজ করে। সাইনের ডেরিভেটিভ কোসাইন হওয়ায় তৃতীয় রেখার পরিবর্তন ডি অফ সাইন অফ এইচ সমান কোসাইন অফ এইচ গুণ ডি এইচ। ছবিতে সাইন অফ এইচ বাঁ দিকে সরে আর ডি এইচ ডান দিকে, এর মানে ডি অফ সাইন অফ এইচ একটি ঋণাত্মক সংখ্যা, ঠিক যেমন কোসাইন অফ এক দশমিক পাঁচের বর্গের চিহ্ন হওয়া উচিত। এই ডি এইচ কে এখন ডি অফ এক্স স্কয়ার দিয়ে প্রতিস্থাপন করলেই সব রেখা একসঙ্গে যুক্ত হয়ে যায়।"},
            {"index": 6, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ডি এফ সমান এফ প্রাইম অফ জি গুণ জি প্রাইম অফ এক্স গুণ ডি এক্স। আর ডি এফ বাই ডি এক্স সমান ডি এফ বাই ডি জি গুণ ডি জি বাই ডি এক্স।"},
            {"index": 7, "type": "p",
             "tts": "উভয়পক্ষকে ডি এক্স দিয়ে ভাগ করলেই লাইবনিজের অমর চেইন রুল পাওয়া যায়, ডি এফ বাই ডি এক্স সমান ডি এফ বাই ডি এইচ গুণ ডি এইচ বাই ডি এক্স। লেখচিত্রে দেখতে মনে হয় মাঝখানের ডি এইচ দুটি সাধারণ ভগ্নাংশের মতো কাটাকাটি গিয়ে গেল, কিন্তু এটি কেবল কাকতালীয় নয়। আসলে প্রতিটি অনুপাতই ক্ষুদ্রাতিক্ষুদ্র পরিবর্তনের অনুপাত, আর এইচ সেই মধ্যবর্তী ভাষা যার মাধ্যমে এক্স এর ধাক্কা শেষ পর্যন্ত এফ এ পৌঁছায়।"},
            {"index": 8, "type": "p", "role": "conclusion",
             "tts": "সুতরাং ডি বাই ডি এক্স অফ সাইন অফ এক্স স্কয়ার সমান কোসাইন অফ এক্স স্কয়ার গুণ দুই এক্স, বাইরের ফাংশনের ডেরিভেটিভ ভেতরের ফাংশনটিকে অপরিবর্তিত রেখে তার ওপর প্রয়োগ করা হচ্ছে, আর সেই ফলাকে গুণ করা হচ্ছে ভেতরের ফাংশনের ডেরিভেটিভ দিয়ে। একই যুক্তি যেকোনো জোড়া ফাংশনের জন্য চলে, ডি বাই ডি এক্স অফ জি অফ এইচ অফ এক্স সমান জি প্রাইম অফ এইচ অফ এক্স গুণ এইচ প্রাইম অফ এক্স। ডি এইচ এর এই বাতিল হওয়া কেবল চিহ্নের খেলা নয়, এটি ক্যালকুলাসের আঁতাতে ছোট ধাক্কাগুলোর বাস্তব ধারাবাহিকতার প্রতিফলন।"},
        ],
    },

    "sec-gears-examples": {
        "title": EXPECTED_TITLES["sec-gears-examples"],
        "audio_file": "sec_04_gears_examples.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, গিয়ার রূপক ও বাস্তব গাণিতিক প্রয়োগ।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, প্রথম গিয়ার যদি দ্বিতীয় গিয়ার কে দ্বিগুণ গতিতে ঘোরায় এবং দ্বিতীয় গিয়ার যদি তৃতীয় গিয়ার কে তিনগুণ গতিতে ঘোরায়, তবে প্রথম গিয়ারের সাপেক্ষে তৃতীয় গিয়ার ঘুরবে দুই গুণ তিন, অর্থাৎ ছয় গুণ দ্রুত। এটি বলা হয়েছে যান্ত্রিক অ্যানালজি হিসেবে।"},
            {"index": 2, "type": "p",
             "tts": "চেইন রুলকে বাস্তবে অনুভব করার সবচেয়ে রোমাঞ্চকর উদাহরণ পরস্পরের সাথে যুক্ত তিনটি দাঁতযুক্ত গিয়ার চাকা। প্রথম গিয়ার এক পাক ঘুরলে দ্বিতীয় গিয়ার দুই পাক ঘোরে, অর্থাৎ ডি বি বাই ডি এ সমান দুই। আবার দ্বিতীয় গিয়ার এক পাক ঘুরলে তৃতীয় গিয়ার তিন পাক ঘোরে, অর্থাৎ ডি সি বাই ডি বি সমান তিন। তাহলে প্রথম গিয়ার এক পাক ঘুরলে তৃতীয় গিয়ার ঘুরবে দুই গুণ তিন, অর্থাৎ ছয় পাক। চেইন রুল মূলত এই বিবর্ধন গুণকগুলোর গুণ ছাড়া আর কিছু নয়, প্রতিটি ডেরিভেটিভ এক একটি গিয়ার অনুপাত, আর ধাপগুলোর সংখ্যা যত বাড়ে, সামগ্রিক সংবেদনশীলতা তত গুণ হয়।"},
            {"index": 3, "type": "figure",
             "tts": "এই চিত্রে ডি এফ বাই ডি এইচ আর ডি এইচ বাই ডি এক্স পাশাপাশি লেখা আছে, আর মাঝখানের ডি এইচ দুটি কাটাকাটি করে ডি এফ বাই ডি এক্স তৈরি করছে। গিয়ারের মতোই প্রতিটি অনুপাত এক ধাপের বিবর্ধন গুণক, প্রথমে এক্স এর ধাক্কা এইচ এ, তারপর এইচ এর ধাক্কা এফ এ। ছবিটি মনে রাখলে বোঝা যায় এই বাতিল কোনো বীজগণিত কৌশল নয়, বরং মধ্যবর্তী চলক এইচ এর মাধ্যমে ছোট ধাক্কার ধারাবাহিক সঞ্চালন। তিনটি সংখ্যারেখার অ্যানিমেশন ঠিক এটিই দেখিয়েছিল।"},
            {"index": 4, "type": "p",
             "tts": "একটি ছোট কিন্তু দরকারি বিষয়, কোনো ফাংশনকে ধ্রুবক দিয়ে গুণ করলে কাজ অনেক সহজ হয়। যেমন দুই গুণ সাইন অফ এক্সের ডেরিভেটিভ হলো দুই গুণ কোসাইন অফ এক্স, ধ্রুবক দুই অক্ষত থাকে, শুধু সাইনের ডেরিভেটিভ কোসাইন হয়। একটু ভাবলেই বোঝা যায় কেন এটি প্রোডাক্ট রুলের একটি সরল বিশেষ ক্ষেত্র। আর আমাদের পুরনো উদাহরণে চেইন রুল প্রয়োগ করলে পাই, ডি বাই ডি এক্স অফ সাইন অফ এক্স স্কয়ার সমান কোসাইন অফ এক্স স্কয়ার গুণ দুই এক্স, বাইরের কোসাইন ভেতরের এক্স স্কয়ার কে ধরে রেখে দুই এক্স দিয়ে গুণিত হচ্ছে।"},
            {"index": 5, "type": "formula-box",
             "tts": "চূড়ান্ত সমাধান, ডি বাই ডি এক্স অফ সাইন অফ এক্স স্কয়ার সমান কোসাইন অফ এক্স স্কয়ার গুণ দুই এক্স। আর ডি বাই ডি এক্স অফ জি অফ এইচ অফ এক্স সমান জি প্রাইম অফ এইচ অফ এক্স গুণ এইচ প্রাইম অফ এক্স।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, সারসংক্ষেপ ও অন্তর্দৃষ্টি, তিনটি হাতিয়ার। এখন আমাদের হাতে তিনটি মৌলিক হাতিয়ার আছে, যোগ, গুণ ও সংযোজন। যোগের নিয়মে অংশের ডেরিভেটিভ যোগ হয়, প্রোডাক্ট রুলে জি গুণ এইচের ডেরিভেটিভ সমান জি প্রাইম গুণ এইচ প্লাস জি গুণ এইচ প্রাইম, অর্থাৎ আয়তক্ষেত্রের দুটি ফালি, আর চেইন রুলে জি প্রাইম অফ এইচ অফ এক্স গুণ এইচ প্রাইম অফ এক্স, অর্থাৎ ধারাবাহিক গিয়ার অনুপাতের গুণফল। পার্থক্যটি মনে রাখুন, প্রোডাক্ট রুল দুটি স্বাধীন প্রসারণের যোগফল দেখায়, চেইন রুল দুটি ধারাবাহিক হারের গুণফল। ছবি আর গিয়ার অ্যানালজি মনে থাকলে কোনো সূত্রই মুখস্থ করার প্রয়োজন হবে না।"},
            {"index": 7, "type": "p", "role": "conclusion",
             "tts": "অফিশিয়াল ব্যায়াম হিসেবে ভাবুন, সাইন অফ এক্সের বর্গের ডেরিভেটিভ কত। প্রথমে চেইন রুল ব্যবহার করুন, সাইন অফ এক্স কে এক্স স্কয়ার ফাংশনের ভেতরে ঢুকানো ধরে বাইরের অন্তরজ দুই গুণ সাইন অফ এক্স কে ভেতরের অন্তরজ কোসাইন অফ এক্স দিয়ে গুণ করুন, পাবেন দুই গুণ সাইন অফ এক্স গুণ কোসাইন অফ এক্স। তারপর একই রাশিকে সাইন অফ এক্স গুণ সাইন অফ এক্স হিসেবে প্রোডাক্ট রুল দিয়েও বের করুন, দুটি ফালি কোসাইন অফ এক্স গুণ সাইন অফ এক্স প্লাস সাইন অফ এক্স গুণ কোসাইন অফ এক্স যোগ করে একই উত্তর পাবেন, ঠিক যেমন আগের অধ্যায়ে এক্স স্কয়ারের দুটি ধার দেখেছিলাম। ক্যালকুলাসের গভীরতম তৃপ্তি লুকিয়ে আছে এই দৃশ্যগুলো নিজের চোখে দেখার মাঝে, যখন সূত্রের পেছনের জ্যামিতি স্পষ্ট হয়, তখন সবচেয়ে জটিল সমীকরণও অর্থবহ ও জীবন্ত হয়ে ওঠে।"},
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
        if sec["title"] != EXPECTED_TITLES[sec_id]:
            raise ValueError(f"{sec_id}: title mismatch")
        indices = [c["index"] for c in sec["cues"]]
        if indices != list(range(len(indices))):
            raise ValueError(f"{sec_id}: cue indices are not 0..n-1")
        total += len(indices)
    if total != 34:
        raise ValueError(f"Expected 34 cues, found {total}")

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
        "lesson": "lesson_04",
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
    assert total_cues == 34

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Calculus Lesson 04")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<24} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 4 sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json is valid JSON; all 4 mp3 files exist and are non-empty.")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(build_all())
