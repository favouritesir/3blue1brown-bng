"""
EXPERIMENT - Full-length clean absolute-sample Bengali dub
(Number Theory, Lesson 01 - "Why do prime numbers make these spirals?")

Adapted verbatim from the proven quality-gated clean_timesync_v2 pipeline:
    lockdown_math/lesson_08/.../build_lock08_clean.py
which itself comes from essence_of_calculus/lesson_08/.../build_calc08_clean.py.

Guarantees (identical to the proven pipeline):
   1. edge_tts bn-BD-PradeepNeural; robust retries (0-byte purge, 12 attempts,
      half-split + sentence-split fallbacks, WinError 1450 retry).
   2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
   3. atempo fit floor 0.82, ceiling 2.2. PAD only, NEVER truncate. NO SFX.
   4. STRONG expansion: the GOLD audio manifest cue texts (alias-deduped) are the
      dubbing script. Section-aware pedagogical Bengali sentences expand every
      cue until the SUMMED rendered speech spans the probed video duration with
      no silent pockets. Windows are RE-DERIVED from measured rendered speech.
   5. Quality gate measured from the rendered waveform: median_fill >= 0.72 and
      max_internal_gap_s <= 1.5, with automatic re-render (extra expansion) if
      the gate fails. Long in-cue silences are gently compressed.
   6. Canvas padded to FULL original video duration so -shortest cannot trim
      video frames. Final cue capped to end inside the video.
   7. loudnorm -14 LUFS; mux with FULL original video via -c:v copy.
   8. Volumedetect on intro and final; verification.json records all metrics.

Everything is written under NEW experiment folders. Teacher audio / manifests
and other lessons are NEVER modified.
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
BASE = EXP.parent.parent                        # .../number_theory/lesson_01/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "number_theory" / "lesson_01.json"
MANIFEST = WEB / "assets" / "audio" / "number_theory" / "lesson_01" / "manifest.json"

ORIGINAL_DIR = WEB / "media_vault" / "number_theory" / "lesson_01" / "original_source"
ORIGINAL_VIDEO = ORIGINAL_DIR / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "number_theory" / "lesson_01" / "experiments" / "3b1b_number_theory_01_full_dubbed.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
MIN_TEMPO = 0.82
FADE_MS = 12
VIDEO_ID = "EK32jo7i5LQ"
LESSON = "lesson_01"
COURSE = "number_theory"

LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

EXPAND_TARGET_FILL = 0.98
TARGET_NATURAL_SCALE = 0.78
MAX_APPENDED_SENTENCES = 120
ACTIVE_THRESHOLD = 0.015
MAX_INTERNAL_SILENCE_S = 1.0
CHARS_PER_CHUNK = 1700

SOURCE_METADATA_NOTE = {
    "youtube_id": VIDEO_ID,
    "source_url": "https://www.youtube.com/watch?v=EK32jo7i5LQ",
    "oembed_title": "Why do prime numbers make these spirals? | Dirichlet's theorem and pi approximations",
    "oembed_author_name": "3Blue1Brown",
    "oembed_author_url": "https://www.youtube.com/@3blue1brown",
    "ytdlp_uploader": "3Blue1Brown",
    "ytdlp_channel": "3Blue1Brown",
    "verified_via": [
        "yt-dlp --skip-download metadata (id/title/uploader/channel) -> 3Blue1Brown",
        "ffprobe of downloaded original_source/full_original.mp4",
    ],
    "note": "Official 3Blue1Brown (Grant Sanderson) source. yt-dlp metadata "
            "is confirmed by YouTube oEmbed (author_name=3Blue1Brown) and yt-dlp metadata "
            "(uploader=channel=3Blue1Brown). ffprobe of the downloaded original is the "
            "canvas authority.",
    "teacher_audio_and_manifests_modified": False,
}

# Section-aware pedagogical Bengali expansion sentences (one pool per manifest
# section). Fresh sentences are cycled, offset by cue index so different cues in
# the same section receive different wording.
EXPANSION_POOL = {
    "sec-polar-plots": [
        "মেরু নির্দেশক ব্যবস্থায় কোনো বিন্দুকে তার মূলবিন্দু থেকে দূরত্ব আর অনুভূমিক রেখার সাথে কোণ দিয়ে চিহ্নিত করা হয়, যা ঘূর্ণনজনিত সমস্যায় সাধারণ এক্স ওয়াই স্থানাঙ্কের চেয়ে সুবিধাজনক।",
        "কোণকে রেডিয়ানে মাপা হয়, যেখানে এক পূর্ণ চক্কর সমান দুই পাই রেডিয়ান আর আধা চক্কর সমান পাই রেডিয়ান।",
        "একই বিন্দুর একাধিক মেরু নির্দেশক থাকতে পারে, কারণ কোণে দুই পাই যোগ করলে বিন্দুটির অবস্থান একই থাকে।",
        "ঋণাত্মক দূরত্বের অর্থ হলো কোণের দিক পরিবর্তন, অর্থাৎ কোণে পাই যোগ করা, তাই ঋণাত্মক র আর ধনাত্মক র আলাদা বিন্দু দেখায়।",
        "আর্কিমিডিয় স্পাইরাল হলো এমন একটি বক্ররেখা যার প্রতিটি বিন্দুতে মূলবিন্দু থেকে দূরত্ব কোণের সমান, অর্থাৎ র সমান থেটা।",
        "এই স্পাইরালে প্রতি ধাপে কোণ এক রেডিয়ান বাড়ে আর দূরত্ব এক একক বাড়ে, ফলে বিন্দুগুলো ঘুরতে ঘুরতে বাইরের দিকে এগিয়ে যায়।",
        "কেন্দ্রের কাছে বিন্দুগুলো ঘন থাকে আর বাইরের দিকে ক্রমশ ছড়িয়ে পড়ে, কারণ একই কোণবৃদ্ধিতে বাইরে আরও বেশি দূরত্ব অতিক্রম করতে হয়।",
        "স্পাইরালটি প্রাইম সংখ্যার কারণে নয়, বরং পূর্ণসংখ্যার ক্রমের কারণেই তৈরি হয়, যেকোনো ক্রমানুসারে বিন্দু নিলেও একই গঠন পাওয়া যায়।",
        "প্রতি ধাপে এক রেডিয়ান ঘোরে, যা এক ষষ্ঠাংশ ঘুরনিরও কম, তাই কয়েকটি ধাপ পরপর নিলে প্রায় সোজা রশ্নি দেখা যায়।",
        "দূরে সরে তাকালে স্পাইরালের বদলে সরল রশ্নিরা ফুটে ওঠে, কারণ অনেকগুলো বিন্দু প্রায় একই রেখায় পড়ে।",
        "পি পি বিন্দু বলতে আমরা এমন বিন্দু বুঝি যার দূরত্ব আর কোণ দুটোই একই প্রাইম সংখ্যা পি।",
        "প্রথমে সব পূর্ণসংখ্যা নিয়ে অঙ্কন করলে স্পাইরালটি স্পষ্ট হয়, তারপর কেবল প্রাইম সংখ্যা রেখে বাকিগুলো বাদ দিই।",
        "প্রাইম সংখ্যা অপ্রত্যাশিত আচরণের জন্য বিখ্যাত, তাই প্রথমে সবই এলোমেলো মনে হওয়া স্বাভাবিক।",
        "কিন্তু যখন আমরা দূরে সরে ছবিটা বড় করে দেখি, তখন স্পষ্ট গ্যালাক্সির মতো স্পাইরাল বাহু ফুটে ওঠে।",
        "প্রাইম সংখ্যা থেকে কুড়িটি স্পাইরাল আর দুশো আশিটি রশ্নি গণনা করা যায়, আর এই সংখ্যাগুলোর পেছনে রয়েছে গাণিতিক কারণ।",
        "রশ্নিগুলো প্রায় চারটির গুচ্ছে আসে আর মাঝে মাঝে একটি ফাঁক পড়ে, এই ফাঁকগুলোই আমাদের অবশিষ্ট শ্রেণির দিকে নিয়ে যায়।",
        "প্রতিটি রশ্নি আসলে একেকটি গাণিতিক শ্রেণির প্রতীক, অর্থাৎ একই ভাগশেষের সংখ্যাগুলো একই রশ্নিতে পড়ে।",
        "এই পর্যবেক্ষণটি আমাদের বলে দেয় যে গাণিতিক শ্রেণিগুলোই জ্যামিতিক বাহুতে রূপ নিচ্ছে।",
        "স্পাইরাল আর রশ্নির এই দ্বৈত দৃশ্য আমাদের প্রশ্নটিকে দুটি ভাগে ভেঙে দেখতে শেখায়।",
        "আসুন এখন এই রশ্নিগুলোর গঠনের কারণটি অবশিষ্ট শ্রেণির ভাষায় খুঁজে বের করি।",
    ],
    "sec-residue-spirals": [
        "ছয়টি ছোট স্পাইরাল দেখা যায় কারণ ছয় ধাপে মোট ছয় রেডিয়ান ঘোরে, যা দুই পাইয়ের কাছাকাছি, অর্থাৎ প্রায় এক পূর্ণ চক্কর।",
        "ছয়ের গুণিতকগুলো এক বাহু তৈরি করে, ছয়ের গুণিতকের এক বেশি সংখ্যারা দ্বিতীয় বাহু, দুই বেশি সংখ্যারা তৃতীয় বাহু, ইত্যাদি।",
        "প্রতিবার ছয় করে এগোলে কোণ খুব কম বদলায়, তাই মনে হয় যেন একটিমাত্র বাঁকা রেখা।",
        "এই ছয়টি বাহুর প্রতিটি আসলে মডুলো ছয়ের একটিমাত্র অবশিষ্ট শ্রেণিকে প্রতিনিধিত্ব করে।",
        "প্রাইম সংখ্যার দিকে নজর দিলে এই ছয়টি বাহুর মধ্যে কেবল দুটি বেঁচে থাকে।",
        "প্রাইম সংখ্যা ছয়ের গুণিতক হতে পারে না, কারণ তখন ছয় দিয়ে বিভাজ্য হওয়ায় তা যৌগিক হবে।",
        "ছয় কে প্লাস দুই আর ছয় কে প্লাস চার আকারের সংখ্যা সবই জোড়, তাই দুই ছাড়া কোনো প্রাইম এদের মধ্যে পড়তে পারে না।",
        "ছয় কে প্লাস তিন আকারের সব সংখ্যা তিন দিয়ে বিভাজ্য, তাই তিন ছাড়া আর কোনো প্রাইম এই শ্রেণিতে নেই।",
        "কেবল ছয় কে প্লাস এক আর ছয় কে প্লাস পাঁচে প্রাইম সংখ্যা পড়তে পারে, ব্যতিক্রম দুই আর তিন।",
        "অবশিষ্ট শ্রেণি হলো একই ভাগশেষের সংখ্যার গুচ্ছ, যেমন কুড়ি কে ছয় দিয়ে ভাগ করলে ভাগশেষ দুই পাই, তাই কুড়ি হলো ছয় কে প্লাস দুই শ্রেণির।",
        "মডুলো ছয় মানে ছয় দিয়ে ভাগের পর ভাগশেষের ভিত্তিতে সংখ্যাকে শ্রেণিবদ্ধ করা।",
        "এই শব্দটি আসলে ছয়ের গুণিতকের দুই বেশি সংখ্যা ছাড়া কিছু নয়, তবে নাম থাকলে কথা বলা সুবিধাজনক হয়।",
        "একই যুক্তি বড় স্কেলে চলে যায়, কারণ চুরাল্লিশ ধাপ অনেক বেশি নিখুঁতভাবে এক পূর্ণ চক্করের কাছে পৌঁছায়।",
        "চুরাল্লিশ ভাগের দুই পাই প্রায় সাত, অর্থাৎ চুরাল্লিশ ভাগ সাত হলো দুই পাইয়ের কাছাকাছি, যা আমাদের পরিচিত বাইশ ভাগ সাতের মতোই।",
        "চুরাল্লিশ ধাপে কোণ প্রায় সাত পূর্ণ ঘুরনি হয়, তাই প্রতিটি বাহু আগেরটির চেয়ে সামান্য কোণে ঘুরে মৃদু স্পাইরাল তৈরি করে।",
        "মডুলো চুরাল্লিশের চুরাল্লিশটি অবশিষ্ট শ্রেণির মধ্যে কেবল কুড়িটি বাহু প্রাইম সংখ্যার জন্য উন্মুক্ত।",
        "বাকিগুলো জোড় বা এগারো দিয়ে বিভাজ্য হওয়ায় বাদ পড়েছে, আর প্রতিটি বাহু প্রায় সোজা কারণ চুরাল্লিশ ধাপে প্রায় সাত চক্কর হয়।",
        "ছয় ও চুরাল্লিশের এই সাদৃশ্য আমাদের দেখায় যে একই নীতি বিভিন্ন স্কেলে বারবার কাজ করে।",
        "অবশিষ্ট শ্রেণির ভাষা আমাদের রশ্নির জ্যামিতিক গঠনকে সঠিকভাবে ব্যাখ্যা করতে সাহায্য করে।",
        "এখন প্রশ্ন ওঠে কেন ঠিক কুড়িটি শ্রেণি বেঁচে থাকে, এর উত্তর সহ-মৌলিকতা আর টোশিয়েন্ট ফাংশনের মাধ্যমে পাওয়া যাবে।",
    ],
    "sec-totient-710": [
        "যে বাহুগুলোতে প্রাইম থাকতে পারে সেগুলো হলো চুরাল্লিশের সাথে যাদের কোনো সাধারণ উৎপাদক নেই, একে বলা হয় কোপ্রাইম বা সহ-মৌলিক।",
        "এক থেকে চুরাল্লিশের মধ্যে চুরাল্লিশের সাথে কোপ্রাইম সংখ্যা আছে কুড়িটি, যা গণিতের ভাষায় ফাই চুরাল্লিশ সমান কুড়ি।",
        "গ্রিক ফাই অক্ষরটি অয়লারের টোশিয়েন্ট ফাংশন, যা কোনো এনের সাথে কোপ্রাইম এক থেকে এনের সংখ্যা গণনা করে।",
        "ফাই দশ সমান চার, কারণ এক, তিন, সাত আর নয় এই চারটি সংখ্যা দশের সাথে সহ-মৌলিক।",
        "ফাই ছয় সমান দুই, কারণ কেবল এক আর পাঁচ ছয়ের সাথে সহ-মৌলিক, আর এ থেকেই ছয়ের ক্ষেত্রে অনুপাত এক ভাগ দুই আসে।",
        "সাতশো দশ রেডিয়ান অসাধারণভাবে পূর্ণ ঘুরনির কাছে, কারণ সাতশো দশ ভাগ একশো তেরো হলো দুই পাইয়ের এক অত্যন্ত ভালো আসন্ন মান।",
        "এই আসন্ন মানটি তিনশো পঞ্চাশ ভাগ একশো তেরোর সমতুল্য, যা ইতিহাসে পাইয়ের জন্য ব্যবহৃত একটি বিখ্যাত অনুপাত।",
        "ফলে সাতশো দশ ধাপে এগোলে পরের বিন্দুর কোণ আগেরটির প্রায় হুবহু মতো হয়, আর অনেক দূর পর্যন্ত বিন্দুগুলো সোজা রশ্নিতে পড়ে।",
        "কেবল অনেক পরে গিয়ে সামান্য বাঁক দেখা যায়, আর এই বাঁকের দূরত্ব আসন্ন মানের গুণমান প্রমাণ করে।",
        "সাতশো দশ সমান দুই গুণ পাঁচ গুণ একশো একাত্তর, তাই এর উৎপাদকগুলো রশ্নির ফাঁকগুলো নির্ধারণ করে।",
        "জোড় শ্রেণি বাদ, তারপর পাঁচ দিয়ে বিভাজ্য শ্রেণি বাদ, আর শেষে একশো একাত্তর দিয়ে বিভাজ্য চারটি শ্রেণি বাদ পড়ে।",
        "ছবিতে প্রতিটি ফাঁকের পেছনে একটি উৎপাদক আছে, তাই রশ্নির গুচ্ছ আর ফাঁকের গঠন সম্পূর্ণরূপে ব্যাখ্যা করা যায়।",
        "ফাই সাতশো দশ সমান ফাই দুই গুণ পাঁচ গুণ একশো একাত্তর, যা সমান এক গুণ চার গুণ সাতশো, অর্থাৎ দুশো আশি।",
        "দুশো আশিটি শ্রেণিকে আমরা শুধু বিভাজ্যতা দিয়ে বাতিল করতে পারি না, বাকি শ্রেণিগুলোতে প্রাইম থাকতে পারে।",
        "ছবিতে দেখা যায় প্রাইমগুলো এই দুশো আশিটি শ্রেণির মধ্যে বেশ সমানভাবে ছড়িয়ে আছে।",
        "এই সমান বণ্টনই ডিরিখলের উপপাদ্যের মূল বিষয়, যা আমাদের পরবর্তী পরিচ্ছেদে আলোচনা করব।",
        "টোশিয়েন্ট ফাংশন আমাদের দেখায় কতগুলো শ্রেণি প্রাইমের জন্য উন্মুক্ত থাকে।",
        "সহ-মৌলিকতার এই ধারণা সংখ্যাতত্ত্বের অসংখ্য জায়গায় কাজে লাগে, এমনকি আধুনিক গোপনীয়তা প্রযুক্তিতেও।",
        "আসন্ন মানের গুণমান আর সহ-মৌলিকতার গণনা একসাথে মিলে দুশো আশি আর চারের গুচ্ছের গল্পটি সম্পূর্ণ করে।",
        "এখন আমরা দেখব এই সমান বণ্টন কীভাবে একটি গভীর উপপাদ্যে রূপ নেয়।",
    ],
    "sec-dirichlet": [
        "মডুলো দশের ক্ষেত্রে দশমিক পদ্ধতিতে সংখ্যাকে শেষ অঙ্ক অনুযায়ী ভাগ করা যায়।",
        "দুই ছাড়া কোনো প্রাইমের শেষ অঙ্ক জোড় হতে পারে না, কারণ তখন সংখ্যাটি দুই দিয়ে বিভাজ্য হবে।",
        "পাঁচ ছাড়া শেষ অঙ্ক পাঁচও হতে পারে না, কারণ তখন সংখ্যাটি পাঁচ দিয়ে বিভাজ্য হবে।",
        "তাই পাঁচের চেয়ে বড় প্রাইমের শেষ অঙ্ক অবশ্যই এক, তিন, সাত বা নয়।",
        "হিস্টোগ্রামে প্রাইম সংখ্যা বাড়ার সাথে সাথে এই চারটি শেষ অঙ্কের অনুপাত প্রায় পঁচিশ শতাংশ করে দাঁড়াচ্ছে।",
        "অর্থাৎ প্রতিটি অনুমোদিত শ্রেণিতে প্রাইম প্রায় সমানভাবে বণ্টিত, কোনো শ্রেণি বেশি দখল করতে পারছে না।",
        "নীল আর হলুদ দণ্ডগুলোর দিকে তাকালে দেখা যায় তারা প্রায় সমান উচ্চতায় স্থির হয়েছে।",
        "দেখতে সহজ হলেও এই সমান বণ্টন প্রমাণ করা অত্যন্ত কঠিন, আর এর জন্য প্রয়োজন হয় গভীর বিশ্লেষণের।",
        "গণিতবিদরা এই পর্যবেক্ষণকে লেখেন এক্স পর্যন্ত সব প্রাইমের মধ্যে এক মডুলো দশ শ্রেণির অনুপাত হিসেবে।",
        "এই অনুপাত এক্স অসীমের দিকে যাওয়ার সাথে সাথে এক ভাগ চারের কাছে পৌঁছায়।",
        "সাধারণভাবে এন আর আর এর জন্য, যেখানে আর আর এন কোপ্রাইম, অনুপাত হয় ফাই এন ভাগের এক।",
        "এখানে পাই অফ এক্স চিহ্নটি পরম পাই নয়, এটি প্রাইম কাউন্টিং ফাংশন, অর্থাৎ নির্দিষ্ট সীমার নিচে প্রাইম সংখ্যা গণনা করে।",
        "প্রাইম কাউন্টিং ফাংশনের এই ব্যবহার আমাদের শতাব্দী পুরনো ধারণাকে আধুনিক ভাষায় প্রকাশ করতে সাহায্য করে।",
        "ডিরিখলে আটশো তিরিশ সালে সামান্য ভিন্ন ঘনত্ব ব্যবহার করে এই সমস্যায় অগ্রগতি করেছিলেন।",
        "তিনি প্রাইম পি এর এক ভাগ পি টু দ্য পাওয়ার এস যোগ নিয়ে কাজ করেছিলেন, যেখানে এস শূন্যের বেশি আর একের দিকে ধাবিত হয়।",
        "এই রূপটি গাণিতিকভাবে নিয়ন্ত্রণ করা সহজ, কারণ এটি কম্পলেক্স বিশ্লেষণের শক্তিশালী কৌশল ব্যবহার করতে দেয়।",
        "তার আসল অর্জন ছিল প্রমাণ করা যে আর ও এন কোপ্রাইম হলে ওই শ্রেণিতে অসংখ্য প্রাইম আছে।",
        "এই উপপাদ্য আমাদের দুই আর তিন ছাড়া সব প্রাইমের ছয় কে প্লাস এক বা পাঁচ আকারের হওয়ার পর্যবেক্ষণকেও ব্যাখ্যা করে।",
        "ডিরিখলের ধারা আর কম্পলেক্স বিশ্লেষণের এই সংযোগ আধুনিক সংখ্যাতত্ত্বের ভিত্তি স্থাপন করেছিল।",
        "আসুন এখন দেখি এই গভীর ফলাফল আমাদের ছোট প্রশ্নটিকে কীভাবে মর্যাদা দেয়।",
    ],
    "sec-conclusion": [
        "মূল ডেটার এই ভিজ্যুয়ালাইজেশন খেলাটির কোনো বিশেষ গুরুত্ব নেই, বরং এটি এক ধরনের কৌতূহলী অন্বেষণ।",
        "পি পি বিন্দু অঙ্কন করা স্বাভাবিক কিছু নয়, তবে অস্বাভাবিক প্রশ্নই অনেক সময় গভীর পথ খুঁজে দেয়।",
        "প্রাথমিক রহস্যের বেশিরভাগই এসেছে পূর্ণসংখ্যার রেডিয়ান নিয়ে কাজ করার কারণে, বিশেষত দুই পাইয়ের আসন্ন মান থেকে।",
        "কিন্তু এই রকম খেলা করার ফলে যদি ডিরিখলের উপপাদ্যের মতো গভীর কিছুর পথে পৌঁছানো যায়, তবে তার মূল্য অস্বীকার করা যায় না।",
        "এই প্রশ্নটিকে থ্রিডিতে নিয়ে যাওয়া যায়, যেখানে গোলীয় নির্দেশক ব্যবস্থা ব্যবহার করা হয়।",
        "গোলীয় ব্যবস্থায় প্রতিটি প্রাইম পির সাথে তিনটি স্থানাঙ্ক যুক্ত হয়, যা স্পাইরালকে গোলকের ওপর স্থানান্তর করে।",
        "কয়েক হাজার প্রাইম নিয়ে অঙ্কন করলে টুডি গ্যালাক্সি আবার দেখা যায়, কিন্তু এখন বাহুগুলো ভেতরে বাইরে বোনা এক অসীম স্পাইরালের মতো।",
        "একশো এগারো আর তিরিশ শ্রেণি আবার বাদ পড়ে, কারণ এগুলোর সাথে ভাগনীয় উৎপাদক রয়েছে।",
        "ছোট প্রশ্নগুলোকে ভেঙে সহজ অংশে ভাগ করেই বড় প্রশ্নের উত্তর খোঁজা হয়, এটি গণিত অন্বেষণের এক সুন্দর শিক্ষা।",
        "থ্রিডি প্যাটার্নটি আগের দুই প্রশ্ন থেকে সম্পূর্ণ আলাদা একটি নতুন প্রশ্ন তুলে ধরে।",
        "শেষে উলাম স্পাইরালের কথা, যেখানে সংখ্যাগুলোকে কেন্দ্র থেকে বাইরের দিকে গ্রিডে স্পাইরাল আকারে লেখা হয়।",
        "প্রাইমগুলোর ওপর দুটি তির্যক রেখা দেখা যায়, অর্থাৎ নির্দিষ্ট দ্বিঘাত ফাংশনে প্রাইম বেশি পড়ে।",
        "আমাদের স্পাইরালের সাথে এটি মিলে না, কারণ আমাদেরটি রৈখিক ফাংশন থেকে আসে।",
        "এর সাথে সম্পর্কিত আছে চেবোতারেভ ঘনত্ব উপপাদ্য, যা বহুপদীর মানে প্রাইমের বণ্টন নিয়ে কথা বলে।",
        "অর্থাৎ প্রাইম সংখ্যার ভেতরে অনেক প্যাটার্ন আছে আর গণিতবিদরা সেগুলো অনেকটাই বুঝেছেন।",
        "অদ্ভুত হওয়ার খ্যাতি সত্ত্বেও প্রাইম সংখ্যা কোনো এলোমেলো বিষয় নয়, বরং গভীর নিয়মের অধীন।",
        "আজকের যাত্রায় আমরা স্পাইরাল থেকে শুরু করে অবশিষ্ট শ্রেণি, টোশিয়েন্ট আর ডিরিখল পর্যন্ত এসেছি।",
        "এই ধাপগুলোর প্রতিটি আমাদের দেখিয়েছে কীভাবে একটি সরল পর্যবেক্ষণ গাণিতিক গভীরতায় রূপ নেয়।",
        "আসুন আমরা এই শিক্ষাসমূহ মনে রেখে পরবর্তী পাঠের জন্য প্রস্তুত হই।",
        "পরের অধ্যায়ে আমরা পাইথাগোরিয়ান ট্রিপলের রহস্য অন্বেষণ করব, যেখানে জ্যামিতি আর বীজগণিতের সুন্দর মিলন দেখা যাবে।",
    ],
}
DEFAULT_EXPANSIONS = [
    "এই ধারণাটি নিজের ভাষায় একবার বলে দেখলে বিষয়টি আরও পরিচ্ছন্ন হবে।",
    "লক্ষ্য করুন, এই অনুপাতটিই আমাদের আসল উত্তরের দিকে নিয়ে যায়।",
    "এখানে যুক্তিটি আবার মনে করিয়ে দিই, কারণ পরের ধাপে এটি বারবার কাজে লাগবে।",
]


# ------------------------- utilities ---------------------------------------
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


def split_chunks(text, limit=CHARS_PER_CHUNK):
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


def load_source_cues():
    """Read the GOLD audio manifest (read-only). Cue texts are the dubbing
    script. Sections are alias-deduped by section_id."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
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
            out.append({"text": text,
                        "dur_ms": float(c.get("duration_ms", 0)),
                        "section": sid})
    if not out:
        raise SystemExit("NO CUES FOUND IN GOLD MANIFEST")
    return out, f"audio_manifest:{MANIFEST.name} (gold cue texts, alias-deduped)"


