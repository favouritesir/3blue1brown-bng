"""
EXPERIMENT — Full-length clean absolute-sample Bengali dub
(Essence of Probability, Lesson 04 — "Continuous Probability Distributions &
Probability Density")

Adapted verbatim from the proven clean_timesync_v2 pipeline:
  probability/lesson_01/dubbing_pipeline/experiments/clean_timesync_v2/build_prob01_clean.py
with the IMPROVED_DUB_FILL_POLICY.md upgrades from the newer reference:
  probability/lesson_06/dubbing_pipeline/experiments/clean_timesync_v2/build_prob06_clean.py

Guarantees:
   1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
      half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
   2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
      NOTE: manifest cue times are in MILLISECONDS (duration_ms); seconds are
      never silently multiplied here (the old master-script path used seconds).
   3. IMPROVED FILL: atempo floor 0.82 (gentle slowdown), ceiling 2.2. Pad only,
      NEVER truncate. NO SFX: clean speech only.
   4. EXPANSION FIRST: any cue whose natural TTS is short of its (provisional)
      window gets pedagogical Bengali sentences appended and is re-synthesized.
   5. RE-COMPUTE SCALE FROM SUMMED RENDERED SPEECH: after expansion the timeline
      is re-laid out so each cue window is proportional to its ACTUAL rendered
      speech length; scale = usable_video / (sum(rendered) + pauses).
   6. Fill metrics (per-cue fill, median_fill, max_internal_gap_s) are measured
      from the rendered waveform. Gate: median_fill >= 0.72 AND
      max_internal_gap <= 1.5 s. If the gate fails the whole cue set is
      re-rendered with progressively stronger expansion (auto re-render).
   7. Canvas padded to the FULL original video duration so -shortest can never
      trim video frames. Final cue is capped to finish inside the video; tail
      silence is preserved.
   8. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
   9. Lightweight volumedetect (-vn -nostats, log to FILE) on intro 0-2s and
      the final 2s, written into verification.json.

Cue source (read-only; teacher audio / manifests are NEVER modified):
    web_platform/assets/audio/probability/lesson_04/manifest.json — 6 narrated
    sections / 36 cues; alias-keyed duplicates are de-duplicated by section_id.

Everything is written under NEW experiment folders. Teacher audio, manifests
and other lessons are untouched.
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
BASE = EXP.parent.parent                        # .../probability/lesson_04/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "probability" / "lesson_04.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "probability" / "lesson_04" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "probability" / "lesson_04" / "experiments" / "3b1b_prob_04_full_dubbed.mp4"

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
VIDEO_ID = "ZA4JkHKZM50"
LESSON = "lesson_04"

# Silence margins: keep 0-2 s and the final 2 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Expansion policy constants (mutated by the auto re-render loop).
EXPAND_TRIGGER_RATIO = 0.62          # expand when natural < 62% of window
EXPAND_TARGET_FILL = 0.80            # aim above the 0.72 median floor (headroom)
MAX_APPENDED_SENTENCES = 12
ACTIVE_THRESHOLD = 0.015             # waveform threshold for internal-gap scan
MAX_RENDER_ATTEMPTS = 3
MEDIAN_FILL_FLOOR = 0.72
MAX_INTERNAL_GAP_CEIL = 1.5

# Section-aware pedagogical sentences appended to short cues. Cycled, never
# repeated verbatim inside a single cue, chosen so the teaching value is real.
EXPANSION_POOL = {
    "sec-discrete-vs-continuous": [
        "লক্ষ্য করুন, বিচ্ছিন্ন ক্ষেত্রে আমরা আলাদা আলাদা স্তম্ভ গণনা করি, কিন্তু অবিচ্ছিন্ন ক্ষেত্রে স্তম্ভের বদলে একটি মসৃণ রেখা আসে।",
        "মুদ্রা বা ছক্কার মতো সীমিত ফলাফলের বিপরীতে উচ্চতা বা সময়ের মতো পরিমাপের কোনো নির্দিষ্ট তালিকা থাকে না।",
        "পি এম এফ থেকে পি ডি এফ-e রূপান্তরের এই ধাপটিই পুরো অধ্যায়ের ভিত্তি তৈরি করে।",
        "তাই প্রশ্নটি বদলে যায়: কোনো বিন্দুর ভর নয়, বরং একটি ব্যবধান জুড়ে কতখানি ঘনত্ব আছে।",
    ],
    "sec-zero-probability-paradox": [
        "অসীম সংখ্যক বিন্দুর মধ্যে যেকোনো একটি নির্দিষ্ট বিন্দু বেছে নেওয়ার ওজন শূন্য হওয়াই স্বাভাবিক।",
        "সম্ভাবনা শূন্য মানেই ঘটনাটি অসম্ভব নয়—ডার্টবোর্ডের একক বিন্দুতেও কিন্তু বাজনা বাজে।",
        "একক প্রান্তবিন্দু অন্তর্ভুক্ত করলে বা না করলে ক্ষেত্রফলের কোনো পরিবর্তন হয় না।",
        "প্রকৃতপক্ষে সম্ভাবনার অর্থবহতা শুরু হয় একটি ব্যবধান থেকে, একক বিন্দু থেকে নয়।",
    ],
    "sec-density-analogy": [
        "লোহার রডের একক বিন্দুর ভর শূন্য হলেও রডের মোট ভর এক কিলোগ্রাম—এই উপমাটি মনে রাখবেন।",
        "ঘনত্বকে দৈর্ঘ্যের ক্ষুদ্র অংশ দিয়ে গুণ করলেই প্রকৃত ভর বা সম্ভাবনা পাওয়া যায়।",
        "পি ডি এফ-এর মান একের চেয়ে বড় হতে পারে, কারণ এটি সম্ভাবনা নয় বরং প্রতি একক দৈর্ঘ্যের হার।",
        "সমাকলন ছাড়া একক বিন্দুগুলোর যোগফল কখনোই পূর্ণ একক গঠন করতে পারে না।",
    ],
    "sec-area-under-curve": [
        "অতি পাতলা প্রতিটি ফালির ক্ষেত্রফল প্রস্থ গুণ উচ্চতা, আর এগুলোর যোগফলই নির্দিষ্ট যোগজ।",
        "বক্ররেখা কখনো অনুভূমিক অক্ষের নিচে নামতে পারে না, কারণ ঋণাত্মক সম্ভাবনার অস্তিত্ব নেই।",
        "মাইনাস অসীম থেকে প্লাস অসীম পর্যন্ত মোট ক্ষেত্রফল ঠিক এক হওয়াই নরমালাইজেশন শর্ত।",
        "সিডিএফ হলো বাম দিক থেকে সঞ্চিত ক্ষেত্রফল, আর তার ঢাল আবার মূল ঘনত্ব ফিরিয়ে আনে।",
    ],
    "sec-gaussian-bell-curve": [
        "মিউ ঠিক করে ঘণ্টাটি কোথায় দাঁড়াবে, আর সিগমা ঠিক করে সেটি কতটা ছড়াবে।",
        "সিগমা ছোট হলে বক্ররেখা চারু ও খাড়া হয়, বড় হলে চ্যাপ্টা হয়ে দুই দিকে বিস্তৃত হয়।",
        "আটষট্টি, পঞ্চানব্বই, নিরানব্বই দশমিক সাতের নীতি প্রতিদিনের পরিসংখ্যানে বারবার কাজে লাগে।",
        "সামনের নরমালাইজিং সহগটি কোনো রহস্য নয়, এটি নিশ্চিত করে মোট ক্ষেত্রফল ঠিক এক।",
    ],
    "sec-clt-intuition": [
        "একটি ছক্কার বণ্টন সমতল, দুটির যোগফল ত্রিভুজাকার, আর দশটির যোগফল মসৃণ ঘণ্টার মতো।",
        "গ্যালটন বোর্ডে প্রতিটি পিনের সংঘর্ষ একক স্বাধীন ঘটনা, কিন্তু নিচে জমা হয় নিখুঁত বেল কার্ভ।",
        "আদি বণ্টনের আকৃতি যেকোনো হোক না কেন, স্বাধীন চলকের সমষ্টি সর্বদা স্বাভাবিক বণ্টনের দিকে যায়।",
        "মানুষের উচ্চতা বা বুদ্ধিমত্তার মতো বাস্তব পরিমাপে এই নিয়মের প্রাচুর্য দেখা যায়।",
    ],
}
DEFAULT_EXPANSIONS = [
    "এই ধারণাটি নিজের ভাষায় একবার বলে দেখলে বিষয়টি আরও পরিচ্ছন্ন হবে।",
    "লক্ষ্য করুন, বক্ররেখার নিচের এই ক্ষেত্রফলই আমাদের আসল উত্তরের দিকে নিয়ে যায়।",
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


def load_manifest_cues(lesson):
    """Read the audio_manifest referenced by lesson_04.json (read-only).

    Times are in MILLISECONDS (duration_ms). The manifest stores each section
    twice (canonical id + alias id) with identical cues; de-duplicate by
    section_id so cues are not doubled (6 sections / 36 cues).
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
            out.append({
                "text": text,
                "dur_ms": float(c.get("duration_ms", 0)),   # milliseconds, NOT seconds
                "section": sid,
            })
    if out:
        return out, f"audio_manifest:{manifest.name} (alias-deduped)"
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
        for t in texts:
            clean = re.sub(r"\$[^\$]*\$", " ", t)
            clean = re.sub(r"[\\\{\}\[\]#*]", " ", clean)
            clean = re.sub(r"\s+", " ", clean).strip()
            if clean:
                out.append({"text": clean,
                            "dur_ms": max(2000.0, len(clean) * 90.0),
                            "section": sec_id})
    return out


