"""
EXPERIMENT — Full-length clean absolute-sample Bengali dub (Essence of Calculus, Lesson 08)
==========================================================================================
Adapted verbatim from the proven clean_timesync_v2 pipeline:
  essence_of_calculus/lesson_05_euler_number/dubbing_pipeline/experiments/clean_timesync_v2/build_calc05_clean.py

AND applies web_platform/governance/IMPROVED_DUB_FILL_POLICY.md (atempo floor 0.82,
contextual pedagogical expansion of short cues, measured median_fill & max_internal_gap_s).

Guarantees (identical to the proven pipeline + improved fill policy):
  1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
     half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
  2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
  3. atempo fit in [0.82, 2.2]; PAD ONLY, NEVER truncate. NO SFX: clean speech only.
  4. IMPROVED FILL: gentle slowdown (floor 0.82) + contextual Bengali pedagogical
     expansion of any cue whose natural TTS would leave a silent pocket. Fill ratio
     (speech_samples / window_samples) measured per cue; median_fill >= 0.72 and
     max_internal_gap_s <= 1.5s recorded into verification.json.
  5. Expand a tail cue when its Bengali TTS is much shorter than its window;
     speed the final cue up so speech ends before the video end (final-cue cap).
  6. Canvas padded to the FULL original video duration so -shortest can never
     trim video frames.
  7. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
  8. Lightweight volumedetect (-vn -nostats, log to FILE) on intro 0-2s and
     the final 2s, written into verification.json.

Cue source (read-only; teacher audio / manifests are NEVER modified):
  1. .../lesson_08_integration/dubbing_pipeline/*master_script*.json  (PRIMARY)
     -- NOTE: this master script stores start/end/duration in SECONDS, so
        duration is converted x1000 to milliseconds before layout. The authored
        cues are then cumulatively laid out and scaled to span the FULL video
        (original ~1245.8s while authored cues cover ~516.5s -> scale ~2.34x).
  2. web_platform/data/calculus/lesson_08.json -> its audio_manifest reference.
  3. last resort: derive cues from the sections of lesson_08.json itself.

Everything is written under NEW experiment folders. Teacher audio, manifests
and other lessons are untouched.
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
BASE = EXP.parent.parent                        # .../lesson_08_integration/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "calculus" / "lesson_08.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "calculus" / "lesson_08" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "calculus" / "lesson_08" / "experiments" / "3b1b_calculus_08_full_dubbed.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
TEMPO_FLOOR = 0.82          # IMPROVED_DUB_FILL_POLICY: gentle natural slowdown
FADE_MS = 12
VIDEO_ID = "rfG8ce4nNh0"
LESSON = "lesson_08_integration"

# Silence margins: keep 0-2 s and the final 2 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# IMPROVED_DUB_FILL_POLICY: expand any cue whose natural TTS would fill less
# than this fraction of its (scaled) window even after the 0.82x slowdown.
# A ratio of 0.85 keeps tempo in [0.85, 1.0] => ~100% fill for expanded cues.
EXPAND_THRESHOLD_RATIO = 0.85

# Extra Bengali narration appended to a closing cue ONLY when its natural TTS
# is much shorter than its visual window (data-driven, never applied blindly).
TAIL_EXPANSIONS = {
    38: (" আরও একটি দৃষ্টিকোণ থেকে দেখা যাক: এই উপপাদ্যটি কেবল একটি গাণিতিক পরিচয় নয়, "
         "বরং অসীম সংখ্যক ক্ষুদ্র অংশকে সসীম ও সুন্দর একটি উত্তরে রূপ দেওয়ার দার্শনিক বিজয়।"),
    39: (" অন্তরীকরণ ও যোগজীকরণের এই দ্বৈততা প্রকৃতির প্রতিটি ক্ষেত্রে প্রতিফলিত হয়—"
         "ত্বরণ থেকে বেগ, বেগ থেকে দূরত্ব, চার্জ থেকে তড়িৎ প্রবাহ—সবেতেই এই একই সুতো কাজ করে।"),
    40: (" আজ এখানেই শেষ। ইন্টিগ্রাল এবং মৌলিক উপপাদ্য আপনার ক্যালকুলাস যাত্রার এক নতুন "
         "দ্বার খুলে দিল। পরের পাঠে আমরা দেখব কীভাবে এই ক্ষেত্রফলের ধারণাটি আবারও "
         "ঢালের সাথে নিখুঁতভাবে জড়িত। আবার দেখা হবে!"),
}

# Contextual pedagogical Bengali sentences used by the improved fill policy.
# Each entry is appended (after sanitize) to that cue's script when its natural
# TTS is short of the scaled visual window. Only short cues actually use these.
EXPANSIONS = {
    1: " আসুন এই দুই ধারণার গভীর সম্পর্কটি ধাপে ধাপে উন্মোচন করি। ডেরিভেটিভ আমাদের বলে কোনো প্রক্রিয়ার তাৎক্ষণিক গতি, আর ইন্টিগ্রাল বলে সেই গতির সামগ্রিক ফলাফল।",
    2: " ডেরিভেটিভ আমাদের শিখিয়েছে কীভাবে একটি বক্ররেখার ঢাল বা পরিবর্তনের হার মাপা যায়। এর সাহায্যে আমরা বুঝতে পেরেছি কীভাবে ছোট ছোট পরিবর্তন যোগ হয়ে বড় পরিবর্তন তৈরি করে।",
    3: " এই দুটি ধারণা একে অপরের বিরোধী মনে হলেও আসলে একই মুদ্রার দুই পিঠ। আর তাদের মাঝের সেই বন্ধনটি খুঁজে বের করাই আজকের পাঠের মূল লক্ষ্য।",
    4: " এই উপপাদ্যের সৌন্দর্য হলো এটি কোনো কৃত্রিম নিয়ম নয়, বরং ক্ষেত্রফল ও ঢালের অবিচ্ছেদ্য সম্পর্কের স্বাভাবিক পরিণতি। আমরা ধাপে ধাপে সেই যুক্তিটি নির্মাণ করব।",
    5: " গাড়ির উদাহরণটি বেছে নেওয়া হয়েছে কারণ বেগ আর দূরত্বের সম্পর্ক আমাদের কাছে স্বজ্ঞাত। স্থির বেগের সহজ ক্ষেত্র থেকে শুরু করে আমরা ধীরে ধীরে জটিল ক্ষেত্রে অগ্রসর হব।",
    6: " এখানে মনে রাখতে হবে যে দূরত্ব আর বেগের এই গুণফল সম্পর্কতি শুধু সংখ্যার গল্প নয়; লেখচিত্রে এটি একটি আয়তক্ষেত্রের ক্ষেত্রফল হিসেবে স্পষ্টভাবে প্রকাশ পায়েই।",
    7: " লেখচিত্রের এই দৃশ্যরূপটি আমাদের পরবর্তী ধাপের ভিত্তি তৈরি করে। উচ্চতা ও প্রস্থের গুণফল যে ক্ষেত্রফল, তা আজকের পুরো যুক্তির কেন্দ্রবিন্দু।",
    8: " মানে হলো, বক্ররেখার নিচের আবদ্ধ ক্ষেত্রফল কেবল একটা জ্যামিতিক রাশি নয়—এটি আক্ষরিক অর্থেই গাড়িটি যতটুকু পথ পাড়ি দিয়েছে তার পরিমাপ।",
    9: " বেগ যখন পরিবর্তনশীল, তখন একক বেগের ধারণা কাজ করে না। তাই আমাদের এমন এক কৌশল প্রয়োজন যা প্রতিটি মুহূর্তের বেগকে আলাদাভাবে ধরে নিতে পারে।",
    10: " প্রতিটি মুহূর্তে বেগ আলাদা হওয়ায় একটি মাত্র সংখ্যা দিয়ে পুরো যাত্রার বর্ণনা দেওয়া সম্ভব নয়। এই অসুবিধাটিই ক্যালকুলাসের মূল উদ্ভাবনের প্রেরণা ছিল।",
    11: " সময়কে ছোট ছোট টুকরোতে ভাগ করার এই কৌশলকে বলা হয় বিভাজন। প্রতিটি টুকরো যত ছোট হবে, তার ভেতর বেগ তত বেশি স্থির ধরা যাবে—আর এটিই আমাদের হিসাবকে নির্ভুল করে তোলে।",
    12: " ডিটি যত ক্ষুদ্র হোক না কেন, ওই সংক্ষিপ্ত ব্যবধানে বেগের পরিবর্তন নগণ্য। এই সরলীকরণই আমাদেরকে জটিল বক্ররেখার নিচের ক্ষেত্রফল হিসাব করতে সাহায্য করে।",
    13: " ডিএস সমান ভি অব টি গুণ ডিটি—এই ছোট্ট সমীকরণটি আজকের পুরো তত্ত্বের বীজ। এটি আমাদের বলে কীভাবে ক্ষুদ্র ক্ষুদ্র অংশগুলোকে একত্রিত করতে হয়।",
    14: " প্রতিটি পাতলা আয়তক্ষেত্রের ক্ষেত্রফল যত কম হোক, সবগুলোকে একসাথে যোগ করলে বক্ররেখার নিচের আবদ্ধ অঞ্চলটির আনুমানিক মান পাওয়া যায়।",
    15: " এই যোগপ্রক্রিয়াটিকেই আমরা পরবর্তীতে রিম্যান সমষ্টি নামে অভিহিত করব। এটি ক্ষেত্রফল গণনার একটি প্রাকৃতিক ও স্বজ্ঞাত পদ্ধতি।",
    16: " রিম্যান সমষ্টির ধারণাটি আধুনিক বিশ্লেষণের ভিত্তি। ডিটি কমানোর সাথে সাথে অনুমানের ভুলও কমতে থাকে এবং ফলাফল প্রকৃত মানের কাছে এগিয়ে যায়।",
    17: " সিঁড়ির মতো খাঁজকাটা শীর্ষভাগ যত মসৃণ বক্ররেখার কাছে আসবে, আনুমানিক ক্ষেত্রফল তত বেশি নিখুঁত হবে। এই দুটি ঘটনা একসাথে ঘটার কারণেই লিমিটের ধারণা এত শক্তিশালী।",
    18: " অসীম সংখ্যক আয়তক্ষেত্রের এই সীমাস্থ যোগফলই হলো নির্দিষ্ট ইন্টিগ্রাল। এখানে অসীমকে নিয়ে কোনো রহস্য নেই—লিমিটের মাধ্যমে আমরা একে সুসংজ্ঞায়িত করি।",
    19: " লাইবনিজের দেওয়া এই প্রতীকটি আজও বিশ্বজুড়ে ব্যবহৃত হয়। প্রসারিত এস অক্ষরটি স্মরণ করিয়ে দেয় যে ইন্টিগ্রাল মূলত এক ধরনের দীর্ঘ যোগফল মাত্র।",
    20: " প্রতীকের প্রতিটি অংশের অর্থ বোঝা গেলে সূত্রটি মুখস্থ করার প্রয়োজন হয় না। এফ অব এক্স হলো উচ্চতা, ডিএক্স হলো প্রস্থ আর এস হলো সমষ্টি—এতটুকুই এই গল্প।",
    21: " কাজেই ইন্টিগ্রালকে কখনোই শুষ্ক চিহ্নের সমষ্টি ভাববেন না। এর পেছনে সবসময় অসংখ্য ক্ষুদ্র আয়তক্ষেত্রের প্রাকৃতিক ছবিটি চোখের সামনে রাখুন।",
    22: " সংজ্ঞা দেওয়া সহজ, কিন্তু লক্ষ লক্ষ আয়তক্ষেত্র হাতে যোগ করা অবাস্তব। তাই প্রশ্ন ওঠে—এই ক্ষেত্রফলের সরাসরি ও নিখুঁত মান বের করার কোনো সহজ উপায় আছে কি?",
    23: " এই প্রশ্নের উত্তরই ক্যালকুলাসের ইতিহাসে সবচেয়ে বড় আবিষ্কারের দিকে নিয়ে যায়। আমরা এখন ক্ষেত্রফলকে একটি চলকের ফাংশন হিসেবে দেখতে শুরু করব।",
    24: " ডান প্রান্তকে চলক বানানোর এই কৌশল অসাধারণ। এর মাধ্যমে একটি স্থির সংখ্যার বদলে আমরা একটি গতিশীল ফাংশন পাই, যার আচরণ আমরা বিশ্লেষণ করতে পারি।",
    25: " ক্যাপিটাল এ অব এক্স হলো একটি ক্রমবর্ধমান ফাংশন। এক্স বাড়ালে আবদ্ধ ক্ষেত্রফলও বাড়ে—এই সরল পর্যবেক্ষণই পরবর্তী যুক্তির চাবিকাঠি।",
    26: " ফাংশনটির এই বৃদ্ধির হারই আমাদের জানতে হবে। ঠিক কী হারে ক্ষেত্রফল বাড়ছে, তা বের করলেই মৌলিক উপপাদ্যের সত্য প্রকাশ পাবে।",
    27: " ডিএ বাই ডিএক্স হলো ক্ষেত্রফলের পরিবর্তনের হার। আমরা দেখব এই হার আশ্চর্যজনকভাবে মূল বক্ররেখার উচ্চতার সমান।",
    28: " এক্সকে সামান্য এগিয়ে দিলে যে নতুন ফালিটি যোগ হয়, তার প্রস্থ ডিএক্স আর উচ্চতা ওই বিন্দুতে ফাংশনের মান। এই চিত্রটি মনে রাখলেই হিসাবটি সহজ হয়ে যায়।",
    29: " স্মল এফ অব এক্স মানে বক্ররেখার ওই বিন্দুতে উচ্চতা। তাই নতুন ফালির ক্ষেত্রফল হলো উচ্চতা গুণ প্রস্থ, অর্থাৎ এফ অব এক্স গুণ ডিএক্স।",
    30: " ডিএক্স দিয়ে ভাগ করার পর যে সুন্দর ফলাফলটি পাই, তা কেবল একটি সূত্র নয়—এটি বোঝায় যে ক্ষেত্রফলের বৃদ্ধির হার আর বক্ররেখার উচ্চতা একই জিনিস।",
    31: " এই উপলব্ধিটি ক্যালকুলাসের সবচেয়ে গুরুত্বপূর্ণ মুহূর্তগুলোর একটি। ক্ষেত্রফল জমা হওয়ার হার ঠিক বক্ররেখার বর্তমান উচ্চতার সমান—এক কথায় ডিএ বাই ডিএক্স সমান এফ অব এক্স।",
    32: " এর মানে হলো ক্ষেত্রফল ফাংশন খোঁজা মানে এমন একটি ফাংশন খোঁজা যার অন্তরজ মূল ফাংশনের সমান। আমরা এই প্রক্রিয়াটিকে বলি প্রতি-অন্তরীকরণ।",
    33: " অ্যান্টি-ডেরিভেটিভের ধারণা ইন্টিগ্রেশনকে বদলে দেয়। অসীম যোগফলের বদলে আমরা এখন সহজেই ডেরিভেটিভের উল্টো নিয়ম খুঁজে বের করতে পারি।",
    34: " আসুন এই নতুন কৌশলটি একটি পরিচিত উদাহরণে পরীক্ষা করি। টি স্কয়ারের মতো সরল ফাংশনের ক্ষেত্রেও এই পদ্ধতি কাজ করে কি না, তা দেখা যাক।",
    35: " পাওয়ার রুল আমাদের আগের পাঠ থেকে পরিচিত। ঘাতকে এক কমিয়ে নতুন ঘাত তৈরি করে এবং আগের ঘাত দিয়ে ভাগ দিলেই আমাদের কাঙ্ক্ষিত ফল পাওয়া যায়।",
    36: " এক-তৃতীয়াংশ টি কিউব—এই সরল উত্তরটি আগের অসীম যোগফলের সমান। এর মাধ্যমে বোঝা যায় মৌলিক উপপাদ্য কতটা শক্তিশালী ও ব্যবহারিক।",
    37: " দুই প্রান্তের ক্ষেত্রফলের পার্থক্য নেওয়ার এই কৌশল আমাদেরকে যেকোনো ব্যবধানের ক্ষেত্রফল দেয়। বি পর্যন্ত ক্ষেত্রফল থেকে এ পর্যন্ত ক্ষেত্রফল বাদ দিলেই মাঝের অংশ পাওয়া যায়।",
    38: " ক্যাপিটাল এফ অব বি মাইনাস ক্যাপিটাল এফ অব এ—এই সূত্রটিই ক্যালকুলাসের মৌলিক উপপাদ্য নামে পরিচিত। এটি অসীমের জটিলতাকে সসীমের সরলতায় রূপ দেয়।",
    39: " ডেরিভেটিভ ভেঙে দেখায় আর ইন্টিগ্রাল জুড়ে দেখায়। একই প্রক্রিয়ার এই দুই দিক আমাদের বিশ্বকে বোঝার এক অতুলনীয় হাতিয়ার।",
    40: " এই উপাদানগুলো একসাথে মিলে ক্যালকুলাসকে একটিমাত্র সুসংবদ্ধ কাঠামোতে পরিণত করে। পরিবর্তন আর সঞ্চয়ের এই মিলনই গাণিতিক চিন্তার সবচেয়ে সুন্দর অধ্যায়।",
}

# Generic pedagogical fallback pool (used only if a cue's primary expansion is
# still insufficient after one more expansion pass).
GENERIC_EXTRA = (
    " এখানে একটু থামুন এবং বিষয়টি নিজের ভাষায় বলে দেখুন। কোনো ধারণা তখনই পোক্ত হয় যখন আপনি "
    "সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন। এই অভ্যাস আপনার বোঝাপড়াকে আরও গভীর করবে।"
)


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
        # Fallback 1: split into two halves and concatenate.
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
        # Fallback 2: synthesize sentence by sentence and concatenate.
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


def load_master_cues():
    """Read the PRIMARY master script. Its start/end/duration are in SECONDS.

    Convert duration (s) -> milliseconds so the shared layout code works.
    """
    masters = sorted(BASE.glob("*master_script*.json"))
    if not masters:
        return None, None
    mpath = masters[0]
    data = json.loads(mpath.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("cues") or data.get("sections") or []
    out = []
    for c in data:
        if not isinstance(c, dict):
            continue
        text = c.get("bn") or c.get("text")
        if not text:
            continue
        # Master script timing is in seconds -> convert to ms.
        dur_s = c.get("duration")
        if dur_s is None:
            dur_s = (float(c.get("end", 0)) - float(c.get("start", 0)))
        dur_ms = float(dur_s) * 1000.0
        out.append({
            "text": text,
            "dur_ms": dur_ms,
            "section": str(c.get("section", "master")),
        })
    if out:
        return out, f"master_script:{mpath.name} (seconds->ms x1000)"
    return None, None


def load_source_cues():
    """Return (list_of_{text,dur_ms,section}, source_description)."""
    # 1) master script (primary) -- durations are in SECONDS
    out, desc = load_master_cues()
    if out:
        return out, desc

    # 2) audio manifest referenced by lesson_08.json (read-only)
    lesson = json.loads(LESSON_JSON.read_text(encoding="utf-8"))
    rel = lesson.get("audio_manifest") or (lesson.get("meta") or {}).get("audio_manifest")
    if rel:
        manifest = (LESSON_JSON.parent / rel).resolve()
        if manifest.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            out = []
            for sec_id, sec in data.get("sections", {}).items():
                for c in sec.get("cues", []):
                    out.append({
                        "text": c["text"],
                        "dur_ms": float(c.get("duration_ms", 0)),
                        "section": sec_id,
                    })
            if out:
                return out, f"audio_manifest:{manifest.name}"
            return derive_from_lesson(lesson), "lesson_08.json:sections"
    return derive_from_lesson(lesson), "lesson_08.json:sections"


def derive_from_lesson(lesson):
    """Last-resort cue derivation from the lesson JSON's rich text sections."""
    out = []
    for sec in lesson.get("sections", []):
        sec_id = sec.get("id") or sec.get("alias") or "section"
        texts = []
        q = sec.get("quote") or {}
        if q.get("text_bn"):
            texts.append(q["text_bn"])
        texts.extend(sec.get("paragraphs", []))
        for fm in sec.get("formulas", []):
            if fm.get("caption_bn"):
                texts.append(fm["caption_bn"])
        co = sec.get("callout") or {}
        if co.get("text_bn"):
            texts.append(co["text_bn"])
        if sec.get("closing_thought_bn"):
            texts.append(sec["closing_thought_bn"])
        for t in texts:
            clean = re.sub(r"\$[^\$]*\$", " ", t)          # drop LaTeX math
            clean = re.sub(r"[\\\{\}\[\]#*]", " ", clean)
            clean = re.sub(r"\s+", " ", clean).strip()
            if clean:
                out.append({"text": clean,
                            "dur_ms": max(2000.0, len(clean) * 90.0),
                            "section": sec_id})
    return out


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
        ok = await synth(sanitize(c["bn"]), raw)
        if not ok:
            failed.append(c["id"])
            print(f"  WARNING cue {c['id']} failed after every fallback", flush=True)
        if (i + 1) % 10 == 0:
            print(f"  TTS {i+1}/{len(cues)}", flush=True)
    return failed


