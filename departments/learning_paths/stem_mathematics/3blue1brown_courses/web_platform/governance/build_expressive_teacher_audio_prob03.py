# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Probability Lesson 03
("Binomial Distribution and Pascal's Triangle — Geometry of Coin Flips", Bengali)
to the gold standard.

Deterministic, re-runnable, self-contained:
  * 36 cues in 6 narrated sections with EXACTLY the same section IDs, audio_file
    names, cue types and cue order as the live narration-engine DOM
    (verified 5/6/6/6/7/6 for sec-bernoulli-intro / sec-probability-tree /
    sec-combinatorics-paths / sec-pascals-triangle / sec-binomial-pmf /
    sec-galton-board). sec-simulator and sec-quizzes carry
    data-no-narration="true" and are deliberately excluded.
  * Section IDs were extracted from the live DOM through narration_engine.js's
    own selector ('h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
    .code-showcase, .formula-box'), never guessed from prose. The media-tab
    captions are styled non-narration blocks and are NOT narration cues.
  * Visual explanations are genuine, natural 2-4 sentence teacher phrasing —
    the artificial label "চিত্র প্রদর্শনী" is never used.
  * Fully phonetic spoken Bengali (no TeX / Latin / markup). Safeguards:
      n choose k / C(n,k) -> এন চুজ কে,  p -> পি,  k -> কে,  n -> এন,
      mu = np -> মিউ ইকুয়াল এন পি,  sigma -> সিগমা,  1 - p -> এক মাইনাস পি.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, p +2%, figure -4%, callout +0%, formula-box -8%,
      conclusion -3%.
  * A real 350 ms silence chunk between cues, so manifest millisecond timings
    match the concatenated audio exactly.
  * ffmpeg -c copy concat into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST).
  * Bumps the page cache-buster manifest.js?v=N -> ?v=N+1.
  * verify_in_chrome() re-checks everything headlessly with channel=chrome.
  * The _backup_before_expressive_build/ folder is NEVER touched.

Usage:
  python governance/build_expressive_teacher_audio_prob03.py
  python governance/build_expressive_teacher_audio_prob03.py --verify-only
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
                         "probability", "lesson_03")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "probability", "lesson_03.html")
