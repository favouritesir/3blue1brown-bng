"""
EXPERIMENT fill_v2 — Full-length Bengali re-render of Calculus Lesson 02
=========================================================================
"The derivative paradox" (3Blue1Brown, 9vKqVkMQHKk). Re-render of the earlier
clean_timesync_v2 dub which had 59 internal silent pockets (up to ~12 s).

Adapted from the quality-gated pipeline:
  essence_of_calculus/lesson_08_integration/dubbing_pipeline/experiments/
  clean_timesync_v2/build_calc08_clean.py
and the proven "recompute scale from rendered speech + fill gate + auto
re-render" implementation used by:
  differential_equations/lesson_05_full_dub/.../build_de05_clean.py
  lockdown_math/lesson_09/.../build_lock09_clean.py

WHAT IS DIFFERENT HERE
----------------------
  1. Cue source is the AUDIO MANIFEST
       web_platform/assets/audio/calculus/lesson_02/manifest.json
     (read-only). The manifest stores every section twice (canonical id and
     alias id); cues are ALIAS-DEDUPE'd by section_id -> 32 unique cues whose
     texts are used verbatim as the dubbing script.
  2. HEAVY pedagogical Bengali expansion. The 32 manifest cues author only
     ~470.8 s while the source video is ~1009.8 s, so each cue window is ~2x
     its authored duration. Every cue is expanded with section-specific,
     pedagogically meaningful Bengali narration until its rendered speech
     reaches NATURAL_TARGET_FRACTION of its equal share of the usable video.
  3. TIMELINE SCALE IS RECOMPUTED FROM THE SUM OF RENDERED SPEECH after every
     expansion (not from authored durations): scale = usable / (sum(naturals)
     + pauses). With scale ~ 1.0 every cue window is filled by its own speech.
  4. QUALITY GATE: median_fill >= 0.72 and max_internal_gap_s <= 1.5 s.
     On failure, low-fill cues are expanded and re-synthesised (up to
     MAX_RERENDER_ATTEMPTS rounds) and the scale is recomputed each round.
  5. Long intra-cue TTS silences are capped (1.0 s) and inter-cue pause is
     kept short, so silencedetect(d=2) sees only the lead-in and the tail.
  6. The FULL original video is reused (video -c:v copy, no re-download, no
     source swap). Canvas is padded to the full video duration so -shortest
     can never trim video frames. Old dubbed video is NEVER overwritten.
  7. Post-mux verification: ffprobe duration + silencedetect internal-run scan
     are written into verification.json.

NOTE ON THE "~589 s" EXPECTATION
--------------------------------
The specified source full_original.mp4 is 1009.81 s. 589 s is the OLD 60-cue
master-script's authored timeline (567.9 s of cues + 59 x 0.35 s pauses =
588.55 s). This build uses the full 1009.8 s source as instructed and does
not swap or truncate the video source.
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
BASE = EXP.parent.parent                        # .../lesson_02_derivative_paradox/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
MANIFEST = WEB / "assets" / "audio" / "calculus" / "lesson_02" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "calculus" / "lesson_02" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "calculus" / "lesson_02" / "experiments" / "fill_v2" / "3b1b_calculus_02_full_dubbed_fill2.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MIN_TEMPO = 0.82
MAX_TEMPO = 2.2
FADE_MS = 12
VIDEO_ID = "9vKqVkMQHKk"
LESSON = "lesson_02_derivative_paradox"

# Keep the first 2.5 s and the last 3 s free of speech (silencedetect sees only
# these two pockets). The inter-cue pause is deliberately short.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 260.0

# Fill policy (IMPROVED_DUB_FILL_POLICY.md).
GATE_MEDIAN_FILL = 0.72
GATE_MAX_INTERNAL_GAP = 1.5
RERENDER_TARGET_FILL = 0.90
MAX_RERENDER_ATTEMPTS = 3

# Heavy-expansion constants.
NATURAL_TARGET_FRACTION = 0.80     # each cue's rendered speech target share;
                                   # one sentence is added per pass so the
                                   # final overshoot keeps tempo near 1.0x
MAX_APPENDED_SENTENCES = 20
ACTIVE_THRESHOLD = 0.015
MAX_INTRA_CUE_SILENCE_S = 1.0
TRIM_EDGE_S = 0.06                 # trim TTS leading/trailing silence

# ---------------------------------------------------------------------------
# Section-specific pedagogical Bengali expansion pools. Every sentence is a
# complete, naturally spoken teaching thought drawn from the lesson content.
# They are appended (after sanitize) only where a cue's rendered speech is
# short of its window, so they improve teaching quality while removing gaps.
# ---------------------------------------------------------------------------
EXPANSION_POOL = {
    "sec-paradox": [
        "আসুন একটু থেমে এই উদাহরণটির দিকে আবার তাকাই। গাড়িটি যখন বিন্দু এ থেকে বিতে যায়, তখন তার গতি সারা পথে একরকম থাকে না—শুরুতে ধীর, মাঝখানে দ্রুত, আর শেষে আবার ধীর হয়ে থামে। তবুও স্পিডোমিটারের কাঁটা একটিমাত্র সংখ্যা দেখায়। সেই একটিমাত্র সংখ্যা দিয়েই আমাদের কীভাবে পুরো যাত্রার গতি বোঝা যায়, সেটাই ভাবার বিষয়।",
        "গড় বেগ আর তাৎক্ষণিক বেগের পার্থক্য আসলে সময়ের ব্যবধানের উপর নির্ভর করে। দশ সেকেন্ডে একশো মিটার গেলে গড় বেগ দশ মিটার প্রতি সেকেন্ড; কিন্তু তৃতীয় সেকেন্ডে গাড়িটি ছিল আরও দ্রুত। একক মুহূর্তের গতি ধরতে হলে সময়ের ব্যবধানকে যত ছোট করা যায়, তত কাছাকাছি পাওয়া যায় সত্যিকারের উত্তর।",
        "চলুন একে অঙ্কনের ভাষায় বলি। দূরত্ব আর সময়ের লেখচিত্রে কোনো বিন্দুর ঢাল মানে সেই বিন্দুতে গাড়িটি কত দ্রুত যাচ্ছে। দুটি দূরের বিন্দু নিলে পাই ছেদকের ঢাল, আর বিন্দু দুটিকে কাছে আনলে সেটি ধীরে ধীরে স্পর্শকের ঢালে রূপ নেয়। এই রূপান্তরটিই ক্যালকুলাসের প্রথম বড় পদক্ষেপ।",
        "প্যারাডক্সটি আসলে আমাদের চোখে দেখা স্থির ছবি আর চলমান সময়ের মধ্যে রয়েছে। একটি ছবিতে গতি নেই, কিন্তু ছবিগুলোকে খুব কাছাকাছি ধরে নিলে গতির ছাপ পড়ে। শূন্য সময় আর শূন্য দূরত্বের অনুপাত অনির্ণেয় হলেও, শূন্যের কাছাকাছি থেকে শুরু করে সীমার মাধ্যমে একটি নির্দিষ্ট উত্তর বের করা যায়।",
        "মনে রাখবেন, স্পিডোমিটার কখনোই একক মুহূর্ত মাপে না। সেটি কয়েক মিলিসেকেন্ডের ব্যবধানে চাকার ঘূর্ণন মেপে সেই ছোট দূরত্বকে ছোট সময় দিয়ে ভাগ করে। আমাদের হিসাবও ঠিক একই কৌশল অনুসরণ করে—ব্যবধান ছোট করি, কিন্তু কখনো শূন্য ধরি না।",
        "দূরত্বের লেখচিত্রের উচ্চতা যেমন বাড়ে, তেমনি তার ঢালও বদলায়। কোনো এক বিন্দুতে যদি ঢাল বেশি হয়, বুঝতে হবে গাড়িটি সেখানে দ্রুত চলছে। ঢাল শূন্য হলে গাড়িটি স্থির; ঢাল ঋনাত্মক হলে সেটি পিছনে ফিরছে। এইভাবে একটি ছবি থেকেই গতির পুরো গল্প পড়া যায়।",
        "প্রশ্ন ওঠে, তিন সেকেন্ডে গাড়িটি সবচেয়ে দ্রুত কেন? কারণ সেই সময়ে বক্ররেখার ঢাল সবচেয়ে খাড়া। ছয় সেকেন্ডে উচ্চতা বেশি হলেও ঢাল কমে এসেছে, অর্থাৎ গাড়িটি ধীর হয়ে এসেছে। উচ্চতা আর ঢাল—এ দুটি আলাদা ধারণা, আর আমাদের কাজ হলো দ্বিতীয়টিকে নিখুঁতভাবে মাপা।",
        "ইতিহাসে এই প্যারাডক্সের সমাধানই ক্যালকুলাসের জন্ম দিয়েছে। নিউটন আর লাইবনিজ প্রথমে ভাবলেন, শূন্যের দিকে ধাবমান এক প্রক্রিয়া দিয়ে এই অদ্ভুত ভাগের অর্থ দেওয়া যায়। সেই প্রক্রিয়ার নাম সীমা, আর তার মাধ্যমেই আমরা তাৎক্ষণিক বেগের সংজ্ঞা পাই।",
    ],
    "sec-derivative-meaning": [
        "এখানে একটি গুরুত্বপূর্ণ ব্যাখ্যা রয়েছে। ক্যালকুলাস শূন্য দিয়ে শূন্যকে ভাগ করে না; সেটি করে শূন্যের কাছাকাছি আসার এক প্রক্রিয়া। প্রথমে আমরা একটি সসীম ছোট সময় নিই, তারপর দেখি সেটি ছোট হতে হতে উত্তরটি কোথায় স্থির হচ্ছে। এই স্থির মানটিই আমাদের কাঙ্ক্ষিত অন্তরজ।",
        "ডি টি কে আমরা কখনো শূন্য বলি না। এটি একটি অতি ক্ষুদ্র কিন্তু অশূন্য সময়—হয়তো এক হাজার ভাগের এক সেকেন্ড। এই সংক্ষিপ্ত ব্যবধানে গাড়ি যে সামান্য পথ যায়, তা হলো ডি এস। দুটির অনুপাত আমাদের একটি ভালো আসন্ন মান দেয়, যা বাস্তব স্পিডোমিটারের পড়ার কাছাকাছি।",
        "সূত্রটিকে আবার লিখে দেখি। তাৎক্ষণিক বেগ সমান ডি এস ভাগ ডি টি। আর ডি এস হলো এস অফ টি প্লাস ডেল্টা টি বিয়োগ এস অফ টি। অর্থাৎ একই সূত্রটা আমরা সময়ের ব্যবধান ছোট করার আগে ও পরে দুইভাবে লিখতে পারি—এই দুই রূপের মিলনেই সীমার ধারণা জন্মায়।",
        "কল্পনা করুন, আপনি গাড়িটির ছবি তুললেন ঠিক পাঁচ সেকেন্ডে। সেই একক ছবি দেখে বেগ বের করা যাবে না, কারণ ছবিতে কোনো সময় ব্যবধান নেই। তাই আপনাকে আরেকটি ছবি লাগবে—সামান্য পরের মুহূর্তের। দুটি ছবির দূরত্ব আর সময়ের পার্থক্য নিলেই গতির আনুমানিক মান পাওয়া যায়।",
        "বাস্তব স্পিডোমিটারের হিসাবও এরকম। সেটি তিন দশমিক শূন্য এক সেকেন্ডের মতো ক্ষুদ্র ব্যবধানে দূরত্বের সামান্য বৃদ্ধি মেপে ভাগ করে বেগ নির্ণয় করে। ব্যবধান যত ছোট, ফলাফল তত নির্ভুল— কিন্তু কখনোই শূন্য নয়। এই ব্যাখ্যাটি মনে রাখলে শূন্য ভাগ শূন্যের প্যারাডক্স আর থাকে না।",
        "অনুপাতটির আচরণ লক্ষ্য করুন। ডি টি কে হাজার ভাগ, লাখ ভাগ, কোটি ভাগ ছোট করতে থাকলে ডি এস-ও ছোট হয়, কিন্তু তাদের ভাগফল কমে যায় না। সেটি একটি নির্দিষ্ট সংখ্যার দিকে এগিয়ে যায়। এই স্থিরতাই বলে দেয় যে সীমাস্থ মান আসলেই আছে—কেবল আমাদের সেটি বের করতে হবে।",
        "গাণিতিক ভাষায় ডি অক্ষরটির মানে ছোট পার্থক্য। ডি টি মানে সময়ের ছোট পরিবর্তন, ডি এস মানে দূরত্বের ছোট পরিবর্তন। এই ছোট্ট ডি অক্ষরটি আমাদের স্বাভাবিক অনুপাত আর সীমাস্থ অনুপাতের মাঝে সেতু বানায়। একে বাদ দিলে সূত্রটি শূন্য ভাগ শূন্য হয়ে দাঁড়ায়।",
        "অন্তরজ কেবল গাড়ির বেগ নয়। যেকোনো পরিবর্তনশীল রাশির ক্ষেত্রেই একই কৌশল কাজ করে—তাপমাত্রার পরিবর্তনের হার, জনসংখ্যার বৃদ্ধির হার, কিংবা কোনো ফাংশনের ঢাল। একবার এই ভাবনাটি বোঝা গেলে, ক্যালকুলাসের বাকি সব অধ্যায় সহজ হয়ে যায়।",
    ],
    "sec-tangent-zoom": [
        "জ্যামিতিকভাবে কী হচ্ছে, সেটি একবার মনে আঁকুন। সময় অনুভূমিক অক্ষে আর দূরত্ব উল্লম্ব অক্ষে নিলে গাড়ির যাত্রা একটি বক্ররেখা তৈরি করে। এই বক্ররেখার প্রতিটি বিন্দুতে রয়েছে একটি নির্দিষ্ট ঢাল, আর সেই ঢালই হলো সেই মুহূর্তের বেগ।",
        "দুটি বিন্দুর মাঝে টানা ছেদকের ঢাল হলো খাড়া উচ্চতা ভাগ আনুভূমিক দৈর্ঘ্য। অর্থাৎ দূরত্বের পার্থক্য ভাগ সময়ের পার্থক্য। এই হিসাবটা আমরা আগেই করেছি; এখন শুধু বিন্দু দুটিকে একে অপরের কাছে আনতে হবে। তখন ছেদকটি আর ছেদক থাকবে না—হয়ে যাবে স্পর্শক।",
        "অসীম জুমের কথাটি একটু ভেবে দেখুন। বক্ররেখার যেকোনো মসৃণ অংশকে যত কাছ থেকে দেখা যায়, সেটি তত বেশি সরলরেখার মতো দেখায়। পৃথিবীও তো আমাদের কাছে সমতল মনে হয়, অথচ দূর থেকে সেটি গোল। এই স্থানীয় সরলতাই লেখচিত্রের ক্ষেত্রে কাজ করে।",
        "ছোট ত্রিভুজটি কেন এত গুরুত্বপূর্ণ? কারণ তার অনুভূমিক বাহু ডি টি আর উল্লম্ব বাহু ডি এস। এই দুই বাহুর অনুপাতই ঢাল, আর ঢালই অন্তরজ। ত্রিভুজটি যত ছোট হয়, সেটি বক্ররেখার ওপর তত ভালো করে বসে—আর ফলাফল তত নির্ভুল।",
        "স্থানীয় রৈখিকতা বলতে বোঝায় যে প্রতিটি মসৃণ বক্ররেখা স্থানীয়ভাবে একটি সরলরেখা। সেই সরলরেখার ঢালই আমাদের খোঁজা অন্তরজ। তাই অন্তরজ কোনো বিমূর্ত সূত্র নয়, বরং একটি ছোট্ট সরলরেখার ঢাল মাত্র—এই ছবিটি মনে রাখলেই সূত্রটি স্বয়ংক্রিয়ভাবে মনে পড়বে।",
        "স্পর্শক আর ছেদকের মাঝের এই সম্পর্ক আসলে আগের পাঠের সীমার ধারণারই জ্যামিতিক রূপ। বিন্দু দুটির দূরত্ব শূন্যের দিকে গেলে ছেদকের ঢাল স্পর্শকের ঢালে পরিণত হয়। একই ঘটনাকে একদিকে হিসাবের ভাষায়, অন্যদিকে ছবির ভাষায় দেখলাম—দুটি ভাষা একই কথা বলছে।",
        "চলুন একটি ব্যবহারিক উদাহরণে পরীক্ষা করি। যদি কোনো বিন্দুতে স্পর্শক অনুভূমিক হয়, সেখানে গাড়িটি স্থির অথচ দূরত্ব সর্বোচ্চ বা সর্বনিম্ন হতে পারে। ঢালের এই শূন্য মান আমাদের বলে দেয় কোথায় গাড়িটি থামল বা দিক বদলাল। পরবর্তী পাঠে এই ধারণাটি খুব কাজে আসবে।",
    ],
    "sec-x2-geometry": [
        "মুখস্থ সূত্র আমাদের বলে এক্স স্কয়ারের অন্তরজ দুই এক্স, কিন্তু এই দুইটি কোথা থেকে এলো? সেটাই আজকের পরীক্ষার মূল প্রশ্ন। আমরা কোনো সূত্র মেনে নেব না; বরং একটি ছবি এঁকে দেখব যে দুই সংখ্যাটি স্বাভাবিকভাবেই বেরিয়ে আসে।",
        "বর্গক্ষেত্রটির এক বাহু এক্স হলে ক্ষেত্রফল এক্স গুণ এক্স, অর্থাৎ এক্স স্কয়ার। এখন দৈর্ঘ্য ও প্রস্থ—দুই দিকেই ডি এক্স যোগ করলাম। নতুন বর্গের বাহু হলো এক্স প্লাস ডি এক্স, আর নতুন ক্ষেত্রফল হলো তার বর্গ। পুরোনো অংশটি তো আছেই, শুধু নতুন যোগ হওয়া টুকরোগুলোই বৃদ্ধি।",
        "নতুন ক্ষেত্রফলটি তিনটি অংশে ভেঙে পড়ে। উপরের ধারে এক্স গুণ ডি এক্স আয়তাকার ফালি, ডান ধারে আরেকটি এক্স গুণ ডি এক্স ফালি, আর কোণায় ডি এক্স গুণ ডি এক্স ছোট্ট বর্গ। মূল এক্স স্কয়ার অপরিবর্তিত থাকে; বৃদ্ধি মানে কেবল এই তিনটি নতুন টুকরো।",
        "কোণার ছোট্ট বর্গটি হলো ডি এক্সের বর্গ। ডি এক্স যখন শূন্যের দিকে যায়, এই পদটি তত দ্রুত ছোট হয়—কারণ এটি ডি এক্সের চেয়েও ছোট। তাই সীমাস্থ অবস্থায় এটি নগণ্য হয়ে যায়। কিন্তু দুটি ফালি তো ডি এক্সের সমানুপাতিক, ভাগ করলে সেগুলো অবশিষ্ট থাকে।",
        "দুই ফালি কেন আছে, সেটি বোঝাই মূল কথা। একটি ফালি উপরের ধারে, অর্থাৎ প্রস্থ বাড়ার ফলে; অন্যটি ডান ধারে, অর্থাৎ দৈর্ঘ্য বাড়ার ফলে। বর্গক্ষেত্রের দুটি বর্ধনশীল ধারই এই দুই সংখ্যার উৎস। তাই দুই কোনো বিমূর্ত সহগ নয়, বরং জ্যামিতির উপহার।",
        "এবার হিসাবটি শেষ করি। নতুন ক্ষেত্রফল বিয়োগ পুরোনো ক্ষেত্রফল সমান দুই এক্স গুণ ডি এক্স প্লাস ডি এক্সের বর্গ। উভয় পক্ষকে ডি এক্স দিয়ে ভাগ করলে পাই দুই এক্স প্লাস ডি এক্স। তারপর ডি এক্স শূন্যের দিকে পাঠালেই অবশিষ্ট থাকে শুধু দুই এক্স।",
        "এই ফলাফলের সাথে আমাদের আগের সীমার ভাবনা মিলিয়ে দেখুন। সীমাস্থ অবস্থায় অনুপাতটি যে স্থির মানের দিকে যায়, সেটিই অন্তরজ। এক্স স্কয়ারের ক্ষেত্রে সেই স্থির মান দুই এক্স। অর্থাৎ জ্যামিতি আর হিসাব একই উত্তর দিচ্ছে—এই মিলনই ক্যালকুলাসের সৌন্দর্য।",
        "মনে রাখবেন, এক্স স্কয়ারের অন্তরজ মুখস্থ করার দরকার নেই। মনের মধ্যে একটি বর্গক্ষেত্র আঁকুন, তার দুটি ধারে দুটি ফালি যোগ করুন, কোণার ক্ষুদ্র বর্গটি বাদ দিন—দুই এক্স নিজেই বেরিয়ে আসবে। এই চোখটি খুলে গেলে বাকি সব নিয়ম নিজেই তৈরি করা যায়।",
    ],
}

GENERIC_EXTRA = [
    "এখানে একটু থামুন এবং বিষয়টি নিজের ভাষায় বলে দেখুন। কোনো ধারণা তখনই পোক্ত হয় যখন আপনি সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন। এই অভ্যাস আপনার বোঝাপড়াকে আরও গভীর করবে।",
    "আগের ধাপটির সাথে এই ধাপটির সম্পর্কটি লক্ষ্য করুন। ক্যালকুলাস কখনোই আলাদা আলাদা সূত্রের সংগ্রহ নয়; প্রতিটি নতুন ধারণা আগেরটির ওপর নির্মিত হয়। এই ধারাবাহিকতা বুঝতে পারলে পুরো পাঠটি একটিমাত্র গল্পের মতো মনে হবে।",
    "চলুন একই বিষয়টি অন্য একটি দিক থেকে দেখি। যে হিসাবটি আমরা পাপের সাহায্যে করলাম, সেটিকে লেখচিত্রের সাহায্যেও ব্যাখ্যা করা যায়। দুই পদ্ধতি থেকে একই ফল পাওয়া আমাদের বোঝাপড়াকে আরও দৃঢ় করে তোলে।",
    "প্রশ্ন করা একটি গুরুত্বপূর্ণ অংশ। কেন ঠিক এই উত্তরটি এলো, অন্য উত্তরটি কেন এলো না—এই প্রশ্নগুলো নিজের মধ্যে জাগালে সূত্র মুখস্থ করার প্রয়োজন থাকে না। সত্যিকারের শিক্ষা তখনই হয় যখন আপনি নিজেই যুক্তিটি পুনরায় গড়ে তুলতে পারেন।",
    "মনে রাখবেন, এই ধারণাটি পরবর্তী পাঠে আবার কাজে আসবে। আজ আমরা যে ছোট্ট সময়ের ব্যবধান নিয়ে কাজ করেছি, তার ওপর ভিত্তি করেই পরে অসীমের যোগফল আর ক্ষেত্রফলের হিসাব গড়ে উঠবে। ভিতটি আজই শক্ত করে নিচ্ছি।",
    "একবার ভেবে দেখুন, যদি গাড়িটির গতি সারাক্ষণ একই রকম হতো, তবে ক্যালকুলাসের প্রয়োজন হতো না। পরিবর্তনশীলতাই অবকলনের জন্ম দেয়। তাই যেখানেই কোনো কিছু বদলাচ্ছে, সেখানেই এই হারের ধারণা প্রয়োগ করা যায়।",
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


# ---------------------------------------------------------------------------
# Cue loading: manifest is the script; sections are duplicated by alias, so
# dedupe by section_id and keep the canonical (first) occurrence.
# ---------------------------------------------------------------------------
def load_manifest_cues():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    seen = set()
    out = []
    for sec_id, sec in data.get("sections", {}).items():
        sid = sec.get("section_id") or sec_id
        if sid in seen:
            continue
        seen.add(sid)
        for c in sec.get("cues", []):
            text = (c.get("text") or "").strip()
            if not text:
                continue
            dms = float(c.get("duration_ms", 0))
            if dms <= 0:
                dms = float(c.get("end_ms", 0)) - float(c.get("start_ms", 0))
            out.append({
                "text": text,
                "dur_ms": max(1000.0, dms),
                "section": sid,
                "alias": sec.get("alias") or sec_id,
            })
    return out, f"audio_manifest:{MANIFEST.name} (alias-deduped by section_id)"


def load_master_sentences():
    """Read-only fallback pool from the old 60-cue master script, if present."""
    masters = sorted(BASE.parent.glob("**/*master_script*.json"))
    if not masters:
        # lesson_02_derivative (old folder) lives next to our lesson folder.
        masters = sorted(BASE.parent.parent.glob("lesson_02_derivative/**/*master_script*.json"))
    if not masters:
        return []
    try:
        d = json.loads(masters[0].read_text(encoding="utf-8"))
        return [sanitize(c["bn"]) for c in d if c.get("bn")]
    except Exception:
        return []


def load_cues(vend, source_cues):
    """Pre-expansion layout estimate (the real layout is recomputed from speech)."""
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
            "alias": c["alias"],
        })
        cursor_ms += c["dur_ms"] + INTER_CUE_PAUSE_MS
    return cues, scale


async def synth_all(cues):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, c in enumerate(cues):
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        ok = await synth(sanitize(c["bn"]), raw)
        if not ok:
            failed.append(c["id"])
            print(f"  WARNING cue {c['id']} failed after every fallback", flush=True)
        if (i + 1) % 8 == 0:
            print(f"  TTS {i+1}/{len(cues)}", flush=True)
    return failed


def section_pool(section, extra):
    pool = list(EXPANSION_POOL.get(section, []))
    pool.extend(extra)
    pool.extend(GENERIC_EXTRA)
    return pool


async def expand_short_cues(cues, usable_sec, extra):
    """HEAVY expansion: grow every cue's rendered speech to its share of video."""
    per_cue = usable_sec / max(1, len(cues))
    natural_target = NATURAL_TARGET_FRACTION * per_cue
    print(f"  heavy-expansion natural target = {natural_target:.2f}s per cue "
          f"(usable={usable_sec:.1f}s / {len(cues)} cues)", flush=True)
    expanded = []
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        natural = duration(raw)
        if natural <= 0 or natural >= natural_target:
            continue
        pool = section_pool(c["section"], extra)
        base = sanitize(c["bn"])
        added = []
        before = natural
        while len(added) < MAX_APPENDED_SENTENCES:
            need = natural_target - natural
            if need <= 0:
                break
            # One pedagogical sentence is ~12-16 s of Bengali speech. Add ONE
            # at a time and re-measure: avoids the large over-expansion that
            # would force an unnecessarily fast atempo during layout.
            n = 1
            k = len(added)
            new_parts = [pool[(k + j) % len(pool)] for j in range(n)]
            new_text = sanitize(base + " " + " ".join(added + new_parts))
            print(f"  expand cue {cid} [{c['section']}]: {natural:.1f}s -> "
                  f"{natural_target:.1f}s (+{n} sentences)", flush=True)
            if not await synth(new_text, raw, force=True):
                break
            added.extend(new_parts)
            natural = duration(raw)
            if natural >= natural_target:
                break
        if added:
            c["bn"] = sanitize(base + " " + " ".join(added))
            expanded.append({
                "id": cid,
                "section": c["section"],
                "natural_before": round(before, 3),
                "natural_after": round(natural, 3),
                "natural_target": round(natural_target, 3),
                "sentences_added": len(added),
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


def active_bounds(arr, thr=ACTIVE_THRESHOLD):
    active = np.flatnonzero(np.abs(arr) > thr)
    if active.size == 0:
        return 0, arr.size
    return int(active[0]), int(active[-1]) + 1


def internal_gap_s(arr, sr=SR, thr=ACTIVE_THRESHOLD):
    if arr.size == 0:
        return 0.0
    lo, hi = active_bounds(arr, thr)
    if hi - lo < 2:
        return 0.0
    active = np.flatnonzero(np.abs(arr[lo:hi]) > thr)
    if active.size < 2:
        return 0.0
    return float(np.diff(active).max()) / sr


def cap_long_silences(arr, sr=SR, thr=ACTIVE_THRESHOLD, max_silence_s=MAX_INTRA_CUE_SILENCE_S):
    lo, hi = active_bounds(arr, thr)
    if hi - lo < 2:
        return arr, 0
    seg = arr[lo:hi]
    pad = np.concatenate(([False], np.abs(seg) <= thr, [False]))
    d = np.diff(pad.astype(np.int8))
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1)
    max_run = int(round(max_silence_s * sr))
    keep = np.ones(seg.size, dtype=bool)
    removed = 0
    for s, e in zip(starts, ends):
        run = e - s
        if run > max_run:
            drop = run - max_run
            half = drop // 2
            keep[s + half:s + half + drop] = False
            removed += drop
    if removed:
        seg = seg[keep]
        arr = np.concatenate((arr[:lo], seg, arr[hi:]))
    return arr, removed


LAST_START = 0.0
VIDEO_END = 0.0
LAST_ID = None


def make_cue(raw, target, out, cid):
    """atempo-fit into the window (floor 0.82); PAD only, NEVER truncate."""
    natural = duration(raw)
    if natural <= 0:
        natural = target
    if cid == LAST_ID:
        target = min(target, VIDEO_END - LAST_START - 0.10)
    tempo = max(MIN_TEMPO, min(MAX_TEMPO, natural / target))
    tmp = out.with_suffix(".fit.wav")
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)
    # Trim TTS encoder lead-in/out silence so inter-cue gaps stay < 2 s.
    lo, hi = active_bounds(arr)
    edge = int(TRIM_EDGE_S * SR)
    if hi > lo:
        lo = max(0, lo - edge)
        hi = min(arr.size, hi + edge)
        arr = arr[lo:hi]
    arr, removed = cap_long_silences(arr)
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
    return arr, tempo, natural, target, fit_samples, removed


