# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for 3Blue1Brown Lesson 01 (Bengali),
expressive-edition.

Deterministic, re-runnable, self-contained:
  * 73 cues in 6 sections with EXACTLY the same section IDs, audio_file names,
    cue types and cue order as governance/l01_dom_blocks.json / manifest.json.
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Figure cues are genuine 2-4 sentence pedagogical explanations.
  * Every script is clean spoken Bengali: no TeX, LaTeX, backslashes, $, braces,
    brackets, em-dashes, raw hyphens or Latin letters.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=).
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST).
  * Validates non-zero durations, zero overlap, valid JSON and non-empty mp3s.

Usage:  python governance/build_expressive_teacher_audio.py
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
                         "linear_algebra", "lesson_01")

# Prosody defaults keyed by cue type: (rate, pitch, volume)
PROSODY_DEFAULT = {
    "h2":           ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
    "h3":           ("-3%", "+0Hz", "+0%"),
    "chapter-quote":("-3%", "+0Hz", "+0%"),
    "p":            ("+2%", "+0Hz", "+0%"),   # natural teacher pace
    "figure":       ("-4%", "+0Hz", "+0%"),   # slower, considerate explanation
    "callout":      ("+0%", "+0Hz", "+0%"),
    "formula-box":  ("-8%", "+0Hz", "+0%"),   # slow and deliberate
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")   # calm concluding prose

# Parity guard: exact cue-type sequence expected for each section.
EXPECTED_TYPES = {
    "sec-interpretations": ["h2", "chapter-quote", "p", "figure", "p", "figure",
                            "callout", "figure", "p", "figure", "callout",
                            "formula-box", "callout", "figure", "p"],
    "sec-coordinates":    ["h2", "p", "figure", "p", "figure", "p", "figure", "p",
                           "figure", "p", "figure", "p", "figure", "formula-box",
                           "p", "p", "p", "p", "figure", "p"],
    "sec-addition":       ["h2", "p", "h3", "p", "figure", "p", "figure", "p", "p",
                           "figure", "p", "figure", "p", "figure", "p", "formula-box"],
    "sec-scalar":         ["h2", "p", "figure", "p", "figure", "p", "figure", "p",
                           "p", "formula-box"],
    "sec-basis":          ["h2", "p", "formula-box", "p", "formula-box", "callout", "p"],
    "sec-conclusion":     ["h2", "p", "p", "p", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-interpretations": "sec_01_sec-interpretations.mp3",
    "sec-coordinates":    "sec_02_sec-coordinates.mp3",
    "sec-addition":       "sec_03_sec-addition.mp3",
    "sec-scalar":         "sec_04_sec-scalar.mp3",
    "sec-basis":          "sec_05_sec-basis.mp3",
    "sec-conclusion":     "sec_06_sec-conclusion.mp3",
}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (73 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-interpretations": {
        "title": "ভেক্টরের তিনটি দৃষ্টিভঙ্গি",
        "audio_file": "sec_01_sec-interpretations.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, ভেক্টরের তিনটি দৃষ্টিভঙ্গি।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, সংখ্যাকে স্থানাঙ্ক হিসেবে উপস্থাপন করা একটি সহিংস কাজ। বলেছেন হের্মান ওয়াইল।"},
            {"index": 2, "type": "p",
             "tts": "লিনিয়ার বীজগণিতের একেবারে গোড়ার, মৌলিক ভিত্তিপ্রস্তর হলো ভেক্টর। কিন্তু ভেক্টর আসলে কী জিনিস? গণিত, পদার্থবিদ্যা আর কম্পিউটার বিজ্ঞানের শিক্ষার্থীরা এই প্রশ্নের উত্তর কিছুটা ভিন্ন ভিন্ন দৃষ্টিভঙ্গি থেকে দিয়ে থাকেন।"},
            {"index": 3, "type": "figure",
             "tts": "লক্ষ্য করুন, এখানে মূলবিন্দু থেকে শুরু হওয়া একটি তীরচিহ্ন দেখা যাচ্ছে। তীরের দৈর্ঘ্য বলছে ভেক্টরের মান, আর যেদিকে মুখ করেছে সেটিই তার দিক। এই দুটি তথ্যই একটিমাত্র ভেক্টরকে সম্পূর্ণরূপে চেনায়।"},
            {"index": 4, "type": "p",
             "tts": "মোটাদাগে তিনটি সুনির্দিষ্ট দৃষ্টিভঙ্গি রয়েছে, পদার্থবিজ্ঞানের ছাত্রের দৃষ্টিভঙ্গি, কম্পিউটার সায়েন্সের ছাত্রের দৃষ্টিভঙ্গি, আর গণিতবিদদের দৃষ্টিভঙ্গি।"},
            {"index": 5, "type": "figure",
             "tts": "একই ভেক্টরকে তিনটি ভিন্ন চোখ দিয়ে দেখানো হয়েছে। বাঁয়ে পদার্থবিদ তীরচিহ্ন দেখছেন, মাঝখানে কম্পিউটার বিজ্ঞানী দেখছেন সংখ্যার তালিকা, আর ডানে গণিতবিদ দেখছেন এক বিমূর্ত নিয়ম। একই জিনিসের এই তিনটি রূপই এই অধ্যায়ে আমাদের সাহায্য করবে।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, এক, পদার্থবিজ্ঞানের ছাত্রের দৃষ্টিভঙ্গি। পদার্থবিজ্ঞানীদের কাছে ভেক্টর মহাশূন্যে বা সমতলে নির্দেশিত এক তীরচিহ্ন। একে সংজ্ঞায়িত করে দুটি মৌলিক বৈশিষ্ট্য, তার দৈর্ঘ্য বা মান, আর তার অভিমুখ বা দিক। যতক্ষণ এই দুটি অপরিবর্তিত থাকছে, আপনি একে যেকোনো জায়গায় সরিয়ে নিতে পারেন, ভেক্টর কিন্তু একই থাকবে।"},
            {"index": 7, "type": "figure",
             "tts": "এখানে তীরচিহ্নের দৈর্ঘ্য আর তার দিক আলাদা করে চিহ্নিত করা হয়েছে। দৈর্ঘ্য যত বেশি, ভেক্টরের মান তত বেশি, আর তীর যেদিকে মুখ করেছে সেদিকেই তার অভিমুখ। মনে রাখবেন, এই দুটির কোনো একটিও বদলালে ভেক্টরটি আর আগের ভেক্টর থাকবে না।"},
            {"index": 8, "type": "p",
             "tts": "যেসব ভেক্টর একটি সমতলে থাকে, তাদের বলি দ্বিমাত্রিক, অর্থাৎ টুডি। আর আমাদের চারপাশের বিস্তৃত স্থানে যেসব ভেক্টর থাকে, তাদের বলি ত্রিমাত্রিক, অর্থাৎ থ্রিডি।"},
            {"index": 9, "type": "figure",
             "tts": "বাঁয়ে ভেক্টরটি একটিমাত্র সমতলে শুয়ে আছে, তাই একে বলছি দ্বিমাত্রিক বা টুডি। ডানে ভেক্টরটি তিন দিকে বিস্তৃত স্থানে মুক্ত, তাই সেটি ত্রিমাত্রিক বা থ্রিডি। সমতল আর স্থানের এই পার্থক্যটা পরের অধ্যায়গুলোতে বারবার সামনে আসবে।"},
            {"index": 10, "type": "callout",
             "tts": "বিশেষ নোট, দুই, কম্পিউটার সায়েন্সের ছাত্রের দৃষ্টিভঙ্গি। অন্যদিকে কম্পিউটার সায়েন্সে ভেক্টর মূলত সংখ্যার একটি সুশৃঙ্খল তালিকা। ধরুন আপনি বাড়ির দাম আর আয়তন নিয়ে বিশ্লেষণ করছেন, তাহলে প্রতিটি বাড়িকে একজোড়া সংখ্যা দিয়ে লেখা যায়, ভেক্টর ভি হাউস বলছে কলাম ভেক্টর, উপরে দুই হাজার ছয়শত বর্গফুট আর নিচে দাম তিন লক্ষ ডলার। এখানে সংখ্যার ক্রম কিন্তু অত্যন্ত সংবেদনশীল, প্রথম সংখ্যাটি সবসময় আয়তন আর দ্বিতীয়টি দাম বোঝায়। এই অর্থে ভেক্টর শব্দটি একটিমাত্র তালিকারই গাণিতিক নাম, আর তার মাত্রা নির্ভর করে তালিকায় কতটি সংখ্যা আছে তার ওপর।"},
            {"index": 11, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। ভেক্টর ভি হাউস সমান কলাম ভেক্টর, উপরে দুই হাজার ছয়শত বর্গফুট, নিচে দাম তিন লক্ষ ডলার।"},
            {"index": 12, "type": "callout",
             "tts": "বিশেষ নোট, তিন, গণিতবিদদের দৃষ্টিভঙ্গি। গণিতবিদরা এই দুই ধারণাকে এক সুতোয় গেঁথে একটি সাধারণ বিমূর্ত রূপ দেন। তাঁদের মতে যেকোনো কিছুকেই ভেক্টর বলা যাবে, যদি সেখানে ভেক্টর যোগ আর স্কেলার দ্বারা গুণনের সুস্পষ্ট ও সংগত নিয়ম থাকে। এই দুটি প্রক্রিয়া নিয়েই এই অধ্যায়ের পরবর্তী অংশে আমরা বিস্তারিত কথা বলব।"},
            {"index": 13, "type": "figure",
             "tts": "এখানে নির্দিষ্ট কোনো তীর বা সংখ্যা নেই, বরং দেখানো হয়েছে এক বিমূর্ত নিয়মের জগৎ। যেকোনো বস্তুকে এখানে ভেক্টর হিসেবে নেওয়া যায়, যদি সেটি যোগ আর স্কেলিংয়ের নিয়ম মেনে চলে। এই সার্বজনীনতাই গণিতবিদদের দৃষ্টিভঙ্গির শক্তি।"},
            {"index": 14, "type": "p", "role": "conclusion",
             "tts": "এই দৃষ্টিভঙ্গিটি কিছুটা বিমূর্ত, তাই সিরিজের শেষ অধ্যায়ে পৌঁছানোর আগে একে সরিয়ে রেখে বাস্তবসম্মত ভিত্তিতে এগোনোই শ্রেয়। তবে এখানে একে তুলে ধরার উদ্দেশ্য হলো, ভেক্টর যোগ আর সংখ্যা দিয়ে গুণের এই দুটি ধারণা পুরো লিনিয়ার বীজগণিত জুড়েই কেন্দ্রীয় ভূমিকা পালন করবে।"},
        ],
    },

    "sec-coordinates": {
        "title": "কোঅর্ডিনেট সিস্টেম ও মূলবিন্দু",
        "audio_file": "sec_02_sec-coordinates.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, কোঅর্ডিনেট সিস্টেম ও মূলবিন্দু।"},
            {"index": 1, "type": "p",
             "tts": "আপনাদের অনেকেই হয়তো স্থানাঙ্ক ব্যবস্থা বা কোঅর্ডিনেট সিস্টেমের সাথে আগেই পরিচিত। তা সত্ত্বেও একবার ঝালিয়ে নেওয়া ফলপ্রসূ, কারণ লিনিয়ার বীজগণিতের দুটি প্রধান দৃষ্টিভঙ্গির মধ্যকার সমস্ত গুরুত্বপূর্ণ আদান প্রদান এখানেই ঘটে। আপাতত আমাদের মনোযোগ দ্বিমাত্রিক বা টুডি তলে সীমাবদ্ধ রাখলে, দেখতে পাই একটি অনুভূমিক রেখা, যাকে আমরা বলি এক্স অক্ষ, আর একটি উল্লম্ব রেখা, যাকে আমরা বলি ওয়াই অক্ষ।"},
            {"index": 2, "type": "figure",
             "tts": "এখানে একটি অনুভূমিক রেখা আর একটি উল্লম্ব রেখা দেখা যাচ্ছে। অনুভূমিক রেখাটি এক্স অক্ষ, উল্লম্ব রেখাটি ওয়াই অক্ষ, আর দুইয়ের ছেদবিন্দু থেকে পুরো স্থানাঙ্ক ব্যবস্থাটি গড়ে ওঠে। এই দুটি অক্ষই পরে প্রতিটি ভেক্টরের অবস্থান নির্ধারণ করবে।"},
            {"index": 3, "type": "p",
             "tts": "যে বিন্দুতে অক্ষ দুটি পরস্পরকে ছেদ করে, সেটিই মূলবিন্দু বা অরিজিন। আপনি একে সম্পূর্ণ স্থানের কেন্দ্রবিন্দু আর সমস্ত ভেক্টরের সূচনাস্থল হিসেবে ভাবতে পারেন।"},
            {"index": 4, "type": "figure",
             "tts": "অক্ষ দুটি যেখানে মিলিত হয়েছে, সেই কেন্দ্রবিন্দুটিই মূলবিন্দু, যার মান শূন্য কমা শূন্য। লক্ষ্য করুন, সব তীরচিহ্নের লেজ ঠিক এই বিন্দুতেই শুরু হয়। মূলবিন্দুকে একটা সাধারণ বিন্দু না ভেবে স্থানের শূন্য অবস্থান হিসেবে দেখা মুখ্য।"},
            {"index": 5, "type": "p",
             "tts": "একক দৈর্ঘ্য বোঝাতে একটি যথেচ্ছ দূরত্ব বেছে নেওয়া হয়, তারপর প্রতিটি অক্ষে সমান ব্যবধানে ছোট ছোট টিক মার্ক বা দাগ কাটা হয়।"},
            {"index": 6, "type": "figure",
             "tts": "অক্ষ বরাবর দেখা যাচ্ছে সমান ব্যবধানে কয়েকটি ছোট দাগ। প্রতিটি দাগ ঠিক এক একক দূরত্ব নির্দেশ করছে। এই দাগগুলো না থাকলে আমরা বলতে পারতাম না কতদূর এগিয়েছি।"},
            {"index": 7, "type": "p",
             "tts": "এরপর যখন আমরা পুরো দ্বিমাত্রিক স্থানটির কথা ভাবি, তখন এই টিক মার্কগুলোকে দুই দিকে বিস্তৃত করে একটি গ্রিড তৈরি করি, ঠিক এভাবে।"},
            {"index": 8, "type": "figure",
             "tts": "দেখুন, ছোট দাগগুলো এখন সারি সারি রেখায় রূপ নিয়েছে, তৈরি হয়েছে ছককাগজের মতো একটা গ্রিড। এখানে গুরুত্বপূর্ণ হলো যে প্রতিটি খানা একক দূরত্বের সমান, তাই যেকোনো ভেক্টরের অবস্থান এখন সহজে মাপা যায়।"},
            {"index": 9, "type": "p",
             "tts": "এখন চলুন একটা বিষয়ে স্থির হই। যখনই আমরা ভেক্টর শব্দটি বলব, মনে একটা তীরচিহ্নই ভেসে উঠুক। এখানে আমরা জ্যামিতিক দৃষ্টিভঙ্গির ওপর জোর দিচ্ছি, তাই নতুন কিছু শেখার সময় প্রথমে তীরচিহ্নের কথা ভাবব। আরও সুস্পষ্টভাবে বললে, এক্স ওয়াই সমতলে এমন এক তীর কল্পনা করুন, যার লেজ সবসময় মূলবিন্দুতে স্থিত থাকে।"},
            {"index": 10, "type": "figure",
             "tts": "এখানে তীরটির লেজ মূলবিন্দুতে আর মাথা বা শীর্ষবিন্দু অন্য কোথাও। লক্ষ্য করুন, তীরের অবস্থান বদলালেও তার দৈর্ঘ্য ও দিক অপরিবর্তিত থাকে। মূলবিন্দু থেকে শুরু হওয়া এই তীরচিহ্নটিই আমাদের কাছে ভেক্টর।"},
            {"index": 11, "type": "p",
             "tts": "একটি ভেক্টরের কোঅর্ডিনেট হলো এক জোড়া সংখ্যা, যা বলে দেয় কীভাবে মূলবিন্দুতে থাকা লেজ থেকে তার শীর্ষবিন্দুতে পৌঁছাতে হবে। প্রথম সংখ্যাটি বলে দেয় এক্স অক্ষ বরাবর কতদূর হাঁটতে হবে, ধনাত্মক হলে ডানদিকে আর ঋণাত্মক হলে বামদিকে। দ্বিতীয় সংখ্যাটি বলে দেয় এরপর ওয়াই অক্ষের সমান্তরালে কতদূর হাঁটতে হবে, ধনাত্মক হলে উপরে আর ঋণাত্মক হলে নিচে।"},
            {"index": 12, "type": "figure",
             "tts": "ভেক্টরের দুটি সংখ্যা এখানে বন্ধনীর ভেতরে উল্লম্বভাবে সাজানো, একটির ওপর আর একটির নিচে। এই রূপটিকে বলি কলাম ভেক্টর। ওপরের সংখ্যাটি এক্স অক্ষের হিসাব, নিচেরটি ওয়াই অক্ষের, ক্রম বদলালেই ভিন্ন ভেক্টর হয়ে যায়।"},
            {"index": 13, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। ভেক্টর ভি সমান কলাম ভেক্টর, উপরে এক্স, নিচে ওয়াই।"},
            {"index": 14, "type": "p",
             "tts": "প্রথম সংখ্যাটি এক্স অক্ষ বরাবর কতদূর যেতে হবে তা নির্ধারণ করে, ধনাত্মক হলে ডানে আর ঋণাত্মক হলে বামে। আর দ্বিতীয় সংখ্যাটি ওয়াই অক্ষের সমান্তরালে কতদূর যেতে হবে তা নির্ধারণ করে, ধনাত্মক হলে উপরে আর ঋণাত্মক হলে নিচে।"},
            {"index": 15, "type": "p",
             "tts": "উদাহরণস্বরূপ, কলাম ভেক্টর উপরে তিন, নিচে মাইনাস দুই মানে এক্স অক্ষ বরাবর ডানদিকে তিন একক, তারপর ওয়াই অক্ষের সমান্তরালে নিচের দিকে দুই একক। এই দুটি পদক্ষেপ শেষে যে বিন্দুতে পৌঁছাবেন, সেখানেই তীরটির মাথা।"},
            {"index": 16, "type": "p",
             "tts": "সাধারণ বিন্দু থেকে পার্থক্য বোঝাতে সংখ্যাজোড়াকে থার্ড ব্র্যাকেট দিয়ে উল্লম্বভাবে লেখা হয়, প্রচলিত নিয়ম হলো কলাম আকারে লেখা। প্রতিটি সংখ্যাজোড়ার জন্য ঠিক একটি অনন্য ভেক্টর পাওয়া যায়, আবার প্রতিটি ভেক্টরের জন্যও নির্ধারিত থাকে ঠিক একটি সংখ্যাজোড়া।"},
            {"index": 17, "type": "p",
             "tts": "ত্রিমাত্রিক বা থ্রিডি স্পেসে আমরা তৃতীয় এক অক্ষ যোগ করি, যার নাম জেড অক্ষ। এটি এক্স ও ওয়াই, দুই অক্ষের সাথেই সমকোণে অবস্থান করে। এখানে প্রতিটি ভেক্টর তিনটি সংখ্যার এক সুশৃঙ্খল ট্রিপলেট দিয়ে প্রকাশ পায়, প্রথম সংখ্যাটি এক্স অক্ষ বরাবর দূরত্ব, দ্বিতীয়টি ওয়াই অক্ষের সমান্তরালে দূরত্ব, আর তৃতীয়টি নতুন জেড অক্ষের সমান্তরালে সরণ নির্দেশ করে।"},
            {"index": 18, "type": "figure",
             "tts": "দেখুন, পরিচিত এক্স ও ওয়াই অক্ষের সাথে আরেকটি অক্ষ যোগ হয়েছে, সেটি জেড অক্ষ। এটি সমতলের বাইরে গভীরতার দিকে নির্দেশ করে। এই তৃতীয় অক্ষই একটা সমতলকে পুরো ত্রিমাত্রিক স্থানে রূপ দেয়।"},
            {"index": 19, "type": "p", "role": "conclusion",
             "tts": "ত্রিমাত্রিক মহাশূন্যের প্রতিটি অনন্য সংখ্যার ট্রিপলেট একটি এবং কেবল একটি ভেক্টর দেয়, আর প্রতিটি ভেক্টর ঠিক একটি সংখ্যার ট্রিপলেটের সাথে জড়িত।"},
        ],
    },

    "sec-addition": {
        "title": "ভেক্টর যোগ — জ্যামিতিক ও সংখ্যাতাত্ত্বিক রূপ",
        "audio_file": "sec_03_sec-addition.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, ভেক্টর যোগ, জ্যামিতিক ও সংখ্যাতাত্ত্বিক রূপ।"},
            {"index": 1, "type": "p",
             "tts": "তাহলে ভেক্টর যোগ আর সংখ্যা দিয়ে ভেক্টরকে গুণ করার ব্যাপারটা আসলে কেমন? সর্বোপরি, লিনিয়ার বীজগণিতের প্রতিটি বিষয়ই এই দুটি মৌলিক অপারেশনের চারপাশে ঘোরে। সৌভাগ্যবশত, এই দুটি ধারণা তুলনামূলকভাবে বেশ সহজ ও সোজাসাপ্টা।"},
            {"index": 2, "type": "h3",
             "tts": "এখন যোগ নিয়ে কথা বলব।"},
            {"index": 3, "type": "p",
             "tts": "ধরা যাক আমাদের দুটি ভেক্টর আছে। ভেক্টর ভি উপরের দিকে আর সামান্য ডানে নির্দেশ করছে, আর ভেক্টর ডব্লিউ ডানে আর সামান্য নিচের দিকে নির্দেশ করছে।"},
            {"index": 4, "type": "figure",
             "tts": "এখানে মূলবিন্দু থেকে দুটি তীরচিহ্ন বের হয়েছে, একটির নাম ভি, অন্যটির নাম ডব্লিউ। লক্ষ্য করুন তাদের দৈর্ঘ্য ও দিক আলাদা, তাই এরা দুটি ভিন্ন ভেক্টর। যোগ শেখার আগে দুটিকে আলাদা করে চেনাটা জরুরি।"},
            {"index": 5, "type": "p",
             "tts": "এই দুটি ভেক্টর যোগ করতে হলে দ্বিতীয় ভেক্টরটিকে এমনভাবে সরাতে হবে, যেন তার লেজ প্রথম ভেক্টরের শীর্ষবিন্দুতে বসে। এরপর প্রথমটির লেজ থেকে দ্বিতীয়টির নতুন অবস্থানের শীর্ষবিন্দু পর্যন্ত একটিমাত্র তীর আঁকলেই সেটি হবে তাদের যোগফল।"},
            {"index": 6, "type": "figure",
             "tts": "এখানে ভেক্টর ডব্লিউকে সরিয়ে তার লেজ ভেক্টর ভির মাথায় বসানো হয়েছে। নতুন যে তীরটি ভির লেজ থেকে ডব্লিউর মাথা পর্যন্ত টানা হয়েছে, সেটিই ভি যোগ ডব্লিউ। এই পদ্ধতিকে বলি টিপ টু টেইল নিয়ম, অর্থাৎ এক তীরের মাথার সাথে পরের তীরের লেজ যোগ করা।"},
            {"index": 7, "type": "p",
             "tts": "যোগের এই সংজ্ঞা কেন যুক্তিযুক্ত, কেন অন্য সংজ্ঞা নয়? এর সুন্দর ব্যাখ্যা হলো, প্রতিটি ভেক্টরকে একটা নির্দিষ্ট সরণ হিসেবে ভাবা। আপনি যদি প্রথমে প্রথম ভেক্টর বরাবর এক ধাপ হাঁটেন, তারপর দ্বিতীয় ভেক্টর বরাবর হাঁটেন, তবে আপনার সার্বিক ফলাফল ঠিক তাই হবে, যেন সরাসরি তাদের যোগফল বরাবর হেঁটেছেন।"},
            {"index": 8, "type": "p",
             "tts": "একে ছোটবেলার সংখ্যারেখার যোগের বর্ধিত রূপ ভাবা যায়। দুই যোগ পাঁচ বোঝাতে আমরা প্রথমে দুই একক ডানে যাই, তারপর আরও পাঁচ একক ডানে যাই, আর শেষ ফল সাত একক ডানে যাওয়ার সমান।"},
            {"index": 9, "type": "figure",
             "tts": "এখানে একমাত্রিক সংখ্যারেখায় দুই ধাপের একটা যাত্রা দেখানো হয়েছে, প্রথমে দুই, তারপর আরও পাঁচ, শেষে সাতে পৌঁছানো। এই সরল চিত্রটিই দেখাচ্ছে যে ভেক্টর যোগ মূলত পদক্ষেপেরই সমষ্টি। দ্বিমাত্রিক বা ত্রিমাত্রিক ক্ষেত্রেও একই নিয়ম কাজ করে।"},
            {"index": 10, "type": "p",
             "tts": "এখন দেখা যাক সংখ্যাতাত্ত্বিকভাবে যোগ কীভাবে কাজ করে। প্রথম ভেক্টরের স্থানাঙ্ক কলাম ভেক্টর, উপরে এক, নিচে দুই, আর দ্বিতীয়টির কলাম ভেক্টর, উপরে তিন, নিচে মাইনাস এক। টিপ টু টেইল পদ্ধতিতে যোগফল বের করতে একে চার ধাপের পথ ভাবুন, প্রথমে এক একক ডানে, তারপর দুই একক উপরে, এরপর তিন একক ডানে, আর শেষে এক একক নিচে।"},
            {"index": 11, "type": "figure",
             "tts": "পথটি চারটি আলাদা পদক্ষেপে ভেঙে দেখানো হয়েছে, এক ডানে, দুই উপরে, তিন ডানে, আর এক নিচে। প্রতিটি পদক্ষেপ একটিমাত্র অক্ষ বরাবর, তাই এগুলোকে আলাদা করে হিসাব করা সহজ। এই চার ধাপই পরে দুটি সরল দিকে গুছানো হবে।"},
            {"index": 12, "type": "p",
             "tts": "এই পদক্ষেপগুলোকে পুনর্বিন্যাস করে সব অনুভূমিক সরণ আগে আর সব উল্লম্ব সরণ পরে করলে ফল দাঁড়ায়, ডানদিকে এক যোগ তিন অর্থাৎ চার একক, আর উল্লম্বভাবে দুই বিয়োগ এক অর্থাৎ এক একক। তাই নতুন ভেক্টরের স্থানাঙ্ক চার আর এক।"},
            {"index": 13, "type": "figure",
             "tts": "এখানে গুরুত্বপূর্ণ হলো যে আগের চারটি পদক্ষেপ দুটি দলে সাজানো, সব ডানের সরণ একসাথে আর সব উপরের সরণ একসাথে। ফলের তীরটি মূলবিন্দু থেকে সরাসরি শেষ বিন্দুতে পৌঁছায়, আর তার স্থানাঙ্ক চার এক। এটিই দেখায় যে যোগ মানে দুই ভেক্টরের অনুরূপ অংশের হিসাব।"},
            {"index": 14, "type": "p",
             "tts": "সাধারণ নিয়মে, সংখ্যার তালিকার দৃষ্টিভঙ্গিতে দুটি ভেক্টর যোগ করতে হলে তাদের একই অবস্থানের উপাদানগুলোকে পরস্পর যোগ করতে হয়।"},
            {"index": 15, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। কলাম ভেক্টর, উপরে এক্স এক আর নিচে ওয়াই এক, যোগ কলাম ভেক্টর, উপরে এক্স দুই আর নিচে ওয়াই দুই, সমান কলাম ভেক্টর, উপরে এক্স এক যোগ এক্স দুই, আর নিচে ওয়াই এক যোগ ওয়াই দুই।"},
        ],
    },

    "sec-scalar": {
        "title": "স্কেলার গুণন — প্রসারণ, সংকোচন ও বিপরীতকরণ",
        "audio_file": "sec_04_sec-scalar.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, স্কেলার গুণন, প্রসারণ, সংকোচন ও বিপরীতকরণ।"},
            {"index": 1, "type": "p",
             "tts": "ভেক্টরের অন্য মৌলিক অপারেশনটি হলো সংখ্যা দিয়ে ভেক্টরকে গুণ করা। কয়েকটি উদাহরণ দেখলে বিষয়টি সবচেয়ে সহজে বোঝা যায়। আপনি যদি সংখ্যা দুই নিয়ে কোনো ভেক্টরকে গুণ করেন, ভেক্টরটি প্রসারিত হয়ে আদি দৈর্ঘ্যের দ্বিগুণ লম্বা হয়ে যায়।"},
            {"index": 2, "type": "figure",
             "tts": "একই দিকে দুটি তীর দেখা যাচ্ছে, ছোটটি আসল ভেক্টর আর বড়টি তার দ্বিগুণ রূপ। লক্ষ্য করুন দিকের কোনো বদল নেই, শুধু দৈর্ঘ্য বেড়েছে। সংখ্যা দুই দিয়ে গুণের অর্থ ঠিক এটি, দিক অটুট রেখে মান দ্বিগুণ করা।"},
            {"index": 3, "type": "p",
             "tts": "আর যদি কোনো ভেক্টরকে এক তৃতীয়াংশ দিয়ে গুণ করেন, তবে তা সংকুচিত হয়ে আদি দৈর্ঘ্যের এক তৃতীয়াংশে দাঁড়ায়।"},
            {"index": 4, "type": "figure",
             "tts": "এখানে আসল তীরের চেয়ে ছোট এক তীর দেখানো হয়েছে, ঠিক এক তৃতীয়াংশ দৈর্ঘ্যের। দিক একই আছে, কিন্তু মান কমে গেছে। ভাবুন তো, এক তৃতীয়াংশ দিয়ে গুণ মানে ভেক্টরটিকে তিন ভাগের এক ভাগ করে নেওয়া।"},
            {"index": 5, "type": "p",
             "tts": "আর যদি আপনি ঋণাত্মক কোনো সংখ্যা, যেমন মাইনাস এক দশমিক পাঁচ দিয়ে গুণ করেন, তবে ভেক্টরটি প্রথমে বিপরীত দিকে একশো আশি ডিগ্রি ঘুরে যাবে, তারপর দেড় গুণ প্রসারিত হবে।"},
            {"index": 6, "type": "figure",
             "tts": "এখানে তীরটি উল্টে গেছে, মাথা যেদিকে ছিল এখন লেজ সেদিকে, আবার দৈর্ঘ্যও বেড়েছে। ঋণাত্মক সংখ্যা মাইনাস এক দশমিক পাঁচের দুটি কাজ, একে দিক বদলায়, অন্যে মান বাড়ায়। এই দুই কাজ একসাথেই চিত্রে দেখা যাচ্ছে।"},
            {"index": 7, "type": "p",
             "tts": "ভেক্টরকে প্রসারিত, সংকুচিত বা উল্টে দেওয়ার এই পূর্ণ প্রক্রিয়াটিকে বলা হয় স্কেলিং। যখনই দুই, এক তৃতীয়াংশ কিংবা মাইনাস এক দশমিক পাঁচের মতো কোনো সংখ্যা ভেক্টরকে এভাবে স্কেল করে, তখন সেই সংখ্যাটিকে বলা হয় স্কেলার। আসলে লিনিয়ার বীজগণিত জুড়ে সংখ্যার প্রধান কাজই হলো ভেক্টরকে স্কেল করা, তাই সাধারণ সংখ্যা আর স্কেলার শব্দ দুটিকে প্রায় সমার্থক ভাবেই ব্যবহার করা হয়।"},
            {"index": 8, "type": "p",
             "tts": "সংখ্যাতাত্ত্বিকভাবে দুই গুণ প্রসারিত মানে প্রতিটি স্থানাঙ্ক বা উপাদানকে দুই দিয়ে গুণ করা। অর্থাৎ সংখ্যার তালিকার ধারণায় কোনো ভেক্টরকে স্কেলার দিয়ে গুণ মানে তার প্রতিটি উপাদানকে আলাদাভাবে সেই স্কেলার দিয়ে গুণ করা।"},
            {"index": 9, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। দুই গুণ ভেক্টর ভি সমান দুই গুণ কলাম ভেক্টর, উপরে এক্স, নিচে ওয়াই, আর তার ফল কলাম ভেক্টর, উপরে দুই গুণ এক্স, নিচে দুই গুণ ওয়াই।"},
        ],
    },

    "sec-basis": {
        "title": "ভিত্তি ভেক্টর — আই হ্যাট ও জে হ্যাট",
        "audio_file": "sec_05_sec-basis.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, ভিত্তি ভেক্টর, আই হ্যাট ও জে হ্যাট।"},
            {"index": 1, "type": "p",
             "tts": "দ্বিমাত্রিক কার্তেসীয় তলে দুটি বিশেষ একক ভেক্টর আছে, যারা পুরো স্থানাঙ্ক ব্যবস্থার মেরুদণ্ড হিসেবে কাজ করে।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। আই হ্যাট সমান কলাম ভেক্টর, উপরে এক, নিচে শূন্য। আর জে হ্যাট সমান কলাম ভেক্টর, উপরে শূন্য, নিচে এক।"},
            {"index": 3, "type": "p",
             "tts": "যেকোনো দ্বিমাত্রিক ভেক্টরকে এই দুটির স্কেল করা রূপের যোগফল হিসেবে, অর্থাৎ রৈখিক সমন্বয় হিসেবে প্রকাশ করা যায়।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। কলাম ভেক্টর, উপরে তিন, নিচে মাইনাস দুই, সমান তিন আই হ্যাট যোগ মাইনাস দুই জে হ্যাট।"},
            {"index": 5, "type": "callout",
             "tts": "গ্রান্ট স্যান্ডারসন, অর্থাৎ থ্রি ব্লু ওয়ান ব্রাউন, সুন্দরভাবে ব্যাখ্যা করেন যে স্থানাঙ্ক আসলে কোনো পরম সত্য নয়। এটি কেবল একটি নির্দিষ্ট ভিত্তি ভেক্টর জোড়ার সাপেক্ষে স্থান পরিমাপের এক চুক্তি মাত্র। আগামী অধ্যায়ে আমরা দেখব কীভাবে এই ভিত্তি ভেক্টরগুলো পুরো দ্বিমাত্রিক ও ত্রিমাত্রিক স্থানকে তৈরি করে, অর্থাৎ স্প্যান করে।"},
            {"index": 6, "type": "p", "role": "conclusion",
             "tts": "এখন যেকোনো স্থানাঙ্ক এক্স কমা ওয়াই দিন, অথবা প্রিসেটে ক্লিক করুন, আর পর্যবেক্ষণ করুন কীভাবে আই হ্যাট আর জে হ্যাট মিলে যেকোনো ভেক্টর গড়ে তোলে।"},
        ],
    },

    "sec-conclusion": {
        "title": "উপসংহার",
        "audio_file": "sec_06_sec-conclusion.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "ষষ্ঠ পরিচ্ছেদ, উপসংহার।"},
            {"index": 1, "type": "p", "role": "conclusion",
             "tts": "পরবর্তী ভিডিওগুলোতে আপনারা আরও স্পষ্ট বুঝতে পারবেন কেন আমি বলেছিলাম, লিনিয়ার বীজগণিতের প্রতিটি বিষয় মূলত দুটি মৌলিক ক্রিয়াকলাপের চারপাশে ঘোরে, ভেক্টর যোগ আর স্কেলার গুণন। আর এই সিরিজের শেষ পর্বে আমি আরও বিস্তারিত বলব, গণিতবিদরা কীভাবে আর কেন শুধু এই অপারেশনগুলো নিয়ে ভাবেন, ভেক্টরকে আপনি যেভাবেই প্রকাশ করুন না কেন, তার রূপভেদ থেকে সম্পূর্ণ স্বাধীন ও বিমূর্তভাবে।"},
            {"index": 2, "type": "p", "role": "conclusion",
             "tts": "সত্যি বলতে, ভেক্টরকে আপনি মহাশূন্যের তীরচিহ্ন ভাবছেন যার এক সুন্দর সংখ্যাতাত্ত্বিক রূপ আছে, যেমনটা আমি পরামর্শ দিচ্ছি, নাকি সংখ্যার তালিকা ভাবছেন যার এক সুন্দর জ্যামিতিক রূপ আছে, তাতে আসলে কোনো তফাত পড়ে না। লিনিয়ার বীজগণিতের আসল শক্তি এক দৃষ্টিভঙ্গিতে সীমাবদ্ধ নয়, বরং এই দুই রূপের মাঝে স্বাচ্ছন্দ্যে রূপান্তর আর আদান প্রদান করতে পারার দক্ষতাই তার মূল বল। একজন ডেটা অ্যানালিস্টের জন্য এটি বিশাল সংখ্যার তালিকাকে চোখের সামনে ভিজ্যুয়ালাইজ করার সুযোগ দেয়, যা লুকোনো প্যাটার্ন স্পষ্ট করতে আর গাণিতিক অপারেশনের প্রভাব বুঝতে দারুণ সাহায্য করে।"},
            {"index": 3, "type": "p", "role": "conclusion",
             "tts": "অন্যদিকে পদার্থবিদ আর কম্পিউটার গ্রাফিক্স প্রোগ্রামারদের জন্য এটি এক শক্তিশালী ভাষা, যার মাধ্যমে স্পেস আর তার পরিবর্তনগুলো কম্পিউটারে হিসাব করা সংখ্যা দিয়ে নিখুঁতভাবে পরিচালনা করা যায়। উদাহরণস্বরূপ, আমি যখন এই গাণিতিক অ্যানিমেশনগুলো বানাই, প্রথমে ভাবি স্পেসের মধ্যে জ্যামিতিকভাবে ঠিক কী ঘটছে, তারপর কম্পিউটার দিয়ে তা সংখ্যায় রূপান্তর করি, যাতে স্ক্রিনের ঠিক কোন পিক্সেল কোথায় জ্বলবে তা বের করা যায়। আর এটি নিখুঁতভাবে করার জন্যই লিনিয়ার বীজগণিতের গভীর বোঝাপড়ার ওপর ভরসা করতে হয়।"},
            {"index": 4, "type": "p", "role": "conclusion",
             "tts": "তো এই ছিল ভেক্টরের একেবারে মৌলিক ভিত্তি। পরবর্তী ভিডিওতে আমরা শুরু করব ভেক্টরের চারপাশের কয়েকটি অসাধারণ ধারণা, যেমন স্প্যান, ভিত্তি ভেক্টর, আর রৈখিক নির্ভরতা নিয়ে।"},
        ],
    },
}

# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")


def assert_clean_scripts():
    """Fail before any TTS work if a script still contains markup or Latin text."""
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars {bad!r} in {cue['tts']!r}")

    # Structural parity guards.
    if len(SECTIONS_DATA) != 6:
        raise ValueError("Expected exactly 6 sections")
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
    if total != 73:
        raise ValueError(f"Expected 73 cues, found {total}")


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
        "course": "linear_algebra",
        "lesson": "lesson_01",
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
    assert len(loaded["sections"]) == 6
    total_cues = 0
    total_ms = 0.0
    figures = 0
    for sec_id, msec in loaded["sections"].items():
        assert len(msec["cues"]) == len(EXPECTED_TYPES[sec_id])
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    assert total_cues == 73

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Lesson 01")
    for sec_id, msec in loaded["sections"].items():
        print(f"  {sec_id:<20} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 6 sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json is valid JSON; all 6 mp3 files exist and are non-empty.")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(build_all())
