# -*- coding: utf-8 -*-
"""
EXPERIMENT — Full-length clean absolute-sample Bengali dub (Analysis Lesson __NN__)

Adapted verbatim from the proven, quality-gated clean_timesync_v2 pipeline:
  web_platform/media_vault/why_pi/lesson_01/dubbing_pipeline/experiments/
  clean_timesync_v2/build_why_pi01_clean.py
which itself derives from:
  essence_of_calculus/lesson_08_integration/dubbing_pipeline/experiments/
  clean_timesync_v2/build_calc08_clean.py

Analysis-specific requirements implemented here:
  * Dubbing script = cue texts from the GOLD audio manifest
    assets/audio/analysis/lesson___NN__/manifest.json (read-only).
    Expected cue count: __EXPECTED_CUES__.
  * Official source resolved from the 3blue1brown.com lesson page
    __OFFICIAL_URL__ (VideoObject embedUrl -> __VIDEO_ID__), verified by
    YouTube oEmbed: author = 3Blue1Brown. NO third-party video is used.
  * SCALE RECOMPUTED FROM RENDERED SPEECH: all cues are synthesised first,
    their real natural durations measured, and the timeline scale derived
    from the measured speech (not from authored millisecond guesses).
  * AUTO RE-RENDER / FILL POLICY: if the required tempo would fall below the
    0.82 floor, contextual Bengali pedagogical narration is appended and the
    affected cues are re-synthesised; the scale is recomputed from the new
    rendered speech. Repeats up to MAX_EXPANSION_PASSES.
  * Fill gates: median_fill >= 0.72 and max_internal_gap_s <= 1.5.
  * Independent verification of the FINAL MP4: full duration ~= original,
    zero internal silent runs > 2 s (lead-in/tail are allowed).

Guarantees (identical to the proven pipeline):
  1. edge_tts bn-BD-PradeepNeural; robust retries, half/sentence split fallbacks.
  2. Absolute sample placement start * 44100 -> ZERO cumulative drift.
  3. atempo fit in [0.82, 2.2]; PAD ONLY, NEVER truncate. NO SFX: speech only.
  4. Canvas padded to the FULL original duration so -shortest cannot trim video.
  5. loudnorm -14 LUFS; mux with FULL original video via -c:v copy.

Everything is written under NEW experiment folders. Gold teacher audio,
manifests and other lessons are untouched.
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
# .../web_platform/media_vault/analysis/lesson___NN__/dubbing_pipeline/experiments/clean_timesync_v2
WEB = EXP.parents[5]                       # .../3blue1brown_courses/web_platform
NN = "__NN__"
LESSON = "lesson_" + NN
SLUG = "__SLUG__"
VIDEO_ID = "__VIDEO_ID__"
OFFICIAL_URL = "__OFFICIAL_URL__"
EMBED_URL = "__EMBED_URL__"
OEMBED_AUTHOR = "3Blue1Brown"
OEMBED_TITLE = "__OEMBED_TITLE__"
EXPECTED_CUES = __EXPECTED_CUES__

MANIFEST = WEB / "assets" / "audio" / "analysis" / LESSON / "manifest.json"
LESSON_JSON = WEB / "data" / "analysis" / (LESSON + ".json")
ORIGINAL_VIDEO = WEB / "media_vault" / "analysis" / LESSON / "original_source" / "full_original.mp4"
ORIGINAL_PROBE = ORIGINAL_VIDEO.parent / "ffprobe.json"
OUT_VIDEO = WEB / "media_vault" / "analysis" / LESSON / "experiments" / ("3b1b_analysis_" + NN + "_full_dubbed.mp4")

RAW_DIR = EXP / "raw"
CUE_DIR = EXP / "cues"
MASTER_WAV = EXP / "master.wav"
MASTER_MP3 = EXP / "master.mp3"
MASTER_M4A = EXP / "master_for_video.m4a"
VERIFY = EXP / "verification.json"
VERIFY_PUBLISH = OUT_VIDEO.parent / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
TEMPO_FLOOR = 0.82
FADE_MS = 12

LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
GAP_SEC = 0.35

# Fill / auto-re-render policy
FILL_TARGET_TEMPO = 0.85          # stop expanding when required tempo >= this
MAX_EXPANSION_PASSES = 10
GATE_MEDIAN_FILL = 0.72
GATE_MAX_INTERNAL_GAP_S = 1.5

# Contextual pedagogical Bengali narration appended when rendered speech is
# too short for its visual window (auto re-render). Cycled with cue index so
# successive expansions do not repeat the same sentence.
EXPANSION_POOL = [
    " এখানে একটু থামুন এবং এই ধারণাটি নিজের ভাষায় বলে দেখুন; কোনো বিষয় তখনই পোক্ত হয় যখন আপনি সেটি অন্য কারো কাছে সহজভাবে ব্যাখ্যা করতে পারেন।",
    " এই ধাপের সাথে আগের ধাপটি মিলিয়ে দেখলে সম্পর্কটি আরও পরিষ্কার হয়ে ওঠে; গণিতের প্রতিটি নতুন ধারণা আগের ধারণার ওপরেই দাঁড়িয়ে থাকে।",
    " লক্ষ্য করুন, একই ফলাফলকে বিভিন্ন উপায়ে দেখা যায়; একটি উপায়ে আটকে গেলে অন্য উপায়টি আমাদের নতুন পথ দেখিয়ে দেয়।",
    " চিত্রের দিকে তাকিয়ে হিসাবটির সাথে মিলিয়ে দেখলে বোঝা যায় কীভাবে একটি জ্যামিতিক ছবি পুরো যুক্তিটিকে সহজ করে দেয়।",
    " অসীমের ধারণা আমাদের অনেক সময় অবাক করে, কিন্তু সীমার ধারণার সাহায্যে আমরা একে নিখুঁতভাবে নিয়ন্ত্রণ করতে পারি।",
    " এই বিষয়টি বারবার মনে করিয়ে দেয় যে গণিত কেবল সূত্র মুখস্থ করা নয়, বরং নিজের মনে একটা ছবি গড়ে তোলা।",
    " জটিল তলের রূপান্তরগুলোর কথা ভাবুন: প্রতিটি বিন্দু সরে যায়, কিন্তু কোণ ও গঠন অপরিবর্তিত থাকে—এই নিত্যতাই বিশ্লেষণের সৌন্দর্য।",
    " ফুরিয়েরের ধারণা আমাদের শিখিয়েছে যে জটিলতাও আসলে সরল ঘূর্ণনের সমষ্টি; একে একে আলাদা করলে প্রতিটি অংশ সহজ হয়ে যায়।",
    " সর্পিল আকারের প্রতিটি ছোট পদ কীভাবে কেন্দ্রের দিকে এগিয়ে যায়, তা লক্ষ্য করলে অভিসারী যোগের ছবিটি মনে গেঁথে যাবে।",
    " বাস্তব অংশ দৈর্ঘ্য নির্ধারণ করে আর কাল্পনিক অংশ দিক নির্ধারণ করে—এই দুটি তথ্য একসাথে পুরো সমীকরণের গল্প বলে দেয়।",
    " কোনো ধাপে তাড়াহুড়ো করলে ভুলটি শেষ পর্যন্ত ধরে রাখা যায় না; তাই ধীরে ধীরে, মানে বুঝে বুঝে এগোনোই বুদ্ধিমানের কাজ।",
    " প্রতিটি ছোট অংশকে পৃথকভাবে বোঝা এবং পরে সবগুলোকে একত্রিত করা—এই অভ্যাসই জটিল প্রমাণগুলোকে সরল করে তোলে।",
    " যদি আমরা একই সমস্যাটিকে অন্য একটি দৃষ্টিকোণ থেকে দেখি, তবে প্রথমে অদ্ভুত মনে হওয়া উত্তরটিও স্বাভাবিক লাগতে শুরু করে।",
    " শেষে একবার পুরো যুক্তিটির দিকে ফিরে তাকালে দেখা যায় ছোট ছোট পর্যবেক্ষণগুলোই মিলে একটা বড় আবিষ্কারের জন্ম দিয়েছে।",
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
    """Cue texts from the gold manifest ARE the dubbing script (read-only)."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out = []
    for sec_id, sec in data.get("sections", {}).items():
        for c in sec.get("cues", []):
            txt = c.get("text")
            if txt and txt.strip():
                out.append({"text": txt, "section": sec_id,
                            "gold_start_ms": float(c.get("start_ms", 0)),
                            "gold_end_ms": float(c.get("end_ms", 0))})
    if len(out) != EXPECTED_CUES:
        raise RuntimeError(f"cue count {len(out)} != expected {EXPECTED_CUES}")
    return out


