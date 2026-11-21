"""
EXPERIMENT — Full-length clean absolute-sample Bengali dub
(Essence of Probability, Lesson 02 — "Bayes' Rule and the False Positive Paradox")

Adapted verbatim from the proven clean_timesync_v2 pipeline:
  probability/lesson_01/dubbing_pipeline/experiments/clean_timesync_v2/build_prob01_clean.py

Guarantees (identical to the proven pipeline, plus IMPROVED_DUB_FILL_POLICY.md):
   1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
      half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
   2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
   3. IMPROVED FILL: atempo floor 0.82 (gentle slowdown), ceiling 2.2. Pad only,
      NEVER truncate. NO SFX: clean speech only.
   4. EXPANSION FIRST: any cue whose natural TTS is < 62% of its (scaled) window
      gets 1..N pedagogical Bengali sentences appended and is re-synthesized,
      until predicted fill >= 0.82 (policy requires median_fill >= 0.72 and
      max internal gap <= 1.5 s; 0.82 gives headroom above the floor).
      Section-aware sentence pools keep the additions pedagogically meaningful
      rather than generic filler.
   5. Fill metrics (per-cue fill, median_fill, max_internal_gap_s) are measured
      from the rendered waveform and written into verification.json.
   6. Canvas padded to the FULL original video duration (tail expansion) so
      -shortest can never trim video frames; final cue window is capped to end
      inside the video.
   7. loudnorm -14 LUFS; mux with the FULL original video via -c:v copy.
   8. Lightweight volumedetect (-vn -nostats, log to FILE) on intro 0-2s and
      the final 2s, written into verification.json.

Cue source (read-only; teacher audio / manifests are NEVER modified):
   1. web_platform/assets/audio/probability/lesson_02/manifest.json (PRIMARY)
      -- cue texts, alias-deduped by section_id. duration_ms is MILLISECONDS.
   2. probability/lesson_02/dubbing_pipeline/*master_script*.json (fallback only)
      -- if present, start/end/duration in SECONDS are converted x1000 to ms.
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
BASE = EXP.parent.parent                        # .../probability/lesson_02/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "probability" / "lesson_02.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "probability" / "lesson_02" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "probability" / "lesson_02" / "experiments" / "3b1b_prob_02_full_dubbed.mp4"

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
VIDEO_ID = "lG4VkPoG3ko"             # FIXED: verified via oEmbed as
                                      # "The medical test paradox, and redesigning Bayes' rule"
LESSON = "lesson_02"

# Silence margins: keep 0-2 s and the final 2 s free of speech.
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Expansion policy constants.
EXPAND_TRIGGER_RATIO = 0.62          # expand when natural < 62% of window
EXPAND_TARGET_FILL = 0.82            # > 0.72 policy floor (headroom)
MAX_APPENDED_SENTENCES = 8
ACTIVE_THRESHOLD = 0.015             # waveform threshold for internal-gap scan

# Section-aware pedagogical sentences appended to short cues. Cycled, never
# repeated verbatim inside a single cue, and chosen so the teaching value is
# real (what to notice / why it matters) rather than filler.
EXPANSION_POOL = {
    "sec-puzzle": [
        "এখানে লক্ষ্য করুন, টেস্টের নির্ভুলতা এবং পজিটিভ ফলের পর রোগ থাকার সম্ভাবনা—এ দুটি সম্পূর্ণ আলাদা সংখ্যা।",
        "সংবেদনশীলতা মানে রোগ থাকলে টেস্টের সঠিক পজিটিভ দেওয়ার হার, আর নির্দিষ্টতা মানে সুস্থ মানুষের সঠিক নেগেটিভ দেওয়ার হার।",
        "প্রাইয়র বা পূর্ব সম্ভাবনা হলো নতুন কোনো প্রমাণ পাওয়ার আগে রোগের স্বাভাবিক হার।",
        "তাই ৯৯ শতাংশ নির্ভুল টেস্টের পজিটিভ ফল দেখে ৯৯ শতাংশ রোগ আছে বলে সিদ্ধান্ত নেওয়া এক ধরনের ভুল।",
        "এই ধাঁধার চাবিকাঠি হলো: আমরা টেস্টের দিকে তাকাই, কিন্তু রোগের বিরলতা বা বেস রেট ভুলে যাই।",
    ],
    "sec-base-rate": [
        "এক হাজার মানুষের দলে মাত্র একজন আক্রান্ত—এই ছোট সংখ্যাটিই পুরো হিসাবের ভিত্তি।",
        "নয়শত নিরানব্বইজন সুস্থ মানুষের মাত্র এক শতাংশ ভুল পজিটিভ মানেই প্রায় দশজন ভুল পজিটিভ রিপোর্ট।",
        "আক্রান্ত একজন থেকে পাওয়া যায় প্রায় একজন ট্রু পজিটিভ, আর সুস্থদের থেকে আসে প্রায় দশজন ফলস পজিটিভ।",
        "সুতরাং মোট এগারোজন পজিটিভের মধ্যে মাত্র একজনই সত্যি আক্রান্ত—অর্থাৎ প্রায় নয় শতাংশ।",
        "বেস রেট ফ্যালাসি মানেই বিরল ঘটনার পূর্ব সম্ভাবনাকে উপেক্ষা করে শক্তিশালী প্রমাণে বিভ্রান্ত হওয়া।",
    ],
    "sec-grid-partition": [
        "বৃক্ষচিত্রের প্রতিটি শাখা আসলে একটি করে যৌথ ক্ষেত্রফলের প্রতিনিধিত্ব করে।",
        "বামদিকের সরু স্ট্রিপের ৯৯ শতাংশ উচ্চতার ক্ষেত্রফলের চেয়ে ডানদিকের চওড়া স্ট্রিপের এক শতাংশ উচ্চতার ক্ষেত্রফল প্রায় দশ গুণ বড়।",
        "ক্ষেত্রফল গ্রিডে শর্তারোপ মানেই অপ্রয়োজনীয় অংশ কেটে কেবল পজিটিভ অঞ্চল রেখে দেওয়া।",
        "সুতরাং পোস্টেরিয়র সম্ভাবনা হলো নতুন সংকুচিত মহাবিশ্বে আক্রান্ত অঞ্চলের আপেক্ষিক ক্ষেত্রফল।",
        "সিমুলেটরে রোগের বিস্তার বাড়ালে ট্রু পজিটিভের সংখ্যা বেড়ে ফলস পজিটিভের প্রভাব কমে যায়।",
    ],
    "sec-formula": [
        "শর্তাধীন সম্ভাবনার সংজ্ঞা থেকে শুরু করে যৌথ সম্ভাবনার গুণন নীতি—এই দুটিকে একত্র করলেই বেজের সূত্র তৈরি হয়।",
        "লবটি আসলে আক্রান্ত হওয়া এবং পজিটিভ ফল আসার যৌথ সম্ভাবনা।",
        "হরটি হলো সমগ্র সম্ভাব্যতা নীতি অনুযায়ী সব উৎস থেকে আসা পজিটিভের মোট ক্ষেত্রফল।",
        "প্রাইয়র, লাইকলিহুড, মার্জিনাল এবং পোস্টেরিয়র—এই চারটি ধারণা বেজিয়ান দর্শনের ভিত্তি।",
        "আজকের পোস্টেরিয়রই হলো আগামীকালের প্রাইয়র; একের পর এক প্রমাণ যোগ করে বিশ্বাস হালনাগাদ হয়।",
    ],
}
DEFAULT_EXPANSIONS = [
    "এই ধারণাটি নিজের ভাষায় একবার বলে দেখলে বিষয়টি আরও পরিচ্ছন্ন হবে।",
    "লক্ষ্য করুন, ক্ষেত্রফলের এই অনুপাতই আমাদের আসল উত্তরের দিকে নিয়ে যায়।",
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


def load_master_cues():
    """FALLBACK master script. Its start/end/duration are in SECONDS (x1000 -> ms)."""
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
            dur_s = float(c.get("end", 0)) - float(c.get("start", 0))
        out.append({
            "text": text,
            "dur_ms": float(dur_s) * 1000.0,   # SECONDS -> MILLISECONDS
            "section": str(c.get("section", "master")),
        })
    if out:
        return out, f"master_script:{mpath.name} (seconds->ms x1000)"
    return None, None


def load_manifest_cues(lesson):
    """Read the audio_manifest referenced by lesson_02.json (read-only).

    SECONDS-vs-MILLISECONDS CHECK: the manifest stores duration_ms in
    MILLISECONDS (values like 3144.0). We assert this explicitly so a future
    unit change cannot silently shrink the timeline by 1000x.

    The manifest stores each section twice (canonical id + alias id) with
    identical cues; de-duplicate by section_id so cues are not doubled.
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
            # MILLISECONDS — never multiply, never divide here.
            dur_ms = float(c.get("duration_ms", 0))
            out.append({
                "text": text,
                "dur_ms": dur_ms,
                "section": sid,
            })
    if out:
        med = statistics.median([c["dur_ms"] for c in out])
        if med < 500.0:
            raise RuntimeError(
                f"UNIT ERROR: manifest {manifest.name} median duration_ms={med} "
                f"looks like SECONDS, expected MILLISECONDS")
        return out, f"audio_manifest:{manifest.name} (alias-deduped, ms verified)"
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
    """Return (list_of_{text,dur_ms,section}, source_description).

    PRIMARY source is the manifest cue texts (alias-deduped) as required.
    """
    lesson = json.loads(LESSON_JSON.read_text(encoding="utf-8"))
    out, desc = load_manifest_cues(lesson)
    if out:
        return out, desc
    out, desc = load_master_cues()
    if out:
        return out, desc
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
        current = sanitize(c["bn"])
        added = 0
        before = natural
        while added < MAX_APPENDED_SENTENCES:
            need = (EXPAND_TARGET_FILL * MIN_TEMPO * target - natural)  # extra seconds
            if need <= 0:
                break
            extra_chars = max(60, int(need / max(natural, 0.1) * len(current)))
            n_sent = max(1, min(MAX_APPENDED_SENTENCES - added,
                                int(np.ceil(extra_chars / 95.0))))
            append_text = " ".join(pool[(added + j) % len(pool)] for j in range(n_sent))
            # ACCUMULATE: each round must build on the previous expanded text,
            # never replace it, so the audio and the recorded script stay in sync
            # and fill grows monotonically.
            new_text = sanitize(current + " " + append_text)
            print(f"  expand cue {cid}: fill {predicted_fill(natural, target):.2f} "
                  f"natural={natural:.2f}s target={target:.2f}s +{n_sent} sent", flush=True)
            if await synth(new_text, raw, force=True):
                added += n_sent
                current = new_text
                natural = duration(raw)
                if predicted_fill(natural, target) >= EXPAND_TARGET_FILL:
                    break
            else:
                break
        if added > 0 and natural > 0:
            c["bn"] = current
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

    if not ORIGINAL_VIDEO.exists():
        raise RuntimeError(f"ORIGINAL_VIDEO missing: {ORIGINAL_VIDEO}")

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
            # TAIL EXPANSION: grow canvas if a cue would run past the video.
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
        "experiment": "clean_timesync_v2 (probability_lesson_02 full-length, improved fill)",
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
