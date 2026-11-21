"""
EXPERIMENT - Full-length clean absolute-sample Bengali dub
(Number Theory, Lesson 02 - "All possible pythagorean triples, visualized")

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
BASE = EXP.parent.parent                        # .../number_theory/lesson_02/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "number_theory" / "lesson_02.json"
MANIFEST = WEB / "assets" / "audio" / "number_theory" / "lesson_02" / "manifest.json"

ORIGINAL_DIR = WEB / "media_vault" / "number_theory" / "lesson_02" / "original_source"
ORIGINAL_VIDEO = ORIGINAL_DIR / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "number_theory" / "lesson_02" / "experiments" / "3b1b_number_theory_02_full_dubbed.mp4"

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
VIDEO_ID = "QJYmyhnaaek"
LESSON = "lesson_02"
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
    "source_url": "https://www.youtube.com/watch?v=QJYmyhnaaek",
    "oembed_title": "All possible pythagorean triples, visualized",
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
            "canvas authority. Real duration ~893 s (ffprobe).",
    "teacher_audio_and_manifests_modified": False,
}


# Section-aware pedagogical Bengali expansion sentences (one pool per manifest
# section). Fresh sentences are cycled, offset by cue index so different cues in
# the same section receive different wording.
EXPANSION_POOL = {
    "sec-familiar-triangles": [
        "স্কুলে আমরা যে তিন চার পাঁচ ত্রিভুজটি শিখি, তা হলো সমকোণী ত্রিভুজের সবচেয়ে পরিচিত উদাহরণ, যার তিন বাহু তিন, চার আর পাঁচ একক।",
        "পাঁচ বারো তেরো আর আট পনেরো সতেরো হলো আরও দুটি পরিচিত পাইথাগোরিয়ান ট্রিপল, যেগুলোর বাহুও পূর্ণসংখ্যা।",
        "পাইথাগোরিয়ান সূত্র বলে যে সমকোণী ত্রিভুজের দুটি ছোট বাহুর বর্গের যোগফল অতিভুজের বর্গের সমান।",
        "এই সূত্রটিকে লেখা যায় এ স্কয়ার প্লাস বি স্কয়ার সমান সি স্কয়ার, যেখানে সি হলো অতিভুজ।",
        "প্রশ্ন হলো এই সমীকরণের সমস্ত পূর্ণসংখ্যা সমাধান কীভাবে পাওয়া যায়, অর্থাৎ কোন কোন তিনটি সংখ্যা এই সম্পর্কটি মেনে চলে।",
        "কোনো ট্রিপলকে দুই, তিন বা যেকোনো পূর্ণসংখ্যা দিয়ে গুণ করলে নতুন ট্রিপল পাওয়া যায়, যেমন তিন চার পাঁচ থেকে ছয় আট দশ।",
        "তিন চার পাঁচ থেকে নয় বারো পনেরোও পাওয়া যায় তিন দিয়ে গুণ করে, কিন্তু এগুলো আসল নতুন নয়।",
        "গুণ করে পাওয়া ট্রিপলগুলো আসলে একই আকারের স্কেল মাত্র বদলেছে, তাই এগুলোকে বলা হয় অপ্রাথমিক ট্রিপল।",
        "আমরা আসলে আদিম ট্রিপল খোঁজছি, যেগুলো আর কোনো পূর্ণসংখ্যা দিয়ে ভাগ করা যায় না।",
        "একটি ট্রিপল আদিম তখনই যখন তার তিনটি বাহুর কোনো সাধারণ উৎপাদক থাকে না।",
        "তিন চার পাঁচ একটি আদিম ট্রিপল, কারণ তিন, চার আর পাঁচের কোনো সাধারণ উৎপাদক নেই।",
        "ছয় আট দশ আদিম নয়, কারণ তিনটিই দুই দিয়ে বিভাজ্য, তাই এটি তিন চার পাঁচেরই স্কেলকৃত রূপ।",
        "অসীম সংখ্যক আদিম ট্রিপল আছে, আর সবগুলোকে একটি সুন্দর সূত্র দিয়ে বর্ণনা করা যায়।",
        "এই সূত্রটি আবিষ্কার করেছিলেন ইউক্লিড, যা দুটি পূর্ণসংখ্যা এম আর এন থেকে ট্রিপল তৈরি করে।",
        "পাইথাগোরাসের নামে পরিচিত এই উপপাদ্য আসলে তার আগেও বাবিলোনীয় আর ভারতীয় গণিতবিদরা জানতেন।",
        "জ্যামিতিকভাবে এই সূত্রটি বলে তিন বাহুর ওপর আঁকা বর্গগুলোর ক্ষেত্রফলের একটি সুন্দর সম্পর্ক।",
        "দুটি ছোট বর্গের ক্ষেত্রফল যোগ করলে বড় বর্গের ক্ষেত্রফলের সমান হয়, এটিই পাইথাগোরাসের উপপাদ্যের জ্যামিতিক রূপ।",
        "আসুন এখন দেখি কীভাবে এই সরল সমীকরণটি আমাদেরকে একক বৃত্তের পরিমেয় বিন্দুর দিকে নিয়ে যায়।",
    ],
    "sec-unit-circle": [
        "সমীকরণকে সরল করতে আমরা সি দিয়ে ভাগ করি, ফলে পাওয়া যায় এ ভাগ সি স্কয়ার প্লাস বি ভাগ সি স্কয়ার সমান এক।",
        "এর অর্থ হলো আমাদের কাজ হলো একক বৃত্তের ওপর এমন সব বিন্দু খোঁজা যাদের স্থানাঙ্ক পরিমেয় সংখ্যা।",
        "একক বৃত্তের সমীকরণ হলো এক্স স্কয়ার প্লাস ওয়াই স্কয়ার সমান এক, যার ব্যাসার্ধ এক আর কেন্দ্র মূলবিন্দুতে।",
        "জ্যামিতির এই প্রশ্নটি বীজগণিতের প্রশ্নে রূপ নেয় যখন আমরা পরিমেয় স্থানাঙ্কের কথা বলি।",
        "মূলবিন্দুর বাঁয়ের বিন্দু থেকে একটি রেখা বৃত্তকে কাটলে ছেদবিন্দুটি পরিমেয় স্থানাঙ্ক পায় যখন রেখার ঢাল পরিমেয় হয়।",
        "রেখার ঢাল টি এইভাবে বেছে নেওয়া হয় কারণ বাঁয়ের বিন্দুটি বৃত্তের ওপর আছে আর ঢাল যুক্তিসহ পরিমেয়।",
        "বৃত্তের ওপরের প্রতিটি বিন্দু এইভাবে একটি নতুন ট্রিপল জন্ম দেয়, কারণ স্থানাঙ্কগুলোই হলো এ ভাগ সি আর বি ভাগ সি।",
        "রেখার সমীকরণ ওয়াই সমান টি গুণ এক্স প্লাস এক কে বৃত্তের সমীকরণে বসিয়ে সমাধান করা যায়।",
        "সমাধানের ফলে পাই এক্স সমান এক বিয়োগ টি স্কয়ার ভাগের এক প্লাস টি স্কয়ার।",
        "আর ওয়াই সমান দুই টি ভাগের এক প্লাস টি স্কয়ার, যা দেখে বোঝা যায় দুটোই পরিমেয় সংখ্যা।",
        "এখানে টি একটি পরিমেয় ঢাল, তাই এক্স ও ওয়াইও পরিমেয় হয়, আর এটি আমাদের মূল কাঙ্ক্ষিত ফলাফল।",
        "পরে এম আর এন দিয়ে টি কে প্রকাশ করে আমরা পূর্ণসংখ্যার সূত্র পাই, যা ইউক্লিডের সূত্র নামে পরিচিত।",
        "ইউক্লিডের সূত্রানুযায়ী এ সমান এম স্কয়ার বিয়োগ এন স্কয়ার, বি সমান দুই এম এন, আর সি সমান এম স্কয়ার প্লাস এন স্কয়ার।",
        "এই সূত্রটি যেকোনো এম আর এনের জন্য কাজ করে, কিন্তু সব ক্ষেত্রেই আদিম ট্রিপল পাওয়া যায় না।",
        "আদিম হওয়ার শর্ত হলো এম বড় এন থেকে, এম আর এনের গসিডি এক, আর এম ও এন এক জোড় এক বিজোড়।",
        "গসিডি এক মানে এম আর এনের কোনো সাধারণ উৎপাদক নেই, আর বিপরীত জোড়-বিজোড়তা নিশ্চিত করে ট্রিপলটি আর ভাগ করা যাবে না।",
        "এই শর্তগুলো ছাড়া একই ট্রিপল বারবার আসবে, তাই শর্তগুলো মেনে চলা অত্যন্ত গুরুত্বপূর্ণ।",
        "আসুন দেখি এই একই গল্প জটিল সংখ্যার ভাষায় কীভাবে আরও সুন্দর হয়।",
    ],
    "sec-complex-numbers": [
        "একই সমীকরণকে জটিল সংখ্যার ভাষায় লেখা যায় এ স্কয়ার প্লাস বি স্কয়ার সমান এ প্লাস বি আই গুণ এ বিয়োগ বি আই।",
        "এখানে এ প্লাস বি আই আর এ বিয়োগ বি আই পরস্পরের কনজুগেট, অর্থাৎ কাল্পনিক অংশের চিহ্ন উল্টো।",
        "দুই কনজুগেটের গুণফল সবসময় একটি বাস্তব পূর্ণবর্গ হয়, যা আমাদের সি স্কয়ারের সমান।",
        "এই পদ্ধতিটি বীজগণিতকে গাউসিয়ান পূর্ণসংখ্যার রিংয়ে নিয়ে যায়, যেখানে সংখ্যাগুলোর রূপ এ প্লাস বি আই।",
        "গাউসিয়ান পূর্ণসংখ্যা হলো এমন সব জটিল সংখ্যা যার বাস্তব আর কাল্পনিক অংশ দুটোই পূর্ণসংখ্যা।",
        "জটিল তলে একটি বিন্দু এ প্লাস বি আই দেখানো হয়, সাথে তার অনুভূমিক উপাদান এ আর উল্লম্ব উপাদান বি।",
        "বিন্দুটির মূলবিন্দু থেকে দূরত্বের বর্গই হলো এ স্কয়ার প্লাস বি স্কয়ার, অর্থাৎ সি স্কয়ার।",
        "এই দূরত্বের বর্গকে বলা হয় জটিল সংখ্যার নর্ম, যা ট্রিপলের তৃতীয় বাহু নির্ধারণ করে।",
        "গাউসিয়ান পূর্ণসংখ্যার রিংয়ে অনন্য ফ্যাক্টরাইজেশন প্রযোজ্য, ঠিক যেমন সাধারণ পূর্ণসংখ্যায় প্রতিটি সংখ্যা প্রাইমের গুণফলে ভেঙে যায়।",
        "পাঁচ কে ভেঙে দেখা যায় পাঁচ সমান দুই প্লাস আই গুণ দুই বিয়োগ আই, অর্থাৎ দুটি গাউসিয়ান গুণনীয়ক।",
        "এই ভাঙা আর তার কনজুগেটের ভাঙা মিলে একটি বর্গ তৈরি করে, যা থেকে ট্রিপলের উৎপত্তি।",
        "কিন্তু সব প্রাইম গাউসিয়ান পূর্ণসংখ্যায় ভেঙে যায় না, যেমন তিন বা সাত।",
        "যে প্রাইম চার কে প্লাস তিন আকারের, যেমন তিন, সাত, একশো একাত্তর, সেগুলো গাউসিয়ান পূর্ণসংখ্যায় ভেঙে যায় না।",
        "এর কারণ হলো সি স্কয়ার একটি পূর্ণবর্গ, তাই তার ফ্যাক্টরাইজেশনে প্রতিটি গাউসিয়ান প্রাইমের ঘাত জোড় হতে হবে।",
        "চার কে প্লাস তিন আকারের প্রাইম গাউসিয়ান পূর্ণসংখ্যায় ভেঙে যায় না, ফলে সি স্কয়ারে তার ঘাত জোড় হতে পারে না।",
        "তাই এই প্রাইমগুলো কোনো আদিম ট্রিপলের অতিভুজ হতে পারে না, যা একটি সুন্দর বাধা প্রমাণ করে।",
        "এম প্লাস এন আইয়ের বর্গ সমান এম স্কয়ার বিয়োগ এন স্কয়ার প্লাস দুই এম এন আই, যা সরাসরি ইউক্লিডের সূত্র দেয়।",
        "জটিল সংখ্যার এই ভাষা আমাদের দেখায় কীভাবে বীজগণিত আর জ্যামিতি একই গল্প বলে।",
    ],
    "sec-all-triples": [
        "এখন সব টুকরো মিলছে, কারণ যেকোনো আদিম ট্রিপলের এ প্লাস বি আই অবশ্যই কোনো গাউসিয়ান পূর্ণসংখ্যার বর্গের সমান।",
        "একক গুণক ছাড়া এই বর্গ সম্পর্কটি সব আদিম ট্রিপলের ক্ষেত্রে কাজ করে।",
        "কারণ সি স্কয়ারের ফ্যাক্টরাইজেশনে প্রতিটি প্রাইমের ঘাত জোড় হওয়ায় ভেতরের সংখ্যাটিও বর্গ হতে বাধ্য।",
        "অনন্য ফ্যাক্টরাইজেশনের গুণটি এখানে কাজে লাগে, যা আমাদের এই সিদ্ধান্তে পৌঁছাতে সাহায্য করে।",
        "এই জোড়া নির্মাণ থেকে ট্রিপলের এক সুন্দর বৃক্ষ তৈরি হয়, যার মূলে আছে তিন চার পাঁচ।",
        "তিন চার পাঁচ থেকে শাখা হিসেবে বের হয় পাঁচ বারো তেরো, আট পনেরো সতেরো, সাত চব্বিশ পঁচিশ, কুড়ি একুশ ঊনত্রিশ ইত্যাদি।",
        "প্রতিটি শাখা আগের একটি গাউসিয়ান সংখ্যাকে আবার বর্গ করে পাওয়া যায়, তাই বৃক্ষটি অসীম পর্যন্ত প্রসারিত হয়।",
        "এই বৃক্ষের প্রতিটি বিন্দু একটি আদিম ট্রিপল, আর কোনো ট্রিপলই বারবার আসে না।",
        "চিত্রটিতে আমরা দেখি বর্গগুলোর ক্ষেত্রফল শুধু সংখ্যা নয়, বরং জটিল সংখ্যার নর্মের গুণফল।",
        "বাঁয়ের বর্গ এ স্কয়ার, ওপরের বর্গ বি স্কয়ার আর ডানের বর্গ সি স্কয়ার, তিনটি মিলে পাইথাগোরিয়ান সমীকরণ গড়ে তোলে।",
        "প্রতিটি বর্গই একটি গাউসিয়ান সংখ্যার বর্গের প্রতীক, তাই ছবিটি বীজগণিত আর জ্যামিতির সেতু।",
        "এই মানচিত্র আমাদের দেখায় যে অসীম সংখ্যক ট্রিপল একটি সুসংগঠিত কাঠামোতে বিন্যস্ত।",
        "বৃক্ষের প্রতিটি স্তর আগের চেয়ে বড় সংখ্যা নিয়ে আসে, কিন্তু মূল নীতি একই থাকে।",
        "গাউসিয়ান পূর্ণসংখ্যার বর্গ নেওয়ার এই কৌশল প্রতিবার নতুন এম আর এন জোড়া তৈরি করে।",
        "এই কারণেই আমরা বলতে পারি যে সব আদিম ট্রিপল এই একই উৎস থেকে আসে।",
        "আসুন এক কথায় বলি, গাউসিয়ান বর্গ আর অনন্য ফ্যাক্টরাইজেশন মিলে পুরো প্রশ্নের উত্তর দেয়।",
        "এই ফলাফলের সৌন্দর্য হলো এটি কোনো হিসাবের চেয়ে বেশি এক ধরনের কাঠামোগত উপলব্ধি।",
        "এখন আমরা দেখব এই পুরো যাত্রাটি কীভাবে একটি সুন্দর উপসংহারে পৌঁছায়।",
    ],
    "sec-conclusion": [
        "আমরা শুরু করেছিলাম তিনটি সংখ্যার এক সরল সমীকরণ দিয়ে, এ স্কয়ার প্লাস বি স্কয়ার সমান সি স্কয়ার।",
        "শেষ করছি জটিল সংখ্যার অনন্য ফ্যাক্টরাইজেশনে, যা অনেক গভীর একটি ধারণা।",
        "একক বৃত্তের পরিমেয় বিন্দু, জটিল তলের ল্যাটিস আর বর্গের জ্যামিতি, এসব মিলে একই গল্প বলে।",
        "এই পদ্ধতি শক্তিশালী কারণ এটি কেবল বের করে না, বোঝায়ও।",
        "কেন চার কে প্লাস তিন প্রাইম আদিম ট্রিপলে আসতে পারে না, তার উত্তর মিলে যায়।",
        "কেন আলাদা এম এন জোড়া আলাদা ট্রিপল দেয়, তাও ব্যাখ্যা করা যায়।",
        "কেন প্রতিটি আদিম ট্রিপল ঠিক একবার আসে, সবকিছুর উত্তর মিলে যায় একক ফ্যাক্টরাইজেশনের জ্যামিতি থেকে।",
        "বীজগণিত আর জ্যামিতির এই মিলন গণিতের সবচেয়ে সুন্দর দিকগুলোর একটি।",
        "একটি সরল প্রশ্ন থেকে শুরু করে আমরা সংখ্যাতত্ত্বের গভীরে পৌঁছেছি।",
        "পাইথাগোরিয়ান ট্রিপলের এই গল্প আমাদের দেখায় যে সঠিক প্রশ্নই আসল আবিষ্কারের চাবিকাঠি।",
        "আজকের পাঠে আমরা দেখেছি কীভাবে একক বৃত্ত, ঢাল আর জটিল সংখ্যা একসাথে কাজ করে।",
        "এই কৌশলগুলো মনে রাখলে ভবিষ্যতে অনেক গাণিতিক সমস্যা সহজ হয়ে যাবে।",
        "আসুন এই শিক্ষাসমূহ নিয়ে পরবর্তী পাঠে অগ্রসর হই, যেখানে পাই লুকোনো থাকবে প্রাইমের নিয়মিততায়।",
        "পরের অধ্যায়ে আমরা লাইবনিজের ধারা আর প্রাইমের গুণফলের মিলন দেখব।",
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
        "experiment": "clean_timesync_v2 (number_theory_lesson_02 full-length, STRONG expansion, scale recomputed from rendered speech)",
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
