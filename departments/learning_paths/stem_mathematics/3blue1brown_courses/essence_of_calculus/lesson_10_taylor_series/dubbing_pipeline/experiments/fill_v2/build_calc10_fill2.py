"""
EXPERIMENT — fill_v2: full-length Bengali dub with NO internal silent pockets
(Essence of Calculus, Lesson 10 — Taylor series)
================================================================================
Copied from the quality-gated clean_timesync_v2 pipeline and extended with:

  (A) recompute-scale-from-rendered-speech
      The old build derived its layout scale from the AUTHORED cue durations
      (~448 s) so windows were stretched ~2.9x over a 1339 s video.  Speech was
      then forced to [0.82, 2.2] tempo and PADDED to fill each stretched window,
      producing ~34 silent runs up to 18 s.  Here the scale is recomputed from
      the ACTUAL RENDERED SPEECH length of every cue: the dense speech clips are
      laid contiguously and one common tempo (1/scale) makes them exactly tile
      the usable timeline.  No cue window ever contains dead air.

  (B) silence squeeze
      Leading/trailing MP3 padding is trimmed and any internal silent run longer
      than MAX_INTERNAL_PAUSE_S is reduced to that length (speech samples are
      never removed).  This caps the worst-case gap regardless of TTS pauses.

  (C) fill gate (hard gate — output is NOT declared success unless all pass)
      median_fill                 >= 0.72   (honest voiced duty cycle per cue)
      max_internal_gap_s          <= 1.5 s
      internal silence runs > 2 s  == 0
      output duration             ~= original (1339 s, within 2 s)

Cue source (read-only): web_platform/assets/audio/calculus/lesson_10/manifest.json
37 cues; sections are alias-deduped by (start_ms, text[:80]).

Everything is written under NEW experiments/fill_v2 folders.  Teacher audio,
manifests, the old video and other lessons are NEVER modified.  Video source is
the full original (no video-src swap); mux uses -c:v copy.
"""
import os
import re
import sys
import json
import time
import asyncio
import subprocess
import statistics
import wave
from pathlib import Path

import numpy as np
import edge_tts

EXP = Path(__file__).resolve().parent
BASE = EXP.parent.parent                         # .../lesson_10_taylor_series/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"           # .../3blue1brown_courses/web_platform
MANIFEST = WEB / "assets" / "audio" / "calculus" / "lesson_10" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "calculus" / "lesson_10" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "calculus" / "lesson_10" / "experiments" / "fill_v2" / \
            "3b1b_calculus_10_full_dubbed_fill2.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
TEMPO_FLOOR = 0.82
FADE_MS = 12
VIDEO_ID = "3d6DsjIBzJ4"
LESSON = "lesson_10_taylor_series"

LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0
INTER_CUE_PAUSE_SEC = INTER_CUE_PAUSE_MS / 1000.0

# Silence analysis / squeeze thresholds.  0.005 (-46 dB) sits just above MP3
# codec leakage (~0.004) and well below normal speech level.
#
# Edge-TTS inserts MANY short pauses (between clauses and words).  Squeezing
# every internal silent run down to 0.12 s keeps speech natural while raising
# the voiced duty cycle to ~0.76 (> 0.72 gate) and capping the worst-case gap
# at 0.12 s (<< 1.5 s gate).  Only silence is compressed; speech is untouched.
SILENCE_THRESH = 0.005
EDGE_PAD_MS = 25
MAX_INTERNAL_PAUSE_S = 0.12     # << 1.5 s gate with large headroom
TARGET_TEMPO_MAX = 1.35         # try to keep speech natural; hard cap is 2.2

