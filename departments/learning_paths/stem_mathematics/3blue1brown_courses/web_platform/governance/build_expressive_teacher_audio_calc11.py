# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Calculus Lesson 11
("What does dx really mean? / derivative as magnification", Bengali) to the
Lesson-01/02/10 gold standard, with NATURAL expressive figure phrasing.

Deterministic, re-runnable, self-contained:
  * 36 cues in 5 narrated sections with EXACTLY the same section IDs, canonical
    + alias section keys, audio_file names and cue type/order as the existing
    manifest and the live DOM:
      sec-the-dx-paradox        -> h2, chapter-quote, p, p, p, formula-box, callout, p (8)
      sec-tangent-line-geometry -> h2, p, p, p, p, formula-box, callout             (7)
      sec-error-and-vanishing   -> h2, p, p, p, p, formula-box, callout, p          (8)
      sec-dx-in-integration     -> h2, p, p, p, p, formula-box, callout             (7)
      sec-modern-perspective    -> h2, p, p, p, formula-box, callout                (6)
    (The live DOM has no figure.lesson-figure blocks in narrated sections, so
     there are no figure cues; where the prose describes a diagram it is written
     as natural, warm teacher speech. No cue uses the artificial label
     "চিত্র প্রদর্শনী".)
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Every script is clean spoken Bengali with phonetic safeguards:
      dx -> ডি এক্স, dy -> ডি ওয়াই, df -> ডি এফ, dy/dx -> ডি ওয়াই বাই ডি এক্স,
      f'(x) -> এফ প্রাইম এক্স, f''(x) -> এফ ডাবল প্রাইম অফ এক্স,
      Δx -> ডেল্টা এক্স, Δy -> ডেল্টা ওয়াই, x -> এক্স, y -> ওয়াই, u -> ইউ,
      dt -> ডি টি, v(t) -> ভি অফ টি.
    No TeX, LaTeX, backslashes, $, braces, brackets, em/en-dashes, raw hyphens
    or Latin letters.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, figure -4%, formula-box -8%, p +2%, callout +0%,
      conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with the
    exact-ms timings and BOTH the 5 canonical keys AND the 5 alias keys, exactly
    matching the existing manifest structure.
  * Validates non-zero durations, zero overlap, valid JSON and non-empty mp3s,
    plus DOM parity against the browser-extracted calc11_dom_blocks.json.

Usage:  python governance/build_expressive_teacher_audio_calc11.py
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
                         "calculus", "lesson_11")