def layout(cues, usable, vend):
    """Recompute timeline scale from the SUM of currently rendered speech."""
    naturals = {}
    for c in cues:
        rawp = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        naturals[c["id"]] = duration(rawp) if valid(rawp) else 0.0
    total_natural = sum(naturals.values())
    expanded_total = total_natural + INTER_CUE_PAUSE_MS * (len(cues) - 1) / 1000.0
    scale = usable / expanded_total if expanded_total > 0 else 1.0
    cursor_ms = 0.0
    for c in cues:
        nat = naturals.get(c["id"], 0.0) or 2.0
        start = LEAD_IN_SEC + (cursor_ms / 1000.0) * scale
        dur = nat * scale
        c["start"] = round(start, 3)
        c["end"] = round(start + dur, 3)
        c["duration"] = round(dur, 3)
        cursor_ms += nat * 1000.0 + INTER_CUE_PAUSE_MS
    return scale, total_natural, expanded_total, naturals


def place_all(cues, vend, expanded_ids):
    """Absolute sample placement on a full-length canvas; measure fill + gaps."""
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    CHUNK = 1_000_000
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    overrun = 0
    last_cue_end = 0.0
    total_removed = 0
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            print(f"  SKIP cue {cid} (no audio)", flush=True)
            continue
        arr, tempo, natural, target, fit_samples, removed = make_cue(
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
        last_cue_end = max(last_cue_end, end / SR)
        total_removed += removed
        if end - start_sample > int(float(c["duration"]) * SR) + 200:
            overrun += 1
        window = int(round(target * SR))
        fill = min(1.0, fit_samples / window) if window > 0 else 0.0
        placed.append({
            "id": cid,
            "section": c["section"],
            "expected_start_ms": round(float(c["start"]) * 1000, 2),
            "actual_start_ms": round(start_sample / SR * 1000, 2),
            "drift_ms": round(start_sample / SR * 1000 - float(c["start"]) * 1000, 6),
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3),
            "target_sec": round(target, 3),
            "fill": round(fill, 4),
            "max_internal_gap_s": round(gap_s, 4),
            "fit_samples": fit_samples,
            "window_samples": window,
            "expanded": cid in expanded_ids,
        })
    return canvas, placed, overrun, total_removed, last_cue_end


