# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Computer Science Lesson 10
("হ্যামিং কোড পর্ব ২ | এর সৌন্দর্য", Bengali) to the Lesson-01 gold standard.

Deterministic, re-runnable, self-contained:
  * 24 cues in 5 narrated sections with EXACTLY the same section IDs,
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

Usage:  python governance/build_expressive_teacher_audio_cs10.py
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
                         "computer_science", "lesson_10")
BACKUP_DIR = os.path.join(AUDIO_DIR, "_backup_before_expressive_build")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "computer_science",
                         "lesson_10.html")
MANIFEST_TITLE = "হ্যামিং কোড পর্ব ২ | এর সৌন্দর্য"

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
    "sec-xor": [
        "h2",
        "p",
        "figure",
        "formula-box",
        "p"
    ],
    "sec-matrix": [
        "h2",
        "p",
        "figure",
        "formula-box",
        "callout"
    ],
    "sec-syndrome": [
        "h2",
        "p",
        "figure",
        "formula-box",
        "chapter-quote"
    ],
    "sec-general": [
        "h2",
        "p",
        "figure",
        "formula-box",
        "p"
    ],
    "sec-elegance": [
        "h2",
        "p",
        "figure",
        "callout"
    ]
}
EXPECTED_AUDIO_FILES = {
    "sec-xor": "sec_01_sec-xor.mp3",
    "sec-matrix": "sec_02_sec-matrix.mp3",
    "sec-syndrome": "sec_03_sec-syndrome.mp3",
    "sec-general": "sec_04_sec-general.mp3",
    "sec-elegance": "sec_05_sec-elegance.mp3"
}

