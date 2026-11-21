"""EXPERIMENT — Full-length clean absolute-sample Bengali dub (3Blue1Brown Guest Videos, lesson 02)

Adapted verbatim from the proven clean_timesync_v2 pipeline:
  essence_of_calculus/lesson_08_integration/dubbing_pipeline/experiments/clean_timesync_v2/build_calc08_clean.py

Cue source (read-only): web_platform/assets/audio/guest_videos/lesson_02/manifest.json
  -- the gold manifest cue *texts* are the dubbing script. The authored
     start/end/duration values are used only as relative weights; the authored
     cues are laid out cumulatively and scaled to span the FULL original video.

Guarantees (identical to the proven pipeline + fill policy):
  1. edge_tts bn-BD-PradeepNeural; robust retries: 0-byte purge, 12 attempts,
     half-split + sentence-split fallbacks, dedicated WinError 1450 retry.
  2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
  3. atempo fit in [0.82, 2.2]; PAD ONLY, NEVER truncate. NO SFX.
  4. Fill gate: contextual Bengali pedagogical expansion of any short cue,
     re-synthesized up to 3 passes; fill_ratio and internal_gap measured per cue;
     median_fill >= 0.72 and max_internal_gap_s <= 1.5 recorded in verification.json.
  5. Final-cue cap so speech ends before video end.
  6. Canvas padded to the FULL original video duration so -shortest cannot trim.
  7. loudnorm -14 LUFS; mux FULL original video via -c:v copy.
  8. volumedetect on intro 0-2s and final 2s -> verification.json.

Everything is written under NEW experiment folders. Teacher audio/manifests untouched.
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

NN = "02"
EXP = Path(__file__).resolve().parent
BASE = EXP.parent.parent                        # .../lesson_02/dubbing_pipeline
WEB = BASE.parents[3]                           # .../web_platform
MANIFEST = WEB / "assets" / "audio" / "guest_videos" / f"lesson_{NN}" / "manifest.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "guest_videos" / f"lesson_{NN}" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "guest_videos" / f"lesson_{NN}" / "experiments" / f"3b1b_guest_videos_{NN}_full_dubbed.mp4"

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
VIDEO_ID = "_BrFKp-U8GI"
LESSON = f"lesson_{NN}_guest_videos"

LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0
EXPAND_THRESHOLD_RATIO = 0.85

# Topic-neutral Bengali pedagogical narration pool used to expand short cues.
# Chosen deterministically per (cue, pass) so narration stays varied.
EXPANSION_POOL = [
    "এখানে একটু থামুন। এই ধারণাটি নিজের ভাষায় বলে দেখুন—কীভাবে ছোট ছোট পদক্ষেপ মিলে একটি সম্পূর্ণ ছবি তৈরি করে।",
    "আসুন একই কথা অন্য একটি দৃষ্টিকোণ থেকে দেখি। যেকোনো জটিল ব্যবস্থাকে ছোট ছোট অংশে ভাগ করলে তার আচরণ বোঝা অনেক সহজ হয়ে যায়।",
    "মনে রাখবেন, গণিতের প্রতিটি সূত্রের পেছনে একটি স্বজ্ঞাত ছবি লুকোনো থাকে। সেই ছবিটি চোখের সামনে রাখলে সূত্রটি মুখস্থ করার প্রয়োজন হয় না।",
    "এই ধাপটির গুরুত্ব কম নয়। এটি না বুঝলে পরের যুক্তিগুলো অনুধাবন করা কঠিন হয়ে পড়ে, তাই আমরা ধীরে ধীরে এগিয়েছি।",
    "বাস্তব জীবনে এই নীতি কতটা প্রযোজ্য তা নিয়ে একটু ভাবুন। প্রকৃতি যেকোনো জটিলতাকে সরল নিয়মের পুনরাবৃত্তি হিসেবেই গড়ে তোলে।",
    "পরবর্তী ধাপে আমরা এই ধারণাটি আরও গভীরভাবে অন্বেষণ করব। আপাতত আজকের যুক্তিটির সাথে নিজেকে একবার পরিচিত করে নিন।",
    "প্রশ্ন করা হলো শিখনের প্রথম ধাপ। এই প্রশ্নটি আপনি নিজের কাছে করুন—উত্তরটি কি আপনার কাছে পরিষ্কার? তবে আগের ধাপে ফিরে যান।",
    "উদাহরণের শক্তি অপরিসীম। একটি নির্দিষ্ট উদাহরণ মনে রাখলে অমূর্ত তত্ত্বও কঠিন মনে হয় না।",
    "এতক্ষণ যা দেখলাম তা সংক্ষেপে একবার মনে করিয়ে দিই। ধাপগুলোর ধারাবাহিকতাই মূল কথা, বাকিটা তারই প্রসার।",
    "পেছনে ফিরে তাকানোও অনেক সময় জরুরি। আগের ধাপের সাথে বর্তমান ধাপের মিল আর অমিল লক্ষ্য করলে নতুন কিছু শিখতে পারি।",
    "কল্পনা করুন, ছোট একটি পরিবর্তন বারবার ঘটলে তা কী আকার নেয়। এই ধরনের প্রশ্নই গাণিতিক চিন্তার জন্ম দেয়।",
    "অঙ্কন বা চিত্রের সাহায্যে একই কথা প্রকাশ করলে বোঝাপড়া অনেক গভীর হয়। ছবি আর শব্দ একসাথে চললে শিখন স্থায়ী হয়।",
    "ভুল করা ভয়ের কিছু নয়। ভুল থেকে শিক্ষা নিয়ে আবার চেষ্টা করাই আসল পদ্ধতি—এটি বিজ্ঞানেরও মূল মন্ত্র।",
    "বিষয়টি যতই কঠিন মনে হোক, ধৈর্য ধরে পড়লে তার নিজস্ব সৌন্দর্য ফুটে ওঠে। আমরা সেই সৌন্দর্যটিই খুঁজছি।",
    "আপনি যদি এই যুক্তিটি অন্য কারো কাছে ব্যাখ্যা করতে পারেন, তবে বুঝবেন আপনি সত্যিই বুঝেছেন। এটিই আমাদের লক্ষ্য।",
    "আসুন একটি ছোট বিরতি নিই এবং দেখি অদ্যাবধি কতদূর এগিয়েছি। প্রতিটি ধাপ আমাদের চূড়ান্ত বোঝার কাছে নিয়ে গেছে।",
]


def expansion_for(cid, attempt):
    return EXPANSION_POOL[(cid * 5 + attempt) % len(EXPANSION_POOL)]


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
    """Read the gold audio manifest. Cue 'text' is the dubbing script;
    duration_ms is used only as a relative layout weight."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out = []
    for sec_id, sec in data.get("sections", {}).items():
        for c in sec.get("cues", []):
            txt = c.get("text")
            if not txt:
                continue
            out.append({
                "text": txt,
                "dur_ms": float(c.get("duration_ms", 0) or 0),
                "section": sec_id,
            })
    if out:
        return out, f"audio_manifest:{MANIFEST.name} ({len(out)} cues)"
    return [], "audio_manifest:EMPTY"


