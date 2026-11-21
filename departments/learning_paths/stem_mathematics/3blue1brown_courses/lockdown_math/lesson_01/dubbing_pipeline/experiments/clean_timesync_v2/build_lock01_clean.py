"""
EXPERIMENT - Full-length clean absolute-sample Bengali dub
(Lockdown Math, Lesson 01 - "The quadratic formula, explained geometrically")

Adapted verbatim from the proven clean_timesync_v2 pipeline:
    probability/lesson_01/dubbing_pipeline/experiments/clean_timesync_v2/build_prob01_clean.py

Guarantees (identical to the proven pipeline, plus IMPROVED_DUB_FILL_POLICY.md):
   1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
      half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
   2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
   3. IMPROVED FILL: atempo floor 0.82 (gentle slowdown), ceiling 2.2. Pad only,
      NEVER truncate. NO SFX: clean speech only.
   4. EXPANSION FIRST: the manifest has only 5 h2 cues (~20 s total) for a
      ~65-minute video, so each cue is expanded HEAVILY with section-aware
      pedagogical Bengali sentences (quadratic derivation, completing the
      square, parabola symmetry, Po-Shen Loh) until predicted fill >= 0.85.
      Section paragraphs from lesson_01.json are folded into the base script.
   5. Fill metrics (per-cue fill, median_fill, max_internal_gap_s) are measured
      from the rendered waveform and written into verification.json.
   6. Canvas padded to the FULL original video duration so -shortest can never
      trim video frames. Final cue is capped to end inside the video.
   7. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
   8. Lightweight volumedetect (-vn -nostats, log to FILE) on intro and final.

Cue source (read-only; teacher audio / manifests are NEVER modified):
   1. web_platform/data/lockdown_math/lesson_01.json -> audio_manifest_url
      (assets/audio/lockdown_math/lesson_01/manifest.json). Alias-keyed
      duplicate sections are de-duplicated by section_id.
   2. Lesson section paragraphs are appended to each cue for real teaching
      content (LaTeX math removed, sanitized for TTS).

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
BASE = EXP.parent.parent                        # .../lockdown_math/lesson_01/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "lockdown_math" / "lesson_01.json"

# Original source: yt-dlp output (verified with ffprobe before use).
ORIGINAL_DIR = WEB / "media_vault" / "lockdown_math" / "lesson_01" / "original_source"
ORIGINAL_VIDEO = ORIGINAL_DIR / "full_original.mp4"

OUT_VIDEO = WEB / "media_vault" / "lockdown_math" / "lesson_01" / "experiments" / "3b1b_lockdown_01_full_dubbed.mp4"

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
VIDEO_ID = "MHXO86wKeDY"             # FIXED from the wrong id in the data file
LESSON = "lesson_01"

# Silence margins: keep 0-2 s and the final 2 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Expansion policy constants.
EXPAND_TRIGGER_RATIO = 0.62          # expand when natural < 62% of window
EXPAND_TARGET_FILL = 0.85            # aim well above the 0.72 median floor (headroom)
MAX_APPENDED_SENTENCES = 160         # lockdown L01 needs HEAVY expansion
ACTIVE_THRESHOLD = 0.015
CHARS_PER_CHUNK = 1700               # chunk long TTS text for robustness


# ---------------------------------------------------------------------------
# Section-aware pedagogical sentences. Cycled (never repeated verbatim inside
# a single add-call); chosen so additions teach real mathematics.
# ---------------------------------------------------------------------------
EXPANSION_POOL = {
    "sec-01-why-memorize": [
        "স্কুলের পাঠ্যপুস্তকে দ্বিঘাত সূত্রটি একটিমাত্র লাইনে লেখা থাকে, আর ছাত্রদের বলা হয় এটি কণ্ঠস্থ করো। কিন্তু এই মুখস্থ করার অভ্যাস গণিতের প্রতি ভয় জন্মায়, কারণ কোনো পরিবর্তনেই সূত্রটি নিজের মতো করে ভাবার সুযোগ থাকে না।",
        "অধিকাংশ শিক্ষার্থী জানে না কেন রুটের নিচে বি বর্গ বিয়োগ চার এ সি আসে, কেন নিচে দুই এ এবং শুরুতে ঋণাত্মক বি বসে। এই প্রশ্নগুলোর উত্তর কোনো বইতে দেওয়া হয় না, অথচ এগুলোই সূত্রটির প্রাণ।",
        "আজ থেকে প্রায় চার হাজার বছর আগে যখন চলকের আবিষ্কার হয়নি, তখনও প্রাচীন ব্যবিলন ও গ্রিক গণিতবিদরা দ্বিঘাত সমীকরণ নিখুঁতভাবে সমাধান করতেন। তাদের একমাত্র হাতিয়ার ছিল মাটি বা প্যাপিরাসে আঁকা বর্গক্ষেত্র ও আয়তক্ষেত্র।",
        "তারা কোনো সূত্র মুখস্থ করেননি; বরং ক্ষেত্রফল দুইটি রূপে প্রকাশ করে একটিকে অন্যটির সাথে মেলাতেন। আজ আমরা সেই একই পদ্ধতি আধুনিক ভাষায় পুনরাবিষ্কার করব, যাতে সূত্রটি মুখস্থ না করলেও মনে থাকে।",
        "ইংরেজি কোয়াড্রাটিক শব্দটি এসেছে ল্যাটিন কোয়াড্রাটাম বা কোয়াড্রাটাস থেকে, যার অর্থ বর্গক্ষেত্র।ুতরাং দ্বিঘাত সমীকরণ কোনো শুষ্ক যান্ত্রিক বীজগণিত নয়, বরং স্থান ও ক্ষেত্রফলের এক জীবন্ত জ্যামিতিক গল্প।",
        "যখনই কোনো পদের ওপর ঘাত দুই থাকে, তখন তাকে বর্গ বলা হয়, কারণ তা বাস্তবিক অর্থেই এক্স গুণ এক্স বাহুবিশিষ্ট একটি জ্যামিতিক বর্গক্ষেত্র। এই সরল পর্যবেক্ষণটিই পুরো অধ্যায়ের চাবিকাঠি।",
        "গ্রান্ট স্যান্ডারসন বলেন, যদি গণিতকে কেবল বিমূ rt প্রতীকের নিয়মকানুন হিসেবে মুখস্থ করো, তবে সামান্য পরিবর্তনেই হারিয়ে যাবে। কিন্তু পেছনের জ্যামিতিক চিত্রটি স্পষ্ট দেখতে পেলে সূত্রটি ভুলে যাওয়া অসম্ভব হয়ে দাঁড়ায়।",
        "একটি আয়তক্ষেত্রের ক্ষেত্রফল যেভাবে দৈর্ঘ্য ও প্রস্থের গুণফল, ঠিক সেভাবেই বর্গক্ষেত্রের ক্ষেত্রফল তার বাহুর বর্গ। দ্বিঘাত সমীকরণে এক্স বর্গ আর বি গুণ এক্স—এই দুটি পদই আসলে দুটি জ্যামিতিক আকৃতির ক্ষেত্রফল।",
        "আমাদের লক্ষ্য হলো একটি অসম্পূর্ণ বর্গকে পূর্ণ করা। যখনই কোণায় ছোট্ট একটি বর্গ যোগ করা হয়, পুরো ছবিটি হঠাৎ করে নিখুঁত হয়ে যায়—বীজগণিতে এই ঘটনাটিই বলা হয় বর্গ পূরণ।",
        "মুখস্থ সূত্রের ক্ষেত্রে একটি ছোট ভুল, যেমন চিহ্নের গাফিলতি, পুরো উত্তর নষ্ট করে দেয়। কিন্তু জ্যামিতিক চিত্রের ক্ষেত্রে আপনি নিজেই দেখতে পারেন কোথায় ভুল হয়েছে এবং কীভাবে তা ঠিক করতে হবে।",
        "প্রাচীন গণিতবিদরা প্রথমে সমীকরণটিকে একটি ক্ষেত্রফলের গল্পে রূপ দিতেন, তারপর সেই ক্ষেত্রফলকে নতুন করে সাজিয়ে সমাধান বের করতেন। আজকের সূত্র আসলে সেই সাজানোরই একটি সংক্ষিপ্ত লিখিত রূপ মাত্র।",
        "অনেক শিক্ষার্থী ভাবে বীজগণিত ও জ্যামিতি দুটি আলাদা বিষয়। কিন্তু দ্বিঘাত সমীকরণ আমাদের দেখিয়ে দেয় যে এই দুটি একই সত্যের দুটি ভাষা—একটি সাহায্য করে হিসেব করতে, অন্যটি সাহায্য করে বুঝতে।",
        "যখন আপনি এক্স বর্গকে একটি বর্গক্ষেত্র হিসেবে কল্পনা করেন, তখন সমীকরণের প্রতিটি পদ একটি নির্দিষ্ট আকৃতি ধারণ করে। এই দৃষ্টিভঙ্গি পরীক্ষার চাপে সূত্র ভুলে গেলেও আপনাকে আবার হিসেব বের করতে সাহায্য করবে।",
        "আজকের পাঠে আমরা কেবল উত্তর বের করব না, বরং জিজ্ঞাসা করব কেন উত্তরটি এই রূপ নেয়। এই কৌতূহলই গণিতকে আনন্দদায়ক করে তোলে এবং পরবর্তী প্রতিটি ধাপে আপনার আত্মবিশ্বাস বাড়িয়ে দেয়।",
        "দ্বিঘাত সমীকরণের প্রমিত রূপ হলো এ এক্স বর্গ plus বি এক্স plus সি equal শূন্য, যেখানে এ শূন্য নয়। এ শূন্য হলে সমীকরণটি রৈখিক হয়ে যায় এবং তার কোনো বক্ররেখা বা শীর্ষবিন্দু থাকে না।",
        "এই প্রথম অধ্যায়ে আমরা দেখব কীভাবে একটি আয়তক্ষেত্রকে দুই টুকরো করে বর্গের পাশে সাজালে অবধারিতভাবে বিশ্বখ্যাত দ্বিঘাত সূত্রটি জন্ম নেয়। এটি কোনো যাদু নয়, বরং সহজ ক্ষেত্রফলের হিসাব মাত্র।",
        "আপনি যদি কখনো ভেবে থাকেন যে গণিত কেবল কাগজের ওপর লেখা প্রতীক, তবে এই পাঠ আপনার দৃষ্টিভঙ্গি বদলে দেবে। প্রতিটি প্রতীকের পেছনে একটি চিত্র আছে আর সেই চিত্রটিই আসল গণিত।",
        "চলুন ধাপে ধাপে এগোনো যাক। প্রথমে বুঝব কেন মুখস্থ করা ক্ষতিকর, তারপর দেখব কীভাবে জ্যামিতি আমাদের নিজেদের সূত্রটি আবিষ্কার করতে শেখায়।",
        "গণিতের ইতিহাসে প্রতিটি বড় আবিষ্কারের পেছনে একটি সরল চিত্র ছিল। দ্বিঘাত সমীকরণের ক্ষেত্রে সেই চিত্র হলো অসম্পূর্ণ বর্গ—একটি কোণা যেটি পূরণ করলেই সবকিছু পরিষ্কার হয়ে যায়।",
        "যখন সূত্রটি মুখস্থ করি, তখন আমরা শুধু ফলাফলটি জানি; কিন্তু যখন এর উৎপত্তি বুঝি, তখন আমরা সূত্রটির মালিক হয়ে যাই। এই পার্থক্যটিই একজন শিক্ষার্থীকে একজন গণিতবিদে রূপ দেয়।",
        "আজকের আলোচনায় কোনো কিছু আপনাকে কেবল বিশ্বাস করতে বলা হবে না। প্রতিটি ধাপ আপনি নিজের চোখে দেখতে পারবেন, নিজের হিসেবে যাচাই করতে পারবেন এবং নিজের ভাষায় বলে দিতে পারবেন।",
        "আমরা এমন এক যাত্রায় বের হচ্ছি যার শেষে দ্বিঘাত সূত্রটি আর কোনো গোপন রহস্য থাকবে না। এটি হবে আপনার নিজের আবিষ্কৃত একটি সহজ ও স্বাভাবিক সত্য।",
        "মনে রাখবেন, ভুল করা গণিতের অংশ; কিন্তু বুঝ না করে মুখস্থ করা ভুলের চেয়েও খারাপ। তাই আজ আমরা বুঝে শিখব, যাতে ভুল হলেও নিজেরাই ঠিক করে নিতে পারি।",
        "প্রতিটি নতুন ধারণার সাথে আমরা একটি ছোট উদাহরণও দেখব, যাতে বিমূর্ত কথাগুলো চোখের সামনে জীবন্ত হয়ে ওঠে। এই অভ্যাস গণিত শেখার সবচেয়ে কার্যকর উপায়।",
        "আপনি যখন পরবর্তীতে কোনো দ্বিঘাত সমীকরণের মুখোমুখি হবেন, তখন মুখস্থ সূত্র খোঁজার বদলে মনে পড়বে আজকের সেই চিত্র—আয়তক্ষেত্র, অর্ধেক করা টুকরো আর পূরণ করা কোণা।",
    ],
    "sec-02-completing-the-square": [
        "চলুন একটি সহজ সমীকরণ বিবেচনা করি: এক্স বর্গ plus ছয় এক্স equal ষোল। এর জ্যামিতিক অর্থ হলো আমাদের কাছে এক্স গুণ এক্স মাপের একটি বর্গ আছে, যার ক্ষেত্রফল এক্স বর্গ, এবং এক্স গুণ ছয় মাপের একটি আয়তক্ষেত্র আছে, যার ক্ষেত্রফল ছয় এক্স।",
        "দুটি ক্ষেত্রফল যোগ করলে মোট ক্ষেত্রফল দাঁড়ায় ষোল একক। অর্থাৎ আমাদের একটি বর্গ ও একটি আয়তক্ষেত্র নিয়ে এমনভাবে সাজতে হবে যাতে মোট ক্ষেত্রফল ঠিক ষোল হয়—এটিই সমীকরণটির জ্যামিতিক রূপ।",
        "এখন একটি চমৎকার বুদ্ধিমত্তার পরিচয় দেওয়া যাক। আয়তক্ষেত্রটিকে যদি মাঝখান বরাবর কেটে সমান দুটি টুকরো করি, তবে প্রতিটি টুকরোর মাপ হবে এক্স গুণ তিন, কারণ ছয় ভাগ দুই equal তিন।",
        "এবার একটি টুকরো মূল বর্গের ডানপাশে এবং অপর টুকরোটি নিচের পাশে বসাই। লক্ষ্য করুন, ছবিটি প্রায় একটি নতুন বৃহৎ বর্গক্ষেত্রে পরিণত হয়েছে—কেবল নিচের ডান কোণাটিতে একটি ছোট ঘাটতি রয়ে গেছে।",
        "সেই খালি কোণাটির মাপ হবে তিন গুণ তিন, অর্থাৎ তার ক্ষেত্রফল নয় একক। এই কোণাটি পূরণ করলেই পুরো আকৃতিটি একটি নিখুঁত এক্স plus তিন বাহুবিশিষ্ট বর্গক্ষেত্রে পরিণত হয়।",
        "যেহেতু কোণায় নয় একক ক্ষেত্রফল যোগ করা হয়েছে, তাই সমতার ভারসাম্য বজায় রাখতে ডানপাশেও নয় যোগ করতে হবে। তখন পাই এক্স plus তিনের বর্গ equal ষোল plus নয় equal পঁচিশ।",
        "উভয় পাশে বর্গমূল নিলেই নিমেষে বেরিয়ে আসে এক্স plus তিন equal প্লাস মাইনাস পাঁচ, অর্থাৎ এক্স equal দুই অথবা এক্স equal ঋণাত্মক আট। কোনো মুখস্থ সূত্র ছাড়াই কেবল কোণা পূরণের জ্যামিতি দিয়ে সমাধান সম্পন্ন হলো।",
        "কেন সহগকে দুই দিয়ে ভাগ করা হয়? একটি বর্গক্ষেত্রের দুটি মুক্ত সংলগ্ন বাহু থাকে—ডানপাশে ও নিচে। তাই অতিরিক্ত আয়তক্ষেত্রটিকে সমদ্বিখণ্ডিত করে দুই বাহুর সাথে জুড়তে হয়, আর এর জন্যই সূত্রে সর্বদা বি ভাগ দুই আসে।",
        "বর্গ পূরণের মূল জ্যামিতিক বীজগণিত হলো: এক্স বর্গ plus বি এক্স plus বি ভাগ দুইয়ের বর্গ equal এক্স plus বি ভাগ দুইয়ের বর্গ। বামপাশটি একটি পূর্ণবর্গ, যা আমাদের পরবর্তী ধাপে কাজে লাগবে।",
        "এই পদ্ধতি আসলে খুব পুরনো। প্রাচীন ব্যবিলনীয় গণিতবিদরা ঠিক এইভাবেই আয়তক্ষেত্র কেটে বর্গের পাশে সাজিয়ে দ্বিঘাত সমীকরণ সমাধান করতেন, তবে তাদের ভাষা ছিল চিত্রের ভাষা, প্রতীকের নয়।",
        "যখন আপনি আয়তক্ষেত্রটিকে দুই ভাগ করেন, তখন প্রতিটি অর্ধেকই আসলে সেই অজানা সংখ্যার সাথে সহগের অর্ধেকের গুণফল। এই অর্ধেকটিই পরে বর্গের নতুন বাহুতে রূপ নেয়।",
        "কোণার ছোট বর্গটি কত বড় হবে তা নির্ভর করে অর্ধেক সহগের ওপর। অর্ধেক সহগ যত বড়, কোণার ঘাটতিও তত বড়—এই সম্পর্কটি মনে রাখলে ভুল করে কোণার ক্ষেত্রফল বসানো যাবে না।",
        "অনেক শিক্ষার্থী ভুল করে পুরো বি কে বর্গ করে কোণায় যোগ করে দেয়। কিন্তু চিত্রটি দেখলেই বোঝা যায় কোণার বাহু হলো বি ভাগ দুই, তাই কোণার ক্ষেত্রফল হবে বি ভাগ দুইয়ের বর্গ, বি বর্গ নয়।",
        "সমতার উভয় পাশে একই পরিমাণ যোগ করলে সমতা অক্ষত থাকে—এটি বীজগণিতের মূল নিয়ম। বর্গ পূরণে ঠিক এই নিয়মটিই ব্যবহার করা হয়, তাই ডানপাশেও একই ক্ষেত্রফল যোগ করা হয়।",
        "বর্গমূল নেওয়ার সময় আমরা প্লাস ও মাইনাস দুটি মানই গ্রহণ করি, কারণ দুটি সংখ্যার বর্গ একই হতে পারে। এই দুইটি মানই মূলত প্যারাবোলার দুটি মূলের সাথে মিলে যায়—পরে আমরা তা বিস্তারিত দেখব।",
        "ঋণাত্মক আট আর দুই—এই দুটি উত্তরের গড় হলো ঋণাত্মক তিন, ঠিক যেটি আমাদের নতুন বর্গের কেন্দ্র। এই পর্যবেক্ষণটি পরবর্তী অধ্যায়ে প্রতিসাম্যের সাথে যুক্ত হয়ে যাবে।",
        "বর্গ পূরণের সৌন্দর্য হলো এটি কোনো নতুন তথ্য যোগ করে না, শুধু পুরনো তথ্যকে নতুন করে সাজায়। একই ক্ষেত্রফলকে অন্য রূপে দেখিয়েই আমরা সমাধান বের করে নিই।",
        " যদি আপনি কোণা পূরণের ধাপটি মনে রাখেন, তবে যেকোনো দ্বিঘাত সমীকরণে কী যোগ করতে হবে তা আপনি নিজেই বলে দিতে পারবেন। এটি কোনো কৃত্রিম কৌশল নয়, বরং স্বাভাবিক জ্যামিতি।",
        "আয়তক্ষেত্রকে দুই টুকরো করার এই সরল ধাপটি আসলে গোটা বিষয়ের সবচেয়ে গুরুত্বপূর্ণ ধাপ। এটি না বুঝলে সূত্রের বি ভাগ দুই কোথা থেকে আসে তা কখনো বোঝা যাবে না।",
        "আমরা এখন একটি নির্দিষ্ট উদাহরণ দিয়ে মূলনীতিটি শিখলাম। পরের ধাপে একই যুক্তি ব্যবহার করে যেকোনো সাধারণ দ্বিঘাত সমীকরণের জন্য একটি সার্বজনীন সূত্র বানাব।",
        "চিত্রের দিকে তাকালে দেখা যায়, নতুন বর্গের বাহু হলো পুরনো বর্গের বাহু plus অর্ধেক আয়তক্ষেত্রের দৈর্ঘ্য। এই বাহুটিই আমাদের সমাধানের কাছে পৌঁছে দেয়।",
        "ঋণাত্মক মান নিয়ে ভয় পাওয়ার কোনো কারণ নেই। জ্যামিতিতে আমরা ক্ষেত্রফল নিয়ে কাজ করি, আর বীজগণিতে সেই ক্ষেত্রফলের কারণে দুটি সম্ভাব্য মান জন্ম নেয়—একটি ধনাত্মক, একটি ঋণাত্মক।",
        "বর্গ পূরণের প্রতিটি ধাপ আপনি কাগজে এঁকে দেখতে পারেন। প্রথমে বর্গ আঁকুন, তারপর আয়তক্ষেত্র যোগ করুন, অর্ধেক করুন, কোণা পূরণ করুন—ব্যাস, সূত্রটি নিজেই জন্ম নেবে।",
        "এই পদ্ধতি কেবল দ্বিঘাত সমীকরণের জন্যই নয়; বৃত্তের সমীকরণ লেখার ক্ষেত্রেও একই কৌশল কাজে লাগে। বর্গ পূরণ একটি সার্বজনীন হাতিয়ার যা বারবার কাজে আসবে।",
        "মনে রাখবেন, ডানপাশের মান যত বড় হবে, বর্গমূলের পর মূল দুটি তত দূরে সরে যাবে। কোণা পূরণের পর অবশিষ্ট ক্ষেত্রফলই আসলে মূলের দূরত্ব নির্ধারণ করে।",
        "আমরা এখানে যে ছোট্ট কৌশলটি শিখলাম তা হলো—অসম্পূর্ণ অংশটি খুঁজে বের করে তা পূরণ করা। গণিতের অনেক জায়গায় এই একই ধারণা বারবার ফিরে আসে।",
    ],
    "sec-03-parabola-symmetry": [
        "বীজগণিত ছেড়ে এবার কার্তেসীয় তলে প্যারাবোলার গ্রাফের দিকে তাকানো যাক। যেকোনো প্যারাবোলার সবচেয়ে মৌলিক ও অনবদ্য বৈশিষ্ট্য হলো এর নিখুঁত দ্বিপাক্ষিক প্রতিসাম্য—এর বাঁ ও ডান অংশ আয়নার মতো হুবহু এক।",
        "যদি সমীকরণটির দুটি মূল থাকে, তবে প্রতিসাম্য অক্ষটি সর্বদা এই দুটি মূলের ঠিক মাঝামাঝি অবস্থান করে। অর্থাৎ প্রতিসাম্য কেন্দ্র হলো দুই মূলের গড়, যা আমরা প্রথম মূল plus দ্বিতীয় মূল ভাগ দুই লিখে থাকি।",
        "ক্যালকুলাসের সাহায্য ছাড়াও এই প্রতিসাম্য অক্ষ খুঁজে পাওয়া সহজ। এক্স equal শূন্য বিন্দুতে যে উচ্চতা পাই, ঠিক সেই একই উচ্চতা আবার পাই যখন এক্স equal ঋণাত্মক বি ভাগ এ, কারণ তখন এ এক্স বর্গ plus বি এক্স equal শূন্য হয়।",
        "যেহেতু শূন্য ও ঋণাত্মক বি ভাগ এ—এই দুটি বিন্দু একই উচ্চতায় আছে, তাই তাদের ঠিক মাঝখানেই শীর্ষবিন্দু অবস্থান করবে। সেই মধ্যবিন্দু হলো ঋণাত্মক বি ভাগ দুই এ।",
        "এখন যদি শীর্ষবিন্দু থেকে মূল দুটির অনুভূমিক দূরত্ব ডি হয়, তবে মূল দুটি হবে ঋণাত্মক বি ভাগ দুই এ প্লাস মাইনাস ডি। দ্বিঘাত সূত্র আসলে এই দূরত্ব ডি কে আর কিছু নয়।",
        "গ্রান্ট স্যান্ডারসনের ভাষায়, দ্বিঘাত সূত্র মূলত প্রতিসাম্য অক্ষের অবস্থান এবং সেখান থেকে মূলের বিচ্যুতির সমষ্টি ছাড়া আর কিছুই নয়। এই বাক্যটি মনে রাখলে সূত্রটি কখনো ভুলে যাবেন না।",
        "প্যারাবোলার শীর্ষবিন্দু হলো সেই চরম বিন্দু যেখানে দিক পরিবর্তন ঘটে। এর উভয় পাশের মান আয়নার মতো হুবহু প্রতিসম, আর এই কারণেই শীর্ষবিন্দুতে ঢাল শূন্য হয়।",
        "যদি এ ধনাত্মক হয়, প্যারাবোলা উপরের দিকে খোলে ও শীর্ষবিন্দু সর্বনিম্ন বিন্দু হয়। আর যদি এ ঋণাত্মক হয়, প্যারাবোলা নিচের দিকে খোলে ও শীর্ষবিন্দু সর্বোচ্চ বিন্দু হয়—কিন্তু প্রতিসাম্য অক্ষ একই থাকে।",
        "সহগ সি হলো সেই বিন্দু যেখানে বক্ররেখা ওয়াই অক্ষকে ছেদ করে। ঋণাত্মক বি ভাগ এ বিন্দুতে একই উচ্চতা সি পাওয়ার কারণেই আমরা প্রতিসাম্য অক্ষের অবস্থান নির্ণয় করতে পারি।",
        "দুই মূলের গড় বের করার এই সরল ধাপটি আমাদের জন্যে অত্যন্ত শক্তিশালী, কারণ এটি কোনো জটিল হিসেব ছাড়াই সূত্রের প্রথম অংশ ঋণাত্মক বি ভাগ দুই এ কে প্রমাণ করে।",
        "যখন প্যারাবোলা এক্স অক্ষকে দুই জায়গায় ছেদ করে, তখন ছেদের দুই বিন্দু প্রতিসাম্য অক্ষ থেকে সমান দূরে থাকে। এই দূরত্বের সমানতাই দ্বিঘাত সূত্রের প্লাস মাইনাস চিহ্নের উৎস।",
        "আপনি যদি প্যারাবোলার এক পাশের যেকোনো বিন্দু নেন, তবে অপর পাশে প্রতিসাম্য অক্ষের সমান দূরে একটি হুবহু অনুরূপ বিন্দু পাবেন। এই বৈশিষ্ট্যটিই একে প্রতিসম করে তোলে।",
        "শীর্ষবিন্দুর এক্স স্থানাঙ্ক ঋণাত্মক বি ভাগ দুই এ, আর ওয়াই স্থানাঙ্ক বের করতে হলে এই এক্স মান মূল সমীকরণে বসাতে হয়। তখন সি মাইনাস বি বর্গ ভাগ চার এ পাওয়া যায়।",
        "প্রতিসাম্যের এই ধারণা কেবল প্যারাবোলার ক্ষেত্রেই নয়; প্রকৃতির অনেক বক্ররেখা ও ভৌত ঘটনার ক্ষেত্রেও দেখা যায়। তাই এটি শিখে রাখা ভবিষ্যতে বহু জায়গায় কাজে আসবে।",
        "অনেক শিক্ষার্থী মনে করে শীর্ষবিন্দু মানেই সর্বোচ্চ বিন্দু, কিন্তু তা সবসময় সত্য নয়। শীর্ষবিন্দু আসলে বক্ররেখার দিক-পরিবর্তনের বিন্দু, যেটি উপরের দিকে খোলা হলে সর্বনিম্ন হয়।",
        "যদি দুই মূল সমান হয়, তবে প্যারাবোলা শীর্ষবিন্দুতে এক্স অক্ষকে কেবল স্পর্শ করে, ছেদ করে না। তখন প্রতিসাম্য কেন্দ্র ও মূল একই বিন্দুতে মিলে যায়—পরে আমরা নিশ্চায়কের মাধ্যমে এটি দেখব।",
        "প্রতিসাম্য অক্ষের সাহায্যে আমরা প্যারাবোলার যেকোনো বিন্দুর প্রতিবিম্ব সহজেই বের করতে পারি। কেবল তার দূরত্বটি অন্য দিকে নিলেই হয়ে যায়—কোনো হিসেবের প্রয়োজন নেই।",
        "দ্বিঘাত সমীকরণের দুটি মূল একসাথে মিলে প্যারাবোলার ছেদবিন্দু গঠন করে, আর তাদের গড় গঠন করে প্রতিসাম্য অক্ষ। এই দুটি তথ্য একসাথে মিলেই পূর্ণ দ্বিঘাত সূত্রটি তৈরি হয়।",
        "আমরা এখন বুঝতে পারলাম কেন সূত্রের শুরুতে ঋণাত্মক বি থাকে—এটি আসলে প্রতিসাম্য কেন্দ্রের অবস্থান। বাকি অংশ অর্থাৎ বর্গমূলের অংশটি হলো সেই কেন্দ্র থেকে মূলের দূরত্ব।",
        "প্যারাবোলার গ্রাফের দিকে তাকালে দেখা যায় এটি কতটা সুসংগঠিত ও প্রতিসম। এই সুসংগঠিতিই আমাদের সূত্রটিকে বিশ্বাসযোগ্য করে তোলে, কারণ পেছনে একটি সুন্দর চিত্র কাজ করছে।",
        "মনে রাখবেন, এক্স ভাগ দুই এ নয়, বরং ঋণাত্মক বি ভাগ দুই এ হলো প্রতিসাম্য অক্ষ। চিহ্নের এই ছোট্ট পার্থক্যের কারণেই অনেকের ভুল হয়, তাই চিত্রের দিকে তাকিয়ে যাচাই করে নেবেন।",
        "আমরা ক্যালকুলাস না জেনেই শীর্ষবিন্দু খুঁজে পেলাম—কেবল একই উচ্চতার দুটি বিন্দুকে কাজে লাগিয়ে। এটি গণিতের একটি সুন্দর কৌশল: জটিল সাধনের বদলে সরল সম্পর্ক খোঁজা।",
        "পরবর্তী অধ্যায়ে আমরা এই প্রতিসাম্য কেন্দ্র ও দূরত্বের ধারণা ব্যবহার করে সম্পূর্ণ সার্বজনীন দ্বিঘাত সূত্রটি প্রাকৃতিকভাবে উন্মোচন করব। এখন পর্যন্ত আমরা কেবল ভিত্তি তৈরি করলাম।",
        "প্রতিসাম্যের এই পর্যবেক্ষণটি আপনাকে ভবিষ্যতে অনেক সময় বাঁচাবে। যখনই কোনো দ্বিঘাত সমীকরণ দেখবেন, প্রথমেই তার প্রতিসাম্য কেন্দ্রটি মনে মনে বের করে নেবেন।",
    ],
    "sec-04-quadratic-derivation": [
        "এবার সাধারণ সমীকরণ এ এক্স বর্গ plus বি এক্স plus সি equal শূন্যের ক্ষেত্রে বর্গ পূরণের জ্যামিতি প্রয়োগ করা যাক, যেখানে এ শূন্য নয়। এটি আমাদের আজ পর্যন্ত শেখা সবকিছুর একত্রিত রূপ।",
        "প্রথম ধাপে সমীকরণটিকে এ দ্বারা ভাগ করে শীর্ষ পদটিকে একক ক্ষেত্রফলে রূপান্তর করি। তখন পাই এক্স বর্গ plus বি ভাগ এ গুণ এক্স equal ঋণাত্মক সি ভাগ এ।",
        "দ্বিতীয় ধাপে রৈখিক সহগ বি ভাগ এ-র অর্ধেক হলো বি ভাগ দুই এ। উভয় পক্ষে কোণা পূরণের ক্ষেত্রফল বি ভাগ দুই এ'র বর্গ, অর্থাৎ বি বর্গ ভাগ চার এ বর্গ যোগ করি।",
        "বামপাশটি এখন একটি পূর্ণবর্গে রূপ নিয়েছে: এক্স plus বি ভাগ দুই এ'র বর্গ। ডানপাশটি সরলে যায় বি বর্গ মাইনাস চার এ সি ভাগ চার এ বর্গ—এই রাশিটিই আমাদের পরিচিত নিশ্চায়ক।",
        "এখন উভয় পাশে বর্গমূল নিলে পাই এক্স plus বি ভাগ দুই এ equal প্লাস মাইনাস বর্গমূল অফ বি বর্গ মাইনাস চার এ সি ভাগ দুই এ। বামপাশের কিছু সরানোর পর সূত্রটি সম্পূর্ণ হয়।",
        "অবশেষে পাই এক্স equal ঋণাত্মক বি প্লাস মাইনাস বর্গমূল অফ বি বর্গ মাইনাস চার এ সি, সবটিকে ভাগ দুই এ দিয়ে। এটিই বিশ্বখ্যাত দ্বিঘাত সূত্র, যা আপনি এতদিন মুখস্থ করে এসেছেন।",
        "নিশ্চায়ক বি বর্গ মাইনাস চার এ সি সরাসরি নির্দেশ করে কোণা পূরণের পর ডানপাশে কোনো ক্ষেত্রফল অবশিষ্ট থাকে কি না। এই এক রাশি মূলের পুরো ভাগ্য নির্ধারণ করে।",
        "যদি নিশ্চায়ক ধনাত্মক হয়, তবে ডানপাশে আসল ক্ষেত্রফল থাকে এবং আমরা দুটি আলাদা বাস্তব মূল পাই। প্যারাবোলা তখন এক্স অক্ষকে দুই জায়গায় ছেদ করে।",
        "যদি নিশ্চায়ক শূন্য হয়, তবে ডানপাশের ক্ষেত্রফল শূন্য এবং বর্গমূলও শূন্য। তখন প্যারাবোলা শীর্ষবিন্দুতে এক্স অক্ষকে কেবল স্পর্শ করে—আমরা একটি মাত্র মূল পাই।",
        "যদি নিশ্চায়ক ঋণাত্মক হয়, তবে ডানপাশে কোনো বাস্তব ক্ষেত্রফল থাকে না। তখন বাস্তব মূল নেই; মূল দুটি জটিল সংখ্যা হয়ে যায়—প্যারাবোলা এক্স অক্ষ থেকে দূরে থাকে।",
        "এই তিনটি কেসের মাধ্যমে বোঝা যায় নিশ্চায়ক কতটা গুরুত্বপূর্ণ। কোনো যান্ত্রিক হিসেব না করে কেবল এই রাশির চিহ্ন দেখেই মূলের প্রকৃতি বলে দেওয়া যায়।",
        "বি বর্গ মাইনাস চার এ সি কোনো যান্ত্রিক রাশি নয়—এটি হলো কোণা পূরণের অতিরিক্ত ক্ষেত্রফল ও মূল ধ্রুবক ক্ষেত্রফলের পার্থক্য। এই ব্যাখ্যাটি মনে রাখলে নিশ্চায়ক কখনো অর্থহীন লাগবে না।",
        "আমাদের বের করা সূত্রটিকে আবার আগের প্রতিসাম্যের সাথে মেলানো যাক। ঋণাত্মক বি ভাগ দুই এ হলো সেই কেন্দ্র, আর বর্গমূলের অংশ হলো সেই কেন্দ্র থেকে ডি দূরত্ব।",
        "দুই এ দিয়ে ভাগ করার কারণ হলো আমরা প্রথমে সমীকরণকে এ দ্বারা ভাগ করেছিলাম। শেষে আবার দুই এ তা ফিরে আসে—এটি কোনো কাকতালীয় ঘটনা নয়, বরং গাণিতিক ধারাবাহিকতা।",
        "সমীকরণকে এ দ্বারা ভাগ করার আগে অবশ্যই নিশ্চিত হতে হবে যে এ শূন্য নয়। এ শূন্য হলে ভাগ করা যাবে না এবং সমীকরণটি আর দ্বিঘাত থাকবে না—এই শর্তটি সবসময় মনে রাখবেন।",
        "প্রতিটি ধাপে আমরা ক্ষেত্রফলের ভারসাম্য বজায় রেখেছি। বাঁ পাশে যা যোগ করেছি, ডান পাশেও তাই যোগ করেছি—এই সরল নিয়মটিই পুরো প্রমাণটিকে বৈধ করে তোলে।",
        "অনেক শিক্ষার্থী এই প্রমাণটি দেখে ভাবে এটি কঠিন, কিন্তু আসলে এটি আগের অধ্যায়ের বর্গ পূরণের সাথে অভিন্ন। কেবল সংখ্যার বদলে এ, বি, সি প্রতীকগুলো এসেছে—যুক্তি একই আছে।",
        "যখন আপনি নিজে এই ধাপগুলো কাগজে লিখবেন, তখন দেখবেন সূত্রটি আপনার হাতের নিচে নিজেই জন্ম নিচ্ছে। এটি কোনো বাইরে থেকে আসা তথ্য নয়, বরং আপনার নিজের যুক্তির ফল।",
        "বর্গমূলের সামনে প্লাস মাইনাস চিহ্ন যোগ করার কারণ হলো একটি ধনাত্মক সংখ্যার দুটি বর্গমূল থাকে। এই দুটি মানই প্যারাবোলার বাঁ ও ডান দিকের দুটি মূলের সাথে মিলে যায়।",
        "আমরা এখন দেখেছি কীভাবে একটি সরল জ্যামিতিক ধারণা থেকে একটি সার্বজনীন বীজগাণিতিক সূত্র জন্ম নেয়। এটি গণিতের সবচেয়ে সুন্দর উদাহরণগুলোর একটি।",
        "নিশ্চায়কের মাধ্যমে আমরা ভবিষ্যতে বৃত্ত ও বিন্দুর অবস্থানও নির্ণয় করতে পারব। দ্বিঘাত সূত্র কেবল এক ধরনের সমীকরণের সমাধান নয়, বরং একটি বিশ্বজনীন হাতিয়ার।",
        "পরের অধ্যায়ে আমরা দেখব কীভাবে এই একই সূত্রকে পো শেন লোহ এমন সরলভাবে পুনর্লিখন করেছেন যে মানসিক গণনায়ই মূল বের করা যায়। সুন্দর গণিত কখনো জটিল হয় না।",
        "আপনি এখন সূত্রটিকে মুখস্থ না করলেও তার পেছনের যুক্তি দিয়ে আবার গড়ে তুলতে পারবেন। এটি আজকের পাঠের সবচেয়ে বড় অর্জন—বুঝে শেখার শক্তি।",
        "ধাপগুলো আবার মনে করিয়ে দিই: ভাগ করা, অর্ধেক করা, কোণা পূরণ করা, বর্গমূল নেওয়া। এই চারটি ধাপই দ্বিঘাত সূত্রের পুরো গল্প, বাকিটা শুধু সরলীকরণ।",
    ],
    "sec-05-po-shen-loh-method": [
        "দুই হাজার উনিশ সালে গণিতবিদ পো শেন লোহ দ্বিঘাত সমীকরণ সমাধানের একটি চমকপ্রদ ও অত্যন্ত সহজ প্রতিসাম্যভিত্তিক পদ্ধতি জনপ্রিয় করে তোলেন, যা জটিল সূত্র মুখস্থ করার প্রয়োজনীয়তা সম্পূর্ণ দূর করে।",
        "মোনিক দ্বিঘাত সমীকরণ এক্স বর্গ plus বি এক্স plus সি equal শূন্যের ক্ষেত্রে মূলদ্বয়ের যোগফল ঋণাত্মক বি এবং গুণফল সি। এই দুটি তথ্যই পদ্ধতিটির ভিত্তি, বাকিটা কেবল প্রতিসাম্য।",
        "যেহেতু মূল দুটি তাদের গড়ের সাপেক্ষে প্রতিসম, তাই মূলদ্বয়ের গড় হলো ঋণাত্মক বি ভাগ দুই। আগের অধ্যায়ে আমরা একই কথা প্রতিসাম্য অক্ষ হিসেবে দেখেছি—এখন তা গড়ের ভাষায় বলা হচ্ছে।",
        "যদি গড় থেকে মূল দুটির দূরত্ব উ হয়, তবে মূল দুটিকে লেখা যায় গড় মাইনাস উ এবং গড় প্লাস উ। তাদের গুণফল হবে গড়ের বর্গ মাইনাস উ'র বর্গ, যেটি equal সি।",
        "এই সম্পর্ক থেকে পাই উ'র বর্গ equal গড়ের বর্গ মাইনাস সি, অর্থাৎ উ equal বর্গমূল অফ গড়ের বর্গ মাইনাস সি। মূল দুটি তখন গড় প্লাস মাইনাস উ—দারুন সরল এক কাহিনী।",
        "উদাহরণস্বরূপ, এক্স বর্গ মাইনাস আট এক্স plus বারো equal শূন্য সমীকরণে গড় হলো আট ভাগ দুই, অর্থাৎ চার। তখন উ'র বর্গ equal চারের বর্গ মাইনাস বারো equal চার, তাই উ equal দুই।",
        "সুতরাং মূল দুটি হলো চার মাইনাস দুই equal দুই এবং চার প্লাস দুই equal ছয়। কোনো জটিল সূত্র না বসিয়ে মাত্র কয়েক সেকেন্ডে মানসিক গণনায় উত্তর বের হয়ে আসল।",
        "পদ্ধতিটির সবচেয়ে বড় গুণ হলো এতে কোনো অনুমান বা ভুল-স্বীকারের প্রয়োজন হয় না। আপনি কেবল গড় বের করুন, তারপর দূরত্ব বের করুন—উত্তর চলে আসবে।",
        "ঐতিহ্যগত পদ্ধতিতে আমরা প্রথমে দুটি সংখ্যা খুঁজতাম যাদের যোগফল ও গুণফল নির্দিষ্ট মান হয়। পো শেন লোহ বললেন, সেই খোঁজার প্রয়োজন নেই—গড়ই আমাদের সব বলে দেয়।",
        "গড় বের করার পর মূল দুটি তার চারপাশে এমনভাবে অবস্থান করে যেন একটি রেখার ওপর প্রতিসমভাবে দাঁড়িয়ে আছে। এই চিত্রটি মনে রাখলে পদ্ধতিটি কখনো ভুলা যাবে না।",
        "যদি গড়ের বর্গের চেয়ে সি বড় হয়, তবে উ'র বর্গ ঋণাত্মক হয় এবং বাস্তব মূল থাকে না। ঠিক যেটি আমরা আগে নিশ্চায়কের মাধ্যমে দেখেছি—এখানে তা আরও স্বাভাবিকভাবে দেখা যায়।",
        "দুই মূলের গুণফল সি হওয়ার কারণে আমরা গড়ের বর্গ থেকে সি বিয়োগ করে দূরত্বের বর্গ পাই। এই বিয়োগটি আসলে সেই কোণা পূরণেরই একটি নতুন রূপ।",
        "পদ্ধতিটি মোনিক সমীকরণের জন্য সবচেয়ে সুবিধাজনক, অর্থাৎ যেখানে এক্স বর্গের সহগ এক। অন্য ক্ষেত্রে প্রথমে সবকিছুকে এ দ্বারা ভাগ করে মোনিক রূপে আনতে হয়।",
        "পো শেন লোহ এই পদ্ধতিটি এককভাবে আবিষ্কার করেননি; এর মূল রয়েছে প্রাচীন গ্রিক ও ভারতীয় গণিতে। তিনি কেবল এটিকে আধুনিক শিক্ষার উপযোগী করে তুলে ধরেছেন।",
        "অনেক শিক্ষক এখন এই পদ্ধতিটি প্রথমে শেখান, কারণ এটি শিক্ষার্থীদের সূত্রের ওপর নির্ভর না করে চিন্তা করতে শেখায়। প্রতিসাম্য বুঝতে পারলেই সূত্রটি নিজেই তৈরি হয়ে যায়।",
        "আপনি যদি দশটি বা শতটি দরজার কথা ভাবেন, তবে প্রতিসাম্যের এই ধারণা আরও পরিচিত লাগবে—মাঝখানে দাঁড়িয়ে দুই দিকে সমান দূরত্বে এগোনো। গণিতও ঠিক তাই করে।",
        "আগের অধ্যায়ে আমরা প্যারাবোলার শীর্ষবিন্দুকে ঋণাত্মক বি ভাগ দুই এ বলেছিলাম। আজকের গড় ঋণাত্মক বি ভাগ দুই আসলে সেই শীর্ষবিন্দুরই অন্য নাম—একই সত্য, দুটি দৃষ্টিকোণ।",
        "এই পদ্ধতি আমাদের দেখায় যে গণিত আবিষ্কার মানে নতুন কিছু উদ্ভাবন করা নয়; বরং পুরনো সত্যকে নতুন করে দেখা। প্রতিসাম্য ছিল সবসময়, কেবল আমরা তা খেয়াল করিনি।",
        "মানসিক গণনার এই কৌশল পরীক্ষায় আপনার অনেক সময় বাঁচাবে। সূত্র লেখার আগেই আপনি মনে মনে গড় ও দূরত্ব বের করে উত্তর যাচাই করে নিতে পারবেন।",
        " যখন মূল দুটি পূর্ণসংখ্যা হয়, তখন পদ্ধতিটি বিশেষভাবে সুন্দর লাগে—গড় একটি পূর্ণসংখ্যা আর দূরত্বও একটি পূর্ণসংখ্যা। ছোট্ট যোগবিয়োগেই উত্তর চলে আসে।",
        "পো শেন লোহ পদ্ধতির পেছনে ভিডিও ও লেখার মাধ্যমে যে শিক্ষাদান হয়েছে তা লক্ষ লাখ শিক্ষার্থীকে গণিতের সাথে নতুন করে প্রেমে ফেলেছে। সরলতাই হলো সৌন্দর্য।",
        "আমরা আজ দেখলাম একই দ্বিঘাত সমীকরণকে তিনটি ভিন্ন দৃষ্টিকোণ থেকে দেখা যায়—জ্যামিতিক বর্গ পূরণ, প্যারাবোলা প্রতিসাম্য এবং গড়ভিত্তিক পদ্ধতি। তিনটিই একই সত্যের তিনটি রূপ।",
        "আপনি এখন নিজেই বেছে নিতে পারেন কোন পদ্ধতিটি আপনার কাছে সবচেয়ে স্বাভাবিক লাগে। যেটিই বেছে নিন না কেন, পেছনের যুক্তি একই—ক্ষেত্রফল, প্রতিসাম্য ও দূরত্ব।",
        "গণিত শেখার আসল আনন্দ এই যে একবার বুঝে গেলে সূত্রগুলো আর আলাদা মনে হয় না। সবকিছু একে অপরের সাথে যুক্ত একটি সুন্দর জালে পরিণত হয়।",
        "আজকের পাঠ শেষে আপনি দ্বিঘাত সূত্রটিকে ভুলে গেলেও তার পেছনের চিত্রটি মনে রাখবেন—একটি বর্গ, একটি কোণা, একটি প্রতিসাম্য অক্ষ এবং একটি গড়। এই চারটি চিত্রই যথেষ্ট।",
        "পরবর্তী পাঠে আমরা এই ধারণাগুলোকে আরও জটিল সমীকরণে প্রয়োগ করব। তখন দেখব যে আজ শেখা সরল পদ্ধতিই বড় বড় সমস্যার চাবিকাঠি।",
        "আপনার নিজের অনুশীলনের জন্য কয়েকটি সমীকরণ নিয়ে গড় ও দূরত্ব বের করে দেখুন। প্রথমে ভুল হতে পারে, কিন্তু প্রতিটি ভুল আপনাকে যুক্তির কাছে আরও কাছে নিয়ে যাবে।",
    ],
}
DEFAULT_EXPANSIONS = [
    "এই ধারণাটি নিজের ভাষায় একবার বলে দেখলে বিষয়টি আরও পরিচ্ছন্ন হবে।",
    "লক্ষ্য করুন, ক্ষেত্রফলের এই অনুপাতই আমাদের আসল উত্তরের দিকে নিয়ে যায়।",
    "এখানে যুক্তিটি আবার মনে করিয়ে দিই, কারণ পরের ধাপে এটি বারবার কাজে লাগবে।",
]


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


def load_manifest_cues(lesson):
    """Read the audio_manifest referenced by lesson_01.json (read-only)."""
    rel = (lesson.get("audio_manifest") or lesson.get("audio_manifest_url") or
           (lesson.get("meta") or {}).get("audio_manifest") or
           (lesson.get("meta") or {}).get("audio_manifest_url"))
    candidates = []
    if rel:
        candidates.append((LESSON_JSON.parent / rel).resolve())
    candidates.append(WEB / "assets" / "audio" / "lockdown_math" / "lesson_01" / "manifest.json")

    for manifest in candidates:
        if not manifest.exists():
            continue
        data = json.loads(manifest.read_text(encoding="utf-8"))
        out, seen = [], set()
        for _key, sec in data.get("sections", {}).items():
            sid = sec.get("section_id") or _key
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
        if out:
            return out, f"audio_manifest:{manifest.name} (alias-deduped)"
    return None, None


def derive_from_lesson(lesson):
    out = []
    for sec in lesson.get("sections", []):
        sec_id = sec.get("id") or sec.get("alias") or "section"
        texts = []
        q = sec.get("quote") or {}
        if q.get("text_bn"):
            texts.append(q["text_bn"])
        texts.extend(sec.get("paragraphs", []))
        co = sec.get("callout") or {}
        if co.get("text_bn") or co.get("text"):
            texts.append(co.get("text_bn") or co.get("text"))
        for t in texts:
            clean = strip_math(t)
            if clean:
                out.append({"text": clean,
                            "dur_ms": max(2000.0, len(clean) * 75.0),
                            "section": sec_id})
    return out


def load_source_cues():
    """Return (list_of_{text,dur_ms,section}, source_description)."""
    lesson = json.loads(LESSON_JSON.read_text(encoding="utf-8"))
    out, desc = load_manifest_cues(lesson)
    if not out:
        return derive_from_lesson(lesson), "lesson_01.json:sections"

    # Fold each section's rich Bengali paragraphs into the matching cue.
    sec_by_key = {}
    for sec in lesson.get("sections", []):
        sec_by_key[sec.get("id")] = sec
        if sec.get("alias"):
            sec_by_key[sec["alias"]] = sec
    for c in out:
        sec = sec_by_key.get(c["section"])
        if not sec:
            continue
        extra = []
        for p in sec.get("paragraphs", []):
            clean = strip_math(p)
            if clean:
                extra.append(clean)
        co = sec.get("callout") or {}
        if co.get("text"):
            clean = strip_math(co["text"])
            if clean:
                extra.append(clean)
        if extra:
            c["text"] = c["text"] + " " + " ".join(extra)
    return out, desc


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
        cues.append({
            "id": i + 1,
            "start": round(start, 3),
            "end": round(start + dur, 3),
            "duration": round(dur, 3),
            "bn": c["text"],
            "section": c["section"],
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
        if (i + 1) % 1 == 0:
            print(f"  TTS {i+1}/{len(cues)} (chars={len(c['bn'])})", flush=True)
    return failed


def predicted_fill(natural, target):
    """Fill with tempo floor 0.82: min(1, natural/(0.82*target))."""
    if target <= 0 or natural <= 0:
        return 0.0
    return min(1.0, natural / (MIN_TEMPO * target))


async def expand_short_cues(cues):
    """IMPROVED_DUB_FILL_POLICY: append pedagogical sentences to any cue whose
    natural TTS is short of its scaled window, then re-synthesize. Multiple
    rounds; section-aware sentences keep the additions meaningful.
    """
    expanded = []
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        target = float(c["duration"])
        natural = duration(raw)
        if natural <= 0 or natural >= EXPAND_TRIGGER_RATIO * target:
            continue
        pool = EXPANSION_POOL.get(c["section"], DEFAULT_EXPANSIONS)
        base = sanitize(c["bn"])
        added = 0
        before = natural
        while added < MAX_APPENDED_SENTENCES:
            need = (EXPAND_TARGET_FILL * MIN_TEMPO * target - natural)
            if need <= 0:
                break
            rate_sec_per_char = natural / max(len(base), 1)
            need_chars = max(200, int(need / max(rate_sec_per_char, 0.01)))
            n_sent = max(1, min(MAX_APPENDED_SENTENCES - added,
                                int(np.ceil(need_chars / 200.0))))
            append_text = " ".join(pool[(added + j) % len(pool)] for j in range(n_sent))
            new_text = sanitize(base + " " + append_text)
            print(f"  expand cue {cid}: fill {predicted_fill(natural, target):.2f} "
                  f"natural={natural:.1f}s target={target:.1f}s +{n_sent} sent "
                  f"(len={len(new_text)})", flush=True)
            if await synth_cue(new_text, raw):
                added += n_sent
                natural = duration(raw)
                base = new_text
                if predicted_fill(natural, target) >= EXPAND_TARGET_FILL:
                    break
            else:
                break
        if added > 0 and natural > 0:
            c["bn"] = sanitize(base)
            expanded.append({
                "id": cid,
                "section": c["section"],
                "natural_before": round(before, 3),
                "natural_after": round(natural, 3),
                "sentences_added": added,
                "final_chars": len(base),
                "fill_before": round(predicted_fill(before, target), 3),
                "fill_after": round(predicted_fill(natural, target), 3),
            })
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

    print("[2/7] Expansion of short cues (IMPROVED_DUB_FILL_POLICY) ...", flush=True)
    expanded = await expand_short_cues(cues)
    print(f"  expanded {len(expanded)} cues", flush=True)

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
        "experiment": "clean_timesync_v2 (lockdown_math_lesson_01 full-length, improved fill, scale recomputed from rendered speech)",
        "lesson": LESSON,
        "course": "lockdown_math",
        "video_id": VIDEO_ID,
        "script_source": source_desc,
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": "absolute sample offset (start*44100); atempo fit floor 0.82; pad only; no truncation",
        "sfx": "NONE - clean speech only",
        "voice": VOICE,
        "min_tempo": MIN_TEMPO,
        "max_tempo": MAX_TEMPO,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "timeline_scale": round(scale, 6),
        "timeline_scale_initial_manifest": round(initial_scale, 6),
        "scale_recomputed_from_rendered_speech": True,
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
            "expand_trigger_ratio": EXPAND_TRIGGER_RATIO,
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
    report["output_duration_sec"] = round(duration(OUT_VIDEO), 3)
    report["output_size_bytes"] = OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0
    try:
        probe = json.loads(run(f'ffprobe -v error -show_entries stream=index,codec_type,codec_name '
                               f'-of json "{OUT_VIDEO}"'))
        report["output_streams"] = probe.get("streams", [])
    except Exception as e:
        report["output_streams_error"] = str(e)

    print("[7/7] Lightweight volumedetect ...", flush=True)
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    odur = duration(OUT_VIDEO)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={report['output_duration_sec']}s size={report['output_size_bytes']}", flush=True)
    print(f"scale={scale:.4f} (recomputed from rendered speech) rounds={render_round}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap={max_internal_gap}s "
          f"expanded={len(expanded)} gate_ok={gate_ok}", flush=True)
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
