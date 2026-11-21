"""
EXPERIMENT — Full-length clean absolute-sample Bengali dub
(Neural Networks, Lesson 02 — "Gradient descent, how neural networks learn")

Adapted verbatim from the proven clean_timesync_v2 pipeline:
  probability/lesson_01/dubbing_pipeline/experiments/clean_timesync_v2/build_prob01_clean.py

Guarantees (identical to the proven pipeline, plus IMPROVED_DUB_FILL_POLICY.md):
    1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
       half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
    2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
    3. IMPROVED FILL: atempo floor 0.82 (gentle slowdown), ceiling 2.2. Pad only,
       NEVER truncate. NO SFX: clean speech only.
    4. EXPANSION FIRST: any cue whose natural TTS is short of its (scaled) window
       gets 1..N pedagogical Bengali sentences appended and is re-synthesized,
       until predicted fill >= EXPAND_TARGET_FILL. Section-aware sentence pools
       keep the additions meaningful (what to notice / why it matters).
       (This lesson's video is ~1233 s vs ~493 s authored => ~2.49x stretch, so
        expansion headroom is raised vs the probability lesson.)
    5. Fill metrics (per-cue fill, median_fill, max_internal_gap_s) are measured
       from the rendered waveform and written into verification.json.
    6. Canvas padded to the FULL original video duration so -shortest can never
       trim video frames.
    7. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
    8. Lightweight volumedetect (-vn -nostats, log to FILE) on intro 0-2s and
       the final 2s, written into verification.json.

Cue source (read-only; teacher audio / manifests are NEVER modified):
    1. .../neural_networks/lesson_02*/dubbing_pipeline/*master_script*.json (PRIMARY)
       -- if present, start/end/duration in SECONDS are converted x1000 to ms.
    2. web_platform/assets/audio/neural_networks/lesson_02/manifest.json
       (audio manifest, EXPLICIT path — lesson_02.json has no audio_manifest key).
       duration_ms is already milliseconds. Alias-keyed duplicate sections are
       de-duplicated by section_id so cues are not doubled.
    3. last resort: derive cues from the sections of lesson_02.json itself.

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
BASE = EXP.parent.parent                        # .../neural_networks/lesson_02_gradient_descent/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "neural_networks" / "lesson_02.json"
MANIFEST = WEB / "assets" / "audio" / "neural_networks" / "lesson_02" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "neural_networks" / "lesson_02" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "neural_networks" / "lesson_02" / "experiments" / "3b1b_nn_02_full_dubbed.mp4"

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
VIDEO_ID = "IHZwWFHWa-w"
LESSON = "lesson_02"

# Silence margins: keep 0-2 s and the final 2 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Expansion policy constants. Video is ~2.49x the authored script, so aim higher
# than the 0.72 median floor to leave headroom after measurement.
EXPAND_TRIGGER_RATIO = 0.62          # expand when natural < 62% of window
EXPAND_TARGET_FILL = 0.80            # headroom above the 0.72 median floor
MAX_APPENDED_SENTENCES = 12
ACTIVE_THRESHOLD = 0.015             # waveform threshold for internal-gap scan

# Section-aware pedagogical sentences appended to short cues. Cycled, never
# repeated verbatim inside a single cue, chosen for real teaching value.
EXPANSION_POOL = {
    "sec-learning-paradox": [
        "এখানে লক্ষ্য করার কথা হলো, শেখা মানে কোনো রহস্যময় ঘটনা নয়—এটি কেবল কিছু সংখ্যার উপযুক্ত সমন্বয় খুঁজে বের করার গাণিতিক প্রক্রিয়া।",
        "এই ১৩,০০২টি ডায়াল একসাথে ঘুরিয়ে সঠিক ফলাফল পাওয়া অসম্ভব মনে হলেও, প্রতিটি ডায়ালের ছোট ছোট পরিবর্তনই শেষ পর্যন্ত কাজে আসে।",
        "মনে রাখবেন, ওজন ও বায়াসের এই সমাহারই পরবর্তীতে কস্ট ফাংশনের মাধ্যমে পরিমাপ করা হবে—তাই আগে কী ঠিক করতে হবে তা বোঝা জরুরি।",
    ],
    "sec-cost-function": [
        "লক্ষ্য করুন, প্রতিটি আউটপুট নিউরনের ভুলের বর্গ নেওয়ার কারণে ঋণাত্মক ও ধনাত্মক ভুল একে অপরকে বাতিল করতে পারে না।",
        "কস্ট ফাংশন আমাদের কেবল একটি সংখ্যা দেয়—এই একক সংখ্যাটিই বলে দেয় নেটওয়ার্কটি কতটা ভুল করছে এবং কোথায় গিয়ে সুধার আনা যায়।",
        "স্কয়ার্ড এরর ছাড়াও অন্যান্য লস ফাংশন আছে, কিন্তু বর্গের এই সূত্র আমাদের ঢালু ভূমির মতো একটি সুন্দর ল্যান্ডস্কেপ দেয়—যার উপর দিয়ে নামতে আমরা শিখব।",
    ],
    "sec-gradient-descent-intuition": [
        "কুয়াশাচ্ছন্ন পাহাড়ে চোখ বেঁধে নামার সময় আপনি কেবল পায়ের নিচের মাটির ঢাল অনুভব করে সবচেয়ে নিচের দিকে পা বাড়ান—এটিই গ্রেডিয়েন্ট ডিসেন্ট।",
        "ঋণাত্মক গ্রেডিয়েন্টের দিকে ছোট ছোট পা দিতে থাকলে কস্ট ক্রমশ কমতে থাকে; একই সাথে অনেক বড় পা দিলে আপনি উপত্যকা পেরিয়ে অন্য পাহাড়ে চলে যেতে পারেন।",
        "এই পুনরাবৃত্ত প্রক্রিয়াটিই শেখানোর মূল: বারবার কস্ট মাপুন, ঢালের দিকে এক ধাপ এগোন, আবার মাপুন—যতক্ষণ না কস্ট প্রায় স্থির হয়।",
    ],
    "sec-multivariable-gradient": [
        "একের বদলে ১৩,০০২টি মাত্রায় ঢাল মাপতে হলে প্রতিটি ওজনের জন্য আলাদা আংশিক ডেরাইভেটিভ বের করতে হয়—এদের নিয়েই গ্রেডিয়েন্ট ভেক্টর গঠিত।",
        "গ্রেডিয়েন্ট ভেক্টর আমাদের বলে দেয় কোন দিকে কস্ট সবচেয়ে দ্রুত বাড়ে; তাই ঠিক তার বিপরীত দিকে পা দিলেই আমরা সবচেয়ে দ্রুত নিচে নামি।",
        "মাত্রা বেশি হলেও ধারণা একই—প্রতিটি অক্ষে অল্প অল্প করে ঢাল অনুসরণ করে আমরা এই উঁচু-নিচু ল্যান্ডস্কেপে পথ খুঁজে পাই।",
    ],
    "sec-learning-rate-landscape": [
        "লার্নিং রেট খুব বড় হলে পা এত বড় হয় যে আপনি সবচেয়ে গভীর খাদের উপর দিয়ে উড়ে যান এবং কখনো নামতে পারেন না।",
        "আবার লার্নিং রেট খুব ছোট হলে নামা শুরু হয় কিন্তু শেষ পর্যন্ত পৌঁছাতে অনেক বেশি সময় লাগে—তাই সঠিক মাত্রা বাছা গুরুত্বপূর্ণ।",
        "অনেক সময় আমরা একটি স্থানীয় ন্যূনতম বা লোকাল মিনিমায় আটকে যাই, যা সার্ভারের সবচেয়ে গভীর গ্লোবাল মিনিমা নাও হতে পারে—এই সীমাবদ্ধতাও মনে রাখতে হবে।",
    ],
    "sec-mini-batch-sgd": [
        "পুরো ডেটাসেটের কস্ট বারবার হিসেব না করে আমরা ছোট ছোট মিনি-ব্যাচ নিয়ে একটিমাত্র ধাপ এগোনোকেই স্টোকাস্টিক গ্রেডিয়েন্ট ডিসেন্ট বলে।",
        "এই পদ্ধতিতে প্রতিটি ধাপে কিছুটা শব্দ বা নয়েজ থাকে, কিন্তু সেই নয়েজই মডেলকে শক্তিশালী করে এবং গণনা অনেক দ্রুত হয়।",
        "ব্যাচের আকার যত বড় হবে গ্রেডিয়েন্ট তত নির্ভুল হবে, কিন্তু প্রতি ধাপের খরচও তত বাড়বে—তাই গতি ও নির্ভুলতার মধ্যে একটি ভারসাম্য খুঁজতে হয়।",
    ],
}
DEFAULT_EXPANSIONS = [
    "এই ধারণাটি নিজের ভাষায় একবার বলে দেখলে বিষয়টি আরও পরিচ্ছন্ন হবে।",
    "লক্ষ্য করুন, কস্টের এই ছোট্ট পরিবর্তনই শেষ পর্যন্ত পুরো নেটওয়ার্কের শেখার দিক নির্ধারণ করে।",
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
    """Make Bengali cue text safe & pronounceable for Edge-TTS.

    The authored manifest embeds LaTeX/math tokens (\\mathbb{R}^{13002}, w_1,
    a_j, ^, braces) that would otherwise be spoken as gibberish. Convert the
    common ones to readable Bengali, then strip the rest.
    """
    t = text
    # Common LaTeX / math tokens -> readable Bengali or plain text.
    t = t.replace(r"\mathbb{R}", "আর")
    t = re.sub(r"\\to\b", " থেকে ", t)
    t = re.sub(r"\\in\b", " এর অন্তর্গত ", t)
    t = re.sub(r"\\times\b", " গুণ ", t)
    t = t.replace(r"\%", " শতাংশ ")
    t = t.replace("$", " ")
    # Strip any remaining backslash command names.
    t = re.sub(r"\\[A-Za-z]+", " ", t)
    # Math punctuation -> spaces / readable words.
    for ch in ["—", "–", "−", "-"]:
        t = t.replace(ch, ", ")
    t = t.replace("_", " ").replace("^", " ").replace("{", " ").replace("}", " ")
    for ch in ["'", '"', "[", "]", "*", "#", "`", "\\", "<", ">"]:
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
    """Read the PRIMARY master script. Its start/end/duration are in SECONDS."""
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
        dur_s = c.get("duration")
        if dur_s is None:
            dur_s = (float(c.get("end", 0)) - float(c.get("start", 0)))
        out.append({
            "text": text,
            "dur_ms": float(dur_s) * 1000.0,
            "section": str(c.get("section", "master")),
        })
    if out:
        return out, f"master_script:{mpath.name} (seconds->ms x1000)"
    return None, None


def load_manifest_cues():
    """Read the audio manifest at the EXPLICIT known path (read-only).

    The manifest stores each section twice in some lessons (canonical id +
    alias id) with identical cues; de-duplicate by section_id so cues are not
    doubled. duration_ms in the manifest is already milliseconds.
    """
    if not MANIFEST.exists():
        return None, None
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
    if out:
        return out, f"audio_manifest:{MANIFEST.name} (alias-deduped, ms as-is)"
    return None, None


def derive_from_lesson(lesson):
    """Last-resort cue derivation from the lesson JSON's rich text sections."""
    out = []
    for sec in lesson.get("sections", []):
        sec_id = sec.get("id") or sec.get("alias") or "section"
        texts = []
        for el in sec.get("elements", []):
            if isinstance(el, dict) and el.get("content"):
                texts.append(el["content"])
        q = sec.get("quote") or {}
        if q.get("text_bn"):
            texts.append(q["text_bn"])
        texts.extend(sec.get("paragraphs", []))
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
    """Return (list_of_{text,dur_ms,section}, source_description)."""
    out, desc = load_master_cues()
    if out:
        return out, desc
    out, desc = load_manifest_cues()
    if out:
        return out, desc
    lesson = json.loads(LESSON_JSON.read_text(encoding="utf-8"))
    return derive_from_lesson(lesson), "lesson_02.json:sections"


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
    natural TTS is short of its scaled window, then re-synthesize. Multiple
    rounds; section-aware sentences keep the additions meaningful.
    """
    expanded = []
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        target = float(c["duration"])
        natural = duration(raw)
        if natural <= 0 or natural >= EXPAND_TRIGGER_RATIO * target:
            continue
        pool = EXPANSION_POOL.get(c["section"], DEFAULT_EXPANSIONS)
        base = sanitize(c["bn"])
        added = 0
        before = natural
        while added < MAX_APPENDED_SENTENCES:
            need = (EXPAND_TARGET_FILL * MIN_TEMPO * target - natural)  # extra seconds
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

    print("[2/6] Expansion of short cues (IMPROVED_DUB_FILL_POLICY) ...", flush=True)
    expanded = await expand_short_cues(cues)
    print(f"  expanded {len(expanded)} cues", flush=True)

    print("[3/6] Absolute sample placement (start*44100, pad-only) ...", flush=True)
    # FULL-length canvas: -shortest can never trim the video.
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    CHUNK = 1_000_000
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    overrun = 0
    last_cue_end = 0.0
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
            "expanded": cid in [x["id"] for x in expanded],
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

    print("[4/6] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    fills = [x["fill"] for x in placed]
    median_fill = round(statistics.median(fills), 4) if fills else 0.0
    max_internal_gap = round(max((x["max_internal_gap_s"] for x in placed), default=0.0), 4)
    report = {
        "experiment": "clean_timesync_v2 (neural_networks_lesson_02 full-length, improved fill)",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": source_desc,
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": "absolute sample offset (start*44100); atempo fit floor 0.82; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "min_tempo": MIN_TEMPO,
        "max_tempo": MAX_TEMPO,
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
        "fill_policy": {
            "expand_trigger_ratio": EXPAND_TRIGGER_RATIO,
            "expand_target_fill": EXPAND_TARGET_FILL,
            "median_fill": median_fill,
            "median_fill_target": 0.72,
            "median_fill_ok": median_fill >= 0.72,
            "max_internal_gap_s": max_internal_gap,
            "max_internal_gap_target": 1.5,
            "max_internal_gap_ok": max_internal_gap <= 1.5,
        },
        "median_fill": median_fill,
        "max_internal_gap_s": max_internal_gap,
        "expanded_cues": expanded,
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

    print("[6/6] Lightweight volumedetect ...", flush=True)
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    odur = duration(OUT_VIDEO)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={report['output_duration_sec']}s size={report['output_size_bytes']}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap={max_internal_gap}s "
          f"expanded={len(expanded)}", flush=True)
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
