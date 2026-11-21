"""
EXPERIMENT fill_v2 — Full-length clean absolute-sample Bengali dub
(Essence of Calculus, Lesson 07: Limits & the definition of derivatives)
==========================================================================================
Goal: eliminate the 43 silent pockets (up to ~19 s) of the previous clean_timesync_v2
render WITHOUT touching teacher audio, manifests, or any other lesson, and WITHOUT
swapping the video source.

Adapted verbatim from the quality-gated script:
  essence_of_calculus/lesson_08_integration/dubbing_pipeline/experiments/
  clean_timesync_v2/build_calc08_clean.py
and specialised for lesson_07 as follows:

  1. Cue source = the lesson_07 AUDIO MANIFEST (read-only), alias-deduped:
        web_platform/assets/audio/calculus/lesson_07/manifest.json
     30 cues across 4 sections. The manifest cue texts ARE the dubbing script.
  2. HEAVY EXPANSION: every cue is appended with a long, contextual, pedagogically
     meaningful Bengali paragraph (EXPANSIONS[i], ~300-450 chars each), roughly
     doubling/tripling the total narration. This is real teaching content, not filler.
  3. RECOMPUTE SCALE FROM RENDERED SPEECH (the key change vs. clean v2): after all
     expanded cues are synthesised, their MEASURED natural durations are summed and
     the timeline scale is recomputed as
         scale = (video - lead_in - tail_margin - pauses) / sum(rendered_speech)
     clamped to [1/MAX_TEMPO, 1/TEMPO_FLOOR]. Every cue window then equals its own
     rendered speech * scale, so tempo = 1/scale fills the window almost perfectly.
  4. Fill gate: median_fill >= 0.72 AND max_internal_gap_s <= 1.5s, plus an
     independent silencedetect check that no INTERNAL silence run exceeds 2 s.
  5. Absolute sample placement (start*44100) -> zero cumulative drift; pad only,
     never truncate; atempo fit in [0.82, 2.2]; NO SFX (clean speech only).
  6. Canvas padded to the FULL original video duration so -shortest cannot trim frames.
  7. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy (video src unchanged).

Everything is written under NEW experiment folders. The previous video
  web_platform/media_vault/calculus/lesson_07/experiments/3b1b_calculus_07_full_dubbed.mp4
is left untouched as a backup.
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
BASE = EXP.parent.parent                        # .../lesson_07_limits_lhopital/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
MANIFEST = WEB / "assets" / "audio" / "calculus" / "lesson_07" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "calculus" / "lesson_07" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "calculus" / "lesson_07" / "experiments" / "fill_v2" / "3b1b_calculus_07_full_dubbed_fill2.mp4"
BACKUP_VIDEO = WEB / "media_vault" / "calculus" / "lesson_07" / "experiments" / "3b1b_calculus_07_full_dubbed.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
TEMPO_FLOOR = 0.82
FADE_MS = 12
VIDEO_ID = "kfF40MiS7zA"
LESSON = "lesson_07_limits_lhopital"

# Silence margins: keep 0-2.5 s and the final ~3 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 300.0

# Safety-net expansion threshold (should never trigger after scale-from-rendered).
EXPAND_THRESHOLD_RATIO = 0.85

# Scale band implied by the tempo limits: tempo = 1/scale must be in [0.82, 2.2].
SCALE_MIN = 1.0 / MAX_TEMPO        # 0.4545...
SCALE_MAX = 1.0 / TEMPO_FLOOR      # 1.2195...

# HEAVY, contextual, cue-specific pedagogical expansions. Keyed by global cue id (1-30),
# following the 30 manifest cues in section order.
EXPANSIONS = {
    1: (" আসুন প্রথমেই এই প্রশ্নটি স্থাপন করি: অন্তরজ মানেই কী? আমরা যখন বলি কোনো ফাংশনের ঢাল "
        "বা পরিবর্তনের হার, তখন আসলে একটা নির্দিষ্ট বিন্দুর কাছ থেকে শুরু করে চলের অদলবদল পর্যবেক্ষণ করি। "
        "এই পাঠে আমরা দেখব কীভাবে সেই পর্যবেক্ষণকেই লিমিট নামক একটি সুশৃঙ্খল ভাষায় অনুবাদ করা যায়। "
        "লিমিট ছাড়া ডি এফ বাই ডি এক্সের অর্থ অসম্পূর্ণ থেকে যায়, আর লিমিট নিলেই সেই অসম্পূর্ণতা দূর হয়। "
        "তাই আজকের আলোচনার কেন্দ্রে রয়েছে এই একটিমাত্র ধারণা—কাছে আসা, কিন্তু কখনোই পৌঁছে না যাওয়া।"),
    2: (" এই উদ্ধৃতিটি ক্যালকুলাসের সারমর্ম ধরে দেয়। বাঁকা জিনিসকে সোজা দেখানো মানে হলো, খুব ছোট "
        "পরিসরে একটি বক্ররেখাকে আমরা একটি সরলরেখা হিসেবে বিবেচনা করতে পারি। ছোট থেকে ছোটতর পরিসরে "
        "এই সরলীকরণ আরও নিখুঁত হয়। প্রশ্ন উঠতে পারে, কত ছোট পরিসর যথেষ্ট? আপাতত আমরা বলি, যতক্ষণ "
        "আমরা শূন্যের কাছে এগিয়ে যাই, ততক্ষণই এই সোজা করার প্রক্রিয়া চলতে থাকে। এই ধারণাটিই পরে "
        "স্পর্শক ও লিমিটের ভাষায় রূপ নেবে।"),
    3: (" আরও একটু খোলাসা করে বলি: ইনপুটে একটু নাড়া দেওয়া মানে আমরা মূল বিন্দু থেকে সামান্য সরে "
        "অন্য একটি বিন্দুতে যাই। সেই নতুন বিন্দুতে ফাংশনের মান কতটা বদলাল, তা উপরে লেখা হয় ডেল্টা "
        "এফ। আর সামান্য যে দূরত্ব অতিক্রম করেছি, তা নিচে ডেল্টা এক্স। এই দুটির ভাগই হলো গড় ঢাল। "
        "ছবির রাইজ ওভার রান ঠিক এই ভাগফলেরই দৃশ্যমান রূপ। যখন ডেল্টা এক্স ছোট হতে থাকে, এই গড় "
        "ঢাল ধীরে ধীরে তাৎক্ষণিক ঢালের কাছে এগিয়ে যায়।"),
    4: (" এই অস্বস্তিটি ক্যালকুলাসের ইতিহাসে অনেক দিন ধরেই ছিল। শূন্য দিয়ে ভাগ করা নিষিদ্ধ, কিন্তু "
        "অন্তরজ বের করার শেষ ধাপে তো আমাদের ঠিক সেটাই করতে হয়। আবার যদি ডি এক্স কে শূন্য না করি, "
        "তবে হিসাবের মধ্যে যে বাড়তি ডি এক্স পদ থেকে যায়, তাকে কোন যুক্তিতে বাদ দেব? এই দ্বিধার "
        "সমাধানই হলো লিমিট। লিমিট আমাদের শূন্য দিয়ে ভাগ না করেই শূন্যের কাছাকাছির আচরণ পড়তে "
        "শেখায়। এই প্রশ্নটি আমাদের পুরো পাঠের মোড় নির্ধারণ করে।"),
    5: (" চিত্রটির দিকে একটুক্ষণ তাকাই। লাল বিন্দুটি আমাদের নির্দিষ্ট বিন্দু, আর হলুদ ভাঙা রেখাটি "
        "দুটি বিন্দু দিয়ে যাওয়া ছেদক। ডি এক্স ছোট করলে ছেদকের দ্বিতীয় বিন্দুটি লাল বিন্দুর কাছে "
        "এসে পড়ে এবং ছেদক ধীরে ধীরে সবুজ স্পর্শকের সাথে মিলে যায়। কিন্তু আমরা কখনোই দ্বিতীয় "
        "বিন্দুটিকে লাল বিন্দুর ওপর স্থাপন করি না। এই কাছে এসে পৌঁছানোর অথচ কখনো না পৌঁছানোর "
        "প্রক্রিয়াটিই লিমিট। ছেদকের ঢালের সীমাস্থ মানই হলো স্পর্শকের ঢাল, আর সেটাই আমাদের "
        "অন্তরজ।"),
    6: (" লিমিটের এই সংজ্ঞায় একটা সুন্দর কৌশল লুকিয়ে আছে। আমরা বিন্দুটিতে ফাংশনের মান দেখি না, "
        "বরং বিন্দুর দুই পাশ থেকে আসা আউটপুটের গন্তব্য দেখি। ফলে বিন্দুটিতে ফাংশনের মান থাকুক বা "
        "না থাকুক, লিমিটের অস্তিত্ব নির্ভর করে শুধুমাত্র কাছাকাছির আচরণের ওপর। এই কারণেই "
        "ক্যালকুলাস অযৌক্তিকতা থেকে মুক্তি পায়। আমরা শূন্য দিয়ে ভাগ না করেই একটি নির্দিষ্ট "
        "উত্তরে পৌঁছাই। মনে রাখবেন, লিমিট হলো একটি প্রক্রিয়া, কোনো স্থির সংখ্যা নয়।"),
    7: (" দ্বিতীয় পরিচ্ছেদে আমরা আগের অস্পষ্ট ধারণাকে একটি দৃঢ় সংজ্ঞায় রূপ দেব। আগে আমরা ডি এক্স "
        "বলতাম, এখন বলব এইচ। এই সূত্রটি শুধু একটি নাম বদল নয়; এটি আমাদের চিন্তাভাবনাকে সুশৃঙ্খল "
        "করে। প্রথমে আমরা একটি সসীম, নির্দিষ্ট এইচ বেছে নিই, তারপর হিসাব করি, এবং সবশেষে এইচকে "
        "শূন্যের দিকে পাঠাই। এই তিন ধাপের ক্রম কখনোই উল্টানো যাবে না। এই ক্রম মেনে চললেই "
        "শূন্য দিয়ে ভাগের অপ্রয়োজনীয় সমস্যা এড়িয়ে যাওয়া যায়।"),
    8: (" এই অনুপাতটিকে বলা হয় ডিফারেন্স কোশেন্ট। এখানে উপের অংশ হলো উচ্চতার পরিবর্তন আর "
        "নিচের অংশ হলো অনুভূমিক দূরত্ব। আমরা প্রথমে এইচ কে একটি সাধারণ সংখ্যা ধরে হিসাব করি, "
        "যেমন শূন্য দশমিক শূন্য এক। তখন ভাগটা সম্পূর্ণ বৈধ। এরপর আমরা দেখি এইচ কে ছোট ছোট "
        "করে আনলে ভাগফল কোন মানের কাছে স্থিতিশীল হয়। এই স্থিতিশীল মানটিই হলো বিন্দুটিতে "
        "ফাংশনের অন্তরজ।"),
    9: (" ঐতিহাসিক কারণে লেখকেরা ডি এক্স লিখতেন, কিন্তু আনুষ্ঠানিক সংজ্ঞায় ডেল্টা এক্স বা কেবল "
        "এইচ লেখা হয়। ডি অক্ষরটিকে অসীম ক্ষুদ্রের রহস্যময় অর্থ দেওয়ার কোনো প্রয়োজন নেই। "
        "গুরুত্বপূর্ণ হলো এইচ শূন্য নয়, বরং শূন্যের দিকে অগ্রসরমান একটি সাধারণ বাস্তব সংখ্যা। "
        "নামের এই পার্থক্যে কোনো গাণিতিক পরিবর্তন আসে না। একই নাড়া, একই অনুপাত, একই সীমা—"
        "শুধু লেখার রীতি আলাদা।"),
    10: (" ছবিতে দুটি সবুজ বিন্দুর মাঝে হলুদ অনুভূমিক রেখা হলো এইচ, আর খাড়া রেখা হলো দুই "
         "বিন্দুতে ফাংশনের মানের পার্থক্য। সাদা তির্যক রেখাটি এই দুই বিন্দু দিয়ে যাওয়া ছেদক, "
         "যার ঢাল ঠিক আমাদের অনুপাত। এইচ ছোট হলে ত্রিভুজটি সঙ্কুচিত হয়, কিন্তু তার আকৃতি "
         "অপরিবর্তিত থাকে, ফলে ঢালও প্রায় একই থাকে। এই স্থিরত্বই আমাদের বিশ্বাস দেয় যে "
         "একটি নির্দিষ্ট অন্তরজ আছে।"),
    11: (" এই সূত্রটিই ক্যালকুলাসের অন্যতম গুরুত্বপূর্ণ সংজ্ঞা। এখানে কোথাও অসীম ক্ষুদ্র বলা নেই, "
         "শুধু বলা আছে এইচ শূন্যের কাছে পাঠালে ভাগফল যে মানে স্থিতিশীল হয়, তাই এফ প্রাইম "
         "অফ এক্স। সীমা চিহ্নের অর্থ হলো আমরা এইচ কে কখনো শূন্য করি না, শুধু শূন্যের দিকে "
         "নিয়ে যাই। এই সূক্ষ্ম পার্থক্যটি বুঝতে পারলেই অন্তরজের সংজ্ঞা সহজ হয়ে যায়।"),
    12: (" একটি উদাহরণ দিয়ে দেখি। এফ অফ টি সমান টি কিউব, অর্থাৎ টির ঘন। টি সমান দুই বিন্দুতে "
         "অনুপাতটি হিসাব করলে দেখা যায় তিন গুণ দুইয়ের বর্গ, অর্থাৎ বারো। আগের অধ্যায়ে আমরা "
         "এই বারোটিই অন্তরজ হিসেবে পেয়েছিলাম। নতুন সংজ্ঞা আর পুরোনো হিসাবের এই মিলন আমাদের "
         "বিশ্বাসকে দৃঢ় করে। এখানে কোনো রহস্যময় অসীম ক্ষুদ্র নেই, শুধু একটি সসীম নাড়া এবং "
         "তার সীমা।"),
    13: (" ডেল্টা এক্স, এইচ আর ডি এক্স—একই কথার তিন রূপ। এগুলো সবই একই ধারণার ভিন্ন পোশাক। "
         "পার্থক্য শুধু ঐতিহ্য ও লেখার সুবিধার, গাণিতিক সারমর্ম অপরিবর্তিত। কোনোটি দিয়ে লিখলেই "
         "হিসাবের ফল একই আসবে। মনে রাখবেন, একটি সসীম নাড়া নেওয়া, অনুপাত বের করা, তারপর "
         "সীমা নেওয়া—এই তিন ধাপই আসল কথা। বাকিটা কেবল প্রতীকের ব্যাপার।"),
    14: (" তৃতীয় পরিচ্ছেদে আমরা সেই ভুল বোঝাবুঝিটির মোকাবেলা করব, যা অনেক শিক্ষার্থীকে বিভ্রান্ত "
         "করে। অনেকেই মনে করেন ক্যালকুলাস অসীম ক্ষুদ্র নামক কোনো রহস্যময় সংখ্যার ওপর দাঁড়িয়ে। "
         "কিন্তু আনুষ্ঠানিক সংজ্ঞায় এমন কোনো জিনিস নেই। আমরা দেখব কীভাবে এইচ একটি একেবারে "
         "সাধারণ বাস্তব সংখ্যা হতে পারে, এবং সীমা কীভাবে তার ওপর ভিত্তি করে কাজ করে।"),
    15: (" বিশপ জর্জ বার্কলে অসীম ক্ষুদ্র নিয়ে তীক্ষ্ণ কটাক্ষ করেছিলেন। তাঁর মতে এগুলো ছিল "
         "বিদায়ী রাশির প্রেতাত্মা—নেই, আবার আছে। এই সমালোচনা ঐতিহাসিক দিক থেকে গুরুত্বপূর্ণ, "
         "কারণ এটি দেখিয়ে দেয় যে অসীম ক্ষুদ্র নিয়ে কাজ করা কতটা বিপজ্জনক হতে পারে। ক্যালকুলাসের "
         "উত্তর ছিল লিমিট। সসীম সংখ্যা নিয়ে হিসাব শেষ করে তারপর সীমা নেওয়ার এই পদ্ধতি "
         "সমালোচনার সব অস্ত্র একে একে কেড়ে নেয়।"),
    16: (" এইচ হলো একেবারে সাধারণ, বাস্তব সংখ্যা, যেমন শূন্য দশমিক শূন্য শূন্য এক। আপনি "
         "ক্যালকুলেটরে বসিয়ে দেখতে পারেন, এফ অফ এক্স প্লাস শূন্য দশমিক শূন্য শূন্য এক বিয়োগ "
         "এফ অফ এক্স, ভাগ শূন্য দশমিক শূন্য শূন্য এক, সত্যিই এফ প্রাইম অফ এক্সের কাছাকাছি। "
         "এখানে কোনো অদৃশ্য অণু সংখ্যা নেই, কোনো রহস্য নেই। শুধু একটি ছোট কিন্তু নির্দিষ্ট "
         "পরিমাপযোগ্য দূরত্ব। এই সরল পর্যবেক্ষণটিই আমাদের পুরো তত্ত্বের ভিত্তি।"),
    17: (" ভুলটা তখন হয় যখন আমরা ডি এক্স কে একই সাথে শূন্য ও অশূন্য ভাবি। আগে ভাগের জন্য "
         "ধরে রাখি, পরে মুছে দিই—এই দ্বিচারিতাই সমস্যার উৎস। লিমিট এই দ্বিচারিতা দূর করে। "
         "প্রথমে এইচ কে সসীম রেখে হিসাব করি, তারপর এইচ শূন্যের দিকে যাচ্ছে বলে সীমা নিই। "
         "কোনো ধাপেই শূন্য দিয়ে ভাগ করা হয় না। পদ্ধতির এই পরিচ্ছন্নতাই আধুনিক ক্যালকুলাসকে "
         "বিশ্বাসযোগ্য করে তুলেছে।"),
    18: (" ছবিতে সংখ্যারেখায় এক্স ও এক্স প্লাস শূন্য দশমিক শূন্য শূন্য এক, এই দুটি বিন্দু "
         "দেখানো হয়েছে। এগুলো আলাদা, পরিমাপযোগ্য দূরত্ব। বড় বিবর্ধক কাঁচটি স্মরণ করিয়ে দেয় "
         "যে আমরা শুধু কাছ থেকে দেখছি, কোনো অদৃশ্য অণু সংখ্যা ব্যবহার করছি না। এইচ সমান "
         "শূন্য দশমিক শূন্য শূন্য এক একটি নির্দিষ্ট, নিরাপদ সংখ্যা, আর সীমা তারপর আসে। "
         "অর্থাৎ প্রথমে হিসাব, পরে সীমা—এই ক্রম কখনো ভাঙা যাবে না।"),
    19: (" এই সূত্রে দুটি ধাপ দেখা যাচ্ছে। প্রথমটিতে আমরা একটি নির্দিষ্ট ছোট সংখ্যা দিয়ে "
         "ভাগ করে আনুমানিক অন্তরজ পাই। দ্বিতীয়টিতে এইচ কে শূন্যের দিকে পাঠিয়ে সেই অনুমানের "
         "সীমাস্থ মান নিই। দুটি ধাপের এই পার্থক্য খুবই গুরুত্বপূর্ণ। প্রথম ধাপে ভগ্নাংশটি "
         "সম্পূর্ণ বৈধ, কারণ নিচের সংখ্যা শূন্য নয়। দ্বিতীয় ধাপে আমরা কোনো ভাগ করি না, "
         "শুধু প্রবণতা পর্যবেক্ষণ করি।"),
    20: (" এই পদ্ধতির সুন্দর দিক হলো ত্রুটিও পরিমাপ করা যায়। এইচ যত ছোট, আনুমানিক ঢালের "
         "শতাংশ ত্রুটি তত কমে। তাই অসীম ক্ষুদ্রের রহস্য না বেঁধেই কাজ চলে, সসীম নাড়া আর "
         "সীমা—এই দুটিই যথেষ্ট। ব্যবহারিক হিসাবেও আমরা যত ছোট এইচ বেছে নিই, ফল তত নিখুঁত "
         "হয়। তবে ত্রুটি কমলেও কখনোই শূন্য হয় না; তাই সীমা আমাদের সেই অসীম কাছাকাছি যাওয়ার "
         "ধারণাটি দেয়।"),
    21: (" আধুনিক গণিতে হাইপাররিয়েল সংখ্যা ব্যবহার করে ইনফিনিটেসিমালকেও সুসংজ্ঞায়িত করা যায়, "
         "বলেছেন অ্যাব্রাহাম রবিনসন। কিন্তু সেটি একটিমাত্র বিকল্প ভাষা, আমাদের জন্য এপসিলন "
         "ডেল্টা ভাষাই যথেষ্ট ও ঝামেলামুক্ত। একাধিক ভাষার অস্তিত্ব মানে এই নয় যে সব ভাষা "
         "একই স্তরে শিখতে হবে। আমরা সেই পথ বেছে নিই যা সরল ও নির্ভরযোগ্য। পরবর্তী অধ্যায়ে "
         "আমরা সেই কঠোর ভাষারই সাথে পরিচিত হব।"),
    22: (" চতুর্থ পরিচ্ছেদে আমরা এক ধাপ পিছিয়ে গিয়ে জিজ্ঞেস করব, কেন আমরা এত খাটাখাটুনি করছি? "
         "অন্তরজের সংজ্ঞা নিয়ে এত কষ্ট করার কারণ কী? এর উত্তর পরবর্তী অধ্যায়ে লুকিয়ে আছে। "
         "আজ আমরা দেখব কীভাবে এই সাধারণ বুদ্ধিকে লিখিত রূপ দেওয়া যায়। এই প্রশ্নের সাথে "
         "সাথে আমরা বুঝতে পারব যে লিমিট কোনো অতিরিক্ত যন্ত্রপাতি নয়, বরং আমাদের দৈনন্দিন "
         "উপলব্ধিরই একটি সুশৃঙ্খল রূপ।"),
    23: (" গ্রান্ট স্যান্ডারসনের এই উদ্ধৃতিটি আজকের পাঠের চাবিকাঠি। যথেষ্ট কাছ থেকে দেখলে "
         "বক্ররেখা সোজা লাগে—এই সরল পর্যবেক্ষণের পেছনে রয়েছে গভীর গাণিতিক তত্ত্ব। অন্তরজ "
         "আমাদের বলে দেয় বক্ররেখাটি ঠিক কেমন দেখায় যখন আমরা তা যথেষ্ট কাছ থেকে দেখি। "
         "জুমের এই ধারণাটি শুধু দৃশ্যমান সাহায্য নয়; এটি আমাদের সীমার ধারণাটি বুঝতে "
         "সাহায্য করে। যত কাছে যাই, বক্রতা তত কমে যায়।"),
    24: (" ই পাওয়ার এক্স বক্ররেখার এক্স সমান শূন্য বিন্দুতে বারবার জুম করলেই দেখা যায় বক্রতা "
         "কমে যাচ্ছে এবং স্পর্শকের ঢাল আসছে একের কাছে। এই একের মান ঠিক সেখানকার ফাংশনের "
         "মানের মতোই। কেন এমন হয়? কারণ ই পাওয়ার এক্স ফাংশনের বিশেষত্ব হলো এর অন্তরজ নিজের "
         "সমান। শূন্য বিন্দুতে ফাংশনের মান এক, তাই ঢালও এক। এই উদাহরণটি আমাদের দেখায় "
         "কীভাবে জুম করে বক্ররেখার আচরণ পড়া যায়।"),
    25: (" কতদূর জুম করা দরকার? ব্যবহারিক প্রকৌশলী বলবেন, যতক্ষণ ত্রুটি সহনশীলতার ভেতরে "
         "থাকে, ততক্ষণই যথেষ্ট। এটা যথার্থতার খেলা। গণিতবিদ চাইবেন একটি নিখুঁত উত্তর। তাঁর "
         "প্রশ্ন হলো, প্রতিটি চ্যালেঞ্জের ব্যবধান এপসিলনের জন্য এমন এক ডেল্টা আছে কি? এই "
         "প্রশ্নের উত্তরই পরবর্তী অধ্যায়ের এপসিলন ডেল্টা সংজ্ঞা। আমরা শিখব কীভাবে সহনশীলতা "
         "ও দূরত্বের এই সম্পর্ককে নিখুঁত ভাষায় লেখা যায়।"),
    26: (" চিত্রে ই পাওয়ার এক্স বক্ররেখার এক্স সমান শূন্য বিন্দুটিকে ঘিরে দুটি জুম বক্স দেখা "
         "যাচ্ছে। সবুজ স্পর্শকের ঢাল এক, আর হলুদ বৃত্তাকার অংশ বাড়ালে বক্ররেখা সরলরেখার "
         "মতো দেখায়। মনে রাখবেন জুম কেবল দৃশ্যমান সাহায্য, আর সীমা হলো তার নিখুঁত গাণিতিক "
         "রূপ। ছবি আমাদের অনুভূতি দেয়, কিন্তু সীমা আমাদের নিশ্চয়তা দেয়। এই দুয়ের মিলনই "
         "ক্যালকুলাসের শক্তি।"),
    27: (" এই সূত্রটি বলে যে হ দিয়ে ভাগ করা আরেকটি পরিচিত সীমা। হ শূন্যের দিকে গেলে ই পাওয়ার "
         "হ বিয়োগ এক, ভাগ হ, তার মান দাঁড়ায় এক। আগে আমরা এটি ছেদকের ঢাল হিসেবে দেখেছি, "
         "এখন সীমা হিসেবে লিখছি। একই সত্যকে দুই ভাষায় বলা হলো। পরবর্তী পাঠে আমরা এই সীমাটিকে "
         "ব্যবহার করে ই পাওয়ার এক্সের অন্তরজ বের করব।"),
    28: (" পরবর্তী পর্বে আমরা এই কাছে আসাকে সংখ্যায় বাঁধব। এক্স মাইনাস এ এর পরিমাপ ডেল্টার "
         "চেয়ে ছোট হলে, এফ অফ এক্স মাইনাস এলের পরিমাপ এপসিলনের চেয়ে ছোট হবে। অর্থাৎ ইনপুট "
         "যত কাছে আসবে, আউটপুট তত নির্দিষ্ট লক্ষ্যের ভেতরে পড়বে। এপসিলন হলো আউটপুটের "
         "সহনশীলতা আর ডেল্টা হলো ইনপুটের অনুমতিপ্রাপ্ত দূরত্ব। এই দুটির সম্পর্কই লিমিটের "
         "পূর্ণ কঠোরতা জন্ম দেবে।"),
    29: (" একটু ভেবে দেখুন: আপনি ইতিমধ্যেই বুঝেছেন বক্ররেখা কাছ থেকে সোজা হয়। এপসিলন ডেল্টা "
         "শুধু সেই বোঝাপড়ার হিসাববই। কোনো নতুন যুক্তি বা অদ্ভুত যন্ত্র এখানে নেই। আপনার "
         "সাধারণ বুদ্ধিকে লিখিত রূপ দেওয়াই হয়েছে। তাই ভয় পাবেন না—পরবর্তী অধ্যায়ের কঠোর "
         "সংজ্ঞা আপনার অজানা কোনো জিনিস বলবে না, শুধু আপনার জানা জিনিসটিকে আরও নিখুঁতভাবে লিখবে।"),
    30: (" শেষ কথা হিসেবে মনে রাখবেন, লিমিট কোনো অতিরিক্ত যন্ত্রপাতি নয়। এটি আমাদের সাধারণ "
         "বুদ্ধিকেই লিখিত রূপ দেয়। আপনি ইতিমধ্যেই বুঝেছেন বক্ররেখা কাছ থেকে সোজা হয়, "
         "এপসিলন ডেল্টা শুধু সেই বোঝাপড়ার হিসাববই। আজ আমরা দেখলাম কীভাবে শূন্য দিয়ে ভাগ "
         "না করেই অন্তরজের একটি দৃঢ় সংজ্ঞা তৈরি করা যায়। পরবর্তী পাঠে আমরা সেই কাছে আসাকে "
         "এপসিলন ও ডেল্টার ভাষায় সম্পূর্ণরূপে বাঁধব। আবার দেখা হবে!"),
}

# Generic pedagogical fallback pool (only used if a cue still needs more fill).
GENERIC_EXTRA = (
    " এখানে একটু থামুন এবং বিষয়টি নিজের ভাষায় বলে দেখুন। কোনো ধারণা তখনই পোক্ত হয় যখন আপনি "
    "সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন। একই ধারণা একাধিক উদাহরণে দেখলে তার "
    "গভীরতা আরও বাড়ে। এই অভ্যাস আপনার বোঝাপড়াকে আরও মজবুত করবে।"
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
    """Read the read-only lesson_07 audio manifest (alias-deduped)."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    seen_aliases = set()
    out = []
    for sec_key, sec in data.get("sections", {}).items():
        alias = sec.get("alias") or sec.get("section_id") or sec_key
        if alias in seen_aliases:
            continue
        seen_aliases.add(alias)
        for c in sec.get("cues", []):
            text = (c.get("text") or "").strip()
            if not text:
                continue
            out.append({
                "text": text,
                "dur_ms": float(c.get("duration_ms", 0)),
                "section": alias,
                "src_index": c.get("index"),
            })
    return out


