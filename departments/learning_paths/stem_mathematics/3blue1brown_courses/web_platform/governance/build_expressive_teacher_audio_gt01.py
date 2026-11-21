# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Group Theory Lesson 01
("Group theory, abstraction and the monster", Bengali) to the gold standard.

Deterministic, re-runnable, self-contained:
  * 40 cues in 5 narrated sections with EXACTLY the same section IDs, audio_file
    names, cue types and cue order as the live DOM / placeholder manifest.
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Figure cues are genuine 2-4 sentence natural explanations - never the
    artificial label "চিত্র প্রদর্শনী".
  * Every script is clean spoken Bengali with phonetic safeguards:
    group -> গ্রুপ, isomorphism -> আইসোমরফিজম, monster -> মনস্টার,
    symmetry -> সমমিতি, complex -> কমপ্লেক্স, permutation -> পারম্যুটেশন,
    homomorphism -> হোমোমরফিজম, i -> আই, pi -> পাই, exp -> এক্সপ, etc.
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

Usage:  python governance/build_expressive_teacher_audio_gt01.py
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
                         "group_theory", "lesson_01")
MANIFEST_TITLE = "গ্রুপ তত্ত্ব, বিমূর্ততা ও মনস্টার"

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
    "sec-intro":        ["h2", "p", "formula-box", "figure", "p"],
    "sec-definition":   ["h2", "p", "figure", "p", "figure", "callout",
                         "p", "figure", "p", "figure", "p", "p"],
    "sec-axioms":       ["h2", "p", "formula-box", "callout", "figure",
                         "p", "p", "figure", "p"],
    "sec-isomorphism":  ["h2", "p", "figure", "p", "callout", "figure"],
    "sec-monster":      ["h2", "p", "p", "figure", "p", "p",
                         "chapter-quote", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-intro":        "sec_sec-intro.mp3",
    "sec-definition":   "sec_sec-definition.mp3",
    "sec-axioms":       "sec_sec-axioms.mp3",
    "sec-isomorphism":  "sec_sec-isomorphism.mp3",
    "sec-monster":      "sec_sec-monster.mp3",
}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (40 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-intro": {
        "title": "১. আমার প্রিয় মেগা-সংখ্যা",
        "audio_file": "sec_sec-intro.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, আমার প্রিয় মেগা সংখ্যা।"},
            {"index": 1, "type": "p",
             "tts": "আমরা আজ যে বিশাল সংখ্যাটি নিয়ে কথা বলব, তা এক মিলিয়নের চেয়েও অনেক বড়, প্রায় আট গুণ দশের ঘাত তিপান্ন। প্রথমে মনে হতে পারে এটি ইচ্ছামাত্রিক কোনো বাছাই, কিন্তু এই সংখ্যার পেছনে লুকিয়ে আছে গণিতের এক গভীর ও অদ্ভুত সত্য।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, মনস্টার গ্রুপের আকার। এই সংখ্যাটি দুই এর ঘাত ছিয়াল্লিশ, গুণ তিনের ঘাত কুড়ি, গুণ পাঁচের ঘাত নয়, গুণ সাতের ঘাত ছয়, গুণ এগারোর ঘাত দুই, গুণ তেরোর ঘাত তিন, আর ১৭, ১৯, ২৩, ২৯, ৩১, ৪১, ৪৭, ৫৯ ও ৭১ এই মৌলিক সংখ্যাগুলোর গুণফল।"},
            {"index": 3, "type": "figure",
             "tts": "এই ছবিতে বৃহস্পতি গ্রহটি দেখা যাচ্ছে। আকর্ষণীয় ব্যাপার হলো, আমাদের এই বিশাল সংখ্যাটি আনুমানিক বৃহস্পতির মোট পরমাণুর সংখ্যার কাছাকাছি। একটিমাত্র গ্রহের পরমাণুর সংখ্যার সাথে একটি বিমূর্ত গাণিতিক গ্রুপের আকারের এই মিল আসলেই অদ্ভুত।"},
            {"index": 4, "type": "p",
             "tts": "এই বিশাল সংখ্যাটি আসলে মনস্টার নামক এক বিশেষ গ্রুপের আকার। কিন্তু মনস্টার কী, তা বোঝার আগে আমাদের কিছুটা পেছনে যেতে হবে, গ্রুপ তত্ত্বের মূল ধারণাগুলোর দিকে।"},
        ],
    },

    "sec-definition": {
        "title": "২. গ্রুপের স্বজ্ঞাত সংজ্ঞা",
        "audio_file": "sec_sec-definition.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, গ্রুপের স্বজ্ঞাত সংজ্ঞা।"},
            {"index": 1, "type": "p",
             "tts": "গ্রুপ তত্ত্বের কাজ হলো সমমিতির ধারণাকে আনুষ্ঠানিকভাবে ধরা। যখন আমরা বলি কোনো মুখ সমমিত, তখন বোঝাই, একে কোনো রেখা বরাবর উল্টালেও সেটি আগের মতোই দেখায়। অর্থাৎ আমরা আসলে একটি কাজ বা ক্রিয়া সম্পর্কেই কথা বলছি।"},
            {"index": 2, "type": "figure",
             "tts": "এই ছবিতে মুখটি প্রতিফলনের আগে ও পরে দেখানো হয়েছে। লক্ষ্য করুন, প্রতিফলনের পরও মুখটি আগের মতোই দেখাচ্ছে। অর্থাৎ এই কাজটি বস্তুটির চেহারা বদলায় না, ঠিক যেমনটি সমমিতিতে প্রত্যাশা করি।"},
            {"index": 3, "type": "p",
             "tts": "তুষারকণা আরও অনেকভাবে সমমিত। আপনি এটিকে ৬০ ডিগ্রি বা ১২০ ডিগ্রি ঘোরাতে পারেন, অথবা বিভিন্ন অক্ষ বরাবর উল্টাতে পারেন, প্রতিটি কাজের পরেই এটি আগের মতোই দেখায়।"},
            {"index": 4, "type": "figure",
             "tts": "এই ছবিতে তুষারকণার একাধিক ঘূর্ণন ও প্রতিফলন সমমিতি দেখানো হয়েছে। একই বস্তুতে এতগুলো ভিন্ন কাজ আগের অবস্থা ফিরিয়ে আনে। এই কাজগুলোরই একটি সুসংগঠিত সংগ্রহ মিলে গড়ে তোলে একটি গ্রুপ।"},
            {"index": 5, "type": "callout",
             "tts": "বিশেষ নোট, গ্রুপ কী। এই ধরনের সব কাজের সমষ্টিকেই আমরা গ্রুপ বলি। কিছু না করা কাজটিও সবসময় গ্রুপের অংশ ধরা হয়। তুষারকণার ক্ষেত্রে এই বারোটি কাজ নিয়ে গড়ে ওঠা গ্রুপটির নাম ডি ছয়।"},
            {"index": 6, "type": "p",
             "tts": "মুখের মতো সরল সমমিতির গ্রুপটির নাম সি দুই। সাধারণভাবে গ্রুপের এক বিশাল প্রাণীশালা রয়েছে, প্রতিটি নামই ভিন্ন ভিন্ন সমমিতির ধরন বর্ণনা করে।"},
            {"index": 7, "type": "figure",
             "tts": "এই ছবিতে বিভিন্ন গ্রুপের প্রাণীশালা দেখা যাচ্ছে, প্রতিটি নাম এক ধরনের সমমিতির প্রতীক। কিছু গ্রুপ ছোট, আবার কিছু গ্রুপ অসংখ্য কাজ নিয়ে গড়া। এই বৈচিত্র্যের মধ্যেও সবগুলোই একই কয়েকটি সরল নিয়ম মেনে চলে।"},
            {"index": 8, "type": "p",
             "tts": "যেকোনো বস্তুর ক্ষেত্রে আমরা তার গঠন অক্ষত রেখে কাজগুলোর কথা ভাবি। ঘনককে চব্বিশভাবে ঘোরালে সেটি আগের মতোই থাকে, আর এই চব্বিশটি কাজ মিলে একটি গ্রুপ গড়ে তোলে।"},
            {"index": 9, "type": "figure",
             "tts": "এই ছবিতে ঘনকের চব্বিশটি ঘূর্ণন দেখানো হয়েছে, যার প্রতিটি গঠন রক্ষা করে। ঘনকটি ঘোরালেও তার আকৃতি ও কোণগুলোর বিন্যাস অপরিবর্তিত থাকে। এই ধরনের প্রতিটি অপরিবর্তনকারী কাজই গ্রুপের একটি উপাদান।"},
            {"index": 10, "type": "p",
             "tts": "যদি প্রতিফলনের অনুমতি দেওয়া হয়, অর্থাৎ অভিমুখ রক্ষা না করা হয়, তবে মোট আটচল্লিশটি কাজ পাওয়া যায়। আবার যদি মুখগুলোকে আলগা ভেবে সরানো ও ঘোরানো যায়, তবে আটের ঘাত ছয় গুণ ছয়ের ফ্যাক্টরিয়াল সংখ্যক কাজের একটি বড় গ্রুপ পাই।"},
            {"index": 11, "type": "p",
             "tts": "সবচেয়ে আলগা কাঠামো হলো বিন্দুগুলোর যেকোনো বিন্যাস, অর্থাৎ যেকোনো পারম্যুটেশনকেই সমমিতি ধরা। ছয়টি বিন্দুর ক্ষেত্রে ছয়ের ফ্যাক্টরিয়াল অর্থাৎ সাতশো বিশটি কাজ। একশো একটি বিন্দুর পারম্যুটেশন গ্রুপের আকার প্রায় ৯.৪৩ গুণ দশের ঘাত ১৫৯, অবজার্ভেবল ইউনিভার্সের প্রতিটি পরমাণুর ভেতরে একটা করে ইউনিভার্স থাকলে যতটি সাবঅ্যাটম হতো, প্রায় ততটি!"},
        ],
    },

    "sec-axioms": {
        "title": "৩. গ্রুপের গাণিতিক সংজ্ঞা",
        "audio_file": "sec_sec-axioms.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, গ্রুপের গাণিতিক সংজ্ঞা।"},
            {"index": 1, "type": "p",
             "tts": "এখন প্রশ্ন, কোনো কিছুকে গ্রুপ বলা যাবে কীভাবে ঠিক করব? প্রথমে লাগবে একটি সেট, যেকোনো জিনিসের সংগ্রহ, যেমন পূর্ণসংখ্যা, পারম্যুটেশন, অথবা কোনো জ্যামিতিক বস্তুর সমমিতি কাজ।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এ বৃত্ত বি সমান সি। এখানে বৃত্তটি হলো বাইনারি অপারেটর, অর্থাৎ দুটি উপাদান নিয়ে একটিমাত্র ফল তৈরি করে।"},
            {"index": 3, "type": "callout",
             "tts": "বিশেষ নোট, গ্রুপের চারটি স্বত্ব বা অ্যাক্সিয়ম। প্রথমত আবদ্ধতা, দুটি উপাদানের ফলাফলও গ্রুপের ভেতরেই থাকবে। দ্বিতীয়ত সহযোগিতা, ব্র্যাকেট বা গ্রুপিং বদলালে ফল বদলায় না। তৃতীয়ত একত্ব, কিছু না করার মতো এক উপাদান থাকবে। চতুর্থত বিপরীত, প্রতিটি উপাদানের একটি বিপরীত থাকবে, যার সাথে যুক্ত করলে একত্ব পাওয়া যায়।"},
            {"index": 4, "type": "figure",
             "tts": "এই ছবিতে দেখানো হয়েছে, দুটি সমমিতি কাজ একের পর এক প্রয়োগ করলে সবসময় আরেকটি সমমিতি কাজই পাওয়া যায়। কোনো ফল দলের বাইরে যায় না। এটিই আবদ্ধতার স্বত্ব, গ্রুপের প্রথম ও মৌলিক শর্ত।"},
            {"index": 5, "type": "p",
             "tts": "তুষারকণার ৬০ ডিগ্রি ঘোরানোকে তিনবার প্রয়োগ করলে ১৮০ ডিগ্রি ঘোরানো পাই। অপারেশন বাইনারি হওয়ায় একবারে দুটিকে নিতে হয়, কিন্তু সহযোগিতার স্বত্ব বলে কোন দুটিকে আগে নিই তা ফল বদলায় না, যেমন ৬০ ডিগ্রির তিনটি ঘূর্ণন যুক্ত করলেই ১৮০ ডিগ্রি পাওয়া যায়।"},
            {"index": 6, "type": "p",
             "tts": "বর্গক্ষেত্রের সমমিতির পূর্ণ আট গুণ আট গুণন সারণি আছে। উপরের সারির কাজের পর বাঁ কলামের কাজ প্রয়োগ করলে যে ঘরে পৌঁছাই, সেটিই তাদের গুণফল।"},
            {"index": 7, "type": "figure",
             "tts": "এই ছবিতে বর্গক্ষেত্রের সমমিতির আট গুণ আট গুণন সারণি দেখা যাচ্ছে। প্রতিটি ঘর গ্রুপের দুটি উপাদানের সংযোজনের ফল দেখায়। সারি ও কলামের কাজগুলো মিলে পুরো গ্রুপের গঠন এক নজরে ধরা পড়ে।"},
            {"index": 8, "type": "p",
             "tts": "ঘোরানো আর এক্স অক্ষ বরাবর প্রতিফলন দিয়ে বর্গের গ্রুপ বর্ণনা করা যায়। কাজগুলো ডান থেকে বাঁয়ে পড়া হয়, তাই আগে ঘোরে পরে উল্টালে লেখা হয় এস আর।"},
        ],
    },

    "sec-isomorphism": {
        "title": "৪. বিভিন্ন গ্রুপের তুলনা ও আইসোমরফিজম",
        "audio_file": "sec_sec-isomorphism.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, বিভিন্ন গ্রুপের তুলনা ও আইসোমরফিজম।"},
            {"index": 1, "type": "p",
             "tts": "তুষারকণা ও ষড়ভুজের সমমিতি একই গ্রুপ ডি ছয়, কারণ দুটির একই কাজ সংরক্ষিত হয়। কিন্তু একটি কম স্পষ্ট উদাহরণ হলো, ঘনকের ঘূর্ণন ও চারটি বস্তুর পারম্যুটেশন গ্রুপ প্রথমে আলাদা মনে হলেও আসলে একই, কারণ তাদের গুণন সারণি অভিন্ন।"},
            {"index": 2, "type": "figure",
             "tts": "এই ছবিতে ঘনকের ঘূর্ণন আর চারটি বিন্দুর পারম্যুটেশন পাশাপাশি দেখা যাচ্ছে, আসলে একই গঠন। ভিন্ন ভিন্ন বস্তু হলেও তাদের কাজের নিয়ম একই ধরনের। এই মিলই আমাদের আইসোমরফিজমের ধারণার দিকে নিয়ে যায়।"},
            {"index": 3, "type": "p",
             "tts": "ঘনকের আটটি কোণের দূরত্ব ও অভিমুখ রক্ষা করা আর চারটি বিন্দুর ওপর সম্পূর্ণ স্বাধীন কাজ, এই দুইয়ের মধ্যে একটি নিখুঁত মিল রয়েছে, যা সংযোজনকেও সংরক্ষণ করে। একে বলা হয় আইসোমরফিজম।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, আইসোমরফিজম কেন গুরুত্বপূর্ণ। দুটি গ্রুপ আইসোমরফিক মানে তাদের একই অন্তর্নিহিত গঠন, এক সম্পর্কে যা বলা যায় তা অপরের ক্ষেত্রেও সত্য। গ্রুপ কোনো এক বস্তুর সমমিতি নয়, বরং সমমিতির একটি বিমূর্ত রূপ, ঠিক যেমন তিন কোনো নির্দিষ্ট ত্রয়ী নয়, সব ত্রয়ীরই সারাংশ।"},
            {"index": 5, "type": "figure",
             "tts": "এই ছবিতে তিনের ধারণাটি দেখানো হয়েছে, যা সব ত্রয়ীর সারাংশ। ঠিক তেমনি গ্রুপও সমমিতির বিমূর্ত রূপ, কোনো একটি বস্তুতে সীমাবদ্ধ নয়। একটি গঠন হিসেবে গ্রুপের পরিচয় তার আচরণেই নিহিত।"},
        ],
    },

    "sec-monster": {
        "title": "৫. মনস্টার",
        "audio_file": "sec_sec-monster.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, মনস্টার।"},
            {"index": 1, "type": "p",
             "tts": "আইসোমরফিজম বোঝার পর একটা স্বাভাবিক প্রশ্ন ওঠে, বিশ্বে কতগুলো গ্রুপ আছে? অবশ্যই আইসোমরফিজম পর্যন্ত। আসলে কতভাবে কিছু সমমিত হতে পারে, সেটাই আমরা জানতে চাই।"},
            {"index": 2, "type": "p",
             "tts": "অসংখ্য গ্রুপ আছে, আবার অনেক সসীম গ্রুপও আছে। পূর্ণসংখ্যার মৌলিক উৎপাদক বা অণুর পরমাণুর মতো অনেক গ্রুপকে ছোট গ্রুপে ভেঙে লেখা যায়। যেগুলো আর ভাঙা যায় না, তাদের বলা হয় সরল গ্রুপ।"},
            {"index": 3, "type": "figure",
             "tts": "এই ছবিতে সরল গ্রুপের শ্রেণীবিভাগ পর্যায় সারণির মতো সাজানো হয়েছে। মৌলিক সংখ্যা যেমন রাসায়নিক উপাদানের ভিত্তি, তেমনি সরল গ্রুপও সব গ্রুপের মৌলিক উপাদান। এই সারণিরই এক কোণে আমাদের মনস্টারটি অবস্থান করে।"},
            {"index": 4, "type": "p",
             "tts": "আঠারোটি অসীম পরিবার ছাড়াও ছাব্বিশটি এমন সরল গ্রুপ আছে যারা কোনো পরিবারে ফিট করে না, তাদের বলা হয় স্পোরাডিক। মনস্টার হলো এদের মধ্যে বৃহত্তম, এর আকারই সেই আট গুণ দশের ঘাত তিপান্ন সংখ্যা। উনিশটি স্পোরাডিক গ্রুপ মনস্টারের সন্তান, আর বাকি ছয়টি প্যারিয়া।"},
            {"index": 5, "type": "p",
             "tts": "মনস্টার কোনো দুই বা তিন মাত্রিক বস্তুর সমমিতি নয়, এটি ১৯৬৮৮৩ মাত্রার একটি স্থানে কাজ করে। একটিমাত্র উপাদান বর্ণনা করতে প্রায় চার গিগাবাইট তথ্য লাগে, যা বোঝায় কতটা বিশাল এই গ্রুপ।"},
            {"index": 6, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, গ্রুপের স্বত্বগুলো সংক্ষিপ্ত ও স্বাভাবিক, কিন্তু এর পেছনে লুকিয়ে আছে মনস্টার সিম্পল গ্রুপ, এক বিশাল ও অসাধারণ গাণিতিক বস্তু। বলেছেন রিচার্ড বোচার্ডস।"},
            {"index": 7, "type": "p", "role": "conclusion",
             "tts": "সত্তরের দশকে জন ম্যাককি লক্ষ করেন ১৯৬৮৮৩ এর কাছাকাছি এক সংখ্যা মডুলার ফর্মের ধারা বিস্তারে হাজির হয়। এটি মুনশাইন নামে পরিচিত হয়, এবং ১৯৯২ সালে রিচার্ড বোচার্ডস এটি প্রমাণ করেন, গণিতের দুই সম্পূর্ণ আলাদা অংশের এই অপ্রত্যাশিত সংযোগই শেষ পর্যন্ত মনস্টারের রহস্য উন্মোচন করে।"},
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
    if total != 40:
        raise ValueError(f"Expected 40 cues, found {total}")

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
        "lesson": "lesson_01",
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
    assert total_cues == 40

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Group Theory Lesson 01")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<24} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTIONS_DATA)} sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json is valid JSON; all 5 mp3 files exist and are non-empty.")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(build_all())
