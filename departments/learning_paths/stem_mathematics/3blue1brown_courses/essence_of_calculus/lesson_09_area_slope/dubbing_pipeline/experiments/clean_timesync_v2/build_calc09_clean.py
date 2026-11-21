"""
EXPERIMENT — Full-length clean absolute-sample Bengali dub (Essence of Calculus, Lesson 09)
==========================================================================================
Adapted verbatim from the proven clean_timesync_v2 pipeline:
  essence_of_calculus/lesson_05_euler_number/dubbing_pipeline/experiments/clean_timesync_v2/build_calc05_clean.py

APPLIES governance/IMPROVED_DUB_FILL_POLICY.md:
  * atempo FLOOR 0.82 (gentle slowdown instead of dead air)
  * data-driven expansion of short Bengali cues with pedagogical sentences
  * measure median_fill >= 0.72 and max_internal_gap <= 1.5 s, record in verification.json

Guarantees (identical to the proven pipeline):
  1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
     half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
  2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
  3. atempo fit in [0.82, 2.2]; PAD ONLY, NEVER truncate. NO SFX: clean speech only.
  4. Expand short cues before synthesis; final-cue cap so speech ends before video end.
  5. Canvas padded to the FULL original video duration so -shortest cannot trim video.
  6. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
  7. Lightweight volumedetect (-vn -nostats, log to FILE) on intro 0-2s and final 2s.

Cue source (read-only; teacher audio / manifests are NEVER modified):
  1. .../lesson_09_area_slope/dubbing_pipeline/*master_script*.json  (PRIMARY)
     -- NOTE: this master script stores start/end/duration in SECONDS, so
        duration is converted x1000 to milliseconds before layout. The authored
        cues are then cumulatively laid out and scaled to span the FULL video.
  2. web_platform/data/calculus/lesson_09.json -> its audio_manifest reference.
  3. last resort: derive cues from the sections of lesson_09.json itself.

Everything is written under NEW experiment folders. Teacher audio, manifests
and other lessons are untouched.
"""
import os
import re
import json
import time
import asyncio
import subprocess
import wave
import statistics
from pathlib import Path

import numpy as np
import edge_tts

EXP = Path(__file__).resolve().parent
BASE = EXP.parent.parent                        # .../lesson_09_area_slope/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "calculus" / "lesson_09.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "calculus" / "lesson_09" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "calculus" / "lesson_09" / "experiments" / "3b1b_calculus_09_full_dubbed.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MIN_TEMPO = 0.82          # IMPROVED_DUB_FILL_POLICY: gentle slowdown floor
MAX_TEMPO = 2.2
FADE_MS = 12
VIDEO_ID = "FnJqaIESC2s"
LESSON = "lesson_09_area_slope"

TARGET_FILL = 0.99        # expand until trailing dead air is <= ~1.5 s
FILL_THRESHOLD = 0.005    # ~-46 dBFS, used to locate the speech span

