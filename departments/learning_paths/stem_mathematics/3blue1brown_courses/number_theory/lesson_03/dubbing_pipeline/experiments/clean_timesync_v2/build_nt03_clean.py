"""
EXPERIMENT - Full-length clean absolute-sample Bengali dub
(Number Theory, Lesson 03 - "Pi hiding in prime regularities")

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
BASE = EXP.parent.parent                        # .../number_theory/lesson_03/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "number_theory" / "lesson_03.json"
MANIFEST = WEB / "assets" / "audio" / "number_theory" / "lesson_03" / "manifest.json"

ORIGINAL_DIR = WEB / "media_vault" / "number_theory" / "lesson_03" / "original_source"
ORIGINAL_VIDEO = ORIGINAL_DIR / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "number_theory" / "lesson_03" / "experiments" / "3b1b_number_theory_03_full_dubbed.mp4"

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
VIDEO_ID = "NaL_Cb42WyY"
LESSON = "lesson_03"
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
    "source_url": "https://www.youtube.com/watch?v=NaL_Cb42WyY",
    "oembed_title": "Pi hiding in prime regularities",
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
            "canvas authority. Real duration ~1783 s (ffprobe).",
    "teacher_audio_and_manifests_modified": False,
}


# Section-aware pedagogical Bengali expansion sentences (one pool per manifest
# section). Fresh sentences are cycled, offset by cue index so different cues in
# the same section receive different wording.
EXPANSION_POOL = {
    "sec-leibniz-series": [
        "সতেরো শতকের সাতের দশকে গটফ্রিড লাইবনিজ এই সূত্রটি আবিষ্কার করেছিলেন যখন তিনি ক্যালকুলাস নিয়ে কাজ করছিলেন।",
        "এক বিয়োগ এক ভাগ তিন প্লাস এক ভাগ পাঁচ বিয়োগ এক ভাগ সাত প্লাস এক ভাগ নয়, এইভাবে পদ পর পদ চলতে থাকে।",
        "বাঁ দিকে কেবল সাধারণ ভগ্নাংশ আর ডান দিকে বৃত্তের পরিমাপ পাই ভাগ চার, এই মিলনই বিস্ময়কর।",
        "ধারাটির প্রতিটি পদ একটি বিজোড় সংখ্যার ব্যস্তানুপাতিক, আর চিহ্নগুলো ধনাত্মক ও ঋণাত্মক হয়ে পর্যায়ক্রমে আসে।",
        "প্রথম পদ এক, তারপর এক ভাগ তিন, তারপর এক ভাগ পাঁচ, এইভাবে হরগুলো দুই করে বাড়তে থাকে।",
        "আংশিক যোগফলগুলো পাই ভাগ চারের চারপাশে দোলে, প্রথমে এক, তারপর শূন্য দশমিক ছয় ছয় সাত।",
        "তারপর শূন্য দশমিক আট ছয় সাত, শূন্য দশমিক সাত দুই চার, করে ক্রমশ সঠিক মানের কাছে আসে।",
        "প্রতিটি নতুন পদ আগেরটির চেয়ে ছোট, তাই দোলনের প্রশস্ততা ক্রমশ কমতে থাকে।",
        "এই ধীর অভিসারী প্রকৃতির কারণে লাইবনিজের ধারা দিয়ে পাইয়ের মান হিসাব করা খুব ধীর।",
        "কয়েক লক্ষ পদ যোগ করলেও মাত্র কয়েকটি দশমিক স্থান পর্যন্ত নির্ভুল ফল পাওয়া যায়।",
        "এই সূত্রের সহজ ব্যাখ্যা আসে আর্কট্যান ফাংশন থেকে, যা ত্রিকোণমিতির একটি গুরুত্বপূর্ণ ফাংশন।",
        "জ্যামিতিক ধারা এক ভাগের এক প্লাস টি স্কয়ার সমান এক বিয়োগ টি স্কয়ার প্লাস টি পাওয়ার ফোর বিয়োগ, ইত্যাদি।",
        "এই ধারাকে শূন্য থেকে এক পর্যন্ত ইন্টিগ্রেট করলে আর্কট্যান এক পাওয়া যায়।",
        "আর আর্কট্যান এক সমান পাই ভাগ চার, কারণ একক বৃত্তে পঁয়তাল্লিশ ডিগ্রি কোণের ট্যানজেন্ট এক।",
        "আর্কট্যান এক্স সমান শূন্য থেকে এক্স পর্যন্ত এক ভাগের এক প্লাস টি স্কয়ারের ইন্টিগ্রাল।",
        "ইন্টিগ্রেট করে পাই এক্স বিয়োগ এক্স কিউব ভাগ তিন প্লাস এক্স পাওয়ার ফাইভ ভাগ পাঁচ, ইত্যাদি।",
        "এখানে এক্স সমান এক বসালেই লাইবনিজের বিখ্যাত ধারাটি ফিরে পাওয়া যায়।",
        "এই আবিষ্কারের গল্প আমাদের দেখায় কীভাবে একটি সরল দেখার ধারায় লুকোনো বৃত্ত ছিল।",
        "আসুন এখন দেখি এই পাই কীভাবে প্রাইম সংখ্যার নিয়মিততার সাথে যুক্ত।",
    ],
    "sec-gaussian": [
        "জটিল তলে পূর্ণসংখ্যার বিন্দুগুলো এ প্লাস বি আই এক একটি বর্গাকার ল্যাটিস তৈরি করে।",
        "এই ল্যাটিসের বিন্দুগুলোকে গাউসিয়ান পূর্ণসংখ্যা বলা হয়, যা কার্ল ফ্রিডরিখ গাউসের নামে পরিচিত।",
        "ব্যাসার্ধ আর এর বৃত্তের ভেতরে কতগুলো ল্যাটিস বিন্দু আছে তা গণনা করা যায়।",
        "বৃত্তের ক্ষেত্রফল পাই আর স্কয়ার হওয়ায় ভেতরের বিন্দুর সংখ্যাও প্রায় পাই আর স্কয়ার হয়।",
        "প্রশ্ন হলো কোন কোন পূর্ণসংখ্যা দুইটি বর্গের যোগফল হিসেবে লেখা যায়।",
        "উদাহরণস্বরূপ পাঁচ সমান এক স্কয়ার প্লাস দুই স্কয়ার, আর তেরো সমান দুই স্কয়ার প্লাস তিন স্কয়ার।",
        "হলুদ বিন্দুগুলো এমন সংখ্যা যারা দুই বর্গের যোগফল, বাকিরা কোনো বর্গ যুগল থেকে আসে না।",
        "ছবিতে দেখা যায় এই বিশেষ সংখ্যাগুলোর ঘনত্ব কতটা, আর তারা কীভাবে ছড়িয়ে আছে।",
        "প্রতিটি গাউসিয়ান পূর্ণসংখ্যার নর্ম এ প্লাস বি আই সমান এ স্কয়ার প্লাস বি স্কয়ার।",
        "নর্ম সমান এ প্লাস বি আই গুণ এ বিয়োগ বি আই, অর্থাৎ সংখ্যা আর তার কনজুগেটের গুণফল।",
        "এখন প্রশ্ন দাঁড়ায় কোন কোন পূর্ণসংখ্যা এনের জন্য এ স্কয়ার প্লাস বি স্কয়ার সমান এন সমাধান আছে।",
        "দুই বর্গের যোগফলের এই প্রশ্নটি সরাসরি নর্মের গুণনীয়ক থেকে উত্তর পায়।",
        "যে প্রাইম চার কে প্লাস এক আকারের, যেমন পাঁচ, তেরো, সতেরো, তা গাউসিয়ান পূর্ণসংখ্যায় দুটি গুণনীয়কে ভেঙে যায়।",
        "পাঁচ কে লেখা যায় দুই প্লাস আই আর দুই বিয়োগ আইয়ের গুণফল হিসেবে।",
        "কিন্তু চার কে প্লাস তিন আকারের প্রাইম ভেঙে যায় না, তাই দুই বর্গের যোগফলে শুধু প্রথম শ্রেণির প্রাইমের জোড় সংখ্যক ঘাতই চলে।",
        "দুইয়ের ক্ষেত্রে রয়েছে এক একক ব্যতিক্রম, কারণ দুই সমান এক প্লাস আই গুণ এক বিয়োগ আই।",
        "গাউসিয়ান পূর্ণসংখ্যার অনন্য ফ্যাক্টরাইজেশন আমাদের এই সম্পূর্ণ শ্রেণিবিভাগ দান করে।",
        "এই ফলাফল পরে অয়লারের গুণফলের সাথে মিলে পাইয়ের একটি নতুন রূপ প্রকাশ করবে।",
        "আসুন এখন দেখি বৃত্তের ভেতরের বিন্দু গণনা করে এই গুণফলটি কীভাবে পাওয়া যায়।",
    ],
    "sec-product": [
        "এখন বৃত্তের ভেতরের বিন্দু সংখ্যা দুইভাবে গণনা করি।",
        "একদিকে বৃত্তের ক্ষেত্রফল থেকে এটি প্রায় পাই আর স্কয়ার।",
        "অন্যদিকে প্রতিটি গাউসিয়ান পূর্ণসংখ্যার নর্ম এনের জন্য আর টু অফ এন সংখ্যক উপায়ে বিন্দু পড়ে।",
        "তাই মোট বিন্দু সংখ্যা হয় আর টু অফ এনের যোগফল, যা নর্মগুলোর ওপর নির্ভর করে।",
        "দুই হিসাব মিলিয়ে অয়লারের বিখ্যাত গুণফল পাওয়া যায়, যা পাই কে প্রাইমের সাথে যুক্ত করে।",
        "পাই ভাগ চার সমান চার একের সমান প্রাইমগুলোর পি ভাগ পি বিয়োগ একের গুণফল।",
        "আর সাথে গুণ থাকে চার তিনের সমান প্রাইমগুলোর পি ভাগ পি প্লাস একের গুণফল।",
        "গাউসিয়ান পূর্ণসংখ্যায় যে প্রাইম ভেঙে যায় তা পি ভাগ পি বিয়োগ এক অবদান রাখে।",
        "আর যে প্রাইম ভেঙে যায় না তা পি ভাগ পি প্লাস এক অবদান রাখে।",
        "পাঁচের ফ্যাক্টর পাঁচ ভাগ চার, তেরোর তেরো ভাগ বারো, আর তিনের তিন ভাগ চার, সাতের সাত ভাগ আট।",
        "এভাবে গুণ করে ক্রমশ পাই ভাগ চারের কাছে পৌঁছানো যায়, প্রতিটি বলয় একটি নতুন প্রাইমের অবদান দেখায়।",
        "সূত্রটি পড়া যায় এভাবে, প্রতিটি চার কে প্লাস এক প্রাইম পাই ভাগ চার কে পি ভাগ পি বিয়োগ এক গুণ বাড়ায়।",
        "আর প্রতিটি চার কে প্লাস তিন প্রাইম পি ভাগ পি প্লাস এক গুণ কমায়।",
        "পাঁচ দিয়ে শুরু করে ক্রমশ গুণ করতে থাকলে মানটি স্থির হয়ে পাই ভাগ চারে পৌঁছায়।",
        "কাই ফোর অফ পি নামক একটি চিহ্ন এই ধনাত্মক আর ঋণাত্মক অবদানকে সুন্দরভাবে প্রকাশ করে।",
        "কাই ফোর অফ দুই সমান শূন্য, চার একের সমান প্রাইমে এক, আর চার তিনের সমান প্রাইমে ঋণাত্মক এক।",
        "তাই পাই ভাগ চার সমান সব প্রাইম পি তে এক বিয়োগ কাই ফোর অফ পি ভাগ পি এর গুণফলের বিপরীত।",
        "এই গুণফল আর লাইবনিজের ধারা একই গাণিতিক বস্তুর দুটি রূপ, যা পরবর্তীতে দেখা যাবে।",
        "আসুন শেষ পরিচ্ছেদে এই দুই রূপের মিলনটি উপভোগ করি।",
    ],
    "sec-conclusion": [
        "এখন লাইবনিজের মূল ধারাটি আবার দেখুন, এক বিয়োগ এক ভাগ তিন প্লাস এক ভাগ পাঁচ।",
        "এই যোগ বিয়োগের পর্যায়ক্রম আসলে কাই ফোর অফ এনের মতোই।",
        "চার কে প্লাস একে ধনাত্মক, চার কে প্লাস তিনে ঋণাত্মক, আর দুইয়ে শূন্য।",
        "তাই লাইবনিজের ধারা আর অয়লারের গুণফল একই গাণিতিক বস্তুর দুটি রূপ।",
        "এই উপলব্ধিই আমাদের পুরো পাঠের কেন্দ্রীয় বার্তা, যা প্রথমে অসম্ভব মনে হয়েছিল।",
        "আরও এক কথা, একই কৌশল বেসেল সমস্যায় কাজ করে।",
        "এক প্লাস এক ভাগ চার প্লাস এক ভাগ নয়, ইত্যাদি সমান পাই স্কয়ার ভাগ ছয়।",
        "শুধু সেখানে কাই ফোরের বদলে সব প্রাইম অংশ নেয়, তাই ফলাফল পাইয়ের বর্গ হয়।",
        "আধুনিক সংখ্যাতত্ত্বে ধারা আর গুণফলের এই মিলন এক অত্যন্ত শক্তিশালী হাতিয়ার।",
        "এই কৌশল ব্যবহার করে অসংখ্য সমস্যার সমাধান করা যায়, যা একশো বছর আগেও অমীমাংসিত ছিল।",
        "পাই শুধু বৃত্তের সংখ্যা নয়, বরং প্রাইম সংখ্যার গভীর নিয়মেরও প্রতীক।",
        "আজকের যাত্রায় আমরা লাইবনিজ থেকে শুরু করে গাউসিয়ান পূর্ণসংখ্যা আর অয়লারের গুণফল পর্যন্ত এসেছি।",
        "প্রতিটি ধাপ আমাদের দেখিয়েছে কীভাবে ভিন্ন ভিন্ন গাণিতিক ক্ষেত্র একসাথে মিলে যায়।",
        "আসুন এই শিক্ষাসমূহ নিয়ে পরবর্তী পাঠের জন্য প্রস্তুত হই।",
        "পরের অধ্যায়ে আমরা নতুন গাণিতিক অ্যাডভেঞ্চারে যাব, যেখানে আরও অনেক লুকোনো সম্পর্ক আছে।",
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
        "experiment": "clean_timesync_v2 (number_theory_lesson_03 full-length, STRONG expansion, scale recomputed from rendered speech)",
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
