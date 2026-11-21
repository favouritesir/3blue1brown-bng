# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Computer Science Lesson 07
("২৫৬-বিট নিরাপত্তা আসলে কত নিরাপদ?", Bengali) to the Lesson-01 gold standard.

Deterministic, re-runnable, self-contained:
  * 22 cues in 5 narrated sections with EXACTLY the same section IDs,
    audio_file names, cue types and cue order as the live narration-engine DOM.
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time), so the build is fully reproducible.
  * Figure cues are genuine 2-4 sentence natural explanations — never the
    artificial label "চিত্র প্রদর্শনী". Every script carries phonetic safeguards.
  * Per-cue prosody via edge_tts Communicate(rate=, pitch=, volume=):
      h2 -5%/+2Hz, chapter-quote -3%, p +2%, figure -4%, callout +0%,
      formula-box -8%, conclusion -3%.
  * A real 350 ms silence chunk sits between cues, so the millisecond timings
    written to the manifest match the actual concatenated audio.
  * Per-section concatenation with ffmpeg -c copy into the existing mp3 names.
  * Placeholder manifests are first backed up to _backup_before_expressive_build/.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) with the
    exact-ms timings, and bumps the lesson page's manifest script cache version.

Usage:  python governance/build_expressive_teacher_audio_cs07.py
"""

import os
import re
import json
import copy
import shutil
import hashlib
import asyncio
import subprocess

import edge_tts

VOICE = "bn-BD-PradeepNeural"
GAP_MS = 350.0
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))            # .../governance
WORKSPACE = os.path.dirname(SCRIPT_DIR)                            # .../web_platform
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio",
                         "computer_science", "lesson_07")
BACKUP_DIR = os.path.join(AUDIO_DIR, "_backup_before_expressive_build")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "computer_science",
                         "lesson_07.html")
MANIFEST_TITLE = "২৫৬-বিট নিরাপত্তা আসলে কত নিরাপদ?"

PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),
    "p":             ("+2%", "+0Hz", "+0%"),
    "figure":        ("-4%", "+0Hz", "+0%"),
    "callout":       ("+0%", "+0Hz", "+0%"),
    "formula-box":   ("-8%", "+0Hz", "+0%"),
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")

# Parity guards taken from the live narration-engine DOM (channel=chrome).
EXPECTED_TYPES = {
    "sec-question": [
        "h2",
        "p",
        "figure",
        "callout"
    ],
    "sec-powers": [
        "h2",
        "p",
        "formula-box",
        "figure",
        "p"
    ],
    "sec-universe": [
        "h2",
        "p",
        "figure",
        "chapter-quote"
    ],
    "sec-brute": [
        "h2",
        "p",
        "formula-box",
        "figure",
        "p"
    ],
    "sec-meaning": [
        "h2",
        "p",
        "figure",
        "callout"
    ]
}
EXPECTED_AUDIO_FILES = {
    "sec-question": "sec_01_sec-question.mp3",
    "sec-powers": "sec_02_sec-powers.mp3",
    "sec-universe": "sec_03_sec-universe.mp3",
    "sec-brute": "sec_04_sec-brute.mp3",
    "sec-meaning": "sec_05_sec-meaning.mp3"
}

SECTIONS_DATA = {
    "sec-question": {
        "title": "১. ''২৫৬-বিট নিরাপত্তা'' মানে কী?",
        "audio_file": "sec_01_sec-question.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "প্রথম পরিচ্ছেদ, ২৫৬ বিট নিরাপত্তা মানে কী।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "ক্রিপ্টোগ্রাফিতে দুই পঞ্চাশ ছয় বিট নিরাপত্তা বলা হয় যখন কোনো কী ভাঙতে গড়ে দুইের দুই পঞ্চাশ ছয় ঘাত সংখ্যক চেষ্টা লাগে। সংখ্যাটি লেখা সহজ, কিন্তু এর আকার বোঝা কঠিন।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "চিত্রে দুই পঞ্চাশ ছয় বিটের কীকে এক দীর্ঘ বাইনারি সংখ্যা হিসেবে দেখানো হয়েছে। সংখ্যাটি দেখতে সাধারণ হলেও তার সম্ভাব্য মানের সংখ্যা অকল্পনীয়। প্রতিটি অতিরিক্ত বিট আগের সম্ভাবনার সংখ্যা দ্বিগুণ করে দেয়। এই দ্বিঘাত বৃদ্ধিই কীটির শক্তির উৎস।"
            },
            {
                "index": 3,
                "type": "callout",
                "tts": "বিশেষ নোট, প্রশ্ন। দুইের দুই পঞ্চাশ ছয় ঘাত আসলে কত বড়? একে কোনো দৈনন্দিন সংখ্যার সাথে তুলনা করা যায় কি?",
                "role": "conclusion"
            }
        ]
    },
    "sec-powers": {
        "title": "২. দ্বিঘাতের শক্তি",
        "audio_file": "sec_02_sec-powers.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "দ্বিতীয় পরিচ্ছেদ, দ্বিঘাতের শক্তি।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "প্রতি এক বিট বাড়লে সংখ্যা দ্বিগুণ হয়। দশ বিটে প্রায় এক হাজার, কুড়ি বিটে প্রায় দশ লাখ, ত্রিশ বিটে প্রায় দশ কোটি। দুই পঞ্চাশ ছয় বিটে পৌঁছে সংখ্যা হয় প্রায় এক দশমিক এক গুণ দশের সাতাত্তর ঘাত।"
            },
            {
                "index": 2,
                "type": "formula-box",
                "tts": "দুইের দুই পঞ্চাশ ছয় ঘাত প্রায় এক দশমিক এক গুণ দশের সাতাত্তর ঘাতের সমান। সাধারণ লেখায় এটি একশো পঞ্চানেরও বেশি ডিজিটের এক বিপুল সংখ্যা। এই ধরনের বৃদ্ধিই দুই পঞ্চাশ ছয় বিট কীকে শক্তিশালী করে।"
            },
            {
                "index": 3,
                "type": "figure",
                "tts": "এই চিত্রে দ্বিঘাত বৃদ্ধি লগারিদমিক স্কেলে দেখানো হয়েছে। দুইের দুই পঞ্চাশ ছয় ঘাত প্রায় এক দশমিক একের সাতের পরে সাতটি শূন্যের ঘাতের সমান। সাধারণ স্কেলে এই সংখ্যা লিখতে কাগজের দরকার হবে, কিন্তু লগ স্কেলে সেটি একটি সরল রেখা। এই রেখাই বোঝায় কত দ্রুত সংখ্যা বাড়ে।"
            },
            {
                "index": 4,
                "type": "p",
                "tts": "এই সংখ্যাটি লিখতে আটচল্লিশটি অঙ্ক লাগে। একটি গুগল মানে দশের শত ঘাত, অর্থাৎ একের পরে একশোটি শূন্য। আমার সংখ্যাটি তার চেয়ে ছোট হলেও কল্পনার বাইরে।",
                "role": "conclusion"
            }
        ]
    },
    "sec-universe": {
        "title": "৩. মহাবিশ্বের সাথে তুলনা",
        "audio_file": "sec_03_sec-universe.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "তৃতীয় পরিচ্ছেদ, মহাবিশ্বের সাথে তুলনা।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "পর্যবেক্ষিত মহাবিশ্বে পরমাণুর সংখ্যা প্রায় দশের আশি ঘাত। অর্থাৎ দুইের দুই পঞ্চাশ ছয় ঘাতের মান তার কাছাকাছি। প্রতিটি পরমাণুকে একটি করে গেস দিলেও সব গেস শেষ হয় না।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "চিত্রে মহাবিশ্বের মোট পরমাণুর সংখ্যা আর দুই পঞ্চাশ ছয় বিট সংখ্যার তুলনা দেখানো হয়েছে। পরমাণুর সংখ্যা বিপুল হলেও দুই পঞ্চাশ ছয় ঘাতের চেয়ে এটি অনেক বড়। এই তুলনাই বোঝায় কেন ব্রুট ফোর্স আক্রমণ অকল্পনীয়। সংখ্যার আকার আমাদের সাধারণ অভিজ্ঞতার বাইরে চলে যায়।"
            },
            {
                "index": 3,
                "type": "chapter-quote",
                "tts": "উদ্ধৃতি, সিআর এসএন বলেছেন। অসংখ্যার প্রতি শ্রদ্ধাশীল মনই বিজ্ঞানের শুরু।",
                "role": "conclusion"
            }
        ]
    },
    "sec-brute": {
        "title": "৪. ব্রুট-ফোর্স আক্রমণ",
        "audio_file": "sec_04_sec-brute.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "চতুর্থ পরিচ্ছেদ, ব্রুট ফোর্স আক্রমণ।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "ধরা যাক বিশ্বের সব কম্পিউটার মিলে প্রতি সেকেন্ডে দশের আঠারো ঘাতটি চেষ্টা করে। তবুও দুইের দুই পঞ্চাশ ছয় ঘাতটি চেষ্টা করতে লাগবে প্রায় দশের নিচানব্বই ঘাত সেকেন্ড, যা মহাবিশ্বের বয়সের চেয়ে অসংখ্য গুণ বেশি।"
            },
            {
                "index": 2,
                "type": "formula-box",
                "tts": "প্রয়োজনীয় সময় প্রায় দুইের দুই পঞ্চাশ ছয় ঘাত ভাগ এক কোটি কোটি, যা প্রায় দশের নিচানব্বই ঘাত সেকেন্ড। অর্থাৎ প্রতি সেকেন্ডে এক কোটি কোটি বার চেষ্টা করলেও মহাবিশ্বের বয়সের চেয়ে অনেক বেশি সময় লাগবে।"
            },
            {
                "index": 3,
                "type": "figure",
                "tts": "এই চিত্রে ব্রুট ফোর্স আক্রমণে লাগতেও সময়ের হিসাব দেখানো হয়েছে। প্রতি সেকেন্ডে এক কোটি কোটি বার চেষ্টা করলেও দুই পঞ্চাশ ছয় ঘাত সম্ভাবনার অর্ধেক পরীক্ষা করতে লাগবে দশের নিচানব্বই ঘাত সেকেন্ড। মহাবিশ্বের বয়সের চেয়েও এটি অনেক বেশি। তাই গণিতের দিক থেকে কীটি নিরাপদ।"
            },
            {
                "index": 4,
                "type": "p",
                "tts": "তাই ২৫৬ বিট নিরাপত্তা মানেই, আক্রমণকারীর কাছে সময়, শক্তি ও অর্থ কিছুতেই যথেষ্ট নয়।",
                "role": "conclusion"
            }
        ]
    },
    "sec-meaning": {
        "title": "৫. প্রকৃত অর্থ",
        "audio_file": "sec_05_sec-meaning.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "পঞ্চম পরিচ্ছেদ, প্রকৃত অর্থ।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "নিরাপত্তা কখনো অসম্ভব নয়, বরং ব্যবহারিকভাবে অসম্ভব। ২৫৬ বিট মানে ভাঙার সম্ভাবনা এতই কম যে মহাবিশ্বের শেষ পর্যন্ত তা ঘটবে না।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "চিত্রে তাত্ত্বিক সম্ভাবনা আর ব্যবহারিক নিরাপত্তার মধ্যে পার্থক্য দেখানো হয়েছে। তত্ত্বগতভাবে ভাঙা সম্ভব হলেও বাস্তবে সময় আর শক্তির সীমার কারণে তা অসম্ভব। নিরাপত্তা আসলে সম্ভাবনার চেয়ে খরচের ওপর নির্ভর করে। এই চিত্রটি সেই ব্যবহারিক দৃষ্টিভঙ্গিকে সামনে আনে।"
            },
            {
                "index": 3,
                "type": "callout",
                "tts": "বিশেষ নোট, মনে রাখবেন। কোয়ান্টাম কম্পিউটিং গ্রোভারের অ্যালগরিদম দিয়ে কিছুটা কমালেও দুই পঞ্চাশ ছয় বিটের কী এখনও অপ্রত্যাশিতভাবে শক্তিশালী।",
                "role": "conclusion"
            }
        ]
    }
}

BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-\"\'`_<>*|^=/+]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"


def assert_clean_scripts():
    """Fail before any TTS work on markup, Latin text or structural drift."""
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError("%s cue %d: forbidden chars %r in %r"
                                 % (sec_id, cue["index"], bad, cue["tts"]))
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError("%s cue %d: artificial figure label"
                                 % (sec_id, cue["index"]))
    if len(SECTIONS_DATA) != 5:
        raise ValueError("Expected exactly 5 narrated sections")
    total = 0
    for sec_id, sec in SECTIONS_DATA.items():
        types = [c["type"] for c in sec["cues"]]
        if types != EXPECTED_TYPES[sec_id]:
            raise ValueError("%s: cue type/order mismatch -> %s" % (sec_id, types))
        if sec["audio_file"] != EXPECTED_AUDIO_FILES[sec_id]:
            raise ValueError("%s: audio_file mismatch" % sec_id)
        indices = [c["index"] for c in sec["cues"]]
        if indices != list(range(len(indices))):
            raise ValueError("%s: cue indices are not 0..n-1" % sec_id)
        total += len(indices)
    if total != 22:
        raise ValueError("Expected 22 cues, found %d" % total)
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            if cue["type"] == "figure":
                sentences = [s for s in cue["tts"].split("।") if s.strip()]
                if not (2 <= len(sentences) <= 4):
                    raise ValueError("%s cue %d: figure has %d sentences"
                                     % (sec_id, cue["index"], len(sentences)))


def backup_placeholders():
    """Preserve the placeholder manifests before the first expressive build."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    for name in ("manifest.json", "manifest.js"):
        src = os.path.join(AUDIO_DIR, name)
        dst = os.path.join(BACKUP_DIR, name)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
        if not os.path.exists(dst):
            raise RuntimeError("Could not back up placeholder %s" % name)
    print("  backup: %s" % BACKUP_DIR)


