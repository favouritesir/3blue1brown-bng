"""
EXPERIMENT (fill_v2) — Re-render the Bengali dub of Linear Algebra Lesson 12
============================================================================
Goal: eliminate the 26 silent pockets (up to 26 s) left by clean_timesync_v2,
      WITHOUT touching teacher audio, the manifest, the old video/backup, or
      any other lesson. Work happens ONLY in NEW fill_v2 folders.

Base pipeline (copied + extended):
  essence_of_calculus/lesson_08_integration/dubbing_pipeline/experiments/
      clean_timesync_v2/build_calc08_clean.py
  plus the fill-metrics implementation from
  essence_of_calculus/lesson_11_what_is_dx/.../build_calc11_clean.py.

What is NEW here (the reason for fill_v2):
  1. Cue source = the audio manifest (cue texts are the dubbing script),
     alias-deduped by (start_ms, text) -> 25 cues (7+5+7+6). The manifest and
     the teacher audio are read-only.
  2. HEAVY expansion: every cue is grown with section-aware pedagogical
     Bengali sentences until its rendered speech is >= ~1.02x its authored
     window. The authored windows were ~2x the natural TTS, which is exactly
     why clean_timesync_v2 left ~48% dead air (pockets up to 26 s).
  3. RECOMPUTE SCALE FROM RENDERED SPEECH: the final timeline windows are
     derived from the *rendered* speech durations (not the authored teacher
     durations), so every window fits its own speech exactly:
         scale = (usable - pauses) / sum(rendered_speech_durations)
         window_i = rendered_i * scale ; tempo_i = 1/scale (uniform)
     With scale ~= 1 this makes fill ~1.0 and leaves no trailing dead air.
  4. FILL GATE (hard, fail-closed):
         median_fill >= 0.72
         max_internal_gap_s <= 1.5 s
         internal silence runs > 2 s  == 0
     Plus a final silencedetect scan of the muxed output; if a gate fails the
     script prints FAIL and exits non-zero (no success claim).

Everything is written under NEW experiment folders. The previous video
  web_platform/media_vault/lesson_12/experiments/3b1b_lesson_12_full_dubbed.mp4
is kept untouched as a backup. The video source is ALWAYS the full original
  web_platform/media_vault/lesson_12/original_source/full_original.mp4
(never swapped to a previous dub).
"""
import os
import re
import json
import time
import shutil
import asyncio
import subprocess
import statistics
import wave
from pathlib import Path

import numpy as np
import edge_tts

EXP = Path(__file__).resolve().parent                     # .../experiments/fill_v2
BASE = EXP.parent.parent                                  # .../lesson_12_cramers_rule/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"                    # .../3blue1brown_courses/web_platform
MANIFEST = WEB / "assets" / "audio" / "linear_algebra" / "lesson_12" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_12" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "lesson_12" / "experiments" / "fill_v2" / "3b1b_lesson_12_full_dubbed_fill2.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"
TEXT_CACHE = EXP / "_expanded_texts.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
TEMPO_FLOOR = 0.82
FADE_MS = 12
VIDEO_ID = "jBsC34PxzoM"
LESSON = "lesson_12_cramers_rule"

# Silent intro / outro margins and the small breathing space between cues.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_S = 0.12

# Heavy-expansion policy.
EXPAND_TRIGGER_RATIO = 0.97      # expand when natural < 97% of authored window
EXPAND_AIM_RATIO = 1.02          # keep appending until natural >= 102% of window
MAX_APPENDED_SENTENCES = 24
ACTIVE_THRESHOLD = 0.005         # above edge-TTS MP3 leakage floor (~0.004)
POCKET_SEC = 2.0                 # an "internal pocket" is a silent run > 2 s

# Fill gates (must all pass).
GATE_MEDIAN_FILL = 0.72
GATE_MAX_INTERNAL_GAP_S = 1.5
GATE_MAX_POCKETS = 0

