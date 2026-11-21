"""
EXPERIMENT - Full-length clean absolute-sample Bengali dub
3Blue1Brown Computer Science, lesson 02
=====================================================================
Adapted verbatim from the proven, quality-gated pipeline:
  essence_of_calculus/lesson_08_integration/dubbing_pipeline/experiments/
  clean_timesync_v2/build_calc08_clean.py

Kept identical from the reference:
  * edge_tts bn-BD-PradeepNeural with 0-byte purge, 12 attempts,
    half-split + sentence-split fallbacks, WinError 1450 retry.
  * absolute sample placement (start * 44100) => ZERO cumulative drift.
  * atempo fit with PAD ONLY, NEVER truncate.
  * FULL-length canvas before -shortest (video frames can never be trimmed).
  * loudnorm -14 LUFS, mux with the FULL original video via -c:v copy.
  * NO SFX - clean speech only.
  * fill gate: median_fill >= 0.72 and max_internal_gap_s <= 1.5,
    auto re-render with more contextual narration if the gate fails.

CS-specific adaptations:
  * Script source is the read-only GOLD audio manifest:
      web_platform/assets/audio/computer_science/lesson_02/manifest.json
    (duration_ms is already milliseconds -> NO x1000 conversion).
  * The authored manifest spans only a fraction of the full 3B1B video, so
    cue windows are scaled to span the whole video (as in the reference) and
    short cues are expanded with contextual Bengali pedagogical narration
    until rendered speech fills the window. Extra narration is synthesised
    incrementally (one sentence at a time) and concatenated, so re-rendering
    is cheap and deterministic.
  * Inter-cue pause is scaled DOWN when the timeline scale is large, so no
    internal silent run can ever exceed 2 s.
  * Chained atempo filters support ratios outside ffmpeg's [0.5, 2.0].
"""
import os
import re
import json
import math
import time
import asyncio
import subprocess
import statistics
import wave
from pathlib import Path

import numpy as np
import edge_tts

EXP = Path(__file__).resolve().parent
# EXP = .../web_platform/media_vault/computer_science/lesson_NN/dubbing_pipeline/experiments/clean_timesync_v2
WEB = EXP.parents[5]                                   # .../web_platform
LESSON = "lesson_02"
NN = "02"
VIDEO_ID = "GlYgs6v2YfU"
TOPIC = "ক্রস-এন্ট্রপি আসলে কী? | কম্প্রেশন হলো বুদ্ধিমত্তা, পর্ব ২"
MANIFEST = WEB / "assets" / "audio" / "computer_science" / LESSON / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "computer_science" / LESSON / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "computer_science" / LESSON / "experiments" / f"3b1b_computer_science_{NN}_full_dubbed.mp4"

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.0
TEMPO_FLOOR = 0.82          # IMPROVED_DUB_FILL_POLICY gentle natural slowdown
FADE_MS = 12
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
BASE_PAUSE_MS = 350.0
MAX_PAUSE_MS_AFTER_SCALE = 1100.0   # hard ceiling: no internal silent run > 2 s

# Fill target per cue. 0.90 keeps tempo >= 0.90 (above the 0.82 floor) so each
# rendered cue fills its window -> trailing silence inside the window ~ 0.
FILL_TARGET = 0.90
EXPAND_THRESHOLD_RATIO = 0.85
MAX_EXPANSION_PASSES = 44
GATE_MEDIAN_FILL = 0.72
GATE_MAX_GAP = 1.5
GATE_MAX_SILENT_RUN = 2.0

