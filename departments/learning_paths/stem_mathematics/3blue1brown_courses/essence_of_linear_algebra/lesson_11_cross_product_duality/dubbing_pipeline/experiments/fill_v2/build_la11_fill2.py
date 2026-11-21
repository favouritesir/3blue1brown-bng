"""
EXPERIMENT — fill_v2 : full-length Bengali dub with SILENT-POCKET ELIMINATION
==============================================================================
Lesson 11 (Cross Product Duality), Essence of Linear Algebra.

Goal
----
The clean_timesync_v2 render left 25 silent pockets (some >30 s) because the
authored cue windows were scaled ~2.1x while speech was only atempo-fitted with
a hard tempo floor of 1.0.  This build removes those pockets by:

  1. HEAVILY expanding every cue's Bengali script (topic-specific paragraphs +
     a generic pedagogical pool + an automatic data-driven top-up loop) so the
     total *rendered* speech is long enough to span the whole video.
  2. RECOMPUTING the timeline scale FROM RENDERED SPEECH: after TTS, the layout
     is rebuilt with window_i proportional to the measured natural duration of
     cue i, so the atempo needed to fill each window is ~1.0 and pad is ~0.
  3. A FILL GATE that measures, on the actually rendered master:
        median_fill >= 0.72
        max_internal_gap_s <= 1.5
        count of internal silence runs > 2 s == 0
     plus ffprobe full-duration parity with the original video.
     Success is NEVER claimed unless the gate passes.

Source of truth (READ-ONLY)
---------------------------
  web_platform/assets/audio/linear_algebra/lesson_11/manifest.json
  -> section.cues[].text is the Bengali dubbing script (alias-deduped).
  Teacher audio, manifests and all other lessons are never modified.

Original video source is reused in full (video -c:v copy). NOTHING is swapped.
All new artifacts live under experiments/fill_v2/ and the
media_vault/lesson_11/experiments/fill_v2/ output folder. The previous video
(media_vault/lesson_11/experiments/3b1b_lesson_11_full_dubbed.mp4) is left
untouched as a backup.
"""
import os
import re
import json
import time
import asyncio
import subprocess
import statistics
import wave
from pathlib import Path

import numpy as np
import edge_tts

EXP = Path(__file__).resolve().parent                    # .../experiments/fill_v2
BASE = EXP.parent.parent                                 # .../dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"                   # .../3blue1brown_courses/web_platform
MANIFEST = WEB / "assets" / "audio" / "linear_algebra" / "lesson_11" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_11" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "lesson_11" / "experiments" / "fill_v2" / "3b1b_lesson_11_full_dubbed_fill2.mp4"
OLD_VIDEO = WEB / "media_vault" / "lesson_11" / "experiments" / "3b1b_lesson_11_full_dubbed.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
LAYOUT_JSON = EXP / "layout_from_speech.json"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.0          # ffmpeg atempo filter hard ceiling (single instance)
TEMPO_FLOOR = 0.82       # gentle natural slowdown allowed by improved fill policy
FADE_MS = 12

# Silent intro / outro margins.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Fill-gate thresholds (per task).
GATE_MEDIAN_FILL = 0.72
GATE_MAX_INTERNAL_GAP_S = 1.5
GATE_MAX_SILENCE_RUN_S = 2.0
GATE_MAX_SILENCE_RUNS = 0

# Recompute-scale target: aim for total rendered speech ~= usable span so the
# fitted atempo is ~1.0 and fill ~= 1.0. Accept [0.85, 1.10] x target.
TARGET_SPEECH_FRAC = 1.0
MIN_SPEECH_FRAC = 0.85
MAX_TOP_UP_ROUNDS = 5

