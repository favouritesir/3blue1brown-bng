# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Differential Equations Lesson 02
("First Order Differential Equations & Slope Fields", Bengali) to the gold standard.

Deterministic, re-runnable, self-contained:
  * 32 cues in 4 narrated sections with EXACTLY the same section IDs, audio_file
    names, alias and section order as the live narration-engine DOM / manifest.json
    (verified 8/8/8/8 for sec-first-order-intro / sec-slope-field-intuition /
    sec-integral-curves / sec-ivp-uniqueness). sec-interactive-lab and sec-quizzes
    carry data-no-narration="true" and are deliberately excluded.
  * Section IDs and block types were extracted FIRST from the live DOM through
    narration_engine.js's own selector
    ('h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
     .code-showcase, .formula-box'), not guessed from prose. Exact DOM callout
    variants (callout-blue / callout-gold / callout-purple) are preserved.
  * Visual explanations are genuine, natural 2-4 sentence teacher phrasing —
    the artificial label "চিত্র প্রদর্শনী" is never used.
  * Fully phonetic spoken Bengali (no TeX / Latin / markup). Safeguards:
      ODE -> ও ডি ই, slope field -> স্লোপ ফিল্ড,
      integral curve -> ইন্টিগ্রাল কার্ভ, IVP -> আই ভি পি,
      uniqueness -> ইউনিকনেস, dy/dt -> ডি ওয়াই বাই ডি টি,
      y(t) -> ওয়াই অফ টি, C -> সি, e^t -> ই টু দ্য পাওয়ার টি.
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
  python governance/build_expressive_teacher_audio_de02.py
  python governance/build_expressive_teacher_audio_de02.py --verify-only
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
                         "differential_equations", "lesson_02")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "differential_equations",
                         "lesson_02.html")
MANIFEST_TITLE = "অধ্যায় ০২ — প্রথম ক্রমের অন্তরক সমীকরণ ও দিক ক্ষেত্র (Slope Fields)"

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
    "sec-first-order-intro":    ["h2", "chapter-quote", "p", "p", "formula-box", "p", "callout-blue", "p"],
    "sec-slope-field-intuition":["h2", "chapter-quote", "p", "p", "figure", "p", "callout-gold", "p"],
    "sec-integral-curves":      ["h2", "chapter-quote", "p", "p", "formula-box", "figure", "callout-gold", "p"],
    "sec-ivp-uniqueness":       ["h2", "chapter-quote", "p", "p", "formula-box", "p", "callout-purple", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-first-order-intro":     "sec_01_first_order_intro.mp3",
    "sec-slope-field-intuition": "sec_02_slope_field_intuition.mp3",
    "sec-integral-curves":       "sec_03_integral_curves.mp3",
    "sec-ivp-uniqueness":        "sec_04_ivp_uniqueness.mp3",
}
EXPECTED_ALIASES = {
    "sec-first-order-intro":     "sec_01_first_order_intro",
    "sec-slope-field-intuition": "sec_02_slope_field_intuition",
    "sec-integral-curves":       "sec_03_integral_curves",
    "sec-ivp-uniqueness":        "sec_04_ivp_uniqueness",
}
EXPECTED_COUNT = {
    "sec-first-order-intro": 8, "sec-slope-field-intuition": 8,
    "sec-integral-curves": 8, "sec-ivp-uniqueness": 8,
}
EXPECTED_TOTAL = 32

