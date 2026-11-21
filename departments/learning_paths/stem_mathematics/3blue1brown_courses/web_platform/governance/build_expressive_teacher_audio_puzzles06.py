# -*- coding: utf-8 -*-
"""Gold-standard TEACHER NARRATION AUDIO for Puzzles Lesson 06 (extra dimension)."""
import os
import sys

import _puzzles_audio_core as core

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
LESSON = "lesson_06"
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "puzzles", LESSON)
PAGE_PATH = os.path.join(WORKSPACE, "courses", "puzzles", LESSON + ".html")

EXPECTED_TYPES = {
    "sec-intro":    ["h2", "p", "figure", "p", "callout"],
    "sec-shadow":   ["h2", "p", "figure", "p"],
    "sec-knot":     ["h2", "p", "figure", "h3", "p"],
    "sec-encoding": ["h2", "p", "figure", "callout"],
    "sec-takeaway": ["h2", "p", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-intro":    "sec_01_sec-intro.mp3",
    "sec-shadow":   "sec_02_sec-shadow.mp3",
    "sec-knot":     "sec_03_sec-knot.mp3",
    "sec-encoding": "sec_04_sec-encoding.mp3",
    "sec-takeaway": "sec_05_sec-takeaway.mp3",
}
GLOBAL_REQUIRED = ["টুডি", "থ্রিডি", "চেসবোর্ড"]

SECTIONS_DATA = {
    "sec-intro": {
        "title": "কেন আরেকটি মাত্রা?",
        "audio_file": "sec_01_sec-intro.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, কেন আরেকটি মাত্রা। কখনো কোনো সমস্যা সমতলে অসম্ভব মনে হয়, কিন্তু ত্রিমাত্রিক স্থানে উঠে গেলেই সহজ হয়ে যায়।"},
            {"index": 1, "type": "p",
             "tts": "বাক্সের বাইরে ভাবা মানেই প্রায়ই এক পা উঠে নতুন মাত্রায় দেখা। টুডিতে যেটি করা যায় না, থ্রিডিতে সেটি সম্ভব হয়।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে একটি সমতল ছায়া তার ত্রিমাত্রিক বস্তু সম্পর্কে ইঙ্গিত দিচ্ছে। ছায়া দেখে আমরা মূল বস্তুর আকার আন্দাজ করতে পারি।"},
            {"index": 3, "type": "p",
             "tts": "এই পাঠে পাঁচটি ছোট ধাঁধা দেখব। প্রতিটিতেই মূল পদক্ষেপ হলো প্রশ্নটিকে আরও বড় স্থানে স্থানান্তর করা।"},
            {"index": 4, "type": "callout", "role": "conclusion",
             "tts": "মানসিক চিত্র, টুডিতে যেটি অতিক্রম করা যায় না, থ্রিডিতে সেটি উপর দিয়ে যাওয়া। নিষেধাজ্ঞা প্রায়ই মাত্রার উপর নির্ভর করে।"},
        ],
    },
    "sec-shadow": {
        "title": "ছায়া থেকে বস্তু",
        "audio_file": "sec_02_sec-shadow.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, ছায়া থেকে বস্তু। একটি ত্রিমাত্রিক বস্তুর ছায়া দেখে তার আসল আকার বোঝা কঠিন।"},
            {"index": 1, "type": "p",
             "tts": "একই বস্তুর বিভিন্ন দিক থেকে একাধিক ছায়া নিলে তথ্য যোগ হয়। একটিমাত্র ছায়া যথেষ্ট নয়, কিন্তু তিনটি ছায়া মিলে গঠনটি ধরা পড়ে।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে একই বস্তুর বিভিন্ন কোণ থেকে নেওয়া ছায়া। প্রতিটি ছায়া আসল বস্তুর এক একটি দিক দেখাচ্ছে।"},
            {"index": 3, "type": "p", "role": "conclusion",
             "tts": "উচ্চ মাত্রার বস্তুকে নিচ মাত্রায় প্রক্ষেপণ করলে তথ্য হারায়। কিন্তু সেই প্রক্ষেপণগুলো একসাথে আসল গঠন সম্পর্কে বলে দেয়।"},
        ],
    },
    "sec-knot": {
        "title": "গিঁট ও খোলা লুপ",
        "audio_file": "sec_03_sec-knot.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, গিঁট ও খোলা লুপ। সমতলে একটি বন্ধ লুপ ভেতরে থাকা বিন্দুকে বাইরে আনতে পারে না।"},
            {"index": 1, "type": "p",
             "tts": "কিন্তু ত্রিমাত্রিকে লুপটিকে উপরে তুলে সহজেই পাশ কাটানো যায়। যেটি টুডিতে অসম্ভব, থ্রিডিতে সেটি সহজ।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে সমতলে আবদ্ধ এক লুপ, আর থ্রিডিতে সেই লুপের সহজ মুক্তি। এক পা উপরে উঠলেই বাধা কেটে যাচ্ছে।"},
            {"index": 3, "type": "h3",
             "tts": "জটিলতা কমে যায়। অনেক টপোলজিকাল প্রশ্ন ঠিক এভাবেই সমাধান হয়।"},
            {"index": 4, "type": "p", "role": "conclusion",
             "tts": "কোনো বস্তুকে নিজের মাত্রার চেয়ে বেশি মাত্রায় রেখে দেখলে অনেক জটিলতা সরল হয়। মাত্রা বদলালেই পথ খুলে যায়।"},
        ],
    },
    "sec-encoding": {
        "title": "তথ্য ও মাত্রা",
        "audio_file": "sec_04_sec-encoding.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, তথ্য ও মাত্রা। কম জায়গায় বেশি তথ্য রাখা কীভাবে সম্ভব, সেটা দেখব।"},
            {"index": 1, "type": "p",
             "tts": "আরেকটি ধাঁধা, কম জায়গায় বেশি তথ্য রাখা। এক মাত্রায় সীমাবদ্ধ থাকলে যা অসম্ভব, দুই মাত্রায় তা সহজ। যেমন একটি সংখ্যার বিটগুলোকে বর্গাকার গ্রিডে সাজানো।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে এক মাত্রার তথ্য দ্বিমাত্রিক গ্রিডে সাজানো হয়েছে। সারি ও কলাম মিলে প্রতিটি বিটের অবস্থান নির্ধারণ করে।"},
            {"index": 3, "type": "callout", "role": "conclusion",
             "tts": "পরবর্তী পাঠে চেসবোর্ড ধাঁধায় ঠিক এই ধারণা ব্যবহার করা হবে। মাত্র দুইয়ের ঘাত ছয় বিট দিয়ে সমস্ত ঘরের বার্তা পাঠানো যাবে।"},
        ],
    },
    "sec-takeaway": {
        "title": "শিক্ষণীয় বিষয়",
        "audio_file": "sec_05_sec-takeaway.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, শিক্ষণীয় বিষয়। ধাঁধা সমাধানের উপকরণ প্রায়ই সমস্যার ভেতরেই থাকে।"},
            {"index": 1, "type": "p",
             "tts": "ধাঁধা সমাধানের জন্য প্রয়োজনীয় উপকরণ প্রায়ই সমস্যার ভেতরেই থাকে। আমরা কেবল সেগুলোকে নতুন কোণ থেকে দেখি না।"},
            {"index": 2, "type": "p", "role": "conclusion",
             "tts": "অসম্ভব মানে অনেক সময় এই মাত্রায় অসম্ভব। সীমাটি আমাদের চিন্তার, বস্তুর নয়।"},
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
    "verify_result_path": os.path.join(HERE, "_verify_puzzles06_result.json"),
}

if __name__ == "__main__":
    core.run(CFG, verify_only="--verify-only" in sys.argv[1:])
