# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Neural Networks Lesson 04
("Backpropagation calculus", Bengali) to the gold standard.

Deterministic, re-runnable, self-contained:

  * 26 cues in 4 narrated sections with EXACTLY the same section IDs, alias,
    audio_file names, cue types and cue order as the LIVE DOM (extracted first
    with the narration engine's own selector, KaTeX <annotation> nodes
    included -- see governance/_nn04_dom_extract.json). The two non-narrated
    sections (sec-lab, sec-quizzes, both data-no-narration="true") are NOT
    included.
  * NOTE: the manifest keeps the callout variants (callout-purple / -blue /
    -gold), but the DOM/narration engine normalise every one of them to the
    base `.callout` type. Verification compares NORMALISED types, and also
    checks the raw callout-* classes survive on the DOM side.
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time), so the build is fully reproducible.
  * Every explanatory cue is a genuine 2-4 sentence natural Bengali
    explanation; the artificial label "চিত্র প্রদর্শনী" is explicitly
    forbidden and checked. There are no `figure` cue types in this lesson's
    narrated DOM (the media-tab diagrams are not part of the selector), but
    figure prosody is still defined for completeness.
  * Phonetic safeguards: dC/dw -> "পার্শিয়াল ডি সি বাই ডি ডাব্লিউ",
    sigmoid -> "সিগময়েড", sigma prime -> "সিগমা প্রাইম",
    chain rule -> "চেইন রুল", eta -> "ইটা", 13,002 -> "তেরো হাজার দুই".
    No TeX, Latin letters, backslashes, braces, brackets, em/en dashes or
    raw hyphens reach the TTS engine.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
    h2 -5%/+2Hz, chapter-quote -3%, p +2%, figure -4%, formula-box -8%,
    callout +0%, conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names
    (sec_01_toy_network.mp3 ... sec_04_matrix_vector.mp3).
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with
    exact-ms timings and the exact existing section keys (no added aliases).
  * Bumps the live page's manifest.js cache-buster to the next version.
  * Verifies with headless Chrome (channel=chrome): 26/26 cues, DOM <-> manifest
    1:1 parity (with callout normalisation), 0 duplicates, 0 quiz/media-tab
    cue types, non-zero mp3s, valid JSON, 0 page errors (uncaught JS
    exceptions), 0 narration-audio resource failures and 0 occurrences of
    "চিত্র প্রদর্শনী". Pre-existing media loads (a blocked YouTube iframe
    and a media-vault .mp4 absent in this workspace) are classified separately.

Usage:
    python governance/build_expressive_teacher_audio_nn04.py            # build + verify
    python governance/build_expressive_teacher_audio_nn04.py --verify-only
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
                         "neural_networks", "lesson_04")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "neural_networks", "lesson_04.html")
MANIFEST_TITLE = ("অধ্যায় ০৪ — ব্যাকপ্রপাগেশন ক্যালকুলাস: বিস্তারিত প্রমাণ ও "
                  "অ্যালগরিদম (Backpropagation Calculus)")

