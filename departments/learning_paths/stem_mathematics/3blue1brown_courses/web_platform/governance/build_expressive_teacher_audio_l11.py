# -*- coding: utf-8 -*-
r"""
Rebuild the TEACHER NARRATION AUDIO for 3Blue1Brown Lesson 11 (Bengali),
expressive-edition, to the Lesson 01 gold standard.

Deterministic, re-runnable, self-contained:

  * 24 cues in 5 narrated sections. The cue count/type/order of every section is
    derived from the LIVE DOM of courses/linear_algebra/lesson_11.html using the
    very selector/rules that narration_engine.js uses:
        .article > section, article section  (skip [data-no-narration="true"])
        h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
        .code-showcase, .formula-box   (skip <p> inside .callout/.chapter-quote)
    Verified 24/24: sec_01_cross_product_puzzle=6, sec_02_volume_function=5,
    sec_03_duality_and_dual_vector=4, sec_04_geometric_proof_p=5,
    sec_05_algebraic_synthesis=4. All other sections are data-no-narration and
    produce no cues (no quiz / media-tab / interactive-section cue types). The
    DOM snapshot (l11_dom_blocks.json) preserves TeX via KaTeX
    <annotation>...</annotation> markers.
  * The section IDs here ARE the existing manifest keys; the audio_file names
    are byte-for-byte the existing manifest keys too (no aliases needed):
    sec_01_cross_product_puzzle / sec_02_volume_function /
    sec_03_duality_and_dual_vector / sec_04_geometric_proof_p /
    sec_05_algebraic_synthesis.
    The backup folder _backup_before_expressive_build/ is never read/written.
  * Figure cues are genuine 2-4 sentence pedagogical explanations that start
    naturally (never a "চিত্র প্রদর্শনী" label): what is drawn / what to notice /
    why it matters (the signed volume of the parallelepiped and its linearity).
  * Scripts are clean spoken Bengali: no TeX, LaTeX, backslashes, $, braces,
    brackets, em/en dashes, raw hyphens or Latin letters. Phonetic safeguards:
    \hat{i}->আই হ্যাট, \hat{j}->জে হ্যাট, \hat{k}->কে হ্যাট, v->ভি, w->ডব্লিউ,
    u->ইউ, p->পি, theta->থিটা, sin->সাইন, 3D->থ্রিডি, 2D->টুডি, 1D->ওয়ানডি ...
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
    no "চিত্র প্রদর্শনী" label and DOM<->manifest 1:1 parity (source +
    browser-extracted DOM blocks) before reporting success.

Usage:  python governance/build_expressive_teacher_audio_l11.py
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
                         "linear_algebra", "lesson_11")
SOURCE_HTML = os.path.join(WORKSPACE, "courses", "linear_algebra",
                           "lesson_11.html")
DOM_BLOCKS = os.path.join(SCRIPT_DIR, "l11_dom_blocks.json")

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
    "sec_01_cross_product_puzzle",
    "sec_02_volume_function",
    "sec_03_duality_and_dual_vector",
    "sec_04_geometric_proof_p",
    "sec_05_algebraic_synthesis",
]

# Exact DOM-derived cue type sequences (parity guards).
# NOTE: the old manifest used "insight-box"; the live DOM renders <b1b-callout>
# as .callout -> narration_engine reports type "callout".
EXPECTED_TYPES = {
    "sec_01_cross_product_puzzle": ["h2", "chapter-quote", "p", "p",
                                    "callout", "p"],
    "sec_02_volume_function":      ["h2", "p", "p", "callout", "figure"],
    "sec_03_duality_and_dual_vector": ["h2", "p", "p", "callout"],
    "sec_04_geometric_proof_p":    ["h2", "p", "p", "callout", "formula-box"],
    "sec_05_algebraic_synthesis":  ["h2", "p", "p", "callout"],
}
EXPECTED_AUDIO_FILES = {
    "sec_01_cross_product_puzzle":    "sec_01_cross_product_puzzle.mp3",
    "sec_02_volume_function":         "sec_02_volume_function.mp3",
    "sec_03_duality_and_dual_vector": "sec_03_duality_and_dual_vector.mp3",
    "sec_04_geometric_proof_p":       "sec_04_geometric_proof_p.mp3",
    "sec_05_algebraic_synthesis":     "sec_05_algebraic_synthesis.mp3",
}
# Preserve the existing manifest titles verbatim (schema compatibility).
EXPECTED_TITLES = {
    "sec_01_cross_product_puzzle":
        "ক্রস প্রোডাক্টের অদ্ভুত সূত্রের রহস্য ও গভীর জিজ্ঞাসা",
    "sec_02_volume_function":
        "সামান্তরিক গোলকের আয়তন এবং ত্রিমাত্রিক রৈখিক ফাংশন",
    "sec_03_duality_and_dual_vector":
        "ডুয়ালিটির ঐশ্বর্য ও দ্বৈত ভেক্টর p-এর অস্তিত্ব",
    "sec_04_geometric_proof_p":
        "জ্যামিতিক প্রমাণ: ভেক্টর p-এর দৈর্ঘ্য ও দিক নির্ধারণ",
    "sec_05_algebraic_synthesis":
        "বীজগাণিতিক সমাপনী: সিউডো-ডিটারমিন্যান্টের পরিপূর্ণ যৌক্তিকতা",
}
FORBIDDEN_CUE_TYPES = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
EXPECTED_FIGURES = 1
EXPECTED_TOTAL_CUES = 24
FORBIDDEN_PHRASE = "চিত্র প্রদর্শনী"

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (24 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec_01_cross_product_puzzle": {
        "title": EXPECTED_TITLES["sec_01_cross_product_puzzle"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_01_cross_product_puzzle"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, ক্রস প্রোডাক্টের অদ্ভুত সূত্রের রহস্য ও গভীর জিজ্ঞাসা।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, পিয়ের দেলিগ্ন বলেছেন, গ্রোথেন্ডিকের কাছ থেকে আমি শিখেছি যে প্রমাণের কঠিনতা নিয়ে গর্ব করা উচিত নয়। কঠিনতা মানে আমরা এখনো বুঝতে পারিনি। লক্ষ্য হলো এমন এক প্রাকৃতিক দৃশ্য আঁকা যার ভেতরে প্রমাণটি স্বতঃসিদ্ধ হয়ে ওঠে।"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, গত অধ্যায়ে আমরা ক্রস প্রোডাক্টের জ্যামিতিক রূপটি দেখেছি। দুটি থ্রিডি ভেক্টর ভি এবং ডব্লিউ এর ক্রস প্রোডাক্ট এমন একটি নতুন ভেক্টর তৈরি করে, যার দৈর্ঘ্য ওই দুই ভেক্টর দ্বারা গঠিত সামান্তরিকের ক্ষেত্রফলের সমান, অর্থাৎ ভি এর দৈর্ঘ্য গুণ ডব্লিউ এর দৈর্ঘ্য গুণ সাইন থিটা, আর দিক ডান হাতের নিয়ম মেনে উভয় ভেক্টরের ওপর লম্ব।"},
            {"index": 3, "type": "p",
             "tts": "কিন্তু ক্লাসরুমে হিসাব করার সময় একটি অদ্ভুত সূত্র শেখানো হয়। প্রথম সারিতে আই হ্যাট, জে হ্যাট ও কে হ্যাট লিখে একটি তিন বাই তিন ছদ্ম নির্ণায়ক হিসাব করা হয়। সংখ্যার জায়গায় ভিত্তি ভেক্টর বসিয়ে নম্বরের মতো আচরণ করানো, এই অদ্ভুততা কি শুধু মুখস্থ করার কৌশল?"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, কাকতালীয় কৌশল নাকি চিরন্তন জ্যামিতিক সত্য। প্রশ্ন হলো, সংখ্যার বদলে ডিটারমিন্যান্টের ভেতরে আই হ্যাট, জে হ্যাট ও কে হ্যাট বসিয়ে দেওয়া কি কেবল কোনো গাণিতিক কারসাজি? নাকি এর পেছনে রৈখিক বীজগণিতের এমন এক গভীর সংযোগ লুকিয়ে আছে, যা একবার বুঝলে সূত্রটি আর কৌশল থাকবে না? উত্তর খুঁজতে আমাদের দরকার হবে অধ্যায় পাঁচের ডিটারমিন্যান্ট এবং অধ্যায় নয়ের ডুয়ালিটি।"},
            {"index": 5, "type": "p",
             "tts": "আজকের পর্বে দেখব, এই রহস্যের চাবিকাঠি হলো ডুয়ালিটি বা দ্বৈততার নীতি। রৈখিক রূপান্তরের দৃষ্টিকোণ থেকে এই সূত্রটি একেবারেই সহজ ও অনিবার্য হয়ে ওঠে। ক্রস প্রোডাক্টকে একটি বিশেষ রৈখিক রূপান্তরের দ্বৈত ভেক্টর হিসেবে দেখলেই সবকিছু পরিষ্কার হয়।"},
        ],
    },

    "sec_02_volume_function": {
        "title": EXPECTED_TITLES["sec_02_volume_function"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_02_volume_function"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, সামান্তরিক গোলকের আয়তন এবং ত্রিমাত্রিক রৈখিক ফাংশন।"},
            {"index": 1, "type": "p",
             "tts": "দুটি নির্দিষ্ট ভেক্টর ভি ও ডব্লিউ নেওয়া যাক। এদের সাথে যেকোনো পরিবর্তনশীল ভেক্টর ইউ যুক্ত করে একটি ফাংশন সংজ্ঞায়িত করি, যা ইনপুটে একটি ভেক্টর গ্রহণ করে আউটপুটে একটি বাস্তব সংখ্যা প্রদান করে। সংক্ষেপে বললে এটি আর থ্রি থেকে আর ওয়ানে যাওয়া একটি ফাংশন।"},
            {"index": 2, "type": "p",
             "tts": "জ্যামিতিকভাবে এই ফাংশনটি ইউ, ভি ও ডব্লিউ দ্বারা গঠিত সামান্তরিক গোলক, অর্থাৎ প্যারালেলেপাইপেডের চিহ্নিত আয়তন বের করে। অধ্যায় পাঁচ থেকে আমরা জানি, তিনটি কলাম ভেক্টরের এই আয়তনই হলো তাদের তিন বাই তিন ম্যাট্রিক্সের নির্ণায়ক। ঋণাত্মক চিহ্নটি তিন ভেক্টরের ডান হাতের ওরিয়েন্টেশন উল্টে যাওয়া নির্দেশ করে।"},
            {"index": 3, "type": "callout",
             "tts": "বিশেষ নোট, কেন এটি একটি রৈখিক রূপান্তর। সবচেয়ে গুরুত্বপূর্ণ কথা হলো, ডিটারমিন্যান্ট তার যেকোনো একটি কলামের সাপেক্ষে পুরোপুরি রৈখিক, অর্থাৎ মাল্টিলিনিয়ার। যেহেতু ভি ও ডব্লিউ স্থির এবং শুধু ইউ পরিবর্তনশীল, তাই ইউ কে দ্বিগুণ করলে ফলাফলও দ্বিগুণ হয়, আর দুটি ইউ এর যোগফল নিলে ফল দুটির সমষ্টি পাওয়া যায়। অর্থাৎ আমাদের হাতে আসলেই একটি থ্রিডি থেকে ওয়ানডি রৈখিক রূপান্তর আছে।"},
            {"index": 4, "type": "figure",
             "tts": "এখানে তিনটি ভেক্টর ইউ, ভি ও ডব্লিউ একসাথে একটি সামান্তরিক গোলক গঠন করেছে, আর এদের ডিটারমিন্যান্টই সেই গোলকের চিহ্নিত আয়তন। লক্ষ্য করুন, ইউ কে দ্বিগুণ করলে গোলকের আয়তনও দ্বিগুণ হয়, আর দুটি ইউ এর যোগফল নিলে আয়তন দুটির সমষ্টি পাওয়া যায়। এই দুটি পর্যবেক্ষণই ফাংশনটির রৈখিকতার চাক্ষুষ প্রমাণ। স্থির ভি ও ডব্লিউ এর দিকে তাকিয়ে বুঝুন কেন কেবল প্রথম কলামের ওপর ফাংশনটি নির্ভর করে।"},
        ],
    },

    "sec_03_duality_and_dual_vector": {
        "title": EXPECTED_TITLES["sec_03_duality_and_dual_vector"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_03_duality_and_dual_vector"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, ডুয়ালিটির ঐশ্বর্য ও দ্বৈত ভেক্টর পি এর অস্তিত্ব।"},
            {"index": 1, "type": "p",
             "tts": "অষ্টম ও নবম অধ্যায়ের ডুয়ালিটির কথা মনে করুন। যেকোনো স্থান থেকে সংখ্যা রেখায় যাওয়া একটি রৈখিক রূপান্তরকে এক সারি ম্যাট্রিক্স দিয়ে লেখা যায়, আর সেই ম্যাট্রিক্সকে পাশে শুইয়ে দিলেই পাওয়া যায় একটি দ্বৈত ভেক্টর। রূপান্তরটি প্রয়োগ করা আর ওই ভেক্টরের সাথে ডট গুণন করা একই কাজ। দ্বিমাত্রিক ক্ষেত্রে এক বাই দুই ম্যাট্রিক্স আর ইউ হ্যাট ভেক্টরের ডট গুণন ছিল ঠিক এই একই সম্পর্কের প্রকাশ।"},
            {"index": 2, "type": "p",
             "tts": "এখন একই কথা ত্রিমাত্রিক ক্ষেত্রে প্রয়োগ করি। আমাদের ফাংশনটি একটি থ্রি টু ওয়ান রূপান্তর, তাই এটি একটি এক বাই থ্রি ম্যাট্রিক্স দ্বারা প্রকাশিত হয়, যার তিনটি ঘরে বসে পি ওয়ান, পি টু ও পি থ্রি। এই ম্যাট্রিক্সের সাথে ইউ এর গুণন আসলেই পি ভেক্টরের সাথে ইউ এর ডট গুণনের সমান। অর্থাৎ এমন একটি অনন্য ভেক্টর পি অবশ্যই আছে, যার জন্য প্রতিটি ইউ এর ক্ষেত্রে পি ডট ইউ সমান ইউ, ভি ও ডব্লিউ দ্বারা গঠিত ডিটারমিন্যান্ট।"},
            {"index": 3, "type": "callout",
             "tts": "বিশেষ নোট, এখন একমাত্র কাজ, পি কে। একদিকে ফাংশনটি হলো ইউ, ভি ও ডব্লিউ এর প্যারালেলেপাইপেডের আয়তন। অন্যদিকে ডুয়ালিটি বলছে, একই আয়তনকে সবসময় একটি নির্দিষ্ট ভেক্টর পি এর সাথে ইউ এর ডট গুণন হিসেবেও লেখা যায়। এখন প্রশ্ন, এই রহস্যময় ভেক্টর পি আসলে কে, আর তার জ্যামিতিক বৈশিষ্ট্য কী? দুই ভাবে উত্তর খুঁজব, প্রথমে হিসাব করে, তারপর ছবি দিয়ে।"},
        ],
    },

    "sec_04_geometric_proof_p": {
        "title": EXPECTED_TITLES["sec_04_geometric_proof_p"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_04_geometric_proof_p"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, জ্যামিতিক প্রমাণ, ভেক্টর পি এর দৈর্ঘ্য ও দিক নির্ধারণ।"},
            {"index": 1, "type": "p",
             "tts": "জ্যামিতির মূল সূত্রে ফিরে যাই। যেকোনো সামান্তরিক গোলকের আয়তন হলো ভূমির ক্ষেত্রফল গুণ লম্ব উচ্চতা। এখানে ভূমি হলো ভি ও ডব্লিউ দ্বারা গঠিত সামান্তরিক, যার ক্ষেত্রফল আমরা জানি। আর উচ্চতা হলো ভি ও ডব্লিউ এর তলের ওপর লম্ব রেখার দিকে ইউ এর প্রক্ষেপণ, অর্থাৎ প্রজেকশন এইচ। আয়তন সমান ভূমির ক্ষেত্রফল গুণ এইচ।"},
            {"index": 2, "type": "p",
             "tts": "এখন ডট গুণনের জ্যামিতিক রূপটি স্মরণ করুন। পি ডট ইউ মানে হলো পি এর দৈর্ঘ্যের সাথে ইউ এর পি এর দিকে লম্ব প্রক্ষেপণের গুণফল। এই দুটি রাশি প্রতিটি ইউ এর জন্য সমান হতে হলে পি কে অবশ্যই ভি ও ডব্লিউ এর তলের ওপর লম্ব হতে হবে, এবং তার দৈর্ঘ্য হতে হবে ভূমির ক্ষেত্রফলের সমান।"},
            {"index": 3, "type": "callout",
             "tts": "বিশেষ নোট, ডান হাতের নিয়ম দিক নির্ধারণ করে। ঋণাত্মক ও ধনাত্মক আয়তনের অবস্থাও মেলাতে হবে। পি ডট ইউ ঋণাত্মক হবে ঠিক তখনি, যখন ইউ, ভি, ডব্লিউ এর ডান হাতের ওরিয়েন্টেশন ঋণাত্মক, যেমন ভি ও ডব্লিউ বদলালে চিহ্ন উল্টে যায়। তাই পি এর অভিমুখও হতে হবে অবিকল ডান হাতের নিয়ম অনুযায়ী। তর্জনী ভি দিকে, মধ্যমা ডব্লিউ দিকে ধরলে বুঁড়ু পি এর দিক দেখায়।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। পি ভি ও ডব্লিউ দ্বারা সৃষ্ট তলের ওপর লম্ব, আর পি এর দৈর্ঘ্য সমান ভি ও ডব্লিউ এর সামান্তরিকের ক্ষেত্রফল, অর্থাৎ ভি ক্রস ডব্লিউ এর দৈর্ঘ্য। এই থেকেই পাওয়া যায় পি সমান ভি ক্রস ডব্লিউ। মনে রাখবেন, দৈর্ঘ্য মিলল আর দিক মিলল, তাই দুটি ভেক্টর হুবহু একই।"},
        ],
    },

    "sec_05_algebraic_synthesis": {
        "title": EXPECTED_TITLES["sec_05_algebraic_synthesis"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_05_algebraic_synthesis"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, বীজগাণিতিক সমাপনী, সিউডো ডিটারমিন্যান্ট সূত্রের পরিপূর্ণ যৌক্তিকতা।"},
            {"index": 1, "type": "p",
             "tts": "এবার হিসাবটি মিলিয়ে নেওয়া যাক। তিন বাই তিন ডিটারমিন্যান্টকে প্রথম কলাম ইউ এর সাপেক্ষে বিস্তার করলে পাই, ইউ ওয়ান গুণ ভি টু ডব্লিউ থ্রি বিয়োগ ভি থ্রি ডব্লিউ টু, যোগ ইউ টু গুণ ভি থ্রি ডব্লিউ ওয়ান বিয়োগ ভি ওয়ান ডব্লিউ থ্রি, যোগ ইউ থ্রি গুণ ভি ওয়ান ডব্লিউ টু বিয়োগ ভি টু ডব্লিউ ওয়ান। প্রতিটি বন্ধনী ঠিক সেই সহগ যা আমরা জ্যামিতিকভাবেই পেয়েছিলাম।"},
            {"index": 2, "type": "p",
             "tts": "যেহেতু এটি পি ডট ইউ, অর্থাৎ পি ওয়ান গুণ ইউ ওয়ান যোগ পি টু গুণ ইউ টু যোগ পি থ্রি গুণ ইউ থ্রি, এর সমান, তাই ইউ ওয়ান, ইউ টু ও ইউ থ্রির এই তিনটি সহগই হলো সরাসরি কাঙ্ক্ষিত ভেক্টর পি এর তিনটি স্থানাঙ্ক। প্রথমটি ভি টু ডব্লিউ থ্রি বিয়োগ ভি থ্রি ডব্লিউ টু, দ্বিতীয়টি ভি থ্রি ডব্লিউ ওয়ান বিয়োগ ভি ওয়ান ডব্লিউ থ্রি, আর তৃতীয়টি ভি ওয়ান ডব্লিউ টু বিয়োগ ভি টু ডব্লিউ ওয়ান।"},
            {"index": 3, "type": "callout", "role": "conclusion",
             "tts": "বিশেষ নোট, জাদুকরি কৌশল নয়, ডুয়ালিটির প্রতিচ্ছবি। আর এই কারণেই পাঠ্যবইগুলোতে ইউ এর জায়গায় প্রতীকীভাবে আই হ্যাট, জে হ্যাট ও কে হ্যাট লিখে দেওয়া হয়, যাতে বিস্তার করার পর স্বয়ংক্রিয়ভাবে ওই সহগগুলো ভেক্টর আকারে প্রকাশিত হয়। এটি কোনো জাদুকরি কৌশল নয়, বরং ডুয়ালিটির এক অনবদ্য গাণিতিক প্রতিচ্ছবি। বীজগণিত ও জ্যামিতি এখানে এক মোহনায় মিলিত হয়েছে, আর ক্রস প্রোডাক্টের সূত্রটি তার সম্পূর্ণ অর্থ পেয়েছে।"},
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
    "sec-intro-formulas", "sec-media-gallery", "sec-practice-quizzes",
    "sec-conclusion", "sec-duality-lab", "sec-cross-product-lab",
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
    title, so the effective selector is 'article section'. Only the five
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
            if FORBIDDEN_PHRASE in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: "
                                 f"forbidden phrase '{FORBIDDEN_PHRASE}'")
            if cue["tts"] in seen:
                raise ValueError(f"{sec_id} cue {cue['index']}: duplicate cue text")
            seen.add(cue["tts"])
            if cue["type"] == "figure":
                body = cue["tts"]
                sentences = [s for s in re.split(r"[।?]", body) if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(f"{sec_id} cue {cue['index']}: figure needs "
                                     f"2-4 sentences, got {len(sentences)}")
                if body.lstrip().startswith(FORBIDDEN_PHRASE):
                    raise ValueError(f"{sec_id} cue {cue['index']}: figure must "
                                     f"start naturally")
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
          f"DOM parity OK (24/24, no duplicates, no '{FORBIDDEN_PHRASE}').")

    manifest_sections = {}
    for sec_id in SECTION_ORDER:
        manifest_sections[sec_id] = await build_section(sec_id)

    manifest_data = {
        "course": "linear_algebra",
        "lesson": "lesson_11",
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
    if any(FORBIDDEN_PHRASE in t for t in all_texts):
        raise RuntimeError(f"Written manifest contains '{FORBIDDEN_PHRASE}'")

    print("\n" + "=" * 70)
    print("BUILD COMPLETE - expressive teacher audio, Lesson 11 (L01 gold standard)")
    for sec_id in SECTION_ORDER:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<34} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTION_ORDER)} sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanation.")
    print("  DOM<->manifest 1:1; 0 duplicate canonical cues; "
          "0 quiz/media-tab types; zero overlaps; exact 350 ms gaps; "
          f"no '{FORBIDDEN_PHRASE}'; all MP3s non-zero; valid JSON.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(build_all())