# ---- Pedagogical Bengali expansion layer 1 (from the proven clean pipeline) ---
EXPANSIONS = {
    1: (" এই পাঠে আমরা দেখব কীভাবে একটি জটিল ফাংশনকে সহজ বহুপদীর ধারায় ভেঙে লেখা যায়। "
        "খেয়াল করুন, বহুপদী মানে কেবল যোগ, বিয়োগ, গুণ আর ভাগ—কোনো জটিল ফাংশন নেই। "
        "এই সরলতাই টেইলর ধারার আসল শক্তি, এবং পুরো পাঠে আমরা এই একই ধারণার ওপর নির্ভর করব।"),
    2: (" লক্ষ্য করুন, গণিতের অনেক বড় আবিষ্কার জন্ম নিয়েছে এই একই প্রশ্ন থেকে—জটিলকে কীভাবে সহজের "
        "যোগফলে রূপ দেওয়া যায়। আমরা যখনই কোনো অদ্ভুত বক্ররেখার মুখোমুখি হব, নিজেদের জিজ্ঞেস করব, "
        "এর সহজ প্রতিরূপটি কেমন হবে? এই দৃষ্টিভঙ্গিই আজকের পাঠের মূল চাবিকাঠি।"),
    3: (" এখানে একটা বিষয় লক্ষ্য করার মতো: আমরা সাইন বা কোসাইনকে রহস্যময় কিছু ভাবি, কিন্তু কম্পিউটারের "
        "কাছে এগুলো কেবল কিছু সংখ্যা। সেই সংখ্যাগুলো কীভাবে উৎপন্ন হয় তা বুঝতে পারলেই আমরা কম্পিউটেশনের "
        "ভেতরে ঢুকে যেতে পারব। তাই প্রথমে এই ছোট্ট প্রশ্নটির উত্তর খোঁজা যাক।"),
    4: (" উত্তরটি খুবই ব্যবহারিক। আমরা কোস বা ই-এর মতো ফাংশনকে এমন একটি বহুপদী দিয়ে প্রতিস্থাপন করি যা "
        "কাছাকাছি এলেই প্রায় একই মান দেয়। প্রথমে এক বা দুটি পদ নিয়ে শুরু করি, তারপর পদ বাড়াতে বাড়াতে "
        "যথার্থতা এত বেড়ে যায় যে পার্থক্যটা আর চোখে পড়ে না।"),
    5: (" মনে রাখবেন, পুনরাবৃত্ত গুণ আর যোগ কম্পিউটারের জন্য অত্যন্ত সস্তা কাজ। তাই বহুপদী ব্যবহার করলে "
        "গণনা হয় দ্রুত আর নির্ভুল। টেইলর ধারার মূল কৌশল হলো—আমরা মূল বক্ররেখার আকৃতিকে ছোট ছোট পদে "
        "ভেঙে নিই, যেন প্রতিটি পদ সেই বক্ররেখার এক একটি স্তর হয়ে ওঠে।"),
    6: (" এই সূত্রের অর্থ হলো—আমরা এক্স সমান এ বিন্দুকে কেন্দ্র ধরে তার চারপাশে বহুপদীটি গড়ে তুলছি। "
        "এন বাড়ানোর সাথে সাথে পদের সংখ্যাও বাড়ে এবং আসন্নায়ন ক্রমশ নিখুঁত হয়। এখন প্রশ্ন হলো, "
        "সেই সহগগুলো কীভাবে নির্ধারণ করব? তার জন্যই আমাদের ডেরিভেটিভের দিকে তাকাতে হবে।"),
    7: (" ভাবুন তো, কেবল একটিমাত্র বিন্দুতে ফাংশনের মান জেনে আমরা কীভাবে তার চারপাশের পুরো অঞ্চল সম্পর্কে "
        "কিছু বলতে পারি? উত্তর হলো—ডেরিভেটিভ আমাদের সেই তথ্য দেয়। প্রথম ডেরিভেটিভ বলে ঢাল, দ্বিতীয়টি বলে "
        "বাঁক, তৃতীয়টি বলে বাঁকের পরিবর্তন। এই ক্রমিক তথ্যগুলোই পদে পদে বহুপদী তৈরি করে।"),
    8: (" সবচেয়ে সহজ আসন্নায়ন মানেই একটি সরলরেখা টানা। এই রেখাটি মূল বক্ররেখাকে শুধু একটি বিন্দুতে "
        "স্পর্শ করে, কিন্তু তার কাছাকাছি এলে দেখা যায় রেখা আর বক্ররেখা প্রায় মিলে যাচ্ছে। "
        "এই সহজ ধাপ থেকেই আমরা ধীরে ধীরে উপরে উঠব।"),
    9: (" এখান থেকে আমরা শুরু করব স্পর্শক রেখা দিয়ে। মনে রাখবেন, স্পর্শক মানে এমন একটি রেখা যা "
        "বক্ররেখার গতিবেগকে ঠিক সেই বিন্দুতে ধরে রাখে। আমরা দেখব কীভাবে এই একটিমাত্র রেখা থেকেই "
        "আসন্নায়নের প্রথম ধাপটি তৈরি হয়।"),
    10: (" কস শূন্যের মান এক—এই ছোট্ট তথ্যটি আমাদের প্রথম পদের সহগ দিয়ে দেয়। কিন্তু শুধু মান মিলালেই "
         "হবে না, কারণ কাছাকাছি গেলে বক্ররেখা নিচে নামতে শুরু করে। তাই আমাদের আরও একটি শর্ত লাগবে, "
         "যা আসবে প্রথম ডেরিভেটিভ থেকে।"),
    11: (" অনুভূমিক রেখাটি ঠিকই শূন্যে মিলে যায়, কিন্তু একটু সরে গেলেই ভুল বেড়ে যায়। এর কারণ হলো—"
         "কোসাইন বক্ররেখা শূন্যের কাছে নিচের দিকে বাঁকে, অথচ আমাদের রেখা সমানভাবে চলে যায়। "
         "এই বাঁকটিই ধরার জন্য আমাদের দ্বিতীয় পদের প্রয়োজন হবে।"),
    12: (" দুটি শর্ত—মান আর ঢাল—মিলিয়ে আমরা এমন একটি রেখা পাই যা শূন্যের কাছে কোসাইনকে খুব ভালোভাবে "
         "অনুকরণ করে। কসের ক্ষেত্রে ঢাল শূন্য, তাই রেখাটি অনুভূমিকই থাকে। কিন্তু অন্য ফাংশনের ক্ষেত্রে "
         "এই রেখা ঢালু হবে। সাধারণ সূত্রটি আমাদের সেই কাজে সাহায্য করবে।"),
    13: (" খেয়াল করুন, কসের ডেরিভেটিভ মাইনাস সাইন, আর শূন্যে সাইনের মান শূন্য—তাই স্পর্শকের ঢাল শূন্য। "
         "কিন্তু যেকোনো ফাংশনের জন্য সূত্রটি একই: মান যোগ ঢাল গুণ দূরত্ব। এই সূত্রটিই আমাদের প্রথম ক্রমের "
         "আসন্নায়ন, এবং পরের সব পদ এই একই নিয়মে গড়া হয়।"),
    14: (" এই সূত্রের সৌন্দর্য হলো—এটি কেবল একটি বিন্দুর তথ্য ব্যবহার করে তার আশেপাশের পুরো অঞ্চলের "
         "একটি রূপরেখা দেয়। আমরা এখন এই রূপরেখাকে আরও ধারালো করব, কারণ একটি সরলরেখা কখনোই বক্রতা "
         "ধরে রাখতে পারে না।"),
    15: (" সীমাবদ্ধতাটা বুঝা জরুরি: স্পর্শক শুধু তাৎক্ষণিক গতিবেগ দেখায়, কিন্তু বক্ররেখা কোন দিকে বাঁক "
         "নিচ্ছে তা বলে না। যেমন কোসাইন শূন্যের পর নিচে নামে—এই নামাটা একটি সরলরেখা কখনো দেখাতে পারবে না। "
         "তাই আমাদের আর একটি পদ যোগ করতে হবে।"),
    16: (" আমরা এখন একটি ধাপ উপরে যাব। সরলরেখার বদলে নেব একটি পরাবৃত্ত—অর্থাৎ একটি বাঁকা রেখা। "
         "পরাবৃত্তের সুবিধা হলো এটি একটি সরলরেখার চেয়ে বেশি নমনীয় এবং কোসাইনের মতো বক্ররেখার "
         "কাছাকাছি যেতে পারে।"),
    17: (" তিনটি শর্ত মিলিয়ে আমরা তিনটি সহগ নির্ধারণ করব: উচ্চতা, ঢাল আর বক্রতা। এই তিনটি একটি দ্বিঘাত "
         "বহুপদীকে সম্পূর্ণরূপে ঠিক করে দেয়। খেয়াল করুন, প্রতিটি নতুন পদ আমাদের এক অতিরিক্ত ডেরিভেটিভের "
         "তথ্য দেয়—এই নিয়মটি সব পদেই চলবে।"),
    18: (" প্রথম শর্তটি সবচেয়ে সহজ: পদটির মান শূন্যে মূল ফাংশনের মানের সমান হতে হবে। কসের ক্ষেত্রে এটি এক। "
         "এর মানে হলো, আমাদের বহুপদীটি শূন্য বিন্দুতে ঠিক ওই উচ্চতায় থাকবে।"),
    19: (" দ্বিতীয় শর্তটি ঢাল সম্পর্কিত। শূন্যে কোসাইনের ঢাল শূন্য, তাই আমাদের বহুপদীর রৈখিক পদটিও "
         "শূন্য হবে। অন্য ফাংশনের ক্ষেত্রে এই পদটি তার প্রথম ডেরিভেটিভের সমান হবে।"),
    20: (" তৃতীয় শর্তটি সবচেয়ে গুরুত্বপূর্ণ—এখানেই বক্রতা বা দ্বিতীয় ডেরিভেটিভটি কাজে আসে। এই শর্তটি "
         "আমাদের বলে দেয় বহুপদীটি কতটা বাঁকবে। কসের ক্ষেত্রে দ্বিতীয় ডেরিভেটিভ ঋণাত্মক, তাই পরাবৃত্তটি "
         "নিচের দিকে খোলা হবে।"),
    21: (" পাওয়ার রুলের কারণে দ্বিঘাত পদটিকে দুইবার ডিফারেনশিয়েট করলে সামনে দুই গুণ চলে আসে। এই ছোট্ট "
         "ঘটনাটিই সহগের মান নির্ধারণ করে দেয়। লক্ষ্য করুন, ঘাত যত বাড়বে, এই গুণক তত বড় হবে—এবং শেষে "
         "আমাদের এন ফ্যাক্টোরিয়ালের মুখোমুখি হতে হবে।"),
    22: (" যার অর্থ, সি টু সমান এফ ডাবল প্রাইম শূন্য ভাগ দুই। অর্থাৎ কসের দ্বিতীয় ডেরিভেটিভ মাইনাস এক, "
         "তাই সহগ হবে মাইনাস এক ভাগ দুই। ফলে আমরা পাই এক বিয়োগ এক্স স্কয়ার ভাগ দুই—যা শূন্যের কাছে "
         "কোসাইনের একদম কাছাকাছি মান দেয়।"),
    23: (" এই সূত্রটি আমাদের প্রথম অর্থপূর্ণ আসন্নায়ন। এক বিয়োগ এক্স স্কয়ার ভাগ দুই—মাত্র দুটি পদ "
         "দিয়েই কোসাইনকে এত ভালোভাবে ধরা যায়! এক্সের মান বাড়লে ধীরে ধীরে পার্থক্য বাড়বে, কিন্তু "
         "কাছাকাছি অঞ্চলে এটি প্রায় নিখুঁত।"),
    24: (" ফ্যাক্টোরিয়ালের উৎপত্তি এই পাওয়ার রুল থেকেই। প্রতিবার ডেরিভেটিভ নেওয়ার সময় ঘাত এক করে কমে যায় "
         "ও সামনে গুণ হয়, তাই এন বার ডেরিভেটিভে এন গুণ এন মাইনাস এক এবং এভাবে এক পর্যন্ত গুণ হয়ে "
         "এন ফ্যাক্টোরিয়াল তৈরি হয়। সহগকে ঠিক রাখতে আমাদের এই অতিরিক্ত গুণককে ভাগ করে দিতে হয়।"),
    25: (" এই পর্যবেক্ষণ আমাদের সাধারণ সূত্রের দিকে নিয়ে যায়। এখন আমরা আর কোনো নির্দিষ্ট পদে আটকে "
         "থাকব না—বরং যেকোনো এন-তম পদের জন্যই একক সূত্র লিখব।"),
    26: (" আমরা এখন টেইলর ধারার সাধারণ রূপে পৌঁছাব। এখান থেকে সবকিছু একটিমাত্র সূত্রে বাঁধা পড়বে—"
         "একক বিন্দুর ডেরিভেটিভসমূহ থেকে গড়া এক অসীম ধারা।"),
    27: (" তৃতীয় ডেরিভেটিভ মেলাতে এক্স কিউবকে তিনবার ডিফারেনশিয়েট করলাম, ফলে পেলাম তিন গুণ দুই গুণ "
         "এক, অর্থাৎ ছয় বা থ্রি ফ্যাক্টোরিয়াল। তাই সহগ হবে এফ ট্রিপল প্রাইম ভাগ ছয়। এই নিয়মটি কোনো "
         "বিশেষ পদের নয়—প্রতিটি পদের জন্য একই রকম কাজ করে।"),
    28: (" যেকোনো এন-তম পদের সহগ হলো ওই বিন্দুতে এন-তম ডেরিভেটিভ ভাগ এন ফ্যাক্টোরিয়াল। যখন কেন্দ্র শূন্য, "
         "তখন একে ম্যাকলরিন ধারা বলা হয়। নাম যাই হোক, কাজ একই—এক বিন্দুতে জড়ো করা তথ্য দিয়ে "
         "পুরো ফাংশনটিকে পুনর্গঠন করা।"),
    29: (" যদি কেন্দ্র শূন্য না হয়, তবে আমরা এক্স বিয়োগ এ ব্যবহার করি। এর মানে হলো—আমরা বহুপদীটিকে "
         "এ বিন্দু থেকে শুরু করে স্থানচ্যুত করছি। এই ছোট্ট পরিবর্তনটি আমাদের যেকোনো বিন্দুতে টেইলর "
         "ধারা লিখতে দেয়।"),
    30: (" এই হলো পূর্ণাঙ্গ টেইলর ধারা—অসীম সংখ্যক পদের একটি যোগফল, যার প্রতিটি পদ ডেরিভেটিভ আর "
         "ফ্যাক্টোরিয়াল দিয়ে তৈরি। মনে হতে পারে অসীম পদ যোগ করা অসম্ভব, কিন্তু বাস্তবে কয়েকটি পদেই "
         "আমরা দারুণ ফল পাই।"),
    31: (" পদ বাড়ানোর সাথে সাথে বহুপদীটি কেন্দ্র থেকে দূরে ছড়িয়ে পড়ে এবং মূল বক্ররেখার বাঁকগুলোকে "
         "আবরণ করে নেয়। যত বেশি পদ, তত বেশি নিখুঁত—এই হলো অসীম ধারার জাদু।"),
    32: (" এখন আমরা একটা গুরুত্বপূর্ণ প্রশ্ন তুলব: এই ধারা কি সব জায়গায় কাজ করে? উত্তর হলো—সবসময় নয়। "
         "কোনো কোনো ফাংশনের ক্ষেত্রে একটি সীমা থাকে, যার বাইরে ধারাটি ভেঙে পড়ে।"),
    33: (" এক বিন্দুতে সব ডেরিভেটিভ জেনে আমরা কি দূরের কোনো বিন্দুতে ফাংশনের মান বের করতে পারব? "
         "এই প্রশ্নটি খুব গভীর, কারণ এটি আমাদের স্থানীয় তথ্য আর বৈশ্বিক জ্ঞানের মধ্যে সম্পর্ক স্থাপন "
         "করতে বলে।"),
    34: (" ই, সাইন আর কোসাইনের মতো ফাংশনের ধারা সব জায়গায় অভিসৃত হয়, কিন্তু ওয়ান বাই ওয়ান মাইনাস "
         "এক্সের মতো ফাংশনের ক্ষেত্রে একের চেয়ে বড় এক্সে ধারাটি অর্থহীন হয়ে পড়ে। একে বলা হয় "
         "অভিসারী ব্যাসার্ধ। এক্সের মান একের কাছে পৌঁছালেই পদগুলো বড়তে থাকে এবং যোগফল নিয়ন্ত্রণ "
         "হারিয়ে ফেলে। একের বাইরে গেলে তো কথাই নেই—ধারাটি দ্রুত অসীমে চলে যায়। তবে একের চেয়ে "
         "ছোট এক্সের ক্ষেত্রে প্রতিটি নতুন পদ আগেরটির চেয়ে ছোট হয় এবং যোগফল শান্তভাবে একটিমাত্র "
         "মানের দিকে এগিয়ে যায়। এই কারণেই কেন্দ্রবিন্দু থেকে এক্সের দূরত্ব আমাদের জন্য এত গুরুত্বপূর্ণ।"),
    35: (" এই কারণেই টেইলর ধারা কেবল তাত্ত্বিক নয়—এটি আধুনিক বিজ্ঞানের মেরুদণ্ড। ছোট ছোট পরিবর্তনের "
         "হিসাব, তরঙ্গের সমীকরণ, এমনকি মেশিন লার্নিংয়ের অপটিমাইজেশন—সব জায়গায় এই একই ধারণা "
         "কাজে লাগে।"),
    36: (" অভিসারী ব্যাসার্ধ আমাদের বলে দেয় ধারাটি কতদূর পর্যন্ত বিশ্বাসযোগ্য। আর ল্যাগ্রাঞ্জ "
         "অবশিষ্টাংশ আমাদের বলে দেয় কতটি পদ নিলে কতটা ভুল থাকবে—অর্থাৎ ব্যবহারিক গণনার জন্য "
         "এটি অপরিহার্য।"),
    37: (" আজ আমরা দেখলাম কীভাবে একক বিন্দুর ডেরিভেটিভসমূহ থেকে একটি পুরো ফাংশনকে পুনর্নির্মাণ করা যায়। "
         "টেইলর ধারা স্থানীয় তথ্যকে বৈশ্বিক জ্ঞানে রূপান্তরিত করে। পরের পাঠে নতুন কিছু নিয়ে আবার "
         "দেখা করব। আবার দেখা হবে!"),
}

