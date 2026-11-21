"""
EXPERIMENT — fill_v2: full-length gap-free Bengali dub (Essence of Calculus, Lesson 01)
======================================================================================
Goal: the previous clean_timesync_v2 video had 29 silent pockets, some up to 72 s,
because its timeline scale was derived from the *authored* manifest durations
(scale ~3.09x) while the *rendered* Edge-TTS speech was roughly half that long.
This build fixes that at the root:

  * Cue texts come from the read-only audio manifest (29 cues, 4 sections,
    alias-deduped). Each cue is HEAVILY expanded with contextual pedagogical
    Bengali so the rendered narration genuinely spans the whole lesson.
  * The layout scale is RECOMPUTED from the SUMMED RENDERED SPEECH (after TTS),
    not from authored durations. Windows are therefore proportional to the
    speech that actually exists -> no multi-second empty windows.
  * Absolute-sample placement (start * 44100) -> ZERO cumulative drift.
  * atempo fit in [0.82, 2.2]; PAD ONLY, NEVER truncate. NO SFX: clean speech.
  * QUALITY GATE: median_fill >= 0.72 AND max_internal_gap <= 1.5 s AND
    silencedetect internal runs > 2 s == 0 (only lead-in / tail allowed).
    On failure the script AUTO RE-RENDERS: it appends more pedagogical Bengali
    to the cues around the offending gaps, re-synthesises ONLY those cues,
    recomputes the scale from rendered speech, and re-checks (up to MAX_PASSES).

The old video (media_vault/calculus/lesson_01/experiments/3b1b_calculus_01_full_dubbed.mp4)
is NEVER overwritten. Teacher audio, manifests and other lessons are untouched.
Everything is written under NEW experiments/.../fill_v2 folders.
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

EXP = Path(__file__).resolve().parent                         # .../experiments/fill_v2
BASE = EXP.parent.parent                                      # .../lesson_01_calculus_intro/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"                        # .../3blue1brown_courses/web_platform
MANIFEST = WEB / "assets" / "audio" / "calculus" / "lesson_01" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "calculus" / "lesson_01" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "calculus" / "lesson_01" / "experiments" / "fill_v2" / "3b1b_calculus_01_full_dubbed_fill2.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_M4A = EXP / "master_for_video.m4a"
SILENCE_LOG = EXP / "_silencedetect.log"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
TEMPO_FLOOR = 0.82
FADE_MS = 12
VIDEO_ID = "WUvTyaaNkzM"
LESSON = "lesson_01_calculus_intro"

LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Quality gate (exactly as requested).
REQ_MEDIAN_FILL = 0.72
REQ_MAX_INTERNAL_GAP = 1.5
REQ_MAX_SILENCE_RUN = 2.0
MAX_PASSES = 5
SILENCE_NOISE_DB = -35.0

# Heavy, contextual pedagogical expansions keyed by the manifest cue's global
# 1-based index (29 cues after alias de-duplication). These are *added* to the
# original manifest cue text; they are never a replacement for it.
EXPANSIONS = {
    1: (" আজ আমরা ক্যালকুলাসের সেই মূল ভাবনার সাথে পরিচিত হব, যা সূত্র মুখস্থ করার বদলে "
        "বোঝার দাঁড়া তৈরি করে। প্রথমে দেখব হিলবার্ট কেন বলেছিলেন একটি বিশেষ উদাহরণের "
        "ভেতরেই সার্বজনীনতার বীজ লুকিয়ে থাকে। তারপর সেই বৃত্তের ক্ষেত্রফল থেকে শুরু করে "
        "পরিবর্তনের হার, আর শেষে ক্ষেত্রফল ও ঢালের মাঝে সেই সংযোগ যাকে আমরা মৌলিক "
        "উপপাদ্য বলি। পুরো যাত্রাটা হবে ভাঙা, আসন্নায়ন আর জুড়ে দেওয়ার।"),
    2: (" হিলবার্টের এই কথাটি আসলে একটা পদ্ধতিগত উপদেশ। ভালো গণিত মানে লক্ষ লক্ষ আলাদা "
        "ঘটনাকে আলাদাভাবে মুখস্থ করা নয়, বরং এমন একটি ক্ষেত্র খোঁজা যার ভেতর থেকে সব "
        "ঘটনারই জন্ম হয়। আমাদের আজকের বিশেষ ক্ষেত্রটি হলো বৃত্ত। এই বৃত্তকে ভালো করে "
        "বুঝলে পাই আর স্কয়ার, দুই পাই আর, আর ডি এ বাই ডি আর—এসব সূত্র আর মনে রাখতে "
        "হবে না, নিজেরাই বের হয়ে আসবে। সুন্দর উদাহরণ আসলে চিন্তার একটা ছাঁচ তৈরি করে দেয়।"),
    3: (" প্রশ্নটা ঠিক এই জায়গাতেই শুরু। আমরা ছোটবেলা থেকে বলে আসছি ক্ষেত্রফল পাই আর "
        "স্কয়ার, কিন্তু কেউ কখনো ব্যাখ্যা করেনি কেন ব্যাসার্ধের বর্গ এসেছে, আর কেন "
        "পারিধির ধ্রুবক পাই এখানে হাজির হয়েছে। একইভাবে দুই এক্স, চেইন রুল, প্রোডাক্ট "
        "রুল—এগুলোকে আমরা নিয়ম হিসেবে মানি, উৎপত্তি হিসেবে নই। কিন্তু গণিতে কোনো নিয়মই "
        "আকাশ থেকে পড়ে না; প্রতিটির পেছনে একটা সরল ছবি আছে। আজ আমরা সেই ছবিটা খুঁজে "
        "বের করব, সূত্রগুলোকে মুখস্থের বদলে উপলব্ধি করে নেব।"),
    4: (" হিলবার্টের উপদেশ মানে আমরা সাধারণ বৃত্তের বদলে একটি নির্দিষ্ট বৃত্ত বেছে নেব। "
        "এই বেছে নেওয়া কোনো সীমাবদ্ধতা নয়, বরং একটা কৌশল। যখন আমরা একটিমাত্র উদাহরণকে "
        "যত গভীরভাবে দেখি, তখন তার ভেতরের কাঠামো অন্য সব ক্ষেত্রেও কাজ করে। বৃত্তের "
        "বলয়গুলোকে সোজা করার যে ছবি আমরা দেখব, সেটাই পরে যেকোনো বক্ররেখার ক্ষেত্রফল,"
        "যেকোনো পরিবর্তনের হার—সবকিছু বোঝার চাবিকাঠি হয়ে যাবে। বিশেষ থেকে সার্বজনীন—এই "
        "লাফটিই ক্যালকুলাসের প্রথম শিক্ষা।"),
    5: (" তিনটি ধাপের প্রথমটি হলো ভাঙা: একটা অচেনা বা কঠিন আকারকে অসংখ্য ছোট ছোট পাতলা "
        "অংশে কাটা, যাদের প্রতিটিকে চেনা সরল আকৃতি হিসেবে মাপা যায়। দ্বিতীয়টি হলো "
        "আসন্নায়ন: প্রতিটি ছোট অংশের জন্য একটা ভালো আনুমানিক হিসাব তৈরি করা। তৃতীয়টি "
        "হলো জুড়ে দাও: ডি আর যখন শূন্যের দিকে এগিয়ে যায়, তখন সব আনুমানিক টুকরোকে "
        "একসাথে যোগ করে নিখুঁত উত্তর বের করা। মনে রাখবেন, ক্যালকুলাসে অসীমকে ভয় পাওয়া "
        "যায় না—সীমার মাধ্যমে অসীম যোগফলকেই সসীম ও নির্ভুল করে তোলা হয়। এই তিন ধাপই "
        "পরবর্তী প্রতিটি পাঠে বারবার ফিরে আসবে।"),
    6: (" সমাকলন আর অন্তরীকরণ—এই দুটিকে কখনো আলাদা মনে করবেন না। সমাকলন জুড়ে দেখে: "
        "অসংখ্য ক্ষুদ্র ক্ষুদ্র ফালিকে যোগ করে মোট ক্ষেত্রফল বার করে। অন্তরীকরণ ভেঙে "
        "দেখে: কোনো রাশির অতিক্ষুদ্র পরিবর্তনকে তার নিজের আকারের সাথে তুলনা করে তাৎক্ষণিক "
        "হার মাপে। একটির কাজ যোগ, অন্যটির কাজ ভাগ; একটা বড় করে, অন্যটি ছোট করে। আমরা "
        "এই পাঠে দুটোকেই একই বৃত্তের ছবির উপর দিয়ে চলে যেতে দেখব, আর শেষে দেখব একটিকে "
        "অন্যটির দর্পণ।"),
    7: (" দ্বিতীয় পরিচ্ছেদে আমরা হাতে-কলমে দেখব সূত্রটা কীভাবে তৈরি হয়। আগে বলয় কাটব, "
        "তারপর প্রতিটি বলয়কে সোজা করব, আর শেষে সব বলয়ের ক্ষেত্রফল একসাথে যোগ করব। "
        "এই তিনটি ছবি মনে থাকলে পাই আর স্কয়ার আর কখনো মুখস্থ করতে হবে না। সাথে সাথে "
        "রিমান সমষ্টির ধারণাও এই প্রক্রিয়ার ভেতর থেকেই জন্ম নেবে—নামটা নতুন হলেও "
        "কাজটা আমরা আগেই করেছি।"),
    8: (" আমরা সবাই জানি আর ব্যাসার্ধবিশিষ্ট বৃত্তের ক্ষেত্রফল পাই আর স্কয়ার। কিন্তু "
        "এই ছোট্ট সূত্রটির ভেতরে আছে জ্যামিতি আর পরিবর্তনের এক গভীর মিল। ব্যাসার্ধ আর "
        "বলতে আমরা সরলরেখার দূরত্ব বুঝি, আর ক্ষেত্রফল বলি সমতলে আবদ্ধ জায়গার পরিমাণ—"
        "দুটো সম্পূর্ণ আলাদা ধরনের রাশি। তবুও একটির বর্গ আর একটা ধ্রুবক গুণ করে ঠিক "
        "অন্যটি পাওয়া যায়। কীভাবে এই দুই ভিন্ন জগৎ একে অপরের সাথে এমনভাবে জড়িয়ে "
        "গেল, তাই আমাদের আজকের অনুসন্ধান।"),
    9: (" সূত্রটিকে এক মুহূর্তের জন্য চোখের সামনে রাখুন: ক্ষেত্রফল সমান পাই আর স্কয়ার। "
        "এখানে পাই একটা ধ্রুবক, আর আর হলো ব্যাসার্ধ। আর বাড়ালে ক্ষেত্রফল কত বাড়ে, "
        "তা কি আন্দাজ করা যায়? এই প্রশ্নটিই সমাকলন আর অন্তরীকরণ দুটোকেই জন্ম দেয়। "
        "আমরা এখন দেখব সূত্রটিকে টুকরো টুকরো করে ভেঙে তার ভেতরের গতি ধরা যায় কি না।"),
    10: (" পাই মূলত পরিধি আর ব্যাসের অনুপাত, অর্থাৎ পাই সমান সি বাই দুই আর। একই কথাকে "
         "উল্টো করে লিখলে সি সমান দুই পাই আর। এখন প্রশ্ন: পরিধির এই দুই পাই আর কীভাবে "
         "ক্ষেত্রফলের ভেতরে আর স্কয়ার হয়ে হাজির হলো? যদি আমরা বৃত্তটিকে পাতলা পাতলা "
         "বলয়ে কাটি, তবে প্রতিটি বলয়ের দৈর্ঘ্য হবে তার পরিধি আর প্রস্থ হবে সেই পাতলা "
         "বেধ। এই দুটোকে গুণ করলেই আমরা একটা ছোট্ট আয়তক্ষেত্রের ক্ষেত্রফল পাই—আর "
         "সবগুলো যোগ করলেই পুরো বৃত্তের ক্ষেত্রফল।"),
    11: (" গ্রান্ট স্যান্ডারসনের এই কৌশলটা আসলে খুব স্বজ্ঞাত। সোজা গ্রিড দিয়ে বৃত্ত মাপতে "
         "গেলে বাঁকা সীমানা আর সরল বর্গের মাঝে সবসময় ফাঁক থাকে; যত ছোট বর্গ নেব, হিসাব "
         "তত কঠিন হয়। কিন্তু বৃত্তকে সমকেন্দ্রিক বলয়ে কাটলে প্রতিটি টুকরো নিজেই প্রায় "
         "একটা আয়তক্ষেত্রের মতো আচরণ করে। এইভাবে কঠিন বক্রতাকে সহজ সরলতায় রূপ দেওয়া "
         "হলো ক্যালকুলাসের প্রথম মহাকৌশল। আসুন ধাপে ধাপে সেই কাটা আর সোজা করার ছবিটি "
         "মনে আঁকি।"),
    12: (" ছবিটির দিকে খনেকক্ষণ তাকাই। হলুদ রেখাটি ব্যাসার্ধ আর, আর গোলাপি রেখাটি সবচেয়ে "
         "বাইরের বলয়ের অতিক্ষুদ্র বেধ ডি আর। ভেতরের বলয়গুলোর ব্যাসার্ধ ছোট, বাইরেরগুলোর "
         "বড়—কিন্তু সবার বেধ একই। এই সুসমতাটি খুব গুরুত্বপূর্ণ, কারণ একই বেধ থাকায় "
         "প্রতিটি বলয়ের হিসাব একই নিয়মে করা যায়। পরে যখন আমরা সব বলয়ের ক্ষেত্রফল "
         "যোগ করব, তখন এই সুসমতার কারণেই কাজটা সহজ হবে।"),
    13: (" ধরা যাক কেন্দ্র থেকে আর দূরত্বে একটা নির্দিষ্ট বলয় নেওয়া হলো। এই বলয়টির বেধ "
         "অত্যন্ত পাতলা—ক্যালকুলাসের ভাষায় একে বলি ডি আর, অর্থাৎ ব্যাসার্ধের একটা "
         "অতিক্ষুদ্র পরিবর্তন। ডি আর যত ছোট হবে, বলয়টির ভেতরের আর বাইরের পরিধির "
         "পার্থক্য তত কম হবে। এইখানেই লিমিটের ধারণা কাজ শুরু করে: আমরা অসীম সংখ্যক "
         "এমন পাতলা বলয় নেব, যেন প্রতিটির হিসাব যত নিখুঁত হওয়া যায়। তখন আনুমানিক "
         "উত্তরটা আসল উত্তরের কাছে এগিয়ে যাবে।"),
    14: (" এখন সবচেয়ে মজার অংশ। এই পাতলা বলয়টিকে এক জায়গায় কাঁচি দিয়ে কেটে সোজা "
         "লম্বা ফিতার মতো বিছিয়ে দিই কি হবে? সেটি প্রায় একটা নিখুঁত আয়তক্ষেত্র তৈরি "
         "করবে। তার দৈর্ঘ্য হবে মূল বলয়ের পরিধি দুই পাই আর, আর প্রস্থ হবে পাতলা বেধ "
         "ডি আর। তাহলে এই একক বলয়ের অতিক্ষুদ্র ক্ষেত্রফল ডি এ হবে দৈর্ঘ্য আর প্রস্থের "
         "গুণফল, অর্থাৎ দুই পাই আর গুণ ডি আর। একটা বাঁকা বলয় সোজা আয়তক্ষেত্রে রূপ "
         "নিল—এই রূপান্তরটাই সমাকলনের সমগ্র কৌশল।"),
    15: (" সূত্রটার দিকে আবার এক নজর দিন: ডি এ প্রায় সমান দুই পাই আর গুণ ডি আর। "
         "এখানে 'প্রায়' শব্দটার উপর জোর দিচ্ছি, কারণ যতক্ষণ ডি আর সসীম, ততক্ষণ "
         "ভুল একটু থাকবেই। কিন্তু ডি আর যখন শূন্যের দিকে ধাবিত হয়, তখন এই 'প্রায়' "
         "ঠিক হয়ে যায়। অর্থাৎ ডি এ বাই ডি আর সমান দুই পাই আর—পরিধি।"),
    16: (" একটা সূক্ষ্ম বিন্দু এখনই পরিষ্কার করে নিই। বলয়টির ভেতরের পরিধি দুই পাই আর আর "
         "বাইরের পরিধি দুই পাই ইনটু আর যোগ ডি আর—এরা ঠিক একই নয়। তাই আমাদের আয়তক্ষেত্র "
         "আসলে সামান্য ট্রাপিজয়েড হবে। কিন্তু ডি আর যত ক্ষুদ্রতর হবে, এই পার্থক্য তত "
         "অদৃশ্য হয়ে যাবে। কাগজের উপর আঁকা সিঁড়ির মতো খাঁজকাটা শীর্ষ যখন মসৃণ বক্ররেখার "
         "কাছে আসে, ঠিক তেমনি এই ট্রাপিজয়েডও আয়তক্ষেত্রে রূপ নেয়। সীমায় ভুল সম্পূর্ণ "
         "শূন্য হয়ে যায়—এই বিশ্বাসটিই আমাদের পরবর্তী হিসাবের ভিত্তি।"),
    17: (" তৃতীয় পরিচ্ছেদে ক্যালকুলাসের অন্য পিঠটি দেখব। এ পর্যন্ত আমরা জুড়ে দিয়ে ক্ষেত্রফল "
         "বার করলাম; এখন ভেঙে দিয়ে পরিবর্তনের হার বার করব। এই দুটো কাজ একে অপরের উল্টো "
         "মনে হলেও আসলে একই ছবির দুই দিক। আমরা আবার সেই বৃত্তের কাছেই ফিরে যাব, কারণ "
         "একটা পরিচিত উদাহরণে নতুন প্রশ্ন জিজ্ঞেস করা সবচেয়ে সহজ পথ।"),
    18: (" বৃত্তের ক্ষেত্রফলের উদাহরণটিতেই প্রশ্ন করি: ব্যাসার্ধ আর কে খুব সামান্য পরিমাণ "
         "ডি আর বৃদ্ধি করলে ক্ষেত্রফল ঠিক কতটুকু বাড়বে? এই প্রশ্নটা দেখতে সাধারণ, কিন্তু "
         "এর ভেতরেই পরিবর্তনের হারের পুরো তত্ত্ব লুকিয়ে আছে। আমরা সাধারণত কোনো রাশির "
         "মান জানি, তার পরিবর্তনটি জানি না।"),
    19: (" এই প্রশ্নের উত্তর আমরা আগেই দেখে এসেছি, কেবল তখন একে বলয়ের ক্ষেত্রফল বলেছিলাম। "
         "ব্যাসার্ধ একটু বাড়ালেই বৃত্তের চারপাশে একটা নতুন পাতলা স্তর যোগ হয়—ঠিক যেমন "
         "গাছের চারপাশে নতুন বাকল তৈরি হয়। এই নতুন স্তরটির ক্ষেত্রফলই হলো ক্ষেত্রফলের "
         "বৃদ্ধি ডি এ। অর্থাৎ ভাঙা আর জুড়ে দেওয়ার আগের হিসাবটা আজ আমাদের কাজে আসছে।"),
    20: (" সেই নতুন অংশের ক্ষেত্রফল হলো একদম বাইরের বলয়টির ক্ষেত্রফল, যার মান দুই পাই আর "
         "গুণ ডি আর। আগের পাঠে আমরা এই কথাটা আয়তক্ষেত্রের ছবি থেকে পেয়েছিলাম। এখন "
         "একই ফলাফলকে অন্য চোখে দেখছি: ব্যাসার্ধ বাড়লেই ক্ষেত্রফল কেবল পরিধি বরাবরই "
         "বিস্তৃত হয়। ভেতরের কোনো অংশ নড়ছেই না—শুধু বাইরের রিমটা নতুন করে তৈরি হচ্ছে।"),
    21: (" এখন উভয়পক্ষকে ডি আর দিয়ে ভাগ করি। বাঁ পাশে থাকল ডি এ বাই ডি আর, অর্থাৎ "
         "ক্ষেত্রফলের পরিবর্তনের হার; ডান পাশে থাকল দুই পাই আর, অর্থাৎ পরিধি। ভাগ করার "
         "এই সরল পদক্ষেপটাই ক্যালকুলাসের সবচেয়ে শক্তিশালী পদক্ষেপ—এটা আমাদের বড় "
         "বৃদ্ধিকে ছোট বৃদ্ধি দিয়ে ভাগ করে তার আসল গতি বের করে দেয়। ডি আর শূন্যের কাছে "
         "গেলে অনুমানটা নিখুঁত হয়।"),
    22: (" সুতরাং আমাদের হাতে একটা সূত্র আছে: ডি এ বাই ডি আর সমান দুই পাই আর। "
         "বাঁ দিকে আছে পরিবর্তনের হার, ডান দিকে আছে একটা পরিচিত জ্যামিতিক রাশি। "
         "এই সূত্রটিকে কেবল মনে রাখলেই হবে না; এর পেছনের ছবিটা মনে রাখতে হবে—ব্যাসার্ধ "
         "বাড়লে ক্ষেত্রফল কেবল বাইরের রিম বরাবর বাড়ে। ছবি মনে থাকলে সূত্র নিজেই তৈরি "
         "হয়ে যায়।"),
    23: (" একবার ভেবে দেখুন কতটা অদ্ভুত! বৃত্তের ক্ষেত্রফলের পরিবর্তনের হার হুবহু তার "
         "পরিধির সমান। ক্ষেত্রফল এক ধরনের রাশি, পরিধি আরেক ধরনের—তবুও একটা অন্যটির "
         "হার হয়ে গেল। এর কারণ আগের ছবিতেই আছে: ব্যাসার্ধ সামান্য বাড়ালে বৃত্ত কেবল "
         "নিজের পরিধি বরাবরই নতুন স্তর পায়। পরিবর্তনের হার নিজেরাই একটা পরিচিত "
         "জ্যামিতিক রাশিকে ছুঁয়ে যায়। এইরকম আশ্চর্য মিলই গণিতকে এত সুন্দর করে তোলে।"),
    24: (" সাধারণীকরণ করা যাক। যেকোনো ফাংশন এফ অফ এক্সের জন্য ইনপুটের ক্ষুদ্র পরিবর্তন "
         "হলো ডি এক্স, আর আউটপুটের সংশ্লিষ্ট বৃদ্ধি হলো ডি এফ। তাদের অনুপাত ডি এফ বাই "
         "ডি এক্স হলো লেখচিত্রের স্পর্শকের ঢাল, অর্থাৎ তাৎক্ষণিক পরিবর্তনের হার। যেমন "
         "এফ অফ এক্স সমান এক্স স্কয়ারের ক্ষেত্রে এই হার দুই এক্স—মূলবিন্দুতে ঢাল প্রায় "
         "শূন্য, এক্স বাড়ার সাথে সাথে ক্রমেই খাড়া। স্পর্শকের এই ছবিটি মনে রাখলেই "
         "অন্তরজ কোনো বিমূর্ত সূত্র থাকে না, একটা সরলরেখার ঢাল হয়ে দাঁড়ায়।"),
    25: (" চতুর্থ পরিচ্ছেদে আমরা দুটো আলাদা গল্পকে এক করে দেখব। এখন পর্যন্ত ক্ষেত্রফল আর "
         "পরিবর্তনের হারকে আমরা আলাদা আলাদাভাবে বুঝেছি। কিন্তু ক্যালকুলাসের প্রাণবন্ত "
         "রহস্য হলো এরা পরস্পরের দর্পণ—একটির ভেতরে অন্যটির প্রতিবিম্ব ঘুরে আসে। এই "
         "সংযোগটাই ক্যালকুলাসের মৌলিক উপপাদ্য নামে পরিচিত, আর এটি পুরো গণিতের সবচেয়ে "
         "গুরুত্বপূর্ণ আবিষ্কারগুলোর একটি।"),
    26: (" ক্ষেত্রফল আর পরিবর্তনের হারকে আমরা ভেবেছিলাম দুটি আলাদা গল্প—একটা জুড়ে দেওয়ার, "
         "অন্যটা ভেঙে দেখার। কিন্তু আসলে এরা একই প্রক্রিয়ার দুই দিক। যেমন যোগ আর বিয়োগ "
         "পরস্পরের বিপরীত, গুণ আর ভাগ পরস্পরের বিপরীত—তেমনি জমা করা আর ভেঙে দেখাও "
         "পরস্পরের বিপরীত ক্রিয়া। একটির ফলকে অন্যটি ফিরিয়ে আনে। এই দর্পণ-সম্পর্কটি "
         "বুঝতে পারলেই ক্যালকুলাস আর সূত্রের ঝোলা থাকে না, একটা সুসংবদ্ধ গল্প হয়ে যায়।"),
    27: (" সূত্রটা হলো: ডি বাই ডি এক্স অফ এ অফ এক্স সমান এফ অফ এক্স। কথায় বললে—ক্ষেত্রফল "
         "ফাংশনের অন্তরজ মূল ফাংশনের সমান। এই এক লাইনে আছে অসীম আর সসীমের মিলন। "
         "বাঁ দিকে আছে একটা চলকের সাথে বদলে যাওয়া ক্ষেত্রফলের হার, আর ডান দিকে আছে "
         "মূল বক্ররেখার উচ্চতা। আমরা এখন দেখব কীভাবে এই দুটো ঠিক একই জিনিস হয়ে যায়।"),
    28: (" একটি নতুন ফাংশন সংজ্ঞায়িত করি: এ অফ এক্স, অর্থাৎ লেখচিত্রের নিচে জমা হওয়া "
         "ক্ষেত্রফল। ডান দিকে অতি ক্ষুদ্র ডি এক্স পদক্ষেপে যোগ হয় এক টুকরো ক্ষেত্রফল, "
         "মূলত উচ্চতা এফ অফ এক্স গুণ ডি এক্স। ফলে এ অফ এক্সের পরিবর্তনের হার ফিরিয়ে দেয় "
         "ঢাল এফ অফ এক্স নিজেকেই। বৃত্তে এসে গল্পটি পূর্ণতা পায়: পাই আর স্কয়ারের ঢাল "
         "দুই পাই আর, ঠিক পরিধি। একটা সরল পদক্ষেপেই অসীম যোগফলের জটিলতা মিলিয়ে গেল।"),
    29: (" মূল অন্তর্দৃষ্টিটা আবার মনে করি: ক্ষুদ্রাতিক্ষুদ্র বলয়ের যোগফল, অর্থাৎ সমাকলন, "
         "দেয় ক্ষেত্রফল; আর ক্ষেত্রফলের ঢাল, অর্থাৎ অন্তরীকরণ, ফিরিয়ে দেয় পরিধিকে। "
         "যেমন গুণ আর ভাগ বিপরীত দুই ক্রিয়া, ক্যালকুলাসের এই দুই স্তম্ভও ঠিক তেমনি "
         "পরস্পরের বিপরীত। বৃত্তের এই বিশেষ উদাহরণের ভেতরেই লুকায় ক্যালকুলাসের সার্বজনীন "
         "বীজ। অতএব ক্যালকুলাস মুখস্থ সূত্রের ঝোলা নয়; এটি সেই শিল্প যেখানে সমষ্টি রূপ নেয় "
         "সীমায়, আর ক্ষেত্রফল ও ঢাল বলে যায় পরস্পরের গল্প। আজ এখানেই শেষ—পরের পাঠে "
         "নতুন কিছু নিয়ে আবার দেখা করব। সবাইকে ধন্যবাদ, আবার দেখা হবে!"),
}

# Generic extra used by the auto re-render loop (appended to a gap-adjacent cue).
GENERIC_EXTRA = (
    " এখানে একটু থামুন এবং বিষয়টি নিজের ভাষায় বলে দেখুন। কোনো ধারণা তখনই পোক্ত হয় যখন "
    "আপনি সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন। আসুন একই ছবিটি অন্য কোণ থেকে "
    "আবার দেখি—কোথায় ক্ষুদ্র অংশ তৈরি হলো, কোথায় আসন্নায়ন নেওয়া হলো, আর কোথায় সীমায় "
    "গিয়ে সব টুকরো আবার এক হয়ে গেল। এই তিনটি প্রশ্ন মনে রাখলে যেকোনো ক্যালকুলাসের সূত্রকেই "
    "নিজের মতো করে পুনর্নির্মাণ করা যায়।"
)


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
    """Robust synth: 0-byte purge, 12 attempts, half/sentence split fallbacks.

    Long texts (>1400 chars) are synthesised in sentence-sized chunks up front
    and concatenated, which avoids any per-request size limit.
    """
    if not force and valid(raw):
        return True
    purge(raw)

    if len(text) > 1400:
        parts, buf = [], ""
        for sent in re.split(r"(?<=।)", text):
            if not sent.strip():
                continue
            if len(buf) + len(sent) > 950 and buf:
                parts.append(buf.strip())
                buf = ""
            buf += " " + sent.strip()
        if buf.strip():
            parts.append(buf.strip())
        made = []
        for j, p in enumerate(parts):
            pp = RAW_DIR / f"chunk_{raw.stem}_{j:02d}.mp3"
            purge(pp)
            try:
                await tts_save(p, pp)
                if valid(pp):
                    made.append(pp)
            except Exception:
                pass
        if made:
            lf = RAW_DIR / f"chunklist_{raw.stem}.txt"
            with open(lf, "w", encoding="utf-8") as f:
                for x in made:
                    f.write(f"file '{x.as_posix()}'\n")
            run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{raw}" > NUL 2>&1')
            if valid(raw):
                return True

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
    """Load the 29 manifest cues, de-duplicated by section_id (alias dedup)."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    seen = set()
    cues = []
    for sec_key, sec in data.get("sections", {}).items():
        sid = sec.get("section_id", sec_key)
        if sid in seen:
            continue
        seen.add(sid)
        for c in sec.get("cues", []):
            cues.append({
                "id": len(cues) + 1,
                "index": int(c.get("index", 0)),
                "section": sid,
                "text": c["text"],
                "authored_dur_ms": float(c.get("duration_ms", 0)),
                "extras": [],
            })
    if len(cues) != 29:
        print(f"  WARNING: expected 29 deduped cues, got {len(cues)}", flush=True)
    return cues


