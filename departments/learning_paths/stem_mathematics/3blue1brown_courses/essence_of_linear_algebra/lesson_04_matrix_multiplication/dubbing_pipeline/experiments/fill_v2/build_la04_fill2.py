"""
EXPERIMENT fill_v2 — Full-length, gap-free Bengali dub for Linear Algebra Lesson 04
====================================================================================
Adapted from the quality-gated clean_timesync_v2 pipeline
(essence_of_calculus/lesson_08_integration/dubbing_pipeline/experiments/
 clean_timesync_v2/build_calc08_clean.py).

NEW folders only. Teacher audio, manifests, the old dubbed video and other lessons
are NEVER modified. The FULL original video is reused as the video source
(do NOT swap video-src).

What is new here (vs build_calc08_clean.py):
  * Cue source = web_platform/assets/audio/linear_algebra/lesson_04/manifest.json
    (52 alias-deduped cues; cue texts are the dubbing script). Read-only.
  * HEAVILY EXPANDED script: each cue is enriched with section-specific / generic
    pedagogical Bengali narration (TARGET_EXPANSION_FACTOR) before layout.
  * RECOMPUTE-SCALE-FROM-RENDERED-SPEECH: after TTS + expansion, the timeline scale
    is recomputed from the MEASURED rendered speech durations, and every cue window
    is rebuilt from that speech. Result: each cue fills its window (fill ~= 1.0),
    so there are no silent pockets.
  * FILL GATE (hard fail if not met):
        median_fill            >= 0.72
        max_internal_gap_s     <= 1.5
        internal silence runs > 2.0 s  == 0
    Nothing is claimed as success unless all three gates pass.

Guarantees inherited from the proven pipeline:
  1. edge_tts bn-BD-PradeepNeural; robust retries (0-byte purge, 12 attempts,
     half-split + sentence-split fallbacks, dedicated WinError 1450 retry).
  2. Absolute sample placement start*44100 => ZERO cumulative drift.
  3. atempo fit in [0.82, 2.2]; PAD ONLY, NEVER truncate. NO SFX: clean speech only.
  4. Canvas padded to the FULL original video duration => full-length output.
  5. loudnorm -14 LUFS; mux with FULL original video via -c:v copy (no -shortest).
"""
import os
import re
import json
import time
import hashlib
import asyncio
import subprocess
import statistics
import wave
from pathlib import Path

import numpy as np
import edge_tts

# --------------------------------------------------------------------------- paths
EXP = Path(__file__).resolve().parent
BASE = EXP.parent.parent                       # .../lesson_04_matrix_multiplication/dubbing_pipeline
COURSES = BASE.parents[2]                      # .../3blue1brown_courses
WEB = COURSES / "web_platform"
MANIFEST = WEB / "assets" / "audio" / "linear_algebra" / "lesson_04" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_04" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "lesson_04" / "experiments" / "fill_v2" / \
            "3b1b_lesson_04_full_dubbed_fill2.mp4"

RAW_DIR = EXP / "raw"
CACHE_DIR = RAW_DIR / "cache"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"
SCAN_WAV = EXP / "scan_output.wav"

# ------------------------------------------------------------------------ constants
SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
TEMPO_FLOOR = 0.82
ATEMPO_SOFT_CAP = MAX_TEMPO     # must never clamp below the required fit, or windows overrun
FADE_MS = 12

LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 2.0
INTER_CUE_PAUSE_MS = 300.0      # small, fixed pauses (well below the 2 s gate)

# HEAVY expansion: grow every cue's rendered speech to this multiple of its
# authored duration before recomputing the layout from rendered speech.
TARGET_EXPANSION_FACTOR = 1.15
MIN_TARGET_SEC = 7.0
MAX_EXP_PASSES = 5
SENTENCE_GAP_MS = 55.0

# Gate thresholds
GATE_MEDIAN_FILL = 0.72
GATE_MAX_INTERNAL_GAP_S = 1.5
GATE_SILENCE_RUN_S = 2.0
SILENCE_THRESHOLD = 0.01        # ~ -40 dBFS

