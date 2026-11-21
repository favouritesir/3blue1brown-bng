# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Group Theory Lesson 02
("Euler's formula through group theory", Bengali) to the gold standard.

Deterministic, re-runnable, self-contained:
  * 46 cues in 8 narrated sections with EXACTLY the same section IDs, audio_file
    names, cue types and cue order as the live DOM / placeholder manifest.
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Figure cues are genuine 2-4 sentence natural explanations - never the
    artificial label "চিত্র প্রদর্শনী".
  * Every script is clean spoken Bengali with phonetic safeguards:
    Euler -> অয়লার, complex -> কমপ্লেক্স, i -> আই, pi -> পাই, exp -> এক্সপ,
    homomorphism -> হোমোমরফিজম, dihedral -> ডাইহেড্রাল, group -> গ্রুপ,
    symmetry -> সমমিতি, radian -> রেডিয়ান, x -> এক্স, y -> ওয়াই, etc.
    No TeX, LaTeX, backslashes, $, braces, brackets, em/en-dashes, raw hyphens
    or Latin letters.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, chapter-quote -3%, p +2%, figure -4%, callout +0%,
      formula-box -8%, conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with the
    exact-ms timings and the canonical DOM section keys.
  * Backs up the placeholder manifest into _backup_before_expressive_build/.
  * Validates non-zero durations, zero overlap, valid JSON and non-empty mp3s.