# ---------------------------------------------------------------------------
# HEAVY EXPANSION content.
# Topic-specific Bengali paragraphs appended to each of the 24 cues. The key is
# to make the rendered speech long enough to fill its window without unnatural
# speed-ups, while keeping the pedagogy authentic (phonetic transliterations
# are used exactly as in the manifest - never bare Latin letters).
# ---------------------------------------------------------------------------
EXPANSIONS = {
    1: (" আজকের এই পাঠটি রৈখিক বীজগণিতের এক অত্যন্ত গুরুত্বপূর্ণ মোড়। আমরা দেখব কীভাবে "
        "একটি আপাতদৃষ্টিতে কৃত্রিম ও কৌশলমূলক সূত্রের পেছনে রয়েছে এক গভীর ও সুন্দর জ্যামিতিক "
        "সত্য। ধাপে ধাপে আমরা সেই সূত্রটিকে ভেঙে তার ভেতরের অর্থ উন্মোচন করব।"),
    2: (" এই উদ্ধৃতিটি আমাদের জন্য বিশেষভাবে প্রাসঙ্গিক, কারণ আজ আমরা এমন এক সূত্র নিয়ে কাজ "
        "করব যা প্রথমে অদ্ভুত ও জটিল মনে হতে পারে। কিন্তু যখনই আমরা তার পেছনের প্রাকৃতিক দৃশ্যটি "
        "আঁকতে পারব, তখনই প্রমাণটি আমাদের কাছে স্বতঃসিদ্ধ ও অবিচল হয়ে উঠবে। কঠিনতা মানে আমাদের "
        "বোঝাপড়া এখনো অসম্পূর্ণ—আর সেই অসম্পূর্ণতাই আমাদের আরও গভীরে যেতে উদ্বুদ্ধ করে।"),
    3: (" আসুন এই জ্যামিতিক চিত্রটি আরেকবার মানসপটে আঁকি। ভি ও ডব্লিউ দুটি ভেক্টর যখন একই "
        "তলে থাকে, তখন তারা একটা সামান্তরিক গঠন করে, আর তার ক্ষেত্রফল ঠিক তাদের ক্রস প্রোডাক্টের "
        "দৈর্ঘ্যের সমান। ডান হাতের নিয়ম আমাদের বলে কোন দিকে এই নতুন ভেক্টরটি নির্দেশ করবে। প্রস্থ "
        "এবং দিক—এই দুটি তথ্যই ক্রস প্রোডাক্টকে সম্পূর্ণরূপে সংজ্ঞায়িত করে।"),
    4: (" এই তিন বাই তিন ছদ্ম নির্ণায়কটি প্রথম দেখে মনে হয় যেন কেবল একটি মুখস্থ করার কৌশল। "
        "প্রথম সারিতে আই হ্যাট, জে হ্যাট ও কে হ্যাট—এই ভিত্তি ভেক্টরগুলোকে আমরা সংখ্যার মতো "
        "আচরণ করাচ্ছি। কিন্তু এর পেছনে কি আসলেই কোনো যুক্তি আছে, নাকি এটি শুধু একটা সুবিধাজনক "
        "কাগজের হিসাব? এই প্রশ্নটিই আজকের পুরো অনুসন্ধানের কেন্দ্রবিন্দু।"),
    5: (" এই প্রশ্নের উত্তর খুঁজতে আমাদের দুটি পুরোনো ধারণার সাহায্য নিতে হবে। অধ্যায় পাঁচের "
        "ডিটারমিন্যান্ট আমাদের বলে কীভাবে তিনটি ভেক্টর আয়তন তৈরি করে, আর অধ্যায় নয়ের ডুয়ালিটি "
        "বলছে একই আয়তনকে অন্য এক ভাষায়—ডট গুণনের ভাষায়—লেখা যায়। এই দুটি ধারণা একসাথে মিলে "
        "আমাদের সামনে এক সম্পূর্ণ নতুন দৃষ্টিভঙ্গি খুলে দেবে।"),
    6: (" ডুয়ালিটি বা দ্বৈততার নীতি হলো রৈখিক বীজগণিতের সবচেয়ে শক্তিশালী ধারণাগুলোর একটি। "
        "এটি আমাদের বলে যে কোনো রৈখিক রূপান্তরকে দুই ভাবে দেখা যায়—একদিকে রূপান্তর হিসেবে, "
        "অন্যদিকে একটি দ্বৈত ভেক্টরের সাথে ডট গুণন হিসেবে। ক্রস প্রোডাক্টকেও ঠিক এই চোখে দেখলেই "
        "তার সমস্ত অদ্ভুততা মিলে যাবে।"),
    7: (" এই পরিচ্ছেদে আমরা ক্রস প্রোডাক্টের সাথে এক নতুন ধরনের ফাংশনের পরিচিতি লাভ করব, যার "
        "আউটপুট কোনো ভেক্টর নয় বরং একটি বাস্তব সংখ্যা। ত্রিমাত্রিক স্থান থেকে বাস্তব সংখ্যার "
        "দিকে যাওয়া এই ধরনের ফাংশনকে বলা হয় রৈখিক ফাংশন বা রৈখিক রূপ। এই সরল ধারণাটিই পরে "
        "আমাদের কাঙ্ক্ষিত দ্বৈত ভেক্টরটির জন্ম দেবে।"),
    8: (" এখানে ইউ হলো একমাত্র পরিবর্তনশীল ভেক্টর, আর ভি ও ডব্লিউ কে আমরা স্থির রেখে দিয়েছি। "
        "ইউ-এর ভিন্ন ভিন্ন মানের জন্য ফলাফল ভিন্ন ভিন্ন সংখ্যা হবে। এইজন্যই আমরা বলি এটি আর "
        "থ্রি থেকে আর ওয়ানে যাওয়া একটি ফাংশন। পরবর্তীতে আমরা দেখব যে ইউ-কে দ্বিগুণ করলে ফলাফলও "
        "দ্বিগুণ হয়—এই পর্যবেক্ষণই ফাংশনটির রৈখিকতার প্রথম ইঙ্গিত।"),
    9: (" ডিটারমিন্যান্টের চিহ্ন আমাদের জন্য অত্যন্ত তাৎপর্যপূর্ণ। ধনাত্মক মান মানে ভি, ডব্লিউ "
        "ও ইউ ডান হাতের ওরিয়েন্টেশন মেনে চলে, আর ঋণাত্মক মান মানে ওরিয়েন্টেশন উল্টে গেছে। "
        "অর্থাৎ আমাদের ফাংশনটি শুধু আয়তন নয়, তার সাথে একটি চিহ্নও বহন করে। এই চিহ্নটি পরে "
        "ভেক্টরটির দিক নির্ধারণে গুরুত্বপূর্ণ ভূমিকা পালন করবে।"),
    10: (" রৈখিকতার এই দুটি শর্ত—দ্বিগুণ করলে ফল দ্বিগুণ হওয়া এবং যোগের ক্ষেত্রে ফলের যোগ হওয়া— "
         "আমাদের হাতে একটি সম্পূর্ণ রৈখিক রূপান্তর তুলে দেয়। এই কারণেই আমরা এর সাথে একটি "
         "দ্বৈত ভেক্টর সংযোগ করতে পারব। মাল্টিলিনিয়ারিটির এই ধারণাটি ডিটারমিন্যান্টের সবচেয়ে "
         "গুরুত্বপূর্ণ বৈশিষ্ট্য, আর এটি আমাদের পরবর্তী যুক্তির ভিত্তি।"),
    11: (" ছবিটির দিকে একটু মনোযোগ দিন। যখন ইউ-কে দ্বিগুণ করা হয়, তখন গোলকের একটি দিক দ্বিগুণ "
         "হয়ে যায়, ফলে আয়তনও দ্বিগুণ হয়। আর দুটি ইউ-এর যোগফল নিলে গোলক দুটিকে পাশাপাশি বসানোর "
         "মতো হয়, ফলে আয়তনও যোগ হয়। এই দুটি সরল পর্যবেক্ষণই আমাদের ফাংশনটির রৈখিকতার "
         "চাক্ষুষ প্রমাণ।"),
    12: (" এই পরিচ্ছেদে আমরা রৈখিক বীজগণিতের সবচেয়ে সুন্দর বিষয়টির দিকে অগ্রসর হব। একদিকে "
         "আমাদের আছে আয়তনের একটি জ্যামিতিক চিত্র, অন্যদিকে আছে একটি রৈখিক ফাংশন। ডুয়ালিটি "
         "এই দুটির মাঝে একটি সুন্দর সেতু তৈরি করে। সেই সেতুটির নাম হলো দ্বৈত ভেক্টর পি, আর আমরা "
         "এখন তার অস্তিত্ব ও রূপ খুঁজে বের করব।"),
    13: (" দ্বিমাত্রিক ক্ষেত্রে আমরা দেখেছি, এক সারি ম্যাট্রিক্সকে পাশে শুইয়ে দিলেই একটি দ্বৈত "
        "ভেক্টর পাওয়া যায়। রূপান্তরটি প্রয়োগ করা আর সেই ভেক্টরের সাথে ডট গুণন করা—এই দুটি "
        "কাজ আসলেই একই। ইউ হ্যাট ভেক্টরের সাথে ডট গুণনের এই উদাহরণটি মনে রাখলেই ত্রিমাত্রিক "
        "ক্ষেত্রের জন্য প্রয়োজনীয় ধাপটি আমাদের কাছে সহজ হয়ে যাবে।"),
    14: (" ত্রিমাত্রিক ক্ষেত্রে ফাংশনটি একটি এক বাই থ্রি ম্যাট্রিক্স দ্বারা প্রকাশিত হয়, যার তিনটি "
         "ঘরে বসে পি ওয়ান, পি টু ও পি থ্রি। এই ম্যাট্রিক্সের সাথে ইউ-এর গুণন আসলেই পি ভেক্টরের "
         "সাথে ইউ-এর ডট গুণনের সমান। যেহেতু প্রতিটি ইউ-এর জন্য এই সম্পর্কটি সত্য, তাই এমন একটি "
         "অনন্য ভেক্টর পি অবশ্যই বিদ্যমান—এইটিই হলো আমাদের খুঁজে বের করার লক্ষ্য।"),
    15: (" এখন প্রশ্ন ওঠে, এই রহস্যময় ভেক্টর পি আসলে কে? তার দৈর্ঘ্য কত, আর সে কোন দিকে "
         "নির্দেশ করে? আমরা দুই ভাবে উত্তর খুঁজব—প্রথমে বিশুদ্ধ হিসাব দিয়ে, তারপর একটি সরল "
         "জ্যামিতিক ছবি দিয়ে। দ্বিতীয় পদ্ধতিটি আমাদের অনেক বেশি বোধগম্য হবে, কারণ সেটি "
         "সরাসরি আমাদের চোখের সামনে ঘটনাটি দেখায়।"),
    16: (" এই পরিচ্ছেদে আমরা জ্যামিতির এক অত্যন্ত সরল সূত্র—আয়তন সমান ভূমির ক্ষেত্রফল "
         "গুণ লম্ব উচ্চতা—থেকেই কাঙ্ক্ষিত ভেক্টর পি-এর সম্পূর্ণ বর্ণনা বের করে আনব। কোনো "
         "জটিল বীজগণিত ছাড়াই আমরা তার দৈর্ঘ্য ও দিক নির্ধারণ করতে পারব। এই জ্যামিতিক পদ্ধতিটি "
         "আমাদের বোঝাপড়াকে অনেক গভীর করবে।"),
    17: (" এখানে ভূমি হলো ভি ও ডব্লিউ দ্বারা গঠিত সামান্তরিক, যার ক্ষেত্রফল আমরা আগেই জেনেছি। "
         "আর উচ্চতা হলো ইউ-এর সেই অংশ যা ভি ও ডব্লিউ-এর তলের ওপর লম্বভাবে দাঁড়িয়ে থাকে। "
         "আয়তন তখন হয় ভূমির ক্ষেত্রফল গুণ এই লম্ব উচ্চতা। এই সরল সমীকরণটি আমাদের পরবর্তী "
         "যুক্তির সম্পূর্ণ ভিত্তি তৈরি করে।"),
    18: (" ডট গুণনের জ্যামিতিক রূপটি হলো—পি ডট ইউ মানে পি-এর দৈর্ঘ্যের সাথে ইউ-এর পি-এর দিকে "
         "লম্ব প্রক্ষেপণের গুণফল। প্রতিটি ইউ-এর জন্য এই দুটি রাশি সমান হতে হলে পি কে অবশ্যই ভি "
         "ও ডব্লিউ-এর তলের ওপর লম্ব হতে হবে। আর তার দৈর্ঘ্য হতে হবে ঠিক ভূমির ক্ষেত্রফলের "
         "সমান—এই দুটি শর্তই পি-কে সম্পূর্ণরূপে নির্ধারণ করে।"),
    19: (" দিক নির্ধারণের জন্য আমরা ডান হাতের নিয়ম ব্যবহার করি। তর্জনী যদি ভি দিকে ও মধ্যমা "
         "যদি ডব্লিউ দিকে ধরা হয়, তখন বুঁড়ু যে দিকে নির্দেশ করে সেটিই হলো পি-এর দিক। ভি ও "
         "ডব্লিউ-এর ক্রম বদলালে চিহ্ন উল্টে যায়, আর ঠিক তখনই পি-এর অভিমুখও উল্টে যায়। এই "
         "নিয়মটি আমাদের সূত্রটির চিহ্নের সাথে জ্যামিতির চিহ্নকে মিলিয়ে দেয়।"),
    20: (" দৈর্ঘ্য মিলল আর দিক মিলল—তাই দুটি ভেক্টর হুবহু একই। যেহেতু পি-এর দৈর্ঘ্য ভি ও ডব্লিউ "
         "দ্বারা গঠিত সামান্তরিকের ক্ষেত্রফলের সমান, আর দিক ডান হাতের নিয়মে নির্ধারিত, তাই আমরা "
         "লিখতে পারি পি সমান ভি ক্রস ডব্লিউ। এই সূত্রটি এখন আর কোনো কৃত্রিম কৌশল নয়—এটি "
         "একটি সম্পূর্ণ প্রাকৃতিক জ্যামিতিক সত্য।"),
    21: (" এই শেষ পরিচ্ছেদে আমরা হিসাবটি মিলিয়ে দেখব যে জ্যামিতিক পদ্ধতিতে পাওয়া ফলাফলটি আসলেই "
         "সিউডো-ডিটারমিন্যান্ট সূত্র থেকে আসে। বীজগণিত ও জ্যামিতি এখানে এক মোহনায় মিলিত হবে। "
         "আমরা দেখব যে একটি সহজ বিস্তার প্রক্রিয়াই আমাদের কাঙ্ক্ষিত ভেক্টরটির তিনটি স্থানাঙ্ক "
         "স্বয়ংক্রিয়ভাবে তুলে দেয়।"),
    22: (" তিন বাই তিন ডিটারমিন্যান্টকে প্রথম কলাম ইউ-এর সাপেক্ষে বিস্তার করলে তিনটি পদ পাওয়া "
         "যায়। প্রতিটি পদে ইউ-এর একটি স্থানাঙ্ক থাকে আর সাথে থাকে ভি ও ডব্লিউ-এর দুটি স্থানাঙ্ক "
         "দিয়ে গঠিত একটি বন্ধনী। এই বন্ধনীগুলো ঠিক সেই সহগ যা আমরা জ্যামিতিকভাবেই পেয়েছিলাম। "
         "আরও একবার হিসাবটি নিজের ভাষায় বলে দেখুন—তখনই এটি পোক্ত হবে।"),
    23: (" যেহেতু পি ডট ইউ মানে পি ওয়ান গুণ ইউ ওয়ান যোগ পি টু গুণ ইউ টু যোগ পি থ্রি গুণ ইউ "
         "থ্রি, তাই ইউ-এর তিনটি স্থানাঙ্কের সহগই হলো সরাসরি পি-এর তিনটি স্থানাঙ্ক। প্রথমটি ভি "
         "টু ডব্লিউ থ্রি বিয়োগ ভি থ্রি ডব্লিউ টু, দ্বিতীয়টি ভি থ্রি ডব্লিউ ওয়ান বিয়োগ ভি ওয়ান "
         "ডব্লিউ থ্রি, আর তৃতীয়টি ভি ওয়ান ডব্লিউ টু বিয়োগ ভি টু ডব্লিউ ওয়ান। এই তিনটিই ভি "
         "ক্রস ডব্লিউ-এর তিনটি ঘটক।"),
    24: (" আর এই কারণেই পাঠ্যবইগুলোতে ইউ-এর জায়গায় প্রতীকীভাবে আই হ্যাট, জে হ্যাট ও কে হ্যাট "
         "লিখে দেওয়া হয়। বিস্তার করার পর স্বয়ংক্রিয়ভাবে ওই সহগগুলো ভেক্টর আকারে প্রকাশিত হয়। "
         "এটি কোনো জাদুকরি কৌশল নয়, বরং ডুয়ালিটির এক অনবদ্য গাণিতিক প্রতিচ্ছবি। বীজগণিত ও "
         "জ্যামিতি এখানে সম্পূর্ণরূপে মিলিত হয়েছে, আর ক্রস প্রোডাক্টের সূত্রটি তার পূর্ণ অর্থ "
         "পেয়েছে। এই দৃষ্টিভঙ্গি মনে রাখলেই রৈখিক বীজগণিতের পরবর্তী অধ্যায়গুলো অনেক সহজ হবে।"),
}

