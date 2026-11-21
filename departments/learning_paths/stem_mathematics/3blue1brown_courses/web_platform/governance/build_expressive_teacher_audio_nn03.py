# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Neural Networks Lesson 03
("What is backpropagation really doing?", Bengali) to the gold standard.

Deterministic, re-runnable, self-contained:

  * 26 cues in 5 narrated sections with EXACTLY the same section IDs,
    audio_file names, cue types and cue order as the LIVE DOM (extracted with
    the narration engine's own selector, including KaTeX <annotation> nodes).
    The seven data-no-narration sections (sec-overview, sec-official-deep-dive,
    sec-sgd-conclusion, sec-media-gallery, sec-lab, sec-quizzes, sec-reference)
    are NOT included.
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time), so the build is fully reproducible.
  * Figure cues are genuine 2-4 sentence natural Bengali explanations; the
    artificial label "চিত্র প্রদর্শনী" is explicitly forbidden and checked.
    The three occurrences present in the old manifest are eliminated.
  * Phonetic safeguards: 13,002 -> "তের হাজার দুই", 784 -> "সাত আট চার",
    gradient -> "গ্রেডিয়েন্ট", eta -> "ইটা", backpropagation -> "ব্যাকপ্রপাগেশন",
    nabla C / gradient of C -> "গ্রেডিয়েন্ট অব সি".
    No TeX, Latin letters, backslashes, braces, brackets, em/en dashes or
    raw hyphens reach the TTS engine.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, chapter-quote -3%, p +2%, figure -4%, callout +0%,
      formula-box -8%, code-showcase -4%, conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with
    exact-ms timings and the exact existing section keys (no added aliases).
  * Bumps the live page's manifest.js cache-buster to the next version.
  * Verifies with headless Chrome (channel=chrome): 26/26 cues, DOM <-> manifest
    1:1 parity, 0 duplicates, 0 quiz/media-tab cue types, non-zero mp3s, valid
    JSON, 0 page errors (uncaught JS exceptions), 0 narration-audio resource
    failures and 0 occurrences of "চিত্র প্রদর্শনী". Pre-existing media loads
    (a blocked YouTube iframe and a media-vault .mp4 absent in this workspace)
    are classified separately.

Usage:
    python governance/build_expressive_teacher_audio_nn03.py            # build + verify
    python governance/build_expressive_teacher_audio_nn03.py --verify-only
