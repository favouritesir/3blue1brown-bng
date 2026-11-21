# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Computer Science Lesson 08
("মহামারি সিমুলেশন: SIR মডেল", Bengali) to the Lesson-01 gold standard.

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

Usage:  python governance/build_expressive_teacher_audio_cs08.py
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
                         "computer_science", "lesson_08")
BACKUP_DIR = os.path.join(AUDIO_DIR, "_backup_before_expressive_build")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "computer_science",
                         "lesson_08.html")
MANIFEST_TITLE = "মহামারি সিমুলেশন: SIR মডেল"

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
    "sec-sir": [
        "h2",
        "p",
        "figure",
        "callout"
    ],
    "sec-eq": [
        "h2",
        "p",
        "formula-box",
        "figure",
        "p"
    ],
    "sec-r0": [
        "h2",
        "p",
        "formula-box",
        "figure",
        "chapter-quote"
    ],
    "sec-sim": [
        "h2",
        "p",
        "figure",
        "callout"
    ],
    "sec-flatten": [
        "h2",
        "p",
        "figure",
        "p"
    ]
}
EXPECTED_AUDIO_FILES = {
    "sec-sir": "sec_01_sec-sir.mp3",
    "sec-eq": "sec_02_sec-eq.mp3",
    "sec-r0": "sec_03_sec-r0.mp3",
    "sec-sim": "sec_04_sec-sim.mp3",
    "sec-flatten": "sec_05_sec-flatten.mp3"
}

