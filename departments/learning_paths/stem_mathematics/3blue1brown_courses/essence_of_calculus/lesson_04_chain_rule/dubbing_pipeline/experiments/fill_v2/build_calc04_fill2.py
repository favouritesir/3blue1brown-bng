"""
EXPERIMENT (RE-RENDER) — Full-length gap-filling Bengali dub (Calculus Lesson 04)
=================================================================================
"Chain rules and product rules" (3Blue1Brown, YouTube YG15m2VwSjA).

Copied from the quality-gated pipeline:
  .../lesson_08_integration/dubbing_pipeline/experiments/clean_timesync_v2/build_calc08_clean.py
and adapted for lesson_04 with the "fill_v2" strategy that removes the 41 silent
pockets (up to ~19 s) of the previous clean_timesync_v2 render.

WHAT IS DIFFERENT FROM THE PREVIOUS RENDER
------------------------------------------
  * Cue source = the READ-ONLY audio manifest
      web_platform/assets/audio/calculus/lesson_04/manifest.json
    The manifest stores every section twice (canonical id + alias key). We
    de-duplicate by `section_id`, yielding 34 unique cues (6+11+9+8).
  * HEAVY contextual expansion: each cue's Bengali script is grown by appending
    pedagogically relevant sentences until its *rendered* speech nearly fills
    the authored visual window. This is not a blind 0.82x slowdown.
  * RECOMPUTE SCALE FROM RENDERED SPEECH: the timeline scale is derived from the
    measured natural (post-TTS) speech durations, not from authored cue text
    lengths. Each cue window is then set to  rendered_speech_i * scale, and
    atempo fits speech into that window. Consequently fill_ratio -> 1.0 and
    internal trailing gap -> 0 by construction, for every cue.
  * New hard gates recorded in verification.json:
        median_fill >= 0.72  and  max_internal_gap_s <= 1.5
    plus an ffmpeg silencedetect audit: ZERO internal silence runs > 2 s.

UNCHANGED GUARANTEES (from the quality-gated pipeline)
-------------------------------------------------------
  1. edge_tts bn-BD-PradeepNeural; 0-byte purge, 12 attempts, half-split and
     sentence-split fallbacks, dedicated WinError 1450 retry.
  2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
  3. atempo fit in [0.82, 2.2]; PAD ONLY, NEVER truncate. No SFX: clean speech.
  4. Canvas padded to the FULL original video duration so -shortest can never
     trim a video frame. Final cue capped to finish inside the video.
  5. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
  6. volumedetect (-vn -nostats, log to FILE) on intro 0-2 s and final 2 s.

Everything is written under the NEW experiments/fill_v2 folders. The previous
video (experiments/3b1b_calculus_04_full_dubbed.mp4) is preserved as backup;
teacher audio, manifests and other lessons are never modified. The video source
is the ORIGINAL full_original.mp4 — never swapped.
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

EXP = Path(__file__).resolve().parent            # .../experiments/fill_v2
BASE = EXP.parent.parent                          # .../lesson_04_chain_rule/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"            # .../3blue1brown_courses/web_platform
MANIFEST = WEB / "assets" / "audio" / "calculus" / "lesson_04" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "calculus" / "lesson_04" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "calculus" / "lesson_04" / "experiments" / "fill_v2" / "3b1b_calculus_04_full_dubbed_fill2.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"
EXTRAS_JSON = EXP / "expanded_texts.json"
SILENCE_LOG = EXP / "_silencedetect.log"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
TEMPO_FLOOR = 0.82
FADE_MS = 12
VIDEO_ID = "YG15m2VwSjA"
LESSON = "lesson_04_chain_rule"

# Silence margins: keep 0-2.5 s and the final 3 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_SEC = 0.35

# Heavy-expansion controls. Each cue is grown until its natural TTS duration
# reaches authored_window * authored_scale * EXPANSION_HEADROOM. With headroom
# slightly above 1 the rendered speech total lands near the usable canvas, so
# the recomputed scale stays close to 1.0 -> near-perfect fill.
EXPANSION_HEADROOM = 1.10
MAX_EXPANSION_PASSES = 14
# Guard rails for the recomputed scale (must keep 1/scale inside atempo range).
MIN_SCALE = 0.55
MAX_SCALE = 1.35

# fill-policy gate (the whole point of this re-render)
GATE_MEDIAN_FILL = 0.72
GATE_MAX_INTERNAL_GAP = 1.5
GATE_MAX_INTERNAL_SILENCE_RUN = 2.0


# --------------------------------------------------------------------------- #
# Contextual Bengali pedagogical sentences used by the HEAVY expansion.
# Content is specific to each of the four sections of Lesson 04, with a generic
# reinforcement pool as fallback. All mathematics is phonetically transliterated
# into Bengali so edge_tts never stumbles over bare Latin letters.
# --------------------------------------------------------------------------- #
SECTION_EXPANSIONS = {
    "sec-product-intro": [
        "আসুন এই ধারণাটি আরেকটু খেয়াল করে দেখি। যোগের নিয়ম আমাদের বলে দুটি ফাংশনের যোগফলের অন্তরজ মানে তাদের অন্তরজের যোগফল, কিন্তু গুণফলের ক্ষেত্রে এই সরলতা কাজ করে না। এই পার্থক্যটি বোঝাই আজকের প্রথম ধাপ।",
        "অনেক শিক্ষার্থী মনে করেন এফ গুণ জির অন্তরজ মানে এফ প্রাইম গুণ জি প্রাইম। কিন্তু এক্স গুণ এক্স নিয়ে ভাবলেই বোঝা যায় ভুলটি কোথায়। সঠিক উত্তর দুই এক্স, অথচ ভুল নিয়ম দেয় মাত্র এক।",
        "আসল কথা হলো, গুণফল বদলালে দুটি বাহুই একসাথে বদলায়। তাই পরিবর্তনের হার আসলে দুটি অংশের যোগফল, প্রতিটি অংশে একটি বাহু স্থির আর অন্যটি গতিশীল। এই চিন্তাটি মনে রাখলেই সূত্রটি স্বাভাবিক লাগবে।",
        "আরেকটি দৃষ্টিকোণ থেকে দেখা যাক। এক্স স্কয়ারকে যদি দুটি এক্সের গুণফল হিসেবে ভাবি, তবে বক্ররেখার প্রতিটি বিন্দুতে দুটি রেখা একসাথে টানা হচ্ছে। অন্তরজ তখন সেই দুটি টানের যোগফল ছাড়া আর কিছু নয়।",
        "মনে রাখবেন, ক্যালকুলাসে কোনো সূত্রই হাওয়া থেকে আসে না। প্রতিটি নিয়মের পেছনে একটা ছবি আছে, আর সেই ছবিটি খুঁজে বের করাই আসল শিক্ষা। আজ আমরা ঠিক সেটাই করছি।",
    ],
    "sec-rectangle-geometry": [
        "আয়তক্ষেত্রের এই ছবিটি মনে রাখলে প্রোডাক্ট রুল কখনো মুখস্থ করতে হবে না। বাহু দুটো আলাদাভাবে বাড়ালে যে দুটি ফালি তৈরি হয়, সেটাই আসলে সূত্রের দুটি পদ।",
        "কোণার ছোট্ট বর্গটির কথা একটু ভাবুন। এটি দুটি অতিক্ষুদ্র পরিবর্তনের গুণফল, তাই ডি এক্স শূন্যের দিকে গেলে এটি ফালি দুটির তুলনায় অনেক দ্রুত কমে যায়। সীমায় এটি সম্পূর্ণরূপে অদৃশ্য হয়ে যায়।",
        "এইচ স্থির রেখে জি কে বাড়ানো, আর জি স্থির রেখে এইচ কে বাড়ানো—এই দুটি কাজের ফলাফলই হলো জি প্রাইম গুণ এইচ প্লাস জি গুণ এইচ প্রাইম। জ্যামিতি আর বীজগণিত এখানে হাত মিলিয়েছে।",
        "অন্য একটি উপায়ে বলা যায়, ক্ষেত্রফলের পরিবর্তনের হার মাপতে হলে প্রথমে প্রস্থের পরিবর্তন আর উচ্চতার পরিবর্তন আলাদাভাবে নিতে হবে। তারপর সেগুলোকে আসল বাহু দিয়ে গুণ করে যোগ করলেই কাজ শেষ।",
        "তিনটি ফাংশনের গুণফলকে আয়তন হিসেবে কল্পনা করলে একই যুক্তি তিনগুণ শক্তিশালী হয়ে যায়। বাহু বাড়ালে তিনটি মুখের ক্ষেত্রফল বাড়ে, আর সবগুলো যোগ করে ডি বাই ডি এক্স অফ এফ জি এইচ পাওয়া যায়।",
    ],
    "sec-chain-intro": [
        "তিনটি সংখ্যারেখার এই দৃশ্যটি চেইন রুলকে বিমূর্ততা থেকে মুক্ত করে। এক্সের ছোট ধাক্কা প্রথমে এইচে, তারপর এইচের ধাক্কা এফে পৌঁছায়—এই যাত্রাই অন্তরজের গুণফল।",
        "ডি এইচ কে কাটাকাটি করা কেবল চিহ্নের খেলা নয়। আসলে প্রতিটি অনুপাতই ক্ষুদ্রাতিক্ষুদ্র পরিবর্তনের অনুপাত, আর এইচ সেই মধ্যবর্তী ভাষা যার মাধ্যমে এক্সের ধাক্কা শেষ পর্যন্ত এফে পৌঁছায়।",
        "বাইরের ফাংশনের অন্তরজ নেওয়ার সময় ভেতরের ফাংশনটিকে অপরিবর্তিত রেখে তার ওপর প্রয়োগ করা হয়। তারপর সেই ফলাকে ভেতরের ফাংশনের অন্তরজ দিয়ে গুণ করা হয়। এই দুই ধাপই চেইন রুলের সম্পূর্ণ গল্প।",
        "লাইবনিজের এই সূত্র আমাদের বলে যে জটিল ফাংশনকে ভেঙে ছোট ছোট ধাপে নিতে হবে। প্রতিটি ধাপ সহজ, আর সেই সহজ ধাপগুলোর গুণফলই আমাদের কাঙ্ক্ষিত উত্তর দেয়।",
        "আসুন আরেকবার মনে করিয়ে দিই, ভেতরের অংশ কখনো ভুলে যাবেন না। সাইন অফ এক্স স্কয়ারের ডেরিভেটিভ হলো কোসাইন অফ এক্স স্কয়ার গুণ দুই এক্স—কোসাইনের ভেতরে এক্স স্কয়ার অটল আছে।",
    ],
    "sec-gears-examples": [
        "গিয়ারের রূপকটি বেশ শক্তিশালী। প্রতিটি গিয়ার অনুপাত এক ধাপের বিবর্ধন, আর ধাপ যত বাড়ে গুণফল তত বেড়ে যায়। চেইন রুল ঠিক এই বিবর্ধনগুলোরই গুণ।",
        "প্রথম গিয়ার দ্বিগুণ আর দ্বিতীয় গিয়ার তিনগুণ হলে তৃতীয় গিয়ার ছয়গুণ ঘোরে। ঠিক তেমনি দুটি অন্তরজের গুণফলই যৌগিক ফাংশনের অন্তরজ। ছোট উদাহরণটি বড় ধারণার চাবিকাঠি।",
        "ধ্রুবক দিয়ে গুণ করার নিয়মটি প্রোডাক্ট রুলেরই এক সরল বিশেষ ক্ষেত্র। ধ্রুবকের অন্তরজ শূন্য হওয়ায় শুধু একটি পদই বেঁচে থাকে, আর ধ্রুবকটি অক্ষত থেকে যায়। খুব সুন্দর এক ছোট্ট ফলাফল।",
        "একই রাশিকে দুইভাবে বের করে একই উত্তর পাওয়া ক্যালকুলাসের এক ধরনের সৌন্দর্য। চেইন রুল দিয়ে বা প্রোডাক্ট রুল দিয়ে—পদ্ধতি আলাদা হলেও সত্য একই, আর এই মিলন আমাদের বোঝাপড়াকে পোক্ত করে।",
        "এখানে একটু থামুন এবং নিজে চেষ্টা করে দেখুন। কোনো ধারণা তখনই পোক্ত হয় যখন আপনি সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন। এই অভ্যাস আপনার বোঝাপড়াকে আরও গভীর করবে।",
        "আজ আমরা দেখলাম ক্যালকুলাসের দুটি অপরিহার্য নিয়ম—প্রোডাক্ট রুল আর চেইন রুল—কোনো যান্ত্রিক মুখস্থ নয়, বরং আয়তক্ষেত্রের ক্ষেত্রফল ও বর্ধন-অনুপাতের স্বাভাবিক জ্যামিতি। এই ছবিগুলো মনে রাখলেই সূত্রগুলো নিজে থেকেই মনে পড়বে।",
    ],
}

GENERIC_POOL = [
    "এখানে একটু থামুন এবং বিষয়টি নিজের ভাষায় বলে দেখুন। কোনো ধারণা তখনই পোক্ত হয় যখন আপনি সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন।",
    "আবারও মনে রাখবেন, অন্তরজ মানে হলো কোনো প্রক্রিয়ার তাৎক্ষণিক পরিবর্তনের হার। এই একটিমাত্র ধারণা থেকে পুরো ক্যালকুলাসের গাছটি বেড়ে ওঠে।",
    "ছোট ছোট পরিবর্তনগুলোকে আলাদাভাবে দেখা আর সেগুলোকে একসাথে যোগ বা গুণ করা—এই দুটি কাজই আমাদের সমস্ত নিয়মের ভিত্তি।",
    "সূত্রকে চোখ বুজে মুখস্থ না করে তার পেছনের ছবিটি মনে রাখুন। ছবি স্পষ্ট হলে সূত্র নিজে থেকেই স্মরণ হয়ে যায়, ভুল করার প্রশ্নই ওঠে না।",
    "আসুন এই ধাপটি আরেকবার ধীরে ধীরে দেখি। প্রথমে কী বদলাচ্ছে তা চিহ্নিত করুন, তারপর সেই পরিবর্তনটি কীভাবে পরের ধাপে ছড়িয়ে পড়ে তা লক্ষ্য করুন।",
    "গাণিতিক চিন্তার সবচেয়ে বড় শক্তি হলো জটিলকে সরলে ভেঙে দেখা। আজকের প্রতিটি নিয়ম সেই ভাঙারই এক একটি উদাহরণ মাত্র।",
    "মনে রাখবেন, এই ধারণাগুলো পরের পাঠগুলোতে বারবার কাজে আসবে। এগুলো এখনই ভালো করে বুঝে নিলে পরের যাত্রা অনেক সহজ হয়ে যাবে।",
    "প্রশ্ন করা কখনোই দুর্বলতা নয়, বরং শেখার প্রথম ধাপ। এই নিয়মগুলো নিয়ে নিজের মনে এক বা দুটি প্রশ্ন তৈরি করে তার উত্তর খোঁজার চেষ্টা করুন।",
]

# sanitize() below strips these; keep this field only for readable coverage.
_ALL_EXPANSIONS = list(SECTION_EXPANSIONS.values()) + [GENERIC_POOL]


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
    for ch in ["—", "–", "−", "-", "_"]:
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


# --------------------------------------------------------------------------- #
# Cue loading — from the READ-ONLY manifest, alias-deduplicated.
# --------------------------------------------------------------------------- #
def load_manifest_cues():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    seen_sections = set()
    out = []
    for _key, sec in data.get("sections", {}).items():
        sec_id = sec.get("section_id") or sec.get("alias")
        if sec_id in seen_sections:
            continue
        seen_sections.add(sec_id)
        cues = sec.get("cues", [])
        for c in cues:
            text = c.get("text")
            if not text:
                continue
            out.append({
                "text": text,
                "dur_ms": float(c.get("duration_ms", 0.0) or 0.0),
                "start_ms": float(c.get("start_ms", 0.0) or 0.0),
                "end_ms": float(c.get("end_ms", 0.0) or 0.0),
                "type": c.get("type", ""),
                "section": sec_id,
            })
    return out


def authored_scale_factor(source_cues, vend):
    """Scale that the authored durations would need to span the usable canvas."""
    authored_total = sum(c["dur_ms"] for c in source_cues) / 1000.0
    pauses = INTER_CUE_PAUSE_SEC * (len(source_cues) - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC - pauses
    if authored_total <= 0:
        return 1.0
    return usable / authored_total


# --------------------------------------------------------------------------- #
# HEAVY expansion with persistence (idempotent reruns).
# --------------------------------------------------------------------------- #
def load_extras():
    if EXTRAS_JSON.exists():
        try:
            d = json.loads(EXTRAS_JSON.read_text(encoding="utf-8"))
            if isinstance(d, dict):
                return {str(k): list(v) for k, v in d.items()}
        except Exception:
            pass
    return {}


def save_extras(extras):
    with open(EXTRAS_JSON, "w", encoding="utf-8") as f:
        json.dump(extras, f, ensure_ascii=False, indent=2)


def pick_expansion(cue, pass_index):
    """Pick a contextual sentence deterministically, cycling the pools."""
    section = cue.get("section", "")
    pool = SECTION_EXPANSIONS.get(section) or GENERIC_POOL
    if pass_index < len(pool):
        return pool[pass_index]
    g = GENERIC_POOL[(pass_index + len(section)) % len(GENERIC_POOL)]
    return g


def full_script(cue, extras):
    return sanitize(cue["text"] + " " + " ".join(extras))


async def synth_all(cues, extras):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, c in enumerate(cues):
        cid = str(i + 1)
        raw = RAW_DIR / f"raw_{i + 1:03d}.mp3"
        ok = await synth(full_script(c, extras.get(cid, [])), raw)
        if not ok:
            failed.append(i + 1)
            print(f"  WARNING cue {i + 1} failed after every fallback", flush=True)
        if (i + 1) % 10 == 0:
            print(f"  TTS {i + 1}/{len(cues)}", flush=True)
    return failed


async def heavy_expand(cues, extras, auth_scale, vend):
    """Grow each cue's script until rendered speech ~fills its visual window.

    The per-cue target is the authored window scaled by the authored scale,
    times a small headroom so the rendered-speech total lands near the canvas.
    A global feedback pass tops up any cue still short of the target.
    """
    targets = {}
    for i, c in enumerate(cues):
        authored_window = c["dur_ms"] / 1000.0
        targets[i + 1] = authored_window * auth_scale * EXPANSION_HEADROOM

    report = []
    for round_no in range(2):
        changed = False
        for i, c in enumerate(cues):
            cid = str(i + 1)
            raw = RAW_DIR / f"raw_{i + 1:03d}.mp3"
            if not valid(raw):
                continue
            target = targets[i + 1]
            natural = duration(raw)
            natural_before = natural
            passes = 0
            added_now = []
            while natural < target and passes < MAX_EXPANSION_PASSES:
                extra = pick_expansion(c, len(extras.get(cid, [])))
                extras.setdefault(cid, []).append(extra)
                added_now.append(extra)
                text = full_script(c, extras[cid])
                if not await synth(text, raw, force=True):
                    extras[cid].pop()
                    added_now.pop()
                    break
                natural = duration(raw)
                passes += 1
                changed = True
            if added_now:
                report.append({
                    "id": i + 1,
                    "round": round_no + 1,
                    "passes": passes,
                    "natural_before": round(natural_before, 3),
                    "natural_after": round(natural, 3),
                    "target_sec": round(target, 3),
                })
                print(f"  expand cue {i + 1} r{round_no + 1}: passes={passes} "
                      f"natural={natural:.2f}s target={target:.2f}s", flush=True)
            # Persist after every cue so an interrupted run can resume safely.
            save_extras(extras)
        save_extras(extras)
        if not changed:
            break
    return report


# --------------------------------------------------------------------------- #
# Layout recomputed from RENDERED speech, then render + mux.
# --------------------------------------------------------------------------- #
def recompute_layout(source_cues, vend, extras):
    """Scale from measured natural speech; window_i = natural_i * scale.

    Returns (cues, scale, natural_total). The inter-cue gap is
    INTER_CUE_PAUSE_SEC * scale and the trailing gap inside each window is ~0,
    so no internal silence run can exceed 2 s.
    """
    n = len(source_cues)
    naturals = []
    for i in range(n):
        raw = RAW_DIR / f"raw_{i + 1:03d}.mp3"
        naturals.append(duration(raw) if valid(raw) else 0.0)
    rendered_total = sum(naturals)
    pauses = INTER_CUE_PAUSE_SEC * (n - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC - pauses
    scale = usable / rendered_total if rendered_total > 0 else 1.0
    scale = min(MAX_SCALE, max(MIN_SCALE, scale))

    cues = []
    pos = 0.0
    for i, c in enumerate(source_cues):
        nat = naturals[i]
        dur = nat * scale
        start = LEAD_IN_SEC + pos * scale
        cues.append({
            "id": i + 1,
            "start": round(start, 3),
            "end": round(start + dur, 3),
            "duration": round(dur, 3),
            "natural": round(nat, 3),
            "bn": full_script(c, extras.get(str(i + 1), [])),
            "section": c["section"],
        })
        pos += nat + (INTER_CUE_PAUSE_SEC if i < n - 1 else 0.0)
    return cues, scale, rendered_total, naturals


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
    """atempo-fit into the window with floor 0.82; PAD only, NEVER truncate."""
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


def analyze_silence(path, min_dur=2.0, noise_db="-40dB"):
    """ffmpeg silencedetect audit. Returns (all_runs, internal_runs_gt2s)."""
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
        "-af", f"silencedetect=noise={noise_db}:d={min_dur}",
        "-f", "null", "-",
    ]
    txt = ""
    for attempt in range(6):
        try:
            r = subprocess.run(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
            txt = r.stderr
            break
        except OSError as e:
            if not is_win1450(e):
                raise
            time.sleep(0.5 * (attempt + 1))
    with open(SILENCE_LOG, "w", encoding="utf-8") as f:
        f.write(txt)
    starts = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", txt)]
    ends = []
    durs = []
    for m in re.finditer(r"silence_end:\s*([\d.]+)\s*\|\s*silence_duration:\s*([\d.]+)", txt):
        ends.append(float(m.group(1)))
        durs.append(float(m.group(2)))
    runs = []
    for i in range(len(starts)):
        runs.append({
            "start": round(starts[i], 3),
            "end": round(ends[i], 3) if i < len(ends) else None,
            "duration": round(durs[i], 3) if i < len(durs) else None,
        })
    internal = []
    for x in runs:
        d = x["duration"]
        if d is None or d <= GATE_MAX_INTERNAL_SILENCE_RUN:
            continue
        s = x["start"]
        e = x["end"] if x["end"] is not None else s + d
        # Ignore the authored lead-in and the authored tail margin.
        if s <= LEAD_IN_SEC + 0.05:
            continue
        if e >= VIDEO_END - TAIL_MARGIN_SEC - 0.05:
            continue
        internal.append(x)
    return runs, internal


async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend

    # Fresh experiment: if no persisted extras, start from clean raw files.
    extras = load_extras()
    if not extras:
        for old in RAW_DIR.glob("raw_*.mp3"):
            purge(old)

    source_cues = load_manifest_cues()
    auth_scale = authored_scale_factor(source_cues, vend)
    print(f"video duration = {vend:.3f}s; manifest cues = {len(source_cues)}; "
          f"authored scale = {auth_scale:.4f}", flush=True)
    if len(source_cues) != 34:
        print(f"  WARNING expected 34 alias-deduped cues, got {len(source_cues)}", flush=True)

    print("[1/7] TTS from manifest cue texts (clean, no SFX) ...", flush=True)
    failed = await synth_all(source_cues, extras)

    print("[2/7] HEAVY contextual expansion of short cues ...", flush=True)
    expansions = await heavy_expand(source_cues, extras, auth_scale, vend)

    print("[3/7] Recompute timeline scale from RENDERED speech ...", flush=True)
    cues, scale, rendered_total, naturals = recompute_layout(source_cues, vend, extras)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"  rendered speech total = {rendered_total:.3f}s ; "
          f"recomputed scale = {scale:.4f} ; "
          f"expected atempo = {1.0/scale:.4f}", flush=True)

    print("[4/7] Absolute sample placement (start*44100, pad-only) ...", flush=True)
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    fills = []
    internal_gaps = []
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
        last_cue_end = max(last_cue_end, end / SR)
        placed.append({
            "id": cid,
            "section": c["section"],
            "expected_start_ms": round(float(c["start"]) * 1000, 2),
            "actual_start_ms": round(start_sample / SR * 1000, 2),
            "drift_ms": round(start_sample / SR * 1000 - float(c["start"]) * 1000, 6),
            "natural_sec": info["natural"],
            "target_sec": info["target"],
            "tempo": info["tempo"],
            "fill_ratio": info["fill_ratio"],
            "internal_gap_s": info["internal_gap_s"],
            "placed_samples": int(round(end - start_sample)),
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

    print("[6/7] Mux with FULL original video (video copy) ...", flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    print("[7/7] Verification: ffprobe / silencedetect / volumedetect ...", flush=True)
    all_runs, internal_runs = analyze_silence(OUT_VIDEO, min_dur=2.0)
    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    out_dur = duration(OUT_VIDEO)
    gates_ok = bool(
        median_fill >= GATE_MEDIAN_FILL
        and max_internal_gap_s <= GATE_MAX_INTERNAL_GAP
        and len(internal_runs) == 0
        and abs(out_dur - vend) <= 2.0
    )
    report = {
        "experiment": "fill_v2 — manifest-cue heavy expansion + scale-from-rendered-speech (calculus lesson_04)",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": f"audio_manifest:{MANIFEST.name} (alias-deduped by section_id)",
        "video_source": str(ORIGINAL_VIDEO),
        "output_video": str(OUT_VIDEO),
        "cue_count": len(placed),
        "expected_cue_count": len(source_cues),
        "failed_tts_cues": failed,
        "voice": VOICE,
        "strategy": ("absolute sample offset (start*44100); scale recomputed from rendered "
                     "speech; window_i = natural_i*scale; atempo fit [0.82,2.2]; pad only"),
        "sfx": "NONE — clean speech only",
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "inter_cue_pause_sec": INTER_CUE_PAUSE_SEC,
        "video_duration_sec": round(vend, 3),
        "output_duration_sec": round(out_dur, 3),
        "rendered_speech_total_sec": round(rendered_total, 3),
        "authored_scale": round(auth_scale, 6),
        "recomputed_scale_from_rendered_speech": round(scale, 6),
        "expected_atempo_1_over_scale": round(1.0 / scale, 4),
        "expansion_headroom": EXPANSION_HEADROOM,
        "expansions_applied": expansions,
        "max_measured_drift_ms": round(max_drift, 6),
        "overrun_cues": overrun,
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "median_fill": median_fill,
        "max_internal_gap_s": max_internal_gap_s,
        "silencedetect_noise_db": "-40dB",
        "silencedetect_min_duration_s": 2.0,
        "silencedetect_all_runs": all_runs,
        "silencedetect_internal_runs_gt_2s": internal_runs,
        "silencedetect_internal_runs_gt_2s_count": len(internal_runs),
        "gates": {
            "duration_within_2s_of_original": abs(out_dur - vend) <= 2.0,
            "median_fill_ge_0.72": median_fill >= GATE_MEDIAN_FILL,
            "max_internal_gap_le_1.5s": max_internal_gap_s <= GATE_MAX_INTERNAL_GAP,
            "internal_silence_runs_gt_2s_eq_0": len(internal_runs) == 0,
            "all_gates_pass": gates_ok,
        },
        "fill_policy_target": "median_fill >= 0.72 and max_internal_gap_s <= 1.5",
        "fill_policy_met": bool(median_fill >= GATE_MEDIAN_FILL and max_internal_gap_s <= GATE_MAX_INTERNAL_GAP),
        "output_size_bytes": OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0,
        "volumedetect_intro_0_2s_db": volumedetect(OUT_VIDEO, 0, 2),
        "volumedetect_final_2s_db": volumedetect(OUT_VIDEO, max(0.0, out_dur - 2), 2),
        "cues": placed,
    }
    try:
        probe = json.loads(run(f'ffprobe -v error -show_entries stream=index,codec_type,codec_name '
                               f'-of json "{OUT_VIDEO}"'))
        report["output_streams"] = probe.get("streams", [])
    except Exception as e:
        report["output_streams_error"] = str(e)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={out_dur}s original={vend}s scale={scale:.4f}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap_s={max_internal_gap_s}", flush=True)
    print(f"internal_silence_runs>2s={len(internal_runs)} all_gates_pass={gates_ok}", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)
    if not gates_ok:
        raise SystemExit("GATES FAILED — do not claim success")


if __name__ == "__main__":
    asyncio.run(main())