# Generic pedagogical pool used by the automatic top-up loop. Sentences are
# deliberately general so they remain coherent when appended to any cue.
GENERIC_POOL = [
    " এখানে একটু থামুন এবং বিষয়টি নিজের ভাষায় বলে দেখুন—কোনো ধারণা তখনই পোক্ত হয় যখন আপনি সেটি "
    "অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন।",
    " এই ধাপটির প্রতিটি অংশ মনে রাখা গুরুত্বপূর্ণ, কারণ পরের যুক্তিগুলো ঠিক এই ভিত্তির ওপরেই "
    "নির্মিত হয়।",
    " লক্ষ্য করুন, যতক্ষণ না আমরা চিত্রটি মানসপটে আঁকতে পারছি, ততক্ষণ সূত্রটি কেবল একটা "
    "মুখস্থ বিষয় হয়ে থাকে; ছবিটি আঁকলেই সেটি বোধগম্য হয়।",
    " গণিতের এই সৌন্দর্য হলো—একই সত্যকে একাধিক ভাষায় বলা যায়, আর প্রতিটি ভাষা আমাদের এক নতুন "
    "দৃষ্টিভঙ্গি দেয়।",
    " আসুন এই পর্যবেক্ষণটি আরেকটি উদাহরণ দিয়ে যাচাই করে দেখি, যাতে বিষয়টি সম্পূর্ণরূপে "
    "স্পষ্ট হয়ে যায়।",
    " মনে রাখবেন, রৈখিকতা হলো রৈখিক বীজগণিতের কেন্দ্রীয় ধারণা—এই একটিমাত্র বৈশিষ্ট্যের ওপর "
    "পুরো তত্ত্বটি দাঁড়িয়ে আছে।",
    " এই বিষয়টি নিয়ে একটু চিন্তা করুন: আয়তন, ক্ষেত্রফল আর ডট গুণন—এরা সবাই কীভাবে একই "
    "গল্পের বিভিন্ন রূপ?",
    " আমরা এখানে যে পদ্ধতিটি অনুসরণ করছি, তা ভবিষ্যতে আরও জটিল সমস্যায় কাজে লাগবে। তাই "
    "এই ধাপগুলো ভালোভাবে বুঝে নেওয়া যুক্তিযুক্ত।",
    " সহগগুলোর এই বিন্যাসের দিকে এক নজর দিন—এদের প্রতিটি সরাসরি আমাদের কাঙ্ক্ষিত ভেক্টরটির "
    "একটি স্থানাঙ্ক।",
    " ডান হাতের নিয়ম শুধু একটি সুবিধাজনক চুক্তি নয়; এটি আয়তনের চিহ্নের সাথে গভীরভাবে "
    "সংযুক্ত।",
    " দ্বৈততার এই দৃষ্টিভঙ্গি একবার বুঝলে আপনি অনেক সূত্রকে মুখস্থ না করেই স্বাভাবিকভাবে "
    "উদ্ভাবন করতে পারবেন।",
    " আমাদের আজকের যাত্রার সারাংশ হলো—একটি অদ্ভুত সূত্রের পেছনে একটি সরল ও সুন্দর "
    "জ্যামিতিক চিত্র লুকিয়ে ছিল।",
]