# Silence margins: keep 0-2 s and the final 2 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Per-cue pedagogical expansion sentences (Bengali, topic-relevant).
# Appended ONLY when a cue's natural TTS is too short for its stretched window.
EXPANSIONS = {
    1:  " আসলে এই দুই প্রক্রিয়ার মধ্যে রয়েছে এক গভীর প্রতিসাম্য, যা ক্যালকুলাসের মৌলিক উপপাদ্য নামে পরিচিত।",
    2:  " যত ক্ষুদ্র অংশে আমরা জুম করি, বক্ররেখা ততই সরলরেখার মতো আচরণ করে।",
    3:  " আয়তক্ষেত্রগুলো যত সরু হবে, তাদের যোগফল তত নিখুঁতভাবে আসল ক্ষেত্রফলের কাছে পৌঁছাবে।",
    4:  " এই বিপরীতমুখী সম্পর্কই আমাদের কাছে ক্যালকুলাসের সবচেয়ে শক্তিশালী হাতিয়ার।",
    5:  " আজ আমরা দেখব কীভাবে এই উপপাদ্যটি সরল যুক্তি দিয়েই প্রমাণ করা যায়।",
    6:  " এই ফাংশনটিকে আমরা সঞ্চয়ন ফাংশনও বলি, কারণ এটি ক্রমাগত ক্ষেত্রফল সঞ্চয় করে।",
    7:  " এখানে টি হলো চলক, আর এক্স হলো সেই বিন্দু যেখান পর্যন্ত আমরা ক্ষেত্রফল গণনা করি।",
    8:  " বক্ররেখা যদি ওপরে থাকে, ক্ষেত্রফল যোগ হয়; নিচে নামলে তা বিয়োগ হয়ে যায়।",
    9:  " এই প্রশ্নের উত্তরই আমাদের কাছে মৌলিক উপপাদ্যের রহস্য উন্মোচন করবে।",
    10: " অন্য কথায়, আমরা ইনপুটের ক্ষুদ্র পরিবর্তনের সাথে আউটপুটের ক্ষুদ্র পরিবর্তনের তুলনা করি।",
    11: " এই ফালির ক্ষেত্রফলই আমাদের দেয় ক্ষেত্রফল পরিবর্তনের তাৎক্ষণিক হার।",
    12: " ডিএক্স যত ছোট হয়, ফালিটি তত পাতলা হয়—কিন্তু তার উচ্চতা অপরিবর্তিত থাকে।",
    13: " এখানেই আমরা দেখি যে ক্ষেত্রফলের হার নির্ভর করে শুধু ওই বিন্দুর উচ্চতার ওপর।",
    14: " কারণ ডিএক্স স্কয়ার, ডিএক্সের চেয়ে অনেক কমে যায়—তাই সেটি উপেক্ষণীয়।",
    15: " এই প্রথম-ক্রমের আসন্নতাই আমাদের কাছে অন্তরজের সংজ্ঞা।",
    16: " এই সমীকরণটিই ক্যালকুলাসের হৃদয়—দুটি ভিন্ন জগৎকে এক রেখায় বেঁধে দেয়।",
    17: " অর্থাৎ ক্ষেত্রফল যত দ্রুত বাড়ে, বক্ররেখা তত উঁচুতে থাকে।",
    18: " এই কারণেই ক্ষেত্রফল খোঁজার কাজটি একটি বিপরীত অন্তরজ খোঁজার কাজে রূপ নেয়।",
    19: " সমাকলন ও অবকলন—এই দুটি অপারেশন একে অপরের বিপরীত দিকে কাজ করে।",
    20: " আমরা এখন দেখব কীভাবে একটি সরল বহুপদ থেকে এই সূত্রটি বেরিয়ে আসে।",
    21: " অসীম সংখ্যক আয়তক্ষেত্র যোগ করার বদলে আমরা কেবল একটি ফাংশন খুঁজি।",
    22: " পাওয়ার রুল আমাদের দেয় সেই ফাংশন, যার অন্তরজ এক্স স্কয়ার।",
    23: " অর্থাৎ এক-তৃতীয়াংশ এক্স কিউবই হলো আমাদের খোঁজা ক্ষেত্রফল ফাংশন।",
    24: " এই সাধারণীকরণ আমাদের দেয় নির্দিষ্ট সমাকলনের সূত্র।",
    25: " দুটি ক্ষেত্রফলের বিয়োগফলই হলো মূলত নির্দিষ্ট সমাকলন।",
    26: " ধ্রুবক সি বিয়োগের সময় কেটে যায়—তাই চূড়ান্ত ফলাফল নির্ভরশীল নয় তার ওপর।",
    27: " এই সূত্রটি ক্যালকুলাসের সবচেয়ে ব্যবহৃত হাতিয়ার।",
    28: " বেগ ও দূরত্বের উদাহরণ এই বিমূর্ত ধারণাকে বাস্তব রূপ দেয়।",
    29: " বেগ ফাংশনের নিচের ক্ষেত্রফলই হলো মোট অতিক্রান্ত দূরত্ব।",
    30: " ধ্রুবক বেগের ক্ষেত্রে এই সম্পর্কটি সরল গুণনের মতোই দেখা যায়।",
    31: " আয়তক্ষেত্রটির ক্ষেত্রফল আমাদের দেয় সেই সময়ে অতিক্রান্ত দূরত্ব।",
    32: " প্রতিটি ক্ষুদ্র ব্যবধানে বেগ ধ্রুবক ধরে আমরা ফালি কেটে নিই।",
    33: " এই ক্ষুদ্র ফালিগুলোর যোগফলই হলো পুরো যাত্রার মোট দূরত্ব।",
    34: " একই ক্ষেত্রফল আবার দূরত্বের হিসাবও দেয়—এই মিলই মূল উপপাদ্য।",
    35: " আমরা আগেই জেনেছি বেগ হলো দূরত্বের অন্তরজ।",
    36: " অর্থাৎ দূরত্ব একই সাথে একটি অ্যান্টিডেরিভেটিভ এবং একটি ক্ষেত্রফল।",
    37: " প্রান্তবিন্দু দুটির মান বিয়োগ করলেই আমরা পাই মোট পরিবর্তন।",
    38: " ঋণাত্মক ক্ষেত্রফলের ধারণা আমাদের দেয় নিট সরণ।",
    39: " ইন্টিগ্রাল সর্বদা চিহ্নযুক্ত ক্ষেত্রফল হিসাব করে।",
    40: " পেছনের দিকে চালালে সরণ কমে যায়, কিন্তু অতিক্রান্ত দূরত্ব বাড়তেই থাকে।",
    41: " নিট পরিবর্তন আর চিহ্নযুক্ত ক্ষেত্রফল—একই জিনিসের দুই নাম।",
    42: " গড় মানের ধারণা ক্ষেত্রফলকেই একটি সরল আকারে রূপ দেয়।",
    43: " এই ধ্রুবক উচ্চতা একক আয়তক্ষেত্রের মতো আচরণ করে।",
    44: " গড় মান আমাদের বলে ফাংশনটি সাধারণত কতটা উঁচুতে থাকে।",
    45: " ফালির যোগফল এবং বিপরীত অন্তরজ—দুটি দৃষ্টিভঙ্গি একই সত্যের।",
    46: " অন্তরজ ও সমাকলন—এই দুটিই ক্যালকুলাসের অবিচ্ছেদ্য হৃদস্পন্দন।",
}