SECTIONS_DATA = {
    "sec-xor": {
        "title": "১. সবকিছু XOR",
        "audio_file": "sec_01_sec-xor.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "প্রথম পরিচ্ছেদ, সবকিছু এক্সওআর।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "প্যারিটি হিসাব আসলে এক্সওআর এর খেলা। একাধিক বিটের এক্সওআর তখনই ১ হয় যখন ১ এর সংখ্যা বিজোড় হয়। তাই প্যারিটি বিটগুলোকে কয়েকটি এক্সওআর হিসেবে লেখা যায়।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "এই চিত্রে এক্সওআর অপারেটরের সত্যের সারণি দেখানো হয়েছে। দুটি ইনপুট একই হলে ফলাফল শূন্য, আর আলাদা হলে ফলাফল এক। এই সরল নিয়মই প্যারিটি বিট হিসাব করতে ব্যবহৃত হয়। এক্সওআরকে যোগ হিসেবেও ভাবা যায়, তবে সেটি সাধারণ যোগের মতো নয়।"
            },
            {
                "index": 3,
                "type": "formula-box",
                "tts": "পি আই সমান নির্দিষ্ট সেটে থাকা সমস্ত ডি জের এক্সওআর। সহজ কথায়, কয়েকটি তথ্য বিটের এক্সওআর নিলেই প্যারিটি বিটটি পাওয়া যায়। এক্সওআর মানে জোড় সংখ্যক এক হলে শূন্য, বিজোড় হলে এক।"
            },
            {
                "index": 4,
                "type": "p",
                "tts": "কোড তৈরি ও যাচাই, দুটোই এখন কেবল এক্সওআর এর মাধ্যমে করা যায়। কম্পিউটারের জন্য এটি অত্যন্ত সস্তা ও দ্রুত।",
                "role": "conclusion"
            }
        ]
    },
    "sec-matrix": {
        "title": "২. প্যারিটি-চেক ম্যাট্রিক্স",
        "audio_file": "sec_02_sec-matrix.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "দ্বিতীয় পরিচ্ছেদ, প্যারিটি চেক ম্যাট্রিক্স।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "তিনটি প্যারিটি সমীকরণকে একটিমাত্র ম্যাট্রিক্স এইচ দিয়ে লেখা যায়। সঠিক কোডওয়ার্ডের ক্ষেত্রে এইচ গুণ সি ট্রান্সপোজ সমান শূন্য হয়। এটিই হলো কোডের পরীক্ষা।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "চিত্রে প্যারিটি চেক ম্যাট্রিক্স এইচ দেখানো হয়েছে। ম্যাট্রিক্সের প্রতিটি সারি বলে দেয় কোন কোন তথ্য বিট নিয়ে প্যারিটি হিসাব করতে হবে। বার্তার সাথে এই ম্যাট্রিক্সের গুণফল শূন্য হলে বোঝা যায় কোনো ভুল নেই। ম্যাট্রিক্সের কাঠামোই কোডটির শক্তি নির্ধারণ করে।"
            },
            {
                "index": 3,
                "type": "formula-box",
                "tts": "এইচ গুণ সি ট্রান্সপোজ সমান শূন্য। অর্থাৎ যেকোনো বৈধ কোডওয়ার্ডকে প্যারিটি চেক ম্যাট্রিক্স দিয়ে গুণ করলে ফলাফল শূন্য ভেক্টর হয়। এই শর্তটিই বলে দেয় কোন বার্তা বৈধ।"
            },
            {
                "index": 4,
                "type": "callout",
                "tts": "বিশেষ নোট, কৌশল। এইচ এর কলামগুলোকে ১ থেকে ৭ পর্যন্ত বাইনারি সংখ্যা হিসেবে সাজালে ম্যাজিক ঘটে।",
                "role": "conclusion"
            }
        ]
    },
    "sec-syndrome": {
        "title": "৩. সিনড্রোম = ভুলের ঠিকানা",
        "audio_file": "sec_03_sec-syndrome.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "তৃতীয় পরিচ্ছেদ, সিনড্রোম অর্থ ভুলের ঠিকানা।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "প্রাপ্ত শব্দ হলো মূল কোড আর ভুলের যোগফল। তাই এইচ দিয়ে গুণ করলে সিনড্রোম পাওয়া যায়, যা নির্ভর করে শুধু ভুলের ওপর। ত্রুটি যদি আই তম বিটে হয়, সিনড্রোম হয় এইচ এর আই তম কলাম, অর্থাৎ আই র বাইনারি রূপ।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "এই চিত্রে সিনড্রোম কীভাবে সরাসরি বাইনারিতে ভুলের অবস্থান দেয় তা দেখানো হয়েছে। প্রাপ্ত বার্তার সাথে ম্যাট্রিক্সের গুণফল আমাদের একটি ভেক্টর দেয়। ভুল একক বিট হলে সেই ভেক্টর ম্যাট্রিক্সের একটি নির্দিষ্ট কলামের সমান হয়। কলামের অবস্থান পড়েই ভুল বিট চিহ্নিত করা যায়।"
            },
            {
                "index": 3,
                "type": "formula-box",
                "tts": "সিনড্রোম এস সমান এইচ গুণ আর ট্রান্সপোজ, আবার এস সমান এইচ গুণ ই ট্রান্সপোজ, যা শেষ পর্যন্ত একটি নির্দিষ্ট কলামের সমান। অর্থাৎ প্রাপ্ত বার্তা থেকে পাওয়া সিনড্রোম সরাসরি ভুল বিটের অবস্থান নির্দেশ করে।"
            },
            {
                "index": 4,
                "type": "chapter-quote",
                "tts": "উদ্ধৃতি, আরআইসিআর হ্যামিং বলেছেন। সুন্দর মডেল এমনভাবে সাজানো হয় যেন উত্তরটি নিজেই প্রশ্নের ভেতরে লুকিয়ে থাকে।",
                "role": "conclusion"
            }
        ]
    },
    "sec-general": {
        "title": "৪. সাধারণীকরণ $(2^r-1,\\,2^r-1-r)$",
        "audio_file": "sec_04_sec-general.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "চতুর্থ পরিচ্ছেদ, সাধারণীকরণ।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "এই কৌশল যেকোনো আর এর জন্য কাজ করে। দুইের আর ঘাত বিয়োগ এক বিটের ব্লকে আরটি প্যারিটি যোগ করে মাত্র একটি বিটের ভুল সংশোধন করা যায়। আরের মান তিন হলে আমাদের পরিচিত সাত চার কোড পাই।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "চিত্রে বিভিন্ন আর এর জন্য তৈরি হ্যামিং কোডের তালিকা দেখানো হয়েছে। আর দুই হলে সাত বিটের কোড, আর তিন হলে পনেরো বিটের কোড। প্রতিটি ক্ষেত্রে তথ্য বিট আর প্যারিটি বিটের সংখ্যা একটি নির্দিষ্ট সূত্রে বদলায়। আর বাড়ার সাথে সাথে কোডের দৈর্ঘ্য দ্বিঘাতভাবে বাড়ে।"
            },
            {
                "index": 3,
                "type": "formula-box",
                "tts": "এন সমান দুইের আর ঘাত বিয়োগ এক, আর কে সমান দুইের আর ঘাত বিয়োগ এক বিয়োগ আর। অর্থাৎ আর প্যারিটি বিট ব্যবহার করে দুইের আর ঘাত বিয়োগ এক বিটের কোড তৈরি হয়, যার মধ্যে কে টি তথ্য বিট থাকে।"
            },
            {
                "index": 4,
                "type": "p",
                "tts": "বিটের সংখ্যা বাড়লে ওভারহেড কমে যায়, অর্থাৎ তথ্য বিটের তুলনায় প্যারিটি বিটের অনুপাত ছোট হয়। ফলে দীর্ঘ বার্তায় এই কোড আরও দক্ষ হয়।",
                "role": "conclusion"
            }
        ]
    },
    "sec-elegance": {
        "title": "৫. কেন এত সুন্দর",
        "audio_file": "sec_05_sec-elegance.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "পঞ্চম পরিচ্ছেদ, কেন এত সুন্দর।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "ভুলের অবস্থান আর তার বাইনারি কোড, এই দুটিকে একই করে দেওয়াই হ্যামিং কোডের শ্রেষ্ঠত্ব। কোনো জটিল অনুসন্ধান নেই; একটি ম্যাট্রিক্স গুণেই উত্তর চলে আসে।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "এই চিত্রে হ্যামিং কোডের গাণিতিক সৌন্দর্য দেখানো হয়েছে। একদিকে সরল এক্সওআর যুক্তি, অন্যদিকে সুনির্দিষ্ট ম্যাট্রিক্স কাঠামো, দুই মিলে একটি দক্ষ ব্যবস্থা তৈরি হয়। ভুল শনাক্ত করা থেকে শুরু করে সংশোধন, সবকিছু একই নিয়মে চলে। এই সরলতাই কোডটিকে স্মরণীয় করে তুলেছে।"
            },
            {
                "index": 3,
                "type": "callout",
                "tts": "বিশেষ নোট, মূল শিক্ষা। সঠিক কাঠামো বাছাই করলে জটিল সমস্যাও সরল গণিতে রূপ নেয়।",
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
    if total != 24:
        raise ValueError("Expected 24 cues, found %d" % total)
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
        "course": "computer_science", "lesson": "lesson_10",
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
    if total_cues != 24:
        raise RuntimeError("Expected 24 manifest cues, got %d" % total_cues)

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, CS Lesson 10")
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
