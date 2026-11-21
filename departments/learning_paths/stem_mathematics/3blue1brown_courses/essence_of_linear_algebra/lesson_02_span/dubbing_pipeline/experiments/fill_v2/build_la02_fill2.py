"""
EXPERIMENT — Full-length, gap-free Bengali dub (Essence of Linear Algebra, Lesson 02)
=====================================================================================
Re-render of lesson_02 to eliminate the 19 silent pockets (up to ~16 s) of the previous
clean_timesync_v2 output.  Adapted from the proven, quality-gated pipeline:

    essence_of_calculus/lesson_08_integration/dubbing_pipeline/experiments/
        clean_timesync_v2/build_calc08_clean.py

NEW in this variant (per governance / orchestrator request):
  * Cue script comes from the AUDIO MANIFEST
    (web_platform/assets/audio/linear_algebra/lesson_02/manifest.json);
    cue texts are used as the dubbing script, alias/deduplicate by text, in order.
  * RECOMPUTE SCALE FROM RENDERED SPEECH: after TTS (+ heavy contextual expansion of
    any cue short of its proportional share), windows are rebuilt from the ACTUAL
    rendered speech durations so speech fills each window instead of leaving pockets.
  * FILL GATE (hard, fails the build if unmet):
        median_fill              >= 0.72
        max_internal_gap_s       <= 1.5
        internal silence runs > 2 s == 0   (measured on the rendered master)
  * HEAVY EXPANSION: a large pedagogical Bengali expansion pool and up to 12 passes
    per cue are applied adaptively to every cue that renders short of its share.

Kept from the proven pipeline:
  * edge_tts bn-BD-PradeepNeural; robust retries (0-byte purge, 12 attempts,
    half-split + sentence-split fallbacks, dedicated WinError 1450 retry).
  * Absolute sample placement start*44100 -> ZERO cumulative drift.
  * atempo fit clamped to [0.82, 2.2]; PAD ONLY, NEVER truncate. NO SFX.
  * Full-video canvas padding so -shortest can never trim video frames.
  * loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
  * Lightweight volumedetect (-vn -nostats, log to FILE).

SAFETY: teacher audio, manifests, the previous output video and all other lessons are
NEVER modified.  All new files live under experiments/fill_v2/ and
media_vault/lesson_02/experiments/fill_v2/.  The video source is the FULL original.
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
BASE = EXP.parent.parent                       # .../lesson_02_span/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"         # .../3blue1brown_courses/web_platform
MANIFEST = WEB / "assets" / "audio" / "linear_algebra" / "lesson_02" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_02" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "lesson_02" / "experiments" / "fill_v2" / "3b1b_lesson_02_full_dubbed_fill2.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
TEMPO_FLOOR = 0.82
FADE_MS = 12
VIDEO_ID = "3b1b_lesson_02"
LESSON = "lesson_02_span"

# Lead/tail quiet margins and the deliberate inter-cue breath pause.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 300.0

# Heavy expansion: append large contextual pedagogical blocks to a cue until its
# natural TTS reaches this fraction of its proportional share of the speech budget.
TARGET_FILL_RATIO = 0.97
EXPAND_TRIGGER_RATIO = 0.92
MAX_EXPAND_PASSES = 12

# Fill gate (hard requirements).
GATE_MEDIAN_FILL = 0.72
GATE_MAX_INTERNAL_GAP_S = 1.5
GATE_MAX_SILENCE_RUN_S = 2.0
SILENCE_THRESHOLD_DB = -45.0

# Large contextual Bengali pool used by the heavy-expansion subsystem.  Each entry
# is topically aligned with Lesson 02 (basis vectors, linear combinations, span,
# linear dependence/independence) so expansion also improves teaching quality.
EXPANSION_POOL = [
    " এখানে একটু থামুন আর নিজের ভাষায় বিষয়টি বলে দেখুন। কোনো ধারণা তখনই পোক্ত হয় যখন আপনি সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন।",
    " মনে রাখবেন, ভেক্টরকে সংখ্যায় প্রকাশ করার অর্থ হলো একটি নির্দিষ্ট ভিত্তি বেছে নেওয়া। ভিত্তি বদলালে সংখ্যার অর্থও বদলে যায়, কিন্তু জ্যামিতিক বস্তুটি একই থাকে।",
    " আই হ্যাট আর জে হ্যাটকে মানসিকভাবে ধরে রাখলে পুরো দ্বিমাত্রিক স্থানের হিসাব সহজ হয়। যেকোনো ভেক্টরকে এর দুটি উপাদানে ভেঙে দেখার অভ্যাস গড়ে তুলুন।",
    " স্কেলার শব্দটির আক্ষরিক অর্থ হলো যা মাপের পরিমাণ বদলায়। এখানে স্কেলার ভেক্টরের দৈর্ঘ্য বা দিক নির্ধারণ করে, তাই স্কেলারকে আলাদা করে ভাবা জরুরি।",
    " রৈখিক সমন্বয়ের এই গঠন একদিকে যেমন সরল, অন্যদিকে তেমনি গভীর। কেবল দুটি মৌলিক কাজ—স্কেলিং আর যোগ—ব্যবহার করে পুরো সমতল তৈরি করা যায়।",
    " যখন দুটি ভেক্টর সমান্তরাল নয়, তখন তাদের রৈখিক সমন্বয় সমতলের প্রতিটি বিন্দুতে পৌঁছাতে পারে। এটিই স্প্যান ধারণার ভিত্তি।",
    " স্প্যান মানে কেবল একটি সেট নয়, এটি এক ধরনের পৌঁছানোর ক্ষমতা। কোন ভেক্টরগুলোর সাহায্যে কতদূর যাওয়া যায়, তাই হলো মূল প্রশ্ন।",
    " ভেক্টরকে তীর হিসেবে ভাবুন যখন একটি মাত্র ভেক্টর নিয়ে কাজ করছেন। আর পুরো সংগ্রহ নিয়ে কাজ করলে শীর্ষবিন্দুগুলোকে বিন্দু হিসেবে কল্পনা করাই সুবিধাজনক।",
    " একটি ভেক্টর স্পেসের ভিত্তি মানে এমন ভেক্টরের সেট যারা পরস্পরের ওপর নির্ভরশীল নয় আবার পুরো স্থানকেও আচ্ছাদিত করে। এই দুই শর্তই অত্যাবশ্যক।",
    " রৈখিক নির্ভরতা আর স্বাধীনতার পার্থক্য বোঝা গেলেই ভিত্তির সংজ্ঞাটি স্বাভাবিকভাবেই পরিষ্কার হয়ে যায়। এগুলো আলাদা করে মনে রাখবেন।",
    " তৃতীয় ভেক্টরটি যদি আগের দুটির সমতলে পড়ে, তবে সে কোনো নতুন মাত্রা যোগ করে না। তখন সেটিকে অতিরিক্ত বা অপ্রয়োজনীয় বলা হয়।",
    " অসীম সংখ্যক ভেক্টর নিয়ে ভাবতে গেলে চিত্র আঁকা কঠিন। তাই শীর্ষবিন্দু দিয়ে বিন্দু হিসেবে উপস্থাপন করা আমাদের চিন্তাকে সুগম করে তোলে।",
    " লিনিয়ার বীজগণিতের সৌন্দর্য হলো জ্যামিতি আর বীজগণিতের এই মিলন। একদিকে ছবি, অন্যদিকে সংখ্যা—দুটো একই কথা ভিন্ন ভাষায় বলে।",
    " পরবর্তী পাঠে ম্যাট্রিক্স আসবে, আর তখন এই ভিত্তি ও স্প্যানের ধারণা নতুন করে কাজে আসবে। তাই আজকের মৌলিক ধারণাগুলো ভালো করে মনে রাখুন।",
    " একটি নির্দিষ্ট ভেক্টরকে তিন আই হ্যাট যোগ মাইনাস দুই জে হ্যাট লেখার অর্থ হলো—আমরা সেটিকে ভিত্তি ভেক্টরের ভাষায় অনুবাদ করেছি।",
    " স্থানাঙ্ক ব্যবস্থা বদল মানে জগৎ বদল নয়, বরং সেই একই জগৎকে নতুন করে বর্ণনা করা। এই পার্থক্যটি বুঝতে পারলে অনেক বিভ্রান্তি দূর হয়।",
    " সরলরেখা, সমতল আর ত্রিমাত্রিক স্থান—এই তিনটি স্তরের স্প্যান একই নীতি অনুসরণ করে। শুধু মাত্রার সংখ্যা বাড়ে, যুক্তি একই থাকে।",
    " যখন দুটি স্কেলার স্বাধীনভাবে পরিবর্তন করি, তখন লব্ধি ভেক্টরের শীর্ষবিন্দু সমতলে পাতলা চাদরের মতো ছড়িয়ে পড়ে। এই ছবিটি মনে রাখবেন।",
    " কোনো ভেক্টর বাদ দিলেও যদি স্প্যান একই থাকে, বুঝতে হবে সেটি আগেই বাকিদের স্প্যানের ভেতরে ছিল। এটিই নির্ভরশীলতার সহজ পরীক্ষা।",
    " লম্ব ভিত্তি বিশেষভাবে সুবিধাজনক কারণ এখানে অক্ষগুলো পরস্পরের সমকোণে থাকে। গণনা সহজ হওয়ায় প্রকৌশলে এটি বহুল ব্যবহৃত।",
    " প্রতিটি উদাহরণের সাথে নিজের মনে একটি করে ভেক্টর কল্পনা করুন। এই সক্রিয় পদ্ধতি শিখনে অনেক গভীর প্রভাব ফেলে।",
    " গাণিতিক সংজ্ঞা মুখস্থ করার আগে তার পেছনের ছবিটি বোঝা জরুরি। ছবি পরিষ্কার হলে সূত্র নিজে নিজেই মনে থেকে যায়।",
    " কখনো ভাবুন, যদি আই হ্যাটের বদলে সম্পূর্ণ নতুন দিকের ভেক্টর বেছে নেওয়া হতো, তবে কী পরিবর্তন হতো? এই প্রশ্নটি গভীর চিন্তার জন্ম দেয়।",
    " দ্বিমাত্রিক হোক বা ত্রিমাত্রিক, সব ক্ষেত্রেই স্কেলিং আর যোগের এই দুটি কাজ আবার আবার ফিরে আসে। এটিই পুরো অধ্যায়ের কেন্দ্রীয় সুতো।",
    " ভেক্টরের দিক আর দৈর্ঘ্য—এই দুটি বৈশিষ্ট্যই তার পূর্ণ পরিচয়। সংখ্যার জোড়া কেবল এই পরিচয়ের এক লিখিত রূপ মাত্র।",
    " শূন্য ভেক্টর একটি বিশেষ ক্ষেত্র, কারণ এটি যেকোনো স্কেলার দিয়ে গুণ করলেও শূন্য থাকে। তাই এটি কখনো নতুন মাত্রা যোগ করতে পারে না।",
    " স্প্যানের ধারণা আমাদের বলে কোন ভেক্টরগুলো পৌঁছানো যোগ্য আর কোনটির জন্য নতুন ভিত্তি দরকার। এটি ভেক্টর স্পেসের সীমানা নির্ধারণ করে।",
    " স্বাধীন ভেক্টরের সংখ্যা যত বাড়ে, স্প্যানের মাত্রাও তত বাড়ে। এই সরল সম্পর্কই র‍্যাংক আর মাত্রার মতো ধারণার ভিত্তি গড়ে তোলে।",
    " আজ যে ধারণাগুলো শিখলাম—ভিত্তি, রৈখিক সমন্বয়, স্প্যান ও নির্ভরতা—এগুলো পরবর্তী সব অধ্যায়ের ভাষা হয়ে কাজ করবে।",
    " একটি ধারণা বোঝার সেরা উপায় হলো সেটিকে বিভিন্ন উদাহরণে পরীক্ষা করা। তাই প্রতিটি নতুন চিত্রের সাথে পুরনো উদাহরণটি মনে করে দেখুন।",
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
            last = RuntimeError("cmd failed: %s\n%s" % (cmd, r.stderr[-1500:]))
        except OSError as e:
            last = e
            if not is_win1450(e):
                raise
        if attempt < retries - 1:
            time.sleep(0.5 * (attempt + 1))
    raise last


def duration(path):
    out = run('ffprobe -v error -show_entries format=duration '
              '-of default=noprint_wrappers=1:nokey=1 "%s"' % path)
    try:
        return float(out.strip())
    except Exception:
        return 0.0


def video_duration(path):
    """Full canvas length = max(container, video-stream) so -shortest cannot trim."""
    d = duration(path)
    try:
        sd = float(run('ffprobe -v error -select_streams v:0 -show_entries stream=duration '
                       '-of default=noprint_wrappers=1:nokey=1 "%s"' % path).strip())
        d = max(d, sd)
    except Exception:
        pass
    return d


def sanitize(text):
    t = text
    for ch in ["\u2014", "\u2013", "\u2212", "-"]:
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
            pp = RAW_DIR / ("half_%s_%d.mp3" % (raw.stem, j))
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
            lf = RAW_DIR / ("list_%s.txt" % raw.stem)
            with open(lf, "w", encoding="utf-8") as f:
                for x in made:
                    f.write("file '%s'\n" % x.as_posix())
            run('ffmpeg -y -f concat -safe 0 -i "%s" -c copy "%s" > NUL 2>&1' % (lf, raw))
            ok = valid(raw)
    if not ok:
        parts = [p.strip() for p in re.split(r"[।]", text) if p.strip()]
        made = []
        for j, p in enumerate(parts):
            pp = RAW_DIR / ("sent_%s_%d.mp3" % (raw.stem, j))
            purge(pp)
            try:
                await tts_save(p + "।", pp)
                if valid(pp):
                    made.append(pp)
            except Exception:
                pass
        if made:
            lf = RAW_DIR / ("sentlist_%s.txt" % raw.stem)
            with open(lf, "w", encoding="utf-8") as f:
                for x in made:
                    f.write("file '%s'\n" % x.as_posix())
            run('ffmpeg -y -f concat -safe 0 -i "%s" -c copy "%s" > NUL 2>&1' % (lf, raw))
            ok = valid(raw)
    return ok


def load_manifest_cues():
    """Read cue TEXTS from the read-only audio manifest, alias-deduped, in order."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out, seen = [], set()
    for sec_id, sec in data.get("sections", {}).items():
        for c in sec.get("cues", []):
            text = (c.get("text") or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            out.append({
                "id": len(out) + 1,
                "text": text,
                "dur_ms": float(c.get("duration_ms", 0) or 0),
                "section": sec_id,
                "type": str(c.get("type", "")),
            })
    return out


def speech_budget(vend, n_cues):
    """Seconds available for actual speech after margins + inter-cue pauses."""
    pauses = (INTER_CUE_PAUSE_MS / 1000.0) * max(0, n_cues - 1)
    return max(30.0, vend - LEAD_IN_SEC - TAIL_MARGIN_SEC - pauses)


def proportional_targets(source_cues, budget):
    """Per-cue target speech seconds, weighted by the manifest authored durations."""
    weights = [max(1.0, float(c["dur_ms"])) for c in source_cues]
    total = sum(weights)
    return [budget * w / total for w in weights]


async def synth_all(cues, texts):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, c in enumerate(cues):
        raw = RAW_DIR / ("raw_%03d.mp3" % c["id"])
        ok = await synth(sanitize(texts[i]), raw)
        if not ok:
            failed.append(c["id"])
            print("  WARNING cue %d failed after every fallback" % c["id"], flush=True)
        if (i + 1) % 10 == 0:
            print("  TTS %d/%d" % (i + 1, len(cues)), flush=True)
    return failed


async def heavy_expand(cues, texts, targets):
    """HEAVY EXPANSION: append large pedagogical blocks to any cue that renders
    short of its proportional share, repeating up to MAX_EXPAND_PASSES times.
    """
    expanded = []
    for i, c in enumerate(cues):
        cid = c["id"]
        raw = RAW_DIR / ("raw_%03d.mp3" % cid)
        if not valid(raw):
            continue
        target = targets[i]
        natural = duration(raw)
        if natural <= 0 or natural >= EXPAND_TRIGGER_RATIO * target:
            continue
        before = natural
        added = []
        for attempt in range(MAX_EXPAND_PASSES):
            natural = duration(raw)
            if natural >= TARGET_FILL_RATIO * target:
                break
            extra = EXPANSION_POOL[(cid - 1 + attempt) % len(EXPANSION_POOL)]
            new_text = sanitize(texts[i] + " " + " ".join(added) + " " + extra)
            print("  heavy-expand cue %d pass %d: natural=%.2fs target=%.2fs"
                  % (cid, attempt + 1, natural, target), flush=True)
            if not await synth(new_text, raw, force=True):
                break
            added.append(extra)
        after = duration(raw)
        expanded.append({
            "id": cid,
            "natural_before": round(before, 3),
            "natural_after": round(after, 3),
            "target_sec": round(target, 3),
            "passes": len(added),
        })
    return expanded


def read_pcm(path):
    norm = path.with_suffix(".norm.wav")
    run('ffmpeg -y -i "%s" -af aresample=44100 -ar 44100 -ac 1 -c:a pcm_s16le "%s" > NUL 2>&1'
        % (path, norm))
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
    """atempo-fit into the window with floor 0.82 / ceiling 2.2; PAD only, NEVER cut."""
    natural = duration(raw)
    if natural <= 0:
        natural = target
    if cid == LAST_ID:
        target = min(target, VIDEO_END - LAST_START - 0.10)
    tempo = max(TEMPO_FLOOR, min(MAX_TEMPO, natural / target)) if target > 0 else TEMPO_FLOOR
    tmp = out.with_suffix(".fit.wav")
    run('ffmpeg -y -i "%s" -af "atempo=%.4f" -ar 44100 -ac 1 -c:a pcm_s16le "%s" > NUL 2>&1'
        % (raw, tempo, tmp))
    arr = read_pcm(tmp)
    speech_samples = len(arr)
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


def internal_silence_report(canvas, first_sample, last_sample, threshold_db, min_run_s):
    """Find contiguous near-silence runs strictly INSIDE [first_sample, last_sample]."""
    thr = 10.0 ** (threshold_db / 20.0)
    if last_sample <= first_sample:
        return [], 0.0
    seg = canvas[first_sample:last_sample]
    quiet = np.abs(seg.astype(np.float32)) / 32768.0 < thr
    runs = []
    i = 0
    n = len(quiet)
    while i < n:
        if quiet[i]:
            j = i + 1
            while j < n and quiet[j]:
                j += 1
            dur = (j - i) / SR
            if dur >= 0.05:
                runs.append({
                    "start_sec": round((first_sample + i) / SR, 3),
                    "end_sec": round((first_sample + j) / SR, 3),
                    "duration_sec": round(dur, 3),
                })
            i = j
        else:
            i += 1
    long_runs = [r for r in runs if r["duration_sec"] > min_run_s]
    max_run = max((r["duration_sec"] for r in runs), default=0.0)
    return long_runs, max_run


def volumedetect(path, start, length):
    """Audio-only volumedetect; log to a FILE so ffmpeg output never floods RAM."""
    log = EXP / "_volumedetect.log"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-nostats", "-vn", "-i", str(path),
           "-af", "atrim=start=%s:duration=%s,volumedetect" % (start, length),
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


async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    source_cues = load_manifest_cues()
    texts = [sanitize(c["text"]) for c in source_cues]
    n = len(source_cues)
    budget = speech_budget(vend, n)
    targets = proportional_targets(source_cues, budget)
    print("video duration = %.3fs; cues = %d; budget = %.3fs; source = manifest.json"
          % (vend, n, budget), flush=True)

    print("[1/7] TTS from manifest cue texts (clean, no SFX) ...", flush=True)
    failed = await synth_all(source_cues, texts)

    print("[2/7] HEAVY expansion of short cues ...", flush=True)
    expansions = await heavy_expand(source_cues, texts, targets)

    # --- RECOMPUTE SCALE FROM RENDERED SPEECH -------------------------------
    rendered = []
    for c in source_cues:
        raw = RAW_DIR / ("raw_%03d.mp3" % c["id"])
        rendered.append(duration(raw) if valid(raw) else 0.0)
    total_rendered = sum(rendered)
    if total_rendered <= 0:
        raise RuntimeError("no rendered speech at all — cannot compute scale")
    recomputed_scale = budget / total_rendered
    print("rendered speech total = %.3fs; recomputed scale (budget/rendered) = %.6f"
          % (total_rendered, recomputed_scale), flush=True)

    # Build windows proportional to ACTUAL rendered speech.
    cues = []
    cursor = LEAD_IN_SEC
    for i, c in enumerate(source_cues):
        window = rendered[i] * recomputed_scale
        cues.append({
            "id": i + 1,
            "start": round(cursor, 4),
            "end": round(cursor + window, 4),
            "duration": round(window, 4),
            "section": c["section"],
            "type": c["type"],
            "rendered": round(rendered[i], 3),
        })
        cursor += window + INTER_CUE_PAUSE_MS / 1000.0
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print("layout ends at %.3fs (video %.3fs)" % (cues[-1]["end"], vend), flush=True)

    print("[3/7] Absolute sample placement (start*44100, pad-only, floor 0.82) ...", flush=True)
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed, fills, internal_gaps = [], [], []
    overrun = 0
    last_cue_end = 0.0
    first_speech_sample = None
    last_speech_sample = 0
    expanded_ids = {x["id"] for x in expansions}
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / ("raw_%03d.mp3" % cid)
        if not valid(raw):
            print("  SKIP cue %d (no audio)" % cid, flush=True)
            continue
        arr, info = make_cue(raw, float(c["duration"]),
                             CUE_DIR / ("cue_%03d.wav" % cid), cid)
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
        # Track the true non-silent extent for the internal-silence audit.
        speech_len = min(info["speech_samples"], len(arr))
        if speech_len > 0:
            s0 = start_sample
            s1 = start_sample + speech_len
            first_speech_sample = s0 if first_speech_sample is None else min(first_speech_sample, s0)
            last_speech_sample = max(last_speech_sample, s1)
        del arr, i16, seg
        last_cue_end = max(last_cue_end, end / SR)
        expected_ms = round(float(c["start"]) * 1000, 2)
        actual_ms = round(start_sample / SR * 1000, 2)
        placed.append({
            "id": cid,
            "section": c["section"],
            "type": c["type"],
            "expected_start_ms": expected_ms,
            "actual_start_ms": actual_ms,
            "drift_ms": round(actual_ms - expected_ms, 6),
            "tempo": info["tempo"],
            "natural_sec": info["natural"],
            "target_sec": info["target"],
            "rendered_sec": c["rendered"],
            "fill_ratio": info["fill_ratio"],
            "internal_gap_s": info["internal_gap_s"],
            "placed_samples": int(round(end - start_sample)),
            "expanded": cid in expanded_ids,
        })

    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    max_internal_gap_s = round(max(internal_gaps), 4) if internal_gaps else 0.0
    long_runs, max_silence_run_s = internal_silence_report(
        canvas, first_speech_sample or 0, last_speech_sample,
        SILENCE_THRESHOLD_DB, GATE_MAX_SILENCE_RUN_S)
    n_long_runs = len(long_runs)
    print("median_fill=%.4f max_internal_gap_s=%.4f internal_silence_runs>2s=%d max_run=%.3fs"
          % (median_fill, max_internal_gap_s, n_long_runs, max_silence_run_s), flush=True)

    gates = {
        "median_fill>=0.72": bool(median_fill >= GATE_MEDIAN_FILL),
        "max_internal_gap_s<=1.5": bool(max_internal_gap_s <= GATE_MAX_INTERNAL_GAP_S),
        "internal_silence_runs_gt_2s==0": bool(n_long_runs == 0),
    }
    gates_pass = all(gates.values())

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

    print("[4/7] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run('ffmpeg -y -i "%s" -af "%s" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "%s" > NUL 2>&1'
        % (MASTER_WAV, af, MASTER_MP3))
    run('ffmpeg -y -i "%s" -af "%s" -ar 44100 -ac 2 -c:a aac -b:a 192k "%s" > NUL 2>&1'
        % (MASTER_WAV, af, MASTER_M4A))

    print("[5/7] Mux with FULL original video (video copy) ...", flush=True)
    run('ffmpeg -y -i "%s" -i "%s" -map 0:v:0 -map 1:a:0 '
        '-c:v copy -c:a aac -shortest "%s" > NUL 2>&1'
        % (ORIGINAL_VIDEO, MASTER_M4A, OUT_VIDEO))

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    odur = duration(OUT_VIDEO)
    report = {
        "experiment": "fill_v2 — manifest-script, recompute-scale-from-rendered-speech, hard fill gate",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": "audio manifest cue texts (alias-deduped): %s" % MANIFEST.name,
        "video_source": str(ORIGINAL_VIDEO),
        "voice": VOICE,
        "sfx": "NONE — clean speech only",
        "strategy": "absolute sample offset (start*44100); atempo fit in [0.82,2.2]; pad only; "
                    "windows rebuilt from rendered speech; no truncation",
        "cue_count": len(placed),
        "expected_cue_count": n,
        "failed_tts_cues": failed,
        "max_tempo": MAX_TEMPO,
        "tempo_floor": TEMPO_FLOOR,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "inter_cue_pause_ms": INTER_CUE_PAUSE_MS,
        "speech_budget_sec": round(budget, 3),
        "rendered_speech_total_sec": round(total_rendered, 3),
        "recomputed_scale": round(recomputed_scale, 6),
        "heavy_expansion": {
            "pool_size": len(EXPANSION_POOL),
            "trigger_ratio": EXPAND_TRIGGER_RATIO,
            "target_fill_ratio": TARGET_FILL_RATIO,
            "max_passes": MAX_EXPAND_PASSES,
            "cues_expanded": len(expansions),
            "details": expansions,
        },
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "median_fill": median_fill,
        "max_internal_gap_s": max_internal_gap_s,
        "internal_silence_runs_gt_2s": n_long_runs,
        "max_internal_silence_run_s": round(max_silence_run_s, 3),
        "internal_silence_run_details": long_runs,
        "silence_threshold_db": SILENCE_THRESHOLD_DB,
        "fill_gate": gates,
        "fill_gate_pass": gates_pass,
        "output_video": str(OUT_VIDEO),
        "output_duration_sec": round(odur, 3),
        "output_size_bytes": OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0,
        "cues": placed,
    }
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\nDONE. cues=%d overrun=%d drift=%.3fms" % (len(placed), overrun, max_drift), flush=True)
    print("video=%.3fs (original %.3fs) size=%d" % (odur, vend, report["output_size_bytes"]), flush=True)
    print("median_fill=%s max_internal_gap_s=%s runs>2s=%d gates=%s"
          % (median_fill, max_internal_gap_s, n_long_runs, gates), flush=True)
    print("VERIFY: %s" % VERIFY, flush=True)

    if not gates_pass:
        raise SystemExit("FILL GATE FAILED — refusing to claim success: %s" % gates)
    if abs(odur - vend) > 2.0:
        raise SystemExit("DURATION MISMATCH — output %.3fs vs original %.3fs" % (odur, vend))


if __name__ == "__main__":
    asyncio.run(main())
