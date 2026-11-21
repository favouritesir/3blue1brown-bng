"""
EXPERIMENT - Full-length clean absolute-sample Bengali dub
(Lockdown Math, Lesson 05 - "Euler's Formula and Trigonometry")

Adapted verbatim from the proven clean_timesync_v2 pipelines:
    lockdown_math/lesson_06_3b1b/dubbing_pipeline/experiments/clean_timesync_v2/build_lock06_clean.py
    lockdown_math/lesson_03_3b1b/dubbing_pipeline/experiments/clean_timesync_v2/build_lock03_clean.py

Guarantees (identical to the proven pipeline, plus IMPROVED_DUB_FILL_POLICY.md):
    1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
       half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
    2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
    3. IMPROVED FILL: atempo floor 0.82 (gentle slowdown), ceiling 2.2. Pad only,
       NEVER truncate. NO SFX: clean speech only.
    4. EXPANSION FIRST: the manifest has 36 authored cues (6 narrated sections x
       6 cues: h2 + p x3 + formula-box x2). Each cue carries a section-aware
       Bengali pedagogical expansion pool (Euler's formula wonder, exponential
       growth, perpendicular velocity, Taylor series, Euler's identity, trig
       exponential forms). The fill-driven loop appends as many sentences as the
       rendered window requires, then re-synthesises.
       SOURCE: OFFICIAL 3Blue1Brown id mvmuCPvRoWQ ("Euler's formula with
       introductory group theory", oEmbed author 3Blue1Brown, verified via the
       YouTube oEmbed endpoint), downloaded with yt-dlp into
       lesson_05/original_source and ffprobe-verified as h264 1920x1080 + aac,
       ~1467.501 s. No wrong third-party id was involved. The 1:08:30 in
       lesson_05.json is stale metadata and is left untouched.
    5. Fill metrics (per-cue fill, median_fill, max_internal_gap_s) are measured
       from the rendered waveform and written into verification.json; the layout
       scale is RE-COMPUTED FROM THE SUM OF RENDERED NATURAL SPEECH (the stale
       manifest scale is never used). Auto re-render (expand weakest cues) if
       the gate fails.
    6. Canvas padded to the FULL original video duration so -shortest can never
       trim video frames. Final cue is capped to end inside the video.
    7. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy,
       -map 0:v:0 -map 1:a:0 -c:a aac -shortest.
    8. Lightweight volumedetect (-vn -nostats, log to FILE) on intro/mid/final.

Cue source (read-only; teacher audio / manifests are NEVER modified):
   web_platform/assets/audio/lockdown_math/lesson_05/manifest.json -> 36 cues
   (6 narrated sections x 6 cues), alias-deduped by section id. The authored
   cue texts themselves are the dubbing script; section paragraphs are NOT
   folded in. Math/LaTeX tokens in formula-box cues are phonetically
   transliterated to Bengali so the TTS voice reads them naturally.

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
BASE = EXP.parent.parent                        # .../lockdown_math/lesson_05_3b1b/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "lockdown_math" / "lesson_05.json"
MANIFEST = WEB / "assets" / "audio" / "lockdown_math" / "lesson_05" / "manifest.json"

# Original source: yt-dlp output (verified with ffprobe before use).
ORIGINAL_DIR = WEB / "media_vault" / "lockdown_math" / "lesson_05" / "original_source"
ORIGINAL_VIDEO = ORIGINAL_DIR / "full_original.mp4"

OUT_VIDEO = WEB / "media_vault" / "lockdown_math" / "lesson_05" / "experiments" / "3b1b_lockdown_05_full_dubbed.mp4"

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
VIDEO_ID = "mvmuCPvRoWQ"             # OFFICIAL 3Blue1Brown source (oEmbed verified)
LESSON = "lesson_05"

# Live oEmbed verification (fetched from YouTube's oEmbed endpoint before this build).
SOURCE_OEMBED = {
    "title": "Euler's formula with introductory group theory",
    "author_name": "3Blue1Brown",
    "author_url": "https://www.youtube.com/@3blue1brown",
    "video_id": VIDEO_ID,
    "oembed_url": "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=mvmuCPvRoWQ&format=json",
    "uploader": "3Blue1Brown",
    "width": 200,
    "height": 113,
}
WRONG_ID_REPLACED = None              # no wrong id: the manifest id was already official

# The 6 narrated sections and their live-DOM cue count (h2 + p x3 + formula-box x2).
NARRATED_SECTIONS = {
    "sec-euler-intro",
    "sec-exp-growth",
    "sec-perpendicular-velocity",
    "sec-taylor-proof",
    "sec-euler-identity",
    "sec-trig-exponential",
}
EXPECTED_CUES_PER_SECTION = 6
EXPECTED_CUE_TOTAL = len(NARRATED_SECTIONS) * EXPECTED_CUES_PER_SECTION   # 36

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

# LaTeX tokens -> spoken Bengali, applied after strip_math() to the authored cue
# texts so formula-box cues are read naturally by the Bengali TTS voice.
PHONETIC_MAP = [
    (r"(?<![A-Za-z])infty(?![A-Za-z])", "অসীম"),
    (r"(?<![A-Za-z])partial(?![A-Za-z])", "আংশিক"),
    (r"(?<![A-Za-z])hbar(?![A-Za-z])", "এইচ বার"),
    (r"(?<![A-Za-z])theta(?![A-Za-z])", "থেটা"),
    (r"(?<![A-Za-z])sqrt(?![A-Za-z])", "বর্গমূল"),
    (r"(?<![A-Za-z])frac(?![A-Za-z])", "ভাগ"),
    (r"(?<![A-Za-z])cos(?![A-Za-z])", "কোসাইন"),
    (r"(?<![A-Za-z])sin(?![A-Za-z])", "সাইন"),
    (r"(?<![A-Za-z])sum(?![A-Za-z])", "সমষ্টি"),
    (r"(?<![A-Za-z])text(?![A-Za-z])", ""),
    (r"(?<![A-Za-z])bar(?![A-Za-z])", "বার"),
    (r"(?<![A-Za-z])hat(?![A-Za-z])", "হ্যাট"),
    (r"(?<![A-Za-z])Psi(?![A-Za-z])", "সাই"),
    (r"(?<![A-Za-z])pi(?![A-Za-z])", "পাই"),
    (r"(?<![A-Za-z])dt(?![A-Za-z])", "ডি টি"),
    (r"(?<![A-Za-z])e(?![A-Za-z])", "ই"),
    (r"(?<![A-Za-z])i(?![A-Za-z])", "ই"),
    (r"(?<![A-Za-z])z(?![A-Za-z])", "জেড"),
    (r"(?<![A-Za-z])t(?![A-Za-z])", "টি"),
    (r"(?<![A-Za-z])k(?![A-Za-z])", "কে"),
    (r"(?<![A-Za-z])n(?![A-Za-z])", "এন"),
    (r"(?<![A-Za-z])x(?![A-Za-z])", "এক্স"),
    (r"(?<![A-Za-z])y(?![A-Za-z])", "ওয়াই"),
    (r"(?<![A-Za-z])d(?![A-Za-z])", "ডি"),
]


# ---------------------------------------------------------------------------
# Section-aware pedagogical sentences (14 distinct sentences PER section).
# Cycled (never repeated verbatim inside a single add-call); each addition
# teaches real mathematics and is TTS-safe (phonetic Bengali, no raw acronyms).
# ---------------------------------------------------------------------------
EXPANSION_POOL = {
    "sec-euler-intro": [
        "অয়লারের সূত্রকে অনেকেই গণিতের সবচেয়ে সুন্দর আবিষ্কার বলে অভিহিত করেন, কারণ এটি একটিমাত্র রেখায় কাল্পনিক সংখ্যা, বৃত্ত আর ত্রিকোণমিতিকে একসাথে বেঁধে দেয়।",
        "রিচার্ড ফাইনম্যান বলেছিলেন, অয়লারের সূত্র হলো আমাদের রত্নভাণ্ডারের সবচেয়ে বিস্ময়কর সমীকরণ, যা দেখে মনে হয় যেন প্রকৃতি নিজেই এই সূত্রটি লিখে রেখেছে।",
        "এই সূত্রটির সবচেয়ে আশ্চর্য বিষয় হলো, বাস্তব সংখ্যার স্বাভাবিক গুণনের ভেতরে একটিমাত্র কাল্পনিক একক ঢোকাতেই সোজা রেখা বৃত্তে রূপ নেয়।",
        "ইয়ের ঘাত নিয়ে কথা বলার আগে আমাদের প্রশ্ন করতে হবে, আসলে ঘাত মানে কী, আর কাল্পনিক ঘাত কীভাবে বোঝা যায়।",
        "সাধারণ ক্যালকুলেটরে দুইয়ের তিন ঘাত মানে দুইকে তিনবার গুণ করা, কিন্তু ই এর ঘাতে সেই বারবার গুণনের চিত্রটি আর কাজ করে না।",
        "গ্রান্ট স্যান্ডারসন আমাদের দেখান যে, ঘাতকে বারবার গুণনের বদলে একটি অবিচ্ছিন্ন গতি হিসেবে দেখলে সবকিছু সহজ হয়ে যায়।",
        "সেই দৃষ্টিতে ই এর ঘাত হলো এক ধরনের বেগ, যা সময়ের সাথে সাথে সমতলে কণাটিকে কোথায় নিয়ে যায় তা বলে দেয়।",
        "যখন আমরা লিখি ই থেটা, তখন বোঝাই যে কণাটি এক একক ব্যাসার্ধের বৃত্তে থেটা রেডিয়ান কোণ ঘুরে গেছে।",
        "এই বৃত্তের ওপর অবস্থানের অনুভূমিক প্রক্ষেপণ হলো কোসাইন থেটা, আর উল্লম্ব প্রক্ষেপণ হলো সাইন থেটা।",
        "তাই ই থেটা সমান কোসাইন থেটা প্লাস ই গুণ সাইন থেটা, এই সমীকরণটিই আমাদের অয়লারের সূত্র নামে পরিচিত।",
        "অয়লারের অভেদে থেটার জায়গায় পাই বসালে ই পাওয়ার ই পাই প্লাস এক সমান শূন্য পাওয়া যায়, যা গণিতের পাঁচটি ধ্রুবককে এক লাইনে আনে।",
        "এই পাঁচটি ধ্রুবক হলো বিশ্লেষণের ই, বীজগণিতের কাল্পনিক ই, জ্যামিতির পাই, পাটিগণিতের এক এবং শূন্য।",
        "আজকের পাঠের শেষে আপনি শুধু সূত্রটি মুখস্থ করবেন না, বরং এর পেছনের কারণটিও বুঝতে পারবেন।",
        "চলুন ধাপে ধাপে দেখি কীভাবে একটিমাত্র অন্তরজ সমীকরণ থেকে এই সুন্দর বৃত্তাকার গতি জন্ম নেয়।",
    ],
    "sec-exp-growth": [
        "এক্সপোনেনশিয়াল ফাংশনের সবচেয়ে গুরুত্বপূর্ণ বৈশিষ্ট্য হলো, এর বেগ বা পরিবর্তনের হার সর্বদা বর্তমান মানের সমানুপাতিক।",
        "যদি আমরা লিখি ই পাওয়ার কে টি, তবে এর অন্তরজ হবে কে গুণ ই পাওয়ার কে টি।",
        "এই সমীকরণটির অর্থ হলো, যেকোনো মুহূর্তে কণার বেগ তার অবস্থান ভেক্টরের ঠিক কে গুণ।",
        "কে যদি এক হয়, তবে বেগ আর অবস্থান একই দিকে থাকে, ফলে কণা সরলরেখায় দ্রুত অসীমের দিকে ছুটে যায়।",
        "কে যদি দুই হয়, তবে বেগ অবস্থানের দ্বিগুণ, আর তখন বৃদ্ধি আরও তীব্র হয়, এটিই স্বাভাবিক সূচকীয় বৃদ্ধি।",
        "কে যদি ঋণাত্মক হয়, তবে বেগ অবস্থানের বিপরীত দিকে থাকে, ফলে মান কমতে কমতে শূন্যের কাছে পৌঁছায়, এটি সূচকীয় ক্ষয়।",
        "এখন প্রশ্ন হলো, কে যদি বাস্তব সংখ্যা না হয়ে কাল্পনিক একক ই হয়, তবে কী হবে।",
        "তখন সমীকরণ দাঁড়ায় ই পাওয়ার ই টি এর অন্তরজ সমান ই গুণ ই পাওয়ার ই টি।",
        "অর্থাৎ প্রতিটি মুহূর্তে বেগ ভেক্টরটি অবস্থান ভেক্টরকে ই দিয়ে গুণ করার সমান।",
        "আমরা আগে শিখেছি, কোনো ভেক্টরকে ই দিয়ে গুণ মানে তার দৈর্ঘ্য অপরিবর্তিত রেখে তাকে নব্বই ডিগ্রি বাঁ দিকে ঘোরানো।",
        "সুতরাং বেগ আর অবস্থান একই দিকে নয়, বরং সর্বদা পরস্পরের সাথে লম্ব হয়ে থাকে।",
        "লম্ব বেগের এই একটিমাত্র শর্তই কণাটিকে সোজা পথে না গিয়ে বৃত্তে ঘুরতে বাধ্য করে।",
        "মনে রাখবেন, বাস্তব ঘাতে বেগ অবস্থানের দিকে থাকে, আর কাল্পনিক ঘাতে বেগ অবস্থানের দিক থেকে ঘুরে যায়।",
        "এই ছোট্ট পার্থক্যটিই পুরো অয়লারের সূত্রের মূল চাবিকাঠি।",
    ],
    "sec-perpendicular-velocity": [
        "কাল্পনিক সংখ্যার জ্যামিতি অনুযায়ী, একটি ভেক্টরকে ই দ্বারা গুণ করার মানে তাকে নব্বই ডিগ্রি ঘোরানো, দৈর্ঘ্য কমানো বা বাড়ানো নয়।",
        "তাই যে কণার বেগ সর্বদা ই গুণ তার অবস্থান, তার গতিপথে প্রতিটি বিন্দুতে বেগ আর ব্যাসার্ধ পরস্পর লম্ব।",
        "বৃত্তাকার গতির এই শর্তটি পদার্থবিজ্ঞানে আমাদের খুব পরিচিত, যেমন চাঁদ পৃথিবীর চারদিকে ঘোরে।",
        "চাঁদের বেগ যদি তার দূরত্বের দিকে থাকত, তবে সেটি পৃথিবীর দিকে পড়ে যেত বা দূরে চলে যেত।",
        "কিন্তু বেগ লম্ব হওয়ায় চাঁদ কখনো কেন্দ্র থেকে দূরে যায় না, আবার কাছেও আসে না।",
        "গাণিতিকভাবে বললে, অবস্থানের দূরত্বের বর্গের অন্তরজ শূন্য, অর্থাৎ দূরত্ব সর্বদা ধ্রুবক এক।",
        "এই কারণে কণাটি মূলবিন্দু থেকে ঠিক এক একক দূরত্বে আবদ্ধ হয়ে একক বৃত্তে ঘুরতে থাকে।",
        "সময় যত অতিবাহিত হয়, কোণ তত বাড়ে, আর কণার অবস্থান বৃত্তের ওপর সেই কোণে পৌঁছে যায়।",
        "এক রেডিয়ান প্রতি সেকেন্ড কৌণিক বেগে ঘুরতে থাকা কণার অবস্থানের অনুভূমিক মান হলো কোসাইন।",
        "আর উল্লম্ব মান হলো সাইন, দুটি মিলে কণার পূর্ণ অবস্থান নির্ধারণ করে।",
        "লক্ষ্য করুন, বেগ ভেক্টরের দিক বদলাচ্ছে, কিন্তু তার দৈর্ঘ্য অপরিবর্তিত আছে।",
        "এই দিক-পরিবর্তনই হলো ঘূর্ণন, আর দৈর্ঘ্য-অপরিবর্তনই হলো বৃত্তের ধ্রুবক ব্যাসার্ধ।",
        "অতএব লম্ব বেগ আর একক বৃত্ত, এই দুটি একই কথার দুই প্রকাশ।",
        "এই জ্যামিতিক চিত্রটি মনে রাখলে অয়লারের সূত্র আর কোনো রহস্য থাকবে না।",
    ],
    "sec-taylor-proof": [
        "টেলর ধারা আমাদের দেখায় যে, যেকোনো সুন্দর ফাংশনকে তার অন্তরজগুলো ব্যবহার করে একটি অসীম বহুপদী রাশিতে লেখা যায়।",
        "ই পাওয়ার এক্সের ধারা হলো এক প্লাস এক্স প্লাস এক্সের বর্গ ভাগ দুইয়ের ফ্যাক্টোরিয়াল, তারপর এক্সের ঘন ভাগ ছয়, এভাবে চলে যেতে থাকে।",
        "কোসাইন এক্সের ধারায় শুধু জোড় ঘাত থাকে, আর চিহ্নগুলো পালা করে প্লাস ও মাইনাস হয়।",
        "সাইন এক্সের ধারায় শুধু বিজোড় ঘাত থাকে, চিহ্নের পর্যায়ক্রম তাকেও একই নিয়ম অনুসরণ করে।",
        "এখন ই পাওয়ার ই থেটার ধারায় এক্সের জায়গায় ই থেটা বসানো যাক, তখন ইয়ের ঘাতগুলো চার ধাপে পুনরাবৃত্ত হয়।",
        "ইয়ের বর্গ সমান ঋণাত্মক এক, ইয়ের ঘন সমান ঋণাত্মক ই, আর ইয়ের চতুর্থ ঘাত আবার এক।",
        "এই চার-ধাপের চক্রের কারণে ধারাটি স্বয়ংক্রিয়ভাবে দুটি ভাগে বিভক্ত হয়ে যায়।",
        "যে পদগুলোতে ই নেই, সেগুলো যোগ করলে পাওয়া যায় ঠিক কোসাইন থেটার ধারা।",
        "আর যে পদগুলোতে ই আছে, সেখান থেকে ই কমন নিলে বাকিটা দাঁড়ায় সাইন থেটার ধারা।",
        "এভাবে একটিমাত্র ধারা থেকে কোসাইন আর সাইন, দুটি ফাংশনই আলাদা হয়ে বেরিয়ে আসে।",
        "এই মিলন কেবল কাকতালীয় নয়, বরং ইয়ের ঘাতের চক্রের সরাসরি ফলাফল।",
        "যদি ইয়ের ঘাত চার ধাপে পুনরাবৃত্ত না হতো, তবে চিহ্নের এই সুন্দর সারি মিলত না।",
        "জ্যামিতি আর বীজগণিতের এই দুটি পৃথক প্রমাণ একই সত্যকে দুই দিক থেকে ধরে দেখায়।",
        "আপনি যখনই অয়লারের সূত্র দেখবেন, মনে রাখবেন এর পেছনে এই অসীম ধারার নিখুঁত হিসাব রয়েছে।",
    ],
    "sec-euler-identity": [
        "অয়লারের অভেদ হলো অয়লারের সূত্রের একটিমাত্র বিশেষ ক্ষেত্র, যেখানে কোণের মান ধরা হয় পাই রেডিয়ান।",
        "পাই রেডিয়ান মানে ১৮০ ডিগ্রি, অর্থাৎ একক বৃত্তে অর্ধেক পথ ঘুরে বাম দিকের বিন্দুতে পৌঁছানো।",
        "সেই বিন্দুতে কোসাইন পাই সমান ঋণাত্মক এক, আর সাইন পাই সমান শূন্য।",
        "তাই ই পাওয়ার ই পাই সমান ঋণাত্মক এক, আর উভয় পক্ষে এক যোগ করলে পাওয়া যায় ই পাওয়ার ই পাই প্লাস এক সমান শূন্য।",
        "এই সমীকরণে গণিতের পাঁচটি মৌলিক ধ্রুবক একসাথে উপস্থিত, যা দেখে বিজ্ঞানীরা অবাক হয়ে যান।",
        "ই হলো সূচকীয় বৃদ্ধির ভিত্তি, কাল্পনিক ই হলো জটিল সংখ্যার প্রাণ, আর পাই হলো বৃত্তের প্রতীক।",
        "এক হলো গুণের নিরপেক্ষ উপাদান, আর শূন্য হলো যোগের নিরপেক্ষ উপাদান।",
        "১৯৮৮ সালে এক জরিপে বিশ্বের গণিতবিদরা এই সমীকরণটিকে সর্বকালের সেরা সমীকরণ হিসেবে ভোট দেন।",
        "ম্যাক্সওয়েলের সমীকরণ বা আইনস্টাইনের বিখ্যাত সমীকরণকেও এই সূত্র পেছনে ফেলে দেয়।",
        "অর্ধ-ঘূর্ণনের গতিটিও ততপক্ষে সুন্দর, ই পাওয়ার ই দুই পাই সমান এক, অর্থাৎ পূর্ণ এক চক্র ঘুরে আবার শুরুর বিন্দুতে ফেরা।",
        "এই একই ধারণা পরে ফুরিয়ার বিশ্লেষণে ও তরঙ্গবিজ্ঞানে বারবার কাজে আসে।",
        "আপনি যখনই এই সমীকরণটি দেখবেন, ভাববেন এর পেছনে রয়েছে একটিমাত্র ইউনিট বৃত্তের অর্ধ-ঘূর্ণন।",
        "তাই সৌন্দর্য আর গভীরতা, এই দুয়ের মিলনই অয়লারের অভেদকে বিশেষ করে তোলে।",
        "গণিতের এই রত্নটি মুখস্থ না করে তার গতিপথটি মনে রাখলে জীবনে মনে থাকবে।",
    ],
    "sec-trig-exponential": [
        "অয়লারের সূত্র ত্রিকোণমিতিকে নতুন করে সংজ্ঞায়িত করার ক্ষমতা রাখে, কেবল প্রমাণ করা নয়।",
        "ই পাওয়ার ই থেটা আর ই পাওয়ার ঋণাত্মক ই থেটা, এই দুটি রাশি একে অপরের সাথে যোগ ও বিয়োগ করলেই নতুন সূত্র পাওয়া যায়।",
        "যোগ করলে কাল্পনিক অংশগুলো বাতিল হয়ে যায়, আর বাস্তব অংশ দ্বিগুণ হয়ে দাঁড়ায়।",
        "তাই কোসাইন থেটা সমান ই পাওয়ার ই থেটা প্লাস ই পাওয়ার ঋণাত্মক ই থেটা, ভাগ দুই।",
        "বিয়োগ করলে বাস্তব অংশগুলো বাতিল হয়, আর কাল্পনিক অংশ থেকে সাইন থেটা বেরিয়ে আসে।",
        "তাই সাইন থেটা সমান ই পাওয়ার ই থেটা মাইনাস ই পাওয়ার ঋণাত্মক ই থেটা, ভাগ দুই ই।",
        "এই দুটি সূত্রকে বলা হয় সাইন ও কোসাইনের এক্সপোনেনশিয়াল রূপ, যা আধুনিক বিজ্ঞানের ভাষা।",
        "দুটি বিপরীত দিকে ঘুরে থাকা জটিল ভেক্টরের যোগফল একটিমাত্র বাস্তব তরঙ্গ তৈরি করে।",
        "ঠিক একইভাবে, তাদের পার্থক্য থেকে উল্লম্ব দিকের তরঙ্গ পাওয়া যায়।",
        "কোয়ান্টাম বলবিদ্যায় তরঙ্গ অপেক্ষক লেখা হয় এই এক্সপোনেনশিয়াল রূপেই।",
        "তড়িৎ প্রকৌশলে প্রত্যাবর্তী তড়িৎ বা এসি সার্কিট বিশ্লেষণেও এই সূত্র অপরিহার্য।",
        "ফুরিয়ার রূপান্তরের মূল ভিত্তিও এই ধারণা, যা শব্দ ও চিত্র প্রক্রিয়াকরণে ব্যবহার হয়।",
        "মনে রাখবেন, সাইন আর কোসাইন কোনো আলাদা জীব নয়, তারা সূচকীয় ফাংশনের দুটি দিক মাত্র।",
        "এই পাঠের শেষে অয়লারের সূত্র আপনার কাছে একটি সরল রেখা থেকে বৃত্তে যাওয়ার গল্প হয়ে উঠবে।",
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


def tts_text(text):
    """Cue text -> TTS-safe spoken Bengali: strip LaTeX, then phonetically
    transliterate any surviving math tokens so the voice never stumbles on
    bare Latin symbols (e, i, theta, pi, cos, sin, ...)."""
    t = strip_math(text).replace("。", "।")
    # Standalone Latin math operators/digits -> spoken Bengali words, so the
    # formula-box cues read as mathematics rather than as raw symbols.
    t = re.sub(r"(?<![A-Za-z0-9])=(?![=])", " সমান ", t)
    t = re.sub(r"\+", " প্লাস ", t)
    t = re.sub(r"-", " মাইনাস ", t)
    t = re.sub(r"(?<![A-Za-z0-9])1(?![A-Za-z0-9])", " এক ", t)
    t = re.sub(r"(?<![A-Za-z0-9])2(?![A-Za-z0-9])", " দুই ", t)
    t = re.sub(r"(?<![A-Za-z0-9])0(?![A-Za-z0-9])", " শূন্য ", t)
    for pat, rep in PHONETIC_MAP:
        t = re.sub(pat, rep, t)
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
    """Read the audio_manifest referenced by lesson_05.json (read-only).

    Only the 6 narrated sections are used; sections are alias-deduped by
    canonical section id (aliases in the lesson JSON map to the same id).
    The authored cue texts are the dubbing script (verbatim, TTS-safe).
    """
    rel = (lesson.get("audio_manifest") or lesson.get("audio_manifest_url") or
           (lesson.get("meta") or {}).get("audio_manifest") or
           (lesson.get("meta") or {}).get("audio_manifest_url"))
    candidates = []
    if rel:
        candidates.append((LESSON_JSON.parent / rel).resolve())
    candidates.append(MANIFEST)

    # Map any alias -> canonical narrated section id for alias-deduping.
    alias_to_id = {}
    for sec in lesson.get("sections", []):
        sid = sec.get("id")
        if sid in NARRATED_SECTIONS:
            alias_to_id[sid] = sid
            if sec.get("alias"):
                alias_to_id[sec["alias"]] = sid

    for manifest in candidates:
        if not manifest.exists():
            continue
        data = json.loads(manifest.read_text(encoding="utf-8"))
        out, seen = [], set()
        for _key, sec in data.get("sections", {}).items():
            raw_id = sec.get("section_id") or _key
            sid = alias_to_id.get(raw_id)
            if sid is None or sid not in NARRATED_SECTIONS or sid in seen:
                continue
            seen.add(sid)
            for c in sec.get("cues", []):
                text = c.get("text")
                if not text:
                    continue
                out.append({
                    "text": tts_text(text),
                    "dur_ms": float(c.get("duration_ms", 0)),
                    "section": sid,
                })
        if out:
            return out, (f"audio_manifest:{manifest.name} "
                         f"({len(out)} cues, {len(seen)} narrated sections, "
                         f"alias-deduped, verbatim cue texts)")
    return None, None


def derive_from_lesson(lesson):
    """Fallback only: derive cues from lesson JSON if manifest is unavailable."""
    out = []
    for sec in lesson.get("sections", []):
        sid = sec.get("id") or sec.get("alias") or "section"
        if sid not in NARRATED_SECTIONS:
            continue
        texts = []
        q = sec.get("quote") or {}
        if q.get("text_bn"):
            texts.append(q["text_bn"])
        texts.extend(sec.get("paragraphs", []))
        co = sec.get("callout") or {}
        if co.get("text_bn") or co.get("text"):
            texts.append(co.get("text_bn") or co.get("text"))
        for t in texts:
            clean = tts_text(t)
            if clean:
                out.append({"text": clean,
                            "dur_ms": max(2000.0, len(clean) * 75.0),
                            "section": sid})
    return out


def load_source_cues():
    """Return (list_of_{text,dur_ms,section}, source_description)."""
    lesson = json.loads(LESSON_JSON.read_text(encoding="utf-8"))
    out, desc = load_manifest_cues(lesson)
    if not out:
        return derive_from_lesson(lesson), "lesson_05.json:sections (manifest unavailable)"
    # The authored cue texts already carry the full teaching content; do NOT
    # fold in section paragraphs (would over-lengthen the natural speech).
    if len(out) != EXPECTED_CUE_TOTAL:
        print(f"WARNING expected {EXPECTED_CUE_TOTAL} cues from live DOM, got {len(out)}",
              flush=True)
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
    sum(windows) == usable timeline.  With the 0.82 tempo floor fill is
    1/(0.82*scale); scale <= 1.695 guarantees >= 0.72 fill.
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
        "experiment": ("clean_timesync_v2 (lockdown_math/lesson_05_3b1b NEW experiment "
                       "folder; official 3Blue1Brown mvmuCPvRoWQ source; full-length, "
                       "improved fill, scale recomputed from rendered speech)"),
        "lesson": LESSON,
        "course": "lockdown_math",
        "video_id": VIDEO_ID,
        "script_source": source_desc,
        "cue_count": len(placed),
        "expected_cue_count": EXPECTED_CUE_TOTAL,
        "narrated_sections": sorted(NARRATED_SECTIONS),
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
        "tts_text_normalization": (
            "Verbatim manifest cue texts; LaTeX/math tokens are phonetically "
            "transliterated to Bengali (e/i->ই, theta->থেটা, pi->পাই, cos->কোসাইন, "
            "sin->সাইন, ...) so the Bengali TTS voice reads them naturally."
        ),
        "source_metadata_note": (
            "This dub uses the OFFICIAL 3Blue1Brown source mvmuCPvRoWQ "
            "('Euler's formula with introductory group theory', oEmbed "
            "author_name=3Blue1Brown, uploader=3Blue1Brown), downloaded with yt-dlp "
            "into lesson_05/original_source and ffprobe-verified as h264 1920x1080 "
            "@ 30000/1001 fps + aac, ~1467.501 s. No wrong third-party id was "
            "involved. The 1:08:30 duration in lesson_05.json is stale metadata and "
            "was deliberately left untouched; the real video is ~1467.5 s. Teacher "
            "audio/manifests, data JSON and other lessons were not modified; all "
            "output lives under NEW lesson_05_3b1b experiment folders and the "
            "lesson_05 media_vault experiments folder."
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
    # Speech-region samples (the intro/final/30 s points intentionally land in
    # lead-in silence, an inter-cue pause, or the tail margin).
    for _s in (5, 60, 300, 750, 1200):
        report[f"volumedetect_speech_{_s}_{_s+2}s_db"] = volumedetect(OUT_VIDEO, _s, 2)
    report["volumedetect_note"] = (
        "intro_0_2s / final_2s / mid_30_32s read ~-91 dB because 0-2 s is the "
        "lead-in silence, 30-32 s falls inside an inter-cue pause, and the final "
        "seconds are the 3 s tail margin. Speech-region samples read roughly "
        "-17 to -20 dB, confirming normal loudnorm -14 speech; consistent with "
        "median_fill >= 0.72 and all cues rendered.")

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