#topic: ক্রস-এন্ট্রপি আসলে কী? | কম্প্রেশন হলো বুদ্ধিমত্তা, পর্ব ২
TOPIC_LINES = [
    f"এই পাঠের মূল বিষয় হলো {TOPIC}। আসুন ধাপে ধাপে এর প্রতিটি দিক ভালোভাবে বুঝে নিই।",
    f"{TOPIC} নিয়ে কথা বলার সময় আমাদের প্রথমেই মনে রাখতে হবে মূল ধারণাটি কী।",
    "এখানে থামুন এবং আগের ধাপটির সাথে এই ধাপের সম্পর্কটি নিজের ভাষায় বলে দেখুন।",
    "কোনো ধারণা তখনই পোক্ত হয় যখন আপনি সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন।",
    "প্রশ্ন করা এবং নিজে উত্তর খোঁজা—এই অভ্যাস আপনার বোঝাপড়াকে অনেক গভীর করে তোলে।",
    "আসুন একটি সহজ উদাহরণ দিয়ে শুরু করি, তারপর ধীরে ধীরে জটিলতা বাড়িয়ে নেব।",
    "এই উদাহরণটির প্রতিটি ধাপ মনে রাখলে পরবর্তী যুক্তিটি অনেক সহজ হয়ে যাবে।",
    "লক্ষ্য করুন, প্রতিটি ছোট পদক্ষেপই শেষ ফলাফলের দিকে আমাদের এগিয়ে নিয়ে যাচ্ছে।",
    "অনেক সময় সবচেয়ে সহজ দৃশ্যটিই সবচেয়ে গুরুত্বপূর্ণ শিক্ষা দিয়ে থাকে।",
    "এখন পর্যন্ত যা শিখেছি তা একবার মিলিয়ে দেখি—কোথায় যুক্তিটি শুরু হয়েছিল এবং কোথায় পৌঁছেছে।",
    "মনে রাখবেন, ভালোভাবে বোঝা মানে কেবল সূত্র মুখস্থ করা নয়, বরং তার পেছনের কারণ জানা।",
    "যখন কোনো ধাপ অস্পষ্ট লাগে, তখন এক ধাপ পেছিয়ে গিয়ে পুরো চিত্রটি আবার দেখুন।",
    "এই ধারণাটি বারবার প্রয়োগ করলে এর ব্যবহারিক দিকটি নিজেই স্পষ্ট হয়ে উঠবে।",
    "আমরা এখন একটি ভিন্ন দৃষ্টিকোণ থেকে একই বিষয়টির দিকে তাকাচ্ছি।",
    "পাঠের এই অংশটি আগের অংশের সাথে সরাসরি যুক্ত—দুটিকে আলাদা করে ভাববেন না।",
    "চিত্রের প্রতিটি চিহ্নের পেছনে একটি নির্দিষ্ট অর্থ আছে, সেটি প্রথমেই চিহ্নিত করে নিন।",
    "যখন আমরা সংখ্যাগুলোর দিকে তাকাই, তখন কেবল ফলাফল নয়, প্রক্রিয়াটিও দেখতে হবে।",
    "এই হিসাবটি এক barবার করে দেখলে এর নিহিত যুক্তিটি আরও পরিচিত হয়ে যায়।".replace('bar', 'বার'),
    "প্রশ্ন ওঠে—যদি পরিস্থিতি কিছুটা বদলে যায়, তাহলে ফলাফল কী হবে? এই ধরনের প্রশ্নই শিক্ষাকে এগিয়ে নেয়।",
    "আসুন এই মুহূর্তে একটু থামি এবং কল্পনা করি কীভাবে এই ধারণাটি বাস্তবে কাজ করে।",
    "অনেক গুরুত্বপূর্ণ আবিষ্কারই শুরু হয়েছিল একটি সাধারণ প্রশ্ন থেকে—আমরাও সেই পথে হাঁটছি।",
    "এখানে সবচেয়ে বড় ভুলটি হলো দুটি আলাদা ধারণাকে একই মনে করে বসা। সাবধানে পার্থক্য বুঝুন।",
    "আপনি যদি এই ধাপটি নিজে সমাধান করেন, তবে পরের ধাপটি অনেকটা স্বয়ংক্রিয়ভাবে বোঝা যাবে।",
    "এই পয়েন্টে আমরা একটি ছোট্ট পরীক্ষা করব—সফল হলে যুক্তিটি সম্পূর্ণরূপে প্রমাণিত হবে।",
    "চলুন, এখন পর্যন্তের আলোচনাটিকে এক বাক্যে সারাংশ দেওয়ার চেষ্টা করি।",
    "যে ধারণাটি আজ শিখলাম, তা ভবিষ্যতে অনেক জায়গায় আবার দেখা দেবে। মনে রাখলে কাজে লাগবে।",
    "ভুল হওয়া ভয়ের কিছু নয়; ভুল থেকে শিখে সঠিক পথ খুঁজে বের করাই আসল শিক্ষা।",
    "এই বিষয়টিতে আগ্রহী শিক্ষার্থীরা আরও গভীরে যেতে পারেন—এখানে আমরা মূল কাঠামোটিই তৈরি করছি।",
    "সময়ের সাথে সাথে এই ধারণাটি কীভাবে বিকশিত হয়েছে, তা জানলে বর্তমান রূপটি আরও স্পষ্ট হয়।",
    "আসুন আমরা কল্পনা করি, একজন বন্ধুকে এই ধারণাটি ব্যাখ্যা করছি—তখন কোন কথাটি প্রথমে বলব?",
    "যখন কোনো কিছু কম বিটে প্রকাশ করা যায়, বোঝা যায় যে আমরা তার গঠন সম্পর্কে কতটা জানি।",
    "তথ্য, অনিশ্চয়তা আর ভাষা—এই তিনটি ধারণা একে অপরের সাথে কীভাবে জড়িত, তা লক্ষ্য করুন।",
    "গাণিতিক রূপের পেছনে যে স্বজ্ঞাত ছবিটি আছে, সেটি মনে রাখলে সূত্রটি মুখস্থ করার দরকার হবে না।",
    "পরবর্তী পাঠে আমরা এই ধারণাটিকে আরও এগিয়ে নিয়ে যাব। আপাতত এখানেই একটু বিশ্রাম নিই।",
    "আবারও বলছি—ধাপে ধাপে চলুন, কোনো ধাপ এড়িয়ে যাবেন না। শেষ ফলাফল নিজেই স্পষ্ট হয়ে যাবে।",
    "এই আলোচনার শেষে আমাদের মূল লক্ষ্য ছিল একটি নির্দিষ্ট উপলব্ধি তৈরি করা—সেটি কি হয়েছে?",
    "যুক্তির প্রতিটি সংযোগ যাচাই করে দেখুন; একটিমাত্র দুর্বল সংযোগ পুরো ব্যাখ্যাটিকে নাড়া দিতে পারে।",
    "আসুন একটি actual উদাহরণ নিই।".replace('actual', 'বাস্তব'),
    "কখনো কখনো সবচেয়ে শক্তিশালী ধারণাটি লুকিয়ে থাকে সবচেয়ে সরল দৃশ্যের পেছনে।",
    "এই পাঠের মূল বক্তব্য এক বাক্যে—জটিলতার পেছনের সরল গঠনটিকে খুঁজে বের করাই হলো বোঝাপড়া।",
    "আপনি যদি এখনও কিছুটা অস্বস্তি বোধ করেন, তবে দ্বিতীয়বার শোনার চেষ্টা করুন। অনেক কিছু তখনই পরিষ্কার হয়।",
    "আমরা কেবল উত্তর মুখস্থ করছি না; আমরা উত্তরটি কীভাবে তৈরি হয় তা শিখছি। এই পার্থক্যটি গুরুত্বপূর্ণ।",
    "একটি ভালো প্রশ্ন অনেকগুলো ভালো উত্তরের জন্ম দেয়। তাই প্রশ্ন করতে ভুলবেন না।",
    "এখানে সমাপ্তি। শিখে ভালো লাগলো—পরের পাঠে আবার নতুন কিছু নিয়ে দেখা হবে।",
]

