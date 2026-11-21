# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Probability Lesson 02
("Bayes' Rule and the False Positive Paradox", Bengali) to the gold standard.

Deterministic, re-runnable, self-contained:
  * 37 cues in 4 narrated sections with EXACTLY the same section keys, alias
    keys, audio_file names, cue types and cue order as the live narration-engine
    DOM (verified 9/9/8/11 for sec-puzzle / sec-base-rate / sec-tree-area /
    sec-formula).
  * Scripts were derived from the live DOM through narration_engine.js's own
    selector ('h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
    .code-showcase, .formula-box'), preserving KaTeX <annotation> content, and
    are embedded below as SECTIONS_DATA so the build needs no external input.
  * Visual cues are genuine 2-4 sentence natural explanations — the artificial
    label "চিত্র প্রদর্শনী" is eliminated (all 4 old occurrences are gone).
  * Every script is clean spoken Bengali with phonetic safeguards:
    P(A|B) -> পি এ গিভন বি, Bayes -> বেজ, false positive -> ফলস পজিটিভ,
    prevalence -> প্রেভ্যালেন্স, P(D) -> পি অব ডি, and Bengali numerals only.
    No TeX, LaTeX, backslashes, $, braces, brackets, em-dashes or Latin letters.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, h3 -3%, chapter-quote -3%, p +2%, figure -4%,
      callout-gold/blue +0%, formula-box -8%, conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with the
    exact-ms timings and both canonical + all legacy alias section keys.
  * Bumps the page cache-buster manifest.js?v=N -> ?v=N+1.
  * verify_in_chrome() re-checks everything headlessly with channel=chrome.

Usage:
  python governance/build_expressive_teacher_audio_prob02.py
  python governance/build_expressive_teacher_audio_prob02.py --verify-only
"""

import os
import re
import sys
import json
import copy
import hashlib
import asyncio
import subprocess

import edge_tts

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
VOICE = "bn-BD-PradeepNeural"
GAP_MS = 350.0
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))            # .../governance
WORKSPACE = os.path.dirname(SCRIPT_DIR)                             # .../web_platform
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio",
                         "probability", "lesson_02")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "probability", "lesson_02.html")
MANIFEST_TITLE = "অধ্যায় ০২ — বেজের সূত্র এবং মেডিকেল টেস্ট প্যারাডক্স"

# Prosody keyed by cue type: (rate, pitch, volume)
PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
    "h3":            ("-3%", "+0Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),
    "p":             ("+2%", "+0Hz", "+0%"),   # natural teacher pace
    "figure":        ("-4%", "+0Hz", "+0%"),   # slower, considerate visual explanation
    "callout-gold":  ("+0%", "+0Hz", "+0%"),
    "callout-blue":  ("+0%", "+0Hz", "+0%"),
    "formula-box":   ("-8%", "+0Hz", "+0%"),   # slow and deliberate
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")     # calm concluding prose

# Cue types the narration engine is allowed to emit. quiz / media-tab are
# deliberately absent; non-narrated sections carry data-no-narration.
ALLOWED_CUE_TYPES = set(PROSODY_DEFAULT) | {"conclusion"}

# Parity guards: exact DOM block-type sequence for each narrated section, as
# produced by narration_engine.parseContent() (callout variant from the class).
EXPECTED_TYPES = {
    "sec-puzzle":    ["h2", "chapter-quote", "p", "p", "p", "p", "p",
                      "callout-gold", "p"],
    "sec-base-rate": ["h2", "p", "p", "formula-box", "p", "p", "p",
                      "callout-blue", "p"],
    "sec-tree-area": ["h2", "p", "figure", "p", "p", "h3", "p", "callout-gold"],
    "sec-formula":   ["h2", "p", "formula-box", "p", "formula-box", "p",
                      "formula-box", "p", "formula-box", "p", "callout-gold"],
}
EXPECTED_AUDIO_FILES = {
    "sec-puzzle":    "sec_01_medical_paradox.mp3",
    "sec-base-rate": "sec_02_base_rate.mp3",
    "sec-tree-area": "sec_03_grid_partition.mp3",
    "sec-formula":   "sec_04_bayes_formula.mp3",
}
EXPECTED_COUNT = {
    "sec-puzzle": 9, "sec-base-rate": 9, "sec-tree-area": 8, "sec-formula": 11,
}

# Canonical DOM id -> its legacy alias keys (all keys that must survive in the
# rebuilt manifest). sec-tree-area has three historical aliases.
ALIASES = {
    "sec-puzzle":    ["sec_01_medical_paradox"],
    "sec-base-rate": ["sec_02_base_rate"],
    "sec-tree-area": ["sec-grid-partition", "sec_03_grid_partition", "sec-simulator"],
    "sec-formula":   ["sec_04_bayes_formula"],
}
CANONICAL_ALIAS = {
    "sec-puzzle": "sec_01_medical_paradox",
    "sec-base-rate": "sec_02_base_rate",
    "sec-tree-area": "sec_03_grid_partition",
    "sec-formula": "sec_04_bayes_formula",
}
ALIAS_TO_CANONICAL = {
    alias: canonical for canonical, aliases in ALIASES.items() for alias in aliases
}
# Preserve the exact key order of the existing manifest.
SECTION_KEY_ORDER = [
    "sec-puzzle", "sec_01_medical_paradox",
    "sec-base-rate", "sec_02_base_rate",
    "sec-grid-partition", "sec_03_grid_partition",
    "sec-tree-area", "sec-simulator",
    "sec-formula", "sec_04_bayes_formula",
]

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (37 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-puzzle": {
        "title": "মেডিকেল টেস্টের ক্লাসিক ধাঁধা ও যৌথ সম্ভাব্যতা",
        "audio_file": "sec_01_medical_paradox.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, মেডিকেল টেস্টের ক্লাসিক ধাঁধা ও যৌথ সম্ভাব্যতা।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, নতুন কোনো প্রমাণের মুখে নিজের বিশ্বাসকে ঠিক কতটা হালনাগাদ করা উচিত, তা পরিমাপ করার অনন্য গাণিতিক ভিত্তি হলো বেজের সূত্র। বলেছেন গ্রান্ট স্যান্ডারসন, থ্রি ব্লু ওয়ান ব্রাউন।"},
            {"index": 2, "type": "p",
             "tts": "কল্পনা করুন একটি বাস্তব পরিস্থিতি। একজন ব্যক্তি সম্পূর্ণ সুস্থ বোধ করছেন, কিন্তু রুটিন চেকআপে একটি রক্ত পরীক্ষা করালেন। কিছুদিন পর ল্যাব থেকে রিপোর্ট এলো, তিনি একটি অত্যন্ত মারাত্মক ভাইরাসে পজিটিভ শনাক্ত হয়েছেন।"},
            {"index": 3, "type": "p",
             "tts": "ল্যাবরেটরি থেকে জানানো হলো টেস্টটির তিনটি মূল বৈশিষ্ট্য।"},
            {"index": 4, "type": "p",
             "tts": "প্রথমত, সংবেদনশীলতা বা ট্রু পজিটিভ রেট, শতকরা নিরানব্বই। অর্থাৎ কারো যদি সত্যি রোগ থাকে, তবে টেস্টটি নিরানব্বই শতাংশ ক্ষেত্রে নির্ভুল পজিটিভ ফল দেয়, আর ফলস নেগেটিভের সম্ভাবনা মাত্র এক শতাংশ।"},
            {"index": 5, "type": "p",
             "tts": "দ্বিতীয়ত, নির্দিষ্টতা বা ট্রু নেগেটিভ রেট, শতকরা নিরানব্বই। অর্থাৎ একজন সুস্থ মানুষকে টেস্ট করলে নিরানব্বই শতাংশ ক্ষেত্রে নেগেটিভ রিপোর্ট আসে, আর সুস্থ মানুষের ফলস পজিটিভ আসার সম্ভাবনা মাত্র এক শতাংশ।"},
            {"index": 6, "type": "p",
             "tts": "এবং তৃতীয়ত, রোগটির প্রেভ্যালেন্স বা প্রাইয়র প্রবাবিলিটি। রোগটি সমাজে অত্যন্ত বিরল, প্রতি এক হাজার জনে মাত্র একজনের এই রোগ থাকে। অর্থাৎ পি অব ডি সমান শূন্য দশমিক শূন্য শূন্য এক, বা মাত্র শূন্য দশমিক এক শতাংশ।"},
            {"index": 7, "type": "callout-gold",
             "tts": "বিশেষ নোট, মৌলিক প্রশ্ন, রোগীর রোগাক্রান্ত হওয়ার সম্ভাবনা কত? টেস্ট যেহেতু নিরানব্বই শতাংশ সঠিক এবং ফলাফল পজিটিভ এসেছে, অধিকাংশ মানুষের তাৎক্ষণিক উত্তর হবে, নিশ্চয়ই নিরানব্বই শতাংশ। কিন্তু গণিত আমাদের জানায়, এই রোগীর সত্যি রোগ থাকার সম্ভাবনা নিরানব্বই শতাংশ নয়, বরং মাত্র নয় শতাংশ, অর্থাৎ প্রায় এগারো জনের মধ্যে মাত্র একজন।"},
            {"index": 8, "type": "p", "role": "conclusion",
             "tts": "কেন এমন অবিশ্বাস্য ঘটনা ঘটে? নিরানব্বই শতাংশ নির্ভুল টেস্ট কীভাবে পজিটিভ ফল দেওয়ার পরেও শতকরা নিরানব্বই ভাগের বেশি ক্ষেত্রে ভুল প্রমাণিত হয়? এর উত্তর কোনো জাদু নয়, রয়েছে শুধু বেস রেটের সাথে যৌথ সম্ভাব্যতার গাণিতিক মিলন। একেই বলে ফলস পজিটিভ প্যারাডক্স, বা ভ্রান্ত পজিটিভের ধাঁধা।"},
        ],
    },

    "sec-base-rate": {
        "title": "বেস রেট ফ্যালাসি (Base Rate Fallacy): মস্তিষ্কের অন্ধবিন্দু",
        "audio_file": "sec_02_base_rate.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, বেস রেট ফ্যালাসি, আমাদের মস্তিষ্কের অন্ধবিন্দু।"},
            {"index": 1, "type": "p",
             "tts": "আমাদের সহজাত প্রবৃত্তি কেবল একটি সংখ্যার দিকে তাকায়, টেস্টের নির্ভুলতা শতকরা নিরানব্বই। কিন্তু আমাদের মস্তিষ্ক মূল জনসংখ্যার প্রাথমিক ভারসাম্য, অর্থাৎ বেস রেট পুরোপুরি ভুলে যায়।"},
            {"index": 2, "type": "p",
             "tts": "আসুন ভগ্নাংশের জটিল হিসাবের বদলে বাস্তব এক হাজার জন মানুষের একটি দল কল্পনা করি। যেহেতু প্রতি এক হাজারে মাত্র একজন আক্রান্ত, তাই এই দলটিকে দুটি স্পষ্ট ভাগে ভাগ করা যায়।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, মোট জনসংখ্যা এক হাজার। এর অর্থ, আক্রান্তের সংখ্যা এক, আর সুস্থের সংখ্যা নয়শত নিরানব্বই।"},
            {"index": 4, "type": "p",
             "tts": "প্রথম দল, অসুস্থ দল, মাত্র একজন মানুষ। দ্বিতীয় দল, সুস্থ দল, বাকি নয়শত নিরানব্বই জন মানুষ।"},
            {"index": 5, "type": "p",
             "tts": "এবার এই এক হাজার জনের সবাইকে সেই নিরানব্বই শতাংশ নির্ভুল টেস্টটি করা হলো। অসুস্থ দলের সেই একমাত্র মানুষটির টেস্ট নিরানব্বই শতাংশ সম্ভাবনায় পজিটিভ আসবে। অর্থাৎ আমরা পাব প্রায় একজন ট্রু পজিটিভ।"},
            {"index": 6, "type": "p",
             "tts": "কিন্তু সুস্থ দলের দিকে তাকান। বাকি নয়শত নিরানব্বই জন সম্পূর্ণ সুস্থ, টেস্টের ফলস পজিটিভ রেট মাত্র এক শতাংশ। কিন্তু নয়শত নিরানব্বই জনের এক শতাংশ কত? নয়শত নিরানব্বই গুণ শূন্য দশমিক শূন্য এক, প্রায় দশ জন। অর্থাৎ সুস্থ দল থেকে ভুলবশত প্রায় দশজন ফলস পজিটিভ রিপোর্ট পাবেন।"},
            {"index": 7, "type": "callout-blue",
             "tts": "বিশেষ নোট, মহাবিশ্ব সংকোচনের জাদু। এখন ল্যাবের সব পজিটিভ রিপোর্ট একত্র করা হলো। অসুস্থ দল থেকে একজন আর সুস্থ দল থেকে দশজন, মোট এগারোজন মানুষ পজিটিভ রিপোর্ট হাতে দাঁড়িয়ে আছেন। আপনি যদি এই এগারোজনের একজন হন, তবে আপনার সত্যি রোগ থাকার সম্ভাবনা কত? এগারোজনের মধ্যে কেবল একজন সত্যি অসুস্থ। সুতরাং পি অব ডি গিভন পজিটিভ সমান এক ভাগ এগারো, যা প্রায় নয় দশমিক এক শতাংশ।"},
            {"index": 8, "type": "p", "role": "conclusion",
             "tts": "সুস্থ মানুষের বিশাল সংখ্যা, নয়শত নিরানব্বই জন, টেস্টের সামান্য এক শতাংশ ত্রুটিকে বহুগুণে বিবর্ধিত করে ফেলেছে। এটিই হলো বেস রেট ফ্যালাসি, প্রমাণ যতই শক্তিশালী হোক, যদি মূল ঘটনাটি অত্যন্ত বিরল হয়, তবে প্রাপ্ত প্রমাণের বেশিরভাগই আসলে ফলস অ্যালার্ম। বেস রেট উপেক্ষা করে কেবল টেস্টের নির্ভুলতা দেখাই মস্তিষ্কের এই অন্ধবিন্দু।"},
        ],
    },

    "sec-tree-area": {
        "title": "বৃক্ষচিত্র (Tree Diagram) ও ক্ষেত্রফল বিভাজন গ্রিড",
        "audio_file": "sec_03_grid_partition.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, বৃক্ষচিত্র ও ক্ষেত্রফল বিভাজন গ্রিড।"},
            {"index": 1, "type": "p",
             "tts": "থ্রি ব্লু ওয়ান ব্রাউন সম্ভাব্যতা বোঝাতে সবসময় দুটি শক্তিশালী জ্যামিতিক হাতিয়ার ব্যবহার করেন, সম্ভাব্যতার বৃক্ষ বা প্রোবাবিলিটি ট্রি, এবং ক্ষেত্রফল বিভাজন গ্রিড বা এরিয়া পার্টিশন গ্রিড।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রের বাঁদিকে সম্ভাব্যতার বৃক্ষটি দেখা যাচ্ছে, যেখানে এক হাজার মানুষের মধ্যে মাত্র একজন আক্রান্ত আর বাকি নয়শত নিরানব্বইজন সুস্থ। আক্রান্তের শাখা থেকে পাওয়া যায় প্রায় একজন ট্রু পজিটিভ, কিন্তু সুস্থ দলের মাত্র এক শতাংশ থেকেই চলে আসে প্রায় দশজন ফলস পজিটিভ। ডানদিকের ক্ষেত্রফল গ্রিডে বাঁদিকের অতি সরু স্ট্রিপের ক্ষেত্রফল মাত্র শূন্য দশমিক শূন্য শূন্য নয় নয়, অথচ ডানদিকের চওড়া স্ট্রিপের এক শতাংশ উচ্চতার ক্ষেত্রফল শূন্য দশমিক শূন্য শূন্য নয় নয় নয়। এই ছবিটি দেখেই বোঝা যায়, সুস্থ অংশের ছোট্ট এক শতাংশ ভুলের ক্ষেত্রফল আক্রান্ত অংশের চেয়ে প্রায় দশ গুণ বড়।"},
            {"index": 3, "type": "p",
             "tts": "এবার এটিকে ক্ষেত্রফল হিসেবে চিন্তা করুন। সমগ্র নমুনা ক্ষেত্র একটি বড় আয়তক্ষেত্র, বামপাশে অত্যন্ত সরু একটি খাড়া স্ট্রিপ হলো রোগাক্রান্ত মানুষের অঞ্চল, যার প্রস্থ মাত্র শূন্য দশমিক শূন্য শূন্য এক। ডানপাশের বিশাল অংশ হলো সুস্থ মানুষ, যার প্রস্থ শূন্য দশমিক নয় নয় নয়। বৃক্ষচিত্রের প্রতিটি ডাল আসলে একটি করে উপ ক্ষেত্রফলের সমান, আর সব ডালের শেষ প্রান্তের সম্ভাবনা যোগ করলে মূল এক পাওয়া যায়।"},
            {"index": 4, "type": "p",
             "tts": "টেস্ট পজিটিভ আসার অর্থ হলো আমরা এই দুই অঞ্চল থেকে কেবল পজিটিভ অংশটুকু কেটে আলাদা করলাম। বামদিকের সরু স্ট্রিপের নিরানব্বই শতাংশ উচ্চতার ক্ষেত্রফল শূন্য দশমিক শূন্য শূন্য শূন্য নয় নয়। কিন্তু ডানদিকের চওড়া স্ট্রিপের মাত্র এক শতাংশ উচ্চতার ক্ষেত্রফল শূন্য দশমিক শূন্য শূন্য নয় নয় নয়, যা বামদিকের চেয়ে প্রায় দশ গুণ বড়। তাই পি অব ডি গিভন পজিটিভ, অর্থাৎ পজিটিভ ফলের পর আক্রান্ত হওয়ার সম্ভাবনা, দাঁড়ায় প্রায় শতকরা নয়।"},
            {"index": 5, "type": "h3",
             "tts": "ইন্টারেক্টিভ মেডিকেল বেজ সিমুলেটর, এক হাজার মানুষের ডট গ্রিড।"},
            {"index": 6, "type": "p",
             "tts": "নিচের সিমুলেটরে এক হাজারটি বিন্দু দিয়ে সমগ্র জনসংখ্যাকে দেখানো হয়েছে। স্লাইডার পরিবর্তন করে দেখুন কীভাবে রোগের প্রেভ্যালেন্স এবং টেস্টের নির্ভুলতা বদলের সাথে সাথে ট্রু পজিটিভ ও ফলস পজিটিভের অনুপাত নাটকীয়ভাবে বদলে যায়।"},
            {"index": 7, "type": "callout-gold", "role": "conclusion",
             "tts": "বিশেষ নোট, পরীক্ষা করে দেখুন। রোগের বিস্তার স্লাইডারটি টেনে একশ জনে, অর্থাৎ শতকরা দশে তুলুন। লক্ষ্য করুন কীভাবে ফলস পজিটিভের চেয়ে ট্রু পজিটিভ বৃদ্ধি পায় এবং পোস্টেরিয়র সম্ভাব্যতা মুহূর্তেই শতকরা একানব্বইয়ে পৌঁছে যায়। বেস রেট বাড়ালেই ফলস পজিটিভের আধিপত্য কমে যায়, এটিই পুরো অধ্যায়ের কেন্দ্রীয় শিক্ষা।"},
        ],
    },

    "sec-formula": {
        "title": "বেজের সূত্রের বীজগাণিতিক প্রতিপাদন ও ফিলোসফি",
        "audio_file": "sec_04_bayes_formula.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, বেজের সূত্রের বীজগাণিতিক প্রতিপাদন ও ফিলোসফি।"},
            {"index": 1, "type": "p",
             "tts": "এবার আমরা এই সুন্দর জ্যামিতিক বাস্তবতাকে সার্বজনীন গাণিতিক সংকেতে রূপান্তর করব। শর্তাধীন সম্ভাব্যতার মৌলিক সংজ্ঞা থেকে জানি, একই যৌথ ক্ষেত্রফলকে দুই দিক থেকে মাপলে পি এ গিভন বি সমান পি বি গিভন এ গুণ পি এ ভাগ পি বি, সম্পর্কটি পাওয়া যায়।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, পি অব ডি গিভন পজিটিভ সমান পি অব ডি ইন্টারসেকশন পজিটিভ ভাগ পি অব পজিটিভ।"},
            {"index": 3, "type": "p",
             "tts": "গুণনের নিয়ম অনুসারে লবকে লেখা যায়।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, পি অব ডি ইন্টারসেকশন পজিটিভ সমান পি অব ডি গুণ পি অব পজিটিভ গিভন ডি।"},
            {"index": 5, "type": "p",
             "tts": "এবং সমগ্র সম্ভাব্যতা নীতি অনুসারে হর পি অব পজিটিভ হলো সমস্ত উৎস থেকে আসা পজিটিভের ক্ষেত্রফলের যোগফল, অর্থাৎ ট্রু পজিটিভ ক্ষেত্রফল যোগ ফলস পজিটিভ ক্ষেত্রফল।"},
            {"index": 6, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, পি অব পজিটিভ সমান পি অব ডি গুণ পি অব পজিটিভ গিভন ডি, যোগ পি অব নট ডি গুণ পি অব পজিটিভ গিভন নট ডি।"},
            {"index": 7, "type": "p",
             "tts": "এই দুটি অংশকে একত্র করলেই পাওয়া যায় ইতিহাসখ্যাত বেজের উপপাদ্য, প্রমাণের আলোকে বিশ্বাস হালনাগাদের সার্বজনীন সমীকরণ।"},
            {"index": 8, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, পি অব ডি গিভন পজিটিভ সমান, উপরে পি অব ডি গুণ পি অব পজিটিভ গিভন ডি, এবং নিচে পি অব ডি গুণ পি অব পজিটিভ গিভন ডি যোগ পি অব নট ডি গুণ পি অব পজিটিভ গিভন নট ডি।"},
            {"index": 9, "type": "p",
             "tts": "বেজিয়ান দর্শনের চারটি স্তম্ভ হলো, প্রাইয়র বা প্রাথমিক বিশ্বাস, লাইকলিহুড বা প্রমাণ দেখার সম্ভাবনা, মার্জিনাল বা সমগ্র প্রমাণের হার, এবং পোস্টেরিয়র বা প্রমাণ সাপেক্ষে আমাদের হালনাগাদ বিশ্বাস।"},
            {"index": 10, "type": "callout-gold", "role": "conclusion",
             "tts": "বিশেষ নোট, দ্বিতীয় টেস্টের ক্ষমতা। যদি প্রথম টেস্ট পজিটিভ আসার পর রোগী আরেকটি স্বাধীন দ্বিতীয় টেস্ট করান এবং সেটিও পজিটিভ আসে, তবে কী ঘটবে? এবার তার প্রাইয়র আর শূন্য দশমিক এক শতাংশ থাকবে না, এবার তার নতুন প্রাইয়র হবে প্রথম টেস্টের পোস্টেরিয়র ফল, অর্থাৎ নয় শতাংশ। এই নতুন প্রাইয়র নিয়ে দ্বিতীয়বার হিসাব করলে তার আক্রান্ত হওয়ার সম্ভাবনা নয় শতাংশ থেকে এক লাফে একানব্বই শতাংশে উন্নীত হবে। আজকের পোস্টেরিয়রই আগামীকালের প্রাইয়র, বিজ্ঞান ও যুক্তি এভাবেই একের পর এক প্রমাণ যোগ করে সত্যের কাছাকাছি পৌঁছায়।"},
        ],
    },
}

# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"


def assert_clean_scripts():
    """Fail before any TTS work if a script contains markup, Latin or the label."""
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars {bad!r} in {cue['tts']!r}")
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: artificial figure label present")

    if len(SECTIONS_DATA) != 4:
        raise ValueError("Expected exactly 4 narrated sections")
    total = 0
    for sec_id, sec in SECTIONS_DATA.items():
        types = [c["type"] for c in sec["cues"]]
        if types != EXPECTED_TYPES[sec_id]:
            raise ValueError(f"{sec_id}: cue type/order mismatch -> {types}")
        if sec["audio_file"] != EXPECTED_AUDIO_FILES[sec_id]:
            raise ValueError(f"{sec_id}: audio_file mismatch")
        indices = [c["index"] for c in sec["cues"]]
        if indices != list(range(len(indices))):
            raise ValueError(f"{sec_id}: cue indices are not 0..n-1")
        if len(indices) != EXPECTED_COUNT[sec_id]:
            raise ValueError(f"{sec_id}: cue count mismatch")
        total += len(indices)
    if total != 37:
        raise ValueError(f"Expected 37 cues, found {total}")

    # Visual cues must be genuine 2-4 sentence explanations.
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            if cue["type"] == "figure" or cue.get("visual"):
                sentences = [s for s in cue["tts"].split("।") if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(f"{sec_id} cue {cue['index']}: visual explanation has "
                                     f"{len(sentences)} sentences")

    # Every manifest key (canonical + alias) must be covered by our mapping.
    if set(SECTION_KEY_ORDER) != set(SECTIONS_DATA) | set(ALIAS_TO_CANONICAL):
        raise ValueError("SECTION_KEY_ORDER does not cover canonical + alias keys")


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
    # Edge TTS occasionally replies with an empty stream. Back off and retry;
    # this is a network-response wait, not an arbitrary fixed delay.
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


async def build_section(sec_id, sec):
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
            print(f"  cue {idx:02d} [{cue['type']:<13}] {rate:>4} {pitch:>5}  {cue['tts'][:30]}...")
            await synth_cue(cue["tts"], chunk, rate, pitch, volume)
        else:
            print(f"  cue {idx:02d} [{cue['type']:<13}] cached")
        chunk_paths.append(chunk)
        durations.append(get_duration_ms(chunk))

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

    # Timings from measured durations + the real 350 ms silence chunks.
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
        "section_id": sec_id,
        "alias": CANONICAL_ALIAS[sec_id],
        "title": sec["title"],
        "audio_file": sec["audio_file"],
        "total_duration_ms": round(cursor, 1),
        "cues": manifest_cues,
    }


def bump_page_manifest_version():
    """manifest.js?v=N -> ?v=N+1 so browsers reload the rebuilt manifest."""
    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    pattern = re.compile(r"(manifest\.js\?v=)(\d+)")
    matches = pattern.findall(html)
    if not matches:
        raise RuntimeError("Page manifest cache-buster not found")
    new_html, count = pattern.subn(lambda m: m.group(1) + str(int(m.group(2)) + 1), html)
    with open(PAGE_PATH, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_html)
    print(f"  bumped manifest cache-buster: {matches[0][1]} -> {int(matches[0][1]) + 1} "
          f"({count} occurrence(s))")


async def build_all():
    assert_clean_scripts()
    print(f"Validated {sum(len(s['cues']) for s in SECTIONS_DATA.values())} clean cues "
          f"in {len(SECTIONS_DATA)} sections (0 artificial figure labels).")

    built = {}
    for sec_id, sec in SECTIONS_DATA.items():
        built[sec_id] = await build_section(sec_id, sec)

    # Rebuild all 10 manifest keys in the exact order of the existing manifest.
    manifest_sections = {}
    for key in SECTION_KEY_ORDER:
        canonical = key if key in SECTIONS_DATA else ALIAS_TO_CANONICAL[key]
        obj = copy.deepcopy(built[canonical])
        obj["section_id"] = canonical
        # Every key of a section mirrors it exactly, including the alias field,
        # matching the existing manifest (e.g. all grid keys alias sec_03_grid_partition).
        obj["alias"] = CANONICAL_ALIAS[canonical]
        manifest_sections[key] = obj

    manifest_data = {
        "course": "probability",
        "lesson": "lesson_02",
        "title": MANIFEST_TITLE,
        "voice": VOICE,
        "mode": "authentic_teacher",
        "sections": manifest_sections,
    }

    json_text = json.dumps(manifest_data, ensure_ascii=False, indent=2)
    with open(os.path.join(AUDIO_DIR, "manifest.json"), "w", encoding="utf-8") as fh:
        fh.write(json_text)
    with open(os.path.join(AUDIO_DIR, "manifest.js"), "w", encoding="utf-8") as fh:
        fh.write("window.TEACHER_AUDIO_MANIFEST = " + json_text + ";\n")

    bump_page_manifest_version()

    # Final integrity checks.
    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert list(loaded["sections"]) == SECTION_KEY_ORDER, "manifest key order/keys changed"
    total_cues = 0
    total_ms = 0.0
    figures = 0
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == len(EXPECTED_TYPES[sec_id])
        assert [c["type"] for c in msec["cues"]] == EXPECTED_TYPES[sec_id]
        for alias in ALIASES[sec_id]:
            assert loaded["sections"][alias] == msec, f"alias {alias} != {sec_id}"
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    assert total_cues == 37
    assert figures == 1

    print("\n" + "=" * 66)
    print("BUILD COMPLETE - expressive teacher audio, Probability Lesson 02")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<16} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 4 sections (+6 alias keys), "
          f"{total_ms / 1000.0:.2f}s, {figures} natural figure explanation.")
    print("  manifest.json is valid JSON; all 4 mp3 files exist and are non-empty.")
    print("=" * 66)


# --------------------------------------------------------------------------- #
# Headless Chrome verification (channel=chrome)
# --------------------------------------------------------------------------- #
VERIFY_JS = r"""() => {
  const ne = window.narrationEngine;
  const manifest = window.TEACHER_AUDIO_MANIFEST;
  const sectionEls = [...document.querySelectorAll('.article > section, article section')];

  function domType(node) {
    if (node.classList.contains('chapter-quote')) return 'chapter-quote';
    if (node.classList.contains('callout')) {
      const v = [...node.classList].find(c => c.startsWith('callout-'));
      return v || 'callout';
    }
    if (node.matches('figure.lesson-figure')) return 'figure';
    if (node.classList.contains('formula-box')) return 'formula-box';
    if (node.classList.contains('code-showcase')) return 'code-showcase';
    return node.tagName.toLowerCase();
  }
  const dom = [];
  for (const el of sectionEls) {
    if (el.getAttribute('data-no-narration') === 'true') continue;
    const nodes = [...el.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box')];
    const blocks = [];
    for (const node of nodes) {
      if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) continue;
      const anns = [...node.querySelectorAll('annotation[encoding="application/x-tex"]')]
                     .map(a => a.textContent);
      blocks.push({element: node, type: domType(node), tex: anns, text: node.innerText || ''});
    }
    dom.push({id: el.id, blocks});
  }

  const engine = ne.sections.map(s => ({
    id: s.id, blockCount: s.blocks.length, cueCount: s.cues.length,
    audioFile: s.audioFile, types: s.blocks.map(b => domType(b.element))
  }));

  return {
    manifestPresent: !!manifest,
    hasStudioAudio: !!ne.hasStudioAudio,
    manifestKeys: Object.keys(manifest ? manifest.sections : {}),
    manifest: manifest,
    dom: dom.map(s => ({id: s.id, types: s.blocks.map(b => b.type),
                        tex: s.blocks.filter(b => b.type === 'formula-box').map(b => b.tex)})),
    engine,
    sectionEls: sectionEls.map(s => ({id: s.id, noNarration: s.getAttribute('data-no-narration')}))
  };
}"""


def verify_in_chrome():
    """Return a verification report dict; raises AssertionError on failure."""
    from pathlib import Path
    from playwright.sync_api import sync_playwright

    page_uri = Path(PAGE_PATH).as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page()
        page_errors = []
        page.on("pageerror", lambda e: page_errors.append("pageerror: " + str(e)))
        page.on("console", lambda m: page_errors.append("console.error: " + m.text)
                if m.type == "error" else None)
        page.goto(page_uri, wait_until="load")
        page.wait_for_function(
            "() => !!window.narrationEngine && !!window.narrationEngine.sections "
            "&& window.narrationEngine.sections.length > 0 "
            "&& !!window.TEACHER_AUDIO_MANIFEST")
        data = page.evaluate(VERIFY_JS)
        browser.close()

    assert page_errors == [], f"Page errors: {page_errors}"
    assert data["manifestPresent"], "window.TEACHER_AUDIO_MANIFEST missing"
    assert data["hasStudioAudio"], "Studio teacher audio not bound"

    # Section keys: canonical ids are exactly the DOM ids, in order; the rest
    # are the legacy alias keys that must also be present.
    mkeys = data["manifestKeys"]
    dom_ids = [s["id"] for s in data["dom"]]
    canonical_ids = list(SECTIONS_DATA)
    assert dom_ids == canonical_ids, f"DOM ids changed: {dom_ids} vs {canonical_ids}"
    assert mkeys == SECTION_KEY_ORDER, f"Manifest keys changed: {mkeys}"
    assert canonical_ids == [s["id"] for s in data["engine"]], "Engine ids changed"
    assert not ({"sec-quizzes", "sec-quiz", "sec-media"} & set(dom_ids)), "quiz/media leaked into DOM sections"

    tsections = data["manifest"]["sections"]
    total_cues = 0
    total_ms = 0.0
    dup_check = set()
    disallowed = set()
    forbidden_hits = []
    figure_count = 0
    tex_annotations = 0
    for sec_id in canonical_ids:
        msec = tsections[sec_id]
        dom_sec = next(s for s in data["dom"] if s["id"] == sec_id)
        eng_sec = next(s for s in data["engine"] if s["id"] == sec_id)
        cues = msec["cues"]
        expected_types = EXPECTED_TYPES[sec_id]

        assert len(cues) == EXPECTED_COUNT[sec_id], (sec_id, len(cues))
        assert len(dom_sec["types"]) == len(cues), (sec_id, "DOM block count", dom_sec["types"])
        assert [c["type"] for c in cues] == expected_types, (sec_id, "manifest types")
        assert dom_sec["types"] == expected_types, (sec_id, "DOM types", dom_sec["types"])
        assert eng_sec["types"] == expected_types, (sec_id, "engine types", eng_sec["types"])
        assert eng_sec["blockCount"] == len(cues) == eng_sec["cueCount"], sec_id
        assert msec["audio_file"] == EXPECTED_AUDIO_FILES[sec_id], (sec_id, "audio_file")
        assert msec["audio_file"] in eng_sec["audioFile"], (sec_id, "engine audio binding", eng_sec["audioFile"])

        # TeX annotation must survive for every formula-box block.
        assert len(dom_sec["tex"]) == expected_types.count("formula-box"), (sec_id, "formula-box tex count")
        for tex in dom_sec["tex"]:
            assert isinstance(tex, list) and any(t.strip() for t in tex), (sec_id, "missing TeX annotation")
            tex_annotations += len(tex)

        # Every alias key mirrors its canonical section exactly.
        for alias in ALIASES[sec_id]:
            assert tsections[alias] == msec, f"alias {alias} != {sec_id}"

        for c in cues:
            total_cues += 1
            key = (sec_id, c["index"], c["type"], c["text"])
            assert key not in dup_check, f"Duplicate cue: {key[:3]}"
            dup_check.add(key)
            if c["type"] not in ALLOWED_CUE_TYPES:
                disallowed.add(c["type"])
            if FORBIDDEN_PREFIX in c["text"]:
                forbidden_hits.append(f"{sec_id}/{c['index']}")
            if c["type"] == "figure":
                figure_count += 1
                sentences = [x for x in c["text"].split("।") if x.strip()]
                assert 2 <= len(sentences) <= 4, (sec_id, c["index"], len(sentences))

        # Timing integrity: exact 350 ms gaps, no overlaps, duration agrees.
        cursor = 0.0
        for i, c in enumerate(cues):
            assert abs(c["start_ms"] - cursor) < 1.0, (sec_id, i, "start", c["start_ms"], cursor)
            assert c["duration_ms"] > 0, (sec_id, i, "zero duration")
            assert abs((c["end_ms"] - c["start_ms"]) - c["duration_ms"]) < 1.0, (sec_id, i)
            cursor = c["end_ms"] + (GAP_MS if i < len(cues) - 1 else 0.0)
        assert abs(msec["total_duration_ms"] - cursor) < 1.0, (sec_id, "total_duration_ms")

        af = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(af) and os.path.getsize(af) > 0, af
        total_ms += msec["total_duration_ms"]

    assert total_cues == 37, total_cues
    assert figure_count == 1, figure_count
    assert not disallowed, f"Disallowed cue types: {disallowed}"
    assert not forbidden_hits, f"Artificial figure label found: {forbidden_hits}"

    # No quiz / media-tab anywhere in the narrated manifest or DOM cue types.
    all_dom_types = [t for s in data["dom"] for t in s["types"]]
    assert not ({"quiz", "media-tab", "b1b-quiz", "b1b-media-tab"} & set(all_dom_types)), all_dom_types

    # manifest.js payload must equal manifest.json.
    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        json_obj = json.load(fh)
    with open(os.path.join(AUDIO_DIR, "manifest.js"), encoding="utf-8") as fh:
        js_text = fh.read().strip()
    assert js_text.startswith("window.TEACHER_AUDIO_MANIFEST = ") and js_text.endswith(";")
    js_obj = json.loads(js_text[len("window.TEACHER_AUDIO_MANIFEST = "):-1].strip())
    assert js_obj == json_obj, "manifest.js != manifest.json"

    # Page cache-buster bumped.
    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    versions = [int(v) for _, v in re.findall(r"(manifest\.js\?v=)(\d+)", html)]
    assert versions and min(versions) >= 2, f"manifest ?v not bumped: {versions}"

    return {
        "channels": "channel=chrome, headless=True",
        "sections": len(SECTIONS_DATA),
        "cues": total_cues,
        "per_section": {sid: EXPECTED_COUNT[sid] for sid in canonical_ids},
        "manifest_keys": len(mkeys),
        "alias_keys": len(ALIAS_TO_CANONICAL),
        "figures": figure_count,
        "duplicates": 0,
        "disallowed_types": 0,
        "forbidden_label_hits": 0,
        "page_errors": len(page_errors),
        "total_duration_ms": round(total_ms, 1),
        "total_duration_s": round(total_ms / 1000.0, 2),
        "tex_annotations": tex_annotations,
        "manifest_js_matches_json": True,
        "manifest_version": versions,
        "ok": True,
    }


def main():
    if "--verify-only" not in sys.argv[1:]:
        asyncio.run(build_all())
    print("Running headless Chrome verification only..." if "--verify-only" in sys.argv[1:] else "")
    report = verify_in_chrome()
    print("\n" + "=" * 66)
    print("VERIFICATION REPORT (headless Chrome channel=chrome)")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("=" * 66)
    if not report.get("ok"):
        raise SystemExit("VERIFICATION FAILED")
    print("VERIFIED: 37/37 cues, DOM<->manifest 1:1, 0 dups, "
          "0 quiz/media-tab types, non-zero mp3s, valid JSON, 0 page errors, "
          "0 'চিত্র প্রদর্শনী' labels.")
    print("=" * 66)


if __name__ == "__main__":
    main()