def load_cues(vend, source_cues):
    authored_total = sum(c["dur_ms"] for c in source_cues) + INTER_CUE_PAUSE_MS * (len(source_cues) - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    scale = usable / (authored_total / 1000.0) if authored_total > 0 else 1.0
    cues, cursor_ms = [], 0.0
    for i, c in enumerate(source_cues):
        start = LEAD_IN_SEC + (cursor_ms / 1000.0) * scale
        dur = (c["dur_ms"] / 1000.0) * scale
        cues.append({"id": i + 1, "start": round(start, 3),
                     "end": round(start + dur, 3), "duration": round(dur, 3),
                     "bn": c["text"], "section": c["section"]})
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
    picked, total, i = [], 0, start_idx
    while total < need_chars and len(picked) < max_n:
        s = pool[i % len(pool)]
        picked.append(s)
        total += len(s) + 1
        i += 1
    return " ".join(picked), (i - start_idx)


def cue_offset(cues, cue):
    """Distinct pool start per cue inside a section (reduces repetition)."""
    return sum(1 for x in cues if x["section"] == cue["section"] and x["id"] < cue["id"])


async def append_audio(text, raw, tag):
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
            expanded.append({"id": cid, "section": c["section"], "cached": True,
                             "natural_before": cached.get("natural_before"),
                             "natural_after": round(natural, 3),
                             "sentences_added": cached.get("sentences_added"),
                             "final_chars": cached.get("final_chars"),
                             "target_sec": round(per_cue_target, 3)})
            continue
        pool = EXPANSION_POOL.get(c["section"], DEFAULT_EXPANSIONS)
        base = sanitize(c["bn"])
        added = 0
        off = cue_offset(cues, c) * 2
        for rnd in range(6):
            if natural >= per_cue_target or added >= MAX_APPENDED_SENTENCES:
                break
            rate_sec_per_char = natural / max(len(base), 1)
            need_chars = max(250, int((per_cue_target - natural) / max(rate_sec_per_char, 0.01)))
            append_text, n_sent = pick_append(pool, added + off, need_chars,
                                              MAX_APPENDED_SENTENCES - added)
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
            entry = {"id": cid, "section": c["section"],
                     "natural_before": round(before, 3),
                     "natural_after": round(natural, 3),
                     "sentences_added": added, "final_chars": len(base),
                     "target_sec": round(per_cue_target, 3)}
            meta.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
            expanded.append(entry)
    return expanded, per_cue_target


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
    return float(gaps.max()) / sr if gaps.size else 0.0


def compress_long_silences(arr, sr=SR, thr=ACTIVE_THRESHOLD, max_sil=MAX_INTERNAL_SILENCE_S):
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


LAST_START = 0.0
VIDEO_END = 0.0
LAST_ID = None


def make_cue(raw, target, out, cid):
    natural = duration(raw)
    if natural <= 0:
        natural = target
    if cid == LAST_ID:
        target = min(target, VIDEO_END - LAST_START - 0.10)
    tempo = max(MIN_TEMPO, min(MAX_TEMPO, natural / target))
    tmp = out.with_suffix(".fit.wav")
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)
    arr = compress_long_silences(arr)
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