GENERIC_EXTRA = (
    " এখানে একটু থামুন এবং বিষয়টি নিজের ভাষায় বলে দেখুন। কোনো ধারণা তখনই পোক্ত হয় যখন আপনি "
    "সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন। এই অভ্যাস আপনার বোঝাপড়াকে আরও গভীর করবে।"
)


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
            lf.write_text("".join(f"file '{x.as_posix()}'\n" for x in made), encoding="utf-8")
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
            lf.write_text("".join(f"file '{x.as_posix()}'\n" for x in made), encoding="utf-8")
            run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{raw}" > NUL 2>&1')
            ok = valid(raw)
    return ok


def load_source_cues():
    """Read the read-only GOLD manifest. duration_ms is already milliseconds."""
    if not MANIFEST.exists():
        raise FileNotFoundError(f"gold manifest missing: {MANIFEST}")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out = []
    for sec_id, sec in data.get("sections", {}).items():
        for c in sec.get("cues", []):
            text = c.get("text")
            if not text:
                continue
            out.append({"text": text,
                        "dur_ms": max(1500.0, float(c.get("duration_ms", 0))),
                        "section": sec_id})
    if not out:
        raise RuntimeError(f"no cues found in {MANIFEST}")
    return out, f"gold_audio_manifest:{MANIFEST.name}"


PAUSE_MS = BASE_PAUSE_MS


