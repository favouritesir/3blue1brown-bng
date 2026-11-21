"""
EXPERIMENT (fill_v2) — Full-length clean absolute-sample Bengali dub
(Essence of Linear Algebra, Lesson 14 — "Eigenvectors and Eigenvalues", PFDu9oVAE-g)

RE-RENDER of the earlier clean_timesync_v2 dub, which left 24 silent pockets
(up to ~41 s each): that build stretched 23 section-based master-script cues
by 2.82x and pinned atempo at 1.0, so most of every window was dead air.

This build follows the quality-gated, scale-recomputed policy proven in:
    neural_networks/lesson_01_intro/dubbing_pipeline/experiments/fill_v2/build_nn01_fill2.py
and web_platform/governance/IMPROVED_DUB_FILL_POLICY.md:

  1. Read the AUDIO MANIFEST
     (web_platform/assets/audio/linear_algebra/lesson_14/manifest.json) as the
     dubbing script — 23 cues across 4 sections, alias-deduped by section key
     and by cue text. Teacher audio/manifests are NEVER modified.
  2. edge_tts bn-BD-PradeepNeural; robust retries (0-byte purge, 12 attempts,
     half-split + sentence-split fallbacks, WinError 1450 retry).
  3. STRONG EXPANSION: every cue is grown with section-aware pedagogical
     Bengali sentences until the SUM of rendered natural speech spans the real
     probed video duration. Only NEW audio is synthesized per append
     (incremental concat), so the run is resumable and not O(n^2).
  4. Recompute the timeline scale from the SUM OF RENDERED NATURAL SPEECH
     (never from authored manifest durations). Windows become proportional to
     each cue's measured TTS duration. With the 0.82 atempo floor the rendered
     fill is ~1.0 (tempo = 1/scale, well under the 2.2 ceiling).
  5. Absolute sample placement start*44100 -> ZERO cumulative drift. Pad only,
     NEVER truncate. NO SFX: clean speech only. Long in-cue silences are
     gently compressed.
  6. QUALITY GATE measured from the rendered waveform:
       median_fill >= 0.72,
       max_internal_gap_s <= 1.5,
       ffmpeg silencedetect internal silence runs > 2 s == 0
     with automatic extra-expansion + re-render if any gate fails.
  7. Canvas padded to the FULL original video duration so -shortest can never
     trim video frames; final cue capped to end inside the video.
  8. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
     The video source is NEVER swapped — the same original_source/full_original.mp4
     is reused.
  9. Lightweight volumedetect (-vn -nostats, log to FILE) on intro and final.

Everything new is written under NEW experiment folders:
    script/metadata : essence_of_linear_algebra/lesson_14_eigenvectors/dubbing_pipeline/experiments/fill_v2/
    output video    : web_platform/media_vault/lesson_14/experiments/fill_v2/
The previous video (experiments/3b1b_lesson_14_full_dubbed.mp4) is left untouched
as backup. No teacher audio, manifest, master script or other lesson is touched.
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
BASE = EXP.parent.parent                        # .../lesson_14_eigenvectors/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform

MANIFEST = WEB / "assets" / "audio" / "linear_algebra" / "lesson_14" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_14" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "lesson_14" / "experiments" / "fill_v2" / "3b1b_lesson_14_full_dubbed_fill2.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
GATE_WAV = EXP / "_gate_master.wav"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
MIN_TEMPO = 0.82                     # IMPROVED_DUB_FILL_POLICY.md
FADE_MS = 12
VIDEO_ID = "PFDu9oVAE-g"
LESSON = "lesson_14_eigenvectors"
COURSE = "linear_algebra"

LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0           # only used for the initial manifest layout

# Expansion / gate policy.
EXPAND_TARGET_FILL = 0.98
TARGET_NATURAL_SCALE = 1.10          # sum(natural) ~= usable / 1.10 -> tempo ~= 0.91
MAX_APPENDED_SENTENCES = 120
ACTIVE_THRESHOLD = 0.015
MAX_INTERNAL_SILENCE_S = 0.9         # compress in-cue pauses longer than this
CHARS_PER_CHUNK = 1700

# QUALITY GATE (task requirement).
GATE_MEDIAN_FILL = 0.72
GATE_MAX_INTERNAL_GAP = 1.5
GATE_SILENCE_RUN_LIMIT = 2.0         # silencedetect internal runs > 2 s must be 0
SILENCE_NOISE_DB = "-45dB"
SILENCE_DETECT_D = 1.5
MAX_RENDER_ROUNDS = 5

SOURCE_METADATA_NOTE = {
    "youtube_id": VIDEO_ID,
    "source_url": "https://www.3blue1brown.com/lessons/eigenvalues",
    "script_source": "web_platform/assets/audio/linear_algebra/lesson_14/manifest.json "
                     "(23 cues across 4 sections, alias-deduped)",
    "video_source": "web_platform/media_vault/lesson_14/original_source/full_original.mp4 "
                    "(NOT swapped)",
    "reason_for_rerender": "prior clean_timesync_v2 build left 24 silent pockets "
                           "(up to ~41 s); atempo was pinned to 1.0 on 2.82x-stretched windows",
    "teacher_audio_and_manifests_modified": False,
}

# ---------------------------------------------------------------------------
# Section-aware pedagogical Bengali sentences. Cycled (never repeated
# back-to-back inside one append) so every addition teaches real content.
# Phonetic safeguards: ল্যাম্বডা, আই হ্যাট, জে হ্যাট, এক্স অক্ষ, ম্যাট্রিক্স, ইত্যাদি।
# ---------------------------------------------------------------------------
EXPANSION_POOL = {
    "sec_01_geometric_intuition": [
        "আইগেনভেক্টরের ধারণাটি আসলে রূপান্তরের ভেতরে লুকোনো এক ধরনের স্থিরতা; যখন পুরো সমতল প্রসারিত বা মোচড় খায়, অধিকাংশ তীর নতুন দিকে মুখ করে, কিন্তু কয়েকটি তীর নিজের রেখাতেই দাঁড়িয়ে থাকে।",
        "ম্যাট্রিক্সকে একটি যন্ত্র হিসেবে ভাবুন যা প্রতিটি বিন্দুকে নতুন জায়গায় পাঠায়; মূলবিন্দু সবসময় নিজের জায়গাতেই থাকে, আর গ্রিডের সমান্তরাল রেখাগুলো সমান্তরালই থাকে—এই দুটি শর্তই একটি রূপান্তরকে রৈখিক করে তোলে।",
        "আই হ্যাট আর জে হ্যাট হলো আমাদের দুটি ভিত্তি ভেক্টর; কোনো ম্যাট্রিক্স এই দুটির ওপর কী কাজ করে, তা জানলেই পুরো রূপান্তরের ছবি মেলে।",
        "তিন এক, শূন্য দুই ম্যাট্রিক্সে আই হ্যাট তিনগুণ হয়ে এক্স অক্ষেই থাকে, আর জে হ্যাট সরে যায় এক কমা দুই বিন্দুতে।",
        "জে হ্যাটের কোনো অংশ আগের জায়গায় থাকে না, বরং সেটি নতুন দিকে ঝুঁকে পড়ে; এই পার্থক্যটিই আমাদের বলে দেয় কোন দিকগুলো অটল আছে।",
        "যে ভেক্টরের স্প্যান রেখা রূপান্তরের পরেও অপরিবর্তিত থাকে, তাকেই আমরা আইগেনভেক্টর বলি; জার্মান শব্দ আইগেন মানে নিজস্ব, নামটিই ধারণাটির গল্প বলে দেয়।",
        "আইগেনভ্যালু হলো সেই গুণক, যা বলে দেয় ভেক্টরটি কতখানি প্রসারিত বা সংকুচিত হয়েছে; ল্যাম্বডা তিন মানে তিনগুণ লম্বা, ল্যাম্বডা আধা মানে অর্ধেক।",
        "ঋণাত্মক ল্যাম্বডাকে ভয় পাবেন না; ভেক্টরটি ঠিক নিজস্ব রেখাতেই থাকে, শুধু বিপরীত দিকে মুখ করে, তাই একশো আশি ডিগ্রি ঘোরা সত্ত্বেও এটি এখনো আইগেনভেক্টর।",
        "এ ভি সমান ল্যাম্বডা ভি—এই ছোট্ট সমীকরণটিই পুরো অধ্যায়ের ভিত্তি; বাম পাশে ম্যাট্রিক্স গুণন আর ডান পাশে সাধারণ সংখ্যা গুণন, এই মিলই আইগেনভেক্টরের সংজ্ঞা।",
        "ভি অবশ্যই শূন্য নয়, কারণ শূন্য ভেক্টর সব রেখাতেই থাকে—তাকে নিয়ে কোনো তথ্য পাওয়া যায় না; তাই আমরা অশূন্য ভেক্টর খুঁজি।",
        "ল্যাম্বডা ধনাত্মক হলে দিক একই থাকে, শূন্যের কাছাকাছি হলে ভেক্টরটি প্রায় মুছে যায়, আর একের বড় হলে সেটি প্রসারিত হয়।",
        "মূলবিন্দু দিয়ে যে সরলরেখা ভেক্টরটির ডগা দিয়ে যায়, তাকে তার স্প্যান বলা হয়; অধিকাংশ ভেক্টর রূপান্তরে এই রেখা ছেড়ে নতুন কোণে চলে যায়।",
        "আমাদের উদাহরণে এক্স অক্ষের সব ভেক্টর তিন গুণ হয়, তাই তাদের আইগেনভ্যালু তিন; আর এক কমা মাইনাস এক বরাবর কর্ণের ভেক্টররা দুই গুণ হয়, ল্যাম্বডা দুই।",
        "জ্যামিতিকভাবে ভাবলে আইগেনভেক্টর হলো রূপান্তরের সেই বিন্দুগুলো যারা নিজেদের পরিচয় হারায় না; শুধু দৈর্ঘ্য বদলায়, দিক নয়।",
        "এই কারণেই আইগেনভেক্টর খোঁজা মানে হলো এমন বিশেষ দিক খোঁজা, যার ওপর ম্যাট্রিক্সের কাজ কেবল একটি সংখ্যা দ্বারা গুণ করে লেখা যায়।",
        "পরের ধাপে আমরা দেখব এই সরল গুণটির ধর্ম ব্যবহার করে এক ম্যাট্রিক্সের শততম ঘাত কত সহজে বের করা যায়।",
    ],
    "sec_02_characteristic_equation": [
        "প্রশ্ন ওঠে, কোনো প্রদত্ত ম্যাট্রিক্সের আইগেনভেক্টর আর আইগেনভ্যালু কীভাবে খুঁজে পাব; প্রতীকীভাবে লিখি এ ভি সমান ল্যাম্বডা ভি।",
        "বাম পাশে আছে ম্যাট্রিক্স ও ভেক্টরের গুণন, ডান পাশে সাধারণ স্কেলার গুণন—দুই ধরনের গুণ একই সমীকরণে বসানোয় প্রথমে একটু অস্বস্তি লাগতে পারে।",
        "এই অস্বস্তিটি দূর করতে ডান পাশের ল্যাম্বডা ভি কে লিখি ল্যাম্বডা আই গুণ ভি; আই হলো কর্ণে এক ও বাকি সব জায়গায় শূন্য বিশিষ্ট আইডেন্টিটি ম্যাট্রিক্স।",
        "আইডেন্টিটি ম্যাট্রিক্স কোনো ভেক্টরকেই বদলায় না; তাই ল্যাম্বডা আই গুণ ভি আগের ল্যাম্বডা ভি-রই মতো, কেবল লেখার ধরন বদলেছে।",
        "এখন ডান পাশের পদটিকে বামে নিয়ে এলে পাই বন্ধনীতে এ মাইনাস ল্যাম্বডা আই, গুণ ভি সমান শূন্য ভেক্টর।",
        "অর্থাৎ একটি নতুন ম্যাট্রিক্স ভেক্টর ভি কে শূন্যে চ্যাপ্টা করে দিচ্ছে; আমরা এমন অশূন্য ভি খুঁজছি যেটি চ্যাপ্টা হতে পারে।",
        "একটি ম্যাট্রিক্স যদি পুরো স্থানকে নিচু মাত্রায় নামিয়ে না আনে, তবে শুধু তুচ্ছ সমাধান ভি সমান শূন্যই পাওয়া যায়—আর তা আমাদের কাজে আসে না।",
        "স্থান চ্যাপ্টা হওয়ার মানে হলো নির্ণায়ক শূন্য; এই শর্তই বলে দেয় ডিটারমিন্যান্ট অফ এ মাইনাস ল্যাম্বডা আই সমান শূন্য।",
        "একে বলা হয় চারিত্রিক সমীকরণ; এটি কেবল একটি বীজগাণিতিক কৌশল নয়, বরং জ্যামিতিক চ্যাপ্টাকরণের ভাষান্তর।",
        "উদাহরণস্বরূপ দুই দুই, এক তিন ম্যাট্রিক্স নিলে পাই দুই মাইনাস ল্যাম্বডা গুণ তিন মাইনাস ল্যাম্বডা বিয়োগ দুই সমান শূন্য।",
        "ল্যাম্বডা কে নবের মতো ঘুরালে দেখা যায় মূলদ্বয় এক আর চার; প্রতিটি মূলের সাথে একটি করে আইগেন রেখা যুক্ত।",
        "প্রথম উদাহরণে ফিরে আসি—তিন এক, শূন্য দুই ম্যাট্রিক্সের নির্ণায়ক তিন মাইনাস ল্যাম্বডা গুণ দুই মাইনাস ল্যাম্বডা।",
        "থেকে পাই ল্যাম্বডা দুই অথবা ল্যাম্বডা তিন; দুটি মূল মানে দুটি স্বাধীন আইগেন দিক, ঠিক যা আমরা চিত্রে দেখেছিলাম।",
        "ল্যাম্বডা দুই বসালে এক এক, শূন্য শূন্য ম্যাট্রিক্স পাই, আর এক্স ওয়াই গুণ করে শূন্য পেতে হলে এক্স সমান মাইনাস ওয়াই।",
        "অর্থাৎ এক কমা মাইনাস এক বরাবর রেখার সব ভেক্টরই আইগেনভেক্টর; বীজগণিত আর জ্যামিতি এখানে হাত মিলিয়েছে।",
        "ব্যবহারিকভাবে আগে চারিত্রিক সমীকরণ থেকে ল্যাম্বডা বের করা হয়, তারপর নাল স্পেস থেকে সংশ্লিষ্ট ভি পাওয়া যায়—এই দুই ধাপই পুরো পদ্ধতি।",
    ],
    "sec_03_special_transformations": [
        "সব ম্যাট্রিক্সের কি বাস্তব আইগেনভেক্টর থাকে? না—সবচেয়ে সুন্দর ব্যতিক্রম হলো নব্বই ডিগ্রি ঘূর্ণন।",
        "শূন্য মাইনাস এক, এক শূন্য ম্যাট্রিক্স প্রতিটি ভেক্টরকে তার নিজস্ব রেখা থেকে নব্বই ডিগ্রি সরে যেতে বাধ্য করে।",
        "ফলে কোনো ভেক্টরই নিজের স্প্যানে থাকে না; জ্যামিতিকভাবে এটি একেবারে স্পষ্ট, কোনো তীর আগের দিকে ফিরে আসছে না।",
        "বীজগণিতও একই কথা বলে: এই ঘূর্ণনের চারিত্রিক সমীকরণ ল্যাম্বডা বর্গ প্লাস এক সমান শূন্য।",
        "এর মূল কেবল জটিল সংখ্যা প্লাস মাইনাস আই; বাস্তব মূলের অনুপস্থিতিই বলে দেয় বাস্তব আইগেনভেক্টর নেই।",
        "একে জটিল আইগেনভ্যালু বলা হয়; জ্যামিতিকভাবে এর অর্থ হলো রূপান্তরটি কেবল স্কেল নয়, একটি অতিরিক্ত ঘূর্ণনও ঘটায়।",
        "অন্য দিকে শিয়ার ম্যাট্রিক্স এক এক, শূন্য এক—এখানে আই হ্যাট স্থির থাকে আর জে হ্যাট ডানে সরে।",
        "কেবল এক্স অক্ষের ভেক্টরাই নিজেদের রেখায় থাকে; নির্ণায়ক এক মাইনাস ল্যাম্বডার বর্গ থেকে একমাত্র ল্যাম্বডা এক।",
        "অর্থাৎ শিয়ারের একটি মাত্র আইগেন রেখা আছে, বাকি সব দিকেই ভেক্টরগুলো ঘুরে যায়।",
        "আর দুই আই ম্যাট্রিক্স সব দিকে সমান দুই গুণ করে; তাই সমতলের প্রতিটি ভেক্টরই ল্যাম্বডা দুই সহ আইগেনভেক্টর।",
        "এখানে একটিমাত্র আইগেনভ্যালু আর অসীম সংখ্যক আইগেনভেক্টর—পরিস্থিতি আগের ঘূর্ণনের ঠিক বিপরীত।",
        "তিন ধরনের আচরণ এক নজরে মনে রাখুন: ঘূর্ণনে কোনো বাস্তব আইগেনভেক্টর নেই, শিয়ারে একটি, আর স্কেলিংয়ে প্রতিটি ভেক্টরই আইগেনভেক্টর।",
        "ল্যাম্বডা মাইনাস এক ভাগের দুইয়ের মতো ঋণাত্মক ক্ষেত্রে ভেক্টরটি উল্টে অর্ধেক হয়, দিক বদলালেও সে নিজস্ব রেখাতেই থাকে।",
        "তাই দিক উল্টানোটা কোনো সমস্যা নয়; আসল কথা হলো ভেক্টরটি যেন তার নিজের রেখা থেকে না সরে।",
        "ঘূর্ণন, শিয়ার আর স্কেলিং—এই তুলনাটি মনে রাখলে পরের অংশের আইগেনবেসিস বোঝা অনেক সহজ হবে।",
        "ম্যাট্রিক্সের এই তিনটি আচরণ আমাদের বলে দেয় কোনটি সুবিধাজনক ভিত্তি গড়ে তুলতে পারবে, আর কোনটি পারবে না।",
    ],
    "sec_04_3d_rotations_and_eigenbasis": [
        "ত্রিমাত্রিক স্পেসে আইগেনভেক্টরের ধারণা আরও প্রাণবন্ত; মূলবিন্দুগামী কোনো অক্ষকে কেন্দ্র করে পুরো স্থান আবর্তিত হলে অক্ষের ওপরের ভেক্টরগুলোর দিক বা দৈর্ঘ্য বিন্দুমাত্র বদলায় না।",
        "অর্থাৎ ঘূর্ণন ম্যাট্রিক্স গুণ অক্ষ ভেক্টর সমান এক গুণ অক্ষ ভেক্টর; এই অক্ষই হলো ঘূর্ণনের আইগেনভেক্টর, আর এর আইগেনভ্যালু এক।",
        "চারপাশের বিন্দুগুলো সরে গেলেও এই অক্ষ অপরিবর্তিত থাকে; তাই থ্রি বাই থ্রি ম্যাট্রিক্সের জটিল ত্রিকোণমিতিক সদস্যের চেয়ে এই একটি রেখা খুঁজে পাওয়া অনেক বেশি স্বজ্ঞাত।",
        "এই চিত্রে ত্রিমাত্রিক ঘূর্ণনের মাঝখান দিয়ে বের হওয়া সরলরেখাটিই ঘূর্ণন অক্ষ; এর ওপর অবস্থিত তীরগুলো ঘোরালেও অক্ষের দিকে কোনো নাড়া খায় না।",
        "ঘূর্ণন অক্ষের ধারণাটি আমাদের দেখায় যে জটিল গণনার বদলে একটি সরল জ্যামিতিক সত্য খুঁজে নেওয়া যায়—আর এটি গণিতের সবচেয়ে শক্তিশালী অভ্যাস।",
        "আইগেনবেসিস মানে যথেষ্ট স্বাধীন আইগেনভেক্টর দিয়ে পুরো স্থান স্প্যান করা; তখন তাদের নতুন ভিত্তি হিসেবে বেছে নেওয়া যায়।",
        "এই ভিত্তিতে মূল রূপান্তরটি একটি ডায়াগনাল ম্যাট্রিক্সে রূপ নেয়, কারণ প্রতিটি ভিত্তি ভেক্টর কেবল নিজের আইগেনভ্যালু দ্বারা স্কেল হয়, অন্যদের সাথে মিশে যায় না।",
        "ফলে শততম ঘাত লেখা যায় তিন শূন্য, শূন্য দুই ম্যাট্রিক্সের একশততম ঘাত সমান তিনের একশততম ঘাত ও দুইয়ের একশততম ঘাত।",
        "অথচ মূল ম্যাট্রিক্সকে একশত বার গুণ করতে হলে কত খাটুনি লাগত ভাবুন; আইগেনবেসিস আমাদের সেই খাটুনি থেকে বাঁচায়।",
        "ভিত্তি পরিবর্তনের সূত্রটি মনে করুন: নতুন ম্যাট্রিক্স সমান এ ইনভার্স গুণ এম গুণ এ।",
        "আইগেনভেক্টরগুলোকে কলাম করে গঠিত পরিবর্তন ম্যাট্রিক্স এস দিলে ডি সমান এস ইনভার্স গুণ এ গুণ এস, অর্থাৎ ল্যাম্বডা।",
        "একই রূপান্তর শুধু আইগেনবেসিসের ভাষায় লেখা; তাই এ এর একশততম ঘাত সমান এস গুণ ল্যাম্বডার একশততম ঘাত গুণ এস ইনভার্স।",
        "সহজে ঘাত বের করে আবার আমাদের ভাষায় ফিরে আসা—এই তিন ধাপই আইগেনবেসিসের ব্যবহারিক শক্তি।",
        "কিন্তু সব রূপান্তরের এই সুবিধা পাওয়া যায় না; শিয়ারের মতো ম্যাট্রিক্সের পর্যাপ্ত স্বাধীন আইগেনভেক্টর নেই, তাই তার আইগেনবেসিস গড়ে ওঠে না।",
        "কৌতূহলীদের জন্য পাজল: শূন্য এক, এক এক ম্যাট্রিক্সের প্রথম কয়েকটি ঘাত বের করলে ফিবোনাচ্চি সংখ্যা এক, এক, দুই, তিন, পাঁচ, আট দেখা যায়।",
        "এর আইগেনভ্যালু এক প্লাস বর্গমূল পাঁচ ভাগ দুই ব্যবহার করে ঘাতের সংকেত বের করা যায়—পরবর্তী অধ্যায়ে এই কৌশলটি আরও পরিশীলিত হবে।",
    ],
}
DEFAULT_EXPANSIONS = [
    "এই ধারণাটি নিজের ভাষায় একবার বলে দেখলে বিষয়টি আরও পরিচ্ছন্ন হবে।",
    "লক্ষ্য করুন, এই অনুপাতই আমাদের আসল উত্তরের দিকে নিয়ে যায়।",
    "এখানে যুক্তিটি আবার মনে করিয়ে দিই, কারণ পরের ধাপে এটি বারবার কাজে লাগবে।",
]


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
# Cue loading — AUDIO MANIFEST IS THE DUBBING SCRIPT (read-only)
# ---------------------------------------------------------------------------
def load_source_cues():
    """Read web_platform/assets/audio/linear_algebra/lesson_14/manifest.json.

    Sections are de-duplicated by key (alias-deduped) and cue texts are
    de-duplicated as well. Cue texts are used verbatim as the dubbing script.
    """
    if not MANIFEST.exists():
        raise SystemExit(f"MANIFEST NOT FOUND: {MANIFEST}")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out, seen_sec, seen_text = [], set(), set()
    for _key, sec in data.get("sections", {}).items():
        sid = sec.get("section_id") or _key
        if sid in seen_sec:
            continue
        seen_sec.add(sid)
        for c in sec.get("cues", []):
            text = c.get("text")
            if not text:
                continue
            key = sanitize(text)
            if key in seen_text:
                continue
            seen_text.add(key)
            dur = float(c.get("duration_ms", 0))
            if dur <= 0 and c.get("end_ms") is not None and c.get("start_ms") is not None:
                dur = float(c["end_ms"]) - float(c["start_ms"])
            out.append({"text": text, "dur_ms": dur, "section": sid})
    if not out:
        raise SystemExit(f"NO CUES IN MANIFEST: {MANIFEST}")
    return out, (f"audio_manifest:{MANIFEST.name} "
                 f"(alias-deduped + text-deduped, {len(out)} cues)")


def load_cues(vend, source_cues):
    """Initial manifest-based layout (later RECOMPUTED from rendered speech)."""
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
        if valid(raw):
            print(f"  TTS {i+1}/{len(cues)} CACHED (natural={duration(raw):.1f}s)", flush=True)
            continue
        ok = await synth_cue(sanitize(c["bn"]), raw)
        if not ok:
            failed.append(c["id"])
            print(f"  WARNING cue {c['id']} failed after every fallback", flush=True)
        print(f"  TTS {i+1}/{len(cues)} (chars={len(c['bn'])}, natural={duration(raw):.1f}s)", flush=True)
    return failed


def pick_append(pool, start_idx, need_chars, max_n):
    """Pick distinct pool sentences until need_chars is covered (cycling)."""
    picked, total, i = [], 0, start_idx
    while total < need_chars and len(picked) < max_n:
        s = pool[i % len(pool)]
        picked.append(s)
        total += len(s) + 1
        i += 1
    return " ".join(picked), (i - start_idx)


async def append_audio(text, raw, tag):
    """Synthesize ONLY `text` and concat onto existing `raw` MP3 (no O(n^2))."""
    tmp = RAW_DIR / f"append_{raw.stem}_{tag}.mp3"
    if not await synth_cue(sanitize(text), tmp):
        return False
    lf = RAW_DIR / f"applist_{raw.stem}_{tag}.txt"
    with open(lf, "w", encoding="utf-8") as f:
        f.write(f"file '{raw.as_posix()}'\n")
        f.write(f"file '{tmp.as_posix()}'\n")
    out = RAW_DIR / f"merged_{raw.stem}_{tag}.mp3"
    run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{out}" > NUL 2>&1')
    if not valid(out):
        return False
    os.replace(out, raw)
    return True


async def expand_short_cues(cues, vend):
    """STRONG expansion: grow every cue until the SUM of rendered natural
    speech spans the real video. Per-cue target = usable / N / TARGET_SCALE.
    """
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    per_cue_target = (usable / len(cues)) / TARGET_NATURAL_SCALE
    expanded = []
    print(f"  expansion target per cue = {per_cue_target:.1f}s "
          f"(usable={usable:.1f}s, cues={len(cues)})", flush=True)
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        meta = RAW_DIR / f"expand_meta_{cid:03d}.json"
        natural = duration(raw)
        if natural <= 0:
            continue
        before = natural
        if natural >= per_cue_target and meta.exists():
            cached = json.loads(meta.read_text(encoding="utf-8"))
            expanded.append({
                "id": cid, "section": c["section"], "cached": True,
                "natural_before": cached.get("natural_before"),
                "natural_after": round(natural, 3),
                "sentences_added": cached.get("sentences_added"),
                "final_chars": cached.get("final_chars"),
                "target_sec": round(per_cue_target, 3),
            })
            continue
        pool = EXPANSION_POOL.get(c["section"], DEFAULT_EXPANSIONS)
        base = sanitize(c["bn"])
        added = 0
        for rnd in range(10):
            if natural >= per_cue_target or added >= MAX_APPENDED_SENTENCES:
                break
            rate_sec_per_char = natural / max(len(base), 1)
            need_chars = max(250, int((per_cue_target - natural) / max(rate_sec_per_char, 0.01)))
            append_text, n_sent = pick_append(pool, added, need_chars, MAX_APPENDED_SENTENCES - added)
            if not append_text:
                break
            print(f"  expand cue {cid} rnd{rnd}: natural={natural:.1f}s "
                  f"target={per_cue_target:.1f}s +{n_sent} sent", flush=True)
            if not await append_audio(append_text, raw, rnd):
                break
            added += n_sent
            natural = duration(raw)
            base = sanitize(base + " " + append_text)
        if added > 0 and natural > 0:
            c["bn"] = sanitize(base)
            entry = {
                "id": cid, "section": c["section"],
                "natural_before": round(before, 3),
                "natural_after": round(natural, 3),
                "sentences_added": added,
                "final_chars": len(base),
                "target_sec": round(per_cue_target, 3),
            }
            meta.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
            expanded.append(entry)
    return expanded, per_cue_target


# ---------------------------------------------------------------------------
# Waveform helpers
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


def compress_long_silences(arr, sr=SR, thr=ACTIVE_THRESHOLD, max_sil=MAX_INTERNAL_SILENCE_S):
    """Gently remove the excess of any in-cue silence longer than max_sil."""
    a = np.abs(arr)
    quiet = (a <= thr).astype(np.int8)
    quiet[0] = 0
    quiet[-1] = 0
    d = np.diff(quiet)
    starts = np.flatnonzero(d == 1) + 1
    ends = np.flatnonzero(d == -1) + 1
    limit = int(max_sil * sr)
    keep = [(0, len(arr))]
    for s, e in sorted(zip(starts, ends), reverse=True):
        run_len = int(e) - int(s)
        if run_len > limit:
            cut_from, cut_to = int(s) + limit, int(e)
            new_keep = []
            for ks, ke in keep:
                if ke <= cut_from or ks >= cut_to:
                    new_keep.append((ks, ke))
                else:
                    if ks < cut_from:
                        new_keep.append((ks, cut_from))
                    if ke > cut_to:
                        new_keep.append((cut_to, ke))
            keep = new_keep
    parts = [arr[s:e] for s, e in keep if e > s]
    return np.concatenate(parts) if parts else arr


def write_canvas_wav(canvas, path, chunk=1_000_000):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        for i in range(0, len(canvas), chunk):
            w.writeframes(canvas[i:i + chunk].tobytes())


def internal_silence_runs(path, vend):
    """ffmpeg silencedetect: internal silence runs longer than the gate limit.

    The deliberate lead-in (0 .. LEAD_IN_SEC) and tail (last TAIL_MARGIN_SEC)
    are boundary silence and are excluded. Returns a list of dicts.
    """
    log = EXP / "_silencedetect.log"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-nostats", "-i", str(path),
           "-af", f"silencedetect=noise={SILENCE_NOISE_DB}:d={SILENCE_DETECT_D}",
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
    starts = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", txt)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([\d.]+)", txt)]
    runs = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else vend
        runs.append((s, e, e - s))
    internal = []
    for s, e, d in runs:
        if (d > GATE_SILENCE_RUN_LIMIT and s >= LEAD_IN_SEC - 0.10
                and e <= max(0.0, vend - TAIL_MARGIN_SEC) + 0.10):
            internal.append({"start": round(s, 3), "end": round(e, 3),
                             "duration": round(d, 3)})
    return internal


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
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" '
        f'-ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)
    arr = compress_long_silences(arr)
    fit_samples = len(arr)
    need = int(round(target * SR))
    if len(arr) < need:
        arr = np.pad(arr, (0, need - len(arr)))
    # If still longer (tempo cap), keep it -> recorded as overrun, never cut.
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(arr, -1, 1) * 32767).astype("<i2").tobytes())
    try:
        os.remove(tmp)
    except OSError:
        pass
    return arr, tempo, natural, target, fit_samples


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


def recompute_layout_from_naturals(cues, vend):
    """Re-derive timeline scale from SUM OF RENDERED NATURAL SPEECH (not manifest).

    Windows are proportional to each cue's measured TTS duration so
    sum(windows) == usable timeline. With the 0.82 tempo floor the resulting
    waveform fill is ~1.0 (tempo = 1/scale, capped at 2.2 on the fast side).
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


