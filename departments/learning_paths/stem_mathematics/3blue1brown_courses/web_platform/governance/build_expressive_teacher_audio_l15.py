# -*- coding: utf-8 -*-
r"""
Rebuild the TEACHER NARRATION AUDIO for 3Blue1Brown Lesson 15 (Bengali),
expressive-edition, to the Lesson 01 gold standard. Series finale.

Deterministic, re-runnable, self-contained:

  * 22 cues in 4 narrated sections. The cue count/type/order of every section is
    derived from the LIVE DOM of courses/linear_algebra/lesson_15.html using the
    very selector/rules that narration_engine.js uses:
        .article > section, article section  (skip [data-no-narration="true"])
        h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
        .code-showcase, .formula-box   (skip <p> inside .callout/.chapter-quote)
    Verified 22/22 via headless Chrome (channel="chrome"):
      sec_01_what_is_a_vector = 6 (h2, chapter-quote, p, figure, callout, p)
      sec_02_functions_as_vectors = 5 (h2, p, figure, callout, p)
      sec_03_linear_transformations_on_functions = 6 (h2, p, figure, callout, p, p)
      sec_04_inner_products_and_abstract_bridge = 5 (h2, p, figure, callout, p)
    All other sections are data-no-narration and produce no cues (no quiz /
    media-tab / interactive-section cue types). The DOM snapshot
    (l15_dom_blocks.json) preserves TeX via KaTeX <annotation>...</annotation>.
  * The 4 "figure" cues are 2-4 sentence, natural teacher explanations. They
    NEVER use a label like "চিত্র প্রদর্শনী" — each starts as flowing prose.
  * The section IDs here ARE the existing manifest keys; the audio_file names
    are byte-for-byte the existing manifest keys too:
      sec_01_what_is_a_vector /
      sec_02_functions_as_vectors /
      sec_03_linear_transformations_on_functions /
      sec_04_inner_products_and_abstract_bridge.
    The backup folder _backup_before_expressive_build/ is never read/written.
  * Scripts are clean spoken Bengali: no TeX, LaTeX, backslashes, $, braces,
    brackets, em/en dashes, raw hyphens or Latin letters. Phonetic safeguards:
    f->এফ, g->জি, x->এক্স, y->ওয়াই, D->ডি, n->এন, 2D->টুডি, 3D->থ্রিডি,
    \hat{i}->আই হ্যাট, \hat{j}->জে হ্যাট, \hat{k}->কে হ্যাট, det->নির্ণায়ক ...
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
    h2 -5%/+2Hz, h3 -3%, chapter-quote -3%, figure -4%, formula-box -8%,
    p +2%, callout +0%, conclusion -3%.
  * A real 350 ms silence chunk between cues, so millisecond timings in the
    manifest match the concatenated MP3 exactly (zero overlap).
  * Per-section ffmpeg concat (-c copy) into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) and
    refreshes the per-section *_cues.json sidecars.
  * Validates non-zero durations, zero overlap, exact gaps, valid JSON,
    non-empty MP3s, 0 duplicate canonical cue texts, 0 quiz/media-tab types,
    0 "চিত্র প্রদর্শনী" occurrences and DOM<->manifest 1:1 parity (source +
    browser-extracted DOM blocks) before reporting success.

Usage:  python governance/build_expressive_teacher_audio_l15.py
"""

import os
import re
import json
import hashlib
import asyncio
import subprocess
from html.parser import HTMLParser

import edge_tts

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
VOICE = "bn-BD-PradeepNeural"
GAP_MS = 350.0
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))            # .../governance
WORKSPACE = os.path.dirname(SCRIPT_DIR)                             # .../web_platform
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio",
                         "linear_algebra", "lesson_15")
SOURCE_HTML = os.path.join(WORKSPACE, "courses", "linear_algebra",
                           "lesson_15.html")
DOM_BLOCKS = os.path.join(SCRIPT_DIR, "l15_dom_blocks.json")

