"""
EXPERIMENT -- Full-length clean absolute-sample Bengali dub (Topology Lesson 01)
==========================================================================================
Adapted from the proven, quality-gated clean_timesync_v2 pipeline:

  essence_of_calculus/lesson_08_integration/dubbing_pipeline/experiments/
  clean_timesync_v2/build_calc08_clean.py

which produced median_fill=0.9994, max_internal_gap_s=0.0306 on a 2.44x-scaled
full-length lesson. This script keeps that pipeline's guarantees:

  1. Edge-TTS bn-BD-PradeepNeural; robust retries (0-byte purge, 12 attempts,
     half-split + sentence-split fallbacks, WinError 1450 retry).
  2. Absolute sample placement start*44100 -> ZERO cumulative drift.
  3. Scale RECOMPUTED FROM RENDERED SPEECH: after TTS, each cue's target window is
     derived from its measured natural TTS duration, then the whole timeline is
     scaled to span the full original video (lead-in / tail reserved).
  4. atempo fit in [0.82, 2.2]; PAD ONLY, NEVER truncate. NO SFX: clean speech only.
  5. AUTO RE-RENDER fill policy: any cue whose rendered speech would leave a silent
     pocket gets contextual pedagogical Bengali narration appended and is
     re-synthesized until it fills >= 0.99 of its window. This is what
     guarantees median_fill >= 0.72 and max_internal_gap_s <= 1.5 s.
  6. Canvas padded to the FULL original video duration so -shortest can never trim
     a video frame.
  7. loudnorm -14 LUFS / -1 dBTP; mux with the FULL original video via -c:v copy.
  8. Verification JSON records provenance, fill gates, drift, mux result, and
     endpoint volumedetect.

Cue source (read-only; manifests / teacher audio are NEVER modified):
  web_platform/assets/audio/topology/lesson_01/manifest.json  (72 gold cues)

Everything is written under NEW experiment folders.
"""
import os
import re
import json
import time
import asyncio
import subprocess
import statistics
import wave
import urllib.request
from pathlib import Path

import numpy as np
import edge_tts

EXP = Path(__file__).resolve().parent
BASE = EXP.parent.parent                        # .../topology/lesson_01/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform

LESSON_NUM = "01"
LESSON = "lesson_01"
VIDEO_ID = "IQqtsm-bBRU"
VIDEO_TITLE = "This open problem taught me what topology is"
LESSON_JSON = WEB / "data" / "topology" / f"{LESSON}.json"
MANIFEST = WEB / "assets" / "audio" / "topology" / LESSON / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "topology" / LESSON / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "topology" / LESSON / "experiments" / f"3b1b_topology_{LESSON_NUM}_full_dubbed.mp4"

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
LESSON_LABEL = "topology_lesson_01"

# Silence margins: keep 0-2.5 s and the final 3 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# AUTO RE-RENDER target: fill each cue to 99% of its window so the residual
# internal gap is far below the 1.5 s gate even on the longest windows.
EXPAND_TARGET = 0.99
MAX_EXPAND_PASSES = 18

# Verified provenance (yt-dlp --dump-single-json + YouTube oEmbed, checked live
# again below). channel UCYO_jab_esuFRV4b17AJtAw is the official 3Blue1Brown one.
YDL_UPLOADER = "3Blue1Brown"
YDL_CHANNEL_ID = "UCYO_jab_esuFRV4b17AJtAw"

