# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Differential Equations Lesson 03
("Oscillations, Damping, and Resonance", Bengali) to the gold standard.

Deterministic, re-runnable, self-contained:
  * 32 cues in 4 narrated sections with EXACTLY the same section IDs, audio_file
    names, alias and section order as the live narration-engine DOM / manifest.json
    (verified 8/9/7/8 for sec-shm-intro / sec-damped-motion / sec-damping-regimes /
    sec-driven-resonance). sec-figures, sec-interactive-lab, sec-quizzes and
    sec-video-note carry data-no-narration="true" and are deliberately excluded.
    L03 has NO dedicated official 3B1B dubbed video (content+audio only); the
    optional video-src / sec-video-note is never touched.
  * Section IDs and block types were extracted FIRST from the live DOM through
    narration_engine.js's own selector
    ('h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
     .code-showcase, .formula-box'), not guessed from prose. Exact DOM callout
    variants (callout-gold / callout-purple / callout-green) are preserved.
  * Visual explanations are genuine, natural 2-4 sentence teacher phrasing —
    the artificial label "চিত্র প্রদর্শনী" is never used.
  * Fully phonetic spoken Bengali (no TeX / Latin / markup). Safeguards:
      SHM -> এস এইচ এম, damping -> ড্যাম্পিং, resonance -> রেজোন্যান্স,
      underdamped -> আন্ডারড্যাম্পড, RK4 -> আর কে ফোর,
      dy/dt -> ডি ওয়াই বাই ডি টি, dx/dt -> ডি এক্স বাই ডি টি,
      x'' -> এক্স ডাবল ডট,  ω0 -> ওমেগা নট,  e^{rt} -> ই টু দ্য পাওয়ার আর টি.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, chapter-quote -3%, p +2%, figure -4%, callout +0%,
      formula-box -8%, conclusion -3%.
  * A real 350 ms silence chunk between cues, so manifest millisecond timings
    match the concatenated audio exactly.
  * ffmpeg -c copy concat into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST).
  * Bumps the page cache-buster manifest.js?v=N -> ?v=N+1.
  * verify_in_chrome() re-checks everything headlessly with channel=chrome.
  * The _backup_before_expressive_build/ folder is NEVER touched.

Usage:
  python governance/build_expressive_teacher_audio_de03.py
  python governance/build_expressive_teacher_audio_de03.py --verify-only
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
                         "differential_equations", "lesson_03")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "differential_equations",
                         "lesson_03.html")
MANIFEST_TITLE = "অধ্যায় ০৩ — দোলন, অবদমন ও অনুনাদ (Oscillations, Damping & Resonance)"

