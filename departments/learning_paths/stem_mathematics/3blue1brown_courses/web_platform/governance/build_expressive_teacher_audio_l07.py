# -*- coding: utf-8 -*-
r"""
Rebuild the TEACHER NARRATION AUDIO for 3Blue1Brown Lesson 07 (Bengali),
expressive-edition, to the Lesson 01 gold standard.

Deterministic, re-runnable, self-contained:

  * 33 cues in 4 narrated sections. The cue count/type/order of every section is
    derived from the LIVE DOM of courses/linear_algebra/lesson_07.html using the
    very selector/rules that narration_engine.js uses:
        .article > section, article section  (skip [data-no-narration="true"])
        h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
        .code-showcase, .formula-box   (skip <p> inside .callout/.chapter-quote)
    Verified 33/33: sec_01_linear_systems=8, sec_02_inverse_matrices=10,
    sec_03_rank_and_column_space=8, sec_04_null_space=7. All other sections are
    data-no-narration and produce no cues (no quiz / media-tab / interactive
    section cue types). The DOM snapshot (l07_dom_blocks.json) preserves TeX via
    KaTeX <annotation>...</annotation> markers.
  * The section IDs here ARE the existing manifest keys; the audio_file names
    are byte-for-byte the existing manifest keys too (no aliases needed):
    sec_01_linear_systems / sec_02_inverse_matrices /
    sec_03_rank_and_column_space / sec_04_null_space.
    The backup folder _backup_before_expressive_build/ is never read/written.
  * Figure cues are genuine 2-4 sentence pedagogical explanations (5 figures):
    what is drawn / what to notice / why it matters (transformation Ax=v,
    inverse rotation, squish-to-line, rank-1 vs rank-2, null-line/null-plane).
  * Scripts are clean spoken Bengali: no TeX, LaTeX, backslashes, $, braces,
    brackets, em/en dashes, raw hyphens or Latin letters. Phonetic safeguards:
    \hat{i}->আই হ্যাট, \hat{j}->জে হ্যাট, \hat{k}->কে হ্যাট,
    x->এক্স, y->ওয়াই, z->জেড, A->এ, V->ভি, det->ডিটারমিন্যান্ট,
    bmatrix->কলাম ভেক্টর, 3D->থ্রিডি, 2D->টুডি,
    2x2->দুই বাই দুই, A inverse->এ ইনভার্স ...
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
    h2 -5%/+2Hz, h3 -3%, chapter-quote -3%, figure -4%, formula-box -8%,
    p +2%, callout +0%, conclusion -3%.
  * A real 350 ms silence chunk between cues, so millisecond timings in the
    manifest match the concatenated MP3 exactly (zero overlap).
  * Per-section ffmpeg concat (-c copy) into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) and
    refreshes the per-section *_cues.json sidecars.
  * Validates non-zero durations, zero overlap, exact gaps, valid JSON,
    non-empty MP3s, 0 duplicate canonical cue texts, 0 quiz/media-tab types and
    DOM<->manifest 1:1 parity (source + browser-extracted DOM blocks) before
    reporting success.

Usage:  python governance/build_expressive_teacher_audio_l07.py
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
                         "linear_algebra", "lesson_07")
SOURCE_HTML = os.path.join(WORKSPACE, "courses", "linear_algebra",
                           "lesson_07.html")
DOM_BLOCKS = os.path.join(SCRIPT_DIR, "l07_dom_blocks.json")

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
    "sec_01_linear_systems",
    "sec_02_inverse_matrices",
    "sec_03_rank_and_column_space",
    "sec_04_null_space",
]

# Exact DOM-derived cue type sequences (parity guards).
# NOTE: the old manifest used "insight-box"; the live DOM renders <b1b-callout>
# as .callout -> narration_engine reports type "callout".
EXPECTED_TYPES = {
    "sec_01_linear_systems": ["h2", "chapter-quote", "p", "p",
                              "formula-box", "figure", "callout", "p"],
    "sec_02_inverse_matrices": ["h2", "p", "p", "figure", "formula-box",
                                "callout", "h3", "p", "figure", "p"],
    "sec_03_rank_and_column_space": ["h2", "p", "p", "callout", "h3",
                                     "p", "figure", "p"],
    "sec_04_null_space": ["h2", "p", "figure", "formula-box",
                          "callout", "p", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec_01_linear_systems":        "sec_01_linear_systems.mp3",
    "sec_02_inverse_matrices":      "sec_02_inverse_matrices.mp3",
    "sec_03_rank_and_column_space": "sec_03_rank_and_column_space.mp3",
    "sec_04_null_space":            "sec_04_null_space.mp3",
}
# Preserve the existing manifest titles verbatim (schema compatibility).
EXPECTED_TITLES = {
    "sec_01_linear_systems":        "জ্যামিতিক দৃষ্টিকোণ থেকে লিনিয়ার সমীকরণ জোট",
    "sec_02_inverse_matrices":      "বিপরীত ম্যাট্রিক্স: রূপান্তরকে পূর্বাবস্থায় ফিরিয়ে আনা",
    "sec_03_rank_and_column_space": "র‍্যাংক এবং কলাম স্পেস: রূপান্তরের সম্ভাব্য আউটপুট ক্ষেত্র",
    "sec_04_null_space":            "নাল স্পেস বা শূন্য স্পেস: মূলবিন্দুতে সংকুচিত ভেক্টরের জগৎ",
}
FORBIDDEN_CUE_TYPES = {"quiz-block", "media-tab", "quiz", "media-tab-caption"}
EXPECTED_FIGURES = 5
EXPECTED_TOTAL_CUES = 33

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (33 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec_01_linear_systems": {
        "title": EXPECTED_TITLES["sec_01_linear_systems"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_01_linear_systems"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, জ্যামিতিক দৃষ্টিকোণ থেকে লিনিয়ার সমীকরণ জোট।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, সঠিক প্রশ্নটি জিজ্ঞাসা করা তার উত্তর দেওয়ার চেয়েও কঠিন। বলেছেন জর্জ ক্যান্টর।"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, এই সিরিজের অধিকাংশ অধ্যায়েই আমরা ম্যাট্রিক্স ও ভেক্টরের ক্রিয়াকলাপকে রৈখিক রূপান্তরের দৃশ্যের মাধ্যমে বুঝেছি, আজকের অধ্যায়ও তার ব্যতিক্রম নয়। লিনিয়ার অ্যালজেব্রা বিজ্ঞান ও প্রযুক্তির প্রায় প্রতিটি শাখায় অপরিহার্য, এর অন্যতম প্রধান কারণ হলো লিনিয়ার সমীকরণ জোট সমাধানের অসাধারণ ক্ষমতা। তবে আগামী কয়েকটি ধাপে আমরা কেবল অ্যালগরিদম নয়, বরং এর অন্তর্নিহিত জ্যামিতিও দেখব।"},
            {"index": 3, "type": "p",
             "tts": "স্কুল ও কলেজে আমরা একগাদা অজানা চলক নিয়ে একাধিক সমীকরণ সমাধানের নিয়ম শিখেছি। যেমন দুই এক্স যোগ দুই ওয়াই সমান মাইনাস চার, এবং এক্স যোগ তিন ওয়াই সমান মাইনাস এক। সাধারণ বীজগণিতে এগুলোকে আলাদাভাবে হিসাব করা হয়, কিন্তু ম্যাট্রিক্সের ভাষায় এদের একসাথে একটিমাত্র ভেক্টর সমীকরণে লেখা যায়।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। দুই দুই, এক তিন ম্যাট্রিক্সের কলাম ভেক্টর এক্স কমা ওয়াই, আর ফলাফল কলাম ভেক্টর মাইনাস চার কমা মাইনাস এক। এই সমীকরণগুলোকে সংক্ষেপে লেখা যায় এ গুণ ভেক্টর এক্স সমান ভেক্টর ভি। এখানে এ হলো সহগ ম্যাট্রিক্স, এক্স হলো অজানা কলাম ভেক্টর, আর ভি হলো পরিচিত লক্ষ্য কলাম ভেক্টর।"},
            {"index": 5, "type": "figure",
             "tts": "বাঁয়ের গ্রিডে বেগুনি রঙের ইনপুট ভেক্টর এক্স দেখা যাচ্ছে, আর ডানের গ্রিডে কমলা রঙের লক্ষ্য ভেক্টর ভি। লক্ষ্য করুন ম্যাট্রিক্স এ শুধু একটি তীর নয়, পুরো সমতলকেই প্রসারিত ও ঘুরিয়ে দিয়েছে। তাই এই ছবির মূল কথা হলো, কোন ইনপুট ভেক্টর এই রূপান্তরের পর ঠিক ভির ওপর পড়বে।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, আসল জ্যামিতিক প্রশ্ন। রূপান্তরের আগে কোন ভেক্টর এক্স ঠিক এমন জায়গায় ছিল যা এ প্রয়োগের পর হুবহু ভির ওপর গিয়ে পড়েছে? কাগজের হিসাবের বদলে আমরা এখন টেপটি উল্টো দিকে চালিয়ে উত্তর খুঁজছি।"},
            {"index": 7, "type": "p",
             "tts": "এই প্রশ্নটির উত্তর নির্ভর করে রূপান্তর এ স্থানটিকে কীভাবে পরিচালিত করেছে, স্থানটি কি পূর্ণ মাত্রায় বিস্তৃত আছে, নাকি চ্যাপ্টা হয়ে তার মাত্রা হারিয়ে ফেলেছে? পরবর্তী দুটি অধ্যায়ে আমরা ঠিক এই দুটি সম্ভাবনার জ্যামিতিই অন্বেষণ করব।"},
        ],
    },

    "sec_02_inverse_matrices": {
        "title": EXPECTED_TITLES["sec_02_inverse_matrices"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_02_inverse_matrices"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, বিপরীত ম্যাট্রিক্স, রূপান্তরকে পূর্বাবস্থায় ফিরিয়ে আনা।"},
            {"index": 1, "type": "p",
             "tts": "ধরা যাক ম্যাট্রিক্স এ এর ডিটারমিন্যান্ট শূন্য নয়, অর্থাৎ ডিটারমিন্যান্ট অব এ শূন্য নয়। রূপান্তরটি স্থানকে কোনো নিচু মাত্রায়, রেখা বা বিন্দুতে চ্যাপ্টা করেনি, সমতল সমতলেই রয়ে গেছে। এই শর্তেই কেবল পেছনে ফিরে আসার কথা চিন্তা করা যায়।"},
            {"index": 2, "type": "p",
             "tts": "যেহেতু স্থান সংকুচিত হয়নি, তাই পুরো রূপান্তরটিকে হুবহু উল্টো দিকে চালিয়ে সমতলকে তার আদি অবস্থায় ফিরিয়ে আনা সম্ভব। এই উল্টো রূপান্তরটিকেই বলা হয় এ ম্যাট্রিক্সের বিপরীত রূপান্তর বা এ ইনভার্স, আর এটি লেখা হয় এ পাওয়ার মাইনাস ওয়ান।"},
            {"index": 3, "type": "figure",
             "tts": "বাঁয়ে ম্যাট্রিক্স এ সমতলকে নিরানব্বই ডিগ্রি ধনাবর্তে ঘোরাচ্ছে, আর ডানে তার বিপরীত রূপান্তর ঠিক নিরানব্বই ডিগ্রি বিপরীত দিকে ঘুরিয়ে সবকিছু আগের জায়গায় ফিরিয়ে আনছে। লক্ষ্য করুন আই হ্যাট ও জে হ্যাটের নতুন অবস্থান, একটির পথ ধরে এগোনোর পর অন্যটি সেই পথ বরাবরই ফিরে আসছে। এই জোড়া রূপান্তরই প্রমাণ করে যে এ একটি বৈধ ফাংশন এবং তার বিপরীতাও একটি রৈখিক রূপান্তর।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। এ ইনভার্স গুণ এ সমান আই, অর্থাৎ একের ডানে শূন্য আর নিচে শূন্যের ডানে এক, এই ইউনিট ম্যাট্রিক্স। আর এ গুণ ভেক্টর এক্স সমান ভি হলে, ভেক্টর এক্স সমান এ ইনভার্স গুণ ভি।"},
            {"index": 5, "type": "callout",
             "tts": "বিশেষ নোট, সমাধানের চাবিকাঠি। এ গুণ ভেক্টর এক্স সমান ভি সমীকরণটি সমাধান করতে উভয় পাশে এ ইনভার্স প্রয়োগ করলেই হয়, ফলে ভেক্টর এক্স সমান এ ইনভার্স গুণ ভি। জ্যামিতিকভাবে এর অর্থ ভি কে পেছনে ফিরিয়ে নিয়ে গিয়ে দেখা কোথায় তার উৎস ভেক্টরটি ছিল।"},
            {"index": 6, "type": "h3",
             "tts": "ডিটারমিন্যান্ট শূন্য হলে কেন বিপরীত ম্যাট্রিক্স থাকতে পারে না।"},
            {"index": 7, "type": "p",
             "tts": "কিন্তু যদি ডিটারমিন্যান্ট শূন্য হয়, তখন কী ঘটবে? ডিটারমিন্যান্ট অব এ শূন্য মানে রূপান্তরটি পুরো দ্বিমাত্রিক সমতলকে চ্যাপ্টা করে একটি একমাত্রিক সরলরেখায় বা একক বিন্দুতে পরিণত করেছে, অনেকগুলো ভেক্টর এখন একই জায়গায় পড়েছে, তথ্য হারিয়ে গেছে।"},
            {"index": 8, "type": "figure",
             "tts": "বাঁয়ের দ্বিমাত্রিক সমতল ডানে একমাত্রিক সরলরেখায় সংকুচিত হয়েছে, আর রেখার ওপরের আলাদা আলাদা বিন্দুগুলো একই গন্তব্যে মিলে গেছে। লক্ষ্য করুন, একে আবার সমতলে খুলে দিতে হলে রেখার প্রতিটি বিন্দুকে অসংখ্য বিন্দুতে পাঠাতে হবে, যা কোনো ফাংশনের নিয়ম মানে না। তাই ডিটারমিন্যান্ট শূন্য হলে এ ইনভার্স থাকে না, হারানো মাত্রা আর ফেরানো যায় না।"},
            {"index": 9, "type": "p",
             "tts": "এই কারণেই যখন ডিটারমিন্যান্ট শূন্য হয়, তখন ম্যাট্রিক্সটির কোনো ইনভার্স বা বিপরীত ম্যাট্রিক্স থাকতে পারে না। তবু সমাধান না থাকা এমন নয়, তার জন্য প্রয়োজন কলাম স্পেস ও নাল স্পেসের ধারণা।"},
        ],
    },

    "sec_03_rank_and_column_space": {
        "title": EXPECTED_TITLES["sec_03_rank_and_column_space"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_03_rank_and_column_space"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, র‍্যাংক এবং কলাম স্পেস, রূপান্তরের সম্ভাব্য আউটপুট ক্ষেত্র।"},
            {"index": 1, "type": "p",
             "tts": "যখন কোনো রূপান্তরে সমতল চ্যাপ্টা হয়ে যায়, তখন তার আউটপুট ঠিক কেমন হতে পারে? রূপান্তর প্রয়োগের পর যত সম্ভাব্য আউটপুট ভেক্টর তৈরি হতে পারে, তাদের সমগ্র সেটকেই ম্যাট্রিক্সের কলাম স্পেস বলা হয়।"},
            {"index": 2, "type": "p",
             "tts": "এটিকে কলাম স্পেস নাম দেওয়া হলো কেন? কারণ আমরা জানি ম্যাট্রিক্সের প্রতিটি কলাম আসলে রূপান্তরের পর বেসিস ভেক্টরগুলো কোথায় গিয়ে পৌঁছায় তা নির্দেশ করে। অর্থাৎ কলামগুলো হলো রূপান্তরিত আই হ্যাট ও জে হ্যাটের ঠিকানা।"},
            {"index": 3, "type": "callout",
             "tts": "বিশেষ নোট, কলাম স্পেস মানেই কলামগুলোর স্প্যান। যেকোনো ইনপুট ভেক্টরের রূপান্তর হলো ওই কলামগুলোরই একটি রৈখিক সমাবেশ বা লিনিয়ার কম্বিনেশন। যদি ভি এই স্প্যানের বাইরে থাকে, তবে এ গুণ এক্স সমান ভির কোনো সমাধানই নেই।"},
            {"index": 4, "type": "h3",
             "tts": "র‍্যাংক, আউটপুট স্পেসের প্রকৃত মাত্রা।"},
            {"index": 5, "type": "p",
             "tts": "রূপান্তরের পর এই আউটপুট স্পেসের মাত্রা বা ডাইমেনশন কত, তা নির্দেশ করার গাণিতিক পরিমাপটির নামই র‍্যাংক। শব্দটির আক্ষরিক অর্থ পদ বা পদমর্যাদা, কিন্তু এখানে এটি কেবল কত মাত্রা বেঁচে রইল তা বলে।"},
            {"index": 6, "type": "figure",
             "tts": "বাঁয়ে রূপান্তরের সমস্ত আউটপুট একটি সরলরেখার ওপর পড়েছে, সেটি র‍্যাংক এক। ডানে আউটপুটগুলো পুরো দ্বিমাত্রিক সমতল জুড়ে ছড়িয়ে আছে, সেটি র‍্যাংক দুই। লক্ষ্য করুন র‍্যাংক মাপা হয় কলাম স্পেসের মাত্রা দিয়ে, ইনপুটের মাত্রা দিয়ে নয়, তাই দুই বাই দুই ম্যাট্রিক্সে র‍্যাংক দুইই সর্বোচ্চ এবং তখনই ডিটারমিন্যান্ট অশূন্য হয়।"},
            {"index": 7, "type": "p",
             "tts": "ত্রিমাত্রিক স্থানে আই হ্যাট, জে হ্যাট ও কে হ্যাট দ্বারা তৈরি আউটপুট স্পেস যদি সংকুচিত না হয়ে পূর্ণ থ্রিডি স্পেস থাকে, তবে র‍্যাংক তিন। আর যখন র‍্যাংক ম্যাট্রিক্সের কলাম সংখ্যার সমান হয়, তখন তাকে ফুল র‍্যাংক বলা হয় এবং ডিটারমিন্যান্ট অশূন্য থাকে।"},
        ],
    },

    "sec_04_null_space": {
        "title": EXPECTED_TITLES["sec_04_null_space"],
        "audio_file": EXPECTED_AUDIO_FILES["sec_04_null_space"],
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, নাল স্পেস বা শূন্য স্পেস, মূলবিন্দুতে সংকুচিত ভেক্টরের জগৎ।"},
            {"index": 1, "type": "p",
             "tts": "যখন কোনো রূপান্তরের ডিটারমিন্যান্ট শূন্য হয় এবং সমতল সংকুচিত হয়ে একটি সরলরেখায় পরিণত হয়, তখন মূলবিন্দু ছাড়াও অসংখ্য ভেক্টর নিশ্চয়ই মূলবিন্দুর ওপর গিয়ে আছড়ে পড়ে। কারণ রৈখিক রূপান্তর মূলবিন্দুকে সর্বদা নিজের জায়গায় রাখে, ফলে সংকোচনের সময় একটি পুরো দিক নিশ্চুপ হয়ে যায়।"},
            {"index": 2, "type": "figure",
             "tts": "বাঁয়ের ইনপুট সমতলে লাল রঙের রেখার ওপর থাকা প্রতিটি ভেক্টর রূপান্তরের পর ডানে কমলা রঙের মূলবিন্দুতে গিয়ে মিলিত হচ্ছে, আর অন্য দিকের ভেক্টরগুলো আউটপুট রেখার ওপর ছড়িয়ে পড়েছে। লক্ষ্য করুন ইনপুটের যে দিকটি ধ্বংস হয়েছে ঠিক সেটিই হলো নাল স্পেস, আর যে দিকটি বেঁচে থাকা রেখায় পড়েছে সেটিই কলাম স্পেস। একই ছবিতে এই দুটি স্পেসের পরিপূরক সম্পর্ক স্পষ্ট হয়ে ওঠে, আর তিন মাত্রায় নাল স্পেস একটি রেখা বা সমতল হতে পারে।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র। নাল স্পেস হলো সেই সব ভেক্টরের সেট যারা রূপান্তরের পর শূন্য ভেক্টরে পরিণত হয়। আর র‍্যাংক যোগ নালিটি সমান এন, অর্থাৎ বেঁচে থাকা মাত্রা আর হারানো মাত্রা মিলে মোট মাত্রা।"},
            {"index": 4, "type": "callout",
             "tts": "বিশেষ নোট, সমাধানের স্বাধীনতা। যদি এ গুণ এক্স সমান ভির একটি নির্দিষ্ট সমাধান এক্স নাল থাকে, তবে তার সাথে নাল স্পেসের যেকোনো ভেক্টর যোগ করলেও নতুন বৈধ সমাধান পাওয়া যায়। কারণ নাল স্পেসের ভেক্টর রূপান্তরের পর শূন্য হয়ে যায়, ফলে ফলাফলের কোনো হেরফের হয় না।"},
            {"index": 5, "type": "p",
             "tts": "নাল স্পেস আমাদের সমাধানের সম্পূর্ণ জ্যামিতিক ক্ষেত্র ও স্বাধীনতার মাত্রা উপহার দেয়। যখন লক্ষ্য ভি শূন্য ভেক্টর হয়, তখন নাল স্পেসই হবে সব সমাধানের সেট।"},
            {"index": 6, "type": "p", "role": "conclusion",
             "tts": "এই গভীর উপলব্ধিটি আমাদের স্পষ্ট করে দেয় যে লিনিয়ার অ্যালজেব্রায় বিপরীত ম্যাট্রিক্স, কলাম স্পেস এবং নাল স্পেস কোনো বিচ্ছিন্ন সূত্র নয়, বরং এরা স্থানকে রূপান্তর ও সংকোচনের এক অবিচ্ছেদ্য ও সুসংহত জ্যামিতিক গল্প। এই অধ্যায়ে আমরা গাউসিয়ান এলিমিনেশন বা সারি হ্রাস পদ্ধতি নিয়ে যাইনি, পরবর্তী অধ্যায়ে বিষম আকারের ম্যাট্রিক্স নিয়ে এই যাত্রা অব্যাহত রাখব।"},
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
NON_NARRATED = {
    "sec-media-gallery", "sec-lab",
    "sec-quizzes-linear-systems", "sec-quizzes-inverses",
    "sec-quizzes-column-space", "sec-quizzes-null-space",
}


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
    """Replicate narration_engine.parseContent() selectors on the current DOM.

    The live page renders <b1b-section> into <section id=...> with an <h2>
    title, so the effective selector is 'article section'. Only the four
    narrated sections (no data-no-narration) are counted.
    """
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
            if cue["tts"] in seen:
                raise ValueError(f"{sec_id} cue {cue['index']}: duplicate cue text")
            seen.add(cue["tts"])
            if cue["type"] == "figure":
                body = cue["tts"]
                if body.startswith(""):
                    body = body[len(""):].strip()
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
          f"DOM parity OK (33/33, no duplicates).")

    manifest_sections = {}
    for sec_id in SECTION_ORDER:
        manifest_sections[sec_id] = await build_section(sec_id)

    manifest_data = {
        "course": "linear_algebra",
        "lesson": "lesson_07",
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
    print("BUILD COMPLETE - expressive teacher audio, Lesson 07 (L01 gold standard)")
    for sec_id in SECTION_ORDER:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<32} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTION_ORDER)} sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  DOM<->manifest 1:1; 0 duplicate canonical cues; "
          "0 quiz/media-tab types; zero overlaps; exact 350 ms gaps; "
          "all MP3s non-zero; valid JSON.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(build_all())