async def expand_cue_more(cue, extra_s, expanded_log, tag):
    """Append more section-aware sentences to a weak cue (quality gate)."""
    cid = cue["id"]
    raw = RAW_DIR / f"raw_{cid:03d}.mp3"
    pool = EXPANSION_POOL.get(cue["section"], DEFAULT_EXPANSIONS)
    text = sanitize(cue["bn"])
    nat = duration(raw)
    rate = nat / max(len(text), 1)
    need_chars = max(300, int(extra_s / max(rate, 0.01)))
    append_text, n = pick_append(pool, len(text), need_chars, 80)
    if not append_text:
        return nat
    print(f"  extra-expand cue {cid}: +{n} sent (extra_s={extra_s:.1f})", flush=True)
    if await append_audio(append_text, raw, f"q{tag}"):
        cue["bn"] = sanitize(text + " " + append_text)
        expanded_log.append({
            "id": cid, "section": cue["section"], "round": "quality_gate",
            "sentences_added": n, "final_chars": len(cue["bn"]),
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
            "id": cid, "section": c["section"],
            "expected_start_ms": expected_ms, "actual_start_ms": actual_ms,
            "drift_ms": round(actual_ms - expected_ms, 6),
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3), "target_sec": round(target, 3),
            "fit_samples": fit_samples, "window_samples": window_samples,
            "fill": round(fill, 4), "max_internal_gap_s": round(gap_s, 4),
            "placed_samples": placed_len, "expanded": cid in expanded_ids,
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
        alts = sorted((ORIGINAL_VIDEO.parent).glob("full_original.*"))
        if alts:
            src = alts[0]
    if not src.exists():
        alts = sorted((ORIGINAL_VIDEO.parent.parent).glob("full_original*.mp4"))
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

    print("[2/7] STRONG expansion driven by real video duration ...", flush=True)
    expanded, per_cue_target = await expand_short_cues(cues, vend)
    print(f"  expanded {len(expanded)} cues", flush=True)

    print("[3/7] Recompute timeline scale from RENDERED natural speech ...", flush=True)
    scale, naturals = recompute_layout_from_naturals(cues, vend)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"  natural_total={sum(naturals):.1f}s -> scale={scale:.4f} "
          f"(was {initial_scale:.4f} from manifest)", flush=True)
    print("  windows:", ", ".join(f"{c['id']}={c['duration']:.1f}s" for c in cues), flush=True)

    print("[4/7] Absolute placement + QUALITY GATE (median/gap/silencedetect) ...", flush=True)
    render_round = 0
    gate_history = []
    canvas, placed, overrun, last_cue_end, CHUNK = None, [], 0, 0.0, 1_000_000
    while True:
        render_round += 1
        canvas, placed, overrun, last_cue_end, CHUNK = render_canvas(
            cues, vend, [x["id"] for x in expanded])
        median_fill, max_internal_gap = fill_metrics(placed)
        write_canvas_wav(canvas, GATE_WAV)
        internal_runs = internal_silence_runs(GATE_WAV, vend)
        gate_ok = (median_fill >= GATE_MEDIAN_FILL
                   and max_internal_gap <= GATE_MAX_INTERNAL_GAP
                   and len(internal_runs) == 0)
        gate_history.append({
            "round": render_round,
            "scale": round(scale, 6),
            "median_fill": median_fill,
            "max_internal_gap_s": max_internal_gap,
            "silencedetect_internal_runs_over_2s": len(internal_runs),
            "internal_runs_detail": internal_runs[:10],
            "gate_ok": gate_ok,
        })
        print(f"  round {render_round}: median_fill={median_fill} "
              f"max_gap={max_internal_gap}s silencedetect_runs={len(internal_runs)} "
              f"gate_ok={gate_ok}", flush=True)
        if gate_ok or render_round >= MAX_RENDER_ROUNDS:
            break

        # Auto re-render: (a) expand the weakest-fill cues, (b) expand any cue
        # adjacent to a >2 s internal silence run, then recompute scale.
        weak = sorted(placed, key=lambda x: x["fill"])[:3]
        fix_ids = {w["id"] for w in weak}
        for r in internal_runs:
            near = min(cues, key=lambda c: abs(c["start"] - r["start"]))
            fix_ids.add(near["id"])
        for cid in sorted(fix_ids):
            cue = next((c for c in cues if c["id"] == cid), None)
            if cue is None:
                continue
            rec = next((x for x in placed if x["id"] == cid), None)
            deficit = 45.0
            if rec is not None:
                deficit = max(45.0, (0.90 - rec["fill"]) * rec["target_sec"] * 2.0)
            await expand_cue_more(cue, deficit, expanded,
                                  f"g{render_round}_{cid}")
        scale, naturals = recompute_layout_from_naturals(cues, vend)
        LAST_START = float(cues[-1]["start"])

    print("[5/7] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    gate_ok = (median_fill >= GATE_MEDIAN_FILL
               and max_internal_gap <= GATE_MAX_INTERNAL_GAP
               and len(internal_runs) == 0)
    report = {
        "experiment": "fill_v2 (linear_algebra lesson_14 full-length, heavy expansion, "
                      "scale recomputed from rendered speech, silencedetect-gated)",
        "lesson": LESSON,
        "course": COURSE,
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
        "video_source_path": str(src),
        "video_source_swapped": False,
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "fill_policy": {
            "expand_target_fill": EXPAND_TARGET_FILL,
            "target_natural_scale": TARGET_NATURAL_SCALE,
            "per_cue_target_sec": round(per_cue_target, 3),
            "median_fill": median_fill,
            "median_fill_target": GATE_MEDIAN_FILL,
            "median_fill_ok": median_fill >= GATE_MEDIAN_FILL,
            "max_internal_gap_s": max_internal_gap,
            "max_internal_gap_target": GATE_MAX_INTERNAL_GAP,
            "max_internal_gap_ok": max_internal_gap <= GATE_MAX_INTERNAL_GAP,
            "max_internal_silence_compression_s": MAX_INTERNAL_SILENCE_S,
        },
        "silencedetect": {
            "noise_db": SILENCE_NOISE_DB,
            "detect_d": SILENCE_DETECT_D,
            "internal_run_limit_s": GATE_SILENCE_RUN_LIMIT,
            "internal_runs_over_limit": len(internal_runs),
            "internal_runs_detail": internal_runs[:20],
            "ok": len(internal_runs) == 0,
        },
        "quality_gate": {
            "median_fill_ok": median_fill >= GATE_MEDIAN_FILL,
            "max_internal_gap_ok": max_internal_gap <= GATE_MAX_INTERNAL_GAP,
            "silencedetect_ok": len(internal_runs) == 0,
            "passed": gate_ok,
        },
        "median_fill": median_fill,
        "max_internal_gap_s": max_internal_gap,
        "silencedetect_internal_runs_over_2s": len(internal_runs),
        "gate_history": gate_history,
        "expanded_cues": expanded,
        "source_metadata_note": SOURCE_METADATA_NOTE,
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

    # Independent silencedetect on the FINAL muxed audio (authoritative).
    final_runs = internal_silence_runs(OUT_VIDEO, vend)
    report["final_video_silencedetect_internal_runs_over_2s"] = len(final_runs)
    report["final_video_silencedetect_detail"] = final_runs[:20]
    report["final_video_silencedetect_ok"] = len(final_runs) == 0

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
          f"silencedetect_runs={len(internal_runs)} gate_ok={gate_ok}", flush=True)
    print(f"final_video_silencedetect_runs={len(final_runs)}", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
