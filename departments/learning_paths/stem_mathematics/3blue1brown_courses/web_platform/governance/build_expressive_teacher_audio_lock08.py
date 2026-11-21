# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Lockdown Math Lesson 08
("Proof of the Basel problem", Bengali) to the gold standard —
warm, natural, fully phonetic figure phrasing, NO artificial figure label.

Deterministic, re-runnable, self-contained:
  * 4 cues in 4 narrated sections with EXACTLY the same section IDs, audio_file
    names, cue type and cue order as the live narration-engine DOM.
    Authoritative DOM extraction (governance/_extract_lock08_dom.py, via the
    narration_engine.js selector) confirmed:
        sec-01-basel-intro            -> ['h2']   (1 cue)
        sec-02-lighthouse-physics     -> ['h2']   (1 cue)
        sec-03-pythagorean-lighthouse -> ['h2']   (1 cue)
        sec-04-circle-limit           -> ['h2']   (1 cue)
    Total = 4 cues. All sec-*-study / sec-interactive-lab / sec-quizzes /
    sec-formulas-glossary sections carry data-no-narration="true" and are
    deliberately excluded. There are NO quiz / media-tab cue types.
  * Each narrated section has only ONE h2 cue, so that single cue is written as
    a rich, warm 4-6 sentence Bengali teacher explanation of that section's
    topic (Basel problem Σ1/n²=π²/6, lighthouse physics / inverse-square law,
    Pythagorean pairing of lighthouses, circle limit to π²/6), with the h2
    title woven in naturally. The artificial label "চিত্র প্রদর্শনী" is NEVER
    used — teacher phrasing uses "চিত্রে দেখা যাচ্ছে" or direct explanation.
  * Fully phonetic spoken Bengali (no TeX / Latin / markup). Safeguards:
        Basel       -> বাসেল,       lighthouse -> লাইটহাউস,
        Pythagorean -> পাইথাগোরিয়ান, infinite series -> অসীম ধারা,
        pi          -> পাই.
  * Per-cue prosody via edge_tts.Communicate(rate=, pitch=, volume=):
        h2 -5% / +2Hz (warm, slightly slower section opening),
        conclusion -3% (final lesson summary, sec-04).
    A real 350 ms silence chunk is inserted between cues (manifest invariant).
  * ffmpeg -c copy concat into the EXISTING mp3 names.
  * Writes manifest.json + manifest.js (window.TEACHER_AUDIO_MANIFEST) + the
    per-section *_cues.json sidecars, all with exact measured ms timings.
  * Bumps the page cache-buster manifest.js?v=N -> ?v=N+1.
  * verify_in_chrome() re-checks everything headlessly with channel=chrome.
  * The _backup_before_expressive_build/ folder is NEVER touched. No other
    lesson or library is touched.

Usage:
  python governance/build_expressive_teacher_audio_lock08.py
  python governance/build_expressive_teacher_audio_lock08.py --verify-only
