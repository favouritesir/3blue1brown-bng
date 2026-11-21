# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Neural Networks Lesson 02
("Gradient descent, how neural networks learn", Bengali) to the gold standard.

Deterministic, re-runnable, self-contained:

  * 32 cues in 6 narrated sections with EXACTLY the same section IDs,
    audio_file names, cue types and cue order as the LIVE DOM (extracted with
    the narration engine's own selector, including KaTeX <annotation> nodes).
    The three data-no-narration sections (sec-official-recap,
    sec-official-gallery, sec-practice-lab) are NOT included.
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time), so the build is fully reproducible.
  * Figure cues are genuine 2-4 sentence natural Bengali explanations; the
    artificial label "চিত্র প্রদর্শনী" is explicitly forbidden and checked.
  * Phonetic safeguards: 13,002 -> "তের হাজার দুই", 784 -> "সাত আট চার",
    gradient -> "গ্রেডিয়েন্ট", eta -> "ইটা",
    gradient of C / nabla C -> "গ্রেডিয়েন্ট অব সি".
    No TeX, Latin letters, backslashes, braces, brackets, em/en dashes or
    raw hyphens reach the TTS engine.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, chapter-quote -3%, p +2%, figure -4%, callout +0%,
      formula-box -8%, conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with
    exact-ms timings and the exact existing section keys (no added aliases).
  * Bumps the live page's manifest.js cache-buster to the next version.
  * Verifies with headless Chrome (channel=chrome): 32/32 cues, DOM <-> manifest
    1:1 parity, 0 duplicates, 0 quiz/media-tab cue types, non-zero mp3s, valid
    JSON, 0 page errors (uncaught JS exceptions) and 0 occurrences of
    "চিত্র প্রদর্শনী". Pre-existing media resource loads (a blocked YouTube
    iframe and a media-vault .mp4 that is absent in this workspace) are
    classified separately; any failed narration-audio/manifest resource still
    fails verification.

Usage:
    python governance/build_expressive_teacher_audio_nn02.py            # build + verify
    python governance/build_expressive_teacher_audio_nn02.py --verify-only
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
                         "neural_networks", "lesson_02")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "neural_networks", "lesson_02.html")
MANIFEST_TITLE = "অধ্যায় ০২ — গ্রেডিয়েন্ট ডিসেন্ট: নিউরাল নেটওয়ার্ক কীভাবে শেখে"

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
    "formula-box":    ("-8%", "+0Hz", "+0%"),   # slow and deliberate
    "code-showcase":  ("-4%", "+0Hz", "+0%"),
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")     # calm concluding prose

# Cue types the narration engine may emit (quiz / media-tab deliberately absent).
ALLOWED_CUE_TYPES = set(PROSODY_DEFAULT) | {"conclusion"}