# ---- HEAVY expansion layer 2 (new): extra pedagogical narration so the
# rendered speech, not the authored timing, spans the full video. ----
HEAVY_EXPANSIONS = {
    1: (" আসুন প্রথমে এই প্রশ্নটি মনে রাখি: একটি ফাংশনকে বহুপদী দিয়ে কীভাবে ধরা যায়? "
        "আজকের পাঠে আমরা ধাপে ধাপে এই প্রশ্নের উত্তর খুঁজব এবং দেখব কীভাবে কয়েকটি সহগই "
        "একটি জটিল বক্ররেখার পুরো গল্প বলে দিতে পারে।"),
    2: (" কনওয়ের এই উদ্ধৃতিটি আমাদের মনে করিয়ে দেয় যে গণিত শেখার অর্থ হলো উদাহরণ থেকে সাধারণ নিয়ম "
        "বের করা। প্রতিটি উদাহরণ আমাদের কাছে এক ধাপের মতো, যা শেষে এক সুন্দর তত্ত্বে পৌঁছে দেয়। "
        "তাই উদাহরণগুলোকে উপেক্ষা করবেন না—সেগুলোই আসল পথপ্রদর্শক।"),
    3: (" পেন্ডুলামের উদাহরণটি বিশেষ কারণ এখানে কোসাইন এসে পড়ে—আমাদের পরিচিত এক ফাংশন, কিন্তু সরাসরি "
        "হিসাব করা কঠিন। আসন্নায়ন আমাদের সেই কঠিন অংশটিকে সহজ করে দেয়। এই কৌশল সব জায়গায় কাজ করে।"),
    4: (" এখন প্রশ্ন হলো এই আসন্নায়নটি কোথা থেকে আসে? টেইলর ধারার উত্তর হলো—ফাংশনের ডেরিভেটিভগুলোই "
        "সেই সহগগুলো নির্ধারণ করে। আমরা ধীরে ধীরে দেখব কীভাবে মান, ঢাল ও বাঁক একের পর এক যোগ হয়ে "
        "বহুপদীটি গড়ে তোলে।"),
    5: (" কম্পিউটারের দৃষ্টিকোণ থেকে এই পদ্ধতি অপরিহার্য। গুণ ও যোগ ছাড়া অন্য কোনো ক্রিয়া না করে আমরা "
        "কোসাইন বা ই-এর মতো ফাংশনের মান বের করতে পারি। এই কথাটি মনে রাখলে টেইলর ধারার উপযোগিতা "
        "আপনার কাছে স্পষ্ট হয়ে যাবে।"),
    6: (" সূত্রটিতে এক্স বিয়োগ এ এই অংশটি আসলে কেন্দ্রবিন্দু থেকে দূরত্ব মাপে। এক্স সমান এ বসালে সব পদ "
        "শূন্য হয়ে যায়—এই সুন্দর বাতিলটি আমাদের হিসাবকে সহজ করে দেয়। পদ বাড়ালেও এই বাতিল অটল থাকে।"),
    7: (" আমাদের চূড়ান্ত লক্ষ্য হলো একটিমাত্র বিন্দুতে পাওয়া তথ্য দিয়ে তার আশেপাশের অঞ্চল পুনর্নির্মাণ করা। "
        "এর জন্য প্রথম ধাপ হলো স্পর্শক রেখা, যা ফাংশনের মান ও ঢাল দুটোই মেলায়। এরপর আসবে বক্রতা।"),
    8: (" রৈখিক আসন্নায়নকে বলা হয় প্রথম ক্রমের আসন্নায়ন। এটি কেবল শূন্যের কাছে কাজ করে—দূরে গেলে ভুল "
        "বেড়ে যায়। এই সীমাটি মনে রাখলে পরের পদগুলোর প্রয়োজন আপনার কাছে সহজেই বোঝা যাবে।"),
    9: (" স্পর্শক রেখার ধারণাটি কেবল গণিতে নয়, দৈনন্দিন জীবনেও কাজে লাগে—যেকোনো পরিবর্তনের তাৎক্ষণিক "
        "হার আমরা এই রেখা দিয়ে বুঝি। আজ আমরা দেখব এই রেখা কীভাবে টেইলর ধারার প্রথম পদ হয়ে ওঠে।"),
    10: (" শূন্যে কোসাইনের মান এক, তাই আমাদের প্রথম পদ এক। কিন্তু কোসাইন শূন্যের পর নিচে নামে—এই নামা "
         "আমরা ধরতে পারব দ্বিতীয় পদ দিয়ে। প্রথম পদটি শুধু ভিত্তি, পুরো গল্প নয়।"),
    11: (" অনুভূমিক রেখা শূন্যে ঠিক মিলে যায়, কিন্তু একটু দূরে গেলেই ফাঁক দেখা দেয়। এই ফাঁকটিই পরবর্তী "
         "পদের ইঙ্গিত দেয়—আমাদের আরও একটি শর্ত যোগ করতে হবে। ফাঁক যত ছোট, আসন্নায়ন তত ভালো।"),
    12: (" মান ও ঢাল—এই দুই শর্ত মিলে স্পর্শক রেখা নির্ধারণ হয়। কসের ক্ষেত্রে ঢাল শূন্য, তাই রেখা "
         "অনুভূমিক। অন্য ফাংশনে এই রেখা ঢালু হবে, কিন্তু নিয়ম একই। সূত্রটি সবার জন্য কাজ করে।"),
    13: (" ডি বাই ডিএক্স অফ কোস ইজ মাইনাস সাইন—এই সরল ডেরিভেটিভটি আমাদের ঢাল দেয়। সাধারণ সূত্রে আমরা "
         "এক বিন্দুর মান ও ঢাল যোগ করে কাছাকাছি বিন্দুর মান আনুমানিক করি। ছোট দূরত্বে ফলাফল চমৎকার।"),
    14: (" এই প্রথম ক্রমের সূত্রটি ছোট বিচ্যুতির জন্য যথেষ্ট ভালো, কিন্তু বড় বিচ্যুতিতে ভুল বাড়ে। "
         "তাই আমাদের আরও উচ্চতর পদ যোগ করতে হবে—এই কথা মনে রেখে আমরা পরবর্তী ধাপে যাব।"),
    15: (" স্পর্শক কেবল গতিবেগ দেখায়, বক্রতা নয়। কোসাইন শূন্যের পর যেভাবে নিচে বাঁকে, তা একটি সরলরেখা "
         "কখনো দেখাতে পারে না। এই সীমাবদ্ধতাই আমাদের দ্বিতীয় পদের দিকে নিয়ে যায়।"),
    16: (" পরাবৃত্ত অর্থাৎ দ্বিঘাত বহুপদী আমাদের একটি অতিরিক্ত স্বাধীনতা দেয়—সেটি হলো বক্রতা। এই এক পদ "
         "যোগ করে আমরা কোসাইনের বাঁকটিকে ধরতে পারব। সরলরেখার চেয়ে পরাবৃত্ত অনেক বেশি নমনীয়।"),
    17: (" তিনটি শর্ত—উচ্চতা, ঢাল ও বক্রতা—একটি দ্বিঘাত বহুপদীকে সম্পূর্ণ ঠিক করে দেয়। লক্ষ্য করুন, "
         "প্রতিটি নতুন পদ এক নতুন ডেরিভেটিভের তথ্য নিয়ে আসে। এই নিয়মটি সব পদেই বারবার কাজ করে।"),
    18: (" প্রথম শর্ত থেকে পাই সি নট সমান এফ অফ শূন্য। কসের ক্ষেত্রে এটি এক। এই সহগটি আমাদের বহুপদীটির "
         "উচ্চতা নির্ধারণ করে—বাকি সহগগুলো তার আকৃতি গড়ে তোলে।"),
    19: (" দ্বিতীয় শর্ত থেকে সি ওয়ান পাই, যা ঢাল নির্ধারণ করে। কসের ক্ষেত্রে এই সহগ শূন্য, তাই রৈখিক "
         "পদটি বাদ যায়। অন্য ফাংশনে এটি প্রথম ডেরিভেটিভের সমান হবে।"),
    20: (" তৃতীয় শর্তটি সবচেয়ে গুরুত্বপূর্ণ—এখানে বক্রতা মেলানো হয়। কসের দ্বিতীয় ডেরিভেটিভ ঋণাত্মক, "
         "তাই পরাবৃত্তটি নিচের দিকে খোলা হবে। চিহ্নটি আমাদের বলে দেয় কোন দিকে বাঁক নিতে হবে।"),
    21: (" দ্বিঘাত পদকে দুইবার ডিফারেনশিয়েট করলে সামনে দুই চলে আসে। এই ছোট্ট গুণকটি সহগ নির্ধারণে মূল "
         "ভূমিকা পালন করে এবং পরে এন ফ্যাক্টোরিয়ালের রূপ নেয়। ঘাত যত বাড়ে, গুণক তত বড়।"),
    22: (" সি টু সমান এফ ডাবল প্রাইম ভাগ দুই—কসের ক্ষেত্রে মাইনাস এক ভাগ দুই। ফলে আসন্নায়ন হয় "
         "এক বিয়োগ এক্স স্কয়ার ভাগ দুই, যা শূন্যের কাছে প্রায় নিখুঁত। দুইয়ের ভাগটি মনে রাখবেন।"),
    23: (" মাত্র দুটি পদ দিয়েই কোসাইনকে এত কাছ থেকে ধরা যায়—এই বিস্ময়টি টেইলর ধারার শক্তি। এক্স বাড়লে "
         "পার্থক্য বাড়বে, কিন্তু কাছাকাছি এটি প্রায় সঠিক। এক্স শূন্য দশমিক এক বসালেই তা দেখা যায়।"),
    24: (" ফ্যাক্টোরিয়াল আসে পাওয়ার রুল থেকে। প্রতিবার ডেরিভেটিভে ঘাত এক কমে ও সামনে গুণ হয়—এন বারে "
         "এন ফ্যাক্টোরিয়াল তৈরি হয়, যাকে আমরা সহগ থেকে ভাগ করে দিই। এই ভাগটি না দিলে সহগ ভুল হবে।"),
    25: (" এই পর্যবেক্ষণ আমাদের নির্দিষ্ট পদ থেকে সাধারণ সূত্রে নিয়ে যায়। এখন আমরা আর কোনো এক পদে "
         "আটকে থাকব না—প্রতিটি এন-তম পদের জন্য একক নিয়ম লিখব। সূত্রটি সব পদে একইভাবে কাজ করে।"),
    26: (" আজ থেকে আমরা টেইলর ধারার সাধারণ রূপ নিয়ে কাজ করব। সমস্ত পদ একটিমাত্র সূত্রে বাঁধা পড়বে—"
         "ডেরিভেটিভ আর ফ্যাক্টোরিয়ালের এক অসীম যোগফল। এই সূত্রই পুরো পাঠের কেন্দ্রবিন্দু।"),
    27: (" তৃতীয় ডেরিভেটিভে পেলাম থ্রি ফ্যাক্টোরিয়াল অর্থাৎ ছয়। কসের তৃতীয় ডেরিভেটিভ শূন্যে শূন্য, "
         "তাই ঘনক পদটি বাদ যায়—একই আসন্নায়ন আবারও কাজ করে। এই ধরনের বাতিল আমরা বারবার দেখব।"),
    28: (" এন-তম সহগ হলো এন-তম ডেরিভেটিভ ভাগ এন ফ্যাক্টোরিয়াল। কেন্দ্র শূন্য হলে একে ম্যাকলরিন ধারা "
         "বলা হয়; নাম আলাদা হলেও কাজ একই। এই ধারা আমাদের অনেক পরিচিত ফাংশনের রূপ দেয়।"),
    29: (" যেকোনো বিন্দুতে ধারা লিখতে আমরা এক্স বিয়োগ এ ব্যবহার করি। এই স্থানচ্যুতি ছোট্ট হলেও এর "
         "মাধ্যমে আমরা পুরো ফাংশনকে নতুন কেন্দ্রে সাজাতে পারি। পাই বিন্দুর কাছে এটি দারুণ কাজ করে।"),
    30: (" পূর্ণাঙ্গ টেইলর ধারা একটি অসীম যোগফল—কিন্তু বাস্তবে কয়েকটি পদেই আমরা দারুণ ফল পাই। "
         "অসীমের ভয় নেই, লিমিটের মাধ্যমে সবকিছু সুসংজ্ঞায়িত। বেশি পদ মানে বেশি নিখুঁত।"),
    31: (" পদ বাড়ালে বহুপদী কেন্দ্র থেকে দূরে ছড়ায় আর মূল বক্ররেখার বাঁকগুলো আবরণ করে। যত বেশি পদ, "
         "তত বেশি নিখুঁত—এই হলো ধারার জাদু। কয়েকটি পদেই বক্ররেখা চোখে পড়ার মতো মিলে যায়।"),
    32: (" এখন একটা গুরুত্বপূর্ণ প্রশ্ন: ধারাটি কি সব জায়গায় কাজ করে? উত্তর হলো সবসময় নয়। কোনো কোনো "
         "ফাংশনের একটি সীমা থাকে, যার বাইরে ধারাটি ভেঙে পড়ে। এই সীমাটি বুঝা আমাদের জন্য জরুরি।"),
    33: (" এক বিন্দুতে সব ডেরিভেটিভ জেনে দূরের বিন্দুর মান বের করার প্রশ্নটি স্থানীয় ও বৈশ্বিক জ্ঞানের "
         "সেতু তৈরি করে। এই প্রশ্নের উত্তর আমাদের অভিসারী ব্যাসার্ধের ধারণা দেয়—একটি অত্যন্ত "
         "গুরুত্বপূর্ণ ধারণা।"),
    34: (" ওয়ান বাই ওয়ান মাইনাস এক্সের ধারা কেবল একের চেয়ে ছোট এক্সেই কাজ করে। একের কাছে পদগুলো বড় "
         "হতে থাকে আর বাইরে যোগফল অর্থহীন হয়—এই সীমাটি বুঝা জরুরি। কিন্তু একের ভেতরে যোগফল শান্তভাবে "
         "একটিমাত্র মানের দিকে এগিয়ে যায়। দূরত্ব কমলে ধারা দ্রুত কাজ করে।"),
    35: (" টেইলর ধারা আধুনিক বিজ্ঞানের মেরুদণ্ড। শক্তির হিসাব, তরঙ্গের সমীকরণ, এমনকি মেশিন লার্নিংয়ের "
         "অপটিমাইজেশন—সব জায়গায় এই একই ধারণা কাজে লাগে। ছোট পরিবর্তনের হিসাব ছাড়া আধুনিক প্রযুক্তি "
         "অসম্ভব।"),
    36: (" অভিসারী ব্যাসার্ধ বলে দেয় ধারা কতদূর বিশ্বাসযোগ্য, আর ল্যাগ্রাঞ্জ অবশিষ্টাংশ বলে দেয় কত পদ "
         "নিলে কত ভুল থাকবে। ব্যবহারিক গণনার জন্য এই দুটি তথ্যই যথেষ্ট। ভুলের পরিমাণ আগে থেকে জানা "
         "থাকলে আমরা আত্মবিশ্বাসের সাথে ফলাফল ব্যবহার করতে পারি।"),
    37: (" আজ আমরা দেখলাম একক বিন্দুর ডেরিভেটিভ থেকে পুরো ফাংশন পুনর্নির্মাণ। স্থানীয় তথ্য বৈশ্বিক জ্ঞানে "
         "রূপ নিল—এই হলো টেইলর ধারার সৌন্দর্য। এই কৌশল আপনার ক্যালকুলাস যাত্রায় বারবার কাজে আসবে।"),
}

