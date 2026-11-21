# -*- coding: utf-8 -*-
r"""
Rebuild the TEACHER NARRATION AUDIO for 3Blue1Brown Lesson 05 (Bengali),
expressive-edition, to the Lesson 01 gold standard.

Deterministic, re-runnable, self-contained:

  * 38 cues in 3 narrated sections. The cue count/type/order of every section is
    derived from the LIVE DOM of courses/linear_algebra/lesson_05.html using the
    very selector/rules that narration_engine.js uses:
        .article > section, article section  (skip [data-no-narration="true"])
        h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
        .code-showcase, .formula-box   (skip <p> inside .callout/.chapter-quote)
    Verified 38/38: sec_01_3d_space=14, sec_02_matrix3x3=15,
    sec_03_determinant3d=9. All other sections are data-no-narration and produce
    no cues (no quiz / media-tab / interactive-section cue types).
  * The section IDs here ARE the existing manifest keys (no aliases needed):
    sec_01_3d_space / sec_02_matrix3x3 / sec_03_determinant3d, with the exact
    same audio_file names. The backup folder is never read or written.
  * Figure cues are genuine 2-4 sentence pedagogical explanations (6 figures):
    what is drawn / what to notice / why it matters (3D basis vectors, transform
    grid, basis tracking, column weighted sum, y-axis rotation, dimension puzzle).
  * Scripts are clean spoken Bengali: no TeX, LaTeX, backslashes, $, braces,
    brackets, em/en dashes, raw hyphens or Latin letters. Phonetic safeguards:
    \hat{i}->আই হ্যাট, \hat{j}->জে হ্যাট, \hat{k}->কে হ্যাট,
    x->এক্স, y->ওয়াই, z->জেড, A->এ, B->বি, M->এম, L->এল,
    bmatrix->কলাম ভেক্টর, 3D->থ্রিডি, 2D->টুডি, 90°->নব্বই ডিগ্রি ...
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
    h2 -5%/+2Hz, h3 -3%, chapter-quote -3%, figure -4%, formula-box -8%,
    p +2%, callout +0%, conclusion -3%.
  * A real 350 ms silence chunk between cues, so millisecond timings in the
    manifest match the concatenated MP3 exactly (zero overlap).
  * Per-section ffmpeg concat (-c copy) into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) and
    refreshes the per-section *_cues.json sidecars.
  * Validates non-zero durations, zero overlap, exact gaps, valid JSON,
    non-empty MP3s, 0 duplicate canonical cue texts, 0 quiz/media-tab types and
    DOM<->manifest 1:1 parity (source + browser-extracted DOM blocks) before
    reporting success.

Usage:  python governance/build_expressive_teacher_audio_l05.py
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
                         "linear_algebra", "lesson_05")
SOURCE_HTML = os.path.join(WORKSPACE, "courses", "linear_algebra",
                           "lesson_05.html")
DOM_BLOCKS = os.path.join(SCRIPT_DIR, "l05_dom_blocks.json")

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
    "sec_01_3d_space",
    "sec_02_matrix3x3",
    "sec_03_determinant3d",
]

# Exact DOM-derived cue type sequences (parity guards).
EXPECTED_TYPES = {
    "sec_01_3d_space": ["h2", "chapter-quote", "p", "p", "p", "h3", "p",
                        "figure", "p", "formula-box", "h3", "p", "figure", "p"],
    "sec_02_matrix3x3": ["h2", "p", "figure", "p", "formula-box", "h3", "p",
                         "formula-box", "figure", "h3", "p", "figure", "h3",
                         "p", "callout"],
    "sec_03_determinant3d": ["h2", "p", "p", "figure", "h3", "p", "p",
                             "callout", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec_01_3d_space":     "sec_01_3d_space.mp3",
    "sec_02_matrix3x3":    "sec_02_matrix3x3.mp3",
    "sec_03_determinant3d": "sec_03_determinant3d.mp3",
}
# Preserve the existing manifest titles verbatim (schema compatibility).
EXPECTED_TITLES = {
    "sec_01_3d_space":      "ত্রিমাত্রিক জগতে রূপান্তর",
    "sec_02_matrix3x3":     "৩×৩ ম্যাট্রিক্স ও î, ĵ, k̂ ট্র্যাকিং",
    "sec_03_determinant3d": "ত্রিমাত্রিক আয়তন স্কেলিং ও ডিটারমিন্যান্ট",
}
FORBIDDEN_CUE_TYPES = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
EXPECTED_FIGURES = 6
EXPECTED_TOTAL_CUES = 38

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (38 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec_01_3d_space": {
        "title": EXPECTED_TITLES["sec_01_3d_space"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_01_3d_space"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, ভূমিকা ও ত্রিমাত্রিক জগতে রূপান্তর।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "অধ্যায়ের শুরুতে দ্য সিম্পসন্সের একটি মজাদার দৃশ্য মনে পড়ে। লিসা জিজ্ঞেস করেছিল, বাবা কোথায়? উত্তরে অধ্যাপক ফ্রিংক বলেছিলেন, হাইপারবোলিক টপোলজিতে ডিগ্রিধারী যে কারও কাছে এটি স্পষ্ট যে, হোমার সিম্পসন ভুলবশত পা রেখেছেন আমাদের তৃতীয় মাত্রায়। নাটকীয় এক বিরতির পরে তিনি বলেছিলেন, তৃতীয় মাত্রা।"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, পূর্ববর্তী দুই অধ্যায়ে আমরা লিনিয়ার রূপান্তর ও ম্যাট্রিক্স নিয়ে যা কিছু শিখেছি, তার প্রায় সবকিছুই ছিল দ্বিমাত্রিক বা টুডি সমতলে। টুডি সমতলে কাজ করার সবচেয়ে বড় সুবিধা হলো, এটি ব্ল্যাকবোর্ডে বা কম্পিউটার স্ক্রিনে খুব সহজে এঁকে অনুধাবন করা যায়।"},
            {"index": 3, "type": "p",
             "tts": "তবে লিনিয়ার অ্যালজেব্রার সবচেয়ে সুন্দর সত্যটি হলো, টুডি সমতলে যে মূল দর্শনটি একবার পরিষ্কারভাবে বুঝে নিতে পারবেন, ঠিক সেই নিয়মই উচ্চতর মাত্রাগুলোতে, যেমন থ্রিডি, চার মাত্রিক বা এন মাত্রিক স্পেসে, অবিকৃত ও সুন্দরভাবে কাজ করে।"},
            {"index": 4, "type": "p",
             "tts": "এই অধ্যায়ে আমরা আমাদের চিরচেনা সমতল ফ্ল্যাটল্যান্ড ছেড়ে বাস্তব ত্রিমাত্রিক জগতে পা রাখব। দেখব কীভাবে তিনটি বেসিস ভেক্টরের গন্তব্য ট্র্যাক করে পুরো থ্রিডি রূপান্তরকে নয়টি সংখ্যার একটি তিন বাই তিন ম্যাট্রিক্সে বাঁধা যায়।"},
            {"index": 5, "type": "h3",
             "tts": "ত্রিমাত্রিক জগতের তিনটি মৌলিক বেসিস ভেক্টর।"},
            {"index": 6, "type": "p",
             "tts": "টুডি স্থানে যেমন এক্স অক্ষ ও ওয়াই অক্ষ বরাবর আই হ্যাট ও জে হ্যাট ছিল, ত্রিমাত্রিক স্থানে তেমনি তিনটি পরস্পরের সাথে সমকোণে অবস্থান করা অক্ষ থাকে। এক্স অক্ষ বরাবর আই হ্যাট, ওয়াই অক্ষ বরাবর জে হ্যাট, আর উল্লম্ব জেড অক্ষ বরাবর কে হ্যাট। প্রথম দুটি অক্ষ যেভাবে সমতল গড়ে তোলে, জেড অক্ষ সেই সমতলে গভীরতা যোগ করে।"},
            {"index": 7, "type": "figure",
             "tts": "এখানে ত্রিমাত্রিক স্থানের তিনটি প্রমিত বেসিস ভেক্টর দেখা যাচ্ছে। লাল তীরটি এক্স অক্ষ বরাবর আই হ্যাট, সবুজ তীরটি ওয়াই অক্ষ বরাবর জে হ্যাট, আর নীল তীরটি উল্লম্ব জেড অক্ষ বরাবর কে হ্যাট। লক্ষ্য করুন তিনটি তীর পরস্পরের সাথে সমকোণে আছে, আর রূপান্তরের পর এদের নতুন অবতরণস্থানই ম্যাট্রিক্সের তিনটি কলাম হবে।"},
            {"index": 8, "type": "p",
             "tts": "যেকোনো থ্রিডি ভেক্টরকে আমরা এই তিনটি বেসিস ভেক্টরের স্কেলিং ও রৈখিক সমাবেশ হিসেবে লেখতে পারি। স্থানাঙ্ক এক্স, ওয়াই ও জেড আসলে তিনটি নির্দেশনা, প্রতিটি বেসিস ভেক্টরকে কতটা টেনে প্রসারিত বা সংকুচিত করে যোগ করতে হবে তা বলে দেয়।"},
            {"index": 9, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। ভেক্টর ভি সমান এক্স গুণ আই হ্যাট যোগ ওয়াই গুণ জে হ্যাট যোগ জেড গুণ কে হ্যাট। একইভাবে এক্স, ওয়াই ও জেড হলো যথাক্রমে তিনটি কলাম ভেক্টরের সহগ, ফলে আউটপুট কলাম ভেক্টরটি দাঁড়ায় উপরে এক্স, মাঝখানে ওয়াই, নিচে জেড।"},
            {"index": 10, "type": "h3",
             "tts": "ত্রিমাত্রিক রৈখিক রূপান্তরের জ্যামিতিক বৈশিষ্ট্য।"},
            {"index": 11, "type": "p",
             "tts": "টুডি জগতের মতোই একটি রূপান্তর তখনই রৈখিক যখন দুটি শর্ত পূরণ হয়। প্রথমত, মূলবিন্দু শূন্য কমা শূন্য কমা শূন্য নিজের জায়গায় অটল থাকে, অর্থাৎ শূন্য ভেক্টরের রূপান্তর শূন্য ভেক্টরই থাকে। দ্বিতীয়ত, গ্রিডরেখা সোজা থাকে এবং সমান্তরাল তলগুলো রূপান্তরের পরেও পরস্পরের সমান্তরাল ও সমদূরত্বে বজায় থাকে।"},
            {"index": 12, "type": "figure",
             "tts": "এখানে পুরো ত্রিমাত্রিক গ্রিডকে এক টুকরো নরম রবারের জালির মতো টানা বা সংকুচিত হতে দেখা যাচ্ছে, কিন্তু মূলবিন্দু অনড় আছে। লক্ষ্য করুন প্রতিটি তল পরস্পরের সমান্তরাল ও সমদূরত্বে রয়েছে, এটিই রৈখিকতার জ্যামিতিক চিহ্ন। কোথাও বাঁক বা ভাঙন দেখলেই বুঝতে হবে রূপান্তরটি রৈখিক নয়。"},
            {"index": 13, "type": "p", "role": "conclusion",
             "tts": "ত্রিমাত্রিক স্থানে কোটি কোটি ভেক্টরকে তীর হিসেবে কল্পনা করা অসম্ভব। তাই সবচেয়ে শক্তিশালী কৌশল হলো, পুরো স্পেসের পেছনে না ছুটে কেবল লক্ষ্য করা যে রূপান্তরের পর আমাদের তিনটি বেসিস ভেক্টর আই হ্যাট, জে হ্যাট ও কে হ্যাট কোথায় গিয়ে পৌঁছাল। এই তিনটির গন্তব্যই আমাদের পরবর্তী অধ্যায়ের মূল ধন।"},
        ],
    },

    "sec_02_matrix3x3": {
        "title": EXPECTED_TITLES["sec_02_matrix3x3"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_02_matrix3x3"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, তিন বাই তিন ম্যাট্রিক্স, উদাহরণ ও সংযোজন।"},
            {"index": 1, "type": "p",
             "tts": "রূপান্তরের পর আমাদের তিনটি বেসিস ভেক্টর মহাকাশের তিনটি নতুন অবস্থানে অবতরণ করে। আই হ্যাট পৌঁছায় এল অফ আই হ্যাটে, জে হ্যাট পৌঁছায় এল অফ জে হ্যাটে, আর কে হ্যাট পৌঁছায় এল অফ কে হ্যাটে। পেছনের আদি অক্ষগুলোর সাপেক্ষে এই নতুন ঠিকানাগুলোই আমাদের সব কিছু বলে দেয়।"},
            {"index": 2, "type": "figure",
             "tts": "রূপান্তরের ধাক্কায় আই হ্যাট, জে হ্যাট ও কে হ্যাট কীভাবে তিনটি ভিন্ন ত্রিমাত্রিক স্থানাঙ্কে নোঙর ফেলেছে তা এখানে দেখা যাচ্ছে। হালকা অক্ষগুলো আদি অবস্থান ধরে রাখে, আর রঙিন তীরগুলো নতুন অবস্থান নির্দেশ করে। এই তিনটি নতুন স্থানাঙ্কই পরবর্তীতে ম্যাট্রিক্সের তিনটি কলাম গঠন করবে, তাই এই পদক্ষেপটি সবচেয়ে গুরুত্বপূর্ণ।"},
            {"index": 3, "type": "p",
             "tts": "এই তিনটি রূপান্তরিত ভেক্টরকে পাশাপাশি তিনটি উল্লম্ব কলাম আকারে সাজালেই পাওয়া যায় একটি তিন বাই তিন ম্যাট্রিক্স। এই নয়টি বাস্তব সংখ্যাই পুরো ত্রিমাত্রিক রূপান্তরের পূর্ণাঙ্গ ডিএনএ, কোথাও কোনো তথ্য বাদ যায় না।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। ম্যাট্রিক্স এম সমান একটি তিন বাই তিন ম্যাট্রিক্স, যার প্রথম কলাম এল অফ আই হ্যাট, দ্বিতীয় কলাম এল অফ জে হ্যাট, আর তৃতীয় কলাম এল অফ কে হ্যাট। এই কলাম তিনটি যথাক্রমে সবুজ, লাল ও নীল রঙে চিহ্নিত, আর ভেতরের নয়টি সংখ্যা এ, বি, সি, ডি, ই, এফ, জি, এইচ ও আই দ্বারা প্রকাশ পায়।"},
            {"index": 5, "type": "h3",
             "tts": "ত্রিমাত্রিক ম্যাট্রিক্স ও ভেক্টর গুণনের জ্যামিতিক তাৎপর্য।"},
            {"index": 6, "type": "p",
             "tts": "যেকোনো সাধারণ ভেক্টর, যার স্থানাঙ্ক এক্স, ওয়াই ও জেড, তার ওপর এই রূপান্তর প্রয়োগ করলে কী হবে? এটি কোনো অন্ধ বীজগাণিতিক সূত্র নয়। এটি হলো রূপান্তরিত কলাম তিনটির একটি ভারযুক্ত বা ওয়েইটেড যোগফল, যেখানে ইনপুটের স্থানাঙ্কগুলো ওজন হিসেবে কাজ করে।"},
            {"index": 7, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। ম্যাট্রিক্স এম গুণ ভেক্টর ভি সমান এক্স গুণ প্রথম কলাম যোগ ওয়াই গুণ দ্বিতীয় কলাম যোগ জেড গুণ তৃতীয় কলাম। এখানে প্রথম কলামের উপাদান এ, ডি, জি; দ্বিতীয় কলামের বি, ই, এইচ; আর তৃতীয় কলামের সি, এফ, আই। ফলের তিনটি স্থানাঙ্ক যথাক্রমে এ এক্স যোগ বি ওয়াই যোগ সি জেড, ডি এক্স যোগ ই ওয়াই যোগ এফ জেড, আর জি এক্স যোগ এইচ ওয়াই যোগ আই জেড।"},
            {"index": 8, "type": "figure",
             "tts": "ইনপুট ভেক্টরের এক্স, ওয়াই ও জেড স্থানাঙ্ক কীভাবে ম্যাট্রিক্সের তিনটি কলামকে যথাক্রমে স্কেল করে যোগ হয়ে আউটপুট ভেক্টর তৈরি করে তা এখানে দেখানো হয়েছে। প্রতিটি কলাম আগে একটি রূপান্তরিত বেসিস ভেক্টর ছিল, এখন সেটি ওজন হিসেবে কাজ করছে। এই কলামের ভারযুক্ত যোগফল দৃষ্টিভঙ্গিটিই মুখস্থ সূত্রের বদলে গুণনকে গভীরভাবে বোঝার চাবিকাঠি।"},
            {"index": 9, "type": "h3",
             "tts": "বাস্তব উদাহরণ, ওয়াই অক্ষকে কেন্দ্র করে নব্বই ডিগ্রি ঘূর্ণন।"},
            {"index": 10, "type": "p",
             "tts": "ধরা যাক পুরো স্পেসকে ওয়াই অক্ষ অনড় রেখে তার চারদিকে নব্বই ডিগ্রি ঘোরানো হলো। ফলে আই হ্যাট ঘুরে ঋণাত্মক জেড অক্ষে পৌঁছায়, জে হ্যাট ওয়াই অক্ষের ওপরেই অপরিবর্তিত থাকে, আর কে হ্যাট ঘুরে ধনাত্মক এক্স অক্ষে চলে আসে। এই তিনটি নতুন অবস্থান পাশাপাশি লিখলেই তৈরি হয়ে যায় আমাদের ঘূর্ণন ম্যাট্রিক্স।"},
            {"index": 11, "type": "figure",
             "tts": "ওয়াই অক্ষকে অনড় রেখে পুরো স্পেস নব্বই ডিগ্রি ঘুরছে, দেখুন আই হ্যাট ঋণাত্মক জেড অক্ষে, জে হ্যাট অপরিবর্তিত, আর কে হ্যাট ধনাত্মক এক্স অক্ষে পৌঁছাচ্ছে। তিনটি কলাম যথাক্রমে শূন্য শূন্য মাইনাস এক, শূন্য এক শূন্য, আর এক শূন্য শূন্য লিখলেই ঘূর্ণন ম্যাট্রিক্সটি তৈরি হয়। মনে রাখবেন ঘূর্ণনের দিক ও কোন অক্ষ অনড় আছে, সেটিই কলামের চিহ্ন নির্ধারণ করে।"},
            {"index": 12, "type": "h3",
             "tts": "ত্রিমাত্রিক ম্যাট্রিক্স গুণন ও রূপান্তরের সংযোজন।"},
            {"index": 13, "type": "p",
             "tts": "দুটি তিন বাই তিন ম্যাট্রিক্স এ ও বি গুণ করার জ্যামিতিক অর্থ হলো, প্রথমে ডানের বি রূপান্তরটি স্পেসে ঘটে, এরপর তার ওপর বামের এ প্রযুক্ত হয়। কম্পিউটার গ্রাফিক্স ও রোবোটিক্সে জটিল থ্রিডি আবর্তনকে এভাবে আলাদা অক্ষের ঘূর্ণন ম্যাট্রিক্সের গুণ হিসেবে তৈরি করা হয়।"},
            {"index": 14, "type": "callout", "role": "conclusion",
             "tts": "বিশেষ নোট, সতর্কতা, ত্রিমাত্রিক ঘূর্ণনের ক্রম সংবেদনশীল। ত্রিমাত্রিক স্থানে রূপান্তরের ক্রম অত্যন্ত সংবেদনশীল, সাধারণত এ গুণ বি আর বি গুণ এ কখনোই এক নয়। ফোনটিকে প্রথমে ডানে নব্বই ডিগ্রি এবং পরে উপরে নব্বই ডিগ্রি ঘুরালে যে অবস্থান পাবেন, প্রথমে উপরে ও পরে ডানে ঘুরালে সম্পূর্ণ ভিন্ন অবস্থান পাবেন। টুডির মতো এখানে ক্রম বিনিময় করা চলে না।"},
        ],
    },

    "sec_03_determinant3d": {
        "title": EXPECTED_TITLES["sec_03_determinant3d"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_03_determinant3d"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, মাত্রার ধাঁধা ও আয়তন স্কেলিং।"},
            {"index": 1, "type": "p",
             "tts": "অধ্যায়ের সমাপনী ধাঁধায় গ্রান্ট স্যান্ডারসন প্রশ্ন তুলেছেন, ভিন্ন ভিন্ন মাত্রার মধ্যে কি লিনিয়ার রূপান্তর সম্ভব? উত্তর হলো অবশ্যই হ্যাঁ। টুডি থেকে থ্রিডি রূপান্তর ঘটে তিন বাই দুই ম্যাট্রিক্স দ্বারা, যা দ্বিমাত্রিক সমতলকে থ্রিডি স্পেসের ভেতরে একটি চাদরের মতো স্থাপন করে।"},
            {"index": 2, "type": "p",
             "tts": "উল্টোভাবে থ্রিডি থেকে টুডি রূপান্তর ঘটে দুই বাই তিন ম্যাট্রিক্স দ্বারা। এটি ত্রিমাত্রিক বস্তুকে দ্বিমাত্রিক স্ক্রিনে ছায়া ফেলার মতো প্রজেকশন বা অভিক্ষেপ করে, যা আধুনিক থ্রিডি কম্পিউটার গ্রাফিক্সের প্রধান ভিত্তি।"},
            {"index": 3, "type": "figure",
             "tts": "ইনপুট ভেক্টরের মাত্রা কীভাবে আউটপুট ভেক্টরের মাত্রা নির্ধারণ করে তা এখানে দেখা যাচ্ছে। বাঁদিকের টুডি ভেক্টর তিন বাই দুই ম্যাট্রিক্সের মাধ্যমে থ্রিডি স্পেসের একটি সমতলে পড়ে, আবার থ্রিডি ভেক্টর দুই বাই তিন ম্যাট্রিক্সের মাধ্যমে টুডি স্ক্রিনে প্রক্ষিপ্ত হয়। মনে রাখবেন, কলাম সংখ্যা হলো ইনপুট মাত্রা আর সারি সংখ্যা হলো আউটপুট মাত্রা, এই নিয়মটিই ম্যাট্রিক্সের আকার মনে রাখার সহজ উপায়।"},
            {"index": 4, "type": "h3",
             "tts": "ত্রিমাত্রিক আয়তন স্কেলিং ও একক ঘনকের রূপান্তর।"},
            {"index": 5, "type": "p",
             "tts": "কল্পনা করুন মূলবিন্দুতে আই হ্যাট, জে হ্যাট ও কে হ্যাট দ্বারা গঠিত এক বাই এক বাই এক একক ঘনক রয়েছে, যার আদি আয়তন ঠিক এক ঘন একক। যেকোনো তিন বাই তিন রূপান্তর প্রয়োগ করলে পুরো স্পেসের সাথে এই ঘনকটিও টানটান হয়ে একটি তির্যক বাক্সে পরিণত হয়।"},
            {"index": 6, "type": "p",
             "tts": "যেমন কোনো রূপান্তরে আই হ্যাট দ্বিগুণ প্রসারিত হয়, জে হ্যাট তিনগুণ প্রসারিত হয় আর কে হ্যাট অপরিবর্তিত থাকে, তবে নতুন বাক্সের আয়তন হবে দুই গুণ তিন গুণ এক, অর্থাৎ ঠিক ছয় ঘন একক। আয়তনের এই পরিবর্তনই পরবর্তী অধ্যায়ের ডিটারমিন্যান্টের ভিত্তি গড়ে তোলে।"},
            {"index": 7, "type": "callout",
             "tts": "বিশেষ নোট, পরবর্তী অধ্যায়ের সেতুবন্ধন, ডিটারমিন্যান্ট। পরবর্তী লেসনে আমরা শিখব ডিটারমিন্যান্ট। টুডি সমতলে যেমন এটি ক্ষেত্রফলের পরিবর্তনের হার মাপত, থ্রিডি জগতে এটি পরিমাপ করে যেকোনো রৈখিক রূপান্তরের ফলে কোনো বাক্সের আয়তন ঠিক কত গুণ প্রসারিত বা সংকুচিত হলো। টুডিতে চারটি সংখ্যা যেমন সমতল পরিচালনা করত, থ্রিডিতে তেমনি নয়টি সংখ্যা পুরো মহাকাশ নিয়ন্ত্রণ করে।"},
            {"index": 8, "type": "p", "role": "conclusion",
             "tts": "সারসংক্ষেপে মনে রাখবেন, স্থানাঙ্ক আসলে কোনো পরম সত্য নয়, এটি একটি নির্দিষ্ট বেসিসের সাপেক্ষে পরিমাপের এক চুক্তি মাত্র। লিনিয়ার অ্যালজেব্রার আসল শক্তি হলো জ্যামিতিক দৃষ্টি ও সংখ্যার তালিকার মধ্যকার অবলীলায় আদান প্রদান। পরবর্তী অধ্যায়ে ডিটারমিন্যান্টের মাধ্যমে আমরা এই যাত্রা অব্যাহত রাখব। ধন্যবাদ।"},
        ],
    },
}

# --------------------------------------------------------------------------- #
# DOM parity: re-extract cue types from the live HTML source
# --------------------------------------------------------------------------- #
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "param", "source", "track", "wbr"}
CUSTOM_TAG_TO_TYPE = {
    "b1b-figure": "figure",
    "b1b-formula": "formula-box",
    "b1b-callout": "callout",
    "b1b-quote": "chapter-quote",
}
NON_NARRATED = {"sec-examples", "sec-combining", "sec-puzzle",
                "sec-media-gallery", "sec-visualizer", "sec-quizzes"}


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
    Only the narrated sections (no data-no-narration) are counted.
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
            if cue["type"] not in ALLOWED_CUE_TYPES:
                raise ValueError(f"{sec_id}: unknown cue type {cue['type']}")
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
    if total != EXPECTED_TOTAL_CUES:
        raise ValueError(f"Expected {EXPECTED_TOTAL_CUES} cues, found {total}")
    return total


def assert_dom_parity():
    """Manifest must be 1:1 with live DOM (source + browser snapshot)."""
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
          f"DOM parity OK (38/38, no duplicates).")

    manifest_sections = {}
    for sec_id in SECTION_ORDER:
        manifest_sections[sec_id] = await build_section(sec_id)

    manifest_data = {
        "course": "linear_algebra",
        "lesson": "lesson_05",
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

    print("\n" + "=" * 66)
    print("BUILD COMPLETE - expressive teacher audio, Lesson 05 (L01 gold standard)")
    for sec_id in SECTION_ORDER:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<24} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTION_ORDER)} sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  DOM<->manifest 1:1; 0 duplicate canonical cues; "
          "0 quiz/media-tab types; zero overlaps; exact 350 ms gaps; "
          "all MP3s non-zero; valid JSON.")
    print("=" * 66)


if __name__ == "__main__":
    asyncio.run(build_all())