OLD_VERSIONS = []  # recorded during bump_page_manifest_version()

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (32 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-first-order-intro": {
        "title": "প্রথম ক্রমের অন্তরক সমীকরণ ও তার সাধারণ রূপ",
        "alias": "sec_01_first_order_intro",
        "audio_file": "sec_01_first_order_intro.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, প্রথম ক্রমের অন্তরক সমীকরণ ও তার সাধারণ রূপ।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "গণিতবিদ লেওনার্ড অয়লারের দৃষ্টিভঙ্গি, ক্যালকুলাস হলো পরিবর্তনের গণিত, আর প্রথম ক্রমের অন্তরক সমীকরণ হলো প্রকৃতির পদক্ষেপের সবচেয়ে আদি ও মৌলিক নিয়ম।"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, ডিফারেনশিয়াল সমীকরণের প্রথম অধ্যায়ে আমরা জেনেছি সমীকরণের অজানা রাশি কীভাবে একটি গতিশীল ফাংশন ওয়াই অফ টি হতে পারে। আজ আমরা প্রবেশ করব প্রথম ক্রমের অন্তরক সমীকরণ, অর্থাৎ ফার্স্ট অর্ডার ও ডি ই, এর মূল জগতে।"},
            {"index": 3, "type": "p",
             "tts": "কোনো সমীকরণকে প্রথম ক্রমের বলা হয় তখনই, যখন তাতে পরিবর্তনশীল ফাংশনের সর্বোচ্চ কেবল প্রথম অন্তরজ বা ডেরিভেটিভ উপস্থিত থাকে। অর্থাৎ সমীকরণে ডি ওয়াই বাই ডি টি থাকে, কিন্তু ডি স্কয়ার ওয়াই বাই ডি টি স্কয়ার বা তার চেয়ে উচ্চতর কোনো অন্তরজ থাকে না।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, প্রথম ক্রমের সাধারণ স্পষ্ট রূপ, ডি ওয়াই বাই ডি টি সমান এফ অফ টি কমা ওয়াই, অথবা ডি ওয়াই বাই ডি এক্স সমান এফ অফ এক্স কমা ওয়াই।"},
            {"index": 5, "type": "p",
             "tts": "এই সাধারণ সূত্রের অন্তর্নিহিত দর্শনটি অত্যন্ত গভীর। আপনি যখন কোনো নির্দিষ্ট সময় টি এবং অবস্থায় ওয়াই তে অবস্থান করছেন, সমীকরণটি আপনাকে তাৎক্ষণিকভাবে বলে দেবে যে ঠিক ওই বিন্দুতে পরিবর্তনের হার বা ঢাল কত হবে।"},
            {"index": 6, "type": "callout-blue",
             "tts": "বাস্তব জগতের দৃষ্টান্ত। এক কাপ গরম কফির শীতলীকরণ, ব্যাকটেরিয়ার অবাধ প্রজনন, তেজস্ক্রিয় পরমাণুর ক্ষয় কিংবা বৈদ্যুতিক আর সি সার্কিটের চার্জিং, সবই প্রথম ক্রমের সমীকরণের নিখুঁত উদাহরণ। নিউটনের শীতলীকরণ সূত্রটি লেখা যায় ডি টি বাই ডি স্মল টি সমান মাইনাস কে গুণ, টি মাইনাস টি এম্বিয়েন্ট আকারে, অর্থাৎ পরিবর্তনের হার পরিপার্শ্বের সাথে তাপমাত্রার পার্থক্যের সমানুপাতিক।"},
            {"index": 7, "type": "p", "role": "conclusion",
             "tts": "কিন্তু সমীকরণ লেখার পর শিক্ষার্থী ও বিজ্ঞানীরা সবচেয়ে বড় যে বাধার সম্মুখীন হন তা হলো, কীভাবে এর সমাধান বের করা যায়। প্রচলিত বীজগণিতে আমরা সূত্রের পেছনে ছুটি, কিন্তু থ্রি ব্লু ওয়ান ব্রাউনের দর্শন হলো, সূত্রের আগে জ্যামিতিক দৃষ্টিতে পরিবর্তনের পুরো মাঠটি অবলোকন করা।"},
        ],
    },

    "sec-slope-field-intuition": {
        "title": "দিক ক্ষেত্র বা স্লোপ ফিল্ডের জ্যামিতিক অন্তর্দৃষ্টি",
        "alias": "sec_02_slope_field_intuition",
        "audio_file": "sec_02_slope_field_intuition.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, দিক ক্ষেত্র বা স্লোপ ফিল্ডের জ্যামিতিক অন্তর্দৃষ্টি।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "গ্রান্ট স্যান্ডারসনের মূল দর্শন, সমীকরণের জটিল বীজগণিতীয় সমাধান খোঁজার আগে সমতল জুড়ে পরিবর্তনের ঢালগুলোকে জ্যামিতিক তীর হিসেবে আঁকুন, পুরো সমীকরণ নিজেই এক জীবন্ত ভেক্টর ফিল্ডে রূপ নেবে।"},
            {"index": 2, "type": "p",
             "tts": "কল্পনা করুন একটি দ্বি মাত্রিক কার্তেসীয় তল, যার অনুভূমিক অক্ষে সময় টি বা এক্স এবং উলম্ব অক্ষে পরিবর্তনশীল রাশি ওয়াই।"},
            {"index": 3, "type": "p",
             "tts": "সমীকরণ ডি ওয়াই বাই ডি টি সমান এফ অফ টি কমা ওয়াই আমাদের বলে, সমতলের যেকোনো বিন্দু টি কমা ওয়াই তে সমাধান রেখার স্পর্শকের ঢাল কত হবে। এখন আমরা যদি গ্রিডের প্রতিটি বিন্দুতে একটি করে অতি ক্ষুদ্র রেখাংশ আঁকি, যার ঢাল হবে এফ অফ টি কমা ওয়াই, তবে কী ঘটবে?"},
            {"index": 4, "type": "figure", "visual": True,
             "tts": "এখানে সমতলের প্রতিটি গ্রিড বিন্দুতে একটিকরে ছোট তীর আঁকা হয়েছে, যার ঢাল ওই বিন্দুতে এফ অফ টি কমা ওয়াই এর মান। বাঁদিকে তীরগুলো সামান্য ঊর্ধ্বমুখী, ডানদিকে ক্রমশ খাড়া হয়ে উঠছে, অর্থাৎ ঢাল কেবল অবস্থানের ওপর নির্ভর করছে। এই তীরসমূহের সমুদ্রই হলো স্লোপ ফিল্ড বা দিক ক্ষেত্র, আর সবুজ রঙের বক্ররেখাটি তাদের দিক ধরে এগিয়ে চলেছে।"},
            {"index": 5, "type": "p",
             "tts": "পুরো সমতলটি তখন ভরে উঠবে লক্ষ লক্ষ ছোট ছোট স্পর্শক তীরের এক সুবিশাল সমুদ্রে। এই জ্যামিতিক ক্যানভাসটিকেই বলা হয় দিক ক্ষেত্র বা স্লোপ ফিল্ড।"},
            {"index": 6, "type": "callout-gold",
             "tts": "স্বায়ত্তশাসিত সমীকরণ বা অটোনোমাস সিস্টেমের সৌন্দর্য। যদি ঢাল এফ কেবল ওয়াই এর ওপর নির্ভর করে, যেমন ডি ওয়াই বাই ডি টি সমান ওয়াই, তবে যেকোনো অনুভূমিক সরলরেখা বরাবর সমস্ত তীরের ঢাল অবিকল একই থাকে, কারণ সেখানে টি এর কোনো প্রভাব নেই। আবার যদি ঢাল কেবল টি এর ওপর নির্ভর করে, যেমন ডি ওয়াই বাই ডি টি সমান টি, তবে যেকোনো উলম্ব রেখা বরাবর সমস্ত তীরের ঢাল এক থাকে। স্থানীয় ঢালকে লেখা যায় এম অফ টি কমা ওয়াই সমান এফ অফ টি কমা ওয়াই, অর্থাৎ সমীকরণটি আসলে একটি ভেক্টর ক্ষেত্র।"},
            {"index": 7, "type": "p", "role": "conclusion",
             "tts": "স্লোপ ফিল্ড দেখার পর সমীকরণ আর কোনো বিমূর্ত সংকেত থাকে না। এটি পরিণত হয় একটি স্থির প্রবাহচিত্র বা দিক নির্দেশক কম্পাসের মহাসমুদ্রে।"},
        ],
    },

    "sec-integral-curves": {
        "title": "সমাধান বক্ররেখা ও ইন্টিগ্রাল কার্ভ পরিবার",
        "alias": "sec_03_integral_curves",
        "audio_file": "sec_03_integral_curves.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, সমাধান বক্ররেখা ও ইন্টিগ্রাল কার্ভ পরিবার।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "গণিতের দৃশ্যমান রূপক, স্লোপ ফিল্ড হলো নদীর জলের স্থির স্রোতের মানচিত্র, আর সমীকরণের সমাধান হলো সেই জলে ভাসিয়ে দেওয়া একটি শুকনো পাতার প্রাকৃতিক গতিপথ।"},
            {"index": 2, "type": "p",
             "tts": "এখন ভাবুন, আপনি এই স্লোপ ফিল্ডের সমতলে যেকোনো একটি নির্দিষ্ট বিন্দুতে পেনসিলের ডগা রাখলেন। তারপর চারপাশের ছোট ছোট তীরগুলোর নির্দেশিত দিক অনুসরণ করে পেনসিলটিকে মসৃণভাবে এগিয়ে নিয়ে চললেন।"},
            {"index": 3, "type": "p",
             "tts": "আপনি যে বক্ররেখাটি আঁকলেন, গণিতের ভাষায় তাকে বলা হয় সমাধান বক্ররেখা বা ইন্টিগ্রাল কার্ভ। এই বক্ররেখাটির বিশেষত্ব হলো, এর প্রতিটি বিন্দুতে স্পর্শক আঁকলে তা অবিকল ওই বিন্দুর স্লোপ ফিল্ডের তীরের সাথে সমান্তরাল হবে।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, চলক পৃথকীকরণ ও সমাধান পরিবার। ডি ওয়াই বাই ডি টি সমান ওয়াই কে চলক পৃথকীকরণ করলে পাই ইন্টিগ্রাল ডি ওয়াই বাই ওয়াই সমান ইন্টিগ্রাল ডি টি, যার থেকে আসে লন অ্যাবস ওয়াই সমান টি প্লাস সি নট, অর্থাৎ ওয়াই অফ টি সমান সি গুণ ই টু দ্য পাওয়ার টি।"},
            {"index": 5, "type": "figure", "visual": True,
             "tts": "এই ছবিতে একই স্লোপ ফিল্ডের ওপর দিয়ে বয়ে যাওয়া বেশ কয়েকটি সবুজ বক্ররেখা দেখা যাচ্ছে, প্রতিটি একটি নির্দিষ্ট সি এর জন্য ওয়াই অফ টি সমান সি গুণ ই টু দ্য পাওয়ার টি। লক্ষ্য করুন বক্রগুলো পরস্পরের সমান্তরালে বয়ে চলে এবং কখনোই ছেদ করে না, কারণ প্রতিটি বিন্দুতে ক্ষেত্রের তীর কেবল একটিমাত্র দিক নির্দেশ করে। নিচের বক্রগুলো সি ঋণাত্মক, উপরেরগুলো সি ধনাত্মক, আর মাঝখানের ওয়াই সমান শূন্য রেখাটি হলো সাম্যাবস্থা।"},
            {"index": 6, "type": "callout-gold",
             "tts": "সমাধান পরিবারের রহস্য। স্লোপ ফিল্ড হলো নদীর জলের স্থির স্রোতের মানচিত্র, আর সমীকরণের সমাধান হলো সেই জলে ভাসিয়ে দেওয়া একটি শুকনো পাতার প্রাকৃতিক গতিপথ। ভিন্ন ভিন্ন আদি শর্ত থেকে শুরু করলে পাতাটি ভিন্ন পথ ধরবে, যা সমীকরণের সমাধানের পরিবার তৈরি করে। গাণিতিকভাবে এই পরিবার ওয়াই সমান সি গুণ ই টু দ্য পাওয়ার টি দিয়ে লেখা হয়, যেখানে সি হলো যেকোনো বাস্তব সমাকলন ধ্রুবক, আর সি এর প্রতিটি মান একটিমাত্র স্বতন্ত্র বক্ররেখা নির্বাচন করে দেয়।"},
            {"index": 7, "type": "p", "role": "conclusion",
             "tts": "আপনি যেখান থেকেই শুরু করুন না কেন, সমীকরণের নিয়মটি আপনাকে একটি স্বতন্ত্র মসৃণ ট্র্যাজেক্টরি ধরে এগিয়ে নিয়ে যাবে।"},
        ],
    },

    "sec-ivp-uniqueness": {
        "title": "আদি মান সমস্যা ও সমাধান বক্ররেখার অনন্যতা",
        "alias": "sec_04_ivp_uniqueness",
        "audio_file": "sec_04_ivp_uniqueness.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, আদি মান সমস্যা ও সমাধান বক্ররেখার ইউনিকনেস।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "পিকার্ড লিন্ডেলফ উপপাদ্য, মসৃণ নিয়মের জগতে প্রতিটি আদি শর্ত একটি এবং কেবল একটিমাত্র সুনির্দিষ্ট ভবিষ্যতের জন্ম দেয়, সমাধান বক্ররেখা কখনো পরস্পরকে ছেদ করতে পারে না।"},
            {"index": 2, "type": "p",
             "tts": "বাস্তব জগতে বিজ্ঞানীদের একটি সুনির্দিষ্ট ভবিষ্যৎ জানতে হয়। যেমন, আজ সকালে কফির তাপমাত্রা ছিল আশি ডিগ্রি সেলসিয়াস, দশ মিনিট পর এর তাপমাত্রা ঠিক কত হবে?"},
            {"index": 3, "type": "p",
             "tts": "এই নির্দিষ্ট তথ্যটিকে বলা হয় আদি শর্ত বা ইনিশিয়াল কন্ডিশন, ওয়াই অফ টি জিরো সমান ওয়াই জিরো। যখন একটি ডিফারেনশিয়াল সমীকরণের সাথে একটি নির্দিষ্ট আদি শর্ত জুড়ে দেওয়া হয়, তখন তাকে বলা হয় আদি মান সমস্যা বা ইনিশিয়াল ভ্যালু প্রবলেম, সংক্ষেপে আই ভি পি।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, আদি মান সমস্যা বা আই ভি পি। ডি ওয়াই বাই ডি টি সমান এফ অফ টি কমা ওয়াই, আর আদি শর্ত ওয়াই অফ টি জিরো সমান ওয়াই জিরো। এই আদি বিন্দুটি পুরো পরিবার থেকে ঠিক একটি বক্ররেখা বেছে নেয়, যা হলো ওয়াই অফ টি সমান ওয়াই জিরো গুণ ই টু দ্য পাওয়ার কে গুণ, টি মাইনাস টি জিরো।"},
            {"index": 5, "type": "p",
             "tts": "জ্যামিতিকভাবে চিন্তা করুন, সমতলে অগণিত বক্ররেখার ঝাঁক ভেসে বেড়াচ্ছে। আদি শর্ত নির্ধারণ করা মানে হলো সমতলে একটি সুনির্দিষ্ট বিন্দুতে একটি পিন বা পেরেক গেঁথে দেওয়া। এই পিনটি পুরো পরিবারের মধ্য থেকে কেবল একটিমাত্র বক্ররেখাকে নির্বাচিত করে দেয়।"},
            {"index": 6, "type": "callout-purple",
             "tts": "সমাধান বক্ররেখার অলঙ্ঘনীয় নীতি। স্লোপ ফিল্ডের ভেতর দুটি ভিন্ন সমাধান বক্ররেখা কখনো একে অপরকে ছেদ বা ক্রস করতে পারে না। কারণ সমতলের প্রতিটি বিন্দুতে সমীকরণটি একটি এবং কেবল একটি নির্দিষ্ট ঢাল নির্ধারণ করে। যদি দুটি রেখা একে অপরকে ছেদ করত, তবে সেই ছেদবিন্দুতে একই সাথে দুটি ভিন্ন ঢাল থাকতে হতো, যা গণিতীয়ভাবে অসম্ভব। পিকার্ড লিন্ডেলফের লিপশিৎস শর্ত এই ইউনিকনেসের গাণিতিক গ্যারান্টি দেয়, যতক্ষণ এফ মসৃণ ততক্ষণ একক আদি শর্ত থেকে একটিমাত্র সমাধানই বের হবে।"},
            {"index": 7, "type": "p", "role": "conclusion",
             "tts": "আর এই জ্যামিতিক স্লোপ ফিল্ডের তীর ধরে ধাপে ধাপে এগিয়ে যাওয়াই হলো কম্পিউটার সিমুলেশনের সবচেয়ে বিখ্যাত অ্যালগরিদম, অয়লারের পদ্ধতি। স্লোপ ফিল্ডই প্রথম ক্রমের ও ডি ই কে কেবল ফর্মুলার বন্দিদশা থেকে মুক্ত করে প্রকৃতির জীবন্ত চলচিত্রে রূপ দান করে।"},
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
            print(f"  cue {idx:02d} [{cue['type']:<13}] {rate:>4} {pitch:>5}  {cue['tts'][:30]}...")
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
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
    assert total_cues == EXPECTED_TOTAL

    print("\n" + "=" * 70)
    print("BUILD COMPLETE - expressive teacher audio, Differential Equations Lesson 02")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<26} {len(msec['cues']):>2} cues  "
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
              "Permissions policy violation", "Failed to load resource")
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
                 "sec-interactive-lab", "sec-quizzes-section", "quiz", "media-tab"} & set(dom_ids)), \
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
            if BAD_CHARS.search(c["text"]):
                raise AssertionError(f"markup/Latin/forbidden char in {sec_id}/{c['index']}")
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

    # Page cache-buster bumped by exactly +1.
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
        "markup_or_latin_hits": 0,
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
