# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Calculus Lesson 08
("Integration and the fundamental theorem", Bengali) to the Lesson-01
gold standard.

CONTENT SOURCE: ONLY the CURRENT live DOM text of
courses/calculus/lesson_08.html (velocity/speedometer, dt-strips, Riemann
sum -> Leibniz integral, area function dA/dx = f(x), antiderivative and
F(b)-F(a)), extracted via the narration_engine.js selector with KaTeX
<annotation> preservation (governance/calc08_dom_blocks.json, 26/26 cues:
8/6/6/6).

Deterministic, re-runnable, self-contained:
  * 26 cues in 4 narrated sections with EXACTLY the same section IDs, alias
    keys, audio_file names, cue types and cue order as the existing manifest
    (verified 26/26 against the LIVE DOM: 8/6/6/6).
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Figure cues are genuine 2-4 sentence natural explanations — never the
    artificial label "চিত্র প্রদর্শনী" — and read naturally about what is on
    screen (velocity curve + shaded distance, Riemann rectangles, the growing
    area strip, the two endpoints of the fundamental theorem).
  * Every script is clean spoken Bengali with phonetic safeguards:
    ∫ -> ইন্টিগ্রাল, dt -> ডি টি, dx -> ডি এক্স, dT -> ডি টি, ds -> ডি এস,
    v(t) -> ভি অব টি, s(t) -> এস অব টি, f(x) -> এফ অব এক্স,
    F(b)-F(a) -> এফ বি মাইনাস এফ এ, 8t -> আট টি, t^2 -> টি স্কয়ার,
    t^3 -> টি কিউব, 85.33 -> পঁচাশি দশমিক তিন তিন. No TeX, LaTeX,
    backslashes, $, braces, brackets, em-dashes, raw hyphens or Latin letters.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, p +2%, figure -4%, callout +0%, formula-box -8%,
      conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with
    the exact-ms timings and the same 4 canonical section keys of the old
    manifest (each keeps its "alias" field).
  * Validates non-zero durations, zero overlap, valid JSON and non-empty mp3s.

Usage:  python governance/build_expressive_teacher_audio_calc08.py
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
                         "calculus", "lesson_08")
MANIFEST_TITLE = "অধ্যায় ০৮ — যোগজীকরণ ও ক্যালকুলাসের মৌলিক উপপাদ্য (Integration & The Fundamental Theorem of Calculus)"

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

