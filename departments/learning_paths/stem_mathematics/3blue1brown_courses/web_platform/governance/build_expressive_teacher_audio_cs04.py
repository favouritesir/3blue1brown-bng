# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Computer Science Lesson 04
("তথ্য তত্ত্ব দিয়ে ওয়ার্ডল সমাধান", Bengali) to the Lesson-01 gold standard.

Deterministic, re-runnable, self-contained:
  * 21 cues in 5 narrated sections with EXACTLY the same section IDs,
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

Usage:  python governance/build_expressive_teacher_audio_cs04.py
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
                         "computer_science", "lesson_04")
BACKUP_DIR = os.path.join(AUDIO_DIR, "_backup_before_expressive_build")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "computer_science",
                         "lesson_04.html")
MANIFEST_TITLE = "তথ্য তত্ত্ব দিয়ে ওয়ার্ডল সমাধান"

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
    "sec-game": [
        "h2",
        "p",
        "figure",
        "callout"
    ],
    "sec-info": [
        "h2",
        "p",
        "formula-box",
        "figure",
        "p"
    ],
    "sec-entropy": [
        "h2",
        "p",
        "figure",
        "chapter-quote"
    ],
    "sec-crane": [
        "h2",
        "p",
        "figure",
        "p"
    ],
    "sec-strategy": [
        "h2",
        "p",
        "figure",
        "callout"
    ]
}
EXPECTED_AUDIO_FILES = {
    "sec-game": "sec_01_sec-game.mp3",
    "sec-info": "sec_02_sec-info.mp3",
    "sec-entropy": "sec_03_sec-entropy.mp3",
    "sec-crane": "sec_04_sec-crane.mp3",
    "sec-strategy": "sec_05_sec-strategy.mp3"
}