SECTIONS_DATA = {
    "sec-sir": {
        "title": "১. S, I, R — তিনটি ভাগ",
        "audio_file": "sec_01_sec-sir.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "প্রথম পরিচ্ছেদ, এস, আই, আর, তিনটি ভাগ।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "মহামারি মডেলে জনসংখ্যাকে তিন ভাগে ভাগ করা হয়, সাসপেক্টেড (এস, সংক্রমিত হতে পারে), ইনফেক্টেড (আই, বর্তমানে অসুস্থ) ও রিকাভার্ড (আর, সেরে গেছে বা মারা গেছে)। সময়ের সাথে এই তিনের অনুপাত বদলাতে থাকে।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "এই চিত্রে এস আই আর মডেলের তিনটি ভাগকে তিনটি পুকুরের মতো দেখানো হয়েছে। সংবেদনশীল, আক্রান্ত এবং আরোগ্য প্রাপ্ত, এই তিন ভাগের মধ্যে মানুষ সময়ের সাথে সাথে স্থানান্তরিত হয়। তীরগুলো দেখাচ্ছে কোন ভাগ থেকে কোন ভাগে লোক যাচ্ছে। মডেলটি সরল হলেও মহামারির মূল গতি ধরতে পারে।"
            },
            {
                "index": 3,
                "type": "callout",
                "tts": "বিশেষ নোট, ধারণা। রোগের বিস্তার নির্ভর করে কতজন সংক্রমিত আর কতজন সংবেদনশীল একে অপরের সাথে মিলছে তার ওপর।",
                "role": "conclusion"
            }
        ]
    },
    "sec-eq": {
        "title": "২. মডেলের সমীকরণ",
        "audio_file": "sec_02_sec-eq.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "দ্বিতীয় পরিচ্ছেদ, মডেলের সমীকরণ।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "সংক্রমিত হওয়ার হার এস ও আই র গুণফলের সমানুপাতিক, কারণ বেশি মানুষ মিললে বেশি সংক্রমণ। আবার অসুস্থ মানুষ সেরে যাওয়ার হার আই র সমানুপাতিক।"
            },
            {
                "index": 2,
                "type": "formula-box",
                "tts": "এসের পরিবর্তনের হার ঋণাত্মক বিটা গুণ এস গুণ আই। আইয়ের পরিবর্তনের হার বিটা গুণ এস গুণ আই বিয়োগ গ্যামা গুণ আই। আর আরের পরিবর্তনের হার গ্যামা গুণ আই। এই তিনটি সমীকরণ মিলে পুরো এস আই আর মডেলটি গঠন করে।"
            },
            {
                "index": 3,
                "type": "figure",
                "tts": "লেখচিত্রে সময়ের সাথে সাথে তিন ভাগের জনসংখ্যা কীভাবে বদলায় তা দেখানো হয়েছে। শুরুতে আক্রান্তের সংখ্যা ক্রমশ বাড়ে আর সংবেদনশীলের সংখ্যা কমে। কিছুক্ষণ পর আক্রান্ত বক্ররেখা শীর্ষে পৌঁছে নিচে নামে, আর আরোগ্য প্রাপ্তের সংখ্যা বাড়তে থাকে। এই বক্ররেখার আকৃতি কোভিডের সময় আমরা সবাই দেখেছি।"
            },
            {
                "index": 4,
                "type": "p",
                "tts": "এই সরল সমীকরণগুলোই পুরো মহামারির গতিপথ প্রভাবিত করে, ধন্যবাদ কম্পিউটার সিমুলেশনের।",
                "role": "conclusion"
            }
        ]
    },
    "sec-r0": {
        "title": "৩. $R_0$ — মূল সংখ্যা",
        "audio_file": "sec_03_sec-r0.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "তৃতীয় পরিচ্ছেদ, আর নল, মূল সংখ্যা।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "একজন অসুস্থ মানুষ গড়ে যতজনকে সংক্রমিত করে, তা হলো আর নল। আর নল একের বেশি হলে মহামারি ছড়ায়, আর একের কম হলে তা শেষ হয়ে যায়। সাধারণত একজন থেকে দুই থেকে তিনজনের কাছে রোগ ছড়ায়।"
            },
            {
                "index": 2,
                "type": "formula-box",
                "tts": "আর নল সমান বিটা ভাগ গ্যামা। বিটা হলো সংক্রমণের হার আর গ্যামা হলো আরোগ্যের হার। আর নল একের বেশি হলে মহামারি ছড়ায়, আর একের কম হলে তা কমে যায়।"
            },
            {
                "index": 3,
                "type": "figure",
                "tts": "চিত্রে আর নলের মান বেশি হলে সংক্রমণ বক্ররেখা কীভাবে খাড়া হয়ে যায় তা দেখানো হয়েছে। আর নল বড় মানে এক আক্রান্ত ব্যক্তি গড়ে অনেকজনের কাছে রোগ ছড়ায়। ফলে আক্রান্তের বক্ররেখা দ্রুত ঊর্ধ্বমুখী হয়। আর নল একের নিচে নামলে মহামারি ধীরে ধীরে কমে যায়।"
            },
            {
                "index": 4,
                "type": "chapter-quote",
                "tts": "উদ্ধৃতি, ৩বিই১বিআরএন বলেছেন। একটি ছোট্ট সংখ্যা, আর নল, পুরো নীতির দিক নির্ধারণ করে।",
                "role": "conclusion"
            }
        ]
    },
    "sec-sim": {
        "title": "৪. সিমুলেশন ও অনিশ্চয়তা",
        "audio_file": "sec_04_sec-sim.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "চতুর্থ পরিচ্ছেদ, সিমুলেশন ও অনিশ্চয়তা।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "কম্পিউটারে আমরা লাখো এজেন্ট তৈরি করে তাদের মাঝে রোগ ছড়িয়ে দিতে পারি। প্রতিটি সিমুলেশনে ফল কিছুটা আলাদা হয়, এতে বোঝা যায় ভবিষ্যৎ কতটা অনিশ্চিত।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "এই চিত্রে এজেন্ট ভিত্তিক মহামারি সিমুলেশন দেখানো হয়েছে। প্রতিটি ছোট বিন্দু একজন মানুষ, আর রঙ তার অবস্থা নির্দেশ করে। মানুষজন চলাফেরা করার সাথে সাথে সংক্রমণ ছড়ায়। এই সিমুলেশন দেখে বোঝা যায় সরল মডেলও বাস্তব আচরণ কতটা ভালোভাবে ধরতে পারে।"
            },
            {
                "index": 3,
                "type": "callout",
                "tts": "বিশেষ নোট, শিক্ষা। মডেল ভবিষ্যৎ ভবিষ্যদ্বাণী করে না, এটি দেখায় কোন পরিস্থিতি কতটা সম্ভব।",
                "role": "conclusion"
            }
        ]
    },
    "sec-flatten": {
        "title": "৫. বক্ররেখা চ্যাপ্টা করা",
        "audio_file": "sec_05_sec-flatten.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "পঞ্চম পরিচ্ছেদ, বক্ররেখা চ্যাপ্টা করা।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "দূরত্ব, মাস্ক বা টিকা কমালে কমে, ফলে আর নল কমে। সংক্রমিতদের সংখ্যার শীর্ষ নিচে নামে ও সময়ে ছড়িয়ে পড়ে। এটিই ফ্ল্যাটেন ই সিআরই, হাসপাতালের চাপ কমায়।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "চিত্রে খাড়া আর চ্যাপ্টা সংক্রমণ বক্ররেখার তুলনা দেখানো হয়েছে। খাড়া বক্ররেখায় একসাথে অনেক মানুষ আক্রান্ত হয়ে হাসপাতালের ওপর চাপ তৈরি করে। চ্যাপ্টা বক্ররেখায় আক্রান্তের সংখ্যা কমে সময়ের দিকে ছড়িয়ে যায়। মূল বক্তব্য হলো সময় কেনা মানেই চাপ কমানো।"
            },
            {
                "index": 3,
                "type": "p",
                "tts": "আচরণের ছোট পরিবর্তন মডেলে বড় প্রভাব ফেলে, এই শিক্ষা কেবল মহামারি নয়, অনেক সামাজিক ব্যবস্থার ক্ষেত্রেও প্রয়োজনীয়।",
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
        "course": "computer_science", "lesson": "lesson_08",
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
    print("BUILD COMPLETE - expressive teacher audio, CS Lesson 08")
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
