# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Calculus Lesson 03
("Power Rule through geometry", Bengali) to the gold standard.

Deterministic, re-runnable, self-contained:
  * 34 cues in 4 narrated sections with EXACTLY the same section IDs, alias keys,
    audio_file names, cue types and cue order as the existing manifest and as
    the LIVE DOM parsed by narration_engine.js (verified 9/8/9/8 via the
    extract_calc03_dom_blocks.py extraction with KaTeX <annotation> preserved).
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Figure cues are genuine 2-4 sentence natural explanations — never the
    artificial label "চিত্র প্রদর্শনী".
  * Every script is clean spoken Bengali with phonetic safeguards:
    x -> এক্স, dx -> ডি এক্স, n -> এন, x^n -> এক্স টু দ্য পাওয়ার এন,
    d/dx -> ডি বাই ডি এক্স. No TeX, LaTeX, backslashes, $, braces, brackets,
    em-dashes, raw hyphens or Latin letters.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, chapter-quote -3%, p +2%, figure -4%, callout +0%,
      formula-box -8%, conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with the
    exact-ms timings and both canonical + alias section keys of the old manifest.
  * Validates non-zero durations, zero overlap, valid JSON and non-empty mp3s.

Usage:  python governance/build_expressive_teacher_audio_calc03.py
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
                         "calculus", "lesson_03")
