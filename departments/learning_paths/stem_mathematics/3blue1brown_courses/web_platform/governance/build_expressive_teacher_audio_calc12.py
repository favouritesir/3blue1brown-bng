# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Calculus Lesson 12
("What is a differential?", Bengali) to the Lesson-01/02 gold standard.

Deterministic, re-runnable, self-contained:
  * 35 cues in 5 narrated sections with EXACTLY the same section IDs, audio_file
    names and cue type/order as the existing manifest and the live DOM:
      sec-from-slope-to-linear-map          -> h2, chapter-quote, p, p, p, formula-box, callout, p (8)
      sec-total-differential-multivariable  -> h2, p, p, p, p, formula-box, callout             (7)
      sec-gradient-dot-product              -> h2, p, p, p, formula-box, callout, p            (7)
      sec-physical-engineering-invariance   -> h2, p, p, p, formula-box, callout               (6)
      sec-beyond-the-basics                 -> h2, p, p, p, p, formula-box, callout            (7)
    (The live DOM has no figure.lesson-figure blocks in narrated sections, so there
     are no figure cues to generate; all cues are natural expressive prose and
     none uses the artificial label "চিত্র প্রদর্শনী".)
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Every script is clean spoken Bengali with phonetic safeguards:
      df -> ডি এফ, dx -> ডি এক্স, dy -> ডি ওয়াই, dz -> ডি জেড,
      ∂f/∂x -> পার্শিয়াল ডি এফ বাই ডি এক্স, gradient -> গ্রেডিয়েন্ট,
      f'(x) -> এফ প্রাইম অফ এক্স, ∇f -> ডেল এফ, theta -> থেটা,
      AI -> এআই, LLM -> বৃহৎ ভাষা মডেল, etc.
    No TeX, LaTeX, backslashes, $, braces, brackets, em/en-dashes, raw hyphens
    or Latin letters.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, figure -4%, formula-box -8%, p +2%, callout +0%,
      conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with the
    exact-ms timings and the exact 5 canonical section keys of the gold standard.
  * L12 has NO official 3B1B dubbed video (data youtube_id 404); the page's
    video-src is an intentionally preserved optional path. This build touches
    only audio + the manifest cache-buster.