def cue_text(c):
    """Manifest cue text + heavy pedagogical expansion + any auto-render extras."""
    base = c["text"] + " " + EXPANSIONS.get(c["id"], "")
    return sanitize(base + " " + " ".join(c.get("extras", [])))


async def synth_all(cues, force_ids=None):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    force_ids = set(force_ids or [])
    failed = []
    for i, c in enumerate(cues):
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        ok = await synth(cue_text(c), raw, force=(c["id"] in force_ids))
        if not ok:
            failed.append(c["id"])
            print(f"  WARNING cue {c['id']} failed after every fallback", flush=True)
        if (i + 1) % 10 == 0:
            print(f"  TTS {i+1}/{len(cues)}", flush=True)
    return failed


def layout_from_rendered(cues, vend, naturals):
    """RECOMPUTE the timeline scale from SUMMED RENDERED SPEECH.

    Each window is made proportional to the speech that actually exists, so a
    cue cannot own a multi-second empty window. The whole timeline is scaled
    once to span [LEAD_IN, vend - TAIL_MARGIN].
    """
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    pause_s = INTER_CUE_PAUSE_MS / 1000.0
    rendered_total = sum(naturals.values())
    basis = rendered_total + pause_s * (len(cues) - 1)
    scale = usable / basis if basis > 0 else 1.0
    cursor = 0.0
    out = []
    for c in cues:
        nat = naturals[c["id"]]
        start = LEAD_IN_SEC + cursor * scale
        window = nat * scale
        out.append({
            "id": c["id"],
            "start": round(start, 6),
            "end": round(start + window, 6),
            "duration": round(window, 6),
            "natural": nat,
        })
        cursor += nat + pause_s
    return out, scale, rendered_total


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