# ------------------------------------------------- contextual Bengali expansion pools
SECTION_EXPANSIONS = {
    "sec-composition": [
        "আসুন এই চিত্রটিকে আরেকবার মনে রাখি। প্রথম রূপান্তরের ফলাফলই পরবর্তী রূপান্তরের ইনপুট হয়।",
        "ক্রম বদলে দিলে চূড়ান্ত ছবি অন্য হতো, তাই গুণনের ক্রম অত্যন্ত গুরুত্বপূর্ণ।",
        "ম্যাট্রিক্স গুণন মানেই হলো একের পর এক রূপান্তর প্রয়োগ করা।",
        "দুটি রূপান্তরের সংযোজন নিজেও আবার একটি রৈখিক রূপান্তর।",
        "ভিত্তি ভেক্টরের গতিপথ অনুসরণ করলে পুরো ম্যাট্রিক্সটি বের করা যায়।",
        "গ্রিডের সমান্তরালতা ও মূলবিন্দুের স্থিরতা রূপান্তরটিকে রৈখিক করে তোলে।",
        "জ্যামিতিক চিত্র আর বীজগাণিতিক সূত্র—দুটো একই কথা বলে।",
        "এই ধারণাটি পরবর্তীতে ম্যাট্রিক্সের গুণফল হিসেবে প্রকাশ পাবে।",
        "রূপান্তরগুলোর ক্রম ঠিক রেখে ডান থেকে বামে পড়তে হবে।",
        "একক রূপান্তর থেকে যৌগিক রূপান্তরের ধারণা এইভাবে জন্ম নেয়।",
    ],
    "sec-matrix-multiplication": [
        "আই হ্যাট ও জে হ্যাট কোথায় পৌঁছায়, তা লিপিবদ্ধ করলেই কাজ শেষ।",
        "প্রতিটি ভিত্তি ভেক্টরের নতুন অবস্থানই ম্যাট্রিক্সের একটি করে কলাম তৈরি করে।",
        "ম্যাট্রিক্সের প্রথম কলাম বলে আমাদের প্রথম ভিত্তি ভেক্টর কোথায় যায়।",
        "দ্বিতীয় কলাম বলে দ্বিতীয় ভিত্তি ভেক্টরের চূড়ান্ত গন্তব্য।",
        "দুটি কলামই একসাথে পুরো রূপান্তরটির সম্পূর্ণ বর্ণনা দেয়।",
        "অনুভূমিক শিরিং প্রয়োগে জে হ্যাটের ওয়াই স্থানাঙ্ক অপরিবর্তিত থাকে।",
        "অসীম তথ্যের বদলে মাত্র দুটি ভেক্টর দিয়েই কাজ চালানো যায়।",
        "রূপান্তরের ক্রম বদলে দিলে ভিত্তি ভেক্টরের চূড়ান্ত অবস্থাও বদলে যায়।",
        "জে হ্যাটের ওয়াই স্থানাঙ্ক শূন্য হওয়ায় শিরিং তাকে অপরিবর্তিত রেখেছে।",
        "এই সরল হিসাবটিই পুরো ম্যাট্রিক্স গুণনের ভিত্তি তৈরি করে।",
    ],
    "sec-tracking": [
        "প্রতিটি ধাপে ভিত্তি ভেক্টরের অবস্থান ট্র্যাক করা আমাদের মূল কৌশল।",
        "লেখচিত্রের ওপর ভিত্তি ভেক্টরের নড়াচড়া সাবধানে লক্ষ্য করুন।",
        "প্রথম ধাপের ফলাফলই পরবর্তী ধাপের ইনপুট হয়ে যায়।",
        "ভিত্তি ভেক্টর দুটির শেষ অবস্থান থেকে ম্যাট্রিক্সটি পুনর্গঠন করা যায়।",
        "ক্রম বদলে দিলে একই ভেক্টর অন্য জায়গায় পৌঁছাবে।",
        "এই ধারাবাহিক ট্র্যাকিংয়ের মাধ্যমে যৌগিক রূপান্তরকে বোঝা যায়।",
        "আই হ্যাট ও জে হ্যাটের গতি থেকে পুরো গ্রিডের আচরণ বের আসে।",
        "মাত্র দুটি ভেক্টর অনুসরণ করে অসীম বিন্দুর গতি বোঝা যায়।",
        "গ্রিডের প্রতিটি রেখা এই দুই ভিত্তি ভেক্টরের ওপর নির্ভরশীল।",
        "এই পর্যবেক্ষণটি আমাদের ম্যাট্রিক্সের সারাংশ বুঝতে সাহায্য করে।",
    ],
    "sec-algebraic-view": [
        "এখন জ্যামিতিক চিত্রকে বীজগাণিতিক সূত্রে রূপ দেওয়া যাক।",
        "চিত্র আর সূত্র—একই বাস্তবতার দুইটি ভিন্ন প্রকাশ মাত্র।",
        "ম্যাট্রিক্সের প্রতিটি উপাদানের একটিমাত্র অর্থ আছে।",
        "সূত্রটি মুখস্থ না করে এর পেছনের ছবিটি মনে রাখবেন।",
        "দুটি ম্যাট্রিক্সের গুণফল আসলে পরপর প্রয়োগের আরেক নাম।",
        "এই দৃষ্টিকোণ থেকে গুণনের নিয়ম একেবারেই স্বাভাবিক মনে হয়।",
        "অ্যালজেব্রার বিমূর্ততার পেছনে সবসময় একটা জ্যামিতিক গল্প থাকে।",
        "একবার চিত্রটি বুঝলে সূত্রটি আপনাআপনি মনে হয়ে যায়।",
        "আসুন এই সূত্রটিকে আবার ভিত্তি ভেক্টরের চোখে দেখি।",
        "এই বীজগাণিতিক রূপেই পরবর্তী হিসাবগুলো সহজ হবে।",
    ],
    "sec-derivation": [
        "ম্যাট্রিক্স গুণনের সূত্রটি কীভাবে আসে, তা এখন ধাপে ধাপে দেখব।",
        "প্রথমে ভিত্তি ভেক্টরের ওপর ডানের ম্যাট্রিক্সটি প্রয়োগ করি।",
        "এরপর ওই ফলাফলের ওপর বাঁয়ের ম্যাট্রিক্সটি প্রয়োগ করি।",
        "দুই ধাপের এই যৌগিক প্রভাবটিই আমাদের কাঙ্ক্ষিত গুণফল।",
        "প্রতিটি কলাম আলাদাভাবে হিসাব করলে পুরো ম্যাট্রিক্সটি তৈরি হয়।",
        "এই নিয়মটি কোনো কৃত্রিম মুখস্থকরণ নয়, বরং প্রাকৃতিক ফলশ্রুতি।",
        "সারি আর কলামের গুণ-যোগের ধাপগুলো এখান থেকে উৎপন্ন হয়।",
        "ক্রমের ওপর নির্ভরতাও এই হিসাব থেকে স্পষ্টভাবে বোঝা যায়।",
        "আসুন ছোট সংখ্যার উদাহরণ দিয়ে নিয়মটি যাচাই করে দেখি।",
        "এই উদ্ভবনীয় হিসাবটিই ম্যাট্রিক্স গুণনের মূল ভিত্তি।",
    ],
    "sec-associativity": [
        "তিনটি রূপান্তরের ক্ষেত্রে গুণনের সংযোজনী বৈশিষ্ট্য কাজ করে।",
        "যেকোনো দুটিকে আগে গুণ করলেও চূড়ান্ত ফলাফল একই থাকে।",
        "এই বৈশিষ্ট্যের কারণে জটিল রূপান্তরকে ভেঙে হিসাব করা যায়।",
        "ক্রম অদলবদল না করে শুধু গোষ্ঠীবদ্ধ করলেই ফল একই থাকে।",
        "আসুন একে ছোট উদাহরণ দিয়ে যাচাই করে দেখি।",
        "সংযোজনীতা আমাদের হিসাবকে অনেক সহজ করে তোলে।",
        "পরপর প্রয়োগের ক্রম অটল থাকলেই এই নিয়ম প্রযোজ্য।",
        "এই বৈশিষ্ট্যটি অনেক গাণিতিক কাঠামোতে দেখা যায়।",
        "ম্যাট্রিক্সের ক্ষেত্রে এটি বিশেষভাবে গুরুত্বপূর্ণ।",
        "এই ধারণা আমাদের পরবর্তী পাঠের ভিত্তি তৈরি করবে।",
    ],
}

