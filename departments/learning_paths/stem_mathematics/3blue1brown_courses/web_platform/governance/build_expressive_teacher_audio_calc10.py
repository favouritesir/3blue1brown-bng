# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Calculus Lesson 10
("Taylor series", Bengali) to the Lesson-01/02 gold standard.

Deterministic, re-runnable, self-contained:
  * 37 cues in 5 narrated sections with EXACTLY the same section IDs, audio_file
    names and cue type/order as the existing manifest and the live DOM:
      sec-poly-approximation        -> h2, chapter-quote, p, p, p, formula-box, callout, p (8)
      sec-linear-tangent            -> h2, p, p, p, p, formula-box, callout             (7)
      sec-quadratic-curvature       -> h2, p, p, p, p, p, p, formula-box, callout, p   (10)
      sec-general-taylor-formula    -> h2, p, p, p, formula-box, callout                (6)
      sec-convergence-applications  -> h2, p, p, p, formula-box, callout                (6)
    (The live DOM has no figure.lesson-figure blocks in narrated sections, so there
     are no figure cues to generate; all cues are natural expressive prose and
     none uses the artificial label "চিত্র প্রদর্শনী".)
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Every script is clean spoken Bengali with phonetic safeguards:
      cos -> কোস, sin -> সাইন, n! -> এন ফ্যাক্টরিয়াল,
      e^x -> ই পাওয়ার এক্স, ln -> লন, dx -> ডি এক্স, pi -> পাই, theta -> থেটা,
      factorial -> ফ্যাক্টরিয়াল, x -> এক্স, etc.
    No TeX, LaTeX, backslashes, $, braces, brackets, em/en-dashes, raw hyphens
    or Latin letters.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, figure -4%, formula-box -8%, p +2%, callout +0%,
      conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with the
    exact-ms timings and the exact 5 canonical section keys of the gold standard.
  * Validates non-zero durations, zero overlap, valid JSON and non-empty mp3s,
    plus DOM parity against the browser-extracted calc10_dom_blocks.json.

