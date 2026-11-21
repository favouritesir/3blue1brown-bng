"""
EXPERIMENT — fill_v2 : silent-pocket-free full-length Bengali dub (Lesson 13)
=============================================================================
Copied from the proven quality-gated pipeline:
  essence_of_calculus/lesson_08_integration/dubbing_pipeline/experiments/
      clean_timesync_v2/build_calc08_clean.py
and adapted for Lesson 13 with TWO NEW STAGES:

  (A) RECOMPUTE-SCALE-FROM-RENDERED-SPEECH:
      The old build_l13_clean.py scaled the timeline from the *authored*
      duration_ms (scale 1.74x) while Edge-TTS speech stayed near 1.0x, leaving
      30 silent pockets of up to ~14 s (28 inter-cue gaps + intro + outro).
      Here every cue is first rendered, then each cue's window and tempo are
      RECOMPUTED FROM ITS MEASURED RENDERED SPEECH via
          scale_rendered = usable / (sum(rendered) + n*BASE_GAP_SEC)
          window_i       = (rendered_i + BASE_GAP_SEC) * scale_rendered
          tempo_i        = clamp(rendered_i / (window_i - BASE_GAP_SEC), ...)
      so speech fills its window and only a small (0.35 s) gap remains.

  (B) FILL GATE (hard, verified before success is claimed):
      median_fill >= 0.72  AND  max_internal_gap_s <= 1.5
      AND  0 internal silence runs > 2.0 s (measured on the rendered master).

Cue source (READ-ONLY; teacher audio / manifests are NEVER modified):
  web_platform/assets/audio/linear_algebra/lesson_13/manifest.json
  The cue `text` fields are the dubbing script (alias-deduped by normalised text).

Original video (READ-ONLY, never swapped):
  web_platform/media_vault/lesson_13/original_source/full_original.mp4
Output (NEW, old video kept as backup):
  web_platform/media_vault/lesson_13/experiments/fill_v2/
      3b1b_lesson_13_full_dubbed_fill2.mp4
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

EXP = Path(__file__).resolve().parent
BASE = EXP.parent.parent                        # .../lesson_13_change_of_basis/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
MANIFEST = WEB / "assets" / "audio" / "linear_algebra" / "lesson_13" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_13" / "original_source" / "full_original.mp4"
OUT_VIDEO = (WEB / "media_vault" / "lesson_13" / "experiments" / "fill_v2" /
             "3b1b_lesson_13_full_dubbed_fill2.mp4")

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
TEMPO_FLOOR = 0.82          # gentle natural slowdown, as in the proven pipeline
FADE_MS = 12
VIDEO_ID = "P2LTAUO1TdA"
LESSON = "lesson_13_change_of_basis"

# Silence margins: keep 0-2.5 s and the final 3 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
BASE_GAP_SEC = 0.35                 # small pedagogical pause AFTER each cue

# Heavy-expansion controls.
EXPAND_TARGET_FRAC = 0.985          # expand until rendered >= 98.5% of target
MAX_EXPANSION_PASSES = 12           # generous cap; expansion is adaptive

# Fill gate thresholds (non-negotiable).
MEDIAN_FILL_MIN = 0.72
MAX_INTERNAL_GAP_SEC = 1.5
MAX_SILENCE_RUN_SEC = 2.0
SILENCE_DB = -45.0

# ---------------------------------------------------------------------------
# Lesson-13-specific pedagogical expansions (natural Bengali, phonetically
# safe: টুডি / আই হ্যাট / জে হ্যাট / বি ওয়ান / বি টু / ম্যাট্রিক্স এ / এ ইনভার্স).
# Each is appended to the matching manifest cue when its rendered speech is
# shorter than the window. A generic pool is used for further passes.
# ---------------------------------------------------------------------------
PER_CUE_EXPANSIONS = {
    1: (" আজ আমরা দেখব কীভাবে একই ভেক্টরকে ভিন্ন ভিত্তিতে ভিন্ন সংখ্যা দিয়ে লেখা যায়। "
        "এই ধারণাটি বুঝতে পারলে রৈখিক রূপান্তরের অনেক রহস্য সহজ হয়ে যাবে। "
        "মনে রাখবেন, সংখ্যাগুলো বদলালেও আসল তীর বা বিন্দু একই জায়গায় থাকে।"),
    2: (" পয়েনকেয়ারের কথাটি মনে রাখলে বোঝা যায় গণিত কেবল সত্য খোঁজা নয়, সত্যকে প্রকাশ করার ভাষাও বদলানো। "
        "আজকের পাঠে আমরা দেখব কীভাবে ভিত্তি বদলে একই বস্তুর নাম বদলে যায়, কিন্তু তার জ্যামিতি অটুট থাকে। "
        "এই উপলব্ধিই ভিত্তি পরিবর্তনের দার্শনিক ভিত্তি তৈরি করে।"),
    3: (" আসুন একটু ধীরে ধীরে দেখি। তিন আই হ্যাট মানে আই হ্যাটকে তিন গুণ বাড়ানো, আর দুই জে হ্যাট মানে জে হ্যাটকে দুই গুণ বাড়ানো। "
        "এই দুটি প্রসারিত তীরকে টিপ টু টেইল পদ্ধতিতে যোগ করলেই আমাদের তিন দুই ভেক্টরটি পাওয়া যায়। "
        "প্রতিটি সংখ্যা আসলে এক একটি নির্দেশ—কতটা এগোতে হবে তা বলে দেয়।"),
    4: (" এই কারণেই ভিত্তি ভেক্টরকে বলা হয় কোঅর্ডিনেট ব্যবস্থার ভাষা। ভিত্তি বদলে গেলে সেই ভাষার শব্দও বদলে যায়, "
        "যদিও যে বস্তুকে বর্ণনা করা হচ্ছে সে অপরিবর্তিত থাকে। "
        "আই হ্যাট আর জে হ্যাট আমাদের কাছে স্বজ্ঞাত মনে হলেও এটি কেবল এক পরিচিত অভ্যাস মাত্র।"),
    5: (" চিত্রটির দিকে লক্ষ্য করলে দেখা যায় জেনিফারের গ্রিডটি আমাদের গ্রিডের চেয়ে হেলানো। "
        "কিন্তু এই হেলানো গ্রিডের রেখাগুলোও ঠিক তেমনি একক দূরত্বের ব্যবধানে আঁকা—শুধু দিক আলাদা। "
        "তাই একই বিন্দুকে দুইজন দুই রকম সংখ্যায় ডাকতে পারেন, এবং দুটিই সঠিক।"),
    6: (" জেনিফারের বি ওয়ান হলো দুই এক, আর বি টু হলো ঋণাত্মক এক এক। "
        "মনে করুন সে এই দুটি তীরকে নিজের হাতের কাছে রেখে বাকি সবকিছু মাপছে। "
        "তার কাছে বি ওয়ান আর বি টু যথাক্রমে প্রথম ও দ্বিতীয় একক, ঠিক যেমন আমাদের কাছে আই হ্যাট আর জে হ্যাট।"),
    7: (" এই পয়েন্টটি খুব গুরুত্বপূর্ণ—গ্রিড কোনো বাস্তব বস্তু নয়, এটি কেবল আমাদের মাপার এক উপায়। "
        "মহাকাশে কোনো খাড়া রেখা আগে থেকেই লেখা থাকে না; আমরাই সেটি আঁকি। "
        "তাই জেনিফারের হেলানো গ্রিড আমাদের চেয়ে কম সঠিক নয়, কেবল ভিন্ন।"),
    8: (" তিন দুই আর পাঁচ বাই তিন, এক বাই তিন—এই তিনটি সংখ্যা একই তীরের তিনটি রূপ। "
        "কোনটি সঠিক তা জিজ্ঞেস করা মানে কোন ভাষা সঠিক তা জিজ্ঞেস করা। "
        "উত্তর হলো সবই সঠিক, কারণ প্রতিটি নিজস্ব ভিত্তির ভাষায় লেখা।"),
    9: (" এই পরিচ্ছেদে আমরা শিখব কীভাবে জেনিফারের ভাষায় লেখা একটি ভেক্টরকে আমাদের ভাষায় আনা যায়। "
        "এর জন্য আমাদের লাগবে একটি বিশেষ ম্যাট্রিক্স, যার নাম ভিত্তি ম্যাট্রিক্স এ। "
        "এই ম্যাট্রিক্সটি আসলে এক নিখুঁত অনুবাদকের মতো কাজ করে।"),
    10: (" জেনিফার ঋণাত্মক বি ওয়ান আর দুই বি টু নিয়েছে। ঋণাত্মক গুণ মানে বি ওয়ানকে উল্টো দিকে ঘোরানো, "
         "আর দুই গুণ মানে বি টু কে দ্বিগুণ লম্বা করা। এই দুটি কাজ একসাথে করলেই সে ওই তীরটি পায়।"),
    11: (" এখন আমাদের পরিচিত মানগুলো বসাতে হবে। ঋণাত্মক এক গুণ দুই এক হলো ঋণাত্মক দুই দুই, "
         "আর দুই গুণ ঋণাত্মক এক এক হলো ঋণাত্মক দুই দুই। যোগ করলে পাই ঋণাত্মক চার এক। "
         "দেখুন, কত সহজে ভাষা বদলা যায়!"),
    12: (" চিত্রে স্কেল করা তীরদুটি পর পর সাজানো দেখা যাচ্ছে। প্রথম তীরটি পেছনে যাচ্ছে, দ্বিতীয়টি ওপরে উঠছে, "
         "আর শেষে ফলাফল ঋণাত্মক চার এক দাঁড়াচ্ছে। এই টিপ টু টেইল ছবিটি মনে রাখলে ম্যাট্রিক্স গুণনের ধারণাও সহজ হয়ে যায়।"),
    13: (" রৈখিক সমাবেশ আর ম্যাট্রিক্স ভেক্টর গুণন আসলে একই কাজের দুটি নাম। "
         "ম্যাট্রিক্সের প্রথম কলাম বলে প্রথম ভিত্তি কোথায় যাবে, দ্বিতীয় কলাম বলে দ্বিতীয়টি কোথায় যাবে। "
         "বাকিটা করে স্কেলার গুণ আর যোগ—এতটুকুই!"),
    14: (" ম্যাট্রিক্স এ-র প্রথম কলাম বি ওয়ান অর্থাৎ দুই এক, দ্বিতীয় কলাম বি টু অর্থাৎ ঋণাত্মক এক এক। "
         "জেনিফারের যেকোনো স্থানাঙ্ককে এই ম্যাট্রিক্স দিয়ে গুণ করলেই আমাদের স্থানাঙ্ক বেরিয়ে আসে। "
         "প্রতিটি কলাম আসলে জেনিফারের এক একটি ভিত্তি আমাদের ভাষায় বলে দেয়।"),
    15: (" এবার আমরা উল্টো দিকের যাত্রা করব—আমাদের ভাষা থেকে জেনিফারের ভাষায় ফেরা। "
         "এর জন্য লাগবে এ ইনভার্স, অর্থাৎ আগের ম্যাট্রিক্সের বিপরীত। "
         "এই দুটি ম্যাট্রিক্স একে অপরের কাজকে উল্টে দেয়।"),
    16: (" আমাদের তিন দুই ভেক্টরটিকে জেনিফার কী সংখ্যা দেবে? এই প্রশ্নের উত্তরেই বোঝা যায় বিপরীত ম্যাট্রিক্স কেন দরকারি। "
         "ঠিক যেমন এক ভাষা থেকে অন্য ভাষায় অনুবাদের জন্য এক ধরনের অভিধান লাগে, "
         "উল্টো পথের জন্য লাগে অন্য রকম অভিধান।"),
    17: (" এ ইনভার্স হলো এ-র ঠিক উল্টো পথের অনুবাদক। যেভাবে এ দিয়ে জেনিফারের সংখ্যাকে আমাদের সংখ্যায় আনি, "
         "তেভাবে এ ইনভার্স দিয়ে আমাদের সংখ্যাকে জেনিফারের সংখ্যায় নিয়ে যাই। "
         "বিপরীত রূপান্তর মানে হলো রূপান্তরটিকে পেছনের দিকে চালানো—এই ছবিটি মনে রাখলেই হবে।"),
    18: (" নির্ণায়ক বের করার নিয়মটি মনে করুন—প্রধান কর্ণের গুণফল বাদ দিতে হয় উপ-কর্ণের গুণফলকে। "
         "এখানে দুই গুণ এক বিয়োগ ঋণাত্মক এক গুণ এক, অর্থাৎ তিন। "
         "তিন অশূন্য হওয়ায় ম্যাট্রিক্সের বিপরীত আছে, তাই অনুবাদ সম্ভব।"),
    19: (" চিত্রে এক বাই তিন আর দুই বাই তিন—এই দুটি ভগ্নাংশ জেনিফারের ভিত্তির ওপর লেখা হয়েছে। "
         "স্থানাঙ্ককে স্কেলার হিসেবে দেখলে হিসাবটি স্বজ্ঞাত হয়ে যায়। "
         "শেষে দেখা যায় জেনিফারের পাঁচ বাই তিন আর এক বাই তিন ঠিক আমাদের তিন দুই তীরটিই তৈরি করে।"),
    20: (" ফিরে দেখি, পাঁচ বাই তিন গুণ দুই এক আর এক বাই তিন গুণ ঋণাত্মক এক এক যোগ করলে হুবহু তিন দুই ফেরত পাই। "
         "এটি প্রমাণ করে এ ইনভার্স সত্যিই নিখুঁত অনুবাদক। "
         "দুটি ভিত্তি রৈখিকভাবে স্বাধীন হওয়ায়ই এই অনুবাদ সম্ভব—নির্ণায়ক তিন অশূন্য ছিল বলেই!"),
    21: (" শেষ পরিচ্ছেদে আমরা সবচেয়ে শক্তিশালী ধারণাটি নিয়ে কাজ করব—রূপান্তরের রূপান্তর। "
         "অর্থাৎ একটি ম্যাট্রিক্সকে ভিন্ন ভিত্তিতে কীভাবে প্রকাশ করতে হয়। "
         "এর ফলাফল হলো অনুরূপ ম্যাট্রিক্স, যা ভিত্তি পরিবর্তনের সবচেয়ে গুরুত্বপূর্ণ প্রয়োগ।"),
    22: (" নব্বই ডিগ্রি ঘূর্ণন আমাদের পরিচিত ম্যাট্রিক্স এম দিয়ে লেখা যায়। "
         "এর প্রথম কলাম আই হ্যাটকে শূন্য এক এ নিয়ে যায়, দ্বিতীয় কলাম জে হ্যাটকে ঋণাত্মক এক শূন্য এ। "
         "কিন্তু এই সংখ্যাগুলো আমাদের ভিত্তির ওপর নির্ভরশীল—জেনিফারের ভাষায় এগুলো আলাদা হবে।"),
    23: (" জেনিফার যদি তার হেলানো গ্রিডে বসে একই শারীরিক ঘূর্ণন দেখে, তবে তাকে নতুন করে হিসাব করতে হবে। "
         "কেবল আমাদের ম্যাট্রিক্সের সংখ্যাগুলোকে তার ভাষায় বদলে দিলে চলবে না। "
         "কারণ ম্যাট্রিক্সের কলামগুলো হলো ভিত্তি ভেক্টরগুলো কোথায় ল্যান্ড করেছে—আর সেই ল্যান্ডিং স্থানগুলোকেও তার ভাষাতেই লেখা লাগবে।"),
    24: (" চিত্রে দেখা যাচ্ছে একই নব্বই ডিগ্রি ঘূর্ণন আমাদের খাড়া গ্রিডে সরল দেখা গেলেও জেনিফারের গ্রিডে সংখ্যাগুলো আলাদা। "
         "কিন্তু শারীরিক ঘূর্ণন তো একই—শুধু বর্ণনার ভাষা বদলেছে। "
         "এই পর্যবেক্ষণটি আমাদের শেষ সূত্রটির দিকে নিয়ে যায়।"),
    25: (" তিন ধাপ মনে রাখুন—ডান থেকে বাঁয়ে পড়ুন। প্রথমে ভিত্তি ম্যাট্রিক্স এ দিয়ে জেনিফারের ভাষা থেকে আমাদের ভাষায় আনুন, "
         "তারপর এম দিয়ে ঘোরান, শেষে এ ইনভার্স দিয়ে আবার জেনিফারের ভাষায় ফেরত দিন। "
         "এই তিন ধাপের সম্মিলনই আমাদের কাঙ্ক্ষিত উত্তর।"),
    26: (" পুরো প্রক্রিয়াটি দাঁড়িয়েছে এ ইনভার্স, এম, এ—অর্থাৎ এ ইনভার্স এম এ গুণ জেনিফারের ভেক্টর। "
         "ডানের এ প্রথমে কাজ করে, মাঝের এম ঘোরায়, বাঁয়ের এ ইনভার্স শেষে ফেরত আনে। "
         "ক্রমটি এত গুরুত্বপূর্ণ যে একটু এদিক ওদিক হলেই উত্তর ভুল হয়ে যায়।"),
    27: (" কলাম হিসেবে ভাবলে বলা যায়—মূল ম্যাট্রিক্সের কলামগুলোকে ঘুরিয়ে নতুন কোথায় পড়ে, "
         "সেই অবস্থানগুলোকে আবার জেনিফারের ভাষায় লেখা হয়। "
         "তাই ফলাফলের প্রতিটি কলাম আসলে একই ঘূর্ণনের জেনিফার-রূপ। এই চিত্রটি একবার মনে গেঁথে গেলে সূত্রটি কখনো ভুলবেন না।"),
    28: (" যখনই পি ইনভার্স এম পি আকারের কোনো রাশি দেখবেন, বুঝবেন এটি দৃষ্টিভঙ্গি পরিবর্তনের গাণিতিক প্রকাশ। "
         "মাঝের ম্যাট্রিক্সটি আসল রূপান্তর, আর দুই পাশের ম্যাট্রিক্সদ্বয় দুটি ভিন্ন জগতের মাঝে অনুবাদ করে। "
         "এক ধরনের গাণিতিক সহানুভূতি—একই ঘটনাকে অন্যের চোখে দেখা।"),
    29: (" অনুরূপ ম্যাট্রিক্সের নির্ণায়ক আর ট্রেস অপরিবর্তিত থাকে, কারণ এরা একই রূপান্তরের বিভিন্ন ভাষা মাত্র। "
         "পরবর্তী অধ্যায়ে আইগেনভেক্টর আর আইগেনভ্যালু ব্যাখ্যা করবে কেন বিকল্প ভিত্তি বেছে নেওয়া এত গুরুত্বপূর্ণ। "
         "আজকের পাঠে আমরা দেখলাম ভিত্তি কেবল সংখ্যা বদলায় না, দৃষ্টিভঙ্গিও বদলায়। আবার দেখা হবে!"),
}

GENERIC_POOL = [
    (" এখানে একটু থামুন এবং নিজের ভাষায় বিষয়টি বলে দেখুন। কোনো ধারণা তখনই পোক্ত হয় যখন আপনি সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন। "
     "এই অভ্যাস আপনার বোঝাপড়াকে আরও গভীর করবে।"),
    (" মনে রাখবেন, রৈখিক বীজগণিতে প্রতিটি সংখ্যার পেছনে এক একটি জ্যামিতিক ছবি লুকিয়ে আছে। "
     "কেবল সূত্র মুখস্থ না করে সেই ছবিটি দেখার চেষ্টা করুন। তবেই এই বিষয়টি আপনার কাছে সত্যিই স্বজ্ঞাত হবে।"),
    (" আসুন একই উদাহরণটি অন্য একটি দৃষ্টিকোণ থেকে আবার দেখি। বারবার বিভিন্ন ভাষায় একই কথা বলা আমাদের বোঝাপড়াকে দৃঢ় করে। "
     "এতে ভুল হওয়ার সম্ভাবনাও অনেক কমে যায়।"),
    (" একই ভেক্টরকে একাধিক ভিত্তিতে লেখা যায়—এই সত্যটি রৈখিক বীজগণিতের অনেক শক্তিশালী কৌশলের ভিত্তি। "
     "আপনি যখনই কোনো জটিল ম্যাট্রিক্স দেখবেন, ভাববেন হয়তো অন্য কোনো ভিত্তিতে সেটি অনেক সরল দেখাবে।"),
    (" গাণিতিক ভাষাও দৈনন্দিন ভাষার মতোই—একই কথা বলার অনেক উপায় আছে। "
     "যে ভাষা কাজটিকে সবচেয়ে সহজ করে, বুদ্ধিমানের কাজ হলো সেটিই বেছে নেওয়া। ভিত্তি পরিবর্তন ঠিক এই কৌশলটিরই এক রূপ।"),
    (" প্রতিটি ধাপ যাচাই করে এগোনোর অভ্যাস গড়ে তুলুন। এখানে আমরা যে ম্যাট্রিক্স গুণন করলাম, "
     "তার ফল আবার উল্টো দিকে গুণ করে পরীক্ষা করা যায়। এই ধরনের নিজস্ব যাচাই আপনাকে আত্মবিশ্বাসী করে তোলে।"),
    (" লেখচিত্র আর সূত্র—এ দুটি একে অপরের পরিপূরক। সূত্র আমাদের নিখুঁত হিসাব দেয়, আর লেখচিত্র সেই হিসাবের পেছনের গল্প বলে। "
     "দুটিকে পাশাপাশি রেখে পড়লে কোনো ধারণাই অস্পষ্ট থাকে না।"),
    (" শেষে একটি ছোট্ট উপদেশ—ভয় না পেয়ে নিজে হাতে কলম নিয়ে একবার হিসাবটি করে দেখুন। "
     "যেভাবেই হোক, নিজে করা হিসাব আমাদের মনে দীর্ঘস্থায়ী হয়। পরের পাঠে আমরা এই একই ধারণা আরও এগিয়ে নিয়ে যাব।"),
]


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
    out = run(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{path}"')
    try:
        return float(out.strip())
    except Exception:
        return 0.0


def video_duration(path):
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


def load_manifest_cues():
    """Read the manifest (read-only). Cue texts are the dubbing script.
    Alias-dedup by normalised text so a repeated alias is spoken only once.
    """
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out, seen = [], set()
    for sec_id, sec in data.get("sections", {}).items():
        for c in sec.get("cues", []):
            text = c.get("text") or ""
            key = sanitize(text)
            if not key or key in seen:
                continue
            seen.add(key)
            out.append({
                "text": text,
                "dur_ms": float(c.get("duration_ms", 0)),
                "type": c.get("type", "p"),
                "section": sec_id,
                "index": c.get("index", 0),
            })
    return out


def allocate_windows(vend, source_cues):
    """Initial windows from authored weights, later replaced by rendered scale."""
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    weights = [c["dur_ms"] for c in source_cues]
    tot = sum(weights) or 1.0
    windows = [usable * w / tot for w in weights]
    desired = [max(1.0, w - BASE_GAP_SEC) for w in windows]
    return windows, desired, usable


def pick_extra(cid, pass_no):
    per = PER_CUE_EXPANSIONS.get(cid, [])
    if pass_no < len(per):
        return per[pass_no]
    return GENERIC_POOL[(cid * 3 + pass_no) % len(GENERIC_POOL)]


async def synth_and_expand(source_cues, desired):
    """Render every cue, then HEAVILY expand short ones until rendered speech
    fills its allocated window (adaptive, up to MAX_EXPANSION_PASSES)."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed, expanded = [], []
    for i, c in enumerate(source_cues):
        cid = i + 1
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        base = sanitize(c["text"])
        ok = await synth(base, raw)
        if not ok:
            failed.append(cid)
            print(f"  WARNING cue {cid} base TTS failed", flush=True)
            continue
        added = []
        natural_before = duration(raw)
        for p in range(MAX_EXPANSION_PASSES):
            nat = duration(raw)
            if nat >= EXPAND_TARGET_FRAC * desired[i]:
                break
            extra = pick_extra(cid, p)
            new_text = sanitize(" ".join([base] + added + [extra]))
            print(f"  fill-expand cue {cid:02d} pass {p+1}: "
                  f"natural={nat:.2f}s < {EXPAND_TARGET_FRAC*desired[i]:.2f}s", flush=True)
            if not await synth(new_text, raw, force=True):
                break
            added.append(extra)
        natural_after = duration(raw)
        if added:
            expanded.append({
                "id": cid,
                "natural_before": round(natural_before, 3),
                "natural_after": round(natural_after, 3),
                "target_sec": round(desired[i], 3),
                "passes": len(added),
            })
        if (i + 1) % 5 == 0:
            print(f"  TTS+expand {i+1}/{len(source_cues)}", flush=True)
    return failed, expanded


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