def build_expanded_cues(source_cues):
    """Attach a heavy contextual expansion to every manifest cue."""
    cues = []
    for i, s in enumerate(source_cues):
        cid = i + 1
        extra = EXPANSIONS.get(cid, GENERIC_EXTRA)
        cues.append({
            "id": cid,
            "bn": sanitize(s["text"] + " " + extra),
            "section": s["section"],
            "authored_dur_ms": s["dur_ms"],
        })
    return cues


def layout_from_rendered(cues, naturals, vend):
    """Recompute the timeline scale from MEASURED rendered speech durations.

    Each cue window = natural_speech * scale, so tempo = 1/scale fills it.
    """
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    pauses = INTER_CUE_PAUSE_MS / 1000.0 * (len(cues) - 1)
    rendered_total = sum(naturals)
    raw_scale = (usable - pauses) / rendered_total if rendered_total > 0 else 1.0
    scale = max(SCALE_MIN, min(SCALE_MAX, raw_scale))
    cursor = LEAD_IN_SEC
    for c, nat in zip(cues, naturals):
        dur = nat * scale
        c["start"] = round(cursor, 3)
        c["duration"] = round(dur, 3)
        c["end"] = round(cursor + dur, 3)
        c["natural_sec"] = round(nat, 3)
        cursor += dur + INTER_CUE_PAUSE_MS / 1000.0
    return scale, raw_scale


