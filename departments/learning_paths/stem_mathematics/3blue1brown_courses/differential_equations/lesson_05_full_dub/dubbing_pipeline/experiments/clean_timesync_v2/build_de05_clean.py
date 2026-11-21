"""
EXPERIMENT - Full-length clean absolute-sample Bengali dub
(Differential Equations, Lesson 05 - "The Heat Equation and Fourier Transforms")

Adapted from the PROVEN clean_timesync_v2 pipeline:
    differential_equations/lesson_02_full_dub/dubbing_pipeline/experiments/clean_timesync_v2/build_de02_clean.py

Guarantees (identical to the proven pipeline, plus IMPROVED_DUB_FILL_POLICY.md):
   1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
      half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
   2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
   3. IMPROVED FILL: atempo floor 0.82 (gentle slowdown), ceiling 2.2. Pad only,
      NEVER truncate. NO SFX: clean speech only.
   4. EXPANSION FIRST: any cue whose natural TTS is short of its share of the
      video gets pedagogical Bengali sentences appended and is re-synthesized.
      The final timeline scale is RECOMPUTED from the SUM of the expanded
      rendered speech durations (never from the authored manifest durations).
   5. FILL GATE WITH AUTO RE-RENDER: per-cue fill, median_fill and
      max_internal_gap_s are measured from the rendered waveform. If
      median_fill < 0.72 or max_internal_gap_s > 1.5 s, short cues are expanded
      again and the whole timeline is re-rendered (up to MAX_RERENDER_ATTEMPTS).
      Every attempt is recorded in verification.json.
   6. Canvas padded to the FULL original video duration so -shortest can never
      trim video frames. Final cue target is capped to end inside the video.
   7. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
   8. Lightweight volumedetect (-vn -nostats, log to FILE) on intro 0-2 s and
      the final 2 s, written into verification.json.

Cue source (read-only; teacher audio / manifests are NEVER modified):
   1. web_platform/assets/audio/differential_equations/lesson_05/manifest.json
      (5 narrated sections, 41 cues) -- PRIMARY. Alias-keyed duplicate sections
      are de-duplicated by section_id. Cue start_ms/end_ms/duration_ms are
      MILLISECONDS and are converted to seconds exactly once in load_cues().
   2. lesson_05_heat_equation/dubbing_pipeline/3b1b_diffeq_l05_bangla_master_script.json
      -- read-only source of extra pedagogical sentences.

Everything is written under NEW experiment folders. Teacher audio, manifests,
master scripts and other lessons are untouched.
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
BASE = EXP.parent.parent                        # .../lesson_05_full_dub/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "differential_equations" / "lesson_05.json"
MASTER_SCRIPT = (BASE.parent / "lesson_05_heat_equation" / "dubbing_pipeline"
                 / "3b1b_diffeq_l05_bangla_master_script.json")   # READ ONLY
ORIGINAL_VIDEO = WEB / "media_vault" / "differential_equations" / "lesson_05" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "differential_equations" / "lesson_05" / "experiments" / "3b1b_de_05_full_dubbed.mp4"

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
VIDEO_ID = "r6sGWTCMz2k"
LESSON = "lesson_05"

# Silence margins: keep 0-2 s and the final 2 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Expansion policy constants.
EXPAND_TRIGGER_RATIO = 0.62          # expand when natural < 62% of window
EXPAND_TARGET_FILL = 0.84            # headroom above the 0.72 policy floor
NATURAL_TARGET_FRACTION = 0.75      # per-cue natural target = fraction * (usable/n)
MAX_APPENDED_SENTENCES = 16
ACTIVE_THRESHOLD = 0.015             # waveform threshold for internal-gap scan
MAX_INTRA_CUE_SILENCE_S = 1.2        # cap long TTS pauses inside a cue

# Fill gate + auto re-render constants (IMPROVED_DUB_FILL_POLICY.md).
GATE_MEDIAN_FILL = 0.72
GATE_MAX_INTERNAL_GAP = 1.5
RERENDER_TARGET_FILL = 0.86          # aim above the gate when re-rendering
MAX_RERENDER_ATTEMPTS = 3

# Section-aware pedagogical sentences (drawn from lesson_05.json content).
EXPANSION_POOL = {
    "sec-heat-pde-review": [
        "এখানে ইউ অব এক্স কমা টি মানে অবস্থান এক্স এবং সময় টি-তে রডের তাপমাত্রা, আর আলফা হলো উপাদানের তাপীয় ব্যাপন সহগ।",
        "দ্বিতীয় স্থানিক অন্তরজ আসলে স্থানীয় বক্রতা মাপে; অবতল বিন্দু উত্তপ্ত হয় আর উত্তল বিন্দু শীতল হয়ে পড়ে।",
        "কেবল আংশিক সমীকরণ দিয়ে ভবিষ্যৎ ঠিক করা যায় না; সমাধান বেছে নিতে হয় সীমানা শর্ত দিয়ে।",
        "ডিরিক্লেট শর্তে দুই প্রান্ত স্থির শূন্য তাপমাত্রায় থাকে, আর নয়ম্যান শর্তে প্রান্ত দিয়ে তাপের প্রবাহ শূন্য হয়।",
        "বরফে ডুবানো প্রান্ত তাপ শোষণ করে, কিন্তু নিরোধক প্রান্ত তাপকে ভেতরেই আটকে রাখে—এই ভৌত পার্থক্যই গাণিতিক শর্ত নির্ধারণ করে।",
        "মনে রাখবেন, একই সমীকরণের জন্য ভিন্ন সীমানা শর্ত সম্পূর্ণ ভিন্ন সমাধান দেয়; তাই সীমানা শর্তের ভৌত অর্থ বোঝা জরুরি।",
    ],
    "sec-boundary-separation": [
        "চলক পৃথচ্ছেদনের ধারণা হলো অজ্ঞাত ফাংশন ইউ অব এক্স কমা টি-কে কেবল অবস্থানের ফাংশন ক্যাপিটাল এক্স ও কেবল সময়ের ফাংশন ক্যাপিটাল টি-এর গুণফল ধরা।",
        "এই অনুমান তাপ সমীকরণে বসালে এক্স প্রাইম ইনটু টি সমান আলফা ইনটু এক্স ডাবল প্রাইম ইনটু টি পাওয়া যায়।",
        "উভয় পক্ষকে আলফা এক্স টি দিয়ে ভাগ করলে বাম পক্ষ কেবল সময়ের আর ডান পক্ষ কেবল অবস্থানের ফাংশন হয়ে যায়।",
        "দুটি স্বাধীন চলকের ফাংশন সবসময় সমান হতে পারে কেবল তখনই যখন উভয়ই একটি ধ্রুবকের সমান—সেটাই পৃথচ্ছেদন ধ্রুবক মাইনাস ল্যাম্বডা স্কয়ার।",
        "এভাবে একটি আংশিক সমীকরণ ভেঙে দুটি সাধারণ ডিফারেনশিয়াল সমীকরণ তৈরি হয়, যেগুলো আমরা অনেক সহজে সমাধান করতে পারি।",
        "শেষ পর্যন্ত শূন্য সীমানা শর্ত ল্যাম্বডাকে এন পাই বাই এল রূপে কোয়ান্টায়িত করে, যা পরমাণুর শক্তিস্তরের কোয়ান্টাইজেশনের আগে থেকে ইঙ্গিত দেয়।",
    ],
    "sec-sine-harmonics-decay": [
        "সময়ের সমীকরণের সমাধান হলো ই টু দ্য পাওয়ার মাইনাস আলফা ল্যাম্বডা স্কয়ার টি—একটি সুপরিচিত সূচকীয় ক্ষয়।",
        "ফলে প্রতিটি মোড একটি ক্ষয়িষ্ণু সাইন তরঙ্গ, যার বিস্তার সময়ের সাথে সাথে কমতে থাকে।",
        "ক্ষয়ের গতিবেগ এন স্কয়ারের সমানুপাতিক: এন সমান দুই চার গুণ দ্রুত, এন সমান তিন নয় গুণ দ্রুত মিলিয়ে যায়।",
        "এন সমান দশের মতো উঁচু হারমোনিক শত গুণ তীব্রতায় বিলীন হয়—তাই তীক্ষ্ণ খাঁজ প্রথমেই মুছে যায়।",
        "তাপমাত্রার যেকোনো ধারালো পরিবর্তন অনেক উঁচু কম্পাঙ্ক নিয়ে গঠিত, আর সেগুলো সবার আগে মিলিয়ে যায়।",
        "কিছুক্ষণ পর কেবল মসৃণতম এন সমান একের আর্চটি বেঁচে থাকে; এই মসৃণকরণই তাপগতিবিদ্যার দ্বিতীয় সূত্রের দিকে ইঙ্গিত করে।",
    ],
    "sec-fourier-orthogonality": [
        "ফুরিয়ারের দাবি ছিল যে যেকোনো ফাংশন এফ অব এক্স-কে অসীম সংখ্যক সাইন তরঙ্গের যোগফল হিসেবে লেখা যায়।",
        "তৎকালীন পণ্ডিতরা এই দাবি বিশ্বাস করতে পারেননি, কারণ মসৃণ তরঙ্গ যোগ করে ধারালো সিঁড়ির ধাপ তৈরি কীভাবে সম্ভব?",
        "এই দাবির ভিত্তি ছিল অর্থোগোনালিটি: দুটি ভিন্ন কম্পাঙ্কের সাইন তরঙ্গের গুণফলের ইন্টিগ্রাল শূন্য হয়।",
        "ঠিক যেমন রৈখিক বীজগণিতে দুটি লম্ব ভেক্টরের ডট প্রোডাক্ট শূন্য, তেমনি ফাংশন স্পেসে সাইন তরঙ্গগুলো পরস্পর লম্ব ভিত্তি ভেক্টর।",
        "উভয় পক্ষকে সাইন এম পাই এক্স বাই এল দিয়ে গুণ করে সমাকলন করলে প্রতিটি সহগ বি এন আলাদাভাবে বেরিয়ে আসে।",
        "যেহেতু তাপ সমীকরণ রৈখিক, তাই প্রতিটি ক্ষয়িষ্ণু মোডের উপরিপাতনেই পূর্ণ সমাধান গঠিত হয়—একটি সিম্ফনির মতো।",
    ],
    "sec-continuous-fourier-transform": [
        "যখন রডের দৈর্ঘ্য এল অসীমের দিকে যায়, তখন পাশাপাশি কম্পাঙ্কের ব্যবধান ডেল্টা কে সমান পাই বাই এল শূন্যের কাছে পৌঁছায়।",
        "বিচ্ছিন্ন পূর্ণসংখ্যার যোগফল তখন মসৃণ অবিচ্ছিন্ন সমাকলে রূপ নেয়—এখানেই জন্ম নেয় ফুরিয়ার রূপান্তর।",
        "ফুরিয়ার রূপান্তর বাস্তব স্থানের ফাংশন এফ অব এক্স-কে কম্পাঙ্ক কে-এর অবিচ্ছিন্ন বর্ণালিতে রূপ দেয়।",
        "এর সবচেয়ে জাদুকরী বৈশিষ্ট্য হলো এটি স্থানিক অন্তরজকে সাধারণ গুণনে রূপান্তর করে, ফলে জটিল আংশিক সমীকরণ রূপ নেয় একটি সহজ ওডিই।",
        "বিপরীত রূপান্তরে দেখা যায় সমাধান মূলত প্রাথমিক তাপমাত্রার সাথে গাউসিয়ান বেল কার্ভের কনভোলিউশন।",
        "এই গাউসিয়ান হিট কার্নেল অবিকল স্বাভাবিক সম্ভাবনা বণ্টনের মতো—অণুদের ব্রাউনিয়ান গতির ম্যাক্রোস্কোপিক রূপই হলো তাপ সমীকরণ।",
    ],
}
DEFAULT_EXPANSIONS = [
    "এই ধারণাটি নিজের ভাষায় একবার বলে দেখলে বিষয়টি আরও পরিচ্ছন্ন হবে।",
    "লক্ষ্য করুন, পরিবর্তনের হারের এই সম্পর্কই আমাদের আসল উত্তরের দিকে নিয়ে যায়।",
    "এখানে যুক্তিটি আবার মনে করিয়ে দিই, কারণ পরের ধাপে এটি বারবার কাজে লাগবে।",
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


def master_script_sentences():
    """Read-only extra pedagogical sentences from the lesson's master script."""
    if not MASTER_SCRIPT.exists():
        return []
    try:
        data = json.loads(MASTER_SCRIPT.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(data, dict):
        data = data.get("cues") or []
    out = []
    for c in data:
        if not isinstance(c, dict):
            continue
        bn = c.get("bn")
        if not bn:
            continue
        for s in re.split(r"[।]", bn):
            s = sanitize(s)
            if len(s) >= 45:
                out.append(s + "।")
    return out


def load_manifest_cues(lesson):
    """Read the audio_manifest referenced by lesson_05.json (read-only).

    The manifest stores sections by canonical id with an alias field; de-
    duplicate by section_id. start_ms/end_ms/duration_ms are MILLISECONDS.
    """
    rel = lesson.get("audio_manifest") or (lesson.get("meta") or {}).get("audio_manifest")
    if not rel:
        return None, None
    manifest = (LESSON_JSON.parent / rel).resolve()
    if not manifest.exists():
        return None, None
    data = json.loads(manifest.read_text(encoding="utf-8"))
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
            # ms -> seconds conversion happens ONCE, here.
            dur_s = float(c.get("duration_ms", 0)) / 1000.0
            if dur_s <= 0 and c.get("end_ms") and c.get("start_ms") is not None:
                dur_s = (float(c["end_ms"]) - float(c["start_ms"])) / 1000.0
            out.append({
                "text": text,
                "dur_ms": dur_s * 1000.0,
                "section": sid,
            })
    if out:
        return out, f"audio_manifest:{manifest.name} ({len(out)} cues, alias-deduped, ms->s)"
    return None, None


def load_master_cues():
    """FALLBACK master script. Its start/end/duration are in SECONDS (x1000 -> ms)."""
    if not MASTER_SCRIPT.exists():
        return None, None
    data = json.loads(MASTER_SCRIPT.read_text(encoding="utf-8"))
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
            dur_s = float(c.get("end", 0)) - float(c.get("start", 0))
        out.append({
            "text": text,
            "dur_ms": float(dur_s) * 1000.0,
            "section": str(c.get("section", "master")),
        })
    if out:
        return out, f"master_script:{MASTER_SCRIPT.name} (seconds->ms x1000)"
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
    """Return (list_of_{text,dur_ms,section}, source_description).

    PRIMARY = manifest cue texts, per task. Master script is fallback only.
    """
    lesson = json.loads(LESSON_JSON.read_text(encoding="utf-8"))
    out, desc = load_manifest_cues(lesson)
    if out:
        return out, desc
    out, desc = load_master_cues()
    if out:
        return out, desc
    return derive_from_lesson(lesson), "lesson_05.json:sections"


def load_cues(vend, source_cues):
    """Lay the authored cues out cumulatively (pre-expansion estimate)."""
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


def predicted_fill(natural, target):
    """Fill with tempo floor 0.82: min(1, natural/(0.82*target))."""
    if target <= 0 or natural <= 0:
        return 0.0
    return min(1.0, natural / (MIN_TEMPO * target))


def section_pool(section, extra):
    pool = list(EXPANSION_POOL.get(section, DEFAULT_EXPANSIONS))
    if extra:
        off = sum(ord(ch) for ch in section) % len(extra)
        pool.extend(extra[off:] + extra[:off])
    pool.extend(DEFAULT_EXPANSIONS)
    return pool


async def expand_short_cues(cues, usable_sec):
    """Append pedagogical sentences to any cue short of its share of the video."""
    extra = master_script_sentences()
    per_cue_usable = usable_sec / max(1, len(cues))
    natural_target = NATURAL_TARGET_FRACTION * per_cue_usable
    print(f"  expansion natural target per cue = {natural_target:.2f}s "
          f"(usable={usable_sec:.1f}s / {len(cues)} cues)", flush=True)
    expanded = []
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        natural = duration(raw)
        if natural <= 0 or natural >= natural_target:
            continue
        pool = section_pool(c["section"], extra)
        base = sanitize(c["bn"])
        added_parts = []
        before = natural
        while len(added_parts) < MAX_APPENDED_SENTENCES:
            need = natural_target - natural
            if need <= 0:
                break
            # Each pedagogical sentence is ~8 s of Bengali speech. Estimate the
            # count from the remaining deficit so the text GROWS monotonically.
            n_sent = max(1, min(MAX_APPENDED_SENTENCES - len(added_parts),
                                int(np.ceil(need / 8.0))))
            k = len(added_parts)
            append_parts = [pool[(k + j) % len(pool)] for j in range(n_sent)]
            # Cumulative: keep everything already appended, then add more.
            new_text = sanitize(base + " " + " ".join(added_parts + append_parts))
            print(f"  expand cue {cid} [{c['section']}]: natural {natural:.2f}s "
                  f"-> target {natural_target:.2f}s  +{n_sent} sent", flush=True)
            if await synth(new_text, raw, force=True):
                added_parts.extend(pool[(k + j) % len(pool)] for j in range(n_sent))
                natural = duration(raw)
                if natural >= natural_target:
                    break
            else:
                break
        if added_parts and natural > 0:
            c["bn"] = sanitize(base + " " + " ".join(added_parts))
            expanded.append({
                "id": cid,
                "section": c["section"],
                "natural_before": round(before, 3),
                "natural_after": round(natural, 3),
                "natural_target": round(natural_target, 3),
                "sentences_added": len(added_parts),
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


def active_bounds(arr, thr=ACTIVE_THRESHOLD):
    active = np.flatnonzero(np.abs(arr) > thr)
    if active.size == 0:
        return 0, arr.size
    return int(active[0]), int(active[-1]) + 1


def internal_gap_s(arr, sr=SR, thr=ACTIVE_THRESHOLD):
    """Longest silent run (seconds) between the first and last active sample."""
    if arr.size == 0:
        return 0.0
    lo, hi = active_bounds(arr, thr)
    if hi - lo < 2:
        return 0.0
    active = np.flatnonzero(np.abs(arr[lo:hi]) > thr)
    if active.size < 2:
        return 0.0
    gaps = np.diff(active)
    if gaps.size == 0:
        return 0.0
    return float(gaps.max()) / sr


def cap_long_silences(arr, sr=SR, thr=ACTIVE_THRESHOLD, max_silence_s=MAX_INTRA_CUE_SILENCE_S):
    """Delete excess samples from silence runs longer than max_silence_s."""
    lo, hi = active_bounds(arr, thr)
    if hi - lo < 2:
        return arr, 0
    seg = arr[lo:hi]
    silent = np.abs(seg) <= thr
    pad = np.concatenate(([False], silent, [False]))
    d = np.diff(pad.astype(np.int8))
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1)
    max_run = int(round(max_silence_s * sr))
    keep = np.ones(seg.size, dtype=bool)
    removed = 0
    for s, e in zip(starts, ends):
        run = e - s
        if run > max_run:
            drop = run - max_run
            half = drop // 2
            keep[s + half:s + half + drop] = False
            removed += drop
    if removed:
        seg = seg[keep]
        arr = np.concatenate((arr[:lo], seg, arr[hi:]))
    return arr, removed


LAST_START = 0.0
VIDEO_END = 0.0
LAST_ID = None


def make_cue(raw, target, out, cid):
    """atempo-fit into the window with floor 0.82; PAD only, NEVER truncate."""
    natural = duration(raw)
    if natural <= 0:
        natural = target
    if cid == LAST_ID:
        # Final cue must finish INSIDE the video, with a small safety margin.
        target = min(target, VIDEO_END - LAST_START - 0.10)
    tempo = max(MIN_TEMPO, min(MAX_TEMPO, natural / target))
    tmp = out.with_suffix(".fit.wav")
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)
    arr, removed = cap_long_silences(arr)
    fit_samples = len(arr)
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
    return arr, tempo, natural, target, fit_samples, removed


def layout(cues, usable, vend):
    """Recompute timeline scale from the SUM of current rendered speech."""
    naturals = {}
    for c in cues:
        rawp = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        naturals[c["id"]] = duration(rawp) if valid(rawp) else 0.0
    total_natural = sum(naturals.values())
    expanded_total_s = total_natural + INTER_CUE_PAUSE_MS * (len(cues) - 1) / 1000.0
    scale = usable / expanded_total_s if expanded_total_s > 0 else 1.0
    cursor_ms = 0.0
    for c in cues:
        nat = naturals.get(c["id"], 0.0) or 2.0   # guard against a failed cue
        start = LEAD_IN_SEC + (cursor_ms / 1000.0) * scale
        dur = nat * scale
        c["start"] = round(start, 3)
        c["end"] = round(start + dur, 3)
        c["duration"] = round(dur, 3)
        cursor_ms += nat * 1000.0 + INTER_CUE_PAUSE_MS
    return scale, total_natural, expanded_total_s, naturals


def place_all(cues, vend, expanded_ids):
    """Absolute sample placement on a FULL-length canvas; measure fill + gaps."""
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    CHUNK = 1_000_000
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    overrun = 0
    last_cue_end = 0.0
    total_silence_removed = 0
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            print(f"  SKIP cue {cid} (no audio)", flush=True)
            continue
        arr, tempo, natural, target, fit_samples, removed = make_cue(
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
        total_silence_removed += removed
        expected_ms = round(float(c["start"]) * 1000, 2)
        actual_ms = round(start_sample / SR * 1000, 2)
        window_samples = int(round(target * SR))
        fill = min(1.0, fit_samples / window_samples) if window_samples > 0 else 0.0
        placed.append({
            "id": cid,
            "section": c["section"],
            "expected_start_ms": expected_ms,
            "actual_start_ms": actual_ms,
            "drift_ms": round(actual_ms - expected_ms, 6),
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3),
            "target_sec": round(target, 3),
            "fit_samples": fit_samples,
            "window_samples": window_samples,
            "fill": round(fill, 4),
            "max_internal_gap_s": round(gap_s, 4),
            "placed_samples": placed_len,
            "expanded": cid in expanded_ids,
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
    return canvas, placed, overrun, total_silence_removed, last_cue_end


async def rerender_low_fill(cues, placed, extra, attempt):
    """Auto re-render: expand cues that failed the fill gate, then re-synth."""
    fixed = []
    for rec in placed:
        if (rec["fill"] >= RERENDER_TARGET_FILL
                and rec["max_internal_gap_s"] <= GATE_MAX_INTERNAL_GAP):
            continue
        c = next((x for x in cues if x["id"] == rec["id"]), None)
        if c is None:
            continue
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        natural = duration(raw)
        if natural <= 0:
            continue
        target = rec["target_sec"]
        need_natural = RERENDER_TARGET_FILL * MIN_TEMPO * target
        need = max(need_natural - natural, 3.0)
        pool = section_pool(c["section"], extra)
        base = sanitize(c["bn"])
        extra_chars = max(90, int(need / max(natural, 0.1) * len(base)))
        n_sent = max(1, min(MAX_APPENDED_SENTENCES, int(np.ceil(extra_chars / 95.0))))
        offset = (attempt * 3 + rec["id"]) % max(1, len(pool))
        append_text = " ".join(pool[(offset + j) % len(pool)] for j in range(n_sent))
        new_text = sanitize(base + " " + append_text)
        print(f"  re-render cue {rec['id']} [{c['section']}]: fill {rec['fill']} "
              f"gap {rec['max_internal_gap_s']}s natural {natural:.2f}s -> +{n_sent} sent",
              flush=True)
        if await synth(new_text, raw, force=True):
            c["bn"] = new_text
            fixed.append({
                "id": rec["id"],
                "fill_before": rec["fill"],
                "max_internal_gap_before_s": rec["max_internal_gap_s"],
                "natural_before": round(natural, 3),
                "sentences_added": n_sent,
            })
    return fixed


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
        raise FileNotFoundError(f"original source not found: {ORIGINAL_VIDEO}")
    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    source_cues, source_desc = load_source_cues()
    cues, scale_pre = load_cues(vend, source_cues)
    LAST_ID = cues[-1]["id"]
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    print(f"video duration = {vend:.3f}s; cues = {len(cues)}; source = {source_desc}; "
          f"pre-expansion timeline scale = {scale_pre:.4f}", flush=True)

    print("[1/7] TTS (clean, no SFX) ...", flush=True)
    failed = await synth_all(cues)

    print("[2/7] Expansion of short cues (IMPROVED_DUB_FILL_POLICY) ...", flush=True)
    expanded = await expand_short_cues(cues, usable)
    expanded_ids = [x["id"] for x in expanded]
    print(f"  expanded {len(expanded)} cues", flush=True)

    print("[3/7] Fill-gate loop: recompute scale from summed speech, place, measure ...", flush=True)
    extra = master_script_sentences()
    rerender_history = []
    attempt = 0
    while True:
        scale, total_natural, expanded_total_s, naturals = layout(cues, usable, vend)
        LAST_START = float(cues[-1]["start"])
        canvas, placed, overrun, total_silence_removed, last_cue_end = place_all(
            cues, vend, expanded_ids)
        fills = [x["fill"] for x in placed]
        median_fill = round(statistics.median(fills), 4) if fills else 0.0
        max_internal_gap = round(max((x["max_internal_gap_s"] for x in placed), default=0.0), 4)
        gate_ok = (median_fill >= GATE_MEDIAN_FILL
                   and max_internal_gap <= GATE_MAX_INTERNAL_GAP)
        rerender_history.append({
            "attempt": attempt,
            "scale": round(scale, 6),
            "sum_natural_s": round(total_natural, 3),
            "median_fill": median_fill,
            "max_internal_gap_s": max_internal_gap,
            "gate_ok": gate_ok,
            "cues_below_target_fill": sum(1 for x in placed
                                          if x["fill"] < RERENDER_TARGET_FILL),
        })
        print(f"  attempt {attempt}: scale={scale:.4f} median_fill={median_fill} "
              f"max_gap={max_internal_gap}s gate_ok={gate_ok}", flush=True)
        if gate_ok or attempt >= MAX_RERENDER_ATTEMPTS:
            break
        attempt += 1
        fixed = await rerender_low_fill(cues, placed, extra, attempt)
        rerender_history[-1]["auto_rerender_fixed"] = fixed
        if not fixed:
            print("  no fixable low-fill cues left; stopping re-render loop", flush=True)
            break

    print("[4/7] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        CHUNK = 1_000_000
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    report = {
        "experiment": "clean_timesync_v2 (differential_equations_lesson_05 full-length, improved fill + auto re-render)",
        "lesson": LESSON,
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
        "timeline_scale_pre_expansion": round(scale_pre, 6),
        "timeline_scale": round(scale, 6),
        "timeline_scale_source": "recomputed from SUM of post-expansion rendered natural speech durations",
        "sum_natural_speech_sec": round(total_natural, 3),
        "expanded_total_sec": round(expanded_total_s, 3),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "time_units_check": "manifest duration_ms/1000 -> seconds; start_seconds*44100 -> samples",
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "silence_samples_removed_in_cues": int(total_silence_removed),
        "fill_policy": {
            "expand_trigger_ratio": EXPAND_TRIGGER_RATIO,
            "expand_target_fill": EXPAND_TARGET_FILL,
            "median_fill": median_fill,
            "median_fill_target": GATE_MEDIAN_FILL,
            "median_fill_ok": median_fill >= GATE_MEDIAN_FILL,
            "max_internal_gap_s": max_internal_gap,
            "max_internal_gap_target": GATE_MAX_INTERNAL_GAP,
            "max_internal_gap_ok": max_internal_gap <= GATE_MAX_INTERNAL_GAP,
            "gate_passed": gate_ok,
            "auto_rerender_attempts_used": attempt,
            "rerender_history": rerender_history,
        },
        "median_fill": median_fill,
        "max_internal_gap_s": max_internal_gap,
        "fill_gate_passed": gate_ok,
        "expanded_cues": expanded,
        "cues": placed,
    }

    print("[5/7] Mux with FULL original video (video copy) ...", flush=True)
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

    print("[6/7] Lightweight volumedetect ...", flush=True)
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    odur = duration(OUT_VIDEO)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={report['output_duration_sec']}s size={report['output_size_bytes']}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap={max_internal_gap}s "
          f"expanded={len(expanded)} gate_ok={gate_ok} rerenders={attempt}", flush=True)
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
