# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Probability Lesson 05
("Markov Chains, Random Walks, and Steady States", Bengali) to the gold standard.

Deterministic, re-runnable, self-contained:
  * 30 cues in 6 narrated sections with EXACTLY the same section IDs, alias keys,
    audio_file names, cue types and cue order as the live narration-engine DOM
    (verified 5/5/5/5/5/5 for sec-intro / sec-transitions / sec-matrix /
    sec-random-walk / sec-steady-state / sec-pagerank). sec-simulator and
    sec-quizzes carry data-no-narration="true" and are deliberately excluded.
  * Section IDs and block types were extracted from the live DOM through
    narration_engine.js's own selector
    ('h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase,
    .formula-box'), never guessed from prose. The callout-blue / callout-gold
    variants are normalised to the canonical 'callout' cue type used by the
    manifest.
  * The 12 manifest keys (6 canonical + 6 legacy alias) and the audio_file names
    (sec_01_intro.mp3 ... sec_06_pagerank.mp3) are preserved exactly from the
    existing manifest; each alias mirrors its canonical section byte-for-byte.
  * Visual explanations are genuine, natural 2-4 sentence teacher phrasing —
    the artificial label "চিত্র প্রদর্শনী" is never used.
  * Fully phonetic spoken Bengali (no TeX / Latin / markup). Safeguards:
      Markov -> মার্কভ, PageRank -> পেজ র‍্যাঙ্ক, steady state -> স্টেডি স্টেট,
      transition matrix -> ট্রানজিশন ম্যাট্রিক্স,  X_n -> এক্স এন,
      k -> কে, N -> এন, lambda -> ল্যাম্বডা, pi -> পাই, P -> পি.
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
  python governance/build_expressive_teacher_audio_prob05.py
  python governance/build_expressive_teacher_audio_prob05.py --verify-only
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
                         "probability", "lesson_05")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "probability", "lesson_05.html")
MANIFEST_TITLE = "অধ্যায় ০৫ — মার্কভ চেইন, র‍্যান্ডম ওয়াক ও স্টেডি স্টেট"

