# -*- coding: utf-8 -*-
"""
Shared engine for the six Geometry expressive TEACHER NARRATION AUDIO builders
(governance/build_expressive_teacher_audio_geo0N.py).

Implements the Lesson-01 / Calculus gold standard:

  * exact DOM section ids, cue counts, cue types and cue order (validated against
    the browser-extracted governance/geoNN_dom_blocks.json snapshot)
  * expressive, fully phonetic Bengali scripts embedded in each lesson builder
  * per-cue prosody: h2 -5%/+2Hz, figure -4%, formula-box -8%, p +2%,
    callout +0%, conclusion -3%
  * real 350 ms silence chunks between cues so manifest millisecond timings
    match the actual concatenated MP3
  * per-section ffmpeg -c copy concatenation into the existing mp3 names
  * manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST)
  * placeholder manifests backed up to _backup_before_expressive_build/ first
  * edge_tts bn-BD-PradeepNeural with robust retries

No external input files are read at build time except the DOM snapshot used
for the structural parity guard.
"""
import os
import re
import json
import shutil
import hashlib
import asyncio
import subprocess

import edge_tts

VOICE = "bn-BD-PradeepNeural"
GAP_MS = 350.0
HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
AUDIO_ROOT = os.path.join(WORKSPACE, "assets", "audio", "geometry")

PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),
    "h3":            ("-3%", "+0Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),
    "p":             ("+2%", "+0Hz", "+0%"),
    "figure":        ("-4%", "+0Hz", "+0%"),
    "callout":       ("+0%", "+0Hz", "+0%"),
    "formula-box":   ("-8%", "+0Hz", "+0%"),
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")

BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"


def audio_dir(n):
    return os.path.join(AUDIO_ROOT, f"lesson_{n:02d}")


def backup_placeholder_manifests(n):
    """Back up placeholder manifests before anything is overwritten (idempotent)."""
    a_dir = audio_dir(n)
    backup = os.path.join(a_dir, "_backup_before_expressive_build")
    os.makedirs(backup, exist_ok=True)
    for name in ("manifest.json", "manifest.js"):
        src = os.path.join(a_dir, name)
        dst = os.path.join(backup, name)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
            print(f"  backed up {name} -> _backup_before_expressive_build/{name}")
        else:
            print(f"  backup present for {name}")


def load_dom_snapshot(n):
    path = os.path.join(HERE, f"geo{n:02d}_dom_blocks.json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return {s["id"]: [b["type"] for b in s["blocks"]] for s in data["sections"]}


def assert_clean_scripts(n, sections_data, expected_audio, expected_title):
    """Fail before any TTS work if scripts or structure deviate from the gold standard."""
    dom_types = load_dom_snapshot(n)
    if set(sections_data) != set(dom_types):
        raise ValueError(f"geo{n:02d}: section ids {list(sections_data)} != DOM {list(dom_types)}")

    total = 0
    figure_count = 0
    texts = []
    for sec_id, sec in sections_data.items():
        types = [c["type"] for c in sec["cues"]]
        if types != dom_types[sec_id]:
            raise ValueError(f"geo{n:02d}/{sec_id}: cue types/order {types} != DOM {dom_types[sec_id]}")
        if sec["audio_file"] != expected_audio[sec_id]:
            raise ValueError(f"geo{n:02d}/{sec_id}: audio_file {sec['audio_file']} != {expected_audio[sec_id]}")
        indices = [c["index"] for c in sec["cues"]]
        if indices != list(range(len(indices))):
            raise ValueError(f"geo{n:02d}/{sec_id}: cue indices are not 0..n-1")
        for cue in sec["cues"]:
            texts.append(cue["tts"])
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"geo{n:02d}/{sec_id} cue {cue['index']}: forbidden chars {bad!r}")
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError(f"geo{n:02d}/{sec_id} cue {cue['index']}: artificial figure label present")
            if cue["type"] == "figure":
                sentences = [s for s in cue["tts"].split("।") if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError(f"geo{n:02d}/{sec_id} cue {cue['index']}: figure has {len(sentences)} sentences")
                figure_count += 1
        total += len(indices)

    if len(texts) != len(set(texts)):
        dupes = [t for t in texts if texts.count(t) > 1]
        raise ValueError(f"geo{n:02d}: duplicate spoken scripts: {dupes}")
    if not expected_title:
        raise ValueError("empty manifest title")
    print(f"geo{n:02d}: validated {total} clean cues in {len(sections_data)} sections "
          f"({figure_count} figure explanations), 0 duplicates -> DOM snapshot 1:1")
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


def prosody_for(cue):
    rate, pitch, volume = PROSODY_DEFAULT[cue["type"]]
    if cue.get("role") == "conclusion" and cue["type"] not in ("h2", "formula-box"):
        rate, pitch, volume = CONCLUSION_PROSODY
    return rate, pitch, volume


def valid_audio(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    try:
        return get_duration_ms(path) > 0
    except Exception:
        return False


async def synth_cue(text, path, rate, pitch, volume):
    # Edge TTS occasionally replies with an empty audio stream; back off and
    # retry (network-response wait, not an arbitrary fixed delay).
    for attempt in range(10):
        try:
            comm = edge_tts.Communicate(text, VOICE,
                                        rate=rate, pitch=pitch, volume=volume)
            await comm.save(path)
            if valid_audio(path):
                return
        except Exception as exc:
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


async def build_section(n, sec_id, sec):
    a_dir = audio_dir(n)
    temp = os.path.join(a_dir, f"_expressive_tmp_{sec_id}")
    os.makedirs(temp, exist_ok=True)

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
    chunk_paths, durations = [], []
    print(f"\n[{sec_id}] {len(cues)} cues -> {sec['audio_file']}")
    for cue in cues:
        idx = cue["index"]
        chunk = os.path.join(temp, f"cue_{idx:02d}.mp3")
        rate, pitch, volume = prosody_for(cue)
        if not valid_audio(chunk):
            print(f"  cue {idx:02d} [{cue['type']:<13}] {rate:>4} {pitch:>5}  {cue['tts'][:28]}...")
            await synth_cue(cue["tts"], chunk, rate, pitch, volume)
        else:
            print(f"  cue {idx:02d} [{cue['type']:<13}] cached")
        chunk_paths.append(chunk)
        durations.append(get_duration_ms(chunk))

    sample_rate, channels = probe_stream(chunk_paths[0])
    silence = os.path.join(temp, "silence_350ms.mp3")
    make_silence(silence, sample_rate, channels)

    concat_paths = []
    for i, chunk in enumerate(chunk_paths):
        concat_paths.append(chunk)
        if i < len(chunk_paths) - 1:
            concat_paths.append(silence)

    final_path = os.path.join(a_dir, sec["audio_file"])
    concat_to(final_path, concat_paths)

    manifest_cues, cursor = [], 0.0
    for i, (cue, dur) in enumerate(zip(cues, durations)):
        start, end = cursor, cursor + dur
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
                raise RuntimeError(f"{sec_id} cue {i}: overlaps previous")
            if abs((mc["start_ms"] - prev["end_ms"]) - GAP_MS) > 1.0:
                raise RuntimeError(f"{sec_id} cue {i}: gap is not {GAP_MS} ms")

    if not os.path.exists(final_path) or os.path.getsize(final_path) == 0:
        raise RuntimeError(f"{sec_id}: missing/empty output {final_path}")

    print(f"  => {sec['audio_file']}: {len(manifest_cues)} cues, "
          f"{cursor / 1000.0:.2f}s, {os.path.getsize(final_path)} bytes")
    return {
        "title": sec["title"],
        "audio_file": sec["audio_file"],
        "total_duration_ms": round(cursor, 1),
        "cues": manifest_cues,
    }


async def build_all(n, sections_data, expected_audio, manifest_title):
    a_dir = audio_dir(n)
    backup_placeholder_manifests(n)
    assert_clean_scripts(n, sections_data, expected_audio, manifest_title)

    built = {}
    for sec_id, sec in sections_data.items():
        built[sec_id] = await build_section(n, sec_id, sec)

    manifest_data = {
        "course": "geometry",
        "lesson": f"lesson_{n:02d}",
        "title": manifest_title,
        "voice": VOICE,
        "mode": "authentic_teacher",
        "sections": built,
    }
    json_text = json.dumps(manifest_data, ensure_ascii=False, indent=2)
    with open(os.path.join(a_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        fh.write(json_text)
    with open(os.path.join(a_dir, "manifest.js"), "w", encoding="utf-8") as fh:
        fh.write("window.TEACHER_AUDIO_MANIFEST = " + json_text + ";\n")

    with open(os.path.join(a_dir, "manifest.json"), encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert set(loaded["sections"]) == set(load_dom_snapshot(n))
    total_cues = total_ms = 0
    figures = 0
    for sec_id in sections_data:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == len(sections_data[sec_id]["cues"])
        path = os.path.join(a_dir, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")

    print("\n" + "=" * 66)
    print(f"BUILD COMPLETE - Geometry Lesson {n:02d} expressive teacher audio")
    for sec_id in sections_data:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<24} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across {len(sections_data)} sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("  manifest.json valid; all mp3 files non-empty; backup preserved.")
    print("=" * 66)