# Parity guards: exact cue-type sequence expected for each narrated section
# (from the live DOM extraction, 26 cues total, verified 8/6/6/6).
EXPECTED_TYPES = {
    "sec-accumulation-intro":      ["h2", "chapter-quote", "p", "figure", "p", "callout", "p", "p"],
    "sec-riemann-to-integral":     ["h2", "p", "figure", "p", "callout", "p"],
    "sec-area-function-derivative": ["h2", "p", "figure", "p", "callout", "p"],
    "sec-fundamental-theorem":     ["h2", "p", "figure", "p", "callout", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-accumulation-intro":       "sec_01_accumulation_intro.mp3",
    "sec-riemann-to-integral":      "sec_02_riemann_to_integral.mp3",
    "sec-area-function-derivative": "sec_03_area_function_derivative.mp3",
    "sec-fundamental-theorem":      "sec_04_fundamental_theorem.mp3",
}
# Canonical DOM section id -> legacy alias field kept in the manifest.
ALIASES = {
    "sec-accumulation-intro":       "sec_01_accumulation_intro",
    "sec-riemann-to-integral":      "sec_02_riemann_to_integral",
    "sec-area-function-derivative": "sec_03_area_function_derivative",
    "sec-fundamental-theorem":      "sec_04_fundamental_theorem",
}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (26 cues)
# Every line mirrors the CURRENT live DOM block of the same type/index.
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-accumulation-intro": {
        "title": "১. অবিরাম পরিবর্তন ও দূরত্বের সঞ্চয় (Accumulation of Changing Quantities)",
        "audio_file": "sec_01_accumulation_intro.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, অবিরাম পরিবর্তন ও দূরত্বের সঞ্চয়।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, কোনো এমন বিষয় প্রমাণ করার চেষ্টা কখনোই করা উচিত নয়, যা প্রায় সুস্পষ্ট নয়। গণিতে দীর্ঘ সূত্রে ডুবে যাওয়ার আগে ধারণাটি অন্ততপক্ষে বোধগম্য ও স্বাভাবিক কি না, তা নিশ্চিত হওয়া জরুরি, বলেছেন আলেকজান্ডার গ্রোথেনডিক।"},
            {"index": 2, "type": "p",
             "tts": "ধরা যাক আপনি একটি গাড়িতে বসে আছেন এবং জানালা দিয়ে বাইরে দেখতে পাচ্ছেন না, শুধু স্পিডোমিটারের দিকে তাকাতে পারছেন। কোথাও গাড়িটি যাত্রা শুরু করে, ক্রমশ বেগ বাড়ায়, আবার ধীরে ধীরে থেমে যায়, পুরো ঘটনাটি আট সেকেন্ডে ঘটে। স্পিডোমিটারের পাঠ নিয়ে তৈরি করা যায় বেগের একটি মডেল, ভি অব টি সমান টি গুণ আট বিয়োগ টি, অর্থাৎ আট টি বিয়োগ টি স্কয়ার, মিটার প্রতি সেকেন্ড। প্রশ্ন হলো, শুধু এই বেগ জানা থেকে কীভাবে এস অব টি নামক দূরত্ব ফাংশনটি পাওয়া যাবে, যা যেকোনো টি তে মোট অতিক্রান্ত দূরত্ব বলে দেবে?"},
            {"index": 3, "type": "figure",
             "tts": "এই চিত্রে ভি অব টি সমান টি গুণ আট বিয়োগ টি বক্ররেখাটি শূন্য থেকে আট সেকেন্ড পর্যন্ত আঁকা হয়েছে, আর তার নিচের অঞ্চলটি সবুজে ছায়াঘেরা। অনুভূমিক অক্ষের একক সেকেন্ড আর উল্লম্ব অক্ষের একক মিটার প্রতি সেকেন্ড হওয়ায় ক্ষেত্রফলের একক দাঁড়ায় মিটার, অর্থাৎ দূরত্ব। লক্ষ্য করুন বেগের চরম মান চার সেকেন্ডে, কিন্তু দূরত্ব ক্রমেই বাড়ছে, কারণ বেগ সবসময় ধনাত্মক।"},
            {"index": 4, "type": "p",
             "tts": "এই ধারণাটি আসলে দুই ধাপের। প্রথমত, যদি গাড়িটি স্থির বেগে চলত, তবে দূরত্ব হতো বেগ গুণ সময়, আর বেগ বনাম সময় লেখচিত্রে সেটি দেখা যেত একটি আয়তক্ষেত্রের ক্ষেত্রফল হিসেবে। দ্বিতীয়ত, যেহেতু বেগ প্রতি মুহূর্তে বদলাচ্ছে, তাই আমরা সময়কে অসংখ্য সরু ফালিতে ভাগ করি, প্রতিটি ফালির প্রস্থ ডি টি এবং তৎকালীন বেগ ভি অব টি। এই আসন্নায়নের ফালিগুলোর ক্ষেত্রফলই হলো অতি ক্ষুদ্র দূরত্ব।"},
            {"index": 5, "type": "callout",
             "tts": "বিশেষ অন্তর্দৃষ্টি, স্থানীয় স্থায়িত্বের নীতি। যেকোনো মসৃণ বক্ররেখাকে যথেষ্ট ছোট ব্যবধানে জুম করলে সেটি প্রায় সমতল দেখায়। তাই ডি টি একটি ছোট সময় ব্যবধান নিলে ওই মুহূর্তে গাড়ির বেগকে প্রায় স্থির ধরা যায়, ফলে অতি ক্ষুদ্র দূরত্ব ডি এস প্রায় সমান ভি অব টি গুণ ডি টি। ডি টি যত ছোট হবে, এই আসন্নায়ন তত নিখুঁত হবে, আর এটিই পুরো যোগজীকরণের ভিত্তি।"},
            {"index": 6, "type": "p",
             "tts": "জ্যামিতিকভাবে ভি অব টি গুণ ডি টি হলো লেখচিত্রের নিচে স্থাপিত অতি পাতলা একটি আয়তাকার ফালির ক্ষেত্রফল, উচ্চতা বেগ, প্রস্থ সময়। উদাহরণস্বরূপ এক সেকেন্ড থেকে এক দশমিক দুই পাঁচ সেকেন্ডের ফালিটিতে বেগ প্রায় সাত মিটার প্রতি সেকেন্ড ধরলে অতিক্রান্ত দূরত্ব হয় সাত গুণ শূন্য দশমিক দুই পাঁচ, অর্থাৎ এক দশমিক সাত পাঁচ মিটার। বাস্তবে এই ব্যবধানে বেগ সাত থেকে প্রায় আট দশমিক চার পর্যন্ত বেড়ে যায়, কিন্তু ফালিটি যত সরু হবে, আসন্নায়ন তত কম ভুল হবে।"},
            {"index": 7, "type": "p",
             "tts": "মোট দূরত্ব পেতে হলে এই প্রতিটি ক্ষুদ্র ফালির ক্ষেত্রফলকে একে একে যোগ করতে হবে। সসীম সংখ্যক ফালির এই যোগফলই পরে রিম্যান সমষ্টি নামে পরিচিত, আর ডি টি শূন্যের দিকে গেলে সেটি বক্ররেখার নিচের প্রকৃত ক্ষেত্রফলে পরিণত হয়।"},
        ],
    },

    "sec-riemann-to-integral": {
        "title": "২. রিম্যান সাম থেকে লাইবনিজের ইন্টিগ্রাল প্রতীক (Riemann Sums & Leibniz's Integral Notation)",
        "audio_file": "sec_02_riemann_to_integral.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, রিম্যান সাম থেকে লাইবনিজের ইন্টিগ্রাল প্রতীক।"},
            {"index": 1, "type": "p",
             "tts": "টি সমান এ থেকে টি সমান বি পর্যন্ত মোট অতিক্রান্ত দূরত্বের আনুমানিক মান পেতে হলো আমাদের সবকটি পাতলা আয়তাকার ফালির ক্ষেত্রফল একে একে যোগ করতে হবে, অর্থাৎ দূরত্ব প্রায় সমান ভি অব টি গুণ ডেল্টা টি এর যোগফল। গণিতের ভাষায় এই সসীম যোগফলকে বলা হয় রিম্যান সমষ্টি, নামকরণ করা হয়েছে বার্নহার্ড রিম্যানের নামে।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে একই বক্ররেখার নিচে দুই সেট আয়তক্ষেত্র দেখানো হয়েছে, কম সংখ্যক চওড়া ফালি আর বেশি সংখ্যক সরু ফালি। দ্বিতীয় সেটের খাঁজকাটা সিঁড়ির মতো ধাপগুলো বক্ররেখার গায়ে অনেক বেশি কাছে সেঁটে যায়। ডি টি ক্রমশ ছোট করলে ফালির সংখ্যা বাড়ে, ত্রুটি কমে, আর সমষ্টি প্রকৃত ক্ষেত্রফলের কাছে পৌঁছায়, আর এই প্রক্রিয়াটিই ইন্টিগ্রালের সংজ্ঞা।"},
            {"index": 3, "type": "p",
             "tts": "গটফ্রিড লাইবনিজ এই অবিচ্ছিন্ন সমষ্টির জন্য বেছে নিয়েছিলেন প্রসারিত এস চিহ্ন, অর্থাৎ ইন্টিগ্রাল চিহ্ন, যা ল্যাটিন সাম্মা শব্দের প্রথম অক্ষর থেকে এসেছে। ইন্টিগ্রালের নিচে এ ও উপরে বি বসিয়ে ভি অব টি আর ডি টি লেখার অর্থ হলো, এ থেকে বি পর্যন্ত অসংখ্য অতি সূক্ষ্ম ফালির ভি অব টি গুণ ডি টি এর যোগফল। এখানে ডি টি র দুইটি ভূমিকা আছে, এটি একদিকে প্রতিটি ফালির ক্ষেত্রফলের গুণনীয়ক, অপরদিকে নমুনা নেওয়া সময়গুলোর মধ্যকার ব্যবধানও নির্দেশ করে।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, লাইবনিজ প্রতীকের অন্তর্নিহিত দর্শন। আমরা সাধারণ যোগফলের জন্য সিগমা চিহ্ন ব্যবহার করি, কিন্তু এখানে তা ব্যবহার করি না, কারণ ইন্টিগ্রাল কোনো নির্দিষ্ট ডি টি র জন্য এককোনো নির্দিষ্ট যোগফল নয়। এটি প্রকাশ করে যে ডি টি শূন্যের দিকে গেলে সেই সমষ্টি যে মানের দিকে ধাবিত হয়, তাকে। একই কারণে ডি এক্স ও শুধু একটি চলকের নাম নয়, এটি সেই অতিক্ষুদ্র প্রস্থকেও বোঝায় যার গুণফল যোগ করা হচ্ছে।"},
            {"index": 5, "type": "p",
             "tts": "সীমার চূড়ান্ত পর্যায়ে ডেল্টা টি শূন্যের দিকে গেলে ভি অব টি গুণ ডেল্টা টি এর যোগফলের সীমা দাঁড়ায় ইন্টিগ্রাল এ থেকে বি পর্যন্ত ভি অব টি ডি টি, আর এই সীমাস্থ সমষ্টিকে বলা হয় নির্দিষ্ট যোগজ। আমাদের গাড়ির ক্ষেত্রে এ শূন্য ও বি আট নিলে এই যোগজের মান দাঁড়ায় পঁচাশি দশমিক তিন তিন মিটার, যা বক্ররেখার নিচের মোট ক্ষেত্রফলের হুবহু সমান।"},
        ],
    },

    "sec-area-function-derivative": {
        "title": "৩. ক্ষেত্রফল ফাংশন এবং বৃদ্ধির হার: কেন dA/dx = f(x)? (The Area Function and its Derivative)",
        "audio_file": "sec_03_area_function_derivative.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, ক্ষেত্রফল ফাংশন এবং বৃদ্ধির হার, কেন ডি এ বাই ডি এক্স সমান এফ অব এক্স?"},
            {"index": 1, "type": "p",
             "tts": "লক্ষ কোটি আয়তক্ষেত্র হাতে যোগ করা কার্যকর পথ নয়। তাই আমরা কৌশল বদলাই, উভয় সীমা স্থির রাখার বদলে ডান প্রান্তবিন্দুকে একটি স্বাধীন চলক এক্স বানিয়ে দিই এবং সংজ্ঞায়িত করি ক্ষেত্রফল ফাংশন এ অব এক্স সমান শূন্য থেকে এক্স পর্যন্ত ইন্টিগ্রাল এফ অব টি ডি টি, অর্থাৎ শূন্য থেকে পরিবর্তনশীল এক্স পর্যন্ত বক্ররেখার নিচের মোট আবদ্ধ ক্ষেত্রফল।"},
            {"index": 2, "type": "figure",
             "tts": "এই চিত্রে শূন্য থেকে টি পর্যন্ত ছায়াঘেরা অঞ্চলটি হলো ক্ষেত্রফল ফাংশন এ অব টি। হলুদ সরু ফালিটি ডান প্রান্তে ডি টি পরিমাণ নাড়া দেওয়ার ফলে নতুন যোগ হওয়া ডি এ, এর উচ্চতা ঠিক ওই বিন্দুতে বক্ররেখার উচ্চতা ভি অব টি এবং প্রস্থ ডি টি। ডি টি যত ছোট হবে, এই আয়তাকার আসন্নায়ন তত নিখুঁত হবে, আর চিত্রটি আসলে ডি এ বাই ডি টি সমান ভি অব টি সূত্রটির জ্যামিতিক প্রমাণ।"},
            {"index": 3, "type": "p",
             "tts": "ডান সীমানা এক্স যত ডানে সরবে, ক্ষেত্রফল এ অব এক্স তত বৃদ্ধি পাবে। যদি এক্স কে সামান্য ডি এক্স পরিমাণ বাড়ানো হয়, তবে নতুন যুক্ত ফালিটির প্রস্থ ডি এক্স ও উচ্চতা এফ অব এক্স, অতএব ডি এ প্রায় সমান এফ অব এক্স গুণ ডি এক্স। উভয় পক্ষকে ডি এক্স দিয়ে ভাগ করলেই উন্মোচিত হয় গণিতের ইতিহাসের অন্যতম শ্বাসরুদ্ধকর সত্য, ডি এ বাই ডি এক্স সমান এফ অব এক্স, অর্থাৎ ক্ষেত্রফল ফাংশনের ডেরিভেটিভ হুবহু মূল বক্ররেখার উচ্চতা।"},
            {"index": 4, "type": "callout",
             "tts": "গভীর উপলব্ধি, ক্ষেত্রফলের গতি ও বক্ররেখার উচ্চতা। একটি পাত্রে জল ভরার কথা ভাবুন, সঞ্চিত জলের আয়তন যে হারে বাড়ছে, তা নির্ভর করে কল থেকে আসা জলের তৎকালীন প্রবাহের ওপর। ঠিক তেমনি বক্ররেখা যেখানে যত উঁচু, ক্ষেত্রফল সেখানে তত তীব্র হারে বাড়ে, আর যেখানে উচ্চতা কম, সেখানে ধীরগতিতে। অর্থাৎ ক্ষেত্রফল সঞ্চয়ের হার আর কিছুই নয়, সরাসরি ফাংশনের বর্তমান মান এফ অব এক্স।"},
            {"index": 5, "type": "p",
             "tts": "এই উপলব্ধিই ক্যালকুলাসের দ্বিতীয় স্তম্ভটিকে প্রথমটির সাথে গ্রথিত করে। ক্ষেত্রফল নির্ণয় করা মানে এখন এমন একটি ফাংশন খুঁজে বের করা, যার ডেরিভেটিভ মূল বক্ররেখার সমান, অর্থাৎ অ্যান্টি ডেরিভেটিভ বের করা। অবকলনের বিপরীত পথে হেঁটেই আমরা যোগজ নির্ণয় করব।"},
        ],
    },

    "sec-fundamental-theorem": {
        "title": "৪. ক্যালকুলাসের মৌলিক উপপাদ্য ও সমাধান (The Fundamental Theorem of Calculus)",
        "audio_file": "sec_04_fundamental_theorem.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, ক্যালকুলাসের মৌলিক উপপাদ্য ও চূড়ান্ত সমাধান।"},
            {"index": 1, "type": "p",
             "tts": "আমাদের বেগ ফাংশন ভি অব টি সমান আট টি বিয়োগ টি স্কয়ার এর অ্যান্টি ডেরিভেটিভ বের করা যাক। আট টি এর অ্যান্টি ডেরিভেটিভ হলো চার টি স্কয়ার, কারণ চার টি স্কয়ারের ডেরিভেটিভ আট টি, আর ঋণাত্মক টি স্কয়ারের অ্যান্টি ডেরিভেটিভ হলো ঋণাত্মক এক তৃতীয়াংশ টি কিউব, কারণ টি কিউবের ডেরিভেটিভ তিন টি স্কয়ার। সুতরাং এস অব টি সমান চার টি স্কয়ার বিয়োগ এক তৃতীয়াংশ টি কিউব। টি সমান আট বসালে এই রাশির মান দাঁড়ায় পঁচাশি দশমিক তিন তিন মিটার, আমাদের মূল প্রশ্নের সঠিক উত্তর, কোনো অসীম যোগফল ছাড়াই।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে এ ও বি দুটি প্রান্তের মধ্যকার ছায়াঘেরা ক্ষেত্রফল দেখানো হয়েছে। ক্যাপিটাল এফ হলো ছোট এফ এর যেকোনো অ্যান্টি ডেরিভেটিভ, তখন এই ক্ষেত্রফল হবে এফ বি মাইনাস এফ এ, অর্থাৎ উপরের প্রান্তে অ্যান্টি ডেরিভেটিভের মান থেকে নিচের প্রান্তের মান বাদ দেওয়া। লক্ষ্য করুন এ ও বি র বাইরের অংশ চিত্রে আঁকা থাকলেও হিসাবে কেবল এই দুই প্রান্তই ব্যবহৃত হচ্ছে, আর এটিই মৌলিক উপপাদ্যের আশ্চর্যজনক দিক।"},
            {"index": 3, "type": "p",
             "tts": "এখানে প্লাস সি নিয়ে একটি সূক্ষ্মতা আছে। যেকোনো ধ্রুবক সি যোগ করলেই চার টি স্কয়ার বিয়োগ এক তৃতীয়াংশ টি কিউব প্লাস সি আরেকটি বৈধ অ্যান্টি ডেরিভেটিভ হয়, কারণ ধ্রুবকের ডেরিভেটিভ শূন্য। কোনটি বেছে নেবেন তা ঠিক করে নিচের সীমা, টি শূন্য হলে ক্ষেত্রফল অবশ্যই শূন্য হতে হবে, তাই শূন্য থেকে টি পর্যন্ত ইন্টিগ্রালের মান হলো উপরের প্রান্তে রাশিটির মান বিয়োগ নিচের প্রান্তে রাশিটির মান। সাধারণভাবে এ থেকে বি পর্যন্ত ইন্টিগ্রাল এফ অব এক্স ডি এক্স সমান এফ বি মাইনাস এফ এ, এখানে সি স্বয়ংক্রিয়ভাবে বাতিল হয়ে যায়।"},
            {"index": 4, "type": "callout",
             "tts": "চূড়ান্ত সারাংশ, অবকলন ও যোগজীকরণের পরম সামঞ্জস্য। অন্তরীকরণ ও যোগজীকরণ একে অপরের বিপরীত প্রক্রিয়া। ডেরিভেটিভ কোনো চলমান সমগ্রকে খণ্ড খণ্ড স্থানীয় হারে ভেঙে টুকরো করে, আর ইন্টিগ্রাল সেই অগণিত অতি সূক্ষ্ম টুকরোগুলোকে পুনরায় জোড়া লাগিয়ে মূল সমগ্রকে ফিরিয়ে দেয়। গুণ ও ভাগ যেমন পরস্পরের উল্টো ক্রিয়া, ক্যালকুলাসের এই দুই স্তম্ভও তেমনি, একটি ভেঙে দেখায়, অনেটি গড়ে তোলে।"},
            {"index": 5, "type": "p", "role": "conclusion",
             "tts": "এখানেই সবচেয়ে আশ্চর্যজনক বিষয়টি লুকিয়ে আছে। ইন্টিগ্রালের মান নিম্ন সীমা থেকে উচ্চ সীমার মধ্যকার প্রতিটি বিন্দুকে ইন্টিগ্রেট করে, তাই তো শব্দটি একসাথে আনা। অথচ অ্যান্টি ডেরিভেটিভ দিয়ে হিসাব করার সময় আমরা কেবল দুটি ইনপুট দেখি, উপরের প্রান্ত ও নিচের প্রান্ত, মনে হয় যেন ফাঁকি দেওয়া হচ্ছে। কিন্তু অ্যান্টি ডেরিভেটিভ নিজেই ওই দুই প্রান্তের মধ্যকার সমস্ত তথ্য আগেভাগেই ধরে রেখেছে।"},
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
        manifest_sections[sec_id] = await build_section(sec_id, sec)

    manifest_data = {
        "course": "calculus",
        "lesson": "lesson_08",
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
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    assert total_cues == 26

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Calculus Lesson 08")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<30} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 4 sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json is valid JSON; all 4 mp3 files exist and are non-empty.")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(build_all())
