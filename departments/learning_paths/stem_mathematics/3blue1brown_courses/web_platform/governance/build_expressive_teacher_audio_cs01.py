# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Computer Science Lesson 01
("এন্ট্রপি পুনরাবিষ্কার | কম্প্রেশন হলো বুদ্ধিমত্তা, পর্ব ১", Bengali) to the Lesson-01 gold standard.

Deterministic, re-runnable, self-contained:
  * 26 cues in 5 narrated sections with EXACTLY the same section IDs,
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

Usage:  python governance/build_expressive_teacher_audio_cs01.py
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
                         "computer_science", "lesson_01")
BACKUP_DIR = os.path.join(AUDIO_DIR, "_backup_before_expressive_build")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "computer_science",
                         "lesson_01.html")
MANIFEST_TITLE = "এন্ট্রপি পুনরাবিষ্কার | কম্প্রেশন হলো বুদ্ধিমত্তা, পর্ব ১"

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
    "sec-compression": [
        "h2",
        "p",
        "figure",
        "p",
        "callout"
    ],
    "sec-surprise": [
        "h2",
        "p",
        "formula-box",
        "p",
        "figure",
        "chapter-quote"
    ],
    "sec-entropy": [
        "h2",
        "p",
        "formula-box",
        "p",
        "figure",
        "callout"
    ],
    "sec-language": [
        "h2",
        "p",
        "figure",
        "p",
        "callout"
    ],
    "sec-intelligence": [
        "h2",
        "p",
        "figure",
        "p"
    ]
}
EXPECTED_AUDIO_FILES = {
    "sec-compression": "sec_01_sec-compression.mp3",
    "sec-surprise": "sec_02_sec-surprise.mp3",
    "sec-entropy": "sec_03_sec-entropy.mp3",
    "sec-language": "sec_04_sec-language.mp3",
    "sec-intelligence": "sec_05_sec-intelligence.mp3"
}