# Prosody keyed by cue type: (rate, pitch, volume)
PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
    "h3":            ("-3%", "+0Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),   # reflective quote
    "p":             ("+2%", "+0Hz", "+0%"),   # natural teacher pace
    "figure":        ("-4%", "+0Hz", "+0%"),   # slower, considerate visual explanation
    "callout":       ("+0%", "+0Hz", "+0%"),
    "callout-blue":  ("+0%", "+0Hz", "+0%"),   # exact DOM variants of callout
    "callout-gold":  ("+0%", "+0Hz", "+0%"),
    "callout-purple":("+0%", "+0Hz", "+0%"),
    "callout-green": ("+0%", "+0Hz", "+0%"),
    "formula-box":   ("-8%", "+0Hz", "+0%"),   # slow and deliberate
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")     # calm concluding prose

ALLOWED_CUE_TYPES = set(PROSODY_DEFAULT) | {"conclusion"}

# Exact DOM block-type sequence per narrated section (extracted from narration_engine).
EXPECTED_TYPES = {
    "sec-shm-intro":         ["h2", "chapter-quote", "p", "p", "figure", "p", "formula-box", "p"],
    "sec-damped-motion":     ["h2", "p", "figure", "formula-box", "p", "formula-box", "callout-gold", "p", "p"],
    "sec-damping-regimes":   ["h2", "p", "figure", "p", "callout-purple", "p", "p"],
    "sec-driven-resonance":  ["h2", "p", "formula-box", "p", "figure", "p", "callout-green", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-shm-intro":         "sec_01_shm_intro.mp3",
    "sec-damped-motion":     "sec_02_damped_motion.mp3",
    "sec-damping-regimes":   "sec_03_damping_regimes.mp3",
    "sec-driven-resonance":  "sec_04_driven_resonance.mp3",
}
EXPECTED_ALIASES = {
    "sec-shm-intro":         "sec_01_shm_intro",
    "sec-damped-motion":     "sec_02_damped_motion",
    "sec-damping-regimes":   "sec_03_damping_regimes",
    "sec-driven-resonance":  "sec_04_driven_resonance",
}
EXPECTED_COUNT = {
    "sec-shm-intro": 8, "sec-damped-motion": 9,
    "sec-damping-regimes": 7, "sec-driven-resonance": 8,
}
EXPECTED_TOTAL = 32

OLD_VERSIONS = []  # recorded during bump_page_manifest_version()

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (32 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-shm-intro": {
        "title": "সরল ছন্দিত স্পন্দন ও হুকের সূত্র",
        "alias": "sec_01_shm_intro",
        "audio_file": "sec_01_shm_intro.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, সরল ছন্দিত স্পন্দন ও হুকের সূত্র।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "পদার্থবিজ্ঞানী লর্ড কেলভিন বলেছিলেন, প্রকৃতির প্রতিটি কম্পমান সুরেই ডিফারেনশিয়াল ইকুয়েশনের নিখুঁত ছন্দের খেলা দেখতে পাওয়া যায়।"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, মহাবিশ্বের যেকোনো স্থিতিশীল ব্যবস্থা, স্প্রিংয়ে ঝুলন্ত ভর হোক কিংবা বাদ্যযন্ত্রের তার, সাম্যাবস্থার সামান্যতম বিচ্যুতিতে অবিকল একই আচরণ করে। এই সার্বজনীন আচরণের নামই সরল ছন্দিত স্পন্দন, বা এস এইচ এম।"},
            {"index": 3, "type": "p",
             "tts": "ধরা যাক, ঘর্ষণহীন অনুভূমিক মেঝের ওপর এম ভরের একটি ব্লককে আদর্শ স্প্রিংয়ের সাথে যুক্ত করা হলো। স্প্রিংটিকে প্রাকৃতিক দৈর্ঘ্য থেকে এক্স পরিমাণ টেনে ছেড়ে দিলে ১৬৭৮ সালে রবার্ট হুকের আবিষ্কৃত নীতি অনুসারে স্প্রিংটি সরণের বিপরীত দিকে প্রত্যয়নী বল প্রয়োগ করে।"},
            {"index": 4, "type": "figure", "visual": True,
             "tts": "এখানে ঘর্ষণহীন মেঝের ওপর এম ভরের ব্লকটি স্প্রিংয়ের সাথে যুক্ত এবং সাম্যাবস্থা থেকে এক্স পরিমাণ সরে গেছে। লাল তীরচিহ্নটি প্রত্যয়নী বল নির্দেশ করছে, যা সবসময় সরণের ঠিক বিপরীত দিকে কাজ করে। লক্ষ্য করুন, স্প্রিং ধ্রুবক কে যত বড়, একই সরণে বল তত বেশি, আর এই সমানুপাতিকতাই হুকের সূত্রের মূল কথা।"},
            {"index": 5, "type": "p",
             "tts": "নিউটনের দ্বিতীয় গতিসূত্র প্রয়োগ করলে ভর গুণ ত্বরণ সমান প্রযুক্ত বল, যা থেকে আমরা পাই দ্বিতীয় ক্রমের ধ্রুপদী রৈখিক সমীকরণ, এম ডি স্কয়ার এক্স বাই ডি টি স্কয়ার সমান মাইনাস কে এক্স।"},
            {"index": 6, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, হুকের সূত্র এফ সমান মাইনাস কে এক্স। গতি সমীকরণ এম ডি স্কয়ার এক্স বাই ডি টি স্কয়ার যোগ কে এক্স সমান শূন্য, যার রূপান্তর ডি স্কয়ার এক্স বাই ডি টি স্কয়ার যোগ ওমেগা নট স্কয়ার এক্স সমান শূন্য। এখানে ওমেগা নট সমান বর্গমূল কে ভাগ এম, পর্যায়কাল টি সমান দুই পাই ভাগ ওমেগা নট, আর সমাধান এক্স অফ টি সমান এ কস অফ ওমেগা নট টি মাইনাস ফাই।"},
            {"index": 7, "type": "p",
             "tts": "এই সমীকরণের সাধারণ সমাধান হলো বিশুদ্ধ সাইন তরঙ্গ, এক্স অফ টি সমান এ কস অফ ওমেগা নট টি মাইনাস ফাই। ফেজ স্পেসে অবস্থান এক্স আর বেগ ভি আঁকলে তা চিরন্তন আবদ্ধ উপবৃত্ত তৈরি করে, যা যান্ত্রিক শক্তির নিখুঁত নিত্যতা প্রকাশ করে। কিন্তু বাস্তব পৃথিবীতে কোনো গতিই ঘর্ষণহীন নয়, তাই পরের পরিচ্ছেদে আমরা দেখব, সান্দ্র ঘর্ষণে এই উপবৃত্তাকার নৃত্য কেমন রূপ নেয়।"},
        ],
    },

    "sec-damped-motion": {
        "title": "সান্দ্র বাধা ও চারিত্রিক সমীকরণ",
        "alias": "sec_02_damped_motion",
        "audio_file": "sec_02_damped_motion.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, সান্দ্র বাধা ও চারিত্রিক সমীকরণ।"},
            {"index": 1, "type": "p",
             "tts": "বাস্তব যেকোনো স্পন্দক বাতাস, তরল কিংবা আণবিক ঘর্ষণের মুখোমুখি হয়। নিম্ন ও মাঝারি বেগে এই সান্দ্র বলটি বস্তুর বেগের সমানুপাতিক এবং গতির বিপরীতমুখী হয়, এফ ড্যাম্পিং সমান মাইনাস বি গুণ ভি, যেখানে বি হলো সান্দ্রতা গুণাঙ্ক।"},
            {"index": 2, "type": "figure", "visual": True,
             "tts": "এই চিত্রে একই স্প্রিং ভর ব্যবস্থায় ব্লকের বেগ ভি ডানদিকে নির্দেশ করছে, আর নীল তীরচিহ্নটি সান্দ্র বাধাকে বিপরীত দিকে দেখাচ্ছে। বেগ যত বাড়ে, এই রোধী বল তত শক্তিশালী হয়, তাই গতিশক্তি ক্রমশ তাপে রূপান্তরিত হয়। লক্ষ্য করুন, ঘর্ষণহীন ক্ষেত্রের সেই আবদ্ধ উপবৃত্ত এখন আর টিকে থাকবে না, গতিপথ ভেতরের দিকে কুঁকড়ে যাবে।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, অবদমিত হারমোনিক অসিলেটরের গতি সমীকরণ, এম ডি স্কয়ার এক্স বাই ডি টি স্কয়ার যোগ বি ডি এক্স বাই ডি টি যোগ কে এক্স সমান শূন্য। পুরো সমীকরণটিকে এম দিয়ে ভাগ করলে পাই ডি স্কয়ার এক্স বাই ডি টি স্কয়ার যোগ টু গামা ডি এক্স বাই ডি টি যোগ ওমেগা নট স্কয়ার এক্স সমান শূন্য, যেখানে গামা সমান বি ভাগ দুই এম এবং ওমেগা নট স্কয়ার সমান কে ভাগ এম।"},
            {"index": 4, "type": "p",
             "tts": "নিউটনের সূত্রে এই প্রতিরোধী বলটি অন্তর্ভুক্ত করলে আমরা পাই পূর্ণ অবদমিত হারমোনিক সমীকরণ, এম এক্স ডাবল ডট যোগ বি এক্স ডট যোগ কে এক্স সমান শূন্য। পুরো সমীকরণটিকে ভর এম দিয়ে ভাগ করে আদর্শ রূপ পাই, এক্স ডাবল ডট যোগ টু গামা এক্স ডট যোগ ওমেগা নট স্কয়ার এক্স সমান শূন্য, যেখানে গামা সমান বি ভাগ দুই এম।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, অয়লারের সূচকীয় অনুমান এক্স অফ টি সমান ই টু দ্য পাওয়ার আর টি প্রতিস্থাপন করলে পাওয়া যায়, ই টু দ্য পাওয়ার আর টি গুণ বন্ধনী আর স্কয়ার যোগ টু গামা আর যোগ ওমেগা নট স্কয়ার সমান শূন্য। সুতরাং চারিত্রিক সমীকরণ আর স্কয়ার যোগ টু গামা আর যোগ ওমেগা নট স্কয়ার সমান শূন্য, আর এর মূল আর সমান মাইনাস গামা প্লাস মাইনাস বর্গমূল গামা স্কয়ার মাইনাস ওমেগা নট স্কয়ার।"},
            {"index": 6, "type": "callout-gold",
             "tts": "বিশেষ নোট, চারিত্রিক সমীকরণের দর্শন। যেহেতু বাস্তব সময় টি এর জন্য ই টু দ্য পাওয়ার আর টি কখনো শূন্য নয়, তাই ডিফারেনশিয়াল ইকুয়েশনটি সিদ্ধ হতে হলে বন্ধনীর ভেতরের দ্বিঘাত রাশিটিই অবশ্যই শূন্য হতে হবে। একটা ক্যালকুলাসের অন্তরজ সমীকরণ রূপ নিল হাইস্কুলের সাধারণ দ্বিঘাত সমীকরণে! এই মূলগুলোর চরিত্রের ওপরই নির্ভর করে প্রকৃতিতে গতির সমগ্র ভবিষ্যৎ রূপরেখা।"},
            {"index": 7, "type": "p",
             "tts": "লক্ষ্য করুন, প্রতিটি পদে এক্স এবং তার অন্তরজগুলো প্রথম ঘাতে রয়েছে, কোনো অরৈখিক গুণন বা ত্রিকোণমিতিক পদ নেই। এটি একটি দ্বিতীয় ক্রমের রৈখিক হোমোজেনিয়াস সাধারণ ডিফারেনশিয়াল ইকুয়েশন, আর এই রৈখিকতাই আমাদের সূচকীয় সমাধান খোঁজার অনুমতি দেয়।"},
            {"index": 8, "type": "p",
             "tts": "অয়লারের অনন্য অন্তর্দৃষ্টি হলো, ই টু দ্য পাওয়ার আর টি এর ডেরিভেটিভ সর্বদা একই ধরণের সূচকীয় ফাংশন ফিরিয়ে দেয়, তাই আমরা সমাধান হিসেবে এক্স অফ টি সমান ই টু দ্য পাওয়ার আর টি প্রস্তাব করি। নিশ্চায়ক ডেল্টা সমান গামা স্কয়ার মাইনাস ওমেগা নট স্কয়ারের চিহ্ন ধনাত্মক, শূন্য নাকি ঋণাত্মক, তার ওপর ভিত্তি করে সৃষ্টি হবে তিনটি সম্পূর্ণ ভিন্ন ভৌত জগৎ।"},
        ],
    },

    "sec-damping-regimes": {
        "title": "তিনটি অবদমন রূপ ও ফেজ স্পেস স্পাইরাল",
        "alias": "sec_03_damping_regimes",
        "audio_file": "sec_03_damping_regimes.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, তিনটি অবদমন রূপ ও ফেজ স্পেস স্পাইরাল।"},
            {"index": 1, "type": "p",
             "tts": "নিশ্চায়ক গামা স্কয়ার মাইনাস ওমেগা নট স্কয়ারের মানের ওপর নির্ভর করে প্রকৃতিতে তিনটি সুস্পষ্ট অবদমন শাসনতন্ত্র দেখা যায়।"},
            {"index": 2, "type": "figure", "visual": True,
             "tts": "এখানে এক্স ভি ফেজ সমতলে কেন্দ্রের চারপাশের আবদ্ধ উপবৃত্তগুলো ভেঙে ভেতরের দিকে পাক খেয়ে মূলবিন্দুর দিকে অগ্রসর হচ্ছে। প্রতিটি সর্পিল পথই একই স্পাইরাল সিঙ্কে পৌঁছায়, অর্থাৎ শুরুর অবস্থা যেমনই হোক, শক্তি ক্ষয়ের কারণে ব্যবস্থা শেষ পর্যন্ত শূন্যে স্থির হয়। ক্রিটিক্যাল বা ওভারড্যাম্পড ক্ষেত্রে এই ঘূর্ণন কেটে গিয়ে সোজা নোডাল পথে রূপ নেয়।"},
            {"index": 3, "type": "p",
             "tts": "প্রথম রূপটি হলো আন্ডারড্যাম্পড বা দুর্বল অবদমন, যেখানে গামা ওমেগা নটের চেয়ে ছোট। বর্গমূলের ভেতরে ঋণাত্মক সংখ্যা এসে মূল দুটি জটিল অনুবন্ধী হয়, আর সমাধান দাঁড়ায় এ গুণ ই টু দ্য পাওয়ার মাইনাস গামা টি গুণ কস অফ ওমেগা ডি টি মাইনাস ফাই। দ্বিতীয় রূপটি হলো ক্রিটিক্যাল ড্যাম্পিং, যেখানে গামা ওমেগা নটের ঠিক সমান, মূলদ্বয় অভিন্ন বাস্তব সংখ্যা আর সমান মাইনাস গামা, আর সমাধান এক্স সমান সি ওয়ান যোগ সি টু টি গুণ ই টু দ্য পাওয়ার মাইনাস গামা টি।"},
            {"index": 4, "type": "callout-purple",
             "tts": "বিশেষ নোট, ফেজ স্পেসে উপবৃত্ত ভেঙে স্পাইরাল সিঙ্ক। আদর্শ স্পন্দকের যে উপবৃত্তগুলো চিরকাল আবদ্ধ ছিল, অবদমনে শক্তি ক্ষয়প্রাপ্ত হওয়ায় ট্র্যাজেক্টরিগুলো ভেতরের দিকে কুঁকড়ে যায়। আন্ডারড্যাম্পড মোশনে প্রতিটি পথ মূলবিন্দুর দিকে একটি নিখুঁত লগারিদমিক সর্পিল স্পাইরাল তৈরি করে। ক্রিটিক্যাল আর ওভারড্যাম্পড ক্ষেত্রে ঘূর্ণন না হয়ে সরাসরি নোডাল সিঙ্কে পৌঁছায়।"},
            {"index": 5, "type": "p",
             "tts": "তৃতীয় রূপটি হলো ওভারড্যাম্পড বা অতি অবদমন, যেখানে গামা ওমেগা নটের চেয়ে অনেক বড়। মধুর ভেতরের মতো তীব্র সান্দ্র বাধায় মূল দুটি পৃথক ঋণাত্মক বাস্তব সংখ্যা হয়, আর বস্তুটি কোনো দোলন ছাড়াই অত্যন্ত মন্থর গতিতে মূলবিন্দুর দিকে ধাবিত হয়।"},
            {"index": 6, "type": "p",
             "tts": "এই তিনটি রূপের মাধ্যমেই ফেজ সমতলের প্রবাহ উপবৃত্তীয় সেন্টার থেকে স্পাইরাল সিঙ্কে আর সবশেষে নোডাল সিঙ্কে রূপান্তরিত হয়। কিন্তু যদি আমরা এই ক্ষয়িষ্ণু ব্যবস্থাকে বাইরে থেকে নির্দিষ্ট ছন্দে ক্রমাগত শক্তি যোগান দিতে থাকি, তখন কী ঘটবে?"},
        ],
    },

    "sec-driven-resonance": {
        "title": "প্রণোদিত দোলন, অনুনাদ ও রৈখিক সিস্টেম",
        "alias": "sec_04_driven_resonance",
        "audio_file": "sec_04_driven_resonance.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, প্রণোদিত দোলন, অনুনাদ ও রৈখিক সিস্টেম।"},
            {"index": 1, "type": "p",
             "tts": "নিকোলা টেসলা বলেছিলেন, ছোট একটি চালক বলও যদি প্রাকৃতিক কম্পাঙ্কের সুরে সুর মেলায়, তবে তা সৃষ্টি করতে পারে অকল্পনীয় শক্তি। যদি অবদমিত স্পন্দকের ওপর বাইরে থেকে পর্যায়বৃত্ত চালক বল এফ নট কস ওমেগা টি প্রয়োগ করা হয়, তবে সমীকরণটি রৈখিক নন হোমোজেনিয়াস ওডিই রূপ ধারণ করে।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, প্রণোদিত দোলকের সমীকরণ, এক্স ডাবল ডট যোগ টু গামা এক্স ডট যোগ ওমেগা নট স্কয়ার এক্স সমান এফ নট ভাগ এম গুণ কস ওমেগা টি। স্থির দশার সমাধান এক্স পি অফ টি সমান এ অফ ওমেগা গুণ কস অফ ওমেগা টি মাইনাস ডেল্টা, যেখানে বিস্তার এ অফ ওমেগা সমান এফ নট ভাগ এম ভাগ বর্গমূল ওমেগা নট স্কয়ার মাইনাস ওমেগা স্কয়ারের বর্গ যোগ চার গামা স্কয়ার ওমেগা স্কয়ার। অনুনাদের শর্ত ওমেগা রেজ সমান বর্গমূল ওমেগা নট স্কয়ার মাইনাস দুই গামা স্কয়ার, যা প্রায় ওমেগা নটের সমান।"},
            {"index": 3, "type": "p",
             "tts": "রৈখিকতার নীতির কারণে সামগ্রিক সমাধান দুটি অংশের যোগফল, এক্স অফ টি সমান এক্স এইচ অফ টি যোগ এক্স পি অফ টি। প্রথমটি ক্ষণস্থায়ী ট্রানজিয়েন্ট সমাধান যা অবদমনের কারণে মিলিয়ে যায়, কিন্তু দ্বিতীয়টি স্থির দশার সমাধান চালক কম্পাঙ্ক ওমেগা তে চিরকাল টিকে থাকে। যখন চালক কম্পাঙ্ক ওমেগা প্রাকৃতিক কম্পাঙ্ক ওমেগা নটের কাছাকাছি পৌঁছায়, তখন হর সর্বনিম্ন হয়ে বিস্তার নাটকীয়ভাবে বৃদ্ধি পায়, আর এই জাদুকরী ঘটনাকেই বলে অনুনাদ বা রেজোন্যান্স।"},
            {"index": 4, "type": "figure", "visual": True,
             "tts": "এই রেখাচিত্রে অনুভূমিক অক্ষে চালক কম্পাঙ্ক ওমেগা আর উল্লম্ব অক্ষে স্থির দশার বিস্তার এ অফ ওমেগা দেখানো হয়েছে। কম অবদমনে চূড়াটি ওমেগা নটের কাছে অত্যন্ত সুউচ্চ ও সরু, আর সেটাই হলো রেজোন্যান্স। অবদমন বাড়ালে চূড়া নিচু ও প্রশস্ত হয়, আর ঠিক এই কারণেই সেতু বা যন্ত্রাংশ নির্দিষ্ট ছন্দে চালিত হলে ভেঙে পড়তে পারে।"},
            {"index": 5, "type": "p",
             "tts": "সবশেষে এই পুরো ব্যবস্থাকে আমরা রৈখিক বীজগণিতের ভাষায় প্রকাশ করতে পারি। অবস্থান এক্স আর বেগ ভি নিয়ে স্টেট ভেক্টর সংজ্ঞায়িত করলে সমীকরণ জোট দাঁড়ায় ডি এক্স বাই ডি টি সমান এ গুণ এক্স, যেখানে ম্যাট্রিক্স এ এর আইগেনভ্যালুগুলোই অবিকল আমাদের চারিত্রিক সমীকরণের মূল।"},
            {"index": 6, "type": "callout-green",
             "tts": "বিশেষ নোট, আইগেনভ্যালু ও ফেজ পোর্ট্রেটের পরম সাদৃশ্য। ম্যাট্রিক্স এ এর ট্রেস সমান মাইনাস দুই গামা এবং ডিটারমিন্যান্ট সমান ওমেগা নট স্কয়ার, যা ধনাত্মক। ট্রেস ঋণাত্মক হওয়ায় বাস্তব অংশ সবসময় ঋণাত্মক, আর এটাই শক্তির অবক্ষয় নিশ্চিত করে। জটিল আইগেনভ্যালু সমতলকে আবর্তন করে স্পাইরাল সিঙ্ক তৈরি করে, আর বাস্তব আইগেনভ্যালু সরাসরি নোডাল সিঙ্ক তৈরি করে। ডিফারেনশিয়াল ইকুয়েশন আর রৈখিক বীজগণিত আসলে একই মহাজাগতিক সত্যের দুটি ভিন্ন ভাষা!"},
            {"index": 7, "type": "p", "role": "conclusion",
             "tts": "এই মৌলিক উপলব্ধি সঙ্গে নিয়েই আমরা পরবর্তী অধ্যায়ে আংশিক ডিফারেনশিয়াল ইকুয়েশন ও তাপ সমীকরণের রহস্য উন্মোচনে অগ্রসর হব। সরল স্প্রিং থেকে পরমাণুর অনুনাদ পর্যন্ত, এই গাণিতিক ভিত্তিই আমাদের প্রস্তুত করে মহাবিশ্বের স্থান কালে ছড়িয়ে থাকা তরঙ্গের ভাষা বুঝতে।"},
        ],
    },
}

# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"


def assert_clean_scripts():
    """Fail before any TTS work if a script has markup/Latin/the forbidden label."""
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(
                    f"{sec_id} cue {cue['index']}: forbidden chars {bad!r} in {cue['tts']!r}")
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: artificial figure label present")

    if list(SECTIONS_DATA) != list(EXPECTED_TYPES):
        raise ValueError("Section ids / order changed")
    total = 0
    for sec_id, sec in SECTIONS_DATA.items():
        types = [c["type"] for c in sec["cues"]]
        if types != EXPECTED_TYPES[sec_id]:
            raise ValueError(f"{sec_id}: cue type/order mismatch -> {types}")
        if sec["audio_file"] != EXPECTED_AUDIO_FILES[sec_id]:
            raise ValueError(f"{sec_id}: audio_file mismatch")
        if sec["alias"] != EXPECTED_ALIASES[sec_id]:
            raise ValueError(f"{sec_id}: alias mismatch")
        indices = [c["index"] for c in sec["cues"]]
        if indices != list(range(len(indices))):
            raise ValueError(f"{sec_id}: cue indices are not 0..n-1")
        if len(indices) != EXPECTED_COUNT[sec_id]:
            raise ValueError(f"{sec_id}: cue count mismatch")
        total += len(indices)
    if total != EXPECTED_TOTAL:
        raise ValueError(f"Expected {EXPECTED_TOTAL} cues, found {total}")

    # Natural figure explanations must be 2-4 sentences (no artificial label).
    visuals = 0
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            if cue.get("visual"):
                sentences = [s for s in cue["tts"].split("।") if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(
                        f"{sec_id} cue {cue['index']}: visual explanation has "
                        f"{len(sentences)} sentences")
                visuals += 1
    return visuals


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
        if not valid_audio(chunk):
            tag = "conclusion" if cue.get("role") == "conclusion" else cue["type"]
            print(f"  cue {idx:02d} [{tag:<13}] {rate:>4} {pitch:>5}  {cue['tts'][:30]}...")
            await synth_cue(cue["tts"], chunk, rate, pitch, volume)
        else:
            print(f"  cue {idx:02d} [{cue['type']:<13}] cached")
        chunk_paths.append(chunk)
        durations.append(get_duration_ms(chunk))

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

    print(f"  => {sec['audio_file']}: {len(manifest_cues)} cues, "
          f"{cursor / 1000.0:.2f}s, {os.path.getsize(final_path)} bytes")

    return {
        "section_id": sec_id,
        "alias": sec["alias"],
        "title": sec["title"],
        "audio_file": sec["audio_file"],
        "total_duration_ms": round(cursor, 1),
        "cues": manifest_cues,
    }


def bump_page_manifest_version():
    """manifest.js?v=N -> ?v=N+1 so browsers reload the rebuilt manifest."""
    global OLD_VERSIONS
    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    pattern = re.compile(r"(manifest\.js\?v=)(\d+)")
    matches = pattern.findall(html)
    if not matches:
        raise RuntimeError("Page manifest cache-buster not found")
    OLD_VERSIONS = [int(m[1]) for m in matches]
    new_html, count = pattern.subn(
        lambda m: m.group(1) + str(int(m.group(2)) + 1), html)
    with open(PAGE_PATH, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_html)
    print(f"  bumped manifest cache-buster: {matches[0][1]} -> "
          f"{int(matches[0][1]) + 1} ({count} occurrence(s))")


async def build_all():
    visuals = assert_clean_scripts()
    print(f"Validated {sum(len(s['cues']) for s in SECTIONS_DATA.values())} clean cues "
          f"in {len(SECTIONS_DATA)} sections ({visuals} natural visual explanations, "
          f"0 artificial figure labels).")

    built = {}
    for sec_id, sec in SECTIONS_DATA.items():
        built[sec_id] = await build_section(sec_id, sec)

    # Manifest keys are exactly the 4 canonical DOM section ids (in DOM order).
    manifest_sections = {sec_id: built[sec_id] for sec_id in SECTIONS_DATA}

    manifest_data = {
        "course": "differential_equations",
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
        assert msec["alias"] == EXPECTED_ALIASES[sec_id]
        assert msec["audio_file"] == EXPECTED_AUDIO_FILES[sec_id]
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
    assert total_cues == EXPECTED_TOTAL

    print("\n" + "=" * 70)
    print("BUILD COMPLETE - expressive teacher audio, Differential Equations Lesson 03")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<22} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTIONS_DATA)} sections, "
          f"{total_ms / 1000.0:.2f}s, {visuals} natural visual explanations.")
    print("  manifest.json is valid JSON; all 4 mp3 files exist and are non-empty.")
    print("=" * 70)


