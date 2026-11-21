"""
EXPERIMENT fill_v2 — RE-RENDER Bengali dubbed video for Calculus Lesson 03
===========================================================================
"Derivative formulas through geometry" (3Blue1Brown, S0_qX4VJhMQ).

Goal: ELIMINATE the 36 silent pockets (up to 26 s) of the previous
clean_timesync_v2 render WITHOUT touching teacher audio, manifests, the old
video, or any other lesson.

Adapted from the QUALITY-GATED script:
  essence_of_calculus/lesson_08_integration/dubbing_pipeline/experiments/
  clean_timesync_v2/build_calc08_clean.py
which applies web_platform/governance/IMPROVED_DUB_FILL_POLICY.md
(tempo floor 0.82, contextual pedagogical expansion, measured median_fill and
max_internal_gap_s).

WHAT IS NEW / DIFFERENT HERE
----------------------------
1. Cue source is the AUDIO MANIFEST (34 cues, alias-deduped), read-only:
   web_platform/assets/audio/calculus/lesson_03/manifest.json
   The cue *texts* are the dubbing script. Alias sections (sec_01_..., etc.)
   are duplicates of the canonical sec-... sections and are skipped.
2. HEAVY EXPANSION: every cue is grown with contextual Bengali pedagogical
   sentences (per-topic banks + a generic review pool) until its rendered
   TTS speech is long enough for its window. The expansion is measured, not
   guessed: synth -> ffprobe -> add more sentences -> synth again.
3. RECOMPUTE SCALE FROM RENDERED SPEECH: the timeline scale is NOT taken from
   the authored manifest durations. After all cues are rendered we measure
   their real speech durations and set
       scale = usable_speech_budget / sum(rendered_speech_durations)
   so each cue window = rendered_speech_i * scale. Because 1/scale stays in
   [0.82, 2.2] this yields atempo ~= 1/scale, fill ~= 1.0, internal gap ~= 0.
   (Initial per-cue targets use the manifest durations only to preserve the
   author's relative pacing.)
4. Absolute sample placement (start*44100) -> zero cumulative drift.
5. GATES recorded in verification.json AND checked after mux:
       median_fill >= 0.72
       max_internal_gap_s <= 1.5
       silencedetect internal runs > 2 s == 0
       full output duration ~= 1053 s
   No success is claimed unless the gates pass.
6. Everything is written under NEW experiments/fill_v2/ folders. The previous
   video (.../experiments/3b1b_calculus_03_full_dubbed.mp4) is left as backup.
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

# ---------------------------------------------------------------------------
# Paths (all writes confined to NEW fill_v2 folders)
# ---------------------------------------------------------------------------
EXP = Path(__file__).resolve().parent                       # .../experiments/fill_v2
BASE = EXP.parent.parent                                    # .../dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"                      # .../3blue1brown_courses/web_platform
MANIFEST = WEB / "assets" / "audio" / "calculus" / "lesson_03" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "calculus" / "lesson_03" / "original_source" / "full_original.mp4"
OUT_VIDEO = (WEB / "media_vault" / "calculus" / "lesson_03" / "experiments" /
             "fill_v2" / "3b1b_calculus_03_full_dubbed_fill2.mp4")

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
TEMPO_FLOOR = 0.82          # IMPROVED_DUB_FILL_POLICY: gentle natural slowdown
FADE_MS = 12
VIDEO_ID = "S0_qX4VJhMQ"
LESSON = "lesson_03_derivative_formulas"

LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_SEC = 0.35

# Heavy-expansion tuning.
CHAR_RATE_EST = 14.6         # chars/second used for the first expansion pass
TARGET_HEADROOM = 1.06       # aim slightly LONG (speed-up is harmless; short is not)
MAX_EXPANSION_PASSES = 6

# Gates
GATE_MEDIAN_FILL = 0.72
GATE_MAX_INTERNAL_GAP = 1.5
GATE_SILENCE_RUN = 2.0

# ---------------------------------------------------------------------------
# Contextual Bengali pedagogical expansion banks.
# Sentences are appended (after sanitize) to short cues. A per-topic bank is
# rotated first, then the generic review pool. Rotation by cue id keeps
# neighbouring cues from repeating the same sentence.
# ---------------------------------------------------------------------------
TOPIC_BANKS = {
    "sec_01_x2_geometry": [
        " আসুন এই বর্গটির ক্রমবর্ধমান প্রকৃতিটি আরও কিছুক্ষণ ধরে লক্ষ্য করি। বাহু বাড়ালে ক্ষেত্রফল যেভাবে বাড়ে, ঠিক সেই হারটিই আমরা অন্তরজ নামে অভিহিত করি।",
        " নীল অংশটি পুরনো বর্গ, আর হলুদ ও সবুজ অংশগুলো নতুন করে যোগ হওয়া ক্ষেত্রফল। ছবিটি মনে রাখলেই দুই এক্স সূত্রটি কখনো মুখস্থ করতে হবে না।",
        " ডান ধার আর উপরের ধার—এই দুটিই হলো সেই দুই এক্স। আর কোণার ছোট বর্গটি ডি এক্স স্কয়ার, যা সীমায় গিয়ে অদৃশ্য হয়ে যায়।",
        " কল্পনা করুন বর্গটির বাহু ক্রমাগত বাড়ছে। প্রতিটি মুহূর্তে নতুন যোগ হওয়া ফালির প্রস্থ ডি এক্স আর দৈর্ঘ্য প্রায় দুই এক্স—এটিই হলো অন্তরজের জ্যামিতিক ছবি।",
        " গাণিতিকভাবে বললে, ডি এফ সমান দুই এক্স গুণ ডি এক্স যোগ ডি এক্স স্কয়ার। ডি এক্স দিয়ে ভাগ করে ডি এক্স শূন্যের দিকে পাঠালেই অবশিষ্ট থাকে দুই এক্স।",
        " লেখচিত্রে ঢাল শূন্য বিন্দুতে শূন্য, একের কাছে এক, আর দুইয়ের কাছে দুই। এই ক্রমবৃদ্ধি আর বর্গের জ্যামিতি হুবহু মেলে—এটিই আমাদের বোঝার গভীরতা বাড়ায়।",
        " প্রশ্ন উঠতে পারে, ডি এক্স স্কয়ার পদটি কেন বাদ দিই? কারণ ডি এক্স যত ছোট হয়, তার বর্গ তত দ্রুত ছোট হয়—দ্বিতীয় ক্রমের এই পদ সীমায় শূন্য হয়ে যায়।",
        " মনে রাখবেন, সূত্র মুখস্থ করা আর সূত্র বোঝা এক জিনিস নয়। আজ আমরা বর্গটির ছবি দেখে সূত্রটি নিজেরাই আবিষ্কার করলাম—এই অভ্যাস পরবর্তীতে সব জায়গায় কাজে লাগবে।",
        " এক্স যখন ঋণাত্মক হয়, তখনো এই জ্যামিতি কাজ করে; কেবল ফালিগুলো বিপরীত দিকে যোগ হয়। তাই দুই এক্স সূত্রটি সব বাস্তব এক্সের জন্যই সত্য।",
    ],
    "sec_02_x3_volume": [
        " এবার ঘনকটির তিনটি উন্মুক্ত তলের দিকে তাকান। প্রতিটি তলের ক্ষেত্রফল এক্স স্কয়ার আর পুরুত্ব ডি এক্স—তিনটির মোট আয়তন থ্রি এক্স স্কয়ার গুণ ডি এক্স।",
        " ধার বরাবর সরু দণ্ড আর শীর্ঘের ছোট ঘনকগুলোর আয়তন ডি এক্সের দ্বিতীয় ও তৃতীয় ঘাত নিয়ে গঠিত। সীমায় এগুলো মারা যায়, টিকে থাকে শুধু প্রথম ঘাতের পদ।",
        " বর্গের দুটি ধার আর ঘনকের তিনটি তল—মাত্রা বাড়লেই যোগ হওয়া অংশের সংখ্যাও বাড়ে। এই সামঞ্জস্যই পাওয়ার রুলের জন্ম দেয়।",
        " ডি এক্স দিয়ে ভাগ করার পর থ্রি এক্স স্কয়ার পদটি আলাদা হয়ে দাঁড়ায়। এটি কোনো যাদু নয়, বরং তলগুলোর আয়তনের সরাসরি ফলাফল।",
        " লেখচিত্রে এক্স কিউবের ঢাল মূলবিন্দুতে শূন্য এবং দুই দিকে ক্রমশ বাড়ে। ছবিটি দেখে থ্রি এক্স স্কয়ারের আকারটি সহজেই চেনা যায়।",
        " এক মাত্রা উপরে উঠে আমরা দেখলাম কীভাবে জ্যামিতি নিজেই সূত্রটি লিখে দেয়। ভবিষ্যতে যেকোনো ঘাতের ক্ষেত্রে এই একই পদ্ধতি কাজে লাগবে।",
        " মনে রাখবেন, ডি এক্স কত ছোট হলো তা নিয়ে ভাবুন; যত ছোট হবে, তলগুলোর আয়তন তত বেশি নিখুঁতভাবে মোট বৃদ্ধি হিসেবে ধরা পড়বে।",
    ],
    "sec_03_power_rule": [
        " এক্স প্লাস ডি এক্সের ঘাতগুলো খুলে লেখলেই দেখা যায় প্রথম পদটিতে কতগুলো এক্স একসাথে গুণ হয়েছে। সেই সংখ্যাটিই আমাদের চাইছে এমন গুণাঙ্ক।",
        " দ্বিপদী বিস্তৃতির এই ধাপগুলো কেবল বীজগণিতের খেলা নয়—প্রতিটি পদ এক একটি জ্যামিতিক অংশের প্রতীক। তাই সূত্রটি মুখস্থ না করলেও চলবে।",
        " ঋণাত্মক ঘাতের ক্ষেত্রে ওয়ান বাই এক্স কে এক্স টু দ্য পাওয়ার মাইনাস ওয়ান হিসেবে লিখে নিন। তাহলে একই নিয়ম কোনো পরিবর্তন ছাড়াই কাজ করে।",
        " ভগ্নাংশ ঘাতের ক্ষেত্রে বর্গমূলের ছবিটি মনে রাখলেই হিসাব সহজ হয়। ক্ষেত্রফল আর বাহুর সম্পর্ক থেকে ডি এস বাই ডি এক্স সরাসরি পাওয়া যায়।",
        " এই সার্বজনীন সূত্রটি ক্যালকুলাসের সবচেয়ে ব্যবহৃত হাতিয়ার। ঘাত যেকোনো সংখ্যা হোক—ধনাত্মক, ঋণাত্মক কিংবা ভগ্নাংশ—ফলাফল একই নিয়মে মেলে।",
        " আসুন একবার নিজের ভাষায় বলে দেখি: ঘাতকে নিচে নামিয়ে এক কমালেই অন্তরজ পাওয়া যায়। এই ছোট্ট কৌশলটি কতটা শক্তিশালী তা আজ দেখলাম।",
        " পরবর্তী পাঠে ত্রিকোণমিতিক অপেক্ষকের ক্ষেত্রেও এই একই ছোট পরিবর্তনের ধারণা কাজে আসবে। তাই আজকের জ্যামিতিক চোখটি সঙ্গে রাখুন।",
    ],
    "sec_04_sine_geometry": [
        " একক বৃত্তের ওই ছোট ত্রিভুজটির উল্লম্ব বাহু আর অতিপর্বের অনুপাত ঠিক কোণের কোসাইনের সমান। ডি এক্স যত ছোট হবে, ছবিটি তত নিখুঁত হবে।",
        " বৃত্তের ব্যাসার্ধ এক হওয়ায় কোণ এক্স রেডিয়ান হলে চাপের দৈর্ঘ্যও ঠিক এক্স হয়। এই একক নির্বাচনই হিসাবটিকে এত পরিচ্ছন্ন করে তোলে।",
        " জুম করে দেখলে বাঁকা চাপটি সোজা রেখা হয়ে যায় আর সরণটি লম্ব হয়ে দাঁড়ায়। তখন সাইনের পরিবর্তন সরাসরি কোসাইন গুণ ডি এক্স হয়ে দেখা দেয়।",
        " ঘূর্ণিত সদৃশ ত্রিভুজের কারণে ছোট বাহুটির দৈর্ঘ্য কোসাইন গুণ ডি এক্স। ডি এক্স দিয়ে ভাগ করলেই আমাদের কাঙ্ক্ষিত ফল পাওয়া যায়।",
        " ডিওয়াই বাই ডিএক্স সমান কস এক্স—এই সূত্রটি কোনো স্মৃতি কৌশল নয়, বরং বৃত্তের নৃত্যের স্বাভাবিক পরিণতি। ছবিটি মনে থাকলে সূত্রটি নিজেই এসে যায়।",
        " লক্ষ্য করুন, কোণ শূন্য হলে কোসাইন এক, আর কোণ নব্বই ডিগ্রির কাছে গেলে কোসাইন শূন্যের কাছে যায়। সাইনের ঢালের এই আচরণ লেখচিত্রের সাথে হুবহু মেলে।",
        " আজ আমরা দেখলাম ক্যালকুলাসের প্রতিটি সূত্র আসলে জ্যামিতিরই একটি ভাষা। সূত্র মুখস্থ করার বদলে ছবিটি দেখতে শিখুন—ক্যালকুলাস তখন আর কঠিন লাগবে না।",
    ],
}

GENERIC_EXTRA = [
    " এখানে একটু থামুন এবং বিষয়টি নিজের ভাষায় বলে দেখুন। কোনো ধারণা তখনই পোক্ত হয় যখন আপনি সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন।",
    " আরও একটি দৃষ্টিকোণ থেকে দেখা যাক: এই উপপাদ্যটি কেবল একটি গাণিতিক পরিচয় নয়, বরং অসীম সংখ্যক ক্ষুদ্র অংশকে সসীম ও সুন্দর একটি উত্তরে রূপ দেওয়ার দার্শনিক বিজয়।",
    " মনে রাখবেন, ছোট পরিবর্তনগুলোকে গুরুত্ব দেওয়াই ক্যালকুলাসের মূল কৌশল। বড় পরিবর্তনকে ছোট ছোট টুকরোতে ভেঙে দেখলেই জটিলতা কমে যায়।",
    " আমরা কেবল ফলাফলই মুখস্থ করছি না; ফলাফলের পেছনের যুক্তিটিও নির্মাণ করছি। এই অভ্যাস আপনাকে অচেনা সমস্যার ক্ষেত্রেও সাহায্য করবে।",
    " লেখচিত্র, জ্যামিতি আর বীজগণিত—এই তিনটি ভাষা একই কথা তিনভাবে বলে। কোনোটি বুঝতে অসুবিধা হলে অন্য দুটির দিকে তাকালেই পথ পাওয়া যায়।",
    " সীমার ধারণাটি আজ বারবার কাজে এসেছে। ডি এক্স শূন্যের দিকে গেলে ঠিক কোন পদটি বেঁচে থাকে, তা বোঝা গেলেই হিসাবের অর্থ বোঝা হয়।",
    " আসুন এই ধাপটি আবার একবার মনের মধ্যে চালিয়ে দেখি। প্রথমে ছবিটি মনে আনুন, তারপর সূত্রটি লিখুন—তাহলে ভুল হওয়ার সম্ভাবনা অনেক কমে যাবে।",
    " শিক্ষার্থীদের জন্য একটি ছোট্ট পরামর্শ: প্রতিটি সূত্রের সাথে একটি করে ছবি যুক্ত করুন। সময়ের সাথে এই ছবিগুলোই আপনার মানসিক ক্যালকুলাসের ভিত্তি হয়ে যাবে।",
    " যখনই কোনো সূত্র অর্থহীন মনে হবে, তখনই বুঝতে হবে ছবিটি এখনো দেখা হয়নি। ক্যালকুলাসের সৌন্দর্য হলো প্রতিটি চিহ্নের পেছনে একটি দৃশ্যময় গল্প।",
    " এই পাঠে আমরা শুধু ডেরিভেটিভের সূত্রই শিখনি, শিখেছি কীভাবে প্রশ্ন তুলতে হয়। সঠিক প্রশ্নই সঠিক উত্তরের দিকে নিয়ে যায়—এটিই আসল শিক্ষা।",
    " অসীম ছোট অংশগুলোর যোগফল কীভাবে একটি সসীম সংখ্যা দেয়, তা আজ প্রতিটি ধাপে দেখলাম। এই উপলব্ধিই গণিতকে ভয়ের বদলে আনন্দের বিষয় করে তোলে।",
    " আপনি যদি আজকের ছবিগুলো মনে রাখতে পারেন, তবে ভবিষ্যতে কোনো সূত্র মুখস্থ করার প্রয়োজন হবে না। ছবিটি মনে পড়লেই সূত্রটি নিজেই তৈরি হয়ে যাবে।",
]


# ---------------------------------------------------------------------------
# Generic pipeline helpers (from the quality-gated calc08 script)
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
    out = run(f'ffprobe -v error -show_entries format=duration '
              f'-of default=noprint_wrappers=1:nokey=1 "{path}"')
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


# ---------------------------------------------------------------------------
# NEW: manifest cue loading (alias-deduped)
# ---------------------------------------------------------------------------
def load_manifest_cues():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    seen_aliases = set()
    cues = []
    for sec_id, sec in data.get("sections", {}).items():
        alias = sec.get("alias") or sec.get("section_id") or sec_id
        # Alias sections are duplicates (sec_01_..., sec_02_...) of the
        # canonical sections (sec-x2-geometry, ...). Keep the first only.
        if alias in seen_aliases:
            continue
        seen_aliases.add(alias)
        for c in sec.get("cues", []):
            text = c.get("text")
            if not text:
                continue
            cues.append({
                "id": len(cues) + 1,
                "text": text,
                "section": alias,
                "manifest_duration_ms": float(c.get("duration_ms", 0)),
                "manifest_start_ms": float(c.get("start_ms", 0)),
                "manifest_end_ms": float(c.get("end_ms", 0)),
            })
    return cues


# ---------------------------------------------------------------------------
# NEW: heavy expansion helpers
# ---------------------------------------------------------------------------
def _bank_for(cue):
    topic = list(TOPIC_BANKS.get(cue["section"], []))
    return topic + GENERIC_EXTRA


def _take_sentences(cue, need_chars, offset):
    """Pick bank sentences totalling >= need_chars, rotating by cue id."""
    bank = _bank_for(cue)
    picked = []
    n = len(bank)
    total = 0
    k = 0
    while total < need_chars and k < n * 4:
        s = bank[(cue["id"] * 5 + offset + k) % n]
        picked.append(s)
        total += len(s)
        k += 1
    return picked


def build_initial_text(cue, target_natural):
    """First heavy-expansion pass: grow text to ~target_natural * CHAR_RATE_EST."""
    base = sanitize(cue["text"])
    target_chars = max(len(base) + 40,
                       int(target_natural * CHAR_RATE_EST * TARGET_HEADROOM))
    need = max(40, target_chars - len(base))
    sentences = _take_sentences(cue, need, 0)
    return sanitize(base + " " + " ".join(sentences)), len(sentences)


async def expand_to_target(cue, target_natural):
    """Measured expansion loop: synth, ffprobe, add sentences, repeat."""
    cid = cue["id"]
    raw = RAW_DIR / f"raw_{cid:03d}.mp3"
    text, n0 = build_initial_text(cue, target_natural)
    ok = await synth(text, raw, force=True)
    natural = duration(raw) if ok else 0.0
    added = n0
    passes = 1
    for attempt in range(MAX_EXPANSION_PASSES - 1):
        if natural >= target_natural * 0.98:
            break
        need = int((target_natural - natural) * CHAR_RATE_EST * TARGET_HEADROOM) + 60
        more = _take_sentences(cue, need, added)
        if not more:
            break
        new_text = sanitize(text + " " + " ".join(more))
        print(f"  fill-expand cue {cid:>2} pass {passes+1}: "
              f"natural={natural:5.2f}s < {target_natural:5.2f}s "
              f"(+{len(more)} sentences)", flush=True)
        if not await synth(new_text, raw, force=True):
            break
        text = new_text
        added += len(more)
        natural = duration(raw)
        passes += 1
    return {
        "id": cid,
        "natural_before": round(duration(raw) if ok else 0.0, 3),
        "target_natural": round(target_natural, 3),
        "sentences_added": added,
        "passes": passes,
        "ok": ok,
        "text_chars": len(text),
    }


# ---------------------------------------------------------------------------
# PCM / cue rendering (kept from the quality-gated script)
# ---------------------------------------------------------------------------
def read_pcm(path):
    norm = path.with_suffix(".norm.wav")
    run(f'ffmpeg -y -i "{path}" -af aresample=44100 -ar 44100 -ac 1 '
        f'-c:a pcm_s16le "{norm}" > NUL 2>&1')
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

    Returns (arr, info) with measured fill ratio and internal silence gap.
    """
    natural = duration(raw)
    if natural <= 0:
        natural = target
    if cid == LAST_ID:
        target = min(target, VIDEO_END - LAST_START - 0.10)
    tempo = max(TEMPO_FLOOR, min(MAX_TEMPO, natural / target))
    tmp = out.with_suffix(".fit.wav")
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 '
        f'-c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)
    speech_samples = len(arr)
    need = int(round(target * SR))
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


