"""
EXPERIMENT fill_v2 — Full-length, high-fill Bengali dub (Essence of Calculus, Lesson 05)
=======================================================================================
Re-render of the clean_timesync_v2 output to eliminate the 42 silent pockets (up to
~14 s) that resulted from scaling 43 short master-script cues (~2.09x) and padding
each TTS clip into an oversized window.

Quality-gated base (copied verbatim where applicable):
  essence_of_calculus/lesson_08_integration/dubbing_pipeline/experiments/
      clean_timesync_v2/build_calc08_clean.py

WHAT IS DIFFERENT HERE (all inside NEW experiments/fill_v2 folders):
  1. Cue source is the AUDIO MANIFEST (23 cues, alias-deduped per section):
       web_platform/assets/audio/calculus/lesson_05/manifest.json
     The manifest cue texts are the dubbing script. Teacher audio / manifests /
     other lessons are NEVER written to.
  2. HEAVY, data-driven expansion: every cue is TTS-rendered first; its measured
     characters-per-second is used to append a large block of contextual Bengali
     narration until its natural speech covers >= 0.92 of its window. Expansion
     pools are pedagogically matched to each of the 4 sections + a generic pool.
  3. RECOMPUTE SCALE FROM RENDERED SPEECH: after expansion the per-cue windows are
     rebuilt directly from the measured *rendered* speech durations
     (window_i = natural_i * window_budget / sum(natural)), not from authored
     manifest timings. This maximizes fill while keeping the exact full timeline.
  4. Fill gate: median_fill >= 0.72 AND max_internal_gap_s <= 1.5 AND zero
     internal silence runs > 2 s (ffmpeg silencedetect on the final mux).
  5. Still: absolute-sample placement (start*44100, zero drift), atempo in
     [0.82, 2.2], PAD ONLY / never truncate, no SFX, full-length canvas,
     -14 LUFS loudnorm, -c:v copy mux of the ORIGINAL video (video-src unchanged).
  6. The previous video (3b1b_calculus_05_full_dubbed.mp4) is left untouched as a
     backup; this script writes only ...fill_v2/3b1b_calculus_05_full_dubbed_fill2.mp4.
"""
import os
import re
import sys
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
BASE = EXP.parent.parent                        # .../lesson_05_euler_number/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
MANIFEST = WEB / "assets" / "audio" / "calculus" / "lesson_05" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "calculus" / "lesson_05" / "original_source" / "full_original.mp4"
OLD_VIDEO = WEB / "media_vault" / "calculus" / "lesson_05" / "experiments" / "3b1b_calculus_05_full_dubbed.mp4"
OUT_VIDEO = WEB / "media_vault" / "calculus" / "lesson_05" / "experiments" / "fill_v2" / "3b1b_calculus_05_full_dubbed_fill2.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"          # from manifest.json
MAX_TEMPO = 2.2
TEMPO_FLOOR = 0.82
FADE_MS = 12
VIDEO_ID = "m2MIpDrF7Es"
LESSON = "lesson_05_euler_number"

# Silence margins: intro and outro stay speech-free; a short inter-cue pause.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_SEC = 0.35

# Heavy-expansion targets.
EXPAND_TARGET_RATIO = 0.92     # render natural speech >= 0.92 * window
EXPAND_ROUNDS = 8              # per-cue appended-block rounds
CHARS_PER_SEC_PAD = 1.25       # overshoot factor when converting deficit (s) -> chars

# Fill gate (task-defined).
GATE_MEDIAN_FILL = 0.72
GATE_MAX_INTERNAL_GAP_S = 1.5
GATE_DURATION_TOL_S = 3.0

