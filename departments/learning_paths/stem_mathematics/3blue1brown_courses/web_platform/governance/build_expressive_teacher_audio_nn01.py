# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Neural Networks Lesson 01
("But what is a neural network?", Bengali) to the Lesson-01 gold standard.

Deterministic, re-runnable, self-contained:

  * 31 cues in 5 narrated sections with EXACTLY the same section IDs,
    audio_file names, cue types and cue order as the existing manifest.
    The non-narrated sec-network-lab (data-no-narration) is NOT included.
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time), so the build is fully reproducible.
  * Figure cues are genuine 2-4 sentence natural Bengali explanations; the
    artificial label "চিত্র প্রদর্শনী" is explicitly forbidden and checked.
  * Phonetic safeguards: 784 -> "সাত আট চার", 13,002 -> "তের হাজার দুই",
    sigmoid -> "সিগময়েড"; no TeX, Latin letters, dashes or markup.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, chapter-quote -3%, p +2%, figure -4%, callout +0%,
      formula-box -8%, conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with the
    exact-ms timings and the exact existing section keys (no added aliases).
  * Bumps the page's manifest.js cache-buster to the next version.
  * Verifies with headless Chrome (channel=chrome): 31/31 cues, DOM <-> manifest
    1:1 parity, 0 duplicates, 0 quiz/media-tab cue types, non-zero mp3s, valid
    JSON, 0 page errors and 0 occurrences of "চিত্র প্রদর্শনী".

Usage:
    python governance/build_expressive_teacher_audio_nn01.py            # build + verify
    python governance/build_expressive_teacher_audio_nn01.py --verify-only
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
                         "neural_networks", "lesson_01")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "neural_networks", "lesson_01.html")
MANIFEST_TITLE = "অধ্যায় ০১ — নিউরাল নেটওয়ার্ক আসলে কী?"

