"""
EXPERIMENT - Full-length clean absolute-sample Bengali dub
(Lockdown Math, Lesson 02 - "Exponential growth and epidemics", YouTube Kas0tIxDvrg)

Adapted verbatim from the proven clean_timesync_v2 pipeline:
    lockdown_math/lesson_01/dubbing_pipeline/experiments/clean_timesync_v2/build_lock01_clean.py

Guarantees (identical to the proven pipeline, plus IMPROVED_DUB_FILL_POLICY.md):
   1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
      half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
   2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
   3. IMPROVED FILL: atempo floor 0.82 (gentle slowdown), ceiling 2.2. Pad only,
      NEVER truncate. NO SFX: clean speech only.
   4. EXPANSION FIRST: the 13 manifest cues total only ~283 s of natural speech
      for a ~536 s video, so each cue is expanded with section-aware pedagogical
      Bengali sentences until the recomputed scale <= TARGET_SCALE (~1.38),
      giving a rendered-waveform fill of ~0.88 (headroom over the 0.72 floor).
      The manifest section IDs are LEGACY calendar names (sec-calendar-puzzle
      etc.); their spoken text is exponential-growth content, keyed by `alias`.
   5. Fill metrics (per-cue fill, median_fill, max_internal_gap_s) are measured
      from the rendered waveform and written into verification.json; auto
      re-render (expand weakest cues) if the gate fails.
   6. Canvas padded to the FULL original video duration so -shortest can never
      trim video frames. Final cue is capped to end inside the video.
   7. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
   8. Lightweight volumedetect (-vn -nostats, log to FILE) on intro and final.

Cue source (read-only; teacher audio / manifests are NEVER modified):
   web_platform/assets/audio/lockdown_math/lesson_02/manifest.json -> 13 cues in
   4 sections, alias-deduped. Cue texts are the dubbing script verbatim.
   web_platform/data/lockdown_math/lesson_02.json is read for topical context
   only (it informs the expansion pools); its wrong duration field is ignored.

Everything is written under NEW experiment folders.
"""
import os
import re
import json
import time
import asyncio
import statistics
import subprocess
import wave
from pathlib import Path

import numpy as np
import edge_tts

EXP = Path(__file__).resolve().parent
BASE = EXP.parent.parent                        # .../lockdown_math/lesson_02/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "lockdown_math" / "lesson_02.json"
MANIFEST = WEB / "assets" / "audio" / "lockdown_math" / "lesson_02" / "manifest.json"

# Original source: yt-dlp output (ffprobe-verified: 536.2 s, AV1+aac).
ORIGINAL_DIR = WEB / "media_vault" / "lockdown_math" / "lesson_02" / "original_source"
ORIGINAL_VIDEO = ORIGINAL_DIR / "full_original.mp4"

OUT_VIDEO = WEB / "media_vault" / "lockdown_math" / "lesson_02" / "experiments" / "3b1b_lockdown_02_full_dubbed.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
MIN_TEMPO = 0.82                     # IMPROVED_DUB_FILL_POLICY.md
FADE_MS = 12
VIDEO_ID = "Kas0tIxDvrg"
LESSON = "lesson_02"

# Silence margins: keep 0-2 s and the final 2 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Expansion policy constants.
TARGET_SCALE = 1.38                  # -> rendered fill ~= 1/(0.82*1.38) ~= 0.884
EXPAND_TARGET_FILL = 0.85            # aim well above the 0.72 median floor (headroom)
MAX_APPENDED_SENTENCES = 160
ACTIVE_THRESHOLD = 0.015
CHARS_PER_CHUNK = 1700               # chunk long TTS text for robustness