# ----------------------------------------------------------------------------
# Contextual pedagogical Bengali narration pools.  Each cue gets section-matched
# sentences first, then the generic pool.  Sentences are long on purpose: this is
# the "HEAVILY expand" step that removes silent pockets while improving teaching.
# ----------------------------------------------------------------------------
SECTION_POOLS = {
    "sec_01_mystery": [
        "আসুন একটু থামি। এই সংখ্যাটি কেন এত গুরুত্বপূর্ণ তা বোঝার আগে আমাদের প্রশ্নটা ঠিক করে নিতে হবে। কোনো ফাংশনের পরিবর্তনের হার যদি তার নিজের মানের সমান হয়, তবে সেই ফাংশন কেমন দেখাবে?",
        "ফিনিক্স পাখির এই উপমাটি এতটা চমৎকার কারণ সত্যিই ই পাওয়ার টি ফাংশনটি বারবার নিজের মধ্যে থেকে নিজেকেই পুনর্সৃষ্টি করে। এর ডেরিভেটিভ আবার সেই একই ফাংশন।",
        "মনে রাখবেন, গণিতে মুখস্থ করা নয়—বোঝাটাই আসল কথা। সূত্রটি আগে থেকে জেনে নেওয়ার বদলে আমরা নিজেরা খুঁজে বের করব কেন ঠিক এই সংখ্যাটিই এই বিশেষ বৈশিষ্ট্যের অধিকারী।",
        "স্পর্শকের ঢাল আর বক্ররেখার উচ্চতা, এই দুটির সম্পর্ক আমাদের পুরো আলোচনার কেন্দ্রে থাকবে। যেকোনো বিন্দুতে ঢাল যদি উচ্চতার সমান হয়, সেখানেই আমরা এই বিশেষ ভিত্তির সন্ধান পাব।",
        "প্রশ্নটি আবার একবার মনে করিয়ে দিই: মহাবিশ্বে এমন কোনো সংখ্যা কেন থাকবে যার বক্ররেখার প্রতিটি বিন্দুতে স্পর্শকের ঢাল তার তৎকালীন উচ্চতার হুবহু সমান? এই এক প্রশ্নই পুরো পাঠের সূত্রপাত।",
        "দুই দশমিক সাত এক আট দুই আট—এই সংখ্যাটি আমরা অনেকবার শুনেছি, কিন্তু এর উৎস কোথায় তা খুব কম লোকই জানেন। আজ আমরা সেই উৎসের দিকে এক ধাপ এগিয়ে যাব।",
    ],
    "sec_02_proportional_growth": [
        "পাই জীবের এই উদাহরণটি বেছে নেওয়া হয়েছে কারণ ভরের ক্রমাগত দ্বিগুণ হওয়া আমাদের কাছে স্বজ্ঞাত। প্রতিটি দিন শেষে নতুন ভর আগের দিনের ভরের সমান পরিমাণে বাড়ে।",
        "এখানে একটা সূক্ষ্ম বিন্দু লক্ষ্য করুন—এক পূর্ণ দিনের বৃদ্ধি আর এক মুহূর্তের বৃদ্ধি এক নয়। ডেরিভেটিভ মাপে তাৎক্ষণিক হার, তাই আমাদের অতিক্ষুদ্র ডিটি নিয়ে কাজ করতে হবে।",
        "সূচকের নিয়মটি আমাদের অনেক কাজ সহজ করে দেয়। একই ভিত্তির ঘাতগুলো যোগ হলে গুণ হয়ে যায়, আর সেই গুণফল থেকে ভিত্তিটিকে সাধারণ উৎপাদক হিসেবে বাইরে আনা যায়।",
        "লন টু নামে পরিচিত এই ধ্রুবকটি আসলে ভিত্তি দুইয়ের স্পর্শকের ঢাল নির্ধারণ করে। একইভাবে ভিত্তি তিন আর ভিত্তি আটের জন্যও আলাদা আলাদা ধ্রুবক তৈরি হয়।",
        "দুই আর তিনের মাঝে যে ভিত্তিটির সমানুপাতিক ধ্রুবক ঠিক এক, সেটিই হলো আমাদের খোঁজা অয়লার সংখ্যা। এই ছোট্ট পর্যবেক্ষণটিই পুরো রহস্যের চাবিকাঠি।",
        "এক দশমাংশ, এক শতাংশ, এক বিলিয়নভাগ দিন—এভাবে ব্যবধানকে ছোট করতে থাকলে আমরা প্রকৃত তাৎক্ষণিক হারের আরও কাছে এগিয়ে যাই। লিমিটের ধারণা ঠিক এখানেই কাজে আসে।",
        "চিত্রে স্পর্শক আর উচ্চতা পাশাপাশি দেখলে বোঝা যায় যে গুণকটি একের কম হওয়ায় প্রকৃত ডেরিভেটিভ সবসময় ফাংশনের মানের চেয়ে কিছুটা ছোট। এই ছোট্ট পার্থক্যটিই আমাদের সেই বিশেষ ভিত্তির দিকে নিয়ে যায়।",
    ],
    "sec_03_compound_interest": [
        "১৬৮৩ সালের এই চিন্তন পরীক্ষাটি গণিতের ইতিহাসে এক যুগান্তকারী মুহূর্ত। বার্নোলি প্রথম দেখেছিলেন যে অসীম সংখ্যক ক্ষুদ্র ক্ষুদ্র সুদের যোগফলও একটা সসীম সীমায় পৌঁছায়।",
        "প্রতিবার সুদকে আরও ছোট ছোট ভাগে ভাগ করলে টাকার পরিমাণ কিছুটা বাড়ে, কিন্তু সেটি কখনোই অসীমে যায় না। এই ধীরে ধীরে সীমার কাছে পৌঁছানোর প্রক্রিয়াটিই লিমিট নামে পরিচিত।",
        "চিত্রের ওই সীমারেখাটি আমাদের বলে দেয় যে প্রকৃতির নিজস্ব একটা গতিসীমা আছে। যতই ভাগ বাড়াই না কেন, ফলাফল সেই একই বিন্দুতে এসে থিতু হয়।",
        "এই সীমার মানটি ঠিক সেই অয়লার সংখ্যা, যার সাথে আমরা আগে পরিচিত হয়েছি। একই সংখ্যা একদিকে ব্যাংকের চক্রবৃদ্ধি সুদে, অন্যদিকে ডেরিভেটিভের ক্ষেত্রে ফিরে আসে।",
        "বার্ষিক একবার, দুইবার, চারবার কিংবা বারোবার চক্রবৃদ্ধি—প্রতিটি ক্ষেত্রে ফলাফল আলাদা, কিন্তু সবগুলোই একটা নির্দিষ্ট সীমার নিচে থাকে। এই সীমাটিই হলো আমাদের অবিচ্ছিন্ন সীমা।",
        "প্রতি ন্যানোসেকেন্ডে হিসাব করলেও সংখ্যাটি আর বেশি বাড়ে না। অর্থাৎ অবিরাম চক্রবৃদ্ধিতেও কোনো বিস্ফোরণ ঘটে না—বরং এক সুন্দর স্থিতিশীল মানে পৌঁছে যায়।",
    ],
    "sec_04_chain_rule_growth": [
        "বাস্তব জগতে প্রতিটি বৃদ্ধির হার একশত শতাংশ হয় না। তাই আমাদের এমন একটা সাধারণ সূত্রের প্রয়োজন যেটি যেকোনো শতকরা হারের ক্ষেত্রেই কাজ করে।",
        "চেইন রুল আমাদের বলে যে ভেতরের ফাংশনের ডেরিভেটিভ কীভাবে বাইরের ফাংশনের সাথে গুণ হয়ে যায়। এই সরল নিয়মটিই ই পাওয়ার কে টির ডেরিভেটিভ বের করার চাবিকাঠি।",
        "নিউটনের ঠান্ডা হওয়ার সূত্র, ব্যাকটেরিয়ার বংশবৃদ্ধি আর ব্যাংকের সুদ—এই তিনটি ঘটনার পেছনে একই গাণিতিক কাঠামো কাজ করে। সেটি হলো পরিবর্তনের হারের সমানুপাতিকতা।",
        "যেকোনো ভিত্তিকে ই ভিত্তিতে রূপান্তর করতে হলে প্রাকৃতিক লগারিদম ব্যবহার করতে হয়। এই রূপান্ত্রটির মাধ্যমে জটিল দেখা ফাংশনগুলো সহজ হয়ে যায়।",
        "প্রাকৃতিক লগারিদম আসলে সেই সময়কে মাপে যার মধ্যে কোনো পরিমাণ ই ভিত্তিতে বৃদ্ধি পেয়ে নির্দিষ্ট মানে পৌঁছায়। এই বোঝাপড়া রহস্যময় ধ্রুবকগুলোর পর্দা উন্মোচন করে।",
        "অয়লার সংখ্যা কোনো কৃত্রিম চুক্তি নয়—এটি মসৃণ, অবিচ্ছিন্ন পরিবর্তনের প্রাকৃতিক ভাষা। এই কারণেই বিজ্ঞানের প্রায় প্রতিটি ক্ষেত্রে এই সংখ্যা আবার আবার ফিরে আসে।",
        "সমীকরণের সমাধান হিসেবে ই পাওয়ার কে টি ফর্মটি বিশ্বজনীন। একই রূপ ফলাফল দেয় জনসংখ্যা বৃদ্ধি, তেজস্ক্রিয় ক্ষয় কিংবা মহামারীর বিস্তার—সবখানেই এই ফাংশনটি প্রধান চরিত্র।",
        "ভিন্ন ভিত্তিগুলো আসলে একে অপরের অনুভূমিকভাবে স্কেল করা রূপ। ভিত্তি বদলালে শুধু অনুভূমিক স্কেলিং হয়, বক্ররেখার আকার বদলায় না—এই উপলব্ধিই রহস্যটির শেষ অধ্যায়।",
    ],
}

