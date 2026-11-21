"""
EXPERIMENT (fill_v2) — Full-length clean absolute-sample Bengali dub
(Essence of Linear Algebra, Lesson 03 — "Linear transformations and matrices", kYB8IZa5AuE)

RE-RENDER of the earlier clean_timesync_v2 dub, which left 36 silent pockets
(up to ~12 s each). This build applies the quality-gated, scale-recomputed
policy of the proven fill_v2 line, which is the clean_timesync_v2 pipeline
(from essence_of_calculus/lesson_08_integration/.../build_calc08_clean.py)
extended with recompute-scale-from-rendered-speech + a hard quality gate:

  1. Read the AUDIO MANIFEST
     (web_platform/assets/audio/linear_algebra/lesson_03/manifest.json) as the
     dubbing script — 32 cues across 4 sections, alias-deduped by section key
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
    script/metadata : essence_of_linear_algebra/lesson_03_linear_transformations/dubbing_pipeline/experiments/fill_v2/
    output video    : web_platform/media_vault/lesson_03/experiments/fill_v2/
The previous video (experiments/3b1b_lesson_03_full_dubbed.mp4) is left untouched
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
BASE = EXP.parent.parent                        # .../lesson_03_linear_transformations/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform

MANIFEST = WEB / "assets" / "audio" / "linear_algebra" / "lesson_03" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_03" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "lesson_03" / "experiments" / "fill_v2" / "3b1b_lesson_03_full_dubbed_fill2.mp4"

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
VIDEO_ID = "kYB8IZa5AuE"
LESSON = "lesson_03_linear_transformations"
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
    "source_url": "https://www.3blue1brown.com/lessons/linear-transformations",
    "script_source": "web_platform/assets/audio/linear_algebra/lesson_03/manifest.json "
                     "(32 cues across 4 sections, alias-deduped)",
    "video_source": "web_platform/media_vault/lesson_03/original_source/full_original.mp4 "
                    "(NOT swapped)",
    "reason_for_rerender": "prior clean_timesync_v2 build left 36 silent pockets "
                           "(up to ~12 s); windows were manifest-stretched with atempo pinned near 1.0",
    "teacher_audio_and_manifests_modified": False,
}

# ---------------------------------------------------------------------------
# Section-aware pedagogical Bengali sentences. Cycled (never repeated
# back-to-back inside one append) so every addition teaches real content.
# Phonetic safeguards: আই হ্যাট, জে হ্যাট, এক্স অক্ষ, ওয়াই অক্ষ, ম্যাট্রিক্স, ভেক্টর, ইত্যাদি।
# ---------------------------------------------------------------------------
EXPANSION_POOL = {
    "sec_01_transformations": [
        "রূপান্তর বলতে আমরা এমন এক নিয়ম বুঝি যা প্রতিটি ইনপুট ভেক্টরকে একটি নির্দিষ্ট আউটপুট ভেক্টরে পাঠায়; যেমন সাধারণ ফাংশন একটি সংখ্যাকে আরেকটি সংখ্যায় বদলে দেয়, তেমনি এখানে ভেক্টরই ভেক্টরে রূপ নেয়।",
        "আমাদের পরিচিত ফাংশন ইনপুট সংখ্যা নিয়ে আউটপুট সংখ্যা দেয়, কিন্তু রৈখিক বীজগণিতে ইনপুট আর আউটপুট দুটোই ভেক্টর; আর তাই একে ফাংশনের চেয়ে রূপান্তর নামে ডাকা হয়।",
        "রূপান্তর শব্দটি আমাদের মনে এক ধরনের গতির ছবি আঁকে—যেন পুরো সমতলটিই নড়াচড়া করছে, মোচড় খাচ্ছে কিংবা প্রসারিত হচ্ছে; এই জ্যামিতিক অনুভূতিই বিষয়টি বোঝার চাবিকাঠি।",
        "কোনো ভেক্টরকে ইনপুট হিসেবে নিলে রূপান্তর সেটিকে একটি নতুন অবস্থানে পাঠায়; এই নতুন ভেক্টরটিকেই আমরা বলি আউটপুট বা রূপান্তরিত ভেক্টর।",
        "প্রতিটি বিন্দু একই নিয়ম অনুসরণ করে নড়ে, তাই আগে যে দুটি বিন্দু কাছাকাছি ছিল রূপান্তরের পরেও তারা কাছাকাছিই থাকে; এই ধারাবাহিকতাই রূপান্তরকে নিয়মবদ্ধ করে।",
        "পুরো তলটিকে ভেক্টরের তীর না দেখে কেবল বিন্দুর সমষ্টি হিসেবে দেখুন; যখন সব বিন্দু একসাথে সরে, তখন তলের ওপর আঁকা গ্রিডটি একটি নতুন আকার ধারণ করে।",
        "মূলবিন্দু হলো সেই বিশেষ বিন্দু যা কোনো রৈখিক রূপান্তরে নিজের জায়গাতেই থাকে; এটি সব ভেক্টরের গতির এক ধরনের নোঙর বিন্দু।",
        "আই হ্যাট আর জে হ্যাট হলো আমাদের দুটি ভিত্তি ভেক্টর; পরের পাঠে আমরা দেখব এই দুটির ওপর কী কাজ করা হয়, তা জানলেই পুরো রূপান্তরের ছবি পাওয়া যায়।",
        "একটি রূপান্তরকে বোঝার সবচেয়ে সহজ উপায় হলো কয়েকটি নির্দিষ্ট ভেক্টরের গতি লক্ষ্য করা; একটির পর একটির গতি দেখলে পুরো তলের আচরণ নিজেই পরিষ্কার হয়ে যায়।",
        "মনে রাখবেন, রূপান্তর কোনো বস্তুকে ধ্বংস করে নতুন কিছু তৈরি করে না; আগের ভেক্টরটি নতুন দিকে ও নতুন দৈর্ঘ্যে মাত্র রূপ নেয়।",
        "এই কারণেই জ্যামিতিক দৃশ্য আর বীজগাণিতিক নিয়ম একে অপরের পরিপূরক; এক দিকে ছবি, অন্য দিকে সূত্র—দুই মিলে রূপান্তর সম্পর্কে পূর্ণ ধারণা জন্মায়।",
        "ঘূর্ণন, প্রসারণ আর মোচড়—এসবই রূপান্তরের উদাহরণ; প্রতিটিতে ভেক্টররা আলাদা আলাদা ভাবে নড়ে, কিন্তু নিয়ম একটিই থাকে।",
        "যখন আমরা বলি তলটি প্রসারিত হচ্ছে, তার মানে প্রতিটি বিন্দু মূলবিন্দু থেকে দূরে সরে যাচ্ছে; দিক একই থাকলেও দৈর্ঘ্য বেড়ে যায়।",
        "একই ভাবে যখন তলটি মোচড় খায়, তখন ভেক্টরের দিক বদলায় কিন্তু মূলবিন্দু অটল থাকে; এই দুই ধরনের পরিবর্তন আলাদা করে চেনা যায়।",
        "আসুন একটি সরল উদাহরণ নিই: প্রতিটি বিন্দুকে তার এক্স অক্ষের মান অনুযায়ী ডানে সরানো; দেখা যাবে পুরো গ্রিড একই নিয়মে টানা পড়ে।",
        "পরের ধাপে আমরা এই রূপান্তরগুলোর নির্দিষ্ট নিয়ম খুঁজব এবং দেখব কীভাবে মাত্র কয়েকটি সংখ্যা দিয়ে পুরো তলের রূপান্তর বর্ণনা করা যায়।",
    ],
    "sec_02_linearity": [
        "একটি রূপান্তরকে রৈখিক বলা যায় যখন মূলবিন্দু নিজের জায়গাতেই থাকে এবং গ্রিডের সমান্তরাল রেখাগুলো রূপান্তরের পরেও সমান্তরালই থাকে।",
        "রৈখিকতার প্রথম শর্ত হলো মূলবিন্দু অটল থাকা; যদি মূলবিন্দু সরে যায়, তবে রূপান্তরটি রৈখিক নয়—এটি সবচেয়ে সহজ পরীক্ষা।",
        "দ্বিতীয় শর্ত হলো সমান্তরাল আর সমান দূরত্বের রেখাগুলো রূপান্তরের পরেও সমান্তরাল ও সমান দূরত্বে থাকা; অর্থাৎ গ্রিডের কোষগুলো টানা বা চ্যাপ্টা হলেও বাঁকা হয় না।",
        "আরেকটি ভাষায় বললে, রৈখিকতা মানে দুটি ভেক্টরের যোগফলের ওপর রূপান্তরের কাজ আগে যোগ করে পরে রূপান্তর করার সমান—একে বলা হয় যোগ সংরক্ষণ।",
        "একই ভাবে কোনো ভেক্টরকে আগে স্কেল করে রূপান্তর করলে যা পাওয়া যায়, আগে রূপান্তর করে স্কেল করলেও তা-ই পাওয়া যায়; একে বলা হয় স্কেল সংরক্ষণ।",
        "এই দুটি শর্ত একসাথে মিলে রৈখিকতার সংজ্ঞা তৈরি করে; জ্যামিতিক ছবি আর বীজগাণিতিক নিয়ম এখানে একই কথা বলে।",
        "নব্বই ডিগ্রি ঘূর্ণন একটি রৈখিক রূপান্তর, কারণ মূলবিন্দু স্থির থাকে আর গ্রিডের রেখাগুলো ঘুরলেও সমান্তরালই থাকে।",
        "দুই গুণ প্রসারণও রৈখিক; প্রতিটি ভেক্টর দ্বিগুণ হয়, কিন্তু গ্রিডের কোষগুলোর আকার ছাড়া তাদের গঠন অপরিবর্তিত থাকে।",
        "শিয়ার বা বিকৃতিও রৈখিক—এখানে ওয়াই অক্ষের মান অনুযায়ী ভেক্টররা ডানে সরে, কিন্তু অনুভূমিক রেখাগুলো অনুভূমিকই থাকে।",
        "অন্যদিকে কোনো রূপান্তর যদি গ্রিডের রেখাগুলোকে বাঁকা করে, তবে সেটি রৈখিক নয়; বক্রতা এসে যাওয়া মানেই জ্যামিতির সরলতা হারানো।",
        "আর যদি মূলবিন্দু নিজের জায়গা ছেড়ে অন্য কোথাও চলে যায়, তবে সেই রূপান্তরকেও আমরা রৈখিক বলব না—সেটি হবে কেবল স্থানান্তর।",
        "রৈখিক রূপান্তরের এই বৈশিষ্ট্যগুলোই আমাদের পরবর্তীতে ম্যাট্রিক্স গুণনের নিয়ম বের করতে সাহায্য করে; নিয়মটি আসলে এই সংরক্ষণশীলতারই প্রতিফলন।",
        "আই হ্যাট ও জে হ্যাটের ওপর রূপান্তরের কাজ জানলে যেকোনো ভেক্টরের কাজ বের করা যায়, কারণ প্রতিটি ভেক্টরই এ দুটির রৈখিক সমন্বয়।",
        "মনে রাখবেন, রৈখিকতা কোনো জটিল শর্ত নয়; এটি কেবল বলে যে রূপান্তরটি গ্রিডের গঠন ভেঙে দেয় না, শুধু টানে, ঘোরায় বা চ্যাপ্টা করে।",
        "আসুন মনে করি একটি ভেক্টর আই হ্যাট ও জে হ্যাটের তিন আর দুই গুণ; রূপান্তরের পর এর নতুন অবস্থান আগের দুটি ভিত্তি ভেক্টরের নতুন অবস্থান থেকে বের করা যায়।",
        "পরের ধাপে আমরা ঠিক এই ধর্মটি ব্যবহার করে রূপান্তরকে কয়েকটি সংখ্যার ছকে লিখব, যার নাম ম্যাট্রিক্স।",
    ],
    "sec_03_basis_tracking": [
        "পুরো তলের অসংখ্য ভেক্টরের গতি এক এক করে লেখা অসম্ভব; তাই আমরা কেবল দুটি বিশেষ ভেক্টরের গতি ট্র্যাক করি—আই হ্যাট আর জে হ্যাট।",
        "আই হ্যাট হলো এক্স অক্ষ বরাবর একক দৈর্ঘ্যের ভেক্টর, আর জে হ্যাট হলো ওয়াই অক্ষ বরাবর একক ভেক্টর; এ দুটিকে বলা হয় ভিত্তি ভেক্টর।",
        "রূপান্তরের পর আই হ্যাট কোথায় পড়ে আর জে হ্যাট কোথায় পড়ে—এই দুটি তথ্যই পুরো রূপান্তরটি বর্ণনা করতে যথেষ্ট।",
        "কারণ যেকোনো ভেক্টর আসলে আই হ্যাট আর জে হ্যাটের একটি রৈখিক সমন্বয়; যেমন তিন আই হ্যাট প্লাস দুই জে হ্যাট মানে তিন এক্স অক্ষ আর দুই ওয়াই অক্ষ।",
        "রূপান্তর রৈখিক হওয়ায় এই সমন্বয়টি অটল থাকে; তাই নতুন ভেক্টরটি হবে আই হ্যাটের নতুন অবস্থানের তিন গুণ প্লাস জে হ্যাটের নতুন অবস্থানের দুই গুণ।",
        "অর্থাৎ ভিত্তি ভেক্টরদ্বয়ের নতুন অবস্থান জানলেই যেকোনো ইনপুট ভেক্টরের আউটপুট বের করা যায়—এটি পুরো অধ্যায়ের কেন্দ্রীয় ধারণা।",
        "উদাহরণস্বরূপ, আই হ্যাট যদি এক কমা এক বিন্দুতে পড়ে আর জে হ্যাট যদি মাইনাস এক কমা এক বিন্দুতে পড়ে, তবে পুরো তলটি ঘুরে ও প্রসারিত হয়।",
        "এই দুটি নতুন অবস্থানকে সরলরেখা দিয়ে যুক্ত করলে দেখা যায় মূল একক বর্গটি কীভাবে নতুন রূপ নিয়েছে—সেটিই রূপান্তরের জ্যামিতিক ছবি।",
        "আগের বর্গ আর নতুন বর্গের ক্ষেত্রফলের অনুপাত আমাদের বলে দেয় ক্ষেত্রফল কতগুণ বদলেছে; পরে এই সংখ্যাটিকে আমরা ডিটারমিন্যান্ট নাম দেব।",
        "আই হ্যাটের নতুন অবস্থানের এক্স এবং ওয়াই মান, আর জে হ্যাটের নতুন অবস্থানের এক্স ওয়াই মান—এই চারটি সংখ্যাই রূপান্তরটি সম্পূর্ণরূপে বর্ণনা করে।",
        "এই চারটি সংখ্যাকে একটি ছকে সাজালেই তৈরি হয় দুই বাই দুই ম্যাট্রিক্স; ম্যাট্রিক্স মানে কেবল সংখ্যার ছক নয়, এটি রূপান্তরের নির্দেশনাপত্র।",
        "প্রথম কলামটি আই হ্যাটের গল্প বলে, দ্বিতীয় কলামটি জে হ্যাটের গল্প বলে; কলাম দুটিকে মিলিয়ে পুরো রূপান্তরের গল্প পড়া যায়।",
        "মনে রাখবেন, ভিত্তি ভেক্টরের পছন্দ আমাদের নিজেদের; কিন্তু একবার পছন্দ করলে রূপান্তরের বিবরণ সম্পূর্ণ নির্দিষ্ট হয়ে যায়।",
        "যদি আই হ্যাট ও জে হ্যাট একই রেখায় পড়ে, তবে পুরো তলটি এক মাত্রায় চ্যাপ্টা হয়ে যায়; এই অবস্থায় ক্ষেত্রফল শূন্য হয়।",
        "আর যদি তারা আগের মতোই দুটি স্বাধীন দিকে থাকে, তবে রূপান্তরটি তলকে নতুন আকারে সাজায় কিন্তু তার দ্বিমাত্রিক প্রকৃতি রক্ষা করে।",
        "পরের ধাপে আমরা এই চারটি সংখ্যার ছকটিকে একটি নির্দিষ্ট লেখার রীতিতে লিখব এবং দেখব কীভাবে ম্যাট্রিক্স আর ভেক্টরের গুণন কাজ করে।",
    ],
    "sec_04_matrix2x2": [
        "একটি দুই বাই দুই ম্যাট্রিক্স মূলত চারটি সংখ্যার একটি ছক; এই চারটি সংখ্যাই আই হ্যাট আর জে হ্যাটের রূপান্তরিত অবস্থান বর্ণনা করে।",
        "প্রথম কলামের উপরের সংখ্যাটি আই হ্যাটের নতুন এক্স মান, নিচের সংখ্যাটি তার নতুন ওয়াই মান; দ্বিতীয় কলামটি জে হ্যাটের ক্ষেত্রে একই কথা বলে।",
        "এই ছকটিকে আমরা ম্যাট্রিক্স নামে ডাকি আর ভেক্টরের সাথে গুণ করে ইনপুট ভেক্টরের রূপান্তরিত রূপ বের করি।",
        "ম্যাট্রিক্স গুণনের নিয়মটি আসলে রৈখিক সমন্বয়েরই প্রতিফলন; ম্যাট্রিক্সের প্রথম কলামকে ইনপুটের এক্স মান দিয়ে ও দ্বিতীয় কলামকে ওয়াই মান দিয়ে গুণ করে যোগ করতে হয়।",
        "উদাহরণস্বরূপ তিন শূন্য, শূন্য দুই ম্যাট্রিক্স নিলে আই হ্যাট তিনগুণ হয়ে এক্স অক্ষেই থাকে আর জে হ্যাট দুইগুণ হয়ে ওয়াই অক্ষেই থাকে।",
        "এই ম্যাট্রিক্সটি পুরো তলটিকে অনুভূমিকে তিন গুণ ও উল্লম্বে দুই গুণ প্রসারিত করে; গ্রিডের আয়তক্ষেত্রগুলো বড় হয় কিন্তু বাঁকা হয় না।",
        "আর শূন্য মাইনাস এক, এক শূন্য ম্যাট্রিক্স নিলে পুরো তলটি নব্বই ডিগ্রি ঘোরে; আই হ্যাট ওয়াই অক্ষে ও জে হ্যাট ঋণাত্মক এক্স অক্ষে পড়ে।",
        "এক শূন্য, এক এক ম্যাট্রিক্স একটি শিয়ার তৈরি করে; আই হ্যাট স্থির থাকে আর জে হ্যাট ডানে সরে, ফলে বর্গগুলো সমান্তরিক চতুর্ভুজে রূপ নেয়।",
        "ম্যাট্রিক্সের কর্ণের দুটি সংখ্যা বিশেষ গুরুত্বপূর্ণ; প্রথমটি বলে আই হ্যাটের এক্স মান কতগুণ হয়, দ্বিতীয়টি বলে জে হ্যাটের ওয়াই মান কতগুণ হয়।",
        "কর্ণের বাইরে থাকা সংখ্যাগুলো দিক মিশ্রিত করে; এগুলোই রূপান্তরে মোচড় বা বিকৃতি এনে দেয়।",
        "ম্যাট্রিক্স গুণনের এই পদ্ধতি মুখস্থ করার চেয়ে ছবিটি মনে রাখা অনেক সহজ—প্রতিটি কলাম হলো একটি ভিত্তি ভেক্টরের নতুন ঠিকানা।",
        "যদি ম্যাট্রিক্সের দুটি কলাম পরস্পরের গুণিতক হয়, তবে রূপান্তরটি পুরো তলকে একটিমাত্র রেখায় চ্যাপ্টা করে দেয়; সেক্ষেত্রে ডিটারমিন্যান্ট শূন্য হয়।",
        "অপরদিকে কলাম দুটি স্বাধীন হলে তলটি তার দ্বিমাত্রিকতা ধরে রাখে আর আমরা একটি নতুন ভিত্তি পাই।",
        "আসুন একটি ভেক্টর নিই যার এক্স মান দুই আর ওয়াই মান তিন; ম্যাট্রিক্স গুণনের নিয়ম প্রয়োগ করলে তার নতুন অবস্থান সরাসরি পাওয়া যায়।",
        "এইভাবে মাত্র চারটি সংখ্যা দিয়ে পুরো তলের অসংখ্য ভেক্টরের গতি বর্ণনা করা যায়—এই সংক্ষিপ্ততাই ম্যাট্রিক্সের শক্তি।",
        "পরের পাঠে আমরা ম্যাট্রিক্স গুণন ও ডিটারমিন্যান্টের আরও গভীরে যাব; আজকের এই ছবিটি সেই যাত্রার ভিত্তি হবে।",
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
    """Read web_platform/assets/audio/linear_algebra/lesson_03/manifest.json.

    Sections are de-duplicated by key (alias-deduped) and cue texts are
    de-duplicated as well. Cue texts are used verbatim as the dubbing script.
    """
    if not MANIFEST.exists():
        raise SystemExit(f"MANIFEST NOT FOUND: {MANIFEST}")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out, seen_sec, seen_text = [], set(), set()
    for _key, sec in data.get("sections", {}).items():
        sid = sec.get("alias") or sec.get("section_id") or _key
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
        "experiment": "fill_v2 (linear_algebra lesson_03 full-length, heavy expansion, "
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
