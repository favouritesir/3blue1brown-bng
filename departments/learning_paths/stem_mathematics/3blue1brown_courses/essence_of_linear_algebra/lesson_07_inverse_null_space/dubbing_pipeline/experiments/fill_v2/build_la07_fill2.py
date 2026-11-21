"""
EXPERIMENT fill_v2 — Full-length Bengali dub for Linear Algebra Lesson 07
(Inverse matrices, column space and null space)
==========================================================================================
Goal: RE-RENDER the Lesson 07 dub to eliminate the 34 silent pockets (up to ~18 s) left
by clean_timesync_v2, WITHOUT touching teacher audio, manifests, or any other lesson,
and WITHOUT swapping the video source.

Copied from the quality-gated pipeline:
    essence_of_calculus/lesson_08_integration/dubbing_pipeline/experiments/
      clean_timesync_v2/build_calc08_clean.py
and specialised for lesson_07 exactly like the proven fill_v2 runs for lessons 06/15:

  1. Cue source = the AUDIO MANIFEST (read-only), alias-deduped:
       web_platform/assets/audio/linear_algebra/lesson_07/manifest.json
     33 cues across 4 sections. The manifest cue texts ARE the dubbing script.
  2. HEAVY contextual pedagogical expansion: every cue is grown INCREMENTALLY, one
     natural teacher-style Bengali sentence at a time (PIECE_DIR), until its rendered
     speech reaches ~97% of its proportional share of the speech budget. A short cue
     can thus grow from ~5 s to ~40 s without one oversized TTS request. The base
     manifest text is never re-synthesised.
  3. RECOMPUTE SCALE FROM RENDERED SPEECH: after all speech is rendered, the timeline
     scale is derived from MEASURED rendered durations (not authored manifest durations)
     and every cue window is rebuilt from its own rendered speech. Hence tempo ~= 1.0
     and fill ratio ~= 1.0, i.e. no dead air inside any cue window.
  4. FILL GATE (hard, no success claimed unless all pass):
       median_fill >= 0.72
       max_internal_gap_s <= 1.5
       silencedetect INTERNAL silence runs > 2 s == 0 (master AND final mp4)
       output duration ~= original duration (|delta| <= 1.0 s)
       all cues placed, zero TTS failures.
  5. Absolute sample placement (start*44100) -> zero cumulative drift; pad only,
     never truncate; atempo fit in [0.82, 2.2]; NO SFX (clean speech only).
  6. Canvas padded to the FULL original video duration so -shortest cannot trim frames.
  7. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.

STRICT SAFETY:
  - Teacher audio, manifests, master scripts and other lessons: READ-ONLY.
  - Video source is NEVER swapped: -c:v copy from original_source/full_original.mp4.
  - Old video at media_vault/lesson_07/experiments/3b1b_lesson_07_full_dubbed.mp4
    is LEFT IN PLACE as the backup; this run only writes into NEW fill_v2 folders.
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

# ---------------------------------------------------------------------------
# Paths (NEW fill_v2 experiment folders only)
# ---------------------------------------------------------------------------
EXP = Path(__file__).resolve().parent
BASE = EXP.parent.parent                        # .../lesson_07_inverse_null_space/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform

MANIFEST = WEB / "assets" / "audio" / "linear_algebra" / "lesson_07" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_07" / "original_source" / "full_original.mp4"
OLD_VIDEO = WEB / "media_vault" / "lesson_07" / "experiments" / "3b1b_lesson_07_full_dubbed.mp4"  # backup, untouched
OUT_VIDEO = WEB / "media_vault" / "lesson_07" / "experiments" / "fill_v2" / "3b1b_lesson_07_full_dubbed_fill2.mp4"

RAW_DIR = EXP / "raw"           # final concatenated speech per cue
PIECE_DIR = EXP / "pieces"      # incremental TTS pieces (base + expansions)
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

# ---------------------------------------------------------------------------
# Audio / timeline constants
# ---------------------------------------------------------------------------
SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
TEMPO_FLOOR = 0.82          # gentle natural slowdown (IMPROVED_DUB_FILL_POLICY)
FADE_MS = 12
VIDEO_ID = "uQhTuRlWM3E"    # official 3Blue1brown video (metadata only; full original reused)

LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Expansion targets / hard gates
EXPAND_TARGET_RATIO = 0.97   # expand each cue until rendered >= 97% of its target window
MAX_EXPAND_PASSES = 30       # generous: long cues need several extra sentences
FILL_GATE_MEDIAN = 0.72
FILL_GATE_MAX_GAP_S = 1.5
SILENCE_RUN_MAX_S = 2.0
DURATION_TOLERANCE_S = 1.0   # |output - original| must be <= this

# ---------------------------------------------------------------------------
# Pedagogical Bengali expansion corpus.
# Section-specific pools plus a generic pool with rotating connectors. All
# sentences are natural teacher-style Bangla; symbols/acronyms are phonetically
# transliterated (আই হ্যাট, জে হ্যাট, কে হ্যাট, এ, ভি, এক্স, টুডি, থ্রিডি ...)
# so Edge-TTS never stumbles on bare Latin text.
# ---------------------------------------------------------------------------
SECTION_POOL = {
    "sec_01_linear_systems": [
        "আসুন প্রথমে সেই দুটি সরল সমীকরণের দিকে ফিরে তাকাই, যেখানে দুই এক্স যোগ দুই ওয়াই সমান মাইনাস চার আর এক্স যোগ তিন ওয়াই সমান মাইনাস এক।",
        "বীজগণিতে আমরা এই দুটিকে আলাদা আলাদা হিসাব করতাম, কিন্তু ম্যাট্রিক্সের ভাষায় এদের একসাথে একটি মাত্র ভেক্টর সমীকরণে লেখা যায়।",
        "সহগগুলো একটি দুই বাই দুই ম্যাট্রিক্স তৈরি করে, আর অজানা চলক এক্স ও ওয়াই মিলে একটি কলাম ভেক্টর গঠন করে।",
        "ম্যাট্রিক্সের প্রথম কলাম আমাদের বলে আই হ্যাট রূপান্তরের পর কোথায় পৌঁছায়, আর দ্বিতীয় কলাম বলে জে হ্যাট কোথায় যায়।",
        "তাই এ গুণ ভেক্টর এক্স সমান ভেক্টর ভি লেখার অর্থ হলো, রূপান্তরিত ভিত্তি ভেক্টরগুলোকে কিছু সংখ্যা দিয়ে গুণ করে যোগ করলেই লক্ষ্য ভেক্টর ভি পাওয়া যাবে।",
        "এই গুণ আর যোগের ক্রিয়াটিকেই আমরা বলি রৈখিক সমাবেশ, আর পুরো লিনিয়ার অ্যালজেব্রার প্রতিটি ধাপ এই একটিমাত্র ধারণার ওপর দাঁড়িয়ে।",
        "জ্যামিতিকভাবে প্রশ্নটি দাঁড়ায় এমন: রূপান্তরের আগে কোন ইনপুট ভেক্টরটি এমন জায়গায় ছিল যা এ প্রয়োগের পর ঠিক ভির ওপর পড়বে?",
        "এই প্রশ্নের উত্তর আমরা সোজাসুজি হিসাব না করে উল্টো দিক থেকে খুঁজি, অর্থাৎ ভিকে পেছনে ফিরিয়ে নিয়ে তার উৎস ভেক্টরটিকে খোঁজা হয়।",
        "সমীকরণ জোটের প্রতিটি সমাধান আসলে একটি নির্দিষ্ট ইনপুট বিন্দু, যার রূপান্তরিত অবস্থান লক্ষ্য ভেক্টরের সাথে মিলে যায়।",
        "যখন ম্যাট্রিক্সের ডিটারমিন্যান্ট শূন্য নয়, তখন সমতল চ্যাপ্টা হয় না, ফলে প্রতিটি লক্ষ্য ভেক্টরের জন্য ঠিক একটি করে ইনপুট ভেক্টর পাওয়া যায়।",
        "কিন্তু ডিটারমিন্যান্ট শূন্য হলে পুরো সমতল একটি রেখায় বা বিন্দুতে সংকুচিত হয়, তখন অনেক ইনপুট একই জায়গায় পড়ে আর তথ্য হারিয়ে যায়।",
        "তাই সমাধান আছে কি না, একটিমাত্র সমাধান না কি অসংখ্য সমাধান—এই প্রশ্নের উত্তর নির্ভর করে রূপান্তরের জ্যামিতির ওপর।",
        "আসুন কল্পনা করি ভেক্টর ভি সমতলে স্থির আছে আর আমরা টেপটিকে উল্টো দিকে টানছি, তখন কোথা থেকে শুরু করা হয়েছে তা দেখা যাবে।",
        "এই উল্টো টানার ক্রিয়াটিই পরবর্তীতে ইনভার্স ম্যাট্রিক্স নামে পরিচিত হবে, যদিও এখন আমরা শুধু ছবিটি মনে রাখছি।",
        "মনে রাখবেন, হিসাবের আগে ছবিটি বোঝা অনেক গুরুত্বপূর্ণ, কারণ ছবি থাকলে সূত্র নিজেই সঠিক পথ বাতলে দেয়।",
        "পরবর্তী ধাপে আমরা দেখব কীভাবে এই রূপান্তরকে পুরোপুরি উল্টানো যায় আর কখনই বা তা অসম্ভব হয়ে পড়ে।",
    ],
    "sec_02_inverse_matrices": [
        "ধরা যাক ম্যাট্রিক্স এ এর ডিটারমিন্যান্ট শূন্য নয়, অর্থাৎ রূপান্তরটি সমতলকে কোনো নিচু মাত্রায় চ্যাপ্টা করেনি।",
        "এই শর্তেই কেবল পেছনে ফিরে আসার কথা চিন্তা করা যায়, কারণ হারানো মাত্রা আর ফেরানো যায় না।",
        "যেহেতু স্থান সংকুচিত হয়নি, তাই পুরো রূপান্তরটিকে হুবহু উল্টো দিকে চালিয়ে সমতলকে আদি অবস্থায় ফিরিয়ে আনা সম্ভব।",
        "এই উল্টো রূপান্তরটিকেই আমরা বলি এ ম্যাট্রিক্সের বিপরীত রূপান্তর, আর লেখা হয় এ পাওয়ার মাইনাস ওয়ান।",
        "যদি এ একটি নিরানব্বই ডিগ্রি ঘোরায়, তবে তার বিপরীত রূপান্তর ঠিক নিরানব্বই ডিগ্রি বিপরীত দিকে ঘুরিয়ে সবকিছু আগের জায়গায় ফিরিয়ে আনে।",
        "আই হ্যাট আর জে হ্যাটের নতুন অবস্থান লক্ষ্য করলে দেখা যায়, একটির পথ ধরে এগোনোর পর অন্যটি সেই পথ বরাবরই ফিরে আসছে।",
        "এই জোড়া রূপান্তরই প্রমাণ করে যে এ একটি বৈধ ফাংশন এবং তার বিপরীতাও একটি রৈখিক রূপান্তর।",
        "গাণিতিকভাবে এ ইনভার্স গুণ এ সমান আই, যেখানে আই হলো সেই ইউনিট ম্যাট্রিক্স যার কর্ণে এক আর বাকি জায়গায় শূন্য।",
        "এ গুণ ভেক্টর এক্স সমান ভি হলে, উভয় পাশে এ ইনভার্স প্রয়োগ করলেই পাই ভেক্টর এক্স সমান এ ইনভার্স গুণ ভি।",
        "জ্যামিতিকভাবে এর অর্থ হলো ভিকে পেছনে ফিরিয়ে নিয়ে দেখা কোথায় তার উৎস ভেক্টরটি ছিল।",
        "কিন্তু যদি ডিটারমিন্যান্ট শূন্য হয়, তখন রূপান্তরটি পুরো সমতলকে একটি সরলরেখায় বা একক বিন্দুতে পরিণত করেছে।",
        "অনেকগুলো ভেক্টর এখন একই জায়গায় পড়েছে, তথ্য হারিয়ে গেছে, তাই পেছনে ফিরে আসার কোনো নির্দিষ্ট নিয়ম থাকে না।",
        "রেখার প্রতিটি বিন্দুকে অসংখ্য বিন্দুতে পাঠাতে হলে তা কোনো ফাংশনের নিয়ম মানে না, তাই এ ইনভার্স থাকে না।",
        "অর্থাৎ ডিটারমিন্যান্ট অশূন্য হওয়া আর ইনভার্সের অস্তিত্ব—এ দুটি কথা আসলে একই কথার দুই রূপ।",
        "আসুন নিজের ভাষায় বলে দেখি, কেন একের পর এক রূপান্তর প্রয়োগ করলে শেষে আবার শূন্য অবস্থানে ফিরে আসা যায়।",
        "এই বোঝাপড়াই পরবর্তীতে কলাম স্পেস আর নাল স্পেসের গল্পকে সম্পূর্ণ করে তুলবে।",
    ],
    "sec_03_rank_and_column_space": [
        "যখন কোনো রূপান্তরে সমতল চ্যাপ্টা হয়ে যায়, তখন তার আউটপুট ঠিক কেমন হতে পারে, সেটাই আমরা এখন দেখব।",
        "রূপান্তর প্রয়োগের পর যত সম্ভাব্য আউটপুট ভেক্টর তৈরি হতে পারে, তাদের সমগ্র সেটকেই ম্যাট্রিক্সের কলাম স্পেস বলা হয়।",
        "এটিকে কলাম স্পেস নাম দেওয়া হলো কেন, কারণ প্রতিটি কলাম আসলে রূপান্তরের পর ভিত্তি ভেক্টরগুলো কোথায় গিয়ে পৌঁছায় তা নির্দেশ করে।",
        "অর্থাৎ কলামগুলো হলো রূপান্তরিত আই হ্যাট আর জে হ্যাটের ঠিকানা, আর তাদের স্প্যানই হলো সম্ভাব্য সব আউটপুট।",
        "যেকোনো ইনপুট ভেক্টরের রূপান্তর হলো ওই কলামগুলোরই একটি রৈখিক সমাবেশ, তাই আউটপুট কখনোই ওই স্প্যানের বাইরে যেতে পারে না।",
        "যদি লক্ষ্য ভেক্টর ভি এই স্প্যানের বাইরে থাকে, তবে এ গুণ এক্স সমান ভির কোনো সমাধানই নেই।",
        "র‍্যাংক মাপা হয় এই আউটপুট স্পেসের মাত্রা দিয়ে, ইনপুটের মাত্রা দিয়ে নয়, এই পার্থক্যটি মনে রাখা জরুরি।",
        "বাঁয়ে রূপান্তরের সমস্ত আউটপুট একটি সরলরেখার ওপর পড়েছে, সেটি র‍্যাংক এক, কারণ বেঁচে থাকা মাত্রা মাত্র একটি।",
        "ডানে আউটপুটগুলো পুরো দ্বিমাত্রিক সমতল জুড়ে ছড়িয়ে আছে, সেটি র‍্যাংক দুই, আর তখনই ডিটারমিন্যান্ট অশূন্য হয়।",
        "ত্রিমাত্রিক স্থানে আই হ্যাট, জে হ্যাট আর কে হ্যাট দ্বারা তৈরি আউটপুট স্পেস যদি পূর্ণ থ্রিডি স্পেস থাকে, তবে র‍্যাংক তিন।",
        "যখন র‍্যাংক ম্যাট্রিক্সের কলাম সংখ্যার সমান হয়, তখন তাকে ফুল র‍্যাংক বলা হয় আর তখনই শুধু ইনভার্সের অস্তিত্ব থাকে।",
        "র‍্যাংক শব্দটির আক্ষরিক অর্থ পদ বা পদমর্যাদা, কিন্তু এখানে এটি কেবল বলে দেয় কত মাত্রা বেঁচে রইল।",
        "আসুন ছবিটি মনে রেখে বলে দেখি, র‍্যাংক এক কোন ক্ষেত্রে আর র‍্যাংক দুই কোন ক্ষেত্রে, আর কোনটিতে সমাধান থাকবে।",
        "কলাম স্পেস আমাদের বলে দেয় কোন লক্ষ্য অর্জন করা সম্ভব, আর নাল স্পেস বলে দেয় কোন দিক হারিয়ে গেছে।",
        "এই দুটি স্পেস একসাথে মিলে পুরো রূপান্তরের জ্যামিতিক ছবিটি সম্পূর্ণ করে, যা শুধু সংখ্যা দিয়ে বোঝা যায় না।",
        "পরবর্তী পাঠে আমরা দেখব হারানো মাত্রাগুলো কোথায় চলে যায় আর সেই জগৎকে কীভাবে নাল স্পেস নামে ডাকা হয়।",
    ],
    "sec_04_null_space": [
        "এখন আমরা সেই হারানো দিকটির কথা বলব, যা সংকোচনের সময় নিশ্চুপ হয়ে যায় এবং মূলবিন্দুতে মিলিয়ে যায়।",
        "রৈখিক রূপান্তর মূলবিন্দুকে সর্বদা নিজের জায়গায় রাখে, ফলে সংকোচনের সময় মূলবিন্দু ছাড়াও অসংখ্য ভেক্টর সেখানে আছড়ে পড়ে।",
        "ইনপুটের যে দিকটি ধ্বংস হয়েছে ঠিক সেটিই হলো নাল স্পেস, আর যে দিকটি বেঁচে থাকা রেখায় পড়েছে সেটিই কলাম স্পেস।",
        "নাল স্পেস হলো সেই সব ভেক্টরের সেট যারা রূপান্তরের পর শূন্য ভেক্টরে পরিণত হয়, অর্থাৎ যাদের ছাপ মুছে যায়।",
        "র‍্যাংক যোগ নালিটি সমান এন, অর্থাৎ বেঁচে থাকা মাত্রা আর হারানো মাত্রা মিলে মোট মাত্রা তৈরি করে।",
        "টুডি সমতলে নাল স্পেস একটি রেখা হতে পারে, আবার থ্রিডি স্থানে এটি একটি রেখা বা সমতল হতে পারে।",
        "যদি ম্যাট্রিক্সের র‍্যাংক এক হয়, তবে নালিটি হবে এক, অর্থাৎ একটা পুরো দিক মূলবিন্দুতে সংকুচিত হয়েছে।",
        "যদি এ গুণ এক্স সমান ভির একটি নির্দিষ্ট সমাধান থাকে, তবে তার সাথে নাল স্পেসের যেকোনো ভেক্টর যোগ করলেও নতুন বৈধ সমাধান পাওয়া যায়।",
        "কারণ নাল স্পেসের ভেক্টর রূপান্তরের পর শূন্য হয়ে যায়, ফলে ফলাফলের কোনো হেরফের হয় না।",
        "অর্থাৎ সমাধানের একটি বিন্দু পেলেই আমরা পুরো সমাধান-সেটটি লিখতে পারি, সেটি হলো নির্দিষ্ট সমাধানের সাথে নাল স্পেসের যোগ।",
        "যখন লক্ষ্য ভি শূন্য ভেক্টর হয়, তখন নাল স্পেসই হবে সব সমাধানের সেট, কারণ শূন্য ভেক্টর সবসময় নিজের জায়গায় থাকে।",
        "এই কারণেই ডিটারমিন্যান্ট শূন্য হলে ইনভার্স থাকে না, কিন্তু সমাধান না থাকা এমন নয়, বরং সমাধানের স্বাধীনতা বেড়ে যায়।",
        "লাল রেখার ওপর থাকা প্রতিটি ভেক্টর রূপান্তরের পর কমলা মূলবিন্দুতে গিয়ে মিলিত হচ্ছে, আর অন্য দিকের ভেক্টরগুলো আউটপুট রেখায় ছড়িয়ে পড়েছে।",
        "একই ছবিতে কলাম স্পেস আর নাল স্পেসের পরিপূরক সম্পর্ক স্পষ্ট হয়ে ওঠে, একটি বেঁচে থাকে আর অন্যটি হারিয়ে যায়।",
        "আসুন নিজের ভাষায় বলে দেখি, কোন ভেক্টরগুলো মূলবিন্দুতে পড়বে আর কোনগুলো বেঁচে থাকা রেখার ওপর থাকবে।",
        "এই গভীর উপলব্ধিটি আমাদের স্পষ্ট করে দেয় যে বিপরীত ম্যাট্রিক্স, কলাম স্পেস আর নাল স্পেস কোনো বিচ্ছিন্ন সূত্র নয়, বরং এক অবিচ্ছেদ্য জ্যামিতিক গল্প।",
    ],
}

GENERIC_POOL = [
    "এখানে একটু থামুন এবং বিষয়টি নিজের ভাষায় বলে দেখুন, কোনো ধারণা তখনই পোক্ত হয় যখন আপনি সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন।",
    "আরেকটি দৃষ্টিকোণ থেকে দেখা যাক, একই সত্যকে ভিন্ন ভাষায় বললে প্রায়ই তার গভীরতা আরও স্পষ্ট হয়ে ওঠে।",
    "মনে রাখার মতো কথা হলো, গণিতে নতুন নাম শেখার চেয়ে পুরোনো ধারণার নতুন প্রয়োগ দেখাটা অনেক বেশি মূল্যবান।",
    "আসুন এই ধাপটিকে একটা সরল উদাহরণ দিয়ে পরীক্ষা করে দেখি, তাহলে বিমূর্ত কথাটি অনেক স্বজ্ঞাত হয়ে উঠবে।",
    "এই জায়গায় অনেক শিক্ষার্থীই একটু বিভ্রান্ত হন, তাই আমরা ধীরে ধীরে ছোট ছোট ধাপে বিষয়টি আবার গড়ে তুলছি।",
    "লেখচিত্রের দিকে তাকালেই দেখা যায় যে নিয়মটি আসলে কতটা স্বাভাবিক, সংখ্যার গল্প আর ছবির গল্প এখানে একই কথা বলে।",
    "আরও একটু গভীরে যাই, এই ধর্মটি কেন ভিত্তি বদলালেও টিকে থাকে, তার কারণ খুঁজে বের করাই শিখনের আসল কাজ।",
    "বলা হয়ে থাকে, যখন কোনো ধারণা একাধিক জগতে একই রকম কাজ করে, তখনই বোঝা যায় সেটি কতটা মৌলিক।",
    "এবার চোখ বন্ধ করে কল্পনা করুন, আমরা স্থানাঙ্কগুলো সরিয়ে দিলেও যে সম্পর্কগুলো পেছনে থাকে, তারাই আসলে গণিত।",
    "পরের ধাপে আমরা এই একই নিয়ম ব্যবহার করব, তাই এখনকার এই ছোট্ট পর্যবেক্ষণটি মনে রাখলে কাজ অনেক সহজ হবে।",
    "সংজ্ঞা মুখস্থ করার বদলে এর পেছনের প্রয়োজনটি বুঝতে চেষ্টা করুন, তখন সূত্রটি নিজেই পথ বাতলে দেবে।",
    "এইভাবে ধাপে ধাপে এগিয়ে গেলে দেখা যাবে, যেটা আজ অসীম আর বিমূর্ত মনে হচ্ছে, সেটি আসলে সসীম ও সুন্দর এক কাঠামো।",
]

CONNECTORS = [
    "",
    " আবার ভাবুন, ",
    " আরেকটু গভীরে যাই। ",
    " এখানে একটু থামি। ",
    " মনে রাখার মতো কথা হলো, ",
    " আরও একটি দৃষ্টিকোণ থেকে দেখলে, ",
]


# ---------------------------------------------------------------------------
# Generic helpers (kept identical to the proven clean_timesync_v2 pipeline)
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
    out = run(f'ffprobe -v error -show_entries format=duration -of '
              f'default=noprint_wrappers=1:nokey=1 "{path}"')
    try:
        return float(out.strip())
    except Exception:
        return 0.0


def video_duration(path):
    d = duration(path)
    try:
        sd = float(run(f'ffprobe -v error -select_streams v:0 -show_entries '
                       f'stream=duration -of default=noprint_wrappers=1:nokey=1 '
                       f'"{path}"').strip())
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
            pp = PIECE_DIR / f"half_{raw.stem}_{j}.mp3"
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
            lf = PIECE_DIR / f"list_{raw.stem}.txt"
            with open(lf, "w", encoding="utf-8") as f:
                for x in made:
                    f.write(f"file '{x.as_posix()}'\n")
            run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{raw}" > NUL 2>&1')
            ok = valid(raw)
    if not ok:
        parts = [p.strip() for p in re.split(r"[।]", text) if p.strip()]
        made = []
        for j, p in enumerate(parts):
            pp = PIECE_DIR / f"sent_{raw.stem}_{j}.mp3"
            purge(pp)
            try:
                await tts_save(p + "।", pp)
                if valid(pp):
                    made.append(pp)
            except Exception:
                pass
        if made:
            lf = PIECE_DIR / f"sentlist_{raw.stem}.txt"
            with open(lf, "w", encoding="utf-8") as f:
                for x in made:
                    f.write(f"file '{x.as_posix()}'\n")
            run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{raw}" > NUL 2>&1')
            ok = valid(raw)
    return ok


def concat_pieces(pieces, out):
    """Concatenate incremental TTS pieces into one raw MP3 for the cue."""
    if not pieces:
        return False
    if len(pieces) == 1:
        run(f'ffmpeg -y -i "{pieces[0]}" -c copy "{out}" > NUL 2>&1')
        return valid(out)
    lf = PIECE_DIR / f"concat_{out.stem}.txt"
    with open(lf, "w", encoding="utf-8") as f:
        for p in pieces:
            f.write(f"file '{p.as_posix()}'\n")
    run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{out}" > NUL 2>&1')
    return valid(out)


# ---------------------------------------------------------------------------
# Cue loading — from the AUDIO MANIFEST (read-only, alias-deduped)
# ---------------------------------------------------------------------------
def load_manifest_cues():
    """Return (cues, dedup_info). cue texts = dubbing script (alias-deduped)."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cues = []
    seen = set()
    duplicates = []
    for sec_id, sec in data.get("sections", {}).items():
        for c in sec.get("cues", []):
            text = sanitize(c.get("text", ""))
            if not text:
                continue
            key = text
            if key in seen:
                duplicates.append({"section": sec_id, "index": c.get("index")})
                continue                       # enforce alias-dedup
            seen.add(key)
            cues.append({
                "text": text,
                "dur_ms": float(c.get("duration_ms", 0)),
                "section": sec_id,
                "index_in_section": c.get("index"),
                "manifest_start_ms": float(c.get("start_ms", 0)),
                "manifest_end_ms": float(c.get("end_ms", 0)),
            })
    return cues, {"input_cues": sum(len(s.get("cues", [])) for s in data.get("sections", {}).values()),
                  "deduped_cues": len(cues), "duplicates_skipped": duplicates}


