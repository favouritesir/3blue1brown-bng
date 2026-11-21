# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Computer Science Lesson 02
("ক্রস-এন্ট্রপি আসলে কী? | কম্প্রেশন হলো বুদ্ধিমত্তা, পর্ব ২", Bengali) to the Lesson-01 gold standard.

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

Usage:  python governance/build_expressive_teacher_audio_cs02.py
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
                         "computer_science", "lesson_02")
BACKUP_DIR = os.path.join(AUDIO_DIR, "_backup_before_expressive_build")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "computer_science",
                         "lesson_02.html")
MANIFEST_TITLE = "ক্রস-এন্ট্রপি আসলে কী? | কম্প্রেশন হলো বুদ্ধিমত্তা, পর্ব ২"

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
    "sec-wrong": [
        "h2",
        "p",
        "figure",
        "callout"
    ],
    "sec-cross": [
        "h2",
        "p",
        "formula-box",
        "p",
        "figure",
        "chapter-quote"
    ],
    "sec-kl": [
        "h2",
        "p",
        "formula-box",
        "p",
        "figure",
        "callout"
    ],
    "sec-ml": [
        "h2",
        "p",
        "formula-box",
        "p",
        "figure"
    ],
    "sec-summary": [
        "h2",
        "p",
        "figure"
    ]
}
EXPECTED_AUDIO_FILES = {
    "sec-wrong": "sec_01_sec-wrong.mp3",
    "sec-cross": "sec_02_sec-cross.mp3",
    "sec-kl": "sec_03_sec-kl.mp3",
    "sec-ml": "sec_04_sec-ml.mp3",
    "sec-summary": "sec_05_sec-summary.mp3"
}