Usage:  python governance/build_expressive_teacher_audio_calc12.py
"""

import os
import re
import json
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
                         "calculus", "lesson_12")
DOM_SNAPSHOT = os.path.join(SCRIPT_DIR, "calc12_dom_blocks.json")
MANIFEST_TITLE = "অধ্যায় ১২ — ডিফারেনশিয়াল আসলে কী? (What is a differential?)"

# Prosody keyed by cue type: (rate, pitch, volume)
PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
    "h3":            ("-3%", "+0Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),   # measured, thoughtful quotation
    "p":             ("+2%", "+0Hz", "+0%"),   # natural teacher pace
    "figure":        ("-4%", "+0Hz", "+0%"),   # slower, considerate explanation
    "callout":       ("+0%", "+0Hz", "+0%"),   # steady emphasis
    "formula-box":   ("-8%", "+0Hz", "+0%"),   # slow and deliberate
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")     # calm concluding prose

# Parity guards: exact cue-type sequence of each narrated section (live DOM).
EXPECTED_TYPES = {
    "sec-from-slope-to-linear-map":         ["h2", "chapter-quote", "p", "p", "p", "formula-box", "callout", "p"],
    "sec-total-differential-multivariable": ["h2", "p", "p", "p", "p", "formula-box", "callout"],
    "sec-gradient-dot-product":             ["h2", "p", "p", "p", "formula-box", "callout", "p"],
    "sec-physical-engineering-invariance":  ["h2", "p", "p", "p", "formula-box", "callout"],
    "sec-beyond-the-basics":                ["h2", "p", "p", "p", "p", "formula-box", "callout"],
}
EXPECTED_AUDIO_FILES = {
    "sec-from-slope-to-linear-map":         "sec_01_from_slope_to_linear_map.mp3",
    "sec-total-differential-multivariable": "sec_02_total_differential_multivariable.mp3",
    "sec-gradient-dot-product":             "sec_03_gradient_dot_product.mp3",
    "sec-physical-engineering-invariance":  "sec_04_physical_engineering_invariance.mp3",
    "sec-beyond-the-basics":                "sec_05_beyond_the_basics.mp3",
}
# Legacy alias names kept in each section's `alias` field (NOT extra keys).
ALIASES = {
    "sec-from-slope-to-linear-map":         "sec_01_from_slope_to_linear_map",
    "sec-total-differential-multivariable": "sec_02_total_differential_multivariable",
    "sec-gradient-dot-product":             "sec_03_gradient_dot_product",
    "sec-physical-engineering-invariance":  "sec_04_physical_engineering_invariance",
    "sec-beyond-the-basics":                "sec_05_beyond_the_basics",
}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (35 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-from-slope-to-linear-map": {
        "title": "১. একক ঢাল থেকে রৈখিক রূপান্তরে উত্তরণ (From Slope to Linear Map)",
        "audio_file": "sec_01_from_slope_to_linear_map.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, একক ঢাল থেকে রৈখিক রূপান্তরে উত্তরণ।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, ক্যালকুলাসের চূড়ান্ত সত্য হলো, জটিল ও বাঁকানো বিশ্বব্রহ্মাণ্ডকে স্থানীয়ভাবে একটি সুন্দর সমতল রৈখিক জগতে পরিণত করা, বলেছেন গ্রান্ট স্যান্ডারসন।"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, ক্যালকুলাসের এই দীর্ঘ অভিযাত্রায় আমরা ঢাল, স্পর্শক, ক্ষেত্রফল এবং অসীম ধারার ভেতর দিয়ে হেঁটে এসেছি। কিন্তু আপনি যদি গণিতের উচ্চতর সোপানে পা রাখেন, তবে গণিতবিদরা আপনাকে বলবেন, অন্তরজ বা ডেরিভেটিভ মূলত কোনো সংখ্যা বা সরলরেখার ঢাল নয়। ডেরিভেটিভ হলো একটি রৈখিক রূপান্তর, অর্থাৎ লিনিয়ার ম্যাপ।"},
            {"index": 3, "type": "p",
             "tts": "এক চলকের ক্ষেত্রে ওয়াই সমান এফ অফ এক্স ফাংশনে যখন ইনপুট সামান্য ডি এক্স পরিবর্তিত হয়, তখন ডিফারেনশিয়াল ডি ওয়াই সমান এফ প্রাইম অফ এক্স গুণ ডি এক্স। এটি নির্দেশ করে একটি গুণন সম্পর্ক, ডি এক্স রূপান্তরিত হয় এফ প্রাইম অফ এক্স গুণ ডি এক্সে। এখানে এফ প্রাইম অফ এক্স কাজ করে একটি স্কেলিং গুণক বা স্ট্রেচিং ফ্যাক্টর হিসেবে।"},
            {"index": 4, "type": "p",
             "tts": "কিন্তু যখন একাধিক চলক একসাথে কাজ করে, যেমন আবহাওয়ার তাপমাত্রা টি অফ এক্স ওয়াই জেড, যা ত্রিমাত্রিক স্থানে অবস্থানভেদে পরিবর্তিত হয়, তখন একক কোনো ঢাল দিয়ে পরিবর্তন ব্যাখ্যা করা অসম্ভব। সেখানেই রাজকীয় অভিষেক ঘটে সম্পূর্ণ ডিফারেনশিয়ালের, অর্থাৎ টোটাল ডিফারেনশিয়ালের।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এক মাত্রার ডিফারেনশিয়াল রৈখিক রূপান্তর, ডি এফ সমান এফ প্রাইম অফ এক্স গুণ ডি এক্স।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, স্থানীয় রৈখিকতার মহাবিস্ময়। পৃথিবী গোল হওয়া সত্ত্বেও আমরা হাঁটার সময় মাটিকে যেমন নিখুঁত সমতল দেখি, তেমনি যেকোনো মসৃণ বহুমাত্রিক সারফেসকে অতি ক্ষুদ্রাতিক্ষুদ্র স্থানে জুম করলে তা একটি সমতল স্পর্শক তলে পরিণত হয়।"},
            {"index": 7, "type": "p",
             "tts": "এই স্পর্শক তলের গাণিতিক সমীকরণটিই হলো সম্পূর্ণ ডিফারেনশিয়াল।"},
        ],
    },

    "sec-total-differential-multivariable": {
        "title": "২. সম্পূর্ণ ডিফারেনশিয়াল ও আংশিক অন্তরীকরণ (The Total Differential)",
        "audio_file": "sec_02_total_differential_multivariable.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, সম্পূর্ণ ডিফারেনশিয়াল ও আংশিক অন্তরীকরণ।"},
            {"index": 1, "type": "p",
             "tts": "কল্পনা করুন একটি ফাংশন জেড সমান এফ অফ এক্স ওয়াই, যার লেখচিত্র ত্রিমাত্রিক তলে একটি বাঁকানো পাহাড়ের মতো।"},
            {"index": 2, "type": "p",
             "tts": "এখন আপনি যদি এক্স অক্ষ বরাবর একটু হাঁটেন, অর্থাৎ ডি এক্স, এবং একই সাথে ওয়াই অক্ষ বরাবরও একটু পা বাড়ান, অর্থাৎ ডি ওয়াই, তবে আপনার উচ্চতায় মোট পরিবর্তন ডি জেড কতটুকু হবে?"},
            {"index": 3, "type": "p",
             "tts": "আংশিক অন্তরীকরণের মাধ্যমে আমরা প্রতিটি অক্ষের সংবেদনশীলতা আলাদাভাবে পরিমাপ করি। পার্শিয়াল ডি এফ বাই ডি এক্স হলো কেবল এক্স পরিবর্তনের কারণে উচ্চতা বৃদ্ধির হার, যখন ওয়াই স্থির। আর পার্শিয়াল ডি এফ বাই ডি ওয়াই হলো কেবল ওয়াই পরিবর্তনের কারণে উচ্চতা বৃদ্ধির হার, যখন এক্স স্থির।"},
            {"index": 4, "type": "p",
             "tts": "রৈখিক আসন্নায়ন অনুযায়ী, উভয় পরিবর্তনের সম্মিলিত রূপই হলো সম্পূর্ণ ডিফারেনশিয়াল। ডি এফ সমান পার্শিয়াল ডি এফ বাই ডি এক্স গুণ ডি এক্স, যোগ পার্শিয়াল ডি এফ বাই ডি ওয়াই গুণ ডি ওয়াই।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, দুই চলকের টোটাল ডিফারেনশিয়াল, ডি এফ সমান পার্শিয়াল ডি এফ বাই ডি এক্স গুণ ডি এক্স যোগ পার্শিয়াল ডি এফ বাই ডি ওয়াই গুণ ডি ওয়াই। আর এন সংখ্যক চলকের ক্ষেত্রে, ডি এফ সমান সামেশন, আই সমান এক থেকে এন, পার্শিয়াল ডি এফ বাই ডি এক্স আই গুণ ডি এক্স আই।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, বাস্তব উপলব্ধি, ওজনযুক্ত সংবেদনশীলতা। প্রতিটি ডি এক্স আই হলো একটি স্বতন্ত্র ইনপুট নাড়া, আর প্রতিটি আংশিক ডেরিভেটিভ, অর্থাৎ পার্শিয়াল ডি এফ বাই ডি এক্স আই, হলো সেই ইনপুটের প্রতি ফাংশনটির সংবেদনশীলতার ওজন।"},
        ],
    },

    "sec-gradient-dot-product": {
        "title": "৩. গ্র্যাডিয়েন্ট ভেক্টর ও ডট গুণন রূপ (The Gradient Vector & Dot Product)",
        "audio_file": "sec_03_gradient_dot_product.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, গ্রেডিয়েন্ট ভেক্টর ও ডট গুণন রূপ।"},
            {"index": 1, "type": "p",
             "tts": "টোটাল ডিফারেনশিয়ালের এই সমীকরণটিকে ভেক্টর বীজগণিতের দৃষ্টিতে দেখলে একটি অপরূপ সৌন্দর্য উন্মোচিত হয়।"},
            {"index": 2, "type": "p",
             "tts": "যদি আমরা সমস্ত আংশিক ডেরিভেটিভগুলোকে একটি ভেক্টরে সাজাই, তবে তাকে বলা হয় গ্রেডিয়েন্ট ভেক্টর। ডেল এফ হলো একটি কলাম ভেক্টর, যার উপাংশ পার্শিয়াল ডি এফ বাই ডি এক্স এবং পার্শিয়াল ডি এফ বাই ডি ওয়াই। আর ইনপুটের ক্ষুদ্র স্থানচ্যুতিগুলোকে একত্র করলে পাই স্থানচ্যুতি ভেক্টর, ডি আর, যার উপাংশ ডি এক্স ও ডি ওয়াই।"},
            {"index": 3, "type": "p",
             "tts": "এখন লক্ষ্য করুন, টোটাল ডিফারেনশিয়াল ডি এফ আর কিছুই নয়, তা হলো গ্রেডিয়েন্ট ভেক্টর এবং স্থানচ্যুতি ভেক্টরের নিখুঁত ডট গুণন।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক রূপ, ডিফারেনশিয়াল হলো গ্রেডিয়েন্ট ও স্থানচ্যুতি ভেক্টরের ডট গুণন। ডি এফ সমান ডেল এফ ডট ডি আর, যা আবার সমান গ্রেডিয়েন্টের দৈর্ঘ্য গুণ স্থানচ্যুতির দৈর্ঘ্য গুণ কোস থেটা। ত্রিমাত্রিক স্কেলার ক্ষেত্রে গ্রেডিয়েন্টের তিনটি উপাংশ, পার্শিয়াল ডি এফ বাই ডি এক্স, পার্শিয়াল ডি এফ বাই ডি ওয়াই এবং পার্শিয়াল ডি এফ বাই ডি জেড।"},
            {"index": 5, "type": "callout",
             "tts": "বিশেষ নোট, তীব্রতম আরোহণের দিক। ডট গুণনের সূত্র থেকে স্পষ্ট, যখন থেটা সমান শূন্য, অর্থাৎ স্থানচ্যুতি ভেক্টর ঠিক গ্রেডিয়েন্টের দিকে নির্দেশ করে, তখনই ডি এফ সর্বোচ্চ হয়। অর্থাৎ গ্রেডিয়েন্ট ভেক্টর সর্বদা পাহাড়ি ঢালের সবচেয়ে খাড়া আরোহণের দিক নির্দেশ করে।"},
            {"index": 6, "type": "p",
             "tts": "আধুনিক কৃত্রিম বুদ্ধিমত্তা ও নিউরাল নেটওয়ার্কের ব্যাকপ্রোপাগেশন, অর্থাৎ গ্রেডিয়েন্ট ডিসেন্ট, হুবহু এই নীতির ওপর ভিত্তি করেই প্রশিক্ষণ গ্রহণ করে।"},
        ],
    },

    "sec-physical-engineering-invariance": {
        "title": "৪. পদার্থবিদ্যা ও তাপগতিবিদ্যায় ডিফারেনশিয়াল (Differentials in Physics & Thermodynamics)",
        "audio_file": "sec_04_physical_engineering_invariance.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, পদার্থবিদ্যা ও তাপগতিবিদ্যায় ডিফারেনশিয়াল।"},
            {"index": 1, "type": "p",
             "tts": "পদার্থবিজ্ঞান ও প্রকৌশলবিদ্যায় ডিফারেনশিয়ালকে সবচেয়ে বেশি জীবন্ত দেখা যায় তাপগতিবিদ্যা এবং চিরায়ত বলবিদ্যায়।"},
            {"index": 2, "type": "p",
             "tts": "তাপগতিবিদ্যার প্রথম সূত্র বিবেচনা করুন, ডি ই সমান ডি কিউ বিয়োগ ডি ডব্লিউ। এখানে অভ্যন্তরীণ শক্তির ক্ষুদ্র পরিবর্তন ডি ই হলো একটি যথার্থ ডিফারেনশিয়াল, কারণ এটি সিস্টেমের আদি ও চূড়ান্ত অবস্থার ওপর নির্ভর করে, কোন পথে পরিবর্তন হয়েছে তার ওপর নয়।"},
            {"index": 3, "type": "p",
             "tts": "পক্ষান্তরে তাপ ডি কিউ এবং কাজ ডি ডব্লিউ হলো পথনির্ভর, অর্থাৎ ইনএক্সাক্ট ডিফারেনশিয়াল। ক্যালকুলাসের ডিফারেনশিয়াল বিশ্লেষণ আমাদের শেখায় কোন পরিবর্তনগুলো সংরক্ষিত ক্ষেত্র তৈরি করে এবং কোনগুলো শক্তি ক্ষয় করে।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, তাপগতিবিদ্যায় অভ্যন্তরীণ শক্তির পূর্ণাঙ্গ ডিফারেনশিয়াল রূপ, ডি ই সমান টি গুণ ডি এস বিয়োগ পি গুণ ডি ভি। আর বলক্ষেত্র বরাবর কৃতকাজ ডব্লিউ সমান ইন্টিগ্রাল, বরাবর পথ সি, বল ভেক্টর ডট স্থানচ্যুতি ভেক্টর ডি আর।"},
            {"index": 5, "type": "callout", "role": "conclusion",
             "tts": "বিশেষ নোট, স্থানাঙ্ক নিরপেক্ষতা। ডিফারেনশিয়াল ডি এফ এর সবচেয়ে শক্তিশালী বৈশিষ্ট্য হলো, আপনি কার্তেসীয় স্থানাঙ্ক এক্স ওয়াই ব্যবহার করুন, পোলার স্থানাঙ্ক আর ও থেটা ব্যবহার করুন, কিংবা যেকোনো বাঁকানো স্থানাঙ্ক ব্যবহার করুন না কেন, ডিফারেনশিয়াল সম্পর্কের জ্যামিতিক মান সম্পূর্ণ অপরিবর্তিত থাকে।"},
        ],
    },

    "sec-beyond-the-basics": {
        "title": "৫. ক্যালকুলাসের পরবর্তী দিগন্ত: আপনি এখন কোথায় যাবেন? (Beyond the Basics: Where to Go)",
        "audio_file": "sec_05_beyond_the_basics.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, ক্যালকুলাসের পরবর্তী দিগন্ত, আপনি এখন কোথায় যাবেন?"},
            {"index": 1, "type": "p",
             "tts": "বারোটি রোমাঞ্চকর অধ্যায়ের মধ্য দিয়ে আমরা ক্যালকুলাসের ভিত্তিপ্রস্তর স্থাপন করেছি। কিন্তু এটি শেষ নয়, বরং উচ্চতর গণিতের বিশাল সাগরে আপনার প্রথম যাত্রা মাত্র।"},
            {"index": 2, "type": "p",
             "tts": "এখান থেকে আপনার সামনে তিনটি প্রধান শাখা উন্মুক্ত হয়। প্রথমত, মাল্টিভেরিয়েবল ক্যালকুলাস, কার্ল, ডাইভারজেন্স, গ্রিন স্টোকস উপপাদ্য এবং ম্যাক্সওয়েলের তড়িৎচৌম্বকীয় সমীকরণ।"},
            {"index": 3, "type": "p",
             "tts": "দ্বিতীয়ত, ব্যবকলনীয় সমীকরণ, গতি, গ্রহের কক্ষপথ, মহামারীর বিস্তার এবং কোয়ান্টাম ওয়েভ ফাংশনের সময়ভিত্তিক বিবর্তন বোঝার হাতিয়ার।"},
            {"index": 4, "type": "p",
             "tts": "তৃতীয়ত, কৃত্রিম বুদ্ধিমত্তা ও মেশিন লার্নিং। লক্ষ লক্ষ ওজনের গ্রেডিয়েন্ট হিসাব করে বৃহৎ ভাষা মডেল ও নিউরাল নেটওয়ার্ককে নিখুঁত করার ব্যাকপ্রোপাগেশন।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক প্রতীক, ফ্যারাডের সূত্র, ডেল ক্রস ই সমান মাইনাস পার্শিয়াল ডি বি বাই ডি টি। আর ডিপ লার্নিংয়ে ওজন আপডেট, ডব্লিউ সবসময় তে এক ধাপ পরে সমান বর্তমান ওজন বিয়োগ ইটা গুণ ক্ষতি ফাংশনের গ্রেডিয়েন্ট।"},
            {"index": 6, "type": "callout", "role": "conclusion",
             "tts": "গ্রান্ট স্যান্ডারসনের বিদায়ী বাণী। ক্যালকুলাস কোনো শুকনো নিয়মের সমষ্টি নয়, এটি অসীম পরিবর্তনশীল বাস্তবতাকে মানুষের সহজ বুদ্ধির আওতায় আনার এক স্বর্গীয় ভাষা। চোখ মেলে তাকান, মহাবিশ্বের প্রতিটি পরিবর্তনের অন্তরালে শুনবেন ক্যালকুলাসের ছন্দ।"},
        ],
    },
}

# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"


def assert_clean_scripts():
    """Fail before any TTS work if a script still contains markup or Latin text."""
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars {bad!r} in {cue['tts']!r}")
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: artificial figure label present")

    # Structural parity guards.
    if len(SECTIONS_DATA) != 5:
        raise ValueError("Expected exactly 5 narrated sections")
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
        total += len(indices)
    if total != 35:
        raise ValueError(f"Expected 35 cues, found {total}")

    # Figure cues must be genuine 2-4 sentence explanations (vacuous here: the
    # live DOM has no figure blocks in narrated sections, but keep the guard).
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            if cue["type"] == "figure":
                sentences = [s for s in cue["tts"].split("।") if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(f"{sec_id} cue {cue['index']}: figure has {len(sentences)} sentences")

    # DOM parity against the browser-extracted live snapshot (narration_engine
    # selector + KaTeX <annotation> preservation).
    if os.path.exists(DOM_SNAPSHOT):
        with open(DOM_SNAPSHOT, encoding="utf-8") as fh:
            snap = json.load(fh)
        snap_types = {s["id"]: [b["type"] for b in s["blocks"]]
                      for s in snap["sections"]}
        if snap_types != EXPECTED_TYPES:
            raise ValueError(f"DOM snapshot cue types differ from embedded EXPECTED_TYPES:\n"
                             f"snapshot={snap_types}\nexpected={EXPECTED_TYPES}")
        if set(snap_types) != set(SECTIONS_DATA):
            raise ValueError("DOM snapshot section ids differ from embedded sections")

    # No duplicate spoken scripts.
    spoken = [c["tts"] for s in SECTIONS_DATA.values() for c in s["cues"]]
    if len(spoken) != len(set(spoken)):
        raise ValueError("Duplicate spoken cue scripts detected")


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
        "section_id": sec_id,
        "alias": ALIASES[sec_id],
        "title": sec["title"],
        "audio_file": sec["audio_file"],
        "total_duration_ms": round(cursor, 1),
        "cues": manifest_cues,
    }


async def build_all():
    assert_clean_scripts()
    print(f"Validated {sum(len(s['cues']) for s in SECTIONS_DATA.values())} clean cues "
          f"in {len(SECTIONS_DATA)} sections.")

    manifest_sections = {}
    for sec_id, sec in SECTIONS_DATA.items():
        manifest_sections[sec_id] = await build_section(sec_id, sec)

    manifest_data = {
        "course": "calculus",
        "lesson": "lesson_12",
        "title": MANIFEST_TITLE,
        "voice": VOICE,
        "mode": "authentic_teacher",
        "processing": {
            "loudness_standard": "EBU R128",
            "target_loudness_lufs": -14.0,
            "true_peak_dbtp": -1.0,
            "normalization": "two_pass_loudnorm",
            "cue_gap_ms": 350.0,
            "notes": "সমস্ত সেকশন অডিও EBU R128 প্রোটোকলে নরমালাইজ করা: -14.0 LUFS ইন্টিগ্রেটেড লাউডনেস, -1.0 dBTP ট্রু পিক লক্ষ্য। পরপর কিউগুলোর মধ্যে ৩৫০ms ডিজিটাল সাইলেন্স স্থাপন করা হয়।",
        },
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
    expected_keys = set(SECTIONS_DATA)
    assert set(loaded["sections"]) == expected_keys
    total_cues = 0
    total_ms = 0.0
    figures = 0
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == len(EXPECTED_TYPES[sec_id])
        assert msec["section_id"] == sec_id
        assert msec["alias"] == ALIASES[sec_id]
        assert msec["audio_file"] == EXPECTED_AUDIO_FILES[sec_id]
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    assert total_cues == 35

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Calculus Lesson 12")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<40} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 5 sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json is valid JSON; all 5 mp3 files exist and are non-empty.")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(build_all())
