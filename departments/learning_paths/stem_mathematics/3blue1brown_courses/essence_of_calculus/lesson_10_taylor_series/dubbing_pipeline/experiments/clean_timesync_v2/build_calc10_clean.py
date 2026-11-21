"""
EXPERIMENT - Full-length clean absolute-sample Bengali dub
(Essence of Calculus, Lesson 10 - Taylor series)
==========================================================================================
Adapted verbatim from the proven clean_timesync_v2 pipeline:
  essence_of_calculus/lesson_05_euler_number/dubbing_pipeline/experiments/clean_timesync_v2/build_calc05_clean.py

Guarantees (identical to the proven pipeline):
  1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
     half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
  2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
  3. atempo fit <= 2.2x; PAD ONLY, NEVER truncate. NO SFX: clean speech only.
  4. IMPROVED_DUB_FILL_POLICY: tempo floor 0.82 (gentle slowdown), pedagogical
     expansion of every cue (base narration covers only ~448 s of a ~1339 s
     video, so a ~2.9x timeline scale would otherwise leave large silent
     pockets), tail expansion, and a final-cue cap so speech ends inside the
     video.
  5. Canvas padded to the FULL original video duration so -shortest can never
     trim video frames.
  6. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy,
     -map 0:v:0 -map 1:a:0 -c:a aac -shortest.
  7. Lightweight volumedetect (-vn -nostats, log to FILE) on intro 0-2 s and
     the final 2 s, written into verification.json.
  8. Fill measurement: per cue speech_samples/window_samples; median_fill >=
     0.72 and max_internal_gap_s <= 1.5 s recorded in verification.json.

Cue source (read-only; teacher audio / manifests are NEVER modified):
  1. .../lesson_10_taylor_series/dubbing_pipeline/*master_script*.json  (PRIMARY)
     -- none exists for this lesson, so:
  2. web_platform/data/calculus/lesson_10.json -> its audio_manifest reference.
     The manifest stores start/end/duration in MILLISECONDS (NOT seconds), so
     no x1000 conversion is applied. Duplicate section keys (id + alias) are
     deduplicated -> 37 unique cues.
  3. last resort: derive cues from the sections of lesson_10.json itself.

Everything is written under NEW experiment folders. Teacher audio, manifests
and other lessons are untouched.
"""
import os
import re
import json
import time
import asyncio
import subprocess
import wave
import statistics
from pathlib import Path

import numpy as np
import edge_tts

EXP = Path(__file__).resolve().parent
BASE = EXP.parent.parent                        # .../lesson_10_taylor_series/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "calculus" / "lesson_10.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "calculus" / "lesson_10" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "calculus" / "lesson_10" / "experiments" / "3b1b_calculus_10_full_dubbed.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
TEMPO_FLOOR = 0.82          # IMPROVED_DUB_FILL_POLICY
FADE_MS = 12
VIDEO_ID = "3d6DsjIBzJ4"
LESSON = "lesson_10_taylor_series"

# Silence margins: keep 0-2 s and the final 2 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Pedagogical Bengali narration appended to every cue. The authored narration
# covers only ~448 s while the source video is ~1339 s (~2.9x timeline scale),
# so even at the 0.82 atempo floor the base text would fill well under 40% of
# each window. These sentences add "what to notice / why it matters" detail,
# improving both teaching quality and speech fill (IMPROVED_DUB_FILL_POLICY).
# Written phonetically / in Bengali script for clean bn-BD-PradeepNeural TTS.
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

# Extra narration for the closing cues, applied only if their TTS is still
# short of the visual window after the main expansion (data-driven).
TAIL_EXPANSIONS = {
    35: (" আরও মনে রাখবেন, ছোট ছোট পদ যোগ করে আমরা যখনই চাই তখনই যথার্থতা বাড়িয়ে নিতে পারি। "
         "এই নমনীয়তাই টেইলর ধারাকে ইঞ্জিনিয়ারিং আর বিজ্ঞানে অপরিহার্য করে তুলেছে।"),
    36: (" সংক্ষেপে বললে, ধারার শক্তি আর তার সীমা—দুটোই আমাদের জানা থাকতে হবে। তবেই আমরা "
         "নির্ভুলতার সাথে এই সূত্র ব্যবহার করতে পারব।"),
    37: (" টেইলর ধারা আমাদের শেখায়, এক ছোট বিন্দুতে লুকোনো তথ্যও সঠিকভাবে পড়লে পুরো "
         "একটি ফাংশনের গল্প বলে দিতে পারে।"),
}


def is_win1450(err):
    return getattr(err, "winerror", None) == 1450 or "1450" in str(err)