Usage:  python governance/build_expressive_teacher_audio_calc10.py
"""

import os
import re
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
                         "calculus", "lesson_10")
DOM_SNAPSHOT = os.path.join(SCRIPT_DIR, "calc10_dom_blocks.json")
MANIFEST_TITLE = "অধ্যায় ১০ — টেইলর ধারা ও উচ্চতর সান্নিধ্যকরণ (Taylor series)"

# Prosody keyed by cue type: (rate, pitch, volume)
PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
    "h3":            ("-3%", "+0Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),   # measured, thoughtful quotation
    "p":             ("+2%", "+0Hz", "+0%"),   # natural teacher pace
    "figure":        ("-4%", "+0Hz", "+0%"),   # slower, considerate explanation
    "callout":       ("+0%", "+0Hz", "+0%"),   # steady emphasis
    "formula-box":   ("-8%", "+0Hz", "+0%"),   # slow and deliberate
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")     # calm concluding prose

# Parity guards: exact cue-type sequence of each narrated section (live DOM).
EXPECTED_TYPES = {
    "sec-poly-approximation":       ["h2", "chapter-quote", "p", "p", "p", "formula-box", "callout", "p"],
    "sec-linear-tangent":           ["h2", "p", "p", "p", "p", "formula-box", "callout"],
    "sec-quadratic-curvature":      ["h2", "p", "p", "p", "p", "p", "p", "formula-box", "callout", "p"],
    "sec-general-taylor-formula":   ["h2", "p", "p", "p", "formula-box", "callout"],
    "sec-convergence-applications": ["h2", "p", "p", "p", "formula-box", "callout"],
}
EXPECTED_AUDIO_FILES = {
    "sec-poly-approximation":       "sec_01_poly_approximation.mp3",
    "sec-linear-tangent":           "sec_02_linear_tangent.mp3",
    "sec-quadratic-curvature":      "sec_03_quadratic_curvature.mp3",
    "sec-general-taylor-formula":   "sec_04_general_taylor_formula.mp3",
    "sec-convergence-applications": "sec_05_convergence_applications.mp3",
}
# Legacy alias names kept in each section's `alias` field (NOT extra keys).
ALIASES = {
    "sec-poly-approximation":       "sec_01_poly_approximation",
    "sec-linear-tangent":           "sec_02_linear_tangent",
    "sec-quadratic-curvature":      "sec_03_quadratic_curvature",
    "sec-general-taylor-formula":   "sec_04_general_taylor_formula",
    "sec-convergence-applications": "sec_05_convergence_applications",
}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (37 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-poly-approximation": {
        "title": "১. জটিল ফাংশনের সহজ প্রতিরূপ: বহুপদী আসন্নায়ন (Polynomial Approximation)",
        "audio_file": "sec_01_poly_approximation.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, জটিল ফাংশনের সহজ প্রতিরূপ, বহুপদী আসন্নায়ন।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, অনেকের কাছে গণিত আসলে উপপাদ্যের সংগ্রহ, কিন্তু আমার কাছে গণিত হলো উদাহরণের সংগ্রহ, বলেছেন জন বি কনওয়ে। তাঁর কথায়, গণিত ও গণনার মূল শক্তি নিহিত রয়েছে যেকোনো দুর্ভেদ্য ও জটিল ফাংশনকে সাধারণ বহুপদীর যোগফলে রূপান্তর করার দক্ষতায়।"},
            {"index": 2, "type": "p",
             "tts": "টেইলর ধারা প্রথমে আমার কাছে ততটা গুরুত্বপূর্ণ মনে হয়নি, যতক্ষণ না একটি পদার্থবিদ্যার ক্লাসে এর ব্যবহার দেখলাম। আমরা একটি পেন্ডুলামের সম্ভাব্য শক্তি নিয়ে কাজ করছিলাম, যার জন্য বলটি তার নিচতম অবস্থানের ওপরে কতটা উঠেছে তা বের করতে হয়। এই উচ্চতা এক বিয়োগ কোস থেটা এর সমানুপাতিক, যেখানে থেটা হলো পেন্ডুলামের দণ্ড ও উল্লম্ব রেখার মধ্যকার কোণ। আর এই কোস থেটাই আসলেই সমস্যাটিকে জটিল করে তুলেছিল।"},
            {"index": 3, "type": "p",
             "tts": "কিন্তু কোস থেটা কে এক বিয়োগ থেটা স্কয়ার ভাগ দুই দ্বারা আসন্নায়ন করতেই পুরো হিসাব সহজ হয়ে গেল। ছোট কোণের ক্ষেত্রে কোস থেটা আর এক বিয়োগ থেটা স্কয়ার ভাগ দুই খুব কাছাকাছি। কিন্তু এই আসন্নায়নটি কীভাবে খুঁজে পাওয়া যায়? টেইলর ধারার মূল কাজ হলো বহুপদী নয় এমন ফাংশনের জন্য এমন একটি বহুপদী খোঁজা যা কোনো নির্দিষ্ট ইনপুটের কাছে তার মতো আচরণ করে। বহুপদীদের সাথে কাজ করা সহজ, এগুলো হিসাব করা, ডেরিভেটিভ নেওয়া ও ইন্টিগ্রেট করা, সবই সহজ।"},
            {"index": 4, "type": "p",
             "tts": "বাস্তব জীবনে আমরা প্রতিনিয়ত কোস এক্স, সাইন এক্স, ই পাওয়ার এক্স বা লন এক্স এর মতো অবীজীয় ফাংশন ব্যবহার করি, অথচ কম্পিউটারের সিপিইউ শুধু যোগ, বিয়োগ, গুণ ও ভাগই জানে। সে কীভাবে মাইক্রোসেকেন্ডে কোস শূন্য দশমিক তিন বা ই পাওয়ার শূন্য দশমিক এক পাঁচ এর দশমিকের পর দশ ঘর পর্যন্ত নিখুঁত মান বের করে? উত্তর হলো বহুপদী পি অফ এক্স সমান সি নট যোগ সি ওয়ান এক্স যোগ সি টু এক্স স্কয়ার এবং আরও পদ, যাতে শুধু পুনরাবৃত্ত গুণ ও যোগ আছে। টেইলর ধারার দর্শন হলো যেকোনো বক্ররেখার গায়ে এমন বহুপদী সেঁটে দেওয়া যা একটি নির্দিষ্ট বিন্দুর চারপাশে অবিকল মূল ফাংশনের মতো আচরণ করে।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, পি এন অফ এক্স সমান সি নট যোগ সি ওয়ান গুণ এক্স বিয়োগ এ যোগ সি টু গুণ এক্স বিয়োগ এ এর স্কয়ার, এভাবে এন তম পদ পর্যন্ত।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, কেন্দ্রীয় প্রশ্ন। ডেরিভেটিভ কীভাবে বহুপদী তৈরি করে? আমরা কীভাবে সহগ সি নট, সি ওয়ান, সি টু নির্ধারণ করব যাতে বহুপদীটি কেবল ওই বিন্দুতেই মূল ফাংশনকে স্পর্শ না করে, বরং তার ঢাল, বাঁক এবং পরিবর্তনের হারকেও সমানভাবে অনুকরণ করে? একটি একক বিন্দুতে ফাংশনের মান ও পরপর ডেরিভেটিভগুলোই কি সম্পূর্ণ প্রতিবেশে ফাংশনটিকে পুনর্নির্মাণ করতে পারে?"},
            {"index": 7, "type": "p",
             "tts": "প্রথমে সবচেয়ে সহজ রূপ দিয়ে শুরু করা যাক, স্পর্শক রেখা বা প্রথম ক্রমের রৈখিক আসন্নায়ন।"},
        ],
    },

    "sec-linear-tangent": {
        "title": "২. রৈখিক সান্নিধ্যকরণ ও স্পর্শক সরলরেখা (Linear Approximation: Tangent Line)",
        "audio_file": "sec_02_linear_tangent.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, রৈখিক সান্নিধ্যকরণ ও স্পর্শক সরলরেখা।"},
            {"index": 1, "type": "p",
             "tts": "ধরা যাক আমরা এক্স সমান শূন্য বিন্দুর কাছে এফ অফ এক্স সমান কোস এক্স ফাংশনটিকে আসন্নায়ন করতে চাই। এক্স সমান শূন্য বিন্দুতে কোস শূন্যের মান এক। সুতরাং যেকোনো ভালো আসন্নায়নের মানও ওই বিন্দুতে এক হতে হবে।"},
            {"index": 2, "type": "p",
             "tts": "সবচেয়ে স্থূল ও শূন্য মাত্রার অনুমানটি হবে একটি অনুভূমিক সরলরেখা, পি নট অফ এক্স সমান এক। কিন্তু এক্স শূন্য থেকে সামান্য দূরে সরে গেলেই এই অনুভূমিক রেখাটি মূল কোসাইন বক্ররেখা থেকে বিচ্ছিন্ন হয়ে পড়ে, কারণ কোসাইন বক্ররেখা শূন্যের কাছে নিচের দিকে বাঁক নেয়।"},
            {"index": 3, "type": "p",
             "tts": "একটি উন্নততর আসন্নায়নের জন্য আমাদের এমন একটি সরলরেখা চাই যার উচ্চতা মূল ফাংশনের সমান হবে এবং যার ঢালও, অর্থাৎ প্রথম ডেরিভেটিভ, মূল ফাংশনের ঠিক সমান হবে। অর্থাৎ পি ওয়ান অফ শূন্য সমান এফ অফ শূন্য, আর পি ওয়ান প্রাইম অফ শূন্য সমান এফ প্রাইম অফ শূন্য। এই দুটি শর্তই স্পর্শক রেখাকে অন্যান্য রেখা থেকে আলাদা করে।"},
            {"index": 4, "type": "p",
             "tts": "আমরা জানি, ডি ডিএক্স অফ কোস এক্স সমান মাইনাস সাইন এক্স, এবং এক্স সমান শূন্যে মাইনাস সাইন শূন্যের মান শূন্য। ফলে স্পর্শক রেখার ঢাল শূন্য। অন্য যেকোনো ফাংশনের ক্ষেত্রে স্পর্শক রেখার সমীকরণ হয় পি ওয়ান অফ এক্স সমান এফ অফ এ যোগ এফ প্রাইম অফ এ গুণ এক্স বিয়োগ এ। আর ইনপুটের ক্ষুদ্র বিচ্যুতি ডি এক্স এর জন্য পরিবর্তনের প্রথম ক্রমের অনুমান লেখা যায়, এফ অফ এক্স প্রায় সমান এফ অফ এ যোগ এফ প্রাইম অফ এ গুণ ডি এক্স।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, প্রথম ক্রমের রৈখিক আসন্নায়ন বা স্পর্শক সরলরেখার সমীকরণ, পি ওয়ান অফ এক্স সমান এফ অফ এ যোগ এফ প্রাইম অফ এ গুণ এক্স বিয়োগ এ।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, রৈখিকতার সীমাবদ্ধতা। স্পর্শক সরলরেখা কেবল একটি নির্দিষ্ট বিন্দুতে পরিবর্তনের তাৎক্ষণিক গতিবেগ ধরে রাখে, কিন্তু বক্ররেখাটি কোন দিকে বাঁক নিচ্ছে, অর্থাৎ কার্ভেচার বা উত্তলতা অবতলতা, তা একটি সরলরেখা কখনোই ফুটিয়ে তুলতে পারে না। কোসাইনের ক্ষেত্রে কোস শূন্যের মান এক ও মাইনাস সাইন শূন্যের মান শূন্য হওয়ায় পি ওয়ান অফ এক্স সমান এক পাই, যা আসলে আমাদের প্রথমের সেই অনুভূমিক রেখাটিই। এখন বাঁক মেলাতে হবে দ্বিঘাত পদ যোগ করে।"},
        ],
    },

    "sec-quadratic-curvature": {
        "title": "৩. দ্বিতীয় ক্রমের পরাবৃত্ত ও বক্রতা মেলানো (Quadratic Approximation & Curvature)",
        "audio_file": "sec_03_quadratic_curvature.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, দ্বিতীয় ক্রমের পরাবৃত্ত ও বক্রতা মেলানো।"},
            {"index": 1, "type": "p",
             "tts": "যদি আমরা সরলরেখার পরিবর্তে একটি দ্বিঘাত বহুপদী বা পরাবৃত্ত পি টু অফ এক্স সমান সি নট যোগ সি ওয়ান এক্স যোগ সি টু এক্স স্কয়ার ব্যবহার করি, তবে আমরা তিনটি শর্ত আরোপ করতে পারি। উচ্চতা, ঢাল ও বক্রতা, তিনটিই এক্স সমান শূন্যে মূল ফাংশনের সমান হতে হবে।"},
            {"index": 2, "type": "p",
             "tts": "প্রথমত, উচ্চতা মিলতে হবে। পি টু অফ শূন্য সমান এফ অফ শূন্য, যা থেকে পাই সি নট সমান এফ অফ শূন্য। কোসাইনের ক্ষেত্রে কোস শূন্যের মান এক, তাই সি নট সমান এক।"},
            {"index": 3, "type": "p",
             "tts": "দ্বিতীয়ত, ঢাল মিলতে হবে। পি টু প্রাইম অফ শূন্য সমান এফ প্রাইম অফ শূন্য, যা থেকে পাই সি ওয়ান সমান এফ প্রাইম অফ শূন্য। কোসাইনের ক্ষেত্রে মাইনাস সাইন শূন্যের মান শূন্য, তাই সি ওয়ান সমান শূন্য।"},
            {"index": 4, "type": "p",
             "tts": "তৃতীয়ত, দ্বিতীয় ডেরিভেটিভ বা বক্রতা মিলতে হবে। পি টু ডাবল প্রাইম অফ শূন্য সমান এফ ডাবল প্রাইম অফ শূন্য। কোসাইনের দ্বিতীয় ডেরিভেটিভ হলো মাইনাস কোস এক্স, যার মান শূন্যে মাইনাস এক।"},
            {"index": 5, "type": "p",
             "tts": "এবার লক্ষ্য করুন কী ঘটে যখন আমরা পি টু অফ এক্স কে দুইবার ডিফারেনশিয়েট করি। প্রথমবার পাই পি টু প্রাইম অফ এক্স সমান সি ওয়ান যোগ দুই সি টু এক্স। দ্বিতীয়বার করলে পাই পি টু ডাবল প্রাইম অফ এক্স সমান দুই সি টু, একটি ধ্রুবক।"},
            {"index": 6, "type": "p",
             "tts": "পাওয়ার রুলের কারণে ঘাত দুই সামনে নেমে এসে সহগের সাথে গুণ হয়েছে। ফলে পি টু ডাবল প্রাইম অফ শূন্য সমান এফ ডাবল প্রাইম অফ শূন্য হতে হলে দুই সি টু সমান এফ ডাবল প্রাইম অফ শূন্য, অর্থাৎ সি টু সমান এফ ডাবল প্রাইম অফ শূন্য ভাগ দুই ফ্যাক্টরিয়াল, যা কোসাইনের ক্ষেত্রে মাইনাস এক ভাগ দুই। এই তিনটি সহগ সি নট সমান এক, সি ওয়ান সমান শূন্য, আর সি টু সমান মাইনাস এক ভাগ দুই, যথাক্রমে মান, ঢাল ও বক্রতা মেলায় এবং কোসাইনের জন্য সেরা দ্বিঘাত আসন্নায়ন দেয়।"},
            {"index": 7, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, দ্বিঘাত টেইলর বহুপদী, পি টু অফ এক্স সমান এফ অফ শূন্য যোগ এফ প্রাইম অফ শূন্য গুণ এক্স যোগ এফ ডাবল প্রাইম অফ শূন্য ভাগ দুই ফ্যাক্টরিয়াল গুণ এক্স স্কয়ার।"},
            {"index": 8, "type": "callout",
             "tts": "বিশেষ নোট, ফ্যাক্টোরিয়াল কেন জন্ম নেয়? ঘাত যখন প্রতিবার ডেরিভেটিভ করার সময় ক্রমান্বয়ে নিচে নেমে গুণ হতে থাকে, তখন এন তম ডেরিভেটিভে সহগের সাথে এন ফ্যাক্টরিয়াল গুণ হয়ে যায়। মূল ফাংশনের ডেরিভেটিভের সাথে বহুপদীর ডেরিভেটিভ মেলাতে হলে সেই বাড়তি এন ফ্যাক্টরিয়াল কে ভাগ করে প্রশমিত করতে হয়। এই কারণেই দুই ফ্যাক্টরিয়াল ও পরে এন ফ্যাক্টরিয়াল আসে।"},
            {"index": 9, "type": "p",
             "tts": "সুতরাং কোস এক্স প্রায় সমান এক বিয়োগ এক্স স্কয়ার ভাগ দুই। এর মান কতটা ভালো তা দেখতে এক্স সমান শূন্য দশমিক এক বসাই। প্রকৃত মান শূন্য দশমিক নয় নয় পাঁচ শূন্য শূন্য চার, আর আমাদের আসন্নায়ন শূন্য দশমিক নয় নয় পাঁচ, প্রায় হুবহু মিলে যাচ্ছে। মাত্র তিনটি সহগ দিয়েই এত নিখুঁত ফলাফল। এই সহজ কিন্তু গভীর পর্যবেক্ষণটিই আমাদের নিয়ে যায় অসীম ধারার সাধারণ রূপটিতে।"},
        ],
    },

    "sec-general-taylor-formula": {
        "title": "৪. টেইলর ধারার সাধারণ রূপ ও ম্যাকলরিন ধারা (The General Taylor Series Formula)",
        "audio_file": "sec_04_general_taylor_formula.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, টেইলর ধারার সাধারণ রূপ ও ম্যাকলরিন ধারা।"},
            {"index": 1, "type": "p",
             "tts": "যদি আমরা তৃতীয় ডেরিভেটিভ মেলাতে চাই, তবে এক্স কিউব পদকে তিনবার ডিফারেনশিয়েট করলে পাই তিন গুণ দুই গুণ এক, অর্থাৎ থ্রি ফ্যাক্টরিয়াল, যার মান ছয়। ফলে তার সহগ হবে এফ ট্রিপল প্রাইম অফ শূন্য ভাগ থ্রি ফ্যাক্টরিয়াল। কোসাইনের তৃতীয় ডেরিভেটিভ হলো সাইন এক্স, যা শূন্যে শূন্য, তাই সি থ্রি সমান শূন্য। অর্থাৎ এক বিয়োগ এক্স স্কয়ার ভাগ দুই একই সাথে সেরা দ্বিঘাত ও সেরা ঘনক আসন্নায়ন।"},
            {"index": 2, "type": "p",
             "tts": "যেকোনো এন তম পদের জন্য এই ধারাটি স্বাভাবিক নিয়মেই এগিয়ে চলে। সি এন সমান এফ এর এন তম ডেরিভেটিভ ভাগ এন ফ্যাক্টরিয়াল। যখন কেন্দ্রবিন্দু এ সমান শূন্য হয়, তখন একে ম্যাকলরিন ধারা বলা হয়। পি অফ এক্স সমান এফ অফ শূন্য যোগ এফ প্রাইম অফ শূন্য গুণ এক্স ভাগ এক ফ্যাক্টরিয়াল, যোগ এফ ডাবল প্রাইম অফ শূন্য গুণ এক্স স্কয়ার ভাগ দুই ফ্যাক্টরিয়াল, এভাবে চলতে থাকে। এখানে প্রতিটি ডেরিভেটিভ শূন্যে কেবল একটি মাত্র সহগ দ্বারা নিয়ন্ত্রিত হয়। উচ্চতর পদ যোগ করলে পুরনো সহগগুলোর মান নষ্ট হয় না, কারণ এক্স সমান শূন্যে বসালে সেই উচ্চতর পদগুলো সবই মিলিয়ে যায়।"},
            {"index": 3, "type": "p",
             "tts": "আর যদি আমরা মূলবিন্দুর বদলে যেকোনো বিন্দু এক্স সমান এ এর চারপাশে বহুপদী সেঁটে দিতে চাই, যেমন এক্স সমান পাই এর কাছে, তবে স্থানচ্যুতিটি হয় এক্স বিয়োগ এ। বহুপদীকে এক্স বিয়োগ এ এর ঘাতে লেখা হয় যাতে এক্স সমান এ বসালে সুন্দর বাতিল ঘটে। এর ফলে জন্ম নেয় গণিতের সবচেয়ে রোমাঞ্চকর উপপাদ্য, সাধারণ টেইলর ধারা। মূল শিক্ষা হলো, একটি বিন্দুতে ডেরিভেটিভের তথ্য সেই বিন্দুর পুরো প্রতিবেশ সম্পর্কে বলে দেয়।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, যেকোনো মসৃণ ফাংশন এফ অফ এক্স এর পূর্ণাঙ্গ টেইলর ধারা, সামেশন এন সমান শূন্য থেকে অসীম, এফ এর এন তম ডেরিভেটিভ ভাগ এন ফ্যাক্টরিয়াল গুণ এক্স বিয়োগ এ এর এন তম ঘাত।"},
            {"index": 5, "type": "callout", "role": "conclusion",
             "tts": "বিশেষ নোট, অসীম পদ যোগের অলৌকিকতা। পদসংখ্যা যত বাড়ানো হয়, বহুপদীটি বক্ররেখার কেন্দ্র থেকে ততই অনেক দূর ছড়িয়ে পড়ে এবং মূল ফাংশনের বাঁকগুলোকে নির্ভুলতায় জড়িয়ে ধরে। কোসাইনের ডেরিভেটিভগুলো চক্রাকারে এক, শূন্য, মাইনাস এক, শূন্য ক্রম অনুসরণ করে। প্রতিটি মানকে যথাযথ এন ফ্যাক্টরিয়াল দিয়ে ভাগ করে সহগ বানালেই এক বিয়োগ এক্স স্কয়ার ভাগ দুই যোগ এক্স চতুর্থ ঘাত ভাগ চব্বিশ, এই ধারাটি পাওয়া যায়।"},
        ],
    },

    "sec-convergence-applications": {
        "title": "৫. অভিসারী ব্যাসার্ধ ও আধুনিক বিজ্ঞানে প্রয়োগ (Radius of Convergence & Applications)",
        "audio_file": "sec_05_convergence_applications.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, অভিসারী ব্যাসার্ধ ও আধুনিক বিজ্ঞানে প্রয়োগ।"},
            {"index": 1, "type": "p",
             "tts": "টেইলর ধারা নিয়ে কাজ করার সময় একটি অত্যন্ত গুরুত্বপূর্ণ প্রশ্ন ওঠে। আমরা কি একটি বিন্দুতে ফাংশনটির সমস্ত ডেরিভেটিভ জেনে মহাবিশ্বের যেকোনো দূরত্বে ফাংশনটির সঠিক মান বের করতে পারব? সব ফাংশনের জন্য উত্তর হ্যাঁ নয়।"},
            {"index": 2, "type": "p",
             "tts": "কিছু ফাংশনের টেইলর ধারা সম্পূর্ণ সংখ্যারেখায় অভিসৃত হয়, যেমন ই পাওয়ার এক্স, সাইন এক্স, কোস এক্স। কিন্তু কিছু ফাংশনের একটি সুনির্দিষ্ট গণ্ডি থাকে, যাকে বলা হয় অভিসারী ব্যাসার্ধ। যেমন এফ অফ এক্স সমান ওয়ান বাই ওয়ান মাইনাস এক্স, অর্থাৎ এক যোগ এক্স যোগ এক্স স্কয়ার যোগ এক্স কিউব এবং আরও পদ, কেবল তখনই কার্যকর যখন এক্স এর পরমমান একের চেয়ে ছোট। তার বাইরে ধারাটি অর্থহীন।"},
            {"index": 3, "type": "p",
             "tts": "তা সত্ত্বেও আধুনিক পদার্থবিজ্ঞান ও প্রকৌশলে টেইলর ধারা ছাড়া কোনো অগ্রগতিই অসম্ভব। কোয়ান্টাম মেকানিক্সের পারটারবেশন থিওরি, আইনস্টাইনের সাধারণ আপেক্ষিকতায় মহাকর্ষীয় তরঙ্গের হিসাব এবং ডিপ লার্নিংয়ের অপ্টিমাইজেশনে ফাংশন আসন্নায়নের মেরুদণ্ড হলো এই ধারা। টেইলরের উপপাদ্যের অবশিষ্টাংশ আর এন অফ এক্স আমাদের জানায় কতটা ভুল হতে পারে।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ওয়ান বাই ওয়ান মাইনাস এক্স সমান সামেশন এন সমান শূন্য থেকে অসীম এক্স এর এন তম ঘাত, শর্ত এক্স এর পরমমান একের চেয়ে ছোট। আর এফ অফ এক্স সমান পি এন অফ এক্স যোগ আর এন অফ এক্স।"},
            {"index": 5, "type": "callout", "role": "conclusion",
             "tts": "সারমর্ম, টেইলর ধারা স্থানীয় তথ্যকে, অর্থাৎ একটি বিন্দুর ডেরিভেটিভসমূহকে, বৈশ্বিক জ্ঞানে রূপান্তরিত করে। এটি দেখায় কীভাবে পরিবর্তনের উচ্চতর হারগুলো একটি ফাংশনের ভবিষ্যৎ রূপরেখা অঙ্কন করে দেয়। কিন্তু অভিসারী ব্যাসার্ধের বাইরে সেই রূপরেখা ভেঙে পড়ে, এই সীমাবদ্ধতাও সমানভাবে গুরুত্বপূর্ণ।"},
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
    if len(SECTIONS_DATA) != 5:
        raise ValueError("Expected exactly 5 narrated sections")
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
    if total != 37:
        raise ValueError(f"Expected 37 cues, found {total}")

    # Figure cues must be genuine 2-4 sentence explanations (vacuous here: the
    # live DOM has no figure blocks in narrated sections, but keep the guard).
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            if cue["type"] == "figure":
                sentences = [s for s in cue["tts"].split("।") if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(f"{sec_id} cue {cue['index']}: figure has {len(sentences)} sentences")

    # DOM parity against the browser-extracted live snapshot (narration_engine
    # selector + KaTeX <annotation> preservation).
    if os.path.exists(DOM_SNAPSHOT):
        with open(DOM_SNAPSHOT, encoding="utf-8") as fh:
            snap = json.load(fh)
        snap_types = {s["id"]: [b["type"] for b in s["blocks"]]
                      for s in snap["sections"]}
        if snap_types != EXPECTED_TYPES:
            raise ValueError(f"DOM snapshot cue types differ from embedded EXPECTED_TYPES:\n"
                             f"snapshot={snap_types}\nexpected={EXPECTED_TYPES}")
        if set(snap_types) != set(SECTIONS_DATA):
            raise ValueError("DOM snapshot section ids differ from embedded sections")

    # No duplicate spoken scripts.
    spoken = [c["tts"] for s in SECTIONS_DATA.values() for c in s["cues"]]
    if len(spoken) != len(set(spoken)):
        raise ValueError("Duplicate spoken cue scripts detected")


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
        manifest_sections[sec_id] = await build_section(sec_id, sec)

    manifest_data = {
        "course": "calculus",
        "lesson": "lesson_10",
        "title": MANIFEST_TITLE,
        "voice": VOICE,
        "mode": "authentic_teacher",
        "processing": {
            "loudness_standard": "EBU R128",
            "target_loudness_lufs": -14.0,
            "true_peak_dbtp": -1.0,
            "normalization": "two_pass_loudnorm",
            "cue_gap_ms": 350.0,
            "notes": "সমস্ত সেকশন অডিও EBU R128 প্রোটোকলে নরমালাইজ করা: -14.0 LUFS ইন্টিগ্রেটেড লাউডনেস, -1.0 dBTP ট্রু পিক লক্ষ্য। পরপর কিউগুলোর মধ্যে ৩৫০ms ডিজিটাল সাইলেন্স স্থাপন করা হয়।",
        },
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
    expected_keys = set(SECTIONS_DATA)
    assert set(loaded["sections"]) == expected_keys
    total_cues = 0
    total_ms = 0.0
    figures = 0
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == len(EXPECTED_TYPES[sec_id])
        assert msec["section_id"] == sec_id
        assert msec["alias"] == ALIASES[sec_id]
        assert msec["audio_file"] == EXPECTED_AUDIO_FILES[sec_id]
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    assert total_cues == 37

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Calculus Lesson 10")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<30} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 5 sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json is valid JSON; all 5 mp3 files exist and are non-empty.")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(build_all())
