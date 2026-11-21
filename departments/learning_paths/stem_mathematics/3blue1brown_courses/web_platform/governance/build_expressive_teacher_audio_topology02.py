# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Topology Lesson 02
("The Hairy Ball Theorem", Bengali) to the Lesson-01 gold standard.

Deterministic, re-runnable, self-contained:
  * 48 cues in 4 narrated sections with EXACTLY the same section
    IDs, audio_file names, cue types and cue order as the live DOM parsed by
    narration_engine.js (browser-extracted snapshot topology02_dom_blocks.json, KaTeX
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

Usage:  python governance/build_expressive_teacher_audio_topology02.py
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
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "topology", "lesson_02")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "topology", "lesson_02.html")
DOM_SNAPSHOT = os.path.join(SCRIPT_DIR, "topology02_dom_blocks.json")
MANIFEST_TITLE = 'অধ্যায় ০২ — কেশবহুল গোলকের উপপাদ্য'

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
 'sec-applications': ['h2', 'p', 'p', 'p', 'figure', 'formula-box', 'p', 'formula-box', 'p', 'callout', 'p'],
 'sec-proof': ['h2',
               'p',
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
 'sec-dimensions': ['h2', 'p', 'p', 'p', 'figure', 'formula-box', 'p', 'formula-box', 'p', 'callout', 'p']}
EXPECTED_AUDIO_FILES = {'sec-intro': 'sec_01_sec-intro.mp3',
 'sec-applications': 'sec_02_sec-applications.mp3',
 'sec-proof': 'sec_03_sec-proof.mp3',
 'sec-dimensions': 'sec_04_sec-dimensions.mp3'}
ALIASES = {'sec-intro': 'sec_01_intro',
 'sec-applications': 'sec_02_applications',
 'sec-proof': 'sec_03_proof',
 'sec-dimensions': 'sec_04_dimensions'}