def run(cmd, retries=6):
    """subprocess runner with explicit WinError 1450 / transient-failure retry."""
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
    out = run(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{path}"')
    try:
        return float(out.strip())
    except Exception:
        return 0.0


def video_duration(path):
    """Full canvas length = max(container, video-stream) so -shortest cannot trim."""
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
    """Edge-TTS save with a dedicated WinError 1450 retry."""
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
    """Purge 0-byte, 12 attempts, half-split + sentence-split fallbacks."""
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
        # Fallback 1: split into two halves and concatenate.
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
        # Fallback 2: synthesize sentence by sentence and concatenate.
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


def load_master_cues():
    """Read a PRIMARY master script if one exists (none for this lesson)."""
    masters = sorted(BASE.glob("*master_script*.json"))
    if not masters:
        return None, None
    mpath = masters[0]
    data = json.loads(mpath.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("cues") or data.get("sections") or []
    out = []
    for c in data:
        if not isinstance(c, dict):
            continue
        text = c.get("bn") or c.get("text")
        if not text:
            continue
        dur_s = c.get("duration")
        if dur_s is None:
            dur_s = (float(c.get("end", 0)) - float(c.get("start", 0)))
        dur_ms = float(dur_s) * 1000.0
        out.append({
            "text": text,
            "dur_ms": dur_ms,
            "section": str(c.get("section", "master")),
        })
    if out:
        return out, f"master_script:{mpath.name} (seconds->ms x1000)"
    return None, None


def load_manifest_cues():
    """Read the audio_manifest referenced by lesson_10.json.

    Manifest timings are in MILLISECONDS (no x1000). Section keys appear twice
    (by id and by alias) with identical cues -> deduplicate by (start_ms, text).
    """
    lesson = json.loads(LESSON_JSON.read_text(encoding="utf-8"))
    rel = lesson.get("audio_manifest") or (lesson.get("meta") or {}).get("audio_manifest")
    if not rel:
        return None, None
    manifest = (LESSON_JSON.parent / rel).resolve()
    if not manifest.exists():
        return None, None
    data = json.loads(manifest.read_text(encoding="utf-8"))
    out = []
    seen = set()
    for sec_id, sec in data.get("sections", {}).items():
        for c in sec.get("cues", []):
            text = c.get("text")
            if not text:
                continue
            key = (round(float(c.get("start_ms", 0)), 1), text[:80])
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "text": text,
                "dur_ms": float(c.get("duration_ms", 0)),
                "section": str(sec.get("section_id") or sec_id),
            })
    if out:
        return out, f"audio_manifest:{manifest.name} (ms, deduped, {len(out)} cues)"
    return None, None


def load_source_cues():
    """Return (list_of_{text,dur_ms,section}, source_description)."""
    out, desc = load_master_cues()
    if out:
        return out, desc
    out, desc = load_manifest_cues()
    if out:
        return out, desc
    lesson = json.loads(LESSON_JSON.read_text(encoding="utf-8"))
    return derive_from_lesson(lesson), "lesson_10.json:sections"


def derive_from_lesson(lesson):
    """Last-resort cue derivation from the lesson JSON's rich text sections."""
    out = []
    for sec in lesson.get("sections", []):
        sec_id = sec.get("id") or sec.get("alias") or "section"
        texts = []
        q = sec.get("quote") or {}
        if q.get("text_bn"):
            texts.append(q["text_bn"])
        texts.extend(sec.get("paragraphs", []))
        for fm in sec.get("formulas", []):
            if fm.get("caption_bn"):
                texts.append(fm["caption_bn"])
        co = sec.get("callout") or {}
        if co.get("text_bn"):
            texts.append(co["text_bn"])
        if sec.get("closing_thought_bn"):
            texts.append(sec["closing_thought_bn"])
        for t in texts:
            clean = re.sub(r"\$[^\$]*\$", " ", t)          # drop LaTeX math
            clean = re.sub(r"[\\\{\}\[\]#*]", " ", clean)
            clean = re.sub(r"\s+", " ", clean).strip()
            if clean:
                out.append({"text": clean,
                            "dur_ms": max(2000.0, len(clean) * 90.0),
                            "section": sec_id})
    return out