def make_cue(raw, window_sec, tempo, out, cid):
    """Stretch with atempo, PAD only (never truncate) to exactly the window."""
    natural = duration(raw)
    tmp = out.with_suffix(".fit.wav")
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)
    speech_samples = len(arr)
    need = int(round(window_sec * SR))
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
        "id": cid,
        "tempo": round(tempo, 4),
        "natural": round(natural, 3),
        "window_sec": round(window_sec, 3),
        "fill_ratio": round(fill, 4),
        "internal_gap_s": round(gap_s, 4),
        "speech_samples": speech_samples,
        "window_samples": need,
    }
    return arr, info


def silence_runs(path, start_s, end_s, threshold_db=SILENCE_DB, min_len=MAX_SILENCE_RUN_SEC):
    """Count silence runs > min_len strictly INSIDE [start_s, end_s] of the
    rendered master (lead-in / tail excluded)."""
    arr = read_pcm(path)
    a = max(0, int(round(start_s * SR)))
    b = min(len(arr), int(round(end_s * SR)))
    seg = arr[a:b]
    frame = int(0.02 * SR)
    n = len(seg) // frame
    if n == 0:
        return []
    amps = np.empty(n, dtype=np.float64)
    for i in range(n):
        block = seg[i * frame:(i + 1) * frame]
        amps[i] = float(np.sqrt(np.mean(block * block)))
    thr = 10.0 ** (threshold_db / 20.0)
    silent = amps < thr
    runs = []
    i = 0
    while i < n:
        if silent[i]:
            j = i
            while j < n and silent[j]:
                j += 1
            dur = (j - i) * 0.02
            if dur > min_len:
                runs.append({"start": round(start_s + i * 0.02, 3),
                             "end": round(start_s + j * 0.02, 3),
                             "duration": round(dur, 3)})
            i = j
        else:
            i += 1
    return runs


