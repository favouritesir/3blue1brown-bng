"""
EXPERIMENT - Full-length clean absolute-sample Bengali dub
(Lockdown Math, Lesson 08 - "Proof of the Basel problem")

Adapted verbatim from the proven clean_timesync_v2 pipeline:
    lockdown_math/lesson_01/dubbing_pipeline/experiments/clean_timesync_v2/build_lock01_clean.py

Guarantees (identical to the proven pipeline, plus IMPROVED_DUB_FILL_POLICY.md):
   1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
      half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
   2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
   3. IMPROVED FILL: atempo floor 0.82, ceiling 2.2. Pad only, NEVER truncate.
      NO SFX: clean speech only.
   4. STRONG EXPANSION: the manifest has only FOUR h2 cues for the whole film.
      Each section gets a pool of 22 distinct, pedagogically meaningful Bengali
      sentences (Basel history, inverse-square lighthouse physics, Pythagorean
      lighthouse merging, circular chord/arc limit). Cues are expanded until the
      SUMMED rendered speech spans the real, probed video duration with no
      silent pockets. Windows are then RE-DERIVED from measured rendered speech.
   5. Quality gate measured from the rendered waveform: median_fill >= 0.72 and
      max_internal_gap_s <= 1.5, with automatic re-render (extra expansion) if
      the gate fails. Long internal silences are gently compressed in-cue.
   6. Canvas padded to the FULL original video duration so -shortest can never
      trim video frames. Final cue is capped to end inside the video.
   7. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
   8. Lightweight volumedetect (-vn -nostats, log to FILE) on intro and final.
   9. source_metadata_note records the verified 3B1B provenance (yt-dlp,
      YouTube oEmbed, ffprobe). Teacher audio/manifests are NEVER modified.

NOTE ON DURATION: lesson_08.json carries a stale "1:02:18". The verified
official source d-o3eB9sfls actually runs ~1028 s (17:08). The pipeline always
uses ffprobe of the downloaded original as the authoritative canvas length.
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
BASE = EXP.parent.parent                        # .../lockdown_math/lesson_08/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "lockdown_math" / "lesson_08.json"

# Original source: yt-dlp output (verified as 3B1B with ffprobe before use).
ORIGINAL_DIR = WEB / "media_vault" / "lockdown_math" / "lesson_08" / "original_source"
ORIGINAL_VIDEO = ORIGINAL_DIR / "full_original.mp4"

OUT_VIDEO = WEB / "media_vault" / "lockdown_math" / "lesson_08" / "experiments" / "3b1b_lockdown_08_full_dubbed.mp4"

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
VIDEO_ID = "d-o3eB9sfls"
LESSON = "lesson_08"

# Silence margins: keep 0-2 s and the final 2 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Expansion policy constants.
EXPAND_TARGET_FILL = 0.98            # aim for a near-perfectly filled window
TARGET_NATURAL_SCALE = 0.78          # STRONG expansion: ~15-20 added sentences/cue,
                                     # summed natural speech > usable video time,
                                     # final atempo ~1.3x (well under 2.2 ceiling)
MAX_APPENDED_SENTENCES = 120         # pool cycles if a cue needs more
ACTIVE_THRESHOLD = 0.015
MAX_INTERNAL_SILENCE_S = 1.0         # compress pauses longer than this in-cue
CHARS_PER_CHUNK = 1700               # chunk long TTS text for robustness

# Verified provenance (yt-dlp metadata + YouTube oEmbed + ffprobe of original).
SOURCE_METADATA_NOTE = {
    "youtube_id": VIDEO_ID,
    "source_url": "https://www.youtube.com/watch?v=d-o3eB9sfls",
    "oembed_title": "Why is pi here?  And why is it squared?  A geometric answer to the Basel problem",
    "oembed_author_name": "3Blue1Brown",
    "oembed_author_url": "https://www.youtube.com/@3blue1brown",
    "ytdlp_uploader": "3Blue1Brown",
    "ytdlp_channel": "3Blue1Brown",
    "verified_via": [
        "yt-dlp --skip-download metadata (id/title/uploader/channel)",
        "https://www.youtube.com/oEmbed endpoint (title + author_name)",
        "ffprobe of the downloaded original_source/full_original.mp4",
    ],
    "note": "Official 3Blue1Brown (Grant Sanderson) source, confirmed by oEmbed "
            "title and uploader. lesson_08.json duration '1:02:18' is stale; "
            "the real video is ~1028 s and ffprobe of the original is authoritative.",
    "teacher_audio_and_manifests_modified": False,
}


# ---------------------------------------------------------------------------
# Section-aware pedagogical sentences. 22 distinct sentences per section.
# Cycled (never repeated back-to-back inside one append) so every addition
# teaches real mathematics about the Basel problem.
# ---------------------------------------------------------------------------
EXPANSION_POOL = {
    "sec-01-basel-intro": [
        "এক হাজার ছয়শত চল্লিশ সালে ইতালীয় গণিতবিদ পিয়েত্রো মেঙ্গোলি এই প্রশ্নটি প্রথম তুলেছিলেন যে স্বাভাবিক সংখ্যাগুলোর বর্গের ব্যস্তানুপাতিক ধারার অসীম যোগফল কত।",
        "তিনি লক্ষ্য করেছিলেন এক, এক ভাগ চার, এক ভাগ নয়, এক ভাগ ষোল, এইভাবে পদ পর পদ যোগ হতে থাকলে যোগফল ধীরে ধীরে কোথাও স্থির হচ্ছে।",
        "কিন্তু সেই স্থিতিশীল মানটি ঠিক কত, তা নির্ণয় করা তার পক্ষে সম্ভব হয়ে ওঠেনি।",
        "এরপর জ্যাকব বার্নৌলি এবং ইয়োহান বার্নৌলি এই একই সমস্যা নিয়ে বহু বছর কাজ করলেন, কিন্তু সঠিক উত্তরের কাছেও পৌঁছাতে পারলেন না।",
        "তখনকার দিনে অনেকের ধারণা ছিল এই যোগফল হয়তো অসীম, অথচ পদগুলো এত দ্রুত ছোট হচ্ছে যে ধারাটি অবশ্যই কোনো সীমার কাছে আসছে।",
        "আসলে প্রতিটি পদ সংখ্যার বর্গের ব্যস্তানুপাতিক হওয়ায় পদগুলো দ্রুত ছোট হয়, আর প্রথম কয়েকটি পদ যোগ করলেই প্রায় এক দশমিক ছয়চার পাওয়া যায়।",
        "সতেরো শতকের মাঝামাঝি সময়ে এই সমস্যা গণিতবিদদের জন্য এক ধরনের চ্যালেঞ্জ হয়ে দাঁড়িয়েছিল, কারণ কেউই এর নিখুঁত মান বের করতে পারছিলেন না।",
        "অনেক পণ্ডিত চেষ্টা করেছিলেন ভিন্ন ভিন্ন উপায়ে, কিন্তু প্রতিটি চেষ্টাই শেষ হয়েছিল আংশিক ফলাফলে।",
        "এইরকম এক দীর্ঘ ব্যর্থতার পর ১৭৩৫ সালে মাত্র আটাইশ বছর বয়সী লেওনার্ড অয়লার গণিতজগৎকে অবাক করে দিয়ে সমাধান দিলেন।",
        "তিনি দেখালেন যে এই অসীম ধারার যোগফল আর কিছুই নয়, বরং পাই এর বর্গ ভাগ ছয়, অর্থাৎ এক দশমিক ছয়চার নয় দশমিক নয় চার।",
        "এই ফলাফল সবাইকে অবাক করেছিল, কারণ ধারার কোথাও কোনো বৃত্ত ছিল না, তবুও হঠাৎ পাই এসে হাজির হলো।",
        "পাই তো বৃত্তের পরিধি আর ব্যাসের অনুপাত; বর্গসংখ্যার এই যোগফলে তার আবির্ভাব ইঙ্গিত করে যে সমস্যার গভীরে কোনো লুকোনো জ্যামিতি আছে।",
        "অয়লারের এই আবিষ্কার গণিতের ইতিহাসে সবচেয়ে সুন্দর আবিষ্কারগুলোর একটি হিসেবে আজ বিবেচিত হয়।",
        "তিনি প্রথমে কিছুটা অনুমানের সাহায্য নিলেন, পরে সেই অনুমানকে দৃঢ় প্রমাণে রূপ দিতে বেশ কিছু বছর লাগিয়েছিলেন।",
        "আসলে অয়লার সাইন ফাংশনের অসীম গুণফল ব্যবহার করে এই ফলাফলটি পেয়েছিলেন, যা আজ অয়লারের উৎপাদক সূত্র নামে পরিচিত।",
        "আমাদের আজকের যাত্রা হবে সেই রহস্যের জ্যামিতিক ব্যাখ্যা খোঁজা, কোনো জটিল বিশ্লেষণের সাহায্য ছাড়াই।",
        "গ্রান্ট স্যান্ডারসন দেখিয়েছেন যে এই সমস্যাটিকে আলোর উজ্জ্বলতার ভাষায় অনুবাদ করলে এর গাণিতিক রূপ অনেক সহজ হয়ে যায়।",
        "ধরুন আপনি সামনের দিকে তাকিয়ে আছেন আর দূরে দূরে কতগুলো বাতিঘর জ্বলজ্বল করছে, তখন প্রতিটি বাতির আলো আপনার চোখে কমে যাবে তার দূরত্বের বর্গ অনুপাতে।",
        "দূরের বাতি কম উজ্জ্বল দেখালেও তারা সংখ্যায় অনেক বেশি, আর সেই দুটি প্রভাব একসাথে মিলে এই বিখ্যাত ধারাটি তৈরি করে।",
        "এই পর্যবেক্ষণটি আমাদের প্রথম ধাপ, বিমূর্ত সংখ্যার যোগফলকে একটি দৃশ্যমান ভৌত প্রক্রিয়ায় রূপ দেওয়া।",
        "পাইয়ের উপস্থিতি আমাদের সতর্ক করে দেয় যে উত্তরটি কোনো সরল ভগ্নাংশ নয়, বরং বৃত্তীয় জ্যামিতির সাথে জড়িত এক বিশেষ সংখ্যা।",
        "তাই আজ আমরা কেবল উত্তরটি মুখস্থ করব না, বরং দেখব কীভাবে বাতিঘরের আলো ও পিথাগোরাসের ত্রিভুজ আমাদের সেই উত্তরের কাছে নিয়ে যায়।",
    ],
    "sec-02-lighthouse-physics": [
        "আলোর বিপরীত বর্গীয় সূত্র হলো এই জ্যামিতিক প্রমাণের ভিত্তি, যা বলে উৎস থেকে দূরে গেলে আলোর তীব্রতা দূরত্বের বর্গের ব্যস্তানুপাতে কমে যায়।",
        "একটি আদর্শ বিন্দু বাতিঘর থেকে নির্গত আলো চারদিকে সমানভাবে ছড়িয়ে পড়ে, ঠিক যেমন এক ফোঁটা রঙ কাগজে সমানভাবে ছড়ায়।",
        "দূরত্ব যদি দ্বিগুণ করা হয়, তবে আলো যে গোলকীয় পৃষ্ঠে পৌঁছায় তার ক্ষেত্রফল চারগুণ হয়ে যায়।",
        "ক্ষেত্রফল চারগুণ হওয়ায় একই পরিমাণ আলো এখন চারগুণ বড় জায়গায় বিভক্ত, ফলে প্রতি একক জায়গায় আলো থাকে এক ভাগ চার।",
        "তাই দূরত্ব তিনগুণ করলে উজ্জ্বলতা হয় এক ভাগ নয়, আর চারগুণ করলে এক ভাগ ষোল।",
        "এই নিয়মটিকে আমরা এরকম লিখতে পারি, উজ্জ্বলতা সমান এক ভাগ দূরত্বের বর্গ।",
        "এখন ধরুন মূলবিন্দুতে দাঁড়িয়ে আছেন একজন পর্যবেক্ষক আর সরলরেখায় এক, দুই, তিন, চার একক দূরে বাতিঘর রাখা আছে।",
        "প্রথম বাতির আলো পৌঁছাবে এক একক দূরত্বে, তাই তার উজ্জ্বলতা এক; দ্বিতীয়টির দূরত্ব দুই, তাই উজ্জ্বলতা এক ভাগ চার।",
        "তৃতীয় বাতিটি তিন একক দূরে, উজ্জ্বলতা এক ভাগ নয়; চতুর্থটি চার একক দূরে, উজ্জ্বলতা এক ভাগ ষোল।",
        "পর্যবেক্ষকের চোখে এই সবগুলো আলো একসাথে যোগ হয়, কারণ আলোর শক্তি যোগ হয় কিন্তু কমে না।",
        "তাই মোট উজ্জ্বলতা দাঁড়ায় এক, এক ভাগ চার, এক ভাগ নয়, এক ভাগ ষোল, অর্থাৎ ঠিক ব্যাসেল ধারার প্রথম চারটি পদ।",
        "অসীম সংখ্যক বাতি রাখলে এই যোগফল হবে ব্যাসেল ধারার পুরো যোগফল, যার মান আমরা খুঁজছি।",
        "এই রূপান্তরের সুবিধা হলো এখন আমরা বিমূর্ত সংখ্যা নিয়ে নয়, বরং দূরত্ব ও আলো নিয়ে কাজ করছি।",
        "জ্যামিতির কৌশল প্রয়োগ করতে আমাদের এখন শুধু দূরত্বগুলো নিয়ে খেলা করতে হবে, আলোর তীব্রতা নিয়ে নয়।",
        "চিত্রে দেখা যাচ্ছে আলোর উৎস থেকে বলয়ের মতো তরঙ্গ ছড়িয়ে যাচ্ছে, আর বাইরের বলয়ের ক্ষেত্রফল বাড়ার সাথে সাথে আলো কমে যাচ্ছে।",
        "এই বলয়গুলোর ক্ষেত্রফল বৃদ্ধির হারই আমাদের বলে দেয় কেন হঠাৎ বর্গ আসে, সরল দূরত্ব নয়।",
        "অনেক শিক্ষার্থী ভুল করে মনে করে দূরত্ব দ্বিগুণ হলে আলো কমে এক ভাগ দুই, কিন্তু সঠিক উত্তর এক ভাগ চার।",
        "এই ভুলটি এড়াতে মনে রাখতে হবে আলো ছড়ায় পৃষ্ঠের ওপর, আর পৃষ্ঠের ক্ষেত্রফল বর্গের সমানুপাতিক।",
        "বাতিঘরের মডেল আমাদের দেখায় যে একটি অসীম যোগফলকে আমরা কীভাবে একটি দৃশ্যমান ছবিতে রূপ দিতে পারি।",
        "এই ছবিটি মনে রাখলে ব্যাসেল সমস্যার বাকি ধাপগুলো অনেক স্বাভাবিক লাগবে।",
        "পরবর্তীতে আমরা দেখব দুটি বাতিকে কীভাবে একটিমাত্র বাতিতে রূপান্তর করা যায়, যা আমাদের বৃত্তের দিকে নিয়ে যাবে।",
        "মনে রাখবেন, আলো যোগ হয়, কিন্তু দূরত্বের বর্গ আমাদের বলে দেয় কতটুকু আলো পৌঁছায়।",
    ],
    "sec-03-pythagorean-lighthouse": [
        "পিথাগোরাসের উপপাদ্য হলো এই প্রমাণের সবচেয়ে সুন্দর চাবিকাঠি, যা আমাদের দুটি বাতিকে একক বাতিতে রূপান্তর করতে সাহায্য করে।",
        "ধরুন একটি সমকোণী ত্রিভুজ আছে, যার সমকোণ সংলগ্ন দুটি বাহুর প্রান্তে দুটি বাতিঘর বসানো হয়েছে।",
        "বাতি দুটির থেকে পর্যবেক্ষকের দূরত্ব যথাক্রমে এ এবং বি, আর অতিভুজের ওপর লম্বের দৈর্ঘ্য এইচ।",
        "পিথাগোরাসের উপপাদ্য বলে এ বর্গ যোগ বি বর্গ সমান ক বর্গ, যেখানে ক হলো অতিভুজ।",
        "আবার ত্রিভুজের ক্ষেত্রফল লেখা যায় দুইভাবে, অর্ধেক গুণ এ গুণ বি, আর অর্ধেক গুণ ক গুণ এইচ।",
        "এই দুই রূপকে সমান করে পাই এ গুণ বি সমান ক গুণ এইচ।",
        "ক বর্গ আর ক গুণ এইচের এই সম্পর্ক ব্যবহার করে আমরা পাই এক ভাগ এ বর্গ যোগ এক ভাগ বি বর্গ সমান এক ভাগ এইচ বর্গ।",
        "এই সমীকরণটিই হলো বিপরীত পিথাগোরাস সম্পর্ক, যা আমাদের পুরো প্রমাণের কেন্দ্রবিন্দু।",
        "এর ভৌত অর্থ হলো দুটি পরস্পর লম্ব বাতির মিলিত আলো ঠিক একক বাতির আলোর সমান, যা এইচ দূরত্বে অবস্থিত।",
        "চিত্রে দেখা যাচ্ছে সমকোণী ত্রিভুজটি, দুই বাহু বরাবর বাতি দুটি, আর অতিভুজে লম্ব হয়ে নামা একটি রেখা।",
        "সেই লম্ব রেখাটি ঠিক যেন দুই বাতির আলোকে এক জায়গায় মিলিয়ে দেয়।",
        "এই কৌশলের সাহায্যে আমরা যেকোনো দুটি লম্বালম্বি বাতিকে একটি সমতুল্য বাতি দিয়ে বদলে দিতে পারি।",
        "বদলে দেওয়ার পর নতুন বাতিটির দূরত্ব হয় অতিভুজের ওপর লম্বের দৈর্ঘ্য, অর্থাৎ এইচ।",
        "লক্ষ্য করুন, এখানে কোনো নতুন আলো তৈরি হয়নি, শুধু দুটি বাতির আলোকে এক বিন্দুতে হিসাব করা হয়েছে।",
        "এই পদ্ধতিটি বারবার প্রয়োগ করে আমরা জটিল বাতির সারিকে সরল রূপে আনতে পারব।",
        "অনেকের কাছে এই সম্পর্কটি অবাক করা লাগতে পারে, কিন্তু ক্ষেত্রফলের দুটি রূপ থেকে এটি সরাসরি বেরিয়ে আসে।",
        "ভুল এড়াতে মনে রাখবেন ছোট বর্গের বাহু হলো এইচ, অতিভুজ নয়, অতিভুজ শুধু ক্ষেত্রফলের হিসাবে আসে।",
        "এই একই যুক্তি পরে বৃত্তের ওপর প্রয়োগ করলে আমাদের চাপ আর জ্যার দৈর্ঘ্যের সাথে পরিচিত হতে হবে।",
        "বৃত্তের ভিতরে আঁকা বহুভুজের বাহুগুলোকে যখন এইভাবে জোড়া করা হয়, তখন লম্বগুলো জ্যার দিকে এগিয়ে যায়।",
        "পিথাগোরাসের উপপাদ্য আমাদের শুধু ত্রিভুজ নয়, বৃত্তের জ্যামিতিতেও একই ভাষায় কথা বলতে শেখায়।",
        "তাই এই ধাপটি হলো সরলরেখার বাতিঘর থেকে বৃত্তাকার বিন্যাসে যাওয়ার সেতু।",
        "মনে রাখবেন, দুটি বাতি এক বাতিতে রূপান্তরের এই কৌশলই শেষ পর্যন্ত পাইয়ের জন্ম দেবে।",
    ],
    "sec-04-circle-limit": [
        "চূড়ান্ত ধাপে আমরা বৃত্তীয় প্রতিসাম্য ব্যবহার করে ব্যাসেল ধারার সঠিক মান বের করব।",
        "বাতিঘরগুলোকে বৃত্তের পরিধিতে সমান ব্যবধানে সাজানো হয়, তারপর পিথাগোরাসের জোড়া করার কৌশল বারবার প্রয়োগ করা হয়।",
        "এই প্রক্রিয়ায় জ্যার দৈর্ঘ্য আর চাপের দৈর্ঘ্যের অনুপাতটা সামনে চলে আসে।",
        "বৃত্তের ব্যাস যদি এক হয়, তবে কোনো কোণ থিটার জন্য জ্যার দৈর্ঘ্য হয় সাইন থিটা।",
        "আর একই কোণের জন্য চাপের দৈর্ঘ্য হয় ঠিক থিটা।",
        "অতি ক্ষুদ্র কোণে সাইন থিটা আর থিটা প্রায় সমান হয়ে যায়, অর্থাৎ সাইন থিটা ভাগ থিটা কাছে যায় একের।",
        "এই সীমাটিই আমাদের জ্যা আর চাপের মধ্যে সেই সেতু তৈরি করে দেয়, যার মাধ্যমে পাই প্রবেশ করে।",
        "চিত্রে দেখা যাচ্ছে বৃত্তের চারপাশে সমান দূরত্বে সাজানো বাতিঘর আর ক্রমশ ছোট হয়ে আসা জ্যাগুলো।",
        "বহুভুজের বাহু যত ছোট হয়, জ্যাগুলো তত বেশি চাপের রেখার সাথে মিলে যায়।",
        "অসীম সংখ্যক বাহু হলে বহুভুজটি সম্পূর্ণ বৃত্তে পরিণত হয় আর জ্যা হয়ে যায় চাপ।",
        "এই অসীম সীমাতে বিজোড় পদগুলোর যোগফল দাঁড়ায় পাই এর বর্গ ভাগ আট।",
        "কেন আট আসে, কারণ আমরা বৃত্তের অর্ধেক অংশ নিয়ে কাজ করেছি, তাই ভাগ আটের মতো একটা সংখ্যা আসে।",
        "এখন পূর্ণ ধারার সাথে বিজোড় ধারার সম্পর্ক স্থাপন করি।",
        "পূর্ণ ধারার জোড় পদগুলো হলো এক ভাগ চার, এক ভাগ ষোল, এক ভাগ ছয়ত্রিশ, অর্থাৎ মূল ধারার এক ভাগ চার।",
        "কারণ প্রতিটি জোড় পদ এক ভাগ দুই এন এর বর্গ, যা মূল পদের এক ভাগ চার।",
        "তাই বাকি তিন ভাগের চার হলো বিজোড় পদের সমষ্টি।",
        "অর্থাৎ তিন ভাগের চার গুণ এস সমান পাই এর বর্গ ভাগ আট, যেখানে এস হলো আমাদের ব্যাসেল ধারার যোগফল।",
        "দুই পাশকে চার দিয়ে ভাগ করে পাই তিন ভাগের চার গুণ এস সমান পাই এর বর্গ ভাগ আট, সরলে এস সমান পাই এর বর্গ ভাগ ছয়।",
        "এইভাবে শেষ পর্যন্ত জন্ম নেয় এক, এক ভাগ চার, এক ভাগ নয়, এভাবে চলতে থাকা অসীম ধারার যোগফল পাই স্কয়ার বাই ছয়।",
        "এই ফলাফলের সৌন্দর্য হলো এতে কোনো জটিল হিসেব নেই, আছে শুধু বৃত্ত, ত্রিভুজ আর আলোর সরল যোগ।",
        "বৃত্তের চাপের দৈর্ঘ্য আর কোণের পরিমাপ থেকেই পাইয়ের আগমন ঘটে, আর সেই পাইয়ের বর্গ উদ্ভাসিত হয় বাতির আলোর ধারায়।",
        "এই অমর ফলাফলের মাধ্যমেই আজকের পাঠের শেষ কথা, বিমূর্ত সংখ্যার রহস্য জ্যামিতির আলোয় উন্মোচিত হলো।",
    ],
}
DEFAULT_EXPANSIONS = [
    "এই ধারণাটি নিজের ভাষায় একবার বলে দেখলে বিষয়টি আরও পরিচ্ছন্ন হবে।",
    "লক্ষ্য করুন, দূরত্বের এই অনুপাতই আমাদের আসল উত্তরের দিকে নিয়ে যায়।",
    "এখানে যুক্তিটি আবার মনে করিয়ে দিই, কারণ পরের ধাপে এটি বারবার কাজে লাগবে।",
]


# ---------------------------------------------------------------------------
# Utilities (verbatim from the proven pipeline)
# ---------------------------------------------------------------------------
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
    """Read the audio_manifest referenced by lesson_08.json (read-only)."""
    rel = (lesson.get("audio_manifest") or lesson.get("audio_manifest_url") or
           (lesson.get("meta") or {}).get("audio_manifest") or
           (lesson.get("meta") or {}).get("audio_manifest_url"))
    candidates = []
    if rel:
        candidates.append((LESSON_JSON.parent / rel).resolve())
    candidates.append(WEB / "assets" / "audio" / "lockdown_math" / "lesson_08" / "manifest.json")

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
        return derive_from_lesson(lesson), "lesson_08.json:sections"

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
        if valid(raw):
            print(f"  TTS {i+1}/{len(cues)} CACHED (natural={duration(raw):.1f}s)", flush=True)
            continue
        ok = await synth_cue(sanitize(c["bn"]), raw)
        if not ok:
            failed.append(c["id"])
            print(f"  WARNING cue {c['id']} failed after every fallback", flush=True)
        print(f"  TTS {i+1}/{len(cues)} (chars={len(c['bn'])}, natural={duration(raw):.1f}s)", flush=True)
    return failed


def predicted_fill(natural, target):
    """Fill with tempo floor 0.82: min(1, natural/(0.82*target))."""
    if target <= 0 or natural <= 0:
        return 0.0
    return min(1.0, natural / (MIN_TEMPO * target))


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
    """Synthesize ONLY `text` and concat it onto the existing `raw` MP3.
    Avoids the O(n^2) cost of re-synthesizing the whole growing cue."""
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
    Section-aware pedagogical sentences keep every addition meaningful.
    Only NEW sentences are synthesized each round (incremental concat).
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
        # Resume path: already-expanded raw from an interrupted prior run.
        if natural >= per_cue_target and meta.exists():
            cached = json.loads(meta.read_text(encoding="utf-8"))
            print(f"  expand cue {cid} CACHED (natural={natural:.1f}s, "
                  f"{cached.get('sentences_added')} sent)", flush=True)
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
        for rnd in range(6):
            if natural >= per_cue_target or added >= MAX_APPENDED_SENTENCES:
                break
            rate_sec_per_char = natural / max(len(base), 1)
            need_chars = max(250, int((per_cue_target - natural) /
                                      max(rate_sec_per_char, 0.01)))
            append_text, n_sent = pick_append(
                pool, added, need_chars, MAX_APPENDED_SENTENCES - added)
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
                "id": cid,
                "section": c["section"],
                "natural_before": round(before, 3),
                "natural_after": round(natural, 3),
                "sentences_added": added,
                "final_chars": len(base),
                "target_sec": round(per_cue_target, 3),
            }
            meta.write_text(json.dumps(entry, ensure_ascii=False, indent=2),
                            encoding="utf-8")
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
    if gaps.size == 0:
        return 0.0
    return float(gaps.max()) / sr


def compress_long_silences(arr, sr=SR, thr=ACTIVE_THRESHOLD, max_sil=MAX_INTERNAL_SILENCE_S):
    """Gently remove the excess of any in-cue silence longer than max_sil.
    Keeps the leading/trailing portion so phrasing stays natural."""
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
            cut_from = int(s) + limit
            cut_to = int(e)
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
    Windows are proportional to each cue's measured TTS duration so that
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
    """Append more section-aware sentences to a weak cue (quality gate)."""
    cid = cue["id"]
    raw = RAW_DIR / f"raw_{cid:03d}.mp3"
    pool = EXPANSION_POOL.get(cue["section"], DEFAULT_EXPANSIONS)
    text = sanitize(cue["bn"])
    nat = duration(raw)
    rate = nat / max(len(text), 1)
    need_chars = max(300, int(extra_s / max(rate, 0.01)))
    offset = len(text)
    append_text, n = pick_append(pool, offset, need_chars, 80)
    print(f"  extra-expand cue {cid}: +{n} sent (extra_s={extra_s:.1f})", flush=True)
    if await append_audio(append_text, raw, f"q{time.time_ns()}"):
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
        "experiment": "clean_timesync_v2 (lockdown_math_lesson_08 full-length, STRONG expansion, scale recomputed from rendered speech)",
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
            "expand_target_fill": EXPAND_TARGET_FILL,
            "target_natural_scale": TARGET_NATURAL_SCALE,
            "per_cue_target_sec": round(per_cue_target, 3),
            "median_fill": median_fill,
            "median_fill_target": 0.72,
            "median_fill_ok": median_fill >= 0.72,
            "max_internal_gap_s": max_internal_gap,
            "max_internal_gap_target": 1.5,
            "max_internal_gap_ok": max_internal_gap <= 1.5,
            "max_internal_silence_compression_s": MAX_INTERNAL_SILENCE_S,
        },
        "quality_gate": {
            "median_fill_ok": median_fill >= 0.72,
            "max_internal_gap_ok": max_internal_gap <= 1.5,
            "passed": gate_ok,
        },
        "median_fill": median_fill,
        "max_internal_gap_s": max_internal_gap,
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
          f"expanded={len(expanded)} gate_ok={gate_ok}", flush=True)
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
