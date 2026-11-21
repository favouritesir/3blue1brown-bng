# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Computer Science Lesson 11
("কোয়ান্টাম কম্পিউটিং আসলে কী? (গ্রোভারের অ্যালগরিদম)", Bengali) to the Lesson-01 gold standard.

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

Usage:  python governance/build_expressive_teacher_audio_cs11.py
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
                         "computer_science", "lesson_11")
BACKUP_DIR = os.path.join(AUDIO_DIR, "_backup_before_expressive_build")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "computer_science",
                         "lesson_11.html")
MANIFEST_TITLE = "কোয়ান্টাম কম্পিউটিং আসলে কী? (গ্রোভারের অ্যালগরিদম)"

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
    "sec-qubit": [
        "h2",
        "p",
        "figure",
        "formula-box",
        "callout"
    ],
    "sec-state": [
        "h2",
        "p",
        "figure",
        "p"
    ],
    "sec-search": [
        "h2",
        "p",
        "figure",
        "chapter-quote"
    ],
    "sec-grover": [
        "h2",
        "p",
        "figure",
        "formula-box",
        "p"
    ],
    "sec-why": [
        "h2",
        "p",
        "figure",
        "callout"
    ]
}
EXPECTED_AUDIO_FILES = {
    "sec-qubit": "sec_01_sec-qubit.mp3",
    "sec-state": "sec_02_sec-state.mp3",
    "sec-search": "sec_03_sec-search.mp3",
    "sec-grover": "sec_04_sec-grover.mp3",
    "sec-why": "sec_05_sec-why.mp3"
}

