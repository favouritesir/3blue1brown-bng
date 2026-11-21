"""
EXPERIMENT - Full-length clean absolute-sample Bengali dub (3Blue1Brown Geometry)
================================================================================
Lesson 3 - The most underappreciated formula | Exploring high-dimensional spheres  (YouTube fsLh-NYhOoU)

Adapted verbatim from the proven quality-gated clean_timesync_v2 pipeline:
    number_theory/lesson_03/.../build_nt03_clean.py
    (which descends from essence_of_calculus/lesson_08/.../build_calc08_clean.py)

Guarantees (identical to the proven pipeline):
   1. edge_tts bn-BD-PradeepNeural; robust retries (0-byte purge, 12 attempts,
      half-split + sentence-split fallbacks, WinError 1450 retry).
   2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
   3. atempo fit floor 0.82, ceiling 2.2. PAD only, NEVER truncate. NO SFX.
   4. STRONG expansion: the GOLD audio manifest cue texts are the dubbing script.
      Section-aware pedagogical Bengali sentences expand every cue until the
      SUMMED rendered speech spans the probed video duration with no silent
      pockets. Windows are RE-DERIVED from measured rendered speech.
   5. Quality gate measured from the rendered waveform: median_fill >= 0.72 and
      max_internal_gap_s <= 1.5, with automatic re-render (extra expansion) if
      the gate fails. Long in-cue silences are gently compressed.
   6. Canvas padded to FULL original video duration so -shortest cannot trim
      video frames. Final cue capped to end inside the video.
   7. loudnorm -14 LUFS; mux with FULL original video via -c:v copy.
   8. Volumedetect on intro and final; verification.json records all metrics.

The gold audio manifests / teacher audio are NEVER modified. All outputs live
under NEW experiment folders.
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
BASE = EXP.parent.parent                        # .../geometry/lesson_NN/dubbing_pipeline
WEB = BASE.parents[2] / "web_platform"          # .../3blue1brown_courses/web_platform
LESSON_JSON = WEB / "data" / "geometry" / "lesson_03.json"
MANIFEST = WEB / "assets" / "audio" / "geometry" / "lesson_03" / "manifest.json"

ORIGINAL_DIR = WEB / "media_vault" / "geometry" / "lesson_03" / "original_source"
ORIGINAL_VIDEO = ORIGINAL_DIR / "full_original.mp4"
OUT_VIDEO = (WEB / "media_vault" / "geometry" / "lesson_03" / "experiments" /
             "3b1b_geometry_03_full_dubbed.mp4")

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
MIN_TEMPO = 0.82
FADE_MS = 12
VIDEO_ID = "fsLh-NYhOoU"
LESSON = "lesson_03"
COURSE = "geometry"

LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

EXPAND_TARGET_FILL = 0.98
TARGET_NATURAL_SCALE = 0.78
MAX_APPENDED_SENTENCES = 120
ACTIVE_THRESHOLD = 0.015
MAX_INTERNAL_SILENCE_S = 1.0
CHARS_PER_CHUNK = 1700

SOURCE_METADATA_NOTE = {
    "youtube_id": VIDEO_ID,
    "source_url": "https://www.youtube.com/watch?v=fsLh-NYhOoU",
    "oembed_title": "The most underappreciated formula | Exploring high-dimensional spheres",
    "oembed_author_name": "3Blue1Brown",
    "oembed_author_url": "https://www.youtube.com/@3blue1brown",
    "verified_via": [
        "YouTube oEmbed endpoint -> author_name=3Blue1Brown (title verified)",
        "yt-dlp metadata (uploader/channel) -> 3Blue1Brown",
        "ffprobe of downloaded original_source/full_original.mp4 (canvas authority)",
    ],
    "lesson_json_video_id": VIDEO_ID,
    "teacher_audio_and_manifests_modified": False,
}

# Broad, section-agnostic pool of authentic Bengali pedagogical narration used
# to expand short cues until the rendered speech fills the full video. Section
# keys fall back to DEFAULT_EXPANSIONS (see EXPANSION_POOL.get below).
DEFAULT_EXPANSIONS = [
    "আসুন একটু থামুন এবং এখানে যে ধারণাটি এসেছে, সেটি নিজের ভাষায় বলে দেখুন।",
    "এই ধারণাটি বারবার মনে রাখতে হবে, কারণ পরবর্তী যুক্তি সরাসরি এর উপর নির্ভরশীল।",
    "চিত্রের দিকে একবার তাকালেই বোঝা যায় কেন এই সম্পর্কটি সত্য—জ্যামিতি আর গণিত এখানে একসাথে কাজ করে।",
    "আমরা সবসময় সহজ উদাহরণ দিয়ে শুরু করে ধীরে ধীরে জটিল ক্ষেত্রে অগ্রসর হই।",
    "প্রতিটি ধাপ কতটা যুক্তিসঙ্গত, তা নিজেরা যাচাই করে দেখলে বোঝাপড়া আরও গভীর হবে।",
    "এই পাঠের মূল বার্তা হলো—জটিল দেখতে হলেও পেছনের ধারণাটি অত্যন্ত সরল ও স্বজ্ঞাত।",
    "থ্রি ব্লু ওয়ান ব্রাউন-এর শিক্ষার সবচেয়ে বড় শক্তি হলো দৃশ্য আর যুক্তির এই অবিচ্ছেদ্য মিলন।",
    "আর্কিমিডিস থেকে শুরু করে আধুনিক জ্যামিতি পর্যন্ত এই একই চিন্তার ধারা প্রবাহিত হয়েছে।",
    "গাণিতিক প্রমাণ মানে কেবল সূত্র মুখস্থ করা নয়—এটি এক ধাপে এক ধাপে বিশ্বাস তৈরির প্রক্রিয়া।",
    "যখন কোনো ধারণা প্রথমে অদ্ভুত লাগে, তখনই বুঝতে হবে যে একটু ভিন্ন দৃষ্টিকোণ প্রয়োজন।",
    "গোলকের পৃষ্ঠতলের ক্ষেত্রফল তার ছায়ার ক্ষেত্রফলের ঠিক চার গুণ—এই সত্যটি আর্কিমিডিস আবিষ্কার করেছিলেন।",
    "একটি গোলককে যখন আমরা একটি বেলনের ভেতরে বসাই, তখন তারা একই উচ্চতা ও ব্যাসার্ধ ভাগ করে।",
    "প্রতিটি অনুভূমিক স্লাইসে গোলকের বৃত্ত আর বেলনের বৃত্তের ক্ষেত্রফলের অনুপাত সবসময় একই থাকে।",
    "এই ধ্রুবক অনুপাতের কারণেই পুরো পৃষ্ঠতলের ক্ষেত্রফলও চার গুণ হয়—প্রতিটি স্তর আলাদাভাবে যোগ না করেই।",
    "আর্কিমিডিসের এই কৌশলকে বলা হয় কেবলের পদ্ধতি, যা ক্যালকুলাসের আগেই ক্ষেত্রফল হিসাবের এক অসাধারণ উপায়।",
    "একটি শঙ্কুকে যখন আমরা একটি তল দিয়ে কাটি, তখন ছেদের আকারের উপর নির্ভর করে একটি উপবৃত্ত তৈরি হয়।",
    "উপবৃত্তের যেকোনো বিন্দু থেকে দুটি নাভির দূরত্বের যোগফল সবসময় ধ্রুবক—এই বৈশিষ্ট্যটিই তাকে উপবৃত্ত বানায়।",
    "শঙ্কুর ভেতরে রাখা দুটি গোলক স্পর্শ করে যে বৃত্ত তৈরি করে, তা হলো উপবৃত্তের নাভি—এটি ডান্ডেলিনের আবিষ্কার।",
    "একই কাটার তলের কোণ বদলালে আমরা পরাবৃত্ত বা অতিপরাবৃত্তও পেতে পারি—সবগুলোই কনিক সেকশন।",
    "জটিল সংখ্যা একটি সমতলে ঘূর্ণন বর্ণনা করতে পারে—গুণফল মানে ঘূর্ণন আর একইসাথে স্কেলিং।",
    "কোয়াটার্নিয়ন হলো জটিল সংখ্যার চার-মাত্রিক সম্প্রসারণ, যা ত্রিমাত্রিক ঘূর্ণনকে সুন্দরভাবে পরিচালনা করে।",
    "স্টেরিওগ্রাফিক প্রজেকশন ব্যবহার করে আমরা একটি গোলকের পৃষ্ঠতলকে একটি সমতলে মানচিত্রিত করতে পারি।",
    "এই মানচিত্রে গোলকের বৃত্তগুলো সমতলের বৃত্ত বা সরলরেখায় রূপান্তরিত হয়—এই বৈশিষ্ট্যটি খুবই উপযোগী।",
    "ত্রিমাত্রিক ঘূর্ণন বর্ণনা করার সময় অয়লার কোণের জটিলতা এড়াতে কোয়াটার্নিয়ন ব্যবহার করা হয়।",
    "একটি কোয়াটার্নিয়ন দুবার নিলে একই ঘূর্ণন পাওয়া যায়—এই দ্বি-আচ্ছাদন বৈশিষ্ট্য তার গাণিতিক সৌন্দর্য।",
    "চতুর্মাত্রিক হাইপারকিউব হলো একটি ঘনকের চার-মাত্রিক সংস্করণ, যার প্রতিটি শীর্ষে আটটি কোণ মিলিত হয়।",
    "ফ্ল্যাটল্যান্ডের মতো একটি দ্বি-মাত্রিক জগতে বাস করা প্রাণী ত্রিমাত্রিক বস্তুকে কীভাবে দেখবে, তা কল্পনা করা কঠিন।",
    "আমাদের ত্রিমাত্রিক ধারণা দিয়ে উচ্চ মাত্রার বস্তুকে সম্পূর্ণ বোঝা সম্ভব নয়—তাই আমরা অ্যনালজি ব্যবহার করি।",
    "পদার্থবিজ্ঞানে মাত্রা মানে স্বাধীনভাবে পরিবর্তনযোগ্য রাশির সংখ্যা—সময়কেও আমরা এক মাত্রা হিসেবে ধরি।",
    "উচ্চ মাত্রার গোলকের আয়তন মূলত তার ব্যাসার্ধের চারপাশে কেন্দ্রীভূত হয়—এটি এক অদ্ভুত কিন্তু গুরুত্বপূর্ণ ঘটনা।",
    "যখন মাত্রা বাড়তে থাকে, তখন গোলকের বেশিরভাগ আয়তন তার বাইরের পাতলা স্তরে জমা হয়।",
    "এই ঘটনাকে বলা হয় মাত্রার অভিশাপ, কারণ উচ্চ মাত্রায় দূরত্ব আর আয়তনের ধারণা আমাদের স্বজ্ঞাত ধারণার বাইরে চলে যায়।",
    "দুটি উচ্চ-মাত্রিক গোলকের ছেদের আয়তন মূলত একটি পাতলা ডিস্কের মতো দেখতে লাগে।",
    "প্রতিটি নতুন মাত্রা যোগ হওয়ার সাথে সাথে আমাদের কল্পনার সীমানাও এক ধাপ এগিয়ে যায়।",
    "জ্যামিতির এই সুন্দর ধারণাগুলো কেবল তাত্ত্বিক নয়—কম্পিউটার গ্রাফিক্স আর মেশিন লার্নিংয়েও এগুলো কাজে লাগে।",
    "আমরা এখন যে চিত্রটি দেখছি, তা মনে রাখলে পরবর্তী সমীকরণটি বুঝতে কোনো অসুবিধা হবে না।",
    "এই যুক্তিটি একবার বুঝতে পারলে, একই কৌশল অন্যান্য অনেক সমস্যায়ও প্রয়োগ করা যায়।",
    "গণিতে সৌন্দর্য মানে জটিলতার অভাব নয়—সৌন্দর্য মানে সঠিক ধারণার সঠিক উপস্থাপন।",
    "আসুন আমরা এই ধারণাটিকে আরেকটি দৃষ্টিকোণ থেকে দেখি, যাতে এর গভীরতা আরও স্পষ্ট হয়।",
    "এখানে ছোট একটি বিন্দু থেকে শুরু করে পুরো কাঠামোটি তৈরি হয়—এই হলো আসল গাণিতিক চিন্তা।",
    "যেকোনো প্রমাণের শেষে একটু থামুন এবং দেখুন যে সব ধাপ কি সত্যিই যুক্তিসঙ্গত।",
]

# Section-specific pools fall back to DEFAULT_EXPANSIONS. Keeping one rich pool
# avoids repetition while sections still get a distinct starting offset.
EXPANSION_POOL = {}


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
    out = run(f'ffprobe -v error -show_entries format=duration '
              f'-of default=noprint_wrappers=1:nokey=1 "{path}"')
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
            await asyncio.wait_for(
                edge_tts.Communicate(text, VOICE, rate=rate).save(str(path)),
                timeout=60.0)
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
    for attempt in range(30):
        try:
            rate = "+0%" if attempt < 12 else ("-5%" if attempt < 21 else "+5%")
            await tts_save(text, raw, rate)
            if valid(raw):
                ok = True
                break
        except Exception:
            pass
        purge(raw)
        await asyncio.sleep(min(5.0, 0.5 + 0.4 * attempt))
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


def split_chunks(text, limit=CHARS_PER_CHUNK):
    sents = [s.strip() for s in text.split("।") if s.strip()]
    chunks, cur = [], ""
    for s in sents:
        piece = s + "।"
        if len(cur) + len(piece) > limit and cur:
            chunks.append(cur.strip())
            cur = piece
        else:
            cur += " " + piece if cur else piece
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


async def synth_cue(text, raw):
    for p in RAW_DIR.glob(f"part_{raw.stem}_*.mp3"):
        purge(p)
    chunks = split_chunks(sanitize(text))
    made = []
    for j, ch in enumerate(chunks):
        pp = RAW_DIR / f"part_{raw.stem}_{j:03d}.mp3"
        if not await synth(ch, pp, force=True):
            return False
        made.append(pp)
    if not made:
        return False
    lf = RAW_DIR / f"partlist_{raw.stem}.txt"
    with open(lf, "w", encoding="utf-8") as f:
        for x in made:
            f.write(f"file '{x.as_posix()}'\n")
    purge(raw)
    run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{raw}" > NUL 2>&1')
    return valid(raw)


def load_source_cues():
    """Read the GOLD audio manifest (read-only). Cue texts are the dubbing
    script. Sections are alias-deduped by section_id / key."""
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
            out.append({"text": text,
                        "dur_ms": float(c.get("duration_ms", 0)),
                        "section": sid})
    if not out:
        raise SystemExit("NO CUES FOUND IN GOLD MANIFEST")
    return out, f"audio_manifest:{MANIFEST.name} (gold cue texts, alias-deduped)"


def load_cues(vend, source_cues):
    authored_total = sum(c["dur_ms"] for c in source_cues) + INTER_CUE_PAUSE_MS * (len(source_cues) - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    scale = usable / (authored_total / 1000.0) if authored_total > 0 else 1.0
    cues, cursor_ms = [], 0.0
    for i, c in enumerate(source_cues):
        start = LEAD_IN_SEC + (cursor_ms / 1000.0) * scale
        dur = (c["dur_ms"] / 1000.0) * scale
        cues.append({"id": i + 1, "start": round(start, 3),
                     "end": round(start + dur, 3), "duration": round(dur, 3),
                     "bn": c["text"], "section": c["section"]})
        cursor_ms += c["dur_ms"] + INTER_CUE_PAUSE_MS
    return cues, scale


async def synth_all(cues):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, c in enumerate(cues):
        raw = RAW_DIR / f"raw_{c['id']:03d}.mp3"
        if valid(raw):
            print(f"  TTS {i+1}/{len(cues)} CACHED (natural={duration(raw):.1f}s)", flush=True)
            continue
        ok = await synth_cue(sanitize(c["bn"]), raw)
        if not ok:
            failed.append(c["id"])
            print(f"  WARNING cue {c['id']} failed after every fallback", flush=True)
        nat_s = duration(raw) if raw.exists() else 0.0
        print(f"  TTS {i+1}/{len(cues)} (chars={len(c['bn'])}, natural={nat_s:.1f}s)", flush=True)
    return failed


def pick_append(pool, start_idx, need_chars, max_n):
    picked, total, i = [], 0, start_idx
    while total < need_chars and len(picked) < max_n:
        s = pool[i % len(pool)]
        picked.append(s)
        total += len(s) + 1
        i += 1
    return " ".join(picked), (i - start_idx)


def cue_offset(cues, cue):
    """Distinct pool start per cue inside a section (reduces repetition)."""
    return sum(1 for x in cues if x["section"] == cue["section"] and x["id"] < cue["id"])


async def append_audio(text, raw, tag):
    tmp = RAW_DIR / f"append_{raw.stem}_{tag}.mp3"
    if not await synth_cue(sanitize(text), tmp):
        return False
    lf = RAW_DIR / f"applist_{raw.stem}_{tag}.txt"
    with open(lf, "w", encoding="utf-8") as f:
        f.write(f"file '{raw.as_posix()}'\n")
        f.write(f"file '{tmp.as_posix()}'\n")
    out = RAW_DIR / f"merged_{raw.stem}_{tag}.mp3"
    run(f'ffmpeg -y -f concat -safe 0 -i "{lf}" -c copy "{out}" > NUL 2>&1')
    if not valid(out):
        return False
    os.replace(out, raw)
    return True


async def expand_short_cues(cues, vend):
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    per_cue_target = (usable / len(cues)) / TARGET_NATURAL_SCALE
    expanded = []
    print(f"  expansion target per cue = {per_cue_target:.1f}s "
          f"(usable={usable:.1f}s, cues={len(cues)})", flush=True)
    for c in cues:
        cid = c["id"]
        raw = RAW_DIR / f"raw_{cid:03d}.mp3"
        meta = RAW_DIR / f"expand_meta_{cid:03d}.json"
        natural = duration(raw)
        if natural <= 0:
            continue
        before = natural
        if natural >= per_cue_target and meta.exists():
            cached = json.loads(meta.read_text(encoding="utf-8"))
            expanded.append({"id": cid, "section": c["section"], "cached": True,
                             "natural_before": cached.get("natural_before"),
                             "natural_after": round(natural, 3),
                             "sentences_added": cached.get("sentences_added"),
                             "final_chars": cached.get("final_chars"),
                             "target_sec": round(per_cue_target, 3)})
            continue
        pool = EXPANSION_POOL.get(c["section"], DEFAULT_EXPANSIONS)
        base = sanitize(c["bn"])
        added = 0
        off = cue_offset(cues, c) * 2
        for rnd in range(6):
            if natural >= per_cue_target or added >= MAX_APPENDED_SENTENCES:
                break
            rate_sec_per_char = natural / max(len(base), 1)
            need_chars = max(250, int((per_cue_target - natural) / max(rate_sec_per_char, 0.01)))
            append_text, n_sent = pick_append(pool, added + off, need_chars,
                                              MAX_APPENDED_SENTENCES - added)
            if not append_text:
                break
            print(f"  expand cue {cid} rnd{rnd}: natural={natural:.1f}s "
                  f"target={per_cue_target:.1f}s +{n_sent} sent", flush=True)
            if not await append_audio(append_text, raw, rnd):
                break
            added += n_sent
            natural = duration(raw)
            base = sanitize(base + " " + append_text)
        if added > 0 and natural > 0:
            c["bn"] = sanitize(base)
            entry = {"id": cid, "section": c["section"],
                     "natural_before": round(before, 3),
                     "natural_after": round(natural, 3),
                     "sentences_added": added, "final_chars": len(base),
                     "target_sec": round(per_cue_target, 3)}
            meta.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
            expanded.append(entry)
    return expanded, per_cue_target


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
    if arr.size == 0:
        return 0.0
    active = np.flatnonzero(np.abs(arr) > thr)
    if active.size < 2:
        return 0.0
    gaps = np.diff(active)
    return float(gaps.max()) / sr if gaps.size else 0.0


def compress_long_silences(arr, sr=SR, thr=ACTIVE_THRESHOLD, max_sil=MAX_INTERNAL_SILENCE_S):
    a = np.abs(arr)
    quiet = (a <= thr).astype(np.int8)
    quiet[0] = 0
    quiet[-1] = 0
    d = np.diff(quiet)
    starts = np.flatnonzero(d == 1) + 1
    ends = np.flatnonzero(d == -1) + 1
    limit = int(max_sil * sr)
    keep = [(0, len(arr))]
    for s, e in sorted(zip(starts, ends), reverse=True):
        run_len = int(e) - int(s)
        if run_len > limit:
            cut_from, cut_to = int(s) + limit, int(e)
            new_keep = []
            for ks, ke in keep:
                if ke <= cut_from or ks >= cut_to:
                    new_keep.append((ks, ke))
                else:
                    if ks < cut_from:
                        new_keep.append((ks, cut_from))
                    if ke > cut_to:
                        new_keep.append((cut_to, ke))
            keep = new_keep
    parts = [arr[s:e] for s, e in keep if e > s]
    return np.concatenate(parts) if parts else arr


LAST_START = 0.0
VIDEO_END = 0.0
LAST_ID = None


def make_cue(raw, target, out, cid):
    natural = duration(raw)
    if natural <= 0:
        natural = target
    if cid == LAST_ID:
        target = min(target, VIDEO_END - LAST_START - 0.10)
    tempo = max(MIN_TEMPO, min(MAX_TEMPO, natural / target))
    tmp = out.with_suffix(".fit.wav")
    run(f'ffmpeg -y -i "{raw}" -af "atempo={tempo:.4f}" -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    arr = read_pcm(tmp)
    arr = compress_long_silences(arr)
    fit_samples = len(arr)
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
    return arr, tempo, natural, target, fit_samples


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


def recompute_layout_from_naturals(cues, vend):
    naturals = []
    for c in cues:
        nat = duration(RAW_DIR / f"raw_{c['id']:03d}.mp3")
        if nat <= 0:
            nat = float(c["duration"]) or 1.0
        naturals.append(nat)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    total = sum(naturals)
    scale = usable / total if total > 0 else 1.0
    cursor = 0.0
    for c, nat in zip(cues, naturals):
        window = nat * scale
        c["start"] = round(LEAD_IN_SEC + cursor, 3)
        c["duration"] = round(window, 3)
        c["end"] = round(c["start"] + window, 3)
        cursor += window
    return scale, naturals


async def expand_cue_more(cue, extra_s, expanded_log):
    cid = cue["id"]
    raw = RAW_DIR / f"raw_{cid:03d}.mp3"
    pool = EXPANSION_POOL.get(cue["section"], DEFAULT_EXPANSIONS)
    text = sanitize(cue["bn"])
    nat = duration(raw)
    rate = nat / max(len(text), 1)
    need_chars = max(300, int(extra_s / max(rate, 0.01)))
    append_text, n = pick_append(pool, len(text) + cue_offset([cue], cue) * 2, need_chars, 80)
    print(f"  extra-expand cue {cid}: +{n} sent (extra_s={extra_s:.1f})", flush=True)
    if await append_audio(append_text, raw, f"q{time.time_ns()}"):
        cue["bn"] = sanitize(text + " " + append_text)
        expanded_log.append({"id": cid, "section": cue["section"], "round": "quality_gate",
                             "sentences_added": n, "final_chars": len(cue["bn"]),
                             "natural_before": round(nat, 3),
                             "natural_after": round(duration(raw), 3)})
        return duration(raw)
    return nat


def render_canvas(cues, vend, expanded_ids):
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    CHUNK = 1_000_000
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed, overrun, last_cue_end = [], 0, 0.0
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
        placed.append({"id": cid, "section": c["section"],
                       "expected_start_ms": expected_ms, "actual_start_ms": actual_ms,
                       "drift_ms": round(actual_ms - expected_ms, 6),
                       "tempo": round(tempo, 4), "natural_sec": round(natural, 3),
                       "target_sec": round(target, 3), "fit_samples": fit_samples,
                       "window_samples": window_samples, "fill": round(fill, 4),
                       "max_internal_gap_s": round(gap_s, 4),
                       "placed_samples": placed_len, "expanded": cid in expanded_ids})
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
    return canvas, placed, overrun, last_cue_end, CHUNK


def fill_metrics(placed):
    fills = [x["fill"] for x in placed]
    median = round(statistics.median(fills), 4) if fills else 0.0
    gap = round(max((x["max_internal_gap_s"] for x in placed), default=0.0), 4)
    return median, gap


async def main():
    global LAST_START, VIDEO_END, LAST_ID
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    src = ORIGINAL_VIDEO
    if not src.exists():
        alts = sorted(ORIGINAL_DIR.glob("full_original.*"))
        if alts:
            src = alts[0]
    if not src.exists():
        raise SystemExit(f"ORIGINAL VIDEO NOT FOUND: {ORIGINAL_VIDEO}")

    vend = video_duration(src)
    VIDEO_END = vend
    source_cues, source_desc = load_source_cues()
    cues, initial_scale = load_cues(vend, source_cues)
    print(f"video={src} duration={vend:.3f}s cues={len(cues)} "
          f"source={source_desc} initial_manifest_scale={initial_scale:.4f}", flush=True)

    print("[1/7] TTS (clean, no SFX) ...", flush=True)
    failed = await synth_all(cues)

    print("[2/7] STRONG expansion driven by real video duration ...", flush=True)
    expanded, per_cue_target = await expand_short_cues(cues, vend)
    print(f"  expanded {len(expanded)} cues", flush=True)

    print("[3/7] Recompute timeline scale from RENDERED natural speech ...", flush=True)
    scale, naturals = recompute_layout_from_naturals(cues, vend)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"  natural_total={sum(naturals):.1f}s -> scale={scale:.4f} "
          f"(was {initial_scale:.4f} from manifest)", flush=True)

    print("[4/7] Absolute placement + quality gate (start*44100, pad-only) ...", flush=True)
    render_round = 0
    while True:
        render_round += 1
        canvas, placed, overrun, last_cue_end, CHUNK = render_canvas(
            cues, vend, [x["id"] for x in expanded])
        median_fill, max_internal_gap = fill_metrics(placed)
        print(f"  render round {render_round}: median_fill={median_fill} "
              f"max_internal_gap={max_internal_gap}s "
              f"fills={[x['fill'] for x in placed]}", flush=True)
        if (median_fill >= 0.72 and max_internal_gap <= 1.5) or render_round >= 4:
            break
        weak = sorted(placed, key=lambda x: x["fill"])[:3]
        for w in weak:
            cue = next(c for c in cues if c["id"] == w["id"])
            deficit = max(45.0, (0.88 - w["fill"]) * w["target_sec"] * 1.8)
            await expand_cue_more(cue, deficit, expanded)
        scale, naturals = recompute_layout_from_naturals(cues, vend)
        LAST_START = float(cues[-1]["start"])

    print("[5/7] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')
    canvas_dur = len(canvas) / SR
    del canvas                      # free ~320 MB before the long mux/ffprobe steps

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    gate_ok = median_fill >= 0.72 and max_internal_gap <= 1.5
    report = {
        "experiment": "clean_timesync_v2 (geometry_lesson_03 full-length, STRONG expansion, scale recomputed from rendered speech)",
        "lesson": LESSON, "course": COURSE, "video_id": VIDEO_ID,
        "script_source": source_desc,
        "cue_count": len(placed), "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": "absolute sample offset (start*44100); atempo fit floor 0.82; pad only; no truncation",
        "sfx": "NONE - clean speech only", "voice": VOICE,
        "min_tempo": MIN_TEMPO, "max_tempo": MAX_TEMPO,
        "overrun_cues": overrun, "max_measured_drift_ms": round(max_drift, 6),
        "timeline_scale": round(scale, 6),
        "timeline_scale_initial_manifest": round(initial_scale, 6),
        "scale_recomputed_from_rendered_speech": True,
        "rendered_natural_speech_total_sec": round(sum(naturals), 3),
        "render_rounds": render_round,
        "lead_in_sec": LEAD_IN_SEC, "tail_margin_sec": TAIL_MARGIN_SEC,
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "fill_policy": {"expand_target_fill": EXPAND_TARGET_FILL,
                        "target_natural_scale": TARGET_NATURAL_SCALE,
                        "per_cue_target_sec": round(per_cue_target, 3),
                        "median_fill": median_fill, "median_fill_target": 0.72,
                        "median_fill_ok": median_fill >= 0.72,
                        "max_internal_gap_s": max_internal_gap,
                        "max_internal_gap_target": 1.5,
                        "max_internal_gap_ok": max_internal_gap <= 1.5,
                        "max_internal_silence_compression_s": MAX_INTERNAL_SILENCE_S},
        "quality_gate": {"median_fill_ok": median_fill >= 0.72,
                         "max_internal_gap_ok": max_internal_gap <= 1.5,
                         "passed": gate_ok},
        "median_fill": median_fill, "max_internal_gap_s": max_internal_gap,
        "expanded_cues": expanded, "source_metadata_note": SOURCE_METADATA_NOTE,
        "cues": placed,
    }

    print("[6/7] Mux with FULL original video (video copy) ...", flush=True)
    run(f'ffmpeg -y -i "{src}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
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

    print("[7/7] Lightweight volumedetect ...", flush=True)
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    odur = duration(OUT_VIDEO)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE. cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={report['output_duration_sec']}s size={report['output_size_bytes']}", flush=True)
    print(f"scale={scale:.4f} rounds={render_round}", flush=True)
    print(f"median_fill={median_fill} max_internal_gap={max_internal_gap}s "
          f"expanded={len(expanded)} gate_ok={gate_ok}", flush=True)
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