GENERIC_EXTRA = (
    " এখানে একটু থামুন এবং বিষয়টি নিজের ভাষায় বলে দেখুন। কোনো ধারণা তখনই পোক্ত হয় যখন আপনি "
    "সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন। এই অভ্যাস আপনার বোঝাপড়াকে আরও গভীর করবে।"
)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def is_win1450(err):
    return getattr(err, "winerror", None) == 1450 or "1450" in str(err)


def run(cmd, retries=6):
    last = None
    for attempt in range(retries):
        try:
            r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
            if r.returncode == 0:
                return r.stdout
            last = RuntimeError(f"cmd failed: {cmd}\n{r.stderr[-1500:]}")
        except OSError as e:
            last = e
            if not is_win1450(e):
                raise
        if attempt < retries - 1:
            time.sleep(0.5 * (attempt + 1))
    raise last


def duration(path):
    out = run(f'ffprobe -v error -show_entries format=duration '
              f'-of default=noprint_wrappers=1:nokey=1 "{path}"')
    try:
        return float(out.strip())
    except Exception:
        return 0.0


def video_duration(path):
    d = duration(path)
    try:
        sd = float(run(f'ffprobe -v error -select_streams v:0 -show_entries stream=duration '
                       f'-of default=noprint_wrappers=1:nokey=1 "{path}"').strip())
        d = max(d, sd)
    except Exception:
        pass
    return d


