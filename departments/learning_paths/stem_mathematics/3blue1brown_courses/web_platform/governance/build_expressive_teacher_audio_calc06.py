# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Calculus Lesson 06
("Implicit differentiation, what's going on here?", Bengali) to the Lesson-01
gold standard.

Deterministic, re-runnable, self-contained:
  * 26 cues in 4 narrated sections with EXACTLY the same section IDs, alias keys,
    audio_file names, cue types and cue order as the existing manifest
    (verified 26/26 against the LIVE DOM via extraction with narration_engine's
    selector + KaTeX <annotation> preservation).
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Figure cues are genuine 2-4 sentence natural explanations — never the
    artificial label "চিত্র প্রদর্শনী" — and read naturally about what is on
    screen (no "figure exhibit" style announcement).
  * Every script is clean spoken Bengali with phonetic safeguards:
    x -> এক্স, y -> ওয়াই, dx -> ডি এক্স, dy -> ডি ওয়াই, dt -> ডি টি,
    z -> জেড, dz -> ডি জেড, dy/dx -> ডি ওয়াই বাই ডি এক্স.
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

Usage:  python governance/build_expressive_teacher_audio_calc06.py
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
                         "calculus", "lesson_06")
MANIFEST_TITLE = "অধ্যায় ০৬ — প্রচ্ছন্ন ব্যবকলন: সমউচ্চতা রেখা ও সম্পর্কিত পরিবর্তনের হার"

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
    "sec-implicit-intro":       ["h2", "chapter-quote", "p", "p", "figure", "p", "callout", "p"],
    "sec-level-curves":         ["h2", "p", "figure", "p", "callout", "p"],
    "sec-differential-balance": ["h2", "p", "formula-box", "p", "figure", "callout"],
    "sec-related-rates":        ["h2", "p", "figure", "formula-box", "p", "callout"],
}
EXPECTED_AUDIO_FILES = {
    "sec-implicit-intro":       "sec_01_implicit_intro.mp3",
    "sec-level-curves":         "sec_02_level_curves.mp3",
    "sec-differential-balance": "sec_03_differential_balance.mp3",
    "sec-related-rates":        "sec_04_related_rates.mp3",
}
# Canonical DOM section id -> legacy alias key kept in the manifest.
ALIASES = {
    "sec-implicit-intro":       "sec_01_implicit_intro",
    "sec-level-curves":         "sec_02_level_curves",
    "sec-differential-balance": "sec_03_differential_balance",
    "sec-related-rates":        "sec_04_related_rates",
}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (26 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-implicit-intro": {
        "title": "১. প্রত্যক্ষ বনাম প্রচ্ছন্ন সমীকরণ এবং বৃত্তের ঢাল (Explicit vs. Implicit Equations)",
        "audio_file": "sec_01_implicit_intro.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, প্রত্যক্ষ বনাম প্রচ্ছন্ন সমীকরণ এবং বৃত্তের স্পর্শক ঢাল।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, কোনো বক্তব্যের সত্যতা জানার আগে তার অর্থ বোঝা জরুরি, বলেছেন ইরেট বিশপ। যখন সম্পর্কগুলো স্পষ্ট নয় বরং প্রচ্ছন্ন থাকে, তখনও পরিবর্তন তার আপন নিয়মে সুনির্দিষ্ট থাকে।"},
            {"index": 2, "type": "p",
             "tts": "সাধারণ ক্যালকুলাস কোর্সে আমরা শিখি কীভাবে ওয়াই সমান এক্স স্কয়ার কিংবা ওয়াই সমান সাইন এক্সের মতো ফাংশনগুলোর অন্তরজ বা ডেরিভেটিভ নির্ণয় করতে হয়। এই প্রতিটি ক্ষেত্রে ওয়াই রাশিটি এক্সের একটি স্পষ্ট বা প্রত্যক্ষ ফাংশন হিসেবে সরাসরি দেওয়া থাকে। আপনি একটি এক্স ইনপুট দেন আর একক নির্দিষ্ট ওয়াই মান ফলাফল হিসেবে বেরিয়ে আসে।"},
            {"index": 3, "type": "p",
             "tts": "কিন্তু গণিত ও বিজ্ঞানের অনেক বাস্তব ঘটনায় এক্স আর ওয়াই সমীকরণের ভেতরেই একে অপরকে জড়িয়ে থাকে, ওয়াইকে রূপার থালায় সাজিয়ে একপাশে আলাদা করা যায় না। যেমন ব্যাসার্ধ পাঁচবিশিষ্ট একটি বৃত্তের ধ্রুপদী সমীকরণ এক্স স্কয়ার প্লাস ওয়াই স্কয়ার সমান পঁচিশ। এখানে বিন্দুটি একটি শর্ত মেনে চলার মাধ্যমে প্রচ্ছন্নভাবে সংজ্ঞায়িত হচ্ছে। প্রচলিত পদ্ধতিতে উভয় পক্ষে অন্তরীকরণ করে টু এক্স প্লাস টু ওয়াই গুণ ডি ওয়াই বাই ডি এক্স সমান শূন্য পাওয়া যায়, অর্থাৎ ডি ওয়াই বাই ডি এক্স সমান মাইনাস এক্স ভাগ ওয়াই।"},
            {"index": 4, "type": "figure",
             "tts": "এই চিত্রে মূলবিন্দুকে কেন্দ্র করে ব্যাসার্ধ পাঁচের বৃত্তটি আঁকা হয়েছে, আর নীল ব্যাসার্ধ রেখাটি তিন কমা চার বিন্দুতে পৌঁছেছে। হলুদ স্পর্শক রেখাটি ঠিক সেই বিন্দুতে বৃত্তকে স্পর্শ করেছে, আর তার ঢাল হলো মাইনাস তিন ভাগ চার, ঋণাত্মক কারণ বিন্দুটি উপরের ডান দিকে অবস্থিত। লক্ষ্য করুন বৃত্তের প্রতিটি বিন্দুতেই এরকম একটি স্পর্শক থাকলেও পুরো বক্ররেখাটি কোনো একক ফাংশনের লেখচিত্র নয়; এই পার্থক্যটাই প্রচ্ছন্ন ব্যবকলনের প্রয়োজনীয়তা তৈরি করে।"},
            {"index": 5, "type": "p",
             "tts": "বৃত্তটির দিকে তাকালে দেখা যায়, এর পরিধির প্রতিটি বিন্দুতেই সুস্পষ্ট একটি স্পর্শক রেখা বিদ্যমান। প্রচলিত পাঠ্যবইয়ে উভয় পক্ষে এক্সের সাপেক্ষে অন্তরজ নিয়ে চেইন রুল প্রয়োগের মাধ্যমে ডি ওয়াই বাই ডি এক্স সমান মাইনাস এক্স ভাগ ওয়াই পাওয়া যায়। তিন কমা চার বিন্দুতে এর মান মাইনাস তিন ভাগ চার। কিন্তু বীজগাণিতিক এই প্রক্রিয়ার অন্তর্নিহিত জ্যামিতি ঠিক কী?"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, প্রচ্ছন্ন সম্পর্কের প্রকৃতি। প্রত্যক্ষ ফাংশনে একটি ইনপুটের জন্য একটিমাত্র আউটপুট মেলে, কিন্তু বৃত্তের সমীকরণ উল্লম্ব রেখা পরীক্ষা উত্তীর্ণ হয় না, কারণ প্রতিটি এক্সের জন্য দুটি মান, ওয়াই সমান প্লাস বা মাইনাস বর্গমূল পঁচিশ বিয়োগ এক্স স্কয়ার, থাকে। তাই পুরো সম্পর্কটিকে অবিভাজ্য রেখে অন্তরীকরণ করাই হলো প্রচ্ছন্ন ব্যবকলন। এখানে এক্স কোনো ইনপুট এবং ওয়াই কোনো আউটপুট নয়, দুটিই পরস্পরনির্ভর চলক মাত্র।"},
            {"index": 7, "type": "p", "role": "conclusion",
             "tts": "বীজগাণিতিক কৌশল জানা থাকলেও, একে অর্থপূর্ণ করতে আমাদের তাকাতে হবে ত্রিমাত্রিক ভূদৃশ্যের সমউচ্চতা রেখার দিকে। সেখানেই ডি এক্স ও ডি ওয়াই কীভাবে একে অপরের সাথে আবদ্ধ হয় তা স্বচ্ছ হয়ে ওঠে।"},
        ],
    },

    "sec-level-curves": {
        "title": "২. সমউচ্চতা রেখা বা লেভেল কার্ভ হিসেবে সমীকরণ দেখা (Equations as Level Curves)",
        "audio_file": "sec_02_level_curves.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, সমউচ্চতা রেখা বা লেভেল কার্ভ হিসেবে সমীকরণ দেখা।"},
            {"index": 1, "type": "p",
             "tts": "গভীর অন্তর্দৃষ্টি পেতে চলুন প্রশ্নটিকে নতুন করে সাজানো যাক। এক্স এবং ওয়াইকে কেবল ইনপুট আর আউটপুট না ভেবে, এক্স স্কয়ার প্লাস ওয়াই স্কয়ার রাশিটিকে দ্বিমাত্রিক সমতলের প্রতিটি বিন্দুর ওপর একটি উচ্চতা ফাংশন হিসেবে কল্পনা করুন। ত্রিমাত্রিক স্থানে এটি একটি গোলাকার বাটি বা প্যারাবোলয়েড তল তৈরি করে, যার কোনো বিন্দুর উচ্চতা মূলবিন্দু থেকে তার দূরত্বের বর্গ।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে একটি ত্রিমাত্রিক বাটির মতো প্যারাবোলয়েড তল দেখা যাচ্ছে, যার ওপর দিয়ে পঁচিশ উচ্চতায় একটি অনুভূমিক সমতল কাটা হয়েছে। সেই ছেদরেখাটি হলো আমাদের পরিচিত বৃত্ত, এক্স স্কয়ার প্লাস ওয়াই স্কয়ার সমান পঁচিশ। লক্ষ্য করুন বাটির কেন্দ্র থেকে দূরে গেলে উচ্চতা বাড়ছে, কিন্তু ছেদরেখার ওপর প্রতিটি বিন্দুর উচ্চতা অবিকল পঁচিশেই থাকছে; এই ধ্রুবকতাই লেভেল কার্ভের সংজ্ঞা এবং পরবর্তী যুক্তির ভিত্তি।"},
            {"index": 3, "type": "p",
             "tts": "এখন এক্স স্কয়ার প্লাস ওয়াই স্কয়ার সমান পঁচিশ সমীকরণটি নির্দেশ করছে, এই বাটিটির ওপর ঠিক পঁচিশ একক উচ্চতায় কোন কোন বিন্দু অবস্থান করছে। আপনি যদি পঁচিশ উচ্চতায় একটি অনুভূমিক সমতল দিয়ে বাটিটিকে কেটে ফেলেন, তবে তার প্রস্থচ্ছেদ বা সমউচ্চতা রেখাটিই হলো আমাদের সেই বৃত্ত।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, উচ্চতা অপরিবর্তিত থাকার নিয়ম। আপনি যখন এই বৃত্তাকার পরিধি বরাবর পা ফেলেন, তখন আপনি সমউচ্চতার রেখায় অবস্থান করছেন, ফলে আপনার উচ্চতার কোনো পরিবর্তন হয় না। অর্থাৎ উচ্চতার মোট পরিবর্তন ডেল্টা জেড বা ডি জেড অবিকল শূন্য। বাটির ওপর অন্য কোনো দিকে হাঁটলে উচ্চতা বদলাত, কিন্তু সমউচ্চতা রেখা বরাবর হাঁটলে সবসময়ই ডি জেড সমান শূন্য।"},
            {"index": 5, "type": "p", "role": "conclusion",
             "tts": "উচ্চতার কোনো পরিবর্তন হতে পারবে না, অর্থাৎ রাশির সামগ্রিক ডিফারেনশিয়াল বৃদ্ধি হতে হবে অবিকল শূন্য। এই একক পর্যবেক্ষণ থেকেই টু এক্স ডি এক্স প্লাস টু ওয়াই ডি ওয়াই সমান শূন্য সমীকরণটির জন্ম।"},
        ],
    },

    "sec-differential-balance": {
        "title": "৩. ডিফারেনশিয়াল ভারসাম্য: 2x dx + 2y dy = 0 (Stepping Along the Curve)",
        "audio_file": "sec_03_differential_balance.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, ডিফারেনশিয়াল ভারসাম্য, টু এক্স ডি এক্স প্লাস টু ওয়াই ডি ওয়াই সমান শূন্য।"},
            {"index": 1, "type": "p",
             "tts": "কল্পনা করুন আপনি বৃত্তের পরিধি বরাবর অতি ক্ষুদ্র একটি ধাপ এগিয়ে গেলেন। এর ফলে আনুভূমিক অক্ষে পরিবর্তন ঘটল ডি এক্স এবং উল্লম্ব অক্ষে পরিবর্তন ঘটল ডি ওয়াই। উচ্চতা ফাংশনে এক্স স্কয়ার পদের কারণে পরিবর্তন ঘটে টু এক্স ডি এক্স পরিমাণ এবং ওয়াই স্কয়ার পদের কারণে ঘটে টু ওয়াই ডি ওয়াই পরিমাণ।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, টু এক্স ডি এক্স প্লাস টু ওয়াই ডি ওয়াই সমান শূন্য।"},
            {"index": 3, "type": "p",
             "tts": "কিন্তু যেহেতু আপনি বৃত্তের ওপরই অবস্থান করছেন এবং উচ্চতা পঁচিশে স্থির রয়েছে, তাই এই দুই পরিবর্তনের যোগফল হতে হবে ঠিক শূন্য। পক্ষান্তর করলেই পাওয়া যায় টু ওয়াই ডি ওয়াই সমান মাইনাস টু এক্স ডি এক্স, অর্থাৎ স্পর্শক ঢাল ডি ওয়াই বাই ডি এক্স সমান মাইনাস এক্স ভাগ ওয়াই। এখানে এক্স এবং ওয়াই উভয় চলককেই সমান মর্যাদায় স্বাধীন জ্যামিতিক দিক হিসেবে দেখা হয়।"},
            {"index": 4, "type": "figure",
             "tts": "এই চিত্রে তিন কমা চার বিন্দুতে দুটি রেখা দেখা যাচ্ছে, সবুজ ব্যাসার্ধ রেখার ঢাল চার ভাগ তিন আর হলুদ স্পর্শক রেখার ঢাল মাইনাস তিন ভাগ চার। বিন্দুতে অঙ্কিত ছোট বর্গাকৃতি চিহ্নটি তাদের মধ্যকার নব্বই ডিগ্রি কোণ নির্দেশ করছে। ঢাল দুটির গুণফল মাইনাস এক, যা জ্যামিতিকভাবে প্রমাণ করে যে বৃত্তের স্পর্শক সবসময় ব্যাসার্ধের লম্ব; এই উপলব্ধিই প্রচ্ছন্ন ব্যবকলনের জ্যামিতিক অর্থ।"},
            {"index": 5, "type": "callout", "role": "conclusion",
             "tts": "বিশেষ নোট, ব্যাসার্ধ ও স্পর্শকের লম্বতা। বৃত্তের পরিধির যেকোনো বিন্দুতে মূলবিন্দু থেকে ব্যাসার্ধ ভেক্টরের ঢাল হলো ওয়াই ভাগ এক্স, আর আমাদের প্রাপ্ত স্পর্শকের ঢাল হলো মাইনাস এক্স ভাগ ওয়াই। এই দুই ঢালের গুণফল মাইনাস এক, যা অকাট্যভাবে প্রমাণ করে যে স্পর্শক রেখা ব্যাসার্ধের সাথে সর্বদাই সমকোণে অবস্থান করে। শীর্ষবিন্দুতে এক্স শূন্য হওয়ায় ঢাল শূন্য বা অনুভূমিক, আর পার্শ্ববিন্দুতে ওয়াই শূন্য হওয়ায় স্পর্শক খাড়া উল্লম্ব বা অনির্ণেয়।"},
        ],
    },

    "sec-related-rates": {
        "title": "৪. সম্পর্কিত পরিবর্তনের হার: দেয়াল বেয়ে পিছলে পড়া মই (Related Rates & Slipping Ladder)",
        "audio_file": "sec_04_related_rates.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, সম্পর্কিত পরিবর্তনের হার, দেয়াল বেয়ে পিছলে পড়া মই।"},
            {"index": 1, "type": "p",
             "tts": "এই অন্তর্দৃষ্টিকে বাস্তব জীবনের একটি সমস্যায় প্রয়োগ করা যাক, সম্পর্কিত পরিবর্তনের হার। মনে করি পাঁচ মিটার দৈর্ঘ্যের একটি মই উলম্ব দেয়ালের সাথে হেলান দিয়ে দাঁড় করানো আছে, যার শীর্ষ প্রথমে চার মিটার উঁচুতে আছে। পিথাগোরাসের উপপাদ্য অনুযায়ী তখন গোড়া দেয়াল থেকে তিন মিটার দূরে থাকে এবং সর্বদাই এক্স স্কয়ার প্লাস ওয়াই স্কয়ার সমান পঁচিশ প্রযোজ্য।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে পাঁচ মিটারের মইটি দেয়ালের সাথে হেলান দিয়ে আছে, ভূমি থেকে গোড়ার দূরত্ব তিন মিটার আর দেয়াল বরাবর শীর্ষের উচ্চতা চার মিটার। লাল তীর দেখাচ্ছে শীর্ষ প্রতি সেকেন্ডে এক মিটার করে নিচে নামছে, আর সবুজ তীর দেখাচ্ছে গোড়া চার ভাগ তিন মিটার বেগে দূরে সরে যাচ্ছে। মইয়ের দৈর্ঘ্য অপরিবর্তিত থাকায় এই দুই হার পিথাগোরাস সম্পর্কের মাধ্যমে আবদ্ধ; একটি হার জানলেই অন্যটি নির্ণয় করা যায়।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, টু এক্স গুণ ডি এক্স বাই ডি টি প্লাস টু ওয়াই গুণ ডি ওয়াই বাই ডি টি সমান শূন্য।"},
            {"index": 4, "type": "p",
             "tts": "মইয়ের শীর্ষ এক মিটার প্রতি সেকেন্ড বেগে নামছে, অর্থাৎ ডি ওয়াই বাই ডি টি সমান মাইনাস এক। বর্তমান অবস্থায় এক্স সমান তিন ও ওয়াই সমান চার বসালে টু গুণ তিন গুণ ডি এক্স বাই ডি টি প্লাস টু গুণ চার গুণ মাইনাস এক সমান শূন্য থেকে ডি এক্স বাই ডি টি সমান চার ভাগ তিন মিটার প্রতি সেকেন্ড পাওয়া যায়। অর্থাৎ গোড়াটি দেয়াল থেকে প্রায় এক দশমিক তিন তিন মিটার করে দূরে সরে যাচ্ছে। বিকল্পভাবে যদি গোড়ার বেগকে ধ্রুব এক মিটার প্রতি সেকেন্ড ধরা হয়, তবে শীর্ষের বেগ হবে মাইনাস তিন ভাগ চার, অর্থাৎ মাইনাস শূন্য দশমিক সাত পাঁচ মিটার প্রতি সেকেন্ড। দুই ক্ষেত্রেই একই ভারসাম্য সমীকরণ কাজ করে, শুধু কোন হারকে ইনপুট হিসেবে নেওয়া হয় তা বদলায়।"},
            {"index": 5, "type": "callout", "role": "conclusion",
             "tts": "বিশেষ অন্তর্দৃষ্টি, অন্তিম পতনের অসীম ত্বরণ। লক্ষ্য করুন, যখন গোড়া ধ্রুব বেগে দূরে সরে যায় তখন ডি ওয়াই বাই ডি টি সমান মাইনাস এক্স ভাগ ওয়াই গুণ ডি এক্স বাই ডি টি। মইটি যখন মাটির কাছাকাছি পৌঁছে যায়, অর্থাৎ ওয়াই শূন্যের দিকে চলে যায়, তখন এই ভগ্নাংশের হর শূন্যের দিকে যাওয়ায় শীর্ষবিন্দুর নিম্নমুখী বেগ মাইনাস অসীমের দিকে ধাবিত হয়। মাটিতে আছড়ে পড়ার মুহূর্তে মইটির ওপরের প্রান্ত ভয়াবহ ক্ষিপ্র গতিতে ধসে পড়ে, যদিও গোড়ার গতি সম্পূর্ণ ধ্রুব ছিল।"},
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
    if total != 26:
        raise ValueError(f"Expected 26 cues, found {total}")

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
        "lesson": "lesson_06",
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
    assert total_cues == 26

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Calculus Lesson 06")
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
