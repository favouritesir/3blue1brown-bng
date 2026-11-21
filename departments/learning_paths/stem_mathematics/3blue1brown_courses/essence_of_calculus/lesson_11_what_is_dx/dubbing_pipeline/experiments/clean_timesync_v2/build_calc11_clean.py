"""
EXPERIMENT — Full-length clean absolute-sample Bengali dub
(Essence of Calculus, Lesson 11 — "What does dx really mean?" / derivative as magnification)

Adapted from the proven clean_timesync_v2 pipelines:
  probability/lesson_01/dubbing_pipeline/experiments/clean_timesync_v2/build_prob01_clean.py
  essence_of_calculus/lesson_10_taylor_series/dubbing_pipeline/experiments/clean_timesync_v2/build_calc10_clean.py

Guarantees (identical to the proven pipeline, plus IMPROVED_DUB_FILL_POLICY.md):
   1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
      half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
   2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
   3. IMPROVED FILL: atempo floor 0.82 (gentle slowdown), ceiling 2.2. Pad only,
      NEVER truncate. NO SFX: clean speech only.
   4. ADAPTIVE EXPANSION FIRST: any cue whose natural TTS is shorter than 78% of
      its (scaled) window gets section-aware pedagogical Bengali sentences
      appended and is re-synthesized until natural >= 80% of the window
      (policy requires median_fill >= 0.72 and max_internal_gap <= 1.5 s).
      Extra TAIL_EXPANSIONS + a FINAL-CUE CAP keep the closing inside the video.
   5. Fill metrics (per-cue fill, median_fill, max_internal_gap_s) are measured
      from the rendered waveform and written into verification.json.
   6. Canvas padded to the FULL original video duration so -shortest can never
      trim video frames.
   7. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
   8. Lightweight volumedetect (-vn -nostats, log to FILE) on intro 0-2 s and
      the final 2 s, written into verification.json.

Cue source (read-only; teacher audio / manifests are NEVER modified):
   1. A master script in this NEW dubbing_pipeline folder, if one is ever added.
      Its start/end/duration are in SECONDS -> converted x1000 to ms.
   2. web_platform/data/calculus/lesson_11.json -> its audio_manifest
      (assets/audio/calculus/lesson_11/manifest.json). The manifest stores
      start/end/duration in MILLISECONDS (e.g. 4920.0 == 4.92 s): NO x1000.
      Section keys appear twice (canonical id + alias) with identical cues;
      de-duplicated by (start_ms, text) so cues are not doubled.
   3. last resort: derive cues from the sections of lesson_11.json itself.

Everything is written under NEW experiment folders. Teacher audio, manifests
and other lessons are untouched.
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
BASE = EXP.parent.parent                        # .../lesson_11_what_is_dx/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "calculus" / "lesson_11.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "calculus" / "lesson_11" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "calculus" / "lesson_11" / "experiments" / "3b1b_calculus_11_full_dubbed.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"
EXPANDED_TEXT_CACHE = EXP / "_expanded_texts.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
TEMPO_FLOOR = 0.82                   # IMPROVED_DUB_FILL_POLICY.md
FADE_MS = 12
VIDEO_ID = "CfW845LNObM"
VIDEO_TITLE = "The other way to visualize derivatives | Chapter 12, Essence of calculus"
LESSON = "lesson_11_what_is_dx"

# Silence margins: keep 0-2 s and the final 2 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Adaptive expansion policy.
EXPAND_TRIGGER_RATIO = 0.78          # expand when natural < 78% of window
EXPAND_AIM_RATIO = 0.80              # keep appending until natural >= 80% of window
MAX_APPENDED_SENTENCES = 16
ACTIVE_THRESHOLD = 0.005             # above edge-TTS MP3 leakage floor (~0.004)

# Section-aware pedagogical Bengali sentences appended to short cues. They are
# cycled (never repeated inside one cue) and chosen for real teaching value —
# "what to notice / why it matters" — rather than generic filler.
EXPANSION_POOL = {
    "sec-the-dx-paradox": [
        "লক্ষ্য করুন, একই প্রতীকের দুটি ভিন্ন ভূমিকা রয়েছে—একটি সীমার ভাষায়, অন্যটি স্পর্শকের ভাষায়।",
        "যখন আমরা ডি এক্স গুণ করি আর কাটাকাটি করি, তখন আসলে রৈখিক আসন্নায়নের অনুপাত নিয়েই কাজ করি।",
        "ইতিহাসে নিউটন আর লাইবনিজের বিতর্কের কারণ ছিল ঠিক এই অস্পষ্টতা—অসীম ক্ষুদ্র কি শূন্য, না অশূন্য।",
        "বিশপ বার্কলির সমালোচনার উত্তরে পরবর্তীতে কশি ও ভাইয়ারস্ট্রাস সীমার কঠোর সংজ্ঞা দেন, কিন্তু লাইবনিজের প্রতীক টিকে গেল তার সহজবোধ্যতার জন্য।",
        "মনে রাখবেন, ভগ্নাংশের নিয়ম কাটাকাটি করতে পারি কারণ আমরা স্পর্শকের রৈখিক জগতে আছি—সীমাস্থ অবস্থায় এটি নিখুঁত ফল দেয়।",
        "এই পয়েন্টটি বারবার মনে হবে যখনই আমরা ডিফারেনশিয়াল সমীকরণ বা চলক প্রতিস্থাপন করব।",
        "এখন প্রশ্ন উঠতে পারে—তাহলে কি ডি এক্স আসলেই একটি সংখ্যা। উত্তর হলো, এটি একটি সসীম ক্ষুদ্র বিচ্যুতি, যাকে আমরা ইচ্ছেমতো ছোট করে নিতে পারি।",
        "গণিতে যেসব প্রতীক প্রথমে বিভ্রান্তিকর মনে হয়, পরে প্রায়শই সেগুলোই সবচেয়ে ফলপ্রসূ প্রমাণিত হয়।",
    ],
    "sec-tangent-line-geometry": [
        "কল্পনা করুন, আপনি বক্ররেখার ওই বিন্দুতে বিশালভাবে জুম করে দেখছেন—জুম বাড়ালে বক্ররেখা সরলরেখার মতো দেখাবে।",
        "স্পর্শক রেখা হলো সেই সরলরেখা যা ওই বিন্দুতে বক্ররেখার গতিভাব ধরে রাখে।",
        "আনুভূমিক দূরত্ব ডি এক্স আর উল্লম্ব দূরত্ব ডি ওয়াই—এই দুটির অনুপাতই হলো ঢাল।",
        "মূল বক্ররেখা বরাবর যে উল্লম্ব সরণ হয়, তা কিন্তু স্পর্শকের সরণ থেকে একটু আলাদা—এই পার্থক্যটিই পরের ধাপে গুরুত্বপূর্ণ হবে।",
        "লক্ষ্য করুন, ডি এক্স কোনো রহস্যময় অসীম সংখ্যা নয়; এটি যেকোনো সসীম সংখ্যা, যেমন শূন্য দশমিক এক বা শূন্য দশমিক শূন্য এক।",
        "যত ছোট ডি এক্স নেব, স্পর্শক আর বক্ররেখা তত বেশি মিলে যাবে—এখানেই ডিফারেনশিয়ালের শক্তি নিহিত।",
        "তাই ঢাল মানে কেবল একটি সংখ্যা নয়, এটি একটি রূপান্তর—ইনপুটের ছোট পরিবর্তনকে আউটপুটের পরিবর্তনে রূপ দেয়।",
        "একবার নিজে একটি সরলরেখা এঁকে দেখলে এই অনুপাতের কথা চিরদিন মনে থাকবে।",
    ],
    "sec-error-and-vanishing": [
        "টেইলর উপপাদনের এই অবশিষ্টাংশের ধারণাটি বুঝতে পারলেই বুঝা যায় কেন ক্যালকুলাস কাজ করে।",
        "প্রথম ক্রমের পদটি স্পর্শকের ঢাল থেকে আসে, আর বাকি সব পদ ক্রমশ ছোট হয়ে যায়।",
        "যখন ডি এক্স শূন্যের দিকে যায়, তখন ডি এক্স স্কয়ার আরও দ্রুত শূন্যের দিকে যায়—এই হলো মূল কথা।",
        "তাই ভগ্নাংশ কাটাকাটি কোনো যাদু নয়—এটি সঠিক কারণে কাজ করে, কারণ ত্রুটির অনুপাত শূন্যে মিলিয়ে যায়।",
        "চেইন রুলে আমরা আসলে একের পর এক রৈখিক রূপান্তরকে গুণ করি, আর রৈখিক জগতে ভগ্নাংশের নিয়ম অটুট থাকে।",
        "এই কারণেই ইন্টিগ্রালে প্রতিস্থাপনের সময় ডি এক্সকে গুণ করে নিতে হয়—নাহলে মাত্রা ভুল হয়ে যায়।",
        "ব্যবহারিক হিসাবে আমরা কয়েকটি পদ নিয়েই কাজ চালাই, কারণ বাকি পদগুলোর অবদান নগণ্য হয়ে পড়ে।",
        "মনে রাখবেন, ডিফারেনশিয়াবিলিটি মানেই হলো—এই অবশিষ্টাংশ শূন্যের দিকে ধাবিত হওয়া।",
    ],
    "sec-dx-in-integration": [
        "ইন্টিগ্রাল চিহ্নের ভেতরে থাকা ডি এক্স আসলে আমাদের বলে দেয় কোন চলকের সাথে ক্ষেত্রফলের ফালি গড়া হচ্ছে।",
        "রিম্যান সমষ্টিতে প্রতিটি সরু ফালির ক্ষেত্রফল উচ্চতা গুণ প্রস্থ—এই সহজ গুণটিই পরে অসীম সংখ্যক ফালির যোগফলে রূপ নেয়।",
        "লাইবনিজের লম্বা এস চিহ্নটি আসলে লাতিন শব্দ সুম্মার সংক্ষিপ্ত রূপ—এর অর্থ হলো যোগফল।",
        "যখন আমরা এক্সের বদলে ইউ চলক ব্যবহার করি, তখন ফালির প্রস্থও সেই অনুপাতে স্কেল হয়—তাই ডি ইউ যোগ করতে হয়।",
        "পদার্থবিজ্ঞানে এই মাত্রার হিসাব অপরিহার্য—বেগ গুণ সময় দূরত্ব দেয়, কারণ সেকেন্ড আর মিটার প্রতি সেকেন্ড কেটে যায়।",
        "ডি টি না থাকলে বেগের ইন্টিগ্রালের একক হতো অর্থহীন—এই ছোট্ট চিহ্নটি পুরো সমীকরণের ভৌত অর্থ বাঁচিয়ে রাখে।",
        "তাই ডি এক্স কেবল একটি বন্ধনী নয়; এটি ক্ষেত্রফলের ফালির প্রস্থ এবং মাত্রার ভারসাম্য—দুটোই।",
        "পরেরবার যখন ইন্টিগ্রাল দেখবেন, ডি এক্সের এই দুই ভূমিকা একসাথে মনে রাখার চেষ্টা করবেন।",
    ],
    "sec-modern-perspective": [
        "আধুনিক জ্যামিতিতে ডি এক্সকে দেখা হয় একটি পরিমাপক যন্ত্র হিসেবে, যা কোনো ভেক্টরের অনুভূমিক অংশ মাপে।",
        "এই দৃষ্টিভঙ্গিতে ডি এক্স কোনো ছোট সংখ্যা নয়, বরং একটি রৈখিক ফাংশন—একটি ওয়ান-ফর্ম।",
        "আপনি যখন একটি স্পর্শক ভেক্টর ইনপুট দেন, ডি এক্স আপনাকে বলে দেয় সেই ভেক্টরটি কতখানি এক্স দিকে এগিয়েছে।",
        "এই একই ধারণা বহুমাত্রিক জ্যামিতিতে প্রসারিত হয়, যেখানে প্রতিটি স্থানাঙ্কের নিজস্ব ডিফারেনশিয়াল থাকে।",
        "সুতরাং ডি এক্সের চারটি ভূমিকা—ছোট বিচ্যুতি, স্পর্শকের ভিত্তি, ইন্টিগ্রাল ফালির প্রস্থ, এবং ভেক্টর পরিমাপক—একই সত্যের বিভিন্ন দিক।",
        "আজকের পাঠে আমরা দেখলাম, একটি ছোট্ট প্রতীকের পেছনে রয়েছে তিনশত বছরের গণিতের বিবর্তন।",
        "পরের বার যখন কেউ বলবে ডি ওয়াই বাই ডি এক্স ভগ্নাংশ নয়, আপনি জানবেন কখন এটি ভগ্নাংশ আর কখন অপারেটর।",
        "সত্যিকারের বোঝাপড়া আসে যখন আমরা একই ধারণাকে একাধিক দৃষ্টিকোণ থেকে দেখতে পারি।",
    ],
}

DEFAULT_EXPANSIONS = [
    "এই ধারণাটি নিজের ভাষায় একবার বলে দেখলে বিষয়টি আরও পরিচ্ছন্ন হবে।",
    "লক্ষ্য করুন, এই অনুপাতই আমাদের আসল উত্তরের দিকে নিয়ে যায়।",
    "এখানে যুক্তিটি আবার মনে করিয়ে দিই, কারণ পরের ধাপে এটি বারবার কাজে লাগবে।",
    "গণিতের প্রতিটি প্রতীকের পেছনে একটি নির্দিষ্ট অর্থ থাকে—সেই অর্থটি আজ আমাদের মূল বিষয়।",
]

# Extra closing narration, applied only if a tail cue is still short after the
# main adaptive expansion. Keys are 1-based cue ids (the last three cues).
TAIL_EXPANSIONS = {
    34: " আরও মনে রাখবেন, আধুনিক গণিতে ডি এক্সকে এক একটি পরিমাপক হিসেবে দেখা হয়—এই দৃষ্টিভঙ্গি পরের অধ্যায়গুলোতে বারবার কাজে আসবে।",
    35: " সংক্ষেপে বললে, ডি এক্স একাধারে ছোট বিচ্যুতি, স্পর্শকের ভিত্তি, ইন্টিগ্রাল ফালির প্রস্থ এবং একটি ওয়ান-ফর্ম।",
    36: " আজ আমরা দেখলাম, স্পর্শকের রৈখিক জগতে ডি ওয়াই বাই ডি এক্স একটি নিখুঁত ভগ্নাংশ, আর সীমার মাধ্যমে এটি পরিবর্তনের হারকে নির্ভুলভাবে ধরে রাখে। পরের পাঠে আবার দেখা হবে।",
}


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


def cue_duration_ms(value):
    """Manifest durations are MILLISECONDS (e.g. 4920.0 == 4.92 s).

    Defensive unit check: a narration cue below 100 can only be expressed in
    SECONDS, so convert it to milliseconds. Master-script durations (if ever
    used) are converted x1000 by load_master_cues() before reaching here.
    """
    v = float(value or 0)
    if 0 < v < 100:
        return v * 1000.0
    return v


def load_master_cues():
    """Read a PRIMARY master script if one exists in this new folder.

    Master scripts store start/end/duration in SECONDS -> x1000 to ms.
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
        dur_s = c.get("duration")
        if dur_s is None:
            dur_s = (float(c.get("end", 0)) - float(c.get("start", 0)))
        out.append({
            "text": text,
            "dur_ms": float(dur_s) * 1000.0,
            "section": str(c.get("section", "master")),
        })
    if out:
        return out, f"master_script:{mpath.name} (seconds->ms x1000)"
    return None, None