# ---------------------------------------------------------------------------
# Section-aware pedagogical sentences (keyed by the manifest `alias`).
# Cycled (never repeated verbatim inside a single add-call); each teaches real
# exponential-growth / epidemic-modelling mathematics in natural Bengali.
# ---------------------------------------------------------------------------
EXPANSION_POOL = {
    "sec_01_linear_vs_exponential": [
        "মানব মস্তিষ্ক বিবর্তনগতভাবে রৈখিক ভাবনায় অভ্যস্ত, তাই আমরা সাধারণভাবে ভাবি প্রতি পদক্ষেপে একই পরিমাণ যোগ হয়। কিন্তু সূচকীয় বৃদ্ধিতে প্রতিটি পদক্ষেপে আগের সম্পূর্ণ পরিমাণটি আবার যোগ হয়, ফলে বৃদ্ধি নিজেই নিজের ইন্ধন হয়ে যায়।",
        "রৈখিক বৃদ্ধিতে দশ পদক্ষেপে মাত্র দশ মিটার হলেও, দ্বিগুণ হওয়া বৃদ্ধিতে দশ পদক্ষেপে দাঁড়ায় এক হাজার গুণেরও বেশি। এই বিশাল পার্থক্যটি আমাদের বোঝা কঠিন, কারণ আমাদের দৈনন্দিন অভিজ্ঞতা সবসময় রৈখিক জগৎ থেকে আসে।",
        "চালের দানার ধাঁধাটি লক্ষ্য করুন। প্রথম ঘরে একটি, দ্বিতীয় ঘরে দুটি, তৃতীয় ঘরে চারটি—এভাবে প্রতি ঘরে আগের দ্বিগুণ করে গেলে ষাটতম ঘরে সংখ্যা হয় দুই এর ষাট ঘাতের কাছাকাছি।",
        "দুই এর ষাট ঘাত মানে এক বিপুল সংখ্যার চালের দানা, প্রায় এক হাজার কোটি কোটি। পুরো পৃথিবীর উপরিভাগকে এক মিটার পুরু করে ঢেলে দিলেও এই পরিমাণের কাছে পৌঁছানো যাবে না।",
        "রাজার সাথে দাবার উদ্ভাবকের গল্পে দেখা যায়, প্রথম কয়েকদিনে দানার সংখ্যা তেমন বাড়ে না, তাই রাজা হাসতে থাকেন। কিন্তু শেষের দিকে একাই পুরো রাজ্যের চাল শেষ করে দেয়।",
        "সূচকীয় বৃদ্ধির প্রথম দিককার ধাপগুলো অত্যন্ত নিরীহ ও ধীর মনে হয়। এই ধীরগতিই মানুষকে আত্মতুষ্টিতে ফেলে দেয়, আর ঠিক তখনই পরিস্থিতি নিয়ন্ত্রণের বাইরে চলে যায়।",
        "রৈখিক লেখচিত্র একটি সরলরেখা, কিন্তু সূচকীয় লেখচিত্র ধীরে শুরু করে হঠাৎ আকাশে উঠে যায়। ছবির এই দুটি রূপের তুলনাটিই আমাদের সতর্কতা শেখায়।",
        "দ্বিগুণ হওয়া মানে প্রতিবারই আগের চেয়ে এক গুণ বেশি বৃদ্ধি। তাই শেষ পদক্ষেপে যে পরিমাণ বাড়ে, তা আগের সব পদক্ষেপে বেড়ে যাওয়া পরিমাণের সমান বা তারও বেশি হয়।",
        "ত্রিশটি দ্বিগুণ পদক্ষেপে দূরত্ব দাঁড়ায় দুই এর উনত্রিশ ঘাত মিটার, যা পৃথিবীকে বারবার প্রদক্ষিণ করে চাঁদে পৌঁছানোর দূরত্বের চেয়েও অনেক বেশি।",
        "আমাদের ভুল ধারণা হয় কারণ আমরা ছোট সংখ্যার সাথে পরিচিত। বড় ঘাতের ক্ষেত্রে সরল অনুমান সম্পূর্ণ ব্যর্থ হয়—এটিই সূচকীয় বৃদ্ধির সবচেয়ে বড় শিক্ষা।",
        "প্রতিটি নতুন ডাবলিংয়ে যোগ হওয়া পরিমাণ আগের পুরো ইতিহাসের সমান। এই সত্য একবার বুঝে গেলে বক্ররেখার হঠাৎ খাড়া ওঠা আর রহস্যময় লাগে না।",
        "লীনার মডেলে বৃদ্ধি ধ্রুবক, সূচকীয় মডেলে বৃদ্ধি আনুপাতিক। এই ছোট্ট পার্থক্যটিই সময়ের সাথে সাথে বিশাল ফারাক তৈরি করে দেয়।",
        "অ্যালবার্ট বার্টলেট বলেছিলেন, মানবজাতির সবচেয়ে বড় ব্যর্থতা হলো সূচকীয় ফাংশনকে অনুধাবন করতে না পারা। এই পাঠে আমরা ঠিক সেই অক্ষমতাটিকে দূর করার চেষ্টা করব।",
        "যখন কোনো রাশি নিজের সমানুপাতে বাড়ে, তখন একে এক্সপোনেনশিয়াল বৃদ্ধি বলা হয়। এর গাণিতিক রূপ হলো আদি পরিমাণের সাথে এক প্লাস বৃদ্ধিহারের ঘাত গুণ করা।",
        "সরলরেখা আর বক্ররেখার এই তুলনা শুধু গণিতের নয়, জীবনের অনেক ক্ষেত্রেই প্রযোজ্য—জনসংখ্যা, টাকা, ভাইরাস সব জায়গায় একই নিয়ম কাজ করে।",
        "প্রথম কয়েক ঘরে চালের দানা দেখে রাজা ভেবেছিলেন পুরস্কার সস্তা। কিন্তু সূচকীয় প্রকৃতি ধীরে ধীরে শক্তি সঞ্চয় করে শেষে বিস্ফোরক রূপ নেয়।",
        "আমাদের কাছে স্বাভাবিক লাগে এমন প্রতিটি ধাপ আসলে রৈখিক অভ্যাসের ফল। সূচকীয় চিন্তা করতে হলে এই অভ্যাসকে ইচ্ছাকৃতভাবে ভেঙে নতুন দৃষ্টিভঙ্গি তৈরি করতে হবে।",
        "দুই এর ঘাত শেখার সবচেয়ে সহজ উপায় হলো ধাপগুলো লিখে দেখা—এক, দুই, চার, আট, ষোলো, বত্রিশ। একবার এই ধাপগুলো মনে হলেই বড় সংখ্যার আকার আন্দাজ করা যায়।",
    ],
    "sec_02_doubling_time": [
        "দ্বিগুণের সময় মানে সেই নির্দিষ্ট সময়কাল, যার মধ্যে কোনো রাশির পরিমাণ ঠিক দ্বিগুণ হয়ে যায়। সূচকীয় বৃদ্ধি বোঝার জন্য এটি সবচেয়ে সহজ মানসিক মানদণ্ড।",
        "যদি কোনো মহামারী প্রতি তিন দিনে দ্বিগুণ হয়, তবে আজ এক হাজার আক্রান্ত থেকে তিন দিন পর দুই হাজার, ছয় দিন পর চার হাজার, নয় দিন পর আট হাজার হয়।",
        "দশটি ডাবলিং পিরিয়ডে এক হাজার থেকে সংখ্যা দাঁড়ায় প্রায় দশ লাখের কাছে। মাত্র ত্রিশ দিনে এই বিশাল বৃদ্ধি সম্ভব হয় শুধু দ্বিগুণের নিয়মের কারণে।",
        "সত্তরের নিয়ম অনুযায়ী, কোনো রাশি প্রতিদিন পি শতাংশ হারে বাড়লে দ্বিগুণ হতে সময় লাগে প্রায় সত্তর ভাগ পি। দৈনিক দশ শতাংশ হারে তা প্রায় সাত দিন।",
        "সত্তরের নিয়মের পেছনের যুক্তি হলো, দুই এর প্রাকৃতিক লগারিদম প্রায় শূন্য দশমিক ছয় নয় তিন। শতকরা হার ছোট হলে সত্তর দিয়ে ভাগ করলে ভালো আন্দাজ পাওয়া যায়।",
        "দ্বিগুণের সময় হিসেবের সূত্র হলো দুই এর লগারিদম ভাগ বৃদ্ধি ধ্রুবক। বৃদ্ধি ধ্রুবক যত বাড়ে, দ্বিগুণ হতে তত কম সময় লাগে।",
        "প্রতিটি নতুন ডাবলিংয়ে যে পরিমাণ বৃদ্ধি পায়, তা অতীতের সব ধাপ মিলিয়ে যা তৈরি হয়েছিল তার চেয়েও বেশি। শেষ ডাবলিংয়ে পুরো ইতিহাসের সমান বোঝা যোগ হয়।",
        "সমান সময় ব্যবধানে দ্বিগুণীকরণের চিত্রটি খুব শিক্ষণীয়। এক, দুই, চার, আট, ষোলো—এই ধাপগুলো ষ্ট্রেট লাইনে নয়, বরং তীব্র বাঁকে এগিয়ে যায়।",
        "অর্থনীতিতে বিনিয়োগের ক্ষেত্রে সত্তরের নিয়ম বহুল ব্যবহৃত হয়। বার্ষিক সাত শতাংশ হারে টাকা দ্বিগুণ হতে প্রায় দশ বছর লাগে।",
        "জনসংখ্যা বৃদ্ধিও এই একই নিয়ম অনুসরণ করে। ছোট শতকরা হার দেখে কম মনে হলেও দীর্ঘ সময়ে তা বিপুল পরিবর্তন আনে।",
        "দ্বিগুণের সময় কমানো মানে বৃদ্ধি ধ্রুবক বাড়ানো। মহামারীতে সংস্পর্শ কমালে এই সময় বাড়ে, আর তাই কার্ভ চ্যাপ্টা হয়।",
        "সূচকীয় বৃদ্ধিতে সময়ের প্রতি ধাপ গুণক হিসেবে কাজ করে। তাই দিনের সংখ্যা এক বাড়লেই ফলাফল দ্বিগুণ হয়ে যায়—এই সরল নিয়মটি মনে রাখা যায়।",
        "আন্দাজের ক্ষেত্রে সত্তরের নিয়মের সীমাবদ্ধতাও আছে। খুব বেশি শতকরা হারে এটি কম নিখুঁত, তবে দৈনন্দিন কাজে এটি যথেষ্ট কার্যকর।",
        "দ্বিগুণের সময়ের ধারণাটি শুধু মহামারী নয়, প্রযুক্তি ও জনসংখ্যাসহ যেকোনো স্ব-ত্বরান্বিত ব্যবস্থায় প্রযোজ্য।",
        "দশটি ডাবলিং পিরিয়ড মানে দুই এর দশ ঘাত, অর্থাৎ এক হাজার গুণ। এই সহজ গুণকটি মনে রাখলে বড় সংখ্যার আকার দ্রুত বের করা যায়।",
        "ধীরে ধীরে শুরু হওয়া বৃদ্ধি যখন চোখে পড়ে, তখনই বুঝতে হয় যে অনেকগুলো ডাবলিং ইতিমধ্যে শেষ হয়ে গেছে। সতর্কতা আসে দেরিতে—এই ছিল আমাদের প্রথম পাঠের মূল কথা।",
    ],
    "sec_03_epidemic_model": [
        "মহামারী কেন সূচকীয় বৃদ্ধি অনুসরণ করে? এর উত্তর লুকিয়ে আছে একটি অতি সাধারণ পারস্পরিক ক্রিয়াশীলতায়—প্রতিটি আক্রান্ত ব্যক্তি নতুন আক্রান্ত তৈরি করে।",
        "ধরা যাক, যেকোনো মুহূর্তে মোট আক্রান্তের সংখ্যা এন। প্রতিটি আক্রান্ত ব্যক্তি প্রতিদিন ই সংখ্যক মানুষের সংস্পর্শে আসে এবং প্রতিটি সংস্পর্শে সংক্রমণের সম্ভাবনা পি।",
        "তাহলে প্রতিদিন একজন আক্রান্ত ব্যক্তি গড়ে ই গুণ পি সংখ্যক নতুন মানুষকে সংক্রামিত করে। এন জন আক্রান্ত মিলে নতুন আক্রান্তের সংখ্যা হয় ই গুণ পি গুণ এন।",
        "এই ই গুণ পি কে আমরা কে ধ্রুবক বলি। তাহলে সমীকরণ দাঁড়ায় ডি এন ভাগ ডি টি equal কে গুণ এন—অর্থাৎ পরিবর্তনের হার বর্তমান পরিমাণের সমানুপাতিক।",
        "ক্যালকুলাসের দৃষ্টিতে এটি প্রকৃতির সবচেয়ে মৌলিক সমীকরণ। কোনো রাশির হার যখন তার নিজের পরিমাণের সরাসরি সমানুপাতিক হয়, তখন তার একমাত্র পথ হয় এক্সপোনেনশিয়াল বিস্তার।",
        "এই সমীকরণের সমাধান হলো এন অফ টি equal এন শূন্য গুণ ই টু দ্য পাওয়ার কে টি। আদি পরিমাণের সাথে একটি ধ্রুবকের ঘাত গুণ—এটিই সূচকীয় ফাংশন।",
        "মৌলিক প্রজনন সংখ্যা বা আর নল মানে সংক্রামক থাকাকালীন একজন ব্যক্তি গড়ে কতজন নতুন রোগী তৈরি করে। এটি মহামারীর গতি নির্ধারণ করে।",
        "যদি আর নল একের বেশি হয়, তবে প্রতিটি প্রজন্মে রোগীর সংখ্যা গুণিতক হারে বাড়ে এবং মহামারী ছড়ায়। আর নল একের কম হলে সংক্রমণ ক্রমশ নিভে যায়।",
        "আর নল equal এক হলো মহামারীর ট্রানজিশন বিন্দু। সামান্য এক দশমিক এক হলেও রোগ ছড়ায়, আবার শূন্য দশমিক নয় এ নামালেই তা কমতে শুরু করে।",
        "এস আই আর মডেলে জনসমষ্টিকে তিন ভাগে ভাগ করা হয়—সংবেদনশীল, আক্রান্ত ও পুনরুদ্ধার। আক্রান্তরা নতুন আক্রান্ত তৈরি করে, আর এই চক্রটিই মহামারীর ইঞ্জিন।",
        "সংক্রমণ বৃক্ষের ছবিটি দেখলে বোঝা যায়, প্রতিটি নোড থেকে আর নল সংখ্যক নতুন শাখা জন্ম নিচ্ছে। শাখা আবার শাখা তৈরি করে—এভাবেই বিস্তার ঘটে।",
        "বর্তমান আক্রান্তের সংখ্যাই নতুন আক্রান্ত সৃষ্টির কারখানা। ফলে বিস্তার সর্বদাই স্ব-ত্বরান্বিত, অর্থাৎ যত বেশি আক্রান্ত তত দ্রুত নতুন আক্রান্ত।",
        "হার্ড ইমিউনিটির সূত্র হলো এক মাইনাস এক ভাগ আর নল। আর নল যত বড়, সংক্রমণ থামাতে তত বেশি শতাংশ মানুষের প্রতিরোধী হতে হবে।",
        "দুই দশমিক পাঁচ আর নল হলে প্রায় ষাট শতাংশ মানুষ প্রতিরোধী হলেই কার্যকর প্রজনন সংখ্যা একের নিচে নেমে আসে।",
        "সংস্পর্শের সংখ্যা কমালেই কে ধ্রুবক কমে, আর কে কমলে দ্বিগুণের সময় বাড়ে। এই যুক্তিটিই পরবর্তীতে কার্ভ ফ্ল্যাটেনিংয়ের ভিত্তি হবে।",
        "মডেলটি সরল হলেও এর ভবিষ্যদ্বাণী শক্তিশালী। প্রথম কয়েকদিনের তথ্য দিয়েই ভবিষ্যতের বিস্তারের আকার আন্দাজ করা যায়।",
        "প্রতিটি সংক্রমণ একটি নতুন সংক্রমণের সূচনা। এই শৃঙ্খল বুঝতে পারলেই সূচকীয় বৃদ্ধি আর আশ্চর্যের বিষয় থাকে না।",
    ],
    "sec_04_logistic_flattening": [
        "যদি সংক্রমণ চিরকাল এক্সপোনেনশিয়ালভাবে বাড়তে থাকত, তবে কয়েক মাসের মধ্যে আক্রান্তের সংখ্যা পৃথিবীর জনসংখ্যাকেও ছাড়িয়ে যেত। কিন্তু বাস্তবে তা ঘটে না—কেন?",
        "কারণ সুস্থ হয়ে অ্যান্টিবডি তৈরি হলে বা মৃত্যুতে সংক্রামিত হতে পারা মানুষের সংখ্যা কমতে থাকে। নতুন আক্রান্ত তৈরির জন্য দরকারী সংবেদনশীল মানুষ কমে গেলে বৃদ্ধি থেমে যায়।",
        "আক্রান্ত ব্যক্তি যখন কারো সংস্পর্শে আসেন, তখন সেই ব্যক্তি ইতিমধ্যে আক্রান্ত হয়ে সুস্থ থাকলে নতুন কোনো সংক্রমণ ঘটে না। এই সত্যটিই সূচকীয় বৃদ্ধিকে সীমিত করে।",
        "বেলজিয়ান গণিতবিদ পিয়েরে ফ্রাঁসোয়া ভেরহুলস্ট ১৮৩৮ সালে লজিস্টিক সমীকরণ প্রবর্তন করেন। এতে বৃদ্ধির হার এন গুণ বন্ধনী এক মাইনাস এন ভাগ কে দিয়ে লেখা হয়।",
        "এখানে কে হলো ধারণক্ষমতা বা মোট জনসংখ্যা। যখন এন কে থেকে অনেক ছোট, তখন বন্ধনীর মান প্রায় এক, ফলে বৃদ্ধি পুরোপুরি সূচকীয় থাকে।",
        "আক্রান্তের সংখ্যা যখন মোট জনসংখ্যার অর্ধেক অর্থাৎ কে ভাগ দুই বিন্দুতে পৌঁছায়, তখন বৃদ্ধির বেগ সর্বোচ্চ হয়। এই বিন্দুকে বলা হয় ইনফ্লেকশন পয়েন্ট।",
        "ইনফ্লেকশন পয়েন্টের পর বৃদ্ধির গতি ক্রমশ মন্থর হয় এবং চূড়ান্ত সীমা কে-তে গিয়ে স্থিতিশীল হয়। এই পুরো যাত্রা একটি সুন্দর এস আকৃতির বক্ররেখা তৈরি করে।",
        "প্রতিদিনের নতুন আক্রান্তের সংখ্যা বা বক্ররেখার ঢাল সর্বোচ্চ হয় ঠিক যখন এন equal কে ভাগ দুই। এটিই মহামারী মোকাবিলার সবচেয়ে সংকটময় শীর্ষক্ষণ।",
        "সূচকীয় শুরু আর সীমিত বাস্তবতার মধ্যে লজিস্টিক ফাংশন একটি নিখুঁত গাণিতিক সেতুবন্ধন রচনা করে। প্রথমে খাড়া, পরে সমতল—এই রূপই বাস্তবতার কাছে সত্য।",
        "মহামারীর সময় বিশ্বজুড়ে সবচেয়ে আলোচিত স্লোগান ছিল বক্ররেখাকে সমতল করা বা ফ্ল্যাটেন দ্য কার্ভ। এর অর্থ হলো দৈনিক নতুন আক্রান্তের শীর্ষকে নিচে নামানো।",
        "স্বাস্থ্যসেবার একটি নির্দিষ্ট ধারণক্ষমতা থাকে—হাসপাতালের আইসিইউ বেড, ভেন্টিলেটর ও চিকিৎসক দল। অনিয়ন্ত্রিত মহামারীতে খাড়া পর্বত এই সীমারেখাকে বহু গুণ ছাড়িয়ে যায়।",
        "মাস্ক পরা, সামাজিক দূরত্ব ও দ্রুত পরীক্ষার মাধ্যমে আমরা দৈনিক গড় সংস্পর্শ ই কমিয়ে দিই। এর ফলে বৃদ্ধি ধ্রুবক কে সামান্য কমে যায়।",
        "যেহেতু কে সূচকে অবস্থান করে, তাই তার সামান্য হ্রাসের ফল রৈখিকভাবে নয়, বরং বহুগুণে বেশি হয়। বক্ররেখা চ্যাপ্টা হওয়ার গাণিতিক কারণ এটিই।",
        "এক দিন আগে নেওয়া ছোট সিদ্ধান্ত দেরিতে নেওয়া বিশাল পদক্ষেপের চেয়ে শতগুণ বেশি শক্তিশালী। সূচকীয় ব্যবস্থায় সময়ের এই অপ্রতিসাম্যতা সবচেয়ে গুরুত্বপূর্ণ শিক্ষা।",
        "মহামারী তুঙ্গে ওঠার পর কুড়ি দিন চেষ্টা করলেও সেই একই সুফল অর্জন করা অসম্ভব। তাই প্রাথমিক হস্তক্ষেপই সবচেয়ে কার্যকর।",
        "খাড়া পর্বত আর সমতল সহনশীল কার্ভের তুলনাটি আমাদের দেখায় যে কম সংক্রমণ মানেই কম মৃত্যু। ধারণক্ষমতার নিচে থাকা বক্ররেখাই নিরাপদ।",
        "সামাজিক দূরত্ব শুধু সংস্পর্শ কমায় না, দ্বিগুণের সময়ও বাড়িয়ে দেয়। ফলে চিকিৎসা ব্যবস্থার ওপর চাপ কমে এবং অনেক জীবন বাঁচে।",
        "আজ আমরা দেখলাম রৈখিক বিভ্রম, দ্বিগুণের সময়, সংক্রমণের ডিফারেনশিয়াল মডেল, লজিস্টিক বক্ররেখা ও ফ্ল্যাটেনিং—এই পাঁচটি ধারণা একসাথে মিলে মহামারীর পুরো গল্প বলে দেয়।",
    ],
}
DEFAULT_EXPANSIONS = [
    "এই ধারণাটি নিজের ভাষায় একবার বলে দেখলে বিষয়টি আরও পরিচ্ছন্ন হবে।",
    "লক্ষ্য করুন, বৃদ্ধির এই অনুপাতই আমাদের আসল উত্তরের দিকে নিয়ে যায়।",
    "এখানে যুক্তিটি আবার মনে করিয়ে দিই, কারণ পরের ধাপে এটি বারবার কাজে লাগবে।",
]


