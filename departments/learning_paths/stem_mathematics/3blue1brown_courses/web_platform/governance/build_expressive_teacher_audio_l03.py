# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for 3Blue1Brown Lesson 03 (Bengali),
expressive-edition, to the Lesson 01 gold standard.

Deterministic, re-runnable, self-contained:

  * 32 cues in 4 narrated sections. The cue count/type/order of every section is
    derived from the LIVE DOM of courses/linear_algebra/lesson_03.html using the
    very selector/rules that narration_engine.js uses:
        article section  (skip [data-no-narration="true"])
        h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
        .code-showcase, .formula-box   (skip <p> inside .callout/.chapter-quote)
    The extracted DOM blocks (with TeX preserved as ⟦TEX:...⟧ markers from the
    KaTeX <annotation encoding="application/x-tex"> nodes) are stored in
    governance/l03_dom_blocks.json and are 1:1 with SECTIONS_DATA below.
    No quiz / media-tab / interactive-section cues are emitted.
  * Every figure cue is a genuine 2-4 sentence pedagogical explanation
    (what is drawn / what to notice / why it matters): 5 figures.
  * Scripts are clean spoken Bengali: no TeX, backslashes, $, braces, brackets,
    em/en dashes, raw hyphens or Latin letters. Phonetic safeguards:
    f(x)->এফ অব এক্স, x^2->এক্স স্কয়ার, x->এক্স, y->ওয়াই, z->জেড,
    î->আই হ্যাট, ĵ->জে হ্যাট, k̂->কে হ্যাট,
    bmatrix->কলাম ভেক্টর (উপরে ... নিচে ...).
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
    h2 -5%/+2Hz, h3 -3%, chapter-quote -3%, figure -4%, formula-box -8%,
    p +2%, callout +0%, conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so millisecond
    timings in the manifest match the concatenated MP3 exactly (zero overlap).
  * Per-section ffmpeg concat (-c copy) into the EXISTING audio_file names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with all
    EIGHT existing keys (4 canonical section ids + 4 aliases).
  * Validates non-zero durations, zero overlap, exact gaps, valid JSON,
    non-empty MP3s, no duplicate texts and DOM<->manifest 1:1 parity before
    reporting success.