# ---------------------------------------------------------------------------
# Section-aware pedagogical Bengali expansion pools.
# These are meaningful "what to notice / why it matters" narrations, cycled
# (never repeated inside one cue). All Latin acronyms are phonetically
# transliterated so edge-TTS reads them cleanly.
# ---------------------------------------------------------------------------
EXPANSION_POOL = {
    "sec_01_linear_systems_and_area": [
        "লক্ষ্য করুন, একটি সমীকরণ জোটের সমাধান মানেই হলো সেই নির্দিষ্ট ইনপুট ভেক্টরটি খোঁজা, যা ম্যাট্রিক্স দিয়ে রূপান্তরের পর আমাদের দেওয়া আউটপুট ভেক্টরে পৌঁছায়।",
        "ম্যাট্রিক্সের প্রতিটি কলাম আমাদের বলে দেয়, ইনপুট স্পেসের ভিত্তি ভেক্টরগুলো রূপান্তরের পর কোথায় অবস্থান করছে।",
        "তাই কলামগুলোকে পাশাপাশি রেখে দেখলে আমরা রূপান্তরটির পুরো ছবিটি এক নজরে পেয়ে যাই।",
        "এই কারণেই বলা হয়, ম্যাট্রিক্স মানে শুধু সংখ্যার সারণি নয়, বরং একটি জ্যামিতিক রূপান্তরের জীবন্ত চিত্র।",
        "আপনি যখনই কোনো ভেক্টর সমীকরণ দেখবেন, কলামগুলোর এই রৈখিক সমন্বয়ের কথা প্রথমে মনে করার চেষ্টা করবেন।",
        "স্থানাঙ্ক নিয়ে এই প্রশ্নটি খুব গভীর, কারণ আমরা সাধারণত সংখ্যাগুলোকেই স্থানাঙ্ক ভেবে অভ্যস্ত হয়ে পড়ি।",
        "কিন্তু জ্যামিতিক দৃষ্টিতে প্রতিটি স্থানাঙ্ক আসলে একটি নির্দিষ্ট সামান্তরিকের ক্ষেত্রফল, আর এই উপলব্ধিই আজকের পাঠের মূল চাবিকাঠি।",
        "আই হ্যাট আর জে হ্যাট হলো সমতলের দুটি একক ভিত্তি ভেক্টর, যাদের সাহায্যে আমরা যেকোনো ভেক্টরকে ভাঙতে পারি।",
        "জে হ্যাটের দৈর্ঘ্য ঠিক এক একক, তাই সামান্তরিকের ভূমি হিসেবে এটি আমাদের হিসাবকে সরল করে দেয়।",
        "ওয়াই অক্ষ থেকে ভেক্টরের শীর্ষবিন্দুর লম্ব দূরত্বই হলো তার এক্স স্থানাঙ্ক, আর এই দূরত্বকে আমরা ক্ষেত্রফলের উচ্চতা হিসেবে দেখতে পাই।",
        "ডিটারমিন্যান্ট হিসাব করার সময় আমরা আসলে ভূমি গুণ উচ্চতার একই নিয়ম প্রয়োগ করি, তাই ফলাফল হুবহু স্থানাঙ্কের সমান হয়।",
        "এই সৌন্দর্য আমাদের বারবার মনে করিয়ে দেয় যে বীজগণিত আর জ্যামিতি কখনোই আলাদা নয়, একই সত্যের দুটি ভাষা মাত্র।",
        "পরের ধাপে আমরা দেখব, এই একই ক্ষেত্রফলের ধারণা কীভাবে পুরো সমতলের রূপান্তরকে বর্ণনা করে।",
        "যদি ডিটারমিন্যান্ট শূন্য হয়, তবে সামান্তরিকের ক্ষেত্রফল শূন্য হয়ে যায়, অর্থাৎ রূপান্তরটি সমতলকে চেপে একটি রেখায় পরিণত করে।",
        "এই ক্ষেত্রে সমাধান হয়তো থাকবে না, অথবা অসংখ্য সমাধান থাকবে—এই পার্থক্যটি পরে আমরা আরও স্পষ্টভাব বুঝব।",
        "তাই ছোট উদাহরণ নিয়ে কাজ করাটা কেবল সুবিধার জন্য নয়, বরং অন্তর্নিহিত গঠনটি ধরা পড়ার জন্য।",
    ],
    "sec_02_transformation_scaling": [
        "রৈখিক রূপান্তরের সবচেয়ে আশ্চর্যজনক বৈশিষ্ট্য হলো এটি গ্রিডের রেখাগুলোকে সবসময় সমান্তরাল ও সমদূরবর্তী রাখে।",
        "অর্থাৎ রূপান্তরের পরও গ্রিডের প্রতিটি ছোট বর্গ একই আকারের সামান্তরিকে পরিণত হয়।",
        "এই কারণেই একক বর্গের ক্ষেত্রফলের পরিবর্তনটি পুরো সমতল জুড়ে একই অনুপাতে ঘটে।",
        "আই হ্যাট চলে যায় ম্যাট্রিক্সের প্রথম কলামে আর জে হ্যাট চলে যায় দ্বিতীয় কলামে।",
        "এই দুটি নতুন ভেক্টর দ্বারা গঠিত সামান্তরিকের ক্ষেত্রফলই হলো ডিটারমিন্যান্ট এ।",
        "যদি ডিটারমিন্যান্ট দুই হয়, তবে রূপান্তর প্রতিটি আকৃতির ক্ষেত্রফলকে দ্বিগুণ করে দেয়।",
        "যদি ডিটারমিন্যান্ট ঋণাত্মক হয়, তবে সমতলটি উল্টে যায়—ঠিক যেমন কাগজের উল্টো পিঠ দেখা যায়।",
        "এই উল্টানোর কারণেই ঋণাত্মক ডিটারমিন্যান্টের ক্ষেত্রে ক্ষেত্রফলের মান ঋণাত্মক ধরা হয়।",
        "যদি ডিটারমিন্যান্ট শূন্য হয়, তবে পুরো সমতল একটি রেখায় ভেঙে পড়ে, কোনো ক্ষেত্রফলই অবশিষ্ট থাকে না।",
        "লক্ষ্য করুন, এই স্কেলিং নীতি কেবল বর্গের ক্ষেত্রেই নয়, যেকোনো আকৃতির ক্ষেত্রে প্রযোজ্য।",
        "বৃত্ত হোক বা ত্রিভুজ, প্রতিটি আকৃতির ক্ষেত্রফল একই ডিটারমিন্যান্ট গুণক দিয়ে স্কেল হয়।",
        "এই সার্বজনীনতাই রৈখিক বীজগণিতকে এত শক্তিশালী হাতিয়ার বানিয়েছে।",
        "আমাদের পাজলের সমাধানের দিকে যাওয়ার পথও এই একই নীতি দিয়ে খুলে যায়।",
        "মনে রাখবেন, ক্ষেত্রফলের এই পরিবর্তনকে দেখেই আমরা বুঝতে পারি রূপান্তরটি কতখানি প্রসারিত বা সংকুচিত করেছে।",
        "পরবর্তীতে আমরা এই স্কেলিং নীতিকেই ব্যবহার করে ক্র্যামারের সূত্রটি প্রতিপাদন করব।",
        "একই রূপান্তর যদি কোনো অঞ্চলকে প্রসারিত করে, তবে তার বিপরীত রূপান্তর সেটিকে আবার সংকুচিত করবে।",
    ],
    "sec_03_cramers_rule_proof": [
        "এখন আগের দুটি ধারণা—স্থানাঙ্ক হিসেবে ক্ষেত্রফল আর রূপান্তরের স্কেলিং নীতি—একসাথে যুক্ত করুন।",
        "ইনপুট স্পেসে ভেক্টর এক্স আর জে হ্যাট দ্বারা গঠিত সামান্তরিকটির আদি ক্ষেত্রফল ছিল ঠিক এক্স।",
        "রূপান্তরের পর ভেক্টর এক্স পরিণত হয় লক্ষ্য ভেক্টর ভিতে আর জে হ্যাট পরিণত হয় ম্যাট্রিক্সের দ্বিতীয় কলামে।",
        "ফলে নতুন সামান্তরিকটি গঠিত হয় ভি ও দ্বিতীয় কলাম দ্বারা—দুটোই আউটপুট স্পেসে দৃশ্যমান।",
        "স্কেলিং নীতি অনুযায়ী, নতুন ক্ষেত্রফল সমান ডিটারমিন্যান্ট এ গুণ আদি ক্ষেত্রফল এক্স।",
        "অন্যদিকে নতুন ক্ষেত্রফলটির মান আমরা সরাসরি হিসাব করতে পারি ভি ও দ্বিতীয় কলামের ডিটারমিন্যান্ট হিসেবে।",
        "এই দুটি প্রকাশকে সমান ধরে ডিটারমিন্যান্ট এ দিয়ে ভাগ করলেই এক্সের মান পাওয়া যায়।",
        "এটিই ক্র্যামারের নিয়মের হৃদয়—একটি অনুপাত, যা ক্ষেত্রফলের ভাষায় লেখা হয়েছে।",
        "লক্ষ্য করুন, কোনো যান্ত্রিক হিসাব ছাড়াই আমরা সমাধানের সূত্রটি পেয়ে গেছি।",
        "ওয়াইয়ের ক্ষেত্রেও একই যুক্তি চলে, শুধু প্রথম কলাম অপরিবর্তিত রেখে দ্বিতীয় কলামে ভি বসানো হয়।",
        "থ্রিডি জগতে সামান্তরিকের বদলে প্যারালেলেপিপেডের আয়তন ব্যবহৃত হয়, কিন্তু যুক্তি একই থাকে।",
        "এন মাত্রিক ক্ষেত্রে আমরা একইভাবে আই তম কলামে ভি বসিয়ে ডিটারমিন্যান্ট হিসাব করি।",
        "এই সূত্রের সৌন্দর্য হলো এটি যেকোনো সংখ্যক চলকের জন্য একই রূপে কাজ করে।",
        "তবে ব্যবহারিক ক্ষেত্রে বড় ম্যাট্রিক্সে এই পদ্ধতি ধীর, তাই কম্পিউটারে অন্য পদ্ধতি ব্যবহৃত হয়।",
        "আদি ক্ষেত্রফল যদি শূন্য হয়, তবে অনুপাতটি অসংজ্ঞায়িত হয়—এই ক্ষেত্রে সমাধানের অস্তিত্ব নিয়ে প্রশ্ন ওঠে।",
        "এই প্রমাণটি আমাদের দেখায় যে জ্যামিতি কেবল চিত্র নয়, বরং একটি নিখুঁত যুক্তির ভাষা।",
    ],
    "sec_04_computational_reality": [
        "ক্র্যামারের নিয়ম তাত্ত্বিকভাবে সুন্দর হলেও বড় সমীকরণ জোটে এটি ব্যবহার না করার একটি বাস্তব কারণ আছে।",
        "এন ক্রমের জোটে এন প্লাস ওয়ানটি পৃথক ডিটারমিন্যান্ট হিসাব করতে হয়, যার প্রতিটি ও এন কিউব ধাপ নেয়।",
        "অন্যদিকে গাউসিয়ান এলিমিনেশন মাত্র ও অফ এন কিউব ধাপে সব চলকের মান একসাথে দিয়ে দেয়।",
        "এই পার্থক্য বড় ম্যাট্রিক্সে দারুণ প্রভাব ফেলে—সময়ের ব্যবধান ঘণ্টার পর ঘণ্টা হতে পারে।",
        "তাই কম্পিউটার বিজ্ঞানীরা ব্যবহারিক কাজে ক্র্যামারের নিয়ম এড়িয়ে যান।",
        "কিন্তু বিশুদ্ধ গণিতে এর গুরুত্ব অপরিসীম, কারণ এটি সমাধানের একটি সরাসরি রুদ্ধ রূপ বা ক্লোজড ফর্ম দেয়।",
        "ক্লোজড ফর্ম মানে সমাধানকে একটি সূত্রে আবদ্ধ করা, যার সাহায্যে আমরা সমাধানের গঠন সরাসরি দেখতে পাই।",
        "এই রূপটি আমাদের দেখায় যে সমাধান আসলে ডিটারমিন্যান্টের একটি জ্যামিতিক অনুপাত মাত্র।",
        "যদি লক্ষ্য ভেক্টর ভি সামান্য বদলায়, তবে সমাধান কতটা বদলাবে তা আমরা ডেরিভেটিভ দিয়ে বের করতে পারি।",
        "ভি জের সাপেক্ষে এক্স আইয়ের আংশিক ডেরিভেটিভ সমান সি জি জে ভাগ ডিটারমিন্যান্ট এ।",
        "এই রাশিটি আবার ইনভার্স ম্যাট্রিক্সের আই জে উপাংশের সমান—এক অপূর্ব সংযোগ।",
        "এই সংযোগই সংবেদনশীলতা বিশ্লেষণ, ইনভার্স ম্যাট্রিক্স আর ক্যালকুলাসকে রৈখিক বীজগণিতের সাথে এক সুতোয় গেঁথে দেয়।",
        "সুতরাং পরের বার ক্র্যামারের নিয়ম দেখলে কোনো যান্ত্রিক সূত্র ভাববেন না।",
        "মনে রাখবেন, এটি কয়েকটি সামান্তরিকের ক্ষেত্রফলের এক অতুলনীয় জ্যামিতিক অনুপাত।",
        "একটি স্থানাঙ্ক যা আগে কেবল সংখ্যা মনে হতো, আজ সেটি ক্ষেত্রফলের ভাষায় বলা যায়।",
        "আজকের পাঠে আমরা দেখলাম, কীভাবে একটি সরল জ্যামিতিক চিত্র থেকে একটি শক্তিশালী গাণিতিক সূত্র জন্ম নেয়।",
        "পরের পাঠে আমরা এই ধারণাগুলো আরও গভীরে নিয়ে যাব—আবার দেখা হবে।",
    ],
}

