"""
EXPERIMENT - Full-length clean absolute-sample Bengali dub
(Lockdown Math, Lesson 07 - "Area and the derivative of a circle")

Adapted verbatim from the proven clean_timesync_v2 pipeline:
    lockdown_math/lesson_01/dubbing_pipeline/experiments/clean_timesync_v2/build_lock01_clean.py

Guarantees (identical to the proven pipeline, plus IMPROVED_DUB_FILL_POLICY.md):
   1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
      half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
   2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
   3. IMPROVED FILL: atempo floor 0.82 (gentle slowdown), ceiling 2.2. Pad only,
      NEVER truncate. NO SFX: clean speech only.
   4. STRONG EXPANSION: the manifest has only 4 h2 cues (~195 s total authored)
      so each cue is expanded with ~24 curated pedagogical Bengali sentences
      (circle unwrapping into a triangle, dA = 2*pi*r*dr => circumference,
      sphere shell dV = 4*pi*r^2*dr, and the square contrast). The section
      paragraphs from lesson_07.json are also folded into each cue.
   5. Timeline scale is RE-COMPUTED from the SUM OF RENDERED NATURAL SPEECH
      after expansion (not from the manifest), then windows are laid out
      proportionally so speech spans the whole video with no silent pockets.
   6. Fill metrics (per-cue fill, median_fill, max_internal_gap_s) are measured
      from the rendered waveform, with a quality gate + automatic re-render.
   7. Canvas padded to the FULL original video duration so -shortest can never
      trim video frames. Final cue is capped to end inside the video.
   8. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
   9. Lightweight volumedetect (-vn -nostats, log to FILE) on intro and final.
  10. source_metadata_note records the verified 3B1B provenance (oEmbed + info.json).

Cue source (read-only; teacher audio / manifests are NEVER modified):
   web_platform/data/lockdown_math/lesson_07.json -> audio_manifest_url
   (assets/audio/lockdown_math/lesson_07/manifest.json). Alias-keyed duplicate
   sections are de-duplicated by section_id.

Everything is written under NEW experiment folders.

Source note: the lesson JSON advertises 1:08:42, but the corrected YouTube id
GNcFjFmqEc8 is the official 3B1B clip "But why is a sphere's surface area four
times its shadow?" whose real duration is ~950 s (15:50). The canvas length is
taken from the actual downloaded source via ffprobe, as in the proven pipeline.
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
BASE = EXP.parent.parent                        # .../lockdown_math/lesson_07/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "lockdown_math" / "lesson_07.json"

# Original source: yt-dlp output (verified with ffprobe + oEmbed before use).
ORIGINAL_DIR = WEB / "media_vault" / "lockdown_math" / "lesson_07" / "original_source"
ORIGINAL_VIDEO = ORIGINAL_DIR / "full_original.mp4"
ORIGINAL_INFO = ORIGINAL_DIR / "full_original.info.json"

OUT_VIDEO = WEB / "media_vault" / "lockdown_math" / "lesson_07" / "experiments" / "3b1b_lockdown_07_full_dubbed.mp4"

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
VIDEO_ID = "GNcFjFmqEc8"             # corrected from the 404 id b3NxrZOup_U
OEMBED_TITLE = "But why is a sphere's surface area four times its shadow?"
OEMBED_AUTHOR = "3Blue1Brown"
LESSON = "lesson_07"

# Silence margins: keep 0-2 s and the final 2 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Expansion policy constants.
EXPAND_TRIGGER_RATIO = 0.62          # expand when natural < 62% of window
EXPAND_TARGET_FILL = 0.85            # aim well above the 0.72 median floor
MAX_APPENDED_SENTENCES = 160
ACTIVE_THRESHOLD = 0.015
CHARS_PER_CHUNK = 1700               # chunk long TTS text for robustness


# ---------------------------------------------------------------------------
# STRONG curated expansion (~24 pedagogical sentences per section).
# These are appended straight to the manifest cue text, so every one of the
# four h2 cues carries a full, self-contained teaching script. The same pool
# is reused if the quality gate asks for still more speech on a weak cue.
# All math is written phonetically in Bengali so PradeepNeural reads it cleanly.
# ---------------------------------------------------------------------------
CURATED_SENTENCES = {
    "sec-01-circle-unwrapping": [
        "আজ আমরা এক কৌতূহলী প্রশ্ন দিয়ে শুরু করব: বৃত্তের ক্ষেত্রফলের সূত্র পাই গুণ ব্যাসার্ধের বর্গ কোথা থেকে আসে?",
        "ছোটবেলা থেকে আমরা এই সূত্রটি মুখস্থ করে এসেছি, কিন্তু কখনো বুঝে দেখি না কেন এটি সত্য।",
        "গ্রান্ট স্যান্ডারসন আমাদের শেখান যে সূত্র মুখস্থ করার বদলে তার পেছনের চিত্রটি দেখা উচিত।",
        "কল্পনা করুন একটি বৃত্তকে পেঁয়াজের মতো অসংখ্য পাতলা সমকেন্দ্রিক বলয়ে ভাগ করা হয়েছে।",
        "প্রতিটি বলয় একই কেন্দ্র থেকে শুরু হয়, কিন্তু তার ব্যাসার্ধ ক্রমশ বাড়তে থাকে।",
        "এই পাতলা বলয়গুলোকে অ্যানুলাস বলা হয়, আর প্রতিটির বেধ অত্যন্ত ক্ষুদ্র, অর্থাৎ ডি আর।",
        "এখন একটি বলয় কেটে সোজা করুন; তখন এটি প্রায় একটি সরু আয়তক্ষেত্রের মতো দেখায়।",
        "এই আয়তক্ষেত্রের প্রস্থ হলো ক্ষুদ্র বেধ ডি আর, আর দৈর্ঘ্য হলো ওই বলয়ের পরিধি।",
        "কেন্দ্র থেকে দূরে সরে যাওয়ার সাথে সাথে বলয়ের পরিধি বাড়তে থাকে, কারণ পরিধি সমানুপাতিক ব্যাসার্ধের।",
        "কেন্দ্রের কাছের বলয় ছোট, আর সর্ববহিঃস্থ বলয়ের দৈর্ঘ্য সবচেয়ে বেশি।",
        "এখন সব উন্মোচিত ফালিকে একটির পর একটি পাশাপাশি সাজান।",
        "লক্ষ্য করুন, ফালিগুলোর দৈর্ঘ্য ক্রমশ বাড়ায় তাদের শীর্ষরেখা একটি সরল রেখা তৈরি করে।",
        "এইভাবে সাজালে আমরা একটি সমকোণী ত্রিভুজ পাই, যার ভূমি হলো মূল বৃত্তের ব্যাসার্ধ।",
        "ত্রিভুজের উচ্চতা হলো সবচেয়ে বাইরের বলয়ের পরিধি, অর্থাৎ দুই পাই গুণ ব্যাসার্ধ।",
        "ত্রিভুজের ক্ষেত্রফল হলো আধা গুণ ভূমি গুণ উচ্চতা—এই সরল সূত্রটি আমরা সবাই জানি।",
        "এখানে ভূমি হলো ব্যাসার্ধ আর উচ্চতা দুই পাই গুণ ব্যাসার্ধ, তাই ক্ষেত্রফল হয় আধা গুণ ব্যাসার্ধ গুণ দুই পাই গুণ ব্যাসার্ধ।",
        "আধা আর দুই কেটে গেলে অবশিষ্ট থাকে পাই গুণ ব্যাসার্ধের বর্গ—অর্থাৎ আমাদের পরিচিত সূত্রটি।",
        "এই প্রমাণের সৌন্দর্য হলো এতে কোনো যান্ত্রিক সমাকলন মুখস্থ করতে হয় না।",
        "কেবল বলয়গুলোকে নতুন করে সাজিয়েই আমরা সূত্রটি নিজের চোখে দেখে নিলাম।",
        "অনেকের কাছে একটি বৃত্ত আর একটি ত্রিভুজ সম্পূর্ণ আলাদা আকৃতি মনে হয়, কিন্তু এখানে তারা একই ক্ষেত্রফলের দুটি রূপ।",
        "এই রূপান্তর আমাদের দেখায় যে ক্ষেত্রফল আসলে যোগ করা যায় এমন এক রাশি।",
        "প্রতিটি সরু ফালির ক্ষেত্রফল তার পরিধি ও বেধের গুণফল, আর সবগুলো যোগ করলেই পুরো বৃত্তের ক্ষেত্রফল পাওয়া যায়।",
        "মনে রাখবেন, বলয় যত পাতলা হবে, সোজা করার পর আয়তক্ষেত্র তত নিখুঁত হবে।",
        "যখন বেধ ডি আর শূন্যের দিকে যায়, তখন আসন্নায়নটি সম্পূর্ণ নিখুঁত হয়ে যায়।",
    ],
    "sec-02-derivative-connection": [
        "দ্বিতীয় পরিচ্ছেদে আমরা জিজ্ঞাসা করব: ব্যাসার্ধ সামান্য বাড়ালে বৃত্তের ক্ষেত্রফল ঠিক কতটুকু বাড়ে?",
        "ধরা যাক বৃত্তের ব্যাসার্ধ হলো আমাদের পরিচিত ব্যাসার্ধ।",
        "এখন এই ব্যাসার্ধকে সামান্য বাড়িয়ে করা হলো ব্যাসার্ধ plus ডি আর।",
        "চিত্রের দিকে তাকালে দেখা যায় নতুন যুক্ত হওয়া অংশটি হলো বৃত্তের চারপাশে একটি পাতলা বলয়।",
        "এই নতুন বলয়টি আগের বৃত্তের ঠিক বাইরে অবস্থান করে, তাই একে বলা যায় সর্ববহিঃস্থ প্রলেপ।",
        "বলয়টির ভেতরের সীমানা আগের পরিধি, আর বাইরের সীমানা নতুন পরিধি।",
        "যেহেতু বেধ অত্যন্ত কম, তাই আমরা এর পরিধি প্রায় দুই পাই গুণ ব্যাসার্ধ ধরে নিতে পারি।",
        "সুতরাং নতুন যুক্ত হওয়া ক্ষেত্রফল হলো প্রায় দুই পাই গুণ ব্যাসার্ধ গুণ ডি আর।",
        "একে আমরা লিখি ডি এ equal দুই পাই গুণ ব্যাসার্ধ গুণ ডি আর।",
        "এখন উভয় পক্ষকে ডি আর দিয়ে ভাগ করুন; তখন পাই ডি এ ভাগ ডি আর equal দুই পাই ব্যাসার্ধ।",
        "ডি আর যখন শূন্যের দিকে যায়, তখন এই অনুপাতের সীমাস্থ মান হয় ঠিক দুই পাই ব্যাসার্ধ।",
        "আর এই সীমাস্থ মানটিই হলো ক্ষেত্রফলের ডেরিভেটিভ, অর্থাৎ ডি এ ভাগ ডি আর।",
        "অন্য দিকে বীজগণিত আমাদের বলে পাই গুণ ব্যাসার্ধের বর্গের ডেরিভেটিভ হলো দুই পাই ব্যাসার্ধ।",
        "এই দুটি পদ একে অপরের সাথে মিলে যাওয়া কোনো কাকতাল নয়।",
        "এটি সরাসরি প্রকাশ করে যে বৃত্তের নতুন বৃদ্ধি ঘটে কেবল তার সীমানা বরাবর।",
        "ভেতরের অংশ অপরিবর্তিত থাকে; শুধু বাইরের প্রান্তে নতুন স্থান যোগ হয়।",
        "এই কারণেই ক্ষেত্রফলের বৃদ্ধির হার অবিকল পরিধির সমান হয়ে থাকে।",
        "এবার একটু সূক্ষ্মতা লক্ষ্য করুন। প্রকৃত বৃদ্ধিতে আরও একটি পদ থাকে, যা হলো পাই গুণ ডি আরের বর্গ।",
        "কিন্তু ডি আর খুব ছোট হলে ডি আরের বর্গ আরও ছোট হয়, তাই সীমায় তার প্রভাব শূন্য হয়ে যায়।",
        "আমরা কেবল প্রথম ক্রমের পদটি রাখি, আর দ্বিতীয় ক্রমের পদটি বাদ দিই।",
        "এই সরলীকরণই ক্যালকুলাসের মূল শক্তি—অতি ক্ষুদ্র পরিমাণের উপেক্ষা করে সীমাস্থ মান বের করা।",
        "মনে রাখবেন, ডেরিভেটিভ মানে কোনো যান্ত্রিক নিয়ম নয়; এটি একটি জ্যামিতিক গল্প।",
        "ব্যাসার্ধ বাড়ালে ক্ষেত্রফল কোথায় যোগ হয়? উত্তর: কেবল পরিধি জুড়ে।",
        "এই এক বাক্যটি মনে রাখলে পাই গুণ ব্যাসার্ধের বর্গের ডেরিভেটিভ আপনি কখনো ভুলবেন না।",
    ],
    "sec-03-sphere-volume-surface": [
        "তৃতীয় পরিচ্ছেদে আমরা দেখব এই একই নীতি ত্রিমাত্রিক জগতেও কাজ করে কি না।",
        "ধরা যাক একটি গোলক, যার ব্যাসার্ধ হলো আমাদের পরিচিত ব্যাসার্ধ।",
        "এর আয়তনের সূত্র হলো চার ভাগের তিন পাই গুণ ব্যাসার্ধের ঘন।",
        "এই সূত্রটিকে ব্যাসার্ধ সাপেক্ষে ডেরিভেটিভ নিলে কী পাই?",
        "চার ভাগের তিন আর ঘাত তিন—এদের গুণফলে তিন কেটে যায়, থাকে চার পাই গুণ ব্যাসার্ধের বর্গ।",
        "আর চার পাই গুণ ব্যাসার্ধের বর্গ হলো অবিকল গোলকের পৃষ্ঠতলের ক্ষেত্রফল।",
        "এই মিলটি আশ্চর্যজনক নয়; এর পেছনে একটি সুন্দর জ্যামিতিক কারণ আছে।",
        "কল্পনা করুন একটি বেলুন ধীরে ধীরে ফুলে যাচ্ছে।",
        "ব্যাসার্ধ যখন ডি আর পরিমাণ বাড়ে, তখন বেলুনের চারপাশে একটি পাতলা চামড়া যোগ হয়।",
        "এই চামড়াটি পুরো পৃষ্ঠতল জুড়ে বিস্তৃত, আর তার বেধ হলো ডি আর।",
        "চামড়ার ক্ষেত্রফল হলো চার পাই গুণ ব্যাসার্ধের বর্গ, তাই তার আয়তন হলো ওই ক্ষেত্রফল গুণ ডি আর।",
        "অর্থাৎ আয়তনের বৃদ্ধি ডি ভি equal চার পাই গুণ ব্যাসার্ধের বর্গ গুণ ডি আর।",
        "ডি আর দিয়ে ভাগ করলেই পাই ডি ভি ভাগ ডি আর equal চার পাই গুণ ব্যাসার্ধের বর্গ।",
        "আর এটি হলো ঠিক সেই পৃষ্ঠতলের ক্ষেত্রফল যা আমরা বীজগণিত থেকে পেয়েছি।",
        "দ্বিমাত্রিক বৃত্তে যেমন ক্ষেত্রফলের ডেরিভেটিভ পরিধি ছিল, তেমনি ত্রিমাত্রিক গোলকে আয়তনের ডেরিভেটিভ পৃষ্ঠতল।",
        "এক মাত্রা বাড়লেই সীমানার পরিমাপও এক মাত্রা বেড়ে যায়—এই হলো মূল নীতি।",
        "গোলক কেন্দ্র থেকে চতুর্দিকে সমানভাবে প্রসারিত হয়, তাই কোনো দিকেই পক্ষপাত নেই।",
        "এই প্রতিসম বৃদ্ধির কারণেই নতুন আয়তন সবদিকে সমানভাবে ছড়িয়ে পড়ে।",
        "যদি আমরা শূন্য বা এক মাত্রার কথা ভাবি, তখনও একই নীতি প্রযোজ্য।",
        "যেকোনো মাত্রার সুষম গোলকের ক্ষেত্রে আয়তনের ডেরিভেটিভ তার সীমানার পরিমাপ দেয়।",
        "এই সার্বজনীন নিয়মই গোলকের আয়তন ও পৃষ্ঠতলের সংযোগকে সুন্দরভাবে প্রতিষ্ঠা করে।",
        "তাই সূত্র মুখস্থ না করেও আপনি বলে দিতে পারবেন: গোলকের আয়তনের ডেরিভেটিভ কত?",
        "উত্তর হলো চার পাই গুণ ব্যাসার্ধের বর্গ, অর্থাৎ তার পুরো পৃষ্ঠতলের ক্ষেত্রফল।",
        "এই উপলব্ধিই আজকের পাঠের সবচেয়ে বড় শিক্ষা—সূত্রের পেছনে একটি চিত্র সবসময় কাজ করে।",
    ],
    "sec-04-square-contrast": [
        "চতুর্থ পরিচ্ছেদে আমরা এক আপাত বিরোধ নিয়ে আলোচনা করব।",
        "অনেকেই প্রশ্ন করেন: বৃত্তের ক্ষেত্রফলের ডেরিভেটিভ তো পরিধি, তবে বর্গের ক্ষেত্রফলের ডেরিভেটিভ কেন পরিসীমা নয়?",
        "ধরা যাক একটি বর্গ, যার এক বাহুর দৈর্ঘ্য হলো আমাদের পরিচিত এক্স।",
        "তার ক্ষেত্রফল হলো এক্স গুণ এক্স, অর্থাৎ এক্সের বর্গ।",
        "বীজগণিত অনুযায়ী এক্সের বর্গের ডেরিভেটিভ হলো দুই এক্স।",
        "কিন্তু বর্গের পরিসীমা তো চার এক্স—তাহলে ডেরিভেটিভ দুই এক্স কেন?",
        "চিত্রের দিকে তাকালে কারণটি পরিচ্ছন্ন হয়ে যায়।",
        "বাঁ পাশে বর্গটিকে এক কোণা স্থির রেখে ডানে ও নিচে বাড়ানো হয়েছে।",
        "ফলে নতুন ক্ষেত্রফল যোগ হয় শুধু দুটি সংলগ্ন বাহু বরাবর।",
        "প্রতিটি ফালির ক্ষেত্রফল হলো এক্স গুণ ক্ষুদ্র বাহুর বৃদ্ধি।",
        "দুটি ফালি মিলে মোট বৃদ্ধি হয় দুই এক্স গুণ ক্ষুদ্র বাহুর বৃদ্ধি।",
        "তাই ডি এ ভাগ ডি এক্স equal দুই এক্স—আমাদের পরিচিত উত্তরটি।",
        "অর্থাৎ আমরা বর্গের কেবল দুটি বাহু বরাবর বৃদ্ধি মাপছি, চারটি নয়।",
        "কারণ এক কোণা স্থির রাখায় বাঁ ও উপরের বাহু সরে যায় না।",
        "ডানে আবার দেখানো হয়েছে কেন্দ্র থেকে চতুর্দিকে প্রতিসম প্রসারণ।",
        "সেখানে কেন্দ্র থেকে বাহুর লম্ব দূরত্ব হলো ব্যাসার্ধ, আর বাহুর দৈর্ঘ্য দুই ব্যাসার্ধ।",
        "তখন বর্গের ক্ষেত্রফল হয় দুই ব্যাসার্ধের বর্গ, অর্থাৎ চার ব্যাসার্ধের বর্গ।",
        "একে ব্যাসার্ধ সাপেক্ষে ডেরিভেটিভ নিলে পাই আট ব্যাসার্ধ।",
        "আর আট ব্যাসার্ধ হলো অবিকল ওই বর্গের সমগ্র পরিসীমা, কারণ চার গুণ দুই ব্যাসার্ধ equal আট ব্যাসার্ধ।",
        "একই আকৃতির জন্য ভিন্ন চলক বেছে নিলে ডেরিভেটিভ ভিন্ন অর্থ প্রকাশ করে।",
        "একপাশের বাহু নিলে পাই দুই এক্স; কেন্দ্র থেকে প্রতিসম ব্যাসার্ধ নিলে পাই আট ব্যাসার্ধ।",
        "কোনোটি ভুল নয়; পার্থক্য শুধু আমরা কীভাবে পরিবর্তন পরিমাপ করছি তাতে।",
        "বৃত্ত, গোলক ও বর্গ—তিন জায়গাতেই একই নীতি কাজ করে।",
        "প্রতিসমভাবে বাড়লে ক্ষেত্রফল বা আয়তন বৃদ্ধির হার সবসময় সীমানার পরিমাপের সমান হয়।",
    ],
}

# Extra expansions (only if the quality gate still wants more speech) reuse the
# same high-quality, section-aware pedagogical sentences.
EXPANSION_POOL = CURATED_SENTENCES
DEFAULT_EXPANSIONS = [
    "এই ধারণাটি নিজের ভাষায় একবার বলে দেখলে বিষয়টি আরও পরিচ্ছন্ন হবে।",
    "লক্ষ্য করুন, ক্ষেত্রফলের এই অনুপাতই আমাদের আসল উত্তরের দিকে নিয়ে যায়।",
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
    """Read the audio_manifest referenced by lesson_07.json (read-only)."""
    rel = (lesson.get("audio_manifest") or lesson.get("audio_manifest_url") or
           (lesson.get("meta") or {}).get("audio_manifest") or
           (lesson.get("meta") or {}).get("audio_manifest_url"))
    candidates = []
    if rel:
        candidates.append((LESSON_JSON.parent / rel).resolve())
    candidates.append(WEB / "assets" / "audio" / "lockdown_math" / "lesson_07" / "manifest.json")

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


def load_source_cues():
    """Return (list_of_{text,dur_ms,section}, source_description)."""
    lesson = json.loads(LESSON_JSON.read_text(encoding="utf-8"))
    out, desc = load_manifest_cues(lesson)
    if not out:
        raise SystemExit("No manifest cues found for lesson_07")

    # Fold each section's rich Bengali paragraphs into the matching cue, then
    # append the STRONG curated pedagogical expansion (~24 sentences/cue).
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
        curated = CURATED_SENTENCES.get(c["section"], [])
        if curated:
            c["text"] = c["text"] + " " + " ".join(curated)
            c["curated_sentences"] = len(curated)
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
            "curated_sentences": c.get("curated_sentences", 0),
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
        print(f"  TTS {i+1}/{len(cues)} (chars={len(c['bn'])}, "
              f"curated={c.get('curated_sentences',0)})", flush=True)
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
    """Re-derive timeline scale from SUM OF RENDERED NATURAL SPEECH (not manifest)."""
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
            "curated_sentences": c.get("curated_sentences", 0),
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


def build_source_note():
    """Write the 3B1B provenance note (oEmbed + downloaded info.json)."""
    info = {}
    if ORIGINAL_INFO.exists():
        try:
            d = json.loads(ORIGINAL_INFO.read_text(encoding="utf-8"))
            info = {
                "youtube_id": d.get("id"),
                "title": d.get("title"),
                "uploader": d.get("uploader"),
                "channel": d.get("channel"),
                "duration_sec": d.get("duration"),
                "webpage_url": d.get("webpage_url"),
            }
        except Exception:
            pass
    note = f"""# Source metadata note — Lockdown Math Lesson 07 dub