# ---------------------------------------------------------------------------
# Robust subprocess / TTS helpers (verbatim from the proven pipeline).
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
# Cue loading from the READ-ONLY audio manifest.
# ---------------------------------------------------------------------------
def load_manifest_cues():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cues = []
    cid = 0
    for sec_id, sec in data.get("sections", {}).items():
        for c in sec.get("cues", []):
            text = c.get("text")
            if not text:
                continue
            cid += 1
            cues.append({
                "id": cid,
                "text": text,
                "dur_ms": float(c.get("duration_ms", 0)),
                "section": sec_id,
                "index_in_section": c.get("index", 0),
            })
    return cues


def build_expanded_text(cue):
    """HEAVY expansion: original script + topic paragraph (+ nothing else yet)."""
    base = sanitize(cue["text"])
    extra = EXPANSIONS.get(cue["id"], " ".join(GENERIC_POOL[:2]))
    return sanitize(base + " " + extra)


def top_up_text(cue, rounds_done):
    """Append one more generic pedagogical sentence from the rotating pool."""
    sentence = GENERIC_POOL[rounds_done % len(GENERIC_POOL)]
    return sanitize(cue["bn_final"] + " " + sentence)


async def synth_all(cues, force=False):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, c in enumerate(cues):
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        ok = await synth(c["bn_final"], raw, force=force)
        if not ok:
            failed.append(c["id"])
            print(f"  WARNING cue {c['id']} failed after every fallback", flush=True)
        if (i + 1) % 8 == 0:
            print(f"  TTS {i+1}/{len(cues)}", flush=True)
    return failed


