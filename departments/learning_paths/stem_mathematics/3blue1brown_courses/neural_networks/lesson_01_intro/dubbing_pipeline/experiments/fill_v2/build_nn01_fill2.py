"""
EXPERIMENT (fill_v2) — Full-length clean absolute-sample Bengali dub
(Neural Networks, Lesson 01 — "But what is a neural network?", aircAruvnKk)

RE-RENDER of the earlier clean_timesync_v2 dub, which left 48 silent pockets
(up to ~18 s each): that build stretched 49 seconds-based master-script cues
by 1.64x and held atempo at 1.0, so ~10-15 s of every window was dead air.

This build follows the quality-gated, scale-recomputed policy proven in:
    lockdown_math/lesson_08/.../clean_timesync_v2/build_lock08_clean.py
and IMPROVED_DUB_FILL_POLICY.md:

  1. Read the AUDIO MANIFEST (web_platform/assets/audio/neural_networks/
     lesson_01/manifest.json) as the dubbing script — 31 cues across 5
     sections, alias-deduped by section_id. Teacher audio/manifests are NEVER
     modified.
  2. edge_tts bn-BD-PradeepNeural; robust retries (0-byte purge, 12 attempts,
     half-split + sentence-split fallbacks, WinError 1450 retry).
  3. STRONG EXPANSION: every cue is grown with section-aware pedagogical
     Bengali sentences until the SUM of rendered natural speech spans the real
     probed video duration. Only NEW sentences are synthesized each round
     (incremental concat), so the run is resumable and not O(n^2).
  4. Recompute the timeline scale from the SUM OF RENDERED NATURAL SPEECH
     (never from authored manifest durations). Windows become proportional to
     each cue's measured TTS duration. With the 0.82 atempo floor the rendered
     fill is ~1.0 (tempo = 1/scale, well under the 2.2 ceiling).
  5. Absolute sample placement start*44100 -> ZERO cumulative drift. Pad only,
     NEVER truncate. NO SFX: clean speech only. Long in-cue silences (>1.0 s)
     are gently compressed.
  6. QUALITY GATE measured from the rendered waveform: median_fill >= 0.72 and
     max_internal_gap_s <= 1.5, with automatic extra-expansion + re-render if
     the gate fails.
  7. Canvas padded to the FULL original video duration so -shortest can never
     trim video frames; final cue capped to end inside the video.
  8. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
     The video source is NEVER swapped — the same original_source/full_original.mp4
     is reused.
  9. Lightweight volumedetect (-vn -nostats, log to FILE) on intro and final.

Everything new is written under NEW experiment folders:
    script/metadata : neural_networks/lesson_01_intro/dubbing_pipeline/experiments/fill_v2/
    output video    : web_platform/media_vault/neural_networks/lesson_01/experiments/fill_v2/
The previous video (3b1b_nn_01_full_dubbed.mp4) is left untouched as backup.
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
BASE = EXP.parent.parent                        # .../lesson_01_intro/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform

MANIFEST = WEB / "assets" / "audio" / "neural_networks" / "lesson_01" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "neural_networks" / "lesson_01" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "neural_networks" / "lesson_01" / "experiments" / "fill_v2" / "3b1b_nn_01_full_dubbed_fill2.mp4"

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
VIDEO_ID = "aircAruvnKk"
LESSON = "lesson_01_intro"
COURSE = "neural_networks"

LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0           # only used for the initial manifest layout

# Expansion / gate policy.
EXPAND_TARGET_FILL = 0.98
TARGET_NATURAL_SCALE = 1.10          # sum(natural) ~= usable / 1.10 -> tempo ~= 0.91
MAX_APPENDED_SENTENCES = 120
ACTIVE_THRESHOLD = 0.015
MAX_INTERNAL_SILENCE_S = 1.0         # compress pauses longer than this in-cue
CHARS_PER_CHUNK = 1700

# Notebook note (read-only provenance; no teacher asset is modified).
SOURCE_METADATA_NOTE = {
    "youtube_id": VIDEO_ID,
    "source_url": "https://www.youtube.com/watch?v=aircAruvnKk",
    "oembed_title": "But what is a neural network? | Chapter 1, Deep learning",
    "oembed_author_name": "3Blue1Brown",
    "script_source": "web_platform/assets/audio/neural_networks/lesson_01/manifest.json (31 cues, alias-deduped)",
    "video_source": "web_platform/media_vault/neural_networks/lesson_01/original_source/full_original.mp4 (NOT swapped)",
    "reason_for_rerender": "prior build left 48 silent pockets (up to 18 s); atempo was pinned to 1.0 on 1.64x-stretched windows",
    "teacher_audio_and_manifests_modified": False,
}


# ---------------------------------------------------------------------------
# Section-aware pedagogical Bengali sentences. Cycled (never repeated
# back-to-back inside one append) so every addition teaches real content.
# ---------------------------------------------------------------------------
EXPANSION_POOL = {
    "sec-intro-mnist": [
        "আসুন একটু থামি এবং ভেবে দেখি, আমাদের চোখে যে সংখ্যাটি এত সহজে ধরা পড়ে, সেটি কম্পিউটারের কাছে কত কঠিন।",
        "আঠাইশ গুণ আঠাইশ অর্থাৎ সাত আট চারটি ছোট্ট বাক্স, প্রতিটিতে একটিমাত্র উজ্জ্বলতার মান।",
        "এই সাত আট চারটি সংখ্যাই আমাদের গোটা ছবির ডিজিটাল রূপ, আর মানুষের চোখ এগুলোকে দেখে সরাসরি একটা অর্থ বের করে।",
        "আমাদের মস্তিষ্ক কিন্তু এই পিক্সেলের স্তূপ থেকে সরাসরি অর্থ বের করে ফেলে, এটি তার সবচেয়ে বিস্ময়কর ক্ষমতা।",
        "ভিজ্যুয়াল কর্টেক্সের নিউরনগুলো প্রথমে ছোট ছোট দাগ আর প্রান্ত চিনতে শুরু করে, তারপর সেগুলো জোড়া লাগিয়ে পূর্ণ অক্ষর গড়ে তোলে।",
        "ঠিক এই ধাপে ধাপে চেনার প্রক্রিয়াটিকেই আমরা একটি কৃত্রিম নেটওয়ার্কের মধ্যে নকল করতে চাই।",
        "প্রথাগত প্রোগ্রামিংয়ে আমরা বলি, যদি এই দাগ থাকে আর ওই বাঁক থাকে, তবে এটি তিন; কিন্তু হাতের লেখা প্রতিবারেই আলাদা।",
        "এই কারণেই নিয়ম ভিত্তিক কোড লেখা প্রায় অসম্ভব হয়ে পড়ে, কারণ সম্ভাব্য রূপের সংখ্যা অসীম।",
        "নিউরাল নেটওয়ার্ক কিন্তু নিয়ম লেখে না, সে উদাহরণ দেখে শিখে নিজের প্রতিক্রিয়া নিজেই তৈরি করে।",
        "এই হলো মূল পার্থক্য, একদিকে মানুষের লেখা নিয়ম, অন্যদিকে মেশিনের শিখে নেওয়া নিয়ম।",
        "গ্রান্ট স্যান্ডারসনের এই পাঠের উদ্দেশ্য হলো সেই শেখার যন্ত্রের ভেতরে কী চলে, তা জ্যামিতিকভাবে দেখানো।",
        "আমরা শেষ পর্যন্ত দেখব কীভাবে একটি সাধারণ গুণ ও যোগের যন্ত্র এই বিস্ময়কর কাজটি সম্পন্ন করে।",
        "তাই প্রথম ধাপ হলো প্রশ্নটি সঠিকভাবে উপলব্ধি করা, সংখ্যা চেনা আসলে কী ধরনের সমস্যা।",
        "মনে রাখবেন, এই ছোট্ট পিক্সেল গ্রিডই আমাদের পরবর্তী সব আলোচনার ভিত্তি।",
    ],
    "sec-neuron-layers": [
        "একটি নিউরনকে ভাবুন এক ছোট্ট পাত্র হিসেবে, যার ভেতরে শূন্য থেকে একের মধ্যে একটি সংখ্যা থাকে।",
        "এই সংখ্যাটিকেই আমরা বলি অ্যাক্টিভেশন, অর্থাৎ ওই নিউরনটি কতটা জ্বলজ্বল করছে।",
        "শূন্য মানে নিউরনটি সম্পূর্ণ নিষ্ক্রিয়, আর এক মানে সম্পূর্ণ সক্রিয়, মাঝের মানের অর্থ আংশিক সক্রিয়তা।",
        "আমাদের ইনপুট স্তরে ঠিক সাত আট চারটি নিউরন থাকে, কারণ ছবিতে সাত আট চারটি পিক্সেল আছে।",
        "প্রতিটি ইনপুট নিউরন সংশ্লিষ্ট পিক্সেলের উজ্জ্বলতা ধারণ করে, কালোর জন্য শূন্য আর সাদার জন্য এক।",
        "আর শেষের আউটপুট স্তরে থাকে দশটি নিউরন, যা শূন্য থেকে নয় পর্যন্ত প্রতিটি ডিজিটের আত্মবিশ্বাস প্রকাশ করে।",
        "দশটি নিউরনের মধ্যে যেটির মান সবচেয়ে বেশি, নেটওয়ার্কটি সেই ডিজিটটিকেই চিনে ফেলে।",
        "মাঝখানে যে দুটি স্তর থাকে, তাদের বলা হয় হিডেন লেয়ার, প্রতিটিতে ষোলোটি করে নিউরন।",
        "হিডেন মানে আমরা সরাসরি দেখতে পাই না, কিন্তু সেগুলোই আসল গণনা করে।",
        "প্রথম হিডেন লেয়ার ছোট ছোট প্রান্ত আর কোণ খোঁজে, দ্বিতীয়টি সেগুলো জোড়া লাগিয়ে অক্ষর গড়ে।",
        "এইভাবে স্তর পর স্তর করে বিমূর্ততা বাড়তে থাকে, আর শেষে পূর্ণ সংখ্যাটি ফুটে ওঠে।",
        "লক্ষ্য করুন, স্তরগুলোর সংখ্যা আর প্রতি স্তরের নিউরনের সংখ্যা আমরা নিজেরাই বেছে নিই।",
        "এই কাঠামোর নাম দেওয়া হয় আর্কিটেকচার, আর এর ওপরেই নেটওয়ার্কের ক্ষমতা নির্ভর করে।",
        "পরবর্তীতে আমরা দেখব এই স্তরগুলোর মধ্যে তথ্য কীভাবে প্রবাহিত হয়।",
    ],
    "sec-weights-biases": [
        "দুটি নিউরনের মধ্যে সংযোগের শক্তিকেই আমরা বলি ওজন বা ওয়েট।",
        "ধনাত্মক ওজন পরবর্তী নিউরনকে প্রজ্বলিত করে, ঋণাত্মক ওজন তাকে নিস্তেজ রাখে।",
        "ওজনের মান যত বড়, প্রভাব তত বেশি; ওজন শূন্য হলে সংযোগটি যেন বিচ্ছিন্ন।",
        "প্রতিটি ইনপুট নিউরন থেকে পরবর্তী স্তরের প্রতিটি নিউরনে আলাদা আলাদা ওজন থাকে।",
        "এই ওজনগুলো গুণ করা হয় সংশ্লিষ্ট অ্যাক্টিভেশনের সাথে, তারপর সব পদ যোগ করা হয়।",
        "এই যোগফলকে বলা হয় ওয়েটেড সাম, যা নিউরনটি কতটা উত্তেজিত হবে তা নির্ধারণ করে।",
        "এর সাথে যোগ হয় এক ধরনের অফসেট, যাকে বলা হয় বায়াস।",
        "ধনাত্মক বায়াস নিউরনটিকে সহজে জ্বলে উঠতে উৎসাহিত করে, ঋণাত্মক বায়াস বাধা দেয়।",
        "বায়াসকে ভাবুন এক ধরনের সীমা বা থ্রেশহোল্ড, যা নির্ধারণ করে কতটা ইনপুট লাগবে।",
        "কিন্তু এই যোগফল যেকোনো বড় সংখ্যা হতে পারে, তাই একে শূন্য ও একের মধ্যে আনতে হয়।",
        "এই কাজটি করে সিগময়েড ফাংশন, যা যেকোনো সংখ্যাকে শূন্য ও একের ব্যবধানে চেপে আনে।",
        "সিগময়েডের সূত্র হলো এক ভাগের এক যোগ ই টু দ্য পাওয়ার মাইনাস জেড।",
        "অত্যন্ত ঋণাত্মক ইনপুটে আউটপুট শূন্যের কাছে যায়, অত্যন্ত ধনাত্মকে একের কাছে।",
        "আধুনিক নেটওয়ার্কে সিগময়েডের জায়গায় রেলু ব্যবহৃত হয়, যা ঋণাত্মকে শূন্য দেয় আর ধনাত্মককে অবিকল পাঠায়।",
        "রেলু ব্যবহারে ভ্যানিশিং গ্রেডিয়েন্ট সমস্যা কমে আর প্রশিক্ষণ বহুগুণ দ্রুত হয়।",
        "তাই একটি নিউরনের চূড়ান্ত মান হলো সিগমা অফ ওয়েটেড সাম প্লাস বায়াস।",
    ],
    "sec-matrix-formulation": [
        "প্রতিটি নিউরনের জন্য আলাদা আলাদা সমীকরণ লেখা একদিকে যেমন ক্লান্তিকর, তেমনি অপ্রয়োজনীয়।",
        "লিনিয়ার অ্যালজেব্রা আমাদের এক লাইনে পুরো স্তরের গণনা প্রকাশ করতে দেয়।",
        "এখানে ওজনগুলোকে একটা ম্যাট্রিক্স হিসেবে আর অ্যাক্টিভেশনগুলোকে একটা ভেক্টর হিসেবে লেখা হয়।",
        "ম্যাট্রিক্সের প্রতিটি সারি পরবর্তী স্তরের একটি নির্দিষ্ট নিউরনে আগত সব ওজন ধারণ করে।",
        "ম্যাট্রিক্স গুণনের ফলে ওই সারি আর ইনপুট ভেক্টরের গুণফল ওই নিউরনের ওয়েটেড সাম হয়।",
        "এইভাবে একসাথে সব নিউরনের ওয়েটেড সাম বের হয়ে যায়, আলাদা আলাদা হিসেবের প্রয়োজন হয় না।",
        "সূত্রটি দাঁড়ায়, পরবর্তী স্তরের অ্যাক্টিভেশন সমান সিগমা অফ ডব্লিউ গুণ এ প্লাস বি।",
        "এখানে ডব্লিউ হলো ওজন ম্যাট্রিক্স, এ হলো অ্যাক্টিভেশন ভেক্টর আর বি হলো বায়াস ভেক্টর।",
        "ম্যাট্রিক্সের সারি আর কলামের এই গুছানোই আমাদের বলে দেয় কে কার কাছ থেকে কত শক্তি পাবে।",
        "এই রূপটি কেবল সংক্ষিপ্ত নয়, এটি নেটওয়ার্রের ভেতরের কাঠামোর সাথে মিশে আছে।",
        "আধুনিক গ্রাফিক্স প্রসেসর বা জিপিইউ এই ম্যাট্রিক্স গুণন অত্যন্ত দ্রুত সমান্তরালভাবে করে।",
        "আর তাই হাজার হাজার সংখ্যা একসাথে প্রক্রিয়া করা সম্ভব হয় কয়েক মিলিসেকেন্ডে।",
        "অ্যানিমেশনে দেখা যাচ্ছে ম্যাট্রিক্সের এক সারি ইনপুট ভেক্টরের সাথে গুণ হয়ে এক নিউরনের মান তৈরি করছে।",
        "সেই মানের সাথে বায়াস যোগ করে সিগময়েড আবার শূন্য থেকে একের মধ্যে নিয়ে আসে।",
        "এই একই অপারেশন বারবার প্রয়োগ করে আমরা সমগ্র নেটওয়ার্কে এগিয়ে যাই।",
        "মনে রাখবেন, ম্যাট্রিক্স গুণনই এই নেটওয়ার্কের মূল গণনার ইঞ্জিন।",
    ],
    "sec-parameter-counting": [
        "এই চার স্তরের সাধারণ নেটওয়ার্কটিতে মোট কতগুলো পরিবর্তনশীল সংখ্যা আছে, আসুন হিসেব করি।",
        "প্রথম স্তরে সাত আট চারটি ইনপুট থেকে ষোলোটি নিউরনে সংযোগ, অর্থাৎ সাত আট চার গুণ ষোলো ওজন।",
        "দ্বিতীয় স্তরে ষোলো থেকে ষোলো, অর্থাৎ ষোলো গুণ ষোলো ওজন।",
        "তৃতীয় স্তরে ষোলো থেকে দশ, অর্থাৎ ষোলো গুণ দশ ওজন।",
        "এই তিনটি যোগ করলে মোট ওজন দাঁড়ায় বারো হাজার নয়শো ষাটটি।",
        "এর সাথে বায়াস আছে ষোলো, ষোলো আর দশ, অর্থাৎ মোট বিয়াল্লিশটি।",
        "সুতরাং মোট প্যারামিটার বারো হাজার নয়শো ষাট যোগ বিয়াল্লিশ, অর্থাৎ তের হাজার দুইটি।",
        "প্রতিটি ওজন ও বায়াস একেকটি ছোট্ট নব বা স্লাইডারের মতো, যার মান আমরা বদলাতে পারি।",
        "এই তের হাজার দুইটি নবের সঠিক সমন্বয়ই নেটওয়ার্কের শেখার রহস্য।",
        "যখন আমরা বলি নেটওয়ার্ক শিখছে, তার অর্থ হলো এই নবগুলোর সঠিক মান খুঁজে বের করা।",
        "লক্ষ্য হলো এমন মান পাওয়া, যাতে যেকোনো হাতের লেখা দিলে সঠিক আউটপুট নিউরনটি জ্বলে ওঠে।",
        "পরের অধ্যায়ে দেখব গ্রেডিয়েন্ট ডিসেন্ট কীভাবে এই নবগুলোকে স্বয়ংক্রিয়ভাবে টিউন করে।",
        "প্রতিটি ভুলের জন্য নবগুলোকে সামান্য করে সাজানো হয়, আর এই প্রক্রিয়া বারবার চলে।",
        "অনেকগুলো ছোট ছোট সংশোধন মিলে শেষ পর্যন্ত নিখুঁত ফলাফল তৈরি করে।",
        "এইভাবে একটি নিউরাল নেটওয়ার্ক মূলত এক বিশাল বহুমাত্রিক গাণিতিক ফাংশন।",
        "সাত আট চারটি সংখ্যা ইনপুট নিয়ে সেটি দশটি সম্ভাব্যতা প্রদান করে।",
        "আর এই সম্পূর্ণ ফাংশনটি নির্ধারিত হয় মাত্র তের হাজার দুইটি সংখ্যা দ্বারা।",
    ],
}
DEFAULT_EXPANSIONS = [
    "এই ধারণাটি নিজের ভাষায় একবার বলে দেখলে বিষয়টি আরও পরিচ্ছন্ন হবে।",
    "লক্ষ্য করুন, এই অনুপাতই আমাদের আসল উত্তরের দিকে নিয়ে যায়।",
    "এখানে যুক্তিটি আবার মনে করিয়ে দিই, কারণ পরের ধাপে এটি বারবার কাজে লাগবে।",
]


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Cue loading — AUDIO MANIFEST IS THE DUBBING SCRIPT (read-only)
# ---------------------------------------------------------------------------
def load_source_cues():
    """Read web_platform/assets/audio/neural_networks/lesson_01/manifest.json.

    Sections are de-duplicated by section_id so alias keys cannot double cues.
    Cue texts are used verbatim as the dubbing script.
    """
    if not MANIFEST.exists():
        raise SystemExit(f"MANIFEST NOT FOUND: {MANIFEST}")
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
            out.append({
                "text": text,
                "dur_ms": float(c.get("duration_ms", 0)),
                "section": sid,
            })
    if not out:
        raise SystemExit(f"NO CUES IN MANIFEST: {MANIFEST}")
    return out, f"audio_manifest:{MANIFEST.name} (alias-deduped, {len(out)} cues)"


def load_cues(vend, source_cues):
    """Initial manifest-based layout (later RECOMPUTED from rendered speech)."""
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
    """Synthesize ONLY `text` and concat onto existing `raw` MP3 (no O(n^2))."""
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
        if natural >= per_cue_target and meta.exists():
            cached = json.loads(meta.read_text(encoding="utf-8"))
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
        for rnd in range(8):
            if natural >= per_cue_target or added >= MAX_APPENDED_SENTENCES:
                break
            rate_sec_per_char = natural / max(len(base), 1)
            need_chars = max(250, int((per_cue_target - natural) / max(rate_sec_per_char, 0.01)))
            append_text, n_sent = pick_append(pool, added, need_chars, MAX_APPENDED_SENTENCES - added)
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
                "id": cid, "section": c["section"],
                "natural_before": round(before, 3),
                "natural_after": round(natural, 3),
                "sentences_added": added,
                "final_chars": len(base),
                "target_sec": round(per_cue_target, 3),
            }
            meta.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
            expanded.append(entry)
    return expanded, per_cue_target


# ---------------------------------------------------------------------------
# Waveform helpers
# ---------------------------------------------------------------------------
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
    """Gently remove the excess of any in-cue silence longer than max_sil."""
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
    # If still longer (tempo cap), keep it -> recorded as overrun, never cut.
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


def recompute_layout_from_naturals(cues, vend):
    """Re-derive timeline scale from SUM OF RENDERED NATURAL SPEECH (not manifest).

    Windows are proportional to each cue's measured TTS duration so
    sum(windows) == usable timeline. With the 0.82 tempo floor the resulting
    waveform fill is ~1.0 (tempo = 1/scale, capped at 2.2 on the fast side).
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
            "id": cid, "section": c["section"],
            "expected_start_ms": expected_ms, "actual_start_ms": actual_ms,
            "drift_ms": round(actual_ms - expected_ms, 6),
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3), "target_sec": round(target, 3),
            "fit_samples": fit_samples, "window_samples": window_samples,
            "fill": round(fill, 4), "max_internal_gap_s": round(gap_s, 4),
            "placed_samples": placed_len, "expanded": cid in expanded_ids,
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
        alts = sorted((ORIGINAL_VIDEO.parent).glob("full_original.*"))
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
        "experiment": "fill_v2 (neural_networks lesson_01 full-length, heavy expansion, scale recomputed from rendered speech)",
        "lesson": LESSON,
        "course": COURSE,
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
        "video_source_path": str(src),
        "video_source_swapped": False,
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
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