LAST_START = 0.0
VIDEO_END = 0.0
LAST_ID = None


def make_cue(raw, target, out, cid):
    """atempo-fit into window; PAD only, NEVER truncate. Returns (arr, info)."""
    natural = duration(raw)
    if natural <= 0:
        natural = target
    eff_target = target
    if cid == LAST_ID:
        eff_target = min(target, VIDEO_END - LAST_START - 0.10)
    tempo = max(TEMPO_FLOOR, min(MAX_TEMPO, natural / eff_target)) if eff_target > 0 else 1.0
    tmp = out.with_suffix(".fit.wav")
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)
    speech_samples = len(arr)
    need = int(round(eff_target * SR))
    if len(arr) < need:
        arr = np.pad(arr, (0, need - len(arr)))     # pad only, never cut
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
        "target": round(eff_target, 3),
        "fill_ratio": round(fill, 4),
        "internal_gap_s": round(gap_s, 4),
        "speech_samples": speech_samples,
        "window_samples": need,
    }
    return arr, info


def place(cues, timeline, vend):
    """Absolute-sample placement onto a FULL-length canvas; measure fill/gaps."""
    global LAST_START, VIDEO_END, LAST_ID
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    CHUNK = 1_000_000
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed, fills, gaps = [], [], []
    overrun = 0
    last_cue_end = 0.0
    tmap = {t["id"]: t for t in timeline}
    for c in cues:
        cid = c["id"]
        t = tmap[cid]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            print(f"  SKIP cue {cid} (no audio)", flush=True)
            continue
        arr, info = make_cue(raw, float(t["duration"]), CUE_DIR / f"cue_{cid:03d}.wav", cid)
        fills.append(info["fill_ratio"])
        gaps.append(info["internal_gap_s"])
        if info["speech_samples"] > info["window_samples"] + 200:
            overrun += 1
        if len(arr) >= 2 * fade_n:
            arr[:fade_n] *= env
            arr[-fade_n:] *= env[::-1]
        start_sample = int(round(float(t["start"]) * SR))
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
        placed.append({
            "id": cid,
            "section": c["section"],
            "expected_start_ms": round(float(t["start"]) * 1000, 2),
            "actual_start_ms": round(start_sample / SR * 1000, 2),
            "drift_ms": round(start_sample / SR * 1000 - float(t["start"]) * 1000, 6),
            "tempo": info["tempo"],
            "natural_sec": info["natural"],
            "target_sec": info["target"],
            "fill_ratio": info["fill_ratio"],
            "internal_gap_s": info["internal_gap_s"],
            "window_start_s": float(t["start"]),
            "window_end_s": float(t["end"]),
            "extras": len(c.get("extras", [])),
        })

    # Peak-normalise in chunks to avoid clipping.
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

    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    max_internal_gap = round(max(gaps), 4) if gaps else 0.0
    return canvas, placed, overrun, last_cue_end, median_fill, max_internal_gap