async def expand_tail_cues(cues):
    """Append richer wording to closing cues whose TTS is short of the window."""
    expanded = []
    last_ids = {c["id"] for c in cues[-3:]}
    for c in cues:
        if c["id"] not in last_ids or c["id"] not in TAIL_EXPANSIONS:
            continue
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        target = float(c["duration"])
        natural = duration(raw)
        if 0 < natural < 0.85 * target and c["id"] not in EXPANSIONS:
            new_text = sanitize(c["bn"] + " " + TAIL_EXPANSIONS[c["id"]])
            print(f"  tail-expand cue {c['id']}: natural={natural:.2f}s < {0.85*target:.2f}s", flush=True)
            if await synth(new_text, raw, force=True):
                expanded.append({"id": c["id"],
                                 "natural_before": round(natural, 3),
                                 "natural_after": round(duration(raw), 3)})
    return expanded


async def expand_short_cues(cues):
    """IMPROVED_DUB_FILL_POLICY.

    For any cue whose natural TTS would occupy less than EXPAND_THRESHOLD_RATIO
    of its (scaled) window, append a contextual Bengali pedagogical sentence and
    re-synthesize, repeating up to 3 passes until the ratio is reached. This
    removes silent pockets and improves teaching quality at the same time.
    """
    expanded = []
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            continue
        # Use the same final-cue cap the placement step uses, so expansion does
        # not accidentally push speech past the end of the video.
        target = float(c["duration"])
        if cid == LAST_ID:
            target = min(target, VIDEO_END - LAST_START - 0.10)
        natural = duration(raw)
        if natural <= 0 or natural >= EXPAND_THRESHOLD_RATIO * target:
            continue
        original_natural = natural
        added = []
        base_text = sanitize(c["bn"])
        for attempt in range(3):
            natural = duration(raw)
            if natural >= EXPAND_THRESHOLD_RATIO * target:
                break
            extra = EXPANSIONS.get(cid, GENERIC_EXTRA) if attempt == 0 else GENERIC_EXTRA
            new_text = sanitize(c["bn"] + " " + " ".join(added) + " " + extra)
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
    """atempo-fit into the window with floor 0.82; PAD only, NEVER truncate.

    Returns (arr, info) where info carries tempo/natural/target plus the
    measured fill ratio and internal silence gap of this cue's window.
    """
    natural = duration(raw)
    if natural <= 0:
        natural = target
    if cid == LAST_ID:
        # Final cue must finish INSIDE the video, with a small safety margin.
        target = min(target, VIDEO_END - LAST_START - 0.10)
    tempo = max(TEMPO_FLOOR, min(MAX_TEMPO, natural / target))
    tmp = out.with_suffix(".fit.wav")
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)
    speech_samples = len(arr)
    need = int(round(target * SR))
    if len(arr) < need:
        arr = np.pad(arr, (0, need - len(arr)))     # pad only, never cut
    # If still longer (tempo cap), keep it -> recorded as overrun, never cut.
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