MANIFEST_TITLE = "অধ্যায় ০৩ — দ্বিপদী বিন্যাস ও প্যাসকেলের ত্রিভুজ — কয়েন টসের জ্যামিতি"

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
EXPECTED_TYPES = {
    "sec-bernoulli-intro":    ["h2", "p", "p", "p", "formula-box"],
    "sec-probability-tree":   ["h2", "p", "p", "p", "formula-box", "formula-box"],
    "sec-combinatorics-paths": ["h2", "p", "p", "p", "formula-box", "formula-box"],
    "sec-pascals-triangle":   ["h2", "p", "p", "p", "formula-box", "formula-box"],
    "sec-binomial-pmf":       ["h2", "p", "p", "p", "formula-box", "formula-box", "formula-box"],
    "sec-galton-board":       ["h2", "p", "p", "p", "formula-box", "formula-box"],
}
EXPECTED_AUDIO_FILES = {
    "sec-bernoulli-intro":     "sec-bernoulli-intro.mp3",
    "sec-probability-tree":    "sec-probability-tree.mp3",
    "sec-combinatorics-paths": "sec-combinatorics-paths.mp3",
    "sec-pascals-triangle":    "sec-pascals-triangle.mp3",
    "sec-binomial-pmf":        "sec-binomial-pmf.mp3",
    "sec-galton-board":        "sec-galton-board.mp3",
}
EXPECTED_COUNT = {
    "sec-bernoulli-intro": 5, "sec-probability-tree": 6,
    "sec-combinatorics-paths": 6, "sec-pascals-triangle": 6,
    "sec-binomial-pmf": 7, "sec-galton-board": 6,
}
EXPECTED_TOTAL = 36

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (36 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-bernoulli-intro": {
        "title": "বার্নৌলি ট্রায়াল: সাফল্যের দ্বিমুখী ভিত্তি",
        "audio_file": "sec-bernoulli-intro.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, বার্নৌলি ট্রায়াল, সাফল্যের দ্বিমুখী ভিত্তি।"},
            {"index": 1, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, সম্ভাব্যতার এই অধ্যায়ে আমাদের প্রথম ধাপ হলো বার্নৌলি ট্রায়াল। এটি হলো দ্বিমুখী ফলাফলের ক্ষুদ্রতম অবিভাজ্য গাণিতিক একক। কয়েন টসে হেড না টেল, মেডিকেল টেস্টে পজিটিভ না নেগেটিভ, কিংবা পরীক্ষায় পাস না ফেল। এই সবই আসলে একই দ্বিমুখী কাঠামোর উদাহরণ।"},
            {"index": 2, "type": "p", "visual": True,
             "tts": "গণিতে একক ট্রায়ালে সাফল্যের সম্ভাবনাকে বলা হয় পি, আর ব্যর্থতার সম্ভাবনা স্বতঃসিদ্ধভাবেই এক মাইনাস পি। চিত্রে বাঁদিকে সাফল্য অর্থাৎ হেড, আর ডানদিকে ব্যর্থতা অর্থাৎ টেল, দুটি টিকিটি বাক্স দেখানো হয়েছে। লক্ষ্য করুন এই দুই বাক্সের সম্ভাবনার যোগফল সবসময় এক দশমিক শূন্য, অর্থাৎ একশো শতাংশ।"},
            {"index": 3, "type": "p",
             "tts": "কিন্তু যখন আমরা এই স্বাধীন ট্রায়ালগুলোকে একাধিকবার পুনরাবৃত্তি করি, যেমন একটি কয়েনকে এন বার টস করি, তখনই জন্ম নেয় দ্বিপদী বিন্যাস। এন বার টসে ঠিক কতটি হেড আসবে, এই সরল প্রশ্নের উত্তরেই লুকানো আছে প্যাসকেলের ত্রিভুজের জ্যামিতি।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, পি এক্স ইকুয়াল ওয়ান হলো পি, আর পি এক্স ইকুয়াল জিরো হলো এক মাইনাস পি। অর্থাৎ সাফল্যের সম্ভাবনা পি এবং ব্যর্থতার সম্ভাবনা এক মাইনাস পি, এই দুটির যোগফল সর্বদা এক।"},
        ],
    },

    "sec-probability-tree": {
        "title": "সম্ভাব্যতার পথজালিকা ও বৃক্ষচিত্র (Probability Tree)",
        "audio_file": "sec-probability-tree.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, সম্ভাব্যতার পথজালিকা ও বৃক্ষচিত্র।"},
            {"index": 1, "type": "p",
             "tts": "ধরা যাক একটি নিরপেক্ষ কয়েন তিন বার টস করা হলো। প্রতিটি ট্রায়ালেই সম্ভাবনার বৃক্ষটি দ্বিগুণ হয়ে যায়, ফলে এনটি ট্রায়ালে মোট দুইয়ের এন ঘাত সংখ্যক পথ তৈরি হয়। এখানে পি হলো আধা, অর্থাৎ হেড আর টেলের সম্ভাবনা সমান।"},
            {"index": 2, "type": "p", "visual": True,
             "tts": "চিত্রের বৃক্ষচিত্রে প্রথম টসে দুটি ডাল, দ্বিতীয়তে চারটি, আর তৃতীয়তে আটটি পাতা ফেটে বেরিয়েছে। প্রতিটি পাতা একই দৈর্ঘ্যের পথ অতিক্রম করেছে, তাই প্রতিটির নিজস্ব সম্ভাবনা আট ভাগের এক ভাগ। যেকোনো একটি নির্দিষ্ট পথের সম্ভাবনা পেতে আমাদের কেটি সাফল্য এবং এন মাইনাস কেটি ব্যর্থতার সম্ভাবনাকে সরাসরি গুণ করতে হয়।"},
            {"index": 3, "type": "p",
             "tts": "কিন্তু ঠিক দুটি হেড পাওয়ার মতো কোনো ঘটনার মোট সম্ভাবনা হিসাব করতে হলে জানতে হবে, ঠিক কতগুলো ভিন্ন পথ একই সংখ্যক হেডে পৌঁছায়। এই প্রশ্নটির উত্তরেই পথ গণনের জ্যামিতি শুরু হয়।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, মোট পথ সমান দুইয়ের এন ঘাত। নিরপেক্ষ মুদ্রার ক্ষেত্রে এনসংখ্যক দ্বিমুখী ট্রায়ালে মোট শাখার সংখ্যা এই ঘাত আকারে বৃদ্ধি পায়। তিনটি টসে তাই মোট আটটি পথ।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, একটি নির্দিষ্ট পথের সম্ভাবনা সমান পির কে ঘাত, গুণ এক মাইনাস পির এন মাইনাস কে ঘাত। অর্থাৎ কেটি সাফল্য আর বাকি ব্যর্থতার সম্ভাবনাগুলোকে একসাথে গুণ করলেই ওই পথের নিজস্ব ওজন পাওয়া যায়।"},
        ],
    },

    "sec-combinatorics-paths": {
        "title": "কম্বিনেটোরিক্স: পথ গণনার জ্যামিতি ও n Choose k",
        "audio_file": "sec-combinatorics-paths.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, কম্বিনেটোরিক্স, পথ গণনের জ্যামিতি ও এন চুজ কে।"},
            {"index": 1, "type": "p",
             "tts": "তিনটি টসে ঠিক দুটি হেড পাওয়ার তিনটি পথ আছে, হেড হেড টেল, হেড টেল হেড, আর টেল হেড হেড। দ্বিপদী সহগ বা এন চুজ কে মূলত একই সংখ্যক সাফল্যে পৌঁছানোর এই সমান্তরাল পথগুলোর সংখ্যাই গুনে দেয়।"},
            {"index": 2, "type": "p",
             "tts": "এই সহগের গাণিতিক রূপ হলো এন ফ্যাক্টোরিয়াল ভাগ কে ফ্যাক্টোরিয়াল ও এন মাইনাস কে ফ্যাক্টোরিয়ালের গুণফল। এই অনুপাতটি আসলে অপ্রয়োজনীয় অভ্যন্তরীণ ক্রমের দ্বৈত গণনাকে বাতিল করে দেয়, ঠিক যেমন আমরা তিনটি অবস্থানের যেকোনো দুটিকে হেড বাছাই করি।"},
            {"index": 3, "type": "p", "visual": True,
             "tts": "চিত্রের শহরের গ্রিডে ডানে ও নিচে যাওয়া নিয়ে যে নীল, সবুজ আর কমলা রেখাগুলো আঁকা আছে, প্রতিটিই একটি করে শর্টেস্ট পথ। আসলে এমন পথ মোট ছয়টি। যেহেতু প্রতিটি পথ সমান সম্ভাবনাময়, তাই মোট পথের সংখ্যাকে একক পথের সম্ভাবনা দিয়ে গুণ করলেই কাঙ্ক্ষিত উত্তর পাওয়া যায়। তিন টসে দুই হেডের সম্ভাবনা তাই আট ভাগের তিন।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এন চুজ কে সমান এন ফ্যাক্টোরিয়াল ভাগ কে ফ্যাক্টোরিয়াল গুণ এন মাইনাস কে ফ্যাক্টোরিয়াল। এটি হলো এনটি স্থানের মধ্য থেকে কেটি সাফল্য বাছাই করার সর্বমোট উপায়।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, তিন চুজ দুই সমান তিন ফ্যাক্টোরিয়াল ভাগ দুই ফ্যাক্টোরিয়াল গুণ এক ফ্যাক্টোরিয়াল, যা ছয় ভাগ দুই, অর্থাৎ তিন। তিনটি স্থানের যেকোনো দুটিকে হেড ধরে নেওয়ার এটিই হলো ঠিক তিনটি উপায়।"},
        ],
    },

    "sec-pascals-triangle": {
        "title": "প্যাসকেলের ত্রিভুজ: প্রতিটি সংখ্যার পেছনের সম্ভাব্যতা",
        "audio_file": "sec-pascals-triangle.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, প্যাসকেলের ত্রিভুজ, প্রতিটি সংখ্যার পেছনের সম্ভাব্যতা।"},
            {"index": 1, "type": "p", "visual": True,
             "tts": "দ্বিপদী সহগগুলোকে সারিবদ্ধভাবে সাজালেই ভেসে ওঠে বিখ্যাত প্যাসকেলের ত্রিভুজ। চিত্রের এই ত্রিকোণাকার কাঠামোতে প্রতিটি সংখ্যা হলো একাধিক দ্বিমুখী পথ একত্রিত হওয়ার প্রত্যক্ষ ফল। শীর্ষে এক, তারপর এক এক, তারপর এক দুই এক, এভাবেই সারিগুলো নিচে নামতে থাকে।"},
            {"index": 2, "type": "p",
             "tts": "লক্ষ্য করুন, প্রতিটি ভেতরের সংখ্যা তার ঠিক উপরের বাঁ ও ডানের দুটি সংখ্যার যোগফলের সমান। আর যেকোনো সারির সব সংখ্যা যোগ করলে পাওয়া যায় দুইয়ের ওই সারির ঘাত, যা নিরপেক্ষ মুদ্রার মোট স্যাম্পল স্পেসেরই সমান।"},
            {"index": 3, "type": "p", "role": "conclusion",
             "tts": "ত্রিভুজটি মাঝ বরাবর নিখুঁত প্রতিসম, বাঁ দিক আর ডান দিকের সংখ্যাগুলো হুবহু মিলে যায়। আর এন বাড়ার সাথে সাথে এর অনুভূমিক প্রোফাইল ধীরে ধীরে একটি মসৃণ ঘণ্টার আকৃতি ধারণ করে, যা পরবর্তীতে নরমাল বেল কার্ভের রূপ নেবে।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এন চুজ কে সমান এন মাইনাস এক চুজ কে মাইনাস এক, যোগ এন মাইনাস এক চুজ কে। অর্থাৎ কোনো নোডে পৌঁছানোর মোট পথ তার ঠিক উপরের বাঁ ও ডানের দুটি পিতামাতা নোডের পথের যোগফল।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, কে সমান শূন্য থেকে এন পর্যন্ত এন চুজ কের যোগফল সমান দুইয়ের এন ঘাত। প্যাসকেলের ত্রিভুজের যেকোনো সারির সমস্ত সংখ্যার সমষ্টি ঠিক দুইয়ের সেই সারির ঘাতের সমান হয়।"},
        ],
    },

    "sec-binomial-pmf": {
        "title": "দ্বিপদী সম্ভাব্যতা ভর ফাংশন (Binomial PMF)",
        "audio_file": "sec-binomial-pmf.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, দ্বিপদী সম্ভাব্যতা ভর ফাংশন, অর্থাৎ দ্বিপদী পিএমএফ।"},
            {"index": 1, "type": "p", "visual": True,
             "tts": "এবার আমরা পথ গণনা ও সম্ভাবনার গুণনকে একটি একক সার্বজনীন সূত্রে রূপ দেব। দ্বিপদী বিন্যাস মূলত দুটি জিনিসের গুণফল, কতগুলো পথ আছে, আর প্রতিটি পথের নিজস্ব সম্ভাবনা কত। চিত্রে বাঁদিকে কম্বিনেশন আর ডানদিকে ওজন দেখানো হয়েছে, আর এই দুটির গুণফলই আমাদের চূড়ান্ত সূত্র।"},
            {"index": 2, "type": "p",
             "tts": "এই বিন্যাসের গড় বা প্রত্যাশার মান হলো মিউ ইকুয়াল এন পি। অর্থাৎ মোট ট্রায়াল এন আর প্রতিটিতে সাফল্যের সম্ভাবনা পি, এই দুটির গুণফলই গড় সাফল্যের সংখ্যা, যা সাধারণ কাণ্ডজ্ঞানের সাথে সরাসরি মিলে যায়।"},
            {"index": 3, "type": "p",
             "tts": "আর পরিমিত ব্যবধান সিগমা নির্ধারণ করে চূড়াটি কতটা চওড়া হবে। সিগমার মান এন গুণ পি গুণ এক মাইনাস পির বর্গমূলের সমান। পি আধার কাছে থাকলে বিস্তার বেশি, আর প্রান্তের দিকে গেলে চূড়া সরু হয়ে যায়।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, পি এক্স ইকুয়াল কে সমান এন চুজ কে, গুণ পির কে ঘাত, গুণ এক মাইনাস পির এন মাইনাস কে ঘাত। এখানে কে হলো শূন্য থেকে এন পর্যন্ত যেকোনো সাফল্যের সংখ্যা। এটিই সম্ভাব্যতা তত্ত্বের অবিস্মরণীয় দ্বিপদী বিন্যাস সূত্র।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, প্রত্যাশা ই এক্স সমান মিউ, সমান এন গুণ পি। অর্থাৎ গড়ে আমরা মোট ট্রায়ালের পি ভগ্নাংশ সাফল্য পাওয়ার আশা করি। শতটি প্রশ্নে এক চতুর্থাংশ করে সঠিক উত্তরের গড় যেমন পঁচিশ, ঠিক তেমনি।"},
            {"index": 6, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ভেদাঙ্ক বা ভ্যারিয়্যান্স ভার এক্স সমান সিগমা বর্গ, সমান এন গুণ পি গুণ এক মাইনাস পি। এটি হলো দ্বিপদী বিস্তারের অনিশ্চয়তার গাণিতিক পরিমাপ, যা পরবর্তী ল্যাবে প্রত্যক্ষ করা যাবে।"},
        ],
    },

    "sec-galton-board": {
        "title": "গ্যালটন বোর্ড: পিন থেকে জন্ম নেওয়া ঘণ্টা আকৃতির কার্ভ",
        "audio_file": "sec-galton-board.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "ষষ্ঠ পরিচ্ছেদ, গ্যালটন বোর্ড, পিন থেকে জন্ম নেওয়া ঘণ্টা আকৃতির কার্ভ।"},
            {"index": 1, "type": "p",
             "tts": "১৮৭৩ সালে বিজ্ঞানী স্যার ফ্রান্সিস গ্যালটন দ্বিপদী বিন্যাসকে চোখের সামনে জীবন্ত করতে এক চমৎকার যন্ত্র বানিয়েছিলেন, গ্যালটন বোর্ড। উপর থেকে ফেলা একটি মার্বেল প্রতিটি পিনের গায়ে আঘাত করে আধা সম্ভাবনায় ডানে বা বাঁয়ে হেলে পড়ে। এই প্রতিটি সংঘর্ষই আসলে একটি স্বাধীন বার্নৌলি ট্রায়াল।"},
            {"index": 2, "type": "p", "visual": True,
             "tts": "চিত্রের ত্রিভুজাকার পিনের সারি আর নিচের খোপগুলোতে জমা মার্বেল দেখা যাচ্ছে। মাঝখানের খোপগুলোতে সবচেয়ে বেশি আর দুই প্রান্তে খুব কম মার্বেল জমা পড়েছে। এই উচ্চতাগুলো সরাসরি প্যাসকেলের ত্রিভুজের দ্বিপদী সহগগুলোকেই প্রদর্শন করে।"},
            {"index": 3, "type": "p", "role": "conclusion",
             "tts": "বিস্ময়কর ব্যাপার হলো, যখন এন বৃদ্ধি পায় তখন এই স্তূপটি একটি নিখুঁত মসৃণ নরমাল বেল কার্ভে রূপ নেয়। বিশৃঙ্খল, এলোমেলো ছোট ঘটনাগুলো একত্র হয়ে বিশ্বব্রহ্মাণ্ডের সুশৃঙ্খল ঘণ্টা আকৃতি তৈরি করে। এই পরীক্ষাটিই পরবর্তী অধ্যায়ের সেন্ট্রাল লিমিট থিওরেম ও নরমাল কার্ভের ভিত্তিপ্রস্তর স্থাপন করে।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ডানে যাওয়ার সম্ভাবনা পি সমান শূন্য দশমিক পাঁচ, আর বাঁয়ে যাওয়ার সম্ভাবনা এক মাইনাস পি, অর্থাৎ আবার শূন্য দশমিক পাঁচ। প্রতিটি পেরেকের সংঘর্ষে মার্বেলটি নিরপেক্ষভাবে দ্বিখণ্ডিত হয়।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ডি মইভ্র লাপ্লাসের আসন্নায়ন। ট্রায়াল সংখ্যা এন অসীমের দিকে বাড়লে দ্বিপদী বিন্যাস অবিচ্ছিন্ন নরমাল গাউসিয়ান বক্ররেখায় রূপ নেয়, যার কেন্দ্রে থাকে মিউ ইকুয়াল এন পি আর বিস্তার নির্ধারিত হয় সিগমা দ্বারা।"},
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

    # Manifest keys are exactly the 6 canonical DOM section ids (in DOM order).
    manifest_sections = {sec_id: built[sec_id] for sec_id in SECTIONS_DATA}

    manifest_data = {
        "course": "probability",
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
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
    assert total_cues == EXPECTED_TOTAL

    print("\n" + "=" * 68)
    print("BUILD COMPLETE - expressive teacher audio, Probability Lesson 03")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<24} {len(msec['cues']):>2} cues  "
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
    assert mkeys == canonical_ids, f"Manifest keys changed: {mkeys}"
    assert canonical_ids == [s["id"] for s in data["engine"]], "Engine ids changed"
    assert not ({"sec-quizzes", "sec-quiz", "sec-media", "sec-simulator"} & set(dom_ids)), \
        "quiz/media/non-narrated section leaked into DOM sections"

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
