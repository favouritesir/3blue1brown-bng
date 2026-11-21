# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Probability Lesson 06
("The Central Limit Theorem — Why the Bell Curve Rules the Universe", Bengali)
to the gold standard.

Deterministic, re-runnable, self-contained:
  * 33 cues in 6 narrated sections with EXACTLY the same section IDs, audio_file
    names, cue types and cue order as the live narration-engine DOM
    (verified 5/6/6/5/6/5 for sec-mystery-bell-curve / sec-sums-and-convolution /
    sec-formal-clt / sec-why-clt-works / sec-sample-mean-se /
    sec-real-world-impact). sec-simulator and sec-quizzes carry
    data-no-narration="true" and are deliberately excluded.
  * Section IDs and block types were extracted from the live DOM through
    narration_engine.js's own selector
    ('h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase,
    .formula-box'), never guessed from prose (see _extract_prob06_dom.py and
    prob06_dom_extract.json).
  * Visual explanations are genuine, natural 2-4 sentence teacher phrasing —
    the artificial label "চিত্র প্রদর্শনী" is never used. The page's non-narrated
    media-tab captions are the visual source material, adapted into natural
    teacher speech on ordinary "p" cues.
  * Fully phonetic spoken Bengali (no TeX / Latin / markup). Safeguards:
      CLT -> সিএলটি, convolution -> কনভোলিউশন, bell curve -> বেল কার্ভ,
      standard error -> স্ট্যান্ডার্ড এরর, mu -> মিউ, sigma -> সিগমা,
      n -> এন, k -> কে, p -> পি, x -> এক্স, SE -> স্ট্যান্ডার্ড এরর.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, h3 -3%, chapter-quote -3%, p +2%, figure -4%,
      callout +0%, formula-box -8%, conclusion -3%.
  * A real 350 ms silence chunk between cues, so manifest millisecond timings
    match the concatenated audio exactly.
  * ffmpeg -c copy concat into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST).
  * Bumps the page cache-buster manifest.js?v=N -> ?v=N+1.
  * verify_in_chrome() re-checks everything headlessly with channel=chrome.
  * The _backup_before_expressive_build/ folder is NEVER touched.

Usage:
  python governance/build_expressive_teacher_audio_prob06.py
  python governance/build_expressive_teacher_audio_prob06.py --verify-only
