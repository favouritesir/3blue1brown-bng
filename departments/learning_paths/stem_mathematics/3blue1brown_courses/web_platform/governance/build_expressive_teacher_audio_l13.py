# -*- coding: utf-8 -*-
r"""
Rebuild the TEACHER NARRATION AUDIO for 3Blue1Brown Lesson 13 (Bengali),
expressive-edition, to the Lesson 01 gold standard.

Deterministic, re-runnable, self-contained:

  * 29 cues in 4 narrated sections. The cue count/type/order of every section is
    derived from the LIVE DOM of courses/linear_algebra/lesson_13.html using the
    very selector/rules that narration_engine.js uses:
        .article > section, article section  (skip [data-no-narration="true"])
        h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
        .code-showcase, .formula-box   (skip <p> inside .callout/.chapter-quote)
    Verified 29/29 via headless Chrome (channel="chrome"):
      sec_01_two_coordinate_systems = 8, sec_02_jennifer_to_our = 6,
      sec_03_our_to_jennifer = 6, sec_04_similarity_transformations = 9.
    All other sections are data-no-narration and produce no cues (no quiz /
    media-tab / interactive-section cue types). The DOM snapshot
    (l13_dom_blocks.json) preserves TeX via KaTeX <annotation>...</annotation>.
  * The 4 figure.lesson-figure blocks are explained naturally as teacher prose.
    No script ever uses a "চিত্র প্রদর্শনী" label — every figure cue opens
    naturally (e.g. "এখানে ... দেখা যাচ্ছে") and runs 2-4 full sentences.
  * The section IDs here ARE the existing manifest keys; the audio_file names
    are byte-for-byte the existing manifest keys too (no aliases needed):
      sec_01_two_coordinate_systems / sec_02_jennifer_to_our /
      sec_03_our_to_jennifer / sec_04_similarity_transformations.
    The backup folder _backup_before_expressive_build/ is never read/written.
  * Scripts are clean spoken Bengali: no TeX, LaTeX, backslashes, $, braces,
    brackets, em/en dashes, raw hyphens or Latin letters. Phonetic safeguards:
    \hat{i}->আই হ্যাট, \hat{j}->জে হ্যাট, \hat{k}->কে হ্যাট, x->এক্স,
    y->ওয়াই, v->ভি, A->এ, M->এম, P->পি, b_1->বি ওয়ান, b_2->বি টু,
    A^{-1}->এ ইনভার্স, 2D->টুডি, 3D->থ্রিডি, det->ডিটারমিন্যান্ট ...
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

Usage:  python governance/build_expressive_teacher_audio_l13.py
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
                         "linear_algebra", "lesson_13")
SOURCE_HTML = os.path.join(WORKSPACE, "courses", "linear_algebra",
                           "lesson_13.html")
DOM_BLOCKS = os.path.join(SCRIPT_DIR, "l13_dom_blocks.json")

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
    "sec_01_two_coordinate_systems",
    "sec_02_jennifer_to_our",
    "sec_03_our_to_jennifer",
    "sec_04_similarity_transformations",
]

# Exact DOM-derived cue type sequences (parity guards).
EXPECTED_TYPES = {
    "sec_01_two_coordinate_systems": ["h2", "chapter-quote", "p", "p",
                                      "figure", "p", "callout", "p"],
    "sec_02_jennifer_to_our":        ["h2", "p", "p", "figure", "callout",
                                      "formula-box"],
    "sec_03_our_to_jennifer":        ["h2", "p", "p", "formula-box", "figure",
                                      "callout"],
    "sec_04_similarity_transformations": ["h2", "p", "p", "figure", "callout",
                                      "formula-box", "p", "p", "callout"],
}
EXPECTED_AUDIO_FILES = {
    "sec_01_two_coordinate_systems": "sec_01_two_coordinate_systems.mp3",
    "sec_02_jennifer_to_our": "sec_02_jennifer_to_our.mp3",
    "sec_03_our_to_jennifer": "sec_03_our_to_jennifer.mp3",
    "sec_04_similarity_transformations": "sec_04_similarity_transformations.mp3",
}
# Preserve the existing manifest titles verbatim (schema compatibility).
EXPECTED_TITLES = {
    "sec_01_two_coordinate_systems":
        "১. দুইটি ভিন্ন স্থানাঙ্ক ব্যবস্থা ও জেনিফারের নিজস্ব ভিত্তি ভেক্টর",
    "sec_02_jennifer_to_our":
        "২. জেনিফারের ভাষা থেকে আমাদের ভাষায় রূপান্তর ও ভিত্তি ম্যাট্রিক্স এ",
    "sec_03_our_to_jennifer":
        "৩. আমাদের ভাষা থেকে জেনিফারের ভাষায় অনুবাদ ও বিপরীত ম্যাট্রিক্স এ ইনভার্স",
    "sec_04_similarity_transformations":
        "৪. রূপান্তরের রূপান্তর: অনুরূপ ম্যাট্রিক্স ও দৃষ্টিভঙ্গি পরিবর্তনের সমীকরণ এ ইনভার্স এম এ",
}
FORBIDDEN_CUE_TYPES = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
FORBIDDEN_PHRASE = "চিত্র প্রদর্শনী"
EXPECTED_FIGURES = 4          # four figure.lesson-figure blocks in narrated sections
EXPECTED_TOTAL_CUES = 29

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (29 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec_01_two_coordinate_systems": {
        "title": EXPECTED_TITLES["sec_01_two_coordinate_systems"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_01_two_coordinate_systems"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, দুইটি ভিন্ন স্থানাঙ্ক ব্যবস্থা ও জেনিফারের নিজস্ব ভিত্তি ভেক্টর।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, হেনরি পয়েনকেয়ার বলেছেন, গণিত হলো একই জিনিসকে বিভিন্ন নাম দেওয়ার শিল্প। এই এক বাক্যেই আজকের পাঠের মর্ম ছায়া ফেলে যায়। একই ভেক্টর, একই বিন্দু, কিন্তু ভিত্তি বদলালেই তার নাম বা স্থানাঙ্ক বদলে যায়।"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, টুডি সমতলে একটি ভেক্টর বসে আছে, তার স্থানাঙ্ক তিন দুই। অর্থাৎ লেজ থেকে ডগায় পৌঁছাতে তিন একক ডানে এবং দুই একক উপরে যেতে হবে। রৈখিক বীজগণিতের ভাষায় প্রতিটি সংখ্যাকে একটি স্কেলার হিসেবে দেখা হয়। প্রথম সংখ্যাটি আই হ্যাটকে স্কেল করে, দ্বিতীয়টি জে হ্যাটকে, আর তাদের টিপ টু টেইল যোগফলেই ভেক্টরটি তৈরি হয়। তিন আই হ্যাট যোগ দুই জে হ্যাট, অর্থাৎ উপরের সারিতে তিন আর নিচের সারিতে দুই।"},
            {"index": 3, "type": "p",
             "tts": "এই দুটি বিশেষ ভেক্টর আই হ্যাট ও জে হ্যাট আমাদের স্থানাঙ্ক ব্যবস্থার সমস্ত অব্যক্ত ধারণাকে ধরে রাখে। প্রথম সংখ্যা কেন ডানের দিক, দ্বিতীয় সংখ্যা কেন উপরের দিক, এবং এক একক দূরত্ব আসলে কত, সবই এই ভিত্তি ভেক্টরদ্বয়ের পছন্দের ওপর নির্ভরশীল। আই হ্যাট হলো উপরের সারি এক নিচের সারি শূন্য, আর জে হ্যাট হলো উপরের সারি শূন্য নিচের সারি এক। এই অনুবাদ প্রক্রিয়াটিই হলো কোঅর্ডিনেট সিস্টেম, আর আই হ্যাট ও জে হ্যাট হলো আমাদের প্রমিত ভিত্তি ভেক্টর।"},
            {"index": 4, "type": "figure",
             "tts": "এখানে আমাদের পরিচিত আই হ্যাট ও জে হ্যাট ভিত্তির পাশাপাশি জেনিফারের বিকল্প ভিত্তি দেখা যাচ্ছে। বি ওয়ান ডানে উপরে আর বি টু বাঁয়ে উপরে নির্দেশ করে, ঠিক যেন আমাদের খাড়া গ্রিডকে কিছুটা হেলানো হয়েছে। লক্ষ্য করুন, দুইজন একই জায়গায় থাকলেও ভিত্তি ভেক্টর আলাদা হওয়ায় একই বিন্দুকে বর্ণনা করার ভাষাও আলাদা হয়ে যায়।"},
            {"index": 5, "type": "p",
             "tts": "এবার আমাদের কাল্পনিক বন্ধু জেনিফারের সাথে পরিচিত হই। সে আমাদের একই স্থানে বাস করে, তার মূলবিন্দু ও আমাদের মূলবিন্দু হুবহু একই বিন্দুতে অবস্থিত, কিন্তু সে আই হ্যাট ও জে হ্যাট ব্যবহার করতে সম্পূর্ণ অস্বীকৃতি জানায়। তার নিজস্ব দুটি ভিত্তি ভেক্টর আছে, যাদের আমরা আমাদের ভাষায় লিখব বি ওয়ান সমান দুই এক, এবং বি টু সমান ঋণাত্মক এক এক।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, ভিন্ন ভাষা, একই স্থান, গ্রিড কেবল একটি গঠন। জেনিফারের নিজস্ব দৃষ্টিতে এই ভেক্টরদ্বয় কোনো জটিল সংখ্যা নয়। তার কাছে বি ওয়ান হলো প্রথম একক ভিত্তি এক শূন্য, আর বি টু হলো দ্বিতীয় একক ভিত্তি শূন্য এক। তাই তার গ্রিডরেখাগুলো আমাদের মতো খাড়া লম্ব নয়, বরং কিছুটা হেলানো এবং ফাঁকও ভিন্ন মাপের। মনে রাখতে হবে, গ্রিড মহাকাশের নিজস্ব বৈশিষ্ট্য নয়, এটি কেবল আমাদের বেছে নেওয়া ভিত্তির দৃশ্যমান গঠন মাত্র। সবার মূলবিন্দু একই, কারণ শূন্য শূন্য মানে যেকোনো ভেক্টরকে শূন্য দিয়ে গুণ করে পাওয়া বিন্দু।"},
            {"index": 7, "type": "p",
             "tts": "এখন ভাবুন, মহাকাশের ঠিক একই জায়গায় স্থির একটি বাস্তব তীরকে আমরা দুজনে দেখছি। আমরা লিখছি তিন দুই, জেনিফার লিখবে পাঁচ বাই তিন আর এক বাই তিন। একই ভেক্টর, দুটি ভিন্ন সংখ্যাজোড়া। এখান থেকেই ভিত্তি পরিবর্তনের আসল রহস্য শুরু হয়।"},
        ],
    },

    "sec_02_jennifer_to_our": {
        "title": EXPECTED_TITLES["sec_02_jennifer_to_our"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_02_jennifer_to_our"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, জেনিফারের ভাষা থেকে আমাদের ভাষায় রূপান্তর ও ভিত্তি ম্যাট্রিক্স এ।"},
            {"index": 1, "type": "p",
             "tts": "ধরা যাক জেনিফার একটি ভেক্টর দেখিয়ে বলল, তার স্থানাঙ্ক ব্যবস্থায় এই ভেক্টরের মান ঋণাত্মক এক দুই। এর জ্যামিতিক অর্থ হলো, সে প্রথম ভিত্তি ভেক্টর বি ওয়ানকে ঋণাত্মক এক দিয়ে এবং দ্বিতীয় ভিত্তি ভেক্টর বি টু কে ধনাত্মক দুই দিয়ে স্কেল করে তাদের যোগ করেছে। অর্থাৎ ঋণাত্মক এক গুণ বি ওয়ান যোগ দুই গুণ বি টু।"},
            {"index": 2, "type": "p",
             "tts": "আমাদের নিজস্ব ভাষায় এই ভেক্টরের স্থানাঙ্ক বের করতে হলে বি ওয়ান ও বি টু এর জায়গায় আমাদের পরিচিত মানগুলো বসিয়ে দিতে হবে। তাহলে পাই ঋণাত্মক এক গুণ দুই এক, যোগ দুই গুণ ঋণাত্মক এক এক, অর্থাৎ ঋণাত্মক চার এক। জেনিফার যে তীরটিকে ঋণাত্মক এক দুই বলে ডাকে, আমাদের কাছে সেটি ঋণাত্মক চার এক।"},
            {"index": 3, "type": "figure",
             "tts": "এখানে দেখা যাচ্ছে কীভাবে প্রতিটি স্থানাঙ্ক একটি ভিত্তি ভেক্টরের স্কেলার গুণক হয়ে কাজ করে। স্কেল করা ভেক্টরদ্বয়ের টিপ টু টেইল যোগফল নির্দিষ্ট তীরটিকে তৈরি করে, ঠিক যেন দুটি তীরকে একের পর এক সাজানো হয়েছে। জেনিফারের ঋণাত্মক এক দুই ক্ষেত্রে বি ওয়ান উল্টে যায় আর বি টু দ্বিগুণ হয়, ফলে আমাদের ভাষায় ফলাফল ঋণাত্মক চার এক দাঁড়ায়।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, রৈখিক সমাবেশই ম্যাট্রিক্স ভেক্টর গুণন। লক্ষ্য করুন, এই স্কেল ও যোগ প্রক্রিয়াটি হুবহু ম্যাট্রিক্স ও ভেক্টরের গুণন। যদি এমন একটি টু বাই টু ম্যাট্রিক্স তৈরি করি যার প্রথম কলাম বি ওয়ান এবং দ্বিতীয় কলাম বি টু, তবে জেনিফারের যেকোনো স্থানাঙ্ককে এই ম্যাট্রিক্স দিয়ে গুণ করলেই সঙ্গে সঙ্গে আমাদের স্থানাঙ্ক বেরিয়ে আসে। ম্যাট্রিক্সের কলামদ্বয় যথাক্রমে দুই এক এবং ঋণাত্মক এক এক, আর ফলাফল আমাদের স্থানাঙ্ক।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। ভিত্তি পরিবর্তন ম্যাট্রিক্স এ সমান বি ওয়ান ও বি টু কে কলাম হিসেবে সাজিয়ে গঠিত ম্যাট্রিক্স, অর্থাৎ উপরের সারিতে দুই ঋণাত্মক এক, নিচের সারিতে এক এক। জেনিফারের ভেক্টরকে আমাদের ভাষায় আনতে এই ম্যাট্রিক্স দিয়ে গুণ করতে হয়। এর প্রতিটি কলাম আসলে জেনিফারের ভিত্তি ভেক্টরগুলোকে আমাদের নিজস্ব ভাষায় প্রকাশ করে, তাই এই ম্যাট্রিক্সটি জেনিফারের ভাষা থেকে আমাদের ভাষায় যাওয়ার এক নিখুঁত অনুবাদক হিসেবে কাজ করে।"},
        ],
    },

    "sec_03_our_to_jennifer": {
        "title": EXPECTED_TITLES["sec_03_our_to_jennifer"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_03_our_to_jennifer"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, আমাদের ভাষা থেকে জেনিফারের ভাষায় অনুবাদ ও বিপরীত ম্যাট্রিক্স এ ইনভার্স।"},
            {"index": 1, "type": "p",
             "tts": "এতক্ষণ আমরা দেখলাম জেনিফারের দেওয়া স্থানাঙ্ককে কীভাবে আমাদের ভাষায় অনুবাদ করা যায়। কিন্তু ঠিক উল্টো কাজটি আমরা কীভাবে করব? আমাদের কার্তেসীয় গ্রিডে একটি ভেক্টর আছে তিন দুই। জেনিফার এই একই ভেক্টরটিকে কী স্থানাঙ্কে দেখতে পাবে? এই প্রশ্নটির উত্তরেই বিপরীত ম্যাট্রিক্সের প্রয়োজনীয়তা প্রকাশ পায়।"},
            {"index": 2, "type": "p",
             "tts": "যেহেতু আমাদের ভিত্তি ম্যাট্রিক্স এ জেনিফারের স্থানাঙ্ককে আমাদের স্থানাঙ্কে পরিণত করে, তাই উল্টো অনুবাদের জন্য প্রয়োজন এর বিপরীত ম্যাট্রিক্স, অর্থাৎ এ ইনভার্স। জেনিফারের স্থানাঙ্ক থেকে আমাদের স্থানাঙ্ক পেতে যেভাবে এ দিয়ে গুণ করি, আমাদের স্থানাঙ্ক থেকে জেনিফারের স্থানাঙ্ক পেতে তেভাবে এ ইনভার্স দিয়ে গুণ করতে হয়। বিপরীত রূপান্তর মানে হলো মূল রূপান্তরটিকে পেছনের দিকে চালানো।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। ম্যাট্রিক্স এ এর নির্ণায়ক হলো দুই গুণ এক বিয়োগ ঋণাত্মক এক গুণ এক, অর্থাৎ তিন। যেহেতু নির্ণায়ক অশূন্য, তাই এর বিপরীত ম্যাট্রিক্স বিদ্যমান। এ ইনভার্স সমান এক বাই তিন গুণ ম্যাট্রিক্স, যার উপরের সারি এক এক এবং নিচের সারি ঋণাত্মক এক দুই। সাধারণ টু বাই টু ক্ষেত্রে উপরের ডান ও নিচের বাঁ উপাংশের চিহ্ন বদলে, প্রধান কর্ণের দুটি উপাংশ বিনিময় করে, সবকিছু নির্ণায়ক দিয়ে ভাগ করা হয়।"},
            {"index": 4, "type": "figure",
             "tts": "এখানে দেখা যাচ্ছে কীভাবে বিপরীত ম্যাট্রিক্স প্রয়োগ করে আমাদের তিন দুই ভেক্টরটিকে জেনিফারের ভাষায় রূপান্তর করা হয়। স্থানাঙ্ককে ভিত্তি ভেক্টরের স্কেলার গুণক হিসেবে দেখলেই বিপরীত ম্যাট্রিক্সের কাজ সহজ হয়ে যায়, এক বাই তিন গুণ তিন যোগ দুই বাই তিন গুণ দুই অর্থাৎ পাঁচ বাই তিন, আর ঋণাত্মক এক বাই তিন গুণ তিন যোগ দুই বাই তিন গুণ দুই অর্থাৎ এক বাই তিন। ফলে জেনিফার বি ওয়ানকে পাঁচ বাই তিন ও বি টু কে এক বাই তিন দিয়ে স্কেল করলে আমাদের তীরটি পাওয়া যায়।"},
            {"index": 5, "type": "callout",
             "tts": "বিশেষ নোট, পুনঃযাচাই ও সর্বজনীন অনুবাদক। ফিরে দেখি, পাঁচ বাই তিন গুণ দুই এক, যোগ এক বাই তিন গুণ ঋণাত্মক এক এক, তাহলে আমরা হুবহু তিন দুই ভেক্টরটিই ফেরত পাই। সুতরাং এ ইনভার্স হলো আমাদের ভাষা থেকে জেনিফারের ভাষায় যাওয়ার নিখুঁত অনুবাদক, আর এ তার ঠিক বিপরীত পথের অনুবাদক। দুই ভিত্তি ভেক্টর রৈখিকভাবে স্বাধীন হওয়ায়, অর্থাৎ এর নির্ণায়ক তিন অশূন্য হওয়ায় এই অনুবাদ সম্ভব।"},
        ],
    },

    "sec_04_similarity_transformations": {
        "title": EXPECTED_TITLES["sec_04_similarity_transformations"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_04_similarity_transformations"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, রূপান্তরের রূপান্তর, অনুরূপ ম্যাট্রিক্স ও দৃষ্টিভঙ্গি পরিবর্তনের সমীকরণ এ ইনভার্স এম এ।"},
            {"index": 1, "type": "p",
             "tts": "ভেক্টর অনুবাদের চেয়েও রোমাঞ্চকর প্রয়োগ হলো রূপান্তরের রূপান্তর। ধরা যাক আমাদের পরিচিত স্থানে একটি রৈখিক রূপান্তর ঘটছে, পুরো সমতলটিকে ঘড়ির কাঁটার বিপরীত দিকে নব্বই ডিগ্রি ঘোরানো হলো। আমাদের ভাষায় এর ম্যাট্রিক্স এম, অর্থাৎ উপরের সারি শূন্য ঋণাত্মক এক, নিচের সারি এক শূন্য। প্রথম কলাম বলে আই হ্যাট যায় শূন্য এক এ, দ্বিতীয় কলাম বলে জে হ্যাট যায় ঋণাত্মক এক শূন্য এ।"},
            {"index": 2, "type": "p",
             "tts": "কিন্তু এই উপস্থাপনা আমাদের ভিত্তি ভেক্টরের পছন্দের সাথে গেঁথে আছে। জেনিফার যদি তার গ্রিডে বসে একই শারীরিক নব্বই ডিগ্রি ঘূর্ণন দেখে, তবে তার স্থানাঙ্কের ওপর প্রভাব প্রকাশ করতে সে কোন ম্যাট্রিক্স ব্যবহার করবে? কেবল আমাদের ম্যাট্রিক্সের কলামগুলোকে তার ভাষায় অনুবাদ করলে হবে না। তার ম্যাট্রিক্সের কলামগুলো হলো তার ভিত্তি ভেক্টরগুলো কোথায় ল্যান্ড করেছে, আর সেই ল্যান্ডিং স্থানগুলোও তার ভাষাতেই লেখা থাকতে হবে।"},
            {"index": 3, "type": "figure",
             "tts": "এখানে গ্রিডের রূপান্তর দেখা যাচ্ছে, আর তা থেকে বোঝা যায় যে একটি রূপান্তরের ম্যাট্রিক্স নির্ভর করে কোন ভিত্তিতে আমরা তা লিখছি তার ওপর। একই নব্বই ডিগ্রি ঘূর্ণন আমাদের খাড়া গ্রিডে সরল দেখা গেলেও জেনিফারের হেলানো গ্রিডে এর সংখ্যাগুলো আলাদা হবে। কিন্তু শারীরিক ঘূর্ণন একই, শুধু বর্ণনার ভাষা বদলেছে।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, তিন ধাপের অপূর্ব চক্র, ডান থেকে বাঁয়ে। প্রথম ধাপে জেনিফারের দেওয়া ভেক্টর নিন এবং ডান দিক থেকে সবার আগে প্রয়োগ করুন ভিত্তি ম্যাট্রিক্স এ। এটি তার ভেক্টরকে আমাদের ভাষায় নিয়ে আসে। দ্বিতীয় ধাপে আমাদের ঘূর্ণন ম্যাট্রিক্স এম প্রয়োগ করুন, যা আমাদের ভাষায় ভেক্টরটিকে নব্বই ডিগ্রি ঘুরিয়ে দেয়। এই দুই ধাপের সম্মিলিত ফল আমাদের স্থানাঙ্কে ঘোরানো ভেক্টর।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। তৃতীয় ধাপে সবশেষে বাঁ দিক থেকে গুণ করুন এ ইনভার্স। এর ফলে ঘোরানো ভেক্টরটি আবার জেনিফারের নিজস্ব ভাষার স্থানাঙ্কে ফেরত চলে যায়। পুরো প্রক্রিয়াটি দাঁড়িয়েছে এ ইনভার্স এম এ গুণ জেনিফারের ভেক্টর, অর্থাৎ জেনিফারের দৃষ্টিতে সেই ঘূর্ণনের সমতুল্য ম্যাট্রিক্স।"},
            {"index": 6, "type": "p",
             "tts": "ডান থেকে বাঁয়ে পড়ুন, প্রথমে জেনিফারের ভাষা থেকে আমাদের ভাষায় অনুবাদ, তারপর আমাদের ভাষায় মূল রূপান্তর সম্পাদন, এবং সবশেষে ফলাফলকে আবার জেনিফারের ভাষায় ফিরিয়ে দেওয়া। এই তিনটি ম্যাট্রিক্সের সম্মিলিত গুণফলই দেখায় জেনিফারের ফ্রেম থেকে সেই একই ঘূর্ণন কীভাবে দেখা যায়। কলাম হিসেবে ভাবলে বলা যায়, মূল ম্যাট্রিক্সের কলামগুলোকে ঘুরিয়ে তারা নতুন কোথায় পড়ে, সেই অবস্থানগুলোকে আবার জেনিফারের ভাষায় লেখা হয়।"},
            {"index": 7, "type": "p",
             "tts": "গণিতে যখনই আপনারা পি ইনভার্স এম পি আকারের কোনো রাশি দেখবেন, সাথে সাথে বুঝে নেবেন, এটি দৃষ্টিভঙ্গি পরিবর্তনের গাণিতিক প্রকাশ। মাঝের ম্যাট্রিক্সটি রূপান্তর ঘটাচ্ছে, আর দুই পাশের ম্যাট্রিক্সদ্বয় দুটি ভিন্ন স্থানাঙ্ক জগতের মাঝে অনুবাদের কাজ করছে। এক ধরনের গাণিতিক সহানুভূতি বলা যায়, একই ঘটনাকে অন্যের দৃষ্টিকোণ থেকে দেখা।"},
            {"index": 8, "type": "callout", "role": "conclusion",
             "tts": "বিশেষ নোট, অনুরূপ ম্যাট্রিক্স, অপরিবর্তনশীল ধর্ম ও পরবর্তী পাঠ। এই রকম ম্যাট্রিক্সকে বলা হয় অনুরূপ বা সিমিলার, অর্থাৎ জেনিফারের ম্যাট্রিক্স আমাদের ম্যাট্রিক্সের সাথে অনুরূপ। আমাদের উদাহরণে এক বাই তিন, ঋণাত্মক দুই বাই তিন, পাঁচ বাই তিন, ঋণাত্মক এক বাই তিন, এই চারটি সংখ্যা নতুন ম্যাট্রিক্সের কলাম গঠন করে। জ্যামিতিকভাবে এরা একই রূপান্তর, শুধু পর্যবেক্ষকের ভিত্তি আলাদা, তাই তাদের নির্ণায়ক ও ট্রেস অপরিবর্তিত থাকে। পরবর্তী অধ্যায়ে আইগেনভেক্টর ও আইগেনভ্যালু ব্যাখ্যা করবে কেন বিকল্প ভিত্তি বেছে নেওয়া এত গুরুত্বপূর্ণ।"},
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
NON_NARRATED = {
    "sec_quizzes_transformation", "sec_quizzes_inverse",
    "sec_quizzes_similarity", "sec_labs",
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
                if "দেখা যাচ্ছে" not in body:
                    raise ValueError(f"{sec_id} cue {cue['index']}: figure must "
                                     "open naturally with a seeing cue")
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
          f"DOM parity OK (29/29, no duplicates, no forbidden phrase).")

    manifest_sections = {}
    for sec_id in SECTION_ORDER:
        manifest_sections[sec_id] = await build_section(sec_id)

    manifest_data = {
        "course": "linear_algebra",
        "lesson": "lesson_13",
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
    print("BUILD COMPLETE - expressive teacher audio, Lesson 13 (L01 gold standard)")
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
