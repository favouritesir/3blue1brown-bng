# -*- coding: utf-8 -*-
"""
Shared deterministic engine for the Analysis course expressive teacher audio
builders (build_expressive_teacher_audio_analysis01.py .. _10.py).

Each lesson builder embeds its own fully phonetic Bengali scripts; this module
handles only validation, edge-tts synthesis (robust retries), real 350 ms
silence gaps, ffmpeg -c copy concatenation and exact-ms manifest emission.

Prosody (per cue type):
    h2 -5% / +2Hz, chapter-quote -3%, p +2%, figure -4%, callout +0%,
    formula-box -8%, conclusion -3%.

Usage (from web_platform/):
    python governance/build_expressive_teacher_audio_analysis01.py
"""
import os
import re
import json
import hashlib
import asyncio
import subprocess

import edge_tts

VOICE = "bn-BD-PradeepNeural"
GAP_MS = 350.0
HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
AUDIO_ROOT = os.path.join(WORKSPACE, "assets", "audio", "analysis")

# Prosody keyed by cue type: (rate, pitch, volume)
PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
    "h3":            ("-3%", "+0Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),   # reflective quotation
    "p":             ("+2%", "+0Hz", "+0%"),   # natural teacher pace
    "figure":        ("-4%", "+0Hz", "+0%"),   # slower, considerate explanation
    "callout":       ("+0%", "+0Hz", "+0%"),   # steady, matter-of-fact note
    "formula-box":   ("-8%", "+0Hz", "+0%"),   # slow and deliberate
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")     # calm concluding prose

BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_LABEL = "চিত্র প্রদর্শনী"


def prosody_for(cue):
    rate, pitch, volume = PROSODY_DEFAULT[cue["type"]]
    if cue.get("role") == "conclusion" and cue["type"] not in ("h2", "formula-box"):
        rate, pitch, volume = CONCLUSION_PROSODY
    return rate, pitch, volume


def assert_clean_scripts(sections_data, expected_types, expected_files, expected_total):
    """Fail before any TTS work if scripts contain markup/Latin text, drift from
    the authoritative live-DOM cue structure, use the artificial figure label,
    duplicate a script, or a figure lacks a genuine 2-4 sentence explanation."""
    seen_texts = set()
    total = 0
    if set(sections_data) != set(expected_types):
        raise ValueError("section set differs from expected DOM sections")
    for sec_id, sec in sections_data.items():
        cues = sec["cues"]
        types = [c["type"] for c in cues]
        if types != expected_types[sec_id]:
            raise ValueError(f"{sec_id}: cue type/order mismatch -> {types}")
        if sec["audio_file"] != expected_files[sec_id]:
            raise ValueError(f"{sec_id}: audio_file mismatch")
        if [c["index"] for c in cues] != list(range(len(cues))):
            raise ValueError(f"{sec_id}: cue indices are not 0..n-1")
        total += len(cues)
        for cue in cues:
            text = cue["tts"]
            bad = BAD_CHARS.findall(text)
            if bad:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars {bad!r} in {text!r}")
            if FORBIDDEN_LABEL in text:
                raise ValueError(f"{sec_id} cue {cue['index']}: artificial figure label present")
            if cue["type"] not in PROSODY_DEFAULT:
                raise ValueError(f"{sec_id} cue {cue['index']}: unknown cue type {cue['type']}")
            if text in seen_texts:
                raise ValueError(f"{sec_id} cue {cue['index']}: duplicate script text")
            seen_texts.add(text)
            if cue["type"] == "figure":
                sentences = [s for s in text.split("।") if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(
                        f"{sec_id} cue {cue['index']}: figure has {len(sentences)} sentences")
    if total != expected_total:
        raise ValueError(f"Expected {expected_total} cues, found {total}")
    return total


def get_duration_ms(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout.strip()
    ms = float(out) * 1000.0
    if ms <= 0:
        raise RuntimeError(f"Non-positive duration for {path}: {ms}")
    return ms


def probe_stream(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=sample_rate,channels", "-of", "json", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout
    st = json.loads(out)["streams"][0]
    return int(st["sample_rate"]), int(st["channels"])


def valid_audio(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    try:
        return get_duration_ms(path) > 0
    except Exception:  # noqa: BLE001 - corrupt / partial download
        return False


async def synth_cue(text, path, rate, pitch, volume):
    """Edge TTS sometimes returns an empty audio stream; retry with backoff.
    The wait is for a network response, never an arbitrary fixed delay."""
    for attempt in range(10):
        try:
            comm = edge_tts.Communicate(text, VOICE,
                                        rate=rate, pitch=pitch, volume=volume)
            await comm.save(path)
            if valid_audio(path):
                return
        except Exception as exc:  # noqa: BLE001 - network hiccups happen
            print(f"    attempt {attempt + 1} failed: {exc}")
        await asyncio.sleep(min(0.5 * (2 ** attempt), 8.0))
    raise RuntimeError(f"Failed to synthesise cue: {text[:40]}...")


def make_silence(path, sample_rate, channels, seconds=GAP_MS / 1000.0):
    layout = "mono" if channels == 1 else "stereo"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-f", "lavfi", "-i", f"anullsrc=r={sample_rate}:cl={layout}",
         "-t", f"{seconds:.3f}",
         "-c:a", "libmp3lame", "-b:a", "64k", path],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True,
    )
    if os.path.getsize(path) == 0:
        raise RuntimeError("Failed to create silence chunk")


def concat_to(final_path, chunk_paths):
    list_path = os.path.splitext(final_path)[0] + "_expressive_concat.txt"
    with open(list_path, "w", encoding="utf-8") as fh:
        for p in chunk_paths:
            fh.write("file '" + p.replace(os.sep, "/") + "'\n")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", list_path, "-c", "copy", final_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True,
    )
    os.remove(list_path)


async def build_section(sec_id, sec, audio_dir):
    temp = os.path.join(audio_dir, f"_expressive_tmp_{sec_id}")
    os.makedirs(temp, exist_ok=True)

    # Version-based cache: changing the embedded scripts invalidates old chunks.
    sig = hashlib.sha256(
        json.dumps(sec, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    sig_path = os.path.join(temp, "scripts.sha256")
    old = ""
    if os.path.exists(sig_path):
        with open(sig_path, encoding="utf-8") as fh:
            old = fh.read().strip()
    if old != sig:
        for name in os.listdir(temp):
            if name.endswith(".mp3"):
                os.remove(os.path.join(temp, name))
        with open(sig_path, "w", encoding="utf-8") as fh:
            fh.write(sig)

    cues = sec["cues"]
    chunk_paths = []
    durations = []

    print(f"\n[{sec_id}] {len(cues)} cues -> {sec['audio_file']}")
    for cue in cues:
        idx = cue["index"]
        chunk = os.path.join(temp, f"cue_{idx:02d}.mp3")
        rate, pitch, volume = prosody_for(cue)
        if not valid_audio(chunk):
            print(f"  cue {idx:02d} [{cue['type']:<13}] {rate:>4} {pitch:>5}  {cue['tts'][:30]}...")
            await synth_cue(cue["tts"], chunk, rate, pitch, volume)
        else:
            print(f"  cue {idx:02d} [{cue['type']:<13}] cached")
        chunk_paths.append(chunk)
        durations.append(get_duration_ms(chunk))

    # Real 350 ms silence between cues, encoded to match the TTS chunks.
    sample_rate, channels = probe_stream(chunk_paths[0])
    silence = os.path.join(temp, "silence_350ms.mp3")
    make_silence(silence, sample_rate, channels)

    concat_paths = []
    for i, chunk in enumerate(chunk_paths):
        concat_paths.append(chunk)
        if i < len(chunk_paths) - 1:
            concat_paths.append(silence)

    final_path = os.path.join(audio_dir, sec["audio_file"])
    concat_to(final_path, concat_paths)

    # Timings from measured durations + the real silence chunks.
    manifest_cues = []
    cursor = 0.0
    for i, (cue, dur) in enumerate(zip(cues, durations)):
        start = cursor
        end = start + dur
        manifest_cues.append({
            "index": cue["index"],
            "type": cue["type"],
            "text": cue["tts"],
            "start_ms": round(start, 1),
            "end_ms": round(end, 1),
            "duration_ms": round(dur, 1),
        })
        cursor = end + (GAP_MS if i < len(cues) - 1 else 0.0)

    for i, mc in enumerate(manifest_cues):
        if mc["duration_ms"] <= 0 or mc["end_ms"] <= mc["start_ms"]:
            raise RuntimeError(f"{sec_id} cue {i}: non-positive span")
        if i > 0:
            prev = manifest_cues[i - 1]
            if mc["start_ms"] < prev["end_ms"]:
                raise RuntimeError(f"{sec_id} cue {i}: overlaps previous cue")
            if abs((mc["start_ms"] - prev["end_ms"]) - GAP_MS) > 1.0:
                raise ValueError(f"{sec_id} cue {i}: gap is not {GAP_MS} ms")

    if not os.path.exists(final_path) or os.path.getsize(final_path) == 0:
        raise RuntimeError(f"{sec_id}: missing/empty output {final_path}")

    print(f"  => {sec['audio_file']}: {len(manifest_cues)} cues, "
          f"{cursor / 1000.0:.2f}s, {os.path.getsize(final_path)} bytes")

    return {
        "section_id": sec_id,
        "title": sec["title"],
        "audio_file": sec["audio_file"],
        "total_duration_ms": round(cursor, 1),
        "cues": manifest_cues,
    }


async def build_lesson(lesson_no, manifest_title, sections_data,
                       expected_types, expected_files, expected_total):
    assert_clean_scripts(sections_data, expected_types, expected_files, expected_total)
    total_cues = sum(len(s["cues"]) for s in sections_data.values())
    print(f"Validated {total_cues} clean cues in {len(sections_data)} sections.")

    audio_dir = os.path.join(AUDIO_ROOT, f"lesson_{lesson_no:02d}")
    os.makedirs(audio_dir, exist_ok=True)

    manifest_sections = {}
    for sec_id, sec in sections_data.items():
        manifest_sections[sec_id] = await build_section(sec_id, sec, audio_dir)

    manifest_data = {
        "course": "analysis",
        "lesson": f"lesson_{lesson_no:02d}",
        "title": manifest_title,
        "voice": VOICE,
        "mode": "authentic_teacher",
        "sections": manifest_sections,
    }
    json_text = json.dumps(manifest_data, ensure_ascii=False, indent=2)
    with open(os.path.join(audio_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        fh.write(json_text)
    with open(os.path.join(audio_dir, "manifest.js"), "w", encoding="utf-8") as fh:
        fh.write("window.TEACHER_AUDIO_MANIFEST = " + json_text + ";\n")

    with open(os.path.join(audio_dir, "manifest.json"), encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert set(loaded["sections"]) == set(sections_data)
    grand_ms = 0.0
    figures = 0
    for sec_id in sections_data:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == len(expected_types[sec_id])
        assert msec["section_id"] == sec_id
        path = os.path.join(audio_dir, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        grand_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    assert sum(len(loaded["sections"][s]["cues"]) for s in sections_data) == expected_total

    print("\n" + "=" * 64)
    print(f"BUILD COMPLETE - expressive teacher audio, Analysis Lesson {lesson_no:02d}")
    for sec_id in sections_data:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<28} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {expected_total} cues across {len(sections_data)} sections, "
          f"{grand_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json valid JSON; all mp3 files exist and are non-empty.")
    print("=" * 64)
    return grand_ms