# ---------------------------------------------------------------------------
# Robust subprocess / TTS helpers (identical to the proven pipeline).
# ---------------------------------------------------------------------------
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


def strip_math(text):
    """Remove LaTeX math / markup from a lesson paragraph for natural TTS."""
    t = re.sub(r"\$\$[^\$]*\$\$", " ", text)
    t = re.sub(r"\$[^\$]*\$", " ", t)
    t = re.sub(r"\\(?:frac|sqrt|left|right|implies|qquad|times|pm|neq|text)\b", " ", t)
    t = re.sub(r"[\\\{\}\[\]#*_^~]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


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


def split_chunks(text, limit=CHARS_PER_CHUNK):
    """Split on Bangla sentence boundary '।' into chunks <= limit chars."""
    sents = [s.strip() for s in text.split("।") if s.strip()]
    chunks, cur = [], ""
    for s in sents:
        piece = s + "।"
        if len(cur) + len(piece) > limit and cur:
            chunks.append(cur.strip())
            cur = piece
        else:
            cur += " " + piece if cur else piece
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


async def synth_cue(text, raw):
    """Synthesize a (possibly very long) cue as chunked MP3s then concatenate."""
    for p in RAW_DIR.glob(f"part_{raw.stem}_*.mp3"):
        purge(p)
    chunks = split_chunks(sanitize(text))
    made = []
    for j, ch in enumerate(chunks):
        pp = RAW_DIR / f"part_{raw.stem}_{j:03d}.mp3"
        if not await synth(ch, pp, force=True):
            return False
        made.append(pp)
    if not made:
        return False
    lf = RAW_DIR / f"partlist_{raw.stem}.txt"
    with open(lf, "w", encoding="utf-8") as f:
        for x in made:
            f.write(f"file '{x.as_posix()}'\n")
    purge(raw)
    run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{raw}" > NUL 2>&1')
    return valid(raw)


# ---------------------------------------------------------------------------
# Cue loading. Manifest cue texts are the dubbing script verbatim; the LEGACY
# section names are replaced by their `alias` key (alias-deduped).
# ---------------------------------------------------------------------------
def load_manifest_cues():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out, seen = [], set()
    for _key, sec in data.get("sections", {}).items():
        sid = sec.get("alias") or sec.get("section_id") or _key
        if sid in seen:
            continue
        seen.add(sid)
        for c in sec.get("cues", []):
            text = c.get("text")
            if not text:
                continue
            out.append({
                "text": text,
                "dur_ms": float(c.get("duration_ms", 0)),
                "section": sid,
            })
    return out, f"audio_manifest:{MANIFEST.name} (alias-deduped)"


def load_source_cues():
    out, desc = load_manifest_cues()
    if not out:
        raise SystemExit("No manifest cues found - cannot dub")
    # Sanity: the manifest is the script; lesson_02.json is topical context only.
    if LESSON_JSON.exists():
        json.loads(LESSON_JSON.read_text(encoding="utf-8"))  # validate readable
    return out, desc


def load_cues(vend, source_cues):
    """Lay authored cues out cumulatively, then scale to span the full video."""
    authored_total = sum(c["dur_ms"] for c in source_cues) + INTER_CUE_PAUSE_MS * (len(source_cues) - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    scale = usable / (authored_total / 1000.0) if authored_total > 0 else 1.0
    cues = []
    cursor_ms = 0.0
    for i, c in enumerate(source_cues):
        start = LEAD_IN_SEC + (cursor_ms / 1000.0) * scale
        dur = (c["dur_ms"] / 1000.0) * scale
        cues.append({
            "id": i + 1,
            "start": round(start, 3),
            "end": round(start + dur, 3),
            "duration": round(dur, 3),
            "bn": c["text"],
            "section": c["section"],
            "manifest_dur_ms": c["dur_ms"],
        })
        cursor_ms += c["dur_ms"] + INTER_CUE_PAUSE_MS
    return cues, scale


async def synth_all(cues):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, c in enumerate(cues):
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        ok = await synth_cue(sanitize(c["bn"]), raw)
        if not ok:
            failed.append(c["id"])
            print(f"  WARNING cue {c['id']} failed after every fallback", flush=True)
        print(f"  TTS {i+1}/{len(cues)} (chars={len(c['bn'])})", flush=True)
    return failed


def predicted_fill(natural, target):
    """Fill with tempo floor 0.82: min(1, natural/(0.82*target))."""
    if target <= 0 or natural <= 0:
        return 0.0
    return min(1.0, natural / (MIN_TEMPO * target))


async def expand_cue_to_target(cue, target, expanded_log):
    """Append section-aware pedagogical sentences until natural >= target."""
    cid = cue["id"]
    raw = RAW_DIR / f"raw_{cid:03d}.mp3"
    pool = EXPANSION_POOL.get(cue["section"], DEFAULT_EXPANSIONS)
    text = sanitize(cue["bn"])
    nat = duration(raw)
    before = nat
    rounds = 0
    while nat < target and rounds < 24:
        rate = nat / max(len(text), 1) if nat > 0 else 1.0 / 14.5
        need_s = target - nat
        need_chars = max(160, int(need_s / max(rate, 0.02)))
        n = max(1, min(4, int(np.ceil(need_chars / 170.0))))
        offset = len(text)
        add = " ".join(pool[(offset + j) % len(pool)] for j in range(n))
        new = sanitize(text + " " + add)
        if not await synth_cue(new, raw):
            break
        text = new
        nat = duration(raw)
        rounds += 1
    if rounds:
        cue["bn"] = text
        expanded_log.append({
            "id": cid, "section": cue["section"], "round": "target_scale",
            "sentences_rounds": rounds, "final_chars": len(text),
            "natural_before": round(before, 3), "natural_after": round(nat, 3),
            "target": round(target, 3),
        })
    return nat


async def expand_to_target_scale(cues, vend, expanded):
    """Expand cues until sum(naturals) is large enough that the recomputed
    timeline scale <= TARGET_SCALE (=> rendered fill ~= 1/(0.82*scale) >= 0.85).
    Per-cue targets are proportional to the manifest cue durations so the
    intended section pacing is preserved.
    """
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    total_target = usable / TARGET_SCALE
    sum_dur = sum(c["manifest_dur_ms"] for c in cues) or 1.0
    targets = {c["id"]: total_target * (c["manifest_dur_ms"] / sum_dur) for c in cues}
    for c in cues:
        nat = duration(RAW_DIR / f"raw_{c['id']:03d}.mp3")
        if nat <= 0:
            nat = float(c["duration"]) or 1.0
        if nat < targets[c["id"]] * 0.98:
            await expand_cue_to_target(c, targets[c["id"]], expanded)
    naturals = [duration(RAW_DIR / f"raw_{c['id']:03d}.mp3") for c in cues]
    return sum(naturals), total_target


# ---------------------------------------------------------------------------
# Render / measure helpers (identical to the proven pipeline).
# ---------------------------------------------------------------------------
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


def internal_gap_s(arr, sr=SR, thr=ACTIVE_THRESHOLD):
    if arr.size == 0:
        return 0.0
    active = np.flatnonzero(np.abs(arr) > thr)
    if active.size < 2:
        return 0.0
    gaps = np.diff(active)
    if gaps.size == 0:
        return 0.0
    return float(gaps.max()) / sr


LAST_START = 0.0
VIDEO_END = 0.0
LAST_ID = None


def make_cue(raw, target, out, cid):
    """atempo-fit into the window with floor 0.82; PAD only, NEVER truncate."""
    natural = duration(raw)
    if natural <= 0:
        natural = target
    if cid == LAST_ID:
        target = min(target, VIDEO_END - LAST_START - 0.10)
    tempo = max(MIN_TEMPO, min(MAX_TEMPO, natural / target))
    tmp = out.with_suffix(".fit.wav")
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)
    fit_samples = len(arr)
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
    return arr, tempo, natural, target, fit_samples


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


def recompute_layout_from_naturals(cues, vend):
    """Re-derive timeline scale from SUM OF RENDERED NATURAL SPEECH (not manifest).

    Windows are made proportional to each cue's measured TTS duration so that
    sum(windows) == usable timeline.  With the 0.82 tempo floor the resulting
    waveform fill is 1/(0.82*scale); scale <= 1.695 guarantees >= 0.72 fill.
    """
    naturals = []
    for c in cues:
        nat = duration(RAW_DIR / f"raw_{c['id']:03d}.mp3")
        if nat <= 0:
            nat = float(c["duration"]) or 1.0
        naturals.append(nat)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    total = sum(naturals)
    scale = usable / total if total > 0 else 1.0
    cursor = 0.0
    for c, nat in zip(cues, naturals):
        window = nat * scale
        c["start"] = round(LEAD_IN_SEC + cursor, 3)
        c["duration"] = round(window, 3)
        c["end"] = round(c["start"] + window, 3)
        cursor += window
    return scale, naturals


async def expand_cue_more(cue, extra_s, expanded_log):
    """Append more section-aware pedagogical sentences to a weak cue."""
    cid = cue["id"]
    raw = RAW_DIR / f"raw_{cid:03d}.mp3"
    pool = EXPANSION_POOL.get(cue["section"], DEFAULT_EXPANSIONS)
    text = sanitize(cue["bn"])
    nat = duration(raw)
    rate = nat / max(len(text), 1)
    need_chars = max(300, int(extra_s / max(rate, 0.01)))
    n = max(1, min(60, int(np.ceil(need_chars / 200.0))))
    offset = len(text)
    added_text = " ".join(pool[(offset + j) % len(pool)] for j in range(n))
    new_text = sanitize(text + " " + added_text)
    print(f"  extra-expand cue {cid}: +{n} sent (extra_s={extra_s:.1f})", flush=True)
    if await synth_cue(new_text, raw):
        cue["bn"] = new_text
        expanded_log.append({
            "id": cid, "section": cue["section"], "round": "quality_gate",
            "sentences_added": n, "final_chars": len(new_text),
            "natural_before": round(nat, 3), "natural_after": round(duration(raw), 3),
        })
        return duration(raw)
    return nat


def render_canvas(cues, vend, expanded_ids):
    """Absolute-sample placement on a FULL-length canvas (pad-only, no SFX)."""
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    CHUNK = 1_000_000
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed, overrun, last_cue_end = [], 0, 0.0
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            print(f"  SKIP cue {cid} (no audio)", flush=True)
            continue
        arr, tempo, natural, target, fit_samples = make_cue(
            raw, float(c["duration"]), CUE_DIR / f"cue_{cid:03d}.wav", cid)
        gap_s = internal_gap_s(arr[:fit_samples]) if fit_samples else 0.0
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
        expected_ms = round(float(c["start"]) * 1000, 2)
        actual_ms = round(start_sample / SR * 1000, 2)
        window_samples = int(round(target * SR))
        fill = min(1.0, fit_samples / window_samples) if window_samples > 0 else 0.0
        placed.append({
            "id": cid,
            "section": c["section"],
            "expected_start_ms": expected_ms,
            "actual_start_ms": actual_ms,
            "drift_ms": round(actual_ms - expected_ms, 6),
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3),
            "target_sec": round(target, 3),
            "fit_samples": fit_samples,
            "window_samples": window_samples,
            "fill": round(fill, 4),
            "max_internal_gap_s": round(gap_s, 4),
            "placed_samples": placed_len,
            "expanded": cid in expanded_ids,
        })
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
    return canvas, placed, overrun, last_cue_end, CHUNK