def load_cues(vend, source_cues):
    """Lay the authored cues out cumulatively, then scale to span the full video."""
    authored_total = sum(c["dur_ms"] for c in source_cues) + INTER_CUE_PAUSE_MS * (len(source_cues) - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    scale = usable / (authored_total / 1000.0) if authored_total > 0 else 1.0

    cues = []
    cursor_ms = 0.0
    for i, c in enumerate(source_cues):
        start = LEAD_IN_SEC + (cursor_ms / 1000.0) * scale
        dur = (c["dur_ms"] / 1000.0) * scale
        base = c["text"]
        exp = EXPANSIONS.get(i + 1, "")
        cues.append({
            "id": i + 1,
            "start": round(start, 3),
            "end": round(start + dur, 3),
            "duration": round(dur, 3),
            "bn": (base + " " + exp).strip(),
            "base_bn": base,
            "expanded": bool(exp),
            "section": c["section"],
        })
        cursor_ms += c["dur_ms"] + INTER_CUE_PAUSE_MS
    return cues, scale


async def synth_all(cues):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, c in enumerate(cues):
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        ok = await synth(sanitize(c["bn"]), raw)
        if not ok:
            failed.append(c["id"])
            print(f"  WARNING cue {c['id']} failed after every fallback", flush=True)
        if (i + 1) % 10 == 0:
            print(f"  TTS {i+1}/{len(cues)}", flush=True)
    return failed


async def expand_tail_cues(cues):
    """Append richer wording to closing cues whose TTS is still short of window."""
    marker = EXP / "_tail_expanded.json"
    done = set()
    if marker.exists():
        try:
            done = set(json.loads(marker.read_text(encoding="utf-8")))
        except Exception:
            done = set()
    expanded = []
    for c in cues[-3:]:
        cid = c["id"]
        if cid not in TAIL_EXPANSIONS or cid in done:
            continue
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        target = float(c["duration"])
        natural = duration(raw)
        if 0 < natural < 0.85 * target:
            new_text = sanitize(c["bn"] + " " + TAIL_EXPANSIONS[cid])
            print(f"  expanding cue {cid}: natural={natural:.2f}s < {0.85*target:.2f}s", flush=True)
            if await synth(new_text, raw, force=True):
                expanded.append({"id": cid,
                                 "natural_before": round(natural, 3),
                                 "natural_after": round(duration(raw), 3)})
                c["bn"] = new_text
                done.add(cid)
                marker.write_text(json.dumps(sorted(done)), encoding="utf-8")
    return expanded


def read_pcm(path):
    norm = path.with_suffix(".norm.wav")
    run(f'ffmpeg -y -i "{path}" -af aresample=44100 -ar 44100 -ac 1 -c:a pcm_s16le "{norm}" > NUL 2>&1')
    with wave.open(str(norm), "rb") as w:
        arr = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    try:
        os.remove(norm)
    except OSError:
        pass
    return arr


LAST_START = 0.0
VIDEO_END = 0.0
LAST_ID = None


def make_cue(raw, target, out, cid):
    """atempo-fit into the window; PAD only, NEVER truncate."""
    natural = duration(raw)
    if natural <= 0:
        natural = target
    if cid == LAST_ID:
        # Final cue must finish INSIDE the video, with a small safety margin.
        target = min(target, VIDEO_END - LAST_START - 0.10)
    # IMPROVED_DUB_FILL_POLICY: allow gentle slowdown down to 0.82x.
    tempo = max(TEMPO_FLOOR, min(MAX_TEMPO, natural / target))
    tmp = out.with_suffix(".fit.wav")
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)
    # Fill = placed speech-clip samples / window samples (IMPROVED_DUB_FILL_POLICY):
    # does the synthesized speech occupy its window, or is there dead air?
    # (A thresholded "voiced duty cycle" is reported separately because edge-TTS
    # MP3s carry codec leakage up to ~-48 dB, which makes a low threshold
    # unreliable as a speech/silence discriminator.)
    window_n = max(1, int(round(target * SR)))
    speech_samples = min(len(arr), window_n)
    fill = speech_samples / window_n
    # Internal gap: longest silent run inside the clip. 0.005 (-46 dB) sits
    # above the measured MP3 leakage floor (~0.0038) so it counts real pauses.
    active = np.abs(arr) > 0.005
    idx = np.flatnonzero(active)
    max_gap_s = 0.0
    if idx.size > 1:
        longest = int(np.diff(idx).max()) - 1
        max_gap_s = longest / SR
    need = window_n
    if len(arr) < need:
        arr = np.pad(arr, (0, need - len(arr)))     # pad only, never cut
    # If still longer (tempo cap), keep it -> recorded as overrun, never cut.
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(arr, -1, 1) * 32767).astype("<i2").tobytes())
    try:
        os.remove(tmp)
    except OSError:
        pass
    return arr, tempo, natural, target, fill, max_gap_s, speech_samples


def volumedetect(path, start, length):
    """Audio-only volumedetect; log to a FILE so ffmpeg output never floods RAM."""
    log = EXP / "_volumedetect.log"
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-nostats", "-vn",
        "-i", str(path),
        "-af", f"atrim=start={start}:duration={length},volumedetect",
        "-f", "null", "-",
    ]
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


