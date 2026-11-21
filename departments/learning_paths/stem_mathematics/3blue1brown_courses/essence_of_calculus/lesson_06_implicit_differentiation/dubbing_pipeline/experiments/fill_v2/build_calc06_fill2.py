"""
EXPERIMENT -- Full-length, gap-filled Bengali dub (Essence of Calculus, Lesson 06)
==================================================================================
Copied from the quality-gated clean_timesync_v2 pipeline (build_calc08_clean.py)
with these Lesson-06 / fill_v2 adaptations:

  * Script source: the audio manifest cues only (26 cues, alias-deduped).
    Teacher audio, manifests, master scripts and other lessons are NEVER touched.
  * HEAVY expansion: the 26 rendered cues total only ~505 s while the original
    video is ~933 s. A slowdown alone (atempo floor 0.82 -> <=1.22x) cannot fill
    the timeline, so every cue's Bengali narration is heavily expanded with
    contextual pedagogical sentences until its rendered speech covers its
    proportional share of the usable timeline.
  * Scale is RECOMPUTED FROM RENDERED SPEECH: after expansion, the layout windows
    are derived from the final measured TTS durations (sum(natural)+pauses scaled
    to span the full video), so atempo ~= 1.0 and fill ~= 1.0 by construction.
  * FILL GATE: median_fill >= 0.72 and max_internal_gap_s <= 1.5 (recorded into
    verification.json). Also checks silencedetect internal runs > 2 s == 0.

Guarantees inherited from the proven pipeline:
  1. edge_tts bn-BD-PradeepNeural; robust retries (0-byte purge, 12 attempts,
     half-split + sentence-split fallbacks, dedicated WinError 1450 retry).
  2. Absolute sample placement start*44100 -> ZERO cumulative drift.
  3. atempo fit in [0.82, 2.2]; PAD ONLY, NEVER truncate. NO SFX: clean speech.
  4. Canvas padded to the FULL original video duration so -shortest cannot trim.
  5. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
  6. The ORIGINAL VIDEO SRC IS NEVER SWAPPED. Old video stays as backup.
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
# Locate the 3blue1brown_courses root robustly.
_p = EXP
while _p.name != "3blue1brown_courses" and _p != _p.parent:
    _p = _p.parent
ROOT = _p
WEB = ROOT / "web_platform"

MANIFEST = WEB / "assets" / "audio" / "calculus" / "lesson_06" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "calculus" / "lesson_06" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "calculus" / "lesson_06" / "experiments" / "fill_v2" / "3b1b_calculus_06_full_dubbed_fill2.mp4"

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
LESSON = "lesson_06_implicit_differentiation"
VIDEO_ID = "full_original"

# Keep short lead-in / tail silent; inter-cue pause stays well under 2 s.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Heavy expansion stops when a cue's rendered speech reaches this fraction of
# its proportional target window (leave a hair of headroom, never cut).
EXPAND_REACH = 0.995
MAX_EXPAND_PASSES = 10

# Large, varied pool of contextual Bengali pedagogical sentences used to expand
# each cue heavily. Clean punctuation only (sanitize() strips the rest).
EXPANSION_POOL = [
    " এখানে একটু থামলে ভালো হয়। আসুন দেখি এই ধাপটির পেছনের ধারণা কী। প্রতিটি ছোট পরিবর্তন কীভাবে পুরো সমীকরণটিকে প্রভাবিত করে, সেটি মনে রাখা জরুরি। ক্যালকুলাসের আসল শক্তি এই সূক্ষ্ম সম্পর্কগুলোকে ধরা।",
    " মনে রাখবেন, কেবল সূত্র মুখস্থ করলে কাজ চলবে না। চিত্রের দিকে তাকিয়ে কল্পনা করুন বিন্দুটি যখন বক্ররেখা বরাবর এগিয়ে যাচ্ছে, তখন তার উচ্চতা আর অবস্থানের সম্পর্ক অপরিবর্তিত থাকে। এই উপলব্ধিই পরবর্তী ধাপের ভিত্তি তৈরি করে।",
    " একই ধারণাটিকে অন্য ভাঙায় বলা যায়। যখন আমরা এক্সের সাপেক্ষে অবকলন করি, তখন ধরে নিই ওয়াই এক্সের উপর নির্ভরশীল। কিন্তু প্রচ্ছন্ন রূপে এই নির্ভরতা সরাসরি লেখা থাকে না। তবুও শৃঙ্খল নিয়ম প্রয়োগ করে সঠিক উত্তর পাওয়া যায়।",
    " আসুন একটি সাধারণ উদাহরণ দিয়ে বিষয়টি পরীক্ষা করে দেখি। বৃত্তের সমীকরণ নিলে দেখা যায়, ব্যাসার্ধ আর বিন্দুর অবস্থানের মধ্যে একটা টানাপোড়েন চলে। স্পর্শক আর ব্যাসার্ধ পরস্পর লম্ব—এই সরল তথ্যটি থেকে পুরো গাণিতিক কাঠামোটি জন্ম নেয়।",
    " যারা প্রথমবার এই ধারণার মুখোমুখি হচ্ছেন, তাদের জন্য একটা পরামর্শ। ভুল করা স্বাভাবিক। ভুলের কারণ খুঁজে বের করে আবার চেষ্টা করুন। প্রতি বার প্রয়োগ করার সাথে সাথে ধারণাটি মনে গেঁথে যাবে।",
    " এখন প্রশ্ন হতে পারে, কেন আমরা ডি ওয়াই বাই ডি এক্স লিখি? এর অর্থ হলো ওয়াইয়ের সূক্ষ্ম পরিবর্তন আর এক্সের সূক্ষ্ম পরিবর্তনের অনুপাত। বক্ররেখার যেকোনো বিন্দুতে এই অনুপাতই ঢাল বা স্লোপ নির্ধারণ করে। এটি পুরো অধ্যায়ের কেন্দ্রীয় ভাবনা।",
    " চিত্রের সবুজ আর কমলা রেখার দিকে লক্ষ্য করুন। একটির ঢাল অন্যটির ঢালের ঋণাত্মক বিপরীত। এই লম্বতার সম্পর্ক কেবল বৃত্তের ক্ষেত্রেই নয়, বরং অনেক বক্ররেখার ক্ষেত্রে প্রযোজ্য। জ্যামিতি আর বীজগণিত এখানে হাত মিলিয়ে কাজ করে।",
    " পাঠকেরা অনেকেই ভেবে বসেন সমীকরণ মানেই শুধু এক্স আর ওয়াইয়ের যোগফল। কিন্তু আসলে এটি এক ধরনের নিয়ম, এক ধরনের ভারসাম্য। বামপক্ষ আর ডানপক্ষ সবসময় সমান। আমরা যখন কিছু যোগ বা গুণ করি, তখন এই ভারসাম্য অটুট রাখতে হয়।",
    " এই ধাপে কোনো নতুন সূত্র আবিষ্কার হচ্ছে না। আগের পাঠে শেখা শৃঙ্খল নিয়মকেই একটা নতুন পরিস্থিতিতে প্রয়োগ করা হচ্ছে। ক্যালকুলাস শেখার সবচেয়ে কার্যকর উপায় হলো পুরনো ধারণাকে নতুন করে ব্যবহার করা।",
    " কল্পনা করুন আপনি রাতের অন্ধকারে একটি বৃত্তের চারপাশে হাঁটছেন। প্রতি মুহূর্তে আপনার দূরত্ব কেন্দ্র থেকে অপরিবর্তিত। তবুও আপনার দিক বদলাচ্ছে। এই দিক বদলানোর হারই মূলত অবকলন। গতি আর অবস্থানের এই খেলা বোঝা গেলে বাকিটা সহজ।",
    " আসুন এই ফলাফলটি একবার নিজের ভাষায় বলে দেখি। যদি কোনো বিন্দু বক্ররেখার ওপর থাকে, তবে তার স্লোপ নির্ভর করবে এক্স আর ওয়াই দুটোরই ওপর। শুধু একটির ওপর নয়। এই দ্বৈত নির্ভরতা প্রচ্ছন্ন অবকলনের বৈশিষ্ট্য।",
    " শিক্ষার্থীরা প্রায়ই জিজ্ঞেস করেন, কখন প্রচ্ছন্ন পদ্ধতি ব্যবহার করবেন? উত্তর সহজ—যখন ওয়াইকে এক্সের সাপেক্ষে সরাসরি লেখা কঠিন বা অসম্ভব। তখন সমীকরণ যেমন আছে তেমনি রেখে উভয় পক্ষে অবকলন করুন। কাজ হয়ে যাবে।",
    " সূত্রটি লিখে রাখা যাক। দুই এক্স ডি এক্স প্লাস দুই ওয়াই ডি ওয়াই সমান শূন্য। এই সরল রূপটি থেকে ডি ওয়াই বাই ডি এক্স বের করা যায়। প্রথমে পদগুলো সাজান, তারপর ভাগ করুন। ছোট ছোট ধাপে ভাঙলেই বড় সমস্যাও সহজ হয়।",
    " আরেকটি দিক থেকে চিন্তা করুন। বৃত্তের ওপর আমরা এক ধাপ এগোলাম। এক্স বাড়ল, ওয়াই কমল। কিন্তু ব্যাসার্ধের বর্গ অপরিবর্তিত রইল। এই অপরিবর্তনীয়তা থেকেই ডিফারেনশিয়াল ভারসাম্য জন্ম নেয়। এটি কেবল গণিত নয়, এক ধরনের ভারসাম্যের দর্শন।",
    " মইয়ের উদাহরণে ফিরে আসি। মিটারের এই মইটি দেয়ালের সাথে হেলান দিয়ে আছে। নিচের প্রান্ত সরে যাচ্ছে, ওপরের প্রান্ত নামছে। দুটো গতি আলাদা হলেও আলাদা নয়—একটি সমীকরণ দুটোকেই বেঁধে রেখেছে।",
    " যখন মইয়ের ওপরের প্রান্ত মেঝের দিকে নামতে থাকে, তখন শেষ মুহূর্তে গতি শূন্য হয়। কিন্তু আমাদের সূত্র বলে কিছু একটা অসীমের দিকে যাচ্ছে। এই বিরোধ নিয়ে ভাবা উচিত। গাণিতিক মডেলের সীমা বোঝাও বিজ্ঞানের অংশ।",
    " পাঠের শেষে একবার মনে পড়ে যাক—আমরা কী শিখলাম? সমীকরণকে ভীতি না দেখে তার গতিপ্রকৃতি দেখতে শিখলাম। নিয়ম প্রয়োগ করলাম, ভুল সংশোধন করলাম, আর নতুন করে ভাবলাম। এই চক্রটাই আসল শিক্ষা।",
    " আপনি যদি এখনই সবকিছু বুঝতে না পারেন, তাতে কিছু যায় আসে না। কয়েকবার শুনুন, চিত্রের সাথে মিলিয়ে দেখুন, নিজে হাতে হিসাব করে দেখুন। ধীরে ধীরে অস্পষ্টতা দূর হয়ে যাবে। ধৈর্য আসলে ক্যালকুলাসের একটা অঙ্গ।",
    " সহকর্মী বা বন্ধুর সাথে এই ধারণা নিয়ে আলোচনা করুন। কাউকে বুঝিয়ে বলার চেষ্টা করুন। যেটা নিজে বুঝেছি মনে হয়, আসলে সেটা অন্যকে বুঝিয়ে বলার সময়ই পরিপক্ক হয়। শেখার এই পদ্ধতি খুবই ফলপ্রসূ।",
    " আমাদের এই যাত্রায় জ্যামিতি আর বীজগণিত বারবার মিলিত হয়েছে। বৃত্তের চিত্র আমাদের বলে দিয়েছে কোন দিকে তাকাতে হবে, আর বীজগণিত সেই দিকের হিসাব দিয়েছে। দুটো একসাথে থাকলে ক্যালকুলাস আর কঠিন থাকে না।",
    " একটু এগিয়ে চলুন। পরবর্তী পাঠে আমরা দেখব এই একই ধারণা কীভাবে সম্পর্কিত পরিবর্তনের হার নামক বৃহত্তর ক্ষেত্রে প্রয়োগ হয়। আজকের ভিত্তি শক্ত হলে আগামীকালের যাত্রা সহজ হবে।",
    " শেষ করার আগে একটা ছোট্ট পরীক্ষা। কাগজে একটি বৃত্ত আঁকুন, একটি বিন্দু নিন, আর স্পর্শক আঁকুন। তারপর আমাদের সূত্রটি প্রয়োগ করে দেখুন স্লোপ কী আসে। হাতে করা এই অনুশীলন মনে দীর্ঘস্থায়ী হয়।",
    " মনে রাখবেন, প্রতিটি বড় আবিষ্কারের পেছনে থাকে ছোট ছোট প্রশ্ন। কেন এই পদ এসেছে? কেন এই চিহ্ন বদলাল? এই ধরনের প্রশ্নই গণিতক এগিয়ে নিয়ে যায়। আপনিও প্রশ্ন করতে ভুলবেন না।",
    " আজকে আমরা দেখলাম একটি সরল বৃত্তের সমীকরণ থেকে কত গভীর অন্তর্দৃষ্টি বের করা যায়। শেষ পর্যন্ত সবকিছু একটিমাত্র ধারণার ওপর দাঁড়িয়ে—সূক্ষ্ম পরিবর্তন আর তার অনুপাত। এটাই ক্যালকুলাসের হৃদয়।",
    " ঠিক আছে, এখন একটু বিশ্রাম নিন। যেটা শিখেছেন সেটা মনে একবার চালিয়ে দেখুন। পরবর্তী পাঠে আমরা আবার নতুন করে শুরু করব, কিন্তু এই ভিত্তি সবসময় সাথে থাকবে।",
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
    for ch in ["\u201c", "\u201d", "\u2018", "\u2019", "\u2014", "-"]:
        t = t.replace(ch, ", ")
    for ch in ["'", '"', "[", "]", "{", "}", "*", "#", "`", "_", ";", ":", "\u2014"]:
        t = t.replace(ch, " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t.strip(" ,;:.")


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
        parts = [text[:mid].strip(" ,;:."), text[mid:].strip(" ,;:.")]
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
        parts = [p.strip() for p in re.split(r"[\u0964\u0965]", text) if p.strip()]
        made = []
        for j, p in enumerate(parts):
            pp = RAW_DIR / f"sent_{raw.stem}_{j}.mp3"
            purge(pp)
            try:
                await tts_save(p + "\u0964", pp)
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
    """Read the audio manifest's 26 cues; dedupe duplicate sections by alias."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    seen, out = set(), []
    for sec_key, sec in data.get("sections", {}).items():
        alias = sec.get("alias") or sec.get("section_id") or sec_key
        if alias in seen:
            continue
        seen.add(alias)
        for c in sec.get("cues", []):
            text = c.get("text")
            if not text:
                continue
            out.append({
                "text": text,
                "dur_ms": float(c.get("duration_ms", 0)),
                "section": alias,
            })
    return out