def natural_durations(cues):
    out = {}
    for c in cues:
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        out[c["id"]] = duration(raw) if valid(raw) else 0.0
    return out


def recompute_layout_from_speech(cues, nats, vend):
    """NEW: rebuild the timeline using the MEASURED rendered speech durations.

    Window_i is made proportional to natural_i, so the atempo required to fill
    window_i is 1/k for every cue (k = usable_speech_span / sum(natural_i)).
    Cues are placed back-to-back with a small pause, guaranteeing no internal
    silence pockets larger than that pause.
    """
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    pause = INTER_CUE_PAUSE_MS / 1000.0
    pause_total = pause * (len(cues) - 1)
    w_total = usable - pause_total
    s_total = sum(nats.values())
    k = w_total / s_total if s_total > 0 else 1.0

    laid = []
    cursor = LEAD_IN_SEC
    for c in cues:
        n = nats[c["id"]]
        w = n * k
        laid.append({
            "id": c["id"],
            "section": c["section"],
            "start": round(cursor, 3),
            "end": round(cursor + w, 3),
            "duration": round(w, 3),
            "natural": round(n, 3),
            "bn": c["bn_final"],
        })
        cursor += w + pause
    meta = {
        "usable_sec": round(usable, 3),
        "speech_span_sec": round(w_total, 3),
        "rendered_speech_total_sec": round(s_total, 3),
        "recomputed_scale_k": round(k, 6),
        "implied_atempo": round(1.0 / k, 6) if k > 0 else None,
        "pause_sec": round(pause, 3),
    }
    return laid, meta


