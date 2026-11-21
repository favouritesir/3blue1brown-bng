# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Calculus Lesson 02
("The paradox of the derivative", Bengali) to the Lesson-01 gold standard.

Deterministic, re-runnable, self-contained:
  * 32 cues in 4 narrated sections with EXACTLY the same section IDs, alias keys,
    audio_file names, cue types and cue order as the existing manifest.
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Figure cues are genuine 2-4 sentence natural explanations — never the
    artificial label "চিত্র প্রদর্শনী".
  * Every script is clean spoken Bengali with phonetic safeguards:
    t -> টি, x -> এক্স, dt -> ডি টি, ds -> ডি এস, ds/dt -> ডি এস বাই ডি টি.
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

Usage:  python governance/build_expressive_teacher_audio_calc02.py
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
                         "calculus", "lesson_02")
MANIFEST_TITLE = "অধ্যায় ০২ — অবকলনের প্যারাডক্স: তাৎক্ষণিক পরিবর্তনের হার"

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
    "sec-paradox":            ["h2", "chapter-quote", "p", "p", "figure", "p", "callout", "p"],
    "sec-derivative-meaning": ["h2", "p", "p", "formula-box", "p", "callout", "p", "p"],
    "sec-tangent-zoom":       ["h2", "p", "figure", "p", "p", "callout", "p"],
    "sec-x2-geometry":        ["h2", "p", "figure", "p", "p", "formula-box", "p", "callout", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-paradox":            "sec_01_paradox.mp3",
    "sec-derivative-meaning": "sec_02_derivative_meaning.mp3",
    "sec-tangent-zoom":       "sec_03_tangent_zoom.mp3",
    "sec-x2-geometry":        "sec_04_x2_geometry.mp3",
}
# Canonical DOM section id -> legacy alias key kept in the manifest.
ALIASES = {
    "sec-paradox":            "sec_01_paradox",
    "sec-derivative-meaning": "sec_02_derivative_meaning",
    "sec-tangent-zoom":       "sec_03_tangent_zoom",
    "sec-x2-geometry":        "sec_04_x2_geometry",
}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (32 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-paradox": {
        "title": "১. তাৎক্ষণিক বেগ ও প্যারাডক্স (Instantaneous Velocity & The Paradox)",
        "audio_file": "sec_01_paradox.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, তাৎক্ষণিক বেগ ও অন্তরীকরণের প্যারাডক্স।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, যতদূর গণিতের তত্ত্বসমূহ বাস্তবতা সম্পর্কে, ততদূর সেগুলো নিশ্চিত নয়, আর যতদূর নিশ্চিত, ততদূর বাস্তবতা সম্পর্কে নয়। বলেছেন আলবার্ট আইনস্টাইন।"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, ক্যালকুলাসের দ্বিতীয় অধ্যায়ে তোমাদের স্বাগত জানাচ্ছি। ধরা যাক, তোমরা একটি সুন্দর হাইওয়ে দিয়ে গাড়ি চালিয়ে যাচ্ছ। হঠাৎ ড্যাশবোর্ডের স্পিডোমিটারের দিকে চোখ পড়ল এবং দেখলে কাঁটাটি ঠিক ষাট কিলোমিটার প্রতি ঘণ্টার ঘরে স্থির হয়ে আছে। আসল উদাহরণে গাড়িটি বিন্দু এ থেকে শুরু করে গতি বাড়িয়ে শেষ পর্যন্ত একশো মিটার দূরের বিন্দু বিতে দশ সেকেন্ডে থামে।"},
            {"index": 3, "type": "p",
             "tts": "কিন্তু একটু গভীরভাবে ভেবে দেখুন, এই ষাট কিলোমিটার প্রতি ঘণ্টা আসলে কীসের পরিমাপ? আমরা ছোটবেলা থেকেই জানি, বেগ মানে হলো অতিক্রান্ত দূরত্ব ভাগ প্রয়োজনীয় সময়। অর্থাৎ দূরত্বের পরিবর্তন ডেল্টা এস কে সময়ের ব্যবধান ডেল্টা টি দিয়ে ভাগ করলে গড় বেগ পাওয়া যায়।"},
            {"index": 4, "type": "figure",
             "tts": "এই লেখচিত্রে অনুভূমিক অক্ষে সময় টি এবং উল্লম্ব অক্ষে অতিক্রান্ত দূরত্ব এস অফ টি দেখানো হয়েছে। গাড়িটি দশ সেকেন্ডে একশো মিটার পথ পাড়ি দিয়ে থামে, আর বক্ররেখার উচ্চতা সেই দূরত্বই নির্দেশ করে। ছয় সেকেন্ডে উচ্চতা সত্তর মিটারের কিছু বেশি। লক্ষ্য করুন, বক্ররেখার ঢালই পরবর্তীতে বেগের ধারণা জন্ম দেবে।"},
            {"index": 5, "type": "p",
             "tts": "এবার ভাবুন, যাত্রা শুরুর ঠিক পাঁচ সেকেন্ডের মাথার মতো একটি একক মুহূর্তের কথা। সেই মুহূর্তে সময়ের কোনো ব্যবধান নেই, অর্থাৎ ডেল্টা টি সমান শূন্য। আর যদি সময়ই না থাকে, তবে গাড়িটি কোনো দূরত্বও অতিক্রম করতে পারে না, ফলে ডেল্টা এসও শূন্য। একটি স্থির ছবি দেখে বেগ বের করা যায় না, তাই দুটি সময়ের স্ন্যাপশট তুলনা করে চার ও পাঁচ সেকেন্ডের ব্যবধানে বিশ মিটার প্রতি সেকেন্ড হিসাব করা হয়। অথচ লেখচিত্র থেকে দেখা যায়, তিন সেকেন্ডে গাড়িটি সবচেয়ে দ্রুত চলে।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, অবকলনের কেন্দ্রীয় প্যারাডক্স। একটি একক মুহূর্তে যদি পরিবর্তনই না ঘটে, তবে শূন্য ভাগ শূন্য সম্পূর্ণ অনির্ণেয়। তবুও স্পিডোমিটার পরিষ্কারভাবে ষাট কিলোমিটার প্রতি ঘণ্টা দেখাচ্ছে। এই আপাত বৈপরীত্যই হলো অন্তরজের প্যারাডক্স, গতি মাপতে হলে দুটি সময় লাগবে, অথচ বেগ চাই একটি মুহূর্তে।"},
            {"index": 7, "type": "p", "role": "conclusion",
             "tts": "এটিই হলো সেই বিখ্যাত প্যারাডক্স। একটি স্থির ছবিতে সবকিছু নিথর, কোনো গতি নেই, তাহলে গতির পরিমাপ কীভাবে একটি একক বিন্দুতে অবস্থান করতে পারে? এই ধাঁধার উত্তর খুঁজতেই জন্ম হয়েছিল ক্যালকুলাসের।"},
        ],
    },

    "sec-derivative-meaning": {
        "title": "২. ডেরিভেটিভ কী? dt ও ds-এর অনুপাত (What is a Derivative?)",
        "audio_file": "sec_02_derivative_meaning.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, ডেরিভেটিভ কী, ডি টি ও ডি এসের অনুপাত।"},
            {"index": 1, "type": "p",
             "tts": "প্যারাডক্সটির চমৎকার সমাধান হলো, ক্যালকুলাস কখনো শূন্য দিয়ে শূন্যকে ভাগ করে না। বরং এটি এমন এক সীমাস্থ প্রক্রিয়ার কথা বলে যা শূন্যের দিকে ধাবমান। প্রথমে একটি সসীম ছোট সময় নেওয়া হয়, তারপর জিজ্ঞেস করা হয় সেটি শূন্যের কাছে গেলে উত্তর কী ধীরে ধীরে অভিমুখী হয়।"},
            {"index": 2, "type": "p",
             "tts": "মনে করি, পাঁচ সেকেন্ড সময়ের পর আমরা অত্যন্ত ক্ষুদ্র একটি সময় ব্যবধান বিবেচনা করলাম, যাকে বলা হয় ডি টি। এই অতি সংক্ষিপ্ত সময়ে গাড়িটি খুব সামান্য একটু পথ অতিক্রম করল, যাকে আমরা বলছি ডি এস।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, তাৎক্ষণিক বেগ ভি ইনস্ট্যান্ট সমান ডি এস বাই ডি টি। আর এটি হলো সেই সীমা, যা ডেল্টা টি শূন্যের দিকে ধাবিত হলে এস অফ টি প্লাস ডেল্টা টি বিয়োগ এস অফ টি কে ডেল্টা টি দিয়ে ভাগ করলে পাওয়া যায়।"},
            {"index": 4, "type": "p",
             "tts": "এখানে ডি টি কিন্তু শূন্য নয়, বরং শূন্যের খুব কাছাকাছি, হয়তো এক হাজার ভাগের এক সেকেন্ড। বাস্তব স্পিডোমিটারও ঠিক এভাবে কাজ করে, তিন থেকে তিন দশমিক শূন্য এক সেকেন্ডের ব্যবধানে দূরত্বের সামান্য বৃদ্ধিকে ভাগ করে বেগ নির্ণয় করে। এই অতি ক্ষুদ্র ব্যবধানে ডি এস বাই ডি টি আমাদের একটি বাস্তব ও সুসংজ্ঞায়িত গড় বেগ প্রদান করে।"},
            {"index": 5, "type": "callout",
             "tts": "বিশেষ নোট, ডেরিভেটিভের মূল রহস্য। ডি টি কে যতই ক্ষুদ্র থেকে ক্ষুদ্রতর করা হোক না কেন, ডি এস বাই ডি টি অনুপাতটি হারিয়ে যায় না, বরং একটি সুনির্দিষ্ট স্থির মানের দিকে ধাবিত হয়। এই সীমাস্থ মানটিই হলো ডেরিভেটিভ বা তাৎক্ষণিক বেগ।"},
            {"index": 6, "type": "p",
             "tts": "তাই স্পিডোমিটার আসলে সময়ের একক মুহূর্তে গতি মাপে না, বরং অত্যন্ত ক্ষুদ্র সময় ব্যবধানে সম্ভাব্য পরিবর্তনের শ্রেষ্ঠ সুষম আসন্নায়ন নির্দেশ করে।"},
            {"index": 7, "type": "p", "role": "conclusion",
             "tts": "গণিতের ভাষায়, দূরত্ব ফাংশন এস অফ টির পরিবর্তনের হার হলো ডি এস বাই ডি টি, আর ডি এস বাই ডি টি কে টির একটি ফাংশন হিসেবে ভাবা যায়। ডি অক্ষরটি ব্যবহার করে আমরা ঘোষণা করি যে শেষ পর্যন্ত ডি টি শূন্যের দিকে যাবে। ছোট পার্থক্য বোঝাতেই এই ডি অক্ষরের ব্যবহার।"},
        ],
    },

    "sec-tangent-zoom": {
        "title": "৩. জ্যামিতিক স্পর্শক ও বক্ররেখা জুম (Geometric Tangent & Graph Zooming)",
        "audio_file": "sec_03_tangent_zoom.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, জ্যামিতিক স্পর্শক ও বক্ররেখার জুম।"},
            {"index": 1, "type": "p",
             "tts": "ডেরিভেটিভের এই ভাবনাটিকে জ্যামিতিক লেখচিত্রে কীভাবে কল্পনা করা যায়? ধরা যাক, অনুভূমিক সময় অক্ষে টি এবং উল্লম্ব অক্ষে দূরত্ব এস স্থাপন করে আমরা দূরত্বের বক্ররেখা এস অফ টি আঁকলাম।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে তিন সেকেন্ড বিন্দুর চারপাশে অতিক্ষুদ্র ডি টি এবং তার ফলে হওয়া ডি এস দেখানো হয়েছে। অনুভূমিক ডি টি হলো সময়ের ছোট ধাপ, আর উল্লম্ব ডি এস হলো দূরত্বের সংশ্লিষ্ট ছোট পরিবর্তন। এই দুটির অনুপাতই হলো ঢাল। বক্ররেখার পাশে আঁকা ছোট ত্রিভুজটির মাধ্যমে বোঝা যায় কেন ডি এস বাই ডি টি আসলে একটি ঢাল।"},
            {"index": 3, "type": "p",
             "tts": "বক্ররেখার যেকোনো দুটি বিন্দুর মধ্যে যদি আমরা একটি ছেদক রেখা টানি, তবে তার ঢাল হবে খাড়া উচ্চতা ডেল্টা এস ভাগ আনুভূমিক দৈর্ঘ্য ডেল্টা টি। এক কথায়, বিন্দু দুটির দূরত্ব পার্থক্যকে সময় পার্থক্য দিয়ে ভাগ করলেই ছেদকের ঢাল পাওয়া যায়।"},
            {"index": 4, "type": "p",
             "tts": "এবার গ্রান্ট স্যান্ডারসনের অন্যতম প্রিয় কৌশলটি লক্ষ্য করুন, লেখচিত্রের একটি নির্দিষ্ট বিন্দুতে অসম্ভব জুম করতে থাকুন। যতই জুম করবেন, বাঁকা বক্ররেখাটি আর বাঁকা থাকবে না, দেখতে প্রায় নিখুঁত সরলরেখার মতো হয়ে যাবে। আর সেই ছেদকটি রূপ নেবে স্পর্শকে।"},
            {"index": 5, "type": "callout",
             "tts": "বিশেষ নোট, স্থানীয় রৈখিকতা। অত্যন্ত ক্ষুদ্র পরিসরে প্রতিটি মসৃণ বক্ররেখাই স্থানীয়ভাবে একটি সরলরেখা। সেই সরলরেখার ঢালই হলো ওই বিন্দুতে অঙ্কিত স্পর্শকের ঢাল, আর তা কিছুই নয়, ডি এস বাই ডি টি।"},
            {"index": 6, "type": "p", "role": "conclusion",
             "tts": "অতএব স্পর্শকের ঢাল আর কিছুই নয়, তা হলো ডি এস বাই ডি টি। তাৎক্ষণিক হার না বলে একে ধীরে ধীরে বিন্দুটির আশেপাশে শ্রেষ্ঠ সুষম আসন্নায়ন হিসেবে ভাবা যায়। স্পর্শকের ঢালই পরিবর্তনের হারকে চোখে দেখার সবচেয়ে শক্তিশালী রূপ।"},
        ],
    },

    "sec-x2-geometry": {
        "title": "৪. x²-এর অন্তরীকরণ জ্যামিতি (Geometry of the Derivative of x²)",
        "audio_file": "sec_04_x2_geometry.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, এক্স স্কয়ারের অন্তরীকরণের জ্যামিতি।"},
            {"index": 1, "type": "p",
             "tts": "চলুন এবার একটি বাস্তব বীজগণিতীয় ফাংশন এফ অফ এক্স সমান এক্স স্কয়ার নিয়ে জ্যামিতিক পরীক্ষা চালানো যাক। মুখস্থ সূত্র বলছে এর ডেরিভেটিভ দুই এক্স, কিন্তু কেন ঠিক দুই এক্স?"},
            {"index": 2, "type": "figure",
             "tts": "এখানে এক্স বাহুর একটি বর্গক্ষেত্র দেখা যাচ্ছে, যার ডান ও উপরের ধারে দুটি এক্স গুণ ডি এক্স আয়তাকার ফালি যোগ হয়েছে, আর কোণে রয়েছে অতিক্ষুদ্র ডি এক্সের বর্গ। মূল অংশ এক্স স্কয়ার অপরিবর্তিত থাকে, শুধু এই তিনটি নতুন টুকরোই ক্ষেত্রফলের বৃদ্ধি গঠন করে। দুটি ফালিই সমান হওয়ায় দুই সংখ্যাটি এসেছে, এটি কোনো বিমূর্ত সহগ নয়, বরং দুই ধারের জ্যামিতি।"},
            {"index": 3, "type": "p",
             "tts": "কল্পনা করুন একটি বর্গক্ষেত্র, যার প্রতিটি বাহুর দৈর্ঘ্য এক্স, তাহলে তার ক্ষেত্রফল এক্স স্কয়ার। এবার বর্গক্ষেত্রের দৈর্ঘ্য ও প্রস্থ উভয় দিকেই অতি সামান্য বৃদ্ধি ডি এক্স যোগ করা হলো।"},
            {"index": 4, "type": "p",
             "tts": "প্রশ্ন হলো, ক্ষেত্রফলের মোট বৃদ্ধি কতটুকু হবে? চিত্রে তাকালে দেখা যায় নতুন ক্ষেত্রফল তিনটি অংশে বিভক্ত, উপরের প্রান্তে এক্স গুণ ডি এক্স, ডান প্রান্তে আরেকটি এক্স গুণ ডি এক্স, এবং কোণায় ডি এক্সের বর্গ নামক অতিক্ষুদ্র বর্গক্ষেত্র।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এক্স প্লাস ডি এক্সের বর্গ বিয়োগ এক্স স্কয়ার সমান দুই এক্স গুণ ডি এক্স প্লাস ডি এক্সের বর্গ।"},
            {"index": 6, "type": "p",
             "tts": "এবার উভয়পক্ষকে ডি এক্স দিয়ে ভাগ করলে পরিবর্তনের হার পাওয়া যায়, ডি এফ বাই ডি এক্স সমান দুই এক্স প্লাস ডি এক্স।"},
            {"index": 7, "type": "callout",
             "tts": "বিশেষ নোট, ক্ষুদ্রাতিক্ষুদ্রের বিলোপ। ডি এক্স শূন্যের দিকে ধাবিত হলে একা পড়ে থাকা ডি এক্স পদটি নগণ্য হয়ে মিলিয়ে যায়, কিন্তু মূল দুই পাশের ফালির অনুপাত দুই এক্স অক্ষত থাকে। এই দুই সংখ্যাটি আসলে বর্গক্ষেত্রের দুটি বর্ধনশীল ধারের প্রতীক।"},
            {"index": 8, "type": "p", "role": "conclusion",
             "tts": "এভাবেই আমরা পাই, এক্স স্কয়ারের অন্তরজ সমান দুই এক্স। এটি কোনো অলৌকিক জাদু নয়, বরং দুটি আয়তাকার ফালির উন্মোচিত জ্যামিতিক রূপ, যার সীমাস্থ অবস্থায় দুই এক্স প্লাস ডি এক্স থেকে শুধু দুই এক্স অবশিষ্ট থাকে।"},
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
    if total != 32:
        raise ValueError(f"Expected 32 cues, found {total}")

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
    assert total_cues == 32

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Calculus Lesson 02")
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
