# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Probability Lesson 01
("What Even is Probability? — The Geometry of Uncertainty", Bengali) to the
Lesson-01 gold standard.

Deterministic, re-runnable, self-contained:
  * 35 cues in 6 narrated sections with EXACTLY the same section IDs, alias keys,
    audio_file names, cue types and cue order as the live narration-engine DOM.
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time, so the build is fully reproducible).
  * Visual cues are genuine 2-4 sentence natural explanations — never the
    artificial label "চিত্র প্রদর্শনী".
  * Every script is clean spoken Bengali with phonetic safeguards:
    P(A|B) -> পি এ গিভন বি, Monty Hall -> মন্টি হল, Bayes -> বেজ,
    P(A n B) -> পি এ ইন্টারসেকশন বি, P(A u B) -> পি এ ইউনিয়ন বি,
    P(Omega) -> পি ওমেগা, 1/3 -> এক তৃতীয়াংশ, 2/3 -> দুই তৃতীয়াংশ.
    No TeX, LaTeX, backslashes, $, braces, brackets, em-dashes, raw hyphens or
    Latin letters.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, chapter-quote -3%, p +2%, figure -4%, callout +0%,
      formula-box -8%, conclusion -3%.
  * A real 350 ms silence chunk is inserted between cues, so the millisecond
    timings written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with the
    exact-ms timings and both canonical + alias section keys of the old manifest.
  * Validates non-zero durations, zero overlap, valid JSON and non-empty mp3s.

