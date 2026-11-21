# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Differential Equations Lesson 05
("The Heat Equation and Fourier Transforms", Bengali) to gold standard.

Deterministic, re-runnable, self-contained:
  * 41 cues in 5 narrated sections with EXACTLY the same section IDs, audio_file
    names, alias and section order as the live narration-engine DOM / manifest.json
    (verified 8/8/7/9/9 for sec-heat-pde-review / sec-boundary-separation /
    sec-sine-harmonics-decay / sec-fourier-orthogonality /
    sec-continuous-fourier-transform). sec-interactive-lab and sec-quizzes carry
    data-no-narration="true" and are deliberately excluded.
  * Section IDs and block types were extracted FIRST from the live DOM through
    narration_engine.js's own selector
    ('h2, h3, p, .chapter-quote, .callout, figure.lesson-figure,
     .code-showcase, .formula-box'), not guessed from prose. Exact DOM callout
    variants (callout-gold / callout-green / callout-purple / callout-red /
    callout-blue) are preserved. See de05_dom_blocks.json.
  * Visual explanations are genuine, natural 2-4 sentence teacher phrasing —
    the artificial label "চিত্র প্রদর্শনী" is never used.
  * Fully phonetic spoken Bengali (no TeX / Latin / markup). Safeguards:
      PDE -> পি ডি ই, ODE -> ও ডি ই, Fourier -> ফুরিয়ার,
      orthogonality -> অর্থোগোন্যালিটি, harmonics -> হারমনিক্স,
      transform -> ট্রান্সফর্ম, entropy -> এন্ট্রপি;
      u(x,t) -> ইউ অব এক্স কমা টি,  du/dt -> ডেল ইউ বাই ডেল টি,
      d2u/dx2 -> ডেল স্কয়ার ইউ বাই ডেল এক্স স্কয়ার,
      e^{...} -> ই টু দ্য পাওয়ার ..., sin -> সাইন.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, chapter-quote -3%, p +2%, figure -4%, callout +0%,
      formula-box -8%, conclusion -3%.
  * A real 350 ms silence chunk between cues, so manifest millisecond timings
    match the concatenated audio exactly.
  * ffmpeg -c copy concat into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST).
  * Bumps the page cache-buster manifest.js?v=N -> ?v=N+1.
  * verify_in_chrome() re-checks everything headlessly with channel=chrome.
  * The _backup_before_expressive_build/ folder is NEVER touched.

Usage:
  python governance/build_expressive_teacher_audio_de05.py
  python governance/build_expressive_teacher_audio_de05.py --verify-only
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
                         "differential_equations", "lesson_05")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "differential_equations",
                         "lesson_05.html")
MANIFEST_TITLE = "অধ্যায় ০৫ — তাপ সমীকরণ ও ফুরিয়ার রূপান্তর"

