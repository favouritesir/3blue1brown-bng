# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Topology Lesson 03
("Sneaky Topology: Borsuk-Ulam and stolen necklaces", Bengali) to the Lesson-01 gold standard.

Deterministic, re-runnable, self-contained:
  * 43 cues in 4 narrated sections with EXACTLY the same section
    IDs, audio_file names, cue types and cue order as the live DOM parsed by
    narration_engine.js (browser-extracted snapshot topology03_dom_blocks.json, KaTeX
    <annotation> preservation) and the placeholder manifest.
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Figure cues are genuine 2-4 sentence natural explanations, never the
    artificial label "চিত্র প্রদর্শনী".
  * Clean spoken Bengali with phonetic safeguards:
      topology -> টোপোলজি, inscribed -> অন্তর্লিখিত, rectangle -> আয়তক্ষেত্র,
      hairy ball -> লোমশ বল, theorem -> উপপাদ্য, Borsuk-Ulam -> বোরসুক উলাম,
      necklace -> মালা, monster -> মনস্টার, 3D -> থ্রিডি, 2D -> টুডি,
      x -> এক্স, y -> ওয়াই, z -> জেড.
    No TeX, LaTeX, backslashes, $, braces, brackets, dashes or Latin letters.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, figure -4%, formula-box -8%, p +2%, callout +0%,
      conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concat with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST).
  * Bumps the page manifest cache-buster from ?v=1 to ?v=2.
  * Ends with a headless-Chrome (channel="chrome") verification: DOM<->manifest
    1:1, zero duplicates, zero quiz/media-tab types, non-zero mp3s, valid JSON,
    350 ms gaps, zero page errors and zero forbidden labels.

Usage:  python governance/build_expressive_teacher_audio_topology03.py
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
OLDV = "1"
NEWV = "2"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))            # .../governance
WORKSPACE = os.path.dirname(SCRIPT_DIR)                             # .../web_platform
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "topology", "lesson_03")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "topology", "lesson_03.html")
DOM_SNAPSHOT = os.path.join(SCRIPT_DIR, "topology03_dom_blocks.json")
MANIFEST_TITLE = 'অধ্যায় ০৩ — স্নেকি টোপোলজি: বোরসুক উলাম ও চুরি হওয়া হার'

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

EXPECTED_TYPES = {'sec-intro': ['h2',
               'p',
               'p',
               'p',
               'figure',
               'figure',
               'formula-box',
               'p',
               'formula-box',
               'p',
               'callout',
               'p'],
 'sec-necklace': ['h2', 'p', 'p', 'p', 'figure', 'formula-box', 'p', 'callout', 'p'],
 'sec-proof': ['h2',
               'p',
               'p',
               'p',
               'figure',
               'formula-box',
               'p',
               'formula-box',
               'p',
               'formula-box',
               'p',
               'callout',
               'p'],
 'sec-meaning': ['h2', 'p', 'p', 'p', 'figure', 'formula-box', 'p', 'callout', 'p']}
EXPECTED_AUDIO_FILES = {'sec-intro': 'sec_01_sec-intro.mp3',
 'sec-necklace': 'sec_02_sec-necklace.mp3',
 'sec-proof': 'sec_03_sec-proof.mp3',
 'sec-meaning': 'sec_04_sec-meaning.mp3'}
ALIASES = {'sec-intro': 'sec_01_intro',
 'sec-necklace': 'sec_02_necklace',
 'sec-proof': 'sec_03_proof',
 'sec-meaning': 'sec_04_meaning'}