async def synth_all(cues):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, c in enumerate(cues):
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        ok = await synth(sanitize(c["text"]), raw)
        if not ok:
            failed.append(c["id"])
            print(f"  WARNING cue {c['id']} failed initial TTS", flush=True)
        if (i + 1) % 10 == 0:
            print(f"  TTS {i+1}/{len(cues)}", flush=True)
    return failed


def compute_expansion_targets(natural, vend):
    """Targets proportional to rendered speech so the whole video is covered."""
    n = len(natural)
    pause_s = INTER_CUE_PAUSE_MS / 1000.0
    usable_speech = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC - pause_s * (n - 1)
    total = sum(natural)
    factor = usable_speech / total if total > 0 else 1.0
    return [x * factor for x in natural], factor, usable_speech


async def heavy_expand(cues, targets):
    """HEAVILY expand every cue until its rendered speech reaches its target."""
    expanded = []
    for c, target in zip(cues, targets):
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        if not valid(raw):
            continue
        before = duration(raw)
        base = sanitize(c["text"])
        added = []
        for attempt in range(MAX_EXPAND_PASSES):
            nat = duration(raw)
            if nat >= EXPAND_REACH * target:
                break
            chunk = EXPANSION_POOL[(cid + attempt) % len(EXPANSION_POOL)]
            new_text = sanitize(base + " " + " ".join(added) + " " + chunk)
            if not await synth(new_text, raw, force=True):
                break
            added.append(chunk)
        after = duration(raw)
        expanded.append({
            "id": cid,
            "natural_before": round(before, 3),
            "natural_after": round(after, 3),
            "target_sec": round(target, 3),
            "passes": len(added),
        })
        print(f"  expand cue {cid:02d}: {before:.1f}s -> {after:.1f}s "
              f"(target {target:.1f}s, +{len(added)} chunks)", flush=True)
    return expanded