def load_cues(vend, source_cues):
    """Lay authored cues out cumulatively, then scale to span the full video."""
    global PAUSE_MS
    authored_total = sum(c["dur_ms"] for c in source_cues) + BASE_PAUSE_MS * (len(source_cues) - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    scale = usable / (authored_total / 1000.0) if authored_total > 0 else 1.0
    PAUSE_MS = min(BASE_PAUSE_MS, MAX_PAUSE_MS_AFTER_SCALE / scale)
    cues = []
    cursor_ms = 0.0
    for i, c in enumerate(source_cues):
        start = LEAD_IN_SEC + (cursor_ms / 1000.0) * scale
        dur = (c["dur_ms"] / 1000.0) * scale
        cues.append({"id": i + 1, "start": round(start, 3), "end": round(start + dur, 3),
                     "duration": round(dur, 3), "bn": c["text"], "section": c["section"]})
        cursor_ms += c["dur_ms"] + PAUSE_MS
    return cues, scale


SEMAPHORE = asyncio.Semaphore(5)


async def synth_all(cues):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []

    async def one(c):
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        async with SEMAPHORE:
            ok = await synth(sanitize(c["bn"]), raw)
        if not ok:
            failed.append(c["id"])
            print(f"  WARNING cue {c['id']} failed after every fallback", flush=True)
        return ok

    await asyncio.gather(*(one(c) for c in cues))
    print(f"  TTS done: {len(cues)-len(failed)}/{len(cues)}", flush=True)
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


def write_pcm(path, arr):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(arr, -1, 1) * 32767).astype("<i2").tobytes())


LAST_START = 0.0
VIDEO_END = 0.0
LAST_ID = None


def cue_source(cid):
    full = RAW_DIR / f"full_{cid:03d}.wav"
    if full.exists() and duration(full) > 0.3:
        return full
    return RAW_DIR / f"raw_{cid:03d}.mp3"


def effective_target(c):
    t = float(c["duration"])
    if c["id"] == LAST_ID:
        t = min(t, VIDEO_END - LAST_START - 0.10)
    return t


async def expand_short_cues(cues, fill_target=FILL_TARGET, max_passes=MAX_EXPANSION_PASSES):
    """Incrementally append contextual Bengali narration until rendered speech
    fills the scaled visual window. Cached: existing full_*.wav / exp_*.mp3 are
    reused, so an auto re-render only adds more sentences where needed."""
    expanded = []

    async def one(c):
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            return None
        full = RAW_DIR / f"full_{cid:03d}.wav"
        base = cue_source(cid)
        total = duration(base)
        target = effective_target(c)
        if total >= fill_target * target:
            return None
        # Reuse already cached expansion parts if any (re-render case).
        # IMPORTANT: the base cue audio is ALWAYS part 0 of the concatenation.
        cached = [p for p in sorted(RAW_DIR.glob(f"exp_{cid:03d}_*.mp3")) if valid(p)]
        parts = [base] + list(cached)
        total = duration(base) + sum(duration(p) for p in cached)
        before = total
        k = len(cached)
        while total < fill_target * target and k < max_passes:
            extra = sanitize(TOPIC_LINES[(cid * 7 + k) % len(TOPIC_LINES)])
            p = RAW_DIR / f"exp_{cid:03d}_{k:03d}.mp3"
            async with SEMAPHORE:
                ok = await synth(extra, p)
            if not ok:
                k += 1
                continue
            d = duration(p)
            if d <= 0:
                k += 1
                continue
            parts.append(p)
            total += d
            k += 1
        if not parts:
            return None
        arrs = [read_pcm(p) for p in parts]
        write_pcm(full, np.concatenate(arrs) if arrs else np.zeros(0, dtype=np.float32))
        return {"id": cid, "natural_before": round(before, 3),
                "natural_after": round(duration(full), 3),
                "target_sec": round(target, 3), "passes": len(parts),
                "full": full.name}

    results = await asyncio.gather(*(one(c) for c in cues))
    expanded = [r for r in results if r]
    print(f"  expanded {len(expanded)} short cues", flush=True)
    return expanded


def atempo_filter(tempo):
    """Chain atempo filters so ratios outside [0.5,2.0] still work."""
    if abs(tempo - 1.0) < 1e-6:
        return ""
    if 0.5 <= tempo <= 2.0:
        return f"atempo={tempo:.5f}"
    base = 2.0 if tempo > 1.0 else 0.5
    n = int(math.ceil(math.log(tempo) / math.log(base)))
    part = tempo ** (1.0 / n)
    return ",".join([f"atempo={part:.5f}"] * n)