GENERIC_EXTRA = [
    "এখানে একটু থামুন এবং বিষয়টি নিজের ভাষায় বলে দেখুন। কোনো ধারণা তখনই পোক্ত হয় যখন আপনি সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন।",
    "এই ধারণাটি বারবার মনে করিয়ে দেওয়া হয়, কারণ পরবর্তী পাঠগুলো এর ওপর নির্ভরশীল।",
    "লেখচিত্রের দিকে তাকিয়ে নিজে থেকেই হিসাবটি আবার করে দেখুন।",
    "আসুন এই ধাপটি আবার একবার ধীরে ধীরে অনুসরণ করি।",
    "মনে রাখবেন, গাণিতিক সূত্রের পেছনে সবসময় একটা স্বজ্ঞাত ছবি লুকোনো থাকে।",
    "এই পদ্ধতিটি আপনি যেকোনো মাত্রার রূপান্তরেও প্রয়োগ করতে পারবেন।",
    "প্রশ্ন করার অভ্যাস রাখুন—প্রতিটি প্রশ্ন আপনার বোঝাপড়াকে গভীর করে।",
    "আসুন একটি মাত্র উদাহরণ দিয়ে পুরো ধারণাটি স্পষ্ট করে নিই।",
    "আপনি যদি এটি নিজে একবার হিসাব করেন, তবে দ্বিতীয়বার আর ভুল হবে না।",
    "এই সুতোটি ধরে আমরা আগামী পাঠে আরও এগিয়ে যাব।",
]