GENERIC_POOL = [
    "এখানে একটু থামুন এবং নিজের ভাষায় বিষয়টি বলে দেখুন। কোনো ধারণা তখনই পোক্ত হয় যখন আপনি সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন।",
    "আসুন এই ধাপটিকে আরও বিশদভাবে দেখি। প্রতিটি ছোট পদক্ষেপের পেছনে একটা সরল যুক্তি রয়েছে, আর সেই যুক্তিগুলো একসাথে মিলে পুরো চিত্রটি তৈরি করে।",
    "এই ধারণাটি আমাদের পরবর্তী আলোচনার ভিত্তি তৈরি করবে। তাই এখনই এটি ভালোভাবে বুঝে নেওয়া জরুরি।",
    "লক্ষ্য করুন, আমরা কোনো নতুন নিয়ম চাপিয়ে দিচ্ছি না—বরং আগের থেকেই পরিচিত সরল ধারণাগুলোকে নতুনভাবে সাজাচ্ছি।",
    "চিত্রের দিকে একবার তাকালেই দেখা যায় কীভাবে এই পরিবর্তন ধাপে ধাপে ঘটছে। দৃশ্যটি মনে রাখলে হিসাবের সূত্রটি স্বয়ংক্রিয়ভাবে মনে পড়বে।",
    "এই যুক্তিটি একবার বুঝতে পারলে পরের ধাপগুলো আরও সহজ হয়ে যাবে। গণিতে ধীরে ধীরে এগোনোই সবচেয়ে নির্ভরযোগ্য পদ্ধতি।",
    "মনে রাখবেন, সূত্র মুখস্থ করার চেয়ে তার পেছনের কারণ বোঝা অনেক বেশি গুরুত্বপূর্ণ। সেটি বুঝতে পারলে যেকোনো নতুন সমস্যায় এই ধারণা কাজে লাগাতে পারবেন।",
    "আবারও বলছি, আমাদের লক্ষ্য হলো শুষ্ক সূত্রের বদলে একটা জীবন্ত ছবি তৈরি করা। ছবিটি মনে থাকলে সূত্র নিজেই নিজের জায়গায় চলে আসে।",
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


def load_manifest_cues():
    """23 cues from the audio manifest, sections alias-deduped, in file order."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out = []
    seen_alias = set()
    for sec_id, sec in data.get("sections", {}).items():
        alias = sec.get("alias") or sec_id
        if alias in seen_alias:              # alias dedup
            continue
        seen_alias.add(alias)
        for c in sec.get("cues", []):
            out.append({
                "text": c["text"],
                "authored_ms": float(c.get("duration_ms", 0)),
                "section": alias,
                "index": int(c.get("index", 0)),
            })
    return out


def authored_layout(cues, vend):
    """Lay authored manifest durations out over the full video (initial scale)."""
    window_budget = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC - INTER_CUE_PAUSE_SEC * (len(cues) - 1)
    authored_total = sum(c["authored_ms"] for c in cues) / 1000.0
    scale = window_budget / authored_total if authored_total > 0 else 1.0
    t = LEAD_IN_SEC
    for c in cues:
        w = (c["authored_ms"] / 1000.0) * scale
        c["window"] = w
        c["start"] = t
        c["end"] = t + w
        t = c["end"] + INTER_CUE_PAUSE_SEC
    return scale, window_budget


def pick_expansion(section, cursor):
    pool = SECTION_POOLS.get(section, []) + GENERIC_POOL
    return pool[cursor % len(pool)]


async def expand_heavily(cues, natural, cps):
    """Append large blocks of pedagogical Bengali until natural >= 0.92*window.

    A cue's characters-per-second is measured from its own base render; the
    deficit in seconds is converted to characters (with a 1.25 safety margin)
    so a single pass usually closes the gap.
    """
    cursors = {}
    for c in cues:
        cursors[c["id"]] = 0
    applied = []
    for rnd in range(EXPAND_ROUNDS):
        changed = False
        for c in cues:
            cid = c["id"]
            raw = RAW_DIR / f"raw_{cid:03d}.mp3"
            nat = natural.get(cid, 0.0)
            target = EXPAND_TARGET_RATIO * c["window"]
            if nat <= 0 or nat >= target:
                continue
            need_chars = (target - nat) * cps * CHARS_PER_SEC_PAD
            extras = []
            acc = 0.0
            while acc < need_chars:
                s = pick_expansion(c["section"], cursors[cid])
                cursors[cid] += 1
                extras.append(s)
                acc += len(s)
            new_text = sanitize(" ".join([c["bn"]] + extras))
            if await synth(new_text, raw, force=True):
                natural[cid] = duration(raw)
                c["bn"] = new_text
                changed = True
                applied.append({
                    "id": cid,
                    "round": rnd + 1,
                    "natural_before": round(nat, 3),
                    "natural_after": round(natural[cid], 3),
                    "window_sec": round(c["window"], 3),
                    "added_sentences": len(extras),
                })
                print(f"  heavy-expand cue {cid} r{rnd+1}: {nat:.2f}s -> "
                      f"{natural[cid]:.2f}s (window {c['window']:.2f}s, +{len(extras)} sent)",
                      flush=True)
        if not changed:
            break
    return applied


def recompute_layout_from_rendered(cues, natural, window_budget):
    """RECOMPUTE SCALE FROM RENDERED SPEECH.

    window_i = natural_i * (window_budget / sum(natural)).  The whole authored
    scale is discarded here; the timeline is rebuilt purely from what the TTS
    engine actually rendered.  Returns the rendered scale factor.
    """
    total_natural = sum(natural.get(c["id"], 0.0) for c in cues)
    rendered_scale = window_budget / total_natural if total_natural > 0 else 1.0
    t = LEAD_IN_SEC
    for c in cues:
        nat = natural.get(c["id"], c["window"])
        w = nat * rendered_scale
        c["window"] = w
        c["start"] = t
        c["end"] = t + w
        t = c["end"] + INTER_CUE_PAUSE_SEC
    return rendered_scale


async def synth_all(cues, natural):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, c in enumerate(cues):
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        ok = await synth(sanitize(c["bn"]), raw)
        if ok:
            natural[c["id"]] = duration(raw)
        else:
            failed.append(c["id"])
            print(f"  WARNING cue {c['id']} failed after every fallback", flush=True)
        if (i + 1) % 5 == 0:
            print(f"  TTS {i+1}/{len(cues)}", flush=True)
    return failed


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
    """atempo-fit into window with floor 0.82; PAD only, NEVER truncate.

    Returns (arr, info).  info carries measured fill ratio and internal silence
    gap of this cue's window.
    """
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


def silencedetect(path, noise_db="-40dB", min_dur=2.0):
    """Return all silence intervals (start, end) reported by ffmpeg."""
    log = EXP / "_silencedetect.log"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-nostats", "-vn", "-i", str(path),
           "-af", f"silencedetect=noise={noise_db}:d={min_dur}", "-f", "null", "-"]
    with open(log, "wb") as fh:
        subprocess.run(cmd, stdout=fh, stderr=fh)
    txt = log.read_text(encoding="utf-8", errors="ignore")
    starts = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", txt)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([\d.]+)", txt)]
    intervals = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else None
        intervals.append((s, e))
    return intervals, txt


async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    source = load_manifest_cues()
    for i, c in enumerate(source):
        c["id"] = i + 1
        c["bn"] = sanitize(c["text"])
    scale0, window_budget = authored_layout(source, vend)
    LAST_START = float(source[-1]["start"])
    LAST_ID = source[-1]["id"]
    print(f"video duration = {vend:.3f}s; manifest cues = {len(source)}; "
          f"window_budget = {window_budget:.3f}s; authored scale = {scale0:.4f}", flush=True)

    natural = {}
    print("[1/7] TTS base manifest cues (bn-BD-PradeepNeural) ...", flush=True)
    failed = await synth_all(source, natural)

    print("[2/7] HEAVY expansion (data-driven, measured chars/sec) ...", flush=True)
    cps_vals = []
    for c in source:
        n = natural.get(c["id"], 0.0)
        if n > 0:
            cps_vals.append(len(c["bn"]) / n)
    cps = statistics.median(cps_vals) if cps_vals else 13.0
    print(f"  measured chars/sec = {cps:.3f}", flush=True)
    expanded = await expand_heavily(source, natural, cps)

    print("[3/7] RECOMPUTE SCALE FROM RENDERED SPEECH ...", flush=True)
    rendered_scale = recompute_layout_from_rendered(source, natural, window_budget)
    print(f"  rendered scale = {rendered_scale:.6f} ; "
          f"rendered speech total = {sum(natural.values()):.3f}s", flush=True)

    # One more expansion pass in case recomputed windows moved a cue out of range.
    extra = await expand_heavily(source, natural, cps)
    expanded += extra
    rendered_scale = recompute_layout_from_rendered(source, natural, window_budget)

    print("[4/7] Absolute sample placement (start*44100, pad-only, floor 0.82) ...", flush=True)
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    fills = []
    internal_gaps = []
    overrun = 0
    last_cue_end = 0.0
    expanded_ids = {x["id"] for x in expanded}
    for c in source:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            print(f"  SKIP cue {cid} (no audio)", flush=True)
            continue
        arr, info = make_cue(raw, float(c["window"]), CUE_DIR / f"cue_{cid:03d}.wav", cid)
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
            "window_samples": info["window_samples"],
            "speech_samples": info["speech_samples"],
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

    print("[6/7] Mux with FULL original video (video copy; video-src unchanged) ...", flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    print("[7/7] Verify: ffprobe duration + silencedetect internal runs ...", flush=True)
    out_dur = duration(OUT_VIDEO)
    intervals, _ = silencedetect(OUT_VIDEO, noise_db="-40dB", min_dur=2.0)
    # Internal runs = silence intervals that are neither the lead-in nor the tail.
    internal_runs = []
    for s, e in intervals:
        if e is None:
            continue
        if s < LEAD_IN_SEC - 0.5:          # lead-in silence
            continue
        if e > out_dur - TAIL_MARGIN_SEC + 0.5:   # tail silence
            continue
        internal_runs.append((round(s, 3), round(e, 3), round(e - s, 3)))
    internal_runs_gt2 = [r for r in internal_runs if r[2] > 2.0]
    print(f"  silence intervals (all) = {len(intervals)} ; internal = {len(internal_runs)} ; "
          f"internal >2s = {len(internal_runs_gt2)}", flush=True)

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    fill_ok = median_fill >= GATE_MEDIAN_FILL
    gap_ok = max_internal_gap_s <= GATE_MAX_INTERNAL_GAP_S
    dur_ok = abs(out_dur - vend) <= GATE_DURATION_TOL_S
    sil_ok = len(internal_runs_gt2) == 0
    gates_ok = bool(fill_ok and gap_ok and dur_ok and sil_ok and not failed)

    report = {
        "experiment": "fill_v2 (calculus_lesson_05 full-length, heavy-expansion, rendered-speech scale)",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": f"audio_manifest:{MANIFEST.name} (23 cues, alias-deduped)",
        "cue_count": len(placed),
        "expected_cue_count": len(source),
        "failed_tts_cues": failed,
        "voice": VOICE,
        "video_src": str(ORIGINAL_VIDEO),
        "backup_video_kept": str(OLD_VIDEO),
        "strategy": "absolute sample offset; atempo fit in [0.82,2.2]; pad only; no truncation; "
                    "windows rebuilt from rendered speech",
        "sfx": "NONE — clean speech only",
        "max_tempo": MAX_TEMPO,
        "tempo_floor": TEMPO_FLOOR,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "authored_timeline_scale": round(scale0, 6),
        "rendered_speech_scale": round(rendered_scale, 6),
        "window_budget_sec": round(window_budget, 3),
        "rendered_speech_total_sec": round(sum(natural.values()), 3),
        "measured_chars_per_sec": round(cps, 3),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "inter_cue_pause_sec": INTER_CUE_PAUSE_SEC,
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "median_fill": median_fill,
        "max_internal_gap_s": max_internal_gap_s,
        "fill_policy_target": "median_fill >= 0.72 and max_internal_gap_s <= 1.5",
        "output_duration_sec": round(out_dur, 3),
        "silencedetect_noise_db": "-40dB",
        "silencedetect_min_dur_s": 2.0,
        "silence_intervals_all": [[round(s, 3), (round(e, 3) if e is not None else None)]
                                  for s, e in intervals],
        "internal_silence_runs": internal_runs,
        "internal_silence_runs_gt2s": internal_runs_gt2,
        "gate_median_fill": fill_ok,
        "gate_max_internal_gap": gap_ok,
        "gate_full_duration": dur_ok,
        "gate_no_internal_silence_gt2s": sil_ok,
        "gates_passed": gates_ok,
        "heavy_expansions_applied": expanded,
        "cues": placed,
    }
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, out_dur - 2), 2)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={out_dur:.3f}s (orig {vend:.3f}s) size={OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap_s={max_internal_gap_s}", flush=True)
    print(f"internal silence runs >2s = {len(internal_runs_gt2)}", flush=True)
    print(f"GATES: fill={fill_ok} gap={gap_ok} duration={dur_ok} silence={sil_ok} => "
          f"{'PASS' if gates_ok else 'FAIL'}", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)
    if not gates_ok:
        print("ERROR: fill_v2 gates did not pass — do not claim success.", flush=True)
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
