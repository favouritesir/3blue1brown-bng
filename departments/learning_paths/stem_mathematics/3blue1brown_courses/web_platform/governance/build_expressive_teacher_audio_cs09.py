# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Computer Science Lesson 09
("হ্যামিং কোড ও ত্রুটি সংশোধন", Bengali) to the Lesson-01 gold standard.

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

Usage:  python governance/build_expressive_teacher_audio_cs09.py
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
                         "computer_science", "lesson_09")
BACKUP_DIR = os.path.join(AUDIO_DIR, "_backup_before_expressive_build")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "computer_science",
                         "lesson_09.html")
MANIFEST_TITLE = "হ্যামিং কোড ও ত্রুটি সংশোধন"

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
    "sec-problem": [
        "h2",
        "p",
        "figure",
        "callout"
    ],
    "sec-parity": [
        "h2",
        "p",
        "figure",
        "p"
    ],
    "sec-74": [
        "h2",
        "p",
        "figure",
        "formula-box",
        "chapter-quote"
    ],
    "sec-distance": [
        "h2",
        "p",
        "figure",
        "formula-box",
        "p"
    ],
    "sec-decode": [
        "h2",
        "p",
        "figure",
        "callout"
    ]
}
EXPECTED_AUDIO_FILES = {
    "sec-problem": "sec_01_sec-problem.mp3",
    "sec-parity": "sec_02_sec-parity.mp3",
    "sec-74": "sec_03_sec-74.mp3",
    "sec-distance": "sec_04_sec-distance.mp3",
    "sec-decode": "sec_05_sec-decode.mp3"
}

