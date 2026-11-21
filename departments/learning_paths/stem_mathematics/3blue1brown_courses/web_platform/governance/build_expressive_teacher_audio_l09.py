# -*- coding: utf-8 -*-
r"""
Rebuild the TEACHER NARRATION AUDIO for 3Blue1Brown Lesson 09 (Bengali),
expressive-edition, to the Lesson 01 gold standard.

Deterministic, re-runnable, self-contained:

  * 32 cues in 4 narrated sections. The cue count/type/order of every section is
    derived from the LIVE DOM of courses/linear_algebra/lesson_09.html using the
    very selector/rules that narration_engine.js uses:
        .article > section, article section  (skip [data-no-narration="true"])
        h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
        .code-showcase, .formula-box   (skip <p> inside .callout/.chapter-quote)
    Verified 32/32: sec_01_geometric_projection=10, sec_02_symmetry_and_algebra=8,
    sec_03_linear_transformations_to_1d=6, sec_04_duality_and_riesz=8. All other
    sections are data-no-narration and produce no cues (no quiz / media-tab /
    interactive-section cue types). The DOM snapshot (l09_dom_blocks.json)
    preserves TeX via KaTeX <annotation>...</annotation> markers.
  * The section IDs here ARE the existing manifest keys; the audio_file names
    are byte-for-byte the existing manifest keys too (no aliases needed):
    sec_01_geometric_projection / sec_02_symmetry_and_algebra /
    sec_03_linear_transformations_to_1d / sec_04_duality_and_riesz.
    The backup folder _backup_before_expressive_build/ is never read/written.
  * Figure cues are genuine 2-4 sentence pedagogical explanations (4 figures):
    what is drawn / what to notice / why it matters (perpendicular projection,
    projection symmetry, evenly spaced points 2d->1d, diagonal number line).
  * Scripts are clean spoken Bengali: no TeX, LaTeX, backslashes, $, braces,
    brackets, em/en dashes, raw hyphens or Latin letters. Phonetic safeguards:
    \hat{i}->আই হ্যাট, \hat{j}->জে হ্যাট, \hat{u}->ইউ হ্যাট,
    \hat{w}->ডব্লিউ হ্যাট, x->এক্স, y->ওয়াই, v->ভি, w->ডব্লিউ,
    u->ইউ, s->এস, theta->থিটা, cos->কোসাইন, 2D->টুডি, 1D->ওয়ানডি,
    3D->থ্রিডি, M->এম, m-atrix->ম্যাট্রিক্স ...
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

Usage:  python governance/build_expressive_teacher_audio_l09.py
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
                         "linear_algebra", "lesson_09")
SOURCE_HTML = os.path.join(WORKSPACE, "courses", "linear_algebra",
                           "lesson_09.html")
DOM_BLOCKS = os.path.join(SCRIPT_DIR, "l09_dom_blocks.json")

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
    "sec_01_geometric_projection",
    "sec_02_symmetry_and_algebra",
    "sec_03_linear_transformations_to_1d",
    "sec_04_duality_and_riesz",
]

# Exact DOM-derived cue type sequences (parity guards).
# NOTE: the old manifest used "insight-box"; the live DOM renders <b1b-callout>
# as .callout -> narration_engine reports type "callout".
EXPECTED_TYPES = {
    "sec_01_geometric_projection": ["h2", "chapter-quote", "p", "p",
                                    "figure", "formula-box", "h3", "p",
                                    "callout", "p"],
    "sec_02_symmetry_and_algebra": ["h2", "p", "figure", "callout", "p",
                                    "h3", "p", "p"],
    "sec_03_linear_transformations_to_1d": ["h2", "p", "figure", "callout",
                                            "formula-box", "p"],
    "sec_04_duality_and_riesz": ["h2", "p", "figure", "p", "callout",
                                 "formula-box", "p", "chapter-quote"],
}
EXPECTED_AUDIO_FILES = {
    "sec_01_geometric_projection":           "sec_01_geometric_projection.mp3",
    "sec_02_symmetry_and_algebra":           "sec_02_symmetry_and_algebra.mp3",
    "sec_03_linear_transformations_to_1d":   "sec_03_linear_transformations_to_1d.mp3",
    "sec_04_duality_and_riesz":              "sec_04_duality_and_riesz.mp3",
}
# Preserve the existing manifest titles verbatim (schema compatibility).
EXPECTED_TITLES = {
    "sec_01_geometric_projection":         "ডট প্রোডাক্টের জ্যামিতিক প্রক্ষেপণ ও মৌলিক ধারণা",
    "sec_02_symmetry_and_algebra":         "প্রতিসাম্যের রহস্য ও বীজগণিত বনাম জ্যামিতির ধাঁধা",
    "sec_03_linear_transformations_to_1d": "দ্বিমাত্রিক স্থান থেকে একমাত্রিক সংখ্যা রেখায় রৈখিক রূপান্তর",
    "sec_04_duality_and_riesz":            "ডুয়ালিটি বা দ্বৈততা এবং রিজ রিপ্রেজেন্টেশন উপপাদ্য",
}
FORBIDDEN_CUE_TYPES = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
EXPECTED_FIGURES = 4
EXPECTED_TOTAL_CUES = 32

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (32 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec_01_geometric_projection": {
        "title": EXPECTED_TITLES["sec_01_geometric_projection"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_01_geometric_projection"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, ডট প্রোডাক্টের জ্যামিতিক প্রক্ষেপণ ও মৌলিক ধারণা।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, গণিতের সৌন্দর্য আসলে এখানেই, যখন একটি আপাত জটিল বীজগাণিতিক সূত্র চোখের সামনে একটি জীবন্ত জ্যামিতিক ছবিতে রূপ নেয়।"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, লিনিয়ার বীজগণিতে ভেক্টর নিয়ে কাজ করার সময় আমরা প্রায়শই দুটি ভেক্টরের গুণন, অর্থাৎ ডট প্রোডাক্টের মুখোমুখি হই। সাধারণ পাঠ্যবইগুলোতে ডট প্রোডাক্ট শেখানো হয় স্থানাঙ্ক গুণনের একটি যান্ত্রিক সূত্র দিয়ে। প্রথম ভেক্টরের এক্স উপাংশের সাথে দ্বিতীয় ভেক্টরের এক্স উপাংশের গুণ, আর ওয়াই উপাংশের সাথে ওয়াই উপাংশের গুণ করে সবগুলো যোগ করা হয়। সংক্ষেপে ভি ডট ডব্লিউ সমান ভি এক্স গুণ ডব্লিউ এক্স যোগ ভি ওয়াই গুণ ডব্লিউ ওয়াই।"},
            {"index": 3, "type": "p",
             "tts": "কিন্তু এই সূত্রের পেছনের আসল জ্যামিতিক দৃশ্যটি কী? জ্যামিতিকভাবে ডট প্রোডাক্ট মানেই প্রক্ষেপণ, বা প্রোজেকশন। স্ক্রিনের দিকে লক্ষ্য করুন, আমাদের সামনে দুটি ভেক্টর আছে, একটি ভি, অন্যটি ডব্লিউ।"},
            {"index": 4, "type": "figure",
             "tts": "এখানে মূলবিন্দু থেকে ভি ভেক্টরটি একটি সরলরেখা বরাবর প্রসারিত হয়েছে, আর ডব্লিউ এর শীর্ষ থেকে ওই রেখার ওপর একটি লম্ব নামানো হয়েছে। লক্ষ্য করুন, লম্বের পতনবিন্দু থেকে মূলবিন্দু পর্যন্ত যে অংশটি পড়েছে, তাকেই বলা হয় ভি এর ওপর ডব্লিউ এর প্রক্ষেপণ, আর প্রক্ষেপণটি ভি এর দিকেই নির্দেশ করছে, তাই এখানে ডট প্রোডাক্ট হবে ধনাত্মক। এই ছবিটিই মূল কথা শিখায়, ডট প্রোডাক্ট কেবল সংখ্যা গুণন নয়, বরং এক তীরের ছায়া অন্য তীরের দিকে কতদূর পড়ল সেই জ্যামিতি।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। ভি ডট ডব্লিউ সমান, ডব্লিউ এর প্রক্ষেপণের দৈর্ঘ্য গুণ ভি এর নিজস্ব দৈর্ঘ্য। অর্থাৎ আগে ছায়ার দৈর্ঘ্যটি মাপুন, তারপর ভি কত দীর্ঘ তা দিয়ে গুণ করুন, ফলটিই হবে ডট প্রোডাক্ট। মনে রাখবেন ছায়া যত লম্বা, গুণফল তত বড়।"},
            {"index": 6, "type": "h3",
             "tts": "দিকবিন্যাস ও চিহ্নের অর্থ।"},
            {"index": 7, "type": "p",
             "tts": "এই গুণফলের চিহ্ন কিন্তু অত্যন্ত গুরুত্বপূর্ণ। যদি প্রক্ষেপণটি ভি এর মূল অভিমুখের দিকেই নির্দেশ করে, তবে ডট প্রোডাক্ট হবে একটি ধনাত্মক সংখ্যা। এর অর্থ ভেক্টর দুটি মোটামুটি একই দিকে মুখ করে আছে, আর তাদের মধ্যবর্তী কোণ নব্বই ডিগ্রির চেয়ে কম, অর্থাৎ থিটা নব্বই ডিগ্রির কম হলে ভি ডট ডব্লিউ শূন্যের বেশি।"},
            {"index": 8, "type": "callout",
             "tts": "বিশেষ নোট, লম্ব হলে গুণফল শূন্য। যদি ভেক্টর দুটি পরস্পরের সাথে ঠিক সমকোণে থাকে, অর্থাৎ লম্ব বা অর্থোগোনাল হয়, তবে ডব্লিউ এর শীর্ষ থেকে টানা লম্ব সরাসরি মূলবিন্দুতেই পতিত হয়। ফলে প্রক্ষেপণের দৈর্ঘ্য হয় শূন্য, আর তাদের ডট প্রোডাক্টও হয় ঠিক শূন্য, অর্থাৎ থিটা নব্বই ডিগ্রি হলে ভি ডট ডব্লিউ শূন্য।"},
            {"index": 9, "type": "p",
             "tts": "আর যদি ভেক্টর দুটির অভিমুখ বিপরীতমুখী হয়, অর্থাৎ মধ্যবর্তী কোণ নব্বই ডিগ্রির চেয়ে বেশি হয়, তবে প্রক্ষেপণটি ভি এর পেছনের দিকে প্রসারিত হবে। তখন ডট প্রোডাক্টের মান দাঁড়াবে একটি ঋণাত্মক সংখ্যা, অর্থাৎ থিটা নব্বই ডিগ্রির বেশি হলে ভি ডট ডব্লিউ শূন্যের কম।"},
        ],
    },

    "sec_02_symmetry_and_algebra": {
        "title": EXPECTED_TITLES["sec_02_symmetry_and_algebra"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_02_symmetry_and_algebra"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, প্রতিসাম্যের রহস্য ও বীজগণিত বনাম জ্যামিতির ধাঁধা।"},
            {"index": 1, "type": "p",
             "tts": "ডট প্রোডাক্টের এই জ্যামিতিক ব্যাখ্যার দিকে তাকালে প্রথমেই একটি রহস্য মনে খটকা তৈরি করে। বীজগণিতে আমরা জানি ভি ডট ডব্লিউ আর ডব্লিউ ডট ভি সম্পূর্ণ একই কথা, ডট প্রোডাক্ট সম্পূর্ণ প্রতিসম বা সিমেট্রিক। কিন্তু জ্যামিতিকভাবে এটা কি আদৌ স্পষ্ট?"},
            {"index": 2, "type": "figure",
             "tts": "বাঁয়ের ছবিতে ডব্লিউ কে ভি এর ওপর প্রক্ষেপ করে ভি এর দৈর্ঘ্য দিয়ে গুণ করা হয়েছে, আর ডানের ছবিতে ঠিক উল্টোভাবে ভি কে ডব্লিউ এর ওপর প্রক্ষেপ করে ডব্লিউ এর দৈর্ঘ্য দিয়ে গুণ করা হয়েছে। দুটি প্রক্রিয়া দেখতে ভিন্ন হলেও তাদের চূড়ান্ত গুণফল একই, আর এই দৃশ্যটিই প্রশ্ন তোলে, কেন ক্রম বদলালেও ফলাফল অপরিবর্তিত থাকে। লক্ষ্য করুন বাঁ আর ডানের ছায়া আলাদা দিকে হলেও সংখ্যাটি একই দাঁড়িয়েছে।"},
            {"index": 3, "type": "callout",
             "tts": "বিশেষ নোট, সমান দৈর্ঘ্যের ক্ষেত্রে প্রতিসাম্য। এর চমৎকার জ্যামিতিক প্রমাণটি দেখুন, প্রথমে ধরে নিন দুটি ভেক্টরই সমান দৈর্ঘ্যের একক ভেক্টর। এবার তাদের মাঝখান দিয়ে একটি দ্বিখণ্ডক প্রতিসাম্য রেখা কল্পনা করুন, এই কর্ণের সাপেক্ষে সমতলটিকে উল্টে দিলে ভেক্টর দুটি নিজেদের স্থান অদলবদল করে। ফলে একটির ওপর অপরটির প্রক্ষেপণ হুবহু সমান হতে বাধ্য, কারণ ইউ হ্যাট ও ডব্লিউ হ্যাট দুটির দৈর্ঘ্য এক, তাই প্রক্ষেপণও একই।"},
            {"index": 4, "type": "p",
             "tts": "এখন যদি আমরা একটি ভেক্টরকে দ্বিগুণ লম্বা করি, তবে তার নিজস্ব দৈর্ঘ্য দ্বিগুণ হওয়ার কারণে প্রথম গণনায় গুণফল দ্বিগুণ হবে। আবার সদৃশ ত্রিভুজের নিয়মে অপর ভেক্টরের ওপর তার প্রক্ষেপণের দৈর্ঘ্যও ঠিক দ্বিগুণ প্রসারিত হবে। উভয় ক্ষেত্রেই গুণফল একই হারে স্কেল হয়, অর্থাৎ এস গুণ ভি ডট ডব্লিউ সমান ভি ডট এস গুণ ডব্লিউ।"},
            {"index": 5, "type": "h3",
             "tts": "মৌলিক ধাঁধা, প্রক্ষেপণের সাথে স্থানাঙ্ক গুণনের সম্পর্ক কোথায়?"},
            {"index": 6, "type": "p",
             "tts": "কিন্তু এখানে সবচেয়ে গভীর ও বিস্ময়কর প্রশ্নটি রয়ে গেছে। ভেক্টরের শীর্ষ থেকে লম্বালম্বি প্রক্ষেপণ টানার মতো খাঁটি জ্যামিতিক ধারণার সাথে, স্থানাঙ্ক ধরে ধরে গুণ করার এই শুষ্ক বীজগাণিতিক সূত্রের কী সম্পর্ক থাকতে পারে? ভি এক্স গুণ ডব্লিউ এক্স যোগ ভি ওয়াই গুণ ডব্লিউ ওয়াই, আর ভির দৈর্ঘ্য গুণ ডব্লিউ এর দৈর্ঘ্য গুণ কোসাইন থিটা, এই দুটি কি আদতে একই?"},
            {"index": 7, "type": "p",
             "tts": "অধিকাংশ পাঠ্যবই একে কোসাইন সূত্র দিয়ে প্রমাণ করে দেয়, কিন্তু তাতে এর অভ্যন্তরীণ রূপটি বোঝা যায় না। এই রহস্যের পর্দা উন্মোচন করতে হলে আমাদের ফিরে তাকাতে হবে রৈখিক রূপান্তরের দিকে, বিশেষ করে দ্বিমাত্রিক স্থান থেকে একমাত্রিক সংখ্যা রেখায় রূপান্তরের দিকে!"},
        ],
    },

    "sec_03_linear_transformations_to_1d": {
        "title": EXPECTED_TITLES["sec_03_linear_transformations_to_1d"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_03_linear_transformations_to_1d"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, দ্বিমাত্রিক স্থান থেকে একমাত্রিক সংখ্যা রেখায় রৈখিক রূপান্তর।"},
            {"index": 1, "type": "p",
             "tts": "পূর্ববর্তী অধ্যায়ে আমরা অসম আকারের ম্যাট্রিক্স নিয়ে কথা বলেছি। এখন কল্পনা করুন এমন একটি রূপান্তর, যা দ্বিমাত্রিক টুডি সমতলের যেকোনো ভেক্টর গ্রহণ করে এবং আউটপুট হিসেবে একটি একক বাস্তব সংখ্যা, অর্থাৎ একমাত্রিক সংখ্যা রেখার একটি বিন্দু প্রদান করে। সংক্ষেপে বললে রূপান্তরটি টুডি স্পেস থেকে ওয়ানডি স্পেসে যায়।"},
            {"index": 2, "type": "figure",
             "tts": "বাঁয়ের দ্বিমাত্রিক সমতলে একটি সরলরেখার ওপর সমান দূরত্বে কয়েকটি বিন্দু দেখা যাচ্ছে, আর ডানের সংখ্যা রেখায় সেই বিন্দুগুলো আবার সমান দূরত্বেই অবতরণ করেছে। রৈখিকতার দৃশ্যমান পরীক্ষা হলো সমান্তর ও সমদূরবর্তী বিন্দুগুলো রূপান্তরের পরও সমদূরবর্তী থাকবে। যদি দূরত্বের অনুপাত বদলে যায়, তবে বুঝতে হবে রূপান্তরটি রৈখিক নয়, তাই এই ছবি আমাদের রৈখিকতা চেনার একটি সহজ মাপকাঠি দেয়।"},
            {"index": 3, "type": "callout",
             "tts": "বিশেষ নোট, দুই সংখ্যাই যথেষ্ট। লিনিয়ার রূপান্তরের মূল চালিকাশক্তি মনে করুন, যেকোনো রূপান্তর সম্পূর্ণভাবে নির্ধারিত হয় ভিত্তি ভেক্টরগুলো কোথায় গিয়ে পৌঁছায় তার ওপর। এখানে আই হ্যাট রূপান্তরিত হয়ে সংখ্যা রেখার ইউ এক্স নামক সংখ্যায় পরিণত হয়, আর জে হ্যাট পৌঁছায় ইউ ওয়াই নামক অপর সংখ্যায়। মাত্র এই দুটি গন্তব্য জানলেই পুরো রূপান্তরটি বের করা যায়।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। এই রূপান্তরটির ম্যাট্রিক্স এম হলো এক বাই দুই ম্যাট্রিক্স, যার প্রথম ও একমাত্র সারিতে বসে ইউ এক্স আর ইউ ওয়াই। মনে রাখবেন ভিত্তি ভেক্টর দুটির গন্তব্য পাশাপাশি বসিয়েই এই সারিটি গড়া হয়।"},
            {"index": 5, "type": "p",
             "tts": "এখন সমতলের যেকোনো ভেক্টর এক্স ওয়াই এর ওপর এই রূপান্তর প্রয়োগ করলে পাই, ইউ এক্স গুণ এক্স যোগ ইউ ওয়াই গুণ ওয়াই। লক্ষ্য করুন, এক বাই দুই ম্যাট্রিক্সটিকে একটি সাধারণ কলাম ভেক্টরকে শুইয়ে দেওয়ার মতো দেখতে লাগে। আর ম্যাট্রিক্স গুণনের এই ফলাফলটি হুবহু ডট প্রোডাক্টের সূত্রের রূপ ধারণ করে, অর্থাৎ ইউ এক্স গুণ এক্স যোগ ইউ ওয়াই গুণ ওয়াই।"},
        ],
    },

    "sec_04_duality_and_riesz": {
        "title": EXPECTED_TITLES["sec_04_duality_and_riesz"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_04_duality_and_riesz"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, ডুয়ালিটি বা দ্বৈততা এবং রিজ রিপ্রেজেন্টেশন উপপাদ্য।"},
            {"index": 1, "type": "p",
             "tts": "এখন আমাদের দুটি পৃথক জগত একত্রিত হতে যাচ্ছে। মূলবিন্দুগামী একটি তির্যক সরলরেখা কল্পনা করুন, যার ওপর ইউ হ্যাট নামক একক ভেক্টরটি অবস্থান করছে। এই রেখাটিকেই আমরা আমাদের একমাত্রিক সংখ্যা রেখা হিসেবে বিবেচনা করতে পারি, আর ইউ হ্যাটের দৈর্ঘ্য হবে এক।"},
            {"index": 2, "type": "figure",
             "tts": "মূলবিন্দু দিয়ে একটি তির্যক রেখা যাচ্ছে, আর তার ওপর ইউ হ্যাট অবস্থান করছে, এই রেখাটিকেই সংখ্যা রেখার কপি ধরা হয়। সমতলের বিভিন্ন বিন্দু থেকে লম্ব টেনে সবগুলোকে এই রেখার ওপর প্রক্ষেপ করা হয়েছে, আর লক্ষ্য করুন সমদূরবর্তী বিন্দুগুলো প্রক্ষেপণের পরও সমদূরবর্তী সংখ্যায় পড়েছে। অর্থাৎ ছবিটি নিজেই প্রমাণ করছে যে প্রক্ষেপণ একটি রৈখিক রূপান্তর, যা আমাদের পরবর্তী ধাপের ভিত্তি।"},
            {"index": 3, "type": "p",
             "tts": "সমতলের প্রতিটি বিন্দুকে যদি আমরা লম্বালম্বিভাবে এই তির্যক রেখাটির ওপর প্রক্ষেপ করি, তবে এটি কি একটি লিনিয়ার রূপান্তর? উত্তর হলো অবশ্যই হ্যাঁ। সমদূরবর্তী যেকোনো বিন্দু প্রক্ষেপণের পরও সংখ্যা রেখায় নিখুঁত সমদূরত্ব বজায় রাখে, তাই একে একমাত্রিক সংখ্যা রেখার দিকে যাওয়া একটি রৈখিক রূপান্তর বলা যায়।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, জাদুকরী প্রতিসাম্য। আই হ্যাটকে ইউ হ্যাট রেখার ওপর প্রক্ষেপ করলে তার মান কত হবে? প্রতিসাম্যের কারণে আই হ্যাটের ওপর ইউ হ্যাটের প্রক্ষেপণ আর ইউ হ্যাটের ওপর আই হ্যাটের প্রক্ষেপণ হুবহু সমান। এক্স অক্ষের ওপর ইউ হ্যাটের ছায়া হলো ইউ হ্যাটের নিজস্ব এক্স স্থানাঙ্ক ইউ এক্স, আর একইভাবে জে হ্যাটের প্রক্ষেপণ হলো ইউ ওয়াই, তাই প্রক্ষেপণ ম্যাট্রিক্সটি পাওয়া গেল ইউ এক্স ও ইউ ওয়াই নিয়ে।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। ইউ হ্যাট রেখার ওপর যেকোনো ভেক্টর ডব্লিউ এর প্রক্ষেপণ হলো ইউ এক্স গুণ ডব্লিউ এক্স যোগ ইউ ওয়াই গুণ ডব্লিউ ওয়াই। কিন্তু এটি আবার ইউ হ্যাট ডট ডব্লিউ এরও সমান। অর্থাৎ একদিকে লম্ব প্রক্ষেপণ, অন্যদিকে স্থানাঙ্ক গুণন, দুইয়ের ফল একই।"},
            {"index": 6, "type": "p",
             "tts": "যদি ভেক্টরটি একক ভেক্টর না হয়ে যেকোনো ভেক্টর ভি হয়, যার দৈর্ঘ্য এস গুণ বেশি, তবে প্রক্ষেপণের পরিমাপও ঠিক এস গুণ স্কেল হবে। আর এভাবেই জ্যামিতিক প্রক্ষেপণ এবং স্থানাঙ্ক ভিত্তিক বীজগাণিতিক গুণন এক অটুট বন্ধনে আবদ্ধ হয়। ভি ডট ডব্লিউ মানে ভি এক্স গুণ ডব্লিউ এক্স যোগ ভি ওয়াই গুণ ডব্লিউ ওয়াই, আর এটি ঠিক ভি কে একটি রূপান্তর হিসেবে ডব্লিউ এর ওপর প্রয়োগ করার সমান।"},
            {"index": 7, "type": "chapter-quote", "role": "conclusion",
             "tts": "উদ্ধৃতি, গ্রান্ট স্যান্ডারসন বলেন, গণিতে একে বলা হয় ডুয়ালিটি বা দ্বৈততা। বহুমাত্রিক স্থান থেকে একমাত্রিক সংখ্যায় যেকোনো লিনিয়ার রূপান্তর আসলে ওই স্থানের একটি নির্দিষ্ট ভেক্টরের সাথে ডট প্রোডাক্টের সমতুল্য। উচ্চতর গণিতে এটি রিজ রিপ্রেজেন্টেশন থিওরেম নামে অমর হয়ে আছে।"},
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
    "sec-intro-numerical", "sec-quizzes-geometry", "sec-symmetry-practice",
    "sec-media-gallery", "sec-quizzes-linear-transformations",
    "sec-unit-vector", "sec-conclusion", "sec-projection-lab",
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
          f"DOM parity OK (32/32, no duplicates).")

    manifest_sections = {}
    for sec_id in SECTION_ORDER:
        manifest_sections[sec_id] = await build_section(sec_id)

    manifest_data = {
        "course": "linear_algebra",
        "lesson": "lesson_09",
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
    print("BUILD COMPLETE - expressive teacher audio, Lesson 09 (L01 gold standard)")
    for sec_id in SECTION_ORDER:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<40} {len(msec['cues']):>2} cues  "
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