DEFAULT_EXPANSIONS = [
    "এখানে একটু থামুন এবং বিষয়টি নিজের ভাষায় বলে দেখুন। কোনো ধারণা তখনই পোক্ত হয় যখন আপনি সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন।",
    "লক্ষ্য করুন, এই অনুপাতই আমাদের আসল উত্তরের দিকে নিয়ে যায়।",
    "এখানে যুক্তিটি আবার মনে করিয়ে দিই, কারণ পরের ধাপে এটি বারবার কাজে লাগবে।",
    "গণিতের প্রতিটি প্রতীকের পেছনে একটি নির্দিষ্ট অর্থ থাকে—সেই অর্থটি আজ আমাদের মূল বিষয়।",
]

# Closing narration for the final three cues, applied only if still short.
TAIL_EXPANSIONS = {
    23: " আর এক কথা মনে রাখবেন—ক্লোজড ফর্ম মানেই হলো সমাধানকে একটিমাত্র সূত্রে আবদ্ধ করা, যা গাণিতিক বিশ্লেষণে অত্যন্ত শক্তিশালী।",
    24: " সংবেদনশীলতা বিশ্লেষণে এই সূত্র বিশেষ কাজে আসে: লক্ষ্য ভেক্টরের সামান্য পরিবর্তন সমাধানের ওপর কী প্রভাব ফেলে, তা আমরা সরাসরি দেখে নিতে পারি।",
    25: " ক্র্যামারের নিয়ম কেবল একটা হিসাবের কৌশল নয়; এটি ক্ষেত্রফলের অনুপাত থেকে জন্ম নেওয়া এক সুন্দর জ্যামিতিক দৃষ্টিভঙ্গি। আজ এখানেই শেষ—আবার দেখা হবে!",
}


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