# Prosody keyed by cue type: (rate, pitch, volume)
PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
    "h3":            ("-3%", "+0Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),   # reflective quote
    "p":             ("+2%", "+0Hz", "+0%"),   # natural teacher pace
    "figure":        ("-4%", "+0Hz", "+0%"),   # slower, considerate visual explanation
    "callout":       ("+0%", "+0Hz", "+0%"),
    "callout-blue":  ("+0%", "+0Hz", "+0%"),   # exact DOM variants of callout
    "callout-gold":  ("+0%", "+0Hz", "+0%"),
    "callout-purple":("+0%", "+0Hz", "+0%"),
    "callout-green": ("+0%", "+0Hz", "+0%"),
    "callout-red":   ("+0%", "+0Hz", "+0%"),
    "formula-box":   ("-8%", "+0Hz", "+0%"),   # slow and deliberate
    "code-showcase": ("+0%", "+0Hz", "+0%"),
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")     # calm concluding prose

ALLOWED_CUE_TYPES = set(PROSODY_DEFAULT) | {"conclusion"}

# Exact DOM block-type sequence per narrated section (extracted from narration_engine).
EXPECTED_TYPES = {
    "sec-heat-pde-review":             ["h2", "chapter-quote", "p", "formula-box", "p", "p", "callout-gold", "figure"],
    "sec-boundary-separation":         ["h2", "p", "p", "formula-box", "p", "p", "formula-box", "callout-green"],
    "sec-sine-harmonics-decay":        ["h2", "p", "formula-box", "p", "figure", "p", "callout-purple"],
    "sec-fourier-orthogonality":       ["h2", "p", "p", "callout-red", "formula-box", "p", "formula-box", "formula-box", "p"],
    "sec-continuous-fourier-transform":["h2", "p", "p", "formula-box", "p", "formula-box", "figure", "formula-box", "callout-blue"],
}
EXPECTED_AUDIO_FILES = {
    "sec-heat-pde-review":              "sec_01_heat_pde_review.mp3",
    "sec-boundary-separation":          "sec_02_boundary_separation.mp3",
    "sec-sine-harmonics-decay":         "sec_03_sine_harmonics_decay.mp3",
    "sec-fourier-orthogonality":        "sec_04_fourier_orthogonality.mp3",
    "sec-continuous-fourier-transform": "sec_05_continuous_fourier_transform.mp3",
}
EXPECTED_ALIASES = {
    "sec-heat-pde-review":              "sec_01_heat_pde_review",
    "sec-boundary-separation":          "sec_02_boundary_separation",
    "sec-sine-harmonics-decay":         "sec_03_sine_harmonics_decay",
    "sec-fourier-orthogonality":        "sec_04_fourier_orthogonality",
    "sec-continuous-fourier-transform": "sec_05_continuous_fourier_transform",
}
EXPECTED_COUNT = {
    "sec-heat-pde-review": 8, "sec-boundary-separation": 8,
    "sec-sine-harmonics-decay": 7, "sec-fourier-orthogonality": 9,
    "sec-continuous-fourier-transform": 9,
}
EXPECTED_TOTAL = 41

OLD_VERSIONS = []  # recorded during bump_page_manifest_version()

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (41 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-heat-pde-review": {
        "title": "তাপ সমীকরণ ও সীমানা শর্তের ভৌত তাৎপর্য",
        "alias": "sec_01_heat_pde_review",
        "audio_file": "sec_01_heat_pde_review.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, তাপ সমীকরণ ও সীমানা শর্তের ভৌত তাৎপর্য।"},
            {"index": 1, "type": "chapter-quote",
             "tts": "জোসেফ ফুরিয়ার বলেছিলেন, প্রকৃতির গভীর পর্যবেক্ষণই গাণিতিক বিশ্লেষণের সবচেয়ে সমৃদ্ধ ভিত্তি।"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, আজ আমরা আংশিক অন্তরক সমীকরণ বা পি ডি ই এর জগতে ফিরে আসছি। গত অধ্যায়ে আমরা দেখেছিলাম একমাত্রিক ধাতব রডে অবস্থান এক্স আর সময় টি, এই দুই চলকের ওপর তাপমাত্রা ইউ অব এক্স কমা টি কীভাবে নির্ভর করে। স্থান ও কালের এই যুগল উপস্থিতিই পি ডি ই কে সাধারণ ও ডি ই থেকে আলাদা করে তোলে।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, একমাত্রিক তাপ সমীকরণ, ডেল ইউ বাই ডেল টি সমান আলফা গুণ ডেল স্কয়ার ইউ বাই ডেল এক্স স্কয়ার, যেখানে অবস্থান এক্স শূন্য থেকে এল এর মধ্যে আর সময় টি শূন্যের পরে। বামপাশে সময়ের প্রথম অন্তরজ আর ডানপাশে অবস্থানের দ্বিতীয় অন্তরজ, আর আলফা হলো তাপীয় ব্যাপন সহগ।"},
            {"index": 4, "type": "p",
             "tts": "এই দ্বিতীয় স্থানিক অন্তরজ আসলে বক্রতার পরিমাপ। কোনো বিন্দুর তাপমাত্রা যদি তার প্রতিবেশীদের গড়ের নিচে থাকে, অর্থাৎ হাসিমুখী অবতল বক্রতা হয়, তবে অন্তরজ ধনাত্মক হয় আর বিন্দুটি উত্তপ্ত হতে শুরু করে। বিপরীতে উত্তল পাহাড়ের চূড়ার মতো কোনো বিন্দু প্রতিবেশীদের চেয়ে উষ্ণ হলে তা শীতল হয়ে পড়ে।"},
            {"index": 5, "type": "p",
             "tts": "কিন্তু বাস্তবে কেবল এই সমীকরণটি দিয়ে কোনো নির্দিষ্ট সমাধান বের করা যায় না। কোনো গতিশীল ব্যবস্থাকে সুনির্দিষ্ট করতে হলে আমাদের জানতে হবে রডের দুই প্রান্তে অর্থাৎ এক্স সমান শূন্য ও এক্স সমান এল বিন্দুতে ঠিক কী ঘটছে। সেখানেই আসে সীমানা শর্তের প্রশ্ন।"},
            {"index": 6, "type": "callout-gold",
             "tts": "বিশেষ নোট, সীমানা শর্তের অপরিসীম গুরুত্ব। যদি দুই প্রান্তকে বরফের পানিতে ডুবিয়ে শূন্য ডিগ্রিতে স্থির রাখা হয়, তবে তা ডিরিক্লেট শর্ত। আর যদি প্রান্তদুটিকে নিখুঁত তাপ নিরোধক দিয়ে আবদ্ধ করা হয় যাতে কোনো তাপ বের হতে না পারে, তবে প্রান্তে তাপের নতি শূন্য হয়, আর এটি নয়ম্যান শর্ত। আংশিক সমীকরণের অসীম সমাধানের পরিবার থেকে মহাবিশ্বের একটিমাত্র বাস্তব সমাধানকে বেছে নেয় এই সীমানা শর্তই।"},
            {"index": 7, "type": "figure", "visual": True,
             "tts": "এই চিত্রে একটি ধাতব রডের দুই প্রান্তে ভিন্ন ভিন্ন সীমানা শর্তের ভৌত প্রভাব পাশাপাশি দেখানো হয়েছে। বাঁ প্রান্তে বরফের পানিতে ডুবিয়ে রাখা শূন্য তাপমাত্রার অবস্থায় ডিরিক্লেট শর্তে বক্ররেখা শূন্যে নামতে বাধ্য হয়, আর ডান প্রান্তের অন্তরক আবরণে নয়ম্যান শর্তে তাপ বের হতে না পারায় বক্ররেখা অনুভূমিক হয়ে দাঁড়ায় অর্থাৎ প্রান্তে নতি শূন্য। এই দুই ভিন্ন নিয়মই ঠিক করে দেয় রডের ভেতর কোন তরঙ্গ বেঁচে থাকবে আর কোনটি মিলিয়ে যাবে, তাই কেবল সমীকরণ নয় বাস্তব সীমানা শর্তও সমাধানের অবিচ্ছেদ্য অংশ।"},
        ],
    },

    "sec-boundary-separation": {
        "title": "চলক পৃথকীকরণ পদ্ধতি ও আইগেনমান সমস্যা",
        "alias": "sec_02_boundary_separation",
        "audio_file": "sec_02_boundary_separation.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, চলক পৃথকীকরণ পদ্ধতি ও আইগেনমান সমস্যা।"},
            {"index": 1, "type": "p",
             "tts": "জটিল আংশিক সমীকরণ সমাধানের জন্য জোসেফ ফুরিয়ার গণিত ইতিহাসের সবচেয়ে কার্যকর হাতিয়ারগুলোর একটি প্রবর্তন করেন, আর তা হলো চলক পৃথকীকরণ পদ্ধতি। কৌশলটি খুবই সুন্দর, একটি কঠিন পি ডি ই কে ভেঙে দুটি সহজ ও ডি ই তে রূপ দেওয়া।"},
            {"index": 2, "type": "p",
             "tts": "আমরা অনুমান করি যে অজ্ঞাত অপেক্ষক ইউ অব এক্স কমা টি আলাদা করা যায়, অর্থাৎ সেটি কেবল অবস্থানের ফাংশন ক্যাপিটাল এক্স অব এক্স আর কেবল সময়ের ফাংশন ক্যাপিটাল টি অব টি এর গুণফল। এই অনুমানটিকে তাপ সমীকরণে বসালে পাই, এক্স অব এক্স গুণ টি প্রাইম সমান আলফা গুণ এক্স ডাবল প্রাইম গুণ টি অব টি।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, চলক পৃথকীকরণের অনুপাত, টি প্রাইম ভাগ আলফা টি সমান এক্স ডাবল প্রাইম ভাগ এক্স সমান মাইনাস ল্যাম্বডা স্কয়ার। একদিকে কেবল সময়, অন্যদিকে কেবল অবস্থান, আর উভয় পক্ষই একই ঋণাত্মক ধ্রুবকের সমান।"},
            {"index": 4, "type": "p",
             "tts": "লক্ষ্য করুন বামপক্ষটি কেবলমাত্র সময় টির ফাংশন আর ডানপক্ষটি কেবলমাত্র অবস্থান এক্সের ফাংশন। দুটি স্বাধীন চলকের ফাংশন সর্বদা সমান হতে পারে কেবল তখনই যখন উভয়েই একটি সার্বজনীন ধ্রুবকের সমান হয়। এই ধ্রুবকটিকেই আমরা পৃথকীকরণ ধ্রুবক মাইনাস ল্যাম্বডা স্কয়ার নামে চিহ্নিত করি।"},
            {"index": 5, "type": "p",
             "tts": "এখান থেকে আমাদের একটিমাত্র আংশিক সমীকরণ ভেঙে দুটি পৃথক সাধারণ অন্তরক সমীকরণ বা ও ডি ই তৈরি হয়। একটি হলো স্থানিক সমীকরণ, এক্স ডাবল প্রাইম যোগ ল্যাম্বডা স্কয়ার এক্স সমান শূন্য, আর অন্যটি কালিক সমীকরণ, টি প্রাইম যোগ আলফা ল্যাম্বডা স্কয়ার টি সমান শূন্য। স্থানিকটির সমাধান সাইন আর কোসাইনের সমন্বয়।"},
            {"index": 6, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, কোয়ান্টায়িত কম্পাঙ্ক, ল্যাম্বডা সাব এন সমান এন পাই ভাগ এল, আর অনুমোদিত আইগেনফাংশন এক্স সাব এন অব এক্স সমান সাইন অব এন পাই এক্স ভাগ এল, যেখানে এন হলো এক, দুই, তিন ইত্যাদি ধনাত্মক পূর্ণসংখ্যা।"},
            {"index": 7, "type": "callout-green",
             "tts": "বিশেষ নোট, কোয়ান্টাম বলবিদ্যার পূর্বাভাস। একটি সীমাবদ্ধ রডে স্থানিক কম্পাঙ্ক ল্যাম্বডা যেকোনো মান নিতে পারে না, সীমানা শর্ত তাকে পূর্ণসংখ্যার গুণিতকে কোয়ান্টায়িত হতে বাধ্য করে। ঠিক এই একই গাণিতিক নীতি এক শতাব্দী পরে শ্রোডিঙ্গার সমীকরণে পরমাণুর শক্তিস্তরের কোয়ান্টাইজেশন ব্যাখ্যা করেছিল।"},
        ],
    },

    "sec-sine-harmonics-decay": {
        "title": "সাইন হারমোনিক্স ও উচ্চ কম্পাঙ্কের তীব্র ক্ষয়",
        "alias": "sec_03_sine_harmonics_decay",
        "audio_file": "sec_03_sine_harmonics_decay.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, সাইন হারমোনিক্স ও উচ্চ কম্পাঙ্কের তীব্র ক্ষয়।"},
            {"index": 1, "type": "p",
             "tts": "স্থানিক আইগেনফাংশন নির্ধারিত হওয়ার পর এবার সময়ের অংশের সমাধান দেখা যাক। কালিক সমীকরণটি হলো টি প্রাইম সমান মাইনাস আলফা ল্যাম্বডা স্কয়ার গুণ টি, যা প্রথম ক্রমের এক অতি পরিচিত সূচকীয় সমীকরণ। এর সমাধান হলো ই টু দ্য পাওয়ার মাইনাস আলফা গুণ এন পাই ভাগ এল হোল স্কয়ার গুণ টি।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এন তম মৌলিক তাপীয় মোড, ইউ সাব এন অব এক্স কমা টি সমান ই টু দ্য পাওয়ার মাইনাস আলফা গুণ এন পাই ভাগ এল হোল স্কয়ার গুণ টি, গুণ সাইন অব এন পাই এক্স ভাগ এল। প্রতিটি মোড একটি ক্ষয়িষ্ণু সাইন তরঙ্গ, যা আকার না বদলিয়ে কেবল নিজস্ব গতিতে মিলিয়ে যায়।"},
            {"index": 3, "type": "p",
             "tts": "এখানেই লুকিয়ে আছে তাপ সমীকরণের সবচেয়ে বৈপ্লবিক পদার্থবিজ্ঞান। সূচকের দিকে তাকান, ক্ষয়ের হার এন স্কয়ারের সমানুপাতিক। এন সমান এক মৌলিক মোড যে গতিতে ঠান্ডা হয়, এন সমান দুই মোড তার চেয়ে চার গুণ দ্রুত, এন সমান তিন মোড নয় গুণ দ্রুত, আর এন সমান দশ মোড একশত গুণ তীব্রতায় বিলীন হয়ে যায়।"},
            {"index": 4, "type": "figure", "visual": True,
             "tts": "এই গ্রাফে তিনটি হারমনিক্স মোডের সূচকীয় ক্ষয় একসাথে দেখানো হয়েছে। এন সমান এক মোড ধীরে ধীরে ক্ষয়প্রাপ্ত হয়, কিন্তু এন সমান দুই মোড চার গুণ দ্রুত আর এন সমান তিন মোড নয় গুণ দ্রুত গতিতে মিলিয়ে যায়। সব বক্ররেখাই একই ই টু দ্য পাওয়ার মাইনাস আলফা ল্যাম্বডা স্কয়ার গুণ টি নিয়ম মেনে চলে, শুধু ঘাতে এন স্কয়ার থাকার কারণে ঘন ঢেউগুলোর আয়ুষ্কাল সংকুচিত হয়, ফলে কিছুক্ষণের মধ্যে কেবল মসৃণতম প্রথম মোডটিই টিকে থাকে।"},
            {"index": 5, "type": "p",
             "tts": "বাস্তব জীবনে এর চাক্ষুষ অর্থ কী? তাপমাত্রার যেকোনো তীক্ষ্ণ খাঁজ বা দ্রুত পরিবর্তন উচ্চ কম্পাঙ্কের হারমোনিক্স দিয়ে গঠিত। যেহেতু উচ্চ কম্পাঙ্কগুলো চোখের পলকেই মিলিয়ে যায়, তাই তাপ প্রবাহ যেকোনো আকৃতিকে অবিশ্বাস্য দ্রুততায় মসৃণ করে ফেলে। কিছুক্ষণের মধ্যেই সমস্ত সূক্ষ্ম খাঁজ বিলুপ্ত হয়ে কেবল মসৃণতম প্রথম আর্চটি অবশিষ্ট থাকে।"},
            {"index": 6, "type": "callout-purple",
             "tts": "বিশেষ নোট, এন্ট্রপি ও সময়ের একমুখী তীর। উচ্চ কম্পাঙ্কের এই বিস্ফোরক ক্ষয় আসলে তথ্য হারানোর নামান্তর। সময়ের সাথে সাথে তাপ উচ্চ কম্পাঙ্কের সমস্ত অতীত স্মৃতি চিরতরে মুছে ফেলে, আর এ কারণেই অতীতের নিখুঁত অবস্থা পুনরুদ্ধার করা অসম্ভব। এটিই তাপগতিবিদ্যার দ্বিতীয় সূত্রের মূল ভিত্তি।"},
        ],
    },

    "sec-fourier-orthogonality": {
        "title": "ফুরিয়ার ধারা, উপরিপাত নীতি ও অর্থোগোন্যালিটি",
        "alias": "sec_04_fourier_orthogonality",
        "audio_file": "sec_04_fourier_orthogonality.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, ফুরিয়ার ধারা, উপরিপাত নীতি ও অর্থোগোন্যালিটি।"},
            {"index": 1, "type": "p",
             "tts": "ধরা যাক শুরুতে রডের তাপমাত্রা একটি মসৃণ সাইন তরঙ্গ নয়, বরং এক অর্ধেক ফুটন্ত পানিতে আর অপর অর্ধেক বরফে রাখা ছিল, ফলে কেন্দ্রে একটি খাড়া স্টেপ ফাংশন তৈরি হয়েছে। এই এবড়োথেবড়ো প্রাথমিক অবস্থা কীভাবে সমাধান করা যাবে?"},
            {"index": 2, "type": "p",
             "tts": "জোসেফ ফুরিয়ার ১৮০৭ সালে ঘোষণা করেছিলেন যে যেকোনো ফাংশন এফ অব এক্স কে অসীম সংখ্যক সাইন তরঙ্গের যোগফল হিসেবে লেখা সম্ভব। প্রতিটি তরঙ্গের নিজস্ব বিস্তার থাকবে, আর তাদের যোগফলই মূল জটিল আকৃতি গড়ে তুলবে। তৎকালীন গণিতের পণ্ডিতরা এই দাবি শুনে চমকে উঠেছিলেন।"},
            {"index": 3, "type": "callout-red",
             "tts": "বিশেষ নোট, ঐতিহাসিক বিতর্ক ও ফাংশন স্পেসে ভিত্তি ভেক্টর। মসৃণ সাইন ঢেউ যোগ করে কীভাবে ধারালো কোণা তৈরি সম্ভব, এই নিয়ে লাগ্রাঞ্জ ও লাপ্লাসের মতো দিগ্গজরা ফুরিয়ারের দাবির তীব্র বিরোধিতা করেছিলেন। কিন্তু তাঁর ভিত্তি ছিল অর্থোগোন্যালিটি, ঠিক যেমন ত্রিমাত্রিক জগতে আই হ্যাট, জে হ্যাট আর কে হ্যাট ভিত্তি ভেক্টর, তেমনি অসীম মাত্রিক ফাংশন স্পেসে সাইন তরঙ্গগুলোই হলো অর্থোগোন্যাল ভিত্তি।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, সাইন আইগেনফাংশনসমূহের অর্থোগোন্যালিটি। শূন্য থেকে এল পর্যন্ত এন পাই এক্স ভাগ এল আর এম পাই এক্স ভাগ এল এর দুটি সাইন তরঙ্গের গুণফলের সমাকলন শূন্য যখন এন ও এম আলাদা, আর যখন এন সমান এম তখন তার মান এল ভাগ দুই। রৈখিক বীজগণিতে যেমন দুটি লম্ব ভেক্টরের ডট প্রোডাক্ট শূন্য হয়, তেমনি এখানে লম্বতার এই ধর্ম কাজ করে।"},
            {"index": 5, "type": "p",
             "tts": "এই অর্থোগোন্যালিটিই আমাদের কাছে সহগ বের করার চাবিকাঠি। সমীকরণের উভয় পাশকে যেকোনো নির্দিষ্ট সাইন তরঙ্গ দিয়ে গুণ করে শূন্য থেকে এল পর্যন্ত সমাকলন করলে, অন্য সব পদ মিলিয়ে যায় আর কেবল ওই একটি পদই টিকে থাকে। ফলে প্রতিটি হারমোনিকের বিস্তার খুব পরিচ্ছন্নভাবে বেরিয়ে আসে।"},
            {"index": 6, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ফুরিয়ার সহগ নির্ণয়, বি সাব এন সমান দুই ভাগ এল গুণ শূন্য থেকে এল পর্যন্ত এফ অব এক্স গুণ সাইন অব এন পাই এক্স ভাগ এল ডি এক্স। অর্থাৎ প্রাথমিক তাপমাত্রা ফাংশনটিকে ওই হারমোনিকের ওপর প্রক্ষেপণ করলেই তার সঠিক অংশ পাওয়া যায়।"},
            {"index": 7, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, সীমাবদ্ধ দণ্ডে তাপ সমীকরণের পূর্ণ সমাধান, ইউ অব এক্স কমা টি সমান সামেশন এন সমান এক থেকে অসীম, বি সাব এন গুণ ই টু দ্য পাওয়ার মাইনাস আলফা গুণ এন পাই ভাগ এল হোল স্কয়ার গুণ টি, গুণ সাইন অব এন পাই এক্স ভাগ এল। প্রতিটি টুকরো আলাদাভাবে ক্ষয় হয় আর তাদের যোগফলই চূড়ান্ত উত্তর।"},
            {"index": 8, "type": "p",
             "tts": "তাপ সমীকরণ রৈখিক হওয়ায় এই উপরিপাত নীতি সম্ভব হয়েছে। যেকোনো জটিল তাপমাত্রা বণ্টন যেন এক সিম্ফনির সুর, প্রতিটি সুর তার নিজস্ব গতিতে ক্ষয়প্রাপ্ত হয়ে শান্তিতে রূপ নেয়। ত্রিকোণমিতি, সমাকলন ও অন্তরকের এই সমন্বয়ই আধুনিক পদার্থবিজ্ঞানের ভিত্তি।"},
        ],
    },

    "sec-continuous-fourier-transform": {
        "title": "অসীম দণ্ড, ফুরিয়ার ট্রান্সফর্ম ও গাউসিয়ান কার্নেল",
        "alias": "sec_05_continuous_fourier_transform",
        "audio_file": "sec_05_continuous_fourier_transform.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, অসীম দণ্ড, ফুরিয়ার ট্রান্সফর্ম ও গাউসিয়ান তাপীয় কার্নেল।"},
            {"index": 1, "type": "p",
             "tts": "এবার কল্পনা করুন আমাদের ধাতব দণ্ডটি সীমাবদ্ধ নয়, এটি মাইনাস অসীম থেকে প্লাস অসীম পর্যন্ত বিস্তৃত। অর্থাৎ অবস্থান এক্স যেকোনো বাস্তব মান নিতে পারে, কোনো প্রান্ত নেই, কোনো বাউন্ডারি শর্তও নেই।"},
            {"index": 2, "type": "p",
             "tts": "যখন দণ্ডের দৈর্ঘ্য এল অসীমের দিকে ধাবিত হয়, তখন পাশাপাশি দুটি অনুমোদিত কম্পাঙ্কের মধ্যবর্তী দূরত্ব শূন্যের কাছাকাছি পৌঁছে যায়। ফলে বিচ্ছিন্ন পূর্ণসংখ্যার যোগফল মসৃণভাবে একটি অবিচ্ছিন্ন সমাকলনে রূপ নেয়। এখান থেকেই জন্ম নেয় আধুনিক বিজ্ঞানের অন্যতম শ্রেষ্ঠ আবিষ্কার, ফুরিয়ার ট্রান্সফর্ম।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, অবিচ্ছিন্ন ফুরিয়ার ট্রান্সফর্ম, এফ হ্যাট অব কে সমান ইন্টিগ্রাল মাইনাস অসীম থেকে অসীম, এফ অব এক্স গুণ ই টু দ্য পাওয়ার মাইনাস আই কে এক্স ডি এক্স। আর বিপরীত রূপান্তরে এফ অব এক্স সমান এক ভাগ দুই পাই গুণ ইন্টিগ্রাল মাইনাস অসীম থেকে অসীম, এফ হ্যাট অব কে গুণ ই টু দ্য পাওয়ার প্লাস আই কে এক্স ডি কে।"},
            {"index": 4, "type": "p",
             "tts": "ফুরিয়ার ট্রান্সফর্মের সবচেয়ে জাদুকরী বৈশিষ্ট্য হলো এটি স্থানিক অন্তরজকে সাধারণ বীজগাণিতিক গুণনে রূপ দেয়। দ্বিতীয় অন্তরজের বদলে আসে কেবল মাইনাস কে স্কয়ার গুণ ইউ হ্যাট। ফলে আমাদের জটিল আংশিক সমীকরণটি সরল হয়ে একটি অতি সহজ ও ডি ই তে দাঁড়ায়, যার সমাধান সরাসরি লেখা যায়।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, কম্পাঙ্ক স্পেসে ও ডি ই, ডি ইউ হ্যাট বাই ডি টি সমান মাইনাস আলফা কে স্কয়ার গুণ ইউ হ্যাট। এর সমাধান হলো ইউ হ্যাট অব কে কমা টি সমান ইউ হ্যাট অব কে শূন্য গুণ ই টু দ্য পাওয়ার মাইনাস আলফা কে স্কয়ার গুণ টি, অর্থাৎ প্রতিটি কম্পাঙ্ক নিজস্ব হারে মিলিয়ে যায়।"},
            {"index": 6, "type": "figure", "visual": True,
             "tts": "এই চিত্রে একটি বিন্দুতে কেন্দ্রীভূত তাপ সময়ের সাথে সাথে কীভাবে প্রসারিত গাউসিয়ান বেল কার্ভে রূপ নেয় তা দেখানো হয়েছে। শুরুর সরু লাল শিখরটি কালের সাথে সাথে নীল ও সবুজ রেখায় নামিয়ে এসে চওড়া ও নিচু হয়, অর্থাৎ মোট তাপ অপরিবর্তিত থাকলেও এর স্থানিক বিস্তার বাড়তে থাকে। বেলটির প্রস্থ সময়ের বর্গমূলের সমানুপাতিকে বাড়ে, যা অণুদের এলোমেলো ব্রাউনিয়ান গতির সাথে সরাসরি মিলে যায়, আর এটিই অসীম ডোমেইনে তাপ সমীকরণের মৌলিক সমাধান।"},
            {"index": 7, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, গাউসিয়ান মৌলিক সমাধান বা হিট কার্নেল, ফাই অব এক্স কমা টি সমান এক ভাগ রুট ফোর পাই আলফা টি, গুণ ই টু দ্য পাওয়ার মাইনাস এক্স স্কয়ার ভাগ চার আলফা টি। বিন্দুতে থাকা প্রাথমিক তাপকে এই কার্নেলের সাথে কনভোলিউশন করলেই অসীম দণ্ডের পূর্ণ সমাধান পাওয়া যায়।"},
            {"index": 8, "type": "callout-blue", "role": "conclusion",
             "tts": "বিশেষ নোট, ব্রাউনিয়ান গতি ও সম্ভাবনা তত্ত্ব। গাউসিয়ান হিট কার্নেল অবিকল স্বাভাবিক সম্ভাবনা বণ্টনের মতো, আর এটি কোনো কাকতালীয় বিষয় নয়। অণুদের এলোমেলো ব্রাউনিয়ান গতির সামগ্রিক ম্যাক্রোস্কোপিক রূপই হলো এই তাপ সমীকরণ। একটি লোহার রডের তাপ পরিবাহিতা থেকে জন্ম নিয়ে ফুরিয়ার ধারা ও ট্রান্সফর্ম আজ কোয়ান্টাম বলবিদ্যা, সিগন্যাল প্রসেসিং আর আধুনিক তথ্যপ্রযুক্তির মেরুদণ্ডে পরিণত হয়েছে।"},
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
                raise ValueError(
                    f"{sec_id} cue {cue['index']}: forbidden chars {bad!r} in {cue['tts']!r}")
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: artificial figure label present")

    if list(SECTIONS_DATA) != list(EXPECTED_TYPES):
        raise ValueError("Section ids / order changed")
    total = 0
    for sec_id, sec in SECTIONS_DATA.items():
        types = [c["type"] for c in sec["cues"]]
        if types != EXPECTED_TYPES[sec_id]:
            raise ValueError(f"{sec_id}: cue type/order mismatch -> {types}")
        if sec["audio_file"] != EXPECTED_AUDIO_FILES[sec_id]:
            raise ValueError(f"{sec_id}: audio_file mismatch")
        if sec["alias"] != EXPECTED_ALIASES[sec_id]:
            raise ValueError(f"{sec_id}: alias mismatch")
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
                    raise ValueError(
                        f"{sec_id} cue {cue['index']}: visual explanation has "
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
            tag = "conclusion" if cue.get("role") == "conclusion" else cue["type"]
            print(f"  cue {idx:02d} [{tag:<13}] {rate:>4} {pitch:>5}  {cue['tts'][:30]}...")
            await synth_cue(cue["tts"], chunk, rate, pitch, volume)
        else:
            print(f"  cue {idx:02d} [{cue['type']:<13}] cached")
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
        "alias": sec["alias"],
        "title": sec["title"],
        "audio_file": sec["audio_file"],
        "total_duration_ms": round(cursor, 1),
        "cues": manifest_cues,
    }


def bump_page_manifest_version():
    """manifest.js?v=N -> ?v=N+1 so browsers reload the rebuilt manifest."""
    global OLD_VERSIONS
    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    pattern = re.compile(r"(manifest\.js\?v=)(\d+)")
    matches = pattern.findall(html)
    if not matches:
        raise RuntimeError("Page manifest cache-buster not found")
    OLD_VERSIONS = [int(m[1]) for m in matches]
    new_html, count = pattern.subn(
        lambda m: m.group(1) + str(int(m.group(2)) + 1), html)
    with open(PAGE_PATH, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_html)
    print(f"  bumped manifest cache-buster: {matches[0][1]} -> "
          f"{int(matches[0][1]) + 1} ({count} occurrence(s))")


async def build_all():
    visuals = assert_clean_scripts()
    print(f"Validated {sum(len(s['cues']) for s in SECTIONS_DATA.values())} clean cues "
          f"in {len(SECTIONS_DATA)} sections ({visuals} natural visual explanations, "
          f"0 artificial figure labels).")

    built = {}
    for sec_id, sec in SECTIONS_DATA.items():
        built[sec_id] = await build_section(sec_id, sec)

    # Manifest keys are exactly the 5 canonical DOM section ids (in DOM order).
    manifest_sections = {sec_id: built[sec_id] for sec_id in SECTIONS_DATA}

    manifest_data = {
        "course": "differential_equations",
        "lesson": "lesson_05",
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
        assert msec["alias"] == EXPECTED_ALIASES[sec_id]
        assert msec["audio_file"] == EXPECTED_AUDIO_FILES[sec_id]
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
    assert total_cues == EXPECTED_TOTAL

    print("\n" + "=" * 70)
    print("BUILD COMPLETE - expressive teacher audio, Differential Equations Lesson 05")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<36} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(SECTIONS_DATA)} sections, "
          f"{total_ms / 1000.0:.2f}s, {visuals} natural visual explanations.")
    print("  manifest.json is valid JSON; all 5 mp3 files exist and are non-empty.")
    print("=" * 70)


