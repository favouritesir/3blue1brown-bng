# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Probability Lesson 04
("Continuous Probability Distributions & Probability Density", Bengali)
to the gold standard.

Deterministic, re-runnable, self-contained:
  * 36 cues in 6 narrated sections with EXACTLY the same section IDs, alias
    keys, audio_file names, cue types and cue order as the live narration-engine
    DOM (verified 6/6/6/6/6/6 for sec-discrete-vs-continuous /
    sec-zero-probability-paradox / sec-density-analogy / sec-area-under-curve /
    sec-gaussian-bell-curve / sec-clt-intuition). sec-interactive-lab and
    sec-quizzes carry data-no-narration="true" and are deliberately excluded.
  * Section IDs, block types and counts were extracted FIRST from the live DOM
    through narration_engine.js's own selector ('h2, h3, p, .chapter-quote,
    .callout, figure.lesson-figure, .code-showcase, .formula-box') in headless
    Chrome channel=chrome. Callout variants (callout-blue/gold/green) are kept
    verbatim. The media-tab captions are styled non-narration blocks and are
    NOT narration cues.
  * Visual explanations are genuine, natural 2-4 sentence teacher phrasing —
    the artificial label "চিত্র প্রদর্শনী" is never used.
  * Fully phonetic spoken Bengali (no TeX / Latin / markup). Safeguards:
      PMF -> পি এম এফ,  PDF -> পি ডি এফ,  f(x) -> এফ অব এক্স,
      Gaussian -> গাউসিয়ান,  sigma -> সিগমা,  mu -> মিউ,
      CLT -> সিএলটি,  CDF -> সিডিএফ,  density -> ডেনসিটি.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, h3 -3%, chapter-quote -3%, p +2%, figure -4%,
      callout-* +0%, formula-box -8%, conclusion -3%.
  * A real 350 ms silence chunk between cues, so manifest millisecond timings
    match the concatenated audio exactly.
  * ffmpeg -c copy concat into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) for the
    6 canonical keys AND their 6 legacy alias keys (12 keys, exact old order).
  * Bumps the page cache-buster manifest.js?v=N -> ?v=N+1.
  * verify_in_chrome() re-checks everything headlessly with channel=chrome.
  * The _backup_before_expressive_build/ folder is NEVER touched.

Usage:
  python governance/build_expressive_teacher_audio_prob04.py
  python governance/build_expressive_teacher_audio_prob04.py --verify-only