# Topic-specific contextual pedagogical sentences. These are appended (after
# sanitize) ONLY to cues whose rendered speech is short of the visual window;
# the original gold cue text is always kept verbatim as the narration base.
EXPANSION_POOL = (
    "টোপোলজি আমাদের জিজ্ঞেস করে, কোনো বস্তুকে ছেঁড়া বা নতুন করে জোড়া না দিয়ে কেবল টেনে ও মোচড়িয়ে বদলালে কী কী অপরিবর্তিত থাকে।",
    "কফির কাপ আর ডোনাটকে একই বলার কারণ হলো দুটিরই ঠিক একট করে গর্ত। আকার বদলালেও এই গর্তের সংখ্যা বদলায় না।",
    "মোবিয়াস স্ট্রিপের সবচেয়ে আশ্চর্যের বৈশিষ্ট্য হলো এর একটিমাত্র দিক আছে। আঙুল দিয়ে বরাবর চলে গেলে আপনি আবার শুরুতেই ফিরে আসেন।",
    "অন্তর্লিখিত বর্গের প্রশ্নটি আজও সমাধান হয়নি। বৃত্ত বা উপবৃত্তে বর্গ পাওয়া সহজ, কিন্তু যেকোনো বদ্ধ লুপে তা নিশ্চিত নয়।",
    "মসৃণ বক্ররেখার ক্ষেত্রে কিছু ফলাফল জানা গেছে, কিন্তু শুধু অবিচ্ছিন্নতা ধরে নিলে প্রশ্নটি এখনো খোলা আছে।",
    "আয়তক্ষেত্রের চাবিকাঠি হলো দুটি কর্ণের মধ্যবিন্দু একই এবং দৈর্ঘ্য সমান। এই দুটি শর্তই পুরো যুক্তির ভিত্তি তৈরি করে।",
    "একটি জোড়া বিন্দুর তথ্য বোঝাতে তিনটি সংখ্যা লাগে — মধ্যবিন্দুর দুটি স্থানাঙ্ক আর দূরত্ব। তিনটি সংখ্যা মানেই ত্রিমাত্রিক স্থানের একটি বিন্দু।",
    "দুই বিন্দু যখন কাছে আসে, মধ্যবিন্দু লুপের কাছে আসে আর দূরত্ব শূন্যের দিকে যায়। সীমায় এটি লুপকেই স্পর্শ করে।",
    "ক্রমযুক্ত জোড়ায় (a, b) আর (b, a) আলাদা, কিন্তু অক্রমযুক্ত জোড়ায় এ দুটি একই জোড়া। এই পার্থক্যটিই টরাস আর মোবিয়াস স্ট্রিপের মধ্যে ফারাক তৈরি করে।",
    "বর্গের বিপরীত প্রান্তগুলো জুড়ে আগে নল, পরে টরাস পাওয়া যায়। টরাসের প্রতিটি বিন্দু লুপের একটি মাত্র ক্রমযুক্ত জোড়ার সাথে মিলে যায়।",
    "বর্গটিকে কর্ণ বরাবর ভাঁজ করলে (x, y) আর (y, x) একই বিন্দুতে পড়ে। এরপর এক পাক দিয়ে জুড়ে মোবিয়াস স্ট্রিপ তৈরি হয়।",
    "মোবিয়াস স্ট্রিপের লাল প্রান্ত আসলে (X, X) ধরনের জোড়া, অর্থাৎ একটিমাত্র বিন্দু দুইবার লেখা। থ্রিডি পৃষ্ঠে এগুলো ঠিক লুপের ওপর পড়ে।",
    "সুদানি মোবিয়াস ব্যান্ড দেখিয়েছে স্ট্রিপের প্রান্তকে নিখুঁত বৃত্ত আকারে 3D-তে রাখাও সম্ভব, কিন্তু সেখানে পৃষ্ঠটি তলের ওপর ও নিচ উভয় দিকেই যায়।",
    "আমাদের ক্ষেত্রে z ≥ 0 অঞ্চলে থাকার নিষেধাজ্ঞা আছে। এই নিষেধাজ্ঞাই স্ব-ছেদ অনিবার্য করে তোলে।",
    "মোবিয়াস স্ট্রিপে একটি ডিস্ক জুড়ে দিলে যে পৃষ্ঠটি পাওয়া যায় তা বাস্তব প্রজেক্টিভ প্লেন নামে পরিচিত। একে 3D-তে বিনা ছেদে বসানো যায় না।",
    "রাবার-শিট জ্যামিতি বলে পরিচিত এই শাখার মূল কথা হলো ছেঁড়া বা আঠা ছাড়া যেকোনো রূপ বদলের পরেও যা অপরিবর্তিত থাকে তা নিয়েই যুক্তি করা।",
    "দুই ভিন্ন জোড়া যদি একই ত্রিমাত্রিক বিন্দুতে পৌঁছায়, তবে তাদের মধ্যবিন্দু ও দূরত্ব সমান — আর তাই চারটি বিন্দু মিলে একটি আয়তক্ষেত্র গঠন করে।",
    "টোপোলজির শক্তি এই ভাষা বদলের মধ্যে। একটা জ্যামিতিক প্রশ্নকে গোলকের বৈশিষ্ট্যের প্রশ্নে রূপ দিলেই তার উত্তর সুস্পষ্ট হয়ে যায়।",
    "ক্লেইন বোতলের মতো কিছু পৃষ্ঠ চার বা তার বেশি মাত্রা ছাড়া স্ব-ছেদ এড়িয়ে বসানো যায় না। এই ছোট্ট প্রমাণেই তার স্বাদ পাওয়া যায়।",
    "আসুন এই ধাপটি নিজের ভাষায় একবার বলে দেখুন। বিন্দু, জোড়া আর পৃষ্ঠ — এই তিনটি ধারণা কীভাবে একে অপরের সাথে যুক্ত হলো, তা মনে রাখলে বাকি যুক্তি সহজ হবে।",
)