# --------------------------------------------------------------------------- #
# Headless Chrome verification (channel=chrome)
# --------------------------------------------------------------------------- #
VERIFY_JS = r"""() => {
  const ne = window.narrationEngine;
  const manifest = window.TEACHER_AUDIO_MANIFEST;
  const sectionEls = [...document.querySelectorAll('.article > section, article section')];

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
    # the hero/watch-panel mp4 and YouTube embeds are network-blocked/absent.
    benign = ("ERR_FILE_NOT_FOUND", "404 (File not found)",
              "Permissions policy violation", "Failed to load resource",
              "net::ERR", "ERR_BLOCKED", "Not allowed to load local resource")
    narration_console_errors = [e for e in console_errors
                                if not any(b in e for b in benign)]

    assert js_errors == [], f"JS page errors: {js_errors}"
    assert narration_console_errors == [], f"Unexpected console errors: {narration_console_errors}"
    assert data["manifestPresent"], "window.TEACHER_AUDIO_MANIFEST missing"
    assert data["hasStudioAudio"], "Studio teacher audio not bound"

    mkeys = data["manifestKeys"]
    dom_ids = [s["id"] for s in data["dom"]]
    canonical_ids = list(SECTIONS_DATA)
    assert dom_ids == canonical_ids, f"DOM ids changed: {dom_ids} vs {canonical_ids}"
    assert mkeys == canonical_ids, f"Manifest keys changed: {mkeys}"
    assert canonical_ids == [s["id"] for s in data["engine"]], "Engine ids changed"
    assert not ({"sec-quizzes", "sec-quiz", "sec-media", "sec-simulator",
                  "sec-figures", "sec-interactive-lab", "sec-video-note"} & set(dom_ids)), \
        "non-narrated section leaked into DOM sections"

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
        assert msec["alias"] == EXPECTED_ALIASES[sec_id], (sec_id, "alias")

        # TeX annotation must survive for every formula-box block.
        n_fb = expected_types.count("formula-box")
        assert len(dom_sec["tex"]) == n_fb, (sec_id, "formula-box tex count")
        for tex in dom_sec["tex"]:
            assert isinstance(tex, list) and any(t.strip() for t in tex), (sec_id, "missing TeX annotation")
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
        total_ms += msec["total_duration_ms"]

    assert total_cues == EXPECTED_TOTAL, total_cues
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

    # Page cache-buster bumped exactly +1 when this process built the audio.
    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    versions = [int(v) for _, v in re.findall(r"(manifest\.js\?v=)(\d+)", html)]
    if OLD_VERSIONS:
        assert versions == [v + 1 for v in OLD_VERSIONS], \
            f"manifest ?v not bumped +1: {OLD_VERSIONS} -> {versions}"
    else:
        assert versions and min(versions) >= 2, f"manifest ?v not bumped: {versions}"

    return {
        "channel": "chrome (headless=True)",
        "sections": len(SECTIONS_DATA),
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
    print("\n" + "=" * 70)
    print("VERIFICATION REPORT (headless Chrome channel=chrome)")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("=" * 70)
    if not report.get("ok"):
        raise SystemExit("VERIFICATION FAILED")
    print("VERIFIED: 41/41 cues, DOM<->manifest 1:1, 0 dups, 0 quiz/media-tab types, "
          "non-zero mp3s, valid JSON, 0 JS page errors, 0 'চিত্র প্রদর্শনী' labels.")
    print("=" * 70)


if __name__ == "__main__":
    main()
