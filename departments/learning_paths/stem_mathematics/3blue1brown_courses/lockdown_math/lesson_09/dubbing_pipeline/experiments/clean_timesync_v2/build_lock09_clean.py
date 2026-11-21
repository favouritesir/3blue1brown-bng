"""
EXPERIMENT - Full-length clean absolute-sample Bengali dub
(Lockdown Math, Lesson 09 - "Geometry of linear combinations and dual vectors")

Adapted verbatim from the proven clean_timesync_v2 pipeline:
    lockdown_math/lesson_01/dubbing_pipeline/experiments/clean_timesync_v2/build_lock01_clean.py

Source video (verified official 3Blue1Brown, oEmbed 2026-11-20):
    YouTube ID LyGKycYT2v0
    Title: "Dot products and duality | Chapter 9, Essence of linear algebra"
    Author: 3Blue1Brown (Grant Sanderson)
    Local copy: web_platform/media_vault/lockdown_math/lesson_09/original_source/full_original.mp4

Guarantees (identical to the proven pipeline, plus IMPROVED_DUB_FILL_POLICY.md):
    1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
       half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
    2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
    3. IMPROVED FILL: atempo floor 0.82 (gentle slowdown), ceiling 2.2. Pad only,
       NEVER truncate. NO SFX: clean speech only.
    4. EXPANSION FIRST: the manifest has only 4 h2 cues (~46 s each) for a
       ~full-length lecture, so each cue is expanded HEAVILY with section-aware
       pedagogical Bengali sentences (linear combinations as vector recipes,
       multidim->1d functions, duality mirror via dot products, orthogonal
       projection) until predicted fill >= 0.85. Section paragraphs from
       lesson_09.json are folded into the base script.
    5. Timeline scale is RECOMPUTED from the SUM OF RENDERED NATURAL SPEECH
       after expansion (not from manifest durations).
    6. Fill metrics (per-cue fill, median_fill, max_internal_gap_s) are measured
       from the rendered waveform; auto re-render (up to 4 rounds) if the gate
       (median_fill >= 0.72, max_internal_gap_s <= 1.5) fails.
    7. Canvas padded to the FULL original video duration so -shortest can never
       trim video frames. Final cue is capped to end inside the video.
    8. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
    9. Lightweight volumedetect (-vn -nostats, log to FILE) on intro and final.
   10. source_metadata_note (3B1B provenance) written both as a verification.json
       field and as a standalone source_metadata_note.md in this folder.

Cue source (read-only; teacher audio / manifests are NEVER modified):
    web_platform/data/lockdown_math/lesson_09.json -> audio_manifest_url
    (assets/audio/lockdown_math/lesson_09/manifest.json). Alias-keyed duplicate
    sections are de-duplicated by section_id.

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
BASE = EXP.parent.parent                        # .../lockdown_math/lesson_09/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "lockdown_math" / "lesson_09.json"

# Original source: yt-dlp output (oEmbed + ffprobe verified before use).
ORIGINAL_DIR = WEB / "media_vault" / "lockdown_math" / "lesson_09" / "original_source"
ORIGINAL_VIDEO = ORIGINAL_DIR / "full_original.mp4"

OUT_VIDEO = WEB / "media_vault" / "lockdown_math" / "lesson_09" / "experiments" / "3b1b_lockdown_09_full_dubbed.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"
SOURCE_NOTE = EXP / "source_metadata_note.md"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
MIN_TEMPO = 0.82                     # IMPROVED_DUB_FILL_POLICY.md
FADE_MS = 12
VIDEO_ID = "LyGKycYT2v0"
VIDEO_TITLE = "Dot products and duality | Chapter 9, Essence of linear algebra"
VIDEO_AUTHOR = "3Blue1Brown (Grant Sanderson)"
LESSON = "lesson_09"

# Silence margins: keep 0-2 s and the final 3 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Expansion policy constants.
EXPAND_TRIGGER_RATIO = 0.62          # expand when natural < 62% of window
EXPAND_TARGET_FILL = 0.85            # aim well above the 0.72 median floor (headroom)
MAX_APPENDED_SENTENCES = 180         # STRONG expansion (video is ~full length)
ACTIVE_THRESHOLD = 0.015
CHARS_PER_CHUNK = 1700               # chunk long TTS text for robustness


# ---------------------------------------------------------------------------
# Section-aware pedagogical sentences (30 distinct sentences per section).
# Cycled (never repeated verbatim inside a single add-call); chosen so the
# additions teach real mathematics. All Latin symbols are spelled out
# phonetically in Bengali for clean Edge-TTS pronunciation.
# ---------------------------------------------------------------------------
EXPANSION_POOL = {
    "sec-01-linear-combinations": [
        "ভেক্টরকে স্কেলার দিয়ে গুণ মানে তার দৈর্ঘ্য বদলানো, কিন্তু দিক একই রাখা; ঋণাত্মক স্কেলার দিক সম্পূর্ণ উল্টে দেয়।",
        "দুটি ভেক্টরকে টিপ টু টেইল নিয়মে যোগ করলে প্রথমটির ডগা থেকে দ্বিতীয়টির ডগা পর্যন্ত একটি নতুন তীর তৈরি হয়।",
        "রেসিপির মতো ভাবুন: ভি ভেক্টরের কতগুলো অংশ আর ডব্লিউ ভেক্টরের কতগুলো অংশ মিলিয়ে নতুন ভেক্টর বানাব।",
        "স্কেলারগুলোকে রেসিপির পরিমাণ হিসেবে মনে করুন—কত বড় অংশ নেবে তা তারাই ঠিক করে দেয়।",
        "যোগের ক্রম গুরুত্বপূর্ণ নয়; ভি যোগ ডব্লিউ আর ডব্লিউ যোগ ভি একই ফল দেয়, কারণ ভেক্টর যোগ বিনিময়ী।",
        "স্প্যান মানে সব সম্ভাব্য রেসিপির ফলাফল—সবগুলো তীর নিয়ে একটি পূর্ণ এলাকা বা সরলরেখা গঠন করে।",
        "যদি ভি আর ডব্লিউ একই রেখায় থাকে, তবে যেকোনো সমাহার সেই রেখার বাইরে যেতে পারে না—স্প্যান সংকুচিত হয়।",
        "যদি দুটি ভেক্টর পরস্পর সমকোণে বা আলাদা দিকে হয়, তবে তাদের সমাহার পূর্ণ দ্বিমাত্রিক তল জুড়ে ছড়িয়ে পড়ে।",
        "ভিত্তি ভেক্টর আই হ্যাট আর জে হ্যাট হলো সবচেয়ে সহজ রেসিপির উপকরণ—একক দৈর্ঘ্য និង পরস্পর লম্ব।",
        "যেকোনো ভেক্টরকে তার স্থানাঙ্ক দ্বারা লেখা আসলে একটি রেসিপি: এক্স গুণ আই হ্যাট যোগ ওয়াই গুণ জে হ্যাট।",
        "স্কেলার দ্বারা গুণ করলে ভেক্টরের দিক অপরিবর্তিত থাকে, শুধু তার অঙ্কন দীর্ঘ বা সংক্ষিপ্ত হয়।",
        "দুটি ভেক্টরের যোগফল সবসময় তাদের তৈরি করা সমান্তরাল ভিত্তির একটি নতুন বর্গের ডগায় পৌঁছায়।",
        "রৈখিক সমাহারের শক্তি এই যে সীমিত কয়েকটি ভেক্টর দিয়ে অসীম সংখ্যক বিন্দুতে পৌঁছানো যায়।",
        "কিছু স্কেলার শূন্য হলে ওই ভেক্টরের অবদান শূন্য হয়—অর্থাৎ সেই উপকরণটি রেসিপি থেকে বাদ পড়ে।",
        "সমাহারের ফলাফল কোথায় পড়বে তা নির্ভর করে স্কেলারের মানের ওপর, ভেক্টরের আসল অবস্থানের ওপর নয়।",
        "একটি ত্রিমাত্রিক স্প্যান তলের চেয়ে বড়—সেটি পুরো কক্ষস্থান দখল করে, যদি তিনটি ভেক্টর স্বাধীন হয়।",
        "রৈখিক নির্ভরতা মানে কোনো একটি ভেক্টর অন্যগুলোর সমাহার হিসেবে লেখা যায়—সেটি নতুন কিছু যোগ করে না।",
        "স্বাধীন ভেক্টর মানে প্রতিটি নতুন দিক যোগ করে, ফলে স্প্যানের মাত্রা এক এক করে বৃদ্ধি পায়।",
        "গ্রিডের ওপর ভেক্টর আঁকালে দেখা যায় স্কেলিং কীভাবে গ্রিডের চৌকাঠি ছাড়িয়ে নতুন বিন্দু তৈরি করে।",
        "নীল আর কমলা তীরকে যতক্ষণ স্কেল করা হয়, ততক্ষণ সবুজ ফলাফলের তীর গ্রিডের বিভিন্ন বিন্দুতে চলে যায়।",
        "স্প্যান নির্ণয়ের আসল প্রশ্ন হলো—এই উপকরণগুলো দিয়ে কতগুলো স্বাধীন দিক তৈরি করা যাবে?",
        "যদি শুধু একটি ভেক্টর থাকে, তবে তার স্প্যান হবে কেবল ওই একটিমাত্র সরলরেখা, তল নয়।",
        "দুটি ভেক্টর সমরেখ হলে তাদের গুণিতক একই রেখায় পড়ে—নতুন কোনো অঞ্চল জন্ম নেয় না।",
        "রৈখিক সমাহার আসলে ভেক্টর স্থানের ভিতরে একটি রেসিপি-নির্ভর ভ্রমণ, যার গন্তব্য স্কেলার ঠিক করে।",
        "ভেক্টর যোগের এই সরল নিয়মই পরবর্তীতে ম্যাট্রিক্স গুণনের ভিত্তি হয়ে ওঠে—মনে রাখবেন।",
        "আপনি যদি স্কেলার দুটিকে বদলান, তবে একই দুটি ভেক্টর দিয়েও সম্পূর্ণ ভিন্ন ফলাফল পেতে পারেন।",
        "তাই রেসিপি আর উপকরণ—এই দুটি মিলেই রৈখিক বীজগণিতের পুরো বুনন তৈরি হয়।",
        "স্প্যানের ধারণা ছাড়া রৈখিক রূপান্তর বোঝা কঠিন, কারণ রূপান্তর আসলে স্প্যানকেই নতুন জায়গায় নিয়ে যায়।",
        "আগের এই পরিচ্ছেদ আমাদের মনে করিয়ে দেয়: জটিলতার আগে সরলতম রেসিপিটি ভালো করে বুঝে নিন।",
        "এখন প্রশ্ন উঠে—এই যে রেসিপি, একে কি উল্টো দিকে চালানো যায়? অর্থাৎ একাধিক মাত্রা থেকে একক সংখ্যায় আনা যায় কি?",
    ],
    "sec-02-multidim-to-1d": [
        "একটি রৈখিক রূপান্তর মূলত একটি নিয়ম, যা প্রতিটি ইনপুট ভেক্টরকে একটি নির্দিষ্ট আউটপুটে পাঠায়।",
        "রৈখিকতার প্রথম শর্ত: যোগফলের রূপান্তর equal রূপান্তরগুলোর যোগফল—অর্থাৎ টি অফ ভি প্লাস ডব্লিউ equal টি ভি যোগ টি ডব্লিউ।",
        "দ্বিতীয় শর্ত: স্কেল করা ইনপুটের রূপান্তর equal স্কেলটির সাথে আউটপুটের গুণ—টি অফ সি ভি equal সি গুণ টি ভি।",
        "এই দুটি শর্ত একসাথে মানে রূপান্তরটি গ্রিড লাইনগুলোকে সরল ও সমান দূরবর্তী রাখে, কেবল ঘোরায় বা প্রসারিত করে।",
        "এখানে ইনপুট হলো দ্বিমাত্রিক ভেক্টর, কিন্তু আউটপুট হলো একটি মাত্র বাস্তব সংখ্যা—একটি সরলরেখার বিন্দু।",
        "দ্বিমাত্রিক তল থেকে সংখ্যারেখায় ভেঙে আনা মানে পুরো তলটিকে একটি রেখার ওপর চাপ দেওয়া।",
        "যেহেতু রূপান্তরটি রৈখিক, তাই এটি সম্পূর্ণ নির্ধারিত হয় আই হ্যাট আর জে হ্যাট কোথায় পড়ে তার ওপর।",
        "আই হ্যাট হলো এক্স অক্ষ বরাবর একক তীর, আর জে হ্যাট হলো ওয়াই অক্ষ বরাবর একক তীর।",
        "ধরা যাক আই হ্যাট পড়ল সংখ্যারেখার ইউ এক বিন্দুতে আর জে হ্যাট পড়ল ইউ দুই বিন্দুতে।",
        "এখন যেকোনো ভেক্টর এক্স আই হ্যাট যোগ ওয়াই জে হ্যাট গিয়ে পড়বে এক্স গুণ ইউ এক যোগ ওয়াই গুণ ইউ দুই বিন্দুতে।",
        "রৈখিকতার কারণেই আমরা ভেক্টরটিকে অংশে ভেঙে প্রতি অংশের ফলাফল যোগ করতে পারি—এটিই মূল কৌশল।",
        "এই হিসাবটিকে আমরা লিখি এক বাই দুই সারি ম্যাট্রিক্স দিয়ে: ইউ এক, ইউ দুই গুণ ভেক্টর।",
        "সারি ম্যাট্রিক্সের দুটি ঘর আসলে আই হ্যাট আর জে হ্যাটের নতুন অবস্থান—কিছু বেশি নয়।",
        "ম্যাট্রিক্সটি কোনো তালিকা নয়; এটি একটি সম্পূর্ণ রূপান্তর নির্দেশিকা, যা বলে দেয় কোথায় কতখানি চলে যাবে।",
        "এক বাই দুই ম্যাট্রিক্স মানে এক সারি ও দুটি কলাম—ইনপুট দুই মাত্রার, আউটপুট এক মাত্রার।",
        "আপনি যদি ইউ এক আর ইউ দুই বদলান, তবে পুরো রূপান্তরটি বদলে যায়—তলের পতনের ভঙ্গিও বদলায়।",
        "ইউ এক ও ইউ দুই যদি সমান হয়, তবে তলটিকে একক ভাবে ভেঙে দেওয়া হয়—অনেক তথ্য হারায়।",
        "যদি দুটিই শূন্য হয়, তবে পুরো তল একশূন্য বিন্দুতে পড়ে যায়—সব ইনপুটের আউটপুট শূন্য।",
        "রূপান্তরটিকে ম্যাট্রিক্স হিসেবে লেখার সুবিধা হলো একই কাঠামো তিন বা চার মাত্রাতেও কাজ করে।",
        "এক বাই দুইয়ের বদলে এক বাই এন ম্যাট্রিক্স লিখে যেকোনো মাত্রার স্থান থেকে সংখ্যারেখায় যাওয়া যায়।",
        "ইনপুটের প্রতিটি উপাংশ আউটপুটে কত অবদান রাখবে তা সারি ম্যাট্রিক্সের ঘরগুলো ঠিক করে।",
        "চিত্রে যখন তলটি সংখ্যারেখার ওপর পড়ে, তখন একই রেখার ওপর অনেক বিন্দু এক বিন্দুতে মিলে যায়।",
        "এই মিলে যাওয়া অপরিবর্তনীয় নয়—রূপান্তরের ক্ষেত্রে একাধিক ইনপুটের এক আউটপুট হতে পারে।",
        "কিন্তু উল্টোটা সবসময় সম্ভব নয়—এক ইনপুটের একাধিক আউটপুট হতে পারে না, কারণ এটি একটি ফাংশন।",
        "আমরা এখন একটি ফাংশন পেলাম যা ভেক্টর নেয় ও সংখ্যা দেয়। এই ফাংশনটিকে কি ভেক্টর হিসেবেও দেখা যায়?",
        "এই প্রশ্নটিই পরবর্তী পরিচ্ছেদের দ্বৈততার জন্ম দেয়—ফাংশন আর ভেক্টরের আয়নার মতো মিল।",
        "মনে রাখবেন, এক বাই দুই ম্যাট্রিক্স আর দুই উপাংশের কলাম ভেক্টর—দেখতে আলাদা, কিন্তু গাণিতিকভাবে যুক্ত।",
        "বহুমাত্রা থেকে এক মাত্রায় আসা একটি বিশেষ রূপান্তর, কারণ আউটপুট স্থান সবচেয়ে সরল—একটি রেখা মাত্র।",
        "এই সরলতার কারণেই এর সাথে একটি জ্যামিতিক বস্তুর এক-to-one মিল খুঁজে পাওয়া সম্ভব হয়।",
        "আসুন এখন সেই সূত্রের দিকে তাকাই ইউ এক গুণ এক্স যোগ ইউ দুই গুণ ওয়াই—কোথাও দেখেছি কি?"
    ],
    "sec-03-duality-dot-product": [
        "ইউ এক গুণ এক্স যোগ ইউ দুই গুণ ওয়াই—এই রাশিটি কি আপনার কাছে পরিচিত মনে হচ্ছে? হ্যাঁ, এটি একটি ডট প্রোডাক্ট।",
        "ইউ ভেক্টরের উপাংশ ইউ এক, ইউ দুই আর ভি ভেক্টরের উপাংশ এক্স, ওয়াই—এদের গুণফলের যোগই ডট প্রোডাক্ট।",
        "অর্থাৎ এক বাই দুই সারি ম্যাট্রিক্স দিয়ে লেখা রূপান্তরটি আসলে ইউ ভেক্টরের সাথে ডট প্রোডাক্ট ছাড়া কিছু নয়।",
        "এখানেই গণিতের সবচেয়ে অপরূপ দ্বৈততা বা ডুয়ালিটির জন্ম হয়—ফাংশন আর ভেক্টর একে অপরের প্রতিবিম্ব।",
        "এক বাই দুই অনুভূমিক সারি ম্যাট্রিক্স একটি ফাংশন হিসেবে কাজ করে, আর উলম্ব কলাম ভেক্টর স্থানে একটি তীর।",
        "একই সংখ্যা ইউ এক আর ইউ দুই দুই জায়গায় বসে—একটি ফাংশনের ঘরে, আরেকটি ভেক্টরের উপাংশে।",
        "আয়নার এক পিঠে রৈখিক ফাংশন, অন্য পিঠে দ্বৈত ভেক্টর—ডট প্রোডাক্ট সেই প্রতিবিম্বকেই সংখ্যায় রূপ দেয়।",
        "গণিতবিদ রিসের প্রতিনিধিত্ব উপপাদ্য এই মিলটিকেই প্রমাণ করেছেন—তাই একে রিস ডুয়ালিটিও বলা হয়।",
        "উপপাদ্যটি বলে: ইউক্লিডীয় স্থানে যেকোনো রৈখিক রূপান্তর একটি নির্দিষ্ট ভেক্টরের সাথে ডট প্রোডাক্টের সমান।",
        "অর্থাৎ টি অফ ভি equal ইউ ডট ভি—একটি ফাংশনকে একটি ভেক্টর দিয়ে সম্পূর্ণ বর্ণনা করা যায়।",
        "এই ভেক্টর ইউ কে বলা হয় দ্বৈত ভেক্টর বা ডুয়াল ভেক্টর—এটি রূপান্তরের জ্যামিতিক মূর্ত রূপ।",
        "দ্বৈততার সৌন্দর্য হলো একই বস্তুকে দুটি ভাষায় বলা যায়—একটি গুণনের ভাষা, অন্যটি প্রক্ষেপণের ভাষা।",
        "সারি ম্যাট্রিক্সের ভাষা বলে কতগুলো ইউ নিতে হবে; কলাম ভেক্টরের ভাষা বলে কোথায় তীরটি আছে।",
        "যখন আমরা ডট প্রোডাক্ট লিখি, তখন আসলে এই দুটি ভাষারই অনুবাদ করি—একটি সংখ্যায় মিলিয়ে দিই।",
        "ডট প্রোডাক্টের আর একটি রূপ হলো ইউর দৈর্ঘ্য গুণ ভির দৈর্ঘ্য গুণ কোস থেটা—অর্থাৎ কোণের ওপর নির্ভরতা।",
        "থেটা শূন্য হলে ভি আর ইউ একই দিকে থাকে—তখন ডট প্রোডাক্ট সর্বোচ্চ, দৈর্ঘ্যের সরল গুণফল।",
        "থেটা নব্বই ডিগ্রি হলে ভি ইউর লম্ব—তখন ডট প্রোডাক্ট শূন্য, কোনো অবদান থাকে না।",
        "থেটা একশো আশি ডিগ্রি হলে দিক বিপরীত—তখন ডট প্রোডাক্ট ঋণাত্মক, অর্থাৎ বিয়োগমূলক অবদান।",
        "এই কোণ-নির্ভরতাই দেখায় ডট প্রোডাক্ট কোনো শুষ্ক গুণন নয়, বরং একটি জ্যামিতিক সম্পর্ক।",
        "রিসের উপপাদ্য কেবল তিন বা চার মাত্রায় নয়, যেকোনো ইউক্লিডীয় স্থানে কাজ করে—এটি সার্বজনীন।",
        "আপনি যদি কোনো রৈখিক ফাংশনের সারি ম্যাট্রিক্স দেখেন, তবে তার সাথে একটি অনন্য ভেক্টর মিলিয়ে নিন—উত্তর মিলবে।",
        "এই মিলনই আধুনিক রৈখिक বীজগণিতের ভিত্তি—ফাংশন ও ভেক্টর আলাদা সত্তা নয়, একই বাস্তবতার দুই রূপ।",
        "আয়নার চিত্রটি মনে রাখলে সূত্রটি মুখস্থ করার প্রয়োজন হবে না—কেবল উপাংশগুলো সাজালেই কাজ চলে যাবে।",
        "আগের পরিচ্ছেদে যে এক বাই দুই ম্যাট্রিক্স পেয়েছিলাম, তার দুটি ঘরই এখন ইউ ভেক্টরের উপাংশ হয়ে গেল।",
        "এই আবিষ্কারের পরে প্রশ্ন থাকে—কেন ডট প্রোডাক্ট ঠিক এইভাবে কাজ করে? তার জ্যামিতিক কারণ কী?",
        "উত্তর হলো লম্ব অভিক্ষেপ—ভেক্টরকে অপর ভেক্টরের রেখার ওপর ছায়ার মতো ফেলা। পরের অধ্যায়ে তা দেখব।",
        "দ্বৈততা কেবল একটি সূত্র নয়; এটি গণিতের একটি দর্শন—একই সত্যকে বিভিন্ন দৃষ্টিকোণ থেকে দেখা।",
        "আপনি যখনই কোনো ডট প্রোডাক্ট দেখবেন, মনে রাখবেন এর পেছনে একটি রৈখিক ফাংশন লুকিয়ে আছে।",
        "এই উপলব্ধিই আজকের পাঠের কেন্দ্র—ফাংশন আর ভেক্টরের মাঝে সেই সুন্দর আয়নাটি।",
        "আসুন এখন সেই ছায়ার জ্যামিতিটি বিশদভাবে দেখি, যা ডট প্রোডাক্টের অর্থকে সম্পূর্ণ করে তোলে।",
    ],
    "sec-04-geometric-projection": [
        "কেন ডট প্রোডাক্ট একটি রৈখিক রূপান্তরের নিয়ম মেনে চলে? এর উত্তর লম্ব অভিক্ষেপের জ্যামিতিতে লুকিয়ে আছে।",
        "কল্পনা করুন ইউ ভেক্টরের দিকে একটি সরলরেখা টানা আছে—এই রেখাটি আমাদের অভিক্ষেপের লক্ষ্য।",
        "সমতলের যেকোনো ভেক্টর থেকে এই রেখার ওপর লম্বভাবে ছায়া ফেলা যায়—এটিই অর্থোগোনাল প্রজেকশন।",
        "লম্ব মানে নব্বই ডিগ্রি কোণ—ছায়া সবসময় রেখার সাথে সমকোণে নামে, তাই এর দৈর্ঘ্য সুনির্দিষ্ট।",
        "ভি ভেক্টরের ছায়ার দৈর্ঘ্য দাঁড়ায় ভির দৈর্ঘ্য গুণ কোস থেটা, যা ঠিক ভি ডট ইউ ভাগ ইউর দৈর্ঘ্য।",
        "ইউ যদি একক ভেক্টর হয়, তবে তার দৈর্ঘ্য এক—তখন ছায়ার দৈর্ঘ্যই হলো ভি ডট ইউ, কোনো ভাগ ছাড়াই।",
        "এই ছায়া ফেলার প্রক্রিয়াটি রৈখিক, কারণ দুটি ভেক্টরের যোগফলের ছায়া equal তাদের ছায়ার যোগফল।",
        "একইভাবে স্কেল করা ভেক্টরের ছায়াও স্কেল অনুযায়ী বাড়ে বা কমে—তাই এটি একটি বৈধ রূপান্তর।",
        "যেহেতু রূপান্তর রৈখিক, তাই আই হ্যাটের ছায়ার দৈর্ঘ্য দাঁড়ায় ইউ এক, আর জে হ্যাটের ছায়া দাঁড়ায় ইউ দুই।",
        "অর্থাৎ আই হ্যাট আর জে হ্যাটের ছায়া মিলেই আগের সারি ম্যাট্রিক্সের দুটি ঘর তৈরি করে।",
        "ফলে যেকোনো ভেক্টরের অভিক্ষেপের মান দাঁড়ায় এক্স গুণ ইউ এক যোগ ওয়াই গুণ ইউ দুই—আগের সূত্রই।",
        "এইভাবে জ্যামিতি ও বীজগণিত সম্পূর্ণ মিলে যায়—একই ফলাফল দুটি ভিন্ন পথে পাওয়া যায়।",
        "এখন ডট প্রোডাক্টের প্রতিসাম্যের প্রশ্ন: ইউ ডট ভি কি সবসময় ভি ডট ইউর সমান? উত্তর হ্যাঁ।",
        "ইউর রেখায় ভির ছায়া গুণ ইউর দৈর্ঘ্য—আর ভির রেখায় ইউর ছায়া গুণ ভির দৈর্ঘ্য।",
        "এই দুটি রাশি হুবহু একই, কারণ উভয়ই একই কোণ থেটা দ্বারা নির্ধারিত একই ত্রিকোণমিতিক ক্ষেত্রফল।",
        "অন্য ভাষায়, ইউর দৈর্ঘ্য গুণ ভির দৈর্ঘ্য গুণ কোস থেটা—যেভাবেই সাজানো হোক, ফল একই আসে।",
        "গুণনের বিনিময়তা আর এই প্রতিসাম্যই ডট প্রোডাক্টের ইউ ডট ভি equal ভি ডট ইউ কে প্রমাণ করে।",
        "অর্থোগোনাল প্রজেকশনের সূত্র হলো ভিকে ইউর ওপর ফেললে ফল equal ইউ ডট ভি ভাগ ইউর দৈর্ঘ্য বর্গ, গুণ ইউ।",
        "ইউ একক হলে ভাগের প্রয়োজন হয় না—তখন অভিক্ষেপ সরাসরি ইউ ডট ভি গুণ ইউ হয়ে যায়।",
        "অভিক্ষেপ ও মূল ভেক্টরের মাঝের অংশটিকে বলা হয় লম্ব উপাংশ—এটি ইউর সাথে সমকোণে থাকে।",
        "মূল ভেক্টর ভিকে আমরা এই দুই ভাগে ভেঙে দেখতে পারি—রেখা বরাবর অংশ আর রেখার লম্ব অংশ।",
        "এই বিভাজনই ব্যাখ্যা করে কেন কোনো লম্ব ভেক্টরের সাথে ডট প্রোডакт শূন্য হয়—তার ছায়াই শূন্য।",
        "চিত্রে লম্ব রেখা আর ছায়ার দৈর্ঘ্য দেখলে বোঝা যায় ডট প্রোডাক্ট কোনো মুখস্থ সূত্র নয়।",
        "এটি হলো প্রজেকশনের জ্যামিতিক প্রক্রিয়াকে একটি একক সংখ্যার মাধ্যমে অনুবাদ করার বিশুদ্ধ উপায়।",
        "দ্বৈততার পুরো ধারণা এই জ্যামিতির ওপর দাঁড়িয়ে—ফাংশন মানে ছায়া, ডট প্রোডাক্ট মানে ছায়ার দৈর্ঘ্য।",
        "আপনি যখনই কোনো দ্বৈত ভেক্টর দেখবেন, তার দিকে একটি রেখা কল্পনা করুন—বাকিটা ছায়া বলে দেবে।",
        "এই সুন্দর মিল আমাদের পাঠের চূড়ান্ত সারসংক্ষেপ—বীজগণিত ও জ্যামিতি একই সত্যের দুটি ভাষা।",
        "আজ আমরা দেখলাম রৈখিক সমাহার থেকে শুরু করে দ্বৈত ভেক্টর ও লম্ব অভিক্ষেপ—সবই একটি সুতোয় গাঁথা।",
        "মনে রাখবেন, ডট প্রোডাক্ট ভুলে গেলেও ছায়ার এই চিত্রটি আপনাকে সবসময় সঠিক পথ দেখিয়ে দেবে।",
        "এই দর্শন নিয়ে আপনি পরবর্তীতে যেকোনো মাত্রার রূপান্তর ও ফাংশন সহজেই বুঝতে পারবেন—ধন্যবাদ।",
    ],
}
DEFAULT_EXPANSIONS = [
    "এই ধারণাটি নিজের ভাষায় একবার বলে দেখলে বিষয়টি আরও পরিচ্ছন্ন হবে।",
    "লক্ষ্য করুন, ছায়ার এই অনুপাতই আমাদের আসল উত্তরের দিকে নিয়ে যায়।",
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
    t = re.sub(r"\\(?:frac|sqrt|left|right|implies|qquad|times|pm|neq|text|vec|bmatrix|cdot|sum|hat|rightarrow|cos|frac)\b", " ", t)
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
    """Read the audio_manifest referenced by lesson_09.json (read-only)."""
    rel = (lesson.get("audio_manifest") or lesson.get("audio_manifest_url") or
           (lesson.get("meta") or {}).get("audio_manifest") or
           (lesson.get("meta") or {}).get("audio_manifest_url"))
    candidates = []
    if rel:
        candidates.append((LESSON_JSON.parent / rel).resolve())
    candidates.append(WEB / "assets" / "audio" / "lockdown_math" / "lesson_09" / "manifest.json")

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
        for t in sec.get("paragraphs", []):
            clean = strip_math(t)
            if clean:
                texts.append(clean)
        co = sec.get("callout") or {}
        if co.get("text"):
            texts.append(strip_math(co["text"]))
        for t in texts:
            if t:
                out.append({"text": t,
                            "dur_ms": max(2000.0, len(t) * 75.0),
                            "section": sec_id})
    return out


def load_source_cues():
    """Return (list_of_{text,dur_ms,section}, source_description)."""
    lesson = json.loads(LESSON_JSON.read_text(encoding="utf-8"))
    out, desc = load_manifest_cues(lesson)
    if not out:
        return derive_from_lesson(lesson), "lesson_09.json:sections"

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


def write_source_note(report, probe_meta):
    """Standalone provenance note confirming the official 3B1B source."""
    lines = [
        "# Source metadata note — Lockdown Math Lesson 09 (full Bengali dub)",
        "",
        f"- Lesson: `{LESSON}` — Geometry of linear combinations and dual vectors / দ্বৈত ভেক্টর ও রৈখিক সমাহার",
        f"- YouTube ID: `{VIDEO_ID}`",
        f"- oEmbed title: **{VIDEO_TITLE}**",
        f"- oEmbed author: **{VIDEO_AUTHOR}**",
        "- Source channel: 3Blue1Brown (official), https://www.youtube.com/@3blue1brown",
        "- oEmbed verified: 2026-11-20 via https://www.youtube.com/oembed?url=...&format=json",
        f"- Local original: `{ORIGINAL_VIDEO}`",
        f"- Original ffprobe duration: `{report.get('video_duration_sec')}` s",
        "",
        "## ffprobe verification of the downloaded original",
        "",
    ]
    for k, v in (probe_meta or {}).items():
        lines.append(f"- {k}: `{v}`")
    lines += [
        "",
        "## Why this source is correct",
        "",
        "The official 3B1B chapter is titled 'Dot products and duality', which is an exact topic",
        "match for this lesson on linear combinations, multidim→1d linear transformations,",
        "duality via the dot product, and orthogonal projection. The Bengali narration is",
        "synthesized with `bn-BD-PradeepNeural`; the original English teacher audio and all",
        "manifests are left untouched. No SFX, no English vocal bleed.",
        "",
        f"- Dub voice: `{VOICE}`",
        f"- Output: `{OUT_VIDEO}`",
        f"- Verification record: `{VERIFY}`",
    ]
    SOURCE_NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def probe_original_metadata(src):
    """ffprobe the local original to confirm it is the 3B1B video."""
    meta = {}
    try:
        out = run(f'ffprobe -v error -show_entries format_tags=title,artist,comment:'
                  f'format=duration -of json "{src}"')
        d = json.loads(out)
        fmt = d.get("format", {})
        tags = fmt.get("tags", {})
        meta["format_duration_sec"] = fmt.get("duration")
        for key in ("title", "artist", "comment"):
            if key in tags:
                meta[f"tag_{key}"] = tags[key]
        sd = json.loads(run(f'ffprobe -v error -select_streams v:0 -show_entries '
                            f'stream=codec_name,width,height,duration -of json "{src}"'))
        if sd.get("streams"):
            s = sd["streams"][0]
            meta["video_codec"] = s.get("codec_name")
            meta["video_resolution"] = f"{s.get('width')}x{s.get('height')}"
            meta["video_stream_duration_sec"] = s.get("duration")
    except Exception as e:
        meta["probe_error"] = str(e)
    return meta


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
    original_meta = probe_original_metadata(src)
    source_cues, source_desc = load_source_cues()
    cues, initial_scale = load_cues(vend, source_cues)
    print(f"video={src} duration={vend:.3f}s cues={len(cues)} "
          f"source={source_desc} initial_manifest_scale={initial_scale:.4f}", flush=True)
    print(f"original_meta={json.dumps(original_meta, ensure_ascii=False)}", flush=True)

    print("[1/7] TTS (clean, no SFX) ...", flush=True)
    failed = await synth_all(cues)

    print("[2/7] Expansion of short cues (STRONG, IMPROVED_DUB_FILL_POLICY) ...", flush=True)
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
        "experiment": "clean_timesync_v2 (lockdown_math_lesson_09 full-length, STRONG expansion, scale recomputed from rendered speech)",
        "lesson": LESSON,
        "course": "lockdown_math",
        "video_id": VIDEO_ID,
        "source_metadata_note": {
            "oembed_title": VIDEO_TITLE,
            "oembed_author": VIDEO_AUTHOR,
            "channel": "3Blue1Brown (official)",
            "oembed_url": f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={VIDEO_ID}&format=json",
            "verified_date": "2026-11-20",
            "topic_match": "Exact: dot products, duality, linear combinations, orthogonal projection",
            "original_ffprobe": original_meta,
        },
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
        probe = json.loads(run(f'ffprobe -v error -show_entries stream=index,codec_type,codec_name,width,height '
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
    write_source_note(report, original_meta)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={report['output_duration_sec']}s size={report['output_size_bytes']}", flush=True)
    print(f"scale={scale:.4f} (recomputed from rendered speech) rounds={render_round}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap={max_internal_gap}s "
          f"expanded={len(expanded)} gate_ok={gate_ok}", flush=True)
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
