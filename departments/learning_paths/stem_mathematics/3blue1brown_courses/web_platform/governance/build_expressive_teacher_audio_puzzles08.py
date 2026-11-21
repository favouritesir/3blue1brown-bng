# -*- coding: utf-8 -*-
"""Gold-standard TEACHER NARRATION AUDIO for Puzzles Lesson 08 (chessboard / XOR)."""
import os
import sys

import _puzzles_audio_core as core

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
LESSON = "lesson_08"
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "puzzles", LESSON)
PAGE_PATH = os.path.join(WORKSPACE, "courses", "puzzles", LESSON + ".html")

EXPECTED_TYPES = {
    "sec-puzzle":   ["h2", "p", "figure", "p", "callout"],
    "sec-bits":     ["h2", "p", "figure", "formula-box", "p"],
    "sec-xor":      ["h2", "p", "figure", "p", "formula-box", "callout"],
    "sec-proof":    ["h2", "p", "figure", "p"],
    "sec-takeaway": ["h2", "p", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-puzzle":   "sec_01_sec-puzzle.mp3",
    "sec-bits":     "sec_02_sec-bits.mp3",
    "sec-xor":      "sec_03_sec-xor.mp3",
    "sec-proof":    "sec_04_sec-proof.mp3",
    "sec-takeaway": "sec_05_sec-takeaway.mp3",
}
GLOBAL_REQUIRED = ["চেসবোর্ড", "এক্সওআর", "দ্বিমিক"]

SECTIONS_DATA = {
    "sec-puzzle": {
        "title": "ধাঁধাটি",
        "audio_file": "sec_01_sec-puzzle.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, ধাঁধাটি। চেসবোর্ডের চারের ষাট ঘরে মুদ্রা সাজানো, আর একটি মুদ্রা উল্টিয়েই চাবির ঘরের বার্তা পাঠাতে হবে।"},
            {"index": 1, "type": "p",
             "tts": "একটি আট গুণ আট চেসবোর্ডের চারের ষাটটি ঘরে প্রতিটিতে একটি মুদ্রা আছে। প্রতিটি মুদ্রার দুই অবস্থা মাথা বা লেজ। একজন চাবির অবস্থান নির্দিষ্ট একটি ঘরে রেখে অন্যজনকে বলবেন, নিয়ম হলো সঙ্গী কেবল একটি মুদ্রা উল্টাতে পারেন।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে চেসবোর্ডের চারের ষাটটি ঘর, প্রতিটিতে মাথা বা লেজ মুদ্রা। ছয়টি বিটের বার্তা এই মুদ্রাগুলোর অবস্থার মধ্যে লুকানো।"},
            {"index": 3, "type": "p",
             "tts": "দ্বিতীয়জন বোর্ড দেখে কোন ঘরে চাবি আছে তা বলতে পারবেন কি। প্রথমে মনে হয় তথ্যের অভাব আছে, কিন্তু একটিমাত্র উল্টানোতেই যথেষ্ট তথ্য লুকানো যায়।"},
            {"index": 4, "type": "callout", "role": "conclusion",
             "tts": "আশ্চর্যের বিষয়, চারের ষাট সমান দুইয়ের ঘাত ছয়। ছয়টি বিটেই সমস্ত অবস্থান নির্দেশ করা যায়, আর একটি মুদ্রা উল্টানো ঠিক ছয় বিটের বার্তা বহন করে।"},
        ],
    },
    "sec-bits": {
        "title": "ঘরে নাম্বার ও বিট",
        "audio_file": "sec_02_sec-bits.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, ঘরে নাম্বার ও বিট। প্রতিটি ঘরকে শূন্য থেকে তেষট্টি পর্যন্ত একটি নাম্বার দেব।"},
            {"index": 1, "type": "p",
             "tts": "প্রতিটি ঘরে শূন্য থেকে তেষট্টি পর্যন্ত একটি নাম্বার দিন। ছয় বিটের দ্বিমিক রূপে এই নাম্বারগুলো লিখুন। প্রতিটি বিট একটি প্রশ্ন, যার উত্তর ওই বিটের মান।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে ছয়টি বিট দিয়ে শূন্য থেকে তেষট্টি পর্যন্ত নাম্বার এনকোড করা। বিটের সমন্বয়েই ঘরের অবস্থান চিহ্নিত হয়।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, চারের ষাট সমান দুইয়ের ঘাত ছয়, অর্থাৎ ছয়টি বিট। এই ছয় বিটই চাবির অবস্থান বলে দিতে পারে।"},
            {"index": 4, "type": "p", "role": "conclusion",
             "tts": "মুদ্রার অবস্থা ব্যবহার করে আমরা ছয়টি প্রশ্নের উত্তর পাই। সেগুলো নিয়ে একটি ছয় বিটের নাম্বার গড়ে ওঠে, যা চাবির ঘর নির্দেশ করে।"},
        ],
    },
    "sec-xor": {
        "title": "এক্স-অর-এর যাদু",
        "audio_file": "sec_03_sec-xor.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, এক্সওআরের যাদু। মাথা আছে এমন ঘরের নাম্বারের এক্সওআর বের করব।"},
            {"index": 1, "type": "p",
             "tts": "যে ঘরগুলোতে মাথা আছে, তাদের নাম্বারগুলোর এক্সওআর বের করুন। এক্সওআর মানে বিটভিত্তিক যোগ, ক্যারি ছাড়া। ফলাফল একটি ছয় বিটের নাম্বার এস, অর্থাৎ বর্তমান বার্তা।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে মাথা ঘরগুলোর নাম্বারের এক্সওআর নির্ণয়। প্রতিটি বিটে জোড় সংখ্যক এক থাকলে শূন্য, বিজোড় থাকলে এক পাওয়া যায়।"},
            {"index": 3, "type": "p",
             "tts": "চাবি আছে এমন ঘরের নাম্বার টি। প্রথমজন সেই ঘরটি খুঁজেন যার নাম্বার এস এক্সওআর টি। সেখানকার মুদ্রা উল্টালে নতুন এক্সওআর হয় ঠিক টি।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, বার্তা এস এক্সওআর করে সেই এস এক্সওআর টি যোগ করলে আবার টি পাওয়া যায়। এই ছোট্ট সূত্রটিই পুরো কৌশলের ভিত্তি।"},
            {"index": 5, "type": "callout", "role": "conclusion",
             "tts": "কেন কাজ করে। একটি মুদ্রা উল্টালে সেই ঘরের নাম্বারটি এক্সওআরের সাথে যোগ বা বাদ যায়। ফলে ঠিক টি পাওয়া যায়, অন্য কিছু নয়।"},
        ],
    },
    "sec-proof": {
        "title": "সম্পূর্ণ প্রক্রিয়া",
        "audio_file": "sec_04_sec-proof.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, সম্পূর্ণ প্রক্রিয়া। তিন ধাপে বার্তা এনকোড ও ডিকোড করা যায়।"},
            {"index": 1, "type": "p",
             "tts": "ধাপ এক, মাথা ঘরগুলোর এক্সওআর বের করুন, সেটি এস। ধাপ দুই, এক্স নির্ণয় করুন এস এক্সওআর টি। ধাপ তিন, এক্স নাম্বারের ঘরের মুদ্রা উল্টান। দ্বিতীয়জন একই হিসাব করে টি পড়েন।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে তিন ধাপে বার্তা এনকোড ও ডিকোড হচ্ছে। প্রথমজনের একটিমাত্র উল্টানোই দ্বিতীয়জনের কাছে পুরো বার্তা পৌঁছে দেয়।"},
            {"index": 3, "type": "p", "role": "conclusion",
             "tts": "কোনো অতিরিক্ত চুক্তি বা আগের বিন্যাস লাগে না। কেবল ছয় বিট, দ্বিমিক ব্যবস্থা ও এক্সওআরের একটি সরল কৌশল।"},
        ],
    },
    "sec-takeaway": {
        "title": "শিক্ষণীয় বিষয়",
        "audio_file": "sec_05_sec-takeaway.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, শিক্ষণীয় বিষয়। অসম্ভব মনে হওয়া তথ্য সমস্যা প্রায়ই কোডিংয়ে রূপান্তরিত হয়।"},
            {"index": 1, "type": "p",
             "tts": "অসম্ভব মনে হওয়া তথ্য সমস্যা প্রায়ই একটি উপযুক্ত কোডিংয়ে রূপান্তরিত হয়। দুইয়ের ঘাত, দ্বিমিক ব্যবস্থা ও এক্সওআর, এই তিনটি টুল অনেক ধাঁধার চাবি।"},
            {"index": 2, "type": "p", "role": "conclusion",
             "tts": "পরবর্তী পাঠে আমরা দেখব কীভাবে একই ধরনের সীমাবদ্ধতা গ্রাফ অঙ্কনে নতুন রূপ নেয়। সীমাবদ্ধতা অনেক সময় নতুন গঠনের জন্ম দেয়।"},
        ],
    },
}

CFG = {
    "course": "puzzles",
    "lesson": LESSON,
    "audio_dir": AUDIO_DIR,
    "page_path": PAGE_PATH,
    "sections_data": SECTIONS_DATA,
    "expected_types": EXPECTED_TYPES,
    "expected_audio_files": EXPECTED_AUDIO_FILES,
    "expected_total": sum(len(v) for v in EXPECTED_TYPES.values()),
    "figure_count": sum(v.count("figure") for v in EXPECTED_TYPES.values()),
    "global_required": GLOBAL_REQUIRED,
    "verify_result_path": os.path.join(HERE, "_verify_puzzles08_result.json"),
}

if __name__ == "__main__":
    core.run(CFG, verify_only="--verify-only" in sys.argv[1:])
