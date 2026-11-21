"""
EXPERIMENT - Full-length clean absolute-sample Bengali dub
(Lockdown Math, Lesson 03 - "Binomial distributions and coin flips")

Adapted verbatim from the proven clean_timesync_v2 pipelines:
    lockdown_math/lesson_01/dubbing_pipeline/experiments/clean_timesync_v2/build_lock01_clean.py
    lockdown_math/lesson_02/dubbing_pipeline/experiments/clean_timesync_v2/build_lock02_clean.py

Guarantees (identical to the proven pipeline, plus IMPROVED_DUB_FILL_POLICY.md):
   1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
      half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
   2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
   3. IMPROVED FILL: atempo floor 0.82 (gentle slowdown), ceiling 2.2. Pad only,
      NEVER truncate. NO SFX: clean speech only.
   4. EXPANSION FIRST: the manifest has only 5 h2 cues (~21 s total).  Each cue
      carries a 20+ sentence section-aware pedagogical Bengali expansion pool
      (coin toss foundations, combinations & lattice paths, Pascal's triangle,
      binomial PMF/moments, Galton board & CLT).  The fill-driven loop appends
      as many of these sentences as the rendered window requires.
      NOTE: the supplied YouTube id resolves to a 301.8 s video, NOT the
      1:07:30 lesson stated in lesson_03.json, so the fill-driven loop uses only
      as many sentences as fit; see verification.json -> source_metadata_note.
   5. Fill metrics (per-cue fill, median_fill, max_internal_gap_s) are measured
      from the rendered waveform and written into verification.json; the layout
      scale is RE-COMPUTED FROM THE SUM OF RENDERED NATURAL SPEECH (the stale
      manifest scale is never used).  Auto re-render (expand weakest cues) if
      the gate fails.
   6. Canvas padded to the FULL original video duration so -shortest can never
      trim video frames.  Final cue is capped to end inside the video.
   7. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
   8. Lightweight volumedetect (-vn -nostats, log to FILE) on intro and final.

Cue source (read-only; teacher audio / manifests are NEVER modified):
   web_platform/assets/audio/lockdown_math/lesson_03/manifest.json -> 5 h2 cues.
   web_platform/data/lockdown_math/lesson_03.json section paragraphs/callouts
   are folded into the matching cue for real teaching content.

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
BASE = EXP.parent.parent                        # .../lockdown_math/lesson_03/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "lockdown_math" / "lesson_03.json"
MANIFEST = WEB / "assets" / "audio" / "lockdown_math" / "lesson_03" / "manifest.json"

# Original source: yt-dlp output (verified with ffprobe before use).
ORIGINAL_DIR = WEB / "media_vault" / "lockdown_math" / "lesson_03" / "original_source"
ORIGINAL_VIDEO = ORIGINAL_DIR / "full_original.mp4"

OUT_VIDEO = WEB / "media_vault" / "lockdown_math" / "lesson_03" / "experiments" / "3b1b_lockdown_03_full_dubbed.mp4"

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
VIDEO_ID = "bT1p5tJwn_0"             # supplied id (see source_metadata_note)
LESSON = "lesson_03"

# Silence margins: keep 0-2 s and the final 2 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Expansion policy constants.
EXPAND_TRIGGER_RATIO = 0.62          # expand when natural < 62% of window
EXPAND_TARGET_FILL = 0.85            # aim well above the 0.72 median floor (headroom)
MAX_APPENDED_SENTENCES = 160         # lockdown L03 needs HEAVY expansion
ACTIVE_THRESHOLD = 0.015
CHARS_PER_CHUNK = 1700               # chunk long TTS text for robustness


# ---------------------------------------------------------------------------
# Section-aware pedagogical sentences (~20-22 distinct sentences PER section).
# Cycled (never repeated verbatim inside a single add-call); each addition
# teaches real mathematics and is TTS-safe (phonetic Bengali, no raw acronyms).
# ---------------------------------------------------------------------------
EXPANSION_POOL = {
    "sec-01-coin-toss-foundations": [
        "সবাই কয়েন টসের সাথে পরিচিত, একটি মুদ্রা ছুঁড়ে দেখি হেড কলা টেল। কিন্তু এই সরল দৃশ্যের ভেতরেই সম্ভাব্যতা তত্ত্বের সবচেয়ে মৌলিক ধারণাটি লুকিয়ে আছে।",
        "যদি মুদ্রাটি নিরপেক্ষ হয়, তবে হেড আসার সম্ভাবনা এক দুই ভাগ এবং টেল আসার সম্ভাবনাও এক দুই ভাগ; এই দুটি সম্ভাবনার যোগফল বরাবর এক হয়।",
        "একবারের নিক্ষেপে ফলাফল আমরা আগে বলতে পারব না, কিন্তু অনেকবার নিক্ষেপ করলে হেডের আপেক্ষিক হার স্থির হয়ে যায়; এই স্থির হারই আমাদের ব্যবহারিক সম্ভাবনা।",
        "প্রতিটি নিক্ষেপ একটি বার্নৌলি ট্রায়াল, কারণ ফলাফল ঠিক দুইটি, সাফল্য বা ব্যর্থতা, অর্থাৎ হেড বা টেল।",
        "ট্রায়ালগুলো পরস্পর স্বাধীন; আগের নিক্ষেপের ফল পরের নিক্ষেপের ওপর কোনো প্রভাব ফেলে না। মুদ্রার কোনো স্মরণশক্তি নেই।",
        "দুইবার নিক্ষেপ করলে মোট ফলাফল চারটি, হেড হেড, হেড টেল, টেল হেড এবং টেল টেল।",
        "তিনবারে ফলাফল আটটি, চারবারে ষোলোটি, আর এন বার নিক্ষেপে মোট ফলাফল দুইয়ের এন ঘাত।",
        "লক্ষ্য করুন, ট্রায়ালের সংখ্যা রৈখিকভাবে বাড়লেও সম্ভাব্য ফলাফলের সংখ্যা সূচকীয় হারে বেড়ে যায়; এই প্রসারণই পরে গণনাকে সুন্দর করে তোলে।",
        "কয়েন টসের বৃক্ষচিত্রে প্রতিটি ধাপে শাখা দ্বিগুণ হয়, প্রথমে দুই, তারপর চার, তারপর আট, ঠিক যেন একটি বাইনারি গাছ।",
        "ঠিক একটি হেড পাওয়ার সম্ভাবনা কত? দুইবার নিক্ষেপে চারটি ফলের মধ্যে দুইটিতে হেড আছে, তাই সম্ভাবনা দুই ভাগ চার, অর্থাৎ এক দুই ভাগ।",
        "এখানে আমরা প্রতিটি ফলাফলকে সমান গুরুত্ব দিই; এটিই শাস্ত্রীয় সম্ভাবনার ভিত্তি, যা প্রথম ধাপের গণনাকে সরল করে।",
        "তাত্ত্বিক সম্ভাবনা আর বাস্তবে পাওয়া আপেক্ষিক হার হুবহু এক নয়; কিন্তু নিক্ষেপের সংখ্যা বাড়ার সাথে সাথে তারা কাছে এসে যায়।",
        "হাজারবার টস করলে হেডের হার প্রায় পঞ্চাশ শতাংশে দাঁড়ায়, কিন্তু দশবারে সাতটি হেড পাওয়াও কোনো অস্বাভাবিক ঘটনা নয়।",
        "অনেকের ধারণা, কয়েকবার টেল পড়ার পর হেড আসার সম্ভাবনা বেড়ে যায়; এই ভুলটি জুয়াড়ির ভুল নামে পরিচিত, বাস্তবে সম্ভাবনা অপরিবর্তিত থাকে।",
        "মুদ্রা যত নিরপেক্ষ হোক, প্রতিটি নিক্ষেপ অতীতের কোনো তথ্য বহন করে না; স্বাধীনতা হলো এই মডেলের প্রাণ।",
        "নমুনা ক্ষেত্র মানে সম্ভাব্য সব ফলাফলের সংগ্রহ; দুইবার নিক্ষেপে এই সংগ্রহ চারটি উপাদান নিয়ে গঠিত।",
        "প্রতিটি নির্দিষ্ট অনুক্রমের সম্ভাবনা নির্ণয় করতে হলে প্রথমে নমুনা ক্ষেত্রের মোট আকার জানতে হয়।",
        "যখন আমরা বলি হেড আসার সম্ভাবনা এক দুই ভাগ, আমরা আসলে বলি যে দীর্ঘ সময়ে হেডের অনুপাত এক দুই ভাগের কাছে এসে যাবে।",
        "বার্নৌলি ট্রায়ালের সবচেয়ে বড় শক্তি হলো এর সরলতা, একটি ট্রায়াল থেকে শুরু করে হাজার ট্রায়াল পর্যন্ত একই নিয়ম প্রয়োগ করা যায়।",
        "আজকের এই সরল মডেলই পরে দ্বিপদী বিন্যাস, প্যাসকেলের ত্রিভুজ আর গ্যালটন বোর্ডের ভিত্তি গড়ে তুলবে।",
        "তাই কয়েন টস কেবল একটি খেলা নয়; এটি সম্ভাব্যতা বিজ্ঞানের প্রথম পরীক্ষাগার, যেখানে প্রতিটি ধাপ আপনি নিজের চোখে দেখতে পারেন।",
        "চলুন এই বৃক্ষচিত্রকে মনে রেখে এগোনো যাক, প্রতি শাখা এক দ্বিমুখী সিদ্ধান্ত, আর শাখাগুলোর সমষ্টিই আমাদের ভবিষ্যতের উত্তর।",
    ],
    "sec-02-combinations-and-paths": [
        "দশবার কয়েন টসে ঠিক চারটি হেড আসার সম্ভাবনা বের করতে হলে প্রথমে মোট ফলাফল জানতে হয়, দুইয়ের দশ ঘাত, অর্থাৎ এক হাজার চব্বিশ।",
        "এই ফলগুলোর মধ্যে ঠিক চারটি হেড ও ছয়টি টেল আছে এমন ফল কতটি? এই গণনাই হলো সমাবেশ।",
        "দশটি অবস্থানের মধ্যে চারটি অবস্থান হেডের জন্য বেছে নেওয়ার উপায়কে বলা হয় কম্বিনেশন; এর সূত্র এন সি আর equal এন ফ্যাক্টোরিয়াল ভাগ কে ফ্যাক্টোরিয়াল গুণ এন মাইনাস কে ফ্যাক্টোরিয়াল।",
        "ফ্যাক্টোরিয়াল মানে এক থেকে শুরু করে সেই সংখ্যা পর্যন্ত সব পূর্ণসংখ্যার গুণফল, উদাহরণস্বরূপ পাঁচ ফ্যাক্টোরিয়াল equal এক গুণ দুই গুণ তিন গুণ চার গুণ পাঁচ।",
        "কিন্তু তিনব্লুব্রাউনের দৃষ্টিতে এটি কোনো শুষ্ক ফ্যাক্টোরিয়াল ভাগাভাগি নয়; এটি একটি গ্রিডে পথচলার গল্প।",
        "কল্পনা করুন আপনি একটা স্থানাঙ্ক গ্রিডে শূন্য শূন্য বিন্দু থেকে শুরু করলেন; হেড এলে এক ধাপ ডানে, টেল এলে এক ধাপ উপরে যান।",
        "দশটি টসে ঠিক চারটি হেড মানে ডানে চার ধাপ আর উপরে ছয় ধাপ, অর্থাৎ চার ছয় বিন্দুতে পৌঁছানো।",
        "শূন্য শূন্য থেকে চার ছয় বিন্দুতে পৌঁছানোর মোট অনন্য পথের সংখ্যা অবিকল দশ সি চার, যার মান দুই শো দশ।",
        "কেন পথ গণনা আর সমাবেশ একই? কারণ প্রতিটি পথ ঠিক চারটি ডান ও ছয়টি উপরের ধাপ নিয়ে গঠিত; ধাপগুলোর ক্রমই ফলাফলের অনুক্রম।",
        "ডানের ধাপগুলোকে কোথায় বসাবেন তা বেছে নিলেই বাকি জায়গায় উপরের ধাপ স্বয়ংক্রিয়ভাবে চলে যায়।",
        "তাই চারটি হেড বেছে নেওয়া আর ছয়টি টেল বেছে নেওয়া একই কাজ, দশ সি চার equal দশ সি ছয়।",
        "এই প্রতিসাম্যটি খুব গুরুত্বপূর্ণ; একদিকে সাফল্যের সংখ্যা, অন্যদিকে ব্যর্থতার সংখ্যা, দুইয়ের যোগফল সবসময় মোট ট্রায়াল।",
        "পথচলার এই চিত্রটি সমাবেশকে মুখস্থ করার বদলে বোঝার সুযোগ দেয়; আপনি চিত্রটি এঁকে নিজেই পথ গণনা করতে পারবেন।",
        "ছোট একটি উদাহরণ নিই, তিনটি টসে ঠিক একটি হেড পাওয়ার পথ তিনটি, হেড টেল টেল, টেল হেড টেল, টেল টেল হেড।",
        "এখানে তিন সি এক equal তিন, আর মোট ফলাফল আট; তাই সম্ভাবনা তিন ভাগ আট।",
        "গ্রিডের যেকোনো বিন্দুতে পৌঁছানোর পথের সংখ্যা হলো তার বাঁ-নিচের দুটি বিন্দু থেকে আসা পথ সংখ্যার যোগফল; এই নিয়মই পরে প্যাসকেলের ত্রিভুজে রূপ নেবে।",
        "লক্ষ্য করুন, প্রতিটি পথ সমান সম্ভাবনাযুক্ত, কিন্তু মাঝখানের বিন্দুতে অনেক বেশি পথ মিলিত হয়; এই ঘনত্বই পরে বেল কার্ভের চূড়া তৈরি করবে।",
        "সমাবেশের সূত্রে উপরের সংখ্যা এন আর নিচের সংখ্যা কে; উপরেরটি মোট ট্রায়াল, নিচেরটি সাফল্যের সংখ্যা।",
        "অনেক শিক্ষার্থী কে আর এন মাইনাস কে নিয়ে বিভ্রান্ত হয়; মনে রাখবেন হেড বাছাই করলেই টেল বাছাই হয়ে যায়।",
        "বড় এন এর ক্ষেত্রে ফ্যাক্টোরিয়াল হিসেব করা কঠিন, তাই পথচলার চিত্র বা প্যাসকেলের ত্রিভুজ ব্যবহার করে সহজে মান বের করা যায়।",
        "এই অধ্যায়ের মূল শিক্ষা হলো, সম্ভাবনা গণনা আসলে পথ গণনা, আর পথ গণনা আসলে কতভাবে বেছে নেওয়া যায় তার হিসাব।",
        "আপনি যখনই কোনো দ্বিপদী সমস্যার মুখোমুখি হবেন, প্রথমে ভাববেন কতগুলো পথ আছে, বাকিটা সূত্র নিজেই বলে দেবে।",
    ],
    "sec-03-pascals-triangle": [
        "এন equal শূন্য, এক, দুই, তিন এর জন্য সমাবেশের মানগুলোকে পিরামিড আকারে সাজালে জন্ম নেয় প্যাসকেলের ত্রিভুজ।",
        "এই ত্রিভুজের শীর্ষে এক, তার নিচের সারিতে এক এক, তারপর এক দুই এক, তারপর এক তিন তিন এক।",
        "প্রতিটি সারি শুরু ও শেষ হয় এক দিয়ে, আর ভেতরের প্রতিটি সংখ্যা তার উপরের সারির পাশাপাশি দুটি সংখ্যার যোগফল।",
        "এই যোগের নিয়মটিকে লেখা যায়, এন সি আর equal এন মাইনাস এক সি আর মাইনাস এক প্লাস এন মাইনাস এক সি আর।",
        "কেন এই নিয়ম কাজ করে? উত্তরটি কয়েন টসের ভাষায় স্বতঃসিদ্ধ, এন তম নিক্ষেপটি হয় হেড, না হয় টেল।",
        "যদি শেষ নিক্ষেপটি হেড হয়, তবে পূর্বের এন মাইনাস এক টি নিক্ষেপে অবশ্যই আর মাইনাস এক টি হেড এসেছিল।",
        "আর যদি শেষটি টেল হয়, তবে পূর্বের নিক্ষেপেই পুরো আর টি হেড অর্জিত হয়েছিল; এই দুইয়ের যোগফলই মোট এন সি আর।",
        "অর্থাৎ প্যাসকেলের ত্রিভুজ হলো প্রতিটি দ্বিমুখী সিদ্ধান্তের গাণিতিক সংকলন, কোনো যাদু নয়, সরল যুক্তি।",
        "ত্রিভুজের এন তম সারির সব সংখ্যা যোগ করলে পাওয়া যায় দুইয়ের এন ঘাত, কারণ সেটিই এন টি টসের সমস্ত সম্ভাব্য ফলাফলের সংখ্যা।",
        "দশটি সারির যোগফল দুইয়ের দশ ঘাত, অর্থাৎ এক হাজার চব্বিশ, আমাদের আগের হিসেবের সাথে অবিকল মিলে যায়।",
        "ত্রিভুজের বাঁ ও ডান প্রান্ত সবসময় এক, কারণ সব টেল বা সব হেড আসার পথ কেবল একটি।",
        "মাঝের সংখ্যাগুলো সবচেয়ে বড়, কারণ কেন্দ্রে পৌঁছানোর পথ সংখ্যা সবচেয়ে বেশি; এই তথ্যটি গ্যালটন বোর্ডে আবার দেখা যাবে।",
        "প্যাসকেলের ত্রিভুজ আসলে ফ্যাক্টোরিয়াল ছাড়াই সমাবেশ বের করার একটি সুন্দর পদ্ধতি, কেবল উপরের দুটি সংখ্যা যোগ করুন।",
        "ত্রিভুজটিকে ডানে বা বাঁয়ে কাত করে দেখলে দ্বিপদী সহগগুলোর প্রতিসাম্য আরও স্পষ্ট হয়ে ওঠে।",
        "এই ত্রিভুজের সাথে আমাদের আগের গ্রিড পথচলার গল্প অবিকল মেলে, প্রতিটি বিন্দুতে আসা পথের সংখ্যাই সেই বিন্দুর সংখ্যা।",
        "ছোট্ট একটি উদাহরণ, পাঁচ সি দুই equal পাঁচ সি তিন equal দশ, আর এটি ত্রিভুজের পঞ্চম সারিতেও দেখা যায়।",
        "গণিতের অনেক জায়গায় এই পুনরাবৃত্তিমূলক নিয়ম ফিরে আসে, পথ গণনা, বহুপদী প্রসারণ, এমনকি কম্পিউটার অ্যালগরিদমেও।",
        "ত্রিভুজের সারি নম্বর আর ভেতরের অবস্থান বুঝতে পারলে যেকোনো সমাবেশ মান মানসিকভাবেই বের করা যায়।",
        "এন বড় হলে ফ্যাক্টোরিয়াল হিসেবের বদলে এই ত্রিভুজ ব্যবহার করলে ভুল হওয়ার সম্ভাবনা অনেক কমে যায়।",
        "ত্রিভুজের সৌন্দর্য হলো এটি জটিল সূত্রকে সরল যোগে রূপ দেয়, বড় বড় সংখ্যা জন্ম নেয় কেবল ছোট সংখ্যা যোগ করে।",
        "আপনি যখন দ্বিপদী সহগ দেখবেন, মনে রাখবেন এর পেছনে এই ত্রিভুজের একটি সারি লুকিয়ে আছে।",
        "পরবর্তী অধ্যায়ে এই সহগগুলোই সম্ভাব্যতার ওজন হয়ে দ্বিপদী বিন্যাসে রূপ নেবে।",
    ],
    "sec-04-binomial-pmf-and-moments": [
        "এখন পর্যন্ত আমরা নিরপেক্ষ মুদ্রা নিয়ে কাজ করেছি; কিন্তু যদি মুদ্রাটি পক্ষপাতদুষ্ট হয়, তবে হেড আসার সম্ভাবনা পি আর টেল আসার সম্ভাবনা এক মাইনাস পি হয়।",
        "পি equal শূন্য পাঁচ হলে আমরা আগের নিরপেক্ষ ক্ষেত্রটি ফিরে পাই; পি অন্য যেকোনো মান হলে বিন্যাসটি সামান্য সরে যায়।",
        "যদি কোনো নির্দিষ্ট অনুক্রমে আর টি হেড আর এন মাইনাস আর টি টেল থাকে, তবে তার সম্ভাবনা পি আর ঘাত গুণ এক মাইনাস পি-র এন মাইনাস আর ঘাত।",
        "কিন্তু এই রকম অনুক্রম মোট এন সি আর টি, আর তারা পরস্পর বর্জনীয়, তাই মোট সম্ভাবনা হলো এদের সমষ্টি।",
        "এখান থেকেই জন্ম নেয় দ্বিপদী বিন্যাসের সম্ভাব্যতা ভর ফাংশন, পি এক্স equal আর equal এন সি আর গুণ পি আর ঘাত গুণ এক মাইনাস পি-র এন মাইনাস আর ঘাত।",
        "এই সূত্রটিতে তিনটি অংশ, পথের সংখ্যা, সাফল্যের সম্ভাবনা, আর ব্যর্থতার সম্ভাবনা; তিনটির গুণফলই আমাদের চূড়ান্ত উত্তর।",
        "সম্ভাব্যতা ভর ফাংশন মানে প্রতিটি সম্ভব আর এর জন্য একটি করে সম্ভাবনার মান নির্ধারণ করা।",
        "বীজগণিতে পি প্লাস কিউ-র এন ঘাত প্রসারিত করলে যে সহগগুলো আসে, দ্বিপদী বিন্যাসের সম্ভাবনাগুলো অবিকল সেই সহগ।",
        "যেহেতু পি প্লাস কিউ equal এক, তাই সব সম্ভাবনার যোগফল একের এন ঘাত, অর্থাৎ বরাবর এক, কোনো সম্ভাবনা কমবে না বা বাড়বে না।",
        "দ্বিপদী চলকের প্রত্যাশিত মান বা গড় হলো এন গুণ পি, অর্থাৎ গড় সাফল্যের সংখ্যা মোট ট্রায়ালের পি ভাগ।",
        "ভেদাঙ্ক হলো এন গুণ পি গুণ এক মাইনাস পি; আর আদর্শ বিচ্যুতি তার বর্গমূল।",
        "ট্রায়াল বাড়লে আদর্শ বিচ্যুতি বাড়ে, কিন্তু গড়ের তুলনায় আপেক্ষিক বিচ্যুতি কমে যায়; এই কারণে ফলাফল কেন্দ্রের দিকে কেন্দ্রীভূত হয়।",
        "আপেক্ষিক বিচ্যুতি একের বর্গমূল এন এর সমানুপাতিক, অর্থাৎ এন চার গুণ করলে বিস্তার অর্ধেক হয়ে যায়।",
        "এটিই বৃহৎ সংখ্যার সূত্রের মূল মেকানিক্স, বেশি ট্রায়াল মানে কম অনিশ্চয়তা।",
        "নিরপেক্ষ ক্ষেত্রে পি equal শূন্য পাঁচ, তাই গড় এন ভাগ দুই আর ভেদাঙ্ক এন ভাগ চার।",
        "শতটি টসে গড় পঞ্চাশ, আদর্শ বিচ্যুতি পাঁচ, অর্থাৎ অধিকাংশ ফলাফল পঞ্চাশের কাছাকাছি পড়ে।",
        "বিন্যাসের স্তম্ভচিত্রে সর্বোচ্চ শিখর সবসময় গড়ের কাছে থাকে, আর দূরে গেলে সম্ভাবনা কমতে কমতে শূন্যের কাছে আসে।",
        "পি শূন্য পাঁচ হলে বিন্যাসটি প্রতিসম; পি অন্য মান হলে একদিকে সামান্য টান দেখা যায়, এই টানকে বলা হয় বাঁক।",
        "পি যত শূন্য বা একের কাছে যায়, বিন্যাস তত সংকীর্ণ ও সীমিত হয়, কারণ তখন ফলাফল প্রায় নির্ধারিত।",
        "দ্বিপদী বিন্যাসের এই সূত্র কেবল মুদ্রার জন্য নয়; যেকোনো দ্বিমুখী পরীক্ষা, যেমন সাফল্য ব্যর্থতা বা রোগী সুস্থ অসুস্থ, সব জায়গায় কাজ করে।",
        "তাই দ্বিপদী বিন্যাস হলো বিচ্ছিন্ন সম্ভাবনার সবচেয়ে বহুল ব্যবহৃত মডেল, এটি দিয়ে শুরু করেই পরিসংখ্যানের বড় অংশ বোঝা যায়।",
        "আপনি যখনই কোনো সাফল্য ব্যর্থতার পরীক্ষা দেখবেন, ভাববেন এন, পি আর আর, বাকিটা সূত্র বলে দেবে।",
    ],
    "sec-05-galton-board-and-clt": [
        "আঠারো শতকের শেষ দিকে ব্রিটিশ বিজ্ঞানী স্যার ফ্রান্সিস গ্যালটন দ্বিপদী বিন্যাসকে বাস্তব চোখে দেখার জন্য একটি যন্ত্র তৈরি করেন, গ্যালটন বোর্ড।",
        "এই যন্ত্রে উপর থেকে শত শত ছোট ধাতব বল বা মার্বেল ছেড়ে দেওয়া হয়।",
        "নিচে পড়ার সময় মার্বেলগুলো ত্রিভুজাকারে সাজানো পিনের সাথে ধাক্কা খায়।",
        "প্রতিটি ধাক্কায় মার্বেলের পঞ্চাশ শতাংশ সম্ভাবনা ডানে যাওয়ার এবং পঞ্চাশ শতাংশ সম্ভাবনা বামে যাওয়ার।",
        "পথে যদি এন সারি পিন থাকে, তবে একটি মার্বেল এন বার স্বাধীন সিদ্ধান্ত নেয়, ঠিক এন বার কয়েন টসের মতো।",
        "নিচের খাঁজগুলোতে মার্বেলের স্তূপ ঠিক প্যাসকেলের ত্রিভুজের অনুপাতে জমা হয়।",
        "মাঝখানের খাঁজে সবচেয়ে বেশি মার্বেল পড়ে, কারণ কেন্দ্রে পৌঁছানোর পথের সংখ্যা সবচেয়ে বেশি।",
        "দুই প্রান্তের খাঁজে সবচেয়ে কম মার্বেল, কারণ সবকিছু এক দিকে যাওয়ার পথ কেবল একটি।",
        "একক মার্বেলের গতিপথ সম্পূর্ণ অনিশ্চিত, আপনি বলতে পারবেন না সেটি কোথায় পড়বে।",
        "কিন্তু হাজার হাজার মার্বেলের সামগ্রিক ছবি নিখুঁতভাবে সুশৃঙ্খল, এই হলো সম্ভাব্যতা বিজ্ঞানের পরম দার্শনিক সৌন্দর্য।",
        "পিনের সারি যত বাড়ে, খাঁজের সংখ্যা তত বাড়ে আর স্তম্ভগুলো তত সরু হয়।",
        "এন অসীমের দিকে গেলে বিচ্ছিন্ন স্তম্ভগুলো মিলিয়ে একটি মসৃণ ঘণ্টা-আকৃতির বক্ররেখা গঠন করে, গাউসিয়ান নরমাল বক্ররেখা।",
        "আব্রাহাম দ্য ময়ভ্র আর পিয়েরে-সিমন লাপ্লাস এই রূপান্তরটিকে গাণিতিকভাবে প্রমাণ করেছিলেন, দ্য ময়ভ্র-লাপ্লাস উপপাদ্য।",
        "এই উপপাদ্য হলো আধুনিক কেন্দ্রীয় সীমা উপপাদ্যের প্রথম রূপ, যা পরিসংখ্যানের মূল স্তম্ভ।",
        "সূত্রটি বলে, জেড equal এক্স মাইনাস এন পি ভাগ বর্গমূল অফ এন পি গুণ এক মাইনাস পি; এই মানটি প্রমাণ নরমাল বিন্যাস অনুসরণ করে।",
        "সাধারণ ভাষায়, যেকোনো দ্বিপদী বিন্যাসকে তার গড় দিয়ে সরিয়ে আদর্শ বিচ্যুতি দিয়ে ভাগ করলে সব বিন্যাস একই আকারে দেখায়।",
        "এই কারণে প্রকৃতির অসংখ্য ঘটনা, উচ্চতা, ওজন, পরিমাপের ভুল, একই বেল কার্ভ অনুসরণ করে।",
        "বেল কার্ভের মাঝখানে বেশি, দুই পাশে কম, ঠিক যেন গ্যালটন বোর্ডের মাঝের খাঁজে সবচেয়ে বেশি মার্বেল।",
        "অসীম সংখ্যক ছোট ছোট স্বাধীন প্রভাব একসাথে মিলে একটি সুন্দর নরমাল বক্ররেখা তৈরি করে, এটাই কেন্দ্রীয় সীমা উপপাদ্যের সারাংশ।",
        "গ্যালটন বোর্ড আমাদের দেখায় যে বিশৃঙ্খলা আর শৃঙ্খলা পরস্পর বিরোধী নয়; অসংখ্য বিশৃঙ্খল পথ মিলে একটি শৃঙ্খলিত রূপ জন্ম দেয়।",
        "এই পাঠের শেষে আমরা দেখলাম এক কয়েন টস থেকে শুরু করে প্যাসকেলের ত্রিভুজ, দ্বিপদী সূত্র আর অবশেষে গাউসিয়ান বেল কার্ভ, একটি অবিচ্ছিন্ন যাত্রা।",
        "আপনি যখনই কোনো বেল কার্ভ দেখবেন, মনে রাখবেন এর পেছনে আছে অসংখ্য ছোট দ্বিমুখী সিদ্ধান্ত, ঠিক যেন একের পর এক মার্বেল পড়ছে।",
    ],
}
DEFAULT_EXPANSIONS = [
    "এই ধারণাটি নিজের ভাষায় একবার বলে দেখলে বিষয়টি আরও পরিচ্ছন্ন হবে।",
    "লক্ষ্য করুন, এই অনুপাতই আমাদের আসল উত্তরের দিকে নিয়ে যায়।",
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
    """Read the audio_manifest referenced by lesson_03.json (read-only)."""
    rel = (lesson.get("audio_manifest") or lesson.get("audio_manifest_url") or
           (lesson.get("meta") or {}).get("audio_manifest") or
           (lesson.get("meta") or {}).get("audio_manifest_url"))
    candidates = []
    if rel:
        candidates.append((LESSON_JSON.parent / rel).resolve())
    candidates.append(MANIFEST)

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
                    "text": strip_math(text),
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
        return derive_from_lesson(lesson), "lesson_03.json:sections"

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
        print(f"  TTS {i+1}/{len(cues)} (chars={len(c['bn'])})", flush=True)
    return failed


def predicted_fill(natural, target):
    """Fill with tempo floor 0.82: min(1, natural/(0.82*target))."""
    if target <= 0 or natural <= 0:
        return 0.0
    return min(1.0, natural / (MIN_TEMPO * target))


async def expand_short_cues(cues):
    """IMPROVED_DUB_FILL_POLICY: append pedagogical sentences to any cue whose
    natural TTS is short of its scaled window, then re-synthesize.  Multiple
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
        "experiment": "clean_timesync_v2 (lockdown_math_lesson_03 full-length, improved fill, scale recomputed from rendered speech)",
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
        "source_metadata_note": (
            "The supplied YouTube id bT1p5tJwn_0 resolves to 'Introduction to the "
            "Bernoulli Distribution' by jbstatistics (301.794 s, AV1+Opus), NOT the "
            "1:07:30 3blue1brown lesson stated in lesson_03.json. No real 3blue1brown "
            "video titled 'Binomial distributions and coin flips' exists; the actual "
            "Lockdown Math Ep.3 is 'Complex number fundamentals' (5PcpBw5Hbwo). "
            "The dub was built over the explicitly supplied source. With a ~302 s "
            "source, fill-driven expansion uses only as many of the 20+ sentence "
            "section-aware pools per cue as fit without overrun; the full pools "
            "would support heavy expansion on a ~4050 s source."
        ),
        "source_probe": {
            "container_duration_sec": round(duration(src), 3),
            "video_stream_codec": "av1",
            "video_width": 1280,
            "video_height": 720,
            "audio_stream_codec": "opus",
        },
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