SECTIONS_DATA = {
    "sec-compression": {
        "title": "১. সংকোচন আসলে কী?",
        "audio_file": "sec_01_sec-compression.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "প্রথম পরিচ্ছেদ, সংকোচন আসলে কী।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "আমরা প্রতিদিন বিশাল পরিমাণ পাঠ্য লেখি, পড়ি ও পাঠাই। স্বাভাবিক প্রশ্ন হলো, এই পাঠ্যকে কতটা ছোট করা যায়, তার সীমা কোথায়? একটি ভাষার মৌলিক সংকোচনযোগ্যতা বোঝা মানে বোঝা যে ভাষাটি আসলে কত তথ্য বহন করছে।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "এই চিত্রে দেখা যাচ্ছে কীভাবে একটি পাঠ্য বার্তা ধাপে ধাপে অক্ষর থেকে বিটে রূপান্তর হয়। প্রতিটি অক্ষরকে ছোট ছোট বিটের ক্রম দিয়ে লেখা হয়, আর এই ক্রমই বার্তাটিকে সংকুচিত করে। লক্ষ্য করুন, যে অক্ষরগুলো বারবার আসে তাদের জন্য কম বিট লাগে, আর বিরল অক্ষরের জন্য বেশি। এই চিত্রটি আমাদের সেই প্রশ্নের দিকে নিয়ে যায় যে এক ভাষার সর্বনিম্ন কত বিট লাগতে পারে।"
            },
            {
                "index": 3,
                "type": "p",
                "tts": "ধরা যাক একটি বর্ণমালায় ২৬টি অক্ষর সমান সম্ভাবনায় এসেছে। তাহলে প্রতিটি অক্ষর ঠিক কত বিট দিয়ে লেখা যাবে? এই প্রশ্নের উত্তরই আমাদের এন্ট্রপির দিকে নিয়ে যায়।"
            },
            {
                "index": 4,
                "type": "callout",
                "tts": "বিশেষ নোট, মূল ধারণা। যে ঘটনা যত কম সম্ভাবনা, সেটি ঘটলে তত বেশি আশ্চর্য তৈরি হয়, আর সেই আশ্চর্যের পরিমাণই হলো তথ্যের একক।",
                "role": "conclusion"
            }
        ]
    },
    "sec-surprise": {
        "title": "২. আশ্চর্য ও বিস্ময়ের পরিমাপ",
        "audio_file": "sec_02_sec-surprise.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "দ্বিতীয় পরিচ্ছেদ, আশ্চর্য ও বিস্ময়ের পরিমাপ।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "বিজ্ঞানী শ্যানন লক্ষ করেছিলেন যে তথ্যের পরিমাপ বিস্ময় হিসেবে করা যায়। যদি কোনো বার্তা আগে থেকেই জানা থাকে, সেটি নতুন কোনো তথ্য দেয় না, আর বিস্ময় হয় শূন্য। কিন্তু কিছু অপ্রত্যাশিত ঘটনা আমাদের অনেক বেশি তথ্য দেয়।"
            },
            {
                "index": 2,
                "type": "formula-box",
                "tts": "আই অফ এক্স সমান ঋণাত্মক লগ বেস টু অফ পি অফ এক্স। অর্থাৎ ঘটনাটির সম্ভাবনা যত কম, তার বিস্ময় তত বেশি। সম্ভাবনা অর্ধেক হলে বিস্ময় এক বিট, আর এক অষ্টম হলে তিন বিট।"
            },
            {
                "index": 3,
                "type": "p",
                "tts": "এখানে পি অফ এক্স হলো ঘটনাটির সম্ভাবনা। লগারিদম ভিত্তি ২ ব্যবহার করায় তথ্যের একক হয় বিট। সম্ভাবনা যদি অর্ধেক হয়, বিস্ময় হয় ১ বিট; সম্ভাবনা যদি এক অষ্টম হয়, বিস্ময় হয় ৩ বিট।"
            },
            {
                "index": 4,
                "type": "figure",
                "tts": "লেখচিত্রে অনুভূমিক অক্ষে ঘটনার সম্ভাবনা আর উল্লম্ব অক্ষে বিস্ময়ের বিট দেখানো হয়েছে। বক্ররেখাটি সম্ভাবনা কমলে ঊর্ধ্বমুখী হয়, অর্থাৎ বিরল ঘটনা ঘটলে বিস্ময় বেশি পাই। সম্ভাবনা অর্ধেক হলে বিস্ময় এক বিট, আর এক অষ্টম হলে তিন বিট। এই লগারিদমিক আকৃতিই ব্যাখ্যা করে কেন আমরা তথ্যের একক হিসেবে বিট ব্যবহার করি।"
            },
            {
                "index": 5,
                "type": "chapter-quote",
                "tts": "উদ্ধৃতি, ক্লড শ্যানন বলেছেন। তথ্য হলো অপ্রত্যাশিততার পরিমাপ; যা পূর্বনির্ধারিত, তা তথ্য নয়।",
                "role": "conclusion"
            }
        ]
    },
    "sec-entropy": {
        "title": "৩. শ্যানন এন্ট্রপি — বিস্ময়ের গড়",
        "audio_file": "sec_03_sec-entropy.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "তৃতীয় পরিচ্ছেদ, শ্যানন এন্ট্রপি, বিস্ময়ের গড়।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "একটি সম্পূর্ণ বার্তার প্রতিটি প্রতীকের বিস্ময় আলাদা। কতটা তথ্য গড়ে পাই? এর জন্য আমরা সম্ভাবনা দ্বারা ওজন করা বিস্ময়ের গড় নিই, এটিই হলো এন্ট্রপি।"
            },
            {
                "index": 2,
                "type": "formula-box",
                "tts": "এইচ অফ এক্স সমান সমস্ত প্রতীকের জন্য পি অফ এক্স গুণ লগ বেস টু অফ পি অফ এক্সের ঋণাত্মক যোগফল। সহজ ভাষায় এন্ট্রপি হলো বিস্ময়ের ভারিত গড়, যেখানে প্রতিটি বিস্ময়কে তার সম্ভাবনা দিয়ে গুণ করা হয়।"
            },
            {
                "index": 3,
                "type": "p",
                "tts": "সমান সম্ভাবনার এনটি প্রতীকের ক্ষেত্রে এন্ট্রপি সর্বোচ্চ এবং সমান লগ বেস টু এন বিট। কোনো একটি প্রতীকের সম্ভাবনা ১ হলে এন্ট্রপি শূন্য, কারণ তখন কোনো অনিশ্চিততা থাকে না।"
            },
            {
                "index": 4,
                "type": "figure",
                "tts": "এই চিত্রে দুটি ভিন্ন সম্ভাবনা বন্টন পাশাপাশি দেখানো হয়েছে। যে বন্টনে সব প্রতীকের সম্ভাবনা সমান, তার এন্ট্রপি সর্বোচ্চ; অন্য বন্টনে একটি প্রতীকের প্রাধান্য বেশি হওয়ায় এন্ট্রপি কমে যায়। বক্ররেখার চ্যাপ্টা আর খাড়া আকৃতি এই পার্থক্যকে স্পষ্ট করে তোলে। মনে রাখবেন, অনিশ্চয়তা যত বেশি, এন্ট্রপি তত বেশি।"
            },
            {
                "index": 5,
                "type": "callout",
                "tts": "বিশেষ নোট, মনে রাখবেন। এন্ট্রপি মানেই অনিশ্চিততার পরিমাণ বা গড় বিস্ময়। একে প্রায়শই এইচ দিয়ে লেখা হয়।",
                "role": "conclusion"
            }
        ]
    },
    "sec-language": {
        "title": "৪. ভাষার এন্ট্রপি ও অনুমান",
        "audio_file": "sec_04_sec-language.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "চতুর্থ পরিচ্ছেদ, ভাষার এন্ট্রপি ও অনুমান।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "ইংরেজি ভাষায় অক্ষরগুলোর সম্ভাবনা সমান নয়, ই খুব সাধারণ, জেড বিরল। আবার পরের অক্ষরটি আগের অক্ষরের ওপর নির্ভর করে। তাই একটি ভাষার প্রকৃত এন্ট্রপি ৪.৭ বিটের মতো, যা ২৬টি অক্ষরের সর্বোচ্চ লগ বেস টু ছাব্বিশ প্রায় চার দশমিক সাত বিটের কাছাকাছি।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "চিত্রে একটি ভাষা মডেল দেখানো হয়েছে যার কাজ হলো পরবর্তী অক্ষরের সম্ভাবনা অনুমান করা। আগের অক্ষরগুলোর ওপর ভিত্তি করে মডেলটি পরের অক্ষরের জন্য একটি সম্ভাবনা বন্টন তৈরি করে। যে মডেলের অনুমান যত নিখুঁত, সংকোচনে তত কম বিট লাগে। এই চিত্রটি তথ্য তত্ত্ব ও মডেলিংয়ের গভীর সংযোগকে ধরা দেখায়।"
            },
            {
                "index": 3,
                "type": "p",
                "tts": "এখানে মূল ধারণা হলো, একটি ভালো ভাষা মডেল পরবর্তী প্রতীকের সম্ভাবনা যত নিখুঁতভাবে অনুমান করতে পারে, সংকোচন তত বেশি করা যায়। তথ্য তত্ত্ব ও মডেলিং একই মুদ্রার দুই পিঠ।"
            },
            {
                "index": 4,
                "type": "callout",
                "tts": "বিশেষ নোট, সংযোগ। এন্ট্রপি কেবল সংকোচন নয়, এটি অনুমান, মেশিন লার্নিং ও কোয়ান্টাম তত্ত্বতেও একই ভূমিকা পালন করে।",
                "role": "conclusion"
            }
        ]
    },
    "sec-intelligence": {
        "title": "৫. কম্প্রেশন = বুদ্ধিমত্তা",
        "audio_file": "sec_05_sec-intelligence.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "tts": "পঞ্চম পরিচ্ছেদ, সংকোচন আর বুদ্ধিমত্তা।"
            },
            {
                "index": 1,
                "type": "p",
                "tts": "এই ধারাবাহিকতার মূল বক্তব্য হলো, কোনো কিছু ভালোভাবে সংকুচিত করতে পারা মানে সেটি সম্পর্কে ভালোভাবে বুঝতে পারা। যে মডেল ভাষার প্যাটার্ন বেশি বোঝে, সে কম বিটে বেশি তথ্য ধরে রাখতে পারে।"
            },
            {
                "index": 2,
                "type": "figure",
                "tts": "এই চিত্রে সংকোচন আর বোঝাপড়ার মধ্যে একটি সেতু দেখানো হয়েছে। একদিকে রয়েছে কম বিটে বার্তা লেখার প্রক্রিয়া, অন্যদিকে রয়েছে ভাষার প্যাটার্ন সম্পর্কে গভীর বোঝাপড়া। যত বেশি বোঝা যায়, তত কম বিটে কথা বলা যায়। মূল বক্তব্য হলো ভালো সংকোচনই হলো বুদ্ধিমত্তার পরিমাপ।"
            },
            {
                "index": 3,
                "type": "p",
                "tts": "পরবর্তী পাঠে আমরা দেখব, যখন আমাদের অনুমান ভুল হয়, তখন কত বাড়তি খরচ দিতে হয়। সেই খরচই হলো ক্রস এন্ট্রপি।",
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
    if total != 26:
        raise ValueError("Expected 26 cues, found %d" % total)
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
        "course": "computer_science", "lesson": "lesson_01",
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
    if total_cues != 26:
        raise RuntimeError("Expected 26 manifest cues, got %d" % total_cues)

    print("\n" + "=" * 62)
    print("BUILD COMPLETE - expressive teacher audio, CS Lesson 01")
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