async def synth_all(cues):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, c in enumerate(cues):
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        ok = await synth(c["bn"], raw)
        if not ok:
            failed.append(c["id"])
            print(f"  WARNING cue {c['id']} failed after every fallback", flush=True)
        if (i + 1) % 10 == 0:
            print(f"  TTS {i+1}/{len(cues)}", flush=True)
    return failed


async def expand_short_cues(cues):
    """Safety net: only triggers if a rendered cue still under-fills its window."""
    expanded = []
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            continue
        target = float(c["duration"])
        if cid == LAST_ID:
            target = min(target, VIDEO_END - LAST_START - 0.10)
        natural = duration(raw)
        if natural <= 0 or natural >= EXPAND_THRESHOLD_RATIO * target:
            continue
        original_natural = natural
        base_text = c["bn"]
        added = []
        for attempt in range(3):
            natural = duration(raw)
            if natural >= EXPAND_THRESHOLD_RATIO * target:
                break
            extra = GENERIC_EXTRA
            new_text = sanitize(base_text + " " + " ".join(added) + " " + extra)
            print(f"  fill-expand cue {cid} pass {attempt+1}: "
                  f"natural={natural:.2f}s < {EXPAND_THRESHOLD_RATIO*target:.2f}s", flush=True)
            if not await synth(new_text, raw, force=True):
                break
            added.append(extra)
        expanded.append({
            "id": cid,
            "natural_before": round(original_natural, 3),
            "natural_after": round(duration(raw), 3),
            "target_sec": round(target, 3),
            "passes": len(added),
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
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
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


def internal_silence_runs(path, vend):
    """Independent silencedetect gate: count INTERNAL silence runs longer than 2 s."""
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
           "-af", "silencedetect=noise=-35dB:d=2", "-f", "null", "-"]
    for attempt in range(6):
        try:
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            txt = r.stderr
            break
        except OSError as e:
            if not is_win1450(e):
                raise
            txt = ""
            time.sleep(0.5 * (attempt + 1))
    starts = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", txt)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([\d.]+)", txt)]
    all_runs = []
    used = set()
    for s in starts:
        e = next((k for k, x in enumerate(ends) if x >= s and k not in used), None)
        if e is None:
            continue
        used.add(e)
        all_runs.append((round(s, 3), round(ends[e], 3), round(ends[e] - s, 3)))
    internal = [r for r in all_runs if r[0] > LEAD_IN_SEC and r[1] < vend - 1.0]
    return {
        "all_silence_runs": all_runs,
        "internal_silence_runs": internal,
        "internal_runs_over_2s": sum(1 for r in internal if r[2] > 2.0),
    }