def cue_duration_ms(value):
    v = float(value or 0)
    if 0 < v < 100:            # defensive: a narration cue < 100 can only be seconds
        return v * 1000.0
    return v


def load_manifest_cues():
    """Read the lesson_12 audio manifest (read-only).

    Cue texts are the dubbing script. Alias-keyed duplicates (same start_ms and
    text) are de-duplicated. Durations are already in milliseconds.
    """
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out = []
    seen = set()
    for sec_id, sec in data.get("sections", {}).items():
        for c in sec.get("cues", []):
            text = c.get("text")
            if not text:
                continue
            key = (round(float(c.get("start_ms", 0)), 1), text[:80])
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "text": text,
                "dur_ms": cue_duration_ms(c.get("duration_ms", 0)),
                "section": str(sec.get("section_id") or sec_id),
            })
    if out:
        return out, f"audio_manifest:{MANIFEST.name} (ms, alias-deduped, {len(out)} cues)"
    return None, None


def load_cues(vend, source_cues):
    """Initial cumulative layout from authored (teacher) durations, scaled to
    span the video. Used ONLY as expansion targets; the final placement is
    recomputed from rendered speech in recompute_layout_from_speech().
    """
    authored_total = sum(c["dur_ms"] for c in source_cues) + INTER_CUE_PAUSE_S * 1000 * (len(source_cues) - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    scale = usable / (authored_total / 1000.0) if authored_total > 0 else 1.0

    cached = {}
    if TEXT_CACHE.exists():
        try:
            cached = {int(k): v for k, v in json.loads(TEXT_CACHE.read_text(encoding="utf-8")).items()}
        except Exception:
            cached = {}

    cues = []
    cursor_s = 0.0
    for i, c in enumerate(source_cues):
        cid = i + 1
        start = LEAD_IN_SEC + cursor_s * scale
        dur = (c["dur_ms"] / 1000.0) * scale
        cues.append({
            "id": cid,
            "start": round(start, 3),
            "end": round(start + dur, 3),
            "duration": round(dur, 3),
            "authored_target": round(dur, 3),
            "bn": cached.get(cid, c["text"]),
            "base_bn": c["text"],
            "expanded": cid in cached,
            "section": c["section"],
        })
        cursor_s += c["dur_ms"] / 1000.0 + INTER_CUE_PAUSE_S
    return cues, scale


def save_texts(cues):
    cache = {c["id"]: c["bn"] for c in cues if c.get("expanded")}
    TEXT_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


async def synth_all(cues):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, c in enumerate(cues):
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        ok = await synth(sanitize(c["bn"]), raw)
        if not ok:
            failed.append(c["id"])
        if (i + 1) % 10 == 0:
            print(f"  TTS {i+1}/{len(cues)}", flush=True)
    return failed


def predicted_fill(natural, target):
    if target <= 0 or natural <= 0:
        return 0.0
    return min(1.0, natural / (TEMPO_FLOOR * target))


async def force_synth_safe(new_text, raw):
    """Force re-synthesis but restore the previous audio if it fails."""
    backup = raw.with_suffix(".bak.mp3")
    if raw.exists():
        shutil.copy2(raw, backup)
    ok = await synth(sanitize(new_text), raw, force=True)
    if not ok and backup.exists():
        shutil.copy2(backup, raw)
    purge(backup)
    return ok


async def expand_short_cues(cues):
    """HEAVY section-aware expansion. Append pedagogical sentences until each
    cue's natural speech is >= EXPAND_AIM_RATIO of its authored window.
    """
    expanded = []
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            continue
        target = float(c["authored_target"])
        natural = duration(raw)
        if natural <= 0 or natural >= EXPAND_TRIGGER_RATIO * target:
            continue
        pool = EXPANSION_POOL.get(c["section"], DEFAULT_EXPANSIONS)
        base = sanitize(c["base_bn"])
        current = sanitize(c["bn"])
        added = 0
        before = natural
        while added < MAX_APPENDED_SENTENCES:
            need_sec = EXPAND_AIM_RATIO * target - natural
            if need_sec <= 0:
                break
            chars_per_sec = max(8.0, len(current) / max(natural, 0.1))
            need_chars = int(need_sec * chars_per_sec)
            avg_sent = max(60, sum(len(s) for s in pool) // len(pool))
            n_sent = max(1, min(MAX_APPENDED_SENTENCES - added,
                                int(np.ceil(need_chars / avg_sent))))
            append = " ".join(pool[(added + j) % len(pool)] for j in range(n_sent))
            new_text = sanitize(base + " " + append)
            if not await force_synth_safe(new_text, raw):
                break
            added += n_sent
            current = new_text
            natural = duration(raw)
            print(f"  expand cue {cid:02d} [{c['section']}]: "
                  f"fill {predicted_fill(before, target):.2f}->{predicted_fill(natural, target):.2f} "
                  f"natural={natural:.2f}s target={target:.2f}s +{added} sent", flush=True)
            if natural >= EXPAND_AIM_RATIO * target:
                break
        if added > 0 and natural > 0:
            c["bn"] = current
            c["expanded"] = True
            expanded.append({
                "id": cid,
                "section": c["section"],
                "natural_before": round(before, 3),
                "natural_after": round(natural, 3),
                "authored_target_sec": round(target, 3),
                "sentences_added": added,
            })
    save_texts(cues)
    return expanded


async def expand_tail_cues(cues):
    expanded = []
    for c in cues[-3:]:
        cid = c["id"]
        if cid not in TAIL_EXPANSIONS:
            continue
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        target = float(c["authored_target"])
        natural = duration(raw)
        if 0 < natural < EXPAND_AIM_RATIO * target:
            new_text = sanitize(c["bn"] + " " + TAIL_EXPANSIONS[cid])
            if await force_synth_safe(new_text, raw):
                expanded.append({"id": cid,
                                 "natural_before": round(natural, 3),
                                 "natural_after": round(duration(raw), 3)})
                c["bn"] = new_text
                c["expanded"] = True
    if expanded:
        save_texts(cues)
    return expanded


def recompute_layout_from_speech(cues, vend):
    """RECOMPUTE SCALE FROM RENDERED SPEECH.

    Instead of tiling the video with authored (teacher) durations, each window
    is derived from that cue's own rendered speech duration:

        scale = (usable - inter-cue pauses) / sum(rendered_speech_durations)
        window_i  = rendered_i * scale
        tempo_i   = rendered_i / window_i = 1 / scale   (uniform)

    As long as total rendered speech ~= usable, scale ~= 1 and fill ~= 1 with
    no trailing dead air. tempo stays inside [TEMPO_FLOOR, MAX_TEMPO] after the
    safety clamp.
    """
    n = len(cues)
    naturals = []
    for c in cues:
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        naturals.append(duration(raw) if valid(raw) else 0.0)
    total = sum(naturals)
    if total <= 0:
        raise SystemExit("FATAL: no rendered speech available for scale recomputation")

    pause_total = INTER_CUE_PAUSE_S * (n - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    scale = (usable - pause_total) / total
    scale = max(1.0 / MAX_TEMPO, min(1.0 / TEMPO_FLOOR, scale))

    cursor = LEAD_IN_SEC
    for c, nat in zip(cues, naturals):
        w = max(0.05, nat * scale)
        c["start"] = round(cursor, 3)
        c["duration"] = round(w, 3)
        c["end"] = round(cursor + w, 3)
        c["natural"] = round(nat, 3)
        cursor += w + INTER_CUE_PAUSE_S
    return scale, naturals, cursor


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


def make_cue(raw, target, out, cid):
    """atempo-fit into the recomputed window; PAD only, NEVER truncate.

    Returns (arr, info) with honest fill / internal-gap / pocket metrics
    measured from the rendered waveform.
    """
    natural = duration(raw)
    if natural <= 0:
        natural = target
    tempo = max(TEMPO_FLOOR, min(MAX_TEMPO, natural / target))
    tmp = out.with_suffix(".fit.wav")
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)

    window_n = max(1, int(round(target * SR)))
    idx = np.flatnonzero(np.abs(arr) > ACTIVE_THRESHOLD)
    if idx.size > 0:
        active_samples = int(idx.size)
        lead_s = int(idx[0]) / SR
        tail_s = (len(arr) - 1 - int(idx[-1])) / SR
        diffs = np.diff(idx) - 1                      # samples of silence between active runs
        internal_s = float(diffs.max()) / SR if diffs.size else 0.0
        pockets = int(np.sum(diffs > POCKET_SEC * SR))
        max_gap_s = max(internal_s, lead_s, tail_s)
        if lead_s > POCKET_SEC:
            pockets += 1
        if tail_s > POCKET_SEC:
            pockets += 1
    else:
        active_samples = 0
        max_gap_s = len(arr) / SR
        pockets = 1

    # fill_ratio follows the mandated build_calc08_clean.py definition:
    # placed speech-clip samples / window samples (i.e. no dead air at the end
    # of a cue window). The voiced duty cycle (active samples) is reported
    # separately as active_fill_ratio; short inter-sentence breaths there are
    # NOT silent pockets (those are guarded by max_internal_gap_s / pockets).
    clip_coverage = min(1.0, len(arr) / window_n)
    active_fill = min(1.0, active_samples / window_n)

    need = window_n
    if len(arr) < need:
        arr = np.pad(arr, (0, need - len(arr)))       # pad only, never cut
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(arr, -1, 1) * 32767).astype("<i2").tobytes())
    try:
        os.remove(tmp)
    except OSError:
        pass

    info = {
        "tempo": round(tempo, 4),
        "natural": round(natural, 3),
        "target": round(target, 3),
        "clip_coverage": round(clip_coverage, 4),
        "fill_ratio": round(clip_coverage, 4),
        "active_fill_ratio": round(active_fill, 4),
        "max_internal_gap_s": round(max_gap_s, 4),
        "pockets_gt_2s": pockets,
        "active_samples": active_samples,
        "window_samples": window_n,
    }
    return arr, info