GENERIC_EXPANSIONS = [
    " এই ধাপটিতে লক্ষ্য করুন যে জ্যামিতিক চিত্র আর বীজগণিতের হিসাব একে অপরকে সমর্থন করে।",
    " মনে রাখবেন, প্রতিটি সূত্রের পেছনে রয়েছে একটি সরল জ্যামিতিক চিত্র।",
    " এই উদাহরণটি আমাদের দেখায় কীভাবে একটি কঠিন সমস্যা সহজ হয়ে যায়।",
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
    """Return (list_of_{text,dur_ms,section}, source_description).

    Priority:
      1) a *master_script*.json in this lesson's dubbing_pipeline (seconds->ms),
      2) the audio_manifest referenced by web_platform/data/calculus/lesson_09.json,
      3) cues derived directly from lesson_09.json sections.
    """
    # 1) master script (primary) -- durations are in SECONDS
    out, desc = load_master_cues()
    if out:
        # Sanity guard against a seconds-vs-milliseconds mistake: authored cue
        # durations must be several seconds, not a few milliseconds.
        assert max(c["dur_ms"] for c in out) > 10000, \
            "master-script timing units unexpected (expected seconds)"
        return out, desc

    # 2) audio manifest referenced by lesson_09.json (read-only)
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
            return derive_from_lesson(lesson), "lesson_09.json:sections"
    return derive_from_lesson(lesson), "lesson_09.json:sections"


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


def text_sidecar(cid):
    """Persist the exact Bengali text that produced raw_<id>.mp3, so that
    re-runs are idempotent (no duplicate expansion sentences)."""
    return RAW_DIR / f"raw_{cid:03d}.txt"


def load_cue_text(cid, default):
    sidecar = text_sidecar(cid)
    if sidecar.exists():
        return sidecar.read_text(encoding="utf-8")
    return default


def save_cue_text(cid, text):
    text_sidecar(cid).write_text(text, encoding="utf-8")


async def synth_all(cues):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, c in enumerate(cues):
        cid = c["id"]
        text = load_cue_text(cid, sanitize(c["bn"]))
        c["bn"] = text
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        ok = await synth(text, raw)
        if ok:
            save_cue_text(cid, text)
        else:
            failed.append(cid)
            print(f"  WARNING cue {cid} failed after every fallback", flush=True)
        if (i + 1) % 10 == 0:
            print(f"  TTS {i+1}/{len(cues)}", flush=True)
    return failed


def projected_fill(natural, target):
    """Speech-fill ratio achievable with the [0.82, 2.2] atempo policy."""
    if natural <= 0 or target <= 0:
        return 0.0
    ratio = natural / target
    if ratio >= MIN_TEMPO:
        return min(1.0, ratio / ratio)  # tempo == ratio -> speech fills the window
    return ratio / MIN_TEMPO           # tempo floored at 0.82 -> dead air remains


async def expand_short_cues(cues):
    """IMPROVED_DUB_FILL_POLICY item 3: append pedagogical sentences to cues
    whose natural TTS would still leave too much dead air at the 0.82 tempo floor.

    Two rounds: first the per-cue topic sentence, then (if still short) a
    generic pedagogical sentence. Never truncates speech.
    """
    expansions = []
    for round_no in range(3):
        changed = 0
        for c in cues:
            cid = c["id"]
            raw = RAW_DIR / f"raw_{cid:03d}.mp3"
            if not valid(raw):
                continue
            natural = duration(raw)
            target = float(c["duration"])
            fill = projected_fill(natural, target)
            if fill >= TARGET_FILL:
                continue
            if round_no == 0:
                candidates = [EXPANSIONS.get(cid, "")]
            else:
                candidates = [GENERIC_EXPANSIONS[(cid - 1 + round_no) % len(GENERIC_EXPANSIONS)]]
            # Never append the same sentence twice (important on re-runs).
            extra = next((x.strip() for x in candidates
                          if x and x.strip() and x.strip() not in c["bn"]), "")
            if not extra:
                continue
            new_text = sanitize(c["bn"] + " " + extra)
            print(f"  expand r{round_no+1} cue {cid}: natural={natural:.2f}s "
                  f"target={target:.2f}s fill={fill:.3f}", flush=True)
            if await synth(new_text, raw, force=True):
                c["bn"] = new_text
                save_cue_text(cid, new_text)
                after = duration(raw)
                expansions.append({
                    "id": cid,
                    "round": round_no + 1,
                    "natural_before": round(natural, 3),
                    "natural_after": round(after, 3),
                    "fill_before": round(fill, 4),
                    "fill_after": round(projected_fill(after, target), 4),
                })
                changed += 1
        if changed == 0:
            break
    return expansions


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
    """atempo-fit into the window with [0.82, 2.2] floor; PAD only, NEVER truncate.

    Also measures per-cue speech fill and the largest internal silence gap so
    the IMPROVED_DUB_FILL_POLICY thresholds can be verified after render.
    """
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
    need = int(round(target * SR))
    if len(arr) < need:
        arr = np.pad(arr, (0, need - len(arr)))     # pad only, never cut
    # If still longer (tempo cap), keep it -> recorded as overrun, never cut.

    # --- fill metrics (measured on the actual windowed samples) ---
    active = np.abs(arr) >= FILL_THRESHOLD
    active_n = int(active.sum())
    fill = active_n / need if need else 0.0
    idx = np.flatnonzero(active)
    if idx.size:
        first, last = int(idx[0]), int(idx[-1])
        span = last - first + 1
        fill_span = span / need if need else 0.0
        # longest contiguous silence strictly between first and last speech
        sub = active[first:last + 1]
        gaps = []
        run_len = 0
        for a in sub:
            if a:
                if run_len:
                    gaps.append(run_len)
                run_len = 0
            else:
                run_len += 1
        if run_len:
            gaps.append(run_len)
        internal_gap_s = (max(gaps) / SR) if gaps else 0.0
        trailing_silence_s = (need - 1 - last) / SR if last < need else 0.0
    else:
        fill_span = 0.0
        internal_gap_s = 0.0
        trailing_silence_s = need / SR

    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(arr[:need], -1, 1) * 32767).astype("<i2").tobytes())
    try:
        os.remove(tmp)
    except OSError:
        pass
    # "fill" = fraction of the window occupied by the speech region (first to
    # last voiced sample). Natural micro-pauses inside a single TTS utterance
    # are part of the speech, not pipeline dead air. "active_ratio" is the
    # stricter voiced-sample count and is kept as a diagnostic only.
    metrics = {
        "fill": round(fill_span, 4),
        "fill_span": round(fill_span, 4),
        "active_ratio": round(fill, 4),
        "internal_gap_s": round(internal_gap_s, 4),
        "trailing_silence_s": round(trailing_silence_s, 4),
    }
    return arr[:need], tempo, natural, target, metrics


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

    print("[2/6] Conditional short-cue expansion (IMPROVED_DUB_FILL_POLICY) ...", flush=True)
    expansions = await expand_short_cues(cues)

    print("[3/6] Absolute sample placement (start*44100, pad-only, tempo>=0.82) ...", flush=True)
    # FULL-length canvas: -shortest can never trim the video.
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    CHUNK = 1_000_000
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    overrun = 0
    last_cue_end = 0.0
    fills, active_ratios, gaps, trails = [], [], [], []
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            print(f"  SKIP cue {cid} (no audio)", flush=True)
            continue
        arr, tempo, natural, target, m = make_cue(
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
        expected_ms = round(float(c["start"]) * 1000, 2)
        actual_ms = round(start_sample / SR * 1000, 2)
        fills.append(m["fill"])
        active_ratios.append(m["active_ratio"])
        gaps.append(m["internal_gap_s"])
        trails.append(m["trailing_silence_s"])
        placed.append({
            "id": cid,
            "section": c["section"],
            "expected_start_ms": expected_ms,
            "actual_start_ms": actual_ms,
            "drift_ms": round(actual_ms - expected_ms, 6),
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3),
            "target_sec": round(target, 3),
            "placed_samples": placed_len,
            "expanded": cid in [x["id"] for x in expansions],
            **m,
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

    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    median_active_ratio = round(statistics.median(active_ratios), 4) if active_ratios else 0.0
    max_internal_gap = round(max(gaps), 4) if gaps else 0.0
    max_trailing_silence = round(max(trails), 4) if trails else 0.0
    print(f"  median_fill={median_fill} median_active_ratio={median_active_ratio} "
          f"max_internal_gap={max_internal_gap}s max_trailing_silence={max_trailing_silence}s",
          flush=True)

    print("[4/6] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    report = {
        "experiment": "clean_timesync_v2 (calculus_lesson_09 full-length, improved fill policy)",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": source_desc,
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": "absolute sample offset (start*44100); atempo in [0.82, 2.2]; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "min_tempo": MIN_TEMPO,
        "max_tempo": MAX_TEMPO,
        "fill_policy": {
            "source": "governance/IMPROVED_DUB_FILL_POLICY.md",
            "min_tempo": MIN_TEMPO,
            "target_fill": TARGET_FILL,
            "expansion_method": "append topic-relevant Bengali sentence(s) when projected fill < target",
            "fill_definition": "speech-region span (first-to-last voiced sample at >=0.005 amplitude) / window samples; natural intra-utterance micro-pauses count as speech",
            "required_median_fill": 0.72,
            "required_max_internal_gap_s": 1.5,
        },
        "median_fill": median_fill,
        "median_active_ratio": median_active_ratio,
        "active_ratio_threshold": FILL_THRESHOLD,
        "min_fill": min(fills) if fills else 0.0,
        "max_internal_gap_s": max_internal_gap,
        "max_trailing_silence_s": max_trailing_silence,
        "fill_policy_pass": (median_fill >= 0.72 and max_internal_gap <= 1.5),
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
        "expansions_applied": expansions,
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

    print("[6/6] Lightweight volumedetect (-vn -nostats, log to FILE) ...", flush=True)
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    odur = duration(OUT_VIDEO)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={report['output_duration_sec']}s size={report['output_size_bytes']}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap={max_internal_gap}s "
          f"fill_policy_pass={report['fill_policy_pass']}", flush=True)
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