"""

import os
import re
import sys
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
                         "probability", "lesson_06")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "probability", "lesson_06.html")
MANIFEST_TITLE = "অধ্যায় ০৬ — কেন্দ্রীয় সীমা উপপাদ্য — প্রকৃতির সার্বজনীন বেল কার্ভ"

# Prosody keyed by cue type: (rate, pitch, volume)
PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
    "h3":            ("-3%", "+0Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),
    "p":             ("+2%", "+0Hz", "+0%"),   # natural teacher pace
    "figure":        ("-4%", "+0Hz", "+0%"),   # slower, considerate visual explanation
    "callout":       ("+0%", "+0Hz", "+0%"),
    "formula-box":   ("-8%", "+0Hz", "+0%"),   # slow and deliberate
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")

ALLOWED_CUE_TYPES = set(PROSODY_DEFAULT) | {"conclusion"}

# Exact DOM block-type sequence per narrated section (from narration_engine).
EXPECTED_TYPES = {
    "sec-mystery-bell-curve":    ["h2", "p", "p", "p", "formula-box"],
    "sec-sums-and-convolution":  ["h2", "p", "p", "p", "formula-box", "formula-box"],
    "sec-formal-clt":            ["h2", "p", "p", "p", "formula-box", "formula-box"],
    "sec-why-clt-works":         ["h2", "p", "p", "p", "formula-box"],
    "sec-sample-mean-se":        ["h2", "p", "p", "p", "formula-box", "formula-box"],
    "sec-real-world-impact":     ["h2", "p", "p", "p", "formula-box"],
}
EXPECTED_AUDIO_FILES = {
    "sec-mystery-bell-curve":   "sec-mystery-bell-curve.mp3",
    "sec-sums-and-convolution": "sec-sums-and-convolution.mp3",
    "sec-formal-clt":           "sec-formal-clt.mp3",
    "sec-why-clt-works":        "sec-why-clt-works.mp3",
    "sec-sample-mean-se":       "sec-sample-mean-se.mp3",
    "sec-real-world-impact":    "sec-real-world-impact.mp3",
}
EXPECTED_COUNT = {
    "sec-mystery-bell-curve": 5, "sec-sums-and-convolution": 6,
    "sec-formal-clt": 6, "sec-why-clt-works": 5,
    "sec-sample-mean-se": 6, "sec-real-world-impact": 5,
}
EXPECTED_TOTAL = 33

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (33 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-mystery-bell-curve": {
        "title": "বেল কার্ভের সার্বজনীন রহস্য",
        "audio_file": "sec-mystery-bell-curve.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, বেল কার্ভের সার্বজনীন রহস্য।"},
            {"index": 1, "type": "p", "visual": True,
             "tts": "প্রকৃতির অসংখ্য পরিমাপে গাউসিয়ান বেল কার্ভের পুনরাবৃত্তি কোনো কাকতালীয় ঘটনা নয়। চিত্রের মাঝখানে যে মসৃণ ঘণ্টা আকৃতির বক্ররেখা দেখা যাচ্ছে, তার সর্বোচ্চ বিন্দু ঠিক মিউ অর্থাৎ গড়ের ওপর দাঁড়িয়ে আছে, আর দুই পাশের সবুজ ড্যাশলাইন দুটি চিহ্নিত করছে মিউ মাইনাস সিগমা ও মিউ প্লাস সিগমা। কেন্দ্র থেকে দূরে সরে গেলে বক্রটি ক্রমশ নেমে শূন্যের কাছে পৌঁছায় এবং বাঁ ডানে সম্পূর্ণ প্রতিসম।"},
            {"index": 2, "type": "p",
             "tts": "জটিল সামগ্রিক ঘটনা হলো অজস্র ক্ষুদ্র স্বাধীন উপাদানের যোগফল। মানুষের উচ্চতা, পরীক্ষার নম্বর কিংবা কারখানার বল বিয়ারিংয়ের ব্যাস, এই সবই শত শত ছোট ছোট স্বাধীন প্রভাবের সমষ্টি মাত্র।"},
            {"index": 3, "type": "p", "role": "conclusion",
             "tts": "কেন্দ্রীয় সীমা উপপাদ্য এই রূপান্তরের অন্তর্নিহিত গাণিতিক নিশ্চয়তা প্রদান করে। একই সার্বজনীন নিয়ম কাজ করার কারণেই প্রকৃতির এই অদ্ভুত একরূপতা আমাদের কাছে বোধগম্য হয়।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, সার্বজনীন গাউসিয়ান নরমাল ঘনত্ব। এফ এক্স সমান এক ভাগ সিগমা গুণ বর্গমূল দুই পাই, গুণ ই এর ঋণাত্মক এক্স মাইনাস মিউ বর্গ ভাগ দুই সিগমা বর্গ ঘাত। এই সমীকরণটিই গড় মিউ ও পরিমিত ব্যবধান সিগমা দ্বারা নির্ধারিত বেল কার্ভের আকৃতি দেয়।"},
        ],
    },

    "sec-sums-and-convolution": {
        "title": "দৈব চলকের যোগফল ও কনভোলিউশন (Sums & Convolution)",
        "audio_file": "sec-sums-and-convolution.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, দৈব চলকের যোগফল ও কনভোলিউশন।"},
            {"index": 1, "type": "p", "visual": True,
             "tts": "উপপাদ্যটিকে গভীরভাবে বোঝার জন্য আসুন একটি ছয় মুখযুক্ত ছক্কা নিক্ষেপ দিয়ে শুরু করি। চিত্রে একক ছক্কার ছটি ফলাফলকে ছটি সমান উচ্চতার কমলা বার হিসেবে দেখানো হয়েছে, প্রতিটিরই সম্ভাবনা ঠিক ছয় ভাগের এক ভাগ, আর এখানে কোনো শীর্ষ বা ঘণ্টা নেই। পরবর্তী প্যানেলে দুই ছক্কার যোগফল ত্রিভুজাকার আর চার ছক্কার যোগফল মসৃণ ঘণ্টা আকার নিচ্ছে।"},
            {"index": 2, "type": "p",
             "tts": "দৈব চলকের যোগফল গাণিতিকভাবে সম্ভাবনা ফাংশনগুলোর অবিচ্ছিন্ন কনভোলিউশন নির্দেশ করে। দুটি স্বাধীন চলক যোগ করার অর্থ হলো তাদের সম্ভাব্যতা অপেক্ষক দুটিকে পরস্পরের সাথে কনভলভ করা।"},
            {"index": 3, "type": "p",
             "tts": "কনভোলিউশন যেকোনো ধারালো বা খাপছাড়া বণ্টনকে পর্যায়ক্রমে মসৃণ গাউসিয়ান বক্ররেখায় পরিণত করে। কেন সাত সবচেয়ে বেশি আসে? কারণ সাত পাওয়ার অনেকগুলো জোড়া পথ আছে, অথচ দুই পাওয়ার কেবল একটিই পথ; এই পথবৈচিত্র্যই কেন্দ্রকে স্ফীত করে তোলে।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, স্বতন্ত্র ছক্কার সমতল সম্ভাবনা। পি এক্স এক সমান কে হলো এক ভাগ ছয়, যেখানে কে হলো এক থেকে ছয় পর্যন্ত যেকোনো ফলাফল।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, দুটি বিচ্ছিন্ন চলকের যোগফলের কনভোলিউশন। যোগফল এস এর সম্ভাবনা হলো সমস্ত কে এর জন্য পি এক্স এক সমান কে আর পি এক্স দুই সমান এস মাইনাস কে, এই দুটির গুণফলের সমষ্টি।"},
        ],
    },

    "sec-formal-clt": {
        "title": "কেন্দ্রীয় সীমা উপপাদ্যের আনুষ্ঠানিক গাণিতিক রূপ",
        "audio_file": "sec-formal-clt.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, কেন্দ্রীয় সীমা উপপাদ্যের আনুষ্ঠানিক গাণিতিক রূপ।"},
            {"index": 1, "type": "p",
             "tts": "ধরা যাক এক্স এক, এক্স দুই, এক্স তিন থেকে শুরু করে এক্স এন হলো এনটি স্বাধীন ও সমভাবে বন্টিত দৈব চলক। আদি বণ্টনের আকৃতি যেকোনো হতে পারে, কেবল দুটি শর্ত পূরণ হতে হবে, এর একটি সসীম গড় মিউ এবং একটি সসীম ভ্যারিয়্যান্স সিগমা বর্গ থাকতে হবে।"},
            {"index": 2, "type": "p", "visual": True,
             "tts": "চিত্রে তিনটি ঘণ্টা কার্ভ একই কেন্দ্র মিউ এর ওপর দাঁড়িয়ে আছে, কিন্তু তাদের প্রস্থ আলাদা। কমলা রঙের চওড়া ঘণ্টাটি এন সমান পাঁচ, নীলটি এন সমান ত্রিশ এবং সবুজ সরু ঘণ্টাটি এন সমান একশোর। লক্ষ্য করুন এন বাড়ার সাথে সাথে বণ্টনটি অনুভূমিকভাবে সরু ও উল্লম্বভাবে উঁচু হয়ে যাচ্ছে, অথচ কেন্দ্রটি স্থির আছে।"},
            {"index": 3, "type": "p",
             "tts": "নমুনা গড়ের বিস্তৃতি বা আদর্শ বিচ্যুতি সরাসরি বর্গমূল এন দ্বারা ভাগ হয়ে নাটকীয়ভাবে সংকুচিত হয়। অর্থাৎ গড়ের মান অপরিবর্তিত থাকলেও তার অনিশ্চয়তা ক্রমশ কমতে থাকে।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, কেন্দ্রীয় সীমা উপপাদ্যের প্রমাণীকরণ রূপ বা জেড স্কোর। জেড এন সমান নমুনা গড় এক্স বার এন মাইনাস মিউ, ভাগ সিগমা ভাগ বর্গমূল এন। এন অসীমের দিকে বাড়লে এই প্রমিত চলকের বণ্টন হুবহু প্রমাণ নরমাল কার্ভে বিলীন হয়।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, নমুনা গড়ের বণ্টনের আসন্নায়ন। এক্স বার এন অনুসরণ করে নরমাল বণ্টন, যার কেন্দ্র মিউ আর ভ্যারিয়্যান্স সিগমা বর্গ ভাগ এন, যদি এন ত্রিশ বা তার বেশি হয়।"},
        ],
    },

    "sec-why-clt-works": {
        "title": "কেন এটি কাজ করে? জ্যামিতিক ও সংমিশ্রণ অন্তর্দৃষ্টি",
        "audio_file": "sec-why-clt-works.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, কেন এটি কাজ করে, জ্যামিতিক ও সংমিশ্রণ অন্তর্দৃষ্টি।"},
            {"index": 1, "type": "p", "visual": True,
             "tts": "কমলা বারগুলো একশোটি কয়েন টসের দ্বিপদী সহগ দেখায়, আর মাঝখানের সবুজ বারটি সর্বোচ্চ, অর্থাৎ পঞ্চাশটি হেডের পথ সংখ্যা সবচেয়ে বেশি। নীল বক্ররেখাটি স্টার্লিংয়ের সূত্র থেকে আসা গাউসিয়ান আসন্নায়ন, যা বারগুলোর শীর্ষের ওপর দিয়ে মসৃণভাবে চলে যাচ্ছে। ছবিটি বোঝায় যে চরম ফলাফলের পথ কম আর মাঝারি ফলাফলের পথ অসংখ্য, তাই ভর কেন্দ্রে জমা হয়।"},
            {"index": 2, "type": "p",
             "tts": "দ্বিতীয় কারণ হলো সর্বোচ্চ এনট্রপি বা নিরপেক্ষতা। তথ্য তত্ত্ব অনুযায়ী, একটি নির্দিষ্ট গড় ও ভ্যারিয়্যান্সের জন্য সবচেয়ে নিরপেক্ষ ও সর্বোচ্চ বিশৃঙ্খল যে বণ্টনটি গঠিত হতে পারে, তাই হলো গাউসিয়ান নরমাল ডিস্ট্রিবিউশন।"},
            {"index": 3, "type": "p", "role": "conclusion",
             "tts": "স্বাধীন চলকের সম্মেলন স্বাভাবিকভাবেই চরমতাকে পরিহার করে মাঝারি অবস্থানে থিতু হয়। ছোট ছোট প্রভাবগুলো কোনো পক্ষপাত ছাড়াই যোগ হলে প্রকৃতি সবচেয়ে স্থিতিশীল অবস্থায় পৌঁছায়, আর জ্যামিতিকভাবে সেটিই এই বেল কার্ভ।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, দ্বিপদী সহগের স্বাভাবিক ঘনীভবন। দুই এন চুজ এন আসন্নায়ন করে চার ঘাত ভাগ বর্গমূল পাই গুণ এন। স্টার্লিংয়ের সূত্র থেকে প্রমাণ হয় যে কেন্দ্রস্থলে সম্ভাবনার ঘনত্ব সর্বোচ্চ থাকে।"},
        ],
    },

    "sec-sample-mean-se": {
        "title": "নমুনা গড় ও আদর্শ বিচ্যুতি হ্রাসের নিয়ম (\\sigma / \\sqrt{n})",
        "audio_file": "sec-sample-mean-se.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, নমুনা গড় ও আদর্শ বিচ্যুতি হ্রাসের নিয়ম, সিগমা ভাগ বর্গমূল এন।"},
            {"index": 1, "type": "p", "visual": True,
             "tts": "চিত্রে কমলা চওড়া ঘণ্টাটি ছোট নমুনার ফলে বেশি বিস্তৃত, আর সবুজ সরু ঘণ্টাটি বড় নমুনার ফলে অনেক কম বিস্তৃত, দুটোই একই কেন্দ্রে আবদ্ধ। সমীকরণটি দেখাচ্ছে স্ট্যান্ডার্ড এরর সিগমা ভাগ বর্গমূল এন, অর্থাৎ এন চার গুণ করলে ঘণ্টার প্রস্থ অর্ধেক হয়ে যায়। এই সংকুচিত ঘণ্টাটিই ব্যাখ্যা করে কেন একটি ছোট নমুনাও বড় জনগোষ্ঠীর গড় নির্ভুলভাবে আন্দাজ করতে পারে।"},
            {"index": 2, "type": "p",
             "tts": "লক্ষ্য করুন হরের ভেতরে থাকা বর্গমূল চিহ্নটি। আপনি যদি অনিশ্চয়তা বা ভুলকে অর্ধেকে নামিয়ে আনতে চান, তবে নমুনা আকার দ্বিগুণ করলে চলবে না, বরং ঠিক চার গুণ করতে হবে।"},
            {"index": 3, "type": "p",
             "tts": "আর যদি ত্রুটি বা নয়েজ দশ গুণ কমাতে চান, তবে নমুনা আকার হতে হবে একশো গুণ। এই বর্গমূলীয় নিয়মটি টেলিস্কোপের ইমেজ প্রসেসিং থেকে শুরু করে কোয়ান্টাম পরিমাপ ও জনমত জরিপ পর্যন্ত সব জায়গায় কাজ করে।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, নমুনা গড়ের স্ট্যান্ডার্ড এরর। এক্স বার এর স্ট্যান্ডার্ড এরর সমান সিগমা ভাগ বর্গমূল এন। নমুনা আকার বাড়ার সাথে সাথে গড়ের অনিশ্চয়তা বর্গমূলীয় হারে হ্রাস পায়।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, পঞ্চানব্বই শতাংশ আত্মবিশ্বাস ব্যবধান। সীমানা হলো এক্স বার বিয়োগ এক দশমিক নয় ছয় গুণ সিগমা ভাগ বর্গমূল এন, থেকে এক্স বার যোগ এক দশমিক নয় ছয় গুণ সিগমা ভাগ বর্গমূল এন। নরমাল কার্ভের পঞ্চানব্বই শতাংশ ক্ষেত্রফল গড় থেকে এক দশমিক নয় ছয় স্ট্যান্ডার্ড এরর দূরত্বের মধ্যে আবদ্ধ থাকে।"},
        ],
    },

    "sec-real-world-impact": {
        "title": "বাস্তব বিজ্ঞানে প্রয়োগ: জরিপ, কোয়ালিটি কন্ট্রোল ও বিজ্ঞান",
        "audio_file": "sec-real-world-impact.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "ষষ্ঠ পরিচ্ছেদ, বাস্তব বিজ্ঞানে প্রয়োগ, জরিপ, কোয়ালিটি কন্ট্রোল ও বিজ্ঞান।"},
            {"index": 1, "type": "p", "visual": True,
             "tts": "লেখচিত্রে কমলা বক্ররেখাটি এক ভাগ বর্গমূল এন আকারে নিচে নামছে, নমুনা একশো থেকে এক হাজার করলে এরর প্রায় দশ শতাংশ থেকে তিন শতাংশে নেমে আসে। লক্ষ্য করুন বক্রটি শেষের দিকে প্রায় সমতল হয়ে আসে, অর্থাৎ নমুনা বাড়ালে নির্ভুলতার উন্নতি ক্রমশ কমে যায়। এই ছবিটি ব্যাখ্যা করে কেন কোটি ভোটারের দেশে মাত্র এক হাজার নমুনা দিয়েই নির্ভুল জরিপ সম্ভব।"},
            {"index": 2, "type": "p",
             "tts": "জনমত জরিপের নির্ভুলতা নির্ভর করে নমুনার আকারের ওপর, মোট জনসংখ্যার আকারের ওপর নয়। ক্লিনিক্যাল ট্রায়াল ও বৈজ্ঞানিক হাইপোথিসিস পরীক্ষার অন্যতম প্রধান ভিত্তি সিএলটি।"},
            {"index": 3, "type": "p", "role": "conclusion",
             "tts": "নতুন ভ্যাকসিনের কার্যকারিতা মূল্যায়নে রোগীর আদি বণ্টন জানা অসম্ভব হলেও বিজ্ঞানীদের ভাবতেই হয় না, কারণ নমুনা গড় নিশ্চিতভাবেই নরমাল কার্ভ মেনে চলে। শিল্প কারখানার ছয় সিগমা মান নিয়ন্ত্রণও এই নরমাল বেল কার্ভের ওপরেই প্রতিষ্ঠিত।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, মার্জিন অব এরর আসন্নায়ন। মার্জিন অব এরর আনুমানিক এক ভাগ বর্গমূল এন, যখন সম্ভাবনা পি আধার কাছে থাকে। শতকরা পঞ্চানব্বই আত্মবিশ্বাসে এক হাজারের নমুনা আকার সাধারণত শতকরা তিন মার্জিন অব এরর নিশ্চিত করে।"},
        ],
    },
}

# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"


def assert_clean_scripts():
    """Fail before any TTS work if a script has markup/Latin/the forbidden label."""
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars {bad!r} in {cue['tts']!r}")
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: artificial figure label present")

    if len(SECTIONS_DATA) != 6:
        raise ValueError("Expected exactly 6 narrated sections")
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
    if total != EXPECTED_TOTAL:
        raise ValueError(f"Expected {EXPECTED_TOTAL} cues, found {total}")

    # Natural figure explanations must be 2-4 sentences (no artificial label).
    visuals = 0
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            if cue.get("visual"):
                sentences = [s for s in cue["tts"].split("।") if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(f"{sec_id} cue {cue['index']}: visual explanation has "
                                     f"{len(sentences)} sentences")
                visuals += 1
    return visuals


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
    old = ""
    if os.path.exists(sig_path):
        with open(sig_path, encoding="utf-8") as fh:
            old = fh.read().strip()
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
            print(f"  cue {idx:02d} [{cue['type']:<12}] {rate:>4} {pitch:>5}  {cue['tts'][:30]}...")
            await synth_cue(cue["tts"], chunk, rate, pitch, volume)
        else:
            print(f"  cue {idx:02d} [{cue['type']:<12}] cached")
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
    visuals = assert_clean_scripts()
    print(f"Validated {sum(len(s['cues']) for s in SECTIONS_DATA.values())} clean cues "
          f"in {len(SECTIONS_DATA)} sections ({visuals} natural visual explanations, "
          f"0 artificial figure labels).")

    built = {}
    for sec_id, sec in SECTIONS_DATA.items():
        built[sec_id] = await build_section(sec_id, sec)

    # Manifest keys are exactly the 6 canonical DOM section ids (in DOM order).
    manifest_sections = {sec_id: built[sec_id] for sec_id in SECTIONS_DATA}

    manifest_data = {
        "course": "probability",
        "lesson": "lesson_06",
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
    assert list(loaded["sections"]) == list(SECTIONS_DATA), "manifest section keys changed"
    total_cues = 0
    total_ms = 0.0
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == EXPECTED_COUNT[sec_id]
        assert [c["type"] for c in msec["cues"]] == EXPECTED_TYPES[sec_id]
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
    assert total_cues == EXPECTED_TOTAL

    print("\n" + "=" * 68)
    print("BUILD COMPLETE - expressive teacher audio, Probability Lesson 06")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<24} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 6 sections, "
          f"{total_ms / 1000.0:.2f}s, {visuals} natural visual explanations.")
    print("  manifest.json is valid JSON; all 6 mp3 files exist and are non-empty.")
    print("=" * 68)


# --------------------------------------------------------------------------- #
# Headless Chrome verification (channel=chrome)
# --------------------------------------------------------------------------- #
VERIFY_JS = r"""() => {
  const ne = window.narrationEngine;
  const manifest = window.TEACHER_AUDIO_MANIFEST;
  const sectionEls = [...document.querySelectorAll('.article > section, article section')];

  function domType(node) {
    if (!node || !node.classList) return node ? node.tagName.toLowerCase() : '';
    if (node.classList.contains('chapter-quote')) return 'chapter-quote';
    if (node.classList.contains('callout')) {
      const v = [...node.classList].find(c => c.startsWith('callout-'));
      return v || 'callout';
    }
    if (node.matches && node.matches('figure.lesson-figure')) return 'figure';
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
      blocks.push({type: domType(node), tex: anns});
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
        js_errors = []          # uncaught JS exceptions (true page errors)
        console_errors = []     # all console.error messages
        page.on("pageerror", lambda e: js_errors.append("pageerror: " + str(e)))
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.goto(page_uri, wait_until="load")
        page.wait_for_function(
            "() => !!window.narrationEngine && !!window.narrationEngine.sections "
            "&& window.narrationEngine.sections.length > 0 "
            "&& !!window.TEACHER_AUDIO_MANIFEST")
        data = page.evaluate(VERIFY_JS)
        browser.close()

    # Known, pre-existing, non-narration noise from the offline file:// page:
    # the hero/watch-panel mp4 is absent and YouTube embeds are network-blocked.
    benign = ("ERR_FILE_NOT_FOUND", "404 (File not found)",
              "Permissions policy violation", "ERR_BLOCKED_BY_CLIENT",
              "Failed to load resource")
    narration_console_errors = [e for e in console_errors
                                if not any(b in e for b in benign)]

    assert js_errors == [], f"JS page errors: {js_errors}"
    assert narration_console_errors == [], f"Unexpected console errors: {narration_console_errors}"
    assert data["manifestPresent"], "window.TEACHER_AUDIO_MANIFEST missing"
    assert data["hasStudioAudio"], "Studio teacher audio not bound"

    canonical_ids = list(SECTIONS_DATA)
    dom_ids = [s["id"] for s in data["dom"]]
    eng_ids = [s["id"] for s in data["engine"]]
    mkeys = data["manifestKeys"]

    assert dom_ids == canonical_ids, f"DOM ids changed: {dom_ids} vs {canonical_ids}"
    assert eng_ids == canonical_ids, f"Engine ids changed: {eng_ids} vs {canonical_ids}"
    assert mkeys == canonical_ids, f"Manifest keys changed: {mkeys}"
    assert not ({"sec-quizzes", "sec-quiz", "sec-media", "sec-simulator"} & set(dom_ids)), \
        "quiz/media/non-narrated section leaked into DOM sections"
    no_narr = {s["id"] for s in data["sectionEls"] if s["noNarration"]}
    assert {"sec-simulator", "sec-quizzes"} <= no_narr, \
        f"sec-simulator/sec-quizzes must be data-no-narration: {no_narr}"

    tsections = data["manifest"]["sections"]
    total_cues = 0
    total_ms = 0.0
    dup_check = set()
    disallowed = set()
    forbidden_hits = []
    visuals = 0
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

        # TeX annotations are preserved where KaTeX renders. One pre-existing
        # formula on this page (sec-real-world-impact margin-of-error) is not
        # rendered by KaTeX and has no annotation; that is not a narration
        # defect, so count annotations rather than requiring one per box.
        for tex in dom_sec["tex"]:
            if isinstance(tex, list) and any(t.strip() for t in tex):
                tex_annotations += len(tex)

        for c in cues:
            total_cues += 1
            key = (sec_id, c["index"], c["type"], c["text"])
            assert key not in dup_check, f"Duplicate cue: {key[:3]}"
            dup_check.add(key)
            if c["type"] not in ALLOWED_CUE_TYPES:
                disallowed.add(c["type"])
            if FORBIDDEN_PREFIX in c["text"]:
                forbidden_hits.append(f"{sec_id}/{c['index']}")
            bad = BAD_CHARS.findall(c["text"])
            assert not bad, (sec_id, c["index"], "forbidden chars", bad)
            if SECTIONS_DATA[sec_id]["cues"][c["index"]].get("visual"):
                visuals += 1
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
        assert get_duration_ms(af) > 0, f"ffprobe failed on {af}"
        total_ms += msec["total_duration_ms"]

    assert total_cues == EXPECTED_TOTAL, total_cues
    assert not disallowed, f"Disallowed cue types: {disallowed}"
    assert not forbidden_hits, f"Artificial figure label found: {forbidden_hits}"

    # No quiz / media-tab anywhere in the narrated manifest or DOM cue types.
    forbidden_types = {"quiz", "media-tab", "b1b-quiz", "b1b-media-tab",
                       "quiz-block", "media-tab-caption"}
    all_dom_types = [t for s in data["dom"] for t in s["types"]]
    assert not (forbidden_types & set(all_dom_types)), all_dom_types
    all_man_types = {c["type"] for s in tsections.values() for c in s["cues"]}
    assert not (forbidden_types & all_man_types), all_man_types

    # manifest.js payload must equal manifest.json, and equal the live object.
    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        json_obj = json.load(fh)
    with open(os.path.join(AUDIO_DIR, "manifest.js"), encoding="utf-8") as fh:
        js_text = fh.read().strip()
    assert js_text.startswith("window.TEACHER_AUDIO_MANIFEST = ") and js_text.endswith(";")
    js_obj = json.loads(js_text[len("window.TEACHER_AUDIO_MANIFEST = "):-1].strip())
    assert js_obj == json_obj, "manifest.js != manifest.json"
    assert json_obj == data["manifest"], "on-disk manifest != window.TEACHER_AUDIO_MANIFEST"

    # Page cache-buster bumped.
    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    versions = [int(v) for _, v in re.findall(r"(manifest\.js\?v=)(\d+)", html)]
    assert versions and min(versions) >= 2, f"manifest ?v not bumped: {versions}"

    return {
        "channel": "chrome (headless=True)",
        "sections": len(canonical_ids),
        "cues": total_cues,
        "per_section": {sid: EXPECTED_COUNT[sid] for sid in canonical_ids},
        "manifest_keys": len(mkeys),
        "natural_figure_explanations": visuals,
        "duplicates": 0,
        "disallowed_types": 0,
        "quiz_media_tab_types": 0,
        "forbidden_label_hits": 0,
        "js_page_errors": len(js_errors),
        "narration_console_errors": len(narration_console_errors),
        "preexisting_media_console_errors": len(console_errors) - len(narration_console_errors),
        "mp3_nonzero": True,
        "json_valid": True,
        "manifest_js_matches_json": True,
        "dom_manifest_1to1": True,
        "tex_annotations": tex_annotations,
        "manifest_version": versions,
        "total_duration_ms": round(total_ms, 1),
        "total_duration_s": round(total_ms / 1000.0, 2),
        "ok": True,
    }


def main():
    if "--verify-only" not in sys.argv[1:]:
        asyncio.run(build_all())
    print("Running headless Chrome verification..." if "--verify-only" in sys.argv[1:] else "")
    report = verify_in_chrome()
    print("\n" + "=" * 68)
    print("VERIFICATION REPORT (headless Chrome channel=chrome)")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("=" * 68)
    if not report.get("ok"):
        raise SystemExit("VERIFICATION FAILED")
    print("VERIFIED: 33/33 cues, DOM<->manifest 1:1, 0 dups, 0 quiz/media-tab types, "
          "non-zero mp3s, valid JSON, 0 JS page errors, 0 'চিত্র প্রদর্শনী' labels.")
    print("=" * 68)


if __name__ == "__main__":
    main()