async def rerender_low_fill(cues, placed, extra, attempt):
    fixed = []
    for rec in placed:
        if (rec["fill"] >= RERENDER_TARGET_FILL
                and rec["max_internal_gap_s"] <= GATE_MAX_INTERNAL_GAP):
            continue
        c = next((x for x in cues if x["id"] == rec["id"]), None)
        if c is None:
            continue
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        natural = duration(raw)
        if natural <= 0:
            continue
        need_natural = RERENDER_TARGET_FILL * MIN_TEMPO * rec["target_sec"]
        need = max(need_natural - natural, 4.0)
        pool = section_pool(c["section"], extra)
        base = sanitize(c["bn"])
        n = max(1, min(MAX_APPENDED_SENTENCES, int(np.ceil(need / 12.0))))
        off = (attempt * 3 + rec["id"]) % len(pool)
        append = " ".join(pool[(off + j) % len(pool)] for j in range(n))
        new_text = sanitize(base + " " + append)
        print(f"  re-render cue {rec['id']}: fill={rec['fill']} gap="
              f"{rec['max_internal_gap_s']}s natural={natural:.1f}s (+{n} sent)", flush=True)
        if await synth(new_text, raw, force=True):
            c["bn"] = new_text
            fixed.append({
                "id": rec["id"],
                "fill_before": rec["fill"],
                "gap_before_s": rec["max_internal_gap_s"],
                "natural_before": round(natural, 3),
                "sentences_added": n,
            })
    return fixed