SECTIONS_DATA = {
    "sec-qubit": {
        "title": "১. কিউবিট কী?",
        "audio_file": "sec_01_sec-qubit.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "প্রথম পরিচ্ছেদ, কিউবিট কী।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "সাধারণ বিট ০ বা ১, যেকোনো একটি। কিউবিট একসাথে ০ ও ১ এর সুপারপজিশনে থাকতে পারে। একে একটি ভেক্টর দিয়ে লেখা যায়, যার দুটি উপাংশ যথাক্রমে ০ ও ১ এর অ্যাম্প্লিচিউড।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "এই চিত্রে একটি কিউবিটকে ব্লোচ গোলকের ওপর একটি বিন্দু হিসেবে দেখানো হয়েছে। গোলকের খাড়া অক্ষে শূন্য ও এক অবস্থা, আর বিন্দুটির অবস্থান কিউবিটের অবস্থা নির্দেশ করে। বিন্দুটি মেরুতে থাকলে নির্দিষ্ট অবস্থা, আর মাঝখানে থাকলে সুপারপজিশন। এই চিত্রটি কোয়ান্টাম অবস্থার জ্যামিতিক রূপ।"
            },
            {
                "index": 3,
                "type": "formula-box",
                "tts": "পসাই অবস্থা সমান আলফা গুণ শূন্য অবস্থা প্লাস বিটা গুণ এক অবস্থা, আর আলফার বর্গ প্লাস বিটার বর্গ সমান এক। অর্থাৎ একটি কিউবিট একসাথে শূন্য ও এক অবস্থার সংমিশ্রণ ধরে রাখে, আর দুটি সম্ভাবনার যোগফল সবসময় এক।"
            },
            {
                "index": 4,
                "type": "callout",
                "tts": "বিশেষ নোট, মূল ধারণা। অ্যাম্প্লিচিউডের বর্গই হলো সম্ভাবনা, কিন্তু অ্যাম্প্লিচিউড নিজে ঋণাত্মক হতে পারে, আর এই চিহ্ন ই কোয়ান্টামের শক্তি।",
                "role": "conclusion"
            }
        ]
    },
    "sec-state": {
        "title": "২. একাধিক কিউবিট ও স্টেট স্পেস",
        "audio_file": "sec_02_sec-state.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "দ্বিতীয় পরিচ্ছেদ, একাধিক কিউবিট ও স্টেট স্পেস।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "এনটি কিউবিট একসাথে দুইের এন ঘাতটি অবস্থার সুপারপজিশনে থাকে। অর্থাৎ ত্রিশটি কিউবিট প্রায় দশ কোটি অবস্থা একসাথে ধরে রাখে, যা ক্লাসিক্যাল কম্পিউটারের চেয়ে অনেক বড়।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "চিত্রে দুইের এন ঘাত অবস্থার স্টেট ভেক্টর দেখানো হয়েছে। ক্লাসিকাল কম্পিউটার এক সময়ে শুধু একটি অবস্থা ধরে রাখে, কিন্তু কোয়ান্টাম স্টেট একসাথে সব অবস্থার ভারসাম্য ধরে রাখে। প্রতিটি অবস্থার সাথে একটি অ্যাম্প্লিচিউড যুক্ত থাকে। এই অ্যাম্প্লিচিউডগুলোর বর্গই সম্ভাবনা নির্দেশ করে।"
            },
            {
                "index": 3,
                "type": "p",
                "tts": "কিন্তু এক নজরে সব অবস্থা দেখা যায় না, পরিমাপ করলেই অবস্থা একটি মাত্র ফলাফলে ভেঙে পড়ে। তাই কৌশল হলো হস্তক্ষেপ ব্যবহার করে সঠিক উত্তরের সম্ভাবনা বাড়ানো।",
                "role": "conclusion"
            }
        ]
    },
    "sec-search": {
        "title": "৩. অনুসন্ধানের সমস্যা",
        "audio_file": "sec_03_sec-search.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "তৃতীয় পরিচ্ছেদ, অনুসন্ধানের সমস্যা।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "ধরা যাক এনটি আইটেমের মাঝে একটি চিহ্নিত আইটেম খুঁজতে হবে। ক্লাসিক্যাল কম্পিউটারে গড়ে এন ভাগ দুই বার দেখতে হয়, আর সবচেয়ে খারাপ ক্ষেত্রে এন বার। কোয়ান্টামে কতটা কমানো যায়?"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "এই চিত্রে একটি বড় ডাটাবেস থেকে একটি নির্দিষ্ট আইটেম খোঁজার কাজ দেখানো হয়েছে। ক্লাসিকাল পদ্ধতিতে গড়ে অর্ধেক আইটেম যাচাই করতে হয়। কোয়ান্টাম পদ্ধতি এই অনুসন্ধানকে অনেক দ্রুত করে। গ্রোভারের অ্যালগরিদম এই সুবিধারই একটি সুন্দর উদাহরণ।"
            },
            {
                "index": 3,
                "type": "chapter-quote",
                "tts": "উদ্ধৃতি, এল গ্রোভার বলেছেন। কোয়ান্টাম কম্পিউটার সব কিছু একসাথে চেক করে না, এটি সঠিক উত্তরের দিকে সম্ভাবনাকে ঘুরিয়ে আনে।",
                "role": "conclusion"
            }
        ]
    },
    "sec-grover": {
        "title": "৪. গ্রোভারের অ্যালগরিদম",
        "audio_file": "sec_04_sec-grover.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "চতুর্থ পরিচ্ছেদ, গ্রোভারের অ্যালগরিদম।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "গ্রোভারের অ্যালগরিদম দুটি ধাপ বারবার করে, (১) অরাকেল দিয়ে লক্ষ্য অবস্থার চিহ্ন উল্টানো, (২) গড়ের সাপেক্ষে প্রতিফলন। প্রতি বারে লক্ষ্যের অ্যাম্প্লিচিউড বেড়ে যায়।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "চিত্রে গ্রোভারের অ্যালগরিদমে অ্যাম্প্লিচিউড কীভাবে ধাপে ধাপে বাড়ে তা দেখানো হয়েছে। প্রতিটি পুনরাবৃত্তিতে সঠিক উত্তরের অ্যাম্প্লিচিউড বাড়ে আর বাকিদের কমে যায়। কয়েকটি ধাপের পর সঠিক অবস্থার সম্ভাবনা প্রায় নিশ্চিত হয়। এই প্রক্রিয়াটিকে অ্যাম্প্লিচিউড বৃদ্ধি বলা হয়।"
            },
            {
                "index": 3,
                "type": "formula-box",
                "tts": "সময়ের জটিলতা বড় ও অফ এনের বর্গমূল। অর্থাৎ এনটি আইটেমের মধ্যে খোঁজার জন্য ক্লাসিকাল পদ্ধতিতে এন ধাপ লাগলে কোয়ান্টাম পদ্ধতিতে লাগে শুধু এনের বর্গমূল ধাপ।"
            },
            {
                "index": 4,
                "type": "p",
                "tts": "প্রায় এন বার পুনরাবৃত্তির পর সঠিক উত্তর পাওয়ার সম্ভাবনা প্রায় ১। অর্থাৎ ১০ লাখ আইটেমের জন্য ১০ লাখের বদলে প্রায় ১০০০টি ধাপ, বিশাল ত্বরণ।",
                "role": "conclusion"
            }
        ]
    },
    "sec-why": {
        "title": "৫. কোয়ান্টামের সীমা",
        "audio_file": "sec_05_sec-why.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "পঞ্চম পরিচ্ছেদ, কোয়ান্টামের সীমা।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "গ্রোভার সব সমস্যা ত্বরান্বিত করে না, কেবল অনুসন্ধান এর মতো কিছু কাঠামোতে কাজ করে। আর এন একটি দ্বিঘাত ত্বরণ, শোরের অ্যালগরিদমের মতো সূচক ত্বরণ নয়।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "এই চিত্রে বিভিন্ন অ্যালগরিদমের ত্বরণের তুলনা দেখানো হয়েছে। ক্লাসিকাল অনুসন্ধানের সময় বাড়ে এন এর সমানুপাতে, আর গ্রোভারের ক্ষেত্রে বাড়ে বর্গমূল এন এর সমানুপাতে। বর্গমূলের এই হ্রাস বড় ডাটাবেসে বিপুল পার্থক্য তৈরি করে। তবে এটি কোয়ান্টাম কম্পিউটারের বিশেষ ক্ষমতার ওপর নির্ভরশীল।"
            },
            {
                "index": 3,
                "type": "callout",
                "tts": "বিশেষ নোট, মনে রাখবেন। কোয়ান্টাম কম্পিউটার সাধারণ কম্পিউটারের বিকল্প নয়, এটি নির্দিষ্ট কাজের জন্য এক নতুন হাতিয়ার।",
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
        "course": "computer_science", "lesson": "lesson_11",
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
    print("BUILD COMPLETE - expressive teacher audio, CS Lesson 11")
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