# --------------------------------------------------------------------------- #
# Headless Chrome verification (channel=chrome)
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
      const anns = [...node.querySelectorAll('annotation[encoding="application/x-tex"]')]
                     .map(a => a.textContent);
      blocks.push({type: domType(node), tex: anns});
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
                        tex: s.blocks.filter(b => b.type === 'formula-box').map(b => b.tex)})),
    engine,
    sectionEls: sectionEls.map(s => ({id: s.id, noNarration: s.getAttribute('data-no-narration')}))
  };
}"""


def verify_in_chrome():
    """Return a verification report dict; raises AssertionError on failure."""
    from pathlib import Path
    from playwright.sync_api import sync_playwright

    page_uri = Path(PAGE_PATH).as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page()
        js_errors = []          # uncaught JS exceptions (true page errors)
        console_errors = []     # all console.error messages
        page.on("pageerror", lambda e: js_errors.append("pageerror: " + str(e)))
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.goto(page_uri, wait_until="load")
        page.wait_for_function(
            "() => !!window.narrationEngine && !!window.narrationEngine.sections "
            "&& window.narrationEngine.sections.length > 0 "
            "&& !!window.TEACHER_AUDIO_MANIFEST")
        data = page.evaluate(VERIFY_JS)
        browser.close()

    # Known, pre-existing, non-narration noise from the offline file:// page:
    # the hero/watch-panel mp4 is absent and YouTube embeds are network-blocked.
    benign = ("ERR_FILE_NOT_FOUND", "404 (File not found)",
              "Permissions policy violation", "Failed to load resource",
              "net::ERR", "ERR_BLOCKED", "Not allowed to load local resource")
    narration_console_errors = [e for e in console_errors
                                if not any(b in e for b in benign)]

    assert js_errors == [], f"JS page errors: {js_errors}"
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
                  "sec-figures", "sec-interactive-lab", "sec-video-note"} & set(dom_ids)), \
        "non-narrated section leaked into DOM sections"

    tsections = data["manifest"]["sections"]
    total_cues = 0
    total_ms = 0.0
    dup_check = set()
    disallowed = set()
    forbidden_hits = []
    visuals = 0
    tex_annotations = 0
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
        assert msec["audio_file"] in eng_sec["audioFile"], (sec_id, "engine audio binding", eng_sec["audioFile"])
        assert msec["alias"] == EXPECTED_ALIASES[sec_id], (sec_id, "alias")

        # TeX annotation must survive for every formula-box block.
        n_fb = expected_types.count("formula-box")
        assert len(dom_sec["tex"]) == n_fb, (sec_id, "formula-box tex count")
        for tex in dom_sec["tex"]:
            assert isinstance(tex, list) and any(t.strip() for t in tex), (sec_id, "missing TeX annotation")
            tex_annotations += len(tex)

        for c in cues:
            total_cues += 1
            key = (sec_id, c["index"], c["type"], c["text"])
            assert key not in dup_check, f"Duplicate cue: {key[:3]}"
            dup_check.add(key)
            if c["type"] not in ALLOWED_CUE_TYPES:
                disallowed.add(c["type"])
            if FORBIDDEN_PREFIX in c["text"]:
                forbidden_hits.append(f"{sec_id}/{c['index']}")
            if SECTIONS_DATA[sec_id]["cues"][c["index"]].get("visual"):
                visuals += 1
                sentences = [x for x in c["text"].split("।") if x.strip()]
                assert 2 <= len(sentences) <= 4, (sec_id, c["index"], len(sentences))

        # Timing integrity: exact 350 ms gaps, no overlaps, duration agrees.
        cursor = 0.0
        for i, c in enumerate(cues):
            assert abs(c["start_ms"] - cursor) < 1.0, (sec_id, i, "start", c["start_ms"], cursor)
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

    # No quiz / media-tab anywhere in the narrated manifest or DOM cue types.
    all_dom_types = [t for s in data["dom"] for t in s["types"]]
    assert not ({"quiz", "media-tab", "b1b-quiz", "b1b-media-tab"} & set(all_dom_types)), all_dom_types

    # manifest.js payload must equal manifest.json.
    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        json_obj = json.load(fh)
    with open(os.path.join(AUDIO_DIR, "manifest.js"), encoding="utf-8") as fh:
        js_text = fh.read().strip()
    assert js_text.startswith("window.TEACHER_AUDIO_MANIFEST = ") and js_text.endswith(";")
    js_obj = json.loads(js_text[len("window.TEACHER_AUDIO_MANIFEST = "):-1].strip())
    assert js_obj == json_obj, "manifest.js != manifest.json"

    # Page cache-buster bumped exactly +1 when this process built the audio.
    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    versions = [int(v) for _, v in re.findall(r"(manifest\.js\?v=)(\d+)", html)]
    if OLD_VERSIONS:
        assert versions == [v + 1 for v in OLD_VERSIONS], \
            f"manifest ?v not bumped +1: {OLD_VERSIONS} -> {versions}"
    else:
        assert versions and min(versions) >= 2, f"manifest ?v not bumped: {versions}"

    return {
        "channel": "chrome (headless=True)",
        "sections": len(SECTIONS_DATA),
        "cues": total_cues,
        "per_section": {sid: EXPECTED_COUNT[sid] for sid in canonical_ids},
        "manifest_keys": len(mkeys),
        "natural_figure_explanations": visuals,
        "duplicates": 0,
        "disallowed_types": 0,
        "quiz_media_tab_types": 0,
        "forbidden_label_hits": 0,
        "js_page_errors": len(js_errors),
        "narration_console_errors": len(narration_console_errors),
        "preexisting_media_console_errors": len(console_errors) - len(narration_console_errors),
        "mp3_nonzero": True,
        "json_valid": True,
        "manifest_js_matches_json": True,
        "tex_annotations": tex_annotations,
        "manifest_version": versions,
        "total_duration_ms": round(total_ms, 1),
        "total_duration_s": round(total_ms / 1000.0, 2),
        "ok": True,
    }


def main():
    if "--verify-only" not in sys.argv[1:]:
        asyncio.run(build_all())
    print("Running headless Chrome verification..." if "--verify-only" in sys.argv[1:] else "")
    report = verify_in_chrome()
    print("\n" + "=" * 70)
    print("VERIFICATION REPORT (headless Chrome channel=chrome)")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("=" * 70)
    if not report.get("ok"):
        raise SystemExit("VERIFICATION FAILED")
    print("VERIFIED: 32/32 cues, DOM<->manifest 1:1, 0 dups, 0 quiz/media-tab types, "
          "non-zero mp3s, valid JSON, 0 JS page errors, 0 'চিত্র প্রদর্শনী' labels.")
    print("=" * 70)


if __name__ == "__main__":
    main()