def silence_runs(path):
    """Return (start, end) silence runs from ffmpeg silencedetect at -35 dB, d=2."""
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
           "-af", "silencedetect=noise=-35dB:d=2", "-f", "null", "NUL"]
    txt = ""
    for attempt in range(6):
        try:
            r = subprocess.run(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
            txt = r.stderr or ""
            break
        except OSError as e:
            if not is_win1450(e):
                raise
            time.sleep(0.5 * (attempt + 1))
    starts = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", txt)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([\d.]+)", txt)]
    return list(zip(starts, ends))


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


async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    if not ORIGINAL_VIDEO.exists():
        raise FileNotFoundError(f"original source not found: {ORIGINAL_VIDEO}")
    if not MANIFEST.exists():
        raise FileNotFoundError(f"manifest not found: {MANIFEST}")

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    source_cues, source_desc = load_manifest_cues()
    cues, scale_pre = load_cues(vend, source_cues)
    LAST_ID = cues[-1]["id"]
    extra = load_master_sentences()
    print(f"video duration = {vend:.3f}s; usable = {usable:.3f}s; "
          f"cues = {len(cues)}; source = {source_desc}; "
          f"pre-expansion scale = {scale_pre:.4f}", flush=True)

    print("[1/7] TTS — manifest cue texts (clean, no SFX) ...", flush=True)
    failed = await synth_all(cues)

    print("[2/7] HEAVY pedagogical Bengali expansion ...", flush=True)
    expanded = await expand_short_cues(cues, usable, extra)
    expanded_ids = [x["id"] for x in expanded]
    print(f"  expanded {len(expanded)} cues", flush=True)

    print("[3/7] Fill-gate loop: recompute scale from rendered speech, place, measure ...", flush=True)
    rerender_history = []
    attempt = 0
    while True:
        scale, total_natural, expanded_total, naturals = layout(cues, usable, vend)
        LAST_START = float(cues[-1]["start"])
        canvas, placed, overrun, removed, last_cue_end = place_all(cues, vend, expanded_ids)
        fills = [x["fill"] for x in placed]
        median_fill = round(statistics.median(fills), 4) if fills else 0.0
        max_gap = round(max((x["max_internal_gap_s"] for x in placed), default=0.0), 4)
        gate_ok = median_fill >= GATE_MEDIAN_FILL and max_gap <= GATE_MAX_INTERNAL_GAP
        rerender_history.append({
            "attempt": attempt,
            "scale": round(scale, 6),
            "sum_rendered_speech_s": round(total_natural, 3),
            "median_fill": median_fill,
            "max_internal_gap_s": max_gap,
            "gate_ok": gate_ok,
            "cues_below_target_fill": sum(1 for x in placed if x["fill"] < RERENDER_TARGET_FILL),
        })
        print(f"  attempt {attempt}: scale={scale:.4f} median_fill={median_fill} "
              f"max_gap={max_gap}s gate_ok={gate_ok}", flush=True)
        if gate_ok or attempt >= MAX_RERENDER_ATTEMPTS:
            break
        attempt += 1
        fixed = await rerender_low_fill(cues, placed, extra, attempt)
        rerender_history[-1]["auto_rerender_fixed"] = fixed
        if not fixed:
            print("  no fixable low-fill cues left; stopping re-render loop", flush=True)
            break

    print("[4/7] Peak normalise + WAV master + loudnorm -14 LUFS ...", flush=True)
    CHUNK = 1_000_000
    peak_i = 0
    for i in range(0, len(canvas), CHUNK):
        seg = canvas[i:i + CHUNK]
        peak_i = max(peak_i, int(seg.max()), int(-seg.min()))
    peak_i = peak_i or 1
    if peak_i > 32112:
        sf = 32112.0 / peak_i
        for i in range(0, len(canvas), CHUNK):
            seg = canvas[i:i + CHUNK].astype(np.float32)
            seg *= sf
            np.rint(seg, out=seg)
            canvas[i:i + CHUNK] = seg.astype(np.int16)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')

    print("[5/7] Mux with FULL original video (video copy, no source swap) ...", flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    print("[6/7] Post-mux verification: ffprobe + silencedetect ...", flush=True)
    out_dur = duration(OUT_VIDEO)
    runs = silence_runs(OUT_VIDEO)
    lead = [r for r in runs if r[0] <= 0.6]
    tail = [r for r in runs if r[1] >= out_dur - 0.6]
    internal = [r for r in runs if r not in lead and r not in tail]
    long_internal = [r for r in internal if (r[1] - r[0]) > 2.0]
    max_internal_run = round(max((r[1] - r[0] for r in internal), default=0.0), 4)

    report = {
        "experiment": "fill_v2 — Calculus Lesson 02 full-length re-render "
                      "(heavy pedagogical expansion, recompute-scale-from-rendered-speech, fill gate + auto re-render)",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": source_desc,
        "source_video": str(ORIGINAL_VIDEO),
        "source_video_duration_sec": round(vend, 3),
        "duration_note": "589 s is the old 60-cue master-script authored timeline "
                         "(567.9 s cues + 59 x 0.35 s pauses); the actual source video is 1009.8 s.",
        "cue_count": len(placed),
        "manifest_entries": sum(1 for _ in json.loads(MANIFEST.read_text(encoding="utf-8"))["sections"].values() for _ in _.get("cues", [])),
        "manifest_cues_after_alias_dedup": len(source_cues),
        "failed_tts_cues": failed,
        "strategy": "absolute sample offset (start*44100); atempo floor 0.82; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "tempo_floor": MIN_TEMPO,
        "max_tempo": MAX_TEMPO,
        "scale_recomputed_from_rendered_speech": True,
        "final_timeline_scale": round(scale, 6),
        "sum_rendered_speech_s": round(total_natural, 3),
        "usable_video_sec": round(usable, 3),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "inter_cue_pause_ms": INTER_CUE_PAUSE_MS,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max((abs(x["drift_ms"]) for x in placed), default=0.0), 6),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(out_dur - last_cue_end, 3),
        "median_fill": median_fill,
        "max_internal_gap_s": max_gap,
        "fill_gate": {"median_fill_min": GATE_MEDIAN_FILL,
                      "max_internal_gap_max_s": GATE_MAX_INTERNAL_GAP},
        "fill_gate_pass": bool(median_fill >= GATE_MEDIAN_FILL and max_gap <= GATE_MAX_INTERNAL_GAP),
        "rerender_history": rerender_history,
        "auto_rerender_attempts_used": attempt,
        "heavy_expansion": {
            "natural_target_fraction": NATURAL_TARGET_FRACTION,
            "max_appended_sentences": MAX_APPENDED_SENTENCES,
            "expanded_cues": expanded,
        },
        "silencedetect": {
            "noise_db": -35,
            "min_duration_s": 2.0,
            "total_runs": len(runs),
            "lead_in_runs": [[round(a, 3), round(b, 3)] for a, b in lead],
            "tail_runs": [[round(a, 3), round(b, 3)] for a, b in tail],
            "internal_runs": len(internal),
            "internal_runs_gt_2s": len(long_internal),
            "internal_runs_gt_2s_detail": [[round(a, 3), round(b, 3)] for a, b in long_internal],
            "max_internal_run_s": max_internal_run,
            "internal_silence_gate_pass": len(long_internal) == 0,
        },
        "cues": placed,
        "output_video": str(OUT_VIDEO),
        "output_duration_sec": round(out_dur, 3),
        "output_size_bytes": OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0,
        "volumedetect_intro_0_2s_db": volumedetect(OUT_VIDEO, 0, 2),
        "volumedetect_final_2s_db": volumedetect(OUT_VIDEO, max(0.0, out_dur - 2), 2),
    }
    try:
        probe = json.loads(run(f'ffprobe -v error -show_entries stream=index,codec_type,codec_name '
                               f'-of json "{OUT_VIDEO}"'))
        report["output_streams"] = probe.get("streams", [])
    except Exception as e:
        report["output_streams_error"] = str(e)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    overall = (report["fill_gate_pass"] and report["silencedetect"]["internal_silence_gate_pass"]
               and abs(out_dur - vend) < 1.0)
    print("\n===== FINAL METRICS =====", flush=True)
    print(f"output duration        = {out_dur:.3f}s (source {vend:.3f}s)", flush=True)
    print(f"cues                   = {len(placed)} (manifest after alias-dedup)", flush=True)
    print(f"final timeline scale   = {scale:.4f} (recomputed from rendered speech)", flush=True)
    print(f"median_fill            = {median_fill} (gate >= {GATE_MEDIAN_FILL})", flush=True)
    print(f"max_internal_gap_s     = {max_gap} (gate <= {GATE_MAX_INTERNAL_GAP})", flush=True)
    print(f"silence runs >2s       = {report['silencedetect']['total_runs']} total, "
          f"{len(long_internal)} internal (lead={len(lead)}, tail={len(tail)})", flush=True)
    print(f"fill gate pass         = {report['fill_gate_pass']}", flush=True)
    print(f"internal silence gate  = {report['silencedetect']['internal_silence_gate_pass']}", flush=True)
    print(f"OVERALL                = {'PASS' if overall else 'FAIL'}", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