# Prosody keyed by cue type: (rate, pitch, volume)
PROSODY_DEFAULT = {
    "h2":             ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
    "h3":             ("-3%", "+0Hz", "+0%"),
    "chapter-quote":  ("-3%", "+0Hz", "+0%"),   # reflective opening quote
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

# EXACT narrated section IDs, alias, audio files, cue-type sequences and counts,
# taken from the LIVE DOM via the narration engine's own selector (KaTeX
# <annotation> nodes included). Order matters (DOM order). These were extracted
# BEFORE writing this builder into governance/_nn04_dom_extract.json:
#   sec-intro-toy-network     6  [h2, chapter-quote, p, p, formula-box, callout-purple]
#   sec-chain-rule-derivation 7  [h2, p, formula-box, formula-box, p, callout-blue, p]
#   sec-generalization-layers 7  [h2, p, formula-box, callout-gold, p, p, formula-box]
#   sec-matrix-formulation    6  [h2, p, formula-box, p, callout-purple, p]
EXPECTED_TYPES = {
    "sec-intro-toy-network":      ["h2", "chapter-quote", "p", "p", "formula-box", "callout-purple"],
    "sec-chain-rule-derivation":  ["h2", "p", "formula-box", "formula-box", "p", "callout-blue", "p"],
    "sec-generalization-layers":  ["h2", "p", "formula-box", "callout-gold", "p", "p", "formula-box"],
    "sec-matrix-formulation":     ["h2", "p", "formula-box", "p", "callout-purple", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-intro-toy-network":      "sec_01_toy_network.mp3",
    "sec-chain-rule-derivation":  "sec_02_chain_rule.mp3",
    "sec-generalization-layers":  "sec_03_generalization.mp3",
    "sec-matrix-formulation":     "sec_04_matrix_vector.mp3",
}
EXPECTED_ALIASES = {
    "sec-intro-toy-network":      "sec_01_toy_network",
    "sec-chain-rule-derivation":  "sec_02_chain_rule",
    "sec-generalization-layers":  "sec_03_generalization",
    "sec-matrix-formulation":     "sec_04_matrix_vector",
}
EXPECTED_TITLES = {
    "sec-intro-toy-network":      "১. খেলনা নেটওয়ার্কে চেইন রুল (Chain Rule on Single-Neuron Network)",
    "sec-chain-rule-derivation":  "২. আংশিক অন্তরজের ব্যবচ্ছেদ ও তিন পদের গুণফল (Dissecting the Three Partial Derivatives)",
    "sec-generalization-layers":  "৩. বহু নিউরন ও লেয়ারে সাধারণীকরণ ও এরর টার্ম (Generalizing to Full Network & Delta Error Term)",
    "sec-matrix-formulation":     "৪. ম্যাট্রিক্স-ভেক্টর রূপ ও গণনামূলক যুগান্তকারী দক্ষতা (Matrix-Vector Formulation & Computational Supremacy)",
}
EXPECTED_COUNT = {sid: len(t) for sid, t in EXPECTED_TYPES.items()}
NON_NARRATED = ["sec-lab", "sec-quizzes"]

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (26 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-intro-toy-network": {
        "title": EXPECTED_TITLES["sec-intro-toy-network"],
        "alias": EXPECTED_ALIASES["sec-intro-toy-network"],
        "audio_file": EXPECTED_AUDIO_FILES["sec-intro-toy-network"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, একক নিউরনের সরল খেলনা নেটওয়ার্কে চেইন রুলের সূচনা।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "ক্যালকুলাস হলো প্রকৃতির পরিবর্তনশীল রূপকে বোঝার অনুবীক্ষণ যন্ত্র, আর ব্যাকপ্রপাগেশন হলো লক্ষ লক্ষ প্যারামিটারের বিশৃঙ্খলাকে নিখুঁত সুরে বাঁধার অদৃশ্য কাণ্ডারি।"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, ডিপ লার্নিংয়ের চতুর্থ অধ্যায়ে তোমাদের স্বাগতম। আগের পর্বে আমরা ব্যাকপ্রপাগেশনের মূল ধারণাটি চাক্ষুষ অন্তর্দৃষ্টি দিয়ে বুঝেছিলাম, এবার আমরা তার নিখুঁত গাণিতিক প্রমাণে প্রবেশ করব। আমাদের লক্ষ্য হলো গ্রেডিয়েন্ট ভেক্টরের প্রতিটি উপাংশ, অর্থাৎ ওজনের সাপেক্ষে কস্টের আংশিক অন্তরজ পার্শিয়াল ডি সি বাই ডি ডাব্লিউ এবং বায়াসের সাপেক্ষে একই রকম আরেকটি অন্তরজ নির্ণয় করা। সবচেয়ে সহজ খেলনা নেটওয়ার্ক দিয়ে, অর্থাৎ প্রতি স্তরে মাত্র একটি করে নিউরন নিয়ে, আমরা হিসাবটি শুরু করব।"},
            {"index": 3, "type": "p",
             "tts": "শুরুতেই শত শত নিউরন আর জটিল সাবস্ক্রিপ্টের গোলকধাঁধায় না জড়িয়ে আমরা একদম সরল একটি নেটওয়ার্ক বাছাই করব, যেখানে প্রতিটি লেয়ারে থাকবে মাত্র একটি করে নিউরন। শেষ লেয়ারের আগের স্তর থেকে শেষ স্তরে আসার সময় তিনটি উপাদান কাজ করে, যথা পূর্ববর্তী অ্যাক্টিভেশন, সংযোগকারী ওজন এবং বায়াস। এই তিনটি থেকে যথাক্রমে ওয়েটেড সমষ্টি, সিগময়েড অ্যাক্টিভেশন এবং একক উদাহরণের বর্গের ত্রুটি তৈরি হয়। মোট তিনটি ওজন আর তিনটি বায়াস নিয়েই আমরা পুরো হিসাবটি করতে পারব।"},
            {"index": 4, "type": "formula-box",
             "tts": "শেষ স্তরের ফরোয়ার্ড সমীকরণটি এইভাবে লেখা যায়। ওয়েটেড সমষ্টি জেড এল সমান ডব্লিউ এল গুণ এ এল মাইনাস ওয়ান, তার সাথে বি এল যোগ। অ্যাক্টিভেশন এ এল হলো সিগময়েড অব জেড এল, অর্থাৎ এক ভাগের এক যোগ ই ঋণাত্মক জেড এল। আর একক উদাহরণের কস্ট সি নট হলো এ এল মাইনাস ওয়াই এর বর্গ।"},
            {"index": 5, "type": "callout-purple",
             "tts": "বিশেষ নোট, কার্যকারণ ও নির্ভরশীলতার শিকল। ওজন ডব্লিউ এল সামান্য বদলালেই ওয়েটেড সমষ্টি জেড এল বদলায়, জেড এল বদলালে অ্যাক্টিভেশন এ এল বদলায়, আর অ্যাক্টিভেশন বদলালেই সরাসরি কস্ট সি নটের পরিবর্তন ঘটে। এই শৃঙ্খলটিই চেইন রুল প্রয়োগের আদর্শ ক্ষেত্র, ছোট এক নাজের প্রভাব তিনটি ধাপ ধরে গুণ হয়ে শেষ পর্যন্ত কস্টে পৌঁছায়। তাই এই সরল শিকল ধরেই আমরা আংশিক অন্তরজের হিসাব চালিয়ে যাব।"},
        ],
    },

    "sec-chain-rule-derivation": {
        "title": EXPECTED_TITLES["sec-chain-rule-derivation"],
        "alias": EXPECTED_ALIASES["sec-chain-rule-derivation"],
        "audio_file": EXPECTED_AUDIO_FILES["sec-chain-rule-derivation"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, চেইন রুলের তিনটি পৃথক পদ এবং ওজন ও বায়াসের গ্রেডিয়েন্ট।"},
            {"index": 1, "type": "p",
             "tts": "আমাদের লক্ষ্য হলো ওজনের সাপেক্ষে কস্টের আংশিক অন্তরজ, অর্থাৎ পার্শিয়াল ডি সি বাই ডি ডাব্লিউ নির্ণয় করা। ক্যালকুলাসের চেইন রুল অনুসারে এই অন্তরজটি তিনটি পৃথক অনুপাতের নিরবচ্ছিন্ন গুণফল হিসেবে ভেঙে যায়, যথা ওজনের সাপেক্ষে জেড এর অন্তরজ, জেড এর সাপেক্ষে অ্যাক্টিভেশনের অন্তরজ, এবং অ্যাক্টিভেশনের সাপেক্ষে কস্টের অন্তরজ। আসুন এই তিনটি পদকে আলাদা করে বিশ্লেষণ ও প্রমাণ করি। তিনটি পদের গুণফলই শেষ পর্যন্ত আমাদের কাঙ্ক্ষিত গ্রেডিয়েন্ট দেবে।"},
            {"index": 2, "type": "formula-box",
             "tts": "প্রথম পদটি হলো অ্যাক্টিভেশনের সাপেক্ষে কস্টের অন্তরজ। বর্গের নিয়ম প্রয়োগ করলে তা দাঁড়ায় দুই গুণ এ এল মাইনাস ওয়াই। লক্ষ্য করুন, নেটওয়ার্কের অনুমান কাঙ্ক্ষিত লক্ষ্য থেকে যত দূরে থাকে, এই মান তত বড় হয়। ভুল যত বড়, সংশোধনের তাগিদও তত তীব্র।"},
            {"index": 3, "type": "formula-box",
             "tts": "দ্বিতীয় পদটি হলো সিগময়েড অ্যাক্টিভেশনের অন্তরজ, যাকে আমরা সিগমা প্রাইম বলে ডাকি। এর মান সমান সিগমা অব জেড, এক মাইনাস সিগমা অব জেড দিয়ে গুণ করা। তৃতীয় পদটি হলো ওজনের সাপেক্ষে জেড এর অন্তরজ, আর তা শুধুই পূর্ববর্তী স্তরের অ্যাক্টিভেশন এ এল মাইনাস ওয়ান। এই তিনটি পদ একসাথে গুণ করলেই ওজনের চূড়ান্ত গ্রেডিয়েন্ট পাওয়া যায়।"},
            {"index": 4, "type": "p",
             "tts": "তিনটি পদকে একসাথে গুণ করলে ওজনের চূড়ান্ত গ্রেডিয়েন্টটি পাই, যা পূর্ববর্তী অ্যাক্টিভেশন, সিগমা প্রাইম এবং দুই গুণ এ মাইনাস ওয়াই তিনটির গুণফল। লক্ষ্য করুন, ওজনের পরিবর্তনশীলতা সরাসরি পূর্ববর্তী নিউরনের উজ্জ্বলতার সমানুপাতিক। ইনপুট নিউরনের মান শূন্য হলে ওজন কোটি কোটি গুণ বদলালেও কস্টে কোনো পরিবর্তন আসবে না। আবার অনুমান লক্ষ্য থেকে অনেক দূরে গেলে প্রথম পদ বড় হয়ে বড় পদক্ষেপ নিতে বাধ্য করে।"},
            {"index": 5, "type": "callout-blue",
             "tts": "বিশেষ নোট, বায়াসের গ্রেডিয়েন্ট। বায়াসের ক্ষেত্রে চেইন রুল হুবহু এক, কারণ বায়াসের সাপেক্ষে জেড এর অন্তরজ সমান এক। তাই বায়াসের গ্রেডিয়েন্ট দাঁড়ায় সিগমা প্রাইম গুণ দুই গুণ এ এল মাইনাস ওয়াই। ওজনের গ্রেডিয়েন্টের সাথে একমাত্র পার্থক্য হলো এখানে পূর্ববর্তী অ্যাক্টিভেশনের জায়গায় একটি এক বসে, কারণ বায়াসের নাজ সরাসরি জেড কে নাড়ায়।"},
            {"index": 6, "type": "p",
             "tts": "ব্যাকপ্রপাগেশনের সবচেয়ে জাদুকরী ধাপটি ঘটে যখন আমরা পূর্ববর্তী অ্যাক্টিভেশনের সাপেক্ষে অন্তরজ নিই। যেহেতু অ্যাক্টিভেশনের সাপেক্ষে জেড এর অন্তরজ হলো ওজন ডব্লিউ এল, তাই কস্টের সংবেদনশীলতা সরাসরি ওজন দিয়ে গুণ করে বের করা যায়। একবার পেছনের অ্যাক্টিভেশনের সংবেদনশীলতা জানা গেলে হুবহু একই চেইন রুল পুনরাবৃত্তি করে আগের লেয়ারের ওজন ও বায়াসের গ্রেডিয়েন্টও বের করা যায়। এইভাবে সব লেয়ারের পার্শিয়াল ডি সি বাই ডি ডাব্লিউ হিসাব করে পুরো গ্রেডিয়েন্ট ভেক্টর গঠন করা হয়।"},
        ],
    },

    "sec-generalization-layers": {
        "title": EXPECTED_TITLES["sec-generalization-layers"],
        "alias": EXPECTED_ALIASES["sec-generalization-layers"],
        "audio_file": EXPECTED_AUDIO_FILES["sec-generalization-layers"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, বহু নিউরন বিশিষ্ট নেটওয়ার্কে সূচক বিন্যাস এবং এরর টার্ম ডেল্টার সংজ্ঞা।"},
            {"index": 1, "type": "p",
             "tts": "বাস্তব নেটওয়ার্কে প্রতিটি স্তরে বহু নিউরন থাকে। এই বহুমাত্রিক সম্পর্কের জন্য আমরা সুনির্দিষ্ট সূচক ব্যবহার করি, লেয়ারকে এল, বর্তমান স্তরের নিউরনকে জে এবং পূর্ববর্তী স্তরের নিউরনকে কে দিয়ে চিহ্নিত করি। ওজন ডব্লিউ জে কে এল নির্দেশ করে কে থেকে জে তে যাওয়া সংযোগ, অর্থাৎ গন্তব্য নিউরন জে প্রথমে আর উৎস নিউরন কে পরে। এই সূচকের ক্রম মনে রাখলে বহু নিউরনের হিসাবও সরল হয়ে যায়।"},
            {"index": 2, "type": "formula-box",
             "tts": "ওয়েটেড সমষ্টির সূত্রটি হলো, জেড জে এল সমান কে জুড়ে ওজন ডব্লিউ জে কে এল গুণ অ্যাক্টিভেশন এ কে এল মাইনাস ওয়ান এর সমষ্টি, তার সাথে বায়াস বি জে এল যোগ। একইভাবে অ্যাক্টিভেশন এ জে এল হলো সিগময়েড অব জেড জে এল। আর সামগ্রিক কস্ট সি নট হলো সমস্ত আউটপুট নিউরনের বর্গের বিয়োগফলের সমষ্টি। এই তিনটি সূত্রই পরবর্তী সমস্ত অন্তরজের ভিত্তি তৈরি করে।"},
            {"index": 3, "type": "callout-gold",
             "tts": "বিশেষ নোট, এরর টার্ম ডেল্টার অবতরণ। গাণিতিক সমীকরণগুলোকে সংহত রাখতে আমরা প্রতিটি নিউরনের জন্য একটি মধ্যবর্তী রাশি সংজ্ঞায়িত করি, যা হলো কস্টের সাপেক্ষে ওয়েটেড সমষ্টির আংশিক অন্তরজ। একে বলা হয় লেয়ার এল এর জে তম নিউরনের এরর বা ত্রুটি, আর লেখা হয় ডেল্টা জে এল। আউটপুট লেয়ারের ক্ষেত্রে এটি সরাসরি ক্যালকুলাস থেকে পাওয়া যায়, দুই গুণ এ জে এল মাইনাস ওয়াই জে, গুণ সিগমা প্রাইম অব জেড জে এল।"},
            {"index": 4, "type": "p",
             "tts": "এই এরর টার্মের সাহায্যে যেকোনো ওজনের আংশিক অন্তরজ এক অপূর্ব সংক্ষিপ্ত রূপ লাভ করে। ওজনের গ্রেডিয়েন্ট দাঁড়ায় পূর্ববর্তী অ্যাক্টিভেশন এ কে এল মাইনাস ওয়ান গুণ বর্তমান এরর টার্ম ডেল্টা জে এল। আর বায়াসের গ্রেডিয়েন্ট হলো শুধুই ডেল্টা জে এল। এই সংক্ষিপ্ত রূপই পুরো ব্যাকপ্রপাগেশন অ্যালগরিদমের হৃদয়।"},
            {"index": 5, "type": "p",
             "tts": "এররটিকে পেছনের হিডেন লেয়ারে টেনে আনতে আমরা মাল্টিভ্যারিয়েবল চেইন রুল প্রয়োগ করি। কারণ একটি কে নিউরন পরবর্তী স্তরের প্রতিটি জে নিউরনকে যুগপৎ প্রভাবিত করে। তাই পেছনের দিকে এরর ফেরত আনার সময় এই সমস্ত অবদানের সমষ্টি নিতে হয়। এইখানেই জন্ম নেয় ব্যাকপ্রপাগেশনের মূল পুনরাবৃত্তিমূলক সূত্র।"},
            {"index": 6, "type": "formula-box",
             "tts": "পুনরাবৃত্তিমূলক সূত্রটি হলো, ডেল্টা কে এল মাইনাস ওয়ান সমান জে জুড়ে ওজন ডব্লিউ জে কে এল গুণ ডেল্টা জে এল এর সমষ্টি, পুরোটার সাথে গুণ সিগমা প্রাইম অব জেড কে এল মাইনাস ওয়ান। অর্থাৎ পেছনের স্তরের প্রতিটি এরর হলো পরবর্তী স্তরের এররগুলোর ভরযুক্ত সমষ্টি, যার সাথে সিগময়েডের অন্তরজ গুণ করা হয়। এই সূত্র বারবার প্রয়োগ করে আমরা ইনপুট স্তর পর্যন্ত সকল এরর হিসাব করতে পারি। এভাবেই চেইন রুল পুরো নেটওয়ার্কজুড়ে পেছনের দিকে ছড়িয়ে পড়ে।"},
        ],
    },

    "sec-matrix-formulation": {
        "title": EXPECTED_TITLES["sec-matrix-formulation"],
        "alias": EXPECTED_ALIASES["sec-matrix-formulation"],
        "audio_file": EXPECTED_AUDIO_FILES["sec-matrix-formulation"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, ব্যাকপ্রপাগেশনের ম্যাট্রিক্স ভেক্টর রূপ এবং কম্পিউটেশনাল দক্ষতা।"},
            {"index": 1, "type": "p",
             "tts": "পুনরাবৃত্তিমূলক সমষ্টির রাশিটি আসলে ওজন ম্যাট্রিক্স ডব্লিউ এল এর ট্রান্সপোজের সাথে এরর ভেক্টর ডেল্টা এল এর ম্যাট্রিক্স গুণন ছাড়া আর কিছুই নয়। একক নিউরনের চেইন রুল এখন পুরো স্তরজুড়ে একসাথে প্রয়োগ করা যায়। প্রতিটি পৃথক হিসাবকে ভেক্টর ও ম্যাট্রিক্সে মোড়ানোই এই রূপান্তরের মর্ম। ট্রান্সপোজের কারণে মাত্রাগুলো ঠিক মিলে যায় এবং হিসাব অনেক সংহত হয়।"},
            {"index": 2, "type": "formula-box",
             "tts": "ভেক্টর ব্যাকপ্রপ সমীকরণটি হলো, ডেল্টা এল মাইনাস ওয়ান সমান ডব্লিউ ট্রান্সপোজ গুণ ডেল্টা এল, তার সাথে উপাদানভিত্তিক হাদামার্দ গুণ সিগমা প্রাইম অব জেড এল মাইনাস ওয়ান। আর ওজন গ্রেডিয়েন্ট ম্যাট্রিক্স হলো ডেল্টা এল এবং পূর্ববর্তী অ্যাক্টিভেশনের ট্রান্সপোজের বহিঃগুণন। এই দুটি সূত্রই পুরো স্তরের জন্য একসাথে গ্রেডিয়েন্ট তৈরি করে। ম্যাট্রিক্স গুণনের শক্তিতে ব্যক্তিগত হিসাবগুলো এক লহমায় সম্পন্ন হয়।"},
            {"index": 3, "type": "p",
             "tts": "এই অ্যালগরিদম কেন ডিপ লার্নিংয়ের ইতিহাসে সবচেয়ে বৈপ্লবিক উদ্ভাবন? প্রথাগতভাবে প্রতিটি ওজনকে সামান্য পরিমাণ নাড়িয়ে সংখ্যাত্মক ডেরিভেটিভ বের করতে গেলে একটিমাত্র পদক্ষেপের জন্য তেরো হাজার বার ফরোয়ার্ড পাস চালাতে হতো। কিন্তু ম্যাট্রিক্স গুণন ও চেইন রুলের এই সংহত রূপ সমস্ত হিসাবকে একযোগে সম্পন্ন করে। ব্যাকপ্রপাগেশনের আসল শক্তি এখানেই।"},
            {"index": 4, "type": "callout-purple",
             "tts": "বিশেষ নোট, গণনামূলক শ্রেষ্ঠত্ব। আমাদের খেলনা নেটওয়ার্কে মোট তেরো হাজার দুইটি ওজন ও বায়াস রয়েছে। যদি সংখ্যাত্মকভাবে প্রতিটি ওজনকে সামান্য বাড়িয়ে ডেরিভেটিভ মাপতে যেতেন, তবে একটিমাত্র পদক্ষেপের জন্য তেরো হাজার বার ফরোয়ার্ড পাস চালাতে হতো। কিন্তু ব্যাকপ্রপাগেশন একটিমাত্র ব্যাকওয়ার্ড পাসে সমস্ত তেরো হাজার দুইটি প্যারামিটারের নিখুঁত গ্রেডিয়েন্ট এক লহমায় বের করে দেয়, ঠিক একটি ফরোয়ার্ড পাসের সমান খরচে।"},
            {"index": 5, "type": "p", "role": "conclusion",
             "tts": "বিশেষ নোট, স্টোকাস্টিক গ্রেডিয়েন্ট ডিসেন্ট ও মিনি ব্যাচ। একক উদাহরণের কস্ট অনেক কোলাহলপূর্ণ হতে পারে, তাই বাস্তব প্রশিক্ষণে আমরা ছোট মিনি ব্যাচের সমস্ত নমুনার গ্রেডিয়েন্ট গড় করে ওজন হালনাগাদ করি। লার্নিং রেট ইটা দিয়ে এই গড় প্রস্তাবকে ছোট করে প্রতিটি ওজনে প্রয়োগ করা হয়। নিচের ইন্টারেক্টিভ ল্যাবে আপনারা লাইভ ব্যাকপ্রপাগেশন এবং ক্যালকুলাসের প্রতিটি ধাপ নিজে পরীক্ষা করে দেখতে পারেন।"},
        ],
    },
}

# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"
REQUIRED_PHONETIC = {
    "পার্শিয়াল ডি সি বাই ডি ডাব্লিউ": "dC/dw safeguard",
    "সিগময়েড": "sigmoid safeguard",
    "সিগমা প্রাইম": "sigma-prime safeguard",
    "চেইন রুল": "chain-rule safeguard",
    "ইটা": "eta safeguard",
    "তেরো হাজার দুই": "13,002 safeguard",
}
# Explanatory cue types must read as genuine 2-4 sentence explanations.
EXPLANATORY_TYPES = {"p", "formula-box", "callout-purple", "callout-blue",
                     "callout-gold", "callout-green"}


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
            if cue["type"] in EXPLANATORY_TYPES:
                sentences = [s for s in cue["tts"].split("।") if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(
                        f"{sec_id} cue {cue['index']}: {cue['type']} has "
                        f"{len(sentences)} sentences (expected 2-4)")

    # Every phonetic safeguard must actually be exercised somewhere.
    joined = "\n".join(c["tts"] for s in SECTIONS_DATA.values() for c in s["cues"])
    for token, label in REQUIRED_PHONETIC.items():
        if token not in joined:
            raise ValueError(f"Missing phonetic {label}: {token!r}")

    # Structural parity guards against the LIVE DOM.
    if len(SECTIONS_DATA) != 4:
        raise ValueError("Expected exactly 4 narrated sections")
    total = 0
    for sec_id, sec in SECTIONS_DATA.items():
        types = [c["type"] for c in sec["cues"]]
        if types != EXPECTED_TYPES[sec_id]:
            raise ValueError(f"{sec_id}: cue type/order mismatch -> {types}")
        if sec["audio_file"] != EXPECTED_AUDIO_FILES[sec_id]:
            raise ValueError(f"{sec_id}: audio_file mismatch")
        if sec["alias"] != EXPECTED_ALIASES[sec_id]:
            raise ValueError(f"{sec_id}: alias mismatch")
        if sec["title"] != EXPECTED_TITLES[sec_id]:
            raise ValueError(f"{sec_id}: title mismatch")
        indices = [c["index"] for c in sec["cues"]]
        if indices != list(range(len(indices))):
            raise ValueError(f"{sec_id}: cue indices are not 0..n-1")
        if len(indices) != EXPECTED_COUNT[sec_id]:
            raise ValueError(f"{sec_id}: expected {EXPECTED_COUNT[sec_id]} cues")
        total += len(indices)
    if total != 26:
        raise ValueError(f"Expected 26 cues, found {total}")


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
        "alias": sec["alias"],
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
    new_html, count = pattern.subn(
        lambda m: m.group(1) + str(int(m.group(2)) + 1), html)
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
        "lesson": "lesson_04",
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
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == len(EXPECTED_TYPES[sec_id])
        assert [c["type"] for c in msec["cues"]] == EXPECTED_TYPES[sec_id]
        assert msec["alias"] == EXPECTED_ALIASES[sec_id]
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
    assert total_cues == 26

    print("\n" + "=" * 70)
    print("BUILD COMPLETE - expressive teacher audio, Neural Networks Lesson 04")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<34} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTIONS_DATA)} sections, "
          f"{total_ms / 1000.0:.2f}s.")
    print("  manifest.json is valid JSON; all 4 mp3 files exist and are non-empty.")
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
  function rawType(node) {
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
  // Manifest callout-purple/blue/gold normalise to the DOM's base .callout.
  function normType(t) {
    return (typeof t === 'string' && t.indexOf('callout-') === 0) ? 'callout' : t;
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
      blocks.push({element: node, raw: rawType(node), type: normType(rawType(node)),
                   tex: anns, text: node.innerText || ''});
    }
    dom.push({id: el.id, blocks});
  }

  const engine = ne.sections.map(s => ({
    id: s.id, blockCount: s.blocks.length, cueCount: s.cues.length,
    audioFile: s.audioFile,
    rawTypes: s.blocks.map(b => rawType(b.element)),
    types: s.blocks.map(b => normType(rawType(b.element)))
  }));

  return {
    manifestPresent: !!manifest,
    hasStudioAudio: !!ne.hasStudioAudio,
    manifestKeys: Object.keys(manifest ? manifest.sections : {}),
    manifest: manifest,
    dom: dom.map(s => ({id: s.id,
                        rawTypes: s.blocks.map(b => b.raw),
                        types: s.blocks.map(b => b.type),
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
    BENIGN_FAILED = ("youtube.com/embed/", "3b1b_nn_04_full_dubbed.mp4")
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
    # Manifest callout variants are compared to the DOM's NORMALISED .callout
    # type; the raw callout-* classes are checked separately below.
    tsections = data["manifest"]["sections"]
    total_cues = 0
    dup_check = set()
    disallowed = set()
    forbidden_hits = []
    total_ms = 0.0
    tex_total = 0
    for sec_id in EXPECTED_TYPES:
        msec = tsections[sec_id]
        dom_sec = next(s for s in data["dom"] if s["id"] == sec_id)
        eng_sec = next(s for s in data["engine"] if s["id"] == sec_id)
        cues = msec["cues"]
        expected_types = EXPECTED_TYPES[sec_id]
        norm_expected = [("callout" if t.startswith("callout-") else t)
                         for t in expected_types]

        assert len(cues) == EXPECTED_COUNT[sec_id], (sec_id, len(cues))
        assert len(dom_sec["types"]) == len(cues), (sec_id, "DOM block count", dom_sec["types"])
        assert [c["type"] for c in cues] == expected_types, (sec_id, "manifest types")
        # Raw DOM callout variants must survive (callout-purple/blue/gold).
        assert dom_sec["rawTypes"] == expected_types, (sec_id, "DOM raw types", dom_sec["rawTypes"])
        assert dom_sec["types"] == norm_expected, (sec_id, "DOM normalised types", dom_sec["types"])
        assert eng_sec["types"] == norm_expected, (sec_id, "engine types", eng_sec["types"])
        assert eng_sec["rawTypes"] == expected_types, (sec_id, "engine raw types", eng_sec["rawTypes"])
        assert eng_sec["blockCount"] == len(cues) == eng_sec["cueCount"], sec_id
        assert eng_sec["audioFile"].endswith(EXPECTED_AUDIO_FILES[sec_id]), (sec_id, eng_sec["audioFile"])
        assert msec["alias"] == EXPECTED_ALIASES[sec_id], (sec_id, "alias")

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
            if c["type"] in EXPLANATORY_TYPES:
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
    assert not disallowed, f"Disallowed cue types: {disallowed}"
    assert not forbidden_hits, f"Artificial figure label found: {forbidden_hits}"
    assert tex_total > 0, "No KaTeX <annotation> nodes were extracted from the DOM"

    # No quiz / media-tab anywhere in the narrated manifest or DOM cue types.
    all_dom_types = [t for s in data["dom"] for tt in (s["types"], s["rawTypes"]) for t in tt]
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
    print("VERIFIED: 26/26 cues, DOM<->manifest 1:1 (callout-normalised), 0 dups, "
          "0 quiz/media-tab types, non-zero mp3s, valid JSON, 0 page errors "
          "(uncaught JS), 0 failed audio resources, 0 'চিত্র প্রদর্শনী'.")


if __name__ == "__main__":
    main()