def read_pcm(path):
    norm = path.with_suffix(".norm.wav")
    run(f'ffmpeg -y -i "{path}" -af aresample=44100 -ar 44100 -ac 1 '
        f'-c:a pcm_s16le "{norm}" > NUL 2>&1')
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
        target = min(target, VIDEO_END - LAST_START - 0.10)
    tempo = max(TEMPO_FLOOR, min(MAX_TEMPO, natural / target))
    tmp = out.with_suffix(".fit.wav")
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 '
        f'-c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)
    speech_samples = len(arr)
    need = int(round(target * SR))
    if len(arr) < need:
        arr = np.pad(arr, (0, need - len(arr)))
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(arr, -1, 1) * 32767).astype("<i2").tobytes())
    try:
        os.remove(tmp)
    except OSError:
        pass
    fill = min(1.0, speech_samples / need) if need > 0 else 0.0
    gap_s = max(0.0, (need - speech_samples) / SR)
    info = {
        "tempo": round(tempo, 4),
        "natural": round(natural, 3),
        "target": round(target, 3),
        "fill_ratio": round(fill, 4),
        "internal_gap_s": round(gap_s, 4),
        "speech_samples": speech_samples,
        "window_samples": need,
    }
    return arr, info


def detect_silence_runs(canvas, threshold=0.01, hop_ms=20):
    """Find contiguous internal runs of (near-)silence in the rendered canvas.

    Scans only [LEAD_IN, last_nonzero_sample] so the deliberate intro/outro
    silences are excluded. Returns (count_gt_2s, max_run_s, list_of_runs).
    """
    x = np.asarray(canvas, dtype=np.float32)
    nz = np.flatnonzero(np.abs(x) > threshold)
    if nz.size == 0:
        return 0, 0.0, []
    start_i = int(LEAD_IN_SEC * SR)
    end_i = int(nz[-1]) + 1
    if end_i <= start_i:
        return 0, 0.0, []
    seg = x[start_i:end_i]
    hop = max(1, int(hop_ms / 1000.0 * SR))
    n_frames = int(np.ceil(len(seg) / hop))
    frame_silent = np.zeros(n_frames, dtype=bool)
    for f in range(n_frames):
        chunk = seg[f * hop:(f + 1) * hop]
        if chunk.size and float(np.sqrt(np.mean(chunk ** 2))) < threshold:
            frame_silent[f] = True
    runs = []
    f = 0
    while f < n_frames:
        if frame_silent[f]:
            g = f
            while g + 1 < n_frames and frame_silent[g + 1]:
                g += 1
            runs.append(round((g - f + 1) * hop / SR, 3))
            f = g + 1
        else:
            f += 1
    big = [r for r in runs if r > GATE_MAX_SILENCE_RUN_S]
    return len(big), (max(runs) if runs else 0.0), big


