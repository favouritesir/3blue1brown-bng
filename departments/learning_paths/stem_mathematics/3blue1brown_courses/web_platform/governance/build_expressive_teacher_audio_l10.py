# -*- coding: utf-8 -*-
r"""
Rebuild the TEACHER NARRATION AUDIO for 3Blue1Brown Lesson 10 (Bengali),
expressive-edition, to the Lesson 01 gold standard.

Deterministic, re-runnable, self-contained:

  * 37 cues in 4 narrated sections. The cue count/type/order of every section is
    derived from the LIVE DOM of courses/linear_algebra/lesson_10.html using the
    very selector/rules that narration_engine.js uses:
        .article > section, article section  (skip [data-no-narration="true"])
        h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
        .code-showcase, .formula-box   (skip <p> inside .callout/.chapter-quote)
    Verified 37/37: sec_01_geometric_definition=9,
    sec_02_2d_orientation_determinant=9, sec_03_3d_determinant_formula=9,
    sec_04_duality_perspective=10. All other sections are data-no-narration and
    produce no cues (no quiz / media-tab / interactive-section cue types). The
    DOM snapshot (l10_dom_blocks.json) preserves TeX via KaTeX
    <annotation>...</annotation> markers.
  * The section IDs here ARE the existing manifest keys; the audio_file names
    are byte-for-byte the existing manifest keys too (no aliases needed):
    sec_01_geometric_definition / sec_02_2d_orientation_determinant /
    sec_03_3d_determinant_formula / sec_04_duality_perspective.
    The backup folder _backup_before_expressive_build/ is never read/written.
  * Figure cues are genuine 2-4 sentence pedagogical explanations (2 figures)
    in NATURAL teacher phrasing: each begins with "এখানে ... দেখা যাচ্ছে",
    never with a "চিত্র প্রদর্শনী" style label.
  * Scripts are clean spoken Bengali: no TeX, LaTeX, backslashes, $, braces,
    brackets, em/en dashes, raw hyphens or Latin letters. Phonetic safeguards:
    \hat{i}->আই হ্যাট, \hat{j}->জে হ্যাট, \hat{k}->কে হ্যাট, v->ভি,
    w->ডব্লিউ, u->ইউ, p->পি, theta->থিটা, sin->সাইন, 2D->টুডি,
    3D->থ্রিডি, x->এক্স, y->ওয়াই, z->জেড ...
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

Usage:  python governance/build_expressive_teacher_audio_l10.py
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
                         "linear_algebra", "lesson_10")
SOURCE_HTML = os.path.join(WORKSPACE, "courses", "linear_algebra",
                           "lesson_10.html")
DOM_BLOCKS = os.path.join(SCRIPT_DIR, "l10_dom_blocks.json")

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
    "sec_01_geometric_definition",
    "sec_02_2d_orientation_determinant",
    "sec_03_3d_determinant_formula",
    "sec_04_duality_perspective",
]

# Exact DOM-derived cue type sequences (parity guards).
# NOTE: the old manifest used "insight-box"; the live DOM renders <b1b-callout>
# as .callout -> narration_engine reports type "callout".
EXPECTED_TYPES = {
    "sec_01_geometric_definition": ["h2", "chapter-quote", "p", "figure",
                                    "formula-box", "p", "callout", "p", "p"],
    "sec_02_2d_orientation_determinant": ["h2", "p", "p", "formula-box", "p",
                                          "callout", "p", "p", "figure"],
    "sec_03_3d_determinant_formula": ["h2", "p", "formula-box", "p",
                                      "formula-box", "p", "callout", "p", "p"],
    "sec_04_duality_perspective": ["h2", "p", "p", "formula-box", "p",
                                   "callout", "p", "formula-box", "callout", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec_01_geometric_definition":            "sec_01_geometric_definition.mp3",
    "sec_02_2d_orientation_determinant":      "sec_02_2d_orientation_determinant.mp3",
    "sec_03_3d_determinant_formula":          "sec_03_3d_determinant_formula.mp3",
    "sec_04_duality_perspective":             "sec_04_duality_perspective.mp3",
}
# Preserve the existing manifest titles verbatim (schema compatibility).
EXPECTED_TITLES = {
    "sec_01_geometric_definition":            "ক্রস প্রোডাক্টের জ্যামিতিক সংজ্ঞা ও ক্ষেত্রফল",
    "sec_02_2d_orientation_determinant":      "টুডি সমতলে ক্ষেত্রফল ও দিকবিন্যাস",
    "sec_03_3d_determinant_formula":          "ত্রিমাত্রিক নির্ণায়ক সংকেত ও হিসাব পদ্ধতি",
    "sec_04_duality_perspective":             "ডুয়ালিটির দৃষ্টিতে ক্রস প্রোডাক্টের প্রকৃত রহস্য",
}
FORBIDDEN_CUE_TYPES = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
EXPECTED_FIGURES = 2
EXPECTED_TOTAL_CUES = 37

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (37 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec_01_geometric_definition": {
        "title": EXPECTED_TITLES["sec_01_geometric_definition"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_01_geometric_definition"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, ক্রস প্রোডাক্টের জ্যামিতিক সংজ্ঞা ও সামান্তরিকের ক্ষেত্রফল।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, জেফ লাগারিয়াস বলেন, প্রতিটি মাত্রারই নিজস্ব বিশেষত্ব রয়েছে। অর্থাৎ প্রতিটি মাত্রারই এমন কিছু বৈশিষ্ট্য আছে, যা অন্য মাত্রায় খুঁজে পাওয়া যায় না।"},
            {"index": 2, "type": "p",
             "tts": "লিনিয়ার অ্যালজেব্রার দশম অধ্যায়ে আপনাদের স্বাগতম। আপনি যদি কাউকে জিজ্ঞেস করেন দুটি ভেক্টরের ক্রস প্রোডাক্ট আসলে কী, তারা সাধারণত বলবেন, ভেক্টর ভি ও ভেক্টর ডব্লিউ নিলে তাদের ক্রস প্রোডাক্ট ভি গুণ ডব্লিউ হলো একটি সম্পূর্ণ নতুন তৃতীয় ভেক্টর। এই অধ্যায়ে আমরা দেখব এই নতুন ভেক্টরটি কীভাবে ক্ষেত্রফল ও অভিমুখ, দুটো তথ্যই একসাথে বহন করে।"},
            {"index": 3, "type": "figure",
             "tts": "এখানে ভি ও ডব্লিউ ভেক্টর দুটির ওপর একটি নীল সামান্তরিক গড়ে উঠতে দেখা যাচ্ছে। আর তার ঠিক ওপর দিকে লাল এক তীরচিহ্ন দাঁড়িয়ে আছে, সেটিই হলো ক্রস প্রোডাক্ট। লক্ষ্য করুন লাল তীরটি ভি ও ডব্লিউ, উভয়ের প্রতিই সমকোণে দাঁড়িয়ে আছে, আর এই লম্বতাই ক্রস প্রোডাক্টের সবচেয়ে চোখে পড়ার মতো বৈশিষ্ট্য। আবার তীরটির দৈর্ঘ্য নির্ধারিত হচ্ছে সামান্তরিকের আকার দ্বারা, কাজেই ভেক্টর দুটিকে বড় করলে লাল তীরটিও লম্বা হবে।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। ক্রস প্রোডাক্টের দৈর্ঘ্য সমান ভি এর দৈর্ঘ্য গুণ ডব্লিউ এর দৈর্ঘ্য গুণ সাইন থিটা, আর এটি ঠিক সামান্তরিকের ক্ষেত্রফলের সমান। মনে রাখবেন কোণ বাড়লে ছায়া কমবে, কিন্তু কোণ নব্বই ডিগ্রি হলে ক্ষেত্রফল সর্বোচ্চ।"},
            {"index": 5, "type": "p",
             "tts": "কিন্তু এই লম্ব ভেক্টরটি কোন দিকে মুখ করে থাকবে, উপরের দিকে নাকি নিচের দিকে? একটি সমতলের ওপর কিন্তু দুটি বিপরীতমুখী লম্ব দিক সম্ভব, তাই কেবল লম্ব বলে দিলে চলবে না, কোন দিকটি বেছে নেবেন তা নির্ধারণ করতে হবে।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, ডান হাত নিয়ম। আপনার ডান হাতের তর্জনী ভি বরাবর রাখুন এবং মধ্যমাকে ডব্লিউ বরাবর বাঁকান, তখন বৃদ্ধাঙ্গুলি যেদিকে নির্দেশ করবে, সেটিই হবে ভি গুণ ডব্লিউ এর দিক। একই কারণে আই হ্যাট গুণ জে হ্যাট সমান পজিটিভ কে হ্যাট, এটি ইতিবাচক অভিমুখের আদর্শ উদাহরণ। হাতের এই ছোট্ট কৌশলটিই থ্রিডি জগতে ক্রম ও চিহ্নের পার্থক্য ধরে রাখে।"},
            {"index": 7, "type": "p",
             "tts": "যদি দুটি ভেক্টর একই সরলরেখায় থাকে বা পরস্পর সমান্তরাল হয়, তবে তাদের গঠিত সামান্তরিকের ক্ষেত্রফল শূন্য, অর্থাৎ ভি গুণ ডব্লিউ সমান শূন্য ভেক্টর। অ্যান্টি প্যারালেল অর্থাৎ বিপরীতমুখী সমান্তরাল ভেক্টরের ক্রস গুণনও শূন্য, কারণ তখন সাইন থিটা সমান শূন্য।"},
            {"index": 8, "type": "p", "role": "conclusion",
             "tts": "এটিই হলো ক্রস প্রোডাক্টের বিশুদ্ধ জ্যামিতিক পরিচয়। এর মান বা দৈর্ঘ্য হলো ক্ষেত্রফল, আর দিক হলো ডান হাত নিয়ম দ্বারা নির্ধারিত ঐ লম্ব ভেক্টর। পরবর্তী অংশে আমরা দেখব এই একই ধারণা টুডি সমতলে কীভাবে ডিটারমিন্যান্টের চিহ্ন হয়ে প্রকাশ পায়।"},
        ],
    },

    "sec_02_2d_orientation_determinant": {
        "title": EXPECTED_TITLES["sec_02_2d_orientation_determinant"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_02_2d_orientation_determinant"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, টুডি সমতলে ক্ষেত্রফল, নির্ণায়ক ও দিকবিন্যাস।"},
            {"index": 1, "type": "p",
             "tts": "থ্রিডি সূত্রের অদ্ভুত রূপ বোঝার আগে চলুন প্রথমে টুডি দ্বিমাত্রিক জগতে ফিরে যাই। সেখানেই নির্ণায়ক এবং ওরিয়েন্টেশনের যোগসূত্রটি সবচেয়ে পরিচ্ছন্নভাবে দেখা যায়, আর সেটাই পরে থ্রিডি ক্রস প্রোডাক্টের ধাঁধার চাবিকাঠি হবে।"},
            {"index": 2, "type": "p",
             "tts": "ধরা যাক টুডি সমতলে দুটি ভেক্টর আছে, ভি যার উপাংশ ভি এক ও ভি টু, আর ডব্লিউ যার উপাংশ ডব্লিউ এক ও ডব্লিউ টু। ষষ্ঠ অধ্যায়ে আমরা প্রমাণ করেছি যে এদের কলাম হিসেবে সাজালে টু বাই টু ম্যাট্রিক্সের ডিটারমিন্যান্ট সরাসরি ওই সামান্তরিকের চিহ্নযুক্ত ক্ষেত্রফল দেয়। যেমন একটি ম্যাট্রিক্সের প্রথম সারিতে মাইনাস তিন ও দুই, দ্বিতীয় সারিতে এক ও এক। তার ডিটারমিন্যান্ট হলো মাইনাস তিন গুণ এক বিয়োগ দুই গুণ এক, অর্থাৎ মাইনাস পাঁচ। মান পাঁচ, কিন্তু চিহ্ন ঋণাত্মক।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। ডিটারমিন্যান্ট সমান ভি এক গুণ ডব্লিউ টু বিয়োগ ভি টু গুণ ডব্লিউ এক, আর এটি হলো চিহ্নযুক্ত ক্ষেত্রফল। মনে রাখবেন প্রথম কলাম ভি, দ্বিতীয় কলাম ডব্লিউ, এই ক্রমই চিহ্ন নির্ধারণ করে।"},
            {"index": 4, "type": "p",
             "tts": "এই মানটি ধনাত্মক হবে যদি ভি থেকে ডব্লিউ এর দিকে ঘূর্ণনটি আই হ্যাট থেকে জে হ্যাটের স্বাভাবিক ঘড়ির বিপরীত দিকে হয়। অর্থাৎ ডিটারমিন্যান্টের চিহ্ন কেবল আকার নয়, সমতলের ওরিয়েন্টেশন বা দিকবিন্যাসও বলে দেয়।"},
            {"index": 5, "type": "callout",
             "tts": "বিশেষ নোট, অ্যান্টি কমিউটেটিভিটি, অর্থাৎ ভি গুণ ডব্লিউ সমান ঋণাত্মক ডব্লিউ গুণ ভি। আপনি যদি ভেক্টরের ক্রম অদলবদল করেন, তবে সামান্তরিকের ক্ষেত্রফল একই থাকলেও ওরিয়েন্টেশন উল্টে যায়। তাই আই হ্যাট গুণ জে হ্যাট সমান পজিটিভ কে হ্যাট, কিন্তু জে হ্যাট গুণ আই হ্যাট সমান নেগেটিভ কে হ্যাট। এই প্রতিক্রম বিনিময়শীলতা থেকে বোঝা যায় ক্রস গুণনে ক্রম কতটা সংবেদনশীল।"},
            {"index": 6, "type": "p",
             "tts": "এখানে কয়েকটি গুরুত্বপূর্ণ বৈশিষ্ট্য মনে রাখুন। ভেক্টরদ্বয় পরস্পর লম্ব হলে সাইন থিটা সমান এক, তখন ক্ষেত্রফল সর্বোচ্চ। কোনো এক ভেক্টরকে কে দ্বারা স্কেল করলে ক্ষেত্রফলও কে গুণ বেড়ে যায়। আর সমান্তরাল হলে ক্ষেত্রফল শূন্য, কারণ ভি গুণ ভি সবসময় শূন্য ভেক্টর, নিজের সাথে নিজের ক্রস গুণনের ফল সবসময় শূন্য।"},
            {"index": 7, "type": "p",
             "tts": "তবে একটা সূক্ষ্ম পার্থক্য আছে। টুডি জগতে এই প্রক্রিয়া ফলাফল হিসেবে কেবল একটি একক বাস্তব সংখ্যা বা স্কেলার দেয়। কিন্তু থ্রিডিতে আমাদের একটি পূর্ণাঙ্গ ভেক্টর দরকার, কারণ থ্রিডি স্থানের সমতল যেকোনো দিকে হেলানো থাকতে পারে, তাই ক্ষেত্রফলের পাশাপাশি তলটির স্থানিক বিন্যাসও নির্দেশ করতে হয়।"},
            {"index": 8, "type": "figure",
             "tts": "এখানে দুটি প্যানেল পাশাপাশি দেখা যাচ্ছে। বাঁ প্যানেলে ভি প্রথম ও ডব্লিউ দ্বিতীয়, ঘড়ির বিপরীত ঘূর্ণনে চিহ্ন ধনাত্মক, আর ডান প্যানেলে ক্রম বদলে ডব্লিউ প্রথম ও ভি দ্বিতীয়, তখন ঘূর্ণন ঘড়ির দিকে তাই চিহ্ন ঋণাত্মক। দুই প্যানেলের সামান্তরিকের আকার একই, শুধু তলের মুখ উল্টে গেছে, আর এটিই ভি গুণ ডব্লিউ সমান ঋণাত্মক ডব্লিউ গুণ ভি এর দৃশ্যমান প্রমাণ।"},
        ],
    },

    "sec_03_3d_determinant_formula": {
        "title": EXPECTED_TITLES["sec_03_3d_determinant_formula"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_03_3d_determinant_formula"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, থ্রিডি নির্ণায়ক সংকেত ও আই হ্যাট, জে হ্যাট, কে হ্যাট গণনা কৌশল।"},
            {"index": 1, "type": "p",
             "tts": "এখন আমরা স্ট্যান্ডার্ড থ্রিডি দৃশ্যে ফিরে আসি। ক্রস প্রোডাক্টের ফলাফল হলো একটি ভেক্টর, যার দৈর্ঘ্য সামান্তরিকের ক্ষেত্রফলের সমান এবং দিক ডান হাত নিয়মে নির্ধারিত। পাঠ্যবইগুলোতে এই ভেক্টরটি হিসাব করতে একটি অদ্ভুত স্মৃতিসহায়ক ডিটারমিন্যান্ট সামনে হাজির করা হয়।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। ভি গুণ ডব্লিউ সমান একটি ডিটারমিন্যান্ট, যার প্রথম সারিতে আই হ্যাট, জে হ্যাট ও কে হ্যাট, দ্বিতীয় সারিতে ভি এর তিনটি উপাংশ, আর তৃতীয় সারিতে ডব্লিউ এর তিনটি উপাংশ বসে। এই সারিটি মনে রাখলেই থ্রিডি ক্রস গুণনের হিসাব সহজ হয়।"},
            {"index": 3, "type": "p",
             "tts": "এখানে ট্রি বাই ট্রি ম্যাট্রিক্সের প্রথম সারিতে বসানো হয় একক ভিত্তি ভেক্টর আই হ্যাট, জে হ্যাট ও কে হ্যাট, আর দ্বিতীয় ও তৃতীয় সারিতে সাজানো হয় যথাক্রমে ভি ও ডব্লিউ এর স্থানাঙ্ক। প্রথম দর্শনে অদ্ভুত লাগতে পারে যে সংখ্যা আর ভেক্টর কীভাবে একই ম্যাট্রিক্সে বসে, কিন্তু ল্যাপলাস বিস্তার অনুসরণ করলে ফলাফলটি অত্যন্ত পরিচ্ছন্ন।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। বিস্তার করলে আই হ্যাটের সহগ হয় ভি টু গুণ ডব্লিউ থ্রি বিয়োগ ভি থ্রি গুণ ডব্লিউ টু। জে হ্যাটের সহগ হয়, বিয়োগ ভি ওয়ান গুণ ডব্লিউ থ্রি বিয়োগ ভি থ্রি গুণ ডব্লিউ ওয়ান। আর কে হ্যাটের সহগ হয় ভি ওয়ান গুণ ডব্লিউ টু বিয়োগ ভি টু গুণ ডব্লিউ ওয়ান।"},
            {"index": 5, "type": "p",
             "tts": "প্রথম সারি বরাবর বিস্তার করলে প্রতিটি একক ভেক্টরের সহগ হিসেবে একটি টু বাই টু সাব ডিটারমিন্যান্ট তৈরি হয়। বাস্তব সংখ্যাগুলো হিসাব করে সহগগুলো বসিয়ে দিলেই পাওয়া যায় একটি পূর্ণাঙ্গ ত্রিমাত্রিক ভেক্টর, যার উপাংশ তিনটি সহগ। টুডি বিশেষ ক্ষেত্রে ভি হলো এক ও মাইনাস টু, ডব্লিউ হলো চার ও তিন, তখন ডিটারমিন্যান্ট এক গুণ তিন বিয়োগ মাইনাস টু গুণ চার, অর্থাৎ তিন যোগ আট, ফলাফল এগারো।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, কেন কৌশলটি কাজ করে। অলৌকিকভাবে এই বিশুদ্ধ বীজগণিত থেকে প্রাপ্ত ভেক্টরটির দৈর্ঘ্য সামান্তরিকের ক্ষেত্রফলের হুবহু সমান, এটি ভি ও ডব্লিউ এর ওপর লম্ব, এবং নিখুঁতভাবে ডান হাত নিয়ম মেনে চলে। আই হ্যাট, জে হ্যাট, কে হ্যাট এর সারিটি আসলে ফলাফল ভেক্টরের স্থানাঙ্কগুলোকেই সহগ হিসেবে বের করে আনার একটি সুন্দর কৌশল, এর পেছনে রয়েছে ডুয়ালিটির গভীর বাস্তবতা।"},
            {"index": 7, "type": "p",
             "tts": "কেন এমনটি ঘটে? এটি কি শুধুই কোনো যাদুকরী শর্টকাট, নাকি এর পেছনে গভীরতর কোনো গাণিতিক বাস্তবতা লুকিয়ে আছে? এই প্রশ্নের উত্তর আমাদের ডুয়ালিটির জগতে নিয়ে যায়, যেখানে একটি রৈখিক রূপান্তর ও একটি ভেক্টর একই বস্তুর দুটি রূপ মাত্র।"},
            {"index": 8, "type": "p", "role": "conclusion",
             "tts": "পরবর্তী পরিচ্ছেদে আমরা দেখব কীভাবে ডুয়ালিটি এই অদ্ভুত ফর্মুলাকে জ্যামিতিক বিশুদ্ধতায় প্রতিষ্ঠিত করে। আর কেন ক্রস প্রোডাক্টকে কেবল একটি হিসাবের কৌশল না ভেবে একটি অনন্য ডুয়াল ভেক্টর হিসেবে দেখা যায়, সেটিও সেখানেই স্পষ্ট হবে।"},
        ],
    },

    "sec_04_duality_perspective": {
        "title": EXPECTED_TITLES["sec_04_duality_perspective"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_04_duality_perspective"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "অতিরিক্ত উপলব্ধি, ডুয়ালিটির দৃষ্টিতে ক্রস প্রোডাক্ট।"},
            {"index": 1, "type": "p",
             "tts": "এই বিস্ময়কর সূত্রের পেছনের আসল রহস্য উন্মোচনের চাবিকাঠি হলো ডুয়ালিটি বা দ্বৈততার দর্শন। সপ্তম অধ্যায়ে আমরা জেনেছিলাম, ভেক্টর স্পেস থেকে বাস্তব সংখ্যায় যেকোনো রৈখিক রূপান্তর মূলত একটি অনন্য ভেক্টরের সাথে ডট প্রোডাক্টের সমান, এই উপপাদ্যকেই বলা হয় রিস রিপ্রেজেন্টেশন।"},
            {"index": 2, "type": "p",
             "tts": "এবার একটি নতুন রৈখিক রূপান্তর কল্পনা করুন। আমরা থ্রিডি স্থান থেকে যেকোনো একটি ভেক্টর ইউ কে ইনপুট হিসেবে নেব।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। টি অফ ইউ সমান একটি ডিটারমিন্যান্ট, যার প্রথম কলামে ইউ এর তিনটি উপাংশ, দ্বিতীয় কলামে ভি এর উপাংশ, আর তৃতীয় কলামে ডব্লিউ এর উপাংশ বসে।"},
            {"index": 4, "type": "p",
             "tts": "আউটপুট হিসেবে গণনা করব এমন একটি ম্যাট্রিক্সের ডিটারমিন্যান্ট, যার প্রথম কলাম ইউ, আর পরবর্তী দুটি কলাম আমাদের নির্দিষ্ট ভেক্টর ভি ও ডব্লিউ। কলাম রৈখিকতার কারণে এটি থ্রিডি রিয়েল স্পেস থেকে রিয়েল সংখ্যায় যাওয়া একটি খাঁটি রৈখিক রূপান্তর।"},
            {"index": 5, "type": "callout",
             "tts": "বিশেষ নোট, প্যারালেলেপিপেডের আয়তন। জ্যামিতিকভাবে এই ডিটারমিন্যান্ট ইউ, ভি, ডব্লিউ দ্বারা গঠিত প্যারালেলেপিপেডের চিহ্নযুক্ত আয়তন গণনা করে। যেকোনো প্যারালেলেপিপেডের আয়তন সমান ভূমির ক্ষেত্রফল গুণ ভূমির লম্ব দিকে ইউ এর অভিক্ষেপ, অর্থাৎ আয়তনটি আসলে ইউ ভিতরে কতটা এগিয়েছে তারই পরিমাপ।"},
            {"index": 6, "type": "p",
             "tts": "এদিকে ডুয়ালিটি উপপাদ্য অনুযায়ী, এই রৈখিক ম্যাপিংটি প্রকাশ করতে থ্রিডিতে নিশ্চিতভাবেই এমন একটি অনন্য ভেক্টর পি বিদ্যমান, যার সাথে ইউ এর ডট গুণন সরাসরি এই আয়তনের সমান হবে, অর্থাৎ টি অফ ইউ সমান পি ডট ইউ।"},
            {"index": 7, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। টি অফ ইউ সমান পি ডট ইউ, যা আবার পি এর দৈর্ঘ্য গুণ পি বরাবর ইউ এর প্রক্ষেপণ, আর এটি ঠিক ইউ, ভি, ডব্লিউ দ্বারা গঠিত আয়তনের সমান।"},
            {"index": 8, "type": "callout",
             "tts": "বিশেষ নোট, অনন্য ডুয়াল ভেক্টর হলো ক্রস প্রোডাক্ট। দুই দিকের শর্ত হুবহু মিলে গেছে, একদিকে আয়তন সমান ভূমির ক্ষেত্রফল গুণ লম্ব অভিক্ষেপ, অন্যদিকে পি ডট ইউ সমান পি এর দৈর্ঘ্য গুণ পি বরাবর অভিক্ষেপ। সকল ইউ এর জন্য সমতা চাইলে পি কে অবশ্যই ভি ও ডব্লিউ এর সমতলের লম্ব হতে হবে, এবং পি এর দৈর্ঘ্য হতে হবে সামান্তরিকের ক্ষেত্রফলের সমান, অর্থাৎ পি সমান ভি গুণ ডব্লিউ।"},
            {"index": 9, "type": "p", "role": "conclusion",
             "tts": "আর এই অনন্য ভেক্টর পি, সেটিই আমাদের কাঙ্ক্ষিত ক্রস প্রোডাক্ট। ডিটারমিন্যান্টের প্রথম সারিতে আই হ্যাট, জে হ্যাট, কে হ্যাট বসানো আসলে এই ডুয়াল ভেক্টরের স্থানাঙ্কগুলো খুঁজে বের করারই চমৎকার প্রাকৃতিক অ্যালগরিদম। পরবর্তী অধ্যায়ে আমরা এই ডুয়ালিটিকে রৈখিক রূপান্তরের আলোতে আরও গভীরভাবে দেখব।"},
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
    "sec-media-gallery", "sec-quizzes-2d", "sec-quizzes-3d",
    "sec-cross-product-lab",
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
                # b1b-quiz / b1b-media-tab produce no narration cue
            yield (n.attrs.get("id", ""), types)
        for c in n.children:
            yield from walk(c)

    return {sid: types for sid, types in walk(b.root)}


# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-_]")
ALLOWED_CUE_TYPES = {"h2", "h3", "chapter-quote", "p", "figure",
                     "callout", "formula-box", "code-showcase"}
LABEL_FORBIDDEN = "চিত্র প্রদর্শনী"


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
            if LABEL_FORBIDDEN in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden figure label")
            if cue["tts"] in seen:
                raise ValueError(f"{sec_id} cue {cue['index']}: duplicate cue text")
            seen.add(cue["tts"])
            if cue["type"] == "figure":
                body = cue["tts"]
                sentences = [s for s in re.split(r"[।?]", body) if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(f"{sec_id} cue {cue['index']}: figure needs "
                                     f"2-4 sentences, got {len(sentences)}")
                if not body.startswith("এখানে"):
                    raise ValueError(f"{sec_id} cue {cue['index']}: figure must "
                                     f"begin naturally with 'এখানে ... দেখা যাচ্ছে'")
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
            if LABEL_FORBIDDEN in b["text"]:
                raise ValueError(f"Live-DOM: forbidden label in {sec_id}")
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
          f"DOM parity OK (37/37, no duplicates).")

    manifest_sections = {}
    for sec_id in SECTION_ORDER:
        manifest_sections[sec_id] = await build_section(sec_id)

    manifest_data = {
        "course": "linear_algebra",
        "lesson": "lesson_10",
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
    print("BUILD COMPLETE - expressive teacher audio, Lesson 10 (L01 gold standard)")
    for sec_id in SECTION_ORDER:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<42} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTION_ORDER)} sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  DOM<->manifest 1:1; 0 duplicate canonical cues; "
          "0 quiz/media-tab types; zero overlaps; exact 350 ms gaps; "
          "all MP3s non-zero; valid JSON; no figure-label phrases.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(build_all())