def silencedetect(path, min_dur=GATE_SILENCE_RUN):
    """Return silence intervals (start, end, duration) longer than min_dur."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-af", f"silencedetect=noise=-50dB:d={min_dur}", "-f", "null", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    txt = proc.stderr
    starts = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", txt)]
    ends = [(float(a), float(b)) for a, b in
            re.findall(r"silence_end:\s*([\d.]+)\s*\|\s*silence_duration:\s*([\d.]+)", txt)]
    runs = []
    for i, s in enumerate(starts):
        if i < len(ends):
            e, d = ends[i]
        else:
            e, d = s + min_dur, min_dur
        runs.append((round(s, 3), round(e, 3), round(d, 3)))
    return runs


def internal_silence_runs(path, out_dur):
    """Silence >2s that is NOT the intentional lead-in or outro."""
    all_runs = silencedetect(path, GATE_SILENCE_RUN)
    internal = []
    for s, e, d in all_runs:
        # Ignore the deliberate head silence (starts ~0) and tail silence
        # (ends at/after video end). Anything wholly inside is a pocket.
        if s <= LEAD_IN_SEC + 0.5:
            continue
        if e >= out_dur - TAIL_MARGIN_SEC - 0.5:
            continue
        internal.append({"start": s, "end": e, "duration": d})
    return all_runs, internal


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend

    source_cues = load_manifest_cues()
    n = len(source_cues)
    if n == 0:
        raise RuntimeError("No cues loaded from manifest (alias-dedup gave zero)")

    # Budget: full video minus lead-in, outro and inter-cue pauses.
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    pause_total = INTER_CUE_PAUSE_SEC * (n - 1)
    speech_budget = usable - pause_total
    manifest_total_ms = sum(c["manifest_duration_ms"] for c in source_cues)
    manifest_total_s = manifest_total_ms / 1000.0

    # Initial per-cue TARGETS use manifest durations ONLY to preserve the
    # author's relative pacing. After rendering, the real scale is recomputed
    # from measured speech (see below).
    pace_factor = (speech_budget / manifest_total_s) if manifest_total_s > 0 else 1.0
    targets = [c["manifest_duration_ms"] / 1000.0 * pace_factor for c in source_cues]

    print(f"video duration = {vend:.3f}s; manifest cues = {n} "
          f"(manifest total {manifest_total_s:.1f}s); "
          f"speech budget = {speech_budget:.1f}s; pace_factor = {pace_factor:.4f}",
          flush=True)

    print("[1/6] TTS + HEAVY measured expansion (topic banks + generic pool) ...", flush=True)
    expansions = []
    for i, (cue, tgt) in enumerate(zip(source_cues, targets)):
        info = await expand_to_target(cue, tgt)
        expansions.append(info)
        if not info["ok"]:
            print(f"  WARNING cue {cue['id']} TTS failed!", flush=True)
        if (i + 1) % 5 == 0:
            print(f"  TTS+expand {i+1}/{n}", flush=True)

    # ----- RECOMPUTE SCALE FROM RENDERED SPEECH -----------------------------
    rendered = []
    for cue in source_cues:
        raw = RAW_DIR / f"raw_{cue['id']:03d}.mp3"
        rendered.append(duration(raw) if valid(raw) else 0.0)
    rendered_total = sum(rendered)
    if rendered_total <= 0:
        raise RuntimeError("No rendered speech — cannot compute scale")

    # scale maps rendered speech -> window length so the timeline exactly
    # spans the usable video. 1/scale is the atempo; it must lie in
    # [TEMPO_FLOOR, MAX_TEMPO] for fill == 1.0 on every cue.
    scale = speech_budget / rendered_total
    print(f"rendered speech total = {rendered_total:.1f}s; "
          f"RECOMPUTED SCALE (from rendered speech) = {scale:.5f}", flush=True)
    if not (TEMPO_FLOOR <= (1.0 / scale) <= MAX_TEMPO):
        print(f"  WARNING: 1/scale={1.0/scale:.3f} outside "
              f"[{TEMPO_FLOOR},{MAX_TEMPO}] — fill may be clamped", flush=True)

    # Lay out cues cumulatively using the rendered-speech-derived windows.
    cues = []
    cursor_s = LEAD_IN_SEC
    for cue, nat in zip(source_cues, rendered):
        window = nat * scale
        cues.append({
            "id": cue["id"],
            "section": cue["section"],
            "start": round(cursor_s, 3),
            "end": round(cursor_s + window, 3),
            "duration": round(window, 3),
            "bn": cue["text"],
            "rendered_natural": round(nat, 3),
        })
        cursor_s += window + INTER_CUE_PAUSE_SEC

    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"last cue ends at ~{cues[-1]['end']:.2f}s (video {vend:.2f}s)", flush=True)

    print("[2/6] Absolute sample placement (start*44100, pad-only, floor 0.82) ...", flush=True)
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    fills = []
    internal_gaps = []
    overrun = 0
    last_cue_end = 0.0
    expanded_ids = {x["id"] for x in expansions}
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            print(f"  SKIP cue {cid} (no audio)", flush=True)
            continue
        arr, info = make_cue(
            raw, float(c["duration"]), CUE_DIR / f"cue_{cid:03d}.wav", cid)
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
            "rendered_natural_sec": c["rendered_natural"],
            "tempo": info["tempo"],
            "window_sec": info["target"],
            "fill_ratio": info["fill_ratio"],
            "internal_gap_s": info["internal_gap_s"],
            "placed_samples": placed_len,
            "expanded": cid in expanded_ids,
        })

    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    max_internal_gap_s = round(max(internal_gaps), 4) if internal_gaps else 0.0
    print(f"  median_fill = {median_fill} ; max_internal_gap_s = {max_internal_gap_s}",
          flush=True)

    print("[3/6] Peak-normalise + WAV master + loudnorm -14 LUFS ...", flush=True)
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

    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 '
        f'-c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 '
        f'-c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    print("[4/6] Mux with FULL original video (video copy) ...", flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    print("[5/6] Verify output (duration / silencedetect / fill gates) ...", flush=True)
    out_dur = duration(OUT_VIDEO)
    all_sil, internal = internal_silence_runs(OUT_VIDEO, out_dur)
    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)

    dur_ok = abs(out_dur - vend) <= 2.0
    fill_ok = median_fill >= GATE_MEDIAN_FILL
    gap_ok = max_internal_gap_s <= GATE_MAX_INTERNAL_GAP
    silence_ok = len(internal) == 0
    all_gates = dur_ok and fill_ok and gap_ok and silence_ok

    report = {
        "experiment": "fill_v2 — manifest cues + heavy expansion + rendered-speech scale (calculus lesson_03)",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": f"audio_manifest:{MANIFEST.name} (alias-deduped)",
        "cue_count": len(placed),
        "expected_cue_count": n,
        "failed_tts_cues": [x["id"] for x in expansions if not x["ok"]],
        "strategy": "absolute sample offset (start*44100); scale RECOMPUTED from rendered speech; atempo [0.82,2.2]; pad only; no SFX",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "tempo_floor": TEMPO_FLOOR,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "timeline_scale": round(scale, 6),
        "scale_source": "rendered_speech",
        "rendered_speech_total_sec": round(rendered_total, 3),
        "speech_budget_sec": round(speech_budget, 3),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "median_fill": median_fill,
        "max_internal_gap_s": max_internal_gap_s,
        "fill_policy_target": f"median_fill >= {GATE_MEDIAN_FILL} and max_internal_gap_s <= {GATE_MAX_INTERNAL_GAP}",
        "fill_policy_met": bool(fill_ok and gap_ok),
        "expansion_summaries": expansions,
        "output_video": str(OUT_VIDEO),
        "output_duration_sec": round(out_dur, 3),
        "output_size_bytes": OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0,
        "silencedetect_all_runs": all_sil,
        "silencedetect_internal_runs_over_2s": internal,
        "internal_runs_over_2s_count": len(internal),
        "gates": {
            "duration_ok": bool(dur_ok),
            "median_fill_ok": bool(fill_ok),
            "max_internal_gap_ok": bool(gap_ok),
            "silence_internal_ok": bool(silence_ok),
            "all_gates_pass": bool(all_gates),
        },
        "cues": placed,
    }
    try:
        probe = json.loads(run(f'ffprobe -v error -show_entries stream=index,codec_type,codec_name '
                               f'-of json "{OUT_VIDEO}"'))
        report["output_streams"] = probe.get("streams", [])
    except Exception as e:
        report["output_streams_error"] = str(e)

    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    report["volumedetect_final_2s_db"] = volumedetect(
        OUT_VIDEO, max(0.0, out_dur - 2), 2)

    print("[6/6] Writing verification.json ...", flush=True)
    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={out_dur:.3f}s (orig {vend:.3f}s) size={report['output_size_bytes']}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap_s={max_internal_gap_s} "
          f"policy_met={report['fill_policy_met']}", flush=True)
    print(f"silencedetect internal runs>2s = {len(internal)} {internal}", flush=True)
    print(f"GATES: dur={dur_ok} fill={fill_ok} gap={gap_ok} silence={silence_ok} "
          f"ALL={all_gates}", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)

    if not all_gates:
        raise SystemExit("FILL v2 GATES FAILED — do NOT claim success")


if __name__ == "__main__":
    asyncio.run(main())