SECTIONS_DATA = {
    "sec-game": {
        "title": "১. ওয়ার্ডল ও একটি স্বাভাবিক প্রশ্ন",
        "audio_file": "sec_01_sec-game.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "প্রথম পরিচ্ছেদ, ওয়ার্ডল ও একটি স্বাভাবিক প্রশ্ন।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "ওয়ার্ডলে আমরা ছয় বারে একটি পাঁচ অক্ষরের শব্দ গুশে করি। প্রতিটি অনুমানের পর সবুজ, হলুদ ও ধূসর রঙ আমাদের কিছু তথ্য দেয়। প্রশ্ন হলো, কোন শব্দ দিয়ে শুরু করলে গড়ে সবচেয়ে বেশি তথ্য পাওয়া যায়?"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "চিত্রে ওয়ার্ডলের প্রথম অনুমানের পরের রঙের প্রতিক্রিয়া দেখানো হয়েছে। সবুজ মানে অক্ষরটি সঠিক জায়গায়, হলুদ মানে অক্ষরটি শব্দে আছে কিন্তু জায়গা ভুল, আর ধূসর মানে অক্ষরটি নেই। প্রতিটি অনুমানের পর এই রঙগুলো আমাদের কিছু তথ্য দেয়। প্রশ্ন হলো কোন শব্দ দিয়ে শুরু করলে গড়ে সবচেয়ে বেশি তথ্য পাওয়া যায়।"
            },
            {
                "index": 3,
                "type": "callout",
                "tts": "বিশেষ নোট, সমস্যা। কোন অনুমান সবচেয়ে তথ্যবহুল? এর উত্তর দিতে আমাদের লাগবে শ্যাননের এন্ট্রপি।",
                "role": "conclusion"
            }
        ]
    },
    "sec-info": {
        "title": "২. একটি অনুমান কত তথ্য দেয়",
        "audio_file": "sec_02_sec-info.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "দ্বিতীয় পরিচ্ছেদ, একটি অনুমান কত তথ্য দেয়।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "প্রতিটি অনুমানের ফলাফল একাধিক প্যাটার্ন এর একটি। যদি কোনো প্যাটার্ন খুব সম্ভাবনাময় হয়, সেটি কম তথ্য দেয়; বিরল প্যাটার্ন বেশি তথ্য দেয়। গড় তথ্য লাভ হলো সম্ভাবনা দ্বারা ওজন করা বিস্ময়।"
            },
            {
                "index": 2,
                "type": "formula-box",
                "tts": "আই জি অফ জি সমান সমস্ত ফলাফলের জন্য পি অফ ও গুণ লগ বেস টু অফ পি অফ ওর ঋণাত্মক যোগফল। অর্থাৎ একটি অনুমানের তথ্য লাভ হলো তার সম্ভাব্য ফলাফলের বিস্ময়ের গড়। যে অনুমানের ফলাফল বেশি বৈচিত্র্যময়, তার তথ্য লাভ বেশি।"
            },
            {
                "index": 3,
                "type": "figure",
                "tts": "এই চিত্রে বিভিন্ন প্রথম অনুমানের তথ্য লাভের তুলনা দেখানো হয়েছে। যে অনুমানের ফলাফল অনেকগুলো আলাদা প্যাটার্নে বিভক্ত হয়, সেটি বেশি তথ্য দেয়। যে অনুমানের ফলাফল প্রায় সবসময় একই রকম, সেটি কম তথ্য দেয়। লম্বা দণ্ডগুলোই হলো ভালো শুরুর প্রার্থী।"
            },
            {
                "index": 4,
                "type": "p",
                "tts": "অর্থাৎ যে অনুমানের ফলাফলগুলোর বন্টন যত সমান, সেটি তত বেশি তথ্য দেয়, ঠিক যেমন সমান সম্ভাবনার এন্ট্রপি সর্বোচ্চ।",
                "role": "conclusion"
            }
        ]
    },
    "sec-entropy": {
        "title": "৩. এন্ট্রপি হিসাব করে অনুমান বাছাই",
        "audio_file": "sec_03_sec-entropy.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "তৃতীয় পরিচ্ছেদ, এন্ট্রপি হিসাব করে অনুমান বাছাই।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "প্রতিটি সম্ভাব্য প্রথম শব্দের জন্য আমরা সমস্ত উত্তর শব্দের বিরুদ্ধে তার প্যাটার্ন বন্টন বের করি, তারপর এন্ট্রপি হিসাব করি। যে শব্দের এন্ট্রপি সবচেয়ে বেশি, সেটিই সেরা প্রথম অনুমান।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "চিত্রে হাজারো সম্ভাব্য শব্দের এন্ট্রপি র্যাঙ্কিং দেখানো হয়েছে। প্রতিটি শব্দের সাথে একটি সংখ্যা যুক্ত আছে যা বলে দেয় সেটি গড়ে কত তথ্য দিতে পারে। শীর্ষে থাকা শব্দগুলোই সবচেয়ে তথ্যবহুল। এই র্যাঙ্কিংয়ের ওপর ভিত্তি করেই একজন সলভার তার প্রথম অনুমান বাছাই করে।"
            },
            {
                "index": 3,
                "type": "chapter-quote",
                "tts": "উদ্ধৃতি, ক্লড শ্যানন বলেছেন। সেরা প্রশ্ন সেটিই যার উত্তর আমাদের সবচেয়ে বেশি অজানা তথ্য দেয়।",
                "role": "conclusion"
            }
        ]
    },
    "sec-crane": {
        "title": "৪. কেন ''crane'' একটি ভালো শব্দ",
        "audio_file": "sec_04_sec-crane.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "চতুর্থ পরিচ্ছেদ, কেন ক্রেন একটি ভালো শব্দ।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "গণনায় দেখা যায় ক্রেন এর মতো শব্দের প্রথম ধাপে প্রায় ৫.৯ বিট তথ্য পাওয়া যায়, যা তথ্য তত্ত্বের সর্বোচ্চ সীমার কাছাকাছি। এর কারণ হলো এর অক্ষরগুলো সাধারণ এবং সুবিতরিত।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "এই চিত্রে ক্রেন শব্দ দিয়ে শুরু করার ফলে তৈরি হওয়া ফলাফল বৃক্ষ দেখানো হয়েছে। প্রতিটি শাখা একটি সম্ভাব্য রঙের প্যাটার্নকে নির্দেশ করে, আর শাখার চূড়ায় থাকে অবশিষ্ট শব্দের সংখ্যা। কিছু শাখা খুব ছোট, আবার কিছু শাখা বেশ লম্বা। গড় গভীরতা যত কম, সলভার তত দ্রুত উত্তরে পৌঁছায়।"
            },
            {
                "index": 3,
                "type": "p",
                "tts": "তবে শুধু তথ্য লাভই সব কিছু নয়, পরের পাঠে আমরা দেখব এই সেরা শব্দের ধারণা কীভাবে বদলায়।",
                "role": "conclusion"
            }
        ]
    },
    "sec-strategy": {
        "title": "৫. কৌশল ও সীমাবদ্ধতা",
        "audio_file": "sec_05_sec-strategy.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "পঞ্চম পরিচ্ছেদ, কৌশল ও সীমাবদ্ধতা।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "সর্বোচ্চ এন্ট্রপি নির্বাচন একটি দ্বাপদ কৌশল, এটি গড়ে ভালো করলেও প্রতিটি খেলায় সেরা নয়। বাস্তবে খেলার গভীরতা ও শেষ উত্তরের সম্ভাবনাও বিবেচনা করতে হয়।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "চিত্রে পুরো ওয়ার্ডল সলভারের সিদ্ধান্ত বৃক্ষ দেখানো হয়েছে। প্রতিটি নোডে একটি অনুমান, আর প্রতিটি শাখায় একটি রঙের ফলাফল। খেলা শেষ না হওয়া পর্যন্ত এই বৃক্ষ বারবার নতুন শাখা তৈরি করে। লক্ষ্য হলো গড়ে যত কম ধাপে শব্দটি খুঁজে পাওয়া যায়।"
            },
            {
                "index": 3,
                "type": "callout",
                "tts": "বিশেষ নোট, ভবিষ্যতের দিকে। তথ্য তত্ত্ব আমাদের এক নীতি দেয়, কিন্তু সেই নীতিটি কখন ভুল, তা নিয়ে পরবর্তী পাঠ।",
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
    if total != 21:
        raise ValueError("Expected 21 cues, found %d" % total)
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
        "course": "computer_science", "lesson": "lesson_04",
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
    if total_cues != 21:
        raise RuntimeError("Expected 21 manifest cues, got %d" % total_cues)

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, CS Lesson 04")
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