MANIFEST_TITLE = "অধ্যায় ০৩ — জ্যামিতির মাধ্যমে অন্তরজের সূত্র (Derivative Formulas Through Geometry)"

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
# (Identical to the LIVE DOM blocks parsed by narration_engine.js.)
EXPECTED_TYPES = {
    "sec-x2-geometry": ["h2", "chapter-quote", "p", "p", "figure", "p", "formula-box", "callout", "p"],
    "sec-x3-volume":   ["h2", "p", "figure", "p", "p", "formula-box", "callout", "p"],
    "sec-power-rule":  ["h2", "p", "formula-box", "p", "p", "figure", "formula-box", "callout", "p"],
    "sec-trig-sine":   ["h2", "p", "figure", "p", "p", "callout", "formula-box", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-x2-geometry": "sec_01_x2_geometry.mp3",
    "sec-x3-volume":   "sec_02_x3_volume.mp3",
    "sec-power-rule":  "sec_03_power_rule.mp3",
    "sec-trig-sine":   "sec_04_sine_geometry.mp3",
}
# Canonical DOM section id -> legacy alias key kept in the manifest.
ALIASES = {
    "sec-x2-geometry": "sec_01_x2_geometry",
    "sec-x3-volume":   "sec_02_x3_volume",
    "sec-power-rule":  "sec_03_power_rule",
    "sec-trig-sine":   "sec_04_sine_geometry",
}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (34 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-x2-geometry": {
        "title": "১. ক্ষেত্রফল বৃদ্ধি ও এক্স স্কয়ারের অন্তরজ (Area Growth & The Derivative of x²)",
        "audio_file": "sec_01_x2_geometry.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, ক্ষেত্রফল বৃদ্ধি ও এক্স স্কয়ারের অন্তরজ জ্যামিতি।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, একজন গণিতবিদের কাছে তাঁর কল্পনা যথেষ্ট ছিল না, কিন্তু তিনি এখন কবি হয়ে গেছেন, আর এখন সব ঠিক আছে। বলেছেন ডেভিড হিলবার্ট।"},
            {"index": 2, "type": "p",
             "tts": "আগের অধ্যায়ে আমরা অন্তরজ আর পরিবর্তনের হারের সম্পর্ক জেনেছি। এখন দেখব কীভাবে সূত্রগুলো আবৃত্তি না করে নিজেরা আবিষ্কার করতে পারি। ক্যালকুলাসের একজন সাধারণ শিক্ষার্থীকে হয়তো সাইন এক্স ভাগ এক্স স্কয়ারের মতো কোনো ফাংশনের অন্তরজ বের করতে বলা হয়, অথচ কোনো বাস্তব প্রসঙ্গ দেওয়া হয় না। গুণন সারণি মুখস্থ করার মতোই এটি এক ধাপের কাজ, কিন্তু আমাদের লক্ষ্য হলো সূত্রগুলো এমনভাবে বোঝা যেন সেগুলো আমরা নিজেদেরই আবিষ্কার করি।"},
            {"index": 3, "type": "p",
             "tts": "চলুন সবচেয়ে পরিচিত ফাংশন এফ অব এক্স সমান এক্স স্কয়ার দিয়ে শুরু করি। একে আপনি কার্তেসীয় তলে পরাবৃত্ত বা প্যারাবোলা হিসেবে না দেখে, আক্ষরিক অর্থেই এক্স বাহুবিশিষ্ট একটি বর্গের ক্ষেত্রফল হিসেবে কল্পনা করুন। তাহলে এক্স বদলালে ক্ষেত্রফল কীভাবে বদলায়, তা সরাসরি চোখে দেখা যাবে।"},
            {"index": 4, "type": "figure",
             "tts": "এই চিত্রে এক্স বাহুবিশিষ্ট বর্গক্ষেত্রটির ডান ও উপরের ধারে ডি এক্স প্রস্থ যোগ করা হয়েছে। নীল মূল অংশ এক্স স্কয়ার অপরিবর্তিত থাকে, আর হলুদ ফালি দুটো ও কোণার সবুজ বর্গটি নতুন করে যোগ হওয়া ক্ষেত্রফল ডি এফ। লক্ষ্য করুন, দুটি ফালি ঠিক একই আকারের। এই সমানতাই পরবর্তীতে দুই সংখ্যাটির জন্ম দেবে।"},
            {"index": 5, "type": "p",
             "tts": "বর্গের বাহু এক্স কে ডি এক্স পরিমাণ বাড়ালে ক্ষেত্রফলের মোট বৃদ্ধি ডি এফ তিনটি অংশ নিয়ে গঠিত হয়, ডান ধারে এক্স গুণ ডি এক্স, উপরের ধারে আরেকটি এক্স গুণ ডি এক্স, এবং কোণায় অতিক্ষুদ্র ডি এক্স স্কয়ার বর্গ। উদাহরণস্বরূপ, এক্স সমান তিন আর ডি এক্স সমান শূন্য দশমিক শূন্য এক হলে ফালি দুটির মোট ক্ষেত্রফল দুই গুণ তিন গুণ শূন্য দশমিক শূন্য এক, অর্থাৎ শূন্য দশমিক শূন্য ছয়, ডি এক্সের প্রায় ছয় গুণ। আর এক্স সমান দুই হলে তা শূন্য দশমিক শূন্য চার, অর্থাৎ ডি এক্সের চার গুণ।"},
            {"index": 6, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ডি এফ সমান দুই এক্স গুণ ডি এক্স যোগ ডি এক্স স্কয়ার। তাই ডি এফ বাই ডি এক্স সমান দুই এক্স যোগ ডি এক্স। আর ডি এক্স শূন্যের দিকে গেলে ফল দাঁড়ায় দুই এক্স।"},
            {"index": 7, "type": "callout",
             "tts": "বিশেষ নোট, জ্যামিতিক অন্তর্দৃষ্টি, দুই কোথা থেকে এলো। দুই এক্স আসলে বর্গের সেই দুটি ধারের মোট দৈর্ঘ্য যেদিকে নতুন ফালি যুক্ত হচ্ছে, ডানে এক্স আর উপরে এক্স। ডি এক্স স্কয়ার পদটি ডি এক্সের চেয়েও অনেক ছোট, তাই ডি এক্স শূন্যের দিকে গেলে সেটি মিলিয়ে যায়, কিন্তু দুই এক্স অক্ষত থাকে। সুতরাং এক্স স্কয়ারের অন্তরজ দুই এক্স কোনো যান্ত্রিক নিয়ম নয়, বরং একটি বাড়ন্ত বর্গের স্বাভাবিক জ্যামিতি।"},
            {"index": 8, "type": "p", "role": "conclusion",
             "tts": "অতএব পাই, এক্স স্কয়ারের অন্তরজ দুই এক্স। লেখচিত্রের ঢাল এক্স সমান শূন্যে শূন্য, এক্স সমান একে কিছুটা খাড়া, আর এক্স সমান দুইতে আরও খাড়া, আর বর্গের জ্যামিতি ঠিক এই ক্রমবৃদ্ধিই প্রকাশ করে। লেখচিত্র দেখে হিসাব শুরু না করে আমরা ফাংশনের আসল অর্থের দিকে তাকালাম, এই অভ্যাসটি পরবর্তী সব সূত্রে কাজে আসবে।"},
        ],
    },

    "sec-x3-volume": {
        "title": "২. আয়তন বৃদ্ধি ও এক্স কিউবের অন্তরজ (Volume Growth & The Derivative of x³)",
        "audio_file": "sec_02_x3_volume.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, আয়তন বৃদ্ধি ও এক্স কিউবের অন্তরজ।"},
            {"index": 1, "type": "p",
             "tts": "এবার এক মাত্রা উপরে উঠে এফ অব এক্স সমান এক্স কিউব নিয়ে ভাবা যাক। থ্রিডিতে এটি স্বাভাবিকভাবেই এক্স বাহুবিশিষ্ট একটি নিরেট ঘনকের আয়তন। আগের বর্গের কথা মনে রেখে এখন ঘনকটির বাহু ডি এক্স পরিমাণ বাড়ালে আয়তন কীভাবে বদলায়, তা দেখব।"},
            {"index": 2, "type": "figure",
             "tts": "এই চিত্রে এক্স বাহুর ঘনকের সাথে ডি এক্স যোগ করার পরে নতুন যে আয়তন যুক্ত হয়েছে তা দেখানো হয়েছে। সবচেয়ে বড় তিনটি পাতলা স্ল্যাব ঘনকের তিনটি উন্মুক্ত তলে লেগে আছে, আর ধারে রয়েছে সরু দণ্ড আর কোণায় ছোট ঘনক। ডি এক্স সীমায় ছোট হলে স্ল্যাব তিনিটিই পুরো বৃদ্ধির প্রায় শতভাগ হয়ে যায়। ছবিটি সেই কারণেই তলের নীতি শেখায়।"},
            {"index": 3, "type": "p",
             "tts": "আয়তন বৃদ্ধির সিংহভাগ আসে তিনটি উন্মুক্ত পৃষ্ঠতলে যুক্ত হওয়া পাতলা স্ল্যাব থেকে। প্রতিটির ক্ষেত্রফল এক্স স্কয়ার আর পুরুত্ব ডি এক্স, ফলে প্রতিটির আয়তন এক্স স্কয়ার গুণ ডি এক্স, আর তিনটির মোট থ্রি এক্স স্কয়ার গুণ ডি এক্স। বর্গে যেমন দুটি ধার ছিল, ঘনকে তেমনি তিনটি তল, আর এই রূপান্তরেই সম্ভাব্য উত্তরের ধারণা তৈরি হয়।"},
            {"index": 4, "type": "p",
             "tts": "এছাড়া ঘনকের ধার বরাবর তিনটি সরু দণ্ড আছে, যাদের আয়তন এক্স গুণ ডি এক্স স্কয়ার, আর শীর্ষে ডি এক্স কিউব আয়তনের এক ছোট ঘনক। কিন্তু ডি এক্স দিয়ে ভাগ করার সময় এদের মধ্যে এখনো ডি এক্স থেকে যায়, তাই সীমাস্থ অবস্থায় এগুলো শূন্যে মিলিয়ে যায়। টিকে থাকে শুধু থ্রি এক্স স্কয়ার গুণ ডি এক্স পদটি।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ডি এফ সমান থ্রি এক্স স্কয়ার গুণ ডি এক্স যোগ থ্রি এক্স গুণ ডি এক্স স্কয়ার যোগ ডি এক্স কিউব। তাই ডি এফ বাই ডি এক্স সমান থ্রি এক্স স্কয়ার যোগ থ্রি এক্স গুণ ডি এক্স যোগ ডি এক্স স্কয়ার। আর ডি এক্স শূন্যের দিকে গেলে ফল দাঁড়ায় থ্রি এক্স স্কয়ার।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, মাত্রার বিলোপ নীতি। যেকোনো পদে ডি এক্সের ঘাত একের বেশি হলেই সেটি সীমায় মারা যায়, কেবল প্রথম ঘাতের পদটি বেঁচে থাকে। দ্বিমাত্রিক বর্গের দুটি ধার দিয়েছিল দুই এক্স, আর ত্রিমাত্রিক ঘনকের তিনটি তল দিল থ্রি এক্স স্কয়ার। মাত্রা বদলালেও জ্যামিতির এই সামঞ্জস্য অটুট থাকে।"},
            {"index": 7, "type": "p", "role": "conclusion",
             "tts": "সুতরাং এক্স কিউবের অন্তরজ থ্রি এক্স স্কয়ার। লেখচিত্রে এক্স কিউবের ঢাল বাঁদিকে কম, মূলবিন্দুতে শূন্য আর ডানদিকে ক্রমশ বাড়তে থাকে, ঠিক থ্রি এক্স স্কয়ারের মতো। কিন্তু শুধু লেখচিত্র দেখে আমরা কখনোই নির্দিষ্ট থ্রি এক্স স্কয়ার রাশিটি পেতাম না, সেটি পেতে হলো ঘনকের আসল অর্থের দিকে তাকাতে।"},
        ],
    },

    "sec-power-rule": {
        "title": "৩. সার্বজনীন পাওয়ার রুল ও অন্যান্য ঘাত (General Power Rule & Geometric Multi-dimensions)",
        "audio_file": "sec_03_power_rule.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, সার্বজনীন পাওয়ার রুল ও বিচিত্র ঘাতের জ্যামিতি।"},
            {"index": 1, "type": "p",
             "tts": "এই পর্যন্ত দেখা প্যাটার্নটিকে সাধারণীকরণ করাই হলো পাওয়ার রুল। এক্স টু দ্য পাওয়ার এন কে এন মাত্রার এক হাইপারকিউব বা এন সংখ্যক এক্সের গুণফল হিসেবে ভাবুন। চার বা পাঁচ মাত্রা কল্পনা করা কঠিন, তাই আমরা বীজগণিতের মাধ্যমে ধারাটি বাড়িয়ে নিই। এক্স প্লাস ডি এক্সের প্রথম ঘাতে পাই এক্স যোগ এক গুণ ডি এক্স, দ্বিতীয় ঘাতে এক্স স্কয়ার যোগ দুই এক্স গুণ ডি এক্স যোগ ডি এক্স স্কয়ার, তৃতীয় ঘাতে এক্স কিউব যোগ থ্রি এক্স স্কয়ার গুণ ডি এক্স, আর এভাবে চতুর্থ ও পঞ্চম ঘাতে যথাক্রমে চার এক্স কিউব আর পাঁচ এক্স টু দ্য পাওয়ার ফোর গুণ ডি এক্স। প্রতিটিতে কমলা রঙের প্রথম পদটিই হলো আমাদের চাইছে এমন অংশ।"},
            {"index": 2, "type": "formula-box",
             "tts": "সার্বজনীন সূত্র, ডি বাই ডি এক্স অব এক্স টু দ্য পাওয়ার এন সমান এন গুণ এক্স টু দ্য পাওয়ার এন মাইনাস ওয়ান।"},
            {"index": 3, "type": "p",
             "tts": "প্রতিটি এক্স যখন ডি এক্স পরিমাণ বাড়ে, তখন এনটি উৎপাদকের প্রতিটি পালাক্রমে এক্স টু দ্য পাওয়ার এন মাইনাস ওয়ান গুণ ডি এক্স পরিমাণ যোগ করে। সব মিলিয়ে এনটি সমমানের টুকরো, অর্থাৎ হার এন গুণ এক্স টু দ্য পাওয়ার এন মাইনাস ওয়ান। ঘাতটি নিচে নামে ও এক কমে যায়, একে আমরা সাধারণত ঘাত লাফ দেওয়া বলে মনে রাখি, কিন্তু তার পেছনে রয়েছে এই জ্যামিতিক যুক্তি।"},
            {"index": 4, "type": "p",
             "tts": "সবচেয়ে আশ্চর্যজনক বিষয় হলো এই নিয়ম ঋণাত্মক ও ভগ্নাংশ ঘাতের ক্ষেত্রেও চলে। এফ অব এক্স সমান ওয়ান বাই এক্স, অর্থাৎ এক্স টু দ্য পাওয়ার মাইনাস ওয়ান, তার কথা নিন। এখানে এন সমান মাইনাস ওয়ান, তাই নিয়ম অনুযায়ী উত্তর মাইনাস ওয়ান গুণ এক্স টু দ্য পাওয়ার মাইনাস টু, অর্থাৎ মাইনাস ওয়ান বাই এক্স স্কয়ার। কিন্তু আসল মজা হলো এটি জ্যামিতিকভাবেও সত্য।"},
            {"index": 5, "type": "figure",
             "tts": "এই চিত্রে একটি ছোট আয়তক্ষেত্রের জলাশয় দেখানো হয়েছে, যার মোট ক্ষেত্রফল সর্বদা এক। প্রস্থ এক্স বাড়ালে উচ্চতা ওয়াই কমে যায়, কারণ এক্স গুণ ওয়াই সমান এক স্থির থাকতে হবে। প্রস্থ বাড়লে যোগ হওয়া অংশের সমান ক্ষেত্রফল উপর থেকে বাদ দিতে হয়, আর এই ভারসাম্যই ঋণাত্মক চিহ্নের কারণ। চিত্রের এই অনুপাতটি মনে রাখলে মাইনাস ওয়ান বাই এক্স স্কয়ার ফলাফলটি আপনি নিজেই অনুমান করতে পারবেন।"},
            {"index": 6, "type": "formula-box",
             "tts": "গাণিতিক সম্পর্ক, এক্স গুণ ওয়াই সমান এক। অন্তরীকরণ করলে এক্স গুণ ডি ওয়াই যোগ ওয়াই গুণ ডি এক্স সমান শূন্য। তাই ডি ওয়াই বাই ডি এক্স সমান মাইনাস ওয়াই বাই এক্স, অর্থাৎ মাইনাস ওয়ান বাই এক্স স্কয়ার।"},
            {"index": 7, "type": "callout",
             "tts": "বিশেষ নোট, ভগ্নাংশ ঘাত ও বর্গমূল। একটি বর্গের ক্ষেত্রফল যদি এক্স হয়, তবে তার বাহু এস সমান রুট এক্স, অর্থাৎ এক্স টু দ্য পাওয়ার ওয়ান বাই টু। তাই ডি এক্স সমান দুই এস গুণ ডি এস, এবং ডি এস বাই ডি এক্স সমান ওয়ান বাই দুই এস, অর্থাৎ ওয়ান বাই দুই রুট এক্স। এখানে ডি এক্স দৈর্ঘ্য নয়, ক্ষেত্রফল বোঝায়, এই একটিমাত্র ধারণা বদলালেই পাওয়ার রুল সঙ্গে সঙ্গে সঠিক ফল দেয়।"},
            {"index": 8, "type": "p", "role": "conclusion",
             "tts": "এভাবেই বীজগণিতের আপাত শুষ্ক সূত্রগুলো জ্যামিতির পরশে প্রাণ পায়। ধনাত্মক, ঋণাত্মক কিংবা ভগ্নাংশ, যেকোনো ঘাতের ক্ষেত্রে এক্স টু দ্য পাওয়ার এনের অন্তরজ এন গুণ এক্স টু দ্য পাওয়ার এন মাইনাস ওয়ান একইভাবে কাজ করে। পরবর্তীতে ত্রিকোণমিতিক ফাংশনের ক্ষেত্রেও এই ছোট পরিবর্তনের ধারণা আমাদের সাহায্য করবে।"},
        ],
    },

    "sec-trig-sine": {
        "title": "৪. একক বৃত্ত ও সাইন এক্স এর অন্তরজ জ্যামিতি (The Unit Circle & Geometric Derivative of sin(x))",
        "audio_file": "sec_04_sine_geometry.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, ত্রিকোণমিতিক অন্তরজ ও একক বৃত্তের জ্যামিতিক নৃত্য।"},
            {"index": 1, "type": "p",
             "tts": "এখন গণিতের অন্যতম নান্দনিক প্রমাণের দিকে যাব, কেন সাইন এক্সের অন্তরজ কস এক্স। একে বুঝতে এক ব্যাসার্ধের একটি একক বৃত্ত কল্পনা করুন। কোণ এক্স রেডিয়ানে এবং বৃত্তের ওপর ওই বিন্দুর অবস্থানই সবকিছু নির্ধারণ করে।"},
            {"index": 2, "type": "figure",
             "tts": "এই চিত্রে ব্যাসার্ধ একের বৃত্তে এক্স কোণে একটি বিন্দু আছে, যার উল্লম্ব উচ্চতা সাইন এক্স ও অনুভূমিক দূরত্ব কস এক্স। কোণটিকে ডি এক্স পরিমাণ বাড়ালে বিন্দুটি পরিধি বরাবর সরে যায় এবং একটি অতিক্ষুদ্র সমকোণী ত্রিভুজ তৈরি হয়। এই ছোট ত্রিভুজটি মূল ত্রিভুজের সদৃশ, কেবল নব্বই ডিগ্রি ঘুরানো। সেই সাদৃশ্যটিই উত্তরের চাবিকাঠি।"},
            {"index": 3, "type": "p",
             "tts": "একক বৃত্তে এক্স রেডিয়ান কোণ হলে পরিধি বরাবর চাপের দৈর্ঘ্যও ঠিক এক্স, এই সুন্দর সম্পর্কের কারণে কোণ বাড়ালে বিন্দুটি চাপ বরাবর ডি এক্স দূরত্ব সরে যায়। আমাদের প্রশ্ন হলো, এই সরণের ফলে উল্লম্ব উচ্চতা সাইন এক্স কতটা বদলায়, অর্থাৎ ডি অব সাইন এক্স কত।"},
            {"index": 4, "type": "p",
             "tts": "সরণের জায়গায় যখন আমরা জুম করি, তখন বাঁকা চাপটি একটি সোজা রেখার মতো দেখায়, ঠিক যেন ডি এক্স দৈর্ঘ্যের একটি অতিভুজ। এই ক্ষুদ্র ত্রিভুজের খাড়া উল্লম্ব বাহুটিই হলো উচ্চতার পরিবর্তন, অর্থাৎ ডি অব সাইন এক্স, আর অতিভুজ হলো ডি এক্স।"},
            {"index": 5, "type": "callout",
             "tts": "বিশেষ নোট, ঘূর্ণিত সদৃশ ত্রিভুজ। বৃত্তের স্পর্শক ব্যাসার্ধের সাথে সমকোণে থাকে, তাই এই পুঁচকে ত্রিভুজটি মূল ত্রিভুজটির সদৃশ, শুধু নব্বই ডিগ্রি ঘুরে আছে। ফলে উল্লম্ব বাহু ভাগ অতিভুজ, অর্থাৎ ডি অব সাইন এক্স ভাগ ডি এক্স অনুপাতটি মূল ত্রিভুজের অনুভূমিক বাহু কস এক্সের সমান হয়ে যায়। জ্যামিতির এই এক কৌশলেই পুরো সূত্রটি প্রমাণিত হয়।"},
            {"index": 6, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ডি অব সাইন এক্স ভাগ ডি এক্স সমান কস এক্স। একইভাবে ডি অব কস এক্স ভাগ ডি এক্স সমান মাইনাস সাইন এক্স।"},
            {"index": 7, "type": "p", "role": "conclusion",
             "tts": "অতএব দেখতে পাচ্ছেন, ক্যালকুলাসের প্রতিটি সূত্র আসলে জ্যামিতির বৃদ্ধি, রূপান্তর ও সীমাস্থ ভারসাম্যের এক অনুপম গল্প। সূত্রগুলো আর স্মৃতির বোঝা নয়, তা আপনার ভাবনার সহজাত অংশ হয়ে যায়, যখনই আপনি তাদের পেছনের ছোট পরিবর্তনগুলো দেখতে পান।"},
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
        "lesson": "lesson_03",
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
    print("BUILD COMPLETE - expressive teacher audio, Calculus Lesson 03")
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