def layout_from_rendered(vend, source_cues, natural):
    """Recompute the timeline scale from the FINAL rendered speech durations.

    Windows are proportional to natural speech; scale maps
    sum(natural) + inter-cue pauses onto the usable timeline. Because speech
    was expanded so sum(natural) ~= usable_speech, the scale is ~= 1.0 and the
    atempo needed per cue is ~= 1.0 -> fill ~= 1.0 with no silent pockets.
    """
    n = len(source_cues)
    pause_s = INTER_CUE_PAUSE_MS / 1000.0
    authored_total = sum(natural) + pause_s * (n - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    scale = usable / authored_total if authored_total > 0 else 1.0
    cues, cursor = [], 0.0
    for i, (c, nat) in enumerate(zip(source_cues, natural)):
        start = LEAD_IN_SEC + cursor * scale
        dur = nat * scale
        cues.append({
            "id": i + 1,
            "start": round(start, 3),
            "end": round(start + dur, 3),
            "duration": round(dur, 3),
            "bn": c["text"],
            "section": c["section"],
        })
        cursor += nat + pause_s
    return cues, scale


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


def silencedetect_runs(path, noise_db="-35dB", min_dur=2.0):
    """Return [(start, end, duration), ...] of silence runs via ffmpeg."""
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-af", f"silencedetect=noise={noise_db}:d={min_dur}", "-f", "null", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    txt = r.stderr
    starts = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", txt)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([\d.]+)", txt)]
    runs = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else s + min_dur
        runs.append((round(s, 3), round(e, 3), round(e - s, 3)))
    return runs