"""

import os
import re
import sys
import json
import hashlib
import asyncio
import subprocess

import edge_tts

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
VOICE = "bn-BD-PradeepNeural"
GAP_MS = 350.0
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))            # .../governance
WORKSPACE = os.path.dirname(SCRIPT_DIR)                             # .../web_platform
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio",
                         "lockdown_math", "lesson_08")
PAGE_PATH = os.path.join(WORKSPACE, "courses", "lockdown_math", "lesson_08.html")
VERIFY_RESULT = os.path.join(SCRIPT_DIR, "_verify_lock08_result.json")
MANIFEST_TITLE = "অধ্যায় ০৮ — ব্যাসেল সমস্যা ও পাই স্কয়ার বাই ৬ এর সমাধান"

# Prosody keyed by cue type: (rate, pitch, volume)
PROSODY_DEFAULT = {
    "h2": ("-5%", "+2Hz", "+0%"),   # warm, slightly slower section opening
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")   # gentle closing cadence

ALLOWED_CUE_TYPES = set(PROSODY_DEFAULT) | {"conclusion"}

# Exact DOM block-type sequence per narrated section (from narration_engine).
EXPECTED_TYPES = {
    "sec-01-basel-intro":            ["h2"],
    "sec-02-lighthouse-physics":     ["h2"],
    "sec-03-pythagorean-lighthouse": ["h2"],
    "sec-04-circle-limit":           ["h2"],
}
# Audio-file names are the EXISTING manifest keys (canonical section ids).
EXPECTED_AUDIO_FILES = {
    "sec-01-basel-intro":            "sec-01-basel-intro.mp3",
    "sec-02-lighthouse-physics":     "sec-02-lighthouse-physics.mp3",
    "sec-03-pythagorean-lighthouse": "sec-03-pythagorean-lighthouse.mp3",
    "sec-04-circle-limit":           "sec-04-circle-limit.mp3",
}
EXPECTED_COUNT = {sid: 1 for sid in EXPECTED_TYPES}
EXPECTED_TOTAL = 4

# --------------------------------------------------------------------------- #
# Embedded, fully phonetic, expressive Bengali scripts (4 cues)
# --------------------------------------------------------------------------- #
SECTIONS_DATA = {
    "sec-01-basel-intro": {
        "title": "১. ব্যাসেল সমস্যার পটভূমি ও পাই-এর রহস্যময় প্রবেশ",
        "audio_file": "sec-01-basel-intro.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "আমাদের প্রথম পরিচ্ছেদ, বাসেল সমস্যার পটভূমি ও পাই এর রহস্যময় প্রবেশ। "
             "সতেরো শতকের মাঝামাঝি ইতালীয় গণিতবিদ পিয়েত্রো মেঙ্গোলি এই প্রশ্নটি তুলেছিলেন, "
             "ধনাত্মক পূর্ণসংখ্যার বর্গের অন্যোন্যকের এক অসীম ধারা যোগ করলে ঠিক কত পাওয়া যায়। "
             "জ্যাকব ও ইয়োহান বার্নৌলির মতো দিকপালরা বহু দশক চেষ্টা করেও এর নিখুঁত মান বের করতে "
             "পারেননি, ধারাটি বারের পর বার ছোট হয়ে প্রায় এক দশমিক ছয়চারের কাছে স্থির হচ্ছিল। "
             "চিত্রে দেখা যাচ্ছে প্রথম কয়েকটি পদ, এক, এক চতুর্থাংশ, এক নবমাংশ, এক ষোড়শাংশ, "
             "ধীরে ধীরে কমে যাচ্ছে আর নিচের রেখার দিকে এগিয়ে যাচ্ছে। "
             "তারপর ১৭৩৫ সালে মাত্র আটাইশ বছর বয়সী লেওনার্ড অয়লার সবাইকে চমকে দিয়ে দেখালেন "
             "এই যোগফল আর কিছুই নয়, বরং পাই এর বর্গ ভাগ ছয়, আর কোথাও বৃত্ত না থাকলেও হঠাৎ "
             "পাই এসে হাজির হওয়া এই রহস্যই আমাদের যাত্রার শুরু।"},
        ],
    },

    "sec-02-lighthouse-physics": {
        "title": "২. পদার্থবিজ্ঞানের দৃষ্টিতে: বাতিঘর ও আলোর তীব্রতা",
        "audio_file": "sec-02-lighthouse-physics.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "দ্বিতীয় পরিচ্ছেদে আমরা দেখব পদার্থবিজ্ঞানের দৃষ্টিতে বাতিঘর ও আলোর তীব্রতা, "
             "অর্থাৎ কীভাবে একটি লাইটহাউসের আলো আমাদের চোখে উজ্জ্বল দেখায়। "
             "আলোর বিপরীত বর্গীয় সূত্র বলে, কোনো বিন্দু উৎস থেকে আলো চারপাশের গোলকীয় পৃষ্ঠে "
             "সমানভাবে ছড়িয়ে পড়ে, তাই দূরত্ব দ্বিগুণ হলে সেই পৃষ্ঠের ক্ষেত্রফল চারগুণ হয়ে "
             "উজ্জ্বলতা নেমে আসে এক চতুর্থাংশে। "
             "অর্থাৎ যে দূরত্বে বাতিঘরটি আছে, তার বর্গের ব্যস্তানুপাতিকই হলো আপাত উজ্জ্বলতা, "
             "এক ভাগ দূরত্বের বর্গ, আর এই নিয়মটিই আমাদের জ্যামিতিক প্রমাণের ভিত্তি। "
             "চিত্রে দেখা যাচ্ছে একটিমাত্র আলোর উৎস থেকে বলয়ের মতো আলো ছড়িয়ে যাচ্ছে, "
             "বাইরের বলয়ের ক্ষেত্রফল বাড়ার সাথে সাথে প্রতি একক জায়গায় আলো কমে যাচ্ছে। "
             "এখন যদি মূলবিন্দু থেকে এক, দুই, তিন, চার একক দূরত্বে সরলরেখায় একের পর এক "
             "লাইটহাউস বসাই, তবে দর্শকের চোখে মোট উজ্জ্বলতা দাঁড়ায় এক যোগ এক চতুর্থাংশ যোগ "
             "এক নবমাংশ যোগ এক ষোড়শাংশ, অর্থাৎ ঠিক সেই বাসেল ধারা যার যোগফল আমরা খুঁজছি।"},
        ],
    },

    "sec-03-pythagorean-lighthouse": {
        "title": "৩. পিথাগোরাস উপপাদ্য ও বাতির সংমিশ্রণ",
        "audio_file": "sec-03-pythagorean-lighthouse.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts":
             "তৃতীয় পরিচ্ছেদে আমরা দেখব পাইথাগোরিয়ান বা পিথাগোরাসের উপপাদ্য ব্যবহার করে "
             "বাতির সংমিশ্রণ, অর্থাৎ কীভাবে দুটি বাতিঘরকে একটিমাত্র বাতিতে রূপান্তর করা যায়। "
             "ধরা যাক একটি সমকোণী ত্রিভুজ, যার সমকোণ সংলগ্ন দুটি বাহুর প্রান্তে দুটি লাইটহাউস "
             "আছে এবং অতিভুজের বিপরীত কোণে দাঁড়িয়ে আছেন এক পর্যবেক্ষক। "
             "পাইথাগোরিয়ান উপপাদ্য আর ক্ষেত্রফলের সূত্র একসাথে ব্যবহার করলে দেখা যায়, "
             "এক ভাগ এ বর্গ যোগ এক ভাগ বি বর্গের যোগফল ঠিক এক ভাগ এইচ বর্গের সমান, "
             "যেখানে এইচ হলো অতিভুজের ওপর লম্ব দূরত্ব। "
             "চিত্রে দেখা যাচ্ছে সমকোণী ত্রিভুজটি, দুই বাহু বরাবর দুটি বাতি, আর অতিভুজে লম্ব "
             "হয়ে নামা একটা রেখা যা দুই বাতির আলোকে এক জায়গায় মিলিয়ে দিচ্ছে। "
             "এর মানে হলো, দুটি পরস্পর লম্বালম্বি বাতিঘরের মিলিত উজ্জ্বলতা অবিকল সেই একক বাতির "
             "উজ্জ্বলতার সমান যা ঠিক এইচ দূরত্বে অবস্থিত, আর এই চমৎকার কৌশলের মাধ্যমেই "
             "জটিল বাতির সারিকে ধাপে ধাপে বৃত্তের ওপর সাজানো যাবে।"},
        ],
    },

    "sec-04-circle-limit": {
        "title": "৪. বৃত্তীয় প্রতিসাম্য ও পাই স্কয়ার বাই ৬ এর চূড়ান্ত প্রমাণ",
        "audio_file": "sec-04-circle-limit.mp3",
        "cues": [
            {"index": 0, "type": "h2", "role": "conclusion",
             "tts":
             "চতুর্থ ও শেষ পরিচ্ছেদে আমরা দেখব বৃত্তীয় প্রতিসাম্য ও পাই স্কয়ার বাই ছয় এর "
             "চূড়ান্ত প্রমাণ, অর্থাৎ কীভাবে বাতিঘরের আলো শেষ পর্যন্ত পাইতে এসে পৌঁছায়। "
             "যখন বাতিঘরগুলোকে বৃত্তের পরিধিতে সমান ব্যবধানে বসিয়ে পাইথাগোরিয়ান দ্বিগুণকরণের "
             "কৌশল বারবার প্রয়োগ করা হয়, তখন জ্যা আর চাপের দৈর্ঘ্যের অনুপাতটা সামনে চলে আসে। "
             "বৃত্তের ব্যাস যদি এক হয়, তবে কোণ থিটার জন্য জ্যার দৈর্ঘ্য হয় সাইন থিটা আর "
             "চাপের দৈর্ঘ্য হয় থিটা, কিন্তু অতি ক্ষুদ্র কোণে সাইন থিটা প্রায় থিটার সমান হয়ে "
             "যায়, আর এই সীমাটিই গণিতের সুন্দরতম উপহার। "
             "চিত্রে দেখা যাচ্ছে বৃত্তের চারপাশে সমান দূরত্বে সাজানো বাতিঘর, আর ক্রমশ ছোট হয়ে "
             "আসা জ্যাগুলো চাপের রেখার সাথে মিলে যাচ্ছে। "
             "অসীমের দিকে এই প্রতিসাম্যকে এগিয়ে নিয়ে গেলে বিজোড় পদগুলোর যোগফল দাঁড়ায় পাই এর "
             "বর্গ ভাগ আট, আর পূর্ণ ধারায় রূপান্তর করলে শেষ পর্যন্ত জন্ম নেয় পাই এর বর্গ ভাগ "
             "ছয়, অর্থাৎ এক যোগ এক চতুর্থাংশ যোগ এক নবমাংশ এবং এভাবে চলতে থাকা অসীম ধারার "
             "যোগফল ঠিক পাই স্কয়ার বাই ছয়, আর এই অমর ফলাফলের মাধ্যমেই আমাদের পাঠের শেষ কথা।"},
        ],
    },
}

# --------------------------------------------------------------------------- #
# Validation / helpers
# --------------------------------------------------------------------------- #
# Latin letters, TeX/markup, long dashes and ASCII hyphens are forbidden.
BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"
NATURAL_FIGURE = "চিত্রে দেখা যাচ্ছে"

# h2 meaning woven in: a shared key phrase from each section's displayed title.
KEY_PHRASES = {
    "sec-01-basel-intro":            "বাসেল সমস্যার পটভূমি",
    "sec-02-lighthouse-physics":     "বাতিঘর ও আলোর তীব্রতা",
    "sec-03-pythagorean-lighthouse": "পাইথাগোরিয়ান",
    "sec-04-circle-limit":           "বৃত্তীয় প্রতিসাম্য",
}

# Phonetic safeguards that must survive in the spoken text.
REQUIRED_PHRASES = {
    "sec-01-basel-intro":            ["বাসেল", "অসীম ধারা", "পাই"],
    "sec-02-lighthouse-physics":     ["লাইটহাউস", "বিপরীত বর্গীয় সূত্র"],
    "sec-03-pythagorean-lighthouse": ["পাইথাগোরিয়ান"],
    "sec-04-circle-limit":           ["পাই", "বৃত্তীয় প্রতিসাম্য"],
}
GLOBAL_REQUIRED = ["বাসেল", "লাইটহাউস", "পাইথাগোরিয়ান", "অসীম ধারা", "পাই"]


def narration_text_blobs():
    blobs = [MANIFEST_TITLE]
    for sec_id, sec in SECTIONS_DATA.items():
        blobs.append(sec["title"])
        for cue in sec["cues"]:
            blobs.append(cue["tts"])
    return blobs


def assert_clean_scripts():
    """Fail before any TTS work if a script has markup/Latin/the banned label."""
    assert PROSODY_DEFAULT == {"h2": ("-5%", "+2Hz", "+0%")}, "prosody spec drift"

    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars {bad!r}")
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: artificial figure label present")
            if NATURAL_FIGURE not in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: missing natural figure phrasing")

    if len(SECTIONS_DATA) != 4:
        raise ValueError("Expected exactly 4 narrated sections")
    total = 0
    for sec_id, sec in SECTIONS_DATA.items():
        types = [c["type"] for c in sec["cues"]]
        if types != EXPECTED_TYPES[sec_id]:
            raise ValueError(f"{sec_id}: cue type/order mismatch -> {types}")
        if sec["audio_file"] != EXPECTED_AUDIO_FILES[sec_id]:
            raise ValueError(f"{sec_id}: audio_file mismatch")
        indices = [c["index"] for c in sec["cues"]]
        if indices != list(range(len(indices))):
            raise ValueError(f"{sec_id}: cue indices are not 0..n-1")
        if len(indices) != EXPECTED_COUNT[sec_id]:
            raise ValueError(f"{sec_id}: cue count mismatch")
        text = sec["cues"][0]["tts"]
        if KEY_PHRASES[sec_id] not in text:
            raise ValueError(f"{sec_id}: key h2 phrase missing")
        for phrase in REQUIRED_PHRASES.get(sec_id, []):
            if phrase not in text:
                raise ValueError(f"{sec_id}: phonetic safeguard missing -> {phrase}")
        # 4-6 natural Bengali sentences per explanation.
        sentences = [s for s in re.split(r"[।?]", text) if s.strip()]
        if not (4 <= len(sentences) <= 6):
            raise ValueError(f"{sec_id}: explanation has {len(sentences)} sentences (need 4-6)")
        total += len(indices)

    all_text = "\n".join(narration_text_blobs())
    for phrase in GLOBAL_REQUIRED:
        if phrase not in all_text:
            raise ValueError(f"global phonetic safeguard missing -> {phrase}")
    if total != EXPECTED_TOTAL:
        raise ValueError(f"Expected {EXPECTED_TOTAL} cues, found {total}")
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
    if cue.get("role") == "conclusion":
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


async def build_section(sec_id, sec):
    temp = os.path.join(AUDIO_DIR, f"_expressive_tmp_{sec_id}")
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

    print(f"\n[{sec_id}] {len(cues)} cue -> {sec['audio_file']}")
    for cue in cues:
        idx = cue["index"]
        chunk = os.path.join(temp, f"cue_{idx:02d}.mp3")
        rate, pitch, volume = prosody_for(cue)
        role = cue.get("role", "")
        if not valid_audio(chunk):
            print(f"  cue {idx:02d} [{cue['type']:<4}] {rate:>4} {pitch:>5} "
                  f"{role:<10} {cue['tts'][:34]}...")
            await synth_cue(cue["tts"], chunk, rate, pitch, volume)
        else:
            print(f"  cue {idx:02d} [{cue['type']:<4}] cached")
        chunk_paths.append(chunk)
        durations.append(get_duration_ms(chunk))

    sample_rate, channels = probe_stream(chunk_paths[0])
    concat_paths = []
    for i, chunk in enumerate(chunk_paths):
        concat_paths.append(chunk)
        if i < len(chunk_paths) - 1:
            silence = os.path.join(temp, f"silence_{i:02d}_{int(GAP_MS)}ms.mp3")
            make_silence(silence, sample_rate, channels)
            concat_paths.append(silence)

    final_path = os.path.join(AUDIO_DIR, sec["audio_file"])
    concat_to(final_path, concat_paths)

    # Timings from measured durations + the real 350 ms silence chunks.
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
        if mc["duration_ms"] <= 0:
            raise RuntimeError(f"{sec_id} cue {i}: zero duration")
        if mc["end_ms"] <= mc["start_ms"]:
            raise RuntimeError(f"{sec_id} cue {i}: non-positive span")
        if i > 0:
            prev = manifest_cues[i - 1]
            if mc["start_ms"] < prev["end_ms"]:
                raise RuntimeError(f"{sec_id} cue {i}: overlaps previous cue")
            if abs((mc["start_ms"] - prev["end_ms"]) - GAP_MS) > 1.0:
                raise RuntimeError(f"{sec_id} cue {i}: gap is not {GAP_MS} ms")

    if not os.path.exists(final_path) or os.path.getsize(final_path) == 0:
        raise RuntimeError(f"{sec_id}: missing/empty output {final_path}")

    # Per-section sidecar, kept in sync with the manifest.
    sidecar = os.path.join(AUDIO_DIR,
                           os.path.splitext(sec["audio_file"])[0] + "_cues.json")
    with open(sidecar, "w", encoding="utf-8") as fh:
        json.dump(manifest_cues, fh, ensure_ascii=False, indent=2)

    print(f"  => {sec['audio_file']}: {len(manifest_cues)} cue, "
          f"{cursor / 1000.0:.2f}s, {os.path.getsize(final_path)} bytes")
    return {
        "section_id": sec_id,
        "title": sec["title"],
        "audio_file": sec["audio_file"],
        "total_duration_ms": round(cursor, 1),
        "cues": manifest_cues,
    }


def bump_page_manifest_version():
    """manifest.js?v=N -> ?v=N+1 so browsers reload the rebuilt manifest."""
    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    pattern = re.compile(r"(manifest\.js\?v=)(\d+)")
    matches = pattern.findall(html)
    if not matches:
        raise RuntimeError("Page manifest cache-buster not found")
    new_html, count = pattern.subn(lambda m: m.group(1) + str(int(m.group(2)) + 1), html)
    with open(PAGE_PATH, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_html)
    print(f"  bumped manifest cache-buster: {matches[0][1]} -> {int(matches[0][1]) + 1} "
          f"({count} occurrence(s))")


async def build_all():
    total = assert_clean_scripts()
    print(f"Validated {total} clean cues in {len(SECTIONS_DATA)} sections "
          f"(0 artificial figure labels, 0 Latin/TeX chars).")

    built = {}
    for sec_id, sec in SECTIONS_DATA.items():
        built[sec_id] = await build_section(sec_id, sec)

    # Manifest keys are exactly the 4 canonical DOM section ids (in DOM order).
    manifest_sections = {sec_id: built[sec_id] for sec_id in SECTIONS_DATA}
    manifest_data = {
        "course": "lockdown_math",
        "lesson": "lesson_08",
        "title": MANIFEST_TITLE,
        "voice": VOICE,
        "mode": "authentic_teacher",
        "sections": manifest_sections,
    }

    json_text = json.dumps(manifest_data, ensure_ascii=False, indent=2)
    with open(os.path.join(AUDIO_DIR, "manifest.json"), "w", encoding="utf-8") as fh:
        fh.write(json_text)
    with open(os.path.join(AUDIO_DIR, "manifest.js"), "w", encoding="utf-8") as fh:
        fh.write("window.TEACHER_AUDIO_MANIFEST = " + json_text + ";\n")

    bump_page_manifest_version()

    # Final integrity checks.
    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert list(loaded["sections"]) == list(SECTIONS_DATA), "manifest section keys changed"
    total_cues = 0
    total_ms = 0.0
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == EXPECTED_COUNT[sec_id]
        assert [c["type"] for c in msec["cues"]] == EXPECTED_TYPES[sec_id]
        assert msec["audio_file"] == EXPECTED_AUDIO_FILES[sec_id]
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
    assert total_cues == EXPECTED_TOTAL

    print("\n" + "=" * 70)
    print("BUILD COMPLETE - expressive teacher audio, Lockdown Math Lesson 08")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<30} {len(msec['cues']):>2} cue  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 4 sections, {total_ms / 1000.0:.2f}s.")
    print("=" * 70)


# --------------------------------------------------------------------------- #
# Headless Chrome verification (channel=chrome, self-contained file://)
# --------------------------------------------------------------------------- #
VERIFY_JS = r"""() => {
  const ne = window.narrationEngine;
  const manifest = window.TEACHER_AUDIO_MANIFEST;
  const sectionEls = [...document.querySelectorAll('.article > section, article section')];

  function domType(node) {
    if (node.classList.contains('chapter-quote')) return 'chapter-quote';
    if (node.classList.contains('callout')) {
      const v = [...node.classList].find(c => c.startsWith('callout-'));
      return v || 'callout';
    }
    if (node.matches('figure.lesson-figure')) return 'figure';
    if (node.classList.contains('formula-box')) return 'formula-box';
    if (node.classList.contains('code-showcase')) return 'code-showcase';
    return node.tagName.toLowerCase();
  }
  const dom = [];
  for (const el of sectionEls) {
    if (el.getAttribute('data-no-narration') === 'true') continue;
    const nodes = [...el.querySelectorAll(
      'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box')];
    const blocks = [];
    for (const node of nodes) {
      if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) continue;
      blocks.push({type: domType(node), text: (node.innerText || '').trim()});
    }
    dom.push({id: el.id, blocks});
  }
  const engine = ne.sections.map(s => ({
    id: s.id, blockCount: s.blocks.length, cueCount: s.cues.length,
    audioFile: s.audioFile, types: s.blocks.map(b => domType(b.element))
  }));
  return {
    manifestPresent: !!manifest,
    hasStudioAudio: !!ne.hasStudioAudio,
    manifestKeys: Object.keys(manifest ? manifest.sections : {}),
    manifest: manifest,
    dom: dom.map(s => ({id: s.id, types: s.blocks.map(b => b.type),
                        texts: s.blocks.map(b => b.text)})),
    engine,
    sectionEls: sectionEls.map(s => ({id: s.id, noNarration: s.getAttribute('data-no-narration')}))
  };
}"""

AUDIO_JS = r"""async (files) => {
  const results = [];
  for (const f of files) {
    const a = new Audio();
    const ok = await new Promise(resolve => {
      const good = () => resolve(true), bad = () => resolve(false);
      a.addEventListener('loadedmetadata', good, { once: true });
      a.addEventListener('error', bad, { once: true });
      a.src = f; a.load();
    });
    results.push({ file: f, ok, duration: isFinite(a.duration) ? a.duration : -1 });
  }
  return results;
}"""


def verify_in_chrome():
    """Return a verification report dict; raises AssertionError on failure."""
    from pathlib import Path
    from playwright.sync_api import sync_playwright

    page_uri = Path(PAGE_PATH).as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page()
        page_errors, console_errors = [], []
        page.on("pageerror", lambda e: page_errors.append("pageerror: " + str(e)))
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.goto(page_uri, wait_until="load")
        page.wait_for_function(
            "() => !!window.narrationEngine && !!window.narrationEngine.sections "
            "&& window.narrationEngine.sections.length > 0 "
            "&& !!window.TEACHER_AUDIO_MANIFEST")
        data = page.evaluate(VERIFY_JS)
        manifest_local = os.path.join(AUDIO_DIR, "manifest.json")
        with open(manifest_local, encoding="utf-8") as fh:
            local_manifest = json.load(fh)
        audio_urls = ["../../assets/audio/lockdown_math/lesson_08/" +
                      local_manifest["sections"][sid]["audio_file"]
                      for sid in SECTIONS_DATA]
        audio_results = page.evaluate(AUDIO_JS, audio_urls)
        browser.close()

    # Benign, pre-existing, non-narration noise from the offline file:// page:
    # hero/watch-panel mp4 + YouTube embeds are unavailable offline.
    benign = ("ERR_FILE_NOT_FOUND", "404 (File not found)", "Failed to load resource",
              "Permissions policy violation", "net::ERR", "youtube", "youtu.be")
    narration_console_errors = [e for e in console_errors
                                if not any(b.lower() in e.lower() for b in benign)]

    assert page_errors == [], f"JS page errors: {page_errors}"
    assert narration_console_errors == [], f"Unexpected console errors: {narration_console_errors}"
    assert data["manifestPresent"], "window.TEACHER_AUDIO_MANIFEST missing"
    assert data["hasStudioAudio"], "Studio teacher audio not bound"

    mkeys = data["manifestKeys"]
    dom_ids = [s["id"] for s in data["dom"]]
    canonical_ids = list(SECTIONS_DATA)
    assert dom_ids == canonical_ids, f"DOM ids changed: {dom_ids} vs {canonical_ids}"
    assert mkeys == canonical_ids, f"Manifest keys changed: {mkeys}"
    assert canonical_ids == [s["id"] for s in data["engine"]], "Engine ids changed"
    assert not ({"sec-quizzes", "sec-quiz", "sec-media", "sec-simulator",
                  "sec-interactive-lab"} & set(dom_ids)), "non-narrated section leaked"

    # All no-narration sections really carry the attribute.
    nn = [e["id"] for e in data["sectionEls"] if e["noNarration"] == "true"]
    for req in ("sec-01-study", "sec-02-study", "sec-03-study", "sec-04-study",
                "sec-interactive-lab", "sec-quizzes", "sec-formulas-glossary"):
        assert req in nn, f"{req} missing no-narration: {nn}"

    tsections = data["manifest"]["sections"]
    total_cues = 0
    total_ms = 0.0
    dup_check = set()
    disallowed = set()
    forbidden_hits = []
    natural_figure_hits = 0
    prosody_variants = set()
    for sec_id in canonical_ids:
        msec = tsections[sec_id]
        dom_sec = next(s for s in data["dom"] if s["id"] == sec_id)
        eng_sec = next(s for s in data["engine"] if s["id"] == sec_id)
        cues = msec["cues"]
        expected_types = EXPECTED_TYPES[sec_id]

        assert len(cues) == EXPECTED_COUNT[sec_id], (sec_id, len(cues))
        assert len(dom_sec["types"]) == len(cues), (sec_id, "DOM block count", dom_sec["types"])
        assert [c["type"] for c in cues] == expected_types, (sec_id, "manifest types")
        assert dom_sec["types"] == expected_types, (sec_id, "DOM types", dom_sec["types"])
        assert eng_sec["types"] == expected_types, (sec_id, "engine types", eng_sec["types"])
        assert eng_sec["blockCount"] == len(cues) == eng_sec["cueCount"], sec_id
        assert msec["audio_file"] == EXPECTED_AUDIO_FILES[sec_id], (sec_id, "audio_file")
        assert msec["audio_file"] in eng_sec["audioFile"], (sec_id, "engine audio binding")

        for cue in cues:
            total_cues += 1
            key = (sec_id, cue["index"], cue["type"], cue["text"])
            assert key not in dup_check, f"Duplicate cue: {key[:3]}"
            dup_check.add(key)
            if cue["type"] not in ALLOWED_CUE_TYPES:
                disallowed.add(cue["type"])
            if FORBIDDEN_PREFIX in cue["text"]:
                forbidden_hits.append(f"{sec_id}/{cue['index']}")
            if NATURAL_FIGURE in cue["text"]:
                natural_figure_hits += 1
            sentences = [x for x in re.split(r"[।?]", cue["text"]) if x.strip()]
            assert 4 <= len(sentences) <= 6, (sec_id, cue["index"], "sentences", len(sentences))
            bad = BAD_CHARS.findall(cue["text"])
            assert not bad, (sec_id, cue["index"], "latin/tex chars", bad)

        assert KEY_PHRASES[sec_id] in cues[0]["text"], (sec_id, "key h2 phrase missing")
        for phrase in REQUIRED_PHRASES.get(sec_id, []):
            assert phrase in cues[0]["text"], (sec_id, "safeguard missing", phrase)
        prosody_variants.add(prosody_for(SECTIONS_DATA[sec_id]["cues"][0]))

        # Timing integrity: exact 350 ms gaps, no overlaps, duration agrees.
        cursor = 0.0
        for i, c in enumerate(cues):
            assert abs(c["start_ms"] - cursor) < 1.0, (sec_id, i, "start")
            assert c["duration_ms"] > 0, (sec_id, i, "zero duration")
            assert abs((c["end_ms"] - c["start_ms"]) - c["duration_ms"]) < 1.0, (sec_id, i)
            cursor = c["end_ms"] + (GAP_MS if i < len(cues) - 1 else 0.0)
        assert abs(msec["total_duration_ms"] - cursor) < 1.0, (sec_id, "total_duration_ms")

        af = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(af) and os.path.getsize(af) > 0, af
        total_ms += msec["total_duration_ms"]

    assert total_cues == EXPECTED_TOTAL, total_cues
    assert not disallowed, f"Disallowed cue types: {disallowed}"
    assert not forbidden_hits, f"Artificial figure label found: {forbidden_hits}"
    assert natural_figure_hits == EXPECTED_TOTAL, natural_figure_hits
    # Both prosody rules are exercised: h2 -5%/+2Hz and conclusion -3%.
    assert ("-5%", "+2Hz", "+0%") in prosody_variants, prosody_variants
    assert CONCLUSION_PROSODY in prosody_variants, prosody_variants
    # Global phonetic safeguard.
    assert any(p in json.dumps(local_manifest, ensure_ascii=False) for p in GLOBAL_REQUIRED)

    # No quiz / media-tab anywhere in the narrated DOM cue types.
    all_dom_types = [t for s in data["dom"] for t in s["types"]]
    assert not ({"quiz", "media-tab", "b1b-quiz", "b1b-media-tab"} & set(all_dom_types)), all_dom_types

    # manifest.js payload must equal manifest.json; sidecars valid and in sync.
    with open(os.path.join(AUDIO_DIR, "manifest.js"), encoding="utf-8") as fh:
        js_text = fh.read().strip()
    assert js_text.startswith("window.TEACHER_AUDIO_MANIFEST = ") and js_text.endswith(";")
    js_obj = json.loads(js_text[len("window.TEACHER_AUDIO_MANIFEST = "):-1].strip())
    assert js_obj == local_manifest, "manifest.js != manifest.json"
    for sec_id in SECTIONS_DATA:
        side = os.path.join(AUDIO_DIR,
                            os.path.splitext(EXPECTED_AUDIO_FILES[sec_id])[0] + "_cues.json")
        with open(side, encoding="utf-8") as fh:
            side_obj = json.load(fh)
        assert side_obj == local_manifest["sections"][sec_id]["cues"], (sec_id, "sidecar out of sync")

    # On-disk forbidden phrase scan (manifest + sidecars).
    disk_blobs = [json.dumps(local_manifest, ensure_ascii=False)]
    for sec_id in SECTIONS_DATA:
        side = os.path.join(AUDIO_DIR,
                            os.path.splitext(EXPECTED_AUDIO_FILES[sec_id])[0] + "_cues.json")
        with open(side, encoding="utf-8") as fh:
            disk_blobs.append(fh.read())
    assert not any(FORBIDDEN_PREFIX in b for b in disk_blobs), "forbidden label on disk"
    # DOM text forbidden phrase scan.
    for s in data["dom"]:
        for t in s["texts"]:
            assert FORBIDDEN_PREFIX not in t, f"forbidden label in DOM text of {s['id']}"

    # Page cache-buster bumped.
    with open(PAGE_PATH, encoding="utf-8") as fh:
        html = fh.read()
    versions = [int(v) for _, v in re.findall(r"(manifest\.js\?v=)(\d+)", html)]
    assert versions and min(versions) >= 2, f"manifest ?v not bumped: {versions}"

    # Browser MP3 loadability.
    for r in audio_results:
        assert r["ok"] and r["duration"] > 0, f"browser MP3 load failed: {r}"

    report = {
        "channel": "chrome (headless=True)",
        "sections": len(SECTIONS_DATA),
        "cues": total_cues,
        "per_section": {sid: EXPECTED_COUNT[sid] for sid in canonical_ids},
        "manifest_keys": len(mkeys),
        "dom_manifest_1to1": True,
        "duplicates": 0,
        "disallowed_types": 0,
        "quiz_media_tab_types": 0,
        "forbidden_label_hits": 0,
        "natural_figure_phrasing_cues": natural_figure_hits,
        "h2_key_phrase_woven": True,
        "phonetic_safeguards_ok": True,
        "prosody_h2": list(PROSODY_DEFAULT["h2"]),
        "prosody_conclusion": list(CONCLUSION_PROSODY),
        "gap_ms": GAP_MS,
        "js_page_errors": len(page_errors),
        "narration_console_errors": len(narration_console_errors),
        "preexisting_media_console_errors": len(console_errors) - len(narration_console_errors),
        "mp3_nonzero": True,
        "mp3_browser_loadable": True,
        "json_valid": True,
        "manifest_js_matches_json": True,
        "sidecars_in_sync": True,
        "manifest_version": versions,
        "total_duration_ms": round(total_ms, 1),
        "total_duration_s": round(total_ms / 1000.0, 2),
        "ok": True,
    }
    with open(VERIFY_RESULT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    return report


def main():
    if "--verify-only" not in sys.argv[1:]:
        asyncio.run(build_all())
    else:
        print("--verify-only: skipping build")
    report = verify_in_chrome()
    print("\n" + "=" * 70)
    print("VERIFICATION REPORT (headless Chrome channel=chrome)")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("=" * 70)
    print(f"VERIFIED: {report['cues']}/{report['cues']} cues, DOM<->manifest 1:1, "
          f"0 dups, 0 quiz/media-tab types, non-zero+loadable mp3s, valid JSON, "
          f"0 JS page errors, 0 'চিত্র প্রদর্শনী' labels, "
          f"{report['natural_figure_phrasing_cues']} natural figure phrasings.")
    print(f"Report written to {VERIFY_RESULT}")


if __name__ == "__main__":
    main()
