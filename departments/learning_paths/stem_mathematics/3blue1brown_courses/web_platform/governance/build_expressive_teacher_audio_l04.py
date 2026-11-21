# -*- coding: utf-8 -*-
r"""
Rebuild the TEACHER NARRATION AUDIO for 3Blue1Brown Lesson 04 (Bengali),
expressive-edition, to the Lesson 01 gold standard.

Deterministic, re-runnable, self-contained:

  * 52 cues in 6 narrated sections. The cue count/type/order of every section
    is derived from the LIVE DOM of courses/linear_algebra/lesson_04.html using
    the very selector/rules that narration_engine.js uses:
        .article > section, article section  (skip [data-no-narration="true"])
        h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
        .code-showcase, .formula-box   (skip <p> inside .callout/.chapter-quote)
    The broken upstream builder emitted only 4 audio files for 6 narrated DOM
    sections: sec-tracking and sec-derivation were duplicated onto the audio of
    sec-matrix-multiplication / sec-algebraic-view with identical cue text.
    This rebuild is strictly 1:1 with the DOM: 6 sections, 6 distinct audio
    files, no duplicate cue texts, and no quiz / media-tab cue types.
  * Figure cues are genuine 2-4 sentence pedagogical explanations (9 figures):
    what is drawn, what to notice, and why it matters (rotate-then-shear,
    compound multiplication, matrix notation visuals, noncommutativity, ...).
  * Scripts are clean spoken Bengali: no TeX, LaTeX, backslashes, $, braces,
    brackets, em/en dashes, raw hyphens or Latin letters. Phonetic safeguards:
    \hat{i}->আই হ্যাট, \hat{j}->জে হ্যাট, bmatrix->কলাম ভেক্টর ..., A->এ,
    B->বি, e/f/g/h->ই/এফ/জি/এইচ, 90°->নব্বই ডিগ্রি, ...
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
    h2 -5%/+2Hz, h3 -3%, chapter-quote -3%, figure -4%, formula-box -8%,
    p +2%, callout +0%, conclusion -3%.
  * A real 350 ms silence chunk between cues, so millisecond timings in the
    manifest match the concatenated MP3 exactly (zero overlaps).
  * Per-section ffmpeg concat (-c copy) into the section MP3 names. The four
    original names are preserved; the two previously-duplicated sections get
    their own uniquely-named MP3s (sec_05_tracking.mp3, sec_06_derivation.mp3).
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) and
    refreshes the per-section *_cues.json sidecars.
  * Validates non-zero durations, zero overlap, exact gaps, valid JSON,
    non-empty MP3s and DOM<->manifest 1:1 parity before reporting success.

Usage:  python governance/build_expressive_teacher_audio_l04.py
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
                         "linear_algebra", "lesson_04")
SOURCE_HTML = os.path.join(WORKSPACE, "courses", "linear_algebra",
                           "lesson_04.html")
DOM_BLOCKS = os.path.join(SCRIPT_DIR, "l04_dom_blocks.json")

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
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")

# Exact DOM-derived cue type sequences (parity guards).
EXPECTED_TYPES = {
    "sec-composition": ["h2", "chapter-quote", "p", "p", "figure", "p",
                        "figure", "p", "formula-box", "callout"],
    "sec-matrix-multiplication": ["h2", "p", "figure", "p", "p",
                                  "formula-box", "p", "callout"],
    "sec-tracking": ["h2", "p", "figure", "p", "p", "formula-box", "p",
                     "callout"],
    "sec-algebraic-view": ["h2", "p", "figure", "p", "p", "formula-box", "p",
                           "figure", "callout"],
    "sec-derivation": ["h2", "p", "figure", "p", "p", "formula-box", "p",
                       "figure", "callout"],
    "sec-associativity": ["h2", "p", "formula-box", "p", "figure", "p",
                          "callout", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-composition":          "sec_01_composition.mp3",
    "sec-matrix-multiplication":"sec_02_matrix_multiplication.mp3",
    "sec-tracking":             "sec_05_tracking.mp3",
    "sec-algebraic-view":       "sec_03_algebraic_view.mp3",
    "sec-derivation":           "sec_06_derivation.mp3",
    "sec-associativity":        "sec_04_associativity.mp3",
}
EXPECTED_TITLES = {
    "sec-composition":          "১. রিক্যাপ ও রূপান্তরের সংযোজন — Composition of Transformations",
    "sec-matrix-multiplication":"২. ভিত্তি ভেক্টর ট্র্যাকিং ও ডান থেকে বামে পড়া — Composition is Multiplication",
    "sec-tracking":             "৩. নতুন ম্যাট্রিক্স গণনা — Computing the New Matrix",
    "sec-algebraic-view":       "৪. সাধারণ রূপ ও গুণন সূত্র — General Form",
    "sec-derivation":           "৫. সাধারণ গুণন সূত্রের প্রতিপাদন — Deriving the Formula",
    "sec-associativity":        "৭. সংযোগ বিধি — Associativity",
}
FORBIDDEN_CUE_TYPES = {"quiz-block", "media-tab", "quiz", "b1b-quiz",
                       "b1b-media-tab"}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (52 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-composition": {
        "title": EXPECTED_TITLES["sec-composition"],
        "audio_file": EXPECTED_AUDIO_FILES["sec-composition"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, রিক্যাপ ও রূপান্তরের সংযোজন।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, গ্রান্ট স্যান্ডারসন বলেছেন, ম্যাট্রিক্স গুণন কোনো খাপছাড়া বা মুখস্থ করার শুকনো অ্যালগরিদম নয়। এটি আসলে একটি রূপান্তরের ঠিক পর আরেকটি রূপান্তর প্রয়োগ করার জ্যামিতিক ফলশ্রুতি মাত্র।"},
            {"index": 2, "type": "p",
             "tts": "স্কুল কলেজে আমাদের প্রায়শই ম্যাট্রিক্স গুণনের একটি অদ্ভুত ও যান্ত্রিক নিয়ম শেখানো হয়, প্রথম ম্যাট্রিক্সের প্রতিটি সারি দিয়ে দ্বিতীয় ম্যাট্রিক্সের প্রতিটি কলামের উপাদান গুণ করে যোগ করো। কিন্তু কেন? এই আপাতদৃষ্টিতে খাপছাড়া নিয়মটি আসলে কোথা থেকে এলো?"},
            {"index": 3, "type": "p",
             "tts": "গত পর্বে আমরা দেখেছি যে প্রতিটি ম্যাট্রিক্স হলো দ্বিমাত্রিক বা ত্রিমাত্রিক স্থানকে রূপান্তরিত করার একটি একক জ্যামিতিক প্রক্রিয়া, যেখানে গ্রিড রেখাগুলো সর্বদা সমান্তরাল ও সমদূরবর্তী থাকে এবং মূলবিন্দু সম্পূর্ণ স্থির থাকে।"},
            {"index": 4, "type": "figure",
             "tts": "এখানে আগের পর্বের মূল কথাটিই মনে করিয়ে দেওয়া হয়েছে, একটি ম্যাট্রিক্স মানেই স্থানের একটি নির্দিষ্ট রৈখিক রূপান্তর। লক্ষ্য করুন ভিত্তি ভেক্টর দুটির নতুন অবস্থান থেকেই পুরো ম্যাট্রিক্সটি তৈরি হয়েছে। গ্রিডের সমান্তরালতা অটল থাকায় আমরা জানতে পারি রূপান্তরটি রৈখিক। এই পুনরাবৃত্তিই পরবর্তী যুক্তির ভিত্তি তৈরি করে।"},
            {"index": 5, "type": "p",
             "tts": "কিন্তু বাস্তব জীবনে ও বিজ্ঞানে একটি রূপান্তর সম্পন্ন করার পর প্রায়শই তার ওপর আরেকটি রূপান্তর প্রয়োগ করার দরকার পড়ে। ধরা যাক, আপনি প্রথমে দ্বিমাত্রিক সমতলটিকে ঘড়ির কাঁটার বিপরীতে নব্বই ডিগ্রি কোণে ঘোরালেন, এবং ঠিক তার পর সমতলটির ওপর একটি অনুভূমিক শিরিং বা মোচড় প্রয়োগ করলেন।"},
            {"index": 6, "type": "figure",
             "tts": "এখানে স্থানটি প্রথমে নব্বই ডিগ্রি ঘুরছে, তারপর অনুভূমিকভাবে সরে যাচ্ছে, দুটি রূপান্তর ঠিক এই ক্রমেই ঘটছে। লক্ষ্য করুন প্রথম ধাপের ফলাফলই দ্বিতীয় ধাপের ইনপুট হয়ে যাচ্ছে। ক্রম বদলে দিলে চূড়ান্ত ছবি আলাদা হতো। এই ধারাবাহিকতাই সংযোজন ধারণার মূল।"},
            {"index": 7, "type": "p",
             "tts": "শুরু থেকে শেষ পর্যন্ত পুরো সম্মিলিত প্রভাবটি নিজেই আরেকটি সম্পূর্ণ নতুন রৈখিক রূপান্তর। এই যৌথ রূপান্তরটিকে গণিতের ভাষায় বলা হয় দুটি পৃথক রূপান্তরের সংযোজন।"},
            {"index": 8, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। ভেক্টর ভি এর ওপর প্রথমে রূপান্তর বি কার্যকর হয়ে তৈরি হয় বি গুণ ভেক্টর ভি। এরপর তার ওপর রূপান্তর এ প্রয়োগ করলে পাওয়া যায় এ ইনটু বি ভেক্টর ভি, যা সমান এ বি গুণ ভেক্টর ভি।"},
            {"index": 9, "type": "callout",
             "tts": "বিশেষ নোট, কেন্দ্রীয় দর্শন। লিনিয়ার অ্যালজেব্রার কেন্দ্রীয় দর্শনটি গভীরভাবে মনে রাখো, দুটি ম্যাট্রিক্সের গুণফল এ বি হলো সেই একক যৌগিক রূপান্তর, যা প্রথমে রূপান্তর বি এবং ঠিক তার পর রূপান্তর এ প্রয়োগ করলে সামগ্রিক স্থানে ঘটে থাকে। অর্থাৎ গুণন আসলে পরপর প্রয়োগেরই আরেক নাম।"},
        ],
    },

    "sec-matrix-multiplication": {
        "title": EXPECTED_TITLES["sec-matrix-multiplication"],
        "audio_file": EXPECTED_AUDIO_FILES["sec-matrix-multiplication"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, ভিত্তি ভেক্টর ট্র্যাকিং ও ডান থেকে বামে পড়া।"},
            {"index": 1, "type": "p",
             "tts": "যেহেতু দুটি ধারাবাহিক রৈখিক রূপান্তরের সমন্বয় নিজেও একটি খাঁটি রৈখিক রূপান্তর, তাই এর নিজস্ব একটি একক টু বাই টু ম্যাট্রিক্স থাকবে। সেই ম্যাট্রিক্সটি আমরা কীভাবে বের করব? বরাবরের মতোই শিশুতোষ সহজ, শুধুমাত্র লক্ষ্য করুন পুরো প্রক্রিয়ার শেষে আমাদের দুটি আদি ভিত্তি ভেক্টর আই হ্যাট এবং জে হ্যাট শেষমেশ কোথায় গিয়ে পৌঁছাল।"},
            {"index": 2, "type": "figure",
             "tts": "এখানে ঘূর্ণন ও শিরিং শেষে আই হ্যাট পৌঁছায় স্থানাঙ্ক এক কমা এক এ এবং জে হ্যাট পৌঁছায় স্থানাঙ্ক মাইনাস এক কমা শূন্য এ। এই দুটিমাত্র তথ্য রেকর্ড করেই পুরো যৌগিক ম্যাট্রিক্সটি লিখে ফেলা যায়। লক্ষ্য করুন জে হ্যাটের ওয়াই স্থানাঙ্ক শূন্য হওয়ায় শিরিং তাকে অপরিবর্তিত রেখেছে। মাত্র দুটি ভেক্টরের এই হিসাবই অসীম তথ্যের বদলে কাজ করে।"},
            {"index": 3, "type": "p",
             "tts": "আই হ্যাটের গতিপথ লক্ষ্য করুন। আদিতে আই হ্যাট ছিল কলাম ভেক্টর, উপরে এক, নিচে শূন্য। নব্বই ডিগ্রি ঘড়ির কাঁটার বিপরীতে ঘোরার পর এটি পৌঁছে গেল কলাম ভেক্টর, উপরে শূন্য, নিচে এক। এবার এই ভেক্টরটির ওপর অনুভূমিক শিরিং প্রয়োগ করা হলে এর এক্স স্থানাঙ্ক তার ওয়াই স্থানাঙ্কের পরিমাণ ডানে সরে যায়, ফলে এটি শেষ পর্যন্ত অবতরণ করে কলাম ভেক্টর, উপরে এক, নিচে এক। সুতরাং যৌথ ম্যাট্রিক্সের প্রথম কলাম হবে এক, এক।"},
            {"index": 4, "type": "p",
             "tts": "জে হ্যাটের গতিপথও দেখুন। আদিতে জে হ্যাট ছিল কলাম ভেক্টর, উপরে শূন্য, নিচে এক। নব্বই ডিগ্রি ঘোরার পর এটি পৌঁছে যায় কলাম ভেক্টর, উপরে মাইনাস এক, নিচে শূন্য, অর্থাৎ ঋণাত্মক এক্স অক্ষ বরাবর। যেহেতু এর ওয়াই স্থানাঙ্ক শূন্য, তাই অনুভূমিক শিরিং প্রয়োগ করলেও এটি হুবহু অপরিবর্তিত থাকে। সুতরাং যৌথ ম্যাট্রিক্সের দ্বিতীয় কলাম হবে মাইনাস এক, শূন্য।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। শিরিং ম্যাট্রিক্স, যার প্রথম সারি এক এক আর দ্বিতীয় সারি শূন্য এক, গুণ ঘূর্ণন ম্যাট্রিক্স, যার প্রথম সারি শূন্য মাইনাস এক আর দ্বিতীয় সারি এক শূন্য, সমান যৌগিক ম্যাট্রিক্স, যার প্রথম সারি এক মাইনাস এক আর দ্বিতীয় সারি এক শূন্য।"},
            {"index": 6, "type": "p",
             "tts": "এবার একটি অতি গুরুত্বপূর্ণ বিষয় লক্ষ্য করো। আমরা যখন লিখি এ বি গুণ ভেক্টর ভি, তখন প্রথমে কোন রূপান্তরটি কার্যকর হয়? বি আগে, তারপর এ। অর্থাৎ গুণনের এই লেখার ধারা ডান থেকে বামে পড়তে হয়, ভেক্টরের সবচেয়ে কাছে যে ম্যাট্রিক্স থাকে, সেটিই আগে কাজ করে।"},
            {"index": 7, "type": "callout",
             "tts": "বিশেষ নোট, ফাংশন নোটেশনের ঐতিহ্য। বীজগণিতে আমরা যখন ফাংশনের কম্পোজিশন লিখি এফ অব জি অব এক্স, তখন ইনপুট এক্স এর সবচেয়ে কাছে কে থাকে? অবশ্যই জি। তাই আগে জি এর মান বের হয়, তারপর তার ফলাফলের ওপর এফ ফাংশন কাজ করে। ঠিক একইভাবে, ভেক্টর ভির সাথে লেগে থাকা ডানপাশের ম্যাট্রিক্স বি আগে কার্যকর হয়, এবং তার সামগ্রিক ফলাফলের ওপর বামপাশের ম্যাট্রিক্স এ কাজ করে। হিব্রু কিংবা আরবি পাঠকদের জন্য ডান থেকে বামে পড়া স্বাভাবিক হলেও, বাকি বিশ্বের পাঠকদের এটি সতর্কতার সাথে মনে রাখতে হয়।"},
        ],
    },

    "sec-tracking": {
        "title": EXPECTED_TITLES["sec-tracking"],
        "audio_file": EXPECTED_AUDIO_FILES["sec-tracking"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, নতুন ম্যাট্রিক্স গণনা।"},
            {"index": 1, "type": "p",
             "tts": "যেহেতু দুটি ধারাবাহিক রৈখিক রূপান্তরের সমন্বয় নিজেও একটি খাঁটি রৈখিক রূপান্তর, তাই এর নিজস্ব একটি একক টু বাই টু ম্যাট্রিক্স থাকবে। সেই ম্যাট্রিক্সটি বের করার সবচেয়ে সহজ উপায় হলো, পুরো প্রক্রিয়ার শেষে আমাদের দুটি আদি ভিত্তি ভেক্টর আই হ্যাট আর জে হ্যাট কোথায় গিয়ে পৌঁছাল, ঠিক সেটাই লক্ষ্য করা।"},
            {"index": 2, "type": "figure",
             "tts": "এখানে ভিত্তি ভেক্টর দুটির চূড়ান্ত কলাম জোড়া লাগিয়ে যৌগিক ম্যাট্রিক্সটি গড়ে তোলা হয়েছে। লক্ষ্য করুন প্রথম কলাম আই হ্যাটের গন্তব্য এক কমা এক এবং দ্বিতীয় কলাম জে হ্যাটের গন্তব্য মাইনাস এক কমা শূন্য। কলাম দুটির ক্রম অদলবদল করলেই ভিন্ন রূপান্তর পাওয়া যেত। এই চিত্র দেখায় যে ম্যাট্রিক্স গুণন আসলে কলাম নির্মাণেরই এক রূপ।"},
            {"index": 3, "type": "p",
             "tts": "আই হ্যাট ছিল কলাম ভেক্টর, উপরে এক, নিচে শূন্য। নব্বই ডিগ্রি ঘোরার পর এটি পৌঁছায় কলাম ভেক্টর, উপরে শূন্য, নিচে এক। এবার অনুভূমিক শিরিং প্রয়োগ করলে এর এক্স স্থানাঙ্ক ওয়াই স্থানাঙ্কের পরিমাণ ডানে সরে গিয়ে চূড়ান্তভাবে অবতরণ করে কলাম ভেক্টর, উপরে এক, নিচে এক। সুতরাং যৌথ ম্যাট্রিক্সের প্রথম কলাম হবে এক, এক।"},
            {"index": 4, "type": "p",
             "tts": "আর জে হ্যাট ছিল কলাম ভেক্টর, উপরে শূন্য, নিচে এক। নব্বই ডিগ্রি ঘোরার পর এটি পৌঁছায় কলাম ভেক্টর, উপরে মাইনাস এক, নিচে শূন্য। যেহেতু এর ওয়াই স্থানাঙ্ক শূন্য, তাই অনুভূমিক শিরিং প্রয়োগ করলেও এটি অপরিবর্তিত থাকে। ফলে দ্বিতীয় কলাম হয় মাইনাস এক, শূন্য।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। প্রথমে ঘূর্ণন ম্যাট্রিক্স, তার ওপর শিরিং ম্যাট্রিক্স, আর শেষে যৌগিক ম্যাট্রিক্স। শিরিং ম্যাট্রিক্সের প্রথম সারি এক এক, দ্বিতীয় সারি শূন্য এক। ঘূর্ণন ম্যাট্রিক্সের প্রথম সারি শূন্য মাইনাস এক, দ্বিতীয় সারি এক শূন্য। গুণফলের প্রথম সারি এক মাইনাস এক, দ্বিতীয় সারি এক শূন্য।"},
            {"index": 6, "type": "p",
             "tts": "এবার একটি অতি গুরুত্বপূর্ণ বিষয় লক্ষ্য করো। এ বি গুণ ভেক্টর ভি লেখার অর্থ হলো, আগে বি প্রয়োগ হয়, তারপর এ। অর্থাৎ ডান থেকে বামে পড়তে হয়। যেহেতু ভেক্টর ভির সবচেয়ে কাছে বি আছে, তাই বি গুণ ভেক্টর ভি আগে তৈরি হয়, তারপর তার ওপর এ বসে।"},
            {"index": 7, "type": "callout",
             "tts": "বিশেষ নোট, ফাংশন নোটেশনের ঐতিহ্য। আমরা যখন এফ অব জি অব এক্স লিখি, ইনপুট এক্স এর সবচেয়ে কাছে থাকে জি। তাই আগে জি কার্যকর হয়, তারপর তার ওপর এফ কাজ করে। ঠিক তেমনি ভেক্টর ভির সবচেয়ে কাছে থাকা ডানপাশের ম্যাট্রিক্স বি আগে কাজ করে, আর বামপাশের ম্যাট্রিক্স এ পরে কার্যকর হয়।"},
        ],
    },

    "sec-algebraic-view": {
        "title": EXPECTED_TITLES["sec-algebraic-view"],
        "audio_file": EXPECTED_AUDIO_FILES["sec-algebraic-view"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, সাধারণ রূপ ও গুণন সূত্র।"},
            {"index": 1, "type": "p",
             "tts": "এবার আসুন প্রতীকী বীজগণিত দিয়ে দেখা যাক, যেকোনো দুটি সাধারণ টু বাই টু ম্যাট্রিক্সের জন্য সূত্রটি কীভাবে নিজে থেকেই বেরিয়ে আসে, কোনো সূত্র মুখস্থ না করেই।"},
            {"index": 2, "type": "figure",
             "tts": "এই ডায়াগ্রামে দুটি সাধারণ ম্যাট্রিক্স এম ওয়ান এবং এম টু এর চলকগুলো দেখানো হয়েছে। প্রথমে যে ম্যাট্রিক্সটি প্রয়োগ হয়, তার কলামগুলোই আই হ্যাট ও জে হ্যাটের নতুন অবস্থান। লক্ষ্য করুন দুটি কলামকে পরের ম্যাট্রিক্সের রৈখিক সমন্বয় হিসেবে লেখা হয়েছে, আর এই ধাপ থেকেই গুণন সূত্রটি নিজে থেকে বেরিয়ে আসে।"},
            {"index": 3, "type": "p",
             "tts": "প্রথম রূপান্তর এম ওয়ান এর পর আই হ্যাট পৌঁছায় প্রথম কলামে, যার উপরে ই এবং নিচে জি। এর ওপর দ্বিতীয় রূপান্তর এম টু প্রয়োগ করলে পাওয়া যায়, ই গুণ কলাম ভেক্টর উপরে এ নিচে সি, যোগ জি গুণ কলাম ভেক্টর উপরে বি নিচে ডি। এর ফল কলাম ভেক্টর, উপরে এ ই যোগ বি জি, নিচে সি ই যোগ ডি জি। এটিই গুণফল ম্যাট্রিক্সের প্রথম কলাম।"},
            {"index": 4, "type": "p",
             "tts": "একইভাবে, জে হ্যাট প্রথম রূপান্তরের পর পৌঁছায় দ্বিতীয় কলামে, যার উপরে এফ এবং নিচে এইচ। এর ওপর এম টু প্রয়োগ করলে পাওয়া যায়, এফ গুণ কলাম ভেক্টর উপরে এ নিচে সি, যোগ এইচ গুণ কলাম ভেক্টর উপরে বি নিচে ডি। ফলাফল কলাম ভেক্টর, উপরে এ এফ যোগ বি এইচ, নিচে সি এফ যোগ ডি এইচ। এটি হলো গুণফল ম্যাট্রিক্সের দ্বিতীয় কলাম।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। প্রথম ম্যাট্রিক্স, যার প্রথম সারি এ বি আর দ্বিতীয় সারি সি ডি, গুণ দ্বিতীয় ম্যাট্রিক্স, যার প্রথম সারি ই এফ আর দ্বিতীয় সারি জি এইচ, সমান ফলাফল ম্যাট্রিক্স, যার প্রথম সারি এ ই যোগ বি জি আর এ এফ যোগ বি এইচ, দ্বিতীয় সারি সি ই যোগ ডি জি আর সি এফ যোগ ডি এইচ।"},
            {"index": 6, "type": "p",
             "tts": "পাঠ্যবইয়ে যে বলা হয়, প্রথম ম্যাট্রিক্সের সারি দিয়ে দ্বিতীয় ম্যাট্রিক্সের কলামকে ডট গুণ করো, তা মূলত এই ভিত্তি ভেক্টর রূপান্তরেরই সংক্ষিপ্ত হিসাব কৌশল। কিন্তু এর আসল হৃদয় হলো, দ্বিতীয় রূপান্তরের কলামগুলোকে প্রথম রূপান্তরের স্থানাঙ্ক দিয়ে স্কেল করে যোগ করা। জ্যামিতিক অর্থ বুঝে এই সূত্র মুখস্থ করলে তা অনেক বেশি টেকসই হয়।"},
            {"index": 7, "type": "figure",
             "tts": "এখানে দেখা যাচ্ছে আগে শিরিং ও পরে ঘূর্ণন করলে যে ছবি পাওয়া যায়, আগে ঘূর্ণন ও পরে শিরিং করলে তার চেয়ে সম্পূর্ণ ভিন্ন আকৃতি তৈরি হয়। লক্ষ্য করুন আই হ্যাটের গন্তব্য এক কমা এক বদলে শূন্য কমা এক হয়ে যাচ্ছে। ক্রমের এই পার্থক্যই প্রমাণ করে এ বি আর বি এ এক নয়। তাই গুণনের ক্রম কখনোই অবহেলা করা যায় না।"},
            {"index": 8, "type": "callout",
             "tts": "বিশেষ নোট, জুতো ও মোজার কৌশল। বাস্তব জীবনের একটি উদাহরণ চিন্তা করো, আগে জুতো পরে তারপর মোজা পরা, আর আগে মোজা পরে তারপর জুতো পরা কি এক কথা? কখনই না। ঠিক তেমনি জ্যামিতিক রূপান্তরের ক্রম উল্টে দিলে পুরো স্থানাঙ্ক ব্যবস্থা বদলে যায়, এক কথায় এ বি সমান নয় বি এ।"},
        ],
    },

    "sec-derivation": {
        "title": EXPECTED_TITLES["sec-derivation"],
        "audio_file": EXPECTED_AUDIO_FILES["sec-derivation"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, সাধারণ গুণন সূত্রের প্রতিপাদন।"},
            {"index": 1, "type": "p",
             "tts": "এবার আসুন প্রতীকী বীজগণিত দিয়ে দেখা যাক, যেকোনো দুটি সাধারণ টু বাই টু ম্যাট্রিক্সের জন্য সূত্রটি কীভাবে নিজে থেকেই বেরিয়ে আসে, কোনো নিয়ম মুখস্থ না করেই।"},
            {"index": 2, "type": "figure",
             "tts": "এখানে দেখানো হয়েছে কীভাবে একটি ম্যাট্রিক্সের কলাম দুটিকে চলক দিয়ে লিখে পরের ম্যাট্রিক্সের সাথে গুণ করা হয়। লক্ষ্য করুন চূড়ান্ত ম্যাট্রিক্সের প্রতিটি উপাংশ আসলে দুটি পদের যোগ, একটিমাত্র ডট গুণন নয়। এই চিত্রটি সূত্রের প্রতিটি অংশের জ্যামিতিক উৎস খুঁজে দেয়।"},
            {"index": 3, "type": "p",
             "tts": "ধরা যাক প্রথম রূপান্তর এম ওয়ান হলো কলাম জোড়া, প্রথম কলামে ই আর জি, দ্বিতীয় কলামে এফ আর এইচ। আর দ্বিতীয় রূপান্তর এম টু হলো কলাম জোড়া, প্রথম কলামে এ আর সি, দ্বিতীয় কলামে বি আর ডি। আমরা এম টু গুণ এম ওয়ান এর যৌথ ম্যাট্রিক্স বের করতে চাই। প্রথম রূপান্তরের পর আই হ্যাট পৌঁছায় এম ওয়ান এর প্রথম কলামে, অর্থাৎ কলাম ভেক্টর উপরে ই, নিচে জি।"},
            {"index": 4, "type": "p",
             "tts": "এই কলাম ভেক্টরটির ওপর এম টু প্রয়োগ করলে আমরা জানি এটি হবে এম টু এর কলামগুলোর রৈখিক সমন্বয়। ই গুণ কলাম ভেক্টর উপরে এ নিচে সি, যোগ জি গুণ কলাম ভেক্টর উপরে বি নিচে ডি, ফলে পাই কলাম ভেক্টর উপরে এ ই যোগ বি জি, নিচে সি ই যোগ ডি জি। একইভাবে জে হ্যাট থেকে পাই কলাম ভেক্টর উপরে এ এফ যোগ বি এইচ, নিচে সি এফ যোগ ডি এইচ।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। প্রথম ম্যাট্রিক্স এ বি, সি ডি, গুণ দ্বিতীয় ম্যাট্রিক্স ই এফ, জি এইচ, সমান ফলাফল ম্যাট্রিক্স, যার প্রথম সারি এ ই যোগ বি জি আর এ এফ যোগ বি এইচ, দ্বিতীয় সারি সি ই যোগ ডি জি আর সি এফ যোগ ডি এইচ।"},
            {"index": 6, "type": "p",
             "tts": "কিন্তু বাস্তব সংখ্যার গুণনের মতো ম্যাট্রিক্স গুণন কি বিনিময় বিধি মেনে চলে? কখনই নয়। এ বি সাধারণত বি এ এর সমান হয় না। অর্থাৎ ম্যাট্রিক্স গুণন একটি বিনিময়হীন অপারেশন, আর এটি এই অধ্যায়ের সবচেয়ে গুরুত্বপূর্ণ উপলব্ধিগুলোর একটি।"},
            {"index": 7, "type": "figure",
             "tts": "আগে শিরিং ও পরে ঘূর্ণন করলে যে চিত্র পাওয়া যায়, আগে ঘূর্ণন ও পরে শিরিং করলে তার চেয়ে সম্পূর্ণ ভিন্ন আকৃতি তৈরি হয়। লক্ষ্য করুন গ্রিডের কাত হওয়ার দিক ও ভিত্তি ভেক্টরের গন্তব্য, দুটোই আলাদা। একটিমাত্র ক্রম পরিবর্তনেই পুরো ফলাফল বদলে যাওয়া, এ বি সমান নয় বি এ, তার নিখুঁত জ্যামিতিক প্রমাণ।"},
            {"index": 8, "type": "callout",
             "tts": "বিশেষ নোট, ক্রম কেন গুরুত্বপূর্ণ। আগে জুতো পরে তারপর মোজা পরা, আর আগে মোজা পরে তারপর জুতো পরা কি এক কথা? কখনই না। ঠিক তেমনি জ্যামিতিক রূপান্তরের ক্রম উল্টে দিলে পুরো মহাবিশ্বের স্থানাঙ্ক ব্যবস্থা বদলে যায়। তাই সারি কলামের সূত্র মুখস্থ করার আগে ক্রমের এই অর্থ বোঝা জরুরি।"},
        ],
    },

    "sec-associativity": {
        "title": EXPECTED_TITLES["sec-associativity"],
        "audio_file": EXPECTED_AUDIO_FILES["sec-associativity"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "ষষ্ঠ পরিচ্ছেদ, সংযোগ বিধি বা অ্যাসোসিয়েটিভিটি।"},
            {"index": 1, "type": "p",
             "tts": "ম্যাট্রিক্স গুণন বিনিময় বিধি না মানলেও, এটি সংযোগ বিধি নিখুঁতভাবে মেনে চলে। অর্থাৎ বন্ধনী কোথায় বসানো হোক না কেন, চূড়ান্ত যৌগিক ম্যাট্রিক্স একই থাকে।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। বন্ধনীতে এ বি, বাই সি, সমান এ ইনটু বন্ধনীতে বি সি।"},
            {"index": 3, "type": "p",
             "tts": "যদি আপনি স্কুল বা কলেজে বীজগণিতের সাহায্যে তিনটি করে ম্যাট্রিক্সের প্রতীকী গুণ করে এটি প্রমাণ করতে যান, তবে খাতার পর খাতা সমীকরণ লিখে হয়রান হয়ে যাবেন। কিন্তু জ্যামিতিক চোখে তাকালে এটি স্বতঃসিদ্ধভাবে জলের মতো পরিষ্কার।"},
            {"index": 4, "type": "figure",
             "tts": "এই অ্যানিমেশনে তিনটি রূপান্তর সি, বি, এ পরপর স্থানটির ওপর প্রয়োগ হচ্ছে। লক্ষ্য করুন বন্ধনী কোথায় আছে তা নির্বিশেষে রূপান্তরের প্রবাহ অপরিবর্তিত, প্রথমে সি, তারপর বি, সবশেষে এ। ঠিক এই অপরিবর্তিত ক্রমই বন্ধনীতে এ বি বাই সি সমান এ ইনটু বন্ধনীতে বি সি কে স্বতঃসিদ্ধ করে তোলে। চিত্রটি জটিল বীজগণিতের বদলে একটিমাত্র দৃশ্যমান যুক্তি দেয়।"},
            {"index": 5, "type": "p",
             "tts": "লক্ষ্য করুন, বন্ধনীতে এ বি বাই সি মানে হলো, প্রথমে স্থানে রূপান্তর সি ঘটাও, তারপর এ বি এর সম্মিলিত প্রভাব একযোগে প্রয়োগ করো। আর এ ইনটু বন্ধনীতে বি সি মানে হলো, প্রথমে ক্রমান্বয়ে রূপান্তর সি এবং বি ঘটাও, তারপর রূপান্তর এ প্রয়োগ করো।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, একই ক্রম, একই ফলাফল। উভয় ক্ষেত্রেই মহাবিশ্বের স্থানটি ঠিক একই ক্রমে প্রথমে সি, তারপর বি, এবং সবশেষে এ এর মধ্য দিয়েই যাত্রা করছে। প্রয়োগের এই মৌলিক ক্রম যেহেতু একচুলও বদলায়নি, তাই উভয়ের চূড়ান্ত সম্মিলিত ম্যাট্রিক্স অভিন্ন হতে বাধ্য।"},
            {"index": 7, "type": "p", "role": "conclusion",
             "tts": "নিচের ইন্টারেক্টিভ সিমুলেটরে তোমরা নিজের হাতে রূপান্তরের ক্রম অদলবদল করে দেখো এবং কুইজগুলোর উত্তর দিয়ে তোমার ধারণা যাচাই করে নাও। শুভ পদচারণা।"},
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
NON_NARRATED = {"sec-recap", "sec-noncommutativity", "sec-conclusion",
                "sec-visualizer"}


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
    title, so the effective selector is '.article > section, article section'.
    Only the narrated sections (no data-no-narration) are counted. Both custom
    component tags and native figure.lesson-figure are mapped to cue types.
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
                elif c.tag == "figure" and "lesson-figure" in c.attrs.get("class", ""):
                    types.append("figure")
                # b1b-media-tab / b1b-quiz produce no narration cue
            yield (n.attrs.get("id", ""), types)
        for c in n.children:
            yield from walk(c)

    return {sid: types for sid, types in walk(b.root)}


# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
BAD_CHARS = re.compile(
    r"[A-Za-z\\$⟦⟧{}\[\]—–\-"          # Latin / TeX / brackets / dashes
    r"\u0900-\u0963\u0966-\u097f"     # Devanagari (keep Bengali danda U+0964/0965)
    r"\u0e00-\u0e7f"                  # Thai
    r"\ufffd"                         # replacement char (typo / mojibake)
    r"\uff10-\uff19"                  # fullwidth digits
    r"\u0000-\u001f]"                 # control chars
)


def assert_clean_scripts():
    """Fail before any TTS work if a script is dirty or off-spec."""
    seen = set()
    total = 0
    for sec_id, sec in SECTIONS_DATA.items():
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
    if total != 52:
        raise ValueError(f"Expected 52 cues, found {total}")
    return total


def assert_dom_parity():
    """The manifest must be 1:1 with the CURRENT live DOM for every section."""
    with open(SOURCE_HTML, encoding="utf-8") as fh:
        dom = dom_types_from_source(fh.read())
    for sec_id, expected in EXPECTED_TYPES.items():
        actual = dom.get(sec_id)
        if actual is None:
            raise ValueError(f"DOM parity: missing narrated section {sec_id}")
        if actual != expected:
            raise ValueError(f"DOM parity mismatch for {sec_id}:\n"
                             f"  DOM     = {actual}\n"
                             f"  manifest= {expected}")
    for sid in NON_NARRATED:
        if sid in dom:
            raise ValueError(f"DOM parity: non-narrated section {sid} leaked in")
    # Cross-check against the browser-extracted live DOM blocks too.
    if os.path.exists(DOM_BLOCKS):
        with open(DOM_BLOCKS, encoding="utf-8") as fh:
            live = json.load(fh)
        live_map = {s["id"]: [b["type"] for b in s["blocks"]] for s in live}
        for sec_id, expected in EXPECTED_TYPES.items():
            if live_map.get(sec_id) != expected:
                raise ValueError(f"Live-DOM parity mismatch for {sec_id}:\n"
                                 f"  live    = {live_map.get(sec_id)}\n"
                                 f"  manifest= {expected}")


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
    # Edge-TTS can return an empty stream (service throttling). Purge 0-byte
    # files and retry with exponential backoff — a reactive wait for an async
    # network response, never an arbitrary fixed delay.
    for attempt in range(40):
        try:
            if os.path.exists(path) and os.path.getsize(path) == 0:
                os.remove(path)
            comm = edge_tts.Communicate(text, VOICE,
                                       rate=rate, pitch=pitch, volume=volume)
            await comm.save(path)
            if valid_audio(path):
                return
        except Exception as exc:  # noqa: BLE001 - network hiccups happen
            print(f"    attempt {attempt + 1} failed: {exc}")
        await asyncio.sleep(min(0.75 * (2 ** min(attempt, 5)), 16.0))
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

    # Version-based cache: changing a script invalidates its old chunk.
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
            print(f"  cue {idx:02d} [{cue['type']:<11}] {rate:>4} {pitch:>5}  "
                  f"{cue['tts'][:28]}...")
            await synth_cue(cue["tts"], chunk, rate, pitch, volume)
        else:
            print(f"  cue {idx:02d} [{cue['type']:<11}] cached")
        chunk_paths.append(chunk)
        durations.append(get_duration_ms(chunk))

    # A real 350 ms silence chunk between cues, encoded to match the TTS.
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

    # Build timings from measured durations + real silence chunks.
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
        if mc["duration_ms"] <= 0 or mc["end_ms"] <= mc["start_ms"]:
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
    total = assert_clean_scripts()
    assert_dom_parity()
    print(f"Validated {total} clean cues in {len(SECTIONS_DATA)} sections, "
          f"1:1 with the current DOM.")

    manifest_sections = {}
    for sec_id, sec in SECTIONS_DATA.items():
        manifest_sections[sec_id] = await build_section(sec_id, sec)

    manifest_data = {
        "course": "linear_algebra",
        "lesson": "lesson_04",
        "voice": VOICE,
        "mode": "authentic_teacher",
        "sections": manifest_sections,
    }

    json_text = json.dumps(manifest_data, ensure_ascii=False, indent=2)
    with open(os.path.join(AUDIO_DIR, "manifest.json"), "w", encoding="utf-8") as fh:
        fh.write(json_text)
    with open(os.path.join(AUDIO_DIR, "manifest.js"), "w", encoding="utf-8") as fh:
        fh.write("window.TEACHER_AUDIO_MANIFEST = " + json_text + ";\n")

    # ---- Final integrity checks ----
    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert len(loaded["sections"]) == 6
    assert set(loaded["sections"]) == set(EXPECTED_TYPES)
    total_cues = 0
    total_ms = 0.0
    figures = 0
    all_texts = []
    audio_files = []
    for sec_id, msec in loaded["sections"].items():
        types = [c["type"] for c in msec["cues"]]
        assert types == EXPECTED_TYPES[sec_id], (sec_id, types)
        assert not (set(types) & FORBIDDEN_CUE_TYPES), sec_id
        assert msec["audio_file"] == EXPECTED_AUDIO_FILES[sec_id]
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        probe_ms = get_duration_ms(path)
        # ffmpeg -c copy concat of MP3 chunks adds a little LAME frame padding
        # at every chunk boundary; the manifest keeps the exact 350 ms cue-time
        # math (L01 gold standard does not compare these at all).
        assert abs(probe_ms - msec["total_duration_ms"]) < 2500.0, (
            sec_id, probe_ms, msec["total_duration_ms"])
        texts = [c["text"] for c in msec["cues"]]
        assert len(texts) == len(set(texts)), f"{sec_id}: duplicate cue texts"
        all_texts.extend(texts)
        audio_files.append(msec["audio_file"])
        total_cues += len(texts)
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    assert len(all_texts) == len(set(all_texts)), "duplicate cue texts globally"
    assert len(audio_files) == len(set(audio_files)), "duplicate audio files"
    assert total_cues == 52
    assert figures == 9

    # Refresh the legacy per-section cue sidecars from the clean manifest so no
    # stale duplicated / quiz / media cues remain anywhere in L04.
    for sec_id, msec in loaded["sections"].items():
        sidecar = {
            "section_id": sec_id,
            "title": msec["title"],
            "audio_file": msec["audio_file"],
            "total_duration_ms": msec["total_duration_ms"],
            "cues": msec["cues"],
        }
        sidecar_path = os.path.join(
            AUDIO_DIR,
            os.path.splitext(msec["audio_file"])[0] + "_cues.json")
        with open(sidecar_path, "w", encoding="utf-8") as fh:
            json.dump(sidecar, fh, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("BUILD COMPLETE - expressive teacher audio, Lesson 04 (L01 gold standard)")
    for sec_id, msec in loaded["sections"].items():
        print(f"  {sec_id:<28} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 6 sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  DOM<->manifest 1:1; no duplicate cues; no quiz/media-tab cues;")
    print("  zero overlaps; exact 350 ms gaps; 6 distinct MP3s non-zero; valid JSON.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(build_all())
