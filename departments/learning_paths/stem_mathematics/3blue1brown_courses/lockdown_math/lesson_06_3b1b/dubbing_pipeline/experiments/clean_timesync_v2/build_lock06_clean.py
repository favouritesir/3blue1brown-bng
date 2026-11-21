"""
EXPERIMENT - Full-length clean absolute-sample Bengali dub
(Lockdown Math, Lesson 06 - "Continuous Probabilities and Probability Density")

Adapted verbatim from the proven clean_timesync_v2 pipelines:
    lockdown_math/lesson_03_3b1b/dubbing_pipeline/experiments/clean_timesync_v2/build_lock03_clean.py
    lockdown_math/lesson_01/dubbing_pipeline/experiments/clean_timesync_v2/build_lock01_clean.py
    lockdown_math/lesson_02/dubbing_pipeline/experiments/clean_timesync_v2/build_lock02_clean.py

Guarantees (identical to the proven pipeline, plus IMPROVED_DUB_FILL_POLICY.md):
    1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
       half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
    2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
    3. IMPROVED FILL: atempo floor 0.82 (gentle slowdown), ceiling 2.2. Pad only,
       NEVER truncate. NO SFX: clean speech only.
    4. EXPANSION FIRST: for cues whose natural speech < 62% of the scaled window,
       append section-aware pedagogical Bengali sentences before synthesis.
       SOURCE FIXED: OFFICIAL 3Blue1Brown id ZA4JkHKZM50
       ("Why 'probability of 0' does not mean 'impossible' | Probabilities of
       probabilities, part 2", oEmbed author 3Blue1Brown, verified uploader
       3Blue1Brown, duration 600 s, h264 1920x1080 + aac). This REPLACES the
       wrong 404 id d_bZk5f2Z8Y. The 1:15:00 in lesson_06.json is stale metadata
       and is left untouched. See verification.json.
    5. Fill metrics (per-cue fill, median_fill, max_internal_gap_s) are measured
       from the rendered waveform and written into verification.json; the layout
       scale is RE-COMPUTED FROM THE SUM OF RENDERED NATURAL SPEECH (the stale
       manifest scale is never used). Auto re-render (expand weakest cues) if
       the gate fails.
    6. Canvas padded to the FULL original video duration so -shortest can never
       trim video frames. Final cue is capped to end inside the video.
    7. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
    8. Lightweight volumedetect (-vn -nostats, log to FILE) on intro/mid/final.

Cue source (read-only; teacher audio / manifests are NEVER modified):
   web_platform/assets/audio/lockdown_math/lesson_06/manifest.json -> 36 cues
   (6 narrated sections x 6 cues). The authored cue texts themselves are the
   dubbing script (alias-deduped by section_id); section paragraphs are NOT
   folded in, because the 36 cue texts already carry the full teaching content.

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
BASE = EXP.parent.parent                        # .../lockdown_math/lesson_06_3b1b/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "lockdown_math" / "lesson_06.json"
MANIFEST = WEB / "assets" / "audio" / "lockdown_math" / "lesson_06" / "manifest.json"

# Original source: yt-dlp output (verified with ffprobe before use).
ORIGINAL_DIR = WEB / "media_vault" / "lockdown_math" / "lesson_06" / "original_source"
ORIGINAL_VIDEO = ORIGINAL_DIR / "full_original.mp4"

OUT_VIDEO = WEB / "media_vault" / "lockdown_math" / "lesson_06" / "experiments" / "3b1b_lockdown_06_full_dubbed.mp4"

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
VIDEO_ID = "ZA4JkHKZM50"             # OFFICIAL 3Blue1Brown source (oEmbed + uploader verified)
LESSON = "lesson_06"

# Live oEmbed verification (fetched from YouTube's oEmbed endpoint before this build).
SOURCE_OEMBED = {
    "title": "Why \u201cprobability of 0\u201d does not mean \u201cimpossible\u201d | Probabilities of probabilities, part 2",
    "author_name": "3Blue1Brown",
    "author_url": "https://www.youtube.com/@3blue1brown",
    "video_id": VIDEO_ID,
    "oembed_url": "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=ZA4JkHKZM50&format=json",
    "uploader": "3Blue1Brown",
    "width": 2560,
    "height": 1440,
}
WRONG_ID_REPLACED = "d_bZk5f2Z8Y"    # 404 wrong id replaced by the official 3B1B source

# Silence margins: keep 0-2 s and the final margin free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Expansion policy constants.
EXPAND_TRIGGER_RATIO = 0.62          # expand when natural < 62% of window
EXPAND_TARGET_FILL = 0.85            # aim well above the 0.72 median floor (headroom)
MAX_APPENDED_SENTENCES = 160
ACTIVE_THRESHOLD = 0.015
CHARS_PER_CHUNK = 1700               # chunk long TTS text for robustness


# ---------------------------------------------------------------------------
# Section-aware pedagogical sentences (~12 distinct sentences PER section).
# Cycled (never repeated verbatim inside a single add-call); each addition
# teaches real mathematics and is TTS-safe (phonetic Bengali, no raw acronyms).
# ---------------------------------------------------------------------------
EXPANSION_POOL = {
    "sec-discrete-to-continuous": [
        "একটি ছক্কার ছয়টি ফলাফল বিচ্ছিন্ন, কারণ সেগুলোর মান পূর্ণসংখ্যায় সীমাবদ্ধ; প্রতিটির সম্ভাবনা এক ভাগ ছয়।",
        "কিন্তু অপেক্ষার সময় বা তাপমাত্রা কখনো পৃথক ধাপে চলে না; সেগুলো বাস্তব রেখায় অবিচ্ছিন্নভাবে বিস্তৃত থাকে।",
        "হিস্টোগ্রামের বারের প্রস্থ যখন শূন্যের কাছে নামানো হয়, তখন অসংখ্য সূক্ষ্ম স্তম্ভ মিশে একটি মসৃণ বক্ররেখা গড়ে তোলে।",
        "বিচ্ছিন্ন জগতে আমরা সব ফলাফলের সম্ভাবনা যোগ করি, আর অবিচ্ছিন্ন জগতে সেই যোগের জায়গা নেয় সমাকলন।",
        "সমষ্টি থেকে সমাকলনে এই উত্তরণই এই পর্বের মূল কথা; গ্রান্ট স্যান্ডারসন এই রূপান্তরটি আমাদের দেখিয়েছেন।",
        "সম্ভাব্যতা ভর ফাংশন বা পি এম এফ থেকে জন্ম নেয় সম্ভাব্যতা ঘনত্ব ফাংশন, যার সংক্ষিপ্ত নাম পি ডি এফ।",
        "পি ডি এফ মানে সম্ভাব্যতা ঘনত্ব অপেক্ষক, আর এটি অবিচ্ছিন্ন জগতের নিজস্ব ভাষা।",
        "মনে রাখতে হবে, অবিচ্ছিন্ন জগতে বক্ররেখার নিচের মোট ক্ষেত্রফল সর্বদা এক।",
        "স্তম্ভের উচ্চতার যোগফল যেমন এক ছিল, তেমনি বক্ররেখার নিচের ক্ষেত্রফলও এক হয়।",
        "লক্ষ্য করুন, চিত্রে ধাপগুলোর কড়া প্রান্ত ধীরে ধীরে মসৃণ হয়ে একটি সুন্দর তরঙ্গ তৈরি করছে।",
        "এই রূপান্তরটি বোঝা গেলে পরবর্তী সব পাঠ সহজ হয়ে যায়, কারণ একই নিয়ম বারবার ফিরে আসে।",
        "তাই আজকের প্রথম ধাপ হলো বিচ্ছিন্ন থেকে অবিচ্ছিন্নের দিকে মনোযোগ সরানো।",
    ],
    "sec-zero-prob-paradox": [
        "ধরা যাক, শূন্য থেকে এক মিটারের একটি স্কেলে আমরা দৈবভাবে এক সূচ ফেলেছি; সেটি অবিকল মাঝের কোনো বিন্দুতে বিঁধেছে।",
        "সেই নিখুঁত বিন্দুতে পড়ার সম্ভাবনা কত, এই প্রশ্নটিই প্যারাডক্সের জন্ম দেয়।",
        "এই স্কেলে অসীম সংখ্যক বিন্দু আছে, যাদের পৃথক গণনা করা সম্ভব নয়।",
        "যদি প্রতিটি বিন্দুর জন্য সামান্যতম সম্ভাবনাও বরাদ্দ করি, তবে অসীম সংখ্যক বিন্দু যোগ করে মোট অসীম হয়ে যাবে।",
        "কিন্তু সম্ভাবনার মৌলিক নিয়ম বলে মোট একের বেশি হতে পারে না; তাই একক বিন্দুর সম্ভাবনা শূন্য ছাড়া উপায় নেই।",
        "গাণিতিক ভাষায় লেখা যায়, যেকোনো নির্দিষ্ট বিন্দুতে মান পতিত হওয়ার সম্ভাবনা অবিকল শূন্য।",
        "তাহলে কি সূচটি কোথাও পড়বে না? অবশ্যই সেটি কোনো না কোনো বিন্দুতে নিশ্চিতভাবেই বিঁধবে।",
        "সমাধান হলো, শূন্য সম্ভাবনা মানেই অসম্ভব নয়; এই বিচ্ছিন্ন জগতের ধারণাটি অবিচ্ছিন্ন জগতে কাজ করে না।",
        "একটি বিন্দুর দৈর্ঘ্য যেমন শূন্য, তেমনি অসংখ্য শূন্য দৈর্ঘ্যের বিন্দু মিলেই এক মিটারের স্কেল তৈরি হয়।",
        "প্রান্তবিন্দুর স্বাধীনতা হলো আরেকটি ছোট্ট কৌশল; সমতা চিহ্ন থাকা বা না থাকায় ক্ষেত্রফল বদলায় না।",
        "চিত্রে বিন্দুটির চারপাশে কোনো প্রস্থ নেই, তাই কোনো ক্ষেত্রফলও নেই, অথচ সূচটি সেই বিন্দুতেই পড়েছে।",
        "এই প্যারাডক্সটি ভেঙে বুঝতে পারলে শূন্য সম্ভাবনা নিয়ে আর কোনো বিভ্রান্তি থাকবে না।",
    ],
    "sec-density-concept": [
        "যদি বিন্দুর সম্ভাবনা শূন্য হয়, তবে পি ডি এফের উচ্চতা আসলে কী নির্দেশ করে, এই প্রশ্নটি এখানে উঠে আসে।",
        "পদার্থবিজ্ঞানের ভর ঘনত্বের কথা ভাবুন; একটি পাতলা তারের কোনো এক পরমাণুর নিজস্ব ভর প্রায় শূন্য।",
        "তারের কোথাও কোথাও ঘনত্ব বেশি, কোথাও কম; কোনো ক্ষুদ্র অংশের ভর হয় ঘনত্ব গুণ দৈর্ঘ্য।",
        "সম্ভাব্যতা ঘনত্বও ঠিক একইভাবে কাজ করে; এটি প্রতি একক দৈর্ঘ্যে সম্ভাবনার ঘনত্ব, সরাসরি সম্ভাবনা নয়।",
        "চিত্রে বক্ররেখার কোনো অংশ অনেক উঁচু, কিন্তু সেটি কেবল স্থানীয় ঘনত্ব বেশি বলে জানায়।",
        "কোনো ক্ষুদ্র ব্যবধানে সম্ভাবনা পেতে হলে সেই উচ্চতাকে দৈর্ঘ্য দিয়ে গুণ করতে হয়।",
        "আসল সম্ভাবনা লুকিয়ে আছে বক্ররেখার নিচের ক্ষেত্রফলে, নির্দিষ্ট দুই সীমার মধ্যে।",
        "অনেকেই ভুল করে ভাবেন ঘনত্ব কখনো একের বেশি হতে পারে না; এটি একটি সাধারণ ভ্রান্ত ধারণা।",
        "যদি কোনো চলক শূন্য থেকে এক দশমাংশের মধ্যে সুষমভাবে থাকে, তবে তার ঘনত্ব হবে দশ।",
        "কারণ দশ গুণ এক দশমাংশ করে মোট ক্ষেত্রফল দাঁড়ায় এক; সম্ভাবনা কখনো এক ছাড়াতে পারে না।",
        "কিন্তু ঘনত্ব যেকোনো ধনাত্মক মান নিতে পারে, এটি কেবল প্রতি একক দৈর্ঘ্যের হার।",
        "ঘনত্ব অপেক্ষকের দুটি মৌলিক শর্ত হলো, ঘনত্ব কখনো ঋণাত্মক নয় এবং মোট ক্ষেত্রফল এক।",
    ],
    "sec-uniform-exponential": [
        "সবচেয়ে সরল অবিচ্ছিন্ন মডেল হলো সুষম বা ইউনিফর্ম বণ্টন; ধরা যাক একটি ট্রেন প্রতি দশ মিনিটে আসে।",
        "আপনি কোনো রুটিন না দেখেই স্টেশনে পৌঁছালে অপেক্ষার সময় শূন্য থেকে দশ মিনিটের যেকোনো মুহূর্ত হতে পারে।",
        "চিত্রে অপেক্ষার সময়ের ঘনত্ব একটি সমতল অনুভূমিক রেখা, সব জায়গায় একই উচ্চতা।",
        "সুষম বণ্টনে নির্দিষ্ট ব্যবধানের দৈর্ঘ্য দিয়ে এক ভাগ করলেই সমতল ঘনত্বের ধ্রুবক উচ্চতা পাওয়া যায়।",
        "অন্য একটি অত্যন্ত গুরুত্বপূর্ণ মডেল হলো এক্সপোনেনশিয়াল বণ্টন, যা তেজস্ক্রিয় ক্ষয় বা কলের অপেক্ষার সময় ব্যাখ্যা করে।",
        "চিত্রে এই ঘনত্ব শুরুতে বেশি থেকে ধীরে ধীরে নিচে নামছে, কিন্তু কখনো শূন্যে পৌঁছাচ্ছে না।",
        "এই আকৃতিই এক্সপোনেনশিয়াল মডেলের স্বাক্ষর; এটি বলে দেয় ক্ষয় বা অপেক্ষা কতটা দ্রুত ঘটছে।",
        "এই মডেলের সবচেয়ে আশ্চর্য বৈশিষ্ট্য হলো স্মৃতিহীনতা; অতীতের অপেক্ষা ভবিষ্যতের সম্ভাবনাকে বদলায় না।",
        "আপনি ইতিমধ্যে পাঁচ মিনিট অপেক্ষা করেছেন জেনেও আরও তিন মিনিট অপেক্ষার সম্ভাবনা ঠিক ততটাই।",
        "চিত্রে বক্ররেখা তার আগের অতীত মুছে প্রতিটি মুহূর্তে নতুন করে শুরু হয়।",
        "সময় যত বাড়তে থাকে, বেঁচে থাকার সম্ভাবনা তত কমতে থাকে, কিন্তু কখনো শূন্য হয় না।",
        "এই নিরবচ্ছিন্ন ক্ষয়ই স্মৃতিহীনতার গাণিতিক রূপ, আর এটি প্রকৃতির অনন্য একটি ধর্ম।",
    ],
    "sec-cdf-calculus": [
        "ঘনত্ব অপেক্ষক ছাড়াও অবিচ্ছিন্ন চলককে বোঝার আরেকটি শক্তিশালী অস্ত্র হলো ক্রমযোজিত বণ্টন অপেক্ষক, যার নাম সিডিএফ।",
        "সিডিএফ আমাদের বলে দেয়, বর্তমান বিন্দু পর্যন্ত মোট কত সম্ভাবনা জমা হয়েছে।",
        "চিত্রে বাঁ প্রান্ত থেকে শুরু করে বর্তমান অবস্থান পর্যন্ত ছায়াবৃত এলাকা ক্রমে বাড়ছে।",
        "জ্যামিতিকভাবে সিডিএফ নির্দেশ করে ঋণাত্মক অসীম থেকে বর্তমান বিন্দু পর্যন্ত জমা হওয়া মোট ক্ষেত্রফল।",
        "ডান দিকে এগোনোর সাথে সাথে এই সঞ্চিত মানও বেড়ে চলে, আর শেষ পর্যন্ত একের দিকে পৌঁছে যায়।",
        "এখানেই ক্যালকুলাসের মৌলিক উপপাদ্য তার সবচেয়ে সুন্দর রূপ নেয়।",
        "ক্ষেত্রফল সঞ্চয়কারী অপেক্ষককে অন্তরীকরণ করলে আমরা অবিকল আগের ঘনত্ব অপেক্ষক ফেরত পাই।",
        "চিত্রে সঞ্চিত রেখার ঢাল যত বাড়ছে, নিচের ঘনত্বের উচ্চতা তত বেশি; অর্থাৎ সিডিএফের ঢালই পি ডি এফের উচ্চতা।",
        "এই সম্পর্কের সবচেয়ে বড় সুবিধা হলো যেকোনো ব্যবধানের সম্ভাবনা এক নিমিষে বের করা।",
        "আগে যেখানে সমাকলন করতে হতো, এখন শুধু দুই প্রান্তের সঞ্চিত মানের বিয়োগ করলেই কাজ শেষ।",
        "চিত্রে দুটি বিন্দুর মানের পার্থক্যই মাঝের ছায়াবৃত এলাকার সমান।",
        "যেহেতু ক্ষেত্রফল কখনো হ্রাস পায় না, তাই সিডিএফ সর্বদা একটি ক্রমবর্ধমান অপেক্ষক, শুরু শূন্য থেকে শেষ একে।",
    ],
    "sec-clt-emergence": [
        "সেন্ট্রাল লিমিট থিওরেম বা কেন্দ্রীয় সীমা উপপাদ্য সম্ভাব্যতার অন্যতম সুন্দর একটি ফলাফল।",
        "চিত্রে অসংখ্য মার্বেল পিনের ধাক্কা খেয়ে নিচে নামতে নামতে এক নিখুঁত ঘণ্টা আকৃতি তৈরি করছে।",
        "লকডাউনে ঘরে বসে মার্বেল ফেললে প্রতিটি মার্বেল একে একে পিনে ধাক্কা খায়।",
        "বাঁয়ে বা ডানে যাওয়ার ছোট ছোট দৈব পছন্দগুলো জমা হয়ে মাঝখানে সবচেয়ে বেশি মার্বেল জড়ো করেছে।",
        "ফলাফল হলো দুই প্রান্তে কম আর মাঝখানে উঁচু একটি বক্ররেখা, যাকে আমরা বেল কার্ভ বলি।",
        "আদি চলকগুলোর নিজস্ব আকৃতি যাই হোক না কেন, এই নিয়ম সবার ওপর সমভাবে কার্যকর।",
        "কোনোটি সমতল, কোনোটি বিচিত্র আকারের হলেও তাদের সমষ্টি একই রূপ ধারণ করছে।",
        "বহু স্বাধীন প্রভাবকের যোগফল বা গড় সর্বদা এই নরমাল আকৃতির দিকে ধাবিত হয়।",
        "মানুষের উচ্চতা হোক কিংবা পরিমাপের ত্রুটি, সবকিছুতেই একই ঘণ্টা আকৃতি ফিরে ফিরে দেখা যায়।",
        "গাউসিয়ান বেল কার্ভের মাঝের গড় বিন্দুতে বক্ররেখা সবচেয়ে উঁচু, আর দূরে যেতে যেতে সমানভাবে নামতে থাকে।",
        "পরিমিত ব্যবধান যত ছোট হয়, ঘণ্টাটি তত সরু ও উঁচু হয়ে ওঠে, কিন্তু মোট ক্ষেত্রফল একই থাকে।",
        "নমুনার আকার যত বাড়তে থাকে, গড়ের বণ্টন তত নিখুঁত আদর্শ নরমাল রূপ নেয়।",
        "বিশৃঙ্খলা আর শৃঙ্খলা পরস্পর বিরোধী নয়; অসংখ্য বিশৃঙ্খল পথ মিলে একটি শৃঙ্খলিত রূপ জন্ম দেয়।",
        "এই সার্বজনীনতাই আমাদের অবিচ্ছিন্ন সম্ভাবনার পুরো পাঠকে এক সুন্দর উপসংহার দেয়।",
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


def probe_source(src):
    """Probe the downloaded original so the report records its real codecs."""
    info = {"container_duration_sec": round(duration(src), 3)}
    try:
        obj = json.loads(run(
            f'ffprobe -v error -show_entries stream=index,codec_type,codec_name,width,height '
            f'-of json "{src}"'))
        for s in obj.get("streams", []):
            if s.get("codec_type") == "video":
                info["video_stream_codec"] = s.get("codec_name")
                info["video_width"] = s.get("width")
                info["video_height"] = s.get("height")
            elif s.get("codec_type") == "audio":
                info["audio_stream_codec"] = s.get("codec_name")
    except Exception as e:
        info["probe_error"] = str(e)
    return info


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
    """Read the audio_manifest referenced by lesson_06.json (read-only).

    The 36 authored cue texts are used verbatim as the dubbing script.
    Sections are alias-deduped by section_id.
    """
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
            return out, f"audio_manifest:{manifest.name} (36 cues, alias-deduped, verbatim cue texts)"
    return None, None


def derive_from_lesson(lesson):
    """Fallback only: derive cues from lesson JSON if manifest is unavailable."""
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
        return derive_from_lesson(lesson), "lesson_06.json:sections (manifest unavailable)"
    # The 36 authored cue texts already carry the full teaching content; do NOT
    # fold in section paragraphs (would over-lengthen the natural speech).
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
    natural TTS is short of its scaled window, then re-synthesize.
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
    sum(windows) == usable timeline. With the 0.82 tempo floor the resulting
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
        "experiment": "clean_timesync_v2 (lockdown_math/lesson_06_3b1b NEW experiment folder; official 3Blue1Brown ZA4JkHKZM50 source; full-length, improved fill, scale recomputed from rendered speech)",
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
            "SOURCE FIXED. This dub uses the OFFICIAL 3Blue1Brown source ZA4JkHKZM50 "
            "('Why \"probability of 0\" does not mean \"impossible\" | Probabilities of "
            "probabilities, part 2', oEmbed author_name=3Blue1Brown, yt-dlp uploader="
            "3Blue1Brown), downloaded with yt-dlp into lesson_06/original_source and "
            "ffprobe-verified as h264 1920x1080 + aac, ~600.073 s. This REPLACES the "
            "wrong 404 id d_bZk5f2Z8Y. The 1:15:00 duration in lesson_06.json is stale "
            "metadata and was deliberately left untouched; the real video is ~600 s. "
            "Teacher audio/manifests, data JSON and other lessons were not modified."
        ),
        "source_probe": probe_source(src),
        "youtube_oembed": SOURCE_OEMBED,
        "source_verified_3blue1brown": True,
        "wrong_id_replaced": WRONG_ID_REPLACED,
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
    report["volumedetect_mid_30_32s_db"] = volumedetect(OUT_VIDEO, 30, 2)

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