def expansion_sentence(sec_id, n):
    """Pedagogical sentence n for a section, cycling pools with varied connectors."""
    pool = SECTION_POOL.get(sec_id, []) + GENERIC_POOL
    if not pool:
        return GENERIC_POOL[0]
    base = pool[n % len(pool)]
    conn = CONNECTORS[(n // len(pool)) % len(CONNECTORS)]
    return (conn + base).strip()


# ---------------------------------------------------------------------------
# Incremental heavy TTS expansion
# ---------------------------------------------------------------------------
async def synth_and_expand(cues, targets):
    """Synthesise base + incremental pedagogical expansions per cue.

    Returns (expansion_records, rendered_durations, failed). Each cue's final
    raw MP3 is written to RAW_DIR/raw_<id>.mp3. Incremental pieces live in
    PIECE_DIR so a long cue never needs a single oversized TTS request.
    """
    PIECE_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    rendered = {}
    failed = []

    for i, c in enumerate(cues):
        cid = i + 1
        target = targets[cid]
        base_piece = PIECE_DIR / f"base_{cid:03d}.mp3"
        ok = await synth(sanitize(c["text"]), base_piece)
        if not ok:
            failed.append(cid)
            print(f"  WARNING cue {cid} base TTS failed", flush=True)
            rendered[cid] = 0.0
            continue

        pieces = [base_piece]
        cur = duration(base_piece)
        base_natural = cur
        added = 0
        for k in range(MAX_EXPAND_PASSES):
            if cur >= EXPAND_TARGET_RATIO * target:
                break
            sent = expansion_sentence(c["section"], k)
            piece = PIECE_DIR / f"exp_{cid:03d}_{k:02d}.mp3"
            if not await synth(sanitize(sent), piece):
                fb = PIECE_DIR / f"fb_{cid:03d}_{k:02d}.mp3"
                if not await synth(sanitize(GENERIC_POOL[k % len(GENERIC_POOL)]), fb):
                    continue
                piece = fb
            pd = duration(piece)
            if pd <= 0.3:
                continue
            pieces.append(piece)
            cur += pd
            added += 1

        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not concat_pieces(pieces, raw):
            failed.append(cid)
            rendered[cid] = 0.0
            continue
        rendered[cid] = duration(raw)
        records.append({
            "id": cid,
            "section": c["section"],
            "base_natural_sec": round(base_natural, 3),
            "target_sec": round(target, 3),
            "rendered_sec": round(rendered[cid], 3),
            "expansion_sentences": added,
            "pieces": len(pieces),
        })
        print(f"  cue {cid:02d}: base={base_natural:6.2f}s -> rendered={rendered[cid]:6.2f}s "
              f"(target={target:6.2f}s, +{added} sentences)", flush=True)

    return records, rendered, failed


# ---------------------------------------------------------------------------
# Scale recomputation from rendered speech + window rebuild
# ---------------------------------------------------------------------------
def recompute_scale_from_rendered(rendered, cues, vend):
    """Derive the timeline scale from ACTUAL rendered speech, then rebuild
    cue windows so they tile [LEAD_IN, vend - TAIL_MARGIN] exactly.

    Initial proportional targets (teacher pacing) are only used to decide how
    much to expand each cue. After expansion, the final scale is:

        scale_render = speech_budget / sum(rendered_i)

    and each final window = rendered_i * scale_render. Because expansion
    drives sum(rendered_i) ~= speech_budget, scale_render ~= 1.0, which makes
    the per-cue tempo ~= 1.0 and the fill ratio ~= 1.0 (no dead air).
    """
    n = len(cues)
    pause_total = (INTER_CUE_PAUSE_MS / 1000.0) * (n - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    speech_budget = usable - pause_total
    rendered_total = sum(rendered.values())

    if rendered_total <= 0:
        rendered_total = speech_budget
    scale_render = speech_budget / rendered_total

    rebuilt = []
    cursor = LEAD_IN_SEC
    for i, c in enumerate(cues):
        cid = i + 1
        r = rendered.get(cid, 0.0)
        if r <= 0:
            r = max(0.5, c["dur_ms"] / 1000.0 * scale_render)
            rendered[cid] = r
        win = r * scale_render
        start = cursor
        end = start + win
        rebuilt.append({
            "id": cid,
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(win, 3),
            "bn": c["text"],
            "section": c["section"],
        })
        cursor = end + INTER_CUE_PAUSE_MS / 1000.0
    return rebuilt, scale_render, {
        "usable_sec": round(usable, 3),
        "pause_total_sec": round(pause_total, 3),
        "speech_budget_sec": round(speech_budget, 3),
        "rendered_total_sec": round(rendered_total, 3),
        "scale_render": round(scale_render, 6),
        "tiled_end_sec": round(rebuilt[-1]["end"], 3) if rebuilt else 0.0,
    }


# ---------------------------------------------------------------------------
# Placement (identical maths to the proven pipeline, with fill measurement)
# ---------------------------------------------------------------------------
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


def silencedetect_internal_runs(path, vend, log_name="_silencedetect.log"):
    """Run ffmpeg silencedetect; count/return silence runs > SILENCE_RUN_MAX_S
    that lie strictly inside (LEAD_IN, vend - TAIL_MARGIN)."""
    log = EXP / log_name
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats", "-vn",
        "-i", str(path),
        "-af", f"silencedetect=noise=-40dB:d={SILENCE_RUN_MAX_S}",
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
    starts = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", txt)]
    ends = [(float(a), float(b)) for a, b in
            re.findall(r"silence_end:\s*([\d.]+)\s*\|\s*silence_duration:\s*([\d.]+)", txt)]
    runs = []
    for idx, (s, (e, d)) in enumerate(zip(starts, ends)):
        runs.append({"index": idx, "start": round(s, 3), "end": round(e, 3),
                     "duration": round(d, 3)})
    lo = LEAD_IN_SEC + 0.10
    hi = vend - TAIL_MARGIN_SEC - 0.10
    internal = [r for r in runs if r["start"] >= lo and r["end"] <= hi
                and r["duration"] > SILENCE_RUN_MAX_S]
    return {"all_runs": runs, "internal_runs_gt_2s": internal,
            "internal_count": len(internal), "window_checked": [round(lo, 3), round(hi, 3)]}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, PIECE_DIR, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    if not ORIGINAL_VIDEO.exists():
        raise RuntimeError(f"original source missing: {ORIGINAL_VIDEO}")

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    source_cues, dedup = load_manifest_cues()
    n = len(source_cues)
    pause_total_s = (INTER_CUE_PAUSE_MS / 1000.0) * (n - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    speech_budget = usable - pause_total_s
    total_manifest_dur = sum(c["dur_ms"] for c in source_cues) / 1000.0

    # Initial proportional target windows (teacher pacing) used ONLY to size
    # how much each cue must be expanded. The final scale is recomputed from
    # rendered speech below.
    targets = {}
    for i, c in enumerate(source_cues):
        share = c["dur_ms"] / 1000.0 / total_manifest_dur if total_manifest_dur else 1.0 / n
        targets[i + 1] = share * speech_budget

    print(f"video={vend:.3f}s cues={n} manifest_audio={total_manifest_dur:.3f}s "
          f"speech_budget={speech_budget:.3f}s", flush=True)

    print("[1/7] TTS base + HEAVY incremental pedagogical expansion ...", flush=True)
    exp_records, rendered, failed = await synth_and_expand(source_cues, targets)

    print("[2/7] Recompute scale from rendered speech + rebuild windows ...", flush=True)
    cues, scale_render, scale_info = recompute_scale_from_rendered(rendered, source_cues, vend)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"  scale_render={scale_render:.4f} rendered_total={scale_info['rendered_total_sec']:.2f}s "
          f"tiled_end={scale_info['tiled_end_sec']:.2f}s", flush=True)

    print("[3/7] Absolute sample placement (start*44100, tempo floor, pad-only) ...", flush=True)
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    CHUNK = 1_000_000
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    fills = []
    internal_gaps = []
    overrun = 0
    last_cue_end = 0.0
    exp_by_id = {r["id"]: r for r in exp_records}
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            print(f"  SKIP cue {cid} (no audio)", flush=True)
            continue
        arr, info = make_cue(raw, float(c["duration"]), CUE_DIR / f"cue_{cid:03d}.wav", cid)
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
        i16 = (np.clip(arr, -1.0, 1.0) * 32767.0).astype(np.int16)
        seg = canvas[start_sample:end].astype(np.int32)
        seg += i16.astype(np.int32)
        np.clip(seg, -32768, 32767, out=seg)
        canvas[start_sample:end] = seg.astype(np.int16)
        del arr, i16, seg
        last_cue_end = max(last_cue_end, end / SR)
        exp = exp_by_id.get(cid, {})
        placed.append({
            "id": cid,
            "section": c["section"],
            "start_sec": c["start"],
            "end_sec": c["end"],
            "expected_start_ms": round(float(c["start"]) * 1000, 2),
            "actual_start_ms": round(start_sample / SR * 1000, 2),
            "drift_ms": round(start_sample / SR * 1000 - float(c["start"]) * 1000, 6),
            "tempo": info["tempo"],
            "natural_sec": info["natural"],
            "target_sec": info["target"],
            "fill_ratio": info["fill_ratio"],
            "internal_gap_s": info["internal_gap_s"],
            "rendered_sec": exp.get("rendered_sec"),
            "expansion_sentences": exp.get("expansion_sentences"),
        })

    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    max_internal_gap_s = round(max(internal_gaps), 4) if internal_gaps else 0.0
    print(f"  median_fill={median_fill} max_internal_gap_s={max_internal_gap_s}", flush=True)

    peak_i = 0
    for i in range(0, len(canvas), CHUNK):
        seg = canvas[i:i + CHUNK]
        peak_i = max(peak_i, int(seg.max()), int(-seg.min()))
    peak_i = peak_i or 1
    if peak_i > 32112:
        scale_pk = 32112.0 / peak_i
        for i in range(0, len(canvas), CHUNK):
            seg = canvas[i:i + CHUNK].astype(np.float32)
            seg *= scale_pk
            np.rint(seg, out=seg)
            canvas[i:i + CHUNK] = seg.astype(np.int16)

    print("[4/7] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 '
        f'-c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 '
        f'-c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    print("[5/7] Mux with FULL original video (video copy, no src swap) ...", flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    print("[6/7] Silencedetect internal-pocket gate ...", flush=True)
    silence = silencedetect_internal_runs(MASTER_M4A, vend)
    final_silence = silencedetect_internal_runs(OUT_VIDEO, vend,
                                                 log_name="_final_mp4_silencedetect.log")
    print(f"  internal silence runs > 2s = {silence['internal_count']} "
          f"(final mp4 = {final_silence['internal_count']})", flush=True)

    print("[7/7] Assemble verification + evaluate gates ...", flush=True)
    out_dur = duration(OUT_VIDEO)
    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)

    gate_duration = abs(out_dur - vend) <= DURATION_TOLERANCE_S
    gate_fill = median_fill >= FILL_GATE_MEDIAN
    gate_gap = max_internal_gap_s <= FILL_GATE_MAX_GAP_S
    gate_silence = silence["internal_count"] == 0 and final_silence["internal_count"] == 0
    gate_cues = len(placed) == n and not failed
    gates_pass = all([gate_duration, gate_fill, gate_gap, gate_silence, gate_cues])

    report = {
        "experiment": "fill_v2 — pedagogical heavy-expand + recompute-scale-from-rendered-speech + fill gate",
        "lesson": "lesson_07_inverse_null_space",
        "video_id": VIDEO_ID,
        "script_source": f"audio_manifest:{MANIFEST.name} (alias-deduped cue texts = dubbing script)",
        "dedup_info": dedup,
        "strategy": ("absolute sample offset (start*44100); atempo fit in [0.82,2.2]; "
                     "pad-only; no truncation; timeline scale recomputed from rendered speech"),
        "voice": VOICE,
        "sfx": "NONE — clean speech only",
        "max_tempo": MAX_TEMPO,
        "tempo_floor": TEMPO_FLOOR,
        "video_source": str(ORIGINAL_VIDEO),
        "video_src_swapped": False,
        "backup_video_untouched": str(OLD_VIDEO),
        "backup_exists": OLD_VIDEO.exists(),
        "cue_count": len(placed),
        "expected_cue_count": n,
        "failed_tts_cues": failed,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "inter_cue_pause_ms": INTER_CUE_PAUSE_MS,
        "video_duration_sec": round(vend, 3),
        "output_duration_sec": round(out_dur, 3),
        "duration_delta_sec": round(out_dur - vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "scale_recompute": scale_info,
        "median_fill": median_fill,
        "max_internal_gap_s": max_internal_gap_s,
        "silencedetect": silence,
        "final_mp4_silencedetect": final_silence,
        "expansion_records": exp_records,
        "gates": {
            "duration_approx_original": {"pass": gate_duration, "delta_sec": round(out_dur - vend, 3),
                                         "tolerance_sec": DURATION_TOLERANCE_S},
            "median_fill_ge_0.72": {"pass": gate_fill, "value": median_fill},
            "max_internal_gap_le_1.5": {"pass": gate_gap, "value": max_internal_gap_s},
            "silencedetect_internal_gt2s_eq_0": {"pass": gate_silence,
                                                 "value": silence["internal_count"],
                                                 "final_mp4_value": final_silence["internal_count"]},
            "all_cues_placed": {"pass": gate_cues},
        },
        "ALL_GATES_PASS": gates_pass,
        "output_video": str(OUT_VIDEO),
        "output_size_bytes": OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0,
        "cues": placed,
    }
    try:
        probe = json.loads(run(f'ffprobe -v error -show_entries '
                               f'stream=index,codec_type,codec_name -of json "{OUT_VIDEO}"'))
        report["output_streams"] = probe.get("streams", [])
    except Exception as e:
        report["output_streams_error"] = str(e)

    odur = duration(OUT_VIDEO)
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\nDONE.", flush=True)
    print(f"cues={len(placed)} failed={failed} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={report['output_duration_sec']}s orig={report['video_duration_sec']}s "
          f"delta={report['duration_delta_sec']}s", flush=True)
    print(f"median_fill={median_fill} max_internal_gap_s={max_internal_gap_s} "
          f"internal_silence_runs={silence['internal_count']} "
          f"final_mp4={final_silence['internal_count']}", flush=True)
    print(f"GATES PASS = {gates_pass}", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