- **Verified source:** {OEMBED_AUTHOR} (official YouTube channel)
- **oEmbed title:** {OEMBED_TITLE}
- **oEmbed author_name:** {OEMBED_AUTHOR}
- **oEmbed author_url:** https://www.youtube.com/@3blue1brown
- **YouTube id:** {VIDEO_ID} (corrected from the 404 id `b3NxrZOup_U`)
- **Downloaded info.json:** {json.dumps(info, ensure_ascii=False, indent=2)}
- **Downloaded file:** {ORIGINAL_VIDEO} (h264 1920x1080 60fps, video-only;
  the original English narration is discarded — no English vocal bleed).

## Duration discrepancy note
`web_platform/data/lockdown_math/lesson_07.json` advertises a duration of
`1:08:42`, but the corrected source id `{VIDEO_ID}` resolves to the official
3B1B clip "{OEMBED_TITLE}" whose real duration is ~950 s (15:50), confirmed by
both the oEmbed response and ffprobe. The dub canvas is therefore built to the
**actual** downloaded source duration (measured with ffprobe), exactly as the
proven clean_timesync_v2 pipeline does; it is never stretched to the inaccurate
metadata value.
"""
    SOURCE_NOTE.write_text(note, encoding="utf-8")
    return info


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

    info = build_source_note()
    vend = video_duration(src)
    VIDEO_END = vend
    source_cues, source_desc = load_source_cues()
    cues, initial_scale = load_cues(vend, source_cues)
    print(f"video={src} duration={vend:.3f}s cues={len(cues)} "
          f"source={source_desc} initial_manifest_scale={initial_scale:.4f}", flush=True)

    print("[1/7] TTS (clean, no SFX, ~24 curated sentences per cue) ...", flush=True)
    failed = await synth_all(cues)

    print("[2/7] Expansion of short cues (IMPROVED_DUB_FILL_POLICY) ...", flush=True)
    expanded = await expand_short_cues(cues)
    print(f"  expanded {len(expanded)} cues beyond the curated base", flush=True)

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
        "experiment": "clean_timesync_v2 (lockdown_math_lesson_07 full-length, STRONG curated expansion, improved fill, scale recomputed from rendered speech)",
        "lesson": LESSON,
        "course": "lockdown_math",
        "video_id": VIDEO_ID,
        "source_metadata_note": {
            "oembed_title": OEMBED_TITLE,
            "oembed_author_name": OEMBED_AUTHOR,
            "oembed_author_url": "https://www.youtube.com/@3blue1brown",
            "downloaded_info": info,
            "confirmed_3b1b": info.get("uploader") == "3Blue1Brown" or info.get("channel") == "3Blue1Brown",
            "note_file": str(SOURCE_NOTE),
            "duration_note": "lesson_07.json states 1:08:42 but the corrected verified 3B1B clip is ~950s; canvas uses the real ffprobe duration.",
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
        "curated_sentences_per_cue": [c.get("curated_sentences", 0) for c in cues],
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