async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    source_cues = load_manifest_cues()
    cues = build_expanded_cues(source_cues)
    print(f"video duration = {vend:.3f}s; manifest cues = {len(cues)} "
          f"(alias-deduped); heavily expanded chars = {sum(len(c['bn']) for c in cues)}",
          flush=True)

    print("[1/7] TTS of heavily expanded cues (clean, no SFX) ...", flush=True)
    failed = await synth_all(cues)

    naturals = [duration(RAW_DIR / f"raw_{c['id']:03d}.mp3") for c in cues]
    rendered_total = sum(naturals)
    scale, raw_scale = layout_from_rendered(cues, naturals, vend)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"  rendered speech total = {rendered_total:.3f}s; raw_scale = {raw_scale:.4f}; "
          f"clamped scale = {scale:.4f} (band [{SCALE_MIN:.4f}, {SCALE_MAX:.4f}])", flush=True)

    print("[2/7] Safety-net fill expansion ...", flush=True)
    fill_expanded = await expand_short_cues(cues)
    # Re-measure in case the safety net re-synthesised anything.
    naturals = [duration(RAW_DIR / f"raw_{c['id']:03d}.mp3") for c in cues]
    scale, raw_scale = layout_from_rendered(cues, naturals, vend)

    print("[3/7] Absolute sample placement (start*44100, pad-only, scale-from-rendered) ...", flush=True)
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    fills = []
    internal_gaps = []
    overrun = 0
    last_cue_end = 0.0
    expanded_ids = {x["id"] for x in fill_expanded}
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
        placed_len = int(round(end - start_sample))
        last_cue_end = max(last_cue_end, end / SR)
        expected_ms = round(float(c["start"]) * 1000, 2)
        actual_ms = round(start_sample / SR * 1000, 2)
        placed.append({
            "id": cid,
            "section": c["section"],
            "expected_start_ms": expected_ms,
            "actual_start_ms": actual_ms,
            "drift_ms": round(actual_ms - expected_ms, 6),
            "tempo": info["tempo"],
            "natural_sec": info["natural"],
            "target_sec": info["target"],
            "fill_ratio": info["fill_ratio"],
            "internal_gap_s": info["internal_gap_s"],
            "placed_samples": placed_len,
            "expanded": cid in expanded_ids,
        })

    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    max_internal_gap_s = round(max(internal_gaps), 4) if internal_gaps else 0.0
    print(f"  median_fill = {median_fill} ; max_internal_gap_s = {max_internal_gap_s}", flush=True)

    CHUNK = 1_000_000
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
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)

    print("[5/7] Mux with FULL original video (video copy, source unchanged) ...", flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    print("[6/7] Independent silencedetect gate (>2 s internal runs) ...", flush=True)
    sil = internal_silence_runs(OUT_VIDEO, vend)

    print("[7/7] Verification report ...", flush=True)
    report = {
        "experiment": "fill_v2 — heavy expansion + scale-from-rendered (calculus_lesson_07)",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": f"audio_manifest:{MANIFEST.name} (alias-deduped, 30 cues, heavily expanded)",
        "video_source": str(ORIGINAL_VIDEO),
        "backup_video_untouched": str(BACKUP_VIDEO),
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": ("absolute sample offset (start*44100); scale recomputed from rendered "
                     "speech; atempo fit in [0.82,2.2]; pad only; no truncation"),
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "tempo_floor": TEMPO_FLOOR,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "rendered_speech_total_sec": round(rendered_total, 3),
        "timeline_scale_raw": round(raw_scale, 6),
        "timeline_scale": round(scale, 6),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "median_fill": median_fill,
        "max_internal_gap_s": max_internal_gap_s,
        "fill_policy_target": "median_fill >= 0.72 and max_internal_gap_s <= 1.5",
        "fill_policy_met": bool(median_fill >= 0.72 and max_internal_gap_s <= 1.5),
        "fill_expansions_applied": fill_expanded,
        "silencedetect": sil,
        "silencedetect_gate_met": bool(sil["internal_runs_over_2s"] == 0),
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
    print(f"median_fill={median_fill} max_internal_gap_s={max_internal_gap_s} "
          f"fill_policy_met={report['fill_policy_met']}", flush=True)
    print(f"silencedetect internal_runs_over_2s={sil['internal_runs_over_2s']} "
          f"gate_met={report['silencedetect_gate_met']}", flush=True)
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