# EXACT narrated section IDs, cue-type sequences and counts, taken from the
# LIVE DOM via: document.querySelectorAll('.article > section, article section')
# plus the engine's readable-node selector. Order matters (DOM order).
EXPECTED_TYPES = {
    "sec-learning-paradox":        ["h2", "p", "p", "figure", "callout-purple"],
    "sec-cost-function":           ["h2", "p", "p", "p", "p", "callout-blue"],
    "sec-gradient-descent-intuition": ["h2", "p", "figure", "p", "p", "figure"],
    "sec-multivariable-gradient":  ["h2", "p", "p", "callout-gold", "p", "p"],
    "sec-learning-rate-landscape": ["h2", "p", "figure", "p"],
    "sec-mini-batch-sgd":          ["h2", "p", "p", "p", "callout-purple"],
}
EXPECTED_AUDIO_FILES = {
    "sec-learning-paradox":           "sec-learning-paradox.mp3",
    "sec-cost-function":              "sec-cost-function.mp3",
    "sec-gradient-descent-intuition": "sec-gradient-descent-intuition.mp3",
    "sec-multivariable-gradient":     "sec-multivariable-gradient.mp3",
    "sec-learning-rate-landscape":    "sec-learning-rate-landscape.mp3",
    "sec-mini-batch-sgd":             "sec-mini-batch-sgd.mp3",
}
EXPECTED_COUNT = {sid: len(t) for sid, t in EXPECTED_TYPES.items()}
NON_NARRATED = ["sec-official-recap", "sec-official-gallery", "sec-practice-lab"]

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (32 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-learning-paradox": {
        "title": "১৩,০০২টি ডায়ালকে টিউন করার বাস্তব সমস্যা",
        "audio_file": "sec-learning-paradox.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, তের হাজার দুইটি ডায়ালকে টিউন করার বাস্তব সমস্যা।"},
            {"index": 1, "type": "p",
             "tts": "প্রথম অধ্যায়ে আমরা দেখেছি কীভাবে হস্তাক্ষর ডিজিট শনাক্ত করতে একটি ক্লাসিক মাল্টিলেয়ার পারসেপট্রন আর্কিটেকচার গড়ে তোলা হয়। আঠাইশ গুণ আঠাইশ পিক্সেলের ইনপুটে সাত আট চারটি নিউরন, দুটি ষোলো নিউরনের হিডেন লেয়ার এবং আউটপুটে দশটি নিউরন। সেখানে সংযোগকারী ওজন বারো হাজার নয়শো ষাটটি আর বায়াস বিয়াল্লিশটি, অর্থাৎ মোট তের হাজার দুইটি পরিবর্তনযোগ্য প্যারামিটার বা স্বাধীন ডায়াল।"},
            {"index": 2, "type": "p",
             "tts": "শুরুতে যখন এই সমস্ত ওজন ও বায়াস এলোমেলোভাবে মান ধারণ করে, তখন নেটওয়ার্কের কার্যকারিতা একেবারেই হতাশাজনক হয়। একটি তিনের ছবি দিলে হয়তো আউটপুটে আট বা পাঁচ নম্বর নিউরনটি জ্বলে ওঠে, আবার কখনো সমস্ত আউটপুটই আবর্জনার মতো একই রকম মান দেখায়। প্রশ্ন হলো, কম্পিউটার কীভাবে নিজে নিজে এই তের হাজার দুইটি নব এমন নিখুঁতভাবে ঘুরিয়ে নেবে যেন যেকোনো হাতের লেখা সঠিক নির্ভুলতায় চেনা যায়?"},
            {"index": 3, "type": "figure",
             "tts": "বাঁ দিকের ছবিতে এলোমেলো ওজন ও বায়াসে শেষ স্তরের দশটি নিউরন প্রায় একই রকম অগোছালো মান দিচ্ছে, ফলে তিনটিকে চেনাও সম্ভব হচ্ছে না। ডান দিকে প্রশিক্ষিত নেটওয়ার্কে তিন সূচকের নিউরনটি সুস্পষ্টভাবে উজ্জ্বল আর বাকিরা নিভে গেছে। এই দুই অবস্থার তুলনাটিই বোঝায় কেন প্রথমে কতটা ভুল হচ্ছে সেটা মাপার একটা ব্যবস্থা দরকার। সেই মাপ না থাকলে ওজন ঠিক করার কোনো লক্ষ্যই থাকবে না।"},
            {"index": 4, "type": "callout-purple",
             "tts": "বিশেষ নোট, শেখার মূল সংজ্ঞার্থ। ডিপ লার্নিংয়ে শেখা কোনো রহস্যময় ভাবাবেগ নয়, এটি নিরেট একটি গাণিতিক অপ্টিমাইজেশন প্রক্রিয়া। আমাদের এমন একটি ব্যবস্থা তৈরি করতে হবে যা নেটওয়ার্কের বর্তমান পারফরম্যান্সকে একটি একক সংখ্যায় পরিমাপ করে বলে দেবে, তুমি কতটা ভুল করছ।"},
        ],
    },

    "sec-cost-function": {
        "title": "স্কয়ার্ড এরর লস ও সামগ্রিক কস্ট",
        "audio_file": "sec-cost-function.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, স্কয়ার্ড এরর লস ও সামগ্রিক কস্ট।"},
            {"index": 1, "type": "p",
             "tts": "একটি একক ট্রেনিং উদাহরণের কথা ভাবুন। ধরুন ইনপুটে আমরা একটি তিনের ছবি দিয়েছি। কাঙ্ক্ষিত লক্ষ্য হলো তিন সূচকের আউটপুট নিউরনটির মান হবে এক, আর বাকি নয়টি নিউরনের মান হবে শূন্য। কিন্তু আমাদের আনট্রেইনড নেটওয়ার্ক প্রতিটি নিউরনে কোনো না কোনো বিভ্রান্তিকর মান দিচ্ছে, যাকে আমরা বলছি এ জে।"},
            {"index": 2, "type": "p",
             "tts": "আমরা প্রতিটি আউটপুট নিউরনের প্রাপ্ত মান এ জে থেকে তার কাঙ্ক্ষিত মান ওয়াই জের পার্থক্য নিয়ে তাকে বর্গ করি, আর দশটি নিউরনের জন্য এই মানগুলো যোগ করি। একে বলা হয় একটি একক উদাহরণের স্কয়ার্ড এরর, অর্থাৎ বর্গকৃত ভুল। বর্গ নেওয়ার কারণে ধনাত্মক আর ঋণাত্মক ভুল একে অপরকে বাতিল না করে যোগ হয়, আর বড় ভুল ছোট ভুলের চেয়ে অনেক বেশি শাস্তি পায়।"},
            {"index": 3, "type": "p",
             "tts": "নেটওয়ার্ক যদি ছবিটিকে পুরোপুরি ভুল চিনে থাকে, তবে এই সমষ্টির মান অনেক বড় হয়। আর আত্মবিশ্বাসের সাথে সঠিক উত্তর দিলে মানটি শূন্যের অত্যন্ত কাছাকাছি নেমে আসে। কিন্তু কেবল একটি ছবির ভুল কমালেই চলবে না, আমাদের কাছে হস্তাক্ষরের ষাট হাজারটি লেবেলযুক্ত ট্রেনিং ছবি রয়েছে।"},
            {"index": 4, "type": "p",
             "tts": "পুরো ডেটাসেটের সমস্ত ট্রেনিং ছবির ভুলের গড় নিলে আমরা পাই সামগ্রিক কস্ট ফাংশন, যাকে লেখি সি অব ডব্লি কমা বি। প্রতিটি ছবির বর্গকৃত ভুলগুলোর গড় নেওয়া হয়, তাই সি হলো ওজন ডব্লি আর বায়াস বির ওপর নির্ভরশীল একটি ফাংশন। এই গড় নিশ্চিত করে যে একটি ছবিতে ভালো করে অন্য নব্বইটিতে খারাপ করে ফেললে চলবে না, লক্ষ্য হলো সবগুলোতেই গড়ে ভালো করা।"},
            {"index": 5, "type": "callout-blue",
             "tts": "বিশেষ নোট, ইনপুট বনাম ভ্যারিয়েবল। মনে রাখবেন, ট্রেনিং ডেটা অর্থাৎ ষাট হাজার ছবি ও লেবেল এখানে স্থির ধ্রুবক। কস্ট ফাংশনের আসল চলক হলো নেটওয়ার্কের সমস্ত ওজন ও বায়াস। অর্থাৎ সি হলো তের হাজার দুইটি চলকের একটি দানবীয় বাস্তব ফাংশন, যা তের হাজার দুই মাত্রার স্থান থেকে একটি একক বাস্তব সংখ্যায় নিয়ে যায়।"},
        ],
    },

    "sec-gradient-descent-intuition": {
        "title": "১ মাত্রা ও ২ মাত্রায় বল গড়িয়ে নামার দৃশ্যকল্প",
        "audio_file": "sec-gradient-descent-intuition.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, এক মাত্রা ও দুই মাত্রায় বল গড়িয়ে নামার দৃশ্যকল্প।"},
            {"index": 1, "type": "p",
             "tts": "তের হাজার দুই মাত্রার চিন্তা মানুষের মস্তিষ্কের পক্ষে অসম্ভব। তাই আসুন কল্পনাকে নামিয়ে আনি মাত্র একটি চলকের সাধারণ ফাংশন সি অব ডব্লিতে। আপনি যদি এই বক্ররেখার কোনো এক বিন্দুতে দাঁড়িয়ে থাকেন আর কস্ট কমাতে চান, তবে কোন দিকে যাবেন? কাছের স্পর্শকের ঢালই এই প্রশ্নের উত্তর দেয়।"},
            {"index": 2, "type": "figure",
             "tts": "এই লেখচিত্রে অনুভূমিক অক্ষে একটিমাত্র প্যারামিটার ডব্লি আর উল্লম্ব অক্ষে কস্ট সি অব ডব্লি দেখানো হয়েছে। বক্ররেখার যে বিন্দুতে আমরা দাঁড়িয়ে আছি, তার স্পর্শকের ঢালই বলে দেয় কোন দিকে গেলে কস্ট কমবে। ঢাল ঋণাত্মক হলে ডানে আর ধনাত্মক হলে বাঁয়ে পা দিতে হবে। লক্ষ্য করুন বক্ররেখা একাধিক উপত্যকা তৈরি করে, তাই কোথা থেকে শুরু করেছি তার ওপর নির্ভর করে আমরা কোন তলিতে পৌঁছাব।"},
            {"index": 3, "type": "p",
             "tts": "ক্যালকুলাস আমাদের শেখায় যে কোনো বিন্দুতে স্পর্শকের ঢাল ডি সি বাই ডি ডব্লি নির্দেশ করে ডব্লি সামান্য বাড়ালে কস্ট বাড়বে না কমবে। ঢাল ধনাত্মক হলে ডব্লি কমালে কস্ট কমে, আর ঋণাত্মক হলে বাড়ালে কমে। তাই সবসময় ঢালের বিপরীত চিহ্নে পদক্ষেপ নিতে হবে। হালনাগাদির সূত্র হলো, পরবর্তী ডব্লি সমান বর্তমান ডব্লি বিয়োগ ইটা গুণ ডি সি বাই ডি ডব্লি। এখানে ইটা হলো লার্নিং রেট, ধাপের আকার নিয়ন্ত্রক এক ছোট ধ্রুবক।"},
            {"index": 4, "type": "p",
             "tts": "এখন কল্পনা করুন দুটি ইনপুট চলক, অর্থাৎ সি অব ডব্লি এক কমা ডব্লি টু। এর লেখচিত্র হবে ত্রিমাত্রিক স্থানে একটি পাহাড়ি উপত্যকার মতো ভূসংস্থান। আপনি যদি এই পাহাড়ের কোনো ঢালে একটি ভারী মার্বেল বল ছেড়ে দেন, তবে মাধ্যাকর্ষণ বলটিকে সবচেয়ে খাড়া ঢাল বরাবর নিচের উপত্যকায় গড়িয়ে নিয়ে যাবে। ঠিক এই কাজটিই করে গ্রেডিয়েন্ট ডিসেন্ট।"},
            {"index": 5, "type": "figure",
             "tts": "দুটি প্যারামিটার নিলে কস্ট ফাংশন একটি সারফেস তৈরি করে, আর তার ওপর থাকা কনট্যুর রেখাগুলো একই কস্টের জায়গা চিহ্নিত করে। হলুদ তীরটি সবচেয়ে খাড়া নামার দিক নির্দেশ করছে, অর্থাৎ গ্রেডিয়েন্টের ঠিক বিপরীত দিক। কনট্যুরের লম্ব বরাবর এই নামাই যত বার করি, তত কম কস্টের রেখায় পৌঁছে যাই। বল যেমন সবচেয়ে খাড়া পথে নিচে নামে, অ্যালগরিদমও তেমনি পদে পদে কস্ট কমিয়ে আনে।"},
        ],
    },

    "sec-multivariable-gradient": {
        "title": "গ্রেডিয়েন্টের গাণিতিক রূপ ও দিকবিন্যাস",
        "audio_file": "sec-multivariable-gradient.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, গ্রেডিয়েন্টের গাণিতিক রূপ ও দিকবিন্যাস।"},
            {"index": 1, "type": "p",
             "tts": "মাল্টিভ্যারিয়েবল ক্যালকুলাসে কোনো বহুমাত্রিক ফাংশনের গ্রেডিয়েন্ট হলো এমন একটি ভেক্টর যা ফাংশনটির সমস্ত আংশিক অন্তরজ ধারণ করে, গ্রেডিয়েন্ট অব সি। এর প্রতিটি উপাংশ হলো সংশ্লিষ্ট ওজন বা বায়াসের সাপেক্ষে সির আংশিক অন্তরজ। আমাদের ক্ষেত্রে এই ভেক্টরে ঠিক তের হাজার দুইটি উপাংশ থাকে, প্রতিটি ওজন ও বায়াসের জন্য একটিমাত্র।"},
            {"index": 2, "type": "p",
             "tts": "জ্যামিতিকভাবে গ্রেডিয়েন্ট অব সির দুটি অত্যন্ত শক্তিশালী ধর্ম রয়েছে। প্রথমত, এটি নির্দেশ করে কোন দিকে পা বাড়ালে কস্ট সবচেয়ে দ্রুত বাড়বে। দ্বিতীয়ত, এর দৈর্ঘ্য বলে দেয় সেই সবচেয়ে খাড়া ঢালটি ঠিক কতখানি খাড়া।"},
            {"index": 3, "type": "callout-gold",
             "tts": "বিশেষ নোট, গ্রেডিয়েন্টের দুটি মৌলিক জ্যামিতিক বৈশিষ্ট্য। প্রথমটি হলো সর্বাধিক বৃদ্ধির দিক, অর্থাৎ ইনপুট স্থানে সেই নির্দিষ্ট দিক যেদিকে পা বাড়ালে কস্ট সবচেয়ে দ্রুত বৃদ্ধি পাবে। দ্বিতীয়টি হলো মানের মাত্রা, অর্থাৎ গ্রেডিয়েন্টের দৈর্ঘ্য ঢালটি কতটা খাড়া তা নির্দেশ করে। খাড়া পাহাড়ে মান বিশাল আর সমতল উপত্যকায় মান শূন্যের কাছাকাছি, তাই একই সূত্র নিজেই ধাপের আকারও নিয়ন্ত্রণ করে।"},
            {"index": 4, "type": "p",
             "tts": "যেহেতু আমাদের লক্ষ্য কস্ট বাড়ানো নয় বরং কমানো, তাই আমরা পা ফেলি ঠিক ঋণাত্মক গ্রেডিয়েন্টের দিকে, অর্থাৎ সবচেয়ে খাড়া অবরোহণের দিকে। পুরো তের হাজার দুইটি প্যারামিটারের ভেক্টর থিটা হালনাগাদ করার সমীকরণটি দাঁড়ায়, পরবর্তী থিটা সমান বর্তমান থিটা বিয়োগ ইটা গুণ গ্রেডিয়েন্ট অব সি অব থিটা। প্রতিটি পুনরাবৃত্তিতে লার্নিং রেট ইটা দিয়ে গুণ করে আমরা এই বিশাল ভেক্টরের ধাপটি ছোট বা বড় করি।"},
            {"index": 5, "type": "p", "role": "conclusion",
             "tts": "প্রতিটি হালনাগাদে কোনো প্যারামিটার কতটা বদলাবে তা নির্ভর করে তার আংশিক অন্তরজের ওপর। যে ওজন সামান্য নড়ালে কস্টের বিশাল পরিবর্তন ঘটে, গ্রেডিয়েন্ট ভেক্টরে তার উপাংশের মান অনেক বড় হয়, ফলে অ্যালগরিদম তাকে বেশি অগ্রাধিকার দিয়ে দ্রুত সংশোধন করে। অন্যভাবে বললে, ঋণাত্মক গ্রেডিয়েন্ট হলো তের হাজার দুইটি নুডজের একটি তালিকা, যার প্রতিটি ঘটকের চিহ্ন বলে কমাও না বাড়াও আর তার মাত্রা বলে কে কতটা গুরুত্বপূর্ণ।"},
        ],
    },

    "sec-learning-rate-landscape": {
        "title": "ধাপের আকার এবং লোকাল মিনিমার চ্যালেঞ্জ",
        "audio_file": "sec-learning-rate-landscape.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, ধাপের আকার আর লোকাল মিনিমার চ্যালেঞ্জ।"},
            {"index": 1, "type": "p",
             "tts": "গ্রেডিয়েন্ট ডিসেন্টের সাফল্য গভীরভাবে নির্ভর করে লার্নিং রেট বা স্টেপ সাইজ ইটার ওপর। যদি ইটা অতিরিক্ত ছোট হয়, তবে পাহাড়ি ঢাল বেয়ে নামতে নেটওয়ার্কের অনন্তকাল সময় লেগে যাবে। অন্যদিকে ইটা যদি অতিরিক্ত বড় হয়, তবে পদক্ষেপ এত বিশাল হবে যে বলটি উপত্যকা পার হয়ে উল্টো পাশের দেয়ালে আঘাত হানবে আর কস্ট কমার বদলে বিস্ফোরিত হয়ে অসীমে ছুটে যাবে।"},
            {"index": 2, "type": "figure",
             "tts": "এই লেখচিত্রে একই সি অব ডব্লি সমান ডব্লি স্কয়ার উপত্যকায় তিনটি ভিন্ন লার্নিং রেটের পথ দেখানো হয়েছে। ছোট ইটার হলুদ পথ ধীরে ধীরে এগোলেও তলিতে পৌঁছাতে অনেক পুনরাবৃত্তি লাগে। মাঝারি ইটার সবুজ পথ সরাসরি নিখুঁতভাবে তলিতে নামে। আর বড় ইটার লাল পথ ওপারের দেয়ালে লাফ দিয়ে দোলে, কখনো কখনো বিস্ফোরিতও হয়।"},
            {"index": 3, "type": "p", "role": "conclusion",
             "tts": "এছাড়াও বাস্তব নিউরাল নেটওয়ার্কের কস্ট সারফেস কোনো নিখুঁত মিষ্টি বাটির মতো উত্তল নয়। এটি অসংখ্য উঁচু টিলা, স্যাডল পয়েন্ট আর স্থানীয় সর্বনিম্ন বিন্দুতে পূর্ণ। তবে আশ্চর্য হলেও সত্যি, তের হাজার মাত্রার মতো উচ্চমাত্রিক স্থানে সব দিক থেকে একসাথে আটকানো লোকাল মিনিমা অত্যন্ত বিরল। বেশিরভাগ আপাত সমতল বিন্দুই স্যাডল পয়েন্ট, যেখান থেকে অন্তত কয়েকটি দিকে নামার পথ উন্মুক্ত থাকে।"},
        ],
    },

    "sec-mini-batch-sgd": {
        "title": "কেন পুরো ডেটাসেট একসাথে গণনা অবাস্তব?",
        "audio_file": "sec-mini-batch-sgd.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "ষষ্ঠ পরিচ্ছেদ, কেন পুরো ডেটাসেট একসাথে গণনা করা অবাস্তব।"},
            {"index": 1, "type": "p",
             "tts": "আমরা দেখেছি যে নিখুঁত গ্রেডিয়েন্ট অব সি গণনা করতে হলে সমস্ত ষাট হাজার ট্রেনিং ছবির জন্য আলাদা আলাদা গ্রেডিয়েন্ট বের করে তাদের গড় নিতে হয়। গ্রেডিয়েন্ট ডিসেন্টের একটিমাত্র ক্ষুদ্র পদক্ষেপ নেওয়ার জন্য ষাট হাজারটি ছবির ফরোয়ার্ড ও ব্যাকওয়ার্ড গণনা কম্পিউটারের জন্য অকল্পনীয়ভাবে ধীরগতির ও অপব্যয়ী।"},
            {"index": 2, "type": "p",
             "tts": "এই সমস্যার চমৎকার সমাধান হলো স্টোকাস্টিক গ্রেডিয়েন্ট ডিসেন্ট, সংক্ষেপে এসজিডি। আমরা পুরো ট্রেনিং ডেটাসেটকে এলোমেলোভাবে ছোট ছোট দলে বা মিনি ব্যাচে ভাগ করে ফেলি, সাধারণত প্রতি ব্যাচে বত্রিশ, চৌষট্টি বা একশো আটাশটি ছবি থাকে। প্রতিটি ব্যাচের গড় গ্রেডিয়েন্ট প্রকৃত গ্রেডিয়েন্টের একটি দ্রুত ও বিশ্বাসযোগ্য আসন্ন মান দেয়।"},
            {"index": 3, "type": "p",
             "tts": "প্রতিটি মিনি ব্যাচের হিসাব শেষ হওয়ার সাথে সাথেই ওজন ও বায়াসগুলো হালনাগাদ করা হয়। যদিও এই পদক্ষেপগুলো সামান্য কোলাহলপূর্ণ বা আঁকাবাঁকা পথে এগোয়, তবে সামগ্রিকভাবে পথটি ঠিকই গভীর উপত্যকার দিকে ধাবিত হয়। এই এলোমেলোতা আসলে নেটওয়ার্ককে অগভীর লোকাল মিনিমা থেকে লাফিয়ে বের হয়ে আরও ভালো সমাধানে পৌঁছাতে সাহায্য করে। একজন মাতাল মানুষ যেমন আঁকাবাঁকা পথে নামলেও শেষ পর্যন্ত উপত্যকাতেই পৌঁছায়।"},
            {"index": 4, "type": "callout-purple",
             "tts": "বিশেষ নোট, পরবর্তী অধ্যায়ের সেতু, ব্যাকপ্রপাগেশনের আগমন। আমরা জানলাম যে ঋণাত্মক গ্রেডিয়েন্টের দিকে পা ফেললেই নেটওয়ার্ক শেখে। কিন্তু প্রশ্ন রয়েই গেল, প্রতিটি ছবির জন্য এই তের হাজার দুইটি আংশিক অন্তরজ কম্পিউটার ঠিক কীভাবে দ্রুত ও নির্ভুলভাবে গণনা করে? সেই জাদুকরী অ্যালগরিদমের নামই ব্যাকপ্রপাগেশন, যা আমাদের পরবর্তী অধ্যায়ের মূল বিষয়।"},
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
            raise ValueError(f"{sec_id}: expected {EXPECTED_COUNT[sec_id]} cues")
        total += len(indices)
    if total != 32:
        raise ValueError(f"Expected 32 cues, found {total}")

    # Figure cues must be genuine 2-4 sentence explanations.
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            if cue["type"] == "figure":
                sentences = [s for s in cue["tts"].split("।") if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(f"{sec_id} cue {cue['index']}: figure has {len(sentences)} sentences")


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
    assert total_cues == 32

    print("\n" + "=" * 70)
    print("BUILD COMPLETE - expressive teacher audio, Neural Networks Lesson 02")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<34} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTIONS_DATA)} sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json is valid JSON; all 6 mp3 files exist and are non-empty.")
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
    BENIGN_FAILED = ("youtube.com/embed/", "3b1b_nn_02_full_dubbed.mp4")
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

    assert total_cues == 32, total_cues
    assert figure_count == 4, figure_count
    assert not disallowed, f"Disallowed cue types: {disallowed}"
    assert not forbidden_hits, f"Artificial figure label found: {forbidden_hits}"

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
    print("VERIFIED: 32/32 cues, DOM<->manifest 1:1, 0 dups, "
          "0 quiz/media-tab types, non-zero mp3s, valid JSON, 0 page errors "
          "(uncaught JS), 0 failed audio resources, 0 'চিত্র প্রদর্শনী'.")


if __name__ == "__main__":
    main()