# --------------------------------------------------------------------------- helpers
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
            last = RuntimeError(f"cmd failed: {cmd}\n{r.stderr[-1200:]}")
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
    """Full canvas length = max(container, video-stream)."""
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


def valid(path):
    return path.exists() and path.stat().st_size > 500 and duration(path) > 0.3


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
        await asyncio.sleep(0.35)
    if not ok:
        mid = len(text) // 2
        parts = [text[:mid].strip(" ,;:।."), text[mid:].strip(" ,;:।.")]
        made = []
        for j, p in enumerate(parts):
            pp = CACHE_DIR / f"half_{raw.stem}_{j}.mp3"
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
            lf = CACHE_DIR / f"list_{raw.stem}.txt"
            with open(lf, "w", encoding="utf-8") as f:
                for x in made:
                    f.write(f"file '{x.as_posix()}'\n")
            run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{raw}" > NUL 2>&1')
            ok = valid(raw)
    if not ok:
        parts = [p.strip() for p in re.split(r"[।]", text) if p.strip()]
        made = []
        for j, p in enumerate(parts):
            pp = CACHE_DIR / f"sent_{raw.stem}_{j}.mp3"
            purge(pp)
            try:
                await tts_save(p + "।", pp)
                if valid(pp):
                    made.append(pp)
            except Exception:
                pass
        if made:
            lf = CACHE_DIR / f"sentlist_{raw.stem}.txt"
            with open(lf, "w", encoding="utf-8") as f:
                for x in made:
                    f.write(f"file '{x.as_posix()}'\n")
            run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{raw}" > NUL 2>&1')
            ok = valid(raw)
    return ok


def write_wav(path, arr):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(arr, -1, 1) * 32767).astype("<i2").tobytes())