def load_source_cues():
    """Return (list_of_{text,dur_ms,section}, source_description)."""
    lesson = json.loads(LESSON_JSON.read_text(encoding="utf-8"))
    out, desc = load_manifest_cues(lesson)
    if out:
        return out, desc
    return derive_from_lesson(lesson), "lesson_04.json:sections"


def load_provisional_cues(vend, source_cues):
    """Lay authored cues out cumulatively, scaled to span the full video.

    This is a PROVISIONAL layout used only to size the expansion step. After
    expansion the scale is re-computed from summed rendered speech.
    """
    authored_total = sum(c["dur_ms"] for c in source_cues) + INTER_CUE_PAUSE_MS * (len(source_cues) - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    authored_scale = usable / (authored_total / 1000.0) if authored_total > 0 else 1.0

    cues = []
    cursor_ms = 0.0
    for i, c in enumerate(source_cues):
        start = LEAD_IN_SEC + (cursor_ms / 1000.0) * authored_scale
        dur = (c["dur_ms"] / 1000.0) * authored_scale
        cues.append({
            "id": i + 1,
            "start": round(start, 3),
            "end": round(start + dur, 3),
            "duration": round(dur, 3),
            "bn": sanitize(c["text"]),
            "section": c["section"],
        })
        cursor_ms += c["dur_ms"] + INTER_CUE_PAUSE_MS
    return cues, authored_scale


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


async def expand_short_cues(cues):
    """IMPROVED_DUB_FILL_POLICY: append pedagogical sentences to any cue whose
    natural TTS is short of its provisional window, then re-synthesize.
    """
    expanded = []
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        target = float(c["duration"])
        natural = duration(raw)
        c["rendered_nat"] = natural
        if natural <= 0 or natural >= EXPAND_TRIGGER_RATIO * target:
            continue
        pool = EXPANSION_POOL.get(c["section"], DEFAULT_EXPANSIONS)
        base = sanitize(c["bn"])
        added = 0
        before = natural
        while added < MAX_APPENDED_SENTENCES:
            need = (EXPAND_TARGET_FILL * MIN_TEMPO * target - natural)
            if need <= 0:
                break
            extra_chars = max(60, int(need / max(natural, 0.1) * len(base)))
            n_sent = max(1, min(MAX_APPENDED_SENTENCES - added,
                                int(np.ceil(extra_chars / 95.0))))
            append_text = " ".join(pool[(added + j) % len(pool)] for j in range(n_sent))
            new_text = sanitize(base + " " + append_text)
            print(f"  expand cue {cid}: fill {predicted_fill(natural, target):.2f} "
                  f"natural={natural:.2f}s target={target:.2f}s +{n_sent} sent", flush=True)
            if await synth(new_text, raw, force=True):
                added += n_sent
                natural = duration(raw)
                if predicted_fill(natural, target) >= EXPAND_TARGET_FILL:
                    break
            else:
                break
        c["rendered_nat"] = natural
        if added > 0 and natural > 0:
            c["bn"] = sanitize(base + " " + " ".join(pool[j % len(pool)] for j in range(added)))
            expanded.append({
                "id": cid,
                "section": c["section"],
                "natural_before": round(before, 3),
                "natural_after": round(natural, 3),
                "sentences_added": added,
                "fill_before": round(predicted_fill(before, target), 3),
                "fill_after": round(predicted_fill(natural, target), 3),
            })
    return expanded


def recompute_scale_from_rendered(cues, vend):
    """Re-layout the timeline so each window is proportional to ACTUAL rendered
    speech. Returns the recomputed scale. This makes fill uniform across cues
    and directly satisfies the IMPROVED_DUB_FILL_POLICY measurement.
    """
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    pause = INTER_CUE_PAUSE_MS / 1000.0
    rendered_total = sum(float(c.get("rendered_nat") or 0) for c in cues) + pause * (len(cues) - 1)
    scale = usable / rendered_total if rendered_total > 0 else 1.0
    cursor = 0.0
    for c in cues:
        nat = float(c.get("rendered_nat") or 0)
        start = LEAD_IN_SEC + cursor * scale
        dur = nat * scale
        c["start"] = round(start, 3)
        c["end"] = round(start + dur, 3)
        c["duration"] = round(dur, 3)
        cursor += nat + pause
    return scale, rendered_total


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
    """Longest silent run (seconds) between the first and last active sample."""
    if arr.size == 0:
        return 0.0
    active = np.flatnonzero(np.abs(arr) > thr)
    if active.size < 2:
        return 0.0
    gaps = np.diff(active)
    if gaps.size == 0:
        return 0.0
    return float(gaps.max()) / sr


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
    return arr, tempo, natural, target, fit_samples


def render_canvas(cues, vend, failed, expanded):
    """Absolute-sample placement into a FULL-length canvas; returns metrics."""
    global LAST_START, VIDEO_END, LAST_ID
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    CHUNK = 1_000_000
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    overrun = 0
    last_cue_end = 0.0
    expanded_ids = {x["id"] for x in expanded}
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

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    fills = [x["fill"] for x in placed]
    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    max_internal_gap = round(max((x["max_internal_gap_s"] for x in placed), default=0.0), 4)
    metrics = {
        "placed": placed,
        "overrun": overrun,
        "max_drift": max_drift,
        "median_fill": median_fill,
        "max_internal_gap": max_internal_gap,
        "last_cue_end": last_cue_end,
        "canvas": canvas,
    }
    return metrics


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
    global EXPAND_TRIGGER_RATIO, EXPAND_TARGET_FILL, MAX_APPENDED_SENTENCES
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    source_cues, source_desc = load_source_cues()
    cues, authored_scale = load_provisional_cues(vend, source_cues)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    for c in cues:
        c["base_bn"] = c["bn"]
    print(f"video duration = {vend:.3f}s; cues = {len(cues)}; source = {source_desc}; "
          f"authored timeline scale = {authored_scale:.4f}", flush=True)

    attempts = []
    final_metrics = None
    final_expanded = []
    final_failed = []
    final_scale = None
    final_rendered_total = None
    gate_ok = False

    for attempt_no in range(1, MAX_RENDER_ATTEMPTS + 1):
        print(f"\n===== RENDER ATTEMPT {attempt_no}/{MAX_RENDER_ATTEMPTS} "
              f"(trigger={EXPAND_TRIGGER_RATIO}, target_fill={EXPAND_TARGET_FILL}, "
              f"max_sent={MAX_APPENDED_SENTENCES}) =====", flush=True)
        # Fresh synthesis from the immutable base texts on every retry.
        for c in cues:
            c["bn"] = c["base_bn"]
            c.pop("rendered_nat", None)
            raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
            if attempt_no > 1:
                purge(raw)
                for extra in RAW_DIR.glob(f"{raw.stem}_*.mp3"):
                    purge(extra)

        print("[1/5] TTS (clean, no SFX) ...", flush=True)
        failed = await synth_all(cues)
        print("[2/5] Expansion of short cues (IMPROVED_DUB_FILL_POLICY) ...", flush=True)
        expanded = await expand_short_cues(cues)
        print(f"  expanded {len(expanded)} cues", flush=True)

        print("[3/5] Re-compute scale from SUMMED RENDERED speech ...", flush=True)
        scale, rendered_total = recompute_scale_from_rendered(cues, vend)
        LAST_START = float(cues[-1]["start"])
        LAST_ID = cues[-1]["id"]
        print(f"  rendered speech total = {rendered_total:.3f}s; recomputed scale = {scale:.4f}", flush=True)

        print("[4/5] Absolute sample placement (start*44100, pad-only) ...", flush=True)
        metrics = render_canvas(cues, vend, failed, expanded)
        attempt_info = {
            "attempt": attempt_no,
            "expand_trigger_ratio": EXPAND_TRIGGER_RATIO,
            "expand_target_fill": EXPAND_TARGET_FILL,
            "max_appended_sentences": MAX_APPENDED_SENTENCES,
            "expanded_cues": len(expanded),
            "rendered_speech_total_sec": round(rendered_total, 3),
            "recomputed_scale": round(scale, 6),
            "median_fill": metrics["median_fill"],
            "max_internal_gap_s": metrics["max_internal_gap"],
            "max_measured_drift_ms": round(metrics["max_drift"], 6),
            "gate_passed": (metrics["median_fill"] >= MEDIAN_FILL_FLOOR and
                            metrics["max_internal_gap"] <= MAX_INTERNAL_GAP_CEIL),
        }
        attempts.append(attempt_info)
        final_metrics = metrics
        final_expanded = expanded
        final_failed = failed
        final_scale = scale
        final_rendered_total = rendered_total
        gate_ok = attempt_info["gate_passed"]
        print(f"  median_fill={metrics['median_fill']} "
              f"max_internal_gap={metrics['max_internal_gap']}s gate={gate_ok}", flush=True)
        if gate_ok:
            break
        # Escalate expansion strength for the next render (auto re-render).
        EXPAND_TRIGGER_RATIO = max(0.20, EXPAND_TRIGGER_RATIO - 0.15)
        EXPAND_TARGET_FILL = min(1.30, EXPAND_TARGET_FILL + 0.15)
        MAX_APPENDED_SENTENCES = min(30, MAX_APPENDED_SENTENCES + 6)

    canvas = final_metrics["canvas"]
    print("[5/5] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        CHUNK = 1_000_000
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    report = {
        "experiment": "clean_timesync_v2 (probability_lesson_04 full-length, improved fill + rendered-scale relayout)",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": source_desc,
        "manifest_cue_count": len(source_cues),
        "cue_count": len(final_metrics["placed"]),
        "expected_cue_count": len(cues),
        "failed_tts_cues": final_failed,
        "strategy": "absolute sample offset (start*44100); atempo fit floor 0.82; pad only; no truncation; scale re-computed from summed rendered speech",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "min_tempo": MIN_TEMPO,
        "max_tempo": MAX_TEMPO,
        "overrun_cues": final_metrics["overrun"],
        "max_measured_drift_ms": round(final_metrics["max_drift"], 6),
        "authored_timeline_scale": round(authored_scale, 6),
        "timeline_scale": round(final_scale, 6),
        "rendered_speech_total_sec": round(final_rendered_total, 3),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(final_metrics["last_cue_end"], 3),
        "tail_silence_sec": round(len(canvas) / SR - final_metrics["last_cue_end"], 3),
        "speech_ends_before_video_end": final_metrics["last_cue_end"] < vend,
        "fill_policy": {
            "expand_trigger_ratio": attempts[-1]["expand_trigger_ratio"],
            "expand_target_fill": attempts[-1]["expand_target_fill"],
            "median_fill": final_metrics["median_fill"],
            "median_fill_target": MEDIAN_FILL_FLOOR,
            "median_fill_ok": final_metrics["median_fill"] >= MEDIAN_FILL_FLOOR,
            "max_internal_gap_s": final_metrics["max_internal_gap"],
            "max_internal_gap_target": MAX_INTERNAL_GAP_CEIL,
            "max_internal_gap_ok": final_metrics["max_internal_gap"] <= MAX_INTERNAL_GAP_CEIL,
        },
        "fill_gate_passed": gate_ok,
        "render_attempts": attempts,
        "attempts_used": len(attempts),
        "median_fill": final_metrics["median_fill"],
        "max_internal_gap_s": final_metrics["max_internal_gap"],
        "expanded_cues": final_expanded,
        "cues": final_metrics["placed"],
    }

    print("Mux with FULL original video (video copy) ...", flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    report["output_video"] = str(OUT_VIDEO)
    report["output_duration_sec"] = round(duration(OUT_VIDEO), 3)
    report["output_size_bytes"] = OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0
    try:
        probe = json.loads(run(f'ffprobe -v error -show_entries stream=index,codec_type,codec_name,width,height '
                               f'-of json "{OUT_VIDEO}"'))
        report["output_streams"] = probe.get("streams", [])
    except Exception as e:
        report["output_streams_error"] = str(e)

    print("Lightweight volumedetect ...", flush=True)
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    odur = duration(OUT_VIDEO)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(final_metrics['placed'])} overrun={final_metrics['overrun']} "
          f"drift={final_metrics['max_drift']:.3f}ms", flush=True)
    print(f"video={report['output_duration_sec']}s size={report['output_size_bytes']}", flush=True)
    print(f"median_fill={final_metrics['median_fill']} max_internal_gap={final_metrics['max_internal_gap']}s "
          f"expanded={len(final_expanded)} gate={gate_ok} attempts={len(attempts)}", flush=True)
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)
    if not gate_ok:
        print("WARNING: fill gate did not pass after all render attempts — see verification.json", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