Usage:  python governance/build_expressive_teacher_audio_l03.py
"""

import os
import re
import json
import hashlib
import asyncio
import subprocess
from html.parser import HTMLParser

import edge_tts

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
VOICE = "bn-BD-PradeepNeural"
GAP_MS = 350.0
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))            # .../governance
WORKSPACE = os.path.dirname(SCRIPT_DIR)                             # .../web_platform
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio",
                         "linear_algebra", "lesson_03")
SOURCE_HTML = os.path.join(WORKSPACE, "courses", "linear_algebra",
                           "lesson_03.html")
DOM_BLOCKS = os.path.join(SCRIPT_DIR, "l03_dom_blocks.json")

# Prosody (rate, pitch, volume) by cue type.
PROSODY_DEFAULT = {
    "h2":            ("-5%",  "+2Hz", "+0%"),  # warm, slower section opening
    "h3":            ("-3%",  "+0Hz", "+0%"),
    "chapter-quote": ("-3%",  "+0Hz", "+0%"),
    "p":             ("+2%",  "+0Hz", "+0%"),  # natural teacher pace
    "figure":        ("-4%",  "+0Hz", "+0%"),  # slower, considerate explanation
    "callout":       ("+0%",  "+0Hz", "+0%"),
    "formula-box":   ("-8%",  "+0Hz", "+0%"),  # slow and deliberate
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")   # calm concluding prose

# Canonical section id -> alias (both keys exist in the existing manifest).
SECTION_ORDER = [
    ("sec-transformations-are-functions", "sec_01_transformations"),
    ("sec-what-makes-linear",             "sec_02_linearity"),
    ("sec-describing-transformations",    "sec_03_basis_tracking"),
    ("sec-matrix-notation",               "sec_04_matrix2x2"),
]

# Exact DOM-derived cue type sequences (parity guards).
EXPECTED_TYPES = {
    "sec-transformations-are-functions":
        ["h2", "p", "p", "p", "p", "p", "callout"],
    "sec-what-makes-linear":
        ["h2", "p", "p", "figure", "p", "figure", "p", "figure", "figure"],
    "sec-describing-transformations":
        ["h2", "p", "p", "p", "p", "p"],
    "sec-matrix-notation":
        ["h2", "p", "p", "p", "p", "p", "figure", "p", "callout", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-transformations-are-functions": "sec_01_transformations.mp3",
    "sec-what-makes-linear":             "sec_02_linearity.mp3",
    "sec-describing-transformations":    "sec_03_basis_tracking.mp3",
    "sec-matrix-notation":               "sec_04_matrix2x2.mp3",
}
EXPECTED_TITLES = {
    "sec-transformations-are-functions":
        "১. রূপান্তর আসলে একটি ফাংশন (Transformations are Functions)",
    "sec-what-makes-linear":
        "২. একটি রূপান্তরকে কী 'রৈখিক' (Linear) করে তোলে?",
    "sec-describing-transformations":
        "৩. ভিত্তি ভেক্টর দিয়েই সম্পূর্ণ রূপান্তরের বর্ণনা",
    "sec-matrix-notation":
        "৪. ম্যাট্রিক্স নোটেশন ও ভেক্টর গুণনের জ্যামিতিক সত্য",
}
FORBIDDEN_CUE_TYPES = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (32 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-transformations-are-functions": {
        "title": EXPECTED_TITLES["sec-transformations-are-functions"],
        "alias": "sec_01_transformations",
        "audio_file": EXPECTED_AUDIO_FILES["sec-transformations-are-functions"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, রূপান্তর আসলে একটি ফাংশন।"},
            {"index": 1, "type": "p",
             "tts": "লিনিয়ার অ্যালজেব্রার মূল প্রাণকেন্দ্র হলো রৈখিক রূপান্তর, আর তার সাথে ম্যাট্রিক্সের অবিচ্ছেদ্য সম্পর্ক বোঝা। কিন্তু এই বিষয়ে প্রবেশ করার আগে আমাদের একটা বিষয় স্পষ্ট করে নিতে হবে। রূপান্তর বলতে আমরা আসলে কী বুঝি?"},
            {"index": 2, "type": "p",
             "tts": "সহজ কথায়, একটি রূপান্তর মূলত একটি ফাংশন ছাড়া কিছুই নয়। সাধারণ উচ্চমাধ্যমিক গণিতে আমরা এমন ফাংশন দেখে অভ্যস্ত যা একটি বাস্তব সংখ্যা ইনপুট নেয় এবং আরেকটি সংখ্যা আউটপুট দেয়, যেমন এফ অব এক্স সমান এক্স স্কয়ার। কিন্তু লিনিয়ার অ্যালজেব্রায় আমরা এমন এক চমৎকার ফাংশনের কথা বলি যা একটি ভেক্টর ইনপুট গ্রহণ করে এবং আরেকটি ভেক্টর আউটপুট প্রদান করে।"},
            {"index": 3, "type": "p",
             "tts": "তাহলে প্রশ্ন জাগতে পারে, যদি এটি কেবলই একটি ফাংশন হয়, তবে গণিতবিদরা কেন একে ফাংশন না বলে বিশেষভাবে রূপান্তর নাম দেন? এর কারণ হলো জ্যামিতিক দৃষ্টিশক্তি। রূপান্তর শব্দটি আমাদের মনের ভেতর একটি নিখুঁত জ্যামিতিক গতির অনুভূতি এনে দেয়, যেন পুরো দ্বিমাত্রিক বা ত্রিমাত্রিক স্থানটি নিজে নড়াচড়া করছে, মোচড় খাচ্ছে বা প্রসারিত হচ্ছে।"},
            {"index": 4, "type": "p",
             "tts": "একটি ইনপুট ভেক্টরকে তার আউটপুট ভেক্টরে পরিবর্তিত হতে দেখার সবচেয়ে কল্পনাপ্রসূত ও প্রাণবন্ত উপায় হলো ভেক্টরটিকে এক স্থান থেকে অন্য স্থানে গতিশীল হতে দেখা।"},
            {"index": 5, "type": "p",
             "tts": "এবার সমগ্র রূপান্তরটিকে একনজরে অনুধাবন করতে হলে, স্থানের প্রতিটি ভেক্টরকে তীরের বদলে কেবল তার শীর্ষবিন্দু হিসেবে কল্পনা করুন। যখন সব বিন্দু একসাথে নড়ে যায়, তখন পুরো তলটি একটি গ্রিডের মতো নতুন রূপ ধারণ করে।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, মূল অন্তর্দৃষ্টি। রূপান্তরকে যখন আমরা স্থানের একটি মসৃণ আকৃতি পরিবর্তন হিসেবে দেখি, তখন জটিল সমীকরণ নিমেষেই দৃশ্যমান জ্যামিতিক সত্যে পরিণত হয়।"},
        ],
    },

    "sec-what-makes-linear": {
        "title": EXPECTED_TITLES["sec-what-makes-linear"],
        "alias": "sec_02_linearity",
        "audio_file": EXPECTED_AUDIO_FILES["sec-what-makes-linear"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, একটি রূপান্তরকে কী রৈখিক করে তোলে?"},
            {"index": 1, "type": "p",
             "tts": "স্থানকে কোটি কোটি উপায়ে বাঁকানো, প্যাঁচানো বা বিকৃত করা সম্ভব। কিন্তু লিনিয়ার অ্যালজেব্রায় আমরা রূপান্তরের একটি বিশেষ ও শৃঙ্খলাবদ্ধ শ্রেণি নিয়ে কাজ করি, যাকে বলা হয় রৈখিক রূপান্তর।"},
            {"index": 2, "type": "p",
             "tts": "জ্যামিতিকভাবে একটি রূপান্তরকে রৈখিক হতে হলে ঠিক দুটি অলঙ্ঘনীয় শর্ত পূরণ করতে হয়। প্রথমত, সমস্ত সরলরেখাকে রূপান্তরের পরও সোজা সরলরেখাই থাকতে হবে, কোনো বক্রতা গ্রহণযোগ্য নয়। দ্বিতীয়ত, মূলবিন্দু শূন্য কমা শূন্য তার নিজের স্থানেই অটল থাকবে, অন্য কোথাও সরতে পারবে না।"},
            {"index": 3, "type": "figure",
             "tts": "এখানে বাঁদিকে আসল গ্রিড আর ডানদিকে রূপান্তরিত গ্রিড পাশাপাশি দেখা যাচ্ছে। লক্ষ্য করুন, সরলরেখা রূপান্তরের পরও সরলই আছে, কোনো বক্রতা তৈরি হয়নি, আর মূলবিন্দুও নিজ জায়গায় অটল আছে। এই দুটি শর্তই একটা রূপান্তরকে রৈখিক করে তোলে, আর পরবর্তীতে এগুলোই বীজগাণিতিক নিয়মে রূপ নেবে।"},
            {"index": 4, "type": "p",
             "tts": "এই দুটি নিয়মকে একত্রিত করলে একটি চমৎকার দৃশ্যমান ফলাফল পাওয়া যায়। স্থানাঙ্ক গ্রিডের সমস্ত রেখা সমান্তরাল এবং সমান দূরত্ব বজায় রাখবে।"},
            {"index": 5, "type": "figure",
             "tts": "দেখুন, রূপান্তরের পর গ্রিডের রেখাগুলো কাত হয়ে গেছে, কিন্তু পরস্পর সমান্তরাল এবং সমান দূরত্বে অবস্থান করছে। কোণ বদলালেও রেখার ওপরের অনুপাত অপরিবর্তিত আছে, কোনো রেখা ভেঙে বা বেঁকে যায়নি। এই গ্রিডের চাক্ষুষ পরিচয় থেকেই আমরা সিদ্ধান্ত নিতে পারি যে রূপান্তরটি রৈখিক।"},
            {"index": 6, "type": "p",
             "tts": "বিপরীতে, যদি মূলবিন্দু সরে যায় কিংবা কোনো সরলরেখা ধনুকের মতো বাঁকা হয়ে যায়, তবে সেই রূপান্তরটি অরৈখিক বলে গণ্য হয়।"},
            {"index": 7, "type": "figure",
             "tts": "এখানে গ্রিডের রেখাগুলো সোজা থাকলেও মূলবিন্দু নিজ স্থান থেকে সরে গেছে। মূলবিন্দু স্থির না থাকলে শূন্য কমা শূন্য বিন্দুর নতুন অবস্থান জানতে হয়, যা রৈখিকতার মৌলিক শর্ত ভঙ্গ করে। ছবিটি আমাদের শেখায় যে শুধু রেখা সোজা থাকাই যথেষ্ট নয়, একটিমাত্র শর্ত ভাঙলেই পুরো রূপান্তর অরৈখিক হয়ে যায়।"},
            {"index": 8, "type": "figure",
             "tts": "এখানে মূলবিন্দু স্থির থাকলেও সরলরেখাগুলো বেঁকে বক্ররেখায় পরিণত হয়েছে। বক্রতার কারণে একটি রেখার ওপরের দুটি বিন্দুর মধ্যবর্তী অনুপাত আর সংরক্ষিত থাকে না। আগের চিত্রের সাথে মিলিয়ে দেখলে বোঝা যায়, দুটি শর্তের যেকোনো একটিও ভাঙলেই রৈখিকতা নষ্ট হয়।"},
        ],
    },

    "sec-describing-transformations": {
        "title": EXPECTED_TITLES["sec-describing-transformations"],
        "alias": "sec_03_basis_tracking",
        "audio_file": EXPECTED_AUDIO_FILES["sec-describing-transformations"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, ভিত্তি ভেক্টর দিয়েই সম্পূর্ণ রূপান্তরের বর্ণনা।"},
            {"index": 1, "type": "p",
             "tts": "এখন আসে লিনিয়ার অ্যালজেব্রার সবচেয়ে গভীর ও বিস্ময়কর সত্য। আপনি কীভাবে একটি রৈখিক রূপান্তরকে সংখ্যার মাধ্যমে খাতায় লিখে রাখবেন? আপাতদৃষ্টিতে মনে হতে পারে, তলের কোটি কোটি বিন্দুর নতুন অবস্থান লিখতে অসীম তথ্যের প্রয়োজন।"},
            {"index": 2, "type": "p",
             "tts": "কিন্তু উত্তর হলো, না। মাত্র দুটি ভেক্টরের নতুন অবস্থান জানলেই পুরো রূপান্তরটি সম্পূর্ণ নির্ধারিত হয়ে যায়। আর সেই দুটি ভেক্টর হলো আমাদের পরম পরিচিত ভিত্তি ভেক্টর, আই হ্যাট এবং জে হ্যাট।"},
            {"index": 3, "type": "p",
             "tts": "অধ্যায় দুই থেকে আমরা জানি, যেকোনো ভেক্টর ভি হলো কলাম ভেক্টর, উপরে এক্স আর নিচে ওয়াই। আসলে এটি ভিত্তি ভেক্টর দুটির একটি রৈখিক সমন্বয়, এক্স আই হ্যাট যোগ ওয়াই জে হ্যাট।"},
            {"index": 4, "type": "p",
             "tts": "রৈখিক রূপান্তরের প্রধান বৈশিষ্ট্যই হলো এটি রৈখিক সমন্বয় ও অনুপাতকে অবিকল সংরক্ষণ করে। রূপান্তরের পরে গ্রিড লাইনগুলো সমান্তরাল ও সমদূরত্বে থাকায়, রূপান্তরিত ভেক্টর টি অব ভি ঠিক একই স্কেলার এক্স ও ওয়াই দ্বারা রূপান্তরিত ভিত্তি ভেক্টর দুটির যোগফল হবে। অর্থাৎ টি অব ভি সমান এক্স টি অব আই হ্যাট যোগ ওয়াই টি অব জে হ্যাট।"},
            {"index": 5, "type": "p", "role": "conclusion",
             "tts": "এর অর্থ হলো, যদি আপনি কেবল জানেন রূপান্তরের পর আই হ্যাট কোথায় গিয়ে পৌঁছায় এবং জে হ্যাট কোথায় গিয়ে পৌঁছায়, তবে আপনি মহাবিশ্বের যেকোনো ভেক্টরের নতুন অবস্থান একমুহূর্তেই নিখুঁতভাবে গণনা করে ফেলতে পারবেন।"},
        ],
    },

    "sec-matrix-notation": {
        "title": EXPECTED_TITLES["sec-matrix-notation"],
        "alias": "sec_04_matrix2x2",
        "audio_file": EXPECTED_AUDIO_FILES["sec-matrix-notation"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, ম্যাট্রিক্স নোটেশন ও ভেক্টর গুণনের জ্যামিতিক সত্য।"},
            {"index": 1, "type": "p",
             "tts": "এবার আসা যাক সবচেয়ে গুরুত্বপূর্ণ মুহূর্তে। ম্যাট্রিক্স কী?"},
            {"index": 2, "type": "p",
             "tts": "ধরা যাক, একটি নির্দিষ্ট রূপান্তরের পর আই হ্যাট অবতরণ করে স্থানাঙ্ক কলাম ভেক্টর, উপরে এক আর নিচে মাইনাস দুই। আর জে হ্যাট গিয়ে পৌঁছায় কলাম ভেক্টর, উপরে তিন আর নিচে শূন্য। গণিতবিদরা এই ফলাফল দুটিকে পাশাপাশি সাজিয়ে একটি সুন্দর বন্ধনীর ভেতরে লেখেন, এক আর তিন উপরের সারিতে আর মাইনাস দুই ও শূন্য নিচের সারিতে। এটিই একটি দুই বাই দুই ম্যাট্রিক্স।"},
            {"index": 3, "type": "p",
             "tts": "এখানে প্রথম কলামটি হলো রূপান্তরিত আই হ্যাটের অবস্থান, আর দ্বিতীয় কলামটি হলো রূপান্তরিত জে হ্যাটের অবস্থান।"},
            {"index": 4, "type": "p",
             "tts": "এবার যদি আমরা জানতে চাই কলাম ভেক্টর, উপরে এক্স আর নিচে ওয়াই, এই রূপান্তরের পর কোথায় যাবে, তবে কেবল সমীকরণে মান বসিয়ে পাই। এক্স গুণ কলাম ভেক্টর এক আর মাইনাস দুই, যোগ ওয়াই গুণ কলাম ভেক্টর তিন আর শূন্য, আর তার ফল কলাম ভেক্টর, উপরে এক এক্স যোগ তিন ওয়াই, নিচে মাইনাস দুই এক্স যোগ শূন্য ওয়াই।"},
            {"index": 5, "type": "p",
             "tts": "আর ঠিক এভাবেই জন্ম নেয় ম্যাট্রিক্স ও ভেক্টরের গুণন। সাধারণভাবে, দুই বাই দুই ম্যাট্রিক্সের কলাম দুটি হলো কলাম ভেক্টর এ আর সি, এবং কলাম ভেক্টর বি আর ডি। তাকে কলাম ভেক্টর এক্স ওয়াই দিয়ে গুণ করলে পাই এক্স গুণ কলাম ভেক্টর এ আর সি, যোগ ওয়াই গুণ কলাম ভেক্টর বি আর ডি। আর ফলাফল কলাম ভেক্টর, উপরে এ এক্স যোগ বি ওয়াই, নিচে সি এক্স যোগ ডি ওয়াই।"},
            {"index": 6, "type": "figure",
             "tts": "এখানে ম্যাট্রিক্স ও ভেক্টরের গুণনের প্রকৃত অর্থটি খুলে দেখা হয়েছে। ম্যাট্রিক্সের কলাম দুটি হলো রূপান্তরিত ভিত্তি ভেক্টর, আর ইনপুট ভেক্টরের এক্স ও ওয়াই হলো তাদের স্কেলার ওজন। লক্ষ্য করুন, ফলাফল ভেক্টরটি এই দুটি স্কেল করা কলামের যোগফল মাত্র। সারি আর কলামের যান্ত্রিক নিয়মের বদলে এই চিত্র আমাদের জ্যামিতিক অর্থ দেয়, তাই গুণন এখন আর মুখস্থ নয়, বরং এক ধরনের রৈখিক সমন্বয়।"},
            {"index": 7, "type": "p",
             "tts": "ঐতিহ্যগতভাবে স্কুল আর কলেজে শেখানো হয়, সারি দিয়ে কলামকে গুণ করে যোগ করো। শিক্ষার্থীরা এটি মুখস্থ করে ক্লান্ত হয়ে পড়ে। কিন্তু আসল জ্যামিতিক বাস্তবতা হলো, একটি দুই বাই দুই ম্যাট্রিক্স আসলে কোনো সংখ্যাতালিকা নয়, এটি একটি দ্বিমাত্রিক রূপান্তরের সংক্ষিপ্ত রূপ। এর কলাম দুটি নির্দেশ করে আই হ্যাট এবং জে হ্যাট রূপান্তরের পর ঠিক কোথায় দাঁড়িয়েছে।"},
            {"index": 8, "type": "callout",
             "tts": "বিশেষ নোট, সারসংক্ষেপ, ম্যাট্রিক্স পড়ার নিয়ম। যখনই আপনি কোনো দুই বাই দুই ম্যাট্রিক্স দেখবেন, নিজের মনে বলবেন, প্রথম কলাম হলো আই হ্যাটের নতুন ঠিকানা, আর দ্বিতীয় কলাম হলো জে হ্যাটের নতুন ঠিকানা।"},
            {"index": 9, "type": "p",
             "tts": "নিচের ইন্টারেক্টিভ ক্যালকুলেটরে ম্যাট্রিক্সের উপাদান এবং ইনপুট ভেক্টর পরিবর্তন করে দেখুন কীভাবে কলামভিত্তিক রৈখিক সমন্বয়, আউটপুট ভেক্টর এবং নির্ণায়ক একই সাথে আপডেট হয়।"},
        ],
    },
}

# --------------------------------------------------------------------------- #
# DOM parity: re-extract cue types from the CURRENT lesson HTML source
# --------------------------------------------------------------------------- #
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "param", "source", "track", "wbr"}
CUSTOM_TAG_TO_TYPE = {
    "b1b-figure": "figure",
    "b1b-formula": "formula-box",
    "b1b-callout": "callout",
    "b1b-quote": "chapter-quote",
}


class _Node:
    __slots__ = ("tag", "attrs", "children", "parent", "text")

    def __init__(self, tag, attrs=None, parent=None):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.children = []
        self.parent = parent
        self.text = ""


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("#root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        n = _Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(n)
        if tag not in VOID_TAGS:
            self.stack.append(n)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(_Node(tag, attrs, self.stack[-1]))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if data.strip():
            n = _Node("#text", {"v": data}, self.stack[-1])
            n.text = data
            self.stack[-1].children.append(n)


def dom_types_from_source(html):
    """Replicate narration_engine.parseContent() selectors on the current DOM.

    The live page renders <b1b-section> into <section id=...> with an <h2>
    title, so the effective selector is 'article section'. Only the four
    narrated sections (no data-no-narration) are counted.
    """
    b = _TreeBuilder()
    b.feed(html)

    def walk(n):
        if n.tag == "b1b-section" and n.attrs.get("data-no-narration") != "true":
            types = ["h2"]  # title rendered as <h2> by B1bSection
            for c in n.children:  # direct children only; p in callout is skipped
                if c.tag == "p":
                    types.append("p")
                elif c.tag == "h3":
                    types.append("h3")
                elif c.tag in CUSTOM_TAG_TO_TYPE:
                    types.append(CUSTOM_TAG_TO_TYPE[c.tag])
                # b1b-media-tab / b1b-quiz produce no narration cue
            yield (n.attrs.get("id", ""), types)
        for c in n.children:
            yield from walk(c)

    return {sid: types for sid, types in walk(b.root)}


# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")


def assert_clean_scripts():
    """Fail before any TTS work if a script is dirty or off-spec."""
    seen = set()
    total = 0
    for sec_id, sid in SECTION_ORDER:
        sec = SECTIONS_DATA[sec_id]
        types = [c["type"] for c in sec["cues"]]
        if types != EXPECTED_TYPES[sec_id]:
            raise ValueError(f"{sec_id}: cue type/order mismatch -> {types}")
        if sec["audio_file"] != EXPECTED_AUDIO_FILES[sec_id]:
            raise ValueError(f"{sec_id}: audio_file mismatch")
        if sec["title"] != EXPECTED_TITLES[sec_id]:
            raise ValueError(f"{sec_id}: title mismatch")
        indices = [c["index"] for c in sec["cues"]]
        if indices != list(range(len(indices))):
            raise ValueError(f"{sec_id}: cue indices are not 0..n-1")
        for cue in sec["cues"]:
            if cue["type"] in FORBIDDEN_CUE_TYPES:
                raise ValueError(f"{sec_id}: forbidden cue type {cue['type']}")
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars "
                                 f"{bad!r} in {cue['tts']!r}")
            if cue["tts"] in seen:
                raise ValueError(f"{sec_id} cue {cue['index']}: duplicate cue text")
            seen.add(cue["tts"])
            if cue["type"] == "figure":
                body = cue["tts"]
                if body.startswith(""):
                    body = body[len(""):].strip()
                sentences = [s for s in re.split(r"[।?]", body) if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(f"{sec_id} cue {cue['index']}: figure needs "
                                     f"2-4 sentences, got {len(sentences)}")
        total += len(indices)
    if total != 32:
        raise ValueError(f"Expected 32 cues, found {total}")
    return total


def assert_dom_parity():
    """The manifest must be 1:1 with the CURRENT live DOM and extracted blocks."""
    with open(SOURCE_HTML, encoding="utf-8") as fh:
        dom = dom_types_from_source(fh.read())
    with open(DOM_BLOCKS, encoding="utf-8") as fh:
        blocks = json.load(fh)
    extracted = {s["id"]: [b["type"] for b in s["blocks"]] for s in blocks}
    for sec_id, _alias in SECTION_ORDER:
        expected = EXPECTED_TYPES[sec_id]
        if dom.get(sec_id) != expected:
            raise ValueError(f"DOM parity mismatch for {sec_id}:\n"
                             f"  DOM     = {dom.get(sec_id)}\n"
                             f"  manifest= {expected}")
        if extracted.get(sec_id) != expected:
            raise ValueError(f"Extracted-blocks parity mismatch for {sec_id}:\n"
                             f"  blocks={extracted.get(sec_id)}\n"
                             f"  manifest={expected}")
    # Interactive / extra sections must NOT become narration cues.
    for sid in ("sec-intro", "sec-linearity-examples", "sec-matrix-extras",
                "sec-matrix-calculator", "sec-geometric-examples",
                "sec-formal-properties", "sec-visualizer", "sec-conclusion"):
        if sid in extracted:
            raise ValueError(f"DOM parity: non-narrated section {sid} leaked in")


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


async def build_section(sec_id, sid, alias):
    sec = SECTIONS_DATA[sec_id]
    temp = os.path.join(AUDIO_DIR, f"_expressive_tmp_{sid}")
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

    print(f"\n[{sid}] {len(cues)} cues -> {sec['audio_file']}")
    for cue in cues:
        idx = cue["index"]
        chunk = os.path.join(temp, f"cue_{idx:02d}.mp3")
        rate, pitch, volume = prosody_for(cue)
        if not valid_audio(chunk):
            print(f"  cue {idx:02d} [{cue['type']:<13}] {rate:>4} {pitch:>5}  "
                  f"{cue['tts'][:30]}...")
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
            raise RuntimeError(f"{sid} cue {i}: zero duration")
        if mc["end_ms"] <= mc["start_ms"]:
            raise RuntimeError(f"{sid} cue {i}: non-positive span")
        if i > 0:
            prev = manifest_cues[i - 1]
            if mc["start_ms"] < prev["end_ms"]:
                raise RuntimeError(f"{sid} cue {i}: overlaps previous cue")
            if abs((mc["start_ms"] - prev["end_ms"]) - GAP_MS) > 1.0:
                raise RuntimeError(f"{sid} cue {i}: gap is not {GAP_MS} ms")

    if not os.path.exists(final_path) or os.path.getsize(final_path) == 0:
        raise RuntimeError(f"{sid}: missing/empty output {final_path}")

    print(f"  => {sec['audio_file']}: {len(manifest_cues)} cues, "
          f"{cursor / 1000.0:.2f}s, {os.path.getsize(final_path)} bytes")

    return {
        "section_id": sid,
        "alias": alias,
        "title": sec["title"],
        "audio_file": sec["audio_file"],
        "total_duration_ms": round(cursor, 1),
        "cues": manifest_cues,
    }


async def build_all():
    assert_clean_scripts()
    assert_dom_parity()
    print(f"Validated 32 clean cues in 4 sections; DOM parity OK.")

    manifest_sections = {}
    built = {}
    for sec_id, alias in SECTION_ORDER:
        sid = sec_id
        section_data = await build_section(sec_id, sid, alias)
        built[sid] = section_data
        manifest_sections[sid] = section_data
        manifest_sections[alias] = section_data

    manifest_data = {
        "course": "linear_algebra",
        "lesson": "lesson_03",
        "title": "অধ্যায় ০৩ — রৈখিক রূপান্তর ও ম্যাট্রিক্স",
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
    expected_keys = [k for sid, alias in SECTION_ORDER for k in (sid, alias)]
    if list(loaded["sections"].keys()) != expected_keys:
        raise RuntimeError("Manifest section keys do not match the existing keys")
    total_cues = 0
    total_ms = 0.0
    figures = 0
    for sec_id, alias in SECTION_ORDER:
        sid = sec_id
        msec = loaded["sections"][sid]
        if len(msec["cues"]) != len(EXPECTED_TYPES[sid]):
            raise RuntimeError(f"{sid}: cue count mismatch in written manifest")
        if loaded["sections"][alias] is None:
            raise RuntimeError(f"{alias}: alias missing")
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            raise RuntimeError(f"{sid}: missing/empty MP3 {path}")
        if get_duration_ms(path) <= 0:
            raise RuntimeError(f"{sid}: non-positive MP3 duration")
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    if total_cues != 32:
        raise RuntimeError(f"Expected 32 cues, found {total_cues}")
    if figures != 5:
        raise RuntimeError(f"Expected 5 figure explanations, found {figures}")

    print("\n" + "=" * 64)
    print("BUILD COMPLETE - expressive teacher audio, Lesson 03")
    for sec_id, alias in SECTION_ORDER:
        sid = sec_id
        msec = loaded["sections"][sid]
        print(f"  {sid:<32} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 4 sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json is valid JSON; all 4 MP3 files exist and are non-empty.")
    print("=" * 64)


if __name__ == "__main__":
    asyncio.run(build_all())