# Prosody keyed by cue type: (rate, pitch, volume)
PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
    "h3":            ("-3%", "+0Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),
    "p":             ("+2%", "+0Hz", "+0%"),   # natural teacher pace
    "figure":        ("-4%", "+0Hz", "+0%"),   # slower, considerate visual explanation
    "callout":       ("+0%", "+0Hz", "+0%"),
    "formula-box":   ("-8%", "+0Hz", "+0%"),   # slow and deliberate
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")

ALLOWED_CUE_TYPES = set(PROSODY_DEFAULT) | {"conclusion"}

# Exact DOM block-type sequence per narrated section (from narration_engine).
# callout-blue / callout-gold are normalised to 'callout'.
EXPECTED_TYPES = {
    "sec-intro":        ["h2", "chapter-quote", "p", "callout", "formula-box"],
    "sec-transitions":  ["h2", "p", "p", "callout", "formula-box"],
    "sec-matrix":       ["h2", "p", "p", "formula-box", "callout"],
    "sec-random-walk":  ["h2", "p", "p", "formula-box", "callout"],
    "sec-steady-state": ["h2", "p", "formula-box", "p", "callout"],
    "sec-pagerank":     ["h2", "p", "p", "formula-box", "callout"],
}
EXPECTED_AUDIO_FILES = {
    "sec-intro":        "sec_01_intro.mp3",
    "sec-transitions":  "sec_02_transitions.mp3",
    "sec-matrix":       "sec_03_matrix.mp3",
    "sec-random-walk":  "sec_04_random_walk.mp3",
    "sec-steady-state": "sec_05_steady_state.mp3",
    "sec-pagerank":     "sec_06_pagerank.mp3",
}
ALIASES = {
    "sec-intro":        "sec_01_intro",
    "sec-transitions":  "sec_02_transitions",
    "sec-matrix":       "sec_03_matrix",
    "sec-random-walk":  "sec_04_random_walk",
    "sec-steady-state": "sec_05_steady_state",
    "sec-pagerank":     "sec_06_pagerank",
}
EXPECTED_COUNT = {sid: 5 for sid in EXPECTED_TYPES}
EXPECTED_TOTAL = 30

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (30 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-intro": {
        "title": "স্মৃতিহীনতার দর্শন ও মার্কভ ধর্মের সূচনা",
        "audio_file": "sec_01_intro.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, স্মৃতিহীনতার দর্শন ও মার্কভ ধর্মের সূচনা।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, বর্তমান অবস্থা জানা থাকলে ভবিষ্যৎ অতীতের সমস্ত ইতিহাস থেকে সম্পূর্ণ স্বাধীন। এই কথা বলেছিলেন আন্দ্রেই মার্কভ।"},
            {"index": 2, "type": "p", "visual": True,
             "tts": "কল্পনা করুন এমন এক পর্যটকের কথা, যিনি এক শহর থেকে আরেক শহরে ঘুরে বেড়ান এবং প্রতিটি পদক্ষেপে পেছনের সম্পূর্ণ ভ্রমণ ইতিহাস ভুলে যান। আগামীকাল তিনি কোথায় যাবেন, তা নির্ভর করে তিনি এই মুহূর্তে কোথায় দাঁড়িয়ে আছেন তার ওপর, অতীতের কোনো পথের ওপর নয়। দাবার বোর্ডের পরবর্তী চাল, স্টক মার্কেটের তাৎক্ষণিক গতি, কিংবা পরমাণুর ব্রাউনীয় গতি, সবই এই একই স্মৃতিহীন নীতি মেনে চলে।"},
            {"index": 3, "type": "callout",
             "tts": "বিশেষ নোট, মার্কভ ধর্ম। যদি কোনো ব্যবস্থার অতীত অবস্থা আর বর্তমান অবস্থা জানা থাকে, তবে পরবর্তী অবস্থার শর্তাধীন সম্ভাবনা কেবল বর্তমান অবস্থার ওপর নির্ভর করে। অতীতের সম্পূর্ণ ইতিহাস এখানে সম্পূর্ণ অপ্রাসঙ্গিক।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, পরবর্তী অবস্থার সম্ভাবনা শূন্য থেকে এন পর্যন্ত পুরো ইতিহাসের শর্তে, সমান শুধু বর্তমান এক্স এন এর শর্তে। অর্থাৎ বর্তমান অবস্থা জানা থাকলে অতীতের সব ইতিহাস বাতিল হয়ে যায়।"},
        ],
    },

    "sec-transitions": {
        "title": "স্টেট ট্রানজিশন ডায়াগ্রাম ও সম্ভাব্যতা সংরক্ষণ",
        "audio_file": "sec_02_transitions.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, স্টেট ট্রানজিশন ডায়াগ্রাম ও সম্ভাব্যতা সংরক্ষণ।"},
            {"index": 1, "type": "p", "visual": True,
             "tts": "যেকোনো মার্কভ চেইনকে আমরা একটি নির্দেশিত গ্রাফ হিসেবে কল্পনা করতে পারি। প্রতিটি অবস্থা হলো একটি নোড বা বৃত্ত, আর সম্ভাব্যতার রূপান্তরগুলো তাদের সংযোগকারী তীরচিহ্ন। এই তীরগুলো দেখেই বোঝা যায় কোন অবস্থা থেকে কোন অবস্থায় যাওয়ার পথ আছে।"},
            {"index": 2, "type": "p",
             "tts": "একটি সহজ দ্বি অবস্থা আবহাওয়া মডেল বিবেচনা করা যাক, রৌদ্রোজ্জ্বল দিন আর বৃষ্টির দিন। রৌদ্রোজ্জ্বল দিনের পর রোদ থাকার সম্ভাবনা আশি শতাংশ আর বৃষ্টি হওয়ার সম্ভাবনা কুড়ি শতাংশ। আবার বৃষ্টির দিনের পর বৃষ্টি থাকার সম্ভাবনা পঞ্চাশ শতাংশ আর রোদ ওঠার সম্ভাবনাও পঞ্চাশ শতাংশ।"},
            {"index": 3, "type": "callout",
             "tts": "বিশেষ নোট, সম্ভাব্যতা সংরক্ষণ। যেকোনো অবস্থা থেকে বের হওয়া সমস্ত তীরচিহ্নের সম্ভাব্যতার যোগফল ঠিক এক দশমিক শূন্য হতে হবে। রোদ থেকে রোদ আশি আর রোদ থেকে বৃষ্টি কুড়ি, যোগফল এক। আবার বৃষ্টি থেকে দুই পথের সম্ভাবনা পঞ্চাশ যোগ পঞ্চাশ, অর্থাৎ একই এক।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, যেকোনো অবস্থা ই থেকে সম্ভাব্য সব পরবর্তী অবস্থা জে এর জন্য রূপান্তর সম্ভাবনার যোগফল সমান এক দশমিক শূন্য। অর্থাৎ কোনো নোড থেকে বের হওয়া সম্ভাবনা কখনোই কম বা বেশি হতে পারে না।"},
        ],
    },

    "sec-matrix": {
        "title": "স্টোক্যাস্টিক ট্রানজিশন ম্যাট্রিক্স এবং অবস্থা ভেক্টর",
        "audio_file": "sec_03_matrix.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, স্টোক্যাস্টিক ট্রানজিশন ম্যাট্রিক্স এবং অবস্থা ভেক্টর।"},
            {"index": 1, "type": "p", "visual": True,
             "tts": "ধাপে ধাপে সম্ভাবনার এই প্রবাহকে গাণিতিকভাবে পরিচালনা করতে আমরা রূপান্তর সম্ভাবনাগুলোকে একটি ম্যাট্রিক্স পি তে সাজাই, যাকে বলা হয় স্টোক্যাস্টিক ট্রানজিশন ম্যাট্রিক্স। এর প্রতিটি সারির উপাদানের যোগফল সর্বদা ঠিক এক, আর এই সারিগুলোই আবহাওয়া মডেলের রূপান্তরকে ধরে রাখে। প্রথম সারিতে রোদ থেকে রোদ আশি শতাংশ আর বৃষ্টি কুড়ি শতাংশ, দ্বিতীয় সারিতে বৃষ্টি থেকে রোদ ও বৃষ্টি সমান পঞ্চাশ শতাংশ।"},
            {"index": 2, "type": "p",
             "tts": "সময়ের যেকোনো ধাপে প্রতিটি অবস্থায় থাকার সম্ভাবনা একটি সম্ভাব্যতা সারি ভেক্টর দিয়ে প্রকাশ করা হয়। এক ধাপ এগিয়ে যাওয়ার অর্থ হলো ভেক্টর আর ম্যাট্রিক্সের গুণন, অর্থাৎ বর্তমান ভেক্টরকে ট্রানজিশন ম্যাট্রিক্স দিয়ে গুণ করলেই পরবর্তী ধাপের বণ্টন পাওয়া যায়।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, কে ধাপ পরের সম্ভাব্যতা ভেক্টর সমান আদি ভেক্টর গুণ ট্রানজিশন ম্যাট্রিক্স পি এর কে তম ঘাত। অর্থাৎ বারবার একই রূপান্তর প্রয়োগ করলে ম্যাট্রিক্সের ঘাত বেড়েই চলে।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, লিনিয়ার অ্যালজেব্রার মেলবন্ধন। সময়ের সাথে সম্ভাবনার বিবর্তন আসলে একটি রৈখিক রূপান্তরের ধারাবাহিক প্রয়োগ। আপনি যখন পি এর দ্বিতীয়, তৃতীয় কিংবা দশম ঘাত নির্ণয় করেন, তখন আসলে সম্ভাবনা প্রবাহের ওপর ম্যাট্রিক্সের পুনরাবৃত্ত গুণন চালাচ্ছেন।"},
        ],
    },

    "sec-random-walk": {
        "title": "র‍্যান্ডম ওয়াক ও জুয়াড়ির নিঃস্ব হওয়ার সমস্যা",
        "audio_file": "sec_04_random_walk.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, র‍্যান্ডম ওয়াক ও জুয়াড়ির নিঃস্ব হওয়ার সমস্যা।"},
            {"index": 1, "type": "p",
             "tts": "মার্কভ চেইনের একটি ধ্রুপদী রূপ হলো একমাত্রিক র‍্যান্ডম ওয়াক, যাকে মাতালের এলোমেলো পদচারণাও বলা হয়। এর সবচেয়ে বিখ্যাত প্রয়োগ হলো জুয়াড়ির নিঃস্ব হওয়ার সমস্যা।"},
            {"index": 2, "type": "p", "visual": True,
             "tts": "ধরা যাক একজন জুয়াড়ি কে ডলার মূলধন নিয়ে খেলা শুরু করলেন আর এন ডলার অর্জনই তার লক্ষ্য। প্রতিটি নিরপেক্ষ বাজিতে পঞ্চাশ শতাংশ সম্ভাবনায় তিনি এক ডলার লাভ করেন আর পঞ্চাশ শতাংশ সম্ভাবনায় এক ডলার হারান। এই পদচারণায় শূন্য আর এন হলো শোষণকারী অবস্থা, একবার সেখানে পৌঁছালে আর ফেরা যায় না।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, কে ডলার থেকে শুরু করে এন ডলারে পৌঁছানোর সম্ভাবনা সমান কে ভাগ এন। আর নিঃস্ব হওয়ার সম্ভাবনা সমান এক মাইনাস কে ভাগ এন।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, ক্যাসিনোর নির্মম সত্য। ধরুন আপনার কাছে এক হাজার টাকা আর ক্যাসিনোর কাছে দশ লক্ষেরও বেশি। খেলা সম্পূর্ণ নিরপেক্ষ হলেও শেষ পর্যন্ত ক্যাসিনোকে হারানোর সম্ভাবনা মাত্র দশমিক এক শতাংশ, আর আপনার নিঃস্ব হওয়ার ঝুঁকি নিরানব্বই দশমিক নয় শতাংশ।"},
        ],
    },

    "sec-steady-state": {
        "title": "স্থিতাবস্থা ও আইগেনভেক্টরের মেলবন্ধন",
        "audio_file": "sec_05_steady_state.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, স্থিতাবস্থা ও আইগেনভেক্টরের মেলবন্ধন।"},
            {"index": 1, "type": "p", "visual": True,
             "tts": "সময় যখন অসীমের দিকে এগোয়, তখন কি ব্যবস্থাটি এমন এক অবস্থানে পৌঁছায় যা আর কখনো পরিবর্তিত হয় না? শুরুতে ব্যবস্থা যেখানেই থাকুক, ধাপে ধাপে রূপান্তরের পর সম্ভাবনার তরল এমন এক সুষম ভারসাম্যে এসে স্থির হয় যাকে পরবর্তী পদক্ষেপ আর নাড়াতে পারে না। এই অপরিবর্তনীয় ভারসাম্যকেই বলা হয় স্টেশনারি ডিস্ট্রিবিউশন বা স্টেডি স্টেট।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, পাই গুণ পি সমান পাই, যেখানে পাই এর সকল উপাদানের সমষ্টি এক দশমিক শূন্য। অর্থাৎ রূপান্তর ম্যাট্রিক্স দিয়ে গুণ করার পরও সম্ভাব্যতা ভেক্টর সম্পূর্ণ অপরিবর্তিত থাকে।"},
            {"index": 3, "type": "p",
             "tts": "লিনিয়ার অ্যালজেব্রার দৃষ্টিতে এটি হলো পাই গুণ পি সমান ল্যাম্বডা গুণ পাই, যেখানে আইগেনমান ল্যাম্বডা সমান এক। অর্থাৎ স্টেডি স্টেট বণ্টন আর কিছুই নয়, ট্রানজিশন ম্যাট্রিক্স পি এর আইগেনমান এক এর সাথে সম্পর্কিত লেফট আইগেনভেক্টর।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, পেরন ফ্রোবেনিয়াস উপপাদ্য। যেকোনো নিয়মিত মার্কভ চেইনের ট্রানজিশন ম্যাট্রিক্সের বৃহত্তম আইগেনমান সর্বদা ঠিক এক হয়। আর তার সাথে সংশ্লিষ্ট নরমালাইজড লেফট আইগেনভেক্টরটিই হলো অনন্য স্টেডি স্টেট, যা আদি অবস্থা যাই হোক না কেন দীর্ঘমেয়াদী রূপ নির্ধারণ করে।"},
        ],
    },

    "sec-pagerank": {
        "title": "গুগল পেজর‍্যাঙ্ক: ইন্টারনেট-স্কেল মার্কভ চেইন",
        "audio_file": "sec_06_pagerank.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "ষষ্ঠ পরিচ্ছেদ, গুগল পেজ র‍্যাঙ্ক, ইন্টারনেট স্কেল মার্কভ চেইন।"},
            {"index": 1, "type": "p",
             "tts": "উনিশ শত নিরানব্বই সালে ল্যারি পেজ আর সার্গেই ব্রিন মার্কভ চেইনের এই আইগেনভেক্টর তত্ত্ব ব্যবহার করে এমন এক ইঞ্জিনিয়ারিং বিপ্লব ঘটান যা মানবজাতির তথ্য অন্বেষণের ইতিহাস বদলে দেয়। এই ইঞ্জিনের নাম গুগল পেজ র‍্যাঙ্ক।"},
            {"index": 2, "type": "p", "visual": True,
             "tts": "তাঁরা সমগ্র ওয়ার্ল্ড ওয়াইড ওয়েবকে এক বিশাল মার্কভ চেইন হিসেবে কল্পনা করেন। প্রতিটি ওয়েবপেজ হলো একটি নোড আর হাইপারলিংক হলো রূপান্তর তীর। একজন কাল্পনিক দৈবসার্ফার যেকোনো পেজে গিয়ে সেখানকার লিংকগুলোতে সমান সম্ভাবনায় ক্লিক করতে থাকেন।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, গুগল ম্যাট্রিক্স জি সমান ডি গুণ পি, যোগ এক মাইনাস ডি ভাগ এন গুণ অল ওয়ানস ম্যাট্রিক্স। ডি এর মান সাধারণত শূন্য দশমিক আট পাঁচ, অর্থাৎ এই ভগ্নাংশ সম্ভাবনায় লিংক অনুসরণ আর বাকি ভগ্নাংশে দৈব টেলিপোর্টেশন।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, পেজ র‍্যাঙ্কের মূল দর্শন। একটি ওয়েবসাইটের পেজ র‍্যাঙ্ক স্কোর আর কিছুই নয়, সেই পেজে দৈবসার্ফারের পৌঁছানোর স্টেডি স্টেট আইগেনভেক্টরের মান। গুরুত্বপূর্ণ পেজ থেকে পাওয়া একটি ব্যাকলিংক শত শত সাধারণ লিংকের চেয়েও বেশি র‍্যাঙ্ক স্থানান্তর করে, আর সার্চ রেজাল্টে সেই পেজ তত উপরে স্থান পায়।"},
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
            print(f"  cue {idx:02d} [{cue['type']:<12}] {rate:>4} {pitch:>5}  {cue['tts'][:30]}...")
            await synth_cue(cue["tts"], chunk, rate, pitch, volume)
        else:
            print(f"  cue {idx:02d} [{cue['type']:<12}] cached")
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
        "alias": ALIASES[sec_id],
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

    manifest_sections = {}
    for sec_id, sec in SECTIONS_DATA.items():
        built = await build_section(sec_id, sec)
        manifest_sections[sec_id] = built
        # Legacy alias key mirrors the canonical section exactly (same fields).
        manifest_sections[ALIASES[sec_id]] = copy.deepcopy(built)

    manifest_data = {
        "course": "probability",
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

    bump_page_manifest_version()

    # Final integrity checks.
    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        loaded = json.load(fh)
    expected_keys = set(SECTIONS_DATA) | set(ALIASES.values())
    assert set(loaded["sections"]) == expected_keys, "manifest section keys changed"
    total_cues = 0
    total_ms = 0.0
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == EXPECTED_COUNT[sec_id]
        assert [c["type"] for c in msec["cues"]] == EXPECTED_TYPES[sec_id]
        assert loaded["sections"][ALIASES[sec_id]] == msec, "alias mirror changed"
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
    assert total_cues == EXPECTED_TOTAL

    print("\n" + "=" * 68)
    print("BUILD COMPLETE - expressive teacher audio, Probability Lesson 05")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<20} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 6 sections, "
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
    if (!node || !node.classList) return node ? node.tagName.toLowerCase() : '';
    if (node.classList.contains('chapter-quote')) return 'chapter-quote';
    // callout-blue / callout-gold are normalised to the canonical 'callout'.
    if (node.classList.contains('callout')) return 'callout';
    if (node.matches && node.matches('figure.lesson-figure')) return 'figure';
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
    audioFile: s.audioFile, types: s.blocks.map(b => domType(b.element)),
    texts: s.blocks.map(b => b.text)
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
              "Permissions policy violation", "ERR_BLOCKED_BY_CLIENT",
              "Failed to load resource")
    narration_console_errors = [e for e in console_errors
                                if not any(b in e for b in benign)]

    assert js_errors == [], f"JS page errors: {js_errors}"
    assert narration_console_errors == [], f"Unexpected console errors: {narration_console_errors}"
    assert data["manifestPresent"], "window.TEACHER_AUDIO_MANIFEST missing"
    assert data["hasStudioAudio"], "Studio teacher audio not bound"

    canonical_ids = list(SECTIONS_DATA)
    dom_ids = [s["id"] for s in data["dom"]]
    eng_ids = [s["id"] for s in data["engine"]]
    mkeys = data["manifestKeys"]
    expected_keys = set(canonical_ids) | set(ALIASES.values())

    assert dom_ids == canonical_ids, f"DOM ids changed: {dom_ids} vs {canonical_ids}"
    assert eng_ids == canonical_ids, f"Engine ids changed: {eng_ids} vs {canonical_ids}"
    assert set(mkeys) == expected_keys, f"Manifest keys changed: {mkeys}"
    for sid, alias in ALIASES.items():
        assert sid in mkeys and alias in mkeys, f"missing key {sid}/{alias}"
    assert not ({"sec-quizzes", "sec-quiz", "sec-media", "sec-simulator"} & set(dom_ids)), \
        "quiz/media/non-narrated section leaked into DOM sections"

    tsections = data["manifest"]["sections"]
    # Alias sections mirror their canonical section exactly.
    for sid, alias in ALIASES.items():
        assert tsections[alias] == tsections[sid], f"alias {alias} does not mirror {sid}"
        assert tsections[sid]["section_id"] == sid and tsections[alias]["section_id"] == sid

    total_cues = 0
    total_ms = 0.0
    dup_check = set()
    disallowed = set()
    forbidden_hits = []
    visuals = 0
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
        assert get_duration_ms(af) > 0, f"ffprobe failed on {af}"
        total_ms += msec["total_duration_ms"]

    assert total_cues == EXPECTED_TOTAL, total_cues
    assert not disallowed, f"Disallowed cue types: {disallowed}"
    assert not forbidden_hits, f"Artificial figure label found: {forbidden_hits}"

    # No quiz / media-tab anywhere in the narrated manifest or DOM cue types.
    all_dom_types = [t for s in data["dom"] for t in s["types"]]
    forbidden_types = {"quiz", "media-tab", "b1b-quiz", "b1b-media-tab",
                       "quiz-block", "media-tab-caption"}
    assert not (forbidden_types & set(all_dom_types)), all_dom_types
    all_man_types = {c["type"] for s in tsections.values() for c in s["cues"]}
    assert not (forbidden_types & all_man_types), all_man_types

    # manifest.js payload must equal manifest.json.
    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        json_obj = json.load(fh)
    with open(os.path.join(AUDIO_DIR, "manifest.js"), encoding="utf-8") as fh:
        js_text = fh.read().strip()
    assert js_text.startswith("window.TEACHER_AUDIO_MANIFEST = ") and js_text.endswith(";")
    js_obj = json.loads(js_text[len("window.TEACHER_AUDIO_MANIFEST = "):-1].strip())
    assert js_obj == json_obj, "manifest.js != manifest.json"
    assert json_obj == data["manifest"], "on-disk manifest != window.TEACHER_AUDIO_MANIFEST"

    # Page cache-buster bumped.
    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    versions = [int(v) for _, v in re.findall(r"(manifest\.js\?v=)(\d+)", html)]
    assert versions and min(versions) >= 2, f"manifest ?v not bumped: {versions}"

    return {
        "channel": "chrome (headless=True)",
        "sections": len(canonical_ids),
        "cues": total_cues,
        "per_section": {sid: EXPECTED_COUNT[sid] for sid in canonical_ids},
        "manifest_keys": len(mkeys),
        "aliases_mirror": True,
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
        "dom_manifest_1to1": True,
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
    print("VERIFIED: 30/30 cues, DOM<->manifest 1:1, 0 dups, 0 quiz/media-tab types, "
          "non-zero mp3s, valid JSON, 0 JS page errors, 0 'চিত্র প্রদর্শনী' labels.")
    print("=" * 68)


if __name__ == "__main__":
    main()