def load_manifest_cues():
    """Read the audio_manifest referenced by lesson_11.json (read-only).

    Manifest timings are in MILLISECONDS (no x1000). Section keys appear twice
    (by id and by alias) with identical cues -> deduplicate by (start_ms, text).
    """
    lesson = json.loads(LESSON_JSON.read_text(encoding="utf-8"))
    rel = lesson.get("audio_manifest") or (lesson.get("meta") or {}).get("audio_manifest")
    if not rel:
        return None, None
    manifest = (LESSON_JSON.parent / rel).resolve()
    if not manifest.exists():
        return None, None
    data = json.loads(manifest.read_text(encoding="utf-8"))
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
        return out, f"audio_manifest:{manifest.name} (ms, alias-deduped, {len(out)} cues)"
    return None, None


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


def load_source_cues():
    out, desc = load_master_cues()
    if out:
        return out, desc
    out, desc = load_manifest_cues()
    if out:
        return out, desc
    lesson = json.loads(LESSON_JSON.read_text(encoding="utf-8"))
    return derive_from_lesson(lesson), "lesson_11.json:sections"


def load_cues(vend, source_cues):
    """Lay authored cues out cumulatively, then scale to span the full video."""
    authored_total = sum(c["dur_ms"] for c in source_cues) + INTER_CUE_PAUSE_MS * (len(source_cues) - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    scale = usable / (authored_total / 1000.0) if authored_total > 0 else 1.0

    # If this experiment was resumed after expansion, reuse the exact final
    # texts so cached raw audio and verification stay consistent.
    cached = {}
    if EXPANDED_TEXT_CACHE.exists():
        try:
            cached = {int(k): v for k, v in json.loads(EXPANDED_TEXT_CACHE.read_text(encoding="utf-8")).items()}
        except Exception:
            cached = {}

    cues = []
    cursor_ms = 0.0
    for i, c in enumerate(source_cues):
        cid = i + 1
        start = LEAD_IN_SEC + (cursor_ms / 1000.0) * scale
        dur = (c["dur_ms"] / 1000.0) * scale
        base = cached.get(cid, c["text"])
        cues.append({
            "id": cid,
            "start": round(start, 3),
            "end": round(start + dur, 3),
            "duration": round(dur, 3),
            "bn": base,
            "base_bn": c["text"],
            "expanded": cid in cached,
            "section": c["section"],
        })
        cursor_ms += c["dur_ms"] + INTER_CUE_PAUSE_MS
    return cues, scale


def save_expanded_texts(cues):
    cache = {c["id"]: c["bn"] for c in cues if c.get("expanded")}
    EXPANDED_TEXT_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


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


def predicted_fill(natural, target):
    """Actual fill when the 0.82 tempo floor is active."""
    if target <= 0 or natural <= 0:
        return 0.0
    return min(1.0, natural / (TEMPO_FLOOR * target))


async def expand_short_cues(cues):
    """IMPROVED_DUB_FILL_POLICY: append pedagogical sentences to any cue whose
    natural TTS is short of its scaled window, then re-synthesize. Multiple
    rounds; section-aware sentences keep the additions meaningful.
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
        current = base
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
            print(f"  expand cue {cid}: fill {predicted_fill(natural, target):.2f} "
                  f"natural={natural:.2f}s target={target:.2f}s +{n_sent} sent", flush=True)
            if await synth(new_text, raw, force=True):
                added += n_sent
                current = new_text
                natural = duration(raw)
                if natural >= EXPAND_AIM_RATIO * target:
                    break
            else:
                break
        if added > 0 and natural > 0:
            c["bn"] = current
            c["expanded"] = True
            expanded.append({
                "id": cid,
                "section": c["section"],
                "natural_before": round(before, 3),
                "natural_after": round(natural, 3),
                "sentences_added": added,
                "fill_before": round(predicted_fill(before, target), 3),
                "fill_after": round(predicted_fill(natural, target), 3),
            })
    save_expanded_texts(cues)
    return expanded


async def expand_tail_cues(cues):
    """Extra narration for the final three cues when still short of window."""
    expanded = []
    for c in cues[-3:]:
        cid = c["id"]
        if cid not in TAIL_EXPANSIONS:
            continue
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        target = float(c["duration"])
        natural = duration(raw)
        if 0 < natural < EXPAND_AIM_RATIO * target:
            new_text = sanitize(c["bn"] + " " + TAIL_EXPANSIONS[cid])
            print(f"  tail-expand cue {cid}: natural={natural:.2f}s < "
                  f"{EXPAND_AIM_RATIO*target:.2f}s", flush=True)
            if await synth(new_text, raw, force=True):
                expanded.append({
                    "id": cid,
                    "natural_before": round(natural, 3),
                    "natural_after": round(duration(raw), 3),
                })
                c["bn"] = new_text
                c["expanded"] = True
    if expanded:
        save_expanded_texts(cues)
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

    Final cue is capped so it always finishes inside the video.
    """
    natural = duration(raw)
    if natural <= 0:
        natural = target
    if cid == LAST_ID:
        # FINAL CUE CAP: must finish INSIDE the video, with a safety margin.
        target = min(target, VIDEO_END - LAST_START - 0.10)
    tempo = max(TEMPO_FLOOR, min(MAX_TEMPO, natural / target))
    tmp = out.with_suffix(".fit.wav")
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)
    # Fill = placed speech-clip samples / window samples (no dead air).
    window_n = max(1, int(round(target * SR)))
    speech_samples = min(len(arr), window_n)
    fill = speech_samples / window_n
    # Internal gap: longest silent run inside the clip (above MP3 leakage).
    idx = np.flatnonzero(np.abs(arr) > ACTIVE_THRESHOLD)
    max_gap_s = 0.0
    if idx.size > 1:
        max_gap_s = (int(np.diff(idx).max()) - 1) / SR
    need = window_n
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
    return arr, tempo, natural, target, fill, max_gap_s, speech_samples


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

    if not ORIGINAL_VIDEO.exists():
        raise SystemExit(f"ORIGINAL VIDEO MISSING: {ORIGINAL_VIDEO}")

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

    print("[2/6] Adaptive expansion of short cues (IMPROVED_DUB_FILL_POLICY) ...", flush=True)
    expanded = await expand_short_cues(cues)
    print(f"  expanded {len(expanded)} cues", flush=True)

    print("[2b/6] Tail expansion + final cue cap ...", flush=True)
    tail_expanded = await expand_tail_cues(cues)
    print(f"  tail-expanded {len(tail_expanded)} cues", flush=True)

    print("[3/6] Absolute sample placement (start*44100, tempo floor 0.82, pad-only) ...", flush=True)
    # FULL-length canvas: -shortest can never trim the video.
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    CHUNK = 1_000_000
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    fills = []
    gaps = []
    overrun = 0
    last_cue_end = 0.0
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            print(f"  SKIP cue {cid} (no audio)", flush=True)
            continue
        arr, tempo, natural, target, fill, max_gap_s, speech_samples = make_cue(
            raw, float(c["duration"]), CUE_DIR / f"cue_{cid:03d}.wav", cid)
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
        fills.append(fill)
        gaps.append(max_gap_s)
        expected_ms = round(float(c["start"]) * 1000, 2)
        actual_ms = round(start_sample / SR * 1000, 2)
        placed.append({
            "id": cid,
            "section": c["section"],
            "expected_start_ms": expected_ms,
            "actual_start_ms": actual_ms,
            "drift_ms": round(actual_ms - expected_ms, 6),
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3),
            "target_sec": round(target, 3),
            "speech_samples": speech_samples,
            "window_samples": int(round(target * SR)),
            "fill_ratio": round(fill, 4),
            "max_internal_gap_s": round(max_gap_s, 4),
            "placed_samples": placed_len,
            "expanded": c["expanded"],
        })

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

    print("[4/6] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    max_internal_gap = round(max(gaps), 4) if gaps else 0.0
    report = {
        "experiment": "clean_timesync_v2 (calculus_lesson_11 'What does dx really mean?' full-length, improved fill)",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "video_title": VIDEO_TITLE,
        "video_id_source": "web_platform/data/calculus/lesson_11.json (oEmbed verified; corrected from wrong duplicate)",
        "script_source": source_desc,
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": "absolute sample offset (start*44100); atempo floor 0.82; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "tempo_floor": TEMPO_FLOOR,
        "fill_policy": "IMPROVED_DUB_FILL_POLICY: adaptive pedagogical expansion of short cues, "
                       "median_fill>=0.72, max_internal_gap<=1.5s",
        "fill_definition": "placed speech-clip samples / window samples per cue",
        "median_fill": median_fill,
        "min_fill": round(min(fills), 4) if fills else 0.0,
        "max_fill": round(max(fills), 4) if fills else 0.0,
        "max_internal_gap_s": max_internal_gap,
        "fill_target_median": 0.72,
        "median_fill_ok": median_fill >= 0.72,
        "internal_gap_target_s": 1.5,
        "internal_gap_ok": max_internal_gap <= 1.5,
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
        "expanded_cues": expanded,
        "tail_expansions_applied": tail_expanded,
        "cues": placed,
    }

    print("[5/6] Mux with FULL original video (video copy) ...", flush=True)
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

    print("[6/6] Lightweight volumedetect ...", flush=True)
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    odur = duration(OUT_VIDEO)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={report['output_duration_sec']}s size={report['output_size_bytes']}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap={max_internal_gap}s "
          f"expanded={len(expanded)} tail={len(tail_expanded)}", flush=True)
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
