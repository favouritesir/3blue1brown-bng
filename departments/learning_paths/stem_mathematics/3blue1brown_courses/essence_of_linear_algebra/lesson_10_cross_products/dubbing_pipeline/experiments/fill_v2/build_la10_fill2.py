"""
EXPERIMENT (fill_v2) - Full-length clean absolute-sample Bengali dub
(Essence of Linear Algebra, Lesson 10 - "Cross products")

RE-RENDER of the earlier clean_timesync_v2 dub, which left ~33 silent pockets
(up to ~8 s each): that build took a 36-cue master script with a 358.5 s
authored span, stretched it ~1.47x onto the 533 s video and held atempo >= 1.0,
so several seconds of every window were dead air.

This build follows the quality-gated, scale-recomputed policy proven in:
    neural_networks/lesson_01_intro/.../fill_v2/build_nn01_fill2.py
and IMPROVED_DUB_FILL_POLICY.md:

  1. Read the AUDIO MANIFEST (web_platform/assets/audio/linear_algebra/
     lesson_10/manifest.json) as the dubbing script - 37 cues across 4
     sections, alias-deduped by section key. The cue texts are already heavily
     expanded pedagogical Bengali; a section-aware expansion pool is available
     for any cue that is still short of its rendered window. Teacher audio,
     manifests and other lessons are NEVER modified.
  2. edge_tts bn-BD-PradeepNeural; robust retries (0-byte purge, 12 attempts,
     half-split + sentence-split fallbacks, WinError 1450 retry).
  3. STRONG (data-driven) EXPANSION: a cue is grown with section-aware
     pedagogical Bengali sentences until its rendered natural speech reaches
     the per-cue target. Only NEW sentences are synthesized each round
     (incremental concat), so the run is resumable and not O(n^2).
  4. Recompute the timeline scale from the SUM OF RENDERED NATURAL SPEECH
     (never from authored manifest durations). Windows become proportional to
     each cue's measured TTS duration, so cue windows abut with no dead air.
     With the 0.82 atempo floor the rendered fill is ~1.0.
  5. Absolute sample placement start*44100 -> ZERO cumulative drift. Pad only,
     NEVER truncate. NO SFX: clean speech only. Long in-cue silences (>1.0 s)
     are gently compressed.
  6. QUALITY GATE measured from the rendered waveform AND the final muxed
     audio:
        median_fill >= 0.72
        max_internal_gap_s <= 1.5
        internal silence runs > 2.0 s == 0 (silencedetect, margins excluded)
     with automatic extra-expansion + re-render if any gate fails.
  7. Canvas padded to the FULL original video duration so -shortest can never
     trim video frames; final cue capped to end inside the video.
  8. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
     The video source is NEVER swapped - the same
     original_source/full_original.mp4 is reused.
  9. Lightweight volumedetect (-vn -nostats, log to FILE) on intro and final.

Everything new is written under NEW experiment folders:
    script/metadata : essence_of_linear_algebra/lesson_10_cross_products/
                      dubbing_pipeline/experiments/fill_v2/
    output video    : web_platform/media_vault/lesson_10/experiments/fill_v2/
                      3b1b_lesson_10_full_dubbed_fill2.mp4
The previous video (3b1b_lesson_10_full_dubbed.mp4) is left untouched as backup.
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
# EXP = .../3blue1brown_courses/essence_of_linear_algebra/lesson_10_cross_products/dubbing_pipeline/experiments/fill_v2
WEB = EXP.parents[4] / "web_platform"          # .../3blue1brown_courses/web_platform

MANIFEST = WEB / "assets" / "audio" / "linear_algebra" / "lesson_10" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_10" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "lesson_10" / "experiments" / "fill_v2" / "3b1b_lesson_10_full_dubbed_fill2.mp4"
OLD_VIDEO = WEB / "media_vault" / "lesson_10" / "experiments" / "3b1b_lesson_10_full_dubbed.mp4"

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
VIDEO_ID = "C0Zc9VCQ4Eo"            # 3Blue1Brown - Cross products (Chapter 10)
LESSON = "lesson_10_cross_products"
COURSE = "linear_algebra"

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

# silencedetect-based gate for the FINAL rendered audio.
SILENCE_NOISE_DB = "-45dB"
SILENCE_DETECT_D = 1.5
SILENCE_RUN_LIMIT_S = 2.0

SOURCE_METADATA_NOTE = {
    "youtube_id": VIDEO_ID,
    "script_source": "web_platform/assets/audio/linear_algebra/lesson_10/manifest.json "
                     "(37 cues, alias-deduped, cue texts = dubbing script)",
    "video_source": "web_platform/media_vault/lesson_10/original_source/full_original.mp4 "
                    "(NOT swapped)",
    "reason_for_rerender": "prior build left ~33 silent pockets (up to 8 s); windows were "
                           "stretched from a short 36-cue master script while atempo was "
                           "pinned >= 1.0",
    "teacher_audio_and_manifests_modified": False,
}


# ---------------------------------------------------------------------------
# Section-aware pedagogical Bengali sentences. Cycled (never repeated
# back-to-back inside one append) so every addition teaches real content.
# ---------------------------------------------------------------------------
EXPANSION_POOL = {
    "sec_01_geometric_definition": [
        "আসুন একটু থামি এবং ক্রস প্রোডাক্টটিকে আবার চোখের সামনে নিয়ে আসি।",
        "দুটি ভেক্টরের সামান্তরিকের ক্ষেত্রফলই হলো ক্রস ভেক্টরের দৈর্ঘ্য, আর ডান হাত নিয়ম ঠিক করে এর দিক।",
        "বৃদ্ধাঙ্গুলি যেদিকে তাকায়, সেটিই ভি গুণ ডব্লিউ এর অভিমুখ—এই ছোট্ট কৌশলটি মনে রাখলে ক্রম নিয়ে বিভ্রান্তি হবে না।",
        "থিটা যখন নব্বই ডিগ্রি, সাইন থিটা এক, তখন ক্ষেত্রফল সর্বোচ্চ; থিটা শূন্য হলে ক্ষেত্রফলও শূন্য।",
        "সমান্তরাল ভেক্টরের ক্রস গুণন শূন্য, কারণ তাদের গঠিত কোনো ক্ষেত্রফলই তৈরি হয় না।",
        "ক্রস প্রোডাক্ট কেবল একটা হিসাব নয়, এটি ক্ষেত্রফল ও অভিমুখ—দুটো তথ্য একসাথে বহন করে।",
        "লাল তীরটি ভি ও ডব্লিউ উভয়ের প্রতিই লম্ব, আর এর দৈর্ঘ্য সামান্তরিকের আকারের সমানুপাতিক।",
        "ভেক্টর দুটিকে বড় করলে সামান্তরিক বড় হবে, আর ক্রস ভেক্টরটিও তেমনি লম্বা হবে।",
        "এই জ্যামিতিক ছবিটি মনে রাখলেই পরের অধ্যায়ের বীজগাণিতিক সূত্রটি স্বাভাবিক লাগবে।",
    ],
    "sec_02_2d_orientation_determinant": [
        "টুডি সমতলে নির্ণায়কের চিহ্নই আমাদের বলে দেয় ঘূর্ণনের দিক।",
        "ভি থেকে ডব্লিউ এর দিকে ঘড়ির বিপরীত ঘূর্ণন হলে চিহ্ন ধনাত্মক, ঘড়ির দিকে হলে ঋণাত্মক।",
        "ডিটারমিন্যান্টের মান হলো চিহ্নযুক্ত ক্ষেত্রফল—আকার একই থাকলেও দিক বদলালে চিহ্ন বদলায়।",
        "প্রথম কলাম ভি, দ্বিতীয় কলাম ডব্লিউ—এই ক্রমই চিহ্ন নির্ধারণ করে, ক্রম বদলালে ফল উল্টে যায়।",
        "আই হ্যাট গুণ জে হ্যাট সমান পজিটিভ কে হ্যাট, কিন্তু জে হ্যাট গুণ আই হ্যাট সমান নেগেটিভ কে হ্যাট।",
        "এই অ্যান্টি কমিউটেটিভিটি ক্রস গুণনের সবচেয়ে গুরুত্বপূর্ণ বৈশিষ্ট্যগুলোর একটি।",
        "কোনো ভেক্টরকে কে দ্বারা স্কেল করলে ক্ষেত্রফলও কে গুণ বেড়ে যায়।",
        "নিজের সাথে নিজের ক্রস গুণনের ফল সবসময় শূন্য ভেক্টর, কারণ তখন কোনো সামান্তরিক গড়ে ওঠে না।",
        "টুডির এই একক সংখ্যাটি থ্রিডিতে একটি পূর্ণাঙ্গ ভেক্টরে রূপ নেয়—এই পার্থক্যটি মনে রাখবেন।",
    ],
    "sec_03_3d_determinant_formula": [
        "থ্রিডি ক্রস গুণনের সূত্রটি মনে রাখার সবচেয়ে সুন্দর কৌশল হলো ডিটারমিন্যান্ট।",
        "প্রথম সারিতে আই হ্যাট, জে হ্যাট, কে হ্যাট বসানো হয়, পরের সারিতে ভি ও ডব্লিউ এর উপাংশ।",
        "ল্যাপলাস বিস্তার অনুসরণ করলে প্রতিটি একক ভেক্টরের সহগ একটি টু বাই টু সাব ডিটারমিন্যান্ট হয়।",
        "আই হ্যাটের সহগ ভি টু গুণ ডব্লিউ থ্রি বিয়োগ ভি থ্রি গুণ ডব্লিউ টু।",
        "জে হ্যাটের সহগে একটি ঋণাত্মক চিহ্ন আসে—এই চিহ্নটিই ক্রমের সংবেদনশীলতা ধরে রাখে।",
        "কে হ্যাটের সহগ ভি ওয়ান গুণ ডব্লিউ টু বিয়োগ ভি টু গুণ ডব্লিউ ওয়ান।",
        "এই তিনটি সহগ নিয়েই গড়ে ওঠে আমাদের কাঙ্ক্ষিত ত্রিমাত্রিক ক্রস ভেক্টর।",
        "বীজগণিত থেকে পাওয়া এই ভেক্টরটির দৈর্ঘ্য সামান্তরিকের ক্ষেত্রফলের হুবহু সমান।",
        "এটি ভি ও ডব্লিউ এর ওপর লম্ব এবং নিখুঁতভাবে ডান হাত নিয়ম মেনে চলে।",
    ],
    "sec_04_duality_perspective": [
        "ডুয়ালিটি বা দ্বৈততার দর্শনই এই অদ্ভুত সূত্রের পেছনের আসল রহস্য।",
        "রিস রিপ্রেজেন্টেশন উপপাদ্য বলে, ভেক্টর স্পেস থেকে বাস্তব সংখ্যায় যেকোনো রৈখিক রূপান্তর একটি অনন্য ভেক্টরের সাথে ডট গুণনের সমান।",
        "ইউ কে ইনপুট নিয়ে আমরা এমন একটি ডিটারমিন্যান্ট গণনা করি, যার প্রথম কলাম ইউ।",
        "কলাম রৈখিকতার কারণে এটি একটি খাঁটি রৈখিক রূপান্তর, অর্থাৎ টি অফ ইউ।",
        "জ্যামিতিকভাবে এই ডিটারমিন্যান্ট ইউ, ভি, ডব্লিউ দ্বারা গঠিত প্যারালেলেপিপেডের চিহ্নযুক্ত আয়তন।",
        "আয়তন সমান ভূমির ক্ষেত্রফল গুণ ভূমির লম্ব দিকে ইউ এর অভিক্ষেপ।",
        "ডুয়ালিটি উপপাদ্য অনুযায়ী একটি অনন্য ভেক্টর পি বিদ্যমান, যার সাথে ইউ এর ডট গুণন আয়তনের সমান।",
        "সকল ইউ এর জন্য সমতা চাইলে পি কে অবশ্যই ভি ও ডব্লিউ এর সমতলের লম্ব হতে হবে।",
        "আর পি এর দৈর্ঘ্য হতে হবে সামান্তরিকের ক্ষেত্রফলের সমান—অর্থাৎ পি সমান ভি গুণ ডব্লিউ।",
        "এই অনন্য ডুয়াল ভেক্টর পিই আমাদের কাঙ্ক্ষিত ক্রস প্রোডাক্ট।",
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
# Cue loading - AUDIO MANIFEST IS THE DUBBING SCRIPT (read-only)
# ---------------------------------------------------------------------------
def load_source_cues():
    """Read web_platform/assets/audio/linear_algebra/lesson_10/manifest.json.

    Sections are de-duplicated by section key (alias-deduped). Cue texts are
    used verbatim as the dubbing script (they are already heavily expanded).
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
    """STRONG expansion driven by real video duration. Per-cue target =
    usable / N / TARGET_SCALE. Only genuinely short cues grow.
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
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(arr, -1, 1) * 32767).astype("<i2").tobytes())
    try:
        os.remove(tmp)
    except OSError:
        pass
    return arr, tempo, natural, target, fit_samples


def silence_runs(path, detect_d=SILENCE_DETECT_D, noise_db=SILENCE_NOISE_DB):
    """Return [(start, end, dur)] of detected silence runs via ffmpeg silencedetect."""
    log = EXP / "_silencedetect.log"
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
           "-af", f"silencedetect=noise={noise_db}:d={detect_d}", "-f", "null", "-"]
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
    starts = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", txt)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([\d.]+)", txt)]
    total = duration(path) or (len(starts) and ends[-1]) or 0.0
    runs = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else total
        runs.append((round(s, 3), round(e, 3), round(e - s, 3)))
    return runs


def internal_silence_runs(runs, total, lead_in=LEAD_IN_SEC, tail=TAIL_MARGIN_SEC,
                          limit=SILENCE_RUN_LIMIT_S):
    """Silence runs > limit that are fully INSIDE the valid speech region."""
    hi = max(0.0, total - tail)
    return [(s, e, d) for (s, e, d) in runs
            if d > limit and s >= lead_in and e <= hi]


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
    """Re-derive timeline scale from SUM OF RENDERED NATURAL SPEECH (not manifest)."""
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

    print("[1/8] TTS (clean, no SFX) ...", flush=True)
    failed = await synth_all(cues)

    print("[2/8] STRONG expansion driven by real video duration ...", flush=True)
    expanded, per_cue_target = await expand_short_cues(cues, vend)
    print(f"  expanded {len(expanded)} cues", flush=True)

    print("[3/8] Recompute timeline scale from RENDERED natural speech ...", flush=True)
    scale, naturals = recompute_layout_from_naturals(cues, vend)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"  natural_total={sum(naturals):.1f}s -> scale={scale:.4f} "
          f"(was {initial_scale:.4f} from manifest)", flush=True)

    print("[4/8] Absolute placement + quality gate (start*44100, pad-only) ...", flush=True)
    render_round = 0
    internal_runs = []
    while True:
        render_round += 1
        canvas, placed, overrun, last_cue_end, CHUNK = render_canvas(
            cues, vend, [x["id"] for x in expanded])
        median_fill, max_internal_gap = fill_metrics(placed)

        # silencedetect gate on the rendered master (before loudnorm/mux).
        with wave.open(str(MASTER_WAV), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            for i in range(0, len(canvas), CHUNK):
                w.writeframes(canvas[i:i + CHUNK].tobytes())
        all_runs = silence_runs(MASTER_WAV)
        internal_runs = internal_silence_runs(all_runs, len(canvas) / SR)

        gate_ok = (median_fill >= 0.72 and max_internal_gap <= 1.5
                   and len(internal_runs) == 0)
        print(f"  render round {render_round}: median_fill={median_fill} "
              f"max_internal_gap={max_internal_gap}s "
              f"internal_silence_runs>2s={len(internal_runs)} gate_ok={gate_ok}", flush=True)
        if gate_ok or render_round >= 5:
            break
        weak = sorted(placed, key=lambda x: x["fill"])[:3]
        for w in weak:
            cue = next(c for c in cues if c["id"] == w["id"])
            deficit = max(45.0, (0.88 - w["fill"]) * w["target_sec"] * 1.8)
            await expand_cue_more(cue, deficit, expanded)
        scale, naturals = recompute_layout_from_naturals(cues, vend)
        LAST_START = float(cues[-1]["start"])

    print("[5/8] loudnorm -14 LUFS ...", flush=True)
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    print("[6/8] Mux with FULL original video (video copy) ...", flush=True)
    run(f'ffmpeg -y -i "{src}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    # Re-check silencedetect on the FINAL muxed audio (authoritative gate).
    final_runs = silence_runs(OUT_VIDEO)
    final_internal = internal_silence_runs(final_runs, duration(OUT_VIDEO))
    gate_ok_final = (median_fill >= 0.72 and max_internal_gap <= 1.5
                     and len(final_internal) == 0)

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    report = {
        "experiment": "fill_v2 (linear_algebra lesson_10 full-length, heavy expansion, "
                      "scale recomputed from rendered speech, quality-gated)",
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
        "old_video_present": OLD_VIDEO.exists(),
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
        "silence_gate": {
            "noise_db": SILENCE_NOISE_DB,
            "detect_d": SILENCE_DETECT_D,
            "run_limit_s": SILENCE_RUN_LIMIT_S,
            "master_internal_runs_over_2s": len(internal_runs),
            "master_internal_runs_detail": internal_runs[:20],
            "final_internal_runs_over_2s": len(final_internal),
            "final_internal_runs_detail": final_internal[:20],
            "zero_internal_silence_runs": len(final_internal) == 0,
        },
        "quality_gate": {
            "median_fill_ok": median_fill >= 0.72,
            "max_internal_gap_ok": max_internal_gap <= 1.5,
            "zero_internal_silence_runs": len(final_internal) == 0,
            "passed": gate_ok_final,
        },
        "median_fill": median_fill,
        "max_internal_gap_s": max_internal_gap,
        "internal_silence_runs_over_2s": len(final_internal),
        "expanded_cues": expanded,
        "source_metadata_note": SOURCE_METADATA_NOTE,
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

    print("[7/8] Lightweight volumedetect ...", flush=True)
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    odur = duration(OUT_VIDEO)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    report["duration_matches_original"] = abs(report["output_duration_sec"] - vend) <= 3.0
    report["ALL_GATES_PASS"] = bool(
        gate_ok_final and report["duration_matches_original"]
        and not report["video_source_swapped"] and report["old_video_present"])

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("[8/8] DONE", flush=True)
    print(f"cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms rounds={render_round}", flush=True)
    print(f"video={report['output_duration_sec']}s (orig {vend:.3f}s) size={report['output_size_bytes']}", flush=True)
    print(f"scale={scale:.4f} (recomputed from rendered speech; was {initial_scale:.4f})", flush=True)
    print(f"median_fill={median_fill} max_internal_gap={max_internal_gap}s "
          f"internal_silence_runs>2s={len(final_internal)}", flush=True)
    print(f"quality_gate_passed={gate_ok_final} ALL_GATES_PASS={report['ALL_GATES_PASS']}", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