def sanitize(text):
    t = text
    for ch in ["—", "–", "−", "-"]:
        t = t.replace(ch, ", ")
    for ch in ["'", '"', "[", "]", "{", "}", "*", "#", "`"]:
        t = t.replace(ch, " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t.strip(" ,;:।.")


async def tts_save(text, path, rate="+0%"):
    last = None
    for attempt in range(5):
        try:
            await edge_tts.Communicate(text, VOICE, rate=rate).save(str(path))
            return
        except OSError as e:
            last = e
            if not is_win1450(e):
                raise
            await asyncio.sleep(0.5 * (attempt + 1))
        except Exception:
            raise
    if last is not None:
        raise last


def valid(raw):
    return raw.exists() and raw.stat().st_size > 500 and duration(raw) > 0.3


def purge(path):
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass


async def synth(text, raw, force=False):
    if not force and valid(raw):
        return True
    purge(raw)
    ok = False
    for attempt in range(12):
        try:
            rate = "+0%" if attempt < 4 else ("-5%" if attempt < 8 else "+5%")
            await tts_save(text, raw, rate)
            if valid(raw):
                ok = True
                break
        except Exception:
            pass
        purge(raw)
        await asyncio.sleep(0.4)
    if not ok:
        mid = len(text) // 2
        parts = [text[:mid].strip(" ,;:।."), text[mid:].strip(" ,;:।.")]
        made = []
        for j, p in enumerate(parts):
            pp = RAW_DIR / f"half_{raw.stem}_{j}.mp3"
            purge(pp)
            if not p:
                continue
            try:
                await tts_save(p, pp)
                if valid(pp):
                    made.append(pp)
            except Exception:
                pass
        if made:
            lf = RAW_DIR / f"list_{raw.stem}.txt"
            with open(lf, "w", encoding="utf-8") as f:
                for x in made:
                    f.write(f"file '{x.as_posix()}'\n")
            run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{raw}" > NUL 2>&1')
            ok = valid(raw)
    if not ok:
        parts = [p.strip() for p in re.split(r"[।]", text) if p.strip()]
        made = []
        for j, p in enumerate(parts):
            pp = RAW_DIR / f"sent_{raw.stem}_{j}.mp3"
            purge(pp)
            try:
                await tts_save(p + "।", pp)
                if valid(pp):
                    made.append(pp)
            except Exception:
                pass
        if made:
            lf = RAW_DIR / f"sentlist_{raw.stem}.txt"
            with open(lf, "w", encoding="utf-8") as f:
                for x in made:
                    f.write(f"file '{x.as_posix()}'\n")
            run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{raw}" > NUL 2>&1')
            ok = valid(raw)
    return ok


# ---------------------------------------------------------------------------
# Manifest (read-only) — alias-deduped
# ---------------------------------------------------------------------------
def load_manifest_cues():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out, seen = [], set()
    for sec_id, sec in data.get("sections", {}).items():
        alias = str(sec.get("alias") or sec_id)
        for c in sec.get("cues", []):
            text = c.get("text")
            if not text:
                continue
            # alias-dedupe: (section alias, absolute start, text prefix).
            key = (alias, round(float(c.get("start_ms", 0)), 1), text[:80])
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "text": text,
                "dur_ms": float(c.get("duration_ms", 0)),
                "section": str(sec.get("section_id") or sec_id),
            })
    return out, f"audio_manifest:{MANIFEST.name} (alias-deduped, {len(out)} cues)"