Usage:  python governance/build_expressive_teacher_audio_prob01.py
"""

import os
import re
import json
import copy
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
                         "probability", "lesson_01")
MANIFEST_TITLE = "অধ্যায় ০১ — সম্ভাব্যতা আসলে কী? — অনিশ্চয়তার জ্যামিতি ও প্যারাডক্স"

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
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")     # calm concluding prose

# Parity guards: exact cue-type sequence expected for each narrated section,
# extracted from the live DOM with narration_engine.js's selector.
EXPECTED_TYPES = {
    "sec-intro":           ["h2", "chapter-quote", "p", "p", "callout"],
    "sec-area-concept":    ["h2", "p", "formula-box", "p", "formula-box",
                            "p", "p", "callout"],
    "sec-sample-space":    ["h2", "p", "p", "p", "formula-box", "callout"],
    "sec-monty-hall":      ["h2", "p", "p", "p", "callout", "p"],
    "sec-conditional":     ["h2", "p", "formula-box", "callout", "p"],
    "sec-bayes-intuition": ["h2", "p", "formula-box", "callout", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-intro":           "sec_01_intro.mp3",
    "sec-area-concept":    "sec_02_area_concept.mp3",
    "sec-sample-space":    "sec_03_sample_space.mp3",
    "sec-monty-hall":      "sec_04_monty_hall.mp3",
    "sec-conditional":     "sec_05_conditional.mp3",
    "sec-bayes-intuition": "sec_06_bayes_intuition.mp3",
}
# Canonical DOM section id -> legacy alias key kept in the manifest.
ALIASES = {
    "sec-intro":           "sec_01_intro",
    "sec-area-concept":    "sec_02_area_concept",
    "sec-sample-space":    "sec_03_sample_space",
    "sec-monty-hall":      "sec_04_monty_hall",
    "sec-conditional":     "sec_05_conditional",
    "sec-bayes-intuition": "sec_06_bayes_intuition",
}

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (35 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-intro": {
        "title": "অনিশ্চয়তাকে কীভাবে পরিমাপ করা যায়?",
        "audio_file": "sec_01_intro.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, অনিশ্চয়তাকে কীভাবে পরিমাপ করা যায়?"},
            {"index": 1, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, সম্ভাব্যতা তত্ত্ব মূলত সাধারণ কাণ্ডজ্ঞানকে গণিতের ভাষায় রূপান্তরিত করার শিল্প ছাড়া আর কিছুই নয়। বলেছেন পিয়েরে সিমন লাপ্লাস।"},
            {"index": 2, "type": "p",
             "tts": "শিক্ষার্থী বন্ধুরা, সম্ভাব্যতার প্রথম অধ্যায়ে তোমাদের স্বাগত। আমরা যখন বলি কাল বৃষ্টি হওয়ার সম্ভাবনা সত্তর শতাংশ, অথবা একটি নিরপেক্ষ ছক্কা ফেললে তিন আসার সম্ভাবনা ছয় ভাগের এক ভাগ, তখন এই সংখ্যাগুলোর পেছনে কী জ্যামিতি লুকানো আছে? অনেকেই সম্ভাব্যতাকে শুধু সূত্র আর ভগ্নাংশের কাটাকাটি হিসেবে শিখে থাকেন। কিন্তু ৩ব্লু১ব্রাউনের দর্শন হলো, সম্ভাব্যতা কোনো বিমূর্ত সংখ্যা নয়, এটি মূলত স্থান ও ক্ষেত্রফলের ভগ্নাংশ।"},
            {"index": 3, "type": "p",
             "tts": "যেকোনো অনিশ্চিত ঘটনাকে জ্যামিতিকভাবে উপস্থাপন করলে জটিল সব উপপাদ্য চোখের সামনে স্বতঃসিদ্ধ ছবির মতো স্পষ্ট হয়ে ওঠে। যেমন শর্তাধীন সম্ভাব্যতা পি এ গিভন বি, ইন্ডিপেন্ডেন্স বা স্বাধীনতা, আর বেজের সূত্র। আজ আমরা এই ছবিগুলোই ধীরে ধীরে আঁকব।"},
            {"index": 4, "type": "callout", "visual": True, "role": "conclusion",
             "tts": "মূল ভাবনার ভিত্তি হলো, আমরা সমস্ত সম্ভাবনার জগতকে একটি এক গুণ এক বর্গক্ষেত্র হিসেবে কল্পনা করব, যার মোট ক্ষেত্রফল এক দশমিক শূন্য বা একশো শতাংশ। এই বর্গক্ষেত্রের ভেতরে যেকোনো নির্দিষ্ট অঞ্চলই একটা ঘটনার প্রতীক। পুরো নমুনা ক্ষেত্রের সম্ভাবনা পি ওমেগা সবসময় একক, কারণ সম্ভাব্যতা আসলে স্থান ও ক্ষেত্রফলের অনুপাত।"},
        ],
    },

    "sec-area-concept": {
        "title": "সম্ভাব্যতা হলো ক্ষেত্রফল (Probability as Area)",
        "audio_file": "sec_02_area_concept.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, সম্ভাব্যতা হলো ক্ষেত্রফল।"},
            {"index": 1, "type": "p",
             "tts": "ধরা যাক, আমরা একটি লক্ষ্যবস্তুতে অন্ধভাবে একটি বিন্দু নিক্ষেপ করলাম। বিন্দুটি যেকোনো জায়গায় সমান সম্ভাবনায় পড়তে পারে।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, পি ওমেগা সমান ওমেগার ক্ষেত্রফল, সমান এক দশমিক শূন্য, সমান একশো শতাংশ।"},
            {"index": 3, "type": "p",
             "tts": "ঘটনা এ ঘটলে সেটি সমগ্র অঞ্চলের কিছু অংশ দখল করে, যেমন বৃষ্টি হওয়া বা মুদ্রায় হেড আসা। আর সেই দখল করা অংশের ক্ষেত্রফলই হলো ঘটনা এ এর সম্ভাব্যতা পি এ।"},
            {"index": 4, "type": "formula-box",
             "tts": "সূত্র, পি এ সমান অঞ্চল এ এর ক্ষেত্রফল ভাগ ওমেগার ক্ষেত্রফল, আর ওমেগার ক্ষেত্রফল এক হওয়ায় এটি কেবল অঞ্চল এ এর ক্ষেত্রফল।"},
            {"index": 5, "type": "p",
             "tts": "যদি দুটি ঘটনা এ এবং বি পরস্পর বর্জনীয় হয়, অর্থাৎ একসাথে ঘটা অসম্ভব, তবে তাদের অঞ্চল দুটি একে অপরকে স্পর্শও করবে না। তখন পি এ ইউনিয়ন বি সমান পি এ যোগ পি বি, কারণ কোনো দ্বিতীয়বার গণনার প্রশ্নই ওঠে না।"},
            {"index": 6, "type": "p",
             "tts": "কিন্তু যদি তারা পরস্পর বর্জনীয় না হয়? তখন তাদের মাঝে একটি সাধারণ ক্ষেত্রফল তৈরি হয়, যাকে আমরা বলি ছেদ বা এ ইন্টারসেকশন বি। এই কারণে সাধারণ ক্ষেত্রে দুটি ক্ষেত্রফল এককভাবে যোগ করা যায় না।"},
            {"index": 7, "type": "callout", "visual": True, "role": "conclusion",
             "tts": "জ্যামিতিক উপলব্ধি, কেন পি এ ইন্টারসেকশন বি বিয়োগ হয়? যখন আপনি এ এর ক্ষেত্রফল আর বি এর ক্ষেত্রফল আলাদাভাবে যোগ করেন, তখন মাঝখানের ওভারল্যাপ অঞ্চলটি দুবার গুনে ফেলা হয়। তাই সঠিক মোট ক্ষেত্রফল পেতে সেই যৌথ ক্ষেত্রফল একবার বিয়োগ দিতে হয়। এটিই ইনক্লুশন এক্সক্লুশন নীতির সবচেয়ে সহজ ভিজ্যুয়াল প্রমাণ, ঠিক যেমন টেবিলের ওপর দুটি কাগজ ওভারল্যাপ করলে মাঝের অংশটি দুবার পড়া যায়।"},
        ],
    },

    "sec-sample-space": {
        "title": "নমুনা ক্ষেত্র এবং ঘটনার পার্টিশন (Partitions & Total Probability)",
        "audio_file": "sec_03_sample_space.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, নমুনা ক্ষেত্র এবং ঘটনার পার্টিশন।"},
            {"index": 1, "type": "p",
             "tts": "বাস্তব জগতের যেকোনো সমস্যাকে সহজে বোঝার জন্য গ্রান্ট স্যান্ডারসন প্রায়ই গ্রিড পার্টিশন ব্যবহার করেন। নমুনা ক্ষেত্রকে আয়তাকার খণ্ডে ভাগ করলে জটিল হিসাবও নিখুঁতভাবে বিশ্লেষণ করা যায়।"},
            {"index": 2, "type": "p",
             "tts": "ধরা যাক, একটি কোম্পানিতে দুটি সার্ভার আছে, সার্ভার এক্স ও সার্ভার ওয়াই। সার্ভার এক্স মোট ট্রাফিকের সত্তর শতাংশ পরিচালনা করে, আর সার্ভার ওয়াই বাকি ত্রিশ শতাংশ।"},
            {"index": 3, "type": "p",
             "tts": "এখন পুরো বর্গক্ষেত্রকে অনুভূমিকভাবে দুই ভাগে ভাগ করি, একটি সত্তর শতাংশ চওড়া স্ট্রিপ এক্স, আরেকটি ত্রিশ শতাংশ স্ট্রিপ ওয়াই। ধরা যাক সার্ভার এক্সে এরর হওয়ার সম্ভাবনা দুই শতাংশ, কিন্তু সার্ভার ওয়াইতে তা দশ শতাংশ। উলম্বভাবে প্রতিটি স্ট্রিপকে এরর ই এবং নো এরর হিসেবে কাটলে মোট এররের সম্ভাবনা হবে দুটি আয়তক্ষেত্রের ক্ষেত্রফলের যোগফল।"},
            {"index": 4, "type": "formula-box",
             "tts": "সমগ্র সম্ভাব্যতা সূত্র, পি ই সমান পি এক্স গুণ পি ই গিভন এক্স, যোগ পি ওয়াই গুণ পি ই গিভন ওয়াই। হিসাব, শূন্য দশমিক সত্তর গুণ শূন্য দশমিক দুই, যোগ শূন্য দশমিক তিন গুণ শূন্য দশমিক এক, সমান শূন্য দশমিক শূন্য চার চার, অর্থাৎ চার দশমিক চার শতাংশ।"},
            {"index": 5, "type": "callout", "visual": True, "role": "conclusion",
             "tts": "জ্যামিতিক আয়তক্ষেত্র নীতি, কোনো জটিল বীজগণিত ছাড়াই শুধু প্রস্থ গুণ উচ্চতা সমান ক্ষেত্রফল সূত্র দিয়েই সমগ্র সম্ভাব্যতা উপপাদ্য চোখের সামনে ভেসে ওঠে। প্রতিটি আয়তক্ষেত্রের ক্ষেত্রফল হলো তার পূর্ব সম্ভাবনা ও শর্তাধীন সম্ভাবনার গুণফল। আর মোট সম্ভাবনা হলো ওই সব ক্ষেত্রফলের সমষ্টি।"},
        ],
    },

    "sec-monty-hall": {
        "title": "মন্টি হল প্যারাডক্স — দরজার পেছনের রহস্য (The Monty Hall Dilemma)",
        "audio_file": "sec_04_monty_hall.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, মন্টি হল প্যারাডক্স, স্বজ্ঞার মহাবিপত্তি।"},
            {"index": 1, "type": "p",
             "tts": "গণিতের ইতিহাসে মন্টি হল সমস্যার মতো তীব্র বিতর্ক আর কোনো সমস্যা তৈরি করতে পারেনি। ১৯৭০ এর দশকে একটি বিখ্যাত আমেরিকান টিভি গেম শো লেটস মেক এ ডিল থেকে এর উৎপত্তি, যার উপস্থাপক ছিলেন মন্টি হল। খেলার নিয়মটি চমৎকার, আপনার সামনে তিনটি বন্ধ দরজা, এক, দুই আর তিন। একটির পেছনে আছে দামি চকচকে গাড়ি, বাকি দুটির পেছনে সাধারণ ছাগল।"},
            {"index": 2, "type": "p",
             "tts": "ধরা যাক, আপনি এক নম্বর দরজা বেছে নিলেন। উপস্থাপক মন্টি হল, যিনি ভালো করেই জানেন কোন দরজার পেছনে কী আছে, বাকি দুটির একটি খুলে দিলেন, ধরা যাক তিন নম্বর দরজা, আর সেখানে একটা ছাগল দাঁড়িয়ে আছে। এবার মন্টি প্রশ্ন করলেন, আপনি কি সিদ্ধান্ত বদলে দুই নম্বর দরজায় যাবেন, নাকি এক নম্বরেই থাকবেন?"},
            {"index": 3, "type": "p",
             "tts": "আমাদের সাধারণ কাণ্ডজ্ঞান বলে, দুটি দরজা বাকি আছে, তাই গাড়ি থাকার সম্ভাবনা পঞ্চাশ পঞ্চাশ, বদলানোর কোনো লাভ নেই। এমনকি ১৯৯০ সালে মেরিলিন ভস সাভান্ত যখন সঠিক সমাধান দেন, তখন প্রায় এক হাজার পিএইচডি গণিতবিদ চিঠি লিখে দাবি করেছিলেন বদলালে কোনো বাড়তি লাভ হবে না।"},
            {"index": 4, "type": "callout", "visual": True,
             "tts": "কিন্তু গণিত ও ক্ষেত্রফল মডেল প্রমাণ করে, দরজা বদলালে গাড়ি জেতার সম্ভাবনা এক তৃতীয়াংশ থেকে লাফিয়ে দুই তৃতীয়াংশে পৌঁছে যায়, অর্থাৎ জয়ের সুযোগ দ্বিগুণ হয়। শুরুতে এক নম্বর দরজায় গাড়ি থাকার সম্ভাবনা ছিল এক তৃতীয়াংশ, আর বাকি দুই দরজার মিলিত সম্ভাবনা ছিল দুই তৃতীয়াংশ। মন্টি কখনো গাড়ির দরজা খুলতে পারেন না, আপনার বাছাইয়ের দরজাও খুলতে পারেন না, তাই তিনি ছাগল দেখিয়ে সেই দুই তৃতীয়াংশ সম্ভাবনাটিই অন্য দরজায় ঘনীভূত করে দেন। একশত দরজা কল্পনা করলেই বিষয়টি পরিষ্কার, আপনি একটা বাছলেন, মন্টি আটানব্বইটা ছাগল খুলে দিলেন, বাকিটাতে নিরানব্বই শতাংশ সম্ভাবনা।"},
            {"index": 5, "type": "p", "role": "conclusion",
             "tts": "কেন এমন হয়? কারণ তিন ভাগের দুই ভাগ ক্ষেত্রে আপনার প্রাথমিক বাছাই ছিল ছাগল। আর যখনই আপনি ছাগল বেছে নেন, মন্টি বাধ্য হয়ে অন্য ছাগলের দরজা খুলে দেন, ফলে বাকি বন্ধ দরজায় নিশ্চিতভাবে গাড়ি থাকে। মন্টি আসলে তথ্য দিচ্ছেন, আর সেই নিয়ন্ত্রিত তথ্যটিই দুই তৃতীয়াংশ সম্ভাবনাকে এক দরজায় কেন্দ্রীভূত করে।"},
        ],
    },

    "sec-conditional": {
        "title": "শর্তাধীন সম্ভাব্যতা: নতুন মহাবিশ্বে সংকোচন (Conditioning is Cropping)",
        "audio_file": "sec_05_conditional.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, শর্তাধীন সম্ভাব্যতা, নতুন মহাবিশ্বে সংকোচন।"},
            {"index": 1, "type": "p",
             "tts": "সম্ভাব্যতা তত্ত্বে সবচেয়ে বিভ্রান্তিকর অথচ সবচেয়ে ক্ষমতাবান ধারণা হলো শর্তাধীন সম্ভাব্যতা পি এ গিভন বি। এর গাণিতিক সংজ্ঞা হলো পি এ গিভন বি সমান পি এ ইন্টারসেকশন বি ভাগ পি বি, অর্থাৎ যৌথ ক্ষেত্রফলকে বি এর ক্ষেত্রফল দিয়ে ভাগ করা।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, পি এ গিভন বি সমান পি এ ইন্টারসেকশন বি ভাগ পি বি, আবার এটি সমান এ ইন্টারসেকশন বি এর ক্ষেত্রফল ভাগ বি এর ক্ষেত্রফল।"},
            {"index": 3, "type": "callout", "visual": True,
             "tts": "মহাবিশ্ব ক্রপিংয়ের মেটাফর, দেওয়া আছে ঘটনা বি ঘটেছে, এর অর্থ আপনার আগের পুরো মহাবিশ্ব ওমেগা বাতিল হয়ে গেল। এখন নতুন মহাবিশ্ব হলো শুধু অঞ্চল বি, যেন ছবি থেকে বাকি সব কেটে শুধু ওই অংশটাই রেখে দেওয়া হয়েছে। এই সংকুচিত মহাবিশ্বে বি এর ক্ষেত্রফল একশো শতাংশ, তাই এ কতটা জায়গা দখল করবে তা নির্ভর করছে বি এর ভেতরে এ এর অংশের ওপর। পি বি দিয়ে ভাগের অর্থই হলো নতুন মহাবিশ্বকে আবার এক দশমিক শূন্যে নরমালাইজ করা।"},
            {"index": 4, "type": "p", "role": "conclusion",
             "tts": "সুতরাং শর্তাধীন সম্ভাব্যতা কোনো ভিনগ্রহের সূত্র নয়, এটি নতুন সংকুচিত মহাবিশ্বের সাপেক্ষে ক্ষেত্রফলের স্বাভাবিক পুনরস্কেলিং। এই ছবিটি একবার মনে রাখলে বেজের সূত্রসহ অনেক ক্লাসিক্যাল প্যারাডক্স সরাসরি বোঝা যায়।"},
        ],
    },

    "sec-bayes-intuition": {
        "title": "বেজের সূত্রের দৃশ্যমান অন্তর্দৃষ্টি (Visual Bayes' Rule)",
        "audio_file": "sec_06_bayes_intuition.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "ষষ্ঠ পরিচ্ছেদ, বেজের সূত্রের দৃশ্যমান অন্তর্দৃষ্টি।"},
            {"index": 1, "type": "p",
             "tts": "বেজের সূত্র আসলে শর্তাধীন সম্ভাব্যতার দ্বিমুখী প্রতিসাম্য থেকেই জন্ম নেয়। পি এ ইন্টারসেকশন বি কে আমরা দুইভাবে লিখতে পারি, পি বি গুণ পি এ গিভন বি, আবার পি এ গুণ পি বি গিভন এ। যেহেতু দুটি প্রকাশই মাঝখানের একই ওভারল্যাপ ক্ষেত্রফলকে নির্দেশ করে, তাই একটিকে আরেকটির সমান লেখা যায়।"},
            {"index": 2, "type": "formula-box",
             "tts": "বেজের উপপাদ্য, পি এ গিভন বি সমান পি এ গুণ পি বি গিভন এ, সম্পূর্ণ ভাগ পি বি।"},
            {"index": 3, "type": "callout", "visual": True,
             "tts": "মেডিকেল টেস্ট প্যারাডক্সের বীজ, ধরা যাক বিরল একটি রোগ জনসংখ্যার এক শতাংশ মানুষের হয়, আর টেস্টটি নিরানব্বই শতাংশ সঠিক। আপনার টেস্ট পজিটিভ এলো, তাহলে কি রোগ থাকার সম্ভাবনা নিরানব্বই শতাংশ? না, কারণ বাকি নিরানব্বই শতাংশ সুস্থ মানুষেরও এক শতাংশের ফলস পজিটিভ ক্ষেত্রফল রোগীদের ট্রু পজিটিভ ক্ষেত্রফলের প্রায় সমান। ফলে পজিটিভ নতুন মহাবিশ্বে আপনার রোগ থাকার সম্ভাবনা আসলে মাত্র পঞ্চাশ শতাংশ, ক্ষেত্রফল আঁকলেই এটি তাৎক্ষণিক পরিষ্কার হয়ে যায়।"},
            {"index": 4, "type": "p", "role": "conclusion",
             "tts": "এটিই হলো বেজের সূত্রের বিশুদ্ধ জ্যামিতিক প্রমাণ, কোনো কৃত্রিম নিয়ম ছাড়া শুধু একই যৌথ ক্ষেত্রফলকে দুই দিক থেকে মাপার মাধ্যমে সমীকরণটি গঠিত হয়। পরবর্তী অধ্যায়ে আমরা দেখব কীভাবে একটি নিরানব্বই শতাংশ নিখুঁত মেডিকেল টেস্ট বিরল রোগের ক্ষেত্রে অধিকাংশ সময়েই ফলস পজিটিভ ফল দেয়।"},
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
        total += len(indices)
    if total != 35:
        raise ValueError(f"Expected 35 cues, found {total}")

    # Figure / visual cues must be genuine 2-4 sentence explanations.
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            if cue["type"] == "figure" or cue.get("visual"):
                sentences = [s for s in cue["tts"].split("।") if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(f"{sec_id} cue {cue['index']}: visual explanation has "
                                     f"{len(sentences)} sentences")


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

    manifest_sections = {}
    for sec_id, sec in SECTIONS_DATA.items():
        built = await build_section(sec_id, sec)
        manifest_sections[sec_id] = built
        # Legacy alias key mirrors the canonical section exactly (same fields).
        manifest_sections[ALIASES[sec_id]] = copy.deepcopy(built)

    manifest_data = {
        "course": "probability",
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
    expected_keys = set(SECTIONS_DATA) | set(ALIASES.values())
    assert set(loaded["sections"]) == expected_keys
    total_cues = 0
    total_ms = 0.0
    visuals = 0
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == len(EXPECTED_TYPES[sec_id])
        assert loaded["sections"][ALIASES[sec_id]] == msec
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        visuals += sum(1 for c in SECTIONS_DATA[sec_id]["cues"] if c.get("visual"))
    assert total_cues == 35

    print("\n" + "=" * 66)
    print("BUILD COMPLETE - expressive teacher audio, Probability Lesson 01")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<22} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  "
              f"{msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 6 sections, "
          f"{total_ms / 1000.0:.2f}s, {visuals} natural visual explanations.")
    print("  manifest.json is valid JSON; all 6 mp3 files exist and are non-empty.")
    print("=" * 66)


if __name__ == "__main__":
    asyncio.run(build_all())