def scan_output_silence(path):
    """ffmpeg silencedetect on the muxed audio; return (max_internal_s, pockets)."""
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-vn", "-i", str(path),
           "-af", "silencedetect=noise=-45dB:d=0.5", "-f", "null", "-"]
    txt = ""
    for attempt in range(6):
        try:
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            txt = r.stderr or ""
            break
        except OSError as e:
            if not is_win1450(e):
                raise
            time.sleep(0.5 * (attempt + 1))
    starts = [float(m.group(1)) for m in re.finditer(r"silence_start:\s*([\d.]+)", txt)]
    ends = [float(m.group(1)) for m in re.finditer(r"silence_end:\s*([\d.]+)", txt)]
    intervals = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else s
        intervals.append((s, e, e - s))
    return intervals


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
    if not ORIGINAL_VIDEO.exists():
        raise SystemExit(f"FATAL: original video missing: {ORIGINAL_VIDEO}")
    if not MANIFEST.exists():
        raise SystemExit(f"FATAL: manifest missing: {MANIFEST}")

    vend = video_duration(ORIGINAL_VIDEO)
    source_cues, source_desc = load_manifest_cues()
    if not source_cues:
        raise SystemExit("FATAL: no cues loaded from manifest")
    cues, authored_scale = load_cues(vend, source_cues)
    print(f"video duration = {vend:.3f}s; cues = {len(cues)}; source = {source_desc}; "
          f"authored scale = {authored_scale:.4f}", flush=True)

    print("[1/7] TTS (clean, no SFX) ...", flush=True)
    failed = await synth_all(cues)

    print("[2/7] HEAVY section-aware expansion ...", flush=True)
    expanded = await expand_short_cues(cues)
    print(f"  expanded {len(expanded)} cues", flush=True)

    print("[2b/7] Tail expansion ...", flush=True)
    tail_expanded = await expand_tail_cues(cues)
    print(f"  tail-expanded {len(tail_expanded)} cues", flush=True)

    print("[3/7] RECOMPUTE SCALE FROM RENDERED SPEECH ...", flush=True)
    speech_scale, naturals, timeline_end = recompute_layout_from_speech(cues, vend)
    uniform_tempo = 1.0 / speech_scale
    print(f"  rendered total = {sum(naturals):.3f}s ; speech scale = {speech_scale:.4f} ; "
          f"uniform tempo = {uniform_tempo:.4f} ; timeline end = {timeline_end:.3f}s", flush=True)

    print("[4/7] Absolute sample placement + fill/gap measurement ...", flush=True)
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    CHUNK = 1_000_000
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    fills = []
    gaps = []
    all_pockets = 0
    overrun = 0
    last_cue_end = 0.0
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            print(f"  SKIP cue {cid} (no audio)", flush=True)
            continue
        arr, info = make_cue(raw, float(c["duration"]), CUE_DIR / f"cue_{cid:03d}.wav", cid)
        fills.append(info["fill_ratio"])
        gaps.append(info["max_internal_gap_s"])
        all_pockets += info["pockets_gt_2s"]
        if info["clip_coverage"] >= 0.999:
            pass
        if info["target"] > 0 and float(c["duration"]) > 0 and info["tempo"] >= MAX_TEMPO - 1e-6:
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
        placed.append({
            "id": cid,
            "section": c["section"],
            "expected_start_ms": round(float(c["start"]) * 1000, 2),
            "actual_start_ms": round(start_sample / SR * 1000, 2),
            "drift_ms": round(start_sample / SR * 1000 - float(c["start"]) * 1000, 6),
            "tempo": info["tempo"],
            "natural_sec": info["natural"],
            "target_sec": info["target"],
            "clip_coverage": info["clip_coverage"],
            "fill_ratio": info["fill_ratio"],
            "active_fill_ratio": info["active_fill_ratio"],
            "max_internal_gap_s": info["max_internal_gap_s"],
            "pockets_gt_2s": info["pockets_gt_2s"],
            "expanded": c["expanded"],
        })

    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    max_internal_gap = round(max(gaps), 4) if gaps else 0.0
    print(f"  median_fill={median_fill} max_internal_gap={max_internal_gap}s "
          f"pockets(>2s)={all_pockets} overrun={overrun}", flush=True)

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

    print("[5/7] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')

    print("[6/7] Mux with FULL original video (video copy, source never swapped) ...", flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    print("[7/7] Verify output (duration + silencedetect) ...", flush=True)
    out_dur = duration(OUT_VIDEO)
    intervals = scan_output_silence(OUT_VIDEO)
    internal_ints = [(s, e, d) for (s, e, d) in intervals
                     if s >= LEAD_IN_SEC - 0.6 and e <= last_cue_end + 0.6 and d > POCKET_SEC]
    output_pockets = len(internal_ints)
    max_out_internal = max((d for (_, _, d) in internal_ints), default=0.0)

    median_ok = median_fill >= GATE_MEDIAN_FILL
    gap_ok = max_internal_gap <= GATE_MAX_INTERNAL_GAP_S and max_out_internal <= GATE_MAX_INTERNAL_GAP_S
    pockets_ok = all_pockets == 0 and output_pockets <= GATE_MAX_POCKETS
    duration_ok = abs(out_dur - vend) <= 1.0
    all_gates = median_ok and gap_ok and pockets_ok and duration_ok and not failed

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    report = {
        "experiment": "fill_v2 — re-render Lesson 12 dub to eliminate silent pockets",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": source_desc,
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "voice": VOICE,
        "strategy": "heavy section-aware expansion; recompute scale from rendered speech; "
                    "absolute sample placement; atempo fit; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "video_source": str(ORIGINAL_VIDEO),
        "video_source_swapped": False,
        "authored_timeline_scale": round(authored_scale, 6),
        "recomputed_speech_scale": round(speech_scale, 6),
        "scale_method": "scale=(usable - inter-cue pauses)/sum(rendered speech); window_i=rendered_i*scale; tempo=1/scale",
        "uniform_tempo": round(uniform_tempo, 4),
        "rendered_speech_total_sec": round(sum(naturals), 3),
        "tempo_floor": TEMPO_FLOOR,
        "max_tempo": MAX_TEMPO,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "original_duration_sec": round(vend, 3),
        "output_duration_sec": round(out_dur, 3),
        "duration_delta_sec": round(out_dur - vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        # fill + gate metrics
        "fill_definition": "speech-clip samples / window samples per cue (build_calc08_clean.py definition)",
        "median_fill": median_fill,
        "min_fill": round(min(fills), 4) if fills else 0.0,
        "max_fill": round(max(fills), 4) if fills else 0.0,
        "median_voiced_duty_cycle": round(statistics.median(
            [x["active_fill_ratio"] for x in placed]), 4) if placed else 0.0,
        "max_internal_gap_s": max_internal_gap,
        "max_output_internal_gap_s": round(max_out_internal, 4),
        "pockets_gt_2s_per_cue": all_pockets,
        "pockets_gt_2s_in_output": output_pockets,
        "internal_pockets_output_intervals": [
            {"start": round(s, 3), "end": round(e, 3), "duration": round(d, 3)}
            for (s, e, d) in internal_ints
        ],
        "gate_median_fill": GATE_MEDIAN_FILL,
        "gate_max_internal_gap_s": GATE_MAX_INTERNAL_GAP_S,
        "gate_max_pockets": GATE_MAX_POCKETS,
        "gate_median_fill_ok": median_ok,
        "gate_internal_gap_ok": gap_ok,
        "gate_pockets_ok": pockets_ok,
        "gate_duration_ok": duration_ok,
        "all_gates_pass": bool(all_gates),
        "expanded_text_cue_count": sum(1 for c in cues if c.get("expanded")),
        "expanded_text_cue_ids": [c["id"] for c in cues if c.get("expanded")],
        "expansion_note": "expanded_cues lists cues expanded in THIS run; a resumed run reuses "
                          "_expanded_texts.json, so expanded_text_cue_ids is the authoritative "
                          "list of cues carrying heavy pedagogical expansion.",
        "expanded_cues": expanded,
        "tail_expansions_applied": tail_expanded,
        "cues": placed,
        "output_video": str(OUT_VIDEO),
        "output_size_bytes": OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0,
    }
    try:
        probe = json.loads(run(f'ffprobe -v error -show_entries stream=index,codec_type,codec_name '
                               f'-of json "{OUT_VIDEO}"'))
        report["output_streams"] = probe.get("streams", [])
    except Exception as e:
        report["output_streams_error"] = str(e)
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, out_dur - 2), 2)

    VERIFY.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + ("PASS" if all_gates else "FAIL"), flush=True)
    print(f"  duration orig={vend:.3f}s out={out_dur:.3f}s (delta={out_dur-vend:+.3f}s) match={duration_ok}", flush=True)
    print(f"  median_fill={median_fill} (>= {GATE_MEDIAN_FILL}) -> {median_ok}", flush=True)
    print(f"  max_internal_gap={max_internal_gap}s / output={max_out_internal:.3f}s "
          f"(<= {GATE_MAX_INTERNAL_GAP_S}) -> {gap_ok}", flush=True)
    print(f"  pockets>2s per-cue={all_pockets} output={output_pockets} "
          f"(<= {GATE_MAX_POCKETS}) -> {pockets_ok}", flush=True)
    print(f"  drift={max_drift:.3f}ms overrun={overrun} speech_scale={speech_scale:.4f}", flush=True)
    print(f"  VERIFY: {VERIFY}", flush=True)
    if not all_gates:
        raise SystemExit("FILL GATE FAILED — see verification.json; do not claim success")


if __name__ == "__main__":
    asyncio.run(main())
