# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Differential Equations Lesson 06
("The Wave Equation and Vibrations", Bengali) to gold standard.

Deterministic, re-runnable, self-contained:
  * 35 cues in 5 narrated sections with EXACTLY the same section IDs, audio_file
    names, alias and section order as the live narration-engine DOM / manifest.json
    (verified 8/8/7/6/6 for sec-wave-intro / sec-wave-derivation /
    sec-standing-waves / sec-dalembert / sec-energy-harmonics).
    sec-figures, sec-interactive-lab, sec-quizzes and sec-video-note carry
    data-no-narration="true" (or live outside .article) and are excluded.
  * Section IDs and block types were extracted FIRST from the live DOM through
    narration_engine.js's own selector
    ('h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
     .code-showcase, .formula-box'), not guessed from prose. Exact DOM callout
    variants (callout-gold / callout-blue / callout-purple / callout-green)
    are preserved (domType() of the engine). See de06_dom_blocks.json.
  * Visual explanations are genuine, natural 2-4 sentence teacher phrasing —
    the artificial label "চিত্র প্রদর্শনী" is never used.
  * Fully phonetic spoken Bengali (no TeX / Latin / markup). Safeguards:
      wave equation -> ওয়েভ ইকুয়েশন, d'Alembert -> ডি'অ্যালেম্বার্ট,
      standing wave -> স্ট্যান্ডিং ওয়েভ, harmonic -> হারমনিক,
      tension -> টেনশন;  u(x,t) -> ইউ অব এক্স কমা টি,
      ∂²u/∂t² -> ডেল স্কয়ার ইউ বাই ডেল টি স্কয়ার,
      ∂²u/∂x² -> ডেল স্কয়ার ইউ বাই ডেল এক্স স্কয়ার,
      c = sqrt(T/mu) -> সি সমান টেনশন ও মিউর অনুপাতের বর্গমূল.
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
  * This lesson has NO official 3B1B dubbed video; the optional video-src is
    deliberately left untouched.

Usage:
  python governance/build_expressive_teacher_audio_de06.py
  python governance/build_expressive_teacher_audio_de06.py --verify-only
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
                         "differential_equations", "lesson_06")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "differential_equations",
                         "lesson_06.html")
MANIFEST_TITLE = "অধ্যায় ০৬ — তরঙ্গ সমীকরণ ও কম্পন"

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
    "sec-wave-intro":           ["h2", "chapter-quote", "p", "p", "figure", "p", "formula-box", "callout-gold"],
    "sec-wave-derivation":      ["h2", "p", "p", "figure", "p", "formula-box", "p", "callout-blue"],
    "sec-standing-waves":       ["h2", "p", "p", "formula-box", "p", "figure", "callout-purple"],
    "sec-dalembert":            ["h2", "p", "formula-box", "p", "figure", "callout-green"],
    "sec-energy-harmonics":     ["h2", "p", "formula-box", "p", "figure", "callout-gold"],
}
EXPECTED_AUDIO_FILES = {
    "sec-wave-intro":           "sec_01_wave_intro.mp3",
    "sec-wave-derivation":      "sec_02_wave_derivation.mp3",
    "sec-standing-waves":       "sec_03_standing_waves.mp3",
    "sec-dalembert":            "sec_04_dalembert.mp3",
    "sec-energy-harmonics":     "sec_05_energy_harmonics.mp3",
}
EXPECTED_ALIASES = {
    "sec-wave-intro":           "sec_01_wave_intro",
    "sec-wave-derivation":      "sec_02_wave_derivation",
    "sec-standing-waves":       "sec_03_standing_waves",
    "sec-dalembert":            "sec_04_dalembert",
    "sec-energy-harmonics":     "sec_05_energy_harmonics",
}
EXPECTED_COUNT = {
    "sec-wave-intro": 8, "sec-wave-derivation": 8,
    "sec-standing-waves": 7, "sec-dalembert": 6,
    "sec-energy-harmonics": 6,
}
EXPECTED_TOTAL = 35