# ---------------------------------------------------------------------------
# Dense speech clips: trim edges, squeeze internal silent runs
# ---------------------------------------------------------------------------
def decode_pcm(path):
    norm = path.with_suffix(".dec.wav")
    run(f'ffmpeg -y -i "{path}" -af aresample=44100 -ar 44100 -ac 1 '
        f'-c:a pcm_s16le "{norm}" > NUL 2>&1')
    with wave.open(str(norm), "rb") as w:
        arr = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    try:
        os.remove(norm)
    except OSError:
        pass
    return arr


def write_wav(path, arr):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(arr, -1, 1) * 32767).astype("<i2").tobytes())


def densify(arr, thresh=SILENCE_THRESH, cap_s=MAX_INTERNAL_PAUSE_S,
            edge_ms=EDGE_PAD_MS):
    """Trim leading/trailing silence and cap internal silent runs.

    No speech samples are ever removed; only silence beyond `cap_s` is dropped.
    """
    active = np.abs(arr) > thresh
    idx = np.flatnonzero(active)
    if idx.size == 0:
        return arr.astype(np.float32)
    d = np.diff(idx)
    br = np.flatnonzero(d > 1)
    starts = np.concatenate(([idx[0]], idx[br + 1]))
    ends = np.concatenate((idx[br], [idx[-1]]))
    cap_n = int(round(cap_s * SR))
    merged = []
    for s, e in zip(starts, ends):
        s, e = int(s), int(e)
        if merged and s - merged[-1][1] <= cap_n:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    pieces, prev_end = [], None
    for s, e in merged:
        seg = arr[s:e + 1]
        if prev_end is None:
            pieces.append(seg)
        else:
            gap = s - prev_end
            keep = min(gap, cap_n)
            if keep > 0:
                pieces.append(np.zeros(keep, dtype=np.float32))
            pieces.append(seg)
        prev_end = e + 1
    out = np.concatenate(pieces) if pieces else arr.astype(np.float32)
    pad = int(round(edge_ms / 1000.0 * SR))
    if pad:
        out = np.concatenate((np.zeros(pad, dtype=np.float32), out,
                              np.zeros(pad, dtype=np.float32)))
    return out.astype(np.float32)