async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    source_cues = load_manifest_cues()
    # Assign stable ids 1..N in manifest order.
    for i, c in enumerate(source_cues):
        c["id"] = i + 1
    n = len(source_cues)
    print(f"video duration = {vend:.3f}s; manifest cues = {n} (alias-deduped)", flush=True)

    print("[1/7] Initial TTS of the 26 manifest cues ...", flush=True)
    failed = await synth_all(source_cues)

    print("[2/7] Measure rendered speech + compute expansion targets ...", flush=True)
    natural0 = [duration(RAW_DIR / f"raw_{c['id']:03d}.mp3") for c in source_cues]
    targets, factor, usable_speech = compute_expansion_targets(natural0, vend)
    print(f"  rendered total = {sum(natural0):.2f}s ; usable speech = {usable_speech:.2f}s "
          f"; expansion factor = {factor:.4f}", flush=True)

    print("[3/7] HEAVY contextual expansion of every cue ...", flush=True)
    expansion = await heavy_expand(source_cues, targets)

    natural_final = [duration(RAW_DIR / f"raw_{c['id']:03d}.mp3") for c in source_cues]
    print(f"  rendered total AFTER expansion = {sum(natural_final):.2f}s", flush=True)

    print("[4/7] Recompute scale from rendered speech + lay out full timeline ...", flush=True)
    cues, scale = layout_from_rendered(vend, source_cues, natural_final)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"  timeline scale from rendered speech = {scale:.6f}", flush=True)

    print("[5/7] Absolute sample placement (start*44100, pad-only, floor 0.82) ...", flush=True)
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed, fills, internal_gaps = [], [], []
    overrun = 0
    last_cue_end = 0.0
    expanded_ids = {x["id"] for x in expansion}
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
            "placed_samples": end - start_sample,
            "expanded": cid in expanded_ids,
        })

    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    max_internal_gap_s = round(max(internal_gaps), 4) if internal_gaps else 0.0
    print(f"  median_fill = {median_fill} ; max_internal_gap_s = {max_internal_gap_s}", flush=True)

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

    print("[6/7] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    print("[7/7] Mux with FULL original video (video copy; src NEVER swapped) ...", flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    odur = duration(OUT_VIDEO)
    runs = silencedetect_runs(OUT_VIDEO)
    internal_runs = [r for r in runs if r[0] > LEAD_IN_SEC - 1.0 and r[1] < odur - TAIL_MARGIN_SEC + 1.0]
    gate_pass = bool(median_fill >= 0.72 and max_internal_gap_s <= 1.5 and len(internal_runs) == 0)

    report = {
        "experiment": "fill_v2 (heavy expansion + scale recomputed from rendered speech) - calculus lesson 06",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": f"audio manifest cues (alias-deduped): {MANIFEST.name}",
        "cue_count": len(placed),
        "expected_cue_count": n,
        "failed_tts_cues": failed,
        "strategy": "26 manifest cues; heavy pedagogical expansion; scale from rendered speech; absolute sample offset; atempo in [0.82,2.2]; pad only; no truncation",
        "sfx": "NONE -- clean speech only",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "tempo_floor": TEMPO_FLOOR,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "expansion_factor": round(factor, 6),
        "usable_speech_sec": round(usable_speech, 3),
        "rendered_total_initial_sec": round(sum(natural0), 3),
        "rendered_total_final_sec": round(sum(natural_final), 3),
        "timeline_scale_from_rendered": round(scale, 6),
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
        "silencedetect_noise_db": "-35dB",
        "silencedetect_min_dur_s": 2.0,
        "silencedetect_runs": runs,
        "silencedetect_internal_runs_gt2s": len(internal_runs),
        "video_src": str(ORIGINAL_VIDEO),
        "video_src_swapped": False,
        "gates_pass": gate_pass,
        "expansion_applied": expansion,
        "cues": placed,
    }

    report["output_video"] = str(OUT_VIDEO)
    report["output_duration_sec"] = round(odur, 3)
    report["output_size_bytes"] = OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0
    try:
        probe = json.loads(run(f'ffprobe -v error -show_entries stream=index,codec_type,codec_name '
                               f'-of json "{OUT_VIDEO}"'))
        report["output_streams"] = probe.get("streams", [])
    except Exception as e:
        report["output_streams_error"] = str(e)

    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\nDONE.", flush=True)
    print(f"cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={odur:.3f}s size={report['output_size_bytes']}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap_s={max_internal_gap_s} "
          f"fill_policy_met={report['fill_policy_met']}", flush=True)
    print(f"silencedetect internal runs>2s = {len(internal_runs)}", flush=True)
    print(f"GATES PASS = {gate_pass}", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