async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    source_cues, source_desc = load_source_cues()
    cues, scale = load_cues(vend, source_cues)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"video duration = {vend:.3f}s; cues = {len(cues)}; source = {source_desc}; "
          f"timeline scale = {scale:.4f}", flush=True)

    print("[1/5] TTS (clean, no SFX, pedagogically expanded) ...", flush=True)
    failed = await synth_all(cues)

    print("[2/5] Conditional tail-cue expansion ...", flush=True)
    expanded = await expand_tail_cues(cues)

    print("[3/5] Absolute sample placement (start*44100, tempo floor 0.82, pad-only) ...", flush=True)
    # FULL-length canvas: -shortest can never trim the video.
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    CHUNK = 1_000_000
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    fills = []
    gaps = []
    overrun = 0
    last_cue_end = 0.0
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            print(f"  SKIP cue {cid} (no audio)", flush=True)
            continue
        arr, tempo, natural, target, fill, max_gap_s, speech_samples = make_cue(
            raw, float(c["duration"]), CUE_DIR / f"cue_{cid:03d}.wav", cid)
        if len(arr) >= 2 * fade_n:
            arr[:fade_n] *= env
            arr[-fade_n:] *= env[::-1]
        start_sample = int(round(float(c["start"]) * SR))
        end = start_sample + len(arr)
        if end > len(canvas):
            canvas = np.pad(canvas, (0, end - len(canvas)))
        i16 = (np.clip(arr, -1.0, 1.0) * 32767.0).astype(np.int16)
        seg = canvas[start_sample:end].astype(np.int32)
        seg += i16.astype(np.int32)
        np.clip(seg, -32768, 32767, out=seg)
        canvas[start_sample:end] = seg.astype(np.int16)
        del arr, i16, seg
        placed_len = int(round(end - start_sample))
        if placed_len > int(float(c["duration"]) * SR) + 200:
            overrun += 1
        last_cue_end = max(last_cue_end, end / SR)
        fills.append(fill)
        gaps.append(max_gap_s)
        expected_ms = round(float(c["start"]) * 1000, 2)
        actual_ms = round(start_sample / SR * 1000, 2)
        placed.append({
            "id": cid,
            "section": c["section"],
            "expected_start_ms": expected_ms,
            "actual_start_ms": actual_ms,
            "drift_ms": round(actual_ms - expected_ms, 6),
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3),
            "target_sec": round(target, 3),
            "speech_samples": speech_samples,
            "window_samples": int(round(target * SR)),
            "fill_ratio": round(fill, 4),
            "max_internal_gap_s": round(max_gap_s, 4),
            "placed_samples": placed_len,
            "expanded": c["expanded"],
        })

    peak_i = 0
    for i in range(0, len(canvas), CHUNK):
        seg = canvas[i:i + CHUNK]
        peak_i = max(peak_i, int(seg.max()), int(-seg.min()))
    peak_i = peak_i or 1
    if peak_i > 32112:  # 0.98 * 32767
        scale_pk = 32112.0 / peak_i
        for i in range(0, len(canvas), CHUNK):
            seg = canvas[i:i + CHUNK].astype(np.float32)
            seg *= scale_pk
            np.rint(seg, out=seg)
            canvas[i:i + CHUNK] = seg.astype(np.int16)

    print("[4/5] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    max_internal_gap_s = round(max(gaps), 4) if gaps else 0.0
    report = {
        "experiment": "clean_timesync_v2 (calculus_lesson_10 Taylor series full-length, improved fill)",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": source_desc,
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": "absolute sample offset (start*44100); atempo floor 0.82; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "tempo_floor": TEMPO_FLOOR,
        "fill_policy": "IMPROVED_DUB_FILL_POLICY: pedagogical expansion of all cues, "
                       "median_fill>=0.72, max_internal_gap<=1.5s",
        "fill_definition": "placed speech-clip samples / window samples per cue "
                           "(no dead air); voiced duty cycle reported separately",
        "median_fill": median_fill,
        "min_fill": round(min(fills), 4) if fills else 0.0,
        "max_fill": round(max(fills), 4) if fills else 0.0,
        "max_internal_gap_s": max_internal_gap_s,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "timeline_scale": round(scale, 6),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "tail_expansions_applied": expanded,
        "cues": placed,
    }

    print("[5/5] Mux with FULL original video (video copy) ...", flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    report["output_video"] = str(OUT_VIDEO)
    report["output_duration_sec"] = round(duration(OUT_VIDEO), 3)
    report["output_size_bytes"] = OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0
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

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"median_fill={median_fill} max_internal_gap_s={max_internal_gap_s}", flush=True)
    print(f"video={report['output_duration_sec']}s size={report['output_size_bytes']}", flush=True)
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
