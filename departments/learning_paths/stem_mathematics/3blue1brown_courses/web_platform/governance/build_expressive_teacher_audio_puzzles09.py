# -*- coding: utf-8 -*-
"""Gold-standard TEACHER NARRATION AUDIO for Puzzles Lesson 09 (Euler / K3,3 / torus)."""
import os
import sys

import _puzzles_audio_core as core

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
LESSON = "lesson_09"
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "puzzles", LESSON)
PAGE_PATH = os.path.join(WORKSPACE, "courses", "puzzles", LESSON + ".html")

EXPECTED_TYPES = {
    "sec-puzzle":    ["h2", "p", "figure", "p", "callout"],
    "sec-euler":     ["h2", "p", "figure", "formula-box", "p"],
    "sec-bipartite": ["h2", "p", "figure", "formula-box", "p"],
    "sec-torus":     ["h2", "p", "figure", "h3", "p"],
    "sec-takeaway":  ["h2", "p", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-puzzle":    "sec_01_sec-puzzle.mp3",
    "sec-euler":     "sec_02_sec-euler.mp3",
    "sec-bipartite": "sec_03_sec-bipartite.mp3",
    "sec-torus":     "sec_04_sec-torus.mp3",
    "sec-takeaway":  "sec_05_sec-takeaway.mp3",
}
GLOBAL_REQUIRED = ["অয়লার", "কে তিন তিন", "টোরাস"]

SECTIONS_DATA = {
    "sec-puzzle": {
        "title": "ধাঁধাটি",
        "audio_file": "sec_01_sec-puzzle.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, ধাঁধাটি। তিনটি বাড়ি আর গ্যাস, পানি, বিদ্যুৎ পরিষেবার তারে ছেদ না করে সংযোগ দেওয়া।"},
            {"index": 1, "type": "p",
             "tts": "তিনটি বাড়ি আছে এবং গ্যাস, পানি ও বিদ্যুৎ কোম্পানির সাথে প্রতিটিকে সংযুক্ত করতে হবে। শর্ত হলো কোনো দুটি তার যেন ছেদ না করে। সমতলে কি এটি সম্ভব।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে বাড়ি ও পরিষেবা, আর রেখা কাটা ছাড়া সংযোগ দেওয়ার চেষ্টা। প্রথম কয়েকটি তার সহজে আঁকা যায়, শেষটি আটকে যায়।"},
            {"index": 3, "type": "p",
             "tts": "দেখে সহজ মনে হলেও বারবার চেষ্টা করলে দেখা যায়, একটির পর একটির মতো করে সব সংযোগ করা যায় না। শেষের সংযোগটি সবসময় আটকে যায়।"},
            {"index": 4, "type": "callout", "role": "conclusion",
             "tts": "ইতিহাস, এই কে তিন তিন গ্রাফটি গ্রাফ তত্ত্বের বিখ্যাত উদাহরণ। কুরাটোভস্কির উপপাদ্য অনুযায়ী এটি সবচেয়ে ছোট অসমতলিক গ্রাফ।"},
        ],
    },
    "sec-euler": {
        "title": "অয়লারের সূত্র",
        "audio_file": "sec_02_sec-euler.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, অয়লারের সূত্র। যেকোনো সংযুক্ত সমতলিক গ্রাফের জন্য ভি বিয়োগ ই প্লাস এফ সমান দুই।"},
            {"index": 1, "type": "p",
             "tts": "যেকোনো সংযুক্ত সমতলিক গ্রাফের জন্য ভি বিয়োগ ই প্লাস এফ সমান দুই। এখানে ভি মানে শীর্ষ, ই মানে ধার আর এফ মানে ফলক, বাইরের অঞ্চলও একটি ফলক।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে শীর্ষ, ধার ও ফলক, অয়লারের সূত্রের তিনটি উপাদান। গ্রাফের প্রতিটি বন্ধ ঘর এক একটি ফলক গণনা হয়।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ভি বিয়োগ ই প্লাস এফ সমান দুই। এই সূত্রটি সমতলে আঁকা যেকোনো সংযুক্ত গ্রাফের ক্ষেত্রে প্রযোজ্য।"},
            {"index": 4, "type": "p", "role": "conclusion",
             "tts": "প্রতিটি ফলকে অন্তত তিনটি ধার থাকে, আবার প্রতিটি ধার দুটি ফলকের সীমানা। তাই তিন এফ ছোট বা সমান দুই ই, বসিয়ে পাই ই ছোট বা সমান তিন ভি বিয়োগ ছয়।"},
        ],
    },
    "sec-bipartite": {
        "title": "দ্বিপাক্ষিকে সীমাবদ্ধতা",
        "audio_file": "sec_03_sec-bipartite.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, দ্বিপাক্ষিকে সীমাবদ্ধতা। এই গ্রাফে ধারগুলো শুধু বাড়ি থেকে পরিষেবার দিকে যায়।"},
            {"index": 1, "type": "p",
             "tts": "এখানে প্রতিটি ধার একটি বাড়ি থেকে একটি পরিষেবার দিকে যায়। কোনো ধার বাড়ি থেকে বাড়ি বা পরিষেবা থেকে পরিষেবার মধ্যে নয়। এমন গ্রাফে প্রতিটি ফলক অন্তত চারটি ধার দ্বারা বেষ্টিত।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে বাড়ি ও পরিষেবা দুই পাশে, আর ধার শুধু পারাপারে। একই পাশের দুটি বিন্দুর মধ্যে কোনো ধার নেই।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, চার এফ ছোট বা সমান দুই ই, তাই এফ ছোট বা সমান ই ভাগের দুই, আর সীমাবদ্ধতা ই ছোট বা সমান দুই ভি বিয়োগ চার। কে তিন তিনের ক্ষেত্রে এই শর্ত ভেঙে পড়ে।"},
            {"index": 4, "type": "p", "role": "conclusion",
             "tts": "কে তিন তিনে ভি ছয় আর ই নয়। কিন্তু ই ছোট বা সমান দুই ভি বিয়োগ চার অর্থাৎ আট হওয়া উচিত, নয় ছোট বা সমান আট মিথ্যা। সুতরাং সমতলে অঙ্কন অসম্ভব।"},
        ],
    },
    "sec-torus": {
        "title": "টোরাসে সমাধান",
        "audio_file": "sec_04_sec-torus.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, টোরাসে সমাধান। সমতলের বদলে নলাকার পৃষ্ঠ ব্যবহার করলে সূত্র বদলে যায়।"},
            {"index": 1, "type": "p",
             "tts": "যদি সমতলের বদলে নলাকার পৃষ্ঠ অর্থাৎ টোরাস ব্যবহার করি, তখন ভি বিয়োগ ই প্লাস এফ সমান শূন্য হয়ে যায়। তখন নতুন সীমাবদ্ধতা ই ছোট বা সমান দুই ভি, আর কে তিন তিনে নয় ছোট বা সমান বারো, অর্থাৎ সম্ভব।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে নলাকার পৃষ্ঠে তিন বাড়ি ও তিন পরিষেবা সংযুক্ত। যেটি সমতলে অসম্ভব ছিল, টোরাসে সেটি সহজেই করা যায়।"},
            {"index": 3, "type": "h3",
             "tts": "টপোলজির পাঠ। একই গ্রাফ একটি পৃষ্ঠে অসম্ভব, অন্য পৃষ্ঠে সম্ভব।"},
            {"index": 4, "type": "p", "role": "conclusion",
             "tts": "সম্ভবত্ব নির্ভর করে স্থানের আকৃতির উপর, কেবল সংখ্যার উপর নয়। পৃষ্ঠের গঠন বদলালেই নিষেধাজ্ঞা বদলে যায়।"},
        ],
    },
    "sec-takeaway": {
        "title": "শিক্ষণীয় বিষয়",
        "audio_file": "sec_05_sec-takeaway.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, শিক্ষণীয় বিষয়। অয়লারের সূত্র কেবল মুখস্থ করার বিষয় নয়।"},
            {"index": 1, "type": "p",
             "tts": "অয়লারের সূত্র কেবল সূত্র মুখস্থ করার বিষয় নয়। এটি সমতলের ক্ষমতা সম্পর্কে এক ধরনের হিসাব।"},
            {"index": 2, "type": "p", "role": "conclusion",
             "tts": "পরবর্তী পাঠে আমরা এই সূত্রের একটি সুন্দর প্রমাণ দেখব, স্প্যানিং ট্রি ও গ্রাফ ডুয়ালিটি ব্যবহার করে। দুটি সরল ধাপে পুরো সূত্রটি প্রমাণিত হবে।"},
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
    "verify_result_path": os.path.join(HERE, "_verify_puzzles09_result.json"),
}

if __name__ == "__main__":
    core.run(CFG, verify_only="--verify-only" in sys.argv[1:])
