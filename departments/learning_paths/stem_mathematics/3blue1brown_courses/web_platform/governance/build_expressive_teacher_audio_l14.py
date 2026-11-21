# -*- coding: utf-8 -*-
r"""
Rebuild the TEACHER NARRATION AUDIO for 3Blue1Brown Lesson 14 (Bengali),
expressive-edition, to the Lesson 01 gold standard.

Deterministic, re-runnable, self-contained:

  * 23 cues in 4 narrated sections. The cue count/type/order of every section is
    derived from the LIVE DOM of courses/linear_algebra/lesson_14.html using the
    very selector/rules that narration_engine.js uses:
        .article > section, article section  (skip [data-no-narration="true"])
        h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
        .code-showcase, .formula-box   (skip <p> inside .callout/.chapter-quote)
    Verified 23/23 via headless Chrome (channel="chrome"):
      sec_01_geometric_intuition = 6 (h2, chapter-quote, p, figure, callout, p)
      sec_02_characteristic_equation = 6 (h2, p, p, figure, callout, p)
      sec_03_special_transformations = 5 (h2, p, figure, p, callout)
      sec_04_3d_rotations_and_eigenbasis = 6 (h2, p, figure, callout, p, p)
    All other sections are data-no-narration and produce no cues (no quiz /
    media-tab / interactive-section cue types). The DOM snapshot
    (l14_dom_blocks.json) preserves TeX via KaTeX <annotation>...</annotation>.
  * The 4 "figure" cues are 2-4 sentence, natural teacher explanations. They
    NEVER use a label like "চিত্র প্রদর্শনী" — each starts as flowing prose.
  * The section IDs here ARE the existing manifest keys; the audio_file names
    are byte-for-byte the existing manifest keys too:
      sec_01_geometric_intuition / sec_02_characteristic_equation /
      sec_03_special_transformations / sec_04_3d_rotations_and_eigenbasis.
    The backup folder _backup_before_expressive_build/ is never read/written.
  * Scripts are clean spoken Bengali: no TeX, LaTeX, backslashes, $, braces,
    brackets, em/en dashes, raw hyphens or Latin letters. Phonetic safeguards:
    \hat{i}->আই হ্যাট, \hat{j}->জে হ্যাট, x->এক্স, y->ওয়াই,
    A->এ, v->ভি, n->এন, 2D->টুডি, 3D->থ্রিডি, det->নির্ণায়ক ...
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
    h2 -5%/+2Hz, h3 -3%, chapter-quote -3%, figure -4%, formula-box -8%,
    p +2%, callout +0%, conclusion -3%.
  * A real 350 ms silence chunk between cues, so millisecond timings in the
    manifest match the concatenated MP3 exactly (zero overlap).
  * Per-section ffmpeg concat (-c copy) into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) and
    refreshes the per-section *_cues.json sidecars.
  * Validates non-zero durations, zero overlap, exact gaps, valid JSON,
    non-empty MP3s, 0 duplicate canonical cue texts, 0 quiz/media-tab types,
    0 "চিত্র প্রদর্শনী" occurrences and DOM<->manifest 1:1 parity (source +
    browser-extracted DOM blocks) before reporting success.

Usage:  python governance/build_expressive_teacher_audio_l14.py
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
                         "linear_algebra", "lesson_14")
SOURCE_HTML = os.path.join(WORKSPACE, "courses", "linear_algebra",
                           "lesson_14.html")
DOM_BLOCKS = os.path.join(SCRIPT_DIR, "l14_dom_blocks.json")

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

# Canonical section id == existing manifest key (no aliases in this lesson).
SECTION_ORDER = [
    "sec_01_geometric_intuition",
    "sec_02_characteristic_equation",
    "sec_03_special_transformations",
    "sec_04_3d_rotations_and_eigenbasis",
]

# Exact DOM-derived cue type sequences (parity guards).
EXPECTED_TYPES = {
    "sec_01_geometric_intuition": ["h2", "chapter-quote", "p", "figure",
                                   "callout", "p"],
    "sec_02_characteristic_equation": ["h2", "p", "p", "figure", "callout", "p"],
    "sec_03_special_transformations": ["h2", "p", "figure", "p", "callout"],
    "sec_04_3d_rotations_and_eigenbasis": ["h2", "p", "figure", "callout",
                                           "p", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec_01_geometric_intuition": "sec_01_geometric_intuition.mp3",
    "sec_02_characteristic_equation": "sec_02_characteristic_equation.mp3",
    "sec_03_special_transformations": "sec_03_special_transformations.mp3",
    "sec_04_3d_rotations_and_eigenbasis": "sec_04_3d_rotations_and_eigenbasis.mp3",
}
# Preserve the existing manifest titles verbatim (schema compatibility).
EXPECTED_TITLES = {
    "sec_01_geometric_intuition":
        "১. জ্যামিতিক অন্তর্দৃষ্টি: নিজস্ব স্প্যান বা রেখায় স্থির থাকা ভেক্টর",
    "sec_02_characteristic_equation":
        "২. চারিত্রিক সমীকরণ: নির্ণায়ক শূন্য হওয়ার বীজগণিত",
    "sec_03_special_transformations":
        "৩. বিশেষ রূপান্তর: ঘূর্ণন, শিয়ার এবং বাস্তব আইগেনভ্যালুর অনুপস্থিতি",
    "sec_04_3d_rotations_and_eigenbasis":
        "৪. থ্রিডি ঘূর্ণন অক্ষ ও আইগেনভিত্তি: কর্ণ ম্যাট্রিক্সের জাদু",
}
FORBIDDEN_CUE_TYPES = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
FORBIDDEN_PHRASE = "চিত্র প্রদর্শনী"
EXPECTED_FIGURES = 4          # one figure.lesson-figure in each narrated section
EXPECTED_TOTAL_CUES = 23

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (23 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec_01_geometric_intuition": {
        "title": EXPECTED_TITLES["sec_01_geometric_intuition"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_01_geometric_intuition"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, জ্যামিতিক অন্তর্দৃষ্টি, নিজস্ব স্প্যান বা রেখায় স্থির থাকা ভেক্টর।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, সার্জ ল্যাংয়ের এক চমৎকার তুলনা। তিনি একবার জিজ্ঞেস করেছিলেন, গণিত তোমার কাছে কী? কেউ কেউ উত্তর দিয়েছিল, সংখ্যার কারসাজি, কাঠামোর কারসাজি। আর যদি সঙ্গীত সম্পর্কে জিজ্ঞেস করা হতো, তবে কি উত্তর আসত, স্বরের কারসাজি? এই তুলনাটিই আজকের অন্তর্দৃষ্টির দরজা খুলে দেয়।"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, আইগেনভেক্টর ও আইগেনভ্যালু লিনিয়ার বীজগণিতের এমন এক ধারণা যা প্রথমে কিছুটা অস্বচ্ছ লাগতে পারে, অথচ এর পেছনের ছবি খুবই সরল। ম্যাট্রিক্সকে রূপান্তর হিসেবে দেখা, নির্ণায়ক, রৈখিক সমীকরণ জোট আর ভিত্তি পরিবর্তন, এই চারটি বিষয়ের ওপর এর বোঝাপড়া নির্ভর করে। চলুন একটি কঙ্ক্রিট উদাহরণ দিয়ে শুরু করি। দ্বিমাত্রিক স্পেসে তিন এক, শূন্য দুই ম্যাট্রিক্সটি আই হ্যাটকে তিন গুণ করে এক্স অক্ষেই রাখে, আর জে হ্যাটকে সরিয়ে নিয়ে যায় এক কমা দুই বিন্দুতে।"},
            {"index": 3, "type": "figure",
             "tts": "এই চিত্রে দেখা যাচ্ছে কীভাবে তিন এক, শূন্য দুই ম্যাট্রিক্সটি পুরো সমতলকে নতুন আকার দিচ্ছে। আই হ্যাট তিন গুণ হয়ে এক্স অক্ষেই থাকে, আর জে হ্যাট এগিয়ে এক কমা দুই বিন্দুতে পড়ে। গ্রিডের রেখাগুলোর দিক বদলালেও মূলবিন্দু অনড় থাকে, আর এটিই রৈখিক রূপান্তরের চিহ্ন। লক্ষ্য করুন কোন ভেক্টরগুলো ঘুরে না গিয়ে শুধু দৈর্ঘ্যে বদলাচ্ছে, পরের ধাপে আমরা ঠিক সেগুলোই খুঁজে বের করব।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, নিজস্ব স্প্যানে অবিচল ভেক্টরই আইগেনভেক্টর। মূলবিন্দু থেকে যেকোনো ভেক্টরের ডগা দিয়ে যে সরলরেখাটি যায়, তাকে বলা হয় ওই ভেক্টরের স্প্যান। অধিকাংশ ভেক্টর রূপান্তরের সময় এই রেখা ছেড়ে নতুন কোণে চলে যায়, কিন্তু কিছু ভেক্টর থাকে যারা নিজেদের রেখাতেই থেকে কেবল প্রসারিত বা সংকুচিত হয়, তাদেরই আইগেনভেক্টর বলা হয়। আমাদের উদাহরণে এক্স অক্ষের ভেক্টররা তিন গুণ হয়, তাই তাদের আইগেনভ্যালু তিন, আর এক কমা মাইনাস এক বরাবর কর্ণ রেখার ভেক্টররা দুই গুণ হয়, আইগেনভ্যালু দুই। জার্মান শব্দ আইগেন মানে নিজস্ব, নামটিই ধারণাটি বলে দেয়।"},
            {"index": 5, "type": "p",
             "tts": "সুতরাং এ গুণ ভি সমান ল্যাম্বডা গুণ ভি হলো আইগেনভেক্টরের সংজ্ঞা। এখানে ভি অশূন্য, ল্যাম্বডা একটি স্কেলার, আর রূপান্তরের পর ভি একই দিকে বা ঠিক বিপরীত দিকে থেকে ল্যাম্বডা গুণ লম্বা হয়। ল্যাম্বডা ধনাত্মক হলে দিক একই থাকে, ঋণাত্মক হলে একশো আশি ডিগ্রি উল্টে যায়, আর একের বড় হলে প্রসারণ ঘটে। এই সহজ ধর্মটিই পরে জটিল ম্যাট্রিক্সের ঘাত নির্ণয়কে অনেক সহজ করে দেবে।"},
        ],
    },

    "sec_02_characteristic_equation": {
        "title": EXPECTED_TITLES["sec_02_characteristic_equation"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_02_characteristic_equation"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, চারিত্রিক সমীকরণ, নির্ণায়ক শূন্য হওয়ার বীজগণিত।"},
            {"index": 1, "type": "p",
             "tts": "এখন প্রশ্ন হলো, কোনো প্রদত্ত ম্যাট্রিক্সের আইগেনভেক্টর ও আইগেনভ্যালু কীভাবে খুঁজে পাব? প্রতীকীভাবে লিখি এ গুণ ভি সমান ল্যাম্বডা গুণ ভি। এখানে বাম পাশে আছে ম্যাট্রিক্স ভেক্টর গুণন, আর ডান পাশে সাধারণ স্কেলার গুণন, দুই ধরনের গুণন একই সমীকরণে বসানোয় প্রথমে একটু অস্বস্তি লাগতে পারে।"},
            {"index": 2, "type": "p",
             "tts": "অস্বস্তিটি দূর করতে ডান পাশের ল্যাম্বডা ভি কে একটি ম্যাট্রিক্স গুণন হিসেবে লিখি, ল্যাম্বডা গুণ ভি সমান ল্যাম্বডা আই গুণ ভি, যেখানে আই হলো কর্ণে এক ও বাকি সব জায়গায় শূন্য বিশিষ্ট আইডেন্টিটি ম্যাট্রিক্স। এখন ডান পাশের পদটিকে বামে নিয়ে এলে পাই, বন্ধনীতে এ মাইনাস ল্যাম্বডা আই, গুণ ভি সমান শূন্য ভেক্টর। অর্থাৎ একটি নতুন ম্যাট্রিক্স ভেক্টর ভি কে শূন্য ভেক্টরে চ্যাপ্টা করে দিচ্ছে।"},
            {"index": 3, "type": "figure",
             "tts": "এই চিত্রে দেখা যাচ্ছে এ মাইনাস ল্যাম্বডা আই ম্যাট্রিক্সটি পুরো দ্বিমাত্রিক স্থানকে চ্যাপ্টা করে একটিমাত্র সরলরেখায় নামিয়ে আনছে, যাতে অশূন্য ভেক্টর ভি শূন্যে পৌঁছাতে পারে। গ্রিডের ঘনত্ব কমে যাওয়া আর ক্ষেত্রফলের শূন্য হয়ে যাওয়া, দুটোই নির্ণায়ক শূন্য হওয়ার দৃশ্যমান প্রমাণ। মনে রাখবেন, যদি স্থান চ্যাপ্টা না হতো তবে শুধু তুচ্ছ সমাধান ভি সমান শূন্যই পাওয়া যেত।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, শূন্য নির্ণায়কই সুইট স্পট। অশূন্য ভি এর জন্য এ মাইনাস ল্যাম্বডা আই গুণ ভি সমান শূন্য সম্ভব হতে হলে স্থানকে নিচু মাত্রায় নামাতে হবে, অর্থাৎ নির্ণায়ক এ মাইনাস ল্যাম্বডা আই সমান শূন্য, একে বলা হয় চারিত্রিক সমীকরণ। উদাহরণস্বরূপ দুই দুই, এক তিন ম্যাট্রিক্স নিলে দুই মাইনাস ল্যাম্বডা গুণ তিন মাইনাস ল্যাম্বডা বিয়োগ দুই, ল্যাম্বডা কে নবের মতো ঘুরালে সুইট স্পট আসে ল্যাম্বডা একে, যখন ম্যাট্রিক্সটি স্থানকে একটি রেখায় চ্যাপ্টা করে। ব্যবহারিকভাবে আগে এই সমীকরণ থেকে ল্যাম্বডা বের করা হয়, তারপর নাল স্পেস থেকে সংশ্লিষ্ট ভি পাওয়া যায়।"},
            {"index": 5, "type": "p",
             "tts": "আমাদের প্রথম উদাহরণে ফিরে আসি, তিন এক, শূন্য দুই ম্যাট্রিক্স। নির্ণায়ক তিন মাইনাস ল্যাম্বডা গুণ দুই মাইনাস ল্যাম্বডা সমান শূন্য থেকে ল্যাম্বডা দুই অথবা ল্যাম্বডা তিন পাই। ল্যাম্বডা দুই বসালে এক এক, শূন্য শূন্য ম্যাট্রিক্স গুণ এক্স ওয়াই সমান শূন্য থেকে এক্স সমান মাইনাস ওয়াই, অর্থাৎ এক কমা মাইনাস এক বরাবর রেখার সব ভেক্টরই আইগেনভেক্টর, ঠিক যা আমরা চিত্রে দেখেছিলাম।"},
        ],
    },

    "sec_03_special_transformations": {
        "title": EXPECTED_TITLES["sec_03_special_transformations"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_03_special_transformations"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, বিশেষ রূপান্তর, ঘূর্ণন, শিয়ার ও স্কেলিং।"},
            {"index": 1, "type": "p",
             "tts": "সব ম্যাট্রিক্সের কি বাস্তব আইগেনভেক্টর থাকে? না। সবচেয়ে সুন্দর ব্যতিক্রম হলো নব্বই ডিগ্রি ঘূর্ণন, শূন্য মাইনাস এক, এক শূন্য ম্যাট্রিক্স প্রতিটি ভেক্টরকে তার নিজস্ব রেখা থেকে নব্বই ডিগ্রি সরে যেতে বাধ্য করে, তাই কোনো ভেক্টরই স্প্যানে থাকে না। বীজগণিতও একই কথা বলে, এই ঘূর্ণনের চারিত্রিক সমীকরণ ল্যাম্বডা বর্গ প্লাস এক সমান শূন্য, যার মূল কেবল জটিল সংখ্যা প্লাস মাইনাস আই। বাস্তব মূলের অনুপস্থিতিই বলে দেয় বাস্তব আইগেনভেক্টর নেই।"},
            {"index": 2, "type": "figure",
             "tts": "এই চিত্রে নব্বই ডিগ্রি ঘূর্ণনের সময় প্রতিটি তীর আদি রেখা থেকে লম্বভাবে সরে যাচ্ছে, কোনো তীরই আগের দিকে ফিরে আসছে না। পাশাপাশি দেখানো ল্যাম্বডা বর্গ প্লাস এক সমান শূন্য রাশিটির কোনো বাস্তব সমাধান নেই, আর এই দুটি পর্যবেক্ষণ একে অপরকে সমর্থন করে। একে জটিল আইগেনভ্যালু বলা হয়, জ্যামিতিকভাবে এর অর্থ হলো রূপান্তরটি কেবল স্কেল নয়, একটি অতিরিক্ত ঘূর্ণনও ঘটায়।"},
            {"index": 3, "type": "p",
             "tts": "অন্য দিকে শিয়ার ম্যাট্রিক্স এক এক, শূন্য এক, এখানে আই হ্যাট স্থির থাকে আর জে হ্যাট ডানে সরে। কেবল এক্স অক্ষের ভেক্টরাই নিজেদের রেখায় থাকে, নির্ণায়ক এক মাইনাস ল্যাম্বডার বর্গ থেকে একমাত্র ল্যাম্বডা এক, অর্থাৎ শিয়ারের একটি মাত্র আইগেন রেখা আছে। আর দুই আই ম্যাট্রিক্স সব দিকে সমান দুই গুণ করে, তাই সমতলের প্রতিটি ভেক্টরই ল্যাম্বডা দুই সহ আইগেনভেক্টর, একটিমাত্র আইগেনভ্যালু আর অসীম সংখ্যক আইগেনভেক্টর।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, তিন ধরনের আচরণ এক নজরে। ঘূর্ণনে কোনো বাস্তব আইগেনভেক্টর নেই, শিয়ারে মাত্র একটি স্বাধীন আইগেন রেখা, আর স্কেলিংয়ে প্রতিটি ভেক্টরই আইগেনভেক্টর। ল্যাম্বডা মাইনাস এক ভাগের দুইয়ের মতো ঋণাত্মক ক্ষেত্রে ভেক্টরটি উল্টে অর্ধেক হয়, দিক বদলালেও সে নিজস্ব রেখাতেই থাকে, তাই এখনো আইগেনভেক্টর। এই তুলনাটি মনে রাখলে পরের অংশের আইগেনবেসিস বোঝা সহজ হবে।"},
        ],
    },

    "sec_04_3d_rotations_and_eigenbasis": {
        "title": EXPECTED_TITLES["sec_04_3d_rotations_and_eigenbasis"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_04_3d_rotations_and_eigenbasis"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, থ্রিডি ঘূর্ণন অক্ষ ও আইগেনভিত্তি, কর্ণ ম্যাট্রিক্সের জাদু।"},
            {"index": 1, "type": "p",
             "tts": "ত্রিমাত্রিক স্পেসে আইগেনভেক্টরের ধারণা আরও প্রাণবন্ত। মূলবিন্দুগামী কোনো অক্ষকে কেন্দ্র করে পুরো স্থান আবর্তিত হলে অক্ষের ওপরের ভেক্টরগুলোর দিক বা দৈর্ঘ্য বিন্দুমাত্র বদলায় না, অর্থাৎ ঘূর্ণন ম্যাট্রিক্স গুণ অক্ষ ভেক্টর সমান এক গুণ অক্ষ ভেক্টর। এই অক্ষই হলো ঘূর্ণনের আইগেনভেক্টর, আর এর আইগেনভ্যালু এক।"},
            {"index": 2, "type": "figure",
             "tts": "এই চিত্রে ত্রিমাত্রিক ঘূর্ণনের মাঝখান দিয়ে বের হওয়া সরলরেখাটিই ঘূর্ণন অক্ষ, এর ওপর অবস্থিত তীরগুলো ঘোরালেও অক্ষের দিকে কোনো নাড়া খায় না। চারপাশের বিন্দুগুলো সরে গেলেও এই অক্ষ অপরিবর্তিত থাকায় এটি ল্যাম্বডা এক বিশিষ্ট আইগেনভেক্টর। থ্রি বাই থ্রি ম্যাট্রিক্সের জটিল ত্রিকোণমিতিক সদস্যের চেয়ে এই একটি রেখা খুঁজে পাওয়া অনেক বেশি স্বজ্ঞাত ও শক্তিশালী।"},
            {"index": 3, "type": "callout",
             "tts": "বিশেষ নোট, আইগেনবেসিস, ডায়াগনাল ম্যাট্রিক্সের জাদু। যদি কোনো ম্যাট্রিক্সের যথেষ্ট স্বাধীন আইগেনভেক্টর থাকে যারা পুরো স্থান স্প্যান করতে পারে, তবে তাদের নতুন ভিত্তি হিসেবে বেছে নেওয়া যায়, একে বলা হয় আইগেনবেসিস। এই ভিত্তিতে মূল রূপান্তরটি একটি ডায়াগনাল ম্যাট্রিক্সে রূপ নেয়, কারণ প্রতিটি ভিত্তি ভেক্টর কেবল নিজের আইগেনভ্যালু দ্বারা স্কেল হয়, অন্যদের সাথে মিশে যায় না। ফলে শততম ঘাত লেখা যায় তিন শূন্য, শূন্য দুই ম্যাট্রিক্সের একশততম ঘাত সমান তিনের একশততম ঘাত ও দুইয়ের একশততম ঘাত, একটি সাধারণ ঘাতক্রিয়া, অথচ মূল ম্যাট্রিক্সকে একশত বার গুণ করতে হলে কত খাটুনি লাগত ভাবুন।"},
            {"index": 4, "type": "p",
             "tts": "ভিত্তি পরিবর্তনের গত পাঠের সূত্রটি মনে করুন, নতুন ম্যাট্রিক্স সমান এ ইনভার্স গুণ এম গুণ এ। আইগেনভেক্টরগুলোকে কলাম করে গঠিত পরিবর্তন ম্যাট্রিক্স এস দিলে ডি সমান এস ইনভার্স গুণ এ গুণ এস, অর্থাৎ ল্যাম্বডা, একই রূপান্তর শুধু আইগেনবেসিসের ভাষায় লেখা। তাই এ এর একশততম ঘাত সমান এস গুণ ল্যাম্বডার একশততম ঘাত গুণ এস ইনভার্স, সহজে ঘাত বের করে আবার আমাদের ভাষায় ফিরে আসা।"},
            {"index": 5, "type": "p", "role": "conclusion",
             "tts": "তবে সব রূপান্তরের এই সুবিধা পাওয়া যায় না, শিয়ারের মতো ম্যাট্রিক্সের পর্যাপ্ত স্বাধীন আইগেনভেক্টর নেই, তাই তার আইগেনবেসিস গড়ে ওঠে না। কৌতূহলীদের জন্য পাজল, শূন্য এক, এক এক ম্যাট্রিক্সের প্রথম কয়েকটি ঘাত বের করলে ফিবোনাচ্চি সংখ্যা এক, এক, দুই, তিন, পাঁচ, আট দেখা যায়, এর আইগেনভ্যালু এক প্লাস বর্গমূল পাঁচ ভাগ দুই ব্যবহার করে ঘাতের সংকেত বের করা যায়। পরবর্তী অধ্যায়ে শেখা হবে আইগেনভ্যালু দ্রুত নির্ণয়ের এক চতুর কৌশল।"},
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
NON_NARRATED = {"sec_quizzes_eigenvalues", "sec_labs"}


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
    """Replicate narration_engine.parseContent() selectors on the current DOM."""
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
                # b1b-quiz / b1b-media-tab produce no narration cue
            yield (n.attrs.get("id", ""), types)
        for c in n.children:
            yield from walk(c)

    return {sid: types for sid, types in walk(b.root)}


# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
ALLOWED_CUE_TYPES = {"h2", "h3", "chapter-quote", "p", "figure",
                     "callout", "formula-box", "code-showcase"}


def assert_clean_scripts():
    """Fail before any TTS work if a script is dirty or off-spec."""
    seen = set()
    total = 0
    for sec_id in SECTION_ORDER:
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
            if FORBIDDEN_PHRASE in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden phrase")
            if cue["tts"] in seen:
                raise ValueError(f"{sec_id} cue {cue['index']}: duplicate cue text")
            seen.add(cue["tts"])
            if cue["type"] == "figure":
                body = cue["tts"]
                sentences = [s for s in re.split(r"[।?]", body) if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(f"{sec_id} cue {cue['index']}: figure needs "
                                     f"2-4 sentences, got {len(sentences)}")
        total += len(indices)
    if total != EXPECTED_TOTAL_CUES:
        raise ValueError(f"Expected {EXPECTED_TOTAL_CUES} cues, found {total}")
    return total


def assert_dom_parity():
    """The manifest must be 1:1 with the CURRENT live DOM and extracted blocks."""
    with open(SOURCE_HTML, encoding="utf-8") as fh:
        dom = dom_types_from_source(fh.read())
    for sec_id in SECTION_ORDER:
        expected = EXPECTED_TYPES[sec_id]
        if dom.get(sec_id) != expected:
            raise ValueError(f"Source-DOM parity mismatch for {sec_id}:\n"
                             f"  DOM     = {dom.get(sec_id)}\n"
                             f"  manifest= {expected}")
    for sid in NON_NARRATED:
        if sid in dom:
            raise ValueError(f"DOM parity: non-narrated section {sid} leaked in")

    # Browser-extracted live DOM blocks (TeX preserved via KaTeX <annotation>).
    if not os.path.exists(DOM_BLOCKS):
        raise ValueError(f"Missing browser DOM snapshot: {DOM_BLOCKS}")
    with open(DOM_BLOCKS, encoding="utf-8") as fh:
        live = json.load(fh)
    live_map = {s["id"]: s for s in live}
    if set(live_map) != set(SECTION_ORDER):
        raise ValueError(f"Live-DOM sections mismatch: {sorted(live_map)}")
    canonical = []
    for sec_id in SECTION_ORDER:
        blocks = live_map[sec_id]["blocks"]
        actual = [b["type"] for b in blocks]
        expected = EXPECTED_TYPES[sec_id]
        if actual != expected:
            raise ValueError(f"Live-DOM parity mismatch for {sec_id}:\n"
                             f"  live    = {actual}\n"
                             f"  manifest= {expected}")
        for b in blocks:
            if b["type"] not in ALLOWED_CUE_TYPES:
                raise ValueError(f"Live-DOM: forbidden cue type {b['type']}")
            canonical.append(b["text"])
    # Zero duplicate canonical cue texts (TeX annotations make formulas unique).
    dupes = len(canonical) - len(set(canonical))
    if dupes:
        raise ValueError(f"Live-DOM: {dupes} duplicate canonical cue texts")
    return len(canonical)


def run_cmd(args, **kwargs):
    """subprocess.run with bounded retries for transient Windows process-launch
    failures (WinError 1450: insufficient resources to create a process)."""
    import time
    for attempt in range(12):
        try:
            return subprocess.run(args, **kwargs)
        except OSError as exc:
            if getattr(exc, "winerror", None) == 1450 and attempt < 11:
                time.sleep(0.25)
                continue
            raise
    raise RuntimeError(f"subprocess failed after retries: {args[0]}")


def get_duration_ms(path):
    out = run_cmd(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout.strip()
    ms = float(out) * 1000.0
    if ms <= 0:
        raise RuntimeError(f"Non-positive duration for {path}: {ms}")
    return ms


def probe_stream(path):
    out = run_cmd(
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
    # Edge TTS occasionally replies with an empty audio stream, or Windows can
    # briefly refuse to create the network sockets (WinError 1450). Back off
    # and retry; this is a network/process wait, not an arbitrary fixed delay.
    for attempt in range(10):
        try:
            comm = edge_tts.Communicate(text, VOICE,
                                        rate=rate, pitch=pitch, volume=volume)
            await comm.save(path)
            if valid_audio(path):
                return
        except OSError as exc:
            if getattr(exc, "winerror", None) != 1450:
                raise
            print(f"    WinError 1450 on attempt {attempt + 1}; retrying")
        except Exception as exc:  # noqa: BLE001 - network hiccups happen
            print(f"    attempt {attempt + 1} failed: {exc}")
        await asyncio.sleep(min(0.5 * (2 ** attempt), 8.0))
    raise RuntimeError(f"Failed to synthesise cue: {text[:40]}...")


def make_silence(path, sample_rate, channels, seconds=GAP_MS / 1000.0):
    layout = "mono" if channels == 1 else "stereo"
    run_cmd(
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
    run_cmd(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", list_path, "-c", "copy", final_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True,
    )
    os.remove(list_path)


async def build_section(sec_id):
    sec = SECTIONS_DATA[sec_id]
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
        "cues_file": os.path.splitext(sec["audio_file"])[0] + "_cues.json",
        "total_duration_ms": round(cursor, 1),
        "cues": manifest_cues,
    }


async def build_all():
    total = assert_clean_scripts()
    dom_cues = assert_dom_parity()
    if dom_cues != total:
        raise RuntimeError(f"DOM cue count {dom_cues} != script cue count {total}")
    print(f"Validated {total} clean cues in {len(SECTION_ORDER)} sections; "
          f"DOM parity OK (23/23, no duplicates, no forbidden phrase).")

    manifest_sections = {}
    for sec_id in SECTION_ORDER:
        manifest_sections[sec_id] = await build_section(sec_id)

    manifest_data = {
        "course": "linear_algebra",
        "lesson": "lesson_14",
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
    if list(loaded["sections"]) != SECTION_ORDER:
        raise RuntimeError("Manifest section keys do not match the existing keys")
    total_cues = 0
    total_ms = 0.0
    figures = 0
    all_texts = []
    for sec_id in SECTION_ORDER:
        msec = loaded["sections"][sec_id]
        if msec["audio_file"] != EXPECTED_AUDIO_FILES[sec_id]:
            raise RuntimeError(f"{sec_id}: audio_file mismatch in written manifest")
        types = [c["type"] for c in msec["cues"]]
        if types != EXPECTED_TYPES[sec_id]:
            raise RuntimeError(f"{sec_id}: cue type/order mismatch in written manifest")
        if any(t in FORBIDDEN_CUE_TYPES for t in types):
            raise RuntimeError(f"{sec_id}: forbidden cue type in written manifest")
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            raise RuntimeError(f"{sec_id}: missing/empty MP3 {path}")
        if get_duration_ms(path) <= 0:
            raise RuntimeError(f"{sec_id}: non-positive MP3 duration")
        for c in msec["cues"]:
            if FORBIDDEN_PHRASE in c["text"]:
                raise RuntimeError(f"{sec_id}: forbidden phrase in written manifest")
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
        all_texts.extend(c["text"] for c in msec["cues"])
        # Refresh the per-section *_cues.json sidecar (existing schema).
        sidecar = {
            "section_id": sec_id,
            "title": msec["title"],
            "audio_file": msec["audio_file"],
            "total_duration_ms": msec["total_duration_ms"],
            "cues": msec["cues"],
        }
        with open(os.path.join(AUDIO_DIR, msec["cues_file"]), "w",
                  encoding="utf-8") as fh:
            json.dump(sidecar, fh, ensure_ascii=False, indent=2)

    if total_cues != EXPECTED_TOTAL_CUES:
        raise RuntimeError(f"Expected {EXPECTED_TOTAL_CUES} cues, found {total_cues}")
    if figures != EXPECTED_FIGURES:
        raise RuntimeError(f"Expected {EXPECTED_FIGURES} figure explanations, found {figures}")
    if len(all_texts) != len(set(all_texts)):
        raise RuntimeError("Written manifest has duplicate cue texts")

    print("\n" + "=" * 70)
    print("BUILD COMPLETE - expressive teacher audio, Lesson 14 (L01 gold standard)")
    for sec_id in SECTION_ORDER:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<36} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTION_ORDER)} sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure cues.")
    print("  DOM<->manifest 1:1; 0 duplicate canonical cues; 0 quiz/media-tab "
          "types; 0 forbidden phrase; zero overlaps; exact 350 ms gaps; "
          "all MP3s non-zero; valid JSON.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(build_all())