def write_and_mux(canvas, vend):
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        CHUNK = 1_000_000
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')
    OUT_VIDEO.parent.mkdir(parents=True, exist_ok=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')


def silencedetect(path, vend):
    """Return (all_runs, internal_runs_gt_2s) parsed from ffmpeg silencedetect."""
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-nostats", "-vn",
        "-i", str(path),
        "-af", f"silencedetect=noise={SILENCE_NOISE_DB}dB:d={REQ_MAX_SILENCE_RUN}",
        "-f", "null", "-",
    ]
    with open(SILENCE_LOG, "wb") as fh:
        subprocess.run(cmd, stdout=fh, stderr=fh)
    txt = SILENCE_LOG.read_text(encoding="utf-8", errors="ignore")
    starts = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", txt)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([\d.]+)", txt)]
    runs = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else vend
        runs.append((round(s, 3), round(e, 3), round(e - s, 3)))
    internal = [r for r in runs
                if r[0] > LEAD_IN_SEC + 1.0 and r[1] < vend - TAIL_MARGIN_SEC + 1.0]
    return runs, internal


def gap_cue_ids(internal, placed):
    """Map each internal silence run to the cue whose window ends just before it."""
    ids = []
    for s, e, _ in internal:
        before = [p for p in placed if p["window_end_s"] <= s + 0.15]
        after = [p for p in placed if p["window_start_s"] >= e - 0.15]
        if before:
            ids.append(before[-1]["id"])
        elif after:
            ids.append(after[0]["id"])
    return ids


