# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Differential Equations Lesson 04
("Partial Differential Equations & Boundary Conditions", Bengali) to gold standard.

Deterministic, re-runnable, self-contained:
  * 40 cues in 5 narrated sections with EXACTLY the same section IDs, audio_file
    names, alias and section order as the live narration-engine DOM / manifest.json
    (verified 9/8/8/8/7 for sec-heat-intro / sec-curvature-intuition /
    sec-sine-decay / sec-fourier-series / sec-entropy-irreversibility).
    sec-interactive-lab and sec-quizzes carry data-no-narration="true" and are
    deliberately excluded.
  * Section IDs and block types were extracted FIRST from the live DOM through
    narration_engine.js's own selector
    ('h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
     .code-showcase, .formula-box'), not guessed from prose. Exact DOM callout
    variants (callout-gold / callout-blue / callout-green / callout-purple /
    callout-red) are preserved.
  * Visual explanations are genuine, natural 2-4 sentence teacher phrasing —
    the artificial label "চিত্র প্রদর্শনী" is never used.
  * Fully phonetic spoken Bengali (no TeX / Latin / markup). Safeguards:
      PDE -> পি ডি ই, Fourier -> ফুরিয়ার, entropy -> এন্ট্রপি,
      curvature -> কার্ভেচার, boundary -> বাউন্ডারি, ODE -> ও ডি ই,
      u(x,t) -> ইউ অব এক্স কমা টি,  du/dt -> ডেল ইউ বাই ডেল টি,
      d2u/dx2 -> ডেল স্কয়ার ইউ বাই ডেল এক্স স্কয়ার,
      e^{...} -> ই টু দ্য পাওয়ার ..., sin -> সাইন.
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
  python governance/build_expressive_teacher_audio_de04.py
  python governance/build_expressive_teacher_audio_de04.py --verify-only
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
                         "differential_equations", "lesson_04")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "differential_equations",
                         "lesson_04.html")
MANIFEST_TITLE = "অধ্যায় ০৪ — আংশিক অন্তরক সমীকরণ ও সীমানা শর্ত"

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
    "callout-red":   ("+0%", "+0Hz", "+0%"),
    "formula-box":   ("-8%", "+0Hz", "+0%"),   # slow and deliberate
    "code-showcase": ("+0%", "+0Hz", "+0%"),
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")     # calm concluding prose

ALLOWED_CUE_TYPES = set(PROSODY_DEFAULT) | {"conclusion"}