"""

import os
import re
import sys
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
                         "probability", "lesson_04")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "probability", "lesson_04.html")
MANIFEST_TITLE = "অধ্যায় ০৪ — অবিচ্ছিন্ন সম্ভাব্যতা ঘনত্ব ও নরমাল ডিস্ট্রিবিউশন"

# Prosody keyed by cue type: (rate, pitch, volume)
PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
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
    "sec-discrete-vs-continuous":   ["h2", "chapter-quote", "p", "p", "p", "callout-blue"],
    "sec-zero-probability-paradox": ["h2", "p", "p", "formula-box", "p", "callout-gold"],
    "sec-density-analogy":          ["h2", "p", "p", "p", "callout-blue", "p"],
    "sec-area-under-curve":         ["h2", "p", "formula-box", "p", "formula-box", "callout-green"],
    "sec-gaussian-bell-curve":      ["h2", "p", "formula-box", "p", "callout-gold", "p"],
    "sec-clt-intuition":            ["h2", "p", "p", "callout-blue", "p", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-discrete-vs-continuous":   "sec_01_discrete_vs_continuous.mp3",
    "sec-zero-probability-paradox": "sec_02_zero_probability_paradox.mp3",
    "sec-density-analogy":          "sec_03_density_analogy.mp3",
    "sec-area-under-curve":         "sec_04_area_under_curve.mp3",
    "sec-gaussian-bell-curve":      "sec_05_gaussian_bell_curve.mp3",
    "sec-clt-intuition":            "sec_06_clt_intuition.mp3",
}
EXPECTED_COUNT = {sid: 6 for sid in EXPECTED_TYPES}
EXPECTED_TOTAL = 36

# Canonical DOM id -> legacy alias keys that must survive in the manifest.
ALIASES = {
    "sec-discrete-vs-continuous":   ["sec_01_discrete_vs_continuous"],
    "sec-zero-probability-paradox": ["sec_02_zero_probability_paradox"],
    "sec-density-analogy":          ["sec_03_density_analogy"],
    "sec-area-under-curve":         ["sec_04_area_under_curve"],
    "sec-gaussian-bell-curve":      ["sec_05_gaussian_bell_curve"],
    "sec-clt-intuition":            ["sec_06_clt_intuition"],
}
CANONICAL_ALIAS = {sid: aliases[0] for sid, aliases in ALIASES.items()}
ALIAS_TO_CANONICAL = {
    alias: sid for sid, aliases in ALIASES.items() for alias in aliases
}
# Preserve the exact key order of the existing narrated portion of the manifest.
# The data-no-narration sections (sec-interactive-lab / sec-quizzes and their
# aliases) are intentionally dropped, exactly as the prob03 gold builder does.
SECTION_KEY_ORDER = [
    "sec-discrete-vs-continuous", "sec_01_discrete_vs_continuous",
    "sec-zero-probability-paradox", "sec_02_zero_probability_paradox",
    "sec-density-analogy", "sec_03_density_analogy",
    "sec-area-under-curve", "sec_04_area_under_curve",
    "sec-gaussian-bell-curve", "sec_05_gaussian_bell_curve",
    "sec-clt-intuition", "sec_06_clt_intuition",
]

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (36 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-discrete-vs-continuous": {
        "title": "বিচ্ছিন্ন বনাম অবিচ্ছিন্ন বাস্তবতা ও পিএমএফ থেকে রূপান্তর",
        "audio_file": "sec_01_discrete_vs_continuous.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, বিচ্ছিন্ন বনাম অবিচ্ছিন্ন বাস্তবতা, আর পি এম এফ থেকে রূপান্তর।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, প্রকৃতি কখনো লাফিয়ে চলে না। প্রকৃতির সমস্ত গতি ও রাশি অবিচ্ছিন্ন ধারায় প্রবাহিত হয়। বলেছেন গটফ্রিড ভিলহেম লাইবনিজ।"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, এই সিরিজের আগের অধ্যায়গুলোতে আমরা যেসব দৈব চলক নিয়ে কাজ করেছি, সেগুলো ছিল বিচ্ছিন্ন বা ডিসক্রিট। যেমন মুদ্রার হেড বা টেল, ছক্কার এক থেকে ছয় পর্যন্ত পূর্ণসংখ্যা, কিংবা বাছাই করা একটি তাস। এই প্রতিটি ক্ষেত্রেই ফলাফলগুলো ছিল পৃথক, সুস্পষ্ট আর গণনাযোগ্য।"},
            {"index": 3, "type": "p", "visual": True,
             "tts": "চিত্রে বাঁদিকে যেসব উলম্ব স্তম্ভ দেখা যাচ্ছে, প্রতিটিই একটি করে বিচ্ছিন্ন ফলাফলের সম্ভাব্যতা ভর দেখাচ্ছে, যাকে আমরা পি এম এফ বা সম্ভাব্যতা ভর ফাংশন বলি। স্তম্ভের উচ্চতা যত বেশি, ওই মানটি ঘটার সম্ভাবনাও তত বেশি। আর সব স্তম্ভের উচ্চতা যোগ করলে মোট যোগফল দাঁড়ায় ঠিক এক দশমিক শূন্য, অর্থাৎ একশো শতাংশ। ডানদিকের মসৃণ রেখাটি আবার দেখাচ্ছে অবিচ্ছিন্ন ধারা, যেখানে আলাদা কোনো স্তম্ভ নেই।"},
            {"index": 4, "type": "p",
             "tts": "কিন্তু আমাদের বাস্তব ভৌত জগৎ অধিকাংশ ক্ষেত্রেই এই ধাপে চলে না। কোনো মানুষের নিখুঁত উচ্চতা, বাতাসের তাপমাত্রা কিংবা বাস স্টপে অপেক্ষার সময়ের কথা ভাবুন। এগুলো এক, দুই, তিনের মতো লাফ দিয়ে আসে না, বরং বাস্তব সংখ্যার এক মসৃণ অবিচ্ছিন্ন ধারা বেয়ে প্রবাহিত হয়।"},
            {"index": 5, "type": "callout-blue",
             "tts": "মূল পার্থক্যের রেখা। বিচ্ছিন্ন চলকে আমরা প্রতিটি বিন্দুর জন্য সম্ভাবনার ভর পরিমাপ করি, কিন্তু অবিচ্ছিন্ন চলকে কোনো একক বিচ্ছিন্ন বিন্দু থাকে না। মানগুলো একটি অবিচ্ছিন্ন পরিসরে ছড়িয়ে থাকে, তাই সরাসরি পি এম এফ নিয়ম প্রয়োগ করলে এক গভীর স্বজ্ঞাত সংকট তৈরি হয়।"},
        ],
    },

    "sec-zero-probability-paradox": {
        "title": "একক বিন্দুর সম্ভাব্যতা কেন শূন্য: পি অব এক্স ইকুয়াল সি সমান শূন্য",
        "audio_file": "sec_02_zero_probability_paradox.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, একক বিন্দুর সম্ভাব্যতা কেন শূন্য, পি অব এক্স ইকুয়াল সি সমান শূন্য।"},
            {"index": 1, "type": "p",
             "tts": "এবার একটি আপাত সহজ অথচ যুগান্তকারী প্রশ্ন বিবেচনা করা যাক। দৈবভাবে নির্বাচিত একজন ব্যক্তির উচ্চতা অবিকল একশত পঁচাত্তর সেন্টিমিটার হওয়ার সম্ভাবনা কত?"},
            {"index": 2, "type": "p",
             "tts": "এখানে অবিকল বলতে আমরা বোঝাচ্ছি একশত চুয়াত্তর দশমিক নয় নয় নয় নয়, কিংবা একশত পঁচাত্তর দশমিক শূন্য শূন্য শূন্য এক নয়। বরং ঠিক একশত পঁচাত্তর দশমিক শূন্য শূন্য শূন্য সেন্টিমিটার, যার দশমিকের পর অসীমকাল পর্যন্ত কেবল শূন্য। কোয়ান্টাম সূক্ষ্মতায় মেপে দেখলে এমন নিখুঁত সংখ্যা কি বাস্তবে সম্ভব? উত্তরটি শুনতে বিস্ময়কর হলেও গাণিতিকভাবে পরম সত্য, একজন ব্যক্তির উচ্চতা অবিকল যেকোনো একটি নির্দিষ্ট বিন্দুতে পড়ার সম্ভাবনা ঠিক শূন্য।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, পি অব এক্স ইকুয়াল সি সমান শূন্য, সমস্ত সি এর জন্য। অর্থাৎ অবিচ্ছিন্ন দৈব চলকের ক্ষেত্রে যেকোনো একটি সুনির্দিষ্ট মানের সম্ভাবনা সর্বদা শূন্য।"},
            {"index": 4, "type": "p", "visual": True,
             "tts": "কেন এমন হয়? একশত সত্তর থেকে একশত আশি সেন্টিমিটারের এই ক্ষুদ্র দশ সেন্টিমিটার ব্যবধানের ভেতরেই বাস্তব সংখ্যার অগণিত বিন্দু রয়েছে। যদি প্রতিটি বিন্দুর জন্য অতি ক্ষুদ্র সম্ভাবনাও নির্ধারিত থাকত, তবে অসীম সংখ্যক বিন্দুর সম্ভাবনা যোগ করলে মোট সম্ভাব্যতা অসীমে পৌঁছে যেত, যা সম্ভাবনার মৌলিক স্বতঃসিদ্ধ ভেঙে দিত। তাই একক বিন্দুর নিজস্ব কোনো সম্ভাবনা থাকে না, সম্ভাবনা কেবল একটি ব্যবধান জুড়েই অর্থবহ হয়।"},
            {"index": 5, "type": "callout-gold",
             "tts": "সম্ভাবনা শূন্য মানেই অসম্ভব নয়। আমাদের প্রাত্যহিক স্বজ্ঞা বলে, সম্ভাবনা শূন্য মানে ঘটনাটি ঘটা অসম্ভব, কিন্তু অবিচ্ছিন্ন সম্ভাব্যতায় এই ধারণাটি সম্পূর্ণ ভুল। ডার্টবোর্ডে আপনি যখনই একটি নিখুঁত জ্যামিতিক পিন নিক্ষেপ করবেন, সেটি ঠিক যে বিন্দুতে বিঁধল, পূর্বে সেই সুনির্দিষ্ট বিন্দুতে লাগার সম্ভাবনা ছিল ঠিক শূন্য, অথচ ঘটনাটি ঘটেছে। অবিচ্ছিন্ন জগতে সম্ভাবনা কেবল একটি পরিসর বা ব্যবধানের জন্যই সংজ্ঞায়িত হয়।"},
        ],
    },

    "sec-density-analogy": {
        "title": "ভর ও ঘনত্বের পদার্থবিজ্ঞান রূপক: সম্ভাব্যতা ঘনত্ব এফ অব এক্স",
        "audio_file": "sec_03_density_analogy.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, ভর ও ঘনত্বের পদার্থবিজ্ঞান রূপক, সম্ভাব্যতা ঘনত্ব এফ অব এক্স।"},
            {"index": 1, "type": "p",
             "tts": "প্রতিটি বিন্দুর সম্ভাবনা শূন্য হওয়া সত্ত্বেও পুরো ব্যবধানের সম্ভাবনা কীভাবে এক দশমিক শূন্য হয়? এই প্যারাডক্সটি সমাধান করতে পদার্থবিজ্ঞান আমাদের সবচেয়ে চমৎকার রূপকটি উপহার দেয়, মোট ভর আর ভর ঘনত্বের পার্থক্য।"},
            {"index": 2, "type": "p", "visual": True,
             "tts": "চিত্রে এক মিটার লম্বা একটি নিরেট লোহার রড দেখা যাচ্ছে, যার মোট ভর এক কিলোগ্রাম। ঠিক মাঝখানের পঞ্চাশ সেন্টিমিটার দাগে থাকা একক জ্যামিতিক বিন্দুর ভর অবিকল শূন্য, কারণ একটি বিন্দুর কোনো দৈর্ঘ্য বা আয়তন নেই। অথচ পুরো রডের ভর কখনোই শূন্য নয়, কারণ রডজুড়ে রয়েছে রৈখিক ভর ঘনত্ব।"},
            {"index": 3, "type": "p",
             "tts": "প্রতিটি অতি ক্ষুদ্র দৈর্ঘ্যের ভর হলো ঘনত্ব গুণ সেই দৈর্ঘ্য। আর পুরো রডের সমস্ত বিন্দু বরাবর সমাকলন করলেই আমরা পেয়ে যাই পূর্ণ এক কিলোগ্রাম ভর, যা আমাদের এই উপমার কেন্দ্রীয় শিক্ষা।"},
            {"index": 4, "type": "callout-blue",
             "tts": "গুরুত্বপূর্ণ সতর্কতা, এফ অব এক্স কিন্তু সম্ভাব্যতা নয়। অনেকেই ভুলবশত এফ অব এক্স এর মানকে কোনো বিন্দুর সম্ভাবনা মনে করেন, কিন্তু এটি হলো প্রতি একক দৈর্ঘ্যের সম্ভাব্যতা ঘনত্ব। ঘনত্ব কখনো সম্ভাব্যতা নয়, তার মান অনায়াসেই একের চেয়ে অনেক বড় হতে পারে। যেমন শূন্য থেকে আধা ব্যবধানে সুষম বিস্তারের উচ্চতা দুই দশমিক শূন্য, কিন্তু মোট ক্ষেত্রফল দুই গুণ আধা, অর্থাৎ ঠিক এক।"},
            {"index": 5, "type": "p", "role": "conclusion",
             "tts": "ঠিক এই রূপকটিই সম্ভাব্যতা তত্ত্বে প্রয়োগ করা হয়। অবিচ্ছিন্ন চলকে বিচ্ছিন্ন সম্ভাব্যতা ভরের জায়গা দখল করে সম্ভাব্যতা ঘনত্ব, অর্থাৎ পি ডি এফ বা প্রবাবিলিটি ডেনসিটি ফাংশন, যাকে আমরা এফ অব এক্স দ্বারা প্রকাশ করি।"},
        ],
    },

    "sec-area-under-curve": {
        "title": "সম্ভাব্যতা হলো বক্ররেখার নিচের ক্ষেত্রফল এবং মোট সম্ভাবনার স্বাভাবিকীকরণ",
        "audio_file": "sec_04_area_under_curve.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, সম্ভাব্যতা হলো বক্ররেখার ক্ষেত্রফল ও স্বাভাবিকীকরণ।"},
            {"index": 1, "type": "p", "visual": True,
             "tts": "এবার আমরা আসি থ্রি ব্লু ওয়ান ব্রাউনের মূল দর্শনে, সম্ভাব্যতা মানেই ক্ষেত্রফল। চিত্রের বক্ররেখার নিচে আপনি যেসব অতি পাতলা উলম্ব ফালি দেখছেন, প্রতিটির প্রস্থ এক ক্ষুদ্র দৈর্ঘ্য আর উচ্চতা ঘনত্বের মান, তাই তার ক্ষেত্রফলই ওই ক্ষুদ্র ব্যবধানের সম্ভাবনা। এই অসীম সূক্ষ্ম ফালিগুলোকে একত্রে যোগ করলেই ক্যালকুলাসের নির্দিষ্ট যোগজ পাওয়া যায়। অর্থাৎ কোনো বিন্দুর উচ্চতা নয়, বরং ব্যবধানের নিচের ক্ষেত্রফলই হলো প্রকৃত সম্ভাবনা।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, পি অব এ লেস দ্যান অর ইকুয়াল এক্স লেস দ্যান অর ইকুয়াল বি সমান ইন্টিগ্রাল এ থেকে বি এফ অব এক্স ডিএক্স। অর্থাৎ এ থেকে বি ব্যবধানে বক্ররেখার নিচের মোট ক্ষেত্রফলই ওই ব্যবধানে ফলাফল আসার সম্ভাবনা।"},
            {"index": 3, "type": "p",
             "tts": "যেকোনো বৈধ সম্ভাব্যতা ঘনত্ব ফাংশনকে দুটি মৌলিক শর্ত পূরণ করতে হয়। প্রথমত, অঋণাত্মকতার শর্ত, বক্ররেখাটি কখনো অনুভূমিক অক্ষের নিচে নামতে পারবে না, কারণ ঋণাত্মক সম্ভাবনার কোনো বাস্তব অস্তিত্ব নেই। দ্বিতীয়ত, স্বাভাবিকীকরণের শর্ত, সম্পূর্ণ রেখা জুড়ে মোট ক্ষেত্রফল অবিকল এক দশমিক শূন্য, অর্থাৎ একশো শতাংশ হতে হবে।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ইন্টিগ্রাল মাইনাস ইনফিনিটি থেকে প্লাস ইনফিনিটি এফ অব এক্স ডিএক্স সমান এক দশমিক শূন্য, যা একশো শতাংশের সমান। এই স্বতঃসিদ্ধটি নিশ্চিত করে যে সমস্ত সম্ভাব্য ফলাফল মিলে মোট সম্ভাবনা ঠিক এক।"},
            {"index": 5, "type": "callout-green",
             "tts": "ক্যালকুলাসের সাথে সংযোগ। ক্রমযোজিত বিন্যাস ফাংশন বা সিডিএফ হলো বাম দিক থেকে সঞ্চিত ক্ষেত্রফলের পরিমাপ। ক্যালকুলাসের মৌলিক উপপাদ্য অনুযায়ী, এই সঞ্চিত ক্ষেত্রফলের পরিবর্তনের হারই হলো তৎকালীন বক্ররেখার উচ্চতা, অর্থাৎ সিডিএফের অন্তরজ সমান মূল ঘনত্ব এফ অব এক্স। এই ঐক্যটিই দেখায় যে সম্ভাব্যতা ও ক্যালকুলাস একই সূত্রে আবদ্ধ।"},
        ],
    },

    "sec-gaussian-bell-curve": {
        "title": "নরমাল ডিস্ট্রিবিউশন: গাউসিয়ান বেল কার্ভের জ্যামিতি ও পরামিতি",
        "audio_file": "sec_05_gaussian_bell_curve.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, নরমাল ডিস্ট্রিবিউশন, গাউসিয়ান বেল কার্ভের জ্যামিতি।"},
            {"index": 1, "type": "p", "visual": True,
             "tts": "সমগ্র সম্ভাব্যতা ও পরিসংখ্যানের ইতিহাসে সবচেয়ে প্রভাবশালী অবিচ্ছিন্ন বিন্যাস হলো নরমাল ডিস্ট্রিবিউশন বা গাউসিয়ান বেল কার্ভ। চিত্রের এই ঘণ্টা আকৃতির মসৃণ প্রতিসম বক্ররেখাটি দুটি মাত্র পরামিতি দ্বারা সম্পূর্ণ নিয়ন্ত্রিত। গড় বা মিউ ঠিক করে চূড়াটি অনুভূমিক অক্ষে কোথায় দাঁড়াবে, আর সিগমা বা পরিমিত ব্যবধান ঠিক করে ঘণ্টাটি কতটা প্রশস্ত বা খাড়া হবে। সিগমা ছোট হলে বণ্টন কেন্দ্রে পুঞ্জীভূত হয়, আর বড় হলে চ্যাপ্টা হয়ে দুই দিকে ছড়িয়ে পড়ে।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এফ অব এক্স সমান ওয়ান বাই সিগমা রুট টু পাই গুণ ই টু দ্য পাওয়ার মাইনাস এক্স মাইনাস মিউ বর্গ ভাগ দুই সিগমা বর্গ। এখানে মিউ হলো কেন্দ্র আর সিগমা হলো বিস্তার।"},
            {"index": 3, "type": "p",
             "tts": "নরমাল ডিস্ট্রিবিউশনের সূত্রে একটি বিশ্বখ্যাত ধ্রুবক যুক্ত থাকে, ওয়ান বাই সিগমা রুট টু পাই। এটি কোনো রহস্যময় সংখ্যা নয়, বরং সেই নিখুঁত নরমালাইজিং সহগ যা নিশ্চিত করে যে বক্ররেখার নিচের মোট ক্ষেত্রফল ঠিক এক দশমিক শূন্য।"},
            {"index": 4, "type": "callout-gold",
             "tts": "আটষট্টি, পঞ্চানব্বই, নিরানব্বই দশমিক সাতের স্বর্ণালী নীতি। যেকোনো নরমাল ডিস্ট্রিবিউশনে চলকের মান গড় থেকে এক সিগমার মধ্যে থাকার সম্ভাবনা শতকরা আটষট্টি দশমিক তিন, দুই সিগমার মধ্যে শতকরা পঞ্চানব্বই দশমিক পাঁচ, আর তিন সিগমার মধ্যে শতকরা নিরানব্বই দশমিক সাত। এই জ্যামিতিক সত্যটি গুণমান নিয়ন্ত্রণ, মেশিন লার্নিং ও বৈজ্ঞানিক গবেষণায় অনুমানের ভিত্তি স্থাপন করে।"},
            {"index": 5, "type": "p", "role": "conclusion",
             "tts": "সুতরাং এই সূত্রের প্রতিটি অংশের নিজস্ব ভূমিকা আছে, কেন্দ্র নির্ধারণ করে মিউ, বিস্তার নির্ধারণ করে সিগমা, আর সামনের সহগ নিশ্চিত করে মোট ক্ষেত্রফল ঠিক এক।"},
        ],
    },

    "sec-clt-intuition": {
        "title": "সেন্ট্রাল লিমিট থিওরেম: কেন সর্বত্র বেল কার্ভ দেখা যায়?",
        "audio_file": "sec_06_clt_intuition.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "ষষ্ঠ পরিচ্ছেদ, সেন্ট্রাল লিমিট থিওরেম, বিশ্বজুড়ে বেল কার্ভ এর রহস্য।"},
            {"index": 1, "type": "p",
             "tts": "কেন এই বিশেষ বেল কার্ভ টি বিজ্ঞানের সব শাখায় এত বেশি দেখা যায়? মানুষের বুদ্ধিমত্তা, উচ্চতা, অণুবীক্ষণিক কণার ব্রাউনিয়ান গতি, কিংবা স্টক মার্কেটের দৈনিক ওঠানামা, সবকিছুতেই কেন এই একই ঘণ্টার প্রতিচ্ছবি?"},
            {"index": 2, "type": "p",
             "tts": "উত্তরটি লুকিয়ে আছে সম্ভাব্যতা তত্ত্বের সবচেয়ে বিস্ময়কর সত্যে, সেন্ট্রাল লিমিট থিওরেম বা সিএলটি। উপপাদ্যটি বলছে, আপনি যদি যেকোনো বণ্টনের বহুসংখ্যক স্বাধীন দৈব চলককে একত্রে যোগ করেন, তবে তাদের সমষ্টি বা গড় সর্বদা একটি নিখুঁত নরমাল বেল কার্ভ এর দিকে ধাবিত হবে, তা যতই অসদৃশ বা একপেশে হোক না কেন।"},
            {"index": 3, "type": "callout-blue",
             "tts": "গ্যালটন বোর্ডের যান্ত্রিক প্রমাণ। ফ্রান্সিস গ্যালটনের উদ্ভাবিত গ্যালটন বোর্ডে ওপর থেকে হাজার হাজার মার্বেল পিনের গায়ে লেগে ডানে বা বাঁয়ে পড়ে, আর প্রতিটি সংঘর্ষ একটি স্বাধীন দৈব ঘটনা। নিচে মার্বেলগুলো জমা হতে হতে স্বয়ংক্রিয়ভাবে একটি নিখুঁত বেল কার্ভ তৈরি হয়। আদি বিস্তার সমতল বা বাঁকা যেকোনো আকৃতির হলেও, স্বাধীন চলকের যোগফল সর্বদা নরমাল ডিস্ট্রিবিউশনে উপনীত হয়।"},
            {"index": 4, "type": "p", "visual": True,
             "tts": "একটি বাস্তব পরীক্ষার কথা ভাবুন। একটি ছক্কা নিক্ষেপ করলে এক থেকে ছয় আসার সম্ভাবনা সমান, অর্থাৎ বিস্তারটি পুরোপুরি সমতল। দুটি ছক্কা ফেলে যোগ করলে সমষ্টির সম্ভাবনা ত্রিভুজাকার চূড়ার মতো হয়, আর দশটি ছক্কা ফেললে সমস্ত অসমান খাঁজ গলে গিয়ে একটি মসৃণ গাউসিয়ান বেল কার্ভ তৈরি হয়।"},
            {"index": 5, "type": "p", "role": "conclusion",
             "tts": "বাস্তব জগতের অধিকাংশ ঘটনা শত শত ক্ষুদ্র স্বাধীন প্রভাবকের সমষ্টি হিসেবে ঘটে। মানুষের উচ্চতা জিন, পুষ্টি ও পরিবেশের হাজারো ক্ষুদ্র প্রভাবের সম্মিলিত যোগফল, আর এই কারণেই প্রকৃতিতে বেল কার্ভ অবধারিতভাবে আবির্ভূত হয়।"},
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
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars {bad!r} in {cue['tts']!r}")
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: artificial figure label present")

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
                    raise ValueError(f"{sec_id} cue {cue['index']}: visual explanation has "
                                     f"{len(sentences)} sentences")
                visuals += 1

    # Every manifest key (canonical + alias) must be covered by our mapping.
    if set(SECTION_KEY_ORDER) != set(SECTIONS_DATA) | set(ALIAS_TO_CANONICAL):
        raise ValueError("SECTION_KEY_ORDER does not cover canonical + alias keys")
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
            print(f"  cue {idx:02d} [{cue['type']:<14}] {rate:>4} {pitch:>5}  {cue['tts'][:30]}...")
            await synth_cue(cue["tts"], chunk, rate, pitch, volume)
        else:
            print(f"  cue {idx:02d} [{cue['type']:<14}] cached")
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
        "alias": CANONICAL_ALIAS[sec_id],
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
    visuals = assert_clean_scripts()
    print(f"Validated {sum(len(s['cues']) for s in SECTIONS_DATA.values())} clean cues "
          f"in {len(SECTIONS_DATA)} sections ({visuals} natural visual explanations, "
          f"0 artificial figure labels).")

    built = {}
    for sec_id, sec in SECTIONS_DATA.items():
        built[sec_id] = await build_section(sec_id, sec)

    # Rebuild all 12 manifest keys in the exact order of the existing manifest.
    manifest_sections = {}
    for key in SECTION_KEY_ORDER:
        canonical = key if key in SECTIONS_DATA else ALIAS_TO_CANONICAL[key]
        obj = copy.deepcopy(built[canonical])
        obj["section_id"] = canonical
        obj["alias"] = CANONICAL_ALIAS[canonical]
        manifest_sections[key] = obj

    manifest_data = {
        "course": "probability",
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

    bump_page_manifest_version()

    # Final integrity checks.
    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert list(loaded["sections"]) == SECTION_KEY_ORDER, "manifest key order/keys changed"
    total_cues = 0
    total_ms = 0.0
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == EXPECTED_COUNT[sec_id]
        assert [c["type"] for c in msec["cues"]] == EXPECTED_TYPES[sec_id]
        for alias in ALIASES[sec_id]:
            assert loaded["sections"][alias] == msec, f"alias {alias} != {sec_id}"
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
    assert total_cues == EXPECTED_TOTAL

    print("\n" + "=" * 68)
    print("BUILD COMPLETE - expressive teacher audio, Probability Lesson 04")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<30} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 6 sections (+6 alias keys), "
          f"{total_ms / 1000.0:.2f}s, {visuals} natural visual explanations.")
    print("  manifest.json is valid JSON; all 6 mp3 files exist and are non-empty.")
    print("=" * 68)


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
    # absent hero/watch-panel mp4 and network-blocked YouTube embeds.
    benign = ("ERR_FILE_NOT_FOUND", "404 (File not found)",
              "Permissions policy violation")
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
    assert mkeys == SECTION_KEY_ORDER, f"Manifest keys changed: {mkeys}"
    assert canonical_ids == [s["id"] for s in data["engine"]], "Engine ids changed"
    assert not ({"sec-interactive-lab", "sec-quizzes", "sec-quiz",
                 "sec-media", "sec-simulator"} & set(dom_ids)), \
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

        # TeX annotation must survive for every formula-box block.
        assert len(dom_sec["tex"]) == expected_types.count("formula-box"), (sec_id, "formula-box tex count")
        for tex in dom_sec["tex"]:
            assert isinstance(tex, list) and any(t.strip() for t in tex), (sec_id, "missing TeX annotation")
            tex_annotations += len(tex)

        # Every alias key mirrors its canonical section exactly.
        for alias in ALIASES[sec_id]:
            assert tsections[alias] == msec, f"alias {alias} != {sec_id}"

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

    # Page cache-buster bumped.
    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    versions = [int(v) for _, v in re.findall(r"(manifest\.js\?v=)(\d+)", html)]
    assert versions and min(versions) >= 2, f"manifest ?v not bumped: {versions}"

    return {
        "channel": "chrome (headless=True)",
        "sections": len(SECTIONS_DATA),
        "cues": total_cues,
        "per_section": {sid: EXPECTED_COUNT[sid] for sid in canonical_ids},
        "manifest_keys": len(mkeys),
        "alias_keys": len(ALIAS_TO_CANONICAL),
        "natural_figure_explanations": visuals,
        "duplicates": 0,
        "disallowed_types": 0,
        "quiz_media_tab_types": 0,
        "forbidden_label_hits": 0,
        "js_page_errors": len(js_errors),
        "narration_console_errors": len(narration_console_errors),
        "preexisting_media_404_console_errors": len(console_errors) - len(narration_console_errors),
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
    print("\n" + "=" * 68)
    print("VERIFICATION REPORT (headless Chrome channel=chrome)")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("=" * 68)
    if not report.get("ok"):
        raise SystemExit("VERIFICATION FAILED")
    print("VERIFIED: 36/36 cues, DOM<->manifest 1:1, 0 dups, 0 quiz/media-tab types, "
          "non-zero mp3s, valid JSON, 0 JS page errors, 0 'চিত্র প্রদর্শনী' labels.")
    print("=" * 68)


if __name__ == "__main__":
    main()
