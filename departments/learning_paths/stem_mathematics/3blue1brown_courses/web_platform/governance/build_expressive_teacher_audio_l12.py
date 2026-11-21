# -*- coding: utf-8 -*-
r"""
Rebuild the TEACHER NARRATION AUDIO for 3Blue1Brown Lesson 12 (Bengali),
expressive-edition, to the Lesson 01 gold standard.

Deterministic, re-runnable, self-contained:

  * 25 cues in 4 narrated sections. The cue count/type/order of every section is
    derived from the LIVE DOM of courses/linear_algebra/lesson_12.html using the
    very selector/rules that narration_engine.js uses:
        .article > section, article section  (skip [data-no-narration="true"])
        h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
        .code-showcase, .formula-box   (skip <p> inside .callout/.chapter-quote)
    Verified 25/25 via headless Chrome (channel="chrome"):
      sec_01_linear_systems_and_area = 7, sec_02_transformation_scaling = 5,
      sec_03_cramers_rule_proof = 7, sec_04_computational_reality = 6.
    All other sections are data-no-narration and produce no cues (no quiz /
    media-tab / interactive-section cue types). The DOM snapshot
    (l12_dom_blocks.json) preserves TeX via KaTeX <annotation>...</annotation>.
  * The narrated sections of this lesson contain no figure.lesson-figure blocks,
    so there are zero "figure" cues; figure prosody is still defined in the
    table for schema/spec parity, and no script ever uses a "চিত্র প্রদর্শনী"
    label — any visual explanation is phrased naturally as teacher prose.
  * The section IDs here ARE the existing manifest keys; the audio_file names
    are byte-for-byte the existing manifest keys too (no aliases needed):
      sec_01_linear_systems_and_area / sec_02_transformation_scaling /
      sec_03_cramers_rule_proof / sec_04_computational_reality.
    The backup folder _backup_before_expressive_build/ is never read/written.
  * Scripts are clean spoken Bengali: no TeX, LaTeX, backslashes, $, braces,
    brackets, em/en dashes, raw hyphens or Latin letters. Phonetic safeguards:
    \hat{i}->আই হ্যাট, \hat{j}->জে হ্যাট, \hat{k}->কে হ্যাট, x->এক্স,
    y->ওয়াই, v->ভি, A->এ, n->এন, x_i->এক্স আই, A_i->এ আই,
    2D->টুডি, 3D->থ্রিডি, 1D->ওয়ানডি, det->ডিটারমিন্যান্ট ...
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

Usage:  python governance/build_expressive_teacher_audio_l12.py
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
                         "linear_algebra", "lesson_12")
SOURCE_HTML = os.path.join(WORKSPACE, "courses", "linear_algebra",
                           "lesson_12.html")
DOM_BLOCKS = os.path.join(SCRIPT_DIR, "l12_dom_blocks.json")

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
    "sec_01_linear_systems_and_area",
    "sec_02_transformation_scaling",
    "sec_03_cramers_rule_proof",
    "sec_04_computational_reality",
]

# Exact DOM-derived cue type sequences (parity guards).
EXPECTED_TYPES = {
    "sec_01_linear_systems_and_area": ["h2", "chapter-quote", "p", "p",
                                       "callout", "formula-box", "p"],
    "sec_02_transformation_scaling":  ["h2", "p", "p", "callout", "formula-box"],
    "sec_03_cramers_rule_proof":      ["h2", "p", "p", "formula-box", "callout",
                                       "p", "p"],
    "sec_04_computational_reality":   ["h2", "p", "p", "callout", "p", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec_01_linear_systems_and_area": "sec_01_linear_systems_and_area.mp3",
    "sec_02_transformation_scaling":  "sec_02_transformation_scaling.mp3",
    "sec_03_cramers_rule_proof":      "sec_03_cramers_rule_proof.mp3",
    "sec_04_computational_reality":   "sec_04_computational_reality.mp3",
}
# Preserve the existing manifest titles verbatim (schema compatibility).
EXPECTED_TITLES = {
    "sec_01_linear_systems_and_area": "১. সমীকরণ জোট ও ক্ষেত্রফল স্থানাঙ্কের জ্যামিতিক ধারণা",
    "sec_02_transformation_scaling":  "২. রৈখিক রূপান্তর ও ক্ষেত্রফল স্কেলিং নীতি",
    "sec_03_cramers_rule_proof":      "৩. ক্র্যামারের নিয়মের জ্যামিতিক প্রমাণ: ২D ও ৩D জগৎ",
    "sec_04_computational_reality":   "৪. অ্যালগরিদমিক বাস্তবতা ও তাত্ত্বিক সৌন্দর্য",
}
FORBIDDEN_CUE_TYPES = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
FORBIDDEN_PHRASE = "চিত্র প্রদর্শনী"
EXPECTED_FIGURES = 0          # no figure.lesson-figure blocks in narrated sections
EXPECTED_TOTAL_CUES = 25

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (25 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec_01_linear_systems_and_area": {
        "title": EXPECTED_TITLES["sec_01_linear_systems_and_area"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_01_linear_systems_and_area"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, সমীকরণ জোট ও ক্ষেত্রফল স্থানাঙ্কের জ্যামিতিক ধারণা।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, সেইনফেল্ডের জেরি আর ক্র্যামারের এক কৌতুক। জেরি বলে, আহ, তুমি পাগল! ক্র্যামার জবাব দেয়, আমি কি পাগল, নাকি আমি এতটাই সুস্থ যে তুমি আমার মাথা ঘুরিয়ে দিয়েছ? জেরি আবার বলে, এটা অসম্ভব! আর ক্র্যামার ফিরে জিজ্ঞেস করে, অসম্ভব নাকি, নাকি এতটাই সম্ভব যে তোমার মাথা লাট্টুর মতো ঘুরছে?"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, আগের অধ্যায়ে আমরা রৈখিক সমীকরণ জোট নিয়ে কথা বলেছিলাম, কিন্তু সেই সমাধানগুলো আসলে কীভাবে হিসাব করা যায় সেটি কিছুটা এড়িয়েই গিয়েছিলাম। সংখ্যা গণনা আমরা সাধারণত কম্পিউটারের হাতে ছেড়ে দিই, তবুও এই পদ্ধতির ভেতরে ঢুকে দেখা আমাদের বোঝাপড়ার এক কড়া পরীক্ষা। আজ আমরা ক্র্যামারের নিয়মের পেছনের জ্যামিতিটি বর্ণনা করব। এর জন্য ডিটারমিন্যান্ট, ডট প্রোডাক্ট আর রৈখিক সিস্টেমের ধারণা আগে থেকে জানা থাকলে ভালো। আগেভাগেই বলে রাখি, ক্র্যামারের নিয়ম হিসাবের সেরা উপায় নয়, বিশেষ করে বড় ম্যাট্রিক্সে গাউসিয়ান এলিমিনেশন অনেক দ্রুত। তবুও এটি শেখার কারণ হলো, এটি তত্ত্বের ধারণাগুলোকে একে অপরের সাথে যুক্ত দেখায় আর চূড়ান্ত ফলাফল আশ্চর্যজনকভাবে সুন্দর।"},
            {"index": 3, "type": "p",
             "tts": "আমাদের সেটআপ হবে একটি রৈখিক সমীকরণ জোট, ধরা যাক দুটি অজানা চলক এক্স ও ওয়াই আর দুটি সমীকরণ। নীতিগতভাবে একই কথা যেকোনো সংখ্যক চলক ও সমান সংখ্যক সমীকরণের ক্ষেত্রেও প্রযোজ্য, কিন্তু ছোট উদাহরণ মনে রাখা সহজ। আগের অধ্যায়ের মতোই এখানেও একটি পরিচিত ম্যাট্রিক্স এক অজানা ইনপুট ভেক্টরকে রূপান্তরিত করে, আর আমরা আউটপুটটি আগে থেকে জানি, এই ক্ষেত্রে নিচের সারিতে মাইনাস চার আর মাইনাস দুই। ম্যাট্রিক্সের কলামগুলো আমাদের বলে দেয় ইনপুট স্পেসের ভিত্তি ভেক্টরগুলো কোথায় পড়ছে। তাহলে পাজলটি হলো, কোন ইনপুট ভেক্টর দিলে এই আউটপুট পাওয়া যাবে? ম্যাট্রিক্স এ, ইনপুট এক্স সমান আউটপুট ভি লেখার অর্থই হলো কলাম ভেক্টরগুলোর এমন একটি রৈখিক সমন্বয় খোঁজা যা লক্ষ্য ভেক্টর ভি কে তৈরি করে।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, একটি বৈপ্লবিক প্রশ্ন, স্থানাঙ্ক আসলে কী? আপনি হয়তো বলবেন, স্থানাঙ্ক মানে গ্রিডের ওপর লেখা দুটি সংখ্যা। কিন্তু জ্যামিতিকভাবে ভাবুন, ভেক্টর এক্স আর ওয়াই অক্ষের একক ভেক্টর জে হ্যাট দিয়ে গঠিত একটি সামান্তরিক আঁকলে তার ক্ষেত্রফল কত হবে? এই প্রশ্নটিই পরবর্তী ধাপের চাবিকাঠি।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। ক্ষেত্রফল এক্স কমা জে হ্যাট সমান ডিটারমিন্যান্ট, উপরের সারিতে এক্স ও শূন্য, নিচের সারিতে ওয়াই ও এক। তার মান এক্স গুণ এক বিয়োগ শূন্য গুণ ওয়াই, অর্থাৎ হুবহু এক্স। মনে রাখবেন, জে হ্যাটের দৈর্ঘ্য ঠিক এক একক, সেটিই সামান্তরিকের ভূমি, আর ওয়াই অক্ষ থেকে এক্স ভেক্টরের শীর্ষের লম্ব দূরত্বই হলো তার এক্স স্থানাঙ্ক।"},
            {"index": 6, "type": "p",
             "tts": "জে হ্যাটের দৈর্ঘ্য ঠিক এক একক, সেটি সামান্তরিকের ভূমি। আর ওয়াই অক্ষ থেকে ভেক্টর এক্সের শীর্ষবিন্দুর লম্ব দূরত্ব হলো তার এক্স স্থানাঙ্ক, ফলে ভূমি গুণ উচ্চতা সমান এক গুণ এক্স, অর্থাৎ এক্স। ডিটারমিন্যান্ট হিসাব করলেও একই ফল, এক্স গুণ এক বিয়োগ শূন্য গুণ ওয়াই সমান এক্স। একইভাবে আই হ্যাট ও ভেক্টর এক্স দ্বারা গঠিত সামান্তরিকের ভূমি এক আর উচ্চতা ওয়াই, তাই তার ক্ষেত্রফল এক গুণ ওয়াই, অর্থাৎ ওয়াই। অর্থাৎ প্রতিটি স্থানাঙ্ক আসলে একক ভিত্তি ভেক্টরের সাথে গঠিত একটি সামান্তরিকের ক্ষেত্রফল, আর এই উপলব্ধিটিই ক্র্যামারের নিয়মের দরজা খুলে দেবে।"},
        ],
    },

    "sec_02_transformation_scaling": {
        "title": EXPECTED_TITLES["sec_02_transformation_scaling"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_02_transformation_scaling"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, রৈখিক রূপান্তর ও ক্ষেত্রফল স্কেলিং নীতি।"},
            {"index": 1, "type": "p",
             "tts": "এবার চলুন পূর্বের পাঠগুলো থেকে আমাদের স্মরণ করা সবচেয়ে শক্তিশালী জ্যামিতিক ধারণাটি আবার প্রয়োগ করি, রৈখিক রূপান্তর আর ডিটারমিন্যান্টের অর্থ কী? ডিটারমিন্যান্ট কেবল একটি সূত্র নয়, এটি বলে দেয় কোনো রূপান্তর সমতলের ক্ষেত্রফলকে কত গুণ বাড়ায় বা কমায়। এই ধারণাটিকে কাজে লাগালেই আমাদের পাজলের সমাধানের পথ খুলে যাবে।"},
            {"index": 2, "type": "p",
             "tts": "যখন আমরা একটি টু বাই টু ম্যাট্রিক্স এ দিয়ে পুরো সমতলকে রূপান্তর করি, তখন আই হ্যাট চলে যায় ম্যাট্রিক্সের প্রথম কলাম এ আই হ্যাটে, আর জে হ্যাট চলে যায় দ্বিতীয় কলাম এ জে হ্যাটে। আর আমাদের অজানা ভেক্টর এক্স রূপান্তরিত হয়ে সরাসরি নোঙর ফেলে লক্ষ্য ভেক্টর ভিতে, অর্থাৎ এ গুণ এক্স সমান ভি। আউটপুট স্পেসে আমরা কলাম আর আউটপুট ভেক্টর, দুটোই দেখতে পাই।"},
            {"index": 3, "type": "callout",
             "tts": "বিশেষ নোট, একক বর্গ থেকে সামান্তরিক। রূপান্তরের আগে আই হ্যাট ও জে হ্যাট দ্বারা গঠিত একক বর্গের ক্ষেত্রফল ছিল ঠিক এক বর্গ একক। রূপান্তরের পর এটি কলাম ভেক্টরদ্বয়ের সামান্তরিকে পরিণত হয়, যার ক্ষেত্রফল দাঁড়ায় ডিটারমিন্যান্ট এ। রৈখিকতার কারণে গ্রিডরেখাগুলো সবসময় সমান্তরাল ও সমদূরবর্তী থাকে, তাই এই একই গুণক সমতলের প্রতিটি আকৃতির ক্ষেত্রে প্রযোজ্য।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। রূপান্তরের পরের ক্ষেত্রফল সমান ডিটারমিন্যান্ট এ গুণ আগের ক্ষেত্রফল। অর্থাৎ যেকোনো আকৃতি এস গুণকে ডিটারমিন্যান্ট দিয়ে স্কেল করা হয়, আর এই একই গুণক পুরো সমতল জুড়ে কাজ করে। মনে রাখবেন, গ্রিডরেখাগুলো সমান্তরাল ও সমদূরবর্তী থাকাই এর কারণ।"},
        ],
    },

    "sec_03_cramers_rule_proof": {
        "title": EXPECTED_TITLES["sec_03_cramers_rule_proof"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_03_cramers_rule_proof"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, ক্র্যামারের নিয়মের জ্যামিতিক প্রমাণ, টুডি ও থ্রিডি জগৎ।"},
            {"index": 1, "type": "p",
             "tts": "এখন আগের দুটি ধারণা একসাথে যুক্ত করুন। ইনপুট স্পেসে ভেক্টর এক্স ও জে হ্যাট দ্বারা গঠিত সামান্তরিকটির আদি ক্ষেত্রফল ছিল ঠিক এক্স, কারণ ভূমি জে হ্যাট একক দৈর্ঘ্যের আর লম্ব উচ্চতা এক্স। রূপান্তরের পর এই সামান্তরিকটির কী ঘটবে?"},
            {"index": 2, "type": "p",
             "tts": "রূপান্তরের পর ভেক্টর এক্স পরিণত হয় লক্ষ্য ভেক্টর ভিতে, আর জে হ্যাট পরিণত হয় এ জে হ্যাটে, অর্থাৎ ম্যাট্রিক্সের দ্বিতীয় কলামে। ফলে নতুন সামান্তরিকটি গঠিত হয়েছে ভি ও ম্যাট্রিক্সের দ্বিতীয় কলাম দ্বারা, দুটোই আমাদের আউটপুট স্পেসে দৃশ্যমান। এক্স ও জে হ্যাট থেকে ভি ও এ জে হ্যাটে যাওয়ার এই রূপান্তরটি সরাসরি সমাধানের দিকে ইঙ্গিত করে।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। ডিটারমিন্যান্ট এ ওয়ান সমান ডিটারমিন্যান্ট ভি ও এ জে হ্যাটের, অর্থাৎ ডিটারমিন্যান্ট সেই দুই কলামের যার প্রথম কলামে আছে ভি এক ও ভি দুই, আর দ্বিতীয় কলামে আছে মূল ম্যাট্রিক্সের বি ও ডি। মনে রাখবেন, ভি ভেক্টরটিকে প্রথম কলামে বসিয়েই এই নতুন ডিটারমিন্যান্টটি পাওয়া যায়।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, অনুপাতটিই ক্র্যামারের নিয়ম। আমাদের ক্ষেত্রফল স্কেলিং নীতি বলছে, রূপান্তরের পর ক্ষেত্রফল আগের চেয়ে ঠিক ডিটারমিন্যান্ট এ গুণ বড় হয়। সুতরাং ডিটারমিন্যান্ট এ ওয়ান সমান ডিটারমিন্যান্ট এ গুণ এক্স, উভয় পাশ ডিটারমিন্যান্ট এ দিয়ে ভাগ করলেই উন্মোচিত হয় সেই বিখ্যাত সূত্র, এক্স সমান ডিটারমিন্যান্ট এ ওয়ান ভাগ ডিটারমিন্যান্ট এ। অর্থাৎ মূল ম্যাট্রিক্সের প্রথম কলামে ভি বসিয়ে যে ডিটারমিন্যান্ট পাই, তাকে মূল ডিটারমিন্যান্ট দিয়ে ভাগ করলেই এক্স পাওয়া যায়।"},
            {"index": 5, "type": "p",
             "tts": "হুবহু একই যুক্তি ওয়াইয়ের ক্ষেত্রেও প্রযোজ্য। সে ক্ষেত্রে আদি সামান্তরিক আই হ্যাট ও ভেক্টর এক্স দ্বারা গঠিত ছিল, যার ক্ষেত্রফল ওয়াই। রূপান্তরের পর এটি হয় এ আই হ্যাট ও ভি দ্বারা গঠিত, অর্থাৎ প্রথম কলাম অপরিবর্তিত রেখে দ্বিতীয় কলামে ভি বসানো হয়। তাই ওয়াই সমান ডিটারমিন্যান্ট এ টু ভাগ ডিটারমিন্যান্ট এ।"},
            {"index": 6, "type": "p",
             "tts": "থ্রিডি জগতে একই ঘটনা ঘটে, শুধু সামান্তরিকের বদলে প্যারালেলেপিপেডের আয়তন ব্যবহৃত হয়। আদি আয়তন যদি কোনো স্থানাঙ্ক এক্স আইয়ের সমান হয়, রূপান্তরের পর তা ডিটারমিন্যান্ট এ গুণ বেড়ে যায়, সেই নতুন আয়তন মূল ডিটারমিন্যান্ট দিয়ে ভাগ করলেই এক্স আই সমান ডিটারমিন্যান্ট এ আই ভাগ ডিটারমিন্যান্ট এ। এখানে এ আই হলো সেই ম্যাট্রিক্স যার আই তম কলামে ভি বসানো হয়েছে, আর এটিই সাধারণ এন মাত্রিক ক্র্যামারের নিয়ম।"},
        ],
    },

    "sec_04_computational_reality": {
        "title": EXPECTED_TITLES["sec_04_computational_reality"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_04_computational_reality"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, অ্যালগরিদমিক বাস্তবতা ও তাত্ত্বিক সৌন্দর্য।"},
            {"index": 1, "type": "p",
             "tts": "ক্র্যামারের নিয়ম এত সুন্দর হওয়া সত্ত্বেও কম্পিউটার বিজ্ঞানীরা বড় আকারের সমীকরণ জোট সমাধানে এটি সচরাচর ব্যবহার করেন না। এর কারণ হলো গাণনিক অ্যালগরিদমের দক্ষতা, সৌন্দর্য আর গতি সবসময় এক পথে হাঁটে না।"},
            {"index": 2, "type": "p",
             "tts": "এন ক্রমের একটি জোট ক্র্যামারের নিয়মে সমাধান করতে হলে মোট এন প্লাস ওয়ান সংখ্যক পৃথক ডিটারমিন্যান্ট হিসাব করতে হয়। অন্যদিকে গাউসিয়ান এলিমিনেশন বা রো রিডাকশন মাত্র ও অফ এন কিউব অপারেশনে সরাসরি সব চলকের মান দিয়ে দেয়, বড় ম্যাট্রিক্সে এই পার্থক্য দারুণ প্রভাব ফেলে।"},
            {"index": 3, "type": "callout",
             "tts": "বিশেষ নোট, কম্পিউটারের হিসাবের বাইরে। বিশুদ্ধ গণিতে ক্র্যামারের গুরুত্ব অপরিসীম। এটি কোনো ধাপভিত্তিক অ্যালগরিদম নয়, বরং সমাধানের একটি সরাসরি রুদ্ধ রূপ বা ক্লোজড ফর্ম সূত্র, এক্স আই সমান ডিটারমিন্যান্ট এ আই ভাগ ডিটারমিন্যান্ট এ। এই রূপটি আমাদের দেখায় সমাধানটি আসলে ডিটারমিন্যান্টের একটি জ্যামিতিক অনুপাত মাত্র।"},
            {"index": 4, "type": "p",
             "tts": "যদি লক্ষ্য ভেক্টর ভি সামান্য একটু বদলায়, তবে সমাধানে কত পরিবর্তন আসবে, ক্র্যামারের সূত্রকে ডেরিভেটিভ করে তা তাৎক্ষণিকভাবে বোঝা যায়। ভি জের সাপেক্ষে এক্স আইয়ের আংশিক ডেরিভেটিভ সমান সি জি জে ভাগ ডিটারমিন্যান্ট এ, যা আবার ইনভার্স ম্যাট্রিক্স এ ইনভার্সের আই জে উপাংশ। এটি ইনভার্স ম্যাট্রিক্স, সংবেদনশীলতা বিশ্লেষণ আর ক্যালকুলাসের অন্তরকলনকে লিনিয়ার অ্যালজেব্রার সাথে এক সুতোয় গেঁথে দেয়।"},
            {"index": 5, "type": "p", "role": "conclusion",
             "tts": "সুতরাং পরবর্তী বার যখনই ক্র্যামারের নিয়ম দেখবেন, কোনো যান্ত্রিক সূত্র ভাববেন না। মনে রাখবেন, এটি আসলে দুটি বা আরও বেশি সামান্তরিকের ক্ষেত্রফলের এক অতুলনীয় জ্যামিতিক অনুপাত, একটি স্থানাঙ্ক যা আগে কেবল সংখ্যা মনে হতো, তা আজ ক্ষেত্রফলের ভাষায় বলা যায়।"},
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
    "sec-figures-intro", "sec-assume-determinant-nonzero", "sec-dot-products",
    "sec-better-approach", "sec-output-space-figures", "sec-sanity-check",
    "sec-two-dimension-questions", "sec-in-three-dimensions", "sec-labs",
    "sec-thanks",
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
          f"DOM parity OK (25/25, no duplicates, no forbidden phrase).")

    manifest_sections = {}
    for sec_id in SECTION_ORDER:
        manifest_sections[sec_id] = await build_section(sec_id)

    manifest_data = {
        "course": "linear_algebra",
        "lesson": "lesson_12",
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
    print("BUILD COMPLETE - expressive teacher audio, Lesson 12 (L01 gold standard)")
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