def volumedetect(path, start, length):
    log = EXP / "_volumedetect.log"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-nostats", "-vn", "-i", str(path),
           "-af", f"atrim=start={start}:duration={length},volumedetect", "-f", "null", "-"]
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


async def main():
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    vend = video_duration(ORIGINAL_VIDEO)
    source_cues = load_manifest_cues()
    n = len(source_cues)
    windows, desired, usable = allocate_windows(vend, source_cues)
    print(f"video={vend:.3f}s usable={usable:.3f}s cues={n} "
          f"(manifest, alias-deduped)", flush=True)

    print("[1/6] TTS + HEAVY expansion (read-only script source) ...", flush=True)
    failed, expanded = await synth_and_expand(source_cues, desired)

    # ---- (A) RECOMPUTE SCALE FROM RENDERED SPEECH -------------------------
    rendered = [duration(RAW_DIR / f"raw_{i+1:03d}.mp3") for i in range(n)]
    rendered_total = sum(rendered)
    scale_rendered = usable / (rendered_total + n * BASE_GAP_SEC)
    print(f"[2/6] recompute-scale-from-rendered-speech: rendered_total="
          f"{rendered_total:.3f}s scale_rendered={scale_rendered:.6f}", flush=True)

    # Per-cue window + tempo both derived from the MEASURED rendered speech.
    final_windows = [(rendered[i] + BASE_GAP_SEC) * scale_rendered for i in range(n)]
    tempos = []
    for i in range(n):
        t = rendered[i] / max(0.05, final_windows[i] - BASE_GAP_SEC)
        tempos.append(max(TEMPO_FLOOR, min(MAX_TEMPO, t)))
    print(f"  tempo range = [{min(tempos):.4f}, {max(tempos):.4f}]", flush=True)

    print("[3/6] Absolute-sample placement (window from rendered speech) ...", flush=True)
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    CHUNK = 1_000_000
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed, fills, gaps = [], [], []
    cursor = LEAD_IN_SEC
    overrun = 0
    for i, c in enumerate(source_cues):
        cid = i + 1
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            print(f"  SKIP cue {cid} (no audio)", flush=True)
            continue
        arr, info = make_cue(raw, final_windows[i], tempos[i],
                             CUE_DIR / f"cue_{cid:03d}.wav", cid)
        fills.append(info["fill_ratio"])
        gaps.append(info["internal_gap_s"])
        if info["speech_samples"] > info["window_samples"] + 200:
            overrun += 1
        if len(arr) >= 2 * fade_n:
            arr[:fade_n] *= env
            arr[-fade_n:] *= env[::-1]
        start_sample = int(round(cursor * SR))
        end = start_sample + len(arr)
        if end > len(canvas):
            canvas = np.pad(canvas, (0, end - len(canvas)))
        i16 = (np.clip(arr, -1.0, 1.0) * 32767.0).astype(np.int16)
        seg = canvas[start_sample:end].astype(np.int32)
        seg += i16.astype(np.int32)
        np.clip(seg, -32768, 32767, out=seg)
        canvas[start_sample:end] = seg.astype(np.int16)
        del arr, i16, seg
        placed.append({
            "id": cid,
            "section": c["section"],
            "type": c["type"],
            "expected_start_ms": round(cursor * 1000, 2),
            "actual_start_ms": round(start_sample / SR * 1000, 2),
            "drift_ms": round(start_sample / SR * 1000 - cursor * 1000, 6),
            "tempo": info["tempo"],
            "natural_sec": info["natural"],
            "window_sec": info["window_sec"],
            "fill_ratio": info["fill_ratio"],
            "internal_gap_s": info["internal_gap_s"],
            "placed_samples": end - start_sample,
            "expanded": any(e["id"] == cid for e in expanded),
        })
        cursor += final_windows[i]

    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    max_internal_gap = round(max(gaps), 4) if gaps else 0.0
    last_cue_end = cursor - BASE_GAP_SEC * scale_rendered

    # Peak-normalise in chunks.
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

    print("[4/6] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    # ---- (B) FILL GATE ----------------------------------------------------
    print("[5/6] FILL GATE measurement ...", flush=True)
    internal_runs = silence_runs(MASTER_WAV, LEAD_IN_SEC, vend - TAIL_MARGIN_SEC)
    gate_pass = bool(median_fill >= MEDIAN_FILL_MIN
                     and max_internal_gap <= MAX_INTERNAL_GAP_SEC
                     and len(internal_runs) == 0)
    print(f"  median_fill={median_fill} (>= {MEDIAN_FILL_MIN})  "
          f"max_internal_gap={max_internal_gap}s (<= {MAX_INTERNAL_GAP_SEC})  "
          f"internal_silence_runs>2s={len(internal_runs)}  ->  "
          f"GATE {'PASS' if gate_pass else 'FAIL'}", flush=True)

    print("[6/6] Mux with FULL original video (-c:v copy) ...", flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    report = {
        "experiment": "fill_v2 (recompute-scale-from-rendered-speech + fill gate)",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": f"audio_manifest:{MANIFEST.name} (cue texts, alias-deduped)",
        "cue_count": len(placed),
        "expected_cue_count": n,
        "failed_tts_cues": failed,
        "strategy": "windows/tempo recomputed from measured rendered speech; absolute "
                    "sample offset (start*44100); atempo fit; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "tempo_floor": TEMPO_FLOOR,
        "base_gap_sec": BASE_GAP_SEC,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "rendered_total_sec": round(rendered_total, 3),
        "recomputed_scale_from_rendered": round(scale_rendered, 6),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        # fill-gate metrics
        "median_fill": median_fill,
        "max_internal_gap_s": max_internal_gap,
        "internal_silence_runs_gt_2s": internal_runs,
        "internal_silence_run_count": len(internal_runs),
        "gate_thresholds": {
            "median_fill_min": MEDIAN_FILL_MIN,
            "max_internal_gap_sec": MAX_INTERNAL_GAP_SEC,
            "max_internal_silence_runs_gt_2s": 0,
        },
        "fill_gate_pass": gate_pass,
        "fill_expansions_applied": expanded,
        "expansion_target_frac": EXPAND_TARGET_FRAC,
        "cues": placed,
    }
    report["output_video"] = str(OUT_VIDEO)
    report["output_duration_sec"] = round(duration(OUT_VIDEO), 3)
    report["output_size_bytes"] = OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0
    try:
        probe = json.loads(run(f'ffprobe -v error -show_entries stream=index,codec_type,codec_name '
                               f'-of json "{OUT_VIDEO}"'))
        report["output_streams"] = probe.get("streams", [])
    except Exception as e:
        report["output_streams_error"] = str(e)
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    odur = duration(OUT_VIDEO)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={report['output_duration_sec']}s size={report['output_size_bytes']}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap_s={max_internal_gap} "
          f"internal_runs={len(internal_runs)} scale_rendered={scale_rendered:.4f} "
          f"GATE={'PASS' if gate_pass else 'FAIL'}", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)

    if not gate_pass:
        raise SystemExit("FILL GATE FAILED — do not claim success")


if __name__ == "__main__":
    asyncio.run(main())