def build_dense_clips(cues):
    """Synthesise + densify every cue; return dense WAV paths & durations."""
    info = []
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        dense = CUE_DIR / f"dense_{cid:03d}.wav"
        arr = densify(decode_pcm(raw))
        write_wav(dense, arr)
        info.append({"id": cid, "dense_sec": len(arr) / SR, "path": dense})
    return info


def recompute_scale(clip_info, usable):
    """Scale based on RENDERED (dense) speech, not authored cue durations."""
    n = len(clip_info)
    pause_total = (n - 1) * INTER_CUE_PAUSE_SEC
    budget = usable - pause_total
    total_speech = sum(x["dense_sec"] for x in clip_info)
    scale = budget / total_speech if total_speech > 0 else 1.0
    return scale, total_speech, pause_total, budget


def layout(cues, clip_info, scale):
    """Place dense speech contiguously; one common tempo tiles the timeline."""
    positions, cursor = [], LEAD_IN_SEC
    for c, ci in zip(cues, clip_info):
        target = ci["dense_sec"] * scale
        positions.append({"id": c["id"], "start": cursor, "target": target,
                          "dense_sec": ci["dense_sec"], "path": ci["path"]})
        cursor += target + INTER_CUE_PAUSE_SEC
    return positions, cursor


# ---------------------------------------------------------------------------
# Fit + absolute-sample placement
# ---------------------------------------------------------------------------
LAST_START, VIDEO_END, LAST_ID = 0.0, 0.0, None


def fit_clip(dense_path, target, cid, tempo_hint):
    """atempo-fit the dense clip to the window; PAD only, never cut speech."""
    natural = duration(dense_path)
    tempo = max(TEMPO_FLOOR, min(MAX_TEMPO, tempo_hint))
    tmp = CUE_DIR / f"fit_{cid:03d}.wav"
    run(f'ffmpeg -y -i "{dense_path}" -af "atempo={tempo:.5f}" '
        f'-ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = decode_pcm(tmp)
    try:
        os.remove(tmp)
    except OSError:
        pass
    need = int(round(target * SR))
    if len(arr) < need:
        arr = np.pad(arr, (0, need - len(arr)))
    elif len(arr) > need:
        # Only trailing edge-padding may be shaved; speech is never truncated.
        arr = arr[:need]
    return arr.astype(np.float32), tempo, natural


def silent_runs(arr, thresh=SILENCE_THRESH, min_s=0.05):
    """Return [(start_sample, end_sample_exclusive, duration_sec), ...]."""
    inactive = (np.abs(arr) <= thresh).astype(np.int8)
    d = np.diff(np.concatenate(([0], inactive, [0])))
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1)
    out = []
    for s, e in zip(starts, ends):
        dur = (e - s) / SR
        if dur >= min_s:
            out.append((int(s), int(e), round(dur, 4)))
    return out