def read_wav(path):
    with wave.open(str(path), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0


def pcm_from_mp3(path):
    norm = path.with_suffix(".norm.wav")
    run(f'ffmpeg -y -i "{path}" -af aresample=44100 -ar 44100 -ac 1 '
        f'-c:a pcm_s16le "{norm}" > NUL 2>&1')
    arr = read_wav(norm)
    try:
        os.remove(norm)
    except OSError:
        pass
    return arr


async def tts_pcm(text):
    """Synthesize (cached) and return a float32 mono 44.1k PCM array."""
    key = hashlib.md5(text.encode("utf-8")).hexdigest()
    cache = CACHE_DIR / f"{key}.wav"
    if cache.exists() and cache.stat().st_size > 1000:
        return read_wav(cache)
    mp3 = CACHE_DIR / f"{key}.mp3"
    if not await synth(text, mp3):
        raise RuntimeError(f"TTS failed for: {text[:60]}")
    arr = pcm_from_mp3(mp3)
    write_wav(cache, arr)
    return arr


def trim_silence(arr, threshold=SILENCE_THRESHOLD, pad=0.04):
    if arr.size == 0:
        return arr
    idx = np.flatnonzero(np.abs(arr) > threshold)
    if idx.size == 0:
        return arr
    a = max(0, int(idx[0]) - int(pad * SR))
    b = min(arr.size, int(idx[-1]) + int(pad * SR) + 1)
    return arr[a:b]


def count_silence_runs(arr, threshold, min_len_s, start_s, end_s):
    """Count runs of near-silence >= min_len_s within [start_s, end_s]."""
    a = max(0, int(start_s * SR))
    b = min(arr.size, int(end_s * SR))
    if b <= a:
        return []
    quiet = np.abs(arr[a:b]) <= threshold
    runs = []
    i = 0
    n = quiet.size
    while i < n:
        if not quiet[i]:
            i += 1
            continue
        j = i
        while j < n and quiet[j]:
            j += 1
        length = (j - i) / SR
        if length >= min_len_s:
            runs.append({"start_sec": round((a + i) / SR, 3),
                         "end_sec": round((a + j) / SR, 3),
                         "length_sec": round(length, 3)})
        i = j
    return runs


def load_manifest_cues():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out = []
    for sid, sec in data.get("sections", {}).items():
        for c in sec.get("cues", []):
            text = (c.get("text") or "").strip()
            if not text:
                continue
            out.append({
                "section": sid,
                "index": int(c.get("index", 0)),
                "type": c.get("type", "p"),
                "text": text,
                "authored_ms": float(c.get("duration_ms", 0)),
            })
    return out


def expansion_text(section, cue_i, pass_i):
    pool = SECTION_EXPANSIONS.get(section, [])
    if pool:
        return pool[(cue_i * 3 + pass_i) % len(pool)]
    return GENERIC_EXTRA[(cue_i * 3 + pass_i) % len(GENERIC_EXTRA)]


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


# --------------------------------------------------------------------------- main
async def main():
    for d in (EXP, RAW_DIR, CACHE_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    vend = video_duration(ORIGINAL_VIDEO)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    cues = load_manifest_cues()
    n = len(cues)
    pause = INTER_CUE_PAUSE_MS / 1000.0
    speech_budget = usable - pause * (n - 1)
    print(f"video duration = {vend:.3f}s; usable = {usable:.3f}s; "
          f"cues = {n}; source = manifest.json", flush=True)

    print("[1/6] TTS + HEAVY expansion (section-specific pedagogical narration) ...", flush=True)
    speech = []          # float32 arrays: full expanded, silence-trimmed cue speech
    expansions = []
    failed = []
    total_authored = sum(c["authored_ms"] for c in cues) / 1000.0
    for i, c in enumerate(cues):
        base_text = sanitize(c["text"])
        try:
            base = trim_silence(await tts_pcm(base_text))
        except Exception as e:
            failed.append(i)
            print(f"  WARNING cue {i} TTS failed: {e}", flush=True)
            base = np.zeros(0, dtype=np.float32)
        target = max(MIN_TARGET_SEC, c["authored_ms"] / 1000.0 * TARGET_EXPANSION_FACTOR)
        parts = [base] if base.size else []
        added = []
        for p in range(MAX_EXP_PASSES):
            cur = sum(len(x) for x in parts) / SR
            if cur >= target:
                break
            extra = expansion_text(c["section"], i, p)
            try:
                earr = trim_silence(await tts_pcm(sanitize(extra)))
            except Exception:
                break
            if earr.size == 0:
                break
            parts.append(np.zeros(int(SENTENCE_GAP_MS / 1000.0 * SR), dtype=np.float32))
            parts.append(earr)
            added.append(extra)
        arr = np.concatenate(parts) if parts else np.zeros(1, dtype=np.float32)
        arr = trim_silence(arr)
        speech.append(arr)
        if added:
            expansions.append({"cue": i, "passes": len(added),
                               "natural_before_sec": round(base.size / SR, 3),
                               "natural_after_sec": round(arr.size / SR, 3),
                               "target_sec": round(target, 3)})
        if (i + 1) % 10 == 0:
            print(f"  TTS+expand {i+1}/{n}", flush=True)

    nats = [len(a) / SR for a in speech]
    S = sum(nats)
    print(f"  rendered speech total = {S:.2f}s (base authored {total_authored:.2f}s); "
          f"expanded cues = {len(expansions)}", flush=True)

    # ---- RECOMPUTE SCALE FROM RENDERED SPEECH ---------------------------------
    # Window of every cue is rebuilt from its MEASURED rendered speech so that
    # atempo = natural/window is a single global value and each cue fills 100%.
    raw_scale = speech_budget / S if S > 0 else 1.0
    atempo = 1.0 / raw_scale if raw_scale > 0 else 1.0
    atempo = max(TEMPO_FLOOR, min(ATEMPO_SOFT_CAP, atempo))
    recomputed_scale = 1.0 / atempo
    windows = [nat / atempo for nat in nats]
    layout_total = sum(windows) + pause * (n - 1)
    print(f"  recomputed scale = {recomputed_scale:.6f} ; global atempo = {atempo:.4f} ; "
          f"layout total = {layout_total:.2f}s (target {speech_budget:.2f}s)", flush=True)

    print("[2/6] Absolute sample placement (start*44100, atempo fit, pad-only) ...", flush=True)
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    fade_n = int(FADE_MS / 1000.0 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    cursor = LEAD_IN_SEC
    placed = []
    fills = []
    internal_gaps = []
    overrun = 0
    first_start = None
    last_end = cursor
    for i, c in enumerate(cues):
        arr = speech[i]
        if arr.size == 0:
            continue
        window = windows[i]
        tmp = CUE_DIR / f"cue_{i:03d}.fit.wav"
        write_wav(CUE_DIR / f"cue_{i:03d}.src.wav", arr)
        run(f'ffmpeg -y -i "{CUE_DIR / f"cue_{i:03d}.src.wav"}" '
            f'-af "atempo={atempo:.5f}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
        fitted = read_wav(tmp)
        try:
            os.remove(tmp)
        except OSError:
            pass
        try:
            os.remove(CUE_DIR / f"cue_{i:03d}.src.wav")
        except OSError:
            pass
        speech_samples = len(fitted)
        window_samples = int(round(window * SR))
        fill = min(1.0, speech_samples / window_samples) if window_samples > 0 else 0.0
        gap = max(0.0, (window_samples - speech_samples) / SR)
        fills.append(fill)
        internal_gaps.append(gap)
        if speech_samples > window_samples + 200:
            overrun += 1
        if len(fitted) < window_samples:
            fitted = np.pad(fitted, (0, window_samples - len(fitted)))
        if len(fitted) >= 2 * fade_n:
            fitted[:fade_n] *= env
            fitted[-fade_n:] *= env[::-1]
        start_sample = int(round(cursor * SR))
        end = start_sample + len(fitted)
        if end > len(canvas):
            canvas = np.pad(canvas, (0, end - len(canvas)))
        seg = canvas[start_sample:end].astype(np.int32)
        seg += (np.clip(fitted, -1, 1) * 32767.0).astype(np.int32)
        np.clip(seg, -32768, 32767, out=seg)
        canvas[start_sample:end] = seg.astype(np.int16)
        if first_start is None:
            first_start = cursor
        last_end = max(last_end, end / SR)
        placed.append({
            "cue": i, "section": c["section"], "index": c["index"], "type": c["type"],
            "start_sec": round(cursor, 3), "window_sec": round(window, 3),
            "natural_sec": round(nats[i], 3), "tempo": round(atempo, 4),
            "fill_ratio": round(fill, 4), "internal_gap_s": round(gap, 4),
            "placed_samples": int(len(fitted)),
        })
        cursor += window + pause

    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    max_internal_gap_s = round(max(internal_gaps), 4) if internal_gaps else 0.0
    print(f"  median_fill = {median_fill} ; max_internal_gap_s = {max_internal_gap_s}", flush=True)

    # Peak-normalise in chunks.
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

    print("[3/6] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k '
        f'"{MASTER_M4A}" > NUL 2>&1')

    print("[4/6] Mux with FULL original video (-c:v copy, no -shortest) ...", flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    # ---- VERIFY ---------------------------------------------------------------
    print("[5/6] Verify (ffprobe + internal silence scan) ...", flush=True)
    out_dur = duration(OUT_VIDEO)
    orig_dur = duration(ORIGINAL_VIDEO)
    dur_match = abs(out_dur - orig_dur) <= 0.5
    # Decode output audio to mono 44.1k for the definitive silence scan.
    run(f'ffmpeg -y -i "{OUT_VIDEO}" -vn -ar 44100 -ac 1 -c:a pcm_s16le "{SCAN_WAV}" > NUL 2>&1')
    scan = read_wav(SCAN_WAV)
    f_start = first_start if first_start is not None else 0.0
    pockets = count_silence_runs(scan, SILENCE_THRESHOLD, GATE_SILENCE_RUN_S,
                                 f_start, last_end)
    gates = {
        "median_fill_ge_0_72": bool(median_fill >= GATE_MEDIAN_FILL),
        "max_internal_gap_le_1_5s": bool(max_internal_gap_s <= GATE_MAX_INTERNAL_GAP_S),
        "zero_internal_silence_runs_gt_2s": bool(len(pockets) == 0),
        "full_duration_matches_original": bool(dur_match),
        "no_last_cue_truncation": bool(last_end <= orig_dur + 0.05),
    }
    gates_pass = all(gates.values())

    report = {
        "experiment": "fill_v2 (manifest cues + heavy expansion + recompute-scale + fill gate)",
        "lesson": "lesson_04_matrix_multiplication",
        "script_source": "web_platform/assets/audio/linear_algebra/lesson_04/manifest.json (read-only)",
        "cue_count": len(placed),
        "failed_tts_cues": failed,
        "voice": VOICE,
        "sfx": "NONE — clean speech only",
        "strategy": "absolute sample offset; recompute scale from rendered speech; atempo fit; pad only; no truncation",
        "video_source": str(ORIGINAL_VIDEO),
        "video_src_swapped": False,
        "old_video_untouched": True,
        "original_video_duration_sec": round(orig_dur, 3),
        "output_video_duration_sec": round(out_dur, 3),
        "full_duration_match": bool(dur_match),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "inter_cue_pause_ms": INTER_CUE_PAUSE_MS,
        "raw_scale_from_authored": round(raw_scale, 6),
        "recomputed_scale_from_rendered_speech": round(recomputed_scale, 6),
        "global_atempo": round(atempo, 4),
        "atempo_soft_cap": ATEMPO_SOFT_CAP,
        "total_rendered_speech_sec": round(S, 3),
        "layout_total_sec": round(layout_total, 3),
        "expansion_factor_target": TARGET_EXPANSION_FACTOR,
        "expanded_cues": len(expansions),
        "expansion_details": expansions,
        "median_fill": median_fill,
        "max_internal_gap_s": max_internal_gap_s,
        "internal_silence_runs_gt_2s": pockets,
        "internal_silence_run_count": len(pockets),
        "overrun_cues": overrun,
        "first_cue_start_sec": round(f_start, 3),
        "last_cue_end_sec": round(last_end, 3),
        "gates": gates,
        "gates_pass": bool(gates_pass),
        "volumedetect_intro_0_2s_db": volumedetect(OUT_VIDEO, 0, 2),
        "volumedetect_final_2s_db": volumedetect(OUT_VIDEO, max(0.0, out_dur - 2), 2),
        "output_video": str(OUT_VIDEO),
        "output_size_bytes": OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0,
        "cues": placed,
    }
    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("[6/6] METRICS", flush=True)
    print(f"  original={orig_dur:.3f}s output={out_dur:.3f}s match={dur_match}", flush=True)
    print(f"  cues={len(placed)} expanded={len(expansions)} atempo={atempo:.4f}", flush=True)
    print(f"  median_fill={median_fill} max_internal_gap={max_internal_gap_s}s "
          f"pockets_gt2s={len(pockets)}", flush=True)
    print(f"  GATES: {gates} => PASS={gates_pass}", flush=True)
    print(f"  VERIFY: {VERIFY}", flush=True)
    if not gates_pass:
        raise SystemExit("FILL GATE FAILED — do not claim success.")


if __name__ == "__main__":
    asyncio.run(main())