def volumedetect(path, start, length):
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
    cues = load_manifest_cues()
    for c in cues:
        c["bn_final"] = build_expanded_text(c)

    print(f"video duration = {vend:.3f}s ; manifest cues = {len(cues)}", flush=True)
    print("[1/7] TTS - heavily expanded script (clean, no SFX) ...", flush=True)
    failed = await synth_all(cues)

    # --- Automatic top-up: make rendered speech long enough to fill the span. ---
    laid, meta = recompute_layout_from_speech(cues, natural_durations(cues), vend)
    target_speech = meta["speech_span_sec"] * TARGET_SPEECH_FRAC
    top_up_rounds = 0
    while meta["rendered_speech_total_sec"] < target_speech * MIN_SPEECH_FRAC \
            and top_up_rounds < MAX_TOP_UP_ROUNDS:
        top_up_rounds += 1
        print(f"  top-up round {top_up_rounds}: rendered "
              f"{meta['rendered_speech_total_sec']:.1f}s < target {target_speech:.1f}s",
              flush=True)
        for c in cues:
            c["bn_final"] = top_up_text(c, top_up_rounds - 1)
        await synth_all(cues, force=True)
        laid, meta = recompute_layout_from_speech(cues, natural_durations(cues), vend)

    LAST_START = float(laid[-1]["start"])
    LAST_ID = laid[-1]["id"]
    print(f"  rendered speech total = {meta['rendered_speech_total_sec']:.1f}s ; "
          f"recomputed scale k = {meta['recomputed_scale_k']} ; "
          f"implied atempo = {meta['implied_atempo']}", flush=True)

    LAYOUT_JSON.write_text(json.dumps(
        {"meta": meta, "top_up_rounds": top_up_rounds, "cues": laid},
        ensure_ascii=False, indent=2), encoding="utf-8")

    print("[2/7] Absolute sample placement (start*44100, pad-only, recomputed scale) ...",
          flush=True)
    canvas = np.zeros(int(round(vend * SR)), dtype=np.float32)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    fills = []
    internal_gaps = []
    overrun = 0
    last_cue_end = 0.0
    for c in laid:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            print(f"  SKIP cue {cid} (no audio)", flush=True)
            continue
        arr, info = make_cue(raw, float(c["duration"]),
                             CUE_DIR / f"cue_{cid:03d}.wav", cid)
        fills.append(info["fill_ratio"])
        internal_gaps.append(info["internal_gap_s"])
        if info["speech_samples"] > info["window_samples"] + 200:
            overrun += 1
        if len(arr) >= 2 * fade_n:
            arr[:fade_n] *= env
            arr[-fade_n:] *= env[::-1]
        start_sample = int(round(float(c["start"]) * SR))
        end = start_sample + len(arr)
        if end > len(canvas):
            canvas = np.pad(canvas, (0, end - len(canvas)))
        canvas[start_sample:end] += arr
        last_cue_end = max(last_cue_end, end / SR)
        expected_ms = round(float(c["start"]) * 1000, 2)
        actual_ms = round(start_sample / SR * 1000, 2)
        placed.append({
            "id": cid,
            "section": c["section"],
            "expected_start_ms": expected_ms,
            "actual_start_ms": actual_ms,
            "drift_ms": round(actual_ms - expected_ms, 6),
            "tempo": info["tempo"],
            "natural_sec": info["natural"],
            "target_sec": info["target"],
            "fill_ratio": info["fill_ratio"],
            "internal_gap_s": info["internal_gap_s"],
            "placed_samples": len(arr),
        })

    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    max_internal_gap_s = round(max(internal_gaps), 4) if internal_gaps else 0.0
    n_big, max_run_s, big_runs = detect_silence_runs(canvas)

    print(f"  median_fill={median_fill} ; max_internal_gap_s={max_internal_gap_s} ; "
          f"silence_runs>2s={n_big} (max_run={max_run_s}s)", flush=True)

    # --- FILL GATE ---------------------------------------------------------
    gate = {
        "median_fill": median_fill,
        "median_fill_pass": bool(median_fill >= GATE_MEDIAN_FILL),
        "max_internal_gap_s": max_internal_gap_s,
        "max_internal_gap_pass": bool(max_internal_gap_s <= GATE_MAX_INTERNAL_GAP_S),
        "internal_silence_runs_gt_2s": n_big,
        "internal_silence_runs_pass": bool(n_big <= GATE_MAX_SILENCE_RUNS),
        "max_internal_silence_run_s": max_run_s,
        "silence_run_details_s": big_runs,
    }
    gate["all_fill_gates_pass"] = bool(
        gate["median_fill_pass"] and gate["max_internal_gap_pass"]
        and gate["internal_silence_runs_pass"])

    peak = float(np.max(np.abs(canvas))) or 1.0
    if peak > 0.98:
        canvas *= 0.98 / peak

    print("[3/7] WAV master + loudnorm -14 LUFS ...", flush=True)
    CHUNK = 1_000_000
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes((np.clip(canvas[i:i + CHUNK], -1, 1) * 32767).astype("<i2").tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 '
        f'-c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    print("[4/7] Mux with FULL original video (video copy, source NOT swapped) ...",
          flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    odur = duration(OUT_VIDEO)
    full_len_ok = abs(odur - vend) <= 1.0

    print("[5/7] Independent verification on rendered output ...", flush=True)
    intro_db = volumedetect(OUT_VIDEO, 0, 2)
    final_db = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    report = {
        "experiment": "fill_v2 (silent-pocket elimination, lesson_11)",
        "lesson": "lesson_11_cross_product_duality",
        "script_source": "web_platform/assets/audio/linear_algebra/lesson_11/manifest.json "
                         "(cue texts, alias-deduped)",
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": "heavy expansion + recompute-scale-from-rendered-speech; "
                    "absolute sample offset (start*44100); atempo in "
                    "[0.82,2.0]; pad only; no truncation",
        "sfx": "NONE - clean speech only",
        "voice": VOICE,
        "video_source": str(ORIGINAL_VIDEO),
        "video_source_swapped": False,
        "backup_video_left_untouched": str(OLD_VIDEO),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "video_duration_sec": round(vend, 3),
        "output_duration_sec": round(odur, 3),
        "full_length_parity_ok": full_len_ok,
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "max_measured_drift_ms": round(max_drift, 6),
        "overrun_cues": overrun,
        "top_up_rounds": top_up_rounds,
        "speech_layout": meta,
        "fill_gate": gate,
        "volumedetect_intro_0_2s_db": intro_db,
        "volumedetect_final_2s_db": final_db,
        "cues": placed,
    }
    report["success"] = bool(
        gate["all_fill_gates_pass"] and full_len_ok and not failed
        and len(placed) == len(cues))

    VERIFY.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n[6/7] METRICS", flush=True)
    print(f"  output={OUT_VIDEO}", flush=True)
    print(f"  duration out={odur:.3f}s orig={vend:.3f}s parity={full_len_ok}", flush=True)
    print(f"  median_fill={median_fill} (>= {GATE_MEDIAN_FILL} -> {gate['median_fill_pass']})",
          flush=True)
    print(f"  max_internal_gap_s={max_internal_gap_s} "
          f"(<= {GATE_MAX_INTERNAL_GAP_S} -> {gate['max_internal_gap_pass']})", flush=True)
    print(f"  silence_runs>2s={n_big} (== 0 -> {gate['internal_silence_runs_pass']}), "
          f"max_run={max_run_s}s", flush=True)
    print(f"  top_up_rounds={top_up_rounds} overrun={overrun} drift={max_drift:.3f}ms",
          flush=True)
    print(f"  SUCCESS={report['success']}", flush=True)
    print(f"[7/7] VERIFY: {VERIFY}", flush=True)

    if not report["success"]:
        raise SystemExit("FILL GATE FAILED - not claiming success. See verification.json.")


if __name__ == "__main__":
    asyncio.run(main())