OLD_VERSIONS = []  # recorded during bump_page_manifest_version()

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (35 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-wave-intro": {
        "title": "তরঙ্গ সমীকরণের সূচনা: তাপের মসৃণকরণ বনাম অবিরাম স্পন্দন",
        "alias": "sec_01_wave_intro",
        "audio_file": "sec_01_wave_intro.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, তরঙ্গ সমীকরণ বা ওয়েভ ইকুয়েশনের সূচনা, তাপের মসৃণকরণ বনাম অবিরাম স্পন্দন।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "জঁ লে রঁ ডি'অ্যালেম্বার্ট বলেছিলেন, প্রকৃতি কম্পনের মাঝে কোনো জটিল ধাঁধা লুকিয়ে রাখেনি, সে কেবল স্থান ও সময়কে তরঙ্গের ছন্দে বেঁধে দিয়েছে।"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, গত অধ্যায়ে আমরা আংশিক ডিফারেনশিয়াল সমীকরণের জগতে পা রেখে তাপ সমীকরণ প্রত্যক্ষ করেছি। সেখানে সময়ের অন্তরজটি ছিল প্রথম ক্রমের, অর্থাৎ একবারই অন্তরীকরণ করা হয়েছিল।"},
            {"index": 3, "type": "p",
             "tts": "সেই প্রথম ডেরিভেটিভের কারণে যেকোনো ধারালো খাঁজ বা তাপমাত্রা একমুখীভাবে মসৃণ হয়ে শূন্যে মিলিয়ে যেত। উচ্চ ফ্রিকোয়েন্সিগুলো ধ্বংস হয়ে যেত, তথ্য হারিয়ে যেত আর ব্যবস্থাটি অনিবার্যভাবে তাপীয় সাম্যাবস্থায় পৌঁছাত।"},
            {"index": 4, "type": "figure", "visual": True,
             "tts": "এই চিত্রে বাঁ ও ডান প্যানেল পাশাপাশি রাখা হয়েছে। বাঁয়ে তাপ সমীকরণের ধারালো খাঁজটি ক্রমশ মসৃণ হয়ে সমতল হচ্ছে, অর্থাৎ তথ্য বিলীন হয়ে যাচ্ছে। ডানে তরঙ্গ সমীকরণের একই খাঁজ বিন্দুমাত্র রূপ না হারিয়ে দুই দিকে অবিকল ছড়িয়ে চলেছে, আর তার চূড়ার উচ্চতা অপরিবর্তিত রয়ে গেছে।"},
            {"index": 5, "type": "p",
             "tts": "কিন্তু এবার এক মহাবিস্ময়কর প্রশ্ন ভাবুন, সময়ের সেই প্রথম অন্তরজের জায়গায় যদি আমরা দ্বিতীয় অন্তরজ অর্থাৎ ত্বরণ বসিয়ে দিই? মাত্র একটি ডেরিভেটিভের ক্রম বাড়ার সাথে সাথে পুরো বিশ্বব্রহ্মাণ্ডের গতিবিধি বদলে যায়। শক্তির অপচয় বিলুপ্ত হয়, তরঙ্গের রূপ অক্ষত থাকে আর সংকেত অনন্তকালের জন্য স্থান জুড়ে প্রতিধ্বনিত হতে থাকে।"},
            {"index": 6, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, একমাত্রিক ওয়েভ ইকুয়েশন, ডেল স্কয়ার ইউ বাই ডেল টি স্কয়ার সমান সি স্কয়ার গুণ ডেল স্কয়ার ইউ বাই ডেল এক্স স্কয়ার। বামপাশে সময়ের দ্বিতীয় অন্তরজ অর্থাৎ ত্বরণ আর ডানপাশে স্থানিক বক্রতা, এই সমতাই ক্ষয়হীন তরঙ্গের জন্ম দেয়।"},
            {"index": 7, "type": "callout-gold",
             "tts": "বিশেষ নোট, তাপ সমীকরণ আর তরঙ্গ সমীকরণের মধ্যেকার রূপান্তর। তাপ সমীকরণ হলো ব্যাপন ও বিস্মৃতির সমীকরণ, এতে জড়তা নেই আর এটি কেবল মসৃণ করে। আর তরঙ্গ সমীকরণ হলো ত্বরণ, জড়তা ও স্মৃতি সংরক্ষণের এক চিরন্তন সংকেতবাহক, যা কোনো ক্ষয় ছাড়াই রূপ ও বিস্তার অবিকল ধরে রাখে।"},
        ],
    },

    "sec-wave-derivation": {
        "title": "টানটান তারের ব্যবকলন ও তরঙ্গ বেগ সি সমান টেনশন ও মিউর অনুপাতের বর্গমূল",
        "alias": "sec_02_wave_derivation",
        "audio_file": "sec_02_wave_derivation.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, টানটান তারের ব্যবকলন ও তরঙ্গ বেগ, সি সমান টেনশন ও মিউর অনুপাতের বর্গমূল।"},
            {"index": 1, "type": "p",
             "tts": "এই মহিমান্বিত সমীকরণটি কোথা থেকে জন্ম নেয়? চলুন সবচেয়ে সহজ একটি ভৌত ব্যবস্থা বিবেচনা করি, দুই প্রান্তে দৃঢ়ভাবে আটকানো একটি টানটান গিটারের তার।"},
            {"index": 2, "type": "p",
             "tts": "তারটির অবস্থান এক্স এবং সময় টি, এই দুই চলকের ওপর উল্লম্ব সরণ ইউ অব এক্স কমা টি নির্ভর করে। এবার এক্স থেকে এক্স প্লাস ডেল্টা এক্স দৈর্ঘ্যের অতি ক্ষুদ্র এক টুকরো কেটে আলাদা করে ভাবুন। প্রতি একক দৈর্ঘ্যের ভর মিউ আর তারটিতে কাজ করা টেনশন ছিল টি।"},
            {"index": 3, "type": "figure", "visual": True,
             "tts": "এই চিত্রে টানটান তারের ক্ষুদ্র অংশটি আলাদা করে দেখানো হয়েছে। দুই প্রান্তে টেনশন বল টি স্পর্শক বরাবর কাজ করছে, কিন্তু দুই প্রান্তের ঢাল আলাদা হওয়ায় তাদের উল্লম্ব উপাংশ পরস্পরকে প্রশমিত করতে পারছে না। ফলে একটি নিট ঊর্ধ্বমুখী বল তৈরি হয়, আর এই অসমতা থেকেই বক্রতা ডেল স্কয়ার ইউ বাই ডেল এক্স স্কয়ার জন্ম নেয়।"},
            {"index": 4, "type": "p",
             "tts": "তারটি যদি বাঁকা বা বক্র থাকে, তবে দুই প্রান্তের টেনশন হুবহু একই সরলরেখায় থাকে না। ডান প্রান্তের ঢাল ও বাম প্রান্তের ঢাল সমান না হওয়ায় একটি নিট উল্লম্ব বল সৃষ্টি হয়, যা কণাটিকে ত্বরণ দেয়।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, নিট উল্লম্ব বল, এফ সমান ক্যাপিটাল টি অর্থাৎ টেনশন গুণ ডেল স্কয়ার ইউ বাই ডেল এক্স স্কয়ার গুণ ডেল্টা এক্স। বক্রতা যত বেশি, প্রত্যয়নী বল তত বড়।"},
            {"index": 6, "type": "p",
             "tts": "নিউটনের দ্বিতীয় সূত্র বলে, বল সমান ভর গুণ ত্বরণ। ভর মিউ গুণ ডেল্টা এক্স আর ত্বরণ ডেল স্কয়ার ইউ বাই ডেল টি স্কয়ার বসিয়ে দিলে উভয় পাশ থেকে ডেল্টা এক্স কাটাকাটি হয়ে অবিকল ওয়েভ ইকুয়েশনটি বেরিয়ে আসে। কেবল একটি ডেল্টা এক্স কমে গেল, আর জন্ম নিল এক মহাজাগতিক সমীকরণ।"},
            {"index": 7, "type": "callout-blue",
             "tts": "বিশেষ নোট, তরঙ্গ গতিবেগের ভৌত স্বজ্ঞা। সি সমান টেনশন ও মিউর অনুপাতের বর্গমূল। গিটারের তার যত বেশি টাইট করা হয়, টেনশন তত বাড়ে আর তরঙ্গ তত দ্রুত ছুটে যায়, ফলে স্বরতীক্ষ্ণতা বৃদ্ধি পায়। আবার মোটা বা ভারী তারের জড়তা বেশি হওয়ায় তরঙ্গের গতি ধীর হয় আর খাদ সুর তৈরি হয়।"},
        ],
    },

    "sec-standing-waves": {
        "title": "স্থির তরঙ্গ, চলক পৃথকীকরণ ও সুরের হারমনিক",
        "alias": "sec_03_standing_waves",
        "audio_file": "sec_03_standing_waves.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, স্থির তরঙ্গ বা স্ট্যান্ডিং ওয়েভ, চলক পৃথকীকরণ ও সুরের হারমনিক।"},
            {"index": 1, "type": "p",
             "tts": "একটি টানটান গিটারের তার যখন দুই প্রান্তে দৃঢ়ভাবে আটকানো থাকে, তখন তরঙ্গ মুক্তভাবে প্রবাহিত হতে পারে না। বরং দুই প্রান্ত থেকে অবিরাম প্রতিফলিত হয়ে একটি সুনির্দিষ্ট ছন্দে স্থির দাঁড়িয়ে থাকে। একে বলে স্থির তরঙ্গ বা স্ট্যান্ডিং ওয়েভ।"},
            {"index": 2, "type": "p",
             "tts": "এই ধরনের সীমানা মান সমস্যা সমাধানের সবচেয়ে শক্তিশালী পদ্ধতি হলো চলক পৃথকীকরণ। আমরা ধরে নিই সমাধানটি স্থানিক ও কালিক দুটি পৃথক অপেক্ষকের গুণফল, ইউ অব এক্স কমা টি সমান ক্যাপিটাল এক্স অব এক্স গুণ ক্যাপিটাল টি অব টি।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, চলক পৃথকীকরণের রূপ, এক বাই সি স্কয়ার গুণ টি ডাবল প্রাইম ভাগ টি সমান এক্স ডাবল প্রাইম ভাগ এক্স সমান মাইনাস কে স্কয়ার। বামপাশ কেবল সময়ের আর ডানপাশ কেবল দূরত্বের ফাংশন, তাই উভয়কেই একই ঋণাত্মক ধ্রুবকের সমান হতে হয়।"},
            {"index": 4, "type": "p",
             "tts": "দুই প্রান্তে আটকানোর শর্ত থেকে স্থানিক সমাধান পাওয়া যায় বিশুদ্ধ সাইন তরঙ্গ হিসেবে। আর কালিক সমীকরণটি রূপ নেয় একটি অবমন্দহীন সরল ছন্দিত স্পন্দনে, যার কম্পাঙ্ক সি গুণ এন পাই ভাগ এল। প্রতিটি মোড নিজস্ব ছন্দে স্পন্দিত হয়, কিন্তু আকৃতি কখনো বদলায় না।"},
            {"index": 5, "type": "figure", "visual": True,
             "tts": "এই অ্যানিমেশনে উপর থেকে নিচে স্থির তরঙ্গের প্রথম তিনটি মোড দেখানো হয়েছে। প্রথম মোডে মাঝখানে সর্বোচ্চ বিস্তার আর দুই প্রান্তে নিস্পন্দ বিন্দু, দ্বিতীয় মোডে মাঝখানে আরও একটি নিস্পন্দ বিন্দু যোগ হয়। মোডের ক্রম যত বাড়ে নিস্পন্দ বিন্দুর সংখ্যা তত বাড়ে আর কম্পাঙ্কও তত বাড়তে থাকে।"},
            {"index": 6, "type": "callout-purple",
             "tts": "বিশেষ নোট, বাদ্যযন্ত্রের সুর ও হারমনিক। প্রথম মোড অর্থাৎ মূল সুরে তারের মাঝখানে সর্বোচ্চ বিস্তার থাকে। দ্বিতীয় মোডে কম্পাঙ্ক অবিকল দ্বিগুণ হয়ে যায়, আর এই পূর্ণসংখ্যা গুণিতকের সম্পর্কই হারমনিক নামে পরিচিত। যেকোনো বাদ্যযন্ত্র বাজালে সমস্ত মোডের রৈখিক উপরিপাত ঘটে আর তাদের বিস্তারের অনুপাতই সুরের বর্ণ বা টিম্বার নির্ধারণ করে।"},
        ],
    },

    "sec-dalembert": {
        "title": "ডি'অ্যালেম্বার্টের পদ্ধতি ও বিপরীতমুখী চলন্ত তরঙ্গ",
        "alias": "sec_04_dalembert",
        "audio_file": "sec_04_dalembert.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, ডি'অ্যালেম্বার্টের পদ্ধতি ও বিপরীতমুখী চলন্ত তরঙ্গ।"},
            {"index": 1, "type": "p",
             "tts": "স্থির তরঙ্গ বাদ্যযন্ত্রের বদ্ধ তারের জন্য চমৎকার, কিন্তু মুক্ত মাধ্যমে ছড়িয়ে পড়া তরঙ্গের ক্ষেত্রে কী ঘটে? ১৭৪৭ সালে জঁ লে রঁ ডি'অ্যালেম্বার্ট আবিষ্কার করেন এক জাদুকরী সত্য। তিনি দেখেছিলেন তরঙ্গ সমীকরণের অপারেটরকে দুটি বর্গের বিয়োগফল হিসেবে উৎপাদকে বিশ্লেষণ করা যায়।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ডি'অ্যালেম্বার্টের সাধারণ সমাধান, ইউ অব এক্স কমা টি সমান এফ অব এক্স মাইনাস সি টি যোগ জি অব এক্স প্লাস সি টি। এর প্রথম অংশ ডান দিকে ছুটে যায় আর দ্বিতীয় অংশ বাম দিকে, দুটোই অবিকল আকৃতি নিয়ে।"},
            {"index": 3, "type": "p",
             "tts": "বৈশিষ্ট্যমূলক স্থানাঙ্ক বসিয়ে দিলে, জাই সমান এক্স মাইনাস সি টি আর এটা সমান এক্স প্লাস সি টি, তরঙ্গ সমীকরণটি সংকুচিত হয়ে দাঁড়ায় ডেল স্কয়ার ইউ বাই ডেল জাই ডেল এটা সমান শূন্য। উভয় পক্ষে ক্রমান্বয়ে দুইবার সমাকলন করলেই সাধারণ সমাধানটি সরাসরি বেরিয়ে আসে।"},
            {"index": 4, "type": "figure", "visual": True,
             "tts": "চলমান সিমুলেশনে দেখুন, কেন্দ্রে থাকা একটি ত্রিভুজাকার খাঁজ সমান দুটি অর্ধেক উচ্চতার তরঙ্গে ভেঙে যাচ্ছে। একটি বেগ সি নিয়ে ডান দিকে আর অন্যটি বেগ সি নিয়ে বাম দিকে ছুটে চলেছে। আকৃতির কোনো বিকৃতি বা শক্তির কোনো ক্ষয় ঘটছে না, দুই তরঙ্গ পরস্পরকে অতিক্রম করেও অবিকল আগের মতোই বেরিয়ে যায়।"},
            {"index": 5, "type": "callout-green",
             "tts": "বিশেষ নোট, ডি'অ্যালেম্বার্ট সমাধানের জ্যামিতিক তাৎপর্য। এফ অব এক্স মাইনাস সি টি মানে এক অনড় আকার বিন্দুমাত্র না বদলে ধ্রুব বেগে ডান দিকে এগিয়ে চলেছে। আর জি অব এক্স প্লাস সি টি একই আকৃতির অপর একটি তরঙ্গ যা বাম দিকে ছুটে যায়। কোনো ক্ষয় নেই, কোনো বিকৃতি নেই, শুধু অবিকল স্থানান্তর, এটাই রৈখিক উপরিপাতের পরম সৌন্দর্য।"},
        ],
    },

    "sec-energy-harmonics": {
        "title": "শক্তির নিত্যতা, তথ্য সংরক্ষণ ও মহাজাগতিক বিস্তার",
        "alias": "sec_05_energy_harmonics",
        "audio_file": "sec_05_energy_harmonics.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, শক্তির নিত্যতা, তথ্য সংরক্ষণ ও মহাজাগতিক বিস্তার।"},
            {"index": 1, "type": "p",
             "tts": "তরঙ্গ সমীকরণের পদার্থবৈজ্ঞানিক আত্মা নিহিত রয়েছে এর নিখুঁত শক্তি সংরক্ষণে। তাপ সমীকরণে যেখানে শক্তি একমুখীভাবে তাপে রূপান্তরিত হয়ে হারিয়ে যায়, ওয়েভ ইকুয়েশনে সেখানে শক্তি চিরকাল সম্পূর্ণ সংরক্ষিত থাকে। কম্পনশীল তারের মোট যান্ত্রিক শক্তি দুটি অংশে বিভক্ত, উল্লম্ব গতির গতিশক্তি আর টেনশনজনিত স্থিতিশক্তি।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, শক্তির নিত্যতা, সময়ের সাপেক্ষে মোট শক্তি ই এর পরিবর্তন ডি ই বাই ডি টি সমান অবিকল শূন্য। গতিশক্তি ও স্থিতিশক্তি একে অপরে রূপান্তরিত হলেও তাদের যোগফল সর্বদা একই থাকে।"},
            {"index": 3, "type": "p",
             "tts": "সমগ্র তারের ওপর শক্তির যোগফলকে সময়ের সাপেক্ষে ব্যবকলন করে দেখা যায় যে মোট শক্তির পরিবর্তন শূন্য। এর অর্থ হলো, ঘর্ষণ বা সান্দ্রতাহীন মাধ্যমে তরঙ্গ শক্তি স্থান থেকে স্থানে পরিবাহিত হয়, কিন্তু মহাবিশ্বে তার মোট পরিমাণ এক ফোঁটাও কমে না। গতিশক্তি আর স্থিতিশক্তি অনবরত বদলাচ্ছে, ঠিক যেমন একটি পেন্ডুলামে ঘটে থাকে।"},
            {"index": 4, "type": "figure", "visual": True,
             "tts": "এই গ্রাফে নীল গতিশক্তি আর কমলা স্থিতিশক্তি পর্যায়ক্রমে ঊর্ধ্ব নিম্ন হচ্ছে, কিন্তু সবুজ মোট শক্তি রেখা একেবারে সমতল। যখন তার সম্পূর্ণ সোজা থাকে তখন বেগ সর্বোচ্চ হওয়ায় সমস্ত শক্তি গতিশক্তিতে জমা হয়। আর যখন সর্বোচ্চ স্থানচ্যুত হয় তখন বক্রতা সর্বোচ্চ হওয়ায় সমস্ত শক্তি স্থিতিশক্তিতে চলে যায়।"},
            {"index": 5, "type": "callout-gold", "role": "conclusion",
             "tts": "বিশেষ নোট, মহাজাগতিক বার্তা ও আলোর গতিবেগ। ১৮৬৫ সালে জেমস ক্লার্ক ম্যাক্সওয়েল তাঁর তড়িৎ ও চুম্বকত্বের সমীকরণগুলো একত্রিত করলে শূন্যস্থানে হুবহু ত্রিমাত্রিক ওয়েভ ইকুয়েশন বেরিয়ে আসে। সেখানে তরঙ্গের বেগ ছিল আলোর পরিমাপকৃত গতিবেগের সমান, অর্থাৎ আলো নিজেই এক তড়িৎচৌম্বকীয় তরঙ্গ। এই একটিমাত্র সমীকরণ কোটি কোটি আলোকবর্ষ দূর থেকে নক্ষত্রের আলো ও মহাকর্ষীয় তরঙ্গকে অবিকৃত আমাদের কাছে পৌঁছে দেয়, আর স্থান ও কালের মাঝে রচনা করে এক অদ্ভুত সেতুবন্ধন।"},
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
    print("BUILD COMPLETE - expressive teacher audio, Differential Equations Lesson 06")
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
    # the optional dubbed mp4 (this lesson has no official video) is absent and
    # YouTube embeds are network-blocked. These are NOT narration errors.
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
    print("VERIFIED: 35/35 cues, DOM<->manifest 1:1, 0 dups, 0 quiz/media-tab types, "
          "non-zero mp3s, valid JSON, 0 JS page errors, 0 'চিত্র প্রদর্শনী' labels.")
    print("=" * 70)


if __name__ == "__main__":
    main()