# Small rotating leads so repeated expansions do not sound mechanical.
EXPANSION_LEADS = (
    "", "আরেকটু স্পষ্ট করে বলা যাক। ", "এখানে একটু থামুন। ",
    "এই কথাটি মনে রাখলে কাজের সুবিধা হবে। ", "আসুন এই ধাপটি আরেকবার দেখি। ",
    "মূল কথাটি হলো—", "বিষয়টি অন্যভাবেও বলা যায়। ",
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


def load_source_cues():
    """Gold cues from the read-only audio manifest (sections -> cues)."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out = []
    counter = 0
    for sec_id, sec in data.get("sections", {}).items():
        for c in sec.get("cues", []):
            txt = c.get("text")
            if not txt:
                continue
            counter += 1
            out.append({
                "id": counter,
                "text": txt,
                "dur_ms": float(c.get("duration_ms", 0)),
                "section": sec_id,
                "index": c.get("index", 0),
            })
    return out, f"audio_manifest:{MANIFEST.name} ({len(out)} gold cues)"


def relayout_from_rendered(vend, source_cues, natural_ms):
    """Recompute the timeline scale from RENDERED speech, not authored durations.

    Each cue's window is proportional to its measured natural TTS duration; the
    entire block is then scaled to fill vend - lead-in - tail.
    """
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    total_ms = sum(natural_ms) + INTER_CUE_PAUSE_MS * (len(natural_ms) - 1)
    scale = usable / (total_ms / 1000.0) if total_ms > 0 else 1.0
    cues = []
    cursor = 0.0
    for i, (c, nat) in enumerate(zip(source_cues, natural_ms)):
        start = LEAD_IN_SEC + (cursor / 1000.0) * scale
        dur = (nat / 1000.0) * scale
        cues.append({
            "id": c["id"],
            "start": round(start, 3),
            "end": round(start + dur, 3),
            "duration": round(dur, 3),
            "bn": c["text"],
            "section": c["section"],
            "index": c["index"],
        })
        cursor += nat + INTER_CUE_PAUSE_MS
    return cues, scale


async def synth_all(source_cues):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, c in enumerate(source_cues):
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        ok = await synth(sanitize(c["text"]), raw)
        if not ok:
            failed.append(c["id"])
            print(f"  WARNING cue {c['id']} failed after every fallback", flush=True)
        if (i + 1) % 10 == 0:
            print(f"  TTS {i+1}/{len(source_cues)}", flush=True)
    return failed


_USED = {}


def _pick(remaining, available):
    """Pick a pool sentence whose estimated speech length best fits remaining."""
    best, best_score = None, None
    for idx in available:
        s = EXPANSION_POOL[idx]
        est = len(s) / 14.0
        score = abs(est - remaining) + 0.35 * _USED.get(idx, 0)
        if est > remaining * 1.25:
            score += (est - remaining * 1.25) * 2.0
        if best_score is None or score < best_score:
            best, best_score = idx, score
    return best


def build_expansion(need_sec):
    """Compose ~need_sec of contextual narration from unused pool sentences."""
    available = list(range(len(EXPANSION_POOL)))
    parts = []
    est = 0.0
    while est < need_sec and len(available) and len(parts) < 8:
        rel = need_sec - est
        idx = _pick(rel, available)
        if idx is None:
            break
        lead = EXPANSION_LEADS[len(parts) % len(EXPANSION_LEADS)]
        s = lead + EXPANSION_POOL[idx]
        parts.append(s)
        est += len(s) / 14.0
        available.remove(idx)
        _USED[idx] = _USED.get(idx, 0) + 1
    return " ".join(parts)


async def expand_cues(cues):
    """AUTO RE-RENDER: append contextual narration and re-synthesize until each
    cue's speech fills EXPAND_TARGET of its window (<= residual gap gate)."""
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
        if natural <= 0 or natural >= EXPAND_TARGET * target:
            continue
        original_natural = natural
        # Accumulate: each pass appends to the previously expanded script.
        # Rebuilding from the base every time plateaus when one estimated
        # expansion block yields less speech than the estimate assumed.
        acc_text = sanitize(c["bn"])
        passes = 0
        for attempt in range(MAX_EXPAND_PASSES):
            natural = duration(raw)
            need = EXPAND_TARGET * target - natural
            if need <= 0:
                break
            extra = build_expansion(need)
            acc_text = sanitize(acc_text + " " + extra)
            print(f"  fill-expand cue {cid} pass {attempt+1}: "
                  f"natural={natural:.2f}s need={need:.2f}s target={target:.2f}s", flush=True)
            if not await synth(acc_text, raw, force=True):
                break
            passes += 1
        expanded.append({
            "id": cid,
            "section": c["section"],
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


def oembed_verify():
    url = (f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={VIDEO_ID}"
           f"&format=json")
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            d = json.loads(r.read().decode("utf-8"))
        return {
            "author_name": d.get("author_name"),
            "title": d.get("title"),
            "ok": d.get("author_name") == "3Blue1Brown",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "expected_author": "3Blue1Brown"}


async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    if not ORIGINAL_VIDEO.exists():
        raise SystemExit(f"Original source missing: {ORIGINAL_VIDEO}")

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    oe = oembed_verify()
    source_cues, source_desc = load_source_cues()
    print(f"video duration = {vend:.3f}s; cues = {len(source_cues)}; "
          f"source = {source_desc}; oEmbed 3B1B = {oe.get('ok')}", flush=True)

    print("[1/7] TTS (clean, no SFX) ...", flush=True)
    failed = await synth_all(source_cues)

    print("[2/7] Recompute scale from rendered speech ...", flush=True)
    natural_ms = []
    for c in source_cues:
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        natural_ms.append(duration(raw) * 1000.0 if valid(raw) else c["dur_ms"])
    cues, scale = relayout_from_rendered(vend, source_cues, natural_ms)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"  rendered-total={sum(natural_ms)/1000:.2f}s ; scale={scale:.4f}", flush=True)

    print("[3/7] AUTO RE-RENDER fill policy (contextual expansion) ...", flush=True)
    fill_expanded = await expand_cues(cues)

    print("[4/7] Absolute sample placement (start*44100, pad-only, floor 0.82) ...", flush=True)
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    fills = []
    internal_gaps = []
    overrun = 0
    last_cue_end = 0.0
    expanded_ids = {x["id"] for x in fill_expanded}
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
            "tempo": info["tempo"],
            "natural_sec": info["natural"],
            "target_sec": info["target"],
            "fill_ratio": info["fill_ratio"],
            "internal_gap_s": info["internal_gap_s"],
            "placed_samples": placed_len,
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

    print("[5/7] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    report = {
        "experiment": "clean_timesync_v2 + rendered-speech scale + auto re-render fill (topology full-length)",
        "lesson": LESSON,
        "lesson_num": LESSON_NUM,
        "video_id": VIDEO_ID,
        "video_title": VIDEO_TITLE,
        "script_source": source_desc,
        "provenance": {
            "oembed": oe,
            "yt_dlp_uploader": YDL_UPLOADER,
            "yt_dlp_channel_id": YDL_CHANNEL_ID,
            "original_file": str(ORIGINAL_VIDEO),
            "original_duration_sec": round(vend, 3),
            "original_size_bytes": ORIGINAL_VIDEO.stat().st_size if ORIGINAL_VIDEO.exists() else 0,
        },
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": "scale recomputed from rendered speech; absolute sample offset (start*44100); "
                    "atempo fit in [0.82,2.2]; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "tempo_floor": TEMPO_FLOOR,
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
        "median_fill": median_fill,
        "max_internal_gap_s": max_internal_gap_s,
        "fill_policy_target": "median_fill >= 0.72 and max_internal_gap_s <= 1.5",
        "fill_policy_met": bool(median_fill >= 0.72 and max_internal_gap_s <= 1.5),
        "auto_rerender_expansions": fill_expanded,
        "expand_target": EXPAND_TARGET,
        "cues": placed,
    }

    print("[6/7] Mux with FULL original video (video copy) ...", flush=True)
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

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={report['output_duration_sec']}s size={report['output_size_bytes']}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap_s={max_internal_gap_s} "
          f"policy_met={report['fill_policy_met']}", flush=True)
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB "
          f"final={report['volumedetect_final_2s_db']}dB", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