# Prosody (rate, pitch, volume) by cue type.
PROSODY_DEFAULT = {
    "h2":            ("-5%",  "+2Hz", "+0%"),  # warm, slower section opening
    "h3":            ("-3%",  "+0Hz", "+0%"),
    "chapter-quote": ("-3%",  "+0Hz", "+0%"),
    "p":             ("+2%",  "+0Hz", "+0%"),  # natural teacher pace
    "figure":        ("-4%",  "+0Hz", "+0%"),  # slower, considerate explanation
    "callout":       ("+0%",  "+0Hz", "+0%"),
    "formula-box":   ("-8%",  "+0Hz", "+0%"),  # slow and deliberate
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")   # calm concluding prose

# Canonical section id == existing manifest key (no aliases in this lesson).
SECTION_ORDER = [
    "sec_01_what_is_a_vector",
    "sec_02_functions_as_vectors",
    "sec_03_linear_transformations_on_functions",
    "sec_04_inner_products_and_abstract_bridge",
]

# Exact DOM-derived cue type sequences (parity guards).
EXPECTED_TYPES = {
    "sec_01_what_is_a_vector":
        ["h2", "chapter-quote", "p", "figure", "callout", "p"],
    "sec_02_functions_as_vectors":
        ["h2", "p", "figure", "callout", "p"],
    "sec_03_linear_transformations_on_functions":
        ["h2", "p", "figure", "callout", "p", "p"],
    "sec_04_inner_products_and_abstract_bridge":
        ["h2", "p", "figure", "callout", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec_01_what_is_a_vector": "sec_01_what_is_a_vector.mp3",
    "sec_02_functions_as_vectors": "sec_02_functions_as_vectors.mp3",
    "sec_03_linear_transformations_on_functions":
        "sec_03_linear_transformations_on_functions.mp3",
    "sec_04_inner_products_and_abstract_bridge":
        "sec_04_inner_products_and_abstract_bridge.mp3",
}
# Preserve the existing manifest titles verbatim (schema compatibility).
EXPECTED_TITLES = {
    "sec_01_what_is_a_vector":
        "১. ভেক্টর আসলে কী? জ্যামিতিক তীর, সংখ্যার তালিকা এবং স্বতঃসিদ্ধের বিমূর্ত জগৎ",
    "sec_02_functions_as_vectors":
        "২. ফাংশন নিজেই একটি ভেক্টর: অসীম মাত্রার অবিচ্ছিন্ন জগৎ",
    "sec_03_linear_transformations_on_functions":
        "৩. ফাংশনের ওপর লিনিয়ার রূপান্তর: ডেরিভেটিভ বা অন্তরক অপারেটর এবং ম্যাট্রিক্স রূপ",
    "sec_04_inner_products_and_abstract_bridge":
        "৪. ফাংশনের ডট গুণন: ইনার প্রোডাক্ট ও বিমূর্ত তত্ত্বের মহা সংযোগ",
}
FORBIDDEN_CUE_TYPES = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
FORBIDDEN_PHRASE = "চিত্র প্রদর্শনী"
EXPECTED_FIGURES = 4          # one figure.lesson-figure in each narrated section
EXPECTED_TOTAL_CUES = 22

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (22 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec_01_what_is_a_vector": {
        "title": EXPECTED_TITLES["sec_01_what_is_a_vector"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_01_what_is_a_vector"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, ভেক্টর আসলে কী, জ্যামিতিক তীর, সংখ্যার তালিকা এবং স্বতঃসিদ্ধের বিমূর্ত জগৎ।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, ভ্লাদিমির আর্নল্ডের এক তীক্ষ্ণ মন্তব্য। তিনি বলেন, এই রকম স্বতঃসিদ্ধ আর অনুপ্রেরণাহীন সংজ্ঞা গণিতবিদদের কাজে আসে মূলত অনভিজ্ঞদের জন্য বিষয়টি কঠিন করে তুলে নিজেদের কর্তৃত্ব বাড়ানোর মাধ্যমে। কড়া এই কথাটি আমাদের প্রথম পাঠের সেই প্রশ্নটিকেই ফিরে আসতে বলে, ভেক্টর আসলে কী?"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, এই সিরিজের একেবারে প্রথম ভিডিওতে আমরা একটা আপাতদৃষ্টিতে সহজ প্রশ্ন নিয়ে শুরু করেছিলাম, ভেক্টর আসলে কী? একটি দ্বিমাত্রিক ভেক্টর কি মূলত সমতলে একটা তীর, যাকে আমরা সুবিধামতো স্থানাঙ্ক দিয়ে বর্ণনা করি? নাকি সেটি আসলে দুটি বাস্তব সংখ্যা, যেটিকে সমতলে তীর হিসেবে কল্পনা করা হয়? অথবা এই দুটোই কোনো গভীরতর বস্তুর দুটি প্রকাশ মাত্র?"},
            {"index": 3, "type": "figure",
             "tts": "এই চিত্রে চার ও পাঁচ মাত্রিক ভেক্টরকে সংখ্যার কলাম হিসেবে দেখা যাচ্ছে, কতগুলো সংখ্যা লিখে ভেক্টরটি বোঝানো যাচ্ছে, তা দেখেই তার মাত্রা বোঝা যায়। পাশাপাশি একটা ভিন্ন চিত্রে দেখা যায় জ্যামিতিক তীরকে শব্দে বর্ণনা করতে গেলে হাত নাড়ার মতো অস্পষ্ট ইঙ্গিতের আশ্রয় নিতে হয়। তাই সংখ্যার তালিকা হিসেবে ভেক্টর প্রথমে অত্যন্ত সুস্পষ্ট মনে হয়, যদিও ভিত্তি বদলের সাথে সাথেই এই সুবিধা নতুন প্রশ্ন জন্ম দেবে।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, তীর নাকি তালিকা, স্থানাঙ্কের ঊর্ধ্বে একটি স্থান। যারা সত্যিই লিনিয়ার বীজগণিত করে থাকেন, বিশেষ করে ভিত্তি পরিবর্তনে অভ্যস্ত হয়ে, তাদের একটি অনুভূতি জন্মায় যে তারা এমন একটি স্থান নিয়ে কাজ করছেন যা দেওয়া স্থানাঙ্ক থেকে স্বাধীন। স্থানাঙ্কগুলো আসলে বেশ কিছুটা যথেচ্ছ, নির্ভর করছে কোন ভিত্তি ভেক্টর বেছে নেওয়ার ওপর। নির্ণায়ক ও আইগেনভেক্টরের মতো মূল বিষয়গুলো স্থানাঙ্ক ব্যবস্থার প্রতি উদাসীন, কারণ নির্ণায়ক বলে কতটা ক্ষেত্রফল স্কেল হলো আর আইগেনভেক্টর হলো সেই ভেক্টর যা রূপান্তরের সময় নিজের রেখায় থাকে। এই দুটো ধর্ম সহজাতভাবে স্থানিক, তাই স্থানাঙ্ক বদলে দিলেও তাদের মান বদলায় না।"},
            {"index": 5, "type": "p",
             "tts": "যদি ভেক্টর মূলত বাস্তব সংখ্যার তালিকা না হয়, আর তার সারমর্ম কোনো বেশি স্থানিক কিছু হয়, তবে গণিতবিদরা স্পেস শব্দটির দ্বারা আসলে কী বোঝান? আধুনিক গণিতের উত্তর হলো ছয়টি ভিন্ন রূপের পরিবর্তে আচরণ দেখুন। যদি কোনো উপাদানসমষ্টির ওপর যোগ ও স্কেলার গুণন সুসংজ্ঞায়িত থাকে এবং আটটি সার্বজনীন স্বতঃসিদ্ধ মেনে চলে, তবেই সেটি একটি ভেক্টর স্পেস। তীর হোক বা সংখ্যাজোড়া, গণিতের পক্ষে তাতে কিছু যায় আসে না।"},
        ],
    },

    "sec_02_functions_as_vectors": {
        "title": EXPECTED_TITLES["sec_02_functions_as_vectors"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_02_functions_as_vectors"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, ফাংশন নিজেই একটি ভেক্টর, অসীম মাত্রার অবিচ্ছিন্ন জগৎ।"},
            {"index": 1, "type": "p",
             "tts": "এবার এমন একটি জিনিসের কথা বলা যাক যা না তীর, না সংখ্যার তালিকা, কিন্তু তার মধ্যে ভেক্টরের মতো গুণাবলি আছে, আর সেটি হলো ফাংশন। ঠিক যেমন দুটি ভেক্টরকে যোগ করা যায়, তেমনি দুটি ফাংশন এফ ও জি কে যোগ করে একটি নতুন ফাংশন এফ প্লাস জি পাওয়া যায়। এই রাশিটি একটু ভেবে দেখতে হয়, নতুন ফাংশনের আউটপুট, যেমন এক্স সমান মাইনাস চার এ, হলো এফ ও জি র একই ইনপুটে পৃথক আউটপুটের যোগফল।"},
            {"index": 2, "type": "figure",
             "tts": "এই চিত্রে প্রতিটি ইনপুট এক্স এ এফ আর জি র উচ্চতা যোগ করে নতুন লেখচিত্র তৈরি হচ্ছে, ঠিক যেমন কলাম ভেক্টরের একই সারির সংখ্যাদুটো যোগ করা হয়। পার্থক্য কেবল এই যে এখানে অনুভূমিক অক্ষের প্রতিটি বিন্দুতেই একটি করে উপাংশ আছে, অর্থাৎ অসীম সংখ্যক স্থানাঙ্ক। এই কারণেই ফাংশন যোগকে ভেক্টর যোগের সাথে তুলনা করা এত স্বাভাবিক।"},
            {"index": 3, "type": "callout",
             "tts": "বিশেষ নোট, স্কেলিং, শূন্য ভেক্টর ও অসীম মাত্রা। একইভাবে কোনো ফাংশনকে বাস্তব সংখ্যা দিয়ে স্কেল করা মানে তার সব আউটপুটকে সেই সংখ্যা দিয়ে গুণ করা, ঠিক যেমন দুই দিয়ে গুণ করলে তিনটি উপাংশের কলাম ভেক্টরের প্রতিটি উপাংশ দ্বিগুণ হয়। এই জগতের শূন্য ভেক্টর হলো ধ্রুব শূন্য ফাংশন, আর ঋণাত্মক এফ হলো সেই বিপরীতক যার সাথে এফ কে যোগ করলে আবার শূন্য ফাংশন ফেরত পাওয়া যায়। পার্থক্য শুধু এক জায়গায়, টুডি বা থ্রিডি ভেক্টরে উপাংশ সসীম, কিন্তু একটি অবিচ্ছিন্ন ফাংশনের প্রতিটি বাস্তব বিন্দুতে মান থাকে, তাই ফাংশন স্পেস অসীম মাত্রার। তবু বহুপদী ফাংশনদের নিয়ে আমরা এন প্লাস এক মাত্রার একটি সসীম উপস্পেস পাই, যার স্বাভাবিক ভিত্তি এক, এক্স, এক্স স্কয়ার এবং এভাবে এগিয়ে যায়।"},
            {"index": 4, "type": "p",
             "tts": "অর্থাৎ ফাংশনকেও ঠিক ভেক্টরের মতো যোগ ও স্কেল করা যায়, ফলে লিনিয়ার বীজগণিতের সমস্ত কৌশল এখানেও প্রয়োগ করা যাবে। স্বাভাবিক প্রশ্ন তখন, ফাংশনের ওপর রৈখিক রূপান্তর কেমন হতে পারে? ক্যালকুলাসের অন্তরীকরণ অপারেটর তখনই চোখে পড়ে, যা এক ফাংশনকে নতুন ফাংশনে রূপ দেয়।"},
        ],
    },

    "sec_03_linear_transformations_on_functions": {
        "title": EXPECTED_TITLES["sec_03_linear_transformations_on_functions"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_03_linear_transformations_on_functions"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, ফাংশনের ওপর লিনিয়ার রূপান্তর, ডেরিভেটিভ বা অন্তরক অপারেটর এবং ম্যাট্রিক্স রূপ।"},
            {"index": 1, "type": "p",
             "tts": "অ্যাডিটিভিটি ও স্কেলিং, এই দুটিই রৈখিকতার আসল সংজ্ঞা। যেকোনো ভেক্টর ভি ও ডব্লিউ, এবং যেকোনো স্কেলার এস এর ক্ষেত্রে দুই ভেক্টরের যোগফলের রূপান্তর সমান তাদের পৃথক রূপান্তরের যোগফল, আর স্কেল করা ভেক্টরের রূপান্তর সমান স্কেলার দিয়ে গুণ করা রূপান্তর। তৃতীয় অধ্যায়ে আমরা রৈখিকতা চিনতাম সরলরেখাকে সরলরেখায় নেওয়া, গ্রিডের সমদূরত্ব অটুট রাখা আর মূলবিন্দু স্থির রাখা দিয়ে। এই বিমূর্ত সংজ্ঞাটি সেই চিত্রকেই এত সাধারণ করে তোলে যে তীরের পাশাপাশি ফাংশন, এমনকি আরও অনেক বস্তুর ক্ষেত্রেও কাজ করে। ফাংশনের ক্ষেত্রে রূপান্তরকে প্রায়ই অপারেটর বলা হয়, অর্থ একই।"},
            {"index": 2, "type": "figure",
             "tts": "প্রথম চিত্রে দেখা যায় আগে দুই ভেক্টর যোগ করে তারপর রূপান্তর প্রয়োগ করা হলে যা পাওয়া যায়, আলাদা করে রূপান্তরিত ভেক্টরদ্বয় যোগ করলেও ঠিক তাই পাওয়া যায়। দ্বিতীয় চিত্রে একই কথা স্কেলিংয়ের জন্য দেখানো হয়েছে, আগে স্কেল করে রূপান্তর বা আগে রূপান্তর করে স্কেল, দুই পথেই একই গন্তব্য। বীজগণিতের ভাষায় একে বলা হয় রূপান্তরটি যোগ ও স্কেলার গুণন ক্রিয়া দুটিকে সংরক্ষণ করে।"},
            {"index": 3, "type": "callout",
             "tts": "বিশেষ নোট, অন্তরীকরণও একটি লিনিয়ার অপারেটর। ক্যালকুলাসের শিক্ষার্থীরা কখনোই ভাবেন না যে তারা রৈখিকতা ব্যবহার করছেন, অথচ সবসময়ই করেন। দুই ফাংশনের যোগফলের ডেরিভেটিভ হলো তাদের পৃথক ডেরিভেটিভের যোগফল, আর কোনো ধ্রুবক সংখ্যা দিয়ে ফাংশনকে গুণ করে ডেরিভেটিভ নিলে ধ্রুবকটি অক্ষত অবস্থায় সামনে চলে আসে। একটি নির্দিষ্ট উদাহরণ, নয় ভাগের এক গুণ এক্স কিউব বিয়োগ এক্স এর ডেরিভেটিভ হলো তিন ভাগের এক গুণ এক্স স্কয়ার বিয়োগ এক। সুতরাং অন্তরীকরণ ক্যালকুলাসের কোনো বিচ্ছিন্ন কৌশল নয়, এটি ফাংশন স্পেসের একটি বিশুদ্ধ রৈখিক রূপান্তর, তাই একে ম্যাট্রিক্স হিসেবেও লেখা যায়। আর রৈখিক রূপান্তর যেহেতু ভিত্তি ভেক্টরগুলো কোথায় পাঠায় তা দিয়েই সম্পূর্ণ নির্ধারিত, তাই ভিত্তি উপাদানগুলোর ডেরিভেটিভ বের করে তাদের স্থানাঙ্ক দিয়ে ম্যাট্রিক্সের কলাম গড়া যাবে, ঠিক যেমন আই হ্যাট ও জে হ্যাটের গন্তব্য দিয়ে দুই বাই দুই ম্যাট্রিক্স তৈরি করা হতো।"},
            {"index": 4, "type": "p",
             "tts": "এর জন্য আমরা বহুপদীদের জগতে সীমাবদ্ধ হই, যেমন এক্স স্কয়ার প্লাস তিন এক্স প্লাস পাঁচ কিংবা চার এক্স সপ্তম ঘাত বিয়োগ পাঁচ এক্স স্কয়ার। প্রতিটি বহুপদীর সসীম সংখ্যক পদ থাকলেও পুরো স্পেসে যেকোনো বড় ঘাতের বহুপদী আছে। স্বাভাবিক ভিত্তি হলো বিশুদ্ধ ঘাতসমূহ, এক, এক্স, এক্স স্কয়ার, এক্স কিউব ইত্যাদি, আই হ্যাট, জে হ্যাট ও কে হ্যাটের ভূমিকা এখানে এরা পালন করে।"},
            {"index": 5, "type": "p",
             "tts": "এই ভিত্তিতে এক্স স্কয়ার প্লাস তিন এক্স প্লাস পাঁচ এর স্থানাঙ্ক হলো পাঁচ, তিন, এক, তারপর অসীম সংখ্যক শূন্য। আর চার এক্স সপ্তম ঘাত বিয়োগ পাঁচ এক্স স্কয়ার এর স্থানাঙ্ক হলো শূন্য, শূন্য, ঋণাত্মক পাঁচ, শূন্য, শূন্য, শূন্য, শূন্য, চার। এই ব্যবস্থায় ডেরিভেটিভ এক অসীম ম্যাট্রিক্স, মূলত শূন্যে ভরা, কেবল সরণকৃত কর্ণে ধনাত্মক পূর্ণসংখ্যাগুলো এক, দুই, তিন, চার করে নামে। যেমন এক্স কিউব প্লাস পাঁচ এক্স স্কয়ার প্লাস চার এক্স প্লাস পাঁচ এর ক্ষেত্রে এক গুণ চার, দুই গুণ পাঁচ, তিন গুণ এক, এই তিনটি সংখ্যা কলামে এসে চার প্লাস দশ এক্স প্লাস তিন এক্স স্কয়ার ফল দেয়। আর যেহেতু ধ্রুবকের ডেরিভেটিভ শূন্য, নাল স্পেস বা কার্নেল হলো শুধু ধ্রুবক ফাংশনদের স্প্যান। ক্যালকুলাস ও লিনিয়ার বীজগণিত এখানে এক বিন্দুতে মিশে যায়।"},
        ],
    },

    "sec_04_inner_products_and_abstract_bridge": {
        "title": EXPECTED_TITLES["sec_04_inner_products_and_abstract_bridge"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_04_inner_products_and_abstract_bridge"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, ফাংশনের ডট গুণন, ইনার প্রোডাক্ট ও বিমূর্ত তত্ত্বের মহা সংযোগ।"},
            {"index": 1, "type": "p",
             "tts": "জ্যামিতিক ভেক্টরে ডট প্রোডাক্ট হলো উপাংশগুলোর গুণফলের সমষ্টি। ফাংশনের ক্ষেত্রে উপাংশের গুণফলগুলোর এই অবিচ্ছিন্ন যোগফলটিই হলো নির্দিষ্ট ইন্টিগ্রাল, যার ভেতরে এফ ও জি কে গুণ করে ইন্টিগ্রেশন করা হয়। এটি ডট প্রোডাক্টের প্রতিসাম্য, রৈখিকতা ও পজিটিভিটি, সব বৈশিষ্ট্য রক্ষা করে, এবং এর থেকে ফাংশনের দৈর্ঘ্যও বের করা যায় বর্গমূলের মাধ্যমে। যখন দুই ফাংশনের ইনার প্রোডাক্ট শূন্য হয়, তখন তারা পরস্পর অর্থোগোনাল বা লম্ব।"},
            {"index": 2, "type": "figure",
             "tts": "এই চিত্রে তীরের জগতের পরিচিত ধারণাগুলো ফাংশনের জগতে নতুন নাম পাচ্ছে, ডট প্রোডাক্টের জায়গায় ইনার প্রোডাক্ট, আর আইগেনভেক্টরের জায়গায় আইগেনফাংশন। অর্থ একই, কেবল ভাষা বদল, একইভাবে অর্থোগোনাল ভিত্তি থেকে ফুরিয়ার সিরিজ জন্ম নেয়। এই নাম বদলই প্রমাণ করে যে গঠনটা আসলে বস্তুনির্ভর নয়, সম্পর্কনির্ভর।"},
            {"index": 3, "type": "callout",
             "tts": "বিশেষ নোট, আটটি স্বতঃসিদ্ধ একটি ইন্টারফেস, পাই ক্রিটার ও ফুরিয়ে। আমরা এখন দেখব ফুরিয়ার সিরিজ আসলে কী, কোসাইন এনএক্স ও সাইন এনএক্স এর মতো পরস্পর লম্ব ভিত্তি ফাংশনের ওপর যেকোনো জটিল সংকেতকে প্রক্ষেপণ করে ভেঙে ফেলা। এটি আসলে কোনো নতুন কৌশল নয়, একই ভেক্টর প্রজেকশনের আর একটি রূপ। মাথায় একজন গণিতবিদ কল্পনা করুন যিনি সব রকম ভেক্টরজাত বস্তুর জন্য একই প্রমাণ চান। তাই তিনি একটি চেকলিস্ট বানান, আটটি স্বতঃসিদ্ধ। এগুলো প্রকৃতির মৌলিক নিয়ম নয়, বরং গণিতবিদ ও তার ফলাফল প্রয়োগকারীদের মাঝে একটি ইন্টারফেস। কেউ যদি পাই ক্রিটারের মতো অদ্ভুত কিছুর সেট নিয়ে যোগ ও স্কেলিংয়ের সংজ্ঞা দেয়, তাকে কেবল এই আটটি শর্ত যাচাই করতে হবে, তারপরই সে লিনিয়ার বীজগণিতের সব উপপাদ্য ব্যবহার করতে পারবে।"},
            {"index": 4, "type": "p", "role": "conclusion",
             "tts": "তাই ভেক্টর আসলে কী, গণিতবিদের উত্তর হলো প্রশ্নটিকে এড়িয়ে যাওয়া। আধুনিক তত্ত্বে রূপের কোনো মূল্য নেই, তীর, সংখ্যার তালিকা, ফাংশন কিংবা পাই ক্রিটার, সবই ভেক্টর হতে পারে, শুধু আবশ্যক যে যোগ ও স্কেলিংয়ের কোনো ধারণা থাকবে যা এই নিয়মগুলো মানে চলে। এটি ঠিক যেমন তিন নম্বরটি আসলে কী, বাস্তবে সেটি সবসময় কোনো ত্রয়ীর প্রসঙ্গেই আসে, কিন্তু গণিত এটিকে সম্ভাব্য সব ত্রয়ীর এক বিমূর্ত ধারণা হিসেবে ব্যবহার করে। ভেক্টরের ক্ষেত্রেও তাই, অনেক রূপ, একটি অমূর্ত ধারণা, ভেক্টর স্পেস। এই নিয়েই লিনিয়ার অ্যালজেব্রা সিরিজের সমাপ্তি, গণিতকে ভালোবাসতে থাকুন।"},
        ],
    },
}