"""

import os
import re
import json
import sys
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
                         "neural_networks", "lesson_03")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "neural_networks", "lesson_03.html")
MANIFEST_TITLE = "অধ্যায় ০৩ — ব্যাকপ্রপাগেশন আসলে কী?"

# Prosody keyed by cue type: (rate, pitch, volume)
PROSODY_DEFAULT = {
    "h2":             ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
    "h3":             ("-3%", "+0Hz", "+0%"),
    "chapter-quote":  ("-3%", "+0Hz", "+0%"),
    "p":              ("+2%", "+0Hz", "+0%"),   # natural teacher pace
    "figure":         ("-4%", "+0Hz", "+0%"),   # slower, considerate explanation
    "callout-purple": ("+0%", "+0Hz", "+0%"),
    "callout-blue":   ("+0%", "+0Hz", "+0%"),
    "callout-gold":   ("+0%", "+0Hz", "+0%"),
    "callout-green":  ("+0%", "+0Hz", "+0%"),
    "formula-box":    ("-8%", "+0Hz", "+0%"),   # slow and deliberate
    "code-showcase":  ("-4%", "+0Hz", "+0%"),
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")     # calm concluding prose

# Cue types the narration engine may emit (quiz / media-tab deliberately absent).
ALLOWED_CUE_TYPES = set(PROSODY_DEFAULT) | {"conclusion"}

# EXACT narrated section IDs, cue-type sequences and counts, taken from the
# LIVE DOM via: document.querySelectorAll('.article > section, article section')
# plus the engine's readable-node selector (KaTeX <annotation> nodes included).
# Order matters (DOM order).
EXPECTED_TYPES = {
    "sec-backprop-core-idea":      ["h2", "p", "p", "figure", "callout-purple"],
    "sec-single-example-wants":    ["h2", "p", "p", "p"],
    "sec-three-ways-to-nudge":     ["h2", "p", "p", "callout-blue", "figure", "p"],
    "sec-backprop-hidden-layers":  ["h2", "p", "p", "p", "callout-gold"],
    "sec-averaging-all-examples":  ["h2", "p", "figure", "p", "p", "callout-purple"],
}
EXPECTED_AUDIO_FILES = {
    "sec-backprop-core-idea":      "sec-backprop-core-idea.mp3",
    "sec-single-example-wants":    "sec-single-example-wants.mp3",
    "sec-three-ways-to-nudge":     "sec-three-ways-to-nudge.mp3",
    "sec-backprop-hidden-layers":  "sec-backprop-hidden-layers.mp3",
    "sec-averaging-all-examples":  "sec-averaging-all-examples.mp3",
}
EXPECTED_COUNT = {sid: len(t) for sid, t in EXPECTED_TYPES.items()}
NON_NARRATED = [
    "sec-overview", "sec-official-deep-dive", "sec-sgd-conclusion",
    "sec-media-gallery", "sec-lab", "sec-quizzes", "sec-reference",
]

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (26 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-backprop-core-idea": {
        "title": "শেখার ইঞ্জিন: গ্রেডিয়েন্ট ভেক্টরের পেছনের রহস্য",
        "audio_file": "sec-backprop-core-idea.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, শেখার ইঞ্জিন, গ্রেডিয়েন্ট ভেক্টরের পেছনের রহস্য।"},
            {"index": 1, "type": "p",
             "tts": "আগের অধ্যায়ে আমরা দেখেছি গ্রেডিয়েন্ট ডিসেন্ট কীভাবে কস্ট ফাংশনের ঢাল মেপে মেপে নেটওয়ার্কের ভুল কমিয়ে আনে। কিন্তু সেই পদক্ষেপ নিতে হলে আমাদের জানতে হবে প্রতিটি ওজন আর বায়াসকে সামান্য নাড়ালে মোট কস্ট ঠিক কতটা বদলায়। সেই সংবেদনশীলতার তালিকাটিই হলো গ্রেডিয়েন্ট ভেক্টর, যাকে লেখা হয় গ্রেডিয়েন্ট অব সি।"},
            {"index": 2, "type": "p",
             "tts": "আমাদের হস্তাক্ষর শনাক্তকারী নেটওয়ার্কে মোট তের হাজার দুইটি প্যারামিটার রয়েছে। জটিল বহুমাত্রিক ক্যালকুলাসের সমীকরণে হারিয়ে যাওয়ার আগে আসুন একটা সহজ মানবিক দৃষ্টিকোণ থেকে ব্যাকপ্রপাগেশনকে অনুভব করি। ক্যালকুলাসের সূত্র ছাড়াই ব্যাকপ্রপাগেশন আসলে কী করে, সেটাই আমরা দেখব।"},
            {"index": 3, "type": "figure",
             "tts": "চিত্রে ইনপুট লেয়ারের সাত আট চারটি নিউরন থেকে শুরু করে দুটি হিডেন লেয়ার হয়ে আউটপুটের দশটি নিউরন পর্যন্ত পথটি দেখানো হয়েছে। আউটপুট লেয়ারে আমরা যে পরিবর্তন চাইছি, সেই ইচ্ছাটি উল্টো দিকে অর্থাৎ হিডেন লেয়ার আর সংযোগকারী ওজনের দিকে ধাবিত হচ্ছে। চিত্রের তীরগুলো যেন বলে দেয় কোন নিউরনকে বাড়াতে হবে আর কোনটিকে কমাতে হবে। এই পেছনের দিকের যাত্রাটিই ব্যাকপ্রপাগেশনের হৃদয়।"},
            {"index": 4, "type": "callout-purple",
             "tts": "বিশেষ নোট, ব্যাকপ্রপাগেশনের মূল কথা। এটি এমন এক চতুর অ্যালগরিদম যা আউটপুট লেয়ার থেকে শুরু করে বিপরীত দিকে তথ্য প্রবাহিত করে প্রতিটি প্যারামিটারের জন্য সংবেদনশীলতা নির্ণয় করে। এক কথায়, ব্যাকপ্রপাগেশন আমাদের বলে দেয় তের হাজার দুইটি ডায়ালের প্রতিটিকে ঠিক কতটুকু আর কোন দিকে ঘুরাতে হবে।"},
        ],
    },

    "sec-single-example-wants": {
        "title": "আউটপুট লেয়ারকে নিখুঁত করার দাবি",
        "audio_file": "sec-single-example-wants.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, আউটপুট লেয়ারকে নিখুঁত করার দাবি।"},
            {"index": 1, "type": "p",
             "tts": "কল্পনা করুন, নেটওয়ার্কে আমরা হাতের লেখা একটা দুইয়ের ছবি দিয়েছি। আউটপুট লেয়ারে আছে দশটি নিউরন, শূন্য থেকে নয় পর্যন্ত। যেহেতু ছবিটি দুইয়ের, তাই দুই নম্বর নিউরনের মান বেড়ে এক হওয়া উচিত, আর বাকি নয়টির মান শূন্যে নেমে আসা উচিত।"},
            {"index": 2, "type": "p",
             "tts": "কিন্তু এখনো অপ্রশিক্ষিত নেটওয়ার্কে ধরা যাক দুই নম্বর নিউরনের মান এসেছে শূন্য দশমিক দুই, আর ভুল করে আট নম্বর নিউরনের মান হয়ে গেছে শূন্য দশমিক আট। তাই এই একক ছবিটির জন্য কস্ট কমাতে হলে দুই নম্বর নিউরনকে উপরে তুলতে হবে আর আট নম্বর নিউরনকে নিচে নামাতে হবে।"},
            {"index": 3, "type": "p",
             "tts": "এখানে পরিবর্তনের মাত্রা একেবারে গুরুত্বপূর্ণ। আট নম্বর নিউরনটি ভয়াবহ ভুল দেখাচ্ছে, শূন্য দশমিক আট এসেছে অথচ শূন্য হওয়া উচিত ছিল, তাই তাকে নামানোর দাবি তীব্র। অন্যদিকে যে নিউরন ইতোমধ্যে শূন্য দশমিক শূন্য পাঁচে বসে আছে, তাকে কমানোর তাগিদ তুলনামূলকভাবে মৃদু। অর্থাৎ প্রতিটি নিউরনের চাওয়ার তীব্রতা তার ভুলের মাত্রার সমানুপাতিক।"},
        ],
    },

    "sec-three-ways-to-nudge": {
        "title": "ওজন, পূর্ববর্তী অ্যাক্টিভেশন আর বায়াসের ভূমিকা",
        "audio_file": "sec-three-ways-to-nudge.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, ওজন, পূর্ববর্তী অ্যাক্টিভেশন আর বায়াসের ভূমিকা।"},
            {"index": 1, "type": "p",
             "tts": "এখন প্রশ্ন হলো, দুই নম্বর আউটপুট নিউরনের অ্যাক্টিভেশন আমরা কীভাবে বাড়াব? মনে করে দেখুন, এই নিউরনের মান ঠিক হয়েছে তার আগের লেয়ারের নিউরনগুলোর ওয়েটেড সমষ্টি আর একটি সিগময়েড ফাংশন দিয়ে। সেই সমষ্টির ভেতরে আছে প্রতিটি সংযোগের ওজন, পূর্ববর্তী নিউরনের অ্যাক্টিভেশন আর একটা বায়াস।"},
            {"index": 2, "type": "p",
             "tts": "যেহেতু সিগময়েড একমুখী বর্ধিষ্ণু ফাংশন, তাই অ্যাক্টিভেশন বাড়াতে হলে ভেতরের ওয়েটেড সমষ্টিটাও বাড়াতে হবে। আর এই সমষ্টি বাড়ানোর জন্য আমাদের হাতে ঠিক তিনটি রাস্তা আছে। বায়াস বদলানো, ওজন বদলানো, অথবা পূর্ববর্তী লেয়ারের অ্যাক্টিভেশন বদলানো।"},
            {"index": 3, "type": "callout-blue",
             "tts": "বিশেষ নোট, তিনটি নিয়ন্ত্রক লিভার। প্রথমত বায়াস বাড়ালে সবার জন্য সীমারেখা সহজ হয়ে যায়। দ্বিতীয়ত যে পূর্ববর্তী নিউরনগুলো ইতোমধ্যে উজ্জ্বলভাবে জ্বলজ্বল করছে, তাদের সংযোগকারী ওজন বাড়ালে সমষ্টি সবচেয়ে দ্রুত বৃদ্ধি পায়। তৃতীয়ত ধনাত্মক ওজনের সাথে যুক্ত নিউরনগুলোকে আরও উজ্জ্বল আর ঋণাত্মক ওজনের নিউরনগুলোকে নিভিয়ে দেওয়া যায়।"},
            {"index": 4, "type": "figure",
             "tts": "এই ছবিতে আগের লেয়ারের একটি নিউরন প্রায় শূন্য দশমিক নয় মানে উজ্জ্বল হয়ে আছে, আর অন্য একটি নিভে আছে। পাশের ছোট্ট সূত্রটি মনে করিয়ে দেয় যে ওজনের সামান্য পরিবর্তনের ফলাফল অ্যাক্টিভেশনের মানের সমান, অর্থাৎ ডি জেড সমান এ গুণ ডি ডব্লিউ। তাই যে সংযোগের অ্যাক্টিভেশন বেশি, সেটিকে নাড়ালেই সবচেয়ে বেশি লাভ হয়। অন্যদিকে যার মান শূন্যের কাছে, তার ওজন যতই বদলানো হোক কিছুই পরিবর্তন হয় না।"},
            {"index": 5, "type": "p",
             "tts": "এখানে একটা গভীর সত্য লক্ষ্য করুন। যে নিউরনটি সক্রিয় ছিল না, অর্থাৎ তার মান প্রায় শূন্য, তার সাথে যুক্ত ওজনকে যতই নাড়াচাড়া করুন না কেন, শূন্যের সাথে গুণ করলে ফল শূন্যই থাকে। তাই কস্টের ওপর তার কোনো প্রভাব পড়ে না। যে নিউরনগুলো সবচেয়ে বেশি প্রজ্জ্বলিত, তাদের সংশ্লিষ্ট ওজনগুলোই সবচেয়ে বেশি পরিবর্তনের দাবি পায়।"},
        ],
    },

    "sec-backprop-hidden-layers": {
        "title": "গণতান্ত্রিক চাহিদা আর পেছনের স্তরে সংকেত প্রেরণ",
        "audio_file": "sec-backprop-hidden-layers.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, গণতান্ত্রিক চাহিদা আর পেছনের স্তরে সংকেত প্রেরণ।"},
            {"index": 1, "type": "p",
             "tts": "আউটপুট লেয়ারের প্রতিটি নিউরন কেবল নিজের ওজন আর বায়াস বদলানোর ইচ্ছা পোষণ করেই থেমে থাকে না। তারা প্রত্যেকেই পূর্ববর্তী হিডেন লেয়ারের নিউরনগুলোর কাছে নিজস্ব চাওয়া পাঠায়, যেন বলে হে নিউরন, তুমি একটু বেশি জ্বলো, অথবা তুমি একটু নিভে যাও।"},
            {"index": 2, "type": "p",
             "tts": "হিডেন লেয়ারের একটি নির্দিষ্ট নিউরনের কথা ভাবুন। আউটপুট লেয়ারের দশটি ভিন্ন নিউরন প্রত্যেকেই তার ওপর বিপরীতমুখী টান তৈরি করতে পারে। দুই নম্বর নিউরন হয়তো চায় সেটি বাড়ুক, আবার আট নম্বর নিউরন হয়তো চায় সেটি কমুক।"},
            {"index": 3, "type": "p",
             "tts": "এইভাবে সমস্ত আউটপুট নিউরনের ইচ্ছাগুলোর একটা ভরযুক্ত সমষ্টি নিয়েই হিডেন লেয়ারের প্রতিটি নিউরনের নিজস্ব কাঙ্ক্ষিত পরিবর্তন ঠিক হয়। আর যেই মুহূর্তে সেই পরিবর্তন জানা হয়ে যায়, আমরা হুবহু একই যুক্তি প্রয়োগ করে তার পেছনের হিডেন লেয়ারে এবং সেখানকার সংযোগকারী ওজনে প্রবেশ করতে পারি। এইভাবে এক স্তর থেকে আরেক স্তরে ইচ্ছাগুলো পিছিয়ে চলে।"},
            {"index": 4, "type": "callout-gold",
             "tts": "বিশেষ নোট, কেন এর নাম ব্যাকপ্রপাগেশন। কারণ ভুলের প্রতিক্রিয়া আর চাওয়াগুলো সামনে থেকে পেছনের দিকে, অর্থাৎ আউটপুট থেকে হিডেন লেয়ার হয়ে তার আগের স্তর পর্যন্ত ঢেউয়ের মতো ধারাবাহিকভাবে ছড়িয়ে পড়ে। সেই পেছনের দিকের প্রবাহটিই এর নামের অর্থ।"},
        ],
    },

    "sec-averaging-all-examples": {
        "title": "একক উদাহরণ থেকে ষাট হাজার ডেটাপয়েন্টের ঐকমত্য",
        "audio_file": "sec-averaging-all-examples.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, একক উদাহরণ থেকে ষাট হাজার ডেটাপয়েন্টের ঐকমত্য।"},
            {"index": 1, "type": "p",
             "tts": "এতক্ষণ আমরা যে পুরো ব্যাকপ্রপাগেশন প্রক্রিয়া দেখলাম, তা শুধু একটি একক হাতের লেখা ছবির জন্য। সেই ছবি নেটওয়ার্কের প্রতিটি ওজনকে বলে দিয়েছে, আমাকে চিনতে হলে তোমাকে অমুক দিকে একটু নড়তে হবে। কিন্তু একটি মাত্র ছবির চাওয়া দিয়ে পুরো নেটওয়ার্ক ঠিক করা যাবে না।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে একাধিক সংখ্যার ছবি পাশাপাশি দেখানো হয়েছে, যেমন দুই, সাত, চার আর নয়। প্রতিটি ছবি নিজস্ব ভাষায় ওজনগুলোকে আলাদা আলাদা নির্দেশ দিচ্ছে, কখনো বাড়াতে বলছে আবার কখনো কমাতে। ওই সব আলাদা মতের গড় নিলে আমরা পাই একটি সম্মিলিত পরামর্শ, যাকে লেখা হয় নেতিবাচক গ্রেডিয়েন্ট। সেই একক পরামর্শই শেষ পর্যন্ত প্রতিটি ডায়ালের চলার দিক নির্ধারণ করে।"},
            {"index": 3, "type": "p",
             "tts": "বাস্তব প্রশিক্ষণে আমাদের কাছে ষাট হাজারটি ছবি আছে। একটি দুইয়ের ছবি যে ওজনকে বাড়াতে বলবে, হয়তো একটি সাতের ছবি সেই একই ওজনকে সামান্য কমাতে বলবে। ব্যাকপ্রপাগেশন প্রতিটি উদাহরণের জন্য তের হাজার দুইটি প্যারামিটারের প্রস্তাবিত পরিবর্তনগুলো হিসাব করে, আর শেষে তাদের সবার গাণিতিক গড় নেয়।"},
            {"index": 4, "type": "p",
             "tts": "এই গড় পরিবর্তনের ভেক্টরটিই হলো আমাদের কাঙ্ক্ষিত নেতিবাচক গ্রেডিয়েন্ট। গাণিতিকভাবে বললে, কোনো ওজনের সাপেক্ষে কস্টের অংশবিশেষের অন্তরজ হলো সকল উদাহরণের অন্তরজের গড়। এই গড় অনুযায়ী সমস্ত ডায়ালকে একসাথে এক কদম ঘুরিয়ে দিলে নেটওয়ার্ক সামগ্রিকভাবে একটু বেশি নিখুঁত হয়।"},
            {"index": 5, "type": "callout-purple", "role": "conclusion",
             "tts": "বিশেষ নোট, মিনি ব্যাচ আর বাস্তব কম্পিউটেশন। ষাট হাজার উদাহরণের দীর্ঘ অপেক্ষার বদলে আমরা বত্রিশ বা চৌষট্টি ছবির মিনি ব্যাচের গড় নিয়ে প্রতিটি পদক্ষেপ দ্রুত সম্পন্ন করি। সেই গড় প্রস্তাবকে লার্নিং রেট ইটা দিয়ে ছোট করে আমরা প্রতিটি ওজনে প্রয়োগ করি। পরবর্তী অধ্যায়ে ক্যালকুলাসের চেইন রুল ব্যবহার করে এই দাবিগুলোর হুবহু গাণিতিক প্রমাণ দেখব।"},
        ],
    },
}

# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"
REQUIRED_PHONETIC = {
    "তের হাজার দুই": "13,002 safeguard",
    "সাত আট চার": "784 safeguard",
    "গ্রেডিয়েন্ট": "gradient safeguard",
    "ইটা": "eta safeguard",
    "ব্যাকপ্রপাগেশন": "backpropagation safeguard",
    "গ্রেডিয়েন্ট অব সি": "nabla-C / gradient-of-C safeguard",
}


def assert_clean_scripts():
    """Fail before any TTS work if a script still contains markup or Latin text."""
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars {bad!r} in {cue['tts']!r}")
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: artificial figure label present")
            if cue["type"] not in PROSODY_DEFAULT:
                raise ValueError(f"{sec_id} cue {cue['index']}: unknown cue type {cue['type']!r}")

    # Every phonetic safeguard must actually be exercised somewhere.
    joined = "\n".join(c["tts"] for s in SECTIONS_DATA.values() for c in s["cues"])
    for token, label in REQUIRED_PHONETIC.items():
        if token not in joined:
            raise ValueError(f"Missing phonetic {label}: {token!r}")

    # Structural parity guards against the LIVE DOM.
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
        if len(indices) != EXPECTED_COUNT[sec_id]:
            raise ValueError(f"{sec_id}: expected {EXPECTED_COUNT[sec_id]} cues")
        total += len(indices)
    if total != 26:
        raise ValueError(f"Expected 26 cues, found {total}")

    # Figure cues must be genuine 2-4 sentence explanations (never a label).
    fig_count = 0
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            if cue["type"] == "figure":
                fig_count += 1
                sentences = [s for s in cue["tts"].split("।") if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(f"{sec_id} cue {cue['index']}: figure has {len(sentences)} sentences")
    if fig_count != 3:
        raise ValueError(f"Expected 3 figure explanations, found {fig_count}")


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
            print(f"  cue {idx:02d} [{cue['type']:<15}] {rate:>4} {pitch:>5}  {cue['tts'][:30]}...")
            await synth_cue(cue["tts"], chunk, rate, pitch, volume)
        else:
            print(f"  cue {idx:02d} [{cue['type']:<15}] cached")
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
          f"in {len(SECTIONS_DATA)} sections.")

    manifest_sections = {}
    for sec_id, sec in SECTIONS_DATA.items():
        manifest_sections[sec_id] = await build_section(sec_id, sec)

    manifest_data = {
        "course": "neural_networks",
        "lesson": "lesson_03",
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
    expected_keys = set(SECTIONS_DATA)
    assert set(loaded["sections"]) == expected_keys
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
    assert total_cues == 26
    assert figures == 3

    print("\n" + "=" * 70)
    print("BUILD COMPLETE - expressive teacher audio, Neural Networks Lesson 03")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<34} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTIONS_DATA)} sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json is valid JSON; all 5 mp3 files exist and are non-empty.")
    print("=" * 70)


# --------------------------------------------------------------------------- #
# Headless Chrome verification (channel=chrome)
# --------------------------------------------------------------------------- #
VERIFY_JS = r"""() => {
  const ne = window.narrationEngine;
  const manifest = window.TEACHER_AUDIO_MANIFEST;
  const sectionEls = [...document.querySelectorAll('.article > section, article section')];

  // Re-extract DOM blocks with the narration engine's own selector, mapping a
  // rendered node to the same cue type the manifest uses. KaTeX <annotation>
  // nodes are collected too, proving the DOM was read with annotation support.
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
    audioFile: s.audioFile,
    types: s.blocks.map(b => domType(b.element))
  }));

  return {
    manifestPresent: !!manifest,
    hasStudioAudio: !!ne.hasStudioAudio,
    manifestKeys: Object.keys(manifest ? manifest.sections : {}),
    manifest: manifest,
    dom: dom.map(s => ({id: s.id, types: s.blocks.map(b => b.type),
                        tex: s.blocks.flatMap(b => b.tex),
                        texCount: s.blocks.reduce((n, b) => n + b.tex.length, 0)})),
    engine,
    sectionEls: sectionEls.map(s => ({id: s.id, noNarration: s.getAttribute('data-no-narration')}))
  };
}"""


def verify_in_chrome():
    """Return a verification report dict; raises AssertionError on failure."""
    from pathlib import Path
    from playwright.sync_api import sync_playwright

    page_uri = Path(PAGE_PATH).as_uri()
    report = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page()
        page_errors = []
        console_errors = []
        failed_requests = []
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.on("requestfailed", lambda r: failed_requests.append((r.url, r.failure)))
        page.goto(page_uri, wait_until="load")
        page.wait_for_function(
            "() => !!window.narrationEngine && !!window.narrationEngine.sections "
            "&& window.narrationEngine.sections.length > 0 "
            "&& !!window.TEACHER_AUDIO_MANIFEST")
        data = page.evaluate(VERIFY_JS)
        browser.close()

    # "Page errors" strictly means uncaught JS exceptions (pageerror). Network
    # resource-load failures are classified separately: this page ships a
    # <video> pointing at a media-vault .mp4 absent in this workspace and a
    # YouTube iframe that Chrome blocks in headless offline runs. Neither is
    # part of the teacher-narration build, BUT any failed manifest/audio
    # resource still fails verification.
    BENIGN_FAILED = ("youtube.com/embed/", "3b1b_nn_03_full_dubbed.mp4")
    AUDIO_FAILED = ("manifest.js", ".mp3", "TEACHER_AUDIO")
    benign_failed = [u for u, _ in failed_requests if any(k in u for k in BENIGN_FAILED)]
    unexpected_failed = [(u, f) for u, f in failed_requests if u not in benign_failed]
    audio_failed = [u for u, _ in failed_requests if any(k in u for k in AUDIO_FAILED)]
    unexpected_console = [c for c in console_errors
                          if not c.startswith("Failed to load resource:")]
    resource_console = [c for c in console_errors
                        if c.startswith("Failed to load resource:")]

    assert page_errors == [], f"Page errors: {page_errors}"
    assert not audio_failed, f"Narration audio resource failed to load: {audio_failed}"
    assert not unexpected_failed, f"Unexpected failed requests: {unexpected_failed}"
    assert not unexpected_console, f"Unexpected console errors: {unexpected_console}"
    assert data["manifestPresent"], "window.TEACHER_AUDIO_MANIFEST missing"
    assert data["hasStudioAudio"], "Studio teacher audio not bound"

    # Section keys 1:1 with the DOM/engine, no extras, no non-narrated sections.
    mkeys = data["manifestKeys"]
    dom_ids = [s["id"] for s in data["dom"]]
    assert mkeys == dom_ids, f"Manifest/DOM section mismatch: {mkeys} vs {dom_ids}"
    assert mkeys == list(EXPECTED_TYPES.keys()), f"Unexpected section keys: {mkeys}"
    for sid in NON_NARRATED:
        assert sid not in mkeys, f"Non-narrated section leaked into manifest: {sid}"
        lab = [s for s in data["sectionEls"] if s["id"] == sid]
        assert lab and lab[0]["noNarration"] == "true", f"{sid} lost data-no-narration"

    # DOM <-> manifest 1:1: section ids, cue counts and cue type order.
    tsections = data["manifest"]["sections"]
    total_cues = 0
    dup_check = set()
    disallowed = set()
    forbidden_hits = []
    total_ms = 0.0
    figure_count = 0
    tex_total = 0
    for sec_id in EXPECTED_TYPES:
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
        assert eng_sec["audioFile"].endswith(EXPECTED_AUDIO_FILES[sec_id]), (sec_id, eng_sec["audioFile"])

        tex_total += dom_sec["texCount"]

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

        # Audio file exists and is non-zero.
        af = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(af) and os.path.getsize(af) > 0, af
        total_ms += msec["total_duration_ms"]

    assert total_cues == 26, total_cues
    assert figure_count == 3, figure_count
    assert not disallowed, f"Disallowed cue types: {disallowed}"
    assert not forbidden_hits, f"Artificial figure label found: {forbidden_hits}"
    assert tex_total > 0, "No KaTeX <annotation> nodes were extracted from the DOM"

    # No quiz / media-tab anywhere in the narrated manifest or DOM cue types.
    all_dom_types = [t for s in data["dom"] for t in s["types"]]
    assert not ({"quiz", "media-tab", "b1b-quiz", "b1b-media-tab",
                 "quiz-block", "media-tab-caption"} & set(all_dom_types)), all_dom_types

    # manifest.js payload must equal manifest.json.
    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        json_obj = json.load(fh)
    with open(os.path.join(AUDIO_DIR, "manifest.js"), encoding="utf-8") as fh:
        js_text = fh.read().strip()
    assert js_text.startswith("window.TEACHER_AUDIO_MANIFEST = ") and js_text.endswith(";")
    js_obj = json.loads(js_text[len("window.TEACHER_AUDIO_MANIFEST = "):-1].strip())
    assert js_obj == json_obj, "manifest.js != manifest.json"

    # Page cache-buster bumped (must be >= 2 after a build).
    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    versions = [int(v) for _, v in re.findall(r"(manifest\.js\?v=)(\d+)", html)]
    assert versions and min(versions) >= 2, f"manifest ?v not bumped: {versions}"

    report.update({
        "channels": "channel=chrome, headless=True",
        "sections": len(EXPECTED_TYPES),
        "cues": total_cues,
        "per_section": {sid: EXPECTED_COUNT[sid] for sid in EXPECTED_TYPES},
        "figures": figure_count,
        "duplicates": 0,
        "disallowed_types": 0,
        "forbidden_label_hits": 0,
        "page_errors": len(page_errors),
        "failed_audio_resources": len(audio_failed),
        "unexpected_failed_requests": len(unexpected_failed),
        "unexpected_console_errors": len(unexpected_console),
        "resource_console_errors": len(resource_console),
        "pre_existing_media_loads": sorted(set(benign_failed)),
        "total_duration_ms": round(total_ms, 1),
        "total_duration_s": round(total_ms / 1000.0, 2),
        "tex_annotations": tex_total,
        "manifest_js_matches_json": True,
        "manifest_version": versions,
        "ok": True,
    })
    return report


def main():
    verify_only = "--verify-only" in sys.argv[1:]
    if verify_only:
        print("Running headless Chrome verification only...")
    else:
        asyncio.run(build_all())
    report = verify_in_chrome()
    print("\n" + "=" * 70)
    print("VERIFICATION REPORT (headless Chrome channel=chrome)")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("=" * 70)
    if not report.get("ok"):
        raise SystemExit("VERIFICATION FAILED")
    print("VERIFIED: 26/26 cues, DOM<->manifest 1:1, 0 dups, "
          "0 quiz/media-tab types, non-zero mp3s, valid JSON, 0 page errors "
          "(uncaught JS), 0 failed audio resources, 0 'চিত্র প্রদর্শনী'.")


if __name__ == "__main__":
    main()
