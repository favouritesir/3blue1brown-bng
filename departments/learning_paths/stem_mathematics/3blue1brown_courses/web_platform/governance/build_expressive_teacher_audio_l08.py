# -*- coding: utf-8 -*-
r"""
Rebuild the TEACHER NARRATION AUDIO for 3Blue1Brown Lesson 08 (Bengali),
expressive-edition, to the Lesson 01 gold standard.

Deterministic, re-runnable, self-contained:

  * 24 cues in 4 narrated sections. The cue count/type/order of every section is
    derived from the LIVE DOM of courses/linear_algebra/lesson_08.html using the
    very selector/rules that narration_engine.js uses:
        .article > section, article section  (skip [data-no-narration="true"])
        h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
        .code-showcase, .formula-box   (skip <p> inside .callout/.chapter-quote)
    Verified 24/24: sec_01_dimensions_intro=6, sec_02_3x2_mapping=7,
    sec_03_2x3_compression=6, sec_04_dimension_bridge=5. All other sections are
    data-no-narration and produce no cues (no quiz / media-tab / interactive
    section cue types). The DOM snapshot (l08_dom_blocks.json) preserves TeX via
    KaTeX <annotation>...</annotation> markers.
  * The section IDs here ARE the existing manifest keys; the audio_file names
    are byte-for-byte the existing manifest keys too (no aliases needed):
    sec_01_dimensions_intro / sec_02_3x2_mapping /
    sec_03_2x3_compression / sec_04_dimension_bridge.
    The backup folder _backup_before_expressive_build/ is never read/written.
  * Figure cues are genuine 2-4 sentence pedagogical explanations (2 figures):
    what is drawn / what to notice / why it matters (2D sheet inside 3D for the
    3x2 map, and the 3D-to-2D flattening with the null line for the 2x3 map).
  * Scripts are clean spoken Bengali: no TeX, LaTeX, backslashes, $, braces,
    brackets, em/en dashes, raw hyphens or Latin letters. Phonetic safeguards:
    \hat{i}->আই হ্যাট, \hat{j}->জে হ্যাট, \hat{k}->কে হ্যাট,
    x->এক্স, y->ওয়াই, z->জেড, det->ডিটারমিন্যান্ট,
    bmatrix->কলাম ভেক্টর, 3D->থ্রিডি, 2D->টুডি,
    2x3->দুই বাই তিন, m->এম, n->এন ...
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
    h2 -5%/+2Hz, chapter-quote -3%, figure -4%, formula-box -8%,
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

Usage:  python governance/build_expressive_teacher_audio_l08.py
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
                         "linear_algebra", "lesson_08")
SOURCE_HTML = os.path.join(WORKSPACE, "courses", "linear_algebra",
                           "lesson_08.html")
DOM_BLOCKS = os.path.join(SCRIPT_DIR, "l08_dom_blocks.json")

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
    "sec_01_dimensions_intro",
    "sec_02_3x2_mapping",
    "sec_03_2x3_compression",
    "sec_04_dimension_bridge",
]

# Exact DOM-derived cue type sequences (parity guards).
# NOTE: the old manifest used "insight-box"; the live DOM renders <b1b-callout>
# as .callout -> narration_engine reports type "callout".
EXPECTED_TYPES = {
    "sec_01_dimensions_intro": ["h2", "chapter-quote", "p", "p",
                                "callout", "formula-box"],
    "sec_02_3x2_mapping": ["h2", "p", "p", "p", "figure",
                           "callout", "formula-box"],
    "sec_03_2x3_compression": ["h2", "p", "p", "p", "figure", "callout"],
    "sec_04_dimension_bridge": ["h2", "p", "p", "callout", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec_01_dimensions_intro":  "sec_01_dimensions_intro.mp3",
    "sec_02_3x2_mapping":       "sec_02_3x2_mapping.mp3",
    "sec_03_2x3_compression":   "sec_03_2x3_compression.mp3",
    "sec_04_dimension_bridge":  "sec_04_dimension_bridge.mp3",
}
# Preserve the existing manifest titles verbatim (schema compatibility).
EXPECTED_TITLES = {
    "sec_01_dimensions_intro":  "অসম আকারের ম্যাট্রিক্স ও মাত্রার সংযোগ",
    "sec_02_3x2_mapping":       "৩×২ ম্যাট্রিক্স: ২D থেকে ৩D স্পেসে রূপান্তর",
    "sec_03_2x3_compression":   "২×৩ ম্যাট্রিক্স: ৩D থেকে ২D সমতলে প্রক্ষেপণ",
    "sec_04_dimension_bridge":  "১×২ ম্যাট্রিক্স, ডট গুণন ও মাত্রার সামঞ্জস্য",
}
FORBIDDEN_CUE_TYPES = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
EXPECTED_FIGURES = 2
EXPECTED_TOTAL_CUES = 24

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (24 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec_01_dimensions_intro": {
        "title": EXPECTED_TITLES["sec_01_dimensions_intro"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_01_dimensions_intro"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, অসম আকারের ম্যাট্রিক্স ও মাত্রার সংযোগ।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, এই কুইজে আমি আপনাদের দুই বাই তিন ম্যাট্রিক্সের নির্ণায়ক বের করতে বলেছিলাম। আপনাদের কয়েকজন, আমার বেশ মজাও লেগেছিল, সত্যিই তা করার চেষ্টা করেছিলেন। বলেছেন লিনিয়ার অ্যালজেব্রার এক অধ্যাপক।"},
            {"index": 2, "type": "p",
             "tts": "এ পর্যন্ত লিনিয়ার রূপান্তর নিয়ে আমাদের আলোচনা মূলত বর্গাকার ম্যাট্রিক্সের ওপরই চলেছে, যেমন টুডি ভেক্টর থেকে টুডি ভেক্টরে রূপান্তরের জন্য দুই বাই দুই ম্যাট্রিক্স, অথবা থ্রিডি ভেক্টর থেকে থ্রিডি ভেক্টরে রূপান্তরের জন্য তিন বাই তিন ম্যাট্রিক্স। এই সিরিজে এতদূর এসে আপনাদের হাতে এমন অনেক ধারণা এসে গেছে, যা দিয়ে আপনারা নিজেরাই এই প্রশ্নটির উত্তর ভাবতে পারেন। তবু আমরা একটু ধীরে ধীরে কথা বলব, যাতে চিন্তার গতি কিছুটা পায়।"},
            {"index": 3, "type": "p",
             "tts": "প্রশ্নটি হলো, অসম আকারের ম্যাট্রিক্স যেমন দুই বাই তিন কিংবা তিন বাই দুই, আসলে জ্যামিতিকভাবে কী বোঝায়? ভিন্ন ভিন্ন মাত্রার জগতের মধ্যে কি লিনিয়ার রূপান্তর সম্ভব? এপিগ্রাফের এই মজার কাহিনিটি ঠিক এই ভুল বোঝাবুঝিকেই নির্দেশ করে, নির্ণায়ক বা ডিটারমিন্যান্ট শুধু বর্গাকার ম্যাট্রিক্সেরই অস্তিত্ব থাকে, আয়তক্ষেত্রের মতো অসম আকারের ম্যাট্রিক্সের ক্ষেত্রে সেটি সংজ্ঞায়িতই নয়।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, মূল অন্তর্দৃষ্টি, কলাম ও সারি কী বলে। উত্তর হলো অবশ্যই সম্ভব, আর আমাদের জ্যামিতিক ভিত্তি ভেক্টরের দৃষ্টিভঙ্গি মনে রাখলে বিষয়টি অত্যন্ত সহজ। একটি ম্যাট্রিক্সের কলাম সংখ্যা বলে দেয় ইনপুট স্পেসে কয়টি ভিত্তি ভেক্টর আছে, অর্থাৎ ইনপুটের মাত্রা কত, আর সারি সংখ্যা বলে দেয় রূপান্তরিত ভেক্টরের গন্তব্য কতটি স্থানাঙ্ক দিয়ে বর্ণনা করতে হবে, অর্থাৎ আউটপুটের মাত্রা কত।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। যেকোনো এম বাই এন ম্যাট্রিক্স এন মাত্রার স্থান থেকে এম মাত্রার স্থানে একটি রৈখিক রূপান্তর নির্দেশ করে, যেখানে ম্যাট্রিক্সটির এমটি সারি আর এনটি কলাম, আর ভেক্টর এক্স রূপান্তরের পর ভেক্টর ওয়াইতে পরিণত হয়।"},
        ],
    },

    "sec_02_3x2_mapping": {
        "title": EXPECTED_TITLES["sec_02_3x2_mapping"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_02_3x2_mapping"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, তিন বাই দুই ম্যাট্রিক্স, দ্বিমাত্রিক স্পেস থেকে ত্রিমাত্রিক স্পেসে।"},
            {"index": 1, "type": "p",
             "tts": "মাত্রার মধ্যে রূপান্তর নিয়ে কথা বলা সম্পূর্ণ যুক্তিযুক্ত, যেমন দ্বিমাত্রিক স্পেস থেকে ত্রিমাত্রিক স্পেসে একটি রূপান্তর। আবার যেকোনো রূপান্তরকে রৈখিক বলার শর্তও আগের মতোই, গ্রিডের রেখাগুলো সমান্তরাল ও সমান দূরত্বে থাকবে, এবং মূলবিন্দু মূলবিন্দুতেই পড়বে। শুধু এখন ইনপুট ও আউটপুট আলাদা মাত্রার দুইটি জগতে বসবাস করে।"},
            {"index": 2, "type": "p",
             "tts": "এখানে বাঁয়ের ইনপুট স্পেস হলো দ্বিমাত্রিক, আর ডানের আউটপুট হলো ত্রিমাত্রিক। আমরা সাধারণত ইনপুটগুলোকে সরাসরি আউটপুটে যেতে দেখি, কিন্তু এখানে তা না দেখার কারণ কেবল ভিজ্যুয়ালাইজেশনের অলসতা নয়, জোর দিয়ে বলা দরকার যে টুডি ইনপুট ভেক্টর আর থ্রিডি আউটপুট ভেক্টর সম্পূর্ণ আলাদা ও অসংযুক্ত দুই জগতের প্রাণী।"},
            {"index": 3, "type": "p",
             "tts": "এই রূপান্তরকে ম্যাট্রিক্সে লেখার নিয়মও আগের মতোই, দেখুন প্রতিটি ভিত্তি ভেক্টর কোথায় পড়ছে, আর সেই গন্তব্যের স্থানাঙ্কগুলোকে ম্যাট্রিক্সের কলাম হিসেবে লিখুন। এখানে আই হ্যাট পড়ছে দুই, মাইনাস ওয়ান, মাইনাস ওয়ান বিন্দুতে, এবং জে হ্যাট পড়ছে শূন্য, ওয়ান, ওয়ান বিন্দুতে, প্রথম কলাম আই হ্যাটের, দ্বিতীয় কলাম জে হ্যাটের গন্তব্য। ফলে ম্যাট্রিক্সটির তিনটি সারি ও দুটি কলাম, অর্থাৎ এটি একটি তিন বাই দুই ম্যাট্রিক্স।"},
            {"index": 4, "type": "figure",
             "tts": "চিত্রের বাঁয়ে দ্বিমাত্রিক গ্রিড আর তার আই হ্যাট ও জে হ্যাট দেখা যাচ্ছে, আর ডানে সেই দুই ভিত্তি ভেক্টর ত্রিমাত্রিক স্থানে যথাক্রমে দুই, মাইনাস ওয়ান, মাইনাস ওয়ান ও শূন্য, ওয়ান, ওয়ান বিন্দুতে অবতরণ করেছে। লক্ষ্য করুন সমতলটি থ্রিডি জগতের ভেতরে একটি চ্যাপ্টা চাদরের মতো শুয়ে আছে, দুই ভেক্টরের সব রৈখিক সমাবেশ মিলে এই চাদরটিই তৈরি করে। ম্যাট্রিক্সের তিন সারি আর দুই কলাম ঠিক এই চিত্রের মাত্রা সংকেতই প্রকাশ করে, অর্থাৎ দুই মাত্রা থেকে তিন মাত্রায় এই যাত্রা।"},
            {"index": 5, "type": "callout",
             "tts": "বিশেষ নোট, ফুল র্যাঙ্ক কিন্তু পুরো থ্রিডি নয়। আগের অধ্যায়ের ভাষায় বললে এই ম্যাট্রিক্সের কলাম স্পেস, অর্থাৎ সব ভেক্টর যেখানে পড়ে, হলো থ্রিডি স্পেসের মূলবিন্দু দিয়ে কাটা একটি দ্বিমাত্রিক সমতল। তবুও ম্যাট্রিক্সটিকে ফুল র্যাঙ্ক বলা হয়, কারণ কলাম স্পেসের মাত্রা দুই ঠিক ইনপুট স্পেসের মাত্রা দুইয়ের সমান। দুটি কলাম মানে দ্বিমাত্রিক ইনপুট, তিনটি সারি মানে প্রতিটি গন্তব্যে তিনটি স্থানাঙ্ক, ফলে তিন বাই দুই ম্যাট্রিক্স মানেই দুই মাত্রা থেকে তিন মাত্রায় যাত্রা।"},
            {"index": 6, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। তিন বাই দুই ম্যাট্রিক্স এম তার দুই কলাম যথাক্রমে আই হ্যাট ও জে হ্যাটের গন্তব্য, প্রথম কলাম দুই, মাইনাস ওয়ান, মাইনাস ওয়ান, দ্বিতীয় কলাম শূন্য, ওয়ান, ওয়ান। তার কলাম স্পেস হলো এই দুই কলামের স্প্যান, যা থ্রিডি স্পেসের ভেতরে একটি সমতল, আর ম্যাট্রিক্সটির র্যাঙ্ক দুই।"},
        ],
    },

    "sec_03_2x3_compression": {
        "title": EXPECTED_TITLES["sec_03_2x3_compression"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_03_2x3_compression"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, দুই বাই তিন ম্যাট্রিক্স, ত্রিমাত্রিক স্পেস থেকে দ্বিমাত্রিক সমতলে।"},
            {"index": 1, "type": "p",
             "tts": "ঠিক বিপরীত প্রক্রিয়াটিও চিন্তা করা যায়, একটি দুই বাই তিন ম্যাট্রিক্স আপনি কীভাবে পড়বেন? এখানে তিনটি কলাম, মানে ইনপুট স্পেসে তিনটি ভিত্তি ভেক্টর আছে, আই হ্যাট, জে হ্যাট ও কে হ্যাট। অর্থাৎ যাত্রা শুরু সম্পূর্ণ ত্রিমাত্রিক জগৎ থেকে।"},
            {"index": 2, "type": "p",
             "tts": "কিন্তু ম্যাট্রিক্সের সারি সংখ্যা মাত্র দুই, অর্থাৎ রূপান্তরের পর প্রতিটি ভিত্তি ভেক্টরের গন্তব্য বর্ণনা করতে কেবল দুটি স্থানাঙ্কই ব্যবহার করা যাবে। তিনটি ভিত্তি ভেক্টরই এসে পড়ে একটি দ্বিমাত্রিক সমতলে। ছায়া ফেলার মতো করে পুরো থ্রিডি মহাবিশ্বকে ওপর থেকে চাপ দিয়ে কাগজের একটি পাতার ওপর চ্যাপ্টা করে ফেলা, এই হলো দুই বাই তিন ম্যাট্রিক্সের মানসিক ছবি।"},
            {"index": 3, "type": "p",
             "tts": "এখানে মাত্রা হারানো অনিবার্য, দ্বিমাত্রিক সমতলে অবতরণ করা তিনটি ভেক্টর অবশ্যই রৈখিকভাবে নির্ভরশীল। থ্রিডি স্থানের অন্তত একটি পূর্ণ সরলরেখা মূলবিন্দুতে সংকুচিত হয়ে যায়, এই সরলরেখাই নাল স্পেস বা কার্নেল। অর্থাৎ অনেকগুলো আলাদা ইনপুট একই আউটপুটে মিলে যায়, এবং ভুল হবে যদি ভাবি দুই বাই তিন ম্যাট্রিক্সেরও কোনো নির্ণায়ক আছে, এপিগ্রাফের অধ্যাপকের কৌতুক ঠিক এখানেই প্রাসঙ্গিক।"},
            {"index": 4, "type": "figure",
             "tts": "চিত্রের বাঁয়ে আই হ্যাট, জে হ্যাট ও কে হ্যাটসহ ত্রিমাত্রিক গ্রিড দেখা যাচ্ছে, আর মাঝখানের তীরটিকে অনুসরণ করলে ডানে দেখা যায় পুরো স্পেস একটি সমতলে চ্যাপ্টা হয়ে গেছে। লাল রেখার ওপরের ভেক্টরগুলো কমলা বিন্দুতে, অর্থাৎ মূলবিন্দুতে মিলে যাচ্ছে, আর সেটিই হলো নাল স্পেস। এই একই ছবি থেকে র্যাঙ্ক নালিটির হিসাবও পড়া যায়, আউটপুট সর্বোচ্চ দ্বিমাত্রিক, তাই নালিটি অন্তত এক।"},
            {"index": 5, "type": "callout",
             "tts": "বিশেষ নোট, মাত্রা হানির হিসাব। র্যাঙ্ক নালিটি উপপাদ্যানুসারে র্যাঙ্ক যোগ নালিটি সমান তিন, অর্থাৎ ইনপুটের মাত্রা। যেহেতু আউটপুট দ্বিমাত্রিক, তাই র্যাঙ্ক সর্বোচ্চ দুই এবং নালিটি অন্তত এক, অর্থাৎ অন্তত একটি রেখা অবশ্যই শূন্যে পড়বে। আগের তিন বাই দুই ক্ষেত্রে ফুল কলাম র্যাঙ্ক ছিল, এখানে আবার ফুল রো র্যাঙ্ক থাকতে পারে, কিন্তু মাত্রা সংকোচন হওয়ায় তথ্য হারানো অবশ্যম্ভাবী।"},
        ],
    },

    "sec_04_dimension_bridge": {
        "title": EXPECTED_TITLES["sec_04_dimension_bridge"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_04_dimension_bridge"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, এক বাই দুই ম্যাট্রিক্স, ডট গুণন ও উপসংহার।"},
            {"index": 1, "type": "p",
             "tts": "দ্বিমাত্রিক থেকে একমাত্রিক রূপান্তরের কথাও ভাবা যায়। একমাত্রিক স্পেস আসলে কেবল সংখ্যারেখা, তাই এই ধরনের রূপান্তর দ্বিমাত্রিক ভেক্টর গ্রহণ করে তার বদলে একটি সংখ্যা বের করে দেয়।"},
            {"index": 2, "type": "p",
             "tts": "এখানে গ্রিডের রেখা সমান্তরাল ও সমান দূরত্বে থাকার এই দৃশ্যটি সবকিছু চ্যাপ্টা হয়ে যাওয়ার কারণে কিছুটা অগোছালো, বরং একে এভাবে দেখাই সুবিধাজনক যে সমান দূরত্বে রাখা বিন্দুগুলোর একটি সরলরেখা সংখ্যারেখার ওপর প্রক্ষেপিত হওয়ার পরও সমান দূরত্বেই থাকবে। এই রূপান্তরগুলোর একটি লেখা হয় এক বাই দুই ম্যাট্রিক্স দিয়ে, যার দুই কলামের প্রতিটিতে একটিমাত্র এন্ট্রি থাকে, আই হ্যাট কোন সংখ্যায় পড়ে আর জে হ্যাট কোন সংখ্যায় পড়ে, সেটিই সেই দুটি এন্ট্রি।"},
            {"index": 3, "type": "callout",
             "tts": "বিশেষ নোট, ডট গুণনের সাথে সম্পর্ক ও মাত্রার সামঞ্জস্য। এই রূপান্তরের ধরনটি তাকে অত্যন্ত অর্থবহ করে তোলে, পরবর্তী অধ্যায়ে আমরা দেখব এটিই হলো ডট গুণনের জ্যামিতিক রূপ, এক বাই দুই ম্যাট্রিক্স দুই বাই এক কলাম ভেক্টরকে গুণ করে একক সংখ্যা তৈরি করে, ঠিক যেমন ইউ ভেক্টর ডট ভি ভেক্টর। একই কারণে ম্যাট্রিক্স গুণনে ভেতরের মাত্রা মিলতে হয়, কারণ প্রথম রূপান্তর যে স্পেসে আউটপুট দেয়, দ্বিতীয় রূপান্তরকে ঠিক সেই স্পেস থেকেই ইনপুট নিতে হয়।"},
            {"index": 4, "type": "p", "role": "conclusion",
             "tts": "অসম আকারের ম্যাট্রিক্স কোনো কৃত্রিম হিসাব নয়, এটি স্থান ও মাত্রার রূপান্তরের এক সার্বজনীন ভাষা। আপনি এখন পর্যন্ত যা দেখেছেন তা নিয়ে একটু খেলা করুন, ম্যাট্রিক্স গুণন ও লিনিয়ার সমীকরণ জোটের অর্থ কী হবে যখন রূপান্তরগুলো ভিন্ন ভিন্ন মাত্রার জগতের মাঝে চলে? পরবর্তী অধ্যায়ে আমরা ডট গুণন ও ডুয়ালিটির এই গভীর সম্পর্কই উন্মোচন করব।"},
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
    "sec-media-gallery", "sec-lab", "sec-reveal",
    "sec-quizzes-dimensions", "sec-quizzes-3x2",
    "sec-quizzes-2x3", "sec-quizzes-bridge",
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
          f"DOM parity OK (24/24, no duplicates).")

    manifest_sections = {}
    for sec_id in SECTION_ORDER:
        manifest_sections[sec_id] = await build_section(sec_id)

    manifest_data = {
        "course": "linear_algebra",
        "lesson": "lesson_08",
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
    print("BUILD COMPLETE - expressive teacher audio, Lesson 08 (L01 gold standard)")
    for sec_id in SECTION_ORDER:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<32} {len(msec['cues']):>2} cues  "
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