SECTIONS_DATA = {
    "sec-problem": {
        "title": "১. ত্রুটি কেন হয়",
        "audio_file": "sec_01_sec-problem.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "প্রথম পরিচ্ছেদ, ত্রুটি কেন হয়।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "তথ্য যখন তারের মাধ্যমে বা ডিস্কে লেখা হয়, তখন কখনো কখনো একটি ০ হয়ে ১ বা ১ হয়ে ০ হয়ে যায়। প্রশ্ন হলো, এই ভুল কি শনাক্ত ও সংশোধন করা যায়?"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "এই চিত্রে একটি বিট উল্টে যাওয়ার ঘটনা দেখানো হয়েছে। ডিজিটাল তথ্য পাঠানোর সময় কখনো কখনো শূন্যের বদলে এক বা একের বদলে শূন্য হয়ে যায়। বার্তাটি বদলে গেলেও আমরা সাধারণত বুঝতে পারি না। হ্যামিং কোড এই ধরনের একক বিটের ভুল শনাক্ত করে সংশোধন করে।"
            },
            {
                "index": 3,
                "type": "callout",
                "tts": "বিশেষ নোট, সমস্যা। শুধু ভুল ধরা যথেষ্ট নয়, আমরা চাই ভুলটি ঠিকও করে দিতে।",
                "role": "conclusion"
            }
        ]
    },
    "sec-parity": {
        "title": "২. প্যারিটি বিট",
        "audio_file": "sec_02_sec-parity.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "দ্বিতীয় পরিচ্ছেদ, প্যারিটি বিট।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "সবচেয়ে সরল পদ্ধতি হলো একটি প্যারিটি বিট যোগ করা, যার মান এমনভাবে বাছাই করা হয় যাতে মোট ১ এর সংখ্যা জোড় হয়। একটি বিট বদলালে এই নিয়ম ভেঙে যায়, তাই ভুল ধরা পড়ে।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "চিত্রে প্যারিটি বিট যোগ করে ভুল শনাক্তের পদ্ধতি দেখানো হয়েছে। বিটগুলোর একের সংখ্যা জোড় না বিজোড় তা প্যারিটি বিট নির্দেশ করে। যদি একটি বিট উল্টায়, তবে প্যারিটির হিসাব মিলে না এবং বোঝা যায় ভুল হয়েছে। তবে শুধু প্যারিটি দিয়ে ভুলের অবস্থান বের করা যায় না।"
            },
            {
                "index": 3,
                "type": "p",
                "tts": "কিন্তু এক প্যারিটি বিট দিয়ে শুধু ভুল আছে বোঝা যায়, কোথায় ভুল তা বোঝা যায় না। তার জন্য লাগবে একাধিক প্যারিটি বিট।",
                "role": "conclusion"
            }
        ]
    },
    "sec-74": {
        "title": "৩. (7,4) হ্যামিং কোড",
        "audio_file": "sec_03_sec-74.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "তৃতীয় পরিচ্ছেদ, সাত চার হ্যামিং কোড।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "রিচার্ড হ্যামিং দেখিয়েছিলেন, ৪টি তথ্য বিটের সাথে ৩টি প্যারিটি বিট যোগ করে ৭ বিটের একটি শব্দ তৈরি করা যায়, যা যেকোনো একটি বিটের ভুল সংশোধন করতে পারে।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "এই চিত্রে সাত চার হ্যামিং কোডের বিটের অবস্থান চিহ্নিত দেখানো হয়েছে। চারটি তথ্য বিটের সাথে তিনটি প্যারিটি বিট যোগ করে মোট সাত বিট তৈরি হয়। প্রতিটি প্যারিটি বিট নির্দিষ্ট কয়েকটি অবস্থান যাচাই করে। তিনটি যাচাইয়ের ফলাফল একসাথে ভুল বিটের অবস্থান বলে দেয়।"
            },
            {
                "index": 3,
                "type": "formula-box",
                "tts": "চারটি তথ্য বিট প্লাস তিনটি প্যারিটি বিট সমান মোট সাত বিট। সাত চার কোডে আমরা চারটি তথ্য বিটের সাথে তিনটি প্যারিটি বিট যোগ করি। এই তিনটি বিটই ভুল শনাক্ত ও সংশোধনের জন্য ব্যবহৃত হয়।"
            },
            {
                "index": 4,
                "type": "chapter-quote",
                "tts": "উদ্ধৃতি, আরআইসিআর হ্যামিং বলেছেন। কম্পিউটার ভুল করবে, এটা অনিবার্য; আমাদের কাজ হলো সেই ভুলকে নির্ভুলভাবে ঠিক করা।",
                "role": "conclusion"
            }
        ]
    },
    "sec-distance": {
        "title": "৪. হ্যামিং দূরত্ব",
        "audio_file": "sec_04_sec-distance.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "চতুর্থ পরিচ্ছেদ, হ্যামিং দূরত্ব।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "দুটি কোডওয়ার্ডের যতগুলো অবস্থানে বিট আলাদা, তা হলো হ্যামিং দূরত্ব। একটি ভুল সংশোধন করতে হলে কোডওয়ার্ডগুলোর মধ্যে ন্যূনতম দূরত্ব কমপক্ষে ৩ হতে হবে।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "চিত্রে বিভিন্ন কোডওয়ার্ডের মধ্যকার হ্যামিং দূরত্ব দেখানো হয়েছে। দূরত্ব মানে দুটি বার্তার কতগুলো বিট আলাদা। কোডওয়ার্ডগুলো যত দূরে থাকবে, এক বিটের ভুল তত সহজে শনাক্ত হবে। ন্যূনতম দূরত্বের ওপর ভিত্তি করেই কতটি ভুল সংশোধন করা যায় তা নির্ধারণ হয়।"
            },
            {
                "index": 3,
                "type": "formula-box",
                "tts": "ন্যূনতম দূরত্ব অন্তত দুই গুণ সংশোধনযোগ্য ভুলের সংখ্যা প্লাস একের সমান হতে হবে। অর্থাৎ কতগুলো ভুল সংশোধন করতে চাই, তার ওপর ভিত্তি করে কোডের ন্যূনতম দূরত্ব নির্ধারণ করা হয়।"
            },
            {
                "index": 4,
                "type": "p",
                "tts": "টি সংখ্যক ভুল সংশোধন করতে ন্যূনতম দূরত্ব দুই গুণ টি প্লাস এক হতে হবে। এই সীমাটিকেই হ্যামিং সীমা বলে।",
                "role": "conclusion"
            }
        ]
    },
    "sec-decode": {
        "title": "৫. ভুল সংশোধন",
        "audio_file": "sec_05_sec-decode.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "পঞ্চম পরিচ্ছেদ, ভুল সংশোধন।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "প্রাপ্ত সাত বিট শব্দের তিনটি প্যারিটি যাচাই করা হয়। তিনটি ফলাফল একসাথে একটি সিনড্রোম তৈরি করে, যা সরাসরি এক থেকে সাতের মধ্যে কোন বিটটি ভুল তা নির্দেশ করে। সেই বিটটি উল্টে দিলেই ঠিক কোডওয়ার্ড পাওয়া যায়।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "এই চিত্রে সিনড্রোম থেকে ভুল বিটের অবস্থান বের করার পদ্ধতি দেখানো হয়েছে। প্রাপ্ত বার্তার প্যারিটি যাচাই করে একটি ছোট বাইনারি সংখ্যা পাওয়া যায়, যাকে সিনড্রোম বলে। সিনড্রোমের মান সরাসরি সেই বিটের অবস্থান নির্দেশ করে। সেই বিটটি উল্টে দিলেই মূল বার্তা ফিরে আসে।"
            },
            {
                "index": 3,
                "type": "callout",
                "tts": "বিশেষ নোট, এখানেই সৌন্দর্য। তিনটি প্যারিটি বিটের অর্থ তিন বিট, তাই আটটি সম্ভাব্য সিনড্রোম তৈরি হয়। একটি অবস্থা বলে দেয় কোনো ভুল নেই, আর বাকি সাতটি নির্দেশ করে কোন বিট ভুল।",
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
        "course": "computer_science", "lesson": "lesson_09",
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
    print("BUILD COMPLETE - expressive teacher audio, CS Lesson 09")
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