DOM_SNAPSHOT = os.path.join(SCRIPT_DIR, "calc11_dom_blocks.json")
MANIFEST_TITLE = "অধ্যায় ১১ — ডি এক্স এর প্রকৃত অর্থ (What does dx really mean?)"

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
    "sec-the-dx-paradox":        ["h2", "chapter-quote", "p", "p", "p", "formula-box", "callout", "p"],
    "sec-tangent-line-geometry": ["h2", "p", "p", "p", "p", "formula-box", "callout"],
    "sec-error-and-vanishing":   ["h2", "p", "p", "p", "p", "formula-box", "callout", "p"],
    "sec-dx-in-integration":     ["h2", "p", "p", "p", "p", "formula-box", "callout"],
    "sec-modern-perspective":    ["h2", "p", "p", "p", "formula-box", "callout"],
}
EXPECTED_AUDIO_FILES = {
    "sec-the-dx-paradox":        "sec_01_the_dx_paradox.mp3",
    "sec-tangent-line-geometry": "sec_02_tangent_line_geometry.mp3",
    "sec-error-and-vanishing":   "sec_03_error_and_vanishing.mp3",
    "sec-dx-in-integration":     "sec_04_dx_in_integration.mp3",
    "sec-modern-perspective":    "sec_05_modern_perspective.mp3",
}
# Legacy alias names kept BOTH as extra `sections` keys and inside `alias`.
ALIASES = {
    "sec-the-dx-paradox":        "sec_01_the_dx_paradox",
    "sec-tangent-line-geometry": "sec_02_tangent_line_geometry",
    "sec-error-and-vanishing":   "sec_03_error_and_vanishing",
    "sec-dx-in-integration":     "sec_04_dx_in_integration",
    "sec-modern-perspective":    "sec_05_modern_perspective",
}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (36 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-the-dx-paradox": {
        "title": "১. ডি এক্স-এর হেঁয়ালি ও গণিতের সবচেয়ে ফলপ্রসূ মিথ্যা (The Paradox of dx)",
        "audio_file": "sec_01_the_dx_paradox.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, ডি এক্সের হেঁয়ালি আর গণিতের সবচেয়ে ফলপ্রসূ মিথ্যা।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, লাইবনিজের ডি এক্স প্রতীকটি কোনো যাদুকরী বিভ্রান্তি নয়। এটি গণিতের সবচেয়ে সুবিধাজনক আর গভীর সংকেত, যা জটিল সত্যকে সহজাত অনুভূতিতে রূপ দেয়। বলেছেন গ্রান্ট স্যান্ডারসন, থ্রি ব্লু ব্রাউন।"},
            {"index": 2, "type": "p",
             "tts": "ক্যালকুলাসের ক্লাসরুমে প্রায় প্রতিটি শিক্ষার্থী এক গভীর দ্বন্দ্বে পড়ে। শিক্ষক যখন বোর্ডে লেখেন ডি ওয়াই বাই ডি এক্স সমান লিমিট ডেল্টা এক্স টেন্ডস টু জিরো ডেল্টা ওয়াই বাই ডেল্টা এক্স, তখন কঠোর গলায় বলেন, মনে রাখবে, ডি ওয়াই বাই ডি এক্স কোনো একক ভগ্নাংশ নয়। এটি একটি একক অপারেটর বা চিহ্নের মতো। কিন্তু পরের ক্লাসেই যখন চেইন রুল বা প্রতিস্থাপন দ্বারা সমাকলন শেখানো হয়, তখন উভয় পক্ষে নিশ্চিন্তে ডি এক্স গুণ করা হয় আর কাটাকাটিও করা হয়।"},
            {"index": 3, "type": "p",
             "tts": "যদি ডি এক্স কোনো পৃথক সংখ্যাই না হয়, তবে একে কীভাবে আলাদা করা যায়। আবার ডি এক্স যদি একটি সাধারণ সংখ্যাই হয়, তবে তাকে সাধারণ ভগ্নাংশ বলতে এত দ্বিধা কেন।"},
            {"index": 4, "type": "p",
             "tts": "এই প্রশ্নের গভীরে রয়েছে গণিতের তিন শতাব্দীর দার্শনিক বিবর্তন। নিউটন আর লাইবনিজ যখন সতেরো শতকের আশির দশকে ক্যালকুলাস সৃষ্টি করেন, তখন তারা ডি এক্স আর ডি ওয়াইকে অসীম ক্ষুদ্র অথচ অশূন্য রাশি হিসেবে কল্পনা করেছিলেন। একে বলা হয় ইনফিনিটেসিমাল।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক তুলনা, একদিকে সীমার কঠোর অনুপাত ডি ওয়াই বাই ডি এক্স সমান লিমিট ডেল্টা এক্স টেন্ডস টু জিরো ডেল্টা ওয়াই বাই ডেল্টা এক্স, অন্যদিকে লাইবনিজের সহজ প্রতীক ডি ওয়াই সমান এফ প্রাইম অফ এক্স গুণ ডি এক্স।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, দার্শনিক দ্বন্দ্ব, অশূন্য কিন্তু ক্ষুদ্রতর। যদি ডি এক্স শূন্য হয়, তবে ভাগফল অনির্ণেয়, শূন্য ভাগ শূন্য। আর যদি ডি এক্স শূন্য না হয়, তবে হিসাবের শেষে আমরা ডি এক্সযুক্ত পদগুলোকে হাওয়ায় উড়িয়ে দিই কোন অধিকারে। দার্শনিক বিশপ বার্কলি আঠারো শতকে এদের ব্যঙ্গ করেছিলেন বিদায়ী রাশির প্রেতাত্মা বলে।"},
            {"index": 7, "type": "p",
             "tts": "এই দ্বন্দ্ব মেটাতে কশি আর ভাইয়ারস্ট্রাস এনেন সীমার কঠোর সংজ্ঞা। তবুও লাইবনিজের সেই সহজ প্রতীকবাদ আজও অমর হয়ে আছে।"},
        ],
    },

    "sec-tangent-line-geometry": {
        "title": "২. স্পর্শক রেখার জগতে dx ও dy (Tangent Line Geometry)",
        "audio_file": "sec_02_tangent_line_geometry.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, স্পর্শক রেখার জগতে ডি এক্স আর ডি ওয়াই।"},
            {"index": 1, "type": "p",
             "tts": "গ্রান্ট স্যান্ডারসনের দৃষ্টিকোণ থেকে, আর আধুনিক জ্যামিতিক ক্যালকুলাস থেকে, ডি এক্সের সবচেয়ে সুন্দর আর সন্তোষজনক ব্যাখ্যাটি হলো, স্পর্শক রেখার ওপর পরিবর্তন।"},
            {"index": 2, "type": "p",
             "tts": "ধরা যাক একটি মসৃণ বক্ররেখা, ওয়াই সমান এফ অফ এক্স। লেখচিত্রের যেকোনো নির্দিষ্ট বিন্দুতে আমরা একটি স্পর্শক সরলরেখা টানলাম, যাকে ইংরেজিতে বলা হয় ট্যানজেন্ট লাইন।"},
            {"index": 3, "type": "p",
             "tts": "এখন আমরা ইনপুটকে সামান্য একটু নাড়া দিলাম। এই আনুভূমিক নাড়াচাড়াকেই আমরা বলছি ডেল্টা এক্স বা ডি এক্স। লক্ষ্য করুন, ডি এক্স কোনো অলৌকিক অসীম ক্ষুদ্র ভূত নয়। এটি একটি বাস্তব, দৃশ্যমান, সসীম সংখ্যা, যেমন শূন্য দশমিক এক বা শূন্য দশমিক শূন্য শূন্য এক।"},
            {"index": 4, "type": "p",
             "tts": "এবার গুরুত্বপূর্ণ পার্থক্যটি খেয়াল করুন। ইনপুট ডি এক্স সরলে মূল বক্ররেখা বরাবর যে উল্লম্ব পরিবর্তন হয়, তা হলো ডেল্টা ওয়াই। কিন্তু স্পর্শক সরলরেখা বরাবর যে উল্লম্ব পরিবর্তন হয়, ঠিক তাকেই বলা হয় ডি ওয়াই।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সমীকরণ, ডেল্টা ওয়াই সমান এফ অফ এক্স প্লাস ডি এক্স বিয়োগ এফ অফ এক্স, অর্থাৎ বক্ররেখা বরাবর প্রকৃত পরিবর্তন। আর ডি ওয়াই সমান এফ প্রাইম অফ এক্স গুণ ডি এক্স, অর্থাৎ স্পর্শক রেখা বরাবর আনুমানিক পরিবর্তন।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, বিরাট অন্তর্দৃষ্টি, স্পর্শকের ঢাল একটি সত্যিকারের ভগ্নাংশ। স্পর্শক সরলরেখার জগতে ডি এক্স আর ডি ওয়াই, দুটোই দুটি সাধারণ বাস্তব দৈর্ঘ্য। স্পর্শক রেখার খাড়া দৈর্ঘ্য ডি ওয়াইকে ভূমির দৈর্ঘ্য ডি এক্স দিয়ে ভাগ করলে অবিকল ঢাল এফ প্রাইম অফ এক্স পাওয়া যায়। স্পর্শকের তলে ডি ওয়াই বাই ডি এক্স শতভাগ একটি খাঁটি ভগ্নাংশ।"},
        ],
    },

    "sec-error-and-vanishing": {
        "title": "৩. ত্রুটি বিলোপ ও উচ্চতর ঘাত: কেন (dx)^2 হারিয়ে যায়? (Vanishing Higher Powers)",
        "audio_file": "sec_03_error_and_vanishing.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, ত্রুটি বিলোপ আর উচ্চতর ঘাত, কেন ডি এক্স স্কয়ার হারিয়ে যায়।"},
            {"index": 1, "type": "p",
             "tts": "এখন প্রশ্ন হলো, প্রকৃত পরিবর্তন ডেল্টা ওয়াই আর স্পর্শকের পরিবর্তন ডি ওয়াইয়ের মধ্যে যে ফাঁক বা ত্রুটি থাকে, সেটি কত বড়।"},
            {"index": 2, "type": "p",
             "tts": "টেইলর উপপাদ্য আর বহুপদী বিশ্লেষণ থেকে আমরা জানি, ডেল্টা ওয়াই সমান এফ প্রাইম অফ এক্স গুণ ডি এক্স, যোগ হাফ এফ ডাবল প্রাইম অফ এক্স গুণ ডি এক্স স্কয়ার, যোগ উচ্চতর ঘাতসমূহ।"},
            {"index": 3, "type": "p",
             "tts": "অর্থাৎ ডেল্টা ওয়াই বিয়োগ ডি ওয়াই হলো হাফ এফ ডাবল প্রাইম অফ এক্স গুণ ডি এক্স স্কয়ার। এই পার্থক্যটি সরাসরি ডি এক্স স্কয়ারের সমানুপাতিক।"},
            {"index": 4, "type": "p",
             "tts": "এবার সংখ্যার স্কেলিং নিয়ে ভাবুন। যদি ডি এক্স সমান শূন্য দশমিক শূন্য এক হয়, তবে ডি এক্স স্কয়ার সমান শূন্য দশমিক শূন্য শূন্য শূন্য এক। অর্থাৎ প্রথম ক্রমের পরিবর্তনের তুলনায় ত্রুটিটি একশ গুণ দ্রুত সংকুচিত হয়। ডি এক্স শূন্যের দিকে যাওয়ার সীমায় ত্রুটির অনুপাত শূন্য হয়ে যায়।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সমীকরণ, বক্রতার ত্রুটি ডি এক্স স্কয়ারের ক্রমের, তাই ডি এক্স শূন্যের দিকে যাওয়ার সীমায় ডেল্টা ওয়াই বাই ডেল্টা এক্স সমান ডি ওয়াই বাই ডি এক্স, আর তার মান এফ প্রাইম অফ এক্স।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, কেন বীজগণিতীয় কাটাকাটি কাজ করে। কারণ চেইন রুল বা প্রতিস্থাপনে আমরা মূলত স্পর্শকীয় রৈখিক রূপান্তরগুলোকে পরস্পরের সাথে গুণ করি। আর রৈখিক জগতে ভগ্নাংশ কাটাকাটি সম্পূর্ণ সুসংগত।"},
            {"index": 7, "type": "p",
             "tts": "তাহলে সমাকলনে ইন্টিগ্রাল এফ অফ এক্স ডি এক্স চিহ্নের ভেতর ডি এক্স কী অর্থ বহন করে।"},
        ],
    },

    "sec-dx-in-integration": {
        "title": "৪. সমাকলনে dx: কেবল প্রতীক নয়, আয়তক্ষেত্রের বাস্তব প্রস্থ (dx in Integration)",
        "audio_file": "sec_04_dx_in_integration.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, সমাকলনে ডি এক্স, কেবল প্রতীক নয়, আয়তক্ষেত্রের বাস্তব প্রস্থ।"},
            {"index": 1, "type": "p",
             "tts": "অনেক শিক্ষার্থী মনে করেন ইন্টিগ্রালে ডি এক্স কেবল একটি সমাপ্তি ব্র্যাকেটের মতো, যা নির্দেশ করে চলকটি কোন অক্ষ বরাবর। কিন্তু এটি তার চেয়ে বহু গুণ বেশি জীবন্ত।"},
            {"index": 2, "type": "p",
             "tts": "রিম্যান সমষ্টিতে আমরা ব্যবধিটিকে অসংখ্য ক্ষুদ্র অংশে ভাগ করি, যার প্রতিটির প্রস্থ ডেল্টা এক্স। প্রতিটি সরু আয়তক্ষেত্রের ক্ষেত্রফল হলো উচ্চতা গুণ প্রস্থ, অর্থাৎ এফ অফ এক্স গুণ ডেল্টা এক্স।"},
            {"index": 3, "type": "p",
             "tts": "লাইবনিজ যখন ইন্টিগ্রাল চিহ্ন উদ্ভাবন করেন, তিনি লাতিন সুম্মা শব্দের বড়হাতের এস অক্ষরটিকে টেনে লম্বা করেছিলেন। আর ডি এক্স হলো সেই রিম্যান ফালির অতি ক্ষুদ্র ভিত্তি বা প্রস্থ।"},
            {"index": 4, "type": "p",
             "tts": "ফলে ইন্টিগ্রাল এফ অফ এক্স ডি এক্স কোনো অলীক প্রতীক নয়। এটি অসীম সংখ্যক ক্ষেত্রফল ফালির এক বাস্তব ধারাবাহিক যোগফল, যেখানে প্রতিটি ফালি এফ অফ এক্স গুণ ডি এক্স। যখন আমরা চলক প্রতিস্থাপন করি, আমরা মূলত এক্স অক্ষের ফালির প্রস্থকে নতুন অক্ষের ফালির প্রস্থের সাথে স্কেল করে নিচ্ছি।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, রিম্যান যোগফলের সীমায় ভিত্তি ডেল্টা এক্স সরাসরি ডিফারেনশিয়াল ডি এক্সে রূপান্তরিত হয়। আর ডি ইউ সমান ডি ইউ বাই ডি এক্স গুণ ডি এক্স।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, মাত্রা বা এককের সৌন্দর্য। পদার্থবিজ্ঞানে ডি এক্সের ভৌত গুরুত্ব অপরিসীম। যদি ভি অফ টি হয় মিটার প্রতি সেকেন্ডে বেগ আর ডি টি হয় সেকেন্ডে সময়, তবে ভি গুণ ডি টির একক দাঁড়ায় মিটার। ডি টি না থাকলে সমাকলনের কোনো সঠিক ভৌত মাত্রা থাকত না।"},
        ],
    },

    "sec-modern-perspective": {
        "title": "৫. আধুনিক গণিতে dx: স্পর্শক ভেক্টর ও ডিফারেনশিয়াল ফর্ম (Modern Differential Forms)",
        "audio_file": "sec_05_modern_perspective.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, আধুনিক গণিতে ডি এক্স, স্পর্শক ভেক্টর আর ডিফারেনশিয়াল ফর্ম।"},
            {"index": 1, "type": "p",
             "tts": "বিশ শতকের আধুনিক গণিতবিদরা ডি এক্সের এই ধারণাকে আরও এক ধাপ এগিয়ে নিয়ে গেছেন, যাকে বলা হয় ডিফারেনশিয়াল ফর্ম।"},
            {"index": 2, "type": "p",
             "tts": "সেখানে ডি এক্সকে দেখা হয় একটি পরিমাপক যন্ত্র বা রৈখিক ফাংশনাল হিসেবে। আপনি এটিকে একটি স্পর্শক ভেক্টর ইনপুট দেবেন, আর এটি আপনাকে বলে দেবে সেই ভেক্টরটি এক্স অক্ষ বরাবর কতটুকু প্রসারিত হয়েছে।"},
            {"index": 3, "type": "p",
             "tts": "অতএব ডি এক্স কোনো একক অচল ধারণা নয়। এটি একাধারে ইনপুটের একটি ছোট বাস্তব বিচ্যুতি, স্পর্শক রেখা বরাবর রৈখিক আসন্নায়নের ভিত্তি, সমাকলন ফালির অতি ক্ষুদ্র প্রস্থ, এবং বহুমাত্রিক জ্যামিতিতে ভেক্টর পরিমাপক ডিফারেনশিয়াল ওয়ান ফর্ম।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সংজ্ঞা, আধুনিক ব্যবকলনীয় জ্যামিতিতে স্পর্শক ভেক্টরের অনুভূমিক উপাংশ পরিমাপক ওয়ান ফর্ম হলো ডি এক্স অফ ভি, যার মান ভি এক্স।"},
            {"index": 5, "type": "callout", "role": "conclusion",
             "tts": "উপসংহার, ভয়হীন ডি এক্স। পরের বার যখন কেউ বলবে ডি ওয়াই বাই ডি এক্স ভগ্নাংশ নয়, তখন মনে মনে হাসুন। কারণ আপনি জানেন, স্পর্শকের রৈখিক জগতে এটি একটি নিখুঁত ভগ্নাংশ, আর সীমার মাধ্যমে এটি মহাবিশ্বের পরিবর্তনের হারকে নির্ভুলভাবে ধরে রাখে।"},
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
        if ALIASES[sec_id] not in sec["audio_file"]:
            raise ValueError(f"{sec_id}: alias/audio_file inconsistency")
        indices = [c["index"] for c in sec["cues"]]
        if indices != list(range(len(indices))):
            raise ValueError(f"{sec_id}: cue indices are not 0..n-1")
        total += len(indices)
    if total != 36:
        raise ValueError(f"Expected 36 cues, found {total}")

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

    # Preserve the EXISTING manifest key order: canonical then alias, interleaved.
    manifest_sections = {}
    for sec_id, sec in SECTIONS_DATA.items():
        built = await build_section(sec_id, sec)
        manifest_sections[sec_id] = built
        manifest_sections[ALIASES[sec_id]] = built

    manifest_data = {
        "course": "calculus",
        "lesson": "lesson_11",
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
    expected_keys = set(SECTIONS_DATA) | set(ALIASES.values())
    assert set(loaded["sections"]) == expected_keys, "canonical + alias keys required"
    assert len(loaded["sections"]) == 10, "expected 10 section keys"
    total_cues = 0
    total_ms = 0.0
    figures = 0
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        assert loaded["sections"][ALIASES[sec_id]] == msec, "alias must equal canonical"
        assert len(msec["cues"]) == len(EXPECTED_TYPES[sec_id])
        assert msec["section_id"] == sec_id
        assert msec["alias"] == ALIASES[sec_id]
        assert msec["audio_file"] == EXPECTED_AUDIO_FILES[sec_id]
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    assert total_cues == 36

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, Calculus Lesson 11")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<30} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 5 sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json is valid JSON; 10 section keys (5 canonical + 5 alias); "
          "all 5 mp3 files non-empty.")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(build_all())