def fill_metrics(placed):
    fills = [x["fill"] for x in placed]
    median = round(statistics.median(fills), 4) if fills else 0.0
    gap = round(max((x["max_internal_gap_s"] for x in placed), default=0.0), 4)
    return median, gap


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    src = ORIGINAL_VIDEO
    if not src.exists():
        alts = sorted(ORIGINAL_DIR.glob("full_original.*"))
        if alts:
            src = alts[0]
    if not src.exists():
        raise SystemExit(f"ORIGINAL VIDEO NOT FOUND: {ORIGINAL_VIDEO}")

    vend = video_duration(src)
    VIDEO_END = vend
    source_cues, source_desc = load_source_cues()
    cues, initial_scale = load_cues(vend, source_cues)
    print(f"video={src} duration={vend:.3f}s cues={len(cues)} "
          f"source={source_desc} initial_manifest_scale={initial_scale:.4f}", flush=True)

    print("[1/7] TTS (clean, no SFX) ...", flush=True)
    failed = await synth_all(cues)

    print("[2/7] Expand short cues to target scale (IMPROVED_DUB_FILL_POLICY) ...", flush=True)
    expanded = []
    nat_sum, target_sum = await expand_to_target_scale(cues, vend, expanded)
    print(f"  natural_total={nat_sum:.1f}s (target>={target_sum:.1f}s) "
          f"expanded {len(expanded)} cues", flush=True)

    print("[3/7] Recompute timeline scale from RENDERED natural speech ...", flush=True)
    scale, naturals = recompute_layout_from_naturals(cues, vend)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"  natural_total={sum(naturals):.1f}s -> scale={scale:.4f} "
          f"(was {initial_scale:.4f} from manifest)", flush=True)
    print("  windows:", ", ".join(f"{c['id']}={c['duration']:.1f}s" for c in cues), flush=True)

    print("[4/7] Absolute placement + quality gate (start*44100, pad-only) ...", flush=True)
    render_round = 0
    while True:
        render_round += 1
        canvas, placed, overrun, last_cue_end, CHUNK = render_canvas(
            cues, vend, [x["id"] for x in expanded])
        median_fill, max_internal_gap = fill_metrics(placed)
        print(f"  render round {render_round}: median_fill={median_fill} "
              f"max_internal_gap={max_internal_gap}s "
              f"fills={[x['fill'] for x in placed]}", flush=True)
        if (median_fill >= 0.72 and max_internal_gap <= 1.5) or render_round >= 4:
            break
        weak = sorted(placed, key=lambda x: x["fill"])[:3]
        for w in weak:
            cue = next(c for c in cues if c["id"] == w["id"])
            deficit = max(45.0, (0.88 - w["fill"]) * w["target_sec"] * 1.8)
            await expand_cue_more(cue, deficit, expanded)
        scale, naturals = recompute_layout_from_naturals(cues, vend)
        LAST_START = float(cues[-1]["start"])

    print("[5/7] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    gate_ok = median_fill >= 0.72 and max_internal_gap <= 1.5
    report = {
        "experiment": "clean_timesync_v2 (lockdown_math_lesson_02 full-length, improved fill, scale recomputed from rendered speech)",
        "lesson": LESSON,
        "course": "lockdown_math",
        "video_id": VIDEO_ID,
        "title": "Exponential growth and epidemics",
        "script_source": source_desc,
        "source_context": "web_platform/data/lockdown_math/lesson_02.json (topical context; wrong duration field ignored)",
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": "absolute sample offset (start*44100); atempo fit floor 0.82; pad only; no truncation",
        "sfx": "NONE - clean speech only",
        "voice": VOICE,
        "min_tempo": MIN_TEMPO,
        "max_tempo": MAX_TEMPO,
        "target_scale": TARGET_SCALE,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "timeline_scale": round(scale, 6),
        "timeline_scale_initial_manifest": round(initial_scale, 6),
        "scale_recomputed_from_rendered_speech": True,
        "usable_timeline_sec": round(vend - LEAD_IN_SEC - TAIL_MARGIN_SEC, 3),
        "rendered_natural_speech_total_sec": round(sum(naturals), 3),
        "render_rounds": render_round,
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "fill_policy": {
            "atempo_floor": MIN_TEMPO,
            "expand_target_fill": EXPAND_TARGET_FILL,
            "median_fill": median_fill,
            "median_fill_target": 0.72,
            "median_fill_ok": median_fill >= 0.72,
            "max_internal_gap_s": max_internal_gap,
            "max_internal_gap_target": 1.5,
            "max_internal_gap_ok": max_internal_gap <= 1.5,
        },
        "quality_gate": {
            "median_fill_ok": median_fill >= 0.72,
            "max_internal_gap_ok": max_internal_gap <= 1.5,
            "passed": gate_ok,
        },
        "median_fill": median_fill,
        "max_internal_gap_s": max_internal_gap,
        "expanded_cues": expanded,
        "cues": placed,
    }

    print("[6/7] Mux with FULL original video (video copy) ...", flush=True)
    run(f'ffmpeg -y -i "{src}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    report["output_video"] = str(OUT_VIDEO)
    odur = duration(OUT_VIDEO)
    report["output_duration_sec"] = round(odur, 3)
    report["output_size_bytes"] = OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0
    report["original_duration_sec"] = round(vend, 3)
    report["duration_matches_original"] = abs(odur - vend) <= 2.0
    try:
        probe = json.loads(run(f'ffprobe -v error -show_entries stream=index,codec_type,codec_name,width,height,r_frame_rate '
                               f'-of json "{OUT_VIDEO}"'))
        report["output_streams"] = probe.get("streams", [])
    except Exception as e:
        report["output_streams_error"] = str(e)

    print("[7/7] Lightweight volumedetect ...", flush=True)
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"output_duration={report['output_duration_sec']}s (original={vend:.3f}s) "
          f"size={report['output_size_bytes']}", flush=True)
    print(f"streams={[(s.get('codec_type'),s.get('codec_name')) for s in report.get('output_streams',[])]}", flush=True)
    print(f"scale={scale:.4f} (recomputed from rendered speech) rounds={render_round}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap={max_internal_gap}s "
          f"expanded={len(expanded)} gate_ok={gate_ok}", flush=True)
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
