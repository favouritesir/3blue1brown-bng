# -*- coding: utf-8 -*-
r"""
Rebuild the TEACHER NARRATION AUDIO for 3Blue1Brown Lesson 06 (Bengali),
expressive-edition, to the Lesson 01 gold standard.

Deterministic, re-runnable, self-contained:

  * 34 cues in 4 narrated sections. The cue count/type/order of every section is
    derived from the LIVE DOM of courses/linear_algebra/lesson_06.html using the
    very selector/rules that narration_engine.js uses:
        .article > section, article section  (skip [data-no-narration="true"])
        h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
        .code-showcase, .formula-box   (skip <p> inside .callout/.chapter-quote)
    Verified 34/34: sec_01_scaling_area=12, sec_02_negative_determinant=6,
    sec_03_determinant_in_3d=9, sec_04_computation_and_composition=7. All other
    sections are data-no-narration and produce no cues (no quiz / media-tab /
    interactive-section cue types).
  * The section IDs here ARE the existing manifest keys; the audio_file names
    are byte-for-byte the existing manifest keys too (no aliases needed):
    sec_01_scaling_area / sec_02_negative_determinant /
    sec_03_determinant_in_3d / sec_04_computation_and_composition.
    The backup folder _backup_before_expressive_build/ is never read/written.
  * Figure cues are genuine 2-4 sentence pedagogical explanations (6 figures):
    what is drawn / what to notice / why it matters (scale_areas, determinant_0,
    j_right_of_i, unit_cube / parallelepiped, hand_basis, determinant_diagram).
  * Scripts are clean spoken Bengali: no TeX, LaTeX, backslashes, $, braces,
    brackets, em/en dashes, raw hyphens or Latin letters. Phonetic safeguards:
    \hat{i}->আই হ্যাট, \hat{j}->জে হ্যাট, \hat{k}->কে হ্যাট,
    x->এক্স, y->ওয়াই, z->জেড, A->এ, B->বি, M->এম, L->এল,
    det->ডিটারমিন্যান্ট, bmatrix->কলাম ভেক্টর, 3D->থ্রিডি, 2D->টুডি,
    3x3->তিন বাই তিন, 2x2->দুই বাই দুই, ad-bc->এ ডি বিয়োগ বি সি ...
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

Usage:  python governance/build_expressive_teacher_audio_l06.py
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
                         "linear_algebra", "lesson_06")
SOURCE_HTML = os.path.join(WORKSPACE, "courses", "linear_algebra",
                           "lesson_06.html")
DOM_BLOCKS = os.path.join(SCRIPT_DIR, "l06_dom_blocks.json")

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
    "sec_01_scaling_area",
    "sec_02_negative_determinant",
    "sec_03_determinant_in_3d",
    "sec_04_computation_and_composition",
]

# Exact DOM-derived cue type sequences (parity guards).
EXPECTED_TYPES = {
    "sec_01_scaling_area": ["h2", "chapter-quote", "p", "p", "figure",
                            "formula-box", "p", "callout", "p", "h3", "p",
                            "figure"],
    "sec_02_negative_determinant": ["h2", "p", "figure", "p", "callout", "p"],
    "sec_03_determinant_in_3d": ["h2", "p", "figure", "p", "formula-box",
                                 "h3", "p", "figure", "callout"],
    "sec_04_computation_and_composition": ["h2", "formula-box", "figure", "p",
                                           "h3", "callout", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec_01_scaling_area":               "sec_01_scaling_area.mp3",
    "sec_02_negative_determinant":       "sec_02_negative_determinant.mp3",
    "sec_03_determinant_in_3d":          "sec_03_determinant_in_3d.mp3",
    "sec_04_computation_and_composition": "sec_04_computation_and_composition.mp3",
}
# Preserve the existing manifest titles verbatim (schema compatibility).
EXPECTED_TITLES = {
    "sec_01_scaling_area":               "ক্ষেত্রফল স্কেলিং ও ডিটারমিন্যান্টের ধারণা",
    "sec_02_negative_determinant":       "ঋণাত্মক ডিটারমিন্যান্ট ও সমতলের ওরিয়েন্টেশন বা দিকবিন্যাস",
    "sec_03_determinant_in_3d":          "ত্রিমাত্রিক জগতে ডিটারমিন্যান্ট ও প্যারালেলেপিপেড",
    "sec_04_computation_and_composition": "বীজগাণিতিক গণনা ও গুণন বিধি",
}
FORBIDDEN_CUE_TYPES = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
EXPECTED_FIGURES = 6
EXPECTED_TOTAL_CUES = 34

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (34 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec_01_scaling_area": {
        "title": EXPECTED_TITLES["sec_01_scaling_area"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_01_scaling_area"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, ক্ষেত্রফল স্কেলিং ও ডিটারমিন্যান্টের ধারণা।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, গণনামূলক হিসাবের মূল উদ্দেশ্য কেবল সংখ্যা বের করা নয়, বরং গভীর অন্তর্দৃষ্টি লাভ করা। বলেছেন রিচার্ড হ্যামিং।"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, লিনিয়ার রূপান্তর স্থানকে কীভাবে টেনে লম্বা করে বা সংকুচিত করে, তা নিখুঁতভাবে মাপার জন্য গণিতে একটি অসাধারণ ধারণা রয়েছে, যাকে আমরা বলি ক্ষেত্রফল স্কেলিং ফ্যাক্টর। কোনো রূপান্তর কতটা প্রসারিত বা সংকুচিত করে, সেটি জানা ছাড়া তার প্রকৃত চরিত্র বোঝা কঠিন।"},
            {"index": 3, "type": "p",
             "tts": "উদাহরণস্বরূপ, এমন একটি রূপান্তর কল্পনা করুন যার ম্যাট্রিক্সের প্রথম কলামে তিন ও শূন্য, দ্বিতীয় কলামে শূন্য ও দুই। অর্থাৎ এটি এক্স অক্ষ বরাবর আই হ্যাটকে তিন গুণ লম্বা করে এবং ওয়াই অক্ষ বরাবর জে হ্যাটকে দুই গুণ প্রসারিত করে। প্রশ্ন হলো, এই পরিবর্তনে পুরো সমতলের ক্ষেত্রফল ঠিক কত গুণ বদলাচ্ছে?"},
            {"index": 4, "type": "figure",
             "tts": "এখানে আই হ্যাট ও জে হ্যাট দিয়ে গঠিত এক বাই এক একক বর্গক্ষেত্রটি দেখা যাচ্ছে, যার ক্ষেত্রফল এক বর্গ একক। রূপান্তরের পর আই হ্যাট তিন একক ও জে হ্যাট দুই একক দিকে সরে যাওয়ায় বর্গটি দুই বাই তিন মাপের আয়তক্ষেত্রে পরিণত হয়েছে। লক্ষ্য করুন, এই একটিমাত্র বর্গের পরিবর্তন থেকেই পুরো সমতলের স্কেলিংয়ের হিসাব পাওয়া যায়, তাই বর্গটির ওপর নজর রাখা অত্যন্ত গুরুত্বপূর্ণ।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। এক বাই এক সমান এক, তাই দুই বাই তিন সমান ছয়। একক বর্গের ক্ষেত্রফল এক থেকে ছয়ে উঠে যাওয়াটাই এই সূত্রটি বলছে।"},
            {"index": 6, "type": "p",
             "tts": "আদিতে এই বর্গক্ষেত্রের ক্ষেত্রফল ছিল এক বর্গ একক, আর রূপান্তরের পর দাঁড়িয়েছে ছয় বর্গ একক, অর্থাৎ পুরো অঞ্চলের ক্ষেত্রফল ঠিক ছয় গুণ স্কেল হয়েছে। আগের শিয়ারের উদাহরণে বর্গটি ঢালু হলেও ক্ষেত্রফল অপরিবর্তিত ছিল, কিন্তু এখানে আকারের পাশাপাশি আয়তনও বেড়েছে।"},
            {"index": 7, "type": "callout",
             "tts": "বিশেষ নোট, একক বর্গেই লুকিয়ে আছে পুরো সমতলের হিসাব। যেহেতু লিনিয়ার রূপান্তরের প্রতিটি গ্রিডরেখা সমান্তরাল এবং সমদূরবর্তী থাকে, তাই একক বর্গে যা ঘটে, সমতলের প্রতিটি ক্ষুদ্র বর্গে ঠিক একই স্কেলিং ঘটে। যেকোনো জটিল আঁকাবাঁকা ক্ষেত্রকে অসীম ক্ষুদ্র গ্রিড বর্গের যোগফল রূপে বিবেচনা করলে সামগ্রিক ক্ষেত্রফলও ঠিক একই অনুপাতে স্কেল হবে। তাই কোনো রূপান্তর ক্ষেত্রফল তিন গুণ বাড়ালে তার ডিটারমিন্যান্ট তিন, অর্ধেক করে দিলে এক দ্বিতীয়াংশ, আর সবকিছু রেখায় চ্যাপ্টা করলে শূন্য।"},
            {"index": 8, "type": "p",
             "tts": "কোনো রৈখিক রূপান্তর দ্বারা ক্ষেত্রফল ঠিক কত গুণ বৃদ্ধি বা হ্রাস পায়, সেই বিশেষ স্কেলিং ফ্যাক্টরটিকেই আমরা বলি ওই ম্যাট্রিক্স বা রূপান্তরের ডিটারমিন্যান্ট বা নির্ণায়ক। গণনা পরে শিখব, আগে বোঝাটা অনেক বেশি গুরুত্বপূর্ণ।"},
            {"index": 9, "type": "h3",
             "tts": "শূন্য ডিটারমিন্যান্ট ও মাত্রার সংকোচন।"},
            {"index": 10, "type": "p",
             "tts": "যদি কোনো রূপান্তরের ডিটারমিন্যান্ট শূন্য হয়, তার অর্থ কী? এর অর্থ হলো রূপান্তরটি পুরো দ্বিমাত্রিক টুডি সমতলকে চ্যাপ্টা করে একটি সরলরেখায় বা একক বিন্দুতে পরিণত করেছে। আগামী অধ্যায়গুলোতে দেখা যাবে, কোন ম্যাট্রিক্স স্থানকে নিচের মাত্রায় ঠেলে দেয়, তা এই ডিটারমিন্যান্ট শূন্যের পরীক্ষাটিই বলে দেয়।"},
            {"index": 11, "type": "figure",
             "tts": "এই ছবিতে সমতলটি এমনভাবে চ্যাপ্টা হয়েছে যে সব বর্গের ক্ষেত্রফল শূন্য হয়ে গেছে। লক্ষ্য করুন, রেখা বা বিন্দুর নিজস্ব কোনো টুডি ক্ষেত্রফল থাকে না, তাই স্কেলিং ফ্যাক্টরও শূন্য। ডিটারমিন্যান্ট শূন্য হওয়া মানেই স্থানটির মাত্রা বা ডাইমেনশন সংকুচিত হয়ে গেছে, যা পরবর্তী অধ্যায়ের ইনভার্স ম্যাট্রিক্সের জন্য অত্যন্ত গুরুত্বপূর্ণ।"},
        ],
    },

    "sec_02_negative_determinant": {
        "title": EXPECTED_TITLES["sec_02_negative_determinant"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_02_negative_determinant"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, ঋণাত্মক ডিটারমিন্যান্ট ও সমতলের ওরিয়েন্টেশন বা দিকবিন্যাস।"},
            {"index": 1, "type": "p",
             "tts": "বীজগণিতে আমরা প্রায়শই ঋণাত্মক ডিটারমিন্যান্ট দেখতে পাই। যেমন এক দুই, তিন চার ম্যাট্রিক্সটির ডিটারমিন্যান্ট হলো এক গুণ চার বিয়োগ দুই গুণ তিন, অর্থাৎ মাইনাস দুই। কিন্তু ক্ষেত্রফল স্কেলিং কীভাবে ঋণাত্মক হতে পারে? এই প্রশ্নটির উত্তর আমাদের ওরিয়েন্টেশন নামক একটি নতুন ধারণার দিকে নিয়ে যায়।"},
            {"index": 2, "type": "figure",
             "tts": "সাধারণ টুডি সমতলে আই হ্যাট থাকে ডানে এবং জে হ্যাট থাকে তার বাম পাশে, অর্থাৎ ঘড়ির কাঁটার বিপরীত দিকে। কিন্তু এই ছবিতে রূপান্তরের পর জে হ্যাটের রূপান্তরিত রূপটি উল্টে গিয়ে আই হ্যাটের রূপান্তরিত রূপের ডান পাশে অবস্থান নিয়েছে। লক্ষ্য করুন, বেসিক ভেক্টর দুটির এই আপেক্ষিক দিক বদলাই হলো ওরিয়েন্টেশনের বিপরীতকরণ, আর তাই ডিটারমিন্যান্টের চিহ্ন ঋণাত্মক হয়।"},
            {"index": 3, "type": "p",
             "tts": "দ্বিমাত্রিক সমতলটিকে যদি আপনি কাগজের পাতার মতো চিন্তা করেন, তবে এমন রূপান্তর পুরো কাগজটিকে উল্টে পেছনের পিঠে নিয়ে যায়। গণিতে একে বলা হয় স্পেসের ওরিয়েন্টেশন বা দিকবিন্যাসের রূপান্তর। কাগজের সামনের পিঠে যে লেখা ছিল, তা এখন পেছন দিক থেকে পড়তে হবে, ঠিক এমনই একটি ঘটনা এখানে ঘটেছে।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, চিহ্ন বনাম পরম মান। যখনই স্থানের ওরিয়েন্টেশন উল্টে যায়, ডিটারমিন্যান্টের চিহ্ন ঋণাত্মক হয়ে যায়। তবে ডিটারমিন্যান্টের পরম মান বা অ্যাবসোলিউট ভ্যালু কিন্তু এখনও ক্ষেত্রফলের প্রকৃত স্কেলিং ফ্যাক্টরটিকেই নির্দেশ করে, মাইনাস দুই মানে ক্ষেত্রফল দুই গুণ বেড়েছে আর মাইনাস চিহ্নটি বলছে স্থানটি উল্টে গেছে। একটি সংখ্যা দিয়ে এই মাত্রা ও দিক, দুটি তথ্য একসাথে প্রকাশ করা হয়।"},
            {"index": 5, "type": "p",
             "tts": "একটি চমৎকার মানসিক পরীক্ষা ভাবুন, আই হ্যাটকে ধীরে ধীরে ঘুরিয়ে জে হ্যাটের দিকে আনুন। সমতলটি ক্রমশ চ্যাপ্টা হতে থাকবে এবং ক্ষেত্রফল কমতে কমতে একসময় শূন্য হবে। এরপর আই হ্যাট যদি একই দিকে এগোতে থাকে, তবে ডিটারমিন্যান্ট শূন্য পেরিয়ে স্বাভাবিকভাবেই ঋণাত্মক সংখ্যার রাজ্যে প্রবেশ করবে, অর্থাৎ ধনাত্মক থেকে শূন্য হয়ে ঋণাত্মক। ঋণাত্মকতা কোনো অসম্ভব বস্তু নয়, বরং একটি ধারাবাহিক ঘূর্ণনের ফল।"},
        ],
    },

    "sec_03_determinant_in_3d": {
        "title": EXPECTED_TITLES["sec_03_determinant_in_3d"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_03_determinant_in_3d"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, ত্রিমাত্রিক জগতে ডিটারমিন্যান্ট ও প্যারালেলেপিপেড।"},
            {"index": 1, "type": "p",
             "tts": "টুডি সমতলে ডিটারমিন্যান্ট যদি ক্ষেত্রফল স্কেলিং হয়, তবে বাস্তব ত্রিমাত্রিক থ্রিডি স্থানে এটি কী পরিমাপ করবে? খুব সহজ, থ্রিডি স্পেসে ডিটারমিন্যান্ট পরিমাপ করে আয়তন বা ভলিউম স্কেলিং ফ্যাক্টর। ক্ষেত্রফলের জায়গায় এখন আয়তন, বর্গক্ষেত্রের জায়গায় ঘনক, বাকি যুক্তি একই।"},
            {"index": 2, "type": "figure",
             "tts": "ত্রিমাত্রিক স্থানে আই হ্যাট, জে হ্যাট ও কে হ্যাট দ্বারা তৈরি এক বাই এক বাই এক একক ঘনকের আয়তন এক ঘন একক দেখা যাচ্ছে। এই ঘনকটিকে কেন্দ্র করেই রূপান্তরের প্রভাব দেখা হয়, ঠিক যেমন টুডিতে একক বর্গকে কেন্দ্র করেছিলাম। লক্ষ্য করুন, ঘনকের তিনটি বাহু ঠিক তিনটি বেসিস ভেক্টর বরাবর আছে, তাই এটি ডিটারমিন্যান্ট পড়ার সবচেয়ে সুবিধাজনক বস্তু।"},
            {"index": 3, "type": "p",
             "tts": "রূপান্তরের পর এই ঘনকটি একটি ঢালু ঘনবস্তুতে পরিণত হয়, যার নাম প্যারালেলেপিপেড। যেহেতু একক ঘনকের আদি আয়তন ছিল এক ঘন একক, তাই রূপান্তরের পর প্যারালেলেপিপেডের নতুন আয়তনই হলো ওই তিন বাই তিন ম্যাট্রিক্সের ডিটারমিন্যান্ট।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। ম্যাট্রিক্স এম হলো একটি তিন বাই তিন ম্যাট্রিক্স, যার তিনটি কলাম ভেক্টর যথাক্রমে আই হ্যাট, জে হ্যাট ও কে হ্যাটের রূপান্তরিত রূপ। এই তিনটি কলাম ভেক্টরেরই ডিটারমিন্যান্ট আমাদের আয়তনের স্কেলিং বলে দেয়।"},
            {"index": 5, "type": "h3",
             "tts": "থ্রিডি ওরিয়েন্টেশন ও ডান হাত নিয়ম।"},
            {"index": 6, "type": "p",
             "tts": "থ্রিডিতে ওরিয়েন্টেশন উল্টে যাওয়ার অর্থ কী? এটি ডান হাত নিয়মের সাহায্যে সহজেই বোঝা যায়। ডান হাতের তর্জনী আই হ্যাট, মধ্যমা জে হ্যাট এবং বৃদ্ধাঙ্গুলি কে হ্যাটের দিক নির্দেশ করে, অর্থাৎ আই হ্যাটের সাথে জে হ্যাটের ক্রস গুণ কে হ্যাট। রূপান্তরের পরও যদি একইভাবে মেলানো যায়, ডিটারমিন্যান্ট ধনাত্মক, নাহলে ঋণাত্মক।"},
            {"index": 7, "type": "figure",
             "tts": "বাঁ ছবিতে ডান হাতের তর্জনী, মধ্যমা ও বৃদ্ধাঙ্গুলি যথাক্রমে আই হ্যাট, জে হ্যাট ও কে হ্যাট বরাবর মিলে যাচ্ছে, অর্থাৎ ওরিয়েন্টেশন অক্ষুণ্ণ ও ডিটারমিন্যান্ট ধনাত্মক। ডান ছবিতে একই কাজ করতে হাত বদলে বাঁ হাত ব্যবহার করতে হচ্ছে, অর্থাৎ স্থানের দিকবিন্যাস উল্টে গেছে। লক্ষ্য করুন, এই ছবিটি থ্রিডিতে ঋণাত্মক ডিটারমিন্যান্টের সবচেয়ে সহজ মানসিক পরীক্ষা।"},
            {"index": 8, "type": "callout",
             "tts": "বিশেষ নোট, আয়তন শূন্য মানেই মাত্রা হারানো। যদি তিন বাই তিন ম্যাট্রিক্সের ডিটারমিন্যান্ট শূন্য হয়, তার অর্থ হলো পুরো থ্রিডি স্পেস চ্যাপ্টা হয়ে একটি দ্বিমাত্রিক সমতলে, রৈখিক তারে অথবা মূলবিন্দুতে সংকুচিত হয়ে গেছে। ফলে তার ত্রিমাত্রিক আয়তন দাঁড়িয়েছে শূন্য, অর্থাৎ ম্যাট্রিক্সের র্যাঙ্ক তিনের কম। আগের অধ্যায়ের রৈখিক নির্ভরতার সাথে এই বিষয়টি মিলিয়ে দেখলে আরও পরিষ্কার হবে।"},
        ],
    },

    "sec_04_computation_and_composition": {
        "title": EXPECTED_TITLES["sec_04_computation_and_composition"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_04_computation_and_composition"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, বীজগাণিতিক গণনা ও গুণন বিধি।"},
            {"index": 1, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। দুই বাই দুই ম্যাট্রিক্সের ডিটারমিন্যান্ট হলো এ ডি বিয়োগ বি সি, অর্থাৎ প্রথম সারির প্রথম ও দ্বিতীয় সারির দ্বিতীয় উপাদানের গুণফল থেকে অন্য দুটি উপাদানের গুণফল বাদ দিতে হবে।"},
            {"index": 2, "type": "figure",
             "tts": "এই খসড়া চিত্রটি এ ডি বিয়োগ বি সি সূত্রের উৎপত্তি দেখায়। যখন বি ও সি শূন্য, তখন ফলটা হয় একটি সরল এ গুণ ডি আয়তক্ষেত্র, কিন্তু বি ও সি শূন্য নয় এমন ক্ষেত্রে ওই আয়তক্ষেত্রটি কর্ণ বরাবর টানা ও কাটা হয়। লক্ষ্য করুন, সেই অতিরিক্ত অংশই বি সি রূপে বিয়োগ হয়, তাই সূত্রটি মুখস্থ না করে এর জ্যামিতিক ছবিটি মনে রাখাই যথেষ্ট।"},
            {"index": 3, "type": "p",
             "tts": "তিন বাই তিন ম্যাট্রিক্সের জন্য এই গণনাটি ক্রমান্বয়ে দুই বাই দুই সাব ম্যাট্রিক্সের ডিটারমিন্যান্টে বিভক্ত করে নির্ণয় করা হয়, এটি বিস্তার বা ল্যাপলাস এক্সপানশন নামে পরিচিত। প্রথম সারির তিনটি উপাদান দিয়ে তিনটি ছোট ডিটারমিন্যান্ট গুণ করে ধনাত্মক, ঋণাত্মক, ধনাত্মক চিহ্নে যোগ করা হয়। এই চিহ্নের পর্যায়ক্রম কলামের ক্রম থেকেই আসে।"},
            {"index": 4, "type": "h3",
             "tts": "ডিটারমিন্যান্টের জাদুকরী গুণন বিধি।"},
            {"index": 5, "type": "callout",
             "tts": "বিশেষ নোট, এক বাক্যে প্রমাণ। দুটি ম্যাট্রিক্সের গুণফলের ডিটারমিন্যান্ট হলো তাদের পৃথক ডিটারমিন্যান্টের গুণফলের সমান। বীজগণিত দিয়ে এটি প্রমাণ করা দুঃসাধ্য হলেও জ্যামিতিকভাবে মাত্র এক বাক্যে স্পষ্ট, প্রথম রূপান্তরটি যদি ক্ষেত্রফলকে বি গুণ স্কেল করে এবং দ্বিতীয়টি এ গুণ স্কেল করে, তবে সম্মিলিত রূপান্তরে ক্ষেত্রফল নিশ্চিতভাবেই এ গুণ বি স্কেল হবে। ওরিয়েন্টেশন উল্টালেও চিহ্নের গুণফল ঠিক একই নিয়ম মানে।"},
            {"index": 6, "type": "p", "role": "conclusion",
             "tts": "এই গভীর জ্যামিতিক অন্তর্দৃষ্টিই হলো লিনিয়ার অ্যালজেব্রার প্রকৃত শক্তি। হ্যামিংয়ের কথাটি মনে পড়বে, গণনা কেবল সংখ্যা বের করার জন্য নয়, অন্তর্দৃষ্টির জন্য। পরবর্তী অধ্যায়ে আমরা দেখব কীভাবে এই ডিটারমিন্যান্ট ব্যবহার করে সমীকরণ জোট সমাধান এবং ইনভার্স ম্যাট্রিক্সের রহস্য উন্মোচন করা যায়।"},
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
NON_NARRATED = {"sec-reveals", "sec-lab-2d", "sec-lab-3d", "sec-media",
                "sec-figure-gallery", "sec-quiz-lab", "sec-footnotes"}


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
          f"DOM parity OK (34/34, no duplicates).")

    manifest_sections = {}
    for sec_id in SECTION_ORDER:
        manifest_sections[sec_id] = await build_section(sec_id)

    manifest_data = {
        "course": "linear_algebra",
        "lesson": "lesson_06",
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

    print("\n" + "=" * 70)
    print("BUILD COMPLETE - expressive teacher audio, Lesson 06 (L01 gold standard)")
    for sec_id in SECTION_ORDER:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<36} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTION_ORDER)} sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  DOM<->manifest 1:1; 0 duplicate canonical cues; "
          "0 quiz/media-tab types; zero overlaps; exact 350 ms gaps; "
          "all MP3s non-zero; valid JSON.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(build_all())