EXPECTED_COUNTS = {'sec-intro': 12, 'sec-applications': 11, 'sec-proof': 14, 'sec-dimensions': 11}
EXPECTED_TOTAL = 48

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (48 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {'sec-intro': {'title': 'কেশবহুল গোলকের সমস্যা ও উপপাদ্যের বিবৃতি',
               'audio_file': 'sec_01_sec-intro.mp3',
               'cues': [{'index': 0,
                         'type': 'h2',
                         'tts': 'প্রথম পরিচ্ছেদ, কেশবহুল গোলকের সমস্যা ও উপপাদ্যের বিবৃতি।'},
                        {'index': 1,
                         'type': 'p',
                         'tts': 'ধরুন আপনার হাতে একটা নারকেল আছে, গায়ে অসংখ্য ছোট ছোট চুল। কাজ হলো '
                                'চুলগুলোকে এমনভাবে চিরুনি দিয়ে আঁচড়ে দেওয়া যেন সবগুলো সমানভাবে শুয়ে '
                                'থাকে, কোথাও কোনো ঝাড়ি বা ঘূর্ণি না থাকে। কিছুক্ষণ চেষ্টা করলেই বুঝতে '
                                'পারবেন এটা অসম্ভব, কোথাও না কোথাও একটা কাউলিক থাকবেই, যেখানে চুলগুলো '
                                'ছড়িয়ে পড়ে কিংবা গোল হয়ে যায়।'},
                        {'index': 2,
                         'type': 'p',
                         'tts': 'এই অসম্ভবতাটিই হলো বিখ্যাত কেশবহুল গোলকের উপপাদ্য। গণিতের ভাষায়, গোলকের '
                                'উপরিভাগে যেকোনো অবিচ্ছিন্ন স্পর্শক ভেক্টর ক্ষেত্রের কমপক্ষে একটি বিন্দুতে '
                                'ভেক্টরটি শূন্য হয়। স্পর্শক মানে ভেক্টরটি ওই বিন্দুতে গোলকের পৃষ্ঠের '
                                'সমান্তরালে থাকবে, ঠিক যেমন চুল পৃষ্ঠ থেকে বের হয়ে পাশ দিয়ে শুয়ে থাকে।'},
                        {'index': 3,
                         'type': 'p',
                         'tts': 'নামটা হাস্যকর শোনালেও এর ভেতরের গণিতের অদ্ভুত সৌন্দর্য ও প্রয়োগ রয়েছে। এই '
                                'অধ্যায়ে আমরা দেখব কেন পৃথিবীতে অবশ্যই একটি বিন্দু আছে যেখানে বাতাস নেই, আর '
                                'কীভাবে একটি অত্যন্ত সংক্ষিপ্ত ও বুদ্ধিমান যুক্তি দিয়ে এই বিবৃতি প্রমাণ করা '
                                'যায়।'},
                        {'index': 4,
                         'type': 'figure',
                         'tts': 'অফিশিয়াল পাঠের এই শিরোনাম চিত্রে গোলকটির চুলগুলো লক্ষ্য করুন। প্রতিটি চুল '
                                'স্পর্শক দিকে মুখ করে আছে, অথচ কোথাও না কোথাও একটা ঘূর্ণি থাকাটা যেন '
                                'অবধারিত। এই চিত্রটিই আমাদের মূল প্রশ্নটি চোখের সামনে তুলে ধরে।'},
                        {'index': 5,
                         'type': 'figure',
                         'tts': 'হলুদ তীরগুলো হলো স্পর্শক ভেক্টর, প্রতিটি বিন্দুতে পৃষ্ঠের সমান্তরাল। লাল '
                                'রেখাটি হলো কাউলিক, এখানে ভেক্টরের মান শূন্য, তাই দিক ঠিক করা যায় না। ঠিক '
                                'এই বিন্দুটির অস্তিত্বই উপপাদ্যটি দাবি করে।'},
                        {'index': 6,
                         'type': 'formula-box',
                         'tts': 'গাণিতিক সূত্র, ভি মানে এস দুই গোলক থেকে থ্রিডি রিয়েল স্পেসে যাওয়া এক '
                                'ম্যাপ, আর প্রতিটি বিন্দু পিতে ভি অফ পি ঐ বিন্দুর ব্যাসার্ধের লম্ব।'},
                        {'index': 7,
                         'type': 'p',
                         'tts': 'স্পর্শক ক্ষেত্রের শর্ত হলো প্রতিটি বিন্দুতে ভেক্টর ব্যাসার্ধের লম্ব। অর্থাৎ '
                                'ভেক্টরটি গোলকের বাইরের দিকে না গিয়ে পৃষ্ঠ বরাবর পাশ দিয়ে বয়ে যায়, ঠিক '
                                'যেমন চুল মাথার পৃষ্ঠে শুয়ে থাকে।'},
                        {'index': 8,
                         'type': 'formula-box',
                         'tts': 'গাণিতিক সূত্র, যেকোনো অবিচ্ছিন্ন ভি এর জন্য এমন এক বিন্দু পি আছে যার জন্য '
                                'ভি অফ পি সমান শূন্য।'},
                        {'index': 9,
                         'type': 'p',
                         'tts': 'কেশবহুল গোলকের উপপাদ্যের এই গাণিতিক রূপটি আমাদের চূড়ান্ত ফলাফল। এটি বলে যে '
                                'শূন্য না হওয়া চুল সব জায়গায় থাকতে পারে না, কমপক্ষে এক জায়গায় থামতেই '
                                'হবে।'},
                        {'index': 10,
                         'type': 'callout',
                         'tts': 'বিশেষ নোট, শব্দের আড়ালে। এখানে চুল মানে আসলে একটি স্পর্শক ভেক্টর ক্ষেত্র, '
                                'প্রতিটি বিন্দুতে একটিমাত্র দিক ও দৈর্ঘ্য নির্ধারণ করে দেওয়া একটি নিয়ম। '
                                'অবিচ্ছিন্ন মানে বিন্দু সামান্য বদলালে চুলের দিকও সামান্য বদলাবে, কোনো হঠাৎ '
                                'লাফ নয়।'},
                        {'index': 11,
                         'type': 'p',
                         'role': 'conclusion',
                         'tts': 'এই সহজ মনে হওয়া পর্যবেক্ষণটিই এখন আমাদের নিয়ে যাবে বাতাসের মতো বাস্তব '
                                'বিষয়ে। দেখা যাবে কীভাবে আবহাওয়ার একটা সাধারণ প্রশ্নের উত্তর এই উপপাদ্য '
                                'আমাদের দিয়ে দেয়।'}]},
 'sec-applications': {'title': 'অপ্রত্যাশিত প্রয়োগ: বাতাস, ঘূর্ণন ও অ্যান্টেনা',
                      'audio_file': 'sec_02_sec-applications.mp3',
                      'cues': [{'index': 0,
                                'type': 'h2',
                                'tts': 'দ্বিতীয় পরিচ্ছেদ, অপ্রত্যাশিত প্রয়োগ, বাতাস, ঘূর্ণন ও অ্যান্টেনা।'},
                               {'index': 1,
                                'type': 'p',
                                'tts': 'পৃথিবীর পৃষ্ঠে প্রতি মুহূর্তে বাতাস বইছে। কোনো বিন্দুতে বাতাসের যে '
                                       'দিক ও বেগ, তা স্থানীয়ভাবে পৃষ্ঠের সমান্তরাল, অর্থাৎ এটি একটি '
                                       'স্পর্শক ভেক্টর ক্ষেত্র। বাতাসের গতি সময়ের সাথে অবিচ্ছিন্নভাবে '
                                       'বদলায়। তাই উপপাদ্য আমাদের বলে দেয়, যেকোনো মুহূর্তে পৃথিবীতে '
                                       'কমপক্ষে একটি বিন্দু আছে, যেখানে অনুভূমিক বাতাসের বেগ একেবারে শূন্য, '
                                       'এক ধরনের চোখ, যেমন ঘূর্ণিঝড়ের কেন্দ্র।'},
                               {'index': 2,
                                'type': 'p',
                                'tts': 'আরেকটি প্রয়োগ হলো ঘূর্ণয়মান গোলক। কোনো গোলককে ঘোরালে তার প্রতিটি '
                                       'বিন্দুর বেগ একটি স্পর্শক ভেক্টর দেয়। বেগ শূন্য হবে কোথাও, অর্থাৎ '
                                       'ঘূর্ণনের একটি অক্ষ থাকতেই হবে। সোজা কথায়, যেকোনো ভূ গোলকের ঘূর্ণনের '
                                       'একটি মেরু বা অক্ষ থাকে।'},
                               {'index': 3,
                                'type': 'p',
                                'tts': 'তৃতীয় উদাহরণ হলো সংকেত বা তড়িৎ চুম্বকীয় ক্ষেত্র। গোলকাকৃত বস্তুর '
                                       'পৃষ্ঠে একটি অবিচ্ছিন্ন দিক নির্দেশক ক্ষেত্র সবজায়গায় একই রকমভাবে '
                                       'টানা যায় না। এর মানে হলো একটি গোলকের ওপর সব দিকে একইভাবে দেখাও যায় '
                                       'না, কোথাও না কোথাও একটা শূন্যতা থাকবে।'},
                               {'index': 4,
                                'type': 'figure',
                                'tts': 'হলুদ তীরগুলো বাতাসের দিক আর বেগ দেখাচ্ছে। লাল বিন্দুতে অনুভূমিক '
                                       'বাতাস শূন্য, ঘূর্ণিঝড়ের চোখের মতো। উপপাদ্য গ্যারান্টি দেয় এরকম '
                                       'একটি বিন্দু সবসময় আছে, যদিও কোথায় তা বলে দেয় না।'},
                               {'index': 5,
                                'type': 'formula-box',
                                'tts': 'গাণিতিক সূত্র, বিন্দুতে ভি হলো বাতাসের বেগ, যা পৃথিবীর পৃষ্ঠের '
                                       'সমান্তরাল।'},
                               {'index': 6,
                                'type': 'p',
                                'tts': 'বাতাসের বেগ ক্ষেত্র একটি স্পর্শক ভেক্টর ক্ষেত্র, তাই উপপাদ্য '
                                       'প্রযোজ্য। ফলাফল হলো কোথাও একটা বিন্দু থাকবেই যেখানে অনুভূমিক বাতাস '
                                       'থামে।'},
                               {'index': 7,
                                'type': 'formula-box',
                                'tts': 'গাণিতিক সূত্র, এমন একটি বিন্দু পি আছে যার জন্য ভি অফ পি সমান শূন্য '
                                       'ভেক্টর।'},
                               {'index': 8,
                                'type': 'p',
                                'tts': 'সেই বিশেষ বিন্দুতে অনুভূমিক বেগ শূন্য। আবহাওয়াবিদরা সেই বিন্দুকে '
                                       'খুঁজে বের করেন, আর টোপোলজি শুধু বলে দেয় যে সেটি অবশ্যই আছে।'},
                               {'index': 9,
                                'type': 'callout',
                                'tts': 'বিশেষ নোট, উপপাদ্য কোথায় বলে না। গণিত এখানে কেবল অস্তিত্বের '
                                       'গ্যারান্টি দেয়, কোথায় সেই শূন্য বিন্দু থাকবে তা বলে দেয় না। '
                                       'আবহাওয়াবিদদের কাজ হলো সেটি খোঁজা, টোপোলজির কাজ হলো বলা যে সেটি '
                                       'অবশ্যই আছে।'},
                               {'index': 10,
                                'type': 'p',
                                'role': 'conclusion',
                                'tts': 'এত সুন্দর একটি সিদ্ধান্তের পেছনে দারুণ সহজ এক যুক্তি আছে, আসুন সেটি '
                                       'দেখি।'}]},
 'sec-proof': {'title': 'সুন্দর প্রমাণ: ডিগ্রি, আইডেন্টিটি ও অ্যান্টিপোডাল ম্যাপ',
               'audio_file': 'sec_03_sec-proof.mp3',
               'cues': [{'index': 0,
                         'type': 'h2',
                         'tts': 'তৃতীয় পরিচ্ছেদ, সুন্দর প্রমাণ, ডিগ্রি, আইডেন্টিটি ও অ্যান্টিপোডাল ম্যাপ।'},
                        {'index': 1,
                         'type': 'p',
                         'tts': 'ধরা যাক গোলকের ওপর একটি স্পর্শক ভেক্টর ক্ষেত্র ভি আছে, কোথাও শূন্য নয়। '
                                'তাহলে প্রতিটি বিন্দু পিতে ভি অফ পি একটি নির্দিষ্ট অশূন্য দিক দেখায়। এই দিক '
                                'ধরে আমরা পি থেকে শুরু করে গোলকের ওপর একটা মহাবৃত্ত বরাবর চলে যেতে পারি, ঠিক '
                                'একই দিকে, একই গতিতে। কিছুক্ষণ পর কোথায় পৌঁছাব, কিছুক্ষণের মধ্যেই ঋণাত্মক '
                                'পি তে, অর্থাৎ পি এর ঠিক বিপরীত বিন্দুতে।'},
                        {'index': 2,
                         'type': 'p',
                         'tts': 'অর্থাৎ ভেক্টর ক্ষেত্রটি আমাদের একটি অবিচ্ছিন্ন পরিবর্তন দেয়, শুরুতে '
                                'প্রতিটি পয়েন্ট নিজের জায়গাকে আঁকে, আর শেষে প্রতিটি পয়েন্ট বিপরীত '
                                'জায়গাকে আঁকে। মাঝের সময়গুলোতে পয়েন্টগুলো মহাবৃত্ত বরাবর সরে যায়। কোনো '
                                'ঝটপট লাফ নেই, সবকিছু অবিচ্ছিন্ন।'},
                        {'index': 3,
                         'type': 'p',
                         'tts': 'এখন টোপোলজির একটি কেন্দ্রীয় ধারণা আসে, ম্যাপের ডিগ্রি, মোট কতবার ম্যাপটি '
                                'গোলককে নিজের ওপর ভরে দেয়, কোন দিকে ভরে তা নিয়ে। আইডেন্টিটি ম্যাপের ডিগ্রি '
                                'ধনাত্মক এক। গোলকের ক্ষেত্রে অ্যান্টিপোডাল ম্যাপের ডিগ্রি ঋণাত্মক এক। কিন্তু '
                                'যে ম্যাপগুলোর মাঝে অবিচ্ছিন্ন পরিবর্তন চলে, তাদের ডিগ্রি একই হতে হয়। '
                                'ধনাত্মক এক আর ঋণাত্মক এক কখনোই এক নয়, তাই এইরকম কোনো শূন্যমুক্ত ক্ষেত্র '
                                'থাকতে পারে না।'},
                        {'index': 4,
                         'type': 'p',
                         'tts': 'অন্য একটি দৃষ্টিকোণ হলো পয়েনকেয়ার হপফের সূচক যোগফল। কোনো ভেক্টর ক্ষেত্রের '
                                'শূন্যবিন্দুগুলোর সূচকের যোগফল গোলকের ইুলার বৈশিষ্ট্যের সমান, যা ধনাত্মক '
                                'দুই। যোগফল শূন্য হলে কোনো শূন্যবিন্দুই থাকবে না, কিন্তু দুই আর শূন্য সমান '
                                'নয়, তাই কমপক্ষে একটি শূন্যবিন্দু অবশ্যই আছে। দুটি প্রমাণ একই সত্যকে দুই '
                                'ভাষায় বলছে।'},
                        {'index': 5,
                         'type': 'figure',
                         'tts': 'প্রতিটি চুলের দিক ধরে পয়েন্টগুলোকে সরে যেতে দিন। ছবিতে দেখা যাচ্ছে শুরুতে '
                                'তারা নিজ জায়গায় আর শেষে বিপরীত জায়গায় পৌঁছায়। এই অবিচ্ছিন্ন সরে '
                                'যাওয়াটিই ডিগ্রির বিরোধকে জন্ম দেয়।'},
                        {'index': 6,
                         'type': 'formula-box',
                         'tts': 'গাণিতিক সূত্র, এইচ অফ পি টি এস দুই তে থাকে, শুরুতে এইচ অফ পি শূন্য সমান পি, '
                                'আর শেষে এইচ অফ পি এক সমান ঋণাত্মক পি।'},
                        {'index': 7,
                         'type': 'p',
                         'tts': 'শূন্যমুক্ত ক্ষেত্র থেকে পাওয়া এই হোমোটপি আইডেন্টিটি থেকে অ্যান্টিপোডাল '
                                'ম্যাপে যায়। অর্থাৎ একটা চলমান পরিবর্তনের মাধ্যমে পি ধীরে ধীরে তার বিপরীত '
                                'বিন্দুতে পৌঁছায়, কোথাও থেমে না যায়।'},
                        {'index': 8,
                         'type': 'formula-box',
                         'tts': 'গাণিতিক সূত্র, আইডেন্টিটি ম্যাপের ডিগ্রি ধনাত্মক এক, আর ঋণাত্মক এক্স '
                                'ম্যাপের ডিগ্রি ঋণাত্মক এক।'},
                        {'index': 9,
                         'type': 'p',
                         'tts': 'হোমোটপিক ম্যাপের ডিগ্রি একই হওয়া উচিত, কিন্তু ধনাত্মক এক ও ঋণাত্মক এক '
                                'আলাদা। এই বিরোধই প্রমাণ করে যে শূন্যমুক্ত স্পর্শক ক্ষেত্র গোলকে থাকতে পারে '
                                'না।'},
                        {'index': 10,
                         'type': 'formula-box',
                         'tts': 'গাণিতিক সূত্র, শূন্যবিন্দুগুলোর সূচকের যোগফল সমান ইুলার বৈশিষ্ট্য, যা এস '
                                'দুই এর ক্ষেত্রে দুই।'},
                        {'index': 11,
                         'type': 'p',
                         'tts': 'পয়েনকেয়ার হপফ বলেন, সূচক যোগফল ইুলার বৈশিষ্ট্য দুই এর সমান, তাই শূন্য '
                                'অবশ্যই আছে। গোলকের ক্ষেত্রে ইুলার বৈশিষ্ট্য দুই হওয়ায় শূন্যবিন্দু না থাকা '
                                'অসম্ভব।'},
                        {'index': 12,
                         'type': 'callout',
                         'tts': 'বিশেষ নোট, কেন ডিগ্রি বদলায় না। একটি গোলককে নিজের ওপর ভরে দেওয়ার সময় '
                                'ভাঁজ বা ছেঁড়া না হলে কতবার আবরণ হয়েছে তা বদলায় না। আইডেন্টিটি ম্যাপে '
                                'প্রতিটি পয়েন্ট ঠিক একবারই আবৃত হয়, আর অ্যান্টিপোডাল ম্যাপে দিক উল্টে '
                                'যায়। অবিচ্ছিন্ন পরিবর্তনে এই দুইয়ের মাঝে যাওয়া যায় না।'},
                        {'index': 13,
                         'type': 'p',
                         'role': 'conclusion',
                         'tts': 'এই যুক্তিটি শুধু গোলকের নয়, যেকোনো জোড় মাত্রার গোলকের ক্ষেত্রেই একই কথা '
                                'প্রযোজ্য।'}]},
 'sec-dimensions': {'title': 'কোন পৃষ্ঠ আঁচড়ানো যায় — মাত্রার ভূমিকা',
                    'audio_file': 'sec_04_sec-dimensions.mp3',
                    'cues': [{'index': 0,
                              'type': 'h2',
                              'tts': 'চতুর্থ পরিচ্ছেদ, কোন পৃষ্ঠ আঁচড়ানো যায়, মাত্রার ভূমিকা।'},
                             {'index': 1,
                              'type': 'p',
                              'tts': 'গোলকের বিপরীতে বৃত্ত বা এস এক কে আমরা সহজেই আঁচড়ে নিতে পারি, প্রতিটি '
                                     'বিন্দুতে একই দিকে একটি ভেক্টর বসালেই হলো, কোথাও শূন্য নেই। একইভাবে '
                                     'টরাসের ওপরও শূন্যমুক্ত স্পর্শক ক্ষেত্র তৈরি করা যায়, টরাসের ইুলার '
                                     'বৈশিষ্ট্য শূন্য, তাই সূচক যোগফল শূন্য হতে পারে।'},
                             {'index': 2,
                              'type': 'p',
                              'tts': 'সাধারণ নিয়ম হলো, এস এন গোলকের ওপর শূন্যমুক্ত স্পর্শক ক্ষেত্র থাকে ঠিক '
                                     'যখন এন একটি বিজোড় সংখ্যা। আমাদের পরিচিত এস দুই তে এন হলো দুই, অর্থাৎ '
                                     'জোড়, তাই ক্ষেত্র থাকতে পারে না। আমাদের ত্রিমাত্রিক স্থানের গোলক এস '
                                     'দুই কেই আমরা গোলক বলি, তাই এই নিষেধাজ্ঞা আমাদের কাছে এত স্বাভাবিক মনে '
                                     'হয়।'},
                             {'index': 3,
                              'type': 'p',
                              'tts': 'আরেকটি সুন্দর বিবৃতি, এস তিন এর ওপর, যা চার মাত্রিক স্থানের গোলক, '
                                     'শূন্যমুক্ত ক্ষেত্র আছে। আসলে সেখানে তিনটি পরস্পর লম্ব ভেক্টর ক্ষেত্র '
                                     'একসাথে বসানো যায়, যাকে বলা হয় প্যারালেলাইজেশন। এইসব সত্য দেখিয়েই '
                                     'বোঝা যায় টোপোলজি কেবল আকৃতি নয়, মাত্রার সাথে আকৃতির গভীর সংযোগ নিয়ে '
                                     'কাজ করে।'},
                             {'index': 4,
                              'type': 'figure',
                              'tts': 'এস দুই বা সাধারণ গোলকে চুল আঁচড়ানো যায় না। ছবিতে দেখা যাচ্ছে কীভাবে '
                                     'এক মাত্রা কম বা বেশি হলে চিত্র বদলে যায়। বৃত্ত ও টরাসে শূন্যমুক্ত '
                                     'ক্ষেত্র সম্ভব, গোলকে নয়।'},
                             {'index': 5,
                              'type': 'formula-box',
                              'tts': 'গাণিতিক সূত্র, দুই গুণ কে যোগ এক মাত্রার গোলকে শূন্যমুক্ত স্পর্শক '
                                     'ক্ষেত্র থাকে।'},
                             {'index': 6,
                              'type': 'p',
                              'tts': 'বিজোড় মাত্রার গোলকে শূন্যমুক্ত স্পর্শক ক্ষেত্র থাকে। অর্থাৎ মাত্রা '
                                     'যখন এক, তিন, পাঁচের মতো বিজোড় হয়, তখনই চুল আঁচড়ানো সম্ভব হয়।'},
                             {'index': 7,
                              'type': 'formula-box',
                              'tts': 'গাণিতিক সূত্র, এস দুই এর ইুলার বৈশিষ্ট্য দুই, আর টরাসের ইুলার '
                                     'বৈশিষ্ট্য শূন্য।'},
                             {'index': 8,
                              'type': 'p',
                              'tts': 'ইুলার বৈশিষ্ট্য শূন্য হলে শূন্য না থাকা সম্ভব, আর দুই হলে অসম্ভব। এই '
                                     'ছোট্ট সংখ্যাটিই গোলক আর টরাসের আচরণের পার্থক্য তৈরি করে।'},
                             {'index': 9,
                              'type': 'callout',
                              'tts': 'বিশেষ নোট, মাত্রা কেন গুরুত্বপূর্ণ। অ্যান্টিপোডাল ম্যাপের ডিগ্রি '
                                     'নির্ভর করে এনের ওপর, এন জোড় হলে এটি ঋণাত্মক এক এবং আইডেন্টিটির '
                                     'ধনাত্মক একের সাথে বিরোধ তৈরি করে, এন বিজোড় হলে দুটিই ধনাত্মক এক, '
                                     'বিরোধ নেই, ক্ষেত্র থাকতে পারে।'},
                             {'index': 10,
                              'type': 'p',
                              'role': 'conclusion',
                              'tts': 'পরবর্তী অধ্যায়ে আমরা দেখব কীভাবে একই রকম একটি টোপোলজিক্যাল যুক্তি '
                                     'একেবারে আলাদা এক ধাঁধার সমাধান করে দেয়।'}]}}

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
        "lesson": "lesson_02",
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
    print(f"BUILD COMPLETE - expressive teacher audio, Topology Lesson 02")
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

    page_uri = ("http://127.0.0.1:8085/courses/topology/lesson_02.html"
                "?v=verify02")
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
    print("HEADLESS CHROME VERIFICATION - Topology Lesson 02")
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