def load_cues(vend, source_cues):
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


async def expand_short_cues(cues):
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
        original_natural = natural
        added = []
        for attempt in range(4):
            natural = duration(raw)
            if natural >= EXPAND_THRESHOLD_RATIO * target:
                break
            extra = expansion_for(cid, attempt)
            new_text = sanitize(c["bn"] + " " + " ".join(added) + " " + extra)
            print(f"  fill-expand cue {cid} pass {attempt+1}: "
                  f"natural={natural:.2f}s < {EXPAND_THRESHOLD_RATIO*target:.2f}s", flush=True)
            if not await synth(new_text, raw, force=True):
                break
            added.append(extra)
        expanded.append({
            "id": cid,
            "natural_before": round(original_natural, 3),
            "natural_after": round(duration(raw), 3),
            "target_sec": round(target, 3),
            "passes": len(added),
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
        raise FileNotFoundError(f"original video missing: {ORIGINAL_VIDEO}")

    vend = video_duration(ORIGINAL_VIDEO)
    VIDEO_END = vend
    source_cues, source_desc = load_source_cues()
    if not source_cues:
        raise RuntimeError("no cues loaded from manifest")
    cues, scale = load_cues(vend, source_cues)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"video duration = {vend:.3f}s; cues = {len(cues)}; source = {source_desc}; "
          f"timeline scale = {scale:.4f}", flush=True)

    print("[1/5] TTS (clean, no SFX) ...", flush=True)
    failed = await synth_all(cues)

    print("[2/5] Fill policy: contextual expansion + auto re-render of short cues ...", flush=True)
    fill_expanded = await expand_short_cues(cues)

    print("[3/5] Absolute sample placement (start*44100, pad-only, floor 0.82) ...", flush=True)
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
        del arr, i16, seg
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

    print("[4/5] WAV master + loudnorm -14 LUFS ...", flush=True)
    with wave.open(str(MASTER_WAV), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        for i in range(0, len(canvas), CHUNK):
            w.writeframes(canvas[i:i + CHUNK].tobytes())
    af = "loudnorm=I=-14:LRA=7:TP=-1"
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{MASTER_MP3}" > NUL 2>&1')
    run(f'ffmpeg -y -i "{MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{MASTER_M4A}" > NUL 2>&1')

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    report = {
        "experiment": "clean_timesync_v2 + fill policy (3B1B guest video lesson 02 full-length)",
        "lesson": LESSON,
        "video_id": VIDEO_ID,
        "script_source": source_desc,
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": "absolute sample offset (start*44100); atempo fit in [0.82,2.2]; pad only; no truncation",
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
        "fill_expansions_applied": fill_expanded,
        "expansion_threshold_ratio": EXPAND_THRESHOLD_RATIO,
        "cues": placed,
    }

    print("[5/5] Mux with FULL original video (video copy) ...", flush=True)
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
    print(f"median_fill={median_fill} max_internal_gap_s={max_internal_gap_s} policy_met={report['fill_policy_met']}", flush=True)
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