Usage:  python governance/build_expressive_teacher_audio_gt02.py
"""

import os
import re
import json
import shutil
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
                         "group_theory", "lesson_02")
MANIFEST_TITLE = "অয়লারের সূত্র ও গ্রুপ তত্ত্ব"

# Prosody keyed by cue type: (rate, pitch, volume)
PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
    "h3":            ("-3%", "+0Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),
    "p":             ("+2%", "+0Hz", "+0%"),   # natural teacher pace
    "figure":        ("-4%", "+0Hz", "+0%"),   # slower, considerate explanation
    "callout":       ("+0%", "+0Hz", "+0%"),
    "formula-box":   ("-8%", "+0Hz", "+0%"),   # slow and deliberate
    "code-showcase": ("-3%", "+0Hz", "+0%"),
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")     # calm concluding prose

# Parity guards: exact cue-type sequence expected for each narrated section.
EXPECTED_TYPES = {
    "sec-intro":          ["h2", "p", "figure"],
    "sec-square":         ["h2", "p", "figure", "p", "callout"],
    "sec-circle":         ["h2", "p", "figure", "p", "figure"],
    "sec-composing":      ["h2", "p", "figure", "p", "figure"],
    "sec-additive":       ["h2", "p", "figure", "p", "figure", "p", "figure"],
    "sec-multiplicative": ["h2", "p", "figure", "p", "p", "figure", "p"],
    "sec-exponents":      ["h2", "p", "p", "figure", "callout", "formula-box"],
    "sec-conclusion":     ["h2", "p", "figure", "p", "figure", "p",
                           "formula-box", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-intro":          "sec_sec-intro.mp3",
    "sec-square":         "sec_sec-square.mp3",
    "sec-circle":         "sec_sec-circle.mp3",
    "sec-composing":      "sec_sec-composing.mp3",
    "sec-additive":       "sec_sec-additive.mp3",
    "sec-multiplicative": "sec_sec-multiplicative.mp3",
    "sec-exponents":      "sec_sec-exponents.mp3",
    "sec-conclusion":     "sec_sec-conclusion.mp3",
}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (46 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-intro": {
        "title": "১. অয়লারের সূত্রের পরিচিতি",
        "audio_file": "sec_sec-intro.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, অয়লারের সূত্রের পরিচিতি।"},
            {"index": 1, "type": "p",
             "tts": "ই পাওয়ার পাই আই সমান বিয়োগ এক, গণিতের সবচেয়ে পরিচিত সমীকরণগুলোর একটি। কিন্তু এটি সত্য কেন? এই পাঠে আমরা গ্রুপ তত্ত্বের কয়েকটি ধারণা ব্যবহার করে এর পেছনের অন্তর্দৃষ্টি খোঁজব। এটি কোনো আনুষ্ঠানিক প্রমাণ নয়, বরং সংখ্যা ও বীজগণিত সম্পর্কে চিন্তার একটি নতুন ধরন।"},
            {"index": 2, "type": "figure",
             "tts": "এই ছবিতে ই পাওয়ার পাই আই সমান বিয়োগ এক সমীকরণটি গ্রুপ তত্ত্বের দৃষ্টিতে দেখানো হয়েছে। সংখ্যা ও জ্যামিতির এই মিল আসলে কীভাবে ঘটে, তা নিয়েই আমাদের আজকের যাত্রা। ছবিটি মনে রেখে পড়লে শেষের দিকে এর অর্থ আরও স্পষ্ট হবে।"},
        ],
    },

    "sec-square": {
        "title": "২. বর্গক্ষেত্রের গ্রুপ",
        "audio_file": "sec_sec-square.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, বর্গক্ষেত্রের গ্রুপ।"},
            {"index": 1, "type": "p",
             "tts": "গ্রুপ তত্ত্ব সমমিতির প্রকৃতি নিয়ে পড়াশোনা করে। বর্গক্ষেত্রকে ৯০ ডিগ্রি ঘোরালে বা উল্লম্ব রেখা বরাবর উল্টালে সেটি আগের মতোই দেখায়।"},
            {"index": 2, "type": "figure",
             "tts": "এই ছবিতে বর্গের আটটি সমমিতি দেখানো হয়েছে, যার মধ্যে কিছু না করা, তিনটি ঘূর্ণন ও চারটি উল্টানো রয়েছে। প্রতিটি কাজের পর বর্গটি আগের মতোই দেখায়। এই আটটি কাজই মিলে গড়ে তোলে একটি ছোট কিন্তু সম্পূর্ণ গ্রুপ।"},
            {"index": 3, "type": "p",
             "tts": "এই ধরনের প্রতিটি কাজ একটি সমমিতি। সবগুলো মিলে গড়ে তোলে সমমিতির গ্রুপ, এখানে আটটি কাজ আছে, কিছু না করা, তিনটি ঘূর্ণন এবং চারটি উল্টানো। এর নাম চতুর্থ মাত্রার ডাইহেড্রাল গ্রুপ বা ডি চার।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, মনে রাখুন, সমমিতি শনাক্ত করতে বর্গের ভেতরে একটিমাত্র ছোট পাই চিহ্ন রাখলে কোন কাজটি হয়েছে তা ট্র্যাক করা সহজ হয়। কোণ বা বাহু সবই একই রকম দেখা যায়, কিন্তু সেই ছোট চিহ্নটি ঘুরে বা উল্টে কোথায় যায় তা দেখলেই কাজটি চেনা যায়।"},
        ],
    },

    "sec-circle": {
        "title": "৩. বৃত্তের গ্রুপ",
        "audio_file": "sec_sec-circle.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, বৃত্তের গ্রুপ।"},
            {"index": 1, "type": "p",
             "tts": "বর্গ একটি সসীম গ্রুপ, মাত্র আটটি কাজ। কিন্তু অনেক গ্রুপে অসংখ্য কাজ থাকে। যেকোনো কোণে ঘোরানোর কথা ভাবুন, শূন্য থেকে দুই পাই রেডিয়ানের অবিচ্ছিন্ন রেখায় প্রতিটি কাজ অবস্থান করে।"},
            {"index": 2, "type": "figure",
             "tts": "এই ছবিতে বৃত্তের ঘূর্ণন গ্রুপ দেখানো হয়েছে, যা শূন্য থেকে দুই পাই পর্যন্ত অবিচ্ছিন্ন। বর্গের মতো এখানে কয়েকটি আলাদা কাজ নেই, বরং অসংখ্য কাজ একটানা সাজানো। প্রতিটি কোণই এই গ্রুপের একটি স্বতন্ত্র উপাদান।"},
            {"index": 3, "type": "p",
             "tts": "এই গ্রুপের সুবিধা হলো প্রতিটি কাজকে বৃত্তের একটিমাত্র বিন্দুর সাথে যুক্ত করা যায়। যেকোনো বিন্দু বেছে নিন, প্রতিটি ঘূর্ণন সেই বিন্দুকে একটি নির্দিষ্ট জায়গায় নিয়ে যায়, আর সেই অবস্থান থেকে কাজটি সম্পূর্ণরূপে শনাক্ত করা যায়।"},
            {"index": 4, "type": "figure",
             "tts": "এই ছবিতে একটি চিহ্নিত বিন্দু ঘূর্ণনকে শনাক্ত করতে সাহায্য করছে। বিন্দুটি কোথায় গেল, তা দেখেই আমরা কোণটি এবং সংশ্লিষ্ট কাজটি চেনে নিই। এই পদ্ধতিটি পরে জটিল সংখ্যার গুণ গ্রুপেও কাজে আসবে।"},
        ],
    },

    "sec-composing": {
        "title": "৪. প্রতিসাম্যের সংযোজন",
        "audio_file": "sec_sec-composing.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, সমমিতির সংযোজন।"},
            {"index": 1, "type": "p",
             "tts": "গ্রুপ তত্ত্বের আসল হৃদয় হলো এই কাজগুলো একের পর এক প্রয়োগ করলে কী হয়। বর্গে ৯০ ডিগ্রি ঘুরে উল্লম্ব অক্ষ বরাবর উল্টালে ফলাফলকে কর্ণ বরাবর উল্টানোর মতোই দেখায়।"},
            {"index": 2, "type": "figure",
             "tts": "এই ছবিতে একটি ৯০ ডিগ্রি ঘূর্ণনের পর উল্লম্ব অক্ষ বরাবর উল্টানো দেখানো হয়েছে। এর ফলাফল ঠিক কর্ণ বরাবর উল্টানোর মতোই দেখা যাচ্ছে। অর্থাৎ দুটি কাজের সংযোজন আবার গ্রুপেরই তৃতীয় একটি কাজ।"},
            {"index": 3, "type": "p",
             "tts": "বৃত্তে ২৭০ ডিগ্রি ঘুরে ১২০ ডিগ্রি ঘোরালে মোট ৩০ ডিগ্রি ঘোরানোর সমান হয়। এক কথায়, যেকোনো গ্রুপেই দুটি কাজ নিয়ে তৃতীয় একটি কাজ পাওয়া যায়, একে যোগ বা গুণ, যেকোনোভাবে ভাবতে পারেন।"},
            {"index": 4, "type": "figure",
             "tts": "এই ছবিতে বৃত্তে দুই ঘূর্ণনের সংযোজন দেখানো হয়েছে। প্রথম কাজের শেষ অবস্থান থেকে দ্বিতীয় কাজ শুরু হয় এবং শেষে একটিমাত্র ঘূর্ণনের মতো ফল পাওয়া যায়। এই সংযোজন নিয়মই গ্রুপের গুণ বা যোগের ভিত্তি।"},
        ],
    },

    "sec-additive": {
        "title": "৫. সংখ্যার যোগ গ্রুপ",
        "audio_file": "sec_sec-additive.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, সংখ্যার যোগ গ্রুপ।"},
            {"index": 1, "type": "p",
             "tts": "গ্রুপ বেশ সাধারণ ধারণা, সংখ্যাকেও গ্রুপ হিসেবে দেখা যায়, আর তা দুইভাবে, যোগের মাধ্যমে ও গুণের মাধ্যমে। প্রথমে সংখ্যারেখা বাঁয়ে ডানে সরানোর কথা ভাবুন, এই সব সরণ নিয়ে একটি গ্রুপ গড়ে ওঠে।"},
            {"index": 2, "type": "figure",
             "tts": "এই ছবিতে সংখ্যারেখার সব সরণ নিয়ে গড়ে ওঠা গ্রুপটি দেখা যাচ্ছে। বাঁয়ে বা ডানে যেকোনো দূরত্বে সরানোই এই গ্রুপের একটি কাজ। সরণগুলোর এই সংগ্রহও ঠিক বৃত্তের ঘূর্ণনের মতোই একটি গ্রুপের নিয়ম মানে।"},
            {"index": 3, "type": "p",
             "tts": "সরণগুলোকেও বিন্দুর সাথে যুক্ত করা যায়, শূন্যে থাকা বিন্দু কোথায় যায় তা দেখলেই কাজটি শনাক্ত হয়। তিন মানে তিন একক ডানে সরণ, বিয়োগ দুই মানে দুই একক বাঁয়ে, আর শূন্য মানে কিছু না করা। একের পর এক সরণ মানে দূরত্বগুলোর যোগ, তাই এটি বাস্তব সংখ্যার যোগ গ্রুপ।"},
            {"index": 4, "type": "figure",
             "tts": "এই ছবিতে বাস্তব সংখ্যার যোগ গ্রুপ, অর্থাৎ সরণের যোগ দেখানো হয়েছে। দুটি সরণ পর পর প্রয়োগ করলে মোট সরণ তাদের দূরত্বের সমান হয়। এই সরল নিয়মেই পুরো গ্রুপটি পরিচালিত হয়।"},
            {"index": 5, "type": "p",
             "tts": "এই ধারণা কমপ্লেক্স তলে বাড়ালে আই, দুই আই, তিন আই ইত্যাদি উল্লম্ব সরণ, আর তিন যোগ দুই আই কর্ণ বরাবর সরণ, যা আগে তিন ডানে, পরে দুই উপরে সরণের সমান।"},
            {"index": 6, "type": "figure",
             "tts": "এই ছবিতে কমপ্লেক্স তলে সরণের সংযোজন ও কমপ্লেক্স সংখ্যার যোগ একই কাজ দেখাচ্ছে। অনুভূমিক ও উল্লম্ব এই দুই সরণ একসাথে কর্ণ বরাবর একটি সরণ তৈরি করে। এইভাবেই জ্যামিতি ও বীজগণিতের মধ্যে গভীর মিল প্রকাশ পায়।"},
        ],
    },

    "sec-multiplicative": {
        "title": "৬. গুণ গ্রুপ",
        "audio_file": "sec_sec-multiplicative.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "ষষ্ঠ পরিচ্ছেদ, গুণ গ্রুপ।"},
            {"index": 1, "type": "p",
             "tts": "সংখ্যার আরেকটি জীবন আছে, গুণ গ্রুপ হিসেবে। সংখ্যারেখাকে শূন্য স্থির রেখে টানা বা চাপা দেওয়ার সব কাজ নিয়ে একটি গ্রুপ তৈরি হয়। একে থাকা বিন্দু কোথায় যায় তা দেখে কাজটি চেনা যায়, তিনে নিয়ে যাওয়া মানে তিন গুণ প্রসার, আর আধাকে নিয়ে যাওয়া মানে আধা গুণ সংকোচন।"},
            {"index": 2, "type": "figure",
             "tts": "এই ছবিতে তিন গুণ প্রসার দেখানো হয়েছে, এক থেকে তিন পর্যন্ত। শূন্য বিন্দুটি স্থির থাকে, কিন্তু বাকি সব বিন্দু তিনগুণ দূরে চলে যায়। এই প্রসারও একটি গুণগত কাজ, যার নিজস্ব বিপরীত আছে।"},
            {"index": 3, "type": "p",
             "tts": "তিন গুণের পর দুই গুণ করলে ফল ছয় গুণ, অর্থাৎ কাজ সংযোজন মানেই গুণ। শূন্য দিয়ে গুণ করা এই গ্রুপে নেই, কারণ তার কোনো বিপরীত নেই।"},
            {"index": 4, "type": "p",
             "tts": "কমপ্লেক্স তলে এককে সরানোর অর্থ প্রসারণ ছাড়াও ঘোরানো। আই দিয়ে গুণ মানে ৯০ ডিগ্রি ঘোরানো, দুইবার প্রয়োগ করলে ১৮০ ডিগ্রি ঘুরে বিয়োগ এক পাই, অর্থাৎ আই গুণ আই সমান বিয়োগ এক।"},
            {"index": 5, "type": "figure",
             "tts": "এই ছবিতে আই দিয়ে গুণ মানে ৯০ ডিগ্রি ঘোরানো আর দুইবার প্রয়োগ মানে ১৮০ ডিগ্রি দেখানো হয়েছে। একক বৃত্তের ওপর বিন্দুটি ঘুরে ঠিক বিপরীত দিকে পৌঁছায়। এই ঘূর্ণনই পরে অয়লারের সূত্রের চাবিকাঠি হবে।"},
            {"index": 6, "type": "p",
             "tts": "সাধারণভাবে প্রতিটি কাজ কিছুটা প্রসারণ বা সংকোচন আর কিছুটা বিশুদ্ধ ঘোরানোর সমন্বয়। প্রসারণ ধনাত্মক বাস্তব রেখার বিন্দু দিয়ে আর ঘোরানো একক বৃত্তের বিন্দু দিয়ে চিহ্নিত হয়।"},
        ],
    },

    "sec-exponents": {
        "title": "৭. ঘাত আসলে কী?",
        "audio_file": "sec_sec-exponents.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "সপ্তম পরিচ্ছেদ, ঘাত আসলে কী?"},
            {"index": 1, "type": "p",
             "tts": "টু পাওয়ার তিন মানে টু গুণ টু গুণ টু, অর্থাৎ পুনরাবৃত্ত গুণ। তাই টু পাওয়ার তিন যোগ পাঁচ সমান টু পাওয়ার তিন গুণ টু পাওয়ার পাঁচ। কিন্তু টু পাওয়ার আধা, টু পাওয়ার বিয়োগ এক বা টু পাওয়ার আই কী? পুনরাবৃত্ত গুণ দিয়ে এর অর্থ বোঝা যায় না। তাই আমরা সংজ্ঞা এমনভাবে বাড়াই যেন টু পাওয়ার এক্স যোগ ওয়াই সমান টু পাওয়ার এক্স গুণ টু পাওয়ার ওয়াই বৈশিষ্ট্যটি টিকে থাকে।"},
            {"index": 2, "type": "p",
             "tts": "গ্রুপ তত্ত্বের দৃষ্টিতে এই বৈশিষ্ট্য বলে, ইনপুটের যোগের সাথে আউটপুটের গুণ মিলে যায়। তাই ইনপুটকে যোগ গ্রুপের সরণ কাজ এবং আউটপুটকে গুণ গ্রুপের প্রসার কাজ হিসেবে ভাবা যায়।"},
            {"index": 3, "type": "figure",
             "tts": "এই ছবিতে যোগ গ্রুপ থেকে গুণ গ্রুপে গঠন সংরক্ষণকারী মানচিত্র দেখানো হয়েছে। বাঁয়ের সরণ স্তর থেকে ডানের প্রসার স্তরে প্রতিটি কাজ ম্যাপ করা হয়। মানচিত্রটি যদি যোগকে গুণে রূপ দেয়, তবে গ্রুপের গঠন অক্ষত থাকে।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, হোমোমরফিজম দুই গ্রুপের মধ্যকার এমন মানচিত্র যা তাদের গঠন বা অ্যারিথমেটিক সংরক্ষণ করে, তাকে হোমোমরফিজম বলে। সূত্রের পেছনের এই গঠন সংরক্ষণই আসল কথা।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এক্সপ এক্স যোগ ওয়াই সমান এক্সপ এক্স গুণ এক্সপ ওয়াই। অর্থাৎ ইনপুট যোগ হলে আউটপুটগুলোর গুণ পাওয়া যায়, যা হোমোমরফিজমেরই আরেক রূপ।"},
        ],
    },

    "sec-conclusion": {
        "title": "৮. জটিল ঘাত ও উপসংহার",
        "audio_file": "sec_sec-conclusion.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "অষ্টম পরিচ্ছেদ, জটিল ঘাত ও উপসংহার।"},
            {"index": 1, "type": "p",
             "tts": "এখন কমপ্লেক্স তলে যোগ গ্রুপ থেকে গুণ গ্রুপে মানচিত্র আঁকা যাক। বাস্তব অংশ প্রসারণ বা সংকোচনে যায়, তাই উল্লম্ব কাল্পনিক অংশ বিশুদ্ধ ঘোরানোয় যাবে, এটা স্বাভাবিক অনুমান।"},
            {"index": 2, "type": "figure",
             "tts": "এই ছবিতে উল্লম্ব সরণ একক বৃত্তে ঘোরানোতে রূপান্তরিত হচ্ছে। সরণের পরিমাণ যত বাড়ে, ঘোরানোর কোণও তত বাড়ে। এই সরল অনুমানই আমাদের অয়লারের সূত্রের কাছে নিয়ে যায়।"},
            {"index": 3, "type": "p",
             "tts": "টু পাওয়ার এক্স এর ক্ষেত্রে আই, অর্থাৎ এক একক উল্লম্ব সরণ, ০ দশমিক ৬৯৩ রেডিয়ান ঘোরানোর সাথে মিলে। ফাইভ পাওয়ার এক্স এ ১ দশমিক ৬০৯ রেডিয়ান। কিন্তু ই পাওয়ার এক্স এর ক্ষেত্রে এক একক উল্লম্ব সরণ ঠিক এক রেডিয়ান ঘোরানোর সমান, আর এটিই ই কে বিশেষ করে তোলে।"},
            {"index": 4, "type": "figure",
             "tts": "এই ছবিতে ই পাওয়ার এক্স, অর্থাৎ এক একক উল্লম্ব সরণ সমান এক রেডিয়ান দেখানো হয়েছে। অন্য কোনো ভিত্তিতে এই মিল থাকে না, শুধু ই এর ক্ষেত্রেই ঘটে। এই কারণেই প্রাকৃতিক লগারিদমের ভিত্তি হিসেবে ই কে বেছে নেওয়া হয়।"},
            {"index": 5, "type": "p",
             "tts": "তাই দুই একক উল্লম্ব সরণ মানে দুই রেডিয়ান, তিন মানে তিন রেডিয়ান, আর পাই একক উল্লম্ব সরণ অর্থাৎ ইনপুট পাই আই মানে পাই রেডিয়ান, বৃত্তের অর্ধেক পথ, যেটি বিয়োগ এক এর গুণগত কাজ।"},
            {"index": 6, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ই পাওয়ার পাই আই সমান বিয়োগ এক। এক একক উল্লম্ব সরণ এক রেডিয়ান হওয়ায় পাই একক সরণ পাই রেডিয়ান, অর্ধবৃত্ত, আর সেটিই বিয়োগ এক দিকে নিয়ে যায়।"},
            {"index": 7, "type": "p", "role": "conclusion",
             "tts": "এই ছবিটি মনে আঁকুন, সমতল প্রথমে বেলনের মতো রোল হয়, তারপর সেটিকে শূন্যের চারপাশে চাপ দেওয়া হয়। গ্রুপ তত্ত্বের চোখ দিয়ে দেখলে ঘাতফলন কেবল এক ধরনের কাজকে অন্য ধরনের কাজে রূপ দেয়, সরণকে প্রসারণ ও ঘোরানোয়। এই রূপান্তরের মাধ্যমেই অয়লারের সূত্রের মতো এক অদ্ভুত সমীকরণের অর্থ স্পষ্ট হয়।"},
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
    if len(SECTIONS_DATA) != 8:
        raise ValueError("Expected exactly 8 narrated sections")
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
    if total != 46:
        raise ValueError(f"Expected 46 cues, found {total}")

    # Figure cues must be genuine 2-4 sentence explanations.
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            if cue["type"] == "figure":
                sentences = [s for s in cue["tts"].split("।") if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(f"{sec_id} cue {cue['index']}: figure has {len(sentences)} sentences")


def backup_placeholder_manifests():
    """Keep the pre-build placeholders before any manifest is overwritten."""
    backup = os.path.join(AUDIO_DIR, "_backup_before_expressive_build")
    os.makedirs(backup, exist_ok=True)
    for name in ("manifest.json", "manifest.js"):
        src = os.path.join(AUDIO_DIR, name)
        dst = os.path.join(backup, name)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
            print(f"  backed up {name} -> _backup_before_expressive_build/{name}")
        else:
            print(f"  backup present for {name}")


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
        "title": sec["title"],
        "audio_file": sec["audio_file"],
        "total_duration_ms": round(cursor, 1),
        "cues": manifest_cues,
    }


async def build_all():
    backup_placeholder_manifests()
    assert_clean_scripts()
    print(f"Validated {sum(len(s['cues']) for s in SECTIONS_DATA.values())} clean cues "
          f"in {len(SECTIONS_DATA)} sections.")

    manifest_sections = {}
    for sec_id, sec in SECTIONS_DATA.items():
        manifest_sections[sec_id] = await build_section(sec_id, sec)

    manifest_data = {
        "course": "group_theory",
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

    # Final integrity checks.
    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert set(loaded["sections"]) == set(SECTIONS_DATA)
    total_cues = 0
    total_ms = 0.0
    figures = 0
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == len(EXPECTED_TYPES[sec_id])
        assert [c["type"] for c in msec["cues"]] == EXPECTED_TYPES[sec_id]
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    assert total_cues == 46

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Group Theory Lesson 02")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<24} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTIONS_DATA)} sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json is valid JSON; all 8 mp3 files exist and are non-empty.")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(build_all())