def recompute_layout_from_naturals(cues, vend):
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
    cid = cue["id"]
    raw = RAW_DIR / f"raw_{cid:03d}.mp3"
    pool = EXPANSION_POOL.get(cue["section"], DEFAULT_EXPANSIONS)
    text = sanitize(cue["bn"])
    nat = duration(raw)
    rate = nat / max(len(text), 1)
    need_chars = max(300, int(extra_s / max(rate, 0.01)))
    append_text, n = pick_append(pool, len(text) + cue_offset([cue], cue) * 2, need_chars, 80)
    print(f"  extra-expand cue {cid}: +{n} sent (extra_s={extra_s:.1f})", flush=True)
    if await append_audio(append_text, raw, f"q{time.time_ns()}"):
        cue["bn"] = sanitize(text + " " + append_text)
        expanded_log.append({"id": cid, "section": cue["section"], "round": "quality_gate",
                             "sentences_added": n, "final_chars": len(cue["bn"]),
                             "natural_before": round(nat, 3),
                             "natural_after": round(duration(raw), 3)})
        return duration(raw)
    return nat


def render_canvas(cues, vend, expanded_ids):
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
        placed.append({"id": cid, "section": c["section"],
                       "expected_start_ms": expected_ms, "actual_start_ms": actual_ms,
                       "drift_ms": round(actual_ms - expected_ms, 6),
                       "tempo": round(tempo, 4), "natural_sec": round(natural, 3),
                       "target_sec": round(target, 3), "fit_samples": fit_samples,
                       "window_samples": window_samples, "fill": round(fill, 4),
                       "max_internal_gap_s": round(gap_s, 4),
                       "placed_samples": placed_len, "expanded": cid in expanded_ids})
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

    print("[2/7] STRONG expansion driven by real video duration ...", flush=True)
    expanded, per_cue_target = await expand_short_cues(cues, vend)
    print(f"  expanded {len(expanded)} cues", flush=True)

    print("[3/7] Recompute timeline scale from RENDERED natural speech ...", flush=True)
    scale, naturals = recompute_layout_from_naturals(cues, vend)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"  natural_total={sum(naturals):.1f}s -> scale={scale:.4f} "
          f"(was {initial_scale:.4f} from manifest)", flush=True)

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
        "experiment": "clean_timesync_v2 (number_theory_lesson_01 full-length, STRONG expansion, scale recomputed from rendered speech)",
        "lesson": LESSON, "course": COURSE, "video_id": VIDEO_ID,
        "script_source": source_desc,
        "cue_count": len(placed), "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": "absolute sample offset (start*44100); atempo fit floor 0.82; pad only; no truncation",
        "sfx": "NONE - clean speech only", "voice": VOICE,
        "min_tempo": MIN_TEMPO, "max_tempo": MAX_TEMPO,
        "overrun_cues": overrun, "max_measured_drift_ms": round(max_drift, 6),
        "timeline_scale": round(scale, 6),
        "timeline_scale_initial_manifest": round(initial_scale, 6),
        "scale_recomputed_from_rendered_speech": True,
        "rendered_natural_speech_total_sec": round(sum(naturals), 3),
        "render_rounds": render_round,
        "lead_in_sec": LEAD_IN_SEC, "tail_margin_sec": TAIL_MARGIN_SEC,
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "fill_policy": {"expand_target_fill": EXPAND_TARGET_FILL,
                        "target_natural_scale": TARGET_NATURAL_SCALE,
                        "per_cue_target_sec": round(per_cue_target, 3),
                        "median_fill": median_fill, "median_fill_target": 0.72,
                        "median_fill_ok": median_fill >= 0.72,
                        "max_internal_gap_s": max_internal_gap,
                        "max_internal_gap_target": 1.5,
                        "max_internal_gap_ok": max_internal_gap <= 1.5,
                        "max_internal_silence_compression_s": MAX_INTERNAL_SILENCE_S},
        "quality_gate": {"median_fill_ok": median_fill >= 0.72,
                         "max_internal_gap_ok": max_internal_gap <= 1.5,
                         "passed": gate_ok},
        "median_fill": median_fill, "max_internal_gap_s": max_internal_gap,
        "expanded_cues": expanded, "source_metadata_note": SOURCE_METADATA_NOTE,
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
    print(f"scale={scale:.4f} rounds={render_round}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap={max_internal_gap}s "
          f"expanded={len(expanded)} gate_ok={gate_ok}", flush=True)
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