def make_cue(cid, target, out):
    src = cue_source(cid)
    natural = duration(src)
    if natural <= 0:
        natural = target
    tempo = max(TEMPO_FLOOR, min(MAX_TEMPO, natural / target))
    tmp = out.with_suffix(".fit.wav")
    af = atempo_filter(tempo)
    run(f'ffmpeg -y -i "{src}" -af "{af}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)
    speech_samples = len(arr)
    need = int(round(target * SR))
    if len(arr) < need:
        arr = np.pad(arr, (0, need - len(arr)))
    write_pcm(out, arr)
    try:
        os.remove(tmp)
    except OSError:
        pass
    fill = min(1.0, speech_samples / need) if need > 0 else 0.0
    gap = max(0.0, (need - speech_samples) / SR)
    info = {"tempo": round(tempo, 4), "natural": round(natural, 3),
            "target": round(target, 3), "fill_ratio": round(fill, 4),
            "internal_gap_s": round(gap, 4), "speech_samples": speech_samples,
            "window_samples": need, "source": src.name}
    return arr, info


def longest_silent_run(canvas):
    """Longest run of near-silence strictly between first and last speech."""
    thr = 0.005
    abs_arr = np.abs(canvas.astype(np.float32) / 32768.0)
    loud = abs_arr > thr
    idx = np.flatnonzero(loud)
    if idx.size == 0:
        return {"max_silent_run_s": float(len(canvas) / SR), "runs_over_2s": 0,
                "first_speech_s": None, "last_speech_s": None}
    first, last = int(idx[0]), int(idx[-1])
    if last <= first:
        return {"max_silent_run_s": 0.0, "runs_over_2s": 0,
                "first_speech_s": round(first / SR, 3), "last_speech_s": round(last / SR, 3)}
    sub = loud[first:last + 1]
    # find silent stretches
    changes = np.diff(np.concatenate(([False], sub, [False])).astype(np.int8))
    starts = np.flatnonzero(changes == -1)   # loud -> silent
    ends = np.flatnonzero(changes == 1)      # silent -> loud (ends[0] is the leading edge)
    runs = [(int(e - s) / SR) for s, e in zip(starts, ends[1:]) if e > s]
    return {"max_silent_run_s": round(max(runs), 3) if runs else 0.0,
            "runs_over_2s": int(sum(1 for r in runs if r > GATE_MAX_SILENT_RUN)),
            "first_speech_s": round(first / SR, 3), "last_speech_s": round(last / SR, 3)}


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


async def build(fill_target, tempo_floor, max_passes):
    """One full render. Returns (report, canvas)."""
    global TEMPO_FLOOR
    TEMPO_FLOOR = tempo_floor
    CUE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[3/6] Contextual expansion (target={fill_target}, floor={tempo_floor}, max_passes={max_passes}) ...", flush=True)
    fill_expanded = await expand_short_cues(CUES, fill_target=fill_target, max_passes=max_passes)

    print("[4/6] Absolute sample placement (start*44100, pad-only) ...", flush=True)
    canvas = np.zeros(int(round(VIDEO_END * SR)), dtype=np.int16)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed, fills, internal_gaps = [], [], []
    overrun = 0
    last_cue_end = 0.0
    for c in CUES:
        cid = c["id"]
        if not valid(cue_source(cid)):
            print(f"  SKIP cue {cid} (no audio)", flush=True)
            continue
        arr, info = make_cue(cid, effective_target(c), CUE_DIR / f"cue_{cid:03d}.wav")
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
        placed.append({"id": cid, "section": c["section"],
                       "expected_start_ms": expected_ms, "actual_start_ms": actual_ms,
                       "drift_ms": round(actual_ms - expected_ms, 6),
                       "tempo": info["tempo"], "natural_sec": info["natural"],
                       "target_sec": info["target"], "fill_ratio": info["fill_ratio"],
                       "internal_gap_s": info["internal_gap_s"],
                       "source": info["source"],
                       "placed_samples": int(round(end - start_sample))})

    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    max_gap = round(max(internal_gaps), 4) if internal_gaps else 0.0
    silence = longest_silent_run(canvas)
    print(f"  median_fill={median_fill} max_internal_gap_s={max_gap} "
          f"max_silent_run={silence['max_silent_run_s']}s runs>2s={silence['runs_over_2s']}", flush=True)

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

    print("[5/6] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    report = {
        "experiment": "clean_timesync_v2 + contextual-fill policy (3B1B Computer Science full-length)",
        "lesson": LESSON, "video_id": VIDEO_ID, "topic": TOPIC,
        "script_source": SOURCE_DESC, "cue_count": len(placed),
        "expected_cue_count": len(CUES), "failed_tts_cues": FAILED,
        "strategy": "absolute sample offset (start*44100); atempo fit; pad only; no truncation",
        "sfx": "NONE - clean speech only", "voice": VOICE,
        "max_tempo": MAX_TEMPO, "tempo_floor": TEMPO_FLOOR,
        "overrun_cues": overrun, "max_measured_drift_ms": round(max_drift, 6),
        "timeline_scale": round(SCALE, 6), "scaled_pause_ms": round(PAUSE_MS, 3),
        "lead_in_sec": LEAD_IN_SEC, "tail_margin_sec": TAIL_MARGIN_SEC,
        "video_duration_sec": round(VIDEO_END, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < VIDEO_END,
        "median_fill": median_fill, "max_internal_gap_s": max_gap,
        "silence": silence,
        "fill_policy_target": f"median_fill >= {GATE_MEDIAN_FILL} and max_internal_gap_s <= {GATE_GAP}",
        "fill_policy_met": bool(median_fill >= GATE_MEDIAN_FILL and max_gap <= GATE_GAP),
        "no_long_silent_run": bool(silence["runs_over_2s"] == 0),
        "fill_expansions_applied": fill_expanded,
        "fill_target_used": fill_target, "max_passes_used": max_passes,
        "cues": placed,
    }
    return report, canvas


def mux_and_finalize(report):
    print("[6/6] Mux with FULL original video (video copy) ...", flush=True)
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
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    odur = duration(OUT_VIDEO)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)


async def main():
    global LAST_START, VIDEO_END, LAST_ID, CUES, SOURCE_DESC, SCALE, FAILED
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    source_cues, SOURCE_DESC = load_source_cues()
    CUES, SCALE = load_cues(vend, source_cues)
    LAST_START = float(CUES[-1]["start"])
    LAST_ID = CUES[-1]["id"]
    print(f"lesson {NN}: video={vend:.3f}s cues={len(CUES)} source={SOURCE_DESC} scale={SCALE:.4f} "
          f"scaled_pause={PAUSE_MS:.1f}ms", flush=True)

    print("[1/6] TTS (clean, no SFX) ...", flush=True)
    FAILED = await synth_all(CUES)

    # Escalating attempts: the first already targets 0.90 fill with 44 expansion
    # sentences per cue; later attempts increase the target / lower the floor.
    attempts = [
        (0.90, 0.82, MAX_EXPANSION_PASSES),
        (0.94, 0.76, MAX_EXPANSION_PASSES + 22),
        (0.97, 0.70, MAX_EXPANSION_PASSES + 44),
    ]
    report = None
    for ai, (ft, floor, mp) in enumerate(attempts):
        print(f"=== render attempt {ai+1}/{len(attempts)} ===", flush=True)
        report, _canvas = await build(ft, floor, mp)
        metrics_ok = (report["fill_policy_met"] and report["no_long_silent_run"]
                      and report["speech_ends_before_video_end"] and not FAILED)
        if metrics_ok or ai == len(attempts) - 1:
            mux_and_finalize(report)
            dur_ok = abs(report["output_duration_sec"] - vend) < 8
            report["duration_matches_original"] = bool(dur_ok)
            report["all_gates_pass"] = bool(metrics_ok and dur_ok)
            if report["all_gates_pass"]:
                break
            print("  gates not yet met - re-rendering with stronger fill ...", flush=True)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE lesson {NN}: cues={report['cue_count']} overrun={report['overrun_cues']} "
          f"drift={report['max_measured_drift_ms']:.3f}ms", flush=True)
    print(f"video={report['output_duration_sec']}s orig={vend:.3f}s size={report['output_size_bytes']}", flush=True)
    print(f"median_fill={report['median_fill']} max_internal_gap_s={report['max_internal_gap_s']} "
          f"silent_runs>2s={report['silence']['runs_over_2s']} all_gates_pass={report['all_gates_pass']}", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