async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    cues = load_manifest_cues()
    LAST_ID = cues[-1]["id"]
    print(f"video duration = {vend:.3f}s; cues = {len(cues)}; source = {MANIFEST.name}", flush=True)

    print("[1] TTS — manifest cue + heavy pedagogical expansion ...", flush=True)
    failed = await synth_all(cues)

    history = []
    metrics = {}
    for pass_no in range(1, MAX_PASSES + 1):
        print(f"[2.{pass_no}] Recompute scale from summed RENDERED speech ...", flush=True)
        naturals = {c["id"]: duration(RAW_DIR / f"raw_{c['id']:03d}.mp3") for c in cues}
        timeline, scale, rendered_total = layout_from_rendered(cues, vend, naturals)
        LAST_START = float(timeline[-1]["start"])
        print(f"  rendered_speech_total = {rendered_total:.2f}s ; scale = {scale:.4f}", flush=True)

        print(f"[3.{pass_no}] Absolute-sample placement (pad-only, tempo "
              f"{TEMPO_FLOOR}-{MAX_TEMPO}) ...", flush=True)
        canvas, placed, overrun, last_end, median_fill, max_gap = place(cues, timeline, vend)

        print(f"[4.{pass_no}] Mux with FULL original video + silencedetect ...", flush=True)
        write_and_mux(canvas, vend)
        runs, internal = silencedetect(OUT_VIDEO, vend)

        median_ok = median_fill >= REQ_MEDIAN_FILL
        gap_ok = max_gap <= REQ_MAX_INTERNAL_GAP
        silence_ok = len(internal) == 0
        gate_ok = median_ok and gap_ok and silence_ok
        metrics = {
            "pass": pass_no,
            "median_fill": median_fill,
            "max_internal_gap_s": max_gap,
            "internal_silence_runs_gt_2s": len(internal),
            "internal_silence_details": internal,
            "median_fill_ok": median_ok,
            "max_internal_gap_ok": gap_ok,
            "silence_ok": silence_ok,
            "gate_ok": gate_ok,
            "scale": round(scale, 6),
            "rendered_speech_total_s": round(rendered_total, 3),
            "overrun_cues": overrun,
        }
        history.append({k: v for k, v in metrics.items() if k != "internal_silence_details"})
        print(f"  median_fill={median_fill} max_internal_gap={max_gap}s "
              f"internal_silence_runs>2s={len(internal)} -> gate_ok={gate_ok}", flush=True)
        if internal:
            print(f"  internal runs: {internal[:6]}{' ...' if len(internal) > 6 else ''}", flush=True)

        if gate_ok:
            break

        if pass_no == MAX_PASSES:
            break

        # AUTO RE-RENDER: expand cues adjacent to the offending silent pockets,
        # plus the lowest-fill cues, then re-synthesise ONLY those cues.
        targets = set(gap_cue_ids(internal, placed))
        low_fill = sorted(placed, key=lambda p: p["fill_ratio"])[:6]
        for p in low_fill:
            if p["fill_ratio"] < 0.95:
                targets.add(p["id"])
        if not targets:
            targets = {c["id"] for c in cues}
        print(f"  auto re-render pass {pass_no+1}: expanding cues {sorted(targets)}", flush=True)
        for cid in targets:
            cues[cid - 1].setdefault("extras", []).append(GENERIC_EXTRA)
        forced = await synth_all(cues, force_ids=targets)
        for fid in forced:
            print(f"  WARNING re-synth failed for cue {fid}", flush=True)

    max_drift = max((abs(p["drift_ms"]) for p in placed), default=0.0)
    report = {
        "experiment": "fill_v2 — gap-free full-length Bengali dub (calculus lesson_01)",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": f"audio_manifest:{MANIFEST.name} (29 cues, alias-deduped, heavily expanded)",
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": "scale recomputed from SUMMED RENDERED speech; absolute sample offset; "
                    "atempo in [0.82,2.2]; pad only; no truncation; no SFX",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "tempo_floor": TEMPO_FLOOR,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "timeline_scale": round(scale, 6),
        "rendered_speech_total_s": round(rendered_total, 3),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "video_duration_sec": round(vend, 3),
        "last_cue_end_sec": round(last_end, 3),
        "tail_silence_sec": round(vend - last_end, 3),
        "quality_gate": {
            "required_median_fill": REQ_MEDIAN_FILL,
            "required_max_internal_gap_s": REQ_MAX_INTERNAL_GAP,
            "required_internal_silence_runs_gt_2s": 0,
            "median_fill": metrics["median_fill"],
            "max_internal_gap_s": metrics["max_internal_gap_s"],
            "internal_silence_runs_gt_2s": metrics["internal_silence_runs_gt_2s"],
            "median_fill_ok": metrics["median_fill_ok"],
            "max_internal_gap_ok": metrics["max_internal_gap_ok"],
            "silence_ok": metrics["silence_ok"],
            "gate_passed": metrics["gate_ok"],
        },
        "all_silence_runs": runs,
        "pass_history": history,
        "passes_used": metrics["pass"],
        "output_video": str(OUT_VIDEO),
        "output_duration_sec": round(duration(OUT_VIDEO), 3),
        "output_size_bytes": OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0,
        "cues": placed,
    }
    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\nDONE.", flush=True)
    print(f"  output = {OUT_VIDEO}", flush=True)
    print(f"  duration = {report['output_duration_sec']}s ; size = {report['output_size_bytes']}", flush=True)
    print(f"  scale = {scale:.4f} ; rendered_speech = {rendered_total:.1f}s ; passes = {metrics['pass']}", flush=True)
    print(f"  median_fill = {metrics['median_fill']} ; max_internal_gap = {metrics['max_internal_gap_s']}s", flush=True)
    print(f"  internal_silence_runs>2s = {metrics['internal_silence_runs_gt_2s']} ; GATE = {metrics['gate_ok']}", flush=True)
    print(f"  VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