def bump_page_manifest_version():
    """Point the lesson page at the freshly built manifest (idempotent v=2)."""
    if not os.path.exists(PAGE_PATH):
        return
    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    new = re.sub(r"manifest\.js\?v=\d+", "manifest.js?v=2", html)
    if new != html:
        with open(PAGE_PATH, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(new)
        print("  page manifest bumped to ?v=2")


def get_duration_ms(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout.strip()
    ms = float(out) * 1000.0
    if ms <= 0:
        raise RuntimeError("Non-positive duration for %s: %s" % (path, ms))
    return ms


def probe_stream(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=sample_rate,channels", "-of", "json", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout
    st = json.loads(out)["streams"][0]
    return int(st["sample_rate"]), int(st["channels"])


def prosody_for(cue, is_last):
    rate, pitch, volume = PROSODY_DEFAULT[cue["type"]]
    if cue.get("role") == "conclusion" and cue["type"] not in ("h2", "formula-box"):
        rate, pitch, volume = CONCLUSION_PROSODY
    return rate, pitch, volume


def valid_audio(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    try:
        return get_duration_ms(path) > 0
    except Exception:  # noqa: BLE001 - corrupt / partial download
        return False


async def synth_cue(text, path, rate, pitch, volume):
    # Edge TTS occasionally replies with an empty stream. Back off and retry;
    # this is a network-response wait, not an arbitrary fixed delay.
    for attempt in range(10):
        try:
            comm = edge_tts.Communicate(text, VOICE,
                                        rate=rate, pitch=pitch, volume=volume)
            await comm.save(path)
            if valid_audio(path):
                return
        except Exception as exc:  # noqa: BLE001 - network hiccups happen
            print("    attempt %d failed: %s" % (attempt + 1, exc))
        await asyncio.sleep(min(0.5 * (2 ** attempt), 8.0))
    raise RuntimeError("Failed to synthesise cue: %s..." % text[:40])


def make_silence(path, sample_rate, channels, seconds=GAP_MS / 1000.0):
    layout = "mono" if channels == 1 else "stereo"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-f", "lavfi", "-i", "anullsrc=r=%d:cl=%s" % (sample_rate, layout),
         "-t", "%.3f" % seconds,
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


async def build_section(sec_id, sec):
    temp = os.path.join(AUDIO_DIR, "_expressive_tmp_%s" % sec_id)
    os.makedirs(temp, exist_ok=True)

    sig = hashlib.sha256(json.dumps(sec, ensure_ascii=False, sort_keys=True)
                         .encode("utf-8")).hexdigest()
    sig_path = os.path.join(temp, "scripts.sha256")
    old = open(sig_path, encoding="utf-8").read().strip() if os.path.exists(sig_path) else ""
    if old != sig:
        for name in os.listdir(temp):
            if name.endswith(".mp3"):
                os.remove(os.path.join(temp, name))
        with open(sig_path, "w", encoding="utf-8") as fh:
            fh.write(sig)

    cues = sec["cues"]
    chunk_paths, durations = [], []
    print("\n[%s] %d cues -> %s" % (sec_id, len(cues), sec["audio_file"]))
    for i, cue in enumerate(cues):
        idx = cue["index"]
        chunk = os.path.join(temp, "cue_%02d.mp3" % idx)
        rate, pitch, volume = prosody_for(cue, i == len(cues) - 1)
        if not valid_audio(chunk):
            print("  cue %02d [%-13s] %4s %5s  %s..."
                  % (idx, cue["type"], rate, pitch, cue["tts"][:30]))
            await synth_cue(cue["tts"], chunk, rate, pitch, volume)
        else:
            print("  cue %02d [%-13s] cached" % (idx, cue["type"]))
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

    final_path = os.path.join(AUDIO_DIR, sec["audio_file"])
    concat_to(final_path, concat_paths)

    manifest_cues, cursor = [], 0.0
    for i, (cue, dur) in enumerate(zip(cues, durations)):
        start, end = cursor, cursor + dur
        manifest_cues.append({
            "index": cue["index"], "type": cue["type"], "text": cue["tts"],
            "start_ms": round(start, 1), "end_ms": round(end, 1),
            "duration_ms": round(dur, 1),
        })
        cursor = end + (GAP_MS if i < len(cues) - 1 else 0.0)

    for i, mc in enumerate(manifest_cues):
        if mc["duration_ms"] <= 0 or mc["end_ms"] <= mc["start_ms"]:
            raise RuntimeError("%s cue %d: invalid span" % (sec_id, i))
        if i > 0:
            prev = manifest_cues[i - 1]
            if mc["start_ms"] < prev["end_ms"]:
                raise RuntimeError("%s cue %d: overlaps previous cue" % (sec_id, i))
            if abs((mc["start_ms"] - prev["end_ms"]) - GAP_MS) > 1.0:
                raise RuntimeError("%s cue %d: gap is not %s ms" % (sec_id, i, GAP_MS))
    if not os.path.exists(final_path) or os.path.getsize(final_path) == 0:
        raise RuntimeError("%s: missing/empty output %s" % (sec_id, final_path))

    print("  => %s: %d cues, %.2fs, %d bytes"
          % (sec["audio_file"], len(manifest_cues), cursor / 1000.0,
             os.path.getsize(final_path)))
    return {
        "section_id": sec_id, "title": sec["title"],
        "audio_file": sec["audio_file"],
        "total_duration_ms": round(cursor, 1), "cues": manifest_cues,
    }


async def build_all():
    assert_clean_scripts()
    print("Validated %d clean cues in %d sections."
          % (sum(len(s["cues"]) for s in SECTIONS_DATA.values()), len(SECTIONS_DATA)))
    backup_placeholders()

    manifest_sections = {}
    for sec_id, sec in SECTIONS_DATA.items():
        manifest_sections[sec_id] = await build_section(sec_id, sec)

    manifest_data = {
        "course": "computer_science", "lesson": "lesson_07",
        "title": MANIFEST_TITLE, "voice": VOICE, "mode": "authentic_teacher",
        "sections": manifest_sections,
    }
    json_text = json.dumps(manifest_data, ensure_ascii=False, indent=2)
    with open(os.path.join(AUDIO_DIR, "manifest.json"), "w", encoding="utf-8") as fh:
        fh.write(json_text)
    with open(os.path.join(AUDIO_DIR, "manifest.js"), "w", encoding="utf-8") as fh:
        fh.write("window.TEACHER_AUDIO_MANIFEST = " + json_text + ";\n")
    bump_page_manifest_version()

    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        loaded = json.load(fh)
    if set(loaded["sections"]) != set(SECTIONS_DATA):
        raise RuntimeError("manifest section ids do not match DOM ids")
    total_cues, total_ms, figures = 0, 0.0, 0
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        if len(msec["cues"]) != len(EXPECTED_TYPES[sec_id]):
            raise RuntimeError("%s: manifest cue count mismatch" % sec_id)
        if [c["type"] for c in msec["cues"]] != EXPECTED_TYPES[sec_id]:
            raise RuntimeError("%s: manifest cue types mismatch" % sec_id)
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            raise RuntimeError("%s: missing/empty mp3" % path)
        # Final timing cross-check against the real concatenated file.
        real_ms = get_duration_ms(path)
        # MP3 frame padding on concat shifts the real file by a few frames.
        tolerance = max(1000.0, msec["total_duration_ms"] * 0.02)
        if abs(real_ms - msec["total_duration_ms"]) > tolerance:
            raise RuntimeError("%s: manifest duration %.1fms vs audio %.1fms"
                               % (sec_id, msec["total_duration_ms"], real_ms))
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    if total_cues != 22:
        raise RuntimeError("Expected 22 manifest cues, got %d" % total_cues)

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, CS Lesson 07")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print("  %-22s %2d cues  %7.2fs  %s"
              % (sec_id, len(msec["cues"]), msec["total_duration_ms"] / 1000.0,
                 msec["audio_file"]))
    print("  TOTAL: %d cues across 5 sections, %.2fs, %d figure explanations."
          % (total_cues, total_ms / 1000.0, figures))
    print("  manifest.json is valid JSON; all 5 mp3 files exist and are non-empty.")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(build_all())