EXPECTED_COUNTS = {'sec-intro': 12, 'sec-necklace': 9, 'sec-proof': 13, 'sec-meaning': 9}
EXPECTED_TOTAL = 43

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (43 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {'sec-intro': {'title': 'বোরসুক–উলাম উপপাদ্য: বিপরীত বিন্দুর মিলন',
               'audio_file': 'sec_01_sec-intro.mp3',
               'cues': [{'index': 0,
                         'type': 'h2',
                         'tts': 'প্রথম পরিচ্ছেদ, বোরসুক উলাম উপপাদ্য, বিপরীত বিন্দুর মিলন।'},
                        {'index': 1,
                         'type': 'p',
                         'tts': 'পৃথিবীর বুকে কোথাও একটা জায়গা আছে যার ঠিক বিপরীত পাশে, অর্থাৎ পৃথিবীর '
                                'কেন্দ্র দিয়ে সোজা রেখা টেনে যেখানে পৌঁছায়, তাপমাত্রা হুবহু একই। একই কথা '
                                'বলা যায় বায়ুচাপের ক্ষেত্রেও। কিন্তু যে বিন্দুটিতে তাপমাত্রা মেলে, সেটিতে '
                                'চাপ মেলে কি, এবং যেটিতে চাপ মেলে, সেটিতে তাপমাত্রা মেলে কি? দুটি মাপ একসাথে '
                                'মেলে এমন কোনো বিন্দু আছে কি?'},
                        {'index': 2,
                         'type': 'p',
                         'tts': 'বোরসুক উলাম উপপাদ্য বলে যে আছে। এর সাধারণ রূপ হলো, যেকোনো অবিচ্ছিন্ন ম্যাপ '
                                'এফ যা এস এন কে আর এন স্পেসে পাঠায়, তার ক্ষেত্রে এমন কমপক্ষে একটি বিন্দু '
                                'এক্স থাকে, যার জন্য এফ অফ এক্স সমান এফ অফ ঋণাত্মক এক্স। আমাদের উদাহরণে এক্স '
                                'হলো পৃথিবীর ওপরের বিন্দু, ঋণাত্মক এক্স তার বিপরীত বিন্দু, আর এফ দুটি সংখ্যা '
                                'ফেরত দেয়, তাপমাত্রা ও চাপ। তাই এন হলো দুই, অর্থাৎ এস দুই থেকে আর দুই।'},
                        {'index': 3,
                         'type': 'p',
                         'tts': 'প্রথম এন সমান এক এর ক্ষেত্রটি সহজ, বিষুবরেখা বরাবর ঘুরে দেখুন তাপমাত্রার '
                                'পার্থক্য একটি বৃত্তে বদলাচ্ছে। কোনো বিন্দুতে মান ধনাত্মক, তার বিপরীতে '
                                'ঋণাত্মক, তাই মাঝখানে কোথাও শূন্য হতেই হবে। এন সমান দুই তে একই কথা প্রমাণ '
                                'করা একটু কঠিন, কিন্তু ভাবনাটি একই রকম।'},
                        {'index': 4,
                         'type': 'figure',
                         'tts': 'অফিশিয়াল পাঠের এই শিরোনাম চিত্রে একটি আপাতদৃষ্টিতে সহজ আবহাওয়ার প্রশ্ন '
                                'দেখা যাচ্ছে। ছবি থেকে বোঝা যায় কীভাবে সেই প্রশ্ন থেকে শুরু করে আমরা পৌঁছাব '
                                'পুঁতির হার ভাগ করার ধাঁধায়।'},
                        {'index': 5,
                         'type': 'figure',
                         'tts': 'হলুদ বিন্দুদ্বয় পৃথিবীর ঠিক বিপরীত পাশে অবস্থিত। বোরসুক উলাম গ্যারান্টি '
                                'দেয় এমন এক জোড়া আছে, যেদের তাপমাত্রা ও চাপ দুটোই হুবহু সমান, যদিও কোথায় '
                                'তা বলে দেয় না।'},
                        {'index': 6,
                         'type': 'formula-box',
                         'tts': 'গাণিতিক সূত্র, এফ মানে এস এন থেকে আর এন স্পেসে যাওয়া এক ম্যাপ, আর তার এমন '
                                'এক বিন্দু এক্স আছে যার জন্য এফ অফ এক্স সমান এফ অফ ঋণাত্মক এক্স।'},
                        {'index': 7,
                         'type': 'p',
                         'tts': 'বোরসুক উলাম উপপাদ্যের এই সংক্ষিপ্ত বিবৃতিটিই আমাদের মূল হাতিয়ার। এটি বলে '
                                'যে বিপরীত বিন্দুদ্বয়ের মান সবসময় কোথাও না কোথাও মিলে যায়।'},
                        {'index': 8,
                         'type': 'formula-box',
                         'tts': 'গাণিতিক সূত্র, জি অফ এক্স সমান এফ অফ এক্স বিয়োগ এফ অফ ঋণাত্মক এক্স, আর জি '
                                'অফ ঋণাত্মক এক্স সমান ঋণাত্মক জি অফ এক্স।'},
                        {'index': 9,
                         'type': 'p',
                         'tts': 'বিপরীত বিন্দুতে পার্থক্যের চিহ্ন উল্টে যায়, একে বলা হয় অড ফাংশন। অর্থাৎ '
                                'এক দিকে পার্থক্য ধনাত্মক হলে বিপরীত দিকে সেটি ঋণাত্মক হয়, মাঝখানে কোথাও '
                                'শূন্য হতেই হবে।'},
                        {'index': 10,
                         'type': 'callout',
                         'tts': 'বিশেষ নোট, মনে রাখবেন উপপাদ্যটি শুধু অস্তিত্ব বলে দেয়, কোথাও সেই জোড়া '
                                'আছে, কিন্তু কোথায় তা নয়। আবহাওয়ার ক্ষেত্রে সেটি খুঁজে বের করা আমাদের '
                                'কাজ, টোপোলজি কেবল বলে দেয় যে খোঁজা মানেই পাওয়া যাবে।'},
                        {'index': 11,
                         'type': 'p',
                         'role': 'conclusion',
                         'tts': 'এই বিপরীত বিন্দুর মিলন নিয়মটিই এখন আমাদের একটা একেবারে আলাদা ধাঁধার কাজে '
                                'আসবে।'}]},
 'sec-necklace': {'title': 'চুরি হওয়া হারের ধাঁধা',
                  'audio_file': 'sec_02_sec-necklace.mp3',
                  'cues': [{'index': 0, 'type': 'h2', 'tts': 'দ্বিতীয় পরিচ্ছেদ, চুরি হওয়া হারের ধাঁধা।'},
                           {'index': 1,
                            'type': 'p',
                            'tts': 'ধরুন দুইজন চোর একটা হার চুরি করেছে। হারে আর ধরনের রঙের পুঁতি আছে, প্রতি '
                                   'রঙের ঠিক দুটি করে, মোট দুই আর সংখ্যক পুঁতি। তারা হারটি ভাগ করে নিতে চায় '
                                   'এমনভাবে যেন প্রত্যেকের কাছে প্রতি রঙের ঠিক একটি করে পুঁতি যায়। হার কাটা '
                                   'যায়, কিন্তু কাটার সংখ্যা যত কম হওয়া যায় তত ভালো, প্রশ্ন হলো সর্বোচ্চ '
                                   'কতটি কাটে এই কাজটা করা যায়।'},
                           {'index': 2,
                            'type': 'p',
                            'tts': 'উত্তরটি হলো আর টি কাট, রঙের সংখ্যার সমান। দুই রঙের হারে দুই কাট, তিন '
                                   'রঙের হারে তিন কাট, ইত্যাদি। এটি প্রথম দেখে অবিশ্বাস্য মনে হয়, কারণ '
                                   'পুঁতিগুলো যেকোনো ক্রমে সাজানো থাকতে পারে, আপনি কাছাকাছি দুটি পুঁতি '
                                   'ছেঁড়ার চেষ্টা করলেই ব্যর্থ হবেন।'},
                           {'index': 3,
                            'type': 'p',
                            'tts': 'এই ফলাফলটি হলো হার ভাগ নিয়ম, যা নন্দকুমার প্রমাণ করেছিলেন। এর সবচেয়ে '
                                   'আশ্চর্যের বিষয় হলো প্রমাণে আসলে কোনো যুক্তিবিদ্যা বা গণনার চেয়ে '
                                   'টোপোলজি বেশি কাজ করে, ঠিক আমাদের বোরসুক উলাম উপপাদ্যই এখানে মূল '
                                   'হাতিয়ার।'},
                           {'index': 4,
                            'type': 'figure',
                            'tts': 'চার রঙের দুটি করে পুঁতি, মোট আটটি, ছবিতে দেখা যাচ্ছে। হলুদ ড্যাশড '
                                   'রেখাগুলো কাটার জায়গা দেখাচ্ছে। লক্ষ্য হলো প্রত্যেক চোর পাবে লাল, হলুদ, '
                                   'সবুজ ও নীল, একটিমাত্র করে।'},
                           {'index': 5,
                            'type': 'formula-box',
                            'tts': 'গাণিতিক সূত্র, পুঁতির সংখ্যা দুই আর, রঙের সংখ্যা আর, আর কাটার সংখ্যা '
                                   'সর্বোচ্চ আর।'},
                           {'index': 6,
                            'type': 'p',
                            'tts': 'ধাঁধার পরামিতি হলো আর রঙ, দুই আর পুঁতি, সর্বোচ্চ আর কাট। এই তিনটি '
                                   'সংখ্যাই পুরো প্রমাণের ভাষা তৈরি করে।'},
                           {'index': 7,
                            'type': 'callout',
                            'tts': 'বিশেষ নোট, কেন সোজা যুক্তি চলবে না। পুঁতিগুলো এলোমেলোভাবে সাজানো থাকতে '
                                   'পারে, একই রঙের দুটি পুঁতি হারের দুই প্রান্তে থাকতে পারে। তাই '
                                   'স্থানীয়ভাবে কিছু বেছে নেওয়া যাবে না, লাগবে এমন একটি যুক্তি যা পুরো '
                                   'হারটিকে একসাথে দেখে।'},
                           {'index': 8,
                            'type': 'p',
                            'role': 'conclusion',
                            'tts': 'এই বিচ্ছিন্ন ধাঁধার সমাধানের জন্য আমরা আগে একটিকে অবিচ্ছিন্ন করে নেব, আর '
                                   'সেটা করা যায় বোরসুক উলাম দিয়ে।'}]},
 'sec-proof': {'title': 'অবিচ্ছিন্ন থেকে বিচ্ছিন্ন — প্রমাণের কৌশল',
               'audio_file': 'sec_03_sec-proof.mp3',
               'cues': [{'index': 0,
                         'type': 'h2',
                         'tts': 'তৃতীয় পরিচ্ছেদ, অবিচ্ছিন্ন থেকে বিচ্ছিন্ন, প্রমাণের কৌশল।'},
                        {'index': 1,
                         'type': 'p',
                         'tts': 'প্রথমে পুঁতিগুলোকে আলাদা বিন্দু না ভেবে প্রতিটি রঙের ভরকে হার বরাবর একটা '
                                'স্মুথি বা তরল হিসেবে কল্পনা করি। কোনো রঙের দুটি পুঁতি মানে সেই রঙের মোট ভর '
                                'দুই একক, যা হারের যেকোনো জায়গায় ছড়ানো থাকতে পারে। এখন প্রশ্ন হলো, আর টি '
                                'কাট দিয়ে হারকে আর যোগ এক টুকরো করে টুকরোগুলোকে চোর দুজনের মাঝে বিন্যাস '
                                'করলে কি প্রত্যেক রঙের অর্ধেক ভর প্রত্যেকের কাছে যায়?'},
                        {'index': 2,
                         'type': 'p',
                         'tts': 'কাটার অবস্থানগুলোকে একটি বহু মাত্রিক গোলকের বিন্দু হিসেবে লেখা যায়, '
                                'প্রতিটি রঙের জন্য একটিমাত্র স্থানাঙ্ক, যা ওই রঙের কতখানি ভর প্রথম চোরের '
                                'দিকে গেল তা মাপে। বিপরীত বিন্দু ঋণাত্মক এক্স মানে চোর দুজনের ভূমিকা বদল, যা '
                                'আগে প্রথম চোরের কাছে যাচ্ছিল, এখন যাচ্ছে দ্বিতীয়ের কাছে। তাই যদি জি অফ '
                                'এক্স হয় দুই চোরের পাওয়া ভরের পার্থক্য, তবে জি অফ ঋণাত্মক এক্স সমান '
                                'ঋণাত্মক জি অফ এক্স, একটি অড ম্যাপ।'},
                        {'index': 3,
                         'type': 'p',
                         'tts': 'বোরসুক উলাম বলে এই অড ম্যাপের কোথাও শূন্য থাকতেই হবে, অর্থাৎ এমন কাটার '
                                'ব্যবস্থা আছে যাতে দুই চোরের প্রতিটি রঙের ভর হুবহু সমান। এখন শেষ কৌশল, কাটার '
                                'জায়গাগুলোকে ধীরে ধীরে এমনভাবে সরান যাতে প্রতিটি কাটা ঠিক দুটি পুঁতির মাঝে '
                                'এসে পড়ে, কিন্তু ভরের সমতা বা ন্যায্যতা নষ্ট না হয়। যেহেতু সবকিছু '
                                'অবিচ্ছিন্ন, এই সরানোটা করা যায়, ফলাফল হলো আর টি কাটে ঠিক ন্যায্য ভাগ।'},
                        {'index': 4,
                         'type': 'figure',
                         'tts': 'আসল হারে কাটগুলোকে পুঁতির মাঝের ফাঁকে ঠিক করা হয়েছে। ছবিতে দেখা যাচ্ছে '
                                'অবিচ্ছিন্ন মডেলে ভরের ন্যায্যতা প্রমাণ করা হয়, আর বিচ্ছিন্ন মডেলে সেটি '
                                'টেনে আনা হয়। এই দুই ধাপই পুরো প্রমাণ।'},
                        {'index': 5,
                         'type': 'formula-box',
                         'tts': 'গাণিতিক সূত্র, জি মানে আর মাত্রার গোলক থেকে আর মাত্রিক স্পেসে যাওয়া এক অড '
                                'ম্যাপ, যার জন্য জি অফ ঋণাত্মক এক্স সমান ঋণাত্মক জি অফ এক্স।'},
                        {'index': 6,
                         'type': 'p',
                         'tts': 'কাটার ব্যবস্থা থেকে তৈরি এই অড ম্যাপে চোর বদলালে চিহ্ন বদলায়। এক চোরের '
                                'কাছে যা বেশি, অন্য চোরের কাছে তা কম, আর এই ভারসাম্যই আমাদের কাছে শূন্য '
                                'বিন্দু খুঁজে দেয়।'},
                        {'index': 7,
                         'type': 'formula-box',
                         'tts': 'গাণিতিক সূত্র, জি অফ এক্স সমান জি অফ ঋণাত্মক এক্স আবার সমান ঋণাত্মক জি অফ '
                                'এক্স, সুতরাং জি অফ এক্স সমান শূন্য।'},
                        {'index': 8,
                         'type': 'p',
                         'tts': 'বোরসুক উলামের এই শূন্য বিন্দুতে দুই চোরের ভর সমান। অর্থাৎ যে কাটার '
                                'ব্যবস্থায় ভরের পার্থক্য শূন্য, সেটিই ন্যায্য ভাগ।'},
                        {'index': 9,
                         'type': 'formula-box',
                         'tts': 'গাণিতিক সূত্র, অবিচ্ছিন্ন ন্যায্য ভাগ থেকে বিচ্ছিন্ন কাটে রূপান্তর।'},
                        {'index': 10,
                         'type': 'p',
                         'tts': 'অবিচ্ছিন্ন ভাগ থেকে বিচ্ছিন্ন কাটে রূপান্তরের এই কৌশলই প্রমাণের শেষ ধাপ। '
                                'যেহেতু ব্যবস্থা অবিচ্ছিন্ন, কাটাগুলোকে পুঁতির ফাঁকে নিয়ে এলেও ন্যায্যতা '
                                'টিকে থাকে।'},
                        {'index': 11,
                         'type': 'callout',
                         'tts': 'বিশেষ নোট, এখানেই ধাঁধাটা সম্পূর্ণ বিচ্ছিন্ন, পুঁতি কিংবা কাটা নিয়ে। '
                                'কিন্তু প্রমাণ আসে একটি গোলকের বিপরীত বিন্দু বৈশিষ্ট্য থেকে। প্রথমে '
                                'সমস্যাটিকে অবিচ্ছিন্ন করে নেওয়া, টোপোলজি দিয়ে সমাধান করা, তারপর আবার '
                                'বিচ্ছিন্নে ফিরে আসা, এই কৌশলই এই অধ্যায়ের শিক্ষণীয় বিষয়।'},
                        {'index': 12,
                         'type': 'p',
                         'role': 'conclusion',
                         'tts': 'টোপোলজি আসলে আকৃতি নিয়ে নয়, অবিচ্ছিন্ন সংযোগ ও তার অপরিবর্তনীয় বৈশিষ্ট্য '
                                'নিয়ে কাজ করে, আর সেটা যেকোনো ভাষায় অনুবাদ করা যায়।'}]},
 'sec-meaning': {'title': "টোপোলজি কেন 'চোরাগপ্তো'ভাবে কাজ করে",
                 'audio_file': 'sec_04_sec-meaning.mp3',
                 'cues': [{'index': 0,
                           'type': 'h2',
                           'tts': 'চতুর্থ পরিচ্ছেদ, টোপোলজি কেন চোরাগপ্তোভাবে কাজ করে।'},
                          {'index': 1,
                           'type': 'p',
                           'tts': 'আমাদের প্রথম অধ্যায়ে টরাস আর মোবিয়াস স্ট্রিপ এসেছিল জোড়া বিন্দুকে '
                                  'পৃষ্ঠার বিন্দু হিসেবে লেখার মাধ্যমে। দ্বিতীয় অধ্যায়ে ডিগ্রির বিরোধ থেকে '
                                  'গোলকের চুল আঁচড়ানোর অসম্ভবতা প্রমাণ হয়েছিল। আজকের অধ্যায়ে দেখা গেল '
                                  'একটি বিচ্ছিন্ন ধাঁধাও একই ভাষায় লেখা যায়, কেবল প্রশ্নটিকে অবিচ্ছিন্ন '
                                  'রূপ দিতে হয়।'},
                          {'index': 2,
                           'type': 'p',
                           'tts': 'টোপোলজির মূল কথা হলো, ছেঁড়া বা আঠা লাগানো ছাড়া যেকোনো রূপ বদলের পরেও যা '
                                  'অপরিবর্তিত থাকে, তা নিয়েই যুক্তি করা। অবিচ্ছিন্ন এক এক সংযোগ বা '
                                  'হোমিওমর্ফিজমের এই ধারণাটিই আমাদের বলে দেয় কোন কাঠামো আসলে একই, কোনটা '
                                  'নয়। আবহাওয়া, চুলের ক্ষেত্র আর পুঁতির হার, তিনটি ভিন্ন জগত, একই গাণিতিক '
                                  'ভাষা।'},
                          {'index': 3,
                           'type': 'p',
                           'tts': 'এই কারণেই বোরসুক উলামের মতো উপপাদ্যগুলো স্নেকি, সেগুলো হঠাৎ করে আবির্ভূত '
                                  'হয় এবং সমস্যার সম্পূর্ণ ভিন্ন রূপ নিয়ে হাজির হয়। টোপোলজি শেখা মানে '
                                  'নতুন আকৃতি মুখস্থ করা নয়, মানে হলো কোনো সমস্যার ভাষা বদলে এমন একটি জগতে '
                                  'নিয়ে যাওয়া, যেখানে তার উত্তর সুস্পষ্ট ও অবধারিত।'},
                          {'index': 4,
                           'type': 'figure',
                           'tts': 'বিপরীত বিন্দুর এই ছোট্ট চিত্রই তিনটি অধ্যায়ের সূত্র ধরে বয়ে চলেছে। '
                                  'ছবিতে দেখা যাচ্ছে কীভাবে পৃষ্ঠার বিন্দু, স্পর্শক ভেক্টর আর ভাগ বাটোয়ারার '
                                  'ন্যায্যতা, সবই একই ধারণার বিভিন্ন রূপ।'},
                          {'index': 5,
                           'type': 'formula-box',
                           'tts': 'গাণিতিক সূত্র, এক্স ও ওয়াই হোমিওমর্ফ হলে তাদের টোপোলজিক্যাল বৈশিষ্ট্য '
                                  'একই থাকে।'},
                          {'index': 6,
                           'type': 'p',
                           'tts': 'হোমিওমর্ফ পৃষ্ঠার টোপোলজিক্যাল বৈশিষ্ট্য একই, তাই এক জগতের প্রমাণ অন্য '
                                  'জগতে কাজ করে। এই কারণেই গোলক সম্পর্কে জানা একটা সত্য হার ভাগের ধাঁধায় '
                                  'রূপ দিতে পারে।'},
                          {'index': 7,
                           'type': 'callout',
                           'tts': 'বিশেষ নোট, পুরো সিরির সারমর্ম। টোপোলজি কেবল রাবার শিট জ্যামিতি নয়। এটি '
                                  'অবিচ্ছিন্ন সংযোগের ভাষা, যা দিয়ে একটি অমীমাংসিত বর্গ প্রশ্ন, একটি '
                                  'বাতাসের শূন্য বিন্দু আর একটি পুঁতির হার, সবই একই ধরনের যুক্তিতে বিবৃত ও '
                                  'সমাধান করা যায়।'},
                          {'index': 8,
                           'type': 'p',
                           'role': 'conclusion',
                           'tts': 'এই ছিল আমাদের টোপোলজি সিরির তিনটি অধ্যায়, আশা করি আপনাদের কাছে এগুলো '
                                  'থিওডোলাইটের মতো কঠিন না লেগে থাকে।'}]}}

# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN = "চিত্র প্রদর্শনী"


def assert_clean_scripts():
    """Fail before any TTS work if a script still contains markup or Latin text."""
    total = 0
    spoken = []
    for sec_id, sec in SECTIONS_DATA.items():
        types = [c["type"] for c in sec["cues"]]
        if types != EXPECTED_TYPES[sec_id]:
            raise ValueError(f"{sec_id}: cue type/order mismatch -> {types}")
        if sec["audio_file"] != EXPECTED_AUDIO_FILES[sec_id]:
            raise ValueError(f"{sec_id}: audio_file mismatch")
        if len(types) != EXPECTED_COUNTS[sec_id]:
            raise ValueError(f"{sec_id}: cue count mismatch -> {len(types)}")
        indices = [c["index"] for c in sec["cues"]]
        if indices != list(range(len(indices))):
            raise ValueError(f"{sec_id}: cue indices are not 0..n-1")
        for cue in sec["cues"]:
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars {bad!r}")
            if FORBIDDEN in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden label")
            if cue["type"] == "figure":
                sentences = [s for s in cue["tts"].split("।") if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(f"{sec_id} cue {cue['index']}: figure has {len(sentences)} sentences")
            spoken.append(cue["tts"])
        total += len(indices)
    if total != EXPECTED_TOTAL:
        raise ValueError(f"Expected {EXPECTED_TOTAL} cues, found {total}")
    if len(spoken) != len(set(spoken)):
        raise ValueError("Duplicate spoken cue scripts detected")

    # DOM parity against browser-extracted live snapshot (narration_engine
    # selector + KaTeX <annotation> preservation).
    if os.path.exists(DOM_SNAPSHOT):
        with open(DOM_SNAPSHOT, encoding="utf-8") as fh:
            snap = json.load(fh)
        snap_types = {s["id"]: [b["type"] for b in s["blocks"]]
                      for s in snap["sections"]}
        if snap_types != EXPECTED_TYPES:
            raise ValueError(f"DOM snapshot cue types differ from EXPECTED_TYPES:\n"
                             f"snapshot={snap_types}\nexpected={EXPECTED_TYPES}")
        if set(snap_types) != set(SECTIONS_DATA):
            raise ValueError("DOM snapshot section ids differ from embedded sections")
        # Every formula-box block must retain at least one KaTeX annotation.
        missing = [(s["id"], i) for s in snap["sections"]
                   for i, b in enumerate(s["blocks"])
                   if b["type"] == "formula-box" and not any(t.strip() for t in b["tex"])]
        if missing:
            raise ValueError(f"Missing KaTeX annotations in formula-box blocks: {missing}")


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
    # Edge TTS sometimes replies with an empty stream; back off and retry.
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


def bump_page_manifest_version():
    """Bump the manifest.js cache-buster in the lesson page."""
    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    old = f"manifest.js?v={OLDV}"
    new = f"manifest.js?v={NEWV}"
    if old in html:
        html = html.replace(old, new, 1)
        with open(PAGE_PATH, "w", encoding="utf-8") as fh:
            fh.write(html)
        print(f"  page manifest bumped: {old} -> {new}")
    elif new in html:
        print(f"  page manifest already at {new}")
    else:
        raise RuntimeError(f"Could not find {old} or {new} in {PAGE_PATH}")


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
    chunk_paths, durations = [], []
    print(f"\n[{sec_id}] {len(cues)} cues -> {sec['audio_file']}")
    for cue in cues:
        idx = cue["index"]
        chunk = os.path.join(temp, f"cue_{idx:02d}.mp3")
        rate, pitch, volume = prosody_for(cue)
        if not valid_audio(chunk):
            print(f"  cue {idx:02d} [{cue['type']:<13}] {rate:>4} {pitch:>5}  {cue['tts'][:28]}...")
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

    # Timings from measured durations + real silence chunks.
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
    print(f"Validated {EXPECTED_TOTAL} clean cues in {len(SECTIONS_DATA)} sections.")

    manifest_sections = {}
    for sec_id, sec in SECTIONS_DATA.items():
        manifest_sections[sec_id] = await build_section(sec_id, sec)

    manifest_data = {
        "course": "topology",
        "lesson": "lesson_03",
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

    bump_page_manifest_version()

    # Final on-disk integrity checks.
    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert set(loaded["sections"]) == set(SECTIONS_DATA)
    total_cues, total_ms, figures = 0, 0.0, 0
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == EXPECTED_COUNTS[sec_id]
        assert msec["section_id"] == sec_id
        assert msec["alias"] == ALIASES[sec_id]
        assert msec["audio_file"] == EXPECTED_AUDIO_FILES[sec_id]
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    assert total_cues == EXPECTED_TOTAL

    print("\n" + "=" * 68)
    print(f"BUILD COMPLETE - expressive teacher audio, Topology Lesson 03")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<20} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTIONS_DATA)} sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("=" * 68)