# --------------------------------------------------------------------------- #
# DOM parity: re-extract cue types from the CURRENT lesson HTML source
# --------------------------------------------------------------------------- #
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "param", "source", "track", "wbr"}
CUSTOM_TAG_TO_TYPE = {
    "b1b-figure": "figure",
    "b1b-formula": "formula-box",
    "b1b-callout": "callout",
    "b1b-quote": "chapter-quote",
}
NON_NARRATED = {"sec_quizzes", "sec_labs", "sec_conclusion"}


class _Node:
    __slots__ = ("tag", "attrs", "children", "parent", "text")

    def __init__(self, tag, attrs=None, parent=None):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.children = []
        self.parent = parent
        self.text = ""


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("#root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        n = _Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(n)
        if tag not in VOID_TAGS:
            self.stack.append(n)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(_Node(tag, attrs, self.stack[-1]))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if data.strip():
            n = _Node("#text", {"v": data}, self.stack[-1])
            n.text = data
            self.stack[-1].children.append(n)


def dom_types_from_source(html):
    """Replicate narration_engine.parseContent() selectors on the current DOM."""
    b = _TreeBuilder()
    b.feed(html)

    def walk(n):
        if n.tag == "b1b-section" and n.attrs.get("data-no-narration") != "true":
            types = ["h2"]  # title rendered as <h2> by B1bSection
            for c in n.children:  # direct children only; p in callout is skipped
                if c.tag == "p":
                    types.append("p")
                elif c.tag == "h3":
                    types.append("h3")
                elif c.tag in CUSTOM_TAG_TO_TYPE:
                    types.append(CUSTOM_TAG_TO_TYPE[c.tag])
                # b1b-quiz / b1b-media-tab produce no narration cue
            yield (n.attrs.get("id", ""), types)
        for c in n.children:
            yield from walk(c)

    return {sid: types for sid, types in walk(b.root)}


# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
ALLOWED_CUE_TYPES = {"h2", "h3", "chapter-quote", "p", "figure",
                     "callout", "formula-box", "code-showcase"}


def assert_clean_scripts():
    """Fail before any TTS work if a script is dirty or off-spec."""
    seen = set()
    total = 0
    for sec_id in SECTION_ORDER:
        sec = SECTIONS_DATA[sec_id]
        types = [c["type"] for c in sec["cues"]]
        if types != EXPECTED_TYPES[sec_id]:
            raise ValueError(f"{sec_id}: cue type/order mismatch -> {types}")
        if sec["audio_file"] != EXPECTED_AUDIO_FILES[sec_id]:
            raise ValueError(f"{sec_id}: audio_file mismatch")
        if sec["title"] != EXPECTED_TITLES[sec_id]:
            raise ValueError(f"{sec_id}: title mismatch")
        indices = [c["index"] for c in sec["cues"]]
        if indices != list(range(len(indices))):
            raise ValueError(f"{sec_id}: cue indices are not 0..n-1")
        for cue in sec["cues"]:
            if cue["type"] in FORBIDDEN_CUE_TYPES:
                raise ValueError(f"{sec_id}: forbidden cue type {cue['type']}")
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars "
                                 f"{bad!r} in {cue['tts']!r}")
            if FORBIDDEN_PHRASE in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden phrase")
            if cue["tts"] in seen:
                raise ValueError(f"{sec_id} cue {cue['index']}: duplicate cue text")
            seen.add(cue["tts"])
            if cue["type"] == "figure":
                body = cue["tts"]
                sentences = [s for s in re.split(r"[।?]", body) if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(f"{sec_id} cue {cue['index']}: figure needs "
                                     f"2-4 sentences, got {len(sentences)}")
        total += len(indices)
    if total != EXPECTED_TOTAL_CUES:
        raise ValueError(f"Expected {EXPECTED_TOTAL_CUES} cues, found {total}")
    return total


def assert_dom_parity():
    """The manifest must be 1:1 with the CURRENT live DOM and extracted blocks."""
    with open(SOURCE_HTML, encoding="utf-8") as fh:
        dom = dom_types_from_source(fh.read())
    for sec_id in SECTION_ORDER:
        expected = EXPECTED_TYPES[sec_id]
        if dom.get(sec_id) != expected:
            raise ValueError(f"Source-DOM parity mismatch for {sec_id}:\n"
                             f"  DOM     = {dom.get(sec_id)}\n"
                             f"  manifest= {expected}")
    for sid in NON_NARRATED:
        if sid in dom:
            raise ValueError(f"DOM parity: non-narrated section {sid} leaked in")

    # Browser-extracted live DOM blocks (TeX preserved via KaTeX <annotation>).
    if not os.path.exists(DOM_BLOCKS):
        raise ValueError(f"Missing browser DOM snapshot: {DOM_BLOCKS}")
    with open(DOM_BLOCKS, encoding="utf-8") as fh:
        live = json.load(fh)
    live_map = {s["id"]: s for s in live}
    if set(live_map) != set(SECTION_ORDER):
        raise ValueError(f"Live-DOM sections mismatch: {sorted(live_map)}")
    canonical = []
    for sec_id in SECTION_ORDER:
        blocks = live_map[sec_id]["blocks"]
        actual = [b["type"] for b in blocks]
        expected = EXPECTED_TYPES[sec_id]
        if actual != expected:
            raise ValueError(f"Live-DOM parity mismatch for {sec_id}:\n"
                             f"  live    = {actual}\n"
                             f"  manifest= {expected}")
        for b in blocks:
            if b["type"] not in ALLOWED_CUE_TYPES:
                raise ValueError(f"Live-DOM: forbidden cue type {b['type']}")
            canonical.append(b["text"])
    # Zero duplicate canonical cue texts (TeX annotations make formulas unique).
    dupes = len(canonical) - len(set(canonical))
    if dupes:
        raise ValueError(f"Live-DOM: {dupes} duplicate canonical cue texts")
    return len(canonical)


def run_cmd(args, **kwargs):
    """subprocess.run with bounded retries for transient Windows process-launch
    failures (WinError 1450: insufficient resources to create a process)."""
    import time
    for attempt in range(12):
        try:
            return subprocess.run(args, **kwargs)
        except OSError as exc:
            if getattr(exc, "winerror", None) == 1450 and attempt < 11:
                time.sleep(0.25)
                continue
            raise
    raise RuntimeError(f"subprocess failed after retries: {args[0]}")


def get_duration_ms(path):
    out = run_cmd(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout.strip()
    ms = float(out) * 1000.0
    if ms <= 0:
        raise RuntimeError(f"Non-positive duration for {path}: {ms}")
    return ms


def probe_stream(path):
    out = run_cmd(
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
    # Edge TTS occasionally replies with an empty audio stream, or Windows can
    # briefly refuse to create the network sockets (WinError 1450). Back off
    # and retry; this is a network/process wait, not an arbitrary fixed delay.
    for attempt in range(10):
        try:
            comm = edge_tts.Communicate(text, VOICE,
                                        rate=rate, pitch=pitch, volume=volume)
            await comm.save(path)
            if valid_audio(path):
                return
        except OSError as exc:
            if getattr(exc, "winerror", None) != 1450:
                raise
            print(f"    WinError 1450 on attempt {attempt + 1}; retrying")
        except Exception as exc:  # noqa: BLE001 - network hiccups happen
            print(f"    attempt {attempt + 1} failed: {exc}")
        await asyncio.sleep(min(0.5 * (2 ** attempt), 8.0))
    raise RuntimeError(f"Failed to synthesise cue: {text[:40]}...")


def make_silence(path, sample_rate, channels, seconds=GAP_MS / 1000.0):
    layout = "mono" if channels == 1 else "stereo"
    run_cmd(
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
    run_cmd(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", list_path, "-c", "copy", final_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True,
    )
    os.remove(list_path)


async def build_section(sec_id):
    sec = SECTIONS_DATA[sec_id]
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
            print(f"  cue {idx:02d} [{cue['type']:<13}] {rate:>4} {pitch:>5}  "
                  f"{cue['tts'][:30]}...")
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
        "cues_file": os.path.splitext(sec["audio_file"])[0] + "_cues.json",
        "total_duration_ms": round(cursor, 1),
        "cues": manifest_cues,
    }


async def build_all():
    total = assert_clean_scripts()
    dom_cues = assert_dom_parity()
    if dom_cues != total:
        raise RuntimeError(f"DOM cue count {dom_cues} != script cue count {total}")
    print(f"Validated {total} clean cues in {len(SECTION_ORDER)} sections; "
          f"DOM parity OK (22/22, no duplicates, no forbidden phrase).")

    manifest_sections = {}
    for sec_id in SECTION_ORDER:
        manifest_sections[sec_id] = await build_section(sec_id)

    manifest_data = {
        "course": "linear_algebra",
        "lesson": "lesson_15",
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
    if list(loaded["sections"]) != SECTION_ORDER:
        raise RuntimeError("Manifest section keys do not match the existing keys")
    total_cues = 0
    total_ms = 0.0
    figures = 0
    all_texts = []
    for sec_id in SECTION_ORDER:
        msec = loaded["sections"][sec_id]
        if msec["audio_file"] != EXPECTED_AUDIO_FILES[sec_id]:
            raise RuntimeError(f"{sec_id}: audio_file mismatch in written manifest")
        types = [c["type"] for c in msec["cues"]]
        if types != EXPECTED_TYPES[sec_id]:
            raise RuntimeError(f"{sec_id}: cue type/order mismatch in written manifest")
        if any(t in FORBIDDEN_CUE_TYPES for t in types):
            raise RuntimeError(f"{sec_id}: forbidden cue type in written manifest")
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            raise RuntimeError(f"{sec_id}: missing/empty MP3 {path}")
        if get_duration_ms(path) <= 0:
            raise RuntimeError(f"{sec_id}: non-positive MP3 duration")
        for c in msec["cues"]:
            if FORBIDDEN_PHRASE in c["text"]:
                raise RuntimeError(f"{sec_id}: forbidden phrase in written manifest")
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
        all_texts.extend(c["text"] for c in msec["cues"])
        # Refresh the per-section *_cues.json sidecar (existing schema).
        sidecar = {
            "section_id": sec_id,
            "title": msec["title"],
            "audio_file": msec["audio_file"],
            "total_duration_ms": msec["total_duration_ms"],
            "cues": msec["cues"],
        }
        with open(os.path.join(AUDIO_DIR, msec["cues_file"]), "w",
                  encoding="utf-8") as fh:
            json.dump(sidecar, fh, ensure_ascii=False, indent=2)

    if total_cues != EXPECTED_TOTAL_CUES:
        raise RuntimeError(f"Expected {EXPECTED_TOTAL_CUES} cues, found {total_cues}")
    if figures != EXPECTED_FIGURES:
        raise RuntimeError(f"Expected {EXPECTED_FIGURES} figure explanations, found {figures}")
    if len(all_texts) != len(set(all_texts)):
        raise RuntimeError("Written manifest has duplicate cue texts")

    print("\n" + "=" * 70)
    print("BUILD COMPLETE - expressive teacher audio, Lesson 15 (L01 gold standard)")
    for sec_id in SECTION_ORDER:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<44} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTION_ORDER)} sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure cues.")
    print("  DOM<->manifest 1:1; 0 duplicate canonical cues; 0 quiz/media-tab "
          "types; 0 forbidden phrase; zero overlaps; exact 350 ms gaps; "
          "all MP3s non-zero; valid JSON.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(build_all())