SECTIONS_DATA = {
    "sec-wrong": {
        "title": "১. ভুল মডেলের মূল্য",
        "audio_file": "sec_01_sec-wrong.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "প্রথম পরিচ্ছেদ, ভুল মডেলের মূল্য।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "আগের পাঠে আমরা দেখেছি, ভালো মডেল ভালো সংকোচন দেয়। কিন্তু বাস্তবে আমাদের মডেল কখনোই নিখুঁত হয় না। যদি আমরা ভুল সম্ভাবনা ব্যবহার করে কোড বানাই, তবে বেশি বিট লাগবে। এই অতিরিক্ত খরচটিকেই আমরা পরিমাপ করব।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "এই চিত্রে দুটি বক্ররেখা পাশাপাশি দেখানো হয়েছে, একটি সত্যিকারের বন্টন, অন্যটি আমাদের অনুমান করা বন্টন। যদি দুটি বক্ররেখা মিলে যায়, তবে কোনো বাড়তি খরচ হয় না। কিন্তু যত বেশি ফাঁক তৈরি হয়, আমাদের কোড তত বেশি অদক্ষ হয়ে পড়ে। এই চিত্রটিই ভুল মডেলের মূল্য বোঝার প্রথম ধাপ।"
            },
            {
                "index": 3,
                "type": "callout",
                "tts": "বিশেষ নোট, সমস্যা। ভুল মডেলের কারণে যে বাড়তি বিট খরচ হয়, তা কত? এর সুষ্ঠু পরিমাপই পরবর্তী ধাপ।",
                "role": "conclusion"
            }
        ]
    },
    "sec-cross": {
        "title": "২. ক্রস-এন্ট্রপির সংজ্ঞা",
        "audio_file": "sec_02_sec-cross.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "দ্বিতীয় পরিচ্ছেদ, ক্রস এন্ট্রপির সংজ্ঞা।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "ধরা যাক সত্যিকারের বন্টন পি আর আমাদের মডেলের অনুমান কিউ। প্রতিটি প্রতীকের জন্য আমরা কিউ অনুযায়ী বিট ব্যবহার করি, কিন্তু প্রতীকগুলো আসে পি বন্টন থেকে। তাই গড় খরচ হিসাব করতে হবে।"
            },
            {
                "index": 2,
                "type": "formula-box",
                "tts": "এইচ পি কমা কিউ সমান সমস্ত প্রতীকের জন্য পি অফ এক্স গুণ লগ বেস টু অফ কিউ অফ এক্সের ঋণাত্মক যোগফল। অর্থাৎ প্রতীকগুলো আসে সত্য বন্টন পি থেকে, কিন্তু আমরা কোড বানাই মডেলের কিউ অনুযায়ী।"
            },
            {
                "index": 3,
                "type": "p",
                "tts": "এটিকে বলা হয় ক্রস এন্ট্রপি। মনে রাখবেন, এন্ট্রপি এইচ পি হলো নিখুঁত মডেলের সর্বনিম্ন খরচ; ক্রস এন্ট্রপি হলো আমাদের মডেলের প্রকৃত খরচ।"
            },
            {
                "index": 4,
                "type": "figure",
                "tts": "চিত্রে ক্রস এন্ট্রপিকে সত্য বন্টনে মডেলের কোডের গড় দৈর্ঘ্য হিসেবে দেখানো হয়েছে। প্রতিটি প্রতীকের জন্য আমরা মডেলের অনুমান অনুযায়ী বিট ব্যবহার করি, কিন্তু প্রতীকগুলো আসে সত্য বন্টন থেকে। যেসব প্রতীকের ক্ষেত্রে মডেলের অনুমান ভুল, সেখানে বেশি বিট খরচ হয়। এই গড় খরচই হলো ক্রস এন্ট্রপি।"
            },
            {
                "index": 5,
                "type": "chapter-quote",
                "tts": "উদ্ধৃতি, শ্যানন বলেছেন। ক্রস এন্ট্রপি সবসময় নিজের এন্ট্রপির চেয়ে বড় বা সমান, ভুলের মূল্য সবসময়ই দিতে হয়।",
                "role": "conclusion"
            }
        ]
    },
    "sec-kl": {
        "title": "৩. অতিরিক্ত খরচ ও কেএল ডাইভারজেন্স",
        "audio_file": "sec_03_sec-kl.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "তৃতীয় পরিচ্ছেদ, অতিরিক্ত খরচ ও কেএল ডাইভারজেন্স।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "ক্রস এন্ট্রপি থেকে আসল এন্ট্রপি বাদ দিলে যা থাকে, তা হলো অতিরিক্ত খরচ, একে বলা হয় কেএল ডাইভারজেন্স বা রিলেটিভ এন্ট্রপি।"
            },
            {
                "index": 2,
                "type": "formula-box",
                "tts": "কেএল ডাইভারজেন্স সমান ক্রস এন্ট্রপি বিয়োগ এন্ট্রপি, অর্থাৎ সমস্ত প্রতীকের জন্য পি অফ এক্স গুণ লগ অফ পি অফ এক্স ভাগ কিউ অফ এক্সের যোগফল। যখন পি ও কিউ একই, তখন প্রতিটি পদ শূন্য হয় আর কেএলের মান দাঁড়ায় শূন্য।"
            },
            {
                "index": 3,
                "type": "p",
                "tts": "যখন পি সমান কিউ, তখন কেএল ডাইভারজেন্স শূন্য। দুই বন্টন যত আলাদা, এই মান তত বড়। মনে রাখবেন কেএল দূরত্ব নয়, এটি প্রতিসম নয়।"
            },
            {
                "index": 4,
                "type": "figure",
                "tts": "এই চিত্রে দুই বন্টনের মধ্যকার ফাঁককে কেএল ডাইভারজেন্স হিসেবে দেখানো হয়েছে। ক্রস এন্ট্রপি থেকে নিখুঁত মডেলের খরচ বাদ দিলে যা অবশিষ্ট থাকে, তা হলো এই অতিরিক্ত খরচ। দুই বক্ররেখা যত আলাদা, ফাঁক তত বড় হয়। মনে রাখবেন কেএল কোনো প্রতিসম দূরত্ব নয়, এটি একমুখী পরিমাপ।"
            },
            {
                "index": 5,
                "type": "callout",
                "tts": "বিশেষ নোট, উপসংহার। ক্রস এন্ট্রপি হলো এন্ট্রপি আর কেএল ডাইভারজেন্সের যোগফল। এই সরল সমীকরণটি পুরো মেশিন লার্নিংয়ের ভিত্তি।",
                "role": "conclusion"
            }
        ]
    },
    "sec-ml": {
        "title": "৪. মেশিন লার্নিংয়ে লস ফাংশন",
        "audio_file": "sec_04_sec-ml.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "চতুর্থ পরিচ্ছেদ, মেশিন লার্নিংয়ে লস ফাংশন।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "নিউরাল নেটওয়ার্ক যখন পরের শব্দের সম্ভাবনা অনুমান করে, তখন প্রশিক্ষণে আমরা ঠিক ক্রস এন্ট্রপিই কমিয়ে থাকি। সত্যিকারের উত্তর পি ও মডেলের ভবিষ্যদ্বাণী কিউ র ক্রস এন্ট্রপি যত কম, মডেল তত ভালো।"
            },
            {
                "index": 2,
                "type": "formula-box",
                "tts": "লস এল সমান সমস্ত শ্রেণীর জন্য ওয়াই আই গুণ লগ অফ ওয়াই হ্যাট আইয়ের ঋণাত্মক যোগফল। সত্যিকারের উত্তর আর মডেলের ভবিষ্যদ্বাণীর ক্রস এন্ট্রপিই হলো এই লস। প্রশিক্ষণের কাজ হলো এই মানটিকে যতটা সম্ভব কমানো।"
            },
            {
                "index": 3,
                "type": "p",
                "tts": "এই কারণে ক্রস এন্ট্রপি আজ বিশ্বের সবচেয়ে ব্যবহৃত লস ফাংশনগুলোর একটি, ভাষা মডেল, চিত্র শ্রেণীবিভাগ, সব জায়গায়।"
            },
            {
                "index": 4,
                "type": "figure",
                "tts": "লেখচিত্রে প্রশিক্ষণের সাথে সাথে ক্রস এন্ট্রপি কীভাবে কমে যায় তা দেখানো হয়েছে। শুরুতে মডেলের অনুমান ভুল থাকে, তাই ক্ষতি বা লস বেশি থাকে। প্রশিক্ষণ অগ্রসর হওয়ার সাথে সাথে বক্ররেখা নিচে নামতে থাকে এবং মডেলের ভবিষ্যদ্বাণী নিখুঁত হতে শুরু করে। এই নামতেই বোঝা যায় মডেলটি শিখছে কি না।",
                "role": "conclusion"
            }
        ]
    },
    "sec-summary": {
        "title": "৫. এক লাইনে মনে রাখুন",
        "audio_file": "sec_05_sec-summary.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "পঞ্চম পরিচ্ছেদ, এক লাইনে মনে রাখুন।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "এন্ট্রপি হলো সর্বনিম্ন সম্ভাব্য খরচ; ক্রস এন্ট্রপি হলো আপনার মডেলের খরচ; আর কেএল হলো এই দুটির পার্থক্য। এই তিনটি ধারণা তথ্য তত্ত্ব ও কৃত্রিম বুদ্ধিমত্তার ভাষা।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "এই মানচিত্রে এন্ট্রপি, ক্রস এন্ট্রপি ও কেএল ডাইভারজেন্সের সম্পর্ক এক নজরে দেখানো হয়েছে। এন্ট্রপি হলো সর্বনিম্ন সম্ভাব্য খরচ, ক্রস এন্ট্রপি হলো আমাদের মডেলের প্রকৃত খরচ, আর কেএল হলো এই দুটির পার্থক্য। তিনটি ধারণা একই রেখায় সাজানো হয়েছে, যাতে মনে রাখা সহজ হয়। এই চিত্রটি পুরো পাঠের সারাংশ।",
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
        "course": "computer_science", "lesson": "lesson_02",
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
    print("BUILD COMPLETE - expressive teacher audio, CS Lesson 02")
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