# Exact DOM block-type sequence per narrated section (extracted from narration_engine).
EXPECTED_TYPES = {
    "sec-heat-intro":           ["h2", "chapter-quote", "p", "p", "figure", "p", "formula-box", "p", "callout-gold"],
    "sec-curvature-intuition":  ["h2", "p", "figure", "p", "p", "formula-box", "callout-blue", "p"],
    "sec-sine-decay":           ["h2", "p", "callout-green", "formula-box", "p", "formula-box", "callout-gold", "p"],
    "sec-fourier-series":       ["h2", "p", "chapter-quote", "p", "formula-box", "p", "formula-box", "callout-purple"],
    "sec-entropy-irreversibility": ["h2", "p", "figure", "p", "callout-red", "p", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-heat-intro":             "sec_01_heat_intro.mp3",
    "sec-curvature-intuition":    "sec_02_curvature_intuition.mp3",
    "sec-sine-decay":             "sec_03_sine_decay.mp3",
    "sec-fourier-series":         "sec_04_fourier_series.mp3",
    "sec-entropy-irreversibility":"sec_05_entropy_irreversibility.mp3",
}
EXPECTED_ALIASES = {
    "sec-heat-intro":             "sec_01_heat_intro",
    "sec-curvature-intuition":    "sec_02_curvature_intuition",
    "sec-sine-decay":             "sec_03_sine_decay",
    "sec-fourier-series":         "sec_04_fourier_series",
    "sec-entropy-irreversibility":"sec_05_entropy_irreversibility",
}
EXPECTED_COUNT = {
    "sec-heat-intro": 9, "sec-curvature-intuition": 8,
    "sec-sine-decay": 8, "sec-fourier-series": 8,
    "sec-entropy-irreversibility": 7,
}
EXPECTED_TOTAL = 40

OLD_VERSIONS = []  # recorded during bump_page_manifest_version()

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (40 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-heat-intro": {
        "title": "আংশিক অন্তরক সমীকরণ ও তাপ সমীকরণের সূচনা",
        "alias": "sec_01_heat_intro",
        "audio_file": "sec_01_heat_intro.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, আংশিক অন্তরক সমীকরণ ও তাপ সমীকরণের সূচনা।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "জোসেফ ফুরিয়ার বলেছিলেন, প্রকৃতির গভীর অনুধ্যানই হলো গাণিতিক আবিষ্কারের সবচেয়ে উর্বর উৎস।"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, গত অধ্যায়গুলোতে আমরা সাধারণ অন্তরক সমীকরণ দেখেছি, যেখানে পরিবর্তনের চলক ছিল একটি মাত্র, সময় টি। পেন্ডুলামের কোণ হোক কিংবা স্প্রিংয়ের সরণ, সবকিছুই একক চলকের ওপর নির্ভর করত। আজ আমরা পা রাখব আংশিক অন্তরক সমীকরণ বা পি ডি ই এর এক অপার মহিমাময় জগতে।"},
            {"index": 3, "type": "p",
             "tts": "কল্পনা করুন একটি একমাত্রিক সরু ধাতব রড। এই রডের প্রতিটি বিন্দুতে তাপমাত্রা সব সমান নাও হতে পারে, আর সময়ের সাথে সাথে সেই তাপমাত্রা ক্রমাগত পরিবর্তিত হচ্ছে। কেবল সময় জানা থাকলে আপনি বলতে পারবেন না কত তাপমাত্রা, আপনাকে জানতে হবে কোন অবস্থানে পরিমাপ করছেন। তাই তাপমাত্রাকে লিখতে হয় ইউ অব এক্স কমা টি, অর্থাৎ অবস্থান এক্স আর সময় টি, দুই চলকের যুগল ফাংশন হিসেবে।"},
            {"index": 4, "type": "figure", "visual": True,
             "tts": "এই চিত্রে একটি ধাতব রড বরাবর অবস্থান এক্স অনুভূমিক অক্ষে আর ওই বিন্দুর তাপমাত্রা ইউ অব এক্স কমা টি উল্লম্ব অক্ষে দেখানো হয়েছে। লাল বক্ররেখাটি মাঝখানে এক উঁচু চূড়া তৈরি করেছে, অর্থাৎ সেখানে রড সবচেয়ে বেশি গরম, আর দুই প্রান্ত তুলনামূলক ঠান্ডা। লক্ষ্য করুন কীভাবে একই মুহূর্তে তাপমাত্রা অবস্থানের সাথে সাথে বদলাচ্ছে। এটি আর কেবল সময়ের ফাংশন নয়, বরং দুই চলকের যুগল ফাংশন, আর এটাই আংশিক অন্তরক সমীকরণের জগতে প্রবেশের প্রথম ধাপ।"},
            {"index": 5, "type": "p",
             "tts": "যেহেতু তাপমাত্রা একই সাথে অবস্থান এক্স আর সময় টি, উভয়ের ওপর নির্ভরশীল, তাই একে বর্ণনা করতে আমাদের প্রয়োজন স্থানিক ও কালিক আংশিক অন্তরজ। আর এই গতিপ্রকৃতি নির্ধারণকারী কেন্দ্রীয় সমীকরণটিই হলো তাপ সমীকরণ, যা আমাদের বলে দেয় কোনো বিন্দুতে তাপ কত দ্রুত বাড়ছে বা কমছে।"},
            {"index": 6, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, একমাত্রিক তাপ সমীকরণ, ডেল ইউ বাই ডেল টি সমান আলফা গুণ ডেল স্কয়ার ইউ বাই ডেল এক্স স্কয়ার। বামপাশে সময়ের প্রথম অন্তরজ আর ডানপাশে অবস্থানের দ্বিতীয় অন্তরজ, এই বৈষম্যমূলক সমীকরণটিই স্থান ও কালের মাঝে নিখুঁত যোগসূত্র তৈরি করে।"},
            {"index": 7, "type": "p",
             "tts": "এখানে আলফা হলো পদার্থের তাপীয় ব্যাপন সহগ, বা থার্মাল ডিফিউসিভিটি, যা বলে দেয় ওই ধাতুর ভেতর দিয়ে তাপ কত দ্রুত ছড়িয়ে পড়ে। আলফার মান যত বেশি, তাপ তত দ্রুত সমতল হয়ে আসে।"},
            {"index": 8, "type": "callout-gold",
             "tts": "বিশেষ নোট, আংশিক অন্তরক সমীকরণের বিশেষত্ব। সাধারণ সমীকরণে ফাংশন কেবল একটি চলকের ওপর নির্ভরশীল থাকে। কিন্তু বাস্তব মহাবিশ্বে তরঙ্গ, তাপ, বিদ্যুৎ ও মহাকর্ষ, সবই স্থান ও সময় উভয়ের ওপর যুগপৎ নির্ভর করে। এই বহুচলকীয় প্রকৃতিই পি ডি ই কে এমন শক্তিশালী করে তুলেছে।"},
        ],
    },

    "sec-curvature-intuition": {
        "title": "বক্রতার স্বজ্ঞাত অর্থ ও স্থানীয় তাপমাত্রা মসৃণকরণ",
        "alias": "sec_02_curvature_intuition",
        "audio_file": "sec_02_curvature_intuition.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, কার্ভেচার বা বক্রতার স্বজ্ঞাত অর্থ ও স্থানীয় তাপমাত্রা মসৃণকরণ।"},
            {"index": 1, "type": "p",
             "tts": "প্রথম দর্শনে সমীকরণটির বামপাশে সময়ের প্রথম অন্তরজ আর ডানপাশে অবস্থানের দ্বিতীয় অন্তরজ দেখে অবাক লাগা স্বাভাবিক। কোনো বিন্দুতে তাপমাত্রা পরিবর্তনের হার কেন অবস্থানের বক্রতার সমানুপাতিক হবে? এর উত্তর লুকিয়ে আছে তাপগতির মৌলিক বিধানে, তাপ স্বতঃস্ফূর্তভাবে উষ্ণ বিন্দু থেকে শীতল বিন্দুর দিকে প্রবাহিত হয়।"},
            {"index": 2, "type": "figure", "visual": True,
             "tts": "এই চিত্রে দুটি পরিস্থিতি পাশাপাশি দেখানো হয়েছে। বাঁয়ের অবতল উপত্যকায় কেন্দ্রীয় বিন্দুটি তার দুই প্রতিবেশীর গড়ের নিচে থাকায় ডেল স্কয়ার ইউ বাই ডেল এক্স স্কয়ার ধনাত্মক, আর তাই তাপ ভেতরে এসে তাপমাত্রা বাড়ে। ডানের উত্তল চূড়ায় বিন্দুটি প্রতিবেশীদের গড়ের ওপরে থাকায় দ্বিতীয় অন্তরজ ঋণাত্মক, আর তাপ বাইরে ছড়িয়ে গিয়ে তাপমাত্রা কমে। মাঝের সোজা রেখায় বক্রতা শূন্য, অর্থাৎ কোনো নিট প্রবাহ নেই।"},
            {"index": 3, "type": "p",
             "tts": "রডের যেকোনো ক্ষুদ্র বিন্দু এক্স কল্পনা করুন, যার ঠিক বামে আছে প্রতিবেশী বিন্দু এক্স মাইনাস ডেল্টা এক্স আর ডানে এক্স প্লাস ডেল্টা এক্স। যদি বিন্দুটির তাপমাত্রা তার দুই প্রতিবেশীর গড়ের চেয়ে কম হয়, তবে চারপাশ থেকে তাপ এসে তাকে গরম করে তুলবে।"},
            {"index": 4, "type": "p",
             "tts": "আর বিন্দুটি যদি প্রতিবেশীদের চেয়ে বেশি গরম হয়, তবে তাপ দুই পাশে ছড়িয়ে গিয়ে বিন্দুটিকে ঠান্ডা করে তুলবে। এক কথায়, প্রকৃতি সবসময় চূড়া নামিয়ে উপত্যকা ভরাট করার চেষ্টা করে।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, দ্বিতীয় অন্তরজের সসীম অন্তর রূপ, ডেল স্কয়ার ইউ বাই ডেল এক্স স্কয়ার প্রায় সমান, ইউ অব এক্স প্লাস ডেল্টা এক্স বিয়োগ দুই ইউ অব এক্স যোগ ইউ অব এক্স মাইনাস ডেল্টা এক্স, ভাগ ডেল্টা এক্স স্কয়ার।"},
            {"index": 6, "type": "callout-blue",
             "tts": "বিশেষ নোট, জ্যামিতিক অন্তর্দৃষ্টি, বক্রতা বা কার্ভেচার। ক্যালকুলাসে দ্বিতীয় অন্তরজ হলো বক্ররেখার বাঁক বা অবতলতার পরিমাপ। দ্বিতীয় অন্তরজ ধনাত্মক হলে হাসিমুখী অবতল বক্রতা তৈরি হয়, আর ঋণাত্মক হলে বিষাদময় উত্তল বক্রতা। আর এই কার্ভেচারই নির্ধারণ করে কোনো বিন্দুতে তাপ বাড়বে নাকি কমবে।"},
            {"index": 7, "type": "p",
             "tts": "এ কারণে তাপ সমীকরণ মহাবিশ্বের সবচেয়ে নিখুঁত মসৃণকারী যন্ত্র। এটি যেকোনো ঢেউ, খাঁজ বা অসঙ্গতিকে নিরবচ্ছিন্নভাবে মুছে দিয়ে পুরো অঞ্চলকে সমতল করে ফেলে।"},
        ],
    },

    "sec-sine-decay": {
        "title": "সীমানা শর্ত, সাইন তরঙ্গের সূচকীয় ক্ষয় ও আইগেনমোড",
        "alias": "sec_03_sine_decay",
        "audio_file": "sec_03_sine_decay.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, বাউন্ডারি বা সীমানা শর্ত, সাইন তরঙ্গের সূচকীয় ক্ষয় ও আইগেনমোড।"},
            {"index": 1, "type": "p",
             "tts": "স্থানীয় ভৌতিক অন্তর্দৃষ্টি তো পাওয়া গেল, কিন্তু একটি নির্দিষ্ট দৈর্ঘ্যের রডে বাস্তব সমাধান নির্ধারণ করতে আমাদের প্রয়োজন প্রান্তীয় বাউন্ডারি কন্ডিশন বা সীমানা শর্ত। ডিফারেনশিয়াল সমীকরণ কেবল স্থানীয় নিয়ম দেয়, আর সীমানা শর্তই ঠিক করে দেয় কোন সমাধানটা আমাদের রডের জন্য বৈধ।"},
            {"index": 2, "type": "callout-green",
             "tts": "বিশেষ নোট, ডিরিখলে বাউন্ডারি শর্ত। ধরা যাক দৈর্ঘ্য এলের একটি ধাতব দণ্ড, যার দুই প্রান্ত এক্স সমান শূন্য ও এক্স সমান এল বরফের পানিতে শূন্য ডিগ্রি তাপমাত্রায় স্থির রাখা হয়েছে। অর্থাৎ ইউ অব শূন্য কমা টি আর ইউ অব এল কমা টি, দুটিই সর্বদা শূন্য।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ডিরিখলে বাউন্ডারি শর্ত, ইউ অব শূন্য কমা টি সমান শূন্য এবং ইউ অব এল কমা টি সমান শূন্য। অনুমোদিত স্থানিক সাইন মোড হলো সাইন অব এন পাই এক্স বাই এল, যা রডের উভয় প্রান্তে নিখুঁতভাবে শূন্য মান বজায় রাখে।"},
            {"index": 4, "type": "p",
             "tts": "এই সাইন ফাংশনকে এক্স এর সাপেক্ষে দুবার অন্তরীকরণ করলে পাওয়া যায়, মাইনাস এন পাই বাই এল হোল স্কয়ার গুণ আদি সাইন ফাংশন। বক্রতা মূল ফাংশনেরই সমানুপাতিক হওয়ায় আংশিক সমীকরণটি সাধারণ ক্ষয় সমীকরণে রূপান্তরিত হয়, যার সমাধান সূচকীয় আকারে লেখা যায়।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, সময় বিবর্তন সমাধান, ইউ সাব এন অব এক্স কমা টি সমান ই টু দ্য পাওয়ার মাইনাস আলফা এন পাই বাই এল হোল স্কয়ার গুণ টি, ভাগ করে সাইন অব এন পাই এক্স বাই এল দিয়ে। প্রতিটি মোড নিজস্ব হারে মিলিয়ে যায়, কিন্তু তার আকার অটুট থাকে।"},
            {"index": 6, "type": "callout-gold",
             "tts": "বিশেষ নোট, কম্পাঙ্কের বর্গের প্রভাব। সূচক রাশিতে লক্ষ্য করুন এন স্কয়ার, অর্থাৎ ক্ষয়ের গতিবেগ কম্পাঙ্কের বর্গের সমানুপাতিক। উচ্চ কম্পাঙ্কের সূক্ষ্ম ঢেউগুলো তীব্র গতিতে বিলীন হয়ে যায়, আর নিম্ন কম্পাঙ্কের চওড়া ঢেউগুলো অনেক দীর্ঘ সময় টিকে থাকে।"},
            {"index": 7, "type": "p",
             "tts": "এই কারণে বাউন্ডারি শর্ত মান্যকারী সাইন তরঙ্গগুলোকে তাপ সমীকরণের স্বাভাবিক আইগেনমোড বলা হয়। তারা রূপ না বদলিয়ে কেবল নিজস্ব গতিতে মিলিয়ে যায়, ঠিক যেমন এক বাদ্যযন্ত্রের তার নিজস্ব সুরে কম্পন করে।"},
        ],
    },

    "sec-fourier-series": {
        "title": "জোসেফ ফুরিয়ারের বিপ্লব ও তরঙ্গের উপরিপাত",
        "alias": "sec_04_fourier_series",
        "audio_file": "sec_04_fourier_series.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, জোসেফ ফুরিয়ারের বৈপ্লবিক দাবি ও হারমোনিক উপরিপাত।"},
            {"index": 1, "type": "p",
             "tts": "একটি বিশুদ্ধ সাইন তরঙ্গের সমাধান তো পাওয়া গেল, কিন্তু বাস্তব জীবনে ধাতব রডের শুরুর তাপমাত্রা কখনোই নিখুঁত সাইন তরঙ্গ হয় না। যদি রডের অর্ধেকটা একশত ডিগ্রি ফুটন্ত জলে থাকে আর বাকি অর্ধেকটা শূন্য ডিগ্রির বরফে থাকে, তবে তার তাপ বণ্টন হবে একটি ধারালো সোপান, যা কোনো একক সাইন দিয়ে বোঝা যায় না।"},
            {"index": 2, "type": "chapter-quote",
             "tts": "১৮০৭ সালে ফরাসি গণিতবিদ জোসেফ ফুরিয়ার দাবি করেছিলেন, বাউন্ডারি শর্ত মান্যকারী যেকোনো তাপমাত্রা অপেক্ষককে অসীম সংখ্যক সাইন তরঙ্গের যোগফল হিসেবে লেখা সম্ভব।"},
            {"index": 3, "type": "p",
             "tts": "লাগ্রাঞ্জ ও লাপ্লাসের মতো দিগ্গজ গণিতবিদরা চমকে উঠেছিলেন, মসৃণ সাইন ঢেউ যোগ করে কীভাবে খাড়া ও ধারালো কোণা তৈরি করা সম্ভব? কিন্তু ফুরিয়ার ছিলেন সম্পূর্ণ নির্ভুল। তাঁর এই দাবিই আজ ফুরিয়ার ধারা নামে পরিচিত।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ফুরিয়ার সাইন ধারা, এফ অব এক্স সমান সামেশন এন ইকুয়াল ওয়ান টু ইনফিনিটি, বি সাব এন গুণ সাইন অব এন পাই এক্স বাই এল। আর সহগ বি সাব এন পাওয়া যায় লম্বতার ধর্ম থেকে, দুই ভাগ এল গুণ ইন্টিগ্রাল শূন্য থেকে এল, এফ অব এক্স গুণ সাইন অব এন পাই এক্স বাই এল ডি এক্স।"},
            {"index": 5, "type": "p",
             "tts": "এবং সবচেয়ে চমকপ্রদ বিষয় হলো, তাপ সমীকরণটি রৈখিক। তাই উপরিপাত নীতি অনুসারে প্রতিটি অনুমোদিত সাইন কম্পাঙ্ককে তার নিজস্ব সূচকীয় হারে ক্ষয় হতে দিন, তারপর সবগুলোকে পুনরায় যোগ করে দিন।"},
            {"index": 6, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, পূর্ণ তাপ সমীকরণ সমাধান, ইউ অব এক্স কমা টি সমান সামেশন বি সাব এন গুণ ই টু দ্য পাওয়ার মাইনাস আলফা এন পাই বাই এল হোল স্কয়ার গুণ টি, গুণ সাইন অব এন পাই এক্স বাই এল। প্রতিটি টুকরো আলাদাভাবে ক্ষয় হয়, আর তাদের যোগফলই আমাদের চূড়ান্ত উত্তর।"},
            {"index": 7, "type": "callout-purple",
             "tts": "বিশেষ নোট, গাণিতিক ঐশ্বর্য। জটিল এক আংশিক অন্তরক সমীকরণ সমাধান হয়ে গেল, কেবল আদি অপেক্ষকটিকে বাউন্ডারি শর্তের সাথে সঙ্গতিপূর্ণ ফুরিয়ার ধারায় ভেঙে ফেলে এবং প্রতিটি টুকরোকে স্বাধীনভাবে সময়ের সাথে মিলিয়ে যেতে দিয়ে। ত্রিকোণমিতি, সমাকলন ও অন্তরকের এই সমন্বয়ই আধুনিক পদার্থবিজ্ঞানের ভিত্তি।"},
        ],
    },

    "sec-entropy-irreversibility": {
        "title": "তাপের মসৃণকরণ, এনট্রপি ও সময়ের একমুখী তীর",
        "alias": "sec_05_entropy_irreversibility",
        "audio_file": "sec_05_entropy_irreversibility.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, তাপের মসৃণকরণ, এন্ট্রপি বৃদ্ধি ও সময়ের একমুখী তীর।"},
            {"index": 1, "type": "p",
             "tts": "ফুরিয়ার ধারার সমাধানটি লক্ষ্য করলে একটি গভীর প্রাকৃতিক সত্য বেরিয়ে আসে। উচ্চ কম্পাঙ্কগুলো ই টু দ্য পাওয়ার মাইনাস এন স্কয়ার হারে ক্ষয়প্রাপ্ত হওয়ায় আদি তাপমাত্রার সমস্ত সূক্ষ্ম তথ্য প্রায় তাৎক্ষণিকভাবেই বিলীন হয়ে যায়।"},
            {"index": 2, "type": "figure", "visual": True,
             "tts": "এই চিত্রে একই রডের তাপ প্রোফাইল তিনটি সময়ে দেখানো হয়েছে, শূন্য, এক ও পাঁচ। শুরুর লাল রেখাটি খাঁজকাটা ও অসম, অনেক সূক্ষ্ম হারমোনিকে ভরা। কালের সাথে সাথে নীল ও সবুজ রেখা ক্রমশ মসৃণ হয়ে এক মৃদু সাইন কার্ভে রূপ নিচ্ছে। লক্ষ্য করুন, যে সূক্ষ্ম তথ্য আদিতে ছিল তাপ সমীকরণ তা সমূলে মুছে দিচ্ছে, আর এটিই এন্ট্রপি বৃদ্ধির দৃশ্যমান রূপ।"},
            {"index": 3, "type": "p",
             "tts": "আপনি যদি সমীকরণে সময় টি এর স্থলে মাইনাস টি বসিয়ে অতীতে ফিরে যাওয়ার চেষ্টা করেন, তবে ঋণাত্মক ঘাত ধনাত্মক হয়ে ওঠে এবং উচ্চ কম্পাঙ্কগুলো বিস্ফোরক হারে অসীমের দিকে বৃদ্ধি পায়।"},
            {"index": 4, "type": "callout-red",
             "tts": "বিশেষ নোট, ইল পোজড ব্যাকওয়ার্ড হিট ইকুয়েশন। নিউটনের গতিসূত্র বা ম্যাক্সওয়েলের তড়িৎচৌম্বকীয় সমীকরণ উভয় দিকেই কাজ করে, কিন্তু তাপ সমীকরণ সম্পূর্ণ ভিন্ন। অতি নগণ্য পরিমাপের ত্রুটিও পেছনের সময় গণনা করতে গেলে মহাজাগতিক বিস্ফোরণের রূপ নেয়। অতীতকে পুঙ্খানুপুঙ্খভাবে পুনরুদ্ধার করা গণিত ও পদার্থবিজ্ঞান উভয়ের দৃষ্টিতেই অসম্ভব।"},
            {"index": 5, "type": "p",
             "tts": "এটিই হলো তাপগতিবিদ্যার দ্বিতীয় সূত্র, এন্ট্রপির অবিরত বৃদ্ধি। তাপ সমীকরণ প্রমাণ করে কেন গরম কফি সর্বদা জুড়িয়ে ঘরের তাপমাত্রায় আসে, কিন্তু কক্ষের তাপ শোষণ করে ঠান্ডা কফি কখনো নিজে থেকে ফুটে ওঠে না।"},
            {"index": 6, "type": "p", "role": "conclusion",
             "tts": "এভাবেই জোসেফ ফুরিয়ারের হাত ধরে গণিতের এক সমীকরণ বিশ্বব্রহ্মাণ্ডের সবচেয়ে মৌলিক সত্য, সময়ের একমুখী যাত্রাকে গাণিতিক রূপ দিয়েছে। সরল তাপ পরিবাহিতা থেকে মহাবিশ্বের এন্ট্রপি পর্যন্ত, এই একটিমাত্র সমীকরণ আমাদের দেখিয়ে দেয় কীভাবে কোলাহলপূর্ণ শুরু থেকে শান্ত সাম্যাবস্থায় পৌঁছায় পুরো প্রকৃতি।"},
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

    # Manifest keys are exactly the 5 canonical DOM section ids (in DOM order).
    manifest_sections = {sec_id: built[sec_id] for sec_id in SECTIONS_DATA}

    manifest_data = {
        "course": "differential_equations",
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
    print("BUILD COMPLETE - expressive teacher audio, Differential Equations Lesson 04")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<30} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTIONS_DATA)} sections, "
          f"{total_ms / 1000.0:.2f}s, {visuals} natural visual explanations.")
    print("  manifest.json is valid JSON; all 5 mp3 files exist and are non-empty.")
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
    print("VERIFIED: 40/40 cues, DOM<->manifest 1:1, 0 dups, 0 quiz/media-tab types, "
          "non-zero mp3s, valid JSON, 0 JS page errors, 0 'চিত্র প্রদর্শনী' labels.")
    print("=" * 70)


if __name__ == "__main__":
    main()