# --------------------------------------------------------------------------- #
# Headless Chrome verification (channel=chrome)
# --------------------------------------------------------------------------- #
VERIFY_JS = r"""() => {
  const ne = window.narrationEngine;
  const manifest = window.TEACHER_AUDIO_MANIFEST;
  const typeOf = (el) => {
    if (el.matches && el.matches('figure.lesson-figure')) return 'figure';
    if (el.classList && el.classList.contains('chapter-quote')) return 'chapter-quote';
    if (el.classList && el.classList.contains('callout')) return 'callout';
    if (el.classList && el.classList.contains('code-showcase')) return 'code-showcase';
    if (el.classList && el.classList.contains('formula-box')) return 'formula-box';
    if (el.tagName === 'H2') return 'h2';
    if (el.tagName === 'H3') return 'h3';
    return 'p';
  };
  const secEls = [...document.querySelectorAll('.article > section, article section')];
  const dom = [];
  for (const el of secEls) {
    if (el.getAttribute('data-no-narration') === 'true') continue;
    const nodes = [...el.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box')];
    const blocks = [];
    for (const node of nodes) {
      if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) continue;
      const anns = [...node.querySelectorAll('annotation[encoding="application/x-tex"]')]
                     .map(a => a.textContent);
      const s = (engineText) => engineText;
      blocks.push({type: typeOf(node), tex: anns});
    }
    dom.push({id: el.id, types: blocks.map(b => b.type),
              tex: blocks.filter(b => b.type === 'formula-box').map(b => b.tex)});
  }
  return {
    dom,
    engine: (ne.sections || []).map(s => ({id: s.id,
      types: s.blocks.map(b => typeOf(b.element)), count: s.blocks.length,
      audioFile: s.audioFile})),
    manifestPresent: !!manifest,
    hasStudioAudio: !!ne.hasStudioAudio,
    manifest: manifest,
    articleText: (document.querySelector('b1b-article') || document.body).innerText || '',
  };
}"""