def volumedetect(path, start, length):
    log = EXP / "_volumedetect.log"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-nostats", "-vn", "-i", str(path),
           "-af", f"atrim=start={start}:duration={length},volumedetect",
           "-f", "null", "-"]
    for attempt in range(6):
        try:
            with open(log, "wb") as fh:
                subprocess.run(cmd, stdout=fh, stderr=fh)
            break
        except OSError as e:
            if not is_win1450(e):
                raise
            time.sleep(0.5 * (attempt + 1))
    txt = log.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"mean_volume:\s*([-\d.]+) dB", txt)
    return float(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC

    source_cues, source_desc = load_manifest_cues()
    cues = []
    for i, c in enumerate(source_cues):
        cid = i + 1
        text = c["text"]
        exp = EXPANSIONS.get(cid, "")
        heavy = HEAVY_EXPANSIONS.get(cid, "")
        cues.append({
            "id": cid,
            "bn": sanitize(f"{text} {exp} {heavy}"),
            "base_bn": text,
            "section": c["section"],
        })
    LAST_ID = cues[-1]["id"]
    print(f"video={vend:.3f}s usable={usable:.3f}s cues={len(cues)} source={source_desc}",
          flush=True)

    # ---- TTS with iterative expansion until recomputed tempo is natural ----
    extra_passes = 0
    for p in range(3):
        print(f"[1/6] TTS pass {p + 1} ({len(cues)} cues) ...", flush=True)
        failed = []
        for i, c in enumerate(cues):
            raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
            if not await synth(c["bn"], raw, force=(p > 0)):
                failed.append(c["id"])
                print(f"  WARNING cue {c['id']} failed after every fallback", flush=True)
            if (i + 1) % 10 == 0:
                print(f"  TTS {i + 1}/{len(cues)}", flush=True)
        if failed:
            raise RuntimeError(f"TTS failed for cues {failed}")

        clip_info = build_dense_clips(cues)
        scale, total_speech, pause_total, budget = recompute_scale(clip_info, usable)
        tempo_hint = 1.0 / scale
        print(f"  rendered dense speech={total_speech:.2f}s ; scale={scale:.4f} ; "
              f"implied tempo={tempo_hint:.4f}", flush=True)
        if TEMPO_FLOOR <= tempo_hint <= MAX_TEMPO:
            break
        extra_passes += 1
        if tempo_hint < TEMPO_FLOOR:
            # Too little rendered speech to tile the video without slowing below
            # the floor: add one more pedagogical sentence and re-synthesise.
            print(f"  tempo {tempo_hint:.4f} < floor -> adding expansion pass", flush=True)
            for c in cues:
                c["bn"] = sanitize(c["bn"] + " " + GENERIC_EXTRA)
        else:
            # Too much rendered speech: drop the heavy layer and re-synthesise.
            print(f"  tempo {tempo_hint:.4f} > cap -> dropping heavy layer", flush=True)
            for c in cues:
                c["bn"] = sanitize(c["base_bn"] + " " + EXPANSIONS.get(c["id"], ""))

    if not (TEMPO_FLOOR <= tempo_hint <= MAX_TEMPO):
        raise RuntimeError(f"recomputed tempo {tempo_hint:.4f} outside "
                           f"[{TEMPO_FLOOR}, {MAX_TEMPO}] after {extra_passes} extra passes")

    positions, timeline_end = layout(cues, clip_info, scale)
    LAST_START = positions[-1]["start"]
    print(f"[2/6] Layout from rendered speech: scale={scale:.4f} tempo={tempo_hint:.4f} "
          f"timeline_end={timeline_end:.3f}s (target {vend - TAIL_MARGIN_SEC:.3f}s)",
          flush=True)

    # ---- Absolute placement on a FULL-length canvas ----
    print("[3/6] Absolute sample placement ...", flush=True)
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed, fills, gaps = [], [], []
    for pos in positions:
        cid = pos["id"]
        target = pos["target"]
        if cid == LAST_ID:
            target = min(target, VIDEO_END - LAST_START - 0.10)
        arr, tempo, natural = fit_clip(Path(pos["path"]), target, cid, tempo_hint)
        if len(arr) >= 2 * fade_n:
            arr[:fade_n] *= env
            arr[-fade_n:] *= env[::-1]
        active_frac = float(np.mean(np.abs(arr) > SILENCE_THRESH))
        runs = silent_runs(arr, min_s=0.05)
        gap = max((r[2] for r in runs), default=0.0)
        fills.append(active_frac)
        gaps.append(gap)
        start_sample = int(round(pos["start"] * SR))
        end = start_sample + len(arr)
        if end > len(canvas):
            canvas = np.pad(canvas, (0, end - len(canvas)))
        i16 = (np.clip(arr, -1.0, 1.0) * 32767.0).astype(np.int16)
        seg = canvas[start_sample:end].astype(np.int32)
        seg += i16.astype(np.int32)
        np.clip(seg, -32768, 32767, out=seg)
        canvas[start_sample:end] = seg.astype(np.int16)
        placed.append({
            "id": cid,
            "section": next(c["section"] for c in cues if c["id"] == cid),
            "start_sec": round(pos["start"], 3),
            "end_sec": round(end / SR, 3),
            "target_sec": round(target, 3),
            "dense_sec": round(pos["dense_sec"], 3),
            "natural_sec": round(natural, 3),
            "tempo": round(tempo, 5),
            "fill_ratio": round(active_frac, 4),
            "max_internal_gap_s": round(gap, 4),
        })
        del arr, i16, seg

    # ---- Gate measurement on the assembled (pre-loudnorm) master ----
    print("[4/6] Measuring fill gates ...", flush=True)
    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    max_internal_gap_s = round(max(gaps), 4) if gaps else 0.0

    all_runs = silent_runs(canvas.astype(np.float32) / 32768.0, min_s=0.05)
    last_cue_end = max(p["end_sec"] for p in placed)
    lead_n = int(LEAD_IN_SEC * SR)
    tail_n = int(last_cue_end * SR)
    internal_pockets = []
    for s, e, d in all_runs:
        if s >= lead_n and e <= tail_n and d > 2.0:
            internal_pockets.append({"start_sec": round(s / SR, 3),
                                     "end_sec": round(e / SR, 3),
                                     "duration_sec": d})

    # Peak-normalise in chunks.
    CHUNK = 1_000_000
    peak_i = 0
    for i in range(0, len(canvas), CHUNK):
        seg = canvas[i:i + CHUNK]
        peak_i = max(peak_i, int(seg.max()), int(-seg.min()))
    peak_i = peak_i or 1
    if peak_i > 32112:
        sp = 32112.0 / peak_i
        for i in range(0, len(canvas), CHUNK):
            seg = canvas[i:i + CHUNK].astype(np.float32)
            seg *= sp
            np.rint(seg, out=seg)
            canvas[i:i + CHUNK] = seg.astype(np.int16)

    # ---- Loudnorm master ----
    print("[5/6] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k '
        f'"{MASTER_M4A}" > NUL 2>&1')

    # ---- Mux with FULL original video (video copy, NO video-src swap) ----
    print("[6/6] Mux with FULL original video (-c:v copy) ...", flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    out_dur = duration(OUT_VIDEO)
    gates = {
        "median_fill_ge_0.72": bool(median_fill >= 0.72),
        "max_internal_gap_le_1.5s": bool(max_internal_gap_s <= 1.5),
        "internal_silence_runs_gt_2s_eq_0": bool(len(internal_pockets) == 0),
        "duration_within_2s_of_original": bool(abs(out_dur - vend) <= 2.0),
    }
    report = {
        "experiment": "fill_v2 — recompute-scale-from-rendered-speech + fill gate "
                      "(calculus_lesson_10 Taylor series)",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": source_desc,
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "voice": VOICE,
        "tempo_floor": TEMPO_FLOOR,
        "max_tempo": MAX_TEMPO,
        "scale_basis": "RENDERED dense speech (not authored durations)",
        "timeline_scale": round(scale, 6),
        "rendered_tempo": round(tempo_hint, 6),
        "extra_expansion_passes": extra_passes,
        "rendered_dense_speech_sec": round(total_speech, 3),
        "inter_cue_pause_total_sec": round(pause_total, 3),
        "speech_budget_sec": round(budget, 3),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "video_duration_sec": round(vend, 3),
        "output_duration_sec": round(out_dur, 3),
        "output_size_bytes": OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0,
        "last_cue_end_sec": round(last_cue_end, 3),
        "median_fill": median_fill,
        "min_fill": round(min(fills), 4) if fills else 0.0,
        "max_fill": round(max(fills), 4) if fills else 0.0,
        "max_internal_gap_s": max_internal_gap_s,
        "internal_silence_runs_gt_2s": len(internal_pockets),
        "internal_pockets": internal_pockets,
        "gates": gates,
        "all_gates_pass": all(gates.values()),
        "video_source": "web_platform/media_vault/calculus/lesson_10/original_source/full_original.mp4 "
                        "(unchanged, -c:v copy)",
        "cues": placed,
    }
    try:
        probe = json.loads(run(f'ffprobe -v error -show_entries stream=index,codec_type,codec_name '
                               f'-of json "{OUT_VIDEO}"'))
        report["output_streams"] = probe.get("streams", [])
    except Exception as e:
        report["output_streams_error"] = str(e)
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    odur = duration(OUT_VIDEO)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. scale={scale:.4f} tempo={tempo_hint:.4f} cues={len(placed)}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap_s={max_internal_gap_s} "
          f"internal_pockets={len(internal_pockets)}", flush=True)
    print(f"output_duration={out_dur:.3f}s original={vend:.3f}s", flush=True)
    print(f"GATES: {gates}", flush=True)
    print(f"ALL_GATES_PASS={report['all_gates_pass']}", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)
    if not report["all_gates_pass"]:
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