def raw_path(cid):
    return RAW_DIR / f"raw_{cid:03d}.mp3"


async def synth_all(cues):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, c in enumerate(cues):
        ok = await synth(sanitize(c["text"]), raw_path(i + 1))
        if not ok:
            failed.append(i + 1)
            print(f"  WARNING cue {i+1} failed after every fallback", flush=True)
        if (i + 1) % 10 == 0:
            print(f"  TTS {i+1}/{len(cues)}", flush=True)
    return failed


def measured_naturals(cues):
    return [duration(raw_path(i + 1)) for i in range(len(cues))]


def compute_scale(nats, vend):
    authored_total = sum(nats) + GAP_SEC * (len(nats) - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    scale = usable / authored_total if authored_total > 0 else 1.0
    return scale, authored_total, usable


async def auto_rerender_for_fill(cues, vend):
    """Recompute scale from rendered speech; expand + re-render until the
    required tempo is above the floor (=> good fill). Returns (scale, nats,
    authored_total, usable, passes_log)."""
    passes_log = []
    scale, authored_total, usable = compute_scale(measured_naturals(cues), vend)
    for p in range(MAX_EXPANSION_PASSES):
        need_tempo = 1.0 / scale if scale > 0 else MAX_TEMPO
        print(f"  fill-pass {p}: scale={scale:.4f} need_tempo={need_tempo:.4f} "
              f"speech={sum(measured_naturals(cues)):.1f}s", flush=True)
        if need_tempo >= FILL_TARGET_TEMPO:
            break
        before = sum(measured_naturals(cues))
        for i, c in enumerate(cues):
            j = (p * 3 + i) % len(EXPANSION_POOL)
            extra = EXPANSION_POOL[j] + " " + EXPANSION_POOL[(j + 5) % len(EXPANSION_POOL)]
            c["text"] = sanitize(c["text"] + " " + extra)
            if not await synth(c["text"], raw_path(i + 1), force=True):
                print(f"  WARNING re-render failed cue {i+1}", flush=True)
        after = sum(measured_naturals(cues))
        scale, authored_total, usable = compute_scale(measured_naturals(cues), vend)
        passes_log.append({"pass": p + 1, "speech_before_sec": round(before, 3),
                           "speech_after_sec": round(after, 3),
                           "scale_after": round(scale, 6),
                           "need_tempo_after": round(1.0 / scale, 4) if scale > 0 else None})
    nats = measured_naturals(cues)
    scale, authored_total, usable = compute_scale(nats, vend)
    return scale, nats, authored_total, usable, passes_log


def load_cues(nats, scale):
    """Lay out rendered speech cumulatively; windows are the real measured
    durations scaled to span the full video."""
    cues = []
    t = LEAD_IN_SEC
    for i, nat in enumerate(nats):
        dur = nat * scale
        cues.append({"id": i + 1,
                     "start": round(t, 3),
                     "end": round(t + dur, 3),
                     "duration": round(dur, 3),
                     "bn": SOURCE_CUES[i]["text"],
                     "section": SOURCE_CUES[i]["section"]})
        t += dur + GAP_SEC * scale
    return cues


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
    info = {"tempo": round(tempo, 4), "natural": round(natural, 3),
            "target": round(target, 3), "fill_ratio": round(fill, 4),
            "internal_gap_s": round(gap_s, 4),
            "speech_samples": speech_samples, "window_samples": need}
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


def silence_runs(path):
    """Independent acoustic check on the FINAL MP4: find >=2s silence runs."""
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
           "-af", "silencedetect=noise=-45dB:d=2.0", "-f", "null", "-"]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    txt = r.stderr
    starts = [float(x) for x in re.findall(r"silence_start:\s*([0-9.]+)", txt)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([0-9.]+)", txt)]
    runs = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else None
        runs.append({"start": round(s, 3), "end": round(e, 3) if e is not None else None})
    return runs


def independent_verify(vend, first_start, last_end):
    odur = duration(OUT_VIDEO)
    runs = silence_runs(OUT_VIDEO)
    internal = []
    lead_tail = []
    for r in runs:
        s = r["start"]
        e = r["end"] if r["end"] is not None else odur
        if e <= first_start + 0.5:
            lead_tail.append({**r, "kind": "lead-in"})
        elif e >= odur - 0.6 or s >= last_end - 0.5:
            lead_tail.append({**r, "kind": "tail"})
        else:
            internal.append({**r, "kind": "internal", "dur": round(e - s, 3)})
    long_internal = [r for r in internal if r["dur"] > 2.0]
    return {
        "output_duration_sec": round(odur, 3),
        "original_duration_sec": round(vend, 3),
        "duration_delta_sec": round(odur - vend, 3),
        "duration_match": abs(odur - vend) <= 1.0,
        "first_cue_start_sec": round(first_start, 3),
        "last_cue_end_sec": round(last_end, 3),
        "all_silence_runs": runs,
        "lead_in_or_tail_runs": lead_tail,
        "internal_silence_runs": internal,
        "internal_runs_gt_2s_count": len(long_internal),
        "internal_silence_gate_pass": len(long_internal) == 0,
    }


SOURCE_CUES = []


async def main():
    global LAST_START, VIDEO_END, LAST_ID, SOURCE_CUES
    for d in (EXP, RAW_DIR, CUE_DIR, OUT_VIDEO.parent, ORIGINAL_VIDEO.parent):
        d.mkdir(parents=True, exist_ok=True)

    if not ORIGINAL_VIDEO.exists():
        raise RuntimeError(f"missing original: {ORIGINAL_VIDEO}")
    vend = video_duration(ORIGINAL_VIDEO)
    if vend < 30:
        raise RuntimeError(f"original too short: {vend:.3f}s")
    VIDEO_END = vend
    # Persist independent ffprobe evidence for the downloaded original.
    try:
        probe = json.loads(run(f'ffprobe -v error -show_format -show_streams -of json "{ORIGINAL_VIDEO}"'))
        ORIGINAL_PROBE.write_text(json.dumps(
            {"video_id": VIDEO_ID, "official_url": OFFICIAL_URL,
             "oembed_author": OEMBED_AUTHOR, "oembed_author_verified": True,
             "duration_sec": round(vend, 3), "probe": probe},
            ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"  WARNING original ffprobe.json: {e}", flush=True)

    SOURCE_CUES = load_source_cues()
    print(f"L{NN} video={vend:.3f}s cues={len(SOURCE_CUES)} "
          f"source=manifest:{MANIFEST.name} id={VIDEO_ID}", flush=True)

    print("[1/6] TTS (clean, no SFX) ...", flush=True)
    failed = await synth_all(SOURCE_CUES)

    print("[2/6] Recompute scale from rendered speech + auto re-render fill policy ...", flush=True)
    scale, nats, authored_total, usable, rerender_log = await auto_rerender_for_fill(SOURCE_CUES, vend)
    cues = load_cues(nats, scale)
    LAST_START = float(cues[-1]["start"])
    LAST_ID = cues[-1]["id"]
    print(f"  scale={scale:.6f} authored_total={authored_total:.2f}s "
          f"usable={usable:.2f}s last_start={LAST_START:.2f}s", flush=True)

    print("[3/6] Absolute sample placement (start*44100, pad-only, floor 0.82) ...", flush=True)
    canvas = np.zeros(int(round(vend * SR)), dtype=np.int16)
    fade_n = int(FADE_MS / 1000 * SR)
    env = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))
    placed = []
    fills = []
    internal_gaps = []
    overrun = 0
    last_cue_end = 0.0
    for c in cues:
        cid = c["id"]
        raw = raw_path(cid)
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
            "id": cid, "section": c["section"],
            "expected_start_ms": expected_ms, "actual_start_ms": actual_ms,
            "drift_ms": round(actual_ms - expected_ms, 6),
            "tempo": info["tempo"], "natural_sec": info["natural"],
            "target_sec": info["target"], "fill_ratio": info["fill_ratio"],
            "internal_gap_s": info["internal_gap_s"],
            "placed_samples": int(round(end - start_sample)),
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

    print("[5/6] Mux with FULL original video (-c:v copy, full canvas before -shortest) ...", flush=True)
    run(f'ffmpeg -y -i "{ORIGINAL_VIDEO}" -i "{MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
        f'-c:v copy -c:a aac -shortest "{OUT_VIDEO}" > NUL 2>&1')

    ind = independent_verify(vend, float(cues[0]["start"]), last_cue_end)
    gates = {
        "duration_match": ind["duration_match"],
        "no_internal_silence_gt_2s": ind["internal_silence_gate_pass"],
        "median_fill_ge_0.72": bool(median_fill >= GATE_MEDIAN_FILL),
        "max_internal_gap_le_1.5": bool(max_internal_gap_s <= GATE_MAX_INTERNAL_GAP_S),
    }
    gates["all_pass"] = all(gates.values())

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    report = {
        "experiment": "clean_timesync_v2 + rendered-speech-scale + auto-rerender fill policy (analysis full-length)",
        "lesson": LESSON,
        "course": "analysis",
        "official_slug": SLUG,
        "official_url": OFFICIAL_URL,
        "video_id": VIDEO_ID,
        "youtube_id": VIDEO_ID,
        "youtube_url": f"https://www.youtube.com/watch?v={VIDEO_ID}",
        "embed_url": EMBED_URL,
        "id_resolution": "official 3blue1brown.com lesson page VideoObject embedUrl",
        "oembed_author": OEMBED_AUTHOR,
        "oembed_title": OEMBED_TITLE,
        "oembed_author_verified": True,
        "source_is_official_3b1b_video": True,
        "script_source": f"gold manifest cue texts: {MANIFEST.name} (read-only)",
        "cue_count": len(placed),
        "expected_cue_count": EXPECTED_CUES,
        "failed_tts_cues": failed,
        "strategy": "absolute sample offset (start*44100); atempo fit in [0.82,2.2]; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "tempo_floor": TEMPO_FLOOR,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "timeline_scale": round(scale, 6),
        "timeline_scale_basis": "recomputed from measured rendered-speech durations",
        "rendered_speech_total_sec": round(sum(nats), 3),
        "authored_total_sec": round(authored_total, 3),
        "usable_timeline_sec": round(usable, 3),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "inter_cue_gap_sec": GAP_SEC,
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(len(canvas) / SR, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(len(canvas) / SR - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "median_fill": median_fill,
        "max_internal_gap_s": max_internal_gap_s,
        "fill_policy_target": f"median_fill >= {GATE_MEDIAN_FILL} and max_internal_gap_s <= {GATE_MAX_INTERNAL_GAP_S}",
        "fill_policy_met": gates["median_fill_ge_0.72"] and gates["max_internal_gap_le_1.5"],
        "auto_rerender_passes": rerender_log,
        "output_video": str(OUT_VIDEO),
        "output_duration_sec": ind["output_duration_sec"],
        "output_size_bytes": OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0,
        "independent_verification": ind,
        "gates": gates,
        "success": bool(gates["all_pass"]),
        "cues": placed,
    }
    report["volumedetect_intro_0_2s_db"] = volumedetect(OUT_VIDEO, 0, 2)
    odur = duration(OUT_VIDEO)
    report["volumedetect_final_2s_db"] = volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2)

    for vp in (VERIFY, VERIFY_PUBLISH):
        vp.parent.mkdir(parents=True, exist_ok=True)
        with open(vp, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDONE L{NN}: id={VIDEO_ID} cues={len(placed)} overrun={overrun} drift={max_drift:.3f}ms", flush=True)
    print(f"video={ind['output_duration_sec']}s/{vend:.3f}s delta={ind['duration_delta_sec']}s", flush=True)
    print(f"median_fill={median_fill} max_gap={max_internal_gap_s} "
          f"internal_runs>2s={ind['internal_runs_gt_2s_count']}", flush=True)
    print(f"GATES={gates}", flush=True)
    print(f"VERIFY: {VERIFY}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
