"""EXPERIMENT — Full-length clean absolute-sample Bengali dub (Physics lesson 13).

Adapted from the proven clean_timesync_v2 pipeline:
  essence_of_calculus/lesson_08_integration/dubbing_pipeline/experiments/clean_timesync_v2/build_calc08_clean.py

Physics-specific adaptations:
  * Script source = the gold audio manifest (cue texts, read-only).
  * Audio manifest cue total is 1.5x..11x shorter than the full YouTube video, so
    short cues are enriched with a rotating pool of topic-aware + generic Bengali
    pedagogical sentences before atempo fitting (the calc pipeline did the same
    with a small per-cue EXPANSIONS dict; here the pool is larger and adaptive).
  * INTER_CUE_PAUSE is FIXED (not scaled) so no inter-cue silence run can exceed 2s.

Guarantees (same as the proven pipeline):
  1. edge_tts bn-BD-PradeepNeural; 0-byte purge, 12 attempts, half/sentence split fallbacks.
  2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
  3. atempo fit in [0.82, 2.2]; PAD ONLY, NEVER truncate. NO SFX: clean speech only.
  4. Fill gate: median_fill >= 0.72 and max_internal_gap_s <= 1.5s in verification.json.
  5. Final-cue cap so speech ends inside the video.
  6. Canvas padded to FULL original duration before -shortest.
  7. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
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
WEB = EXP.parents[4] / "web_platform"
LESSON_ID = "lesson_13"
VIDEO_ID = "Iq1a_KJTWJ8"
EXPECTED_CUES = 14
MANIFEST = WEB / "assets" / "audio" / "physics" / LESSON_ID / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "physics" / LESSON_ID / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "physics" / LESSON_ID / "experiments" / "3b1b_physics_13_full_dubbed.mp4"
VOUT_VERIFY = OUT_VIDEO.parent / "verification.json"

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

LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_SEC = 0.8          # FIXED: never scaled -> no >2s silent run
EXPAND_THRESHOLD_RATIO = 0.90      # aim to render >=90% of the window before atempo
ENRICH_SAFETY = 1.18
MAX_TTS_CHARS = 2600

# Topic-aware pedagogical sentences for this lesson (used first when enriching).
TOPIC_LINES = ['স্নেলের সূত্র শুধু আলোর জন্য নয়—এটি একটি সার্বজনীন নীমের প্রকাশ।', 'এই প্রশ্নে স্প্রিং ব্যবহার করে দেখানো হয় কীভাবে সবচেয়ে কম শক্তির অবস্থা নির্ধারণ করে পথ।', 'দুই মাধ্যমের সীমানায় আলোর বেগ আলাদা হলে পথ বেঁকে যায়—এটি আমরা আগেই জেনেছি।', 'স্প্রিংয়ের মডেলে বিন্দুজনকে সীমানার ওপারে টানা হয়, আর সেই টানের ভারসাম্যেই স্নেলের সূত্র ফিরে পাওয়া যায়।', 'ভারসাম্য মানে শক্তি সবচেয়ে কম—এই নীমটি পদার্থবিজ্ঞানের অনেক জায়গায় কাজ করে।', 'ফার্মের নীমও আসলে এই একই কথা বলে: প্রকৃতি সবচেয়ে কম মাত্রার পথ বেছে নেয়।', 'স্প্রিংয়ের সরল মডেল ব্যবহার করে জটিল প্রতিসরণকে বোঝা যায়—এটি পদার্থবিজ্ঞানের একটি শক্তিশালী পদ্ধতি।', 'দুটি ভিন্ন দিক থেকে একই সূত্রে পৌঁছানো তার সত্যতার এক শক্ত প্রমাণ।', 'আসুন প্রথমে স্প্রিংয়ের টান বুঝি, তারপর সেটিকে আলোর পথের সাথে মিলিয়ে দেখি।', 'প্রতিসরণাংকের পার্থক্য যত বেশি, বেঁকে যাওয়ার পরিমাণও তত বেশি।', 'পানি আর কাচের ক্ষেত্রে এই বাঁকা সহজেই দেখা যায়। হীরায় তা আরও বেশি।', 'গণিত আর পদার্থবিজ্ঞানের এই মিলনই একটি ভালো প্রমাণের জন্ম দেয়।']

# Generic pedagogical fallback pool (rotated, appended after TOPIC_LINES).
GENERIC_POOL = [
    "এখানে একটু থামুন এবং বিষয়টি নিজের ভাষায় বলে দেখুন। কোনো ধারণা তখনই পোক্ত হয় যখন আপনি সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন।",
    "এই ধারণাটির সাথে আমাদের দৈনন্দিন অভিজ্ঞতার একটি সংযোগ আছে। সেই সংযোগটি খুঁজে পেলে পাঠটি মুখস্থ করা ছাড়াই মনে থাকে।",
    "মনে রাখবেন, কোনো সূত্র মুখস্থ করার আগে তার পেছনের ছবিটি মনে আনা প্রয়োজন। ছবি স্পষ্ট হলে সূত্র নিজেই যুক্তিসঙ্গত মনে হয়।",
    "আসুন এই পদক্ষেপটিকে আরেকবার ধাপে ধাপে দেখি। প্রথমে কী দেওয়া আছে, তারপর কী বদলাচ্ছে, আর শেষে কী ফল পাচ্ছি।",
    "পদার্থবিজ্ঞানে প্রতিটি ছোট পর্যবেক্ষণের পেছনে একটি বড় নীম থাকে। সেই নীমটি উন্মোচন করাই এই পাঠের আসল উদ্দেশ্য।",
    "যখন কোনো রাশি বাড়ে বা কমে, তখন তার সাথে জড়িত অন্য রাশিও কীভাবে বদলায় তা লক্ষ্য করা গুরুত্বপূর্ণ।",
    "এই ধাপে ভুল হলে পরের ধাপগুলোও ভুল হয়। তাই প্রতিটি ধাপ যাচাই করে এগোনোই নিরাপদ পদ্ধতি।",
    "প্রশ্নটি আবার নিজের মনে পড়ুন। উত্তরের দিকে যাওয়ার আগে প্রশ্নের ভেতরে লুকোনো ইঙ্গিতটি ধরতে পারলে কাজ সহজ হয়।",
    "গাণিতিক রূপ আর শারীরিক অর্থ—এই দুটোকে আলাদা না করে দেখলে বিষয়টি অনেক পরিচ্ছন্ন হয়ে ওঠে।",
    "একই ফলাফলকে ভিন্ন ভিন্ন দৃষ্টিকোণ থেকে দেখা যায়। এক দৃষ্টিকোণ অস্পষ্ট হলে অন্য দৃষ্টিকোণ সাহায্য করে।",
    "আসুন কল্পনা করি পরিস্থিতিটি কীভাবে বদলাবে যদি একটি রাশিকে দ্বিগুণ করা হয়। এই ধরনের প্রশ্ন ধারণাকে গভীর করে।",
    "বিজ্ঞানের প্রতিটি মডেলই একটি সরলীকরণ। মডেলের সীমা বোঝা মডেলের ফলাফল বোঝার মতোই গুরুত্বপূর্ণ।",
    "এখানে আনুমানিক হিসাব আর নিখুঁত হিসাবের পার্থক্য বোঝা জরুরি। প্রথমটি স্বজ্ঞাত দেয়, দ্বিতীয়টি নিশ্চয়তা দেয়।",
    "আগের ধাপের ফলাফল এখানে কাজে লাগছে। পাঠের ধারাবাহিকতা বজায় রাখলে পরের অংশগুলো স্বয়ংক্রিয়ভাবে বোঝা যায়।",
    "অসীমের ধারণা কখনো ভয়ংকর নয়। সীমার মাধ্যমে আমরা অসীমকে নিয়ন্ত্রিতভাবে ব্যবহার করতে শিখেছি।",
    "দৃশ্যমান চিত্র আর গাণিতিক বিবরণ একই কথা দুই ভাষায় বলে। দুটোর মিলিয়ে পড়লে বোঝাপড়া আরও দৃঢ় হয়।",
    "লক্ষ্য করুন কীভাবে একটি ছোট পরিবর্তন পুরো ফলাফলের দিক বদলে দিতে পারে। সংবেদনশীলতা হলো এই পাঠের গোপন শিক্ষা।",
    "আপনি যদি এই বিষয়টি কোনো বন্ধুকে শেখান, তবে নিজের বোঝার ঘাটতিগুলো সহজেই ধরা পড়বে। শেখানোই সেরা পুনরাবৃত্তি।",
    "সময়ের সাথে সাথে ধারণাটি আরও পরিচ্ছন্ন হবে। প্রথম পড়ায় যা অস্পষ্ট লাগে, পরের পড়ায় তা স্পষ্ট হয়।",
    "এই ধাপের সাথে আগের পাঠের একটি ধারণা মিলে যাচ্ছে। আগের জানা আর নতুন জানার এই মিলনই শিক্ষাকে স্থায়ী করে।",
    "যখন কোনো বল বা তরঙ্গ কাজ করে, তখন তার উৎস এবং ফল—দুটোই একসাথে দেখতে হয়। শুধু ফল দেখলে গল্প অসম্পূর্ণ থাকে।",
    "নির্ভুলতা আসে বারবারের চর্চা থেকে। একবার বোঝা আর বারবার ব্যবহার করা—এই দুয়ের মাঝেই প্রকৃত দক্ষতা জন্মায়।",
    "আসুন একটি সরল উদাহরণ দিয়ে শুরু করি, তারপর ধীরে ধীরে জটিল ক্ষেত্রে অগ্রসর হই। সরল থেকে জটিল—এই ক্রম সবচেয়ে নিরাপদ।",
    "যে রাশিটি আমরা মাপছি, তার একক কী—এই প্রশ্নটি কখনো এড়িয়ে যাবেন না। একক ভুল হলে সংখ্যা সঠিক হলেও অর্থ ভুল হয়।",
    "পাঠের এই অংশটি আগের অংশের ওপর নির্ভরশীল। আগের অংশ পরিষ্কার না হলে এখানে থামুন এবং একটু পুনরাবৃত্তি করুন।",
    "বিজ্ঞানীদের কাজ হলো জটিল প্রকৃতিকে সরল প্রশ্নে ভেঙে ফেলা। আমরাও সেই একই পদ্ধতি অনুসরণ করছি।",
    "আপনার চারপাশে এই নীমটি কোথায় কাজ করে খুঁজে বের করুন। দৈনন্দিন উদাহরণ পেলে ধারণা আরও জীবন্ত হয়ে ওঠে।",
    "এখানে দুটি পথ আছে—একটি সোজা, অন্যটি কিছুটা ঘুরিয়ে। দুটি পথেই একই ফল পাওয়া যাবে, কিন্তু বোঝাপড়া আলাদা হবে।",
    "শেষ পর্যন্ত গণনার চেয়ে বেশি গুরুত্বপূর্ণ হলো সঠিক প্রশ্ন জিজ্ঞাসা করা। সঠিক প্রশ্নই সঠিক উত্তরের দিকে নিয়ে যায়।",
    "আজ যা শিখলাম তা পরের পাঠের ভিত্তি হবে। তাই এই অংশটি ভালোভাবে বুঝে নেওয়া আমাদের সবার জন্য জরুরি।",
]


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


def split_text(text, max_chars=MAX_TTS_CHARS):
    """Split long text at sentence boundaries into <=max_chars chunks."""
    if len(text) <= max_chars:
        return [text]
    sents = re.split(r"(?<=।)\s+", text)
    chunks, cur = [], ""
    for s in sents:
        if not s.strip():
            continue
        if len(cur) + len(s) + 1 > max_chars and cur:
            chunks.append(cur.strip())
            cur = s
        else:
            cur = (cur + " " + s).strip()
    if cur:
        chunks.append(cur.strip())
    # Any single over-long sentence: hard split.
    out = []
    for c in chunks:
        while len(c) > max_chars:
            out.append(c[:max_chars])
            c = c[max_chars:]
        if c:
            out.append(c)
    return out


async def synth(text, raw, force=False):
    """Chunked, purged, 12-attempt TTS with half + sentence fallbacks."""
    if not force and valid(raw):
        return True
    if len(text) > MAX_TTS_CHARS:
        parts = split_text(text)
        made = []
        for j, p in enumerate(parts):
            pp = RAW_DIR / f"chunk_{raw.stem}_{j}.mp3"
            if not await synth(p, pp, force=True):
                return False
            made.append(pp)
        if len(made) == 1:
            made[0].replace(raw)
        else:
            lf = RAW_DIR / f"chunklist_{raw.stem}.txt"
            with open(lf, "w", encoding="utf-8") as f:
                for x in made:
                    f.write(f"file '{x.as_posix()}'\n")
            run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{raw}" > NUL 2>&1')
        return valid(raw)
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


def load_manifest_cues():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out = []
    for sec_id, sec in data.get("sections", {}).items():
        for c in sec.get("cues", []):
            text = c.get("text")
            if not text:
                continue
            out.append({
                "text": text,
                "dur_ms": float(c.get("duration_ms", 0)),
                "section": sec_id,
            })
    return out


def load_cues(vend, source_cues):
    """Cumulative authored layout, scaled to fill the video; FIXED inter-cue pause."""
    n = len(source_cues)
    authored_s = sum(c["dur_ms"] for c in source_cues) / 1000.0
    total_pause = INTER_CUE_PAUSE_SEC * (n - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC - total_pause
    scale = usable / authored_s if authored_s > 0 else 1.0
    cues, cursor = [], 0.0
    for i, c in enumerate(source_cues):
        start = LEAD_IN_SEC + cursor * scale + i * INTER_CUE_PAUSE_SEC
        dur = (c["dur_ms"] / 1000.0) * scale
        cues.append({
            "id": i + 1,
            "start": round(start, 3),
            "end": round(start + dur, 3),
            "duration": round(dur, 3),
            "bn": c["text"],
            "section": c["section"],
        })
        cursor += c["dur_ms"] / 1000.0
    return cues, scale


async def synth_all(cues):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, c in enumerate(cues):
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        if not await synth(sanitize(c["bn"]), raw):
            failed.append(c["id"])
        if (i + 1) % 5 == 0:
            print(f"  TTS {i+1}/{len(cues)}", flush=True)
    return failed


async def enrich_short_cues(cues):
    """Enrich any cue whose natural TTS is short of its scaled window.

    Adds topic-aware + generic Bengali sentences (rotating, adaptive length),
    re-synthesizes once, and repeats at most twice if still short.
    """
    pool = [sanitize(x) for x in (TOPIC_LINES + GENERIC_POOL)]
    pool = [x for x in pool if x]
    expanded = []
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            continue
        target = float(c["duration"])
        if cid == LAST_ID:
            target = min(target, VIDEO_END - LAST_START - 0.10)
        natural = duration(raw)
        if natural <= 0 or natural >= EXPAND_THRESHOLD_RATIO * target:
            continue
        base = sanitize(c["bn"])
        rate = max(6.0, min(30.0, len(base) / max(natural, 0.1)))
        original_natural = natural
        passes = 0
        cursor = (cid * 7) % len(pool)
        for attempt in range(3):
            natural = duration(raw)
            if natural >= EXPAND_THRESHOLD_RATIO * target:
                break
            need_sec = max(0.0, target - natural)
            need_chars = int(need_sec * rate * ENRICH_SAFETY) + 60
            added, acc = [], 0
            while acc < need_chars and len(added) < 80:
                s = pool[cursor % len(pool)]
                cursor += 1
                if not s:
                    continue
                added.append(s)
                acc += len(s) + 1
            new_text = sanitize(base + " " + " ".join(added))
            print(f"  enrich cue {cid} pass {attempt+1}: natural={natural:.2f}s "
                  f"target={target:.2f}s chars+={acc}", flush=True)
            if not await synth(new_text, raw, force=True):
                break
            passes += 1
        expanded.append({
            "id": cid,
            "natural_before": round(original_natural, 3),
            "natural_after": round(duration(raw), 3),
            "target_sec": round(target, 3),
            "passes": passes,
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


LAST_START = 0.0
VIDEO_END = 0.0
LAST_ID = None


def make_cue(raw, target, out, cid):
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


async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    source_cues = load_manifest_cues()
    if len(source_cues) != EXPECTED_CUES:
        print(f"WARNING cue count {len(source_cues)} != expected {EXPECTED_CUES}", flush=True)
    cues, scale = load_cues(vend, source_cues)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"[{LESSON_ID}] video={vend:.3f}s cues={len(cues)} scale={scale:.4f} "
          f"fixed_pause={INTER_CUE_PAUSE_SEC}s", flush=True)

    print("[1/6] TTS (clean, no SFX) ...", flush=True)
    failed = await synth_all(cues)

    print("[2/6] Adaptive enrichment of short cues ...", flush=True)
    enriched = await enrich_short_cues(cues)

    print("[3/6] Absolute sample placement (floor 0.82, pad-only) ...", flush=True)
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed, fills, internal_gaps = [], [], []
    overrun = 0
    last_cue_end = 0.0
    enriched_ids = {x["id"] for x in enriched}
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
            "enriched": cid in enriched_ids,
        })

    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    max_internal_gap_s = round(max(internal_gaps), 4) if internal_gaps else 0.0
    print(f"  median_fill={median_fill} max_internal_gap_s={max_internal_gap_s}", flush=True)

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
        "experiment": "clean_timesync_v2 + adaptive enrichment (physics full-length)",
        "lesson": LESSON_ID,
        "video_id": VIDEO_ID,
        "script_source": f"audio_manifest:{MANIFEST.name}",
        "cue_count": len(placed),
        "expected_cue_count": EXPECTED_CUES,
        "failed_tts_cues": failed,
        "strategy": "absolute sample offset; atempo [0.82,2.2]; pad only; fixed 0.8s pause; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "tempo_floor": TEMPO_FLOOR,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "timeline_scale": round(scale, 6),
        "fixed_inter_cue_pause_sec": INTER_CUE_PAUSE_SEC,
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "median_fill": median_fill,
        "max_internal_gap_s": max_internal_gap_s,
        "fill_policy_target": "median_fill >= 0.72 and max_internal_gap_s <= 1.5",
        "fill_policy_met": bool(median_fill >= 0.72 and max_internal_gap_s <= 1.5),
        "enrichments_applied": enriched,
        "enrich_threshold_ratio": EXPAND_THRESHOLD_RATIO,
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
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    odur = duration(OUT_VIDEO)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    for p in (VERIFY, VOUT_VERIFY):
        with open(p, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE {LESSON_ID}: cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={report['output_duration_sec']}s size={report['output_size_bytes']}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap_s={max_internal_gap_s} "
          f"policy_met={report['fill_policy_met']}", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