# Prosody keyed by cue type: (rate, pitch, volume)
PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
    "h3":            ("-3%", "+0Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),
    "p":             ("+2%", "+0Hz", "+0%"),   # natural teacher pace
    "figure":        ("-4%", "+0Hz", "+0%"),   # slower, considerate explanation
    "callout-purple":("+0%", "+0Hz", "+0%"),
    "callout-blue":  ("+0%", "+0Hz", "+0%"),
    "callout-gold":  ("+0%", "+0Hz", "+0%"),
    "formula-box":   ("-8%", "+0Hz", "+0%"),   # slow and deliberate
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")     # calm concluding prose

# Cue types that the narration engine is allowed to emit (quiz / media-tab are
# deliberately absent; the lab section is data-no-narration).
ALLOWED_CUE_TYPES = set(PROSODY_DEFAULT) | {"conclusion"}

# Parity guards: exact cue-type sequence expected for each narrated section.
# These are the DOM block types produced by narration_engine.parseContent(),
# with the callout variant taken from the rendered class (callout-<variant>).
EXPECTED_TYPES = {
    "sec-intro-mnist":        ["h2", "chapter-quote", "p", "figure", "p", "callout-purple"],
    "sec-neuron-layers":      ["h2", "p", "formula-box", "p", "figure", "callout-blue"],
    "sec-weights-biases":     ["h2", "p", "formula-box", "p", "figure", "callout-gold", "p"],
    "sec-matrix-formulation": ["h2", "p", "formula-box", "p", "figure", "callout-purple"],
    "sec-parameter-counting": ["h2", "p", "formula-box", "p", "figure", "callout-blue"],
}
EXPECTED_AUDIO_FILES = {
    "sec-intro-mnist":        "sec_01_intro_mnist.mp3",
    "sec-neuron-layers":      "sec_02_neuron_layers.mp3",
    "sec-weights-biases":     "sec_03_weights_biases.mp3",
    "sec-matrix-formulation": "sec_04_matrix_formulation.mp3",
    "sec-parameter-counting": "sec_05_parameter_counting.mp3",
}
EXPECTED_COUNT = {
    "sec-intro-mnist": 6, "sec-neuron-layers": 6, "sec-weights-biases": 7,
    "sec-matrix-formulation": 6, "sec-parameter-counting": 6,
}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (31 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-intro-mnist": {
        "title": "ভূমিকা: হস্তাক্ষর সংখ্যা ও মস্তিষ্কের বিস্ময়",
        "audio_file": "sec_01_intro_mnist.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, একটি তিন চেনার রহস্য ও ভিজ্যুয়াল কর্টেক্স।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, মস্তিষ্কের দৃষ্টিশক্তি এক অদ্ভুত মায়াবী ইন্দ্রজাল। অগোছালো পিক্সেলের স্তূপ থেকেও মানুষের মন এক লহমায় বিমূর্ত অর্থ উদ্ধার করতে পারে। বলেছেন গ্রান্ট স্যান্ডারসন।"},
            {"index": 2, "type": "p",
             "tts": "এটি একটি তিন। বেশ অগোছালোভাবে লেখা, আর মাত্র আঠাইশ গুণ আঠাইশ পিক্সেলের অত্যন্ত কম রেজোলিউশনে রেন্ডার করা। তবুও আপনার মস্তিষ্ক কোনো দ্বিধা ছাড়াই একে তিন হিসেবে চিনে ফেলছে। আর এক মুহূর্তের জন্য ভেবে দেখুন, মস্তিষ্ক কত অবলীলায় আর কোনো কষ্ট ছাড়াই এই বিস্ময়কর কাজটি সম্পন্ন করে ফেলে।"},
            {"index": 3, "type": "figure",
             "tts": "পাশের চিত্রে তিনজনের হাতে লেখা তিন দেখা যাচ্ছে, প্রতিটি আঠাইশ গুণ আঠাইশ পিক্সেলের গ্রিডে আঁকা। কোনো দুটির পিক্সেল অবিকল এক নয়, তবুও ওদের মধ্যে একটা পরিচিত গঠন আছে। বাঁকের জায়গা আর খাড়া দাগের অবস্থান আলাদা হলেও দুটি বাঁকের এই প্যাটার্নটি অটুট থাকে। আর এই বিমূর্ত প্যাটার্নটিই আমাদের ভিজ্যুয়াল কর্টেক্স এক পলকেই ধরে ফেলে, আর নেটওয়ার্ককেও তাই শিখতে হবে।"},
            {"index": 4, "type": "p",
             "tts": "কিন্তু কোনো প্রোগ্রামারকে যদি প্রথাগত শর্তভিত্তিক কোড দিয়ে এমন একটি সাধারণ প্রোগ্রাম লিখতে বলা হয় যা আঠাইশ গুণ আঠাইশ পিক্সেলের গ্রিড দেখে বলে দেবে এটি কোন সংখ্যা, তবে সেই কাজটি প্রায় অসম্ভব হয়ে দাঁড়ায়। প্রথাগত নিয়মমাফিক অ্যালগরিদম ব্যর্থ হলেও কৃত্রিম নিউরাল নেটওয়ার্ক মানুষের মস্তিষ্ককে অনুকরণ করে এই সমস্যাটি অবিশ্বাস্য সফলতার সাথে সমাধান করে। আর ঠিক এখানেই আবির্ভাব ঘটে কৃত্রিম নিউরাল নেটওয়ার্কের।"},
            {"index": 5, "type": "callout-purple",
             "tts": "বিশেষ নোট, মূল চ্যালেঞ্জ ও ডিপ লার্নিংয়ের আগমন। ইনপুট স্তরের সাত আট চারটি পিক্সেল থেকে শুরু করে শেষ আউটপুট স্তরে দশটি সংখ্যার সম্ভাব্যতা নির্ণয় করা, আর এটি সম্ভব একটি মাল্টিলেয়ার পারসেপট্রনের মাধ্যমে।"},
        ],
    },

    "sec-neuron-layers": {
        "title": "নিউরন ও স্তরের কাঠামো (Neurons & Layers)",
        "audio_file": "sec_02_neuron_layers.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, নিউরন আসলে কী এবং লেয়ার কীভাবে কাজ করে।"},
            {"index": 1, "type": "p",
             "tts": "শুরুতেই একটি মৌলিক প্রশ্ন, নিউরন আসলে কী? একদম প্রাথমিক পর্যায়ে নিউরনকে কেবল এমন একটি পাত্র ভাবুন যা শূন্য থেকে একের মধ্যবর্তী একটি বাস্তব সংখ্যা ধারণ করে। আর এই সংখ্যাটিকেই বলা হয় নিউরনের অ্যাক্টিভেশন।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, অ্যাক্টিভেশন এ এর মান শূন্য ও একের ব্যবধানে অবস্থান করে। অর্থাৎ নিউরনের ভেতরের এই সংখ্যা কখনো শূন্যের নিচে বা একের উপরে যায় না।"},
            {"index": 3, "type": "p",
             "tts": "যেহেতু আমাদের ছবিতে আঠাইশ গুণ আঠাইশ অর্থাৎ সর্বমোট সাত আট চারটি পিক্সেল রয়েছে, তাই নেটওয়ার্কটি শুরু হয় ইনপুট লেয়ারে সাত আট চারটি নিউরন দিয়ে। প্রতিটি নিউরন সংশ্লিষ্ট পিক্সেলের উজ্জ্বলতা ধারণ করে, কালো পিক্সেলের জন্য শূন্য আর সম্পূর্ণ সাদা পিক্সেলের জন্য এক। নেটওয়ার্কের অপর প্রান্তে থাকে দশটি আউটপুট নিউরন, যা শূন্য থেকে নয় পর্যন্ত প্রতিটি ডিজিটের আত্মবিশ্বাস নির্দেশ করে। মাঝে অবস্থান করে দুটি হিডেন লেয়ার, প্রতিটিতে ষোলোটি করে নিউরন।"},
            {"index": 4, "type": "figure",
             "tts": "এই আর্কিটেকচারের ছবিতে বাঁ দিকে আঠাইশ গুণ আঠাইশ পিক্সেলের ইনপুট থেকে শুরু করে ডান দিকের দশটি সম্ভাব্যতা পর্যন্ত পুরো যাত্রাটি ধরা পড়েছে। সাত আট চারটি ইনপুট নিউরনের পরে দুটি হিডেন লেয়ার আছে, প্রতিটিতে ষোলোটি করে নিউরন। শেষে দশটি আউটপুট নিউরন দাঁড়িয়ে আছে, আর এই তিন স্তরের মধ্যে ছড়ানো সংযোগগুলোই তথ্যের প্রবাহ দেখায়।"},
            {"index": 5, "type": "callout-blue",
             "tts": "বিশেষ নোট, কেন এই স্তরভিত্তিক স্তরবিন্যাস। মানুষ যেমন জটিল অবয়বকে সরল অংশে ভাগ করে দেখে, নিউরাল নেটওয়ার্কের হিডেন লেয়ারগুলোও পর্যায়ক্রমে কাজ করে। প্রথম হিডেন লেয়ার ছোট ছোট প্রান্ত ও কোণ শনাক্ত করে, আর দ্বিতীয় হিডেন লেয়ার লুপ ও রেখাংশ জোড়া লাগিয়ে পূর্ণাঙ্গ ডিজিটের অবয়ব তৈরি করে।"},
        ],
    },

    "sec-weights-biases": {
        "title": "ওজন, বায়াস ও সিগময়েড অ্যাক্টিভেশন",
        "audio_file": "sec_03_weights_biases.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, ওয়েটেড সাম, বায়াস এবং সিগময়েড স্কুইশিং।"},
            {"index": 1, "type": "p",
             "tts": "এক লেয়ারের অ্যাক্টিভেশন কীভাবে পরবর্তী লেয়ারের অ্যাক্টিভেশন নির্ধারণ করে? আমরা প্রথম স্তরের প্রতিটি নিউরনকে পরবর্তী স্তরের প্রতিটি নিউরনের সাথে সংযুক্ত করি, আর প্রতিটি সংযোগের সাথে থাকে একটি সংখ্যা যাকে বলা হয় ওয়েট বা ওজন। দুটি নিউরনের মধ্যকার এই সংযোগের শক্তিই ওজন। ধনাত্মক ওজন পরবর্তী নিউরনকে প্রজ্বলিত করে, আর ঋণাত্মক ওজন তাকে নিস্তেজ রাখে।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, জেড সমান ওয়ান নম্বর ওজন গুণ ওয়ান নম্বর অ্যাক্টিভেশন, প্লাস টু নম্বর ওজন গুণ টু নম্বর অ্যাক্টিভেশন, আর এভাবে অনেকগুলো পদ যোগ হয়ে শেষে বায়াস বি যুক্ত হয়। এক কথায় জেড হলো সমস্ত ওজন ও অ্যাক্টিভেশনের গুণফলের সমষ্টি, তার সাথে বায়াস যোগ করা।"},
            {"index": 3, "type": "p",
             "tts": "বায়াস হলো নিউরনের নিষ্ক্রিয়তা কাটিয়ে সক্রিয় হওয়ার একটি সীমা বা থ্রেশহোল্ড। ধনাত্মক বায়াস নিউরনটিকে সহজে জ্বলে উঠতে উৎসাহিত করে, আর ঋণাত্মক বায়াস তাকে সহজে জ্বলতে দেয় না। কিন্তু এই যোগফল যেকোনো বিশাল বাস্তব সংখ্যা হতে পারে, তাই একে শূন্য ও একের মধ্যে সীমাবদ্ধ রাখার জন্য সিগময়েড ফাংশন দিয়ে সংকুচিত করা হয়। সিগমা অফ জেড সমান এক ভাগের এক যোগ ই টু দ্য পাওয়ার মাইনাস জেড।"},
            {"index": 4, "type": "figure",
             "tts": "এই সিগময়েড বক্ররেখার ছবিতে দেখা যাচ্ছে, বাঁ দিকে বড় ঋণাত্মক ইনপুটে বক্ররেখা শূন্যের কাছে নেমে আসে আর ডান দিকে বড় ধনাত্মক ইনপুটে একের কাছে উঠে যায়। ইনপুট শূন্য হলে আউটপুট ঠিক শূন্য দশমিক পাঁচ, আর মাঝের অংশটি মসৃণভাবে ওঠে। এই স্কুইশিংয়ের কারণেই নিউরনের অ্যাক্টিভেশন সবসময় শূন্য ও একের মধ্যে থাকে।"},
            {"index": 5, "type": "callout-gold",
             "tts": "বিশেষ নোট, আধুনিক অল্টারনেটিভ রেলু বা রেকটিফাইড লিনিয়ার ইউনিট। আধুনিক গভীর নেটওয়ার্কে সিগময়েডের পরিবর্তে ব্যাপকভাবে রেলু ব্যবহার করা হয়, যা ভ্যানিশিং গ্রেডিয়েন্ট সমস্যা দূর করে এবং প্রশিক্ষণকে বহুগুণ দ্রুততর করে। রেলু ঋণাত্মক ইনপুটে শূন্য দেয়, আর ধনাত্মক ইনপুটে মানটিকে অবিকল প্রবাহিত করে।"},
            {"index": 6, "type": "p", "role": "conclusion",
             "tts": "অতএব একটি নিউরনের চূড়ান্ত সক্রিয়তা নির্ধারিত হয় সিগমা অফ ওয়েটেড সাম প্লাস বায়াস সমীকরণের মাধ্যমে। অর্থাৎ প্রথমে সমস্ত ইনপুটের ওয়েটেড সাম বের করা হয়, তারপর বায়াস যোগ করে সিগময়েড দিয়ে মানটিকে শূন্য ও একের ব্যবধানে আনা হয়।"},
        ],
    },

    "sec-matrix-formulation": {
        "title": "লিনিয়ার অ্যালজেব্রা ও ম্যাট্রিক্স রূপায়ন",
        "audio_file": "sec_04_matrix_formulation.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, ম্যাট্রিক্স আর লিনিয়ার অ্যালজেব্রার মাধ্যমে সংহত রূপ।"},
            {"index": 1, "type": "p",
             "tts": "প্রতিটি নিউরনের জন্য আলাদা আলাদা সমীকরণ না লিখে লিনিয়ার অ্যালজেব্রার মাধ্যমে পুরো একটি লেয়ারের গণনা এক লাইনে প্রকাশ করা যায়। পৃথক পৃথক হাজার হাজার সমীকরণ লেখার বদলে লিনিয়ার অ্যালজেব্রা আমাদের এক অসাধারণ নান্দনিক ও কম্প্যাক্ট রূপ প্রদান করে।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, প্রথম স্তরের অ্যাক্টিভেশন ভেক্টর এ সমান সিগমা অফ ওজন ম্যাট্রিক্স ডব্লিউ গুণ শূন্য স্তরের অ্যাক্টিভেশন ভেক্টর এ প্লাস বায়াস ভেক্টর বি। এখানে ডব্লিউ হলো ওজন ম্যাট্রিক্স, এ হলো অ্যাক্টিভেশন ভেক্টর আর বি হলো বায়াস ভেক্টর।"},
            {"index": 3, "type": "p",
             "tts": "ম্যাট্রিক্স ডব্লিউ এর প্রতিটি সারি পরবর্তী লেয়ারের একটি নির্দিষ্ট নিউরনে আগত সমস্ত ওজনকে ধারণ করে, তাই ম্যাট্রিক্স গুণনের ফলে পুরো স্তরের সব নিউরনের ওয়েটেড সাম একসাথে নির্ণয় করা যায়। আর আধুনিক গ্রাফিক্স প্রসেসর বা জিপিইউতে এই গণনা অত্যন্ত দ্রুত সমান্তরালভাবে সম্পন্ন হয়।"},
            {"index": 4, "type": "figure",
             "tts": "এই অ্যানিমেশনে দেখা যাচ্ছে, ওজন ম্যাট্রিক্সের একটি পূর্ণ সারি অ্যাক্টিভেশন ভেক্টরের সাথে গুণ হয়ে একটি একক নিউরনের মান তৈরি করছে। ডব্লিউ এর এক একটি সারি আগের লেয়ারের সাত আট চারটি অ্যাক্টিভেশনের সাথে গুণ হয়ে পরবর্তী লেয়ারের একটিমাত্র নিউরনের ইনপুট ঠিক করে। বায়াস যোগের পর সিগময়েড সেই মানকে আবার শূন্য থেকে একের ব্যবধানে নিয়ে আসে।"},
            {"index": 5, "type": "callout-purple",
             "tts": "বিশেষ নোট, গণিতের সৌন্দর্য। লিনিয়ার অ্যালজেব্রা কেবল গণনা সহজ করে না, এটি নিউরাল নেটওয়ার্কের অভ্যন্তরীণ স্থাপত্যের সাথে অবিচ্ছেদ্যভাবে মিশে আছে। একটি ম্যাট্রিক্সের সারি আর কলামের এই সাজানোই আমাদের বলে দেয় কোন নিউরন কার কাছ থেকে কতটা শক্তি পাবে।"},
        ],
    },

    "sec-parameter-counting": {
        "title": "প্যারামিটার গণনা ও ১৩,০০২টি ডায়ালের রহস্য",
        "audio_file": "sec_05_parameter_counting.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, তের হাজার নব টিউন করার চ্যালেঞ্জ।"},
            {"index": 1, "type": "p",
             "tts": "এই চার স্তরের সাধারণ নেটওয়ার্কটিতে মোট কতগুলো পরিবর্তনশীল প্যারামিটার রয়েছে, আসুন হিসেব করে দেখি।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, মোট ওজন, সাত আট চার গুণ ষোলো যোগ ষোলো গুণ ষোলো যোগ ষোলো গুণ দশ, অর্থাৎ বারো হাজার পাঁচশো চুরাল্লিশ যোগ দুইশো ছাপ্পান্ন যোগ একশো ষাট, মোট বারো হাজার নয়শো ষাটটি ওজন। মোট বায়াস, ষোলো যোগ ষোলো যোগ দশ অর্থাৎ বিয়াল্লিশটি। সর্বমোট বারো হাজার নয়শো ষাট যোগ বিয়াল্লিশ, অর্থাৎ তের হাজার দুইটি প্যারামিটার।"},
            {"index": 3, "type": "p",
             "tts": "যখন আমরা বলি একটি নিউরাল নেটওয়ার্ক শিখছে, তার আক্ষরিক অর্থ হলো এই তের হাজার দুইটি সংখ্যার নিখুঁত মান খুঁজে বের করা, যাতে যেকোনো হস্তাক্ষরের সংখ্যা দিলে সঠিক আউটপুট নিউরনটি সক্রিয় হয়। পরবর্তী অধ্যায়ে আমরা দেখব গ্রেডিয়েন্ট ডিসেন্ট কীভাবে এই নবগুলোকে স্বয়ংক্রিয়ভাবে টিউন করে।"},
            {"index": 4, "type": "figure",
             "tts": "এই ছবিতে কল্পনা করুন, আপনার সামনে সারি সারি ছোট ছোট নব ও স্লাইডার রয়েছে, প্রতিটি এক একটি ওজন বা বায়াসের প্রতীক। প্রশ্ন হলো, গ্রেডিয়েন্ট ডিসেন্ট অ্যালগরিদম কীভাবে এই নবগুলোর সমন্বয় করে সর্বনিম্ন ভুলের বিন্দুতে নিয়ে যায়। আর এই নবগুলোর সঠিক সমন্বয়ই নেটওয়ার্কের শেখার রহস্য।"},
            {"index": 5, "type": "callout-blue", "role": "conclusion",
             "tts": "বিশেষ নোট, উপসংহার, একটি উচ্চমাত্রিক গাণিতিক ফাংশন। নিউরাল নেটওয়ার্ক মূলত এমন এক ফাংশন যা সাত আট চারটি বাস্তব সংখ্যাকে ইনপুট হিসেবে নিয়ে দশটি সম্ভাব্যতা প্রদান করে। এই তের হাজার দুইটি নবের সঠিক সমন্বয়ই আমাদের হস্তাক্ষর সংখ্যা চেনার ক্ষমতা দেয়।"},
        ],
    },
}

# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"
REQUIRED_PHONETIC = {
    "সাত আট চার": "784 safeguard",
    "তের হাজার দুই": "13,002 safeguard",
    "সিগময়েড": "sigmoid safeguard",
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
        if len(indices) != EXPECTED_COUNT[sec_id]:
            raise ValueError(f"{sec_id}: expected {EXPECTED_COUNT[sec_id]} cues")
        total += len(indices)
    if total != 31:
        raise ValueError(f"Expected 31 cues, found {total}")

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
    assert total_cues == 31

    print("\n" + "=" * 66)
    print("BUILD COMPLETE - expressive teacher audio, Neural Networks Lesson 01")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<24} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTIONS_DATA)} sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json is valid JSON; all 5 mp3 files exist and are non-empty.")
    print("=" * 66)


# --------------------------------------------------------------------------- #
# Headless Chrome verification (channel=chrome)
# --------------------------------------------------------------------------- #
VERIFY_JS = r"""() => {
  const ne = window.narrationEngine;
  const manifest = window.TEACHER_AUDIO_MANIFEST;
  const sectionEls = [...document.querySelectorAll('.article > section, article section')];

  // Re-extract DOM blocks with the narration engine's own selector, mapping a
  // rendered node to the same cue type the manifest uses.
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
    report = {}
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

    report["page_errors"] = page_errors
    assert page_errors == [], f"Page errors: {page_errors}"
    assert data["manifestPresent"], "window.TEACHER_AUDIO_MANIFEST missing"
    assert data["hasStudioAudio"], "Studio teacher audio not bound"

    # Section keys 1:1 with the DOM/engine, no extras, no lab section.
    mkeys = data["manifestKeys"]
    dom_ids = [s["id"] for s in data["dom"]]
    assert mkeys == dom_ids, f"Manifest/DOM section mismatch: {mkeys} vs {dom_ids}"
    assert mkeys == list(EXPECTED_TYPES.keys()), f"Unexpected section keys: {mkeys}"
    assert "sec-network-lab" not in mkeys, "Non-narrated lab leaked into manifest"
    lab = [s for s in data["sectionEls"] if s["id"] == "sec-network-lab"]
    assert lab and lab[0]["noNarration"] == "true", "Lab section lost data-no-narration"

    # DOM <-> manifest 1:1: section ids, cue counts and cue type order.
    tsections = data["manifest"]["sections"]
    total_cues = 0
    dup_check = set()
    disallowed = set()
    forbidden_hits = []
    total_ms = 0.0
    figure_count = 0
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

        # TeX annotation must be present for every formula-box block.
        for tex in dom_sec["tex"]:
            assert isinstance(tex, list) and any(t.strip() for t in tex), (sec_id, "missing TeX annotation")

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

    assert total_cues == 31, total_cues
    assert figure_count == 5, figure_count
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
        "total_duration_ms": round(total_ms, 1),
        "total_duration_s": round(total_ms / 1000.0, 2),
        "tex_annotations": sum(len(s["tex"]) for s in data["dom"]),
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
    print("\n" + "=" * 66)
    print("VERIFICATION REPORT (headless Chrome channel=chrome)")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("=" * 66)
    if not report.get("ok"):
        raise SystemExit("VERIFICATION FAILED")
    print("VERIFIED: 31/31 cues, DOM<->manifest 1:1, 0 dups, "
          "0 quiz/media-tab types, non-zero mp3s, valid JSON, 0 page errors, "
          "0 'চিত্র প্রদর্শনী'.")


if __name__ == "__main__":
    main()