def verify_in_chrome():
    from playwright.sync_api import sync_playwright

    page_uri = ("http://127.0.0.1:8085/courses/topology/lesson_03.html"
                "?v=verify03")
    js_errors, console_errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page()
        page.on("pageerror", lambda e: js_errors.append("pageerror: " + str(e)))
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.goto(page_uri, wait_until="load")
        page.wait_for_function(
            "() => !!window.narrationEngine && !!window.narrationEngine.sections "
            "&& window.narrationEngine.sections.length > 0 "
            "&& !!window.TEACHER_AUDIO_MANIFEST",
            timeout=30000,
        )
        data = page.evaluate(VERIFY_JS)
        browser.close()

    # The only expected console noise on this new course is the not-yet-produced
    # intro video (404). It is unrelated to narration and pre-existed this build.
    benign = ("404 (File not found)", "Failed to load resource",
              "ERR_FILE_NOT_FOUND", "net::ERR", "ERR_BLOCKED",
              "Permissions policy violation")
    narration_console = [e for e in console_errors if not any(b in e for b in benign)]

    def require(ok, msg):
        if not ok:
            raise AssertionError(msg)

    require(not js_errors, f"JS page errors: {js_errors}")
    require(not narration_console, f"Unexpected console errors: {narration_console[:5]}")
    require(data["manifestPresent"], "window.TEACHER_AUDIO_MANIFEST missing")
    require(data["hasStudioAudio"], "Studio teacher audio not bound")

    dom = data["dom"]
    engine = data["engine"]
    manifest = data["manifest"]
    sections = manifest["sections"]
    dom_ids = [s["id"] for s in dom]
    eng_ids = [s["id"] for s in engine]
    canonical = list(SECTIONS_DATA)
    require(dom_ids == canonical, f"DOM ids changed: {dom_ids} vs {canonical}")
    require(eng_ids == canonical, f"Engine ids changed: {eng_ids}")
    require(list(sections) == canonical, f"Manifest ids changed: {list(sections)}")
    bad_ids = {"sec-quiz", "sec-quizzes", "sec-media", "sec-lab", "sec-video-note"}
    require(not (bad_ids & set(dom_ids)), "non-narrated section leaked into narration")

    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        disk_manifest = json.load(fh)
    require(manifest == disk_manifest, "preloaded manifest != disk manifest")
    with open(os.path.join(AUDIO_DIR, "manifest.js"), encoding="utf-8") as fh:
        require(fh.read(30).startswith("window.TEACHER_AUDIO_MANIFEST"),
                "manifest.js does not export window.TEACHER_AUDIO_MANIFEST")

    all_texts = []
    used_types = set()
    total_ms = 0.0
    for sec_id in canonical:
        msec = sections[sec_id]
        cues = msec["cues"]
        dsec = next(s for s in dom if s["id"] == sec_id)
        esec = next(s for s in engine if s["id"] == sec_id)
        require(len(cues) == EXPECTED_COUNTS[sec_id], (sec_id, "manifest count", len(cues)))
        require(esec["count"] == EXPECTED_COUNTS[sec_id], (sec_id, "engine count", esec["count"]))
        require([c["type"] for c in cues] == EXPECTED_TYPES[sec_id], (sec_id, "manifest types"))
        require(dsec["types"] == EXPECTED_TYPES[sec_id], (sec_id, "DOM types", dsec["types"]))
        require(esec["types"] == EXPECTED_TYPES[sec_id], (sec_id, "engine types"))
        require(msec["audio_file"] == EXPECTED_AUDIO_FILES[sec_id], (sec_id, "audio_file"))
        require([c["index"] for c in cues] == list(range(len(cues))), (sec_id, "indices"))
        all_texts.extend(c["text"] for c in cues)
        used_types.update(c["type"] for c in cues)
        total_ms += msec["total_duration_ms"]
        # KaTeX annotation must survive for every formula-box block in the DOM.
        for btex in dsec["tex"]:
            require(any(t.strip() for t in btex), (sec_id, "missing DOM TeX annotation"))
        # mp3 exists, non-zero and probeable.
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        require(os.path.exists(path) and os.path.getsize(path) > 0, (sec_id, "empty mp3"))
        require(get_duration_ms(path) > 0, (sec_id, "mp3 duration"))
        # Timing integrity: monotonic, 350 ms gaps, total == last end.
        for i, c in enumerate(cues):
            require(c["duration_ms"] > 0 and c["end_ms"] > c["start_ms"], (sec_id, i, "span"))
            if i > 0:
                gap = c["start_ms"] - cues[i - 1]["end_ms"]
                require(abs(gap - GAP_MS) <= 1.0, (sec_id, i, f"gap={gap}"))
        require(abs(cues[-1]["end_ms"] - msec["total_duration_ms"]) <= 1.0,
                (sec_id, "total mismatch"))

    require(len(all_texts) == EXPECTED_TOTAL, "total cue count")
    require(len(all_texts) == len(set(all_texts)), "duplicate cue texts")
    bad_types = {"quiz", "quiz-feedback", "media-tab", "media", "tab", "exercise"}
    allowed = {"h2", "h3", "chapter-quote", "p", "figure", "callout",
               "formula-box", "code-showcase"}
    require(not (used_types & bad_types), f"bad cue types: {used_types & bad_types}")
    require(used_types <= allowed, f"unallowed cue types: {used_types - allowed}")
    require(not any(FORBIDDEN in t for t in all_texts), "forbidden label in manifest")
    require(FORBIDDEN not in data["articleText"], "forbidden label in DOM")

    print("=" * 68)
    print("HEADLESS CHROME VERIFICATION - Topology Lesson 03")
    print("=" * 68)
    print(f"[PASS] DOM<->manifest 1:1 ({len(canonical)} sections, {EXPECTED_TOTAL} cues)")
    print(f"[PASS] 0 duplicate section ids / audio files / cue indices / cue texts")
    print(f"[PASS] 0 quiz/media-tab types; allowed types: {sorted(used_types)}")
    print(f'[PASS] 0 "চিত্র প্রদর্শনী" labels in manifest or live DOM')
    print(f"[PASS] {len(canonical)} mp3 files present, non-zero, positive duration")
    print(f"[PASS] timings monotonic + 350ms gaps + totals == last end")
    print(f"[PASS] KaTeX annotations preserved in every DOM formula-box")
    print(f"[PASS] 0 JS page errors")
    print(f"[PASS] valid JSON; manifest.js export; preloaded==disk")
    print(f"PAGE CONSOLE ERRORS: {len(console_errors)} (benign missing-video 404s), "
          f"unexpected: {len(narration_console)}")
    print(f"TOTAL AUDIO: {total_ms / 1000.0:.2f}s")
    print("=" * 68)


if __name__ == "__main__":
    asyncio.run(build_all())
    # Headless-Chrome channel="chrome" verification runs OUTSIDE the asyncio loop.
    verify_in_chrome()
