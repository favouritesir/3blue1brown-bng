"""
EXPERIMENT — fill_v2: full-length Bengali dub for Linear Algebra Lesson 06 (Determinants)
=========================================================================================
Goal: RE-RENDER the Lesson 06 dub to eliminate the 33 silent pockets (up to ~12 s long)
produced by clean_timesync_v2, where most cues were rendered with tempo=1.0 and
pad-only, leaving the remainder of every (scaled) visual window as dead air.

Copied from the quality-gated pipeline:
  essence_of_calculus/lesson_08_integration/dubbing_pipeline/experiments/
    clean_timesync_v2/build_calc08_clean.py
and ADDS, as instructed:
  * cue source = the AUDIO MANIFEST
      web_platform/assets/audio/linear_algebra/lesson_06/manifest.json
    (cue texts are the dubbing script; already alias-deduped).
  * HEAVY contextual pedagogical Bengali expansion of every cue, done
    INCREMENTALLY (synthesise one extra sentence at a time) so a single cue
    can grow from ~5 s to ~60 s without ever re-rendering the base text.
  * recompute-scale-from-rendered-speech: after all speech is rendered and
    expanded, the timeline scale is derived from the ACTUAL rendered speech
    durations (not from the authored manifest durations), and the cue windows
    are rebuilt from those rendered durations.  This makes fill ratio ~1.0.
  * FILL GATE (hard): median_fill >= 0.72 AND max_internal_gap_s <= 1.5 AND
    silencedetect internal silence runs > 2 s == 0 AND output duration ~=
    original duration.  No success is claimed unless every gate passes.

STRICT SAFETY:
  - Teacher audio, manifests, master scripts and other lessons: READ-ONLY.
  - Video source is NEVER swapped: -c:v copy from original_source/full_original.mp4.
  - Old video at media_vault/lesson_06/experiments/3b1b_lesson_06_full_dubbed.mp4
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
# Paths
# ---------------------------------------------------------------------------
EXP = Path(__file__).resolve().parent
BASE = EXP.parent.parent                        # .../lesson_06_determinant/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform

MANIFEST = WEB / "assets" / "audio" / "linear_algebra" / "lesson_06" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_06" / "original_source" / "full_original.mp4"
OLD_VIDEO = WEB / "media_vault" / "lesson_06" / "experiments" / "3b1b_lesson_06_full_dubbed.mp4"  # backup, untouched
OUT_VIDEO = WEB / "media_vault" / "lesson_06" / "experiments" / "fill_v2" / "3b1b_lesson_06_full_dubbed_fill2.mp4"

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
VIDEO_ID = "Ip3X9LOh2dk"    # official 3Blue1brown "Determinants" video, reused full original

LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Expansion targets / gates
EXPAND_TARGET_RATIO = 0.97   # expand each cue until rendered >= 97% of its target window
MAX_EXPAND_PASSES = 30       # generous: long cues need several extra sentences
FILL_GATE_MEDIAN = 0.72
FILL_GATE_MAX_GAP_S = 1.5
SILENCE_RUN_MAX_S = 2.0
DURATION_TOLERANCE_S = 1.0   # |output - original| must be <= this

# ---------------------------------------------------------------------------
# Pedagogical Bengali expansion corpus.
# Each section gets a dedicated pool; a generic pool + rotating connectors is
# appended when a section pool is exhausted.  All sentences are natural,
# teacher-style Bangla and phonetically transliterate symbols/acronyms
# (টুডি, থ্রিডি, আই হ্যাট, জে হ্যাট, কে হ্যাট, এ, বি, সি, ডি ...) so Edge-TTS
# never stumbles on bare Latin text.
# ---------------------------------------------------------------------------
SECTION_POOL = {
    "sec_01_scaling_area": [
        "আসুন প্রথমে সেই একক বর্গটির দিকে আবার ফিরে তাকাই, কারণ পুরো সমতলের হিসাব এই একটিমাত্র বর্গের ভেতরেই লুকিয়ে আছে।",
        "রূপান্তরের আগে ভেক্টর দুটো ছিল আই হ্যাট আর জে হ্যাট, আর তাদের দিয়ে গড়া বর্গটির ক্ষেত্রফল ছিল ঠিক এক বর্গ একক।",
        "আই হ্যাট যখন তিন গুণ লম্বা হয় আর জে হ্যাট দুই গুণ, তখন বর্গটি টেনে একটি আয়তক্ষেত্রে পরিণত হয়, যার বাহু তিন আর দুই।",
        "সেই নতুন আয়তক্ষেত্রের ক্ষেত্রফল দাঁড়ায় ছয়, অর্থাৎ মূল ক্ষেত্রফলের ছয় গুণ, আর এই ছয়টিই আমাদের প্রথম স্কেলিং ফ্যাক্টর।",
        "গ্রিডের প্রতিটি রেখা সমান্তরাল আর সমদূরবর্তী থাকায় এক বর্গে যা ঘটে, সমতলের প্রতিটি ক্ষুদ্র বর্গে ঠিক একই ঘটনা ঘটে।",
        "যেকোনো জটিল আঁকাবাঁকা আকৃতিকে অসীম ক্ষুদ্র গ্রিড বর্গের যোগ বলে ভাবলে সামগ্রিক ক্ষেত্রফলও ঠিক একই অনুপাতে বদলায়।",
        "আগের শিয়ারের উদাহরণে বর্গটি ঢালু হয়েছিল মাত্র, ক্ষেত্রফল একই ছিল, কিন্তু এখানে আকারের পাশাপাশি আয়তনও বেড়েছে।",
        "দুই বাই তিন আর তিন বাই দুইয়ের ফল একই, অর্থাৎ কোন বাহুকে প্রথমে টানা হলো তা নিয়ে ভাবনার দরকার নেই।",
        "যদি আই হ্যাটকে দুই গুণ আর জে হ্যাটকেও দুই গুণ করা হয়, তবে ক্ষেত্রফল হবে চার গুণ, কারণ দৈর্ঘ্য আর প্রস্থ দুটোই গুণ হয়।",
        "বর্গের ওপর নজর রাখা সহজ বলেই আমরা প্রথমে জ্যামিতি দেখি, পরে হিসাবের সূত্র আসে স্বাভাবিকভাবেই।",
        "এই স্কেলিং ফ্যাক্টরটিকেই পরে আমরা নির্ণায়ক বা ডিটারমিন্যান্ট নাম দেব, এখন শুধু এর জ্যামিতিক অর্থটি মনে রাখলেই চলবে।",
        "মনে রাখবেন, হিসাব শেষে বের হওয়া সংখ্যাটি কেবল একটি উত্তর নয়, বরং রূপান্তরের চরিত্রের একটা গল্প বলে দেয়।",
        "প্রশ্নটা আবার নিজের ভাষায় বলে দেখুন, কতগুণ বেড়েছে ক্ষেত্রফল, আর সেই সংখ্যাটি কোথা থেকে এসেছে?",
        "রূপান্তরকে ছবি হিসেবে দেখলে এই ধারণা কখনো মুখস্থ করতে হয় না, ছবিটি নিজেই সূত্র তৈরি করে দেয়।",
        "পরবর্তীতে আমরা দেখব ঋণাত্মক সংখ্যাও এই একই স্কেলিংয়ের গল্প বলে, কেবল দিকটা বদলে যায়।",
        "তাই এই প্রথম পাঠের কেন্দ্রীয় কথা হলো, একক বর্গের পরিবর্তনই পুরো সমতলের পরিবর্তনের নমুনা।",
    ],
    "sec_02_negative_determinant": [
        "ঋণাত্মক চিহ্নটি কোনো অসম্ভব পরিমাপ নয়, বরং সমতলের দিক বদলের একটা সরল ইঙ্গিত মাত্র।",
        "আই হ্যাট আর জে হ্যাটের আপেক্ষিক অবস্থান বদলালেই ওরিয়েন্টেশন উল্টে যায়, আর তখনই ডিটারমিন্যান্টের চিহ্ন ঋণাত্মক হয়।",
        "কাগজের এক পিঠে লেখা কথা পেছন দিক থেকে পড়তে হলে যেমন অদ্ভুত লাগে, তেমনি এই রূপান্তরও আমাদের চেনা দিককে উল্টে দেয়।",
        "এক দুই, তিন চার ম্যাট্রিক্সে গুণফলের পার্থক্য মাইনাস দুই, অথচ ক্ষেত্রফলের পরম মান দুই-ই থেকে যায়।",
        "মানে হলো চিহ্ন বলে দেয় দিক কোনে গেল, আর সংখ্যার মান বলে দেয় কতটুকু প্রসারিত হলো, দুটি তথ্য একসাথে।",
        "সাধারণ সমতলে আই হ্যাট ডানে আর জে হ্যাট তার বাঁ পাশে, অর্থাৎ ঘড়ির কাঁটার বিপরীত দিকে অবস্থান করে।",
        "রূপান্তরের পর জে হ্যাট যদি আই হ্যাটের ডান পাশে চলে আসে, তাহলে বোঝা যাবে কাগজটি উল্টে গেছে।",
        "বীজগণিতে ঋণাত্মকতা আমাদের অনেক সময় ভয় দেখায়, কিন্তু এখানে সেটি কেবল একটা দিক নির্দেশক চিহ্ন।",
        "আই হ্যাটকে ধীরে ধীরে জে হ্যাটের দিকে ঘুরালে ক্ষেত্রফল কমে শূন্য হয়, তারপর আবার বাড়তে থাকে ঋণাত্মক দিকে।",
        "এই ধারাবাহিক ঘূর্ণন দেখলে বোঝা যায় ঋণাত্মকতা কোনো হঠাৎ অদ্ভুত ঘটনা নয়, বরং স্বাভাবিক একটি ধাপ।",
        "ধনাত্মক, শূন্য, ঋণাত্মক — এই তিন অবস্থা একই রেখা বরাবর চলে, কোনো ফাঁক বা লাফ নেই।",
        "অ্যাবসোলিউট মান বা পরম মান নিয়ে ভুল না করা, সেটি সবসময় ক্ষেত্রফলের প্রকৃত স্কেলিংয়কেই বোঝায়।",
        "ম্যাট্রিক্সের চিহ্ন পড়ে আমরা বলতে পারি রূপান্তরটি স্থানকে উল্টে দিয়েছে কি না, হিসাব না করেই।",
        "আসুন একটু থামি এবং নিজের ভাষায় বলে দেখি, কেন দিক বদলালে চিহ্ন বদলায় কিন্তু মান একই থাকে।",
        "এই বোঝাপড়া পরে থ্রিডি ওরিয়েন্টেশন আর ডান হাত নিয়মের ক্ষেত্রেও কাজে আসবে।",
        "মনে রাখার মতো কথা হলো, একটি সংখ্যা দিয়েই আমরা মাত্রা আর দিক, দুটি তথ্য একসাথে প্রকাশ করছি।",
    ],
    "sec_03_determinant_in_3d": [
        "টুডি সমতলে যেমন ক্ষেত্রফল, থ্রিডি স্থানে তেমনি আয়তনই হলো ডিটারমিন্যান্টের পরিমাপ।",
        "একক ঘনকের তিন বাহু আই হ্যাট, জে হ্যাট আর কে হ্যাট বরাবর, আর তার আয়তন এক ঘন একক।",
        "রূপান্তরের পর ঘনকটি ঢালু হয়ে প্যারালেলেপিপেডে পরিণত হয়, আর তার নতুন আয়তনই হলো ডিটারমিন্যান্ট।",
        "তিন বাই তিন ম্যাট্রিক্সের তিনটি কলাম ঠিক এই তিনটি ভেক্টরের রূপান্তরিত রূপ বলে দেয়।",
        "টুডিতে যেভাবে একক বর্গকে কেন্দ্র করেছিলাম, থ্রিডিতেও ঠিক সেভাবেই একক ঘনককে কেন্দ্র করি।",
        "ক্ষেত্রফলের জায়গায় এখন আয়তন, বর্গক্ষেত্রের জায়গায় ঘনক, বাকি যুক্তি একই।",
        "ঘনকের তিন বাহু পরস্পর লম্ব হওয়ায় তার আয়তন তিনটি বাহুর গুণফলের সমান হয়।",
        "রূপান্তরের পর বাহুগুলো আর লম্ব না থাকলেও তাদের তিনটি ভেক্টরের মিশ্র গুণফলই আয়তন দেয়।",
        "ডান হাতের তর্জনী আই হ্যাট, মধ্যমা জে হ্যাট আর বৃদ্ধাঙ্গুলি কে হ্যাটের দিকে মেলালে যে চিহ্ন পাই, সেটিই ডিটারমিন্যান্টের চিহ্ন।",
        "রূপান্তরের পরও যদি একইভাবে হাত মেলানো যায়, ডিটারমিন্যান্ট ধনাত্মক, নাহলে ঋণাত্মক।",
        "বাঁ হাত ব্যবহার করতে হচ্ছে মানেই স্থানের দিকবিন্যাস উল্টে গেছে, চিত্রটি দেখেই বোঝা যায়।",
        "যদি তিন বাই তিন ম্যাট্রিক্সের ডিটারমিন্যান্ট শূন্য হয়, তবে পুরো থ্রিডি স্পেস চ্যাপ্টা হয়ে যায়।",
        "সেক্ষেত্রে আয়তন দাঁড়ায় শূন্য, অর্থাৎ ম্যাট্রিক্সের র্যাঙ্ক তিনের কম, আগের রৈখিক নির্ভরতার সাথে মিলে যায়।",
        "চ্যাপ্টা হওয়া মানেই এক একটি মাত্রা হারানো, সমতলে, রেখায় অথবা একক বিন্দুতে সংকুচিত হওয়া।",
        "আসুন ছবিটি মনে রেখে বলে দেখি, কোন বাহু বদলালে আয়তন শূন্য হবে, আর কোনটা বদলালে কেবল চিহ্ন বদলাবে।",
        "থ্রিডির এই অন্তর্দৃষ্টিই পরে ভলিউম ইন্টিগ্রাল আর জ্যাকোবিয়ানের ভিত্তি তৈরি করে।",
    ],
    "sec_04_computation_and_composition": [
        "দুই বাই দুই ম্যাট্রিক্সের ডিটারমিন্যান্টের সূত্র এ ডি বিয়োগ বি সি, কিন্তু এটা মুখস্থ না করে জ্যামিতিক ছবিটি মনে রাখলে কাজ সহজ হয়।",
        "বি আর সি শূন্য হলে ফলটা সরল এ গুণ ডি আয়তক্ষেত্র, কিন্তু সেগুলো অশূন্য হলে কর্ণ বরাবর টানা আর কাটার কারণে বি সি অংশটি বাদ যায়।",
        "তিন বাই তিনের ক্ষেত্রে প্রথম সারির উপাদান দিয়ে ছোট ডিটারমিন্যান্ট তৈরি করে ধনাত্মক, ঋণাত্মক, ধনাত্মক চিহ্নে যোগ করতে হয়, এটিই ল্যাপলাস বিস্তার।",
        "চিহ্নের এই পর্যায়ক্রম কলামের ক্রম থেকেই আসে, তাই এটি কোনো কৃত্রিম নিয়ম নয়।",
        "প্রতিটি ছোট ডিটারমিন্যান্ট আবার দুই বাই দুইয়ের সেই পরিচিত সূত্র দিয়েই বের করা যায়।",
        "দুটি ম্যাট্রিক্সের গুণফলের ডিটারমিন্যান্ট সমান তাদের আলাদা ডিটারমিন্যান্টের গুণফলের, এক বাক্যেই প্রমাণ হয়ে যায়।",
        "প্রথম রূপান্তর যদি ক্ষেত্রফলকে বি গুণ স্কেল করে আর দ্বিতীয়টি এ গুণ, তবে ধারাবাহিক প্রয়োগে মোট স্কেল অবশ্যই এ গুণ বি হবে।",
        "ওরিয়েন্টেশন উল্টালেও চিহ্নের গুণফল একই নিয়ম মানে, মাইনাস গুণ মাইনাস আবার প্লাস হয়।",
        "বীজগণিত দিয়ে এই উপপাদ্য প্রমাণ করা কঠিন হলেও জ্যামিতি একে প্রায় সঙ্গে সঙ্গে বোঝা যায়।",
        "গণনা শিখতে হবে বটে, কিন্তু আগে ছবিটি বোঝা অনেক বেশি গুরুত্বপূর্ণ, সূত্র তখন নিজেই মনে থাকে।",
        "ম্যাট্রিক্সের কলামগুলো আসলে ভিত্তি ভেক্টরগুলো কোথায় পাঠায় তার গল্প, আর ডিটারমিন্যান্ট সেই গল্পের একক সংখ্যা।",
        "আসুন একটা ছোট উদাহরণে হিসাবটি মিলিয়ে দেখি, তাহলে সূত্রের প্রতিটি অংশের অর্থ পরিষ্কার হবে।",
        "ভুল হলে ভয় পাবেন না, চিত্রের দিকে ফিরে তাকালেই দেখা যায় কোথায় ঋণাত্মক চিহ্নটি এসেছে।",
        "পরবর্তী পাঠে এই ডিটারমিন্যান্ট ব্যবহার করে সমীকরণ জোটের সমাধান আর ইনভার্স ম্যাট্রিক্সের রহস্য খোলা হবে।",
        "হ্যামিংয়ের কথাটি আবার মনে পড়ে, গণনা কেবল সংখ্যা বের করার জন্য নয়, গভীর অন্তর্দৃষ্টির জন্য।",
        "আজ এখানেই শেষ, ডিটারমিন্যান্ট আপনার রৈখিক বীজগণিত যাত্রার এক নতুন দরফুলে দিল, আবার দেখা হবে।",
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
# Cue loading — from the AUDIO MANIFEST (read-only)
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

    Returns (expansion_records, rendered_durations, failed).  Each cue's final
    raw MP3 is written to RAW_DIR/raw_<id>.mp3.  Incremental pieces live in
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
    much to expand each cue.  After expansion, the final scale is:

        scale_render = speech_budget / sum(rendered_i)

    and each final window = rendered_i * scale_render.  Because expansion
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
        "lesson": "lesson_06_determinant",
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