async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    source_cues, source_desc = load_source_cues()
    cues, scale = load_cues(vend, source_cues)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"video duration = {vend:.3f}s; cues = {len(cues)}; source = {source_desc}; "
          f"timeline scale = {scale:.4f}", flush=True)

    print("[1/6] TTS (clean, no SFX) ...", flush=True)
    failed = await synth_all(cues)

    print("[2/6] Conditional tail-cue expansion ...", flush=True)
    tail_expanded = await expand_tail_cues(cues)

    print("[3/6] IMPROVED fill policy: contextual expansion of short cues ...", flush=True)
    fill_expanded = await expand_short_cues(cues)

    print("[4/6] Absolute sample placement (start*44100, pad-only, floor 0.82) ...", flush=True)
    # FULL-length canvas: -shortest can never trim the video.
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    fills = []
    internal_gaps = []
    overrun = 0
    last_cue_end = 0.0
    expanded_ids = {x["id"] for x in fill_expanded} | {x["id"] for x in tail_expanded}
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

    # Peak-normalise in chunks to avoid clipping.
    CHUNK = 1_000_000
    peak_i = 0
    for i in range(0, len(canvas), CHUNK):
        seg = canvas[i:i + CHUNK]
        peak_i = max(peak_i, int(seg.max()), int(-seg.min()))
    peak_i = peak_i or 1
    if peak_i > 32112:  # 0.98 * 32767
        scale_pk = 32112.0 / peak_i
        for i in range(0, len(canvas), CHUNK):
            seg = canvas[i:i + CHUNK].astype(np.float32)
            seg *= scale_pk
            np.rint(seg, out=seg)
            canvas[i:i + CHUNK] = seg.astype(np.int16)

    print("[5/6] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    report = {
        "experiment": "clean_timesync_v2 + IMPROVED_DUB_FILL_POLICY (calculus_lesson_08 full-length)",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": source_desc,
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": "absolute sample offset (start*44100); atempo fit in [0.82,2.2]; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "tempo_floor": TEMPO_FLOOR,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
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
        "tail_expansions_applied": tail_expanded,
        "fill_expansions_applied": fill_expanded,
        "expansion_threshold_ratio": EXPAND_THRESHOLD_RATIO,
        "cues": placed,
    }

    print("[6/6] Mux with FULL original video (video copy) ...", flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
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

    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    odur = duration(OUT_VIDEO)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={report['output_duration_sec']}s size={report['output_size_bytes']}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap_s={max_internal_gap_s} policy_met={report['fill_policy_met']}", flush=True)
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
