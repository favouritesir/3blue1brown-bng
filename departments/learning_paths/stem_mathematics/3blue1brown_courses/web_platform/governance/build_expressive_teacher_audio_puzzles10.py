# -*- coding: utf-8 -*-
"""Gold-standard TEACHER NARRATION AUDIO for Puzzles Lesson 10 (Euler formula proof)."""
import os
import sys

import _puzzles_audio_core as core

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
LESSON = "lesson_10"
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "puzzles", LESSON)
PAGE_PATH = os.path.join(WORKSPACE, "courses", "puzzles", LESSON + ".html")

EXPECTED_TYPES = {
    "sec-formula":     ["h2", "p", "figure", "formula-box", "p", "callout"],
    "sec-tree":        ["h2", "p", "figure", "p", "formula-box"],
    "sec-dual":        ["h2", "p", "figure", "p", "callout"],
    "sec-generalize":  ["h2", "p", "figure", "formula-box", "p"],
    "sec-takeaway":    ["h2", "p", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-formula":    "sec_01_sec-formula.mp3",
    "sec-tree":       "sec_02_sec-tree.mp3",
    "sec-dual":       "sec_03_sec-dual.mp3",
    "sec-generalize": "sec_04_sec-generalize.mp3",
    "sec-takeaway":   "sec_05_sec-takeaway.mp3",
}
GLOBAL_REQUIRED = ["অয়লার", "ডুয়ালিটি", "স্প্যানিং ট্রি", "ইনভ্যারিয়েন্ট"]

SECTIONS_DATA = {
    "sec-formula": {
        "title": "সূত্রটি",
        "audio_file": "sec_01_sec-formula.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, সূত্রটি। যেকোনো সংযুক্ত সমতলিক গ্রাফের শীর্ষ, ধার ও ফলকের সম্পর্ক।"},
            {"index": 1, "type": "p",
             "tts": "যেকোনো সংযুক্ত সমতলিক গ্রাফের শীর্ষ ভি, ধার ই ও ফলক এফ হলে সবসময় ভি বিয়োগ ই প্লাস এফ সমান দুই। বাইরের অঞ্চলটিকেও একটি ফলক হিসেবে গণনা করা হয়।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে একটি সমতলিক গ্রাফ, তার শীর্ষ, ধার ও ফলক। ভেতরের ছোট ঘরগুলো আর বাইরের বড় অঞ্চল সব মিলে ফলক।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, ভি বিয়োগ ই প্লাস এফ সমান দুই। এই সূত্রটি কেবল মুখস্থ নয়, এর পেছনে এক সুন্দর গঠন আছে।"},
            {"index": 4, "type": "p",
             "tts": "উদাহরণ, একটি ত্রিভুজে ভি তিন, ই তিন, এফ দুই, ভেতর ও বাইর। তিন বিয়োগ তিন প্লাস দুই সমান দুই।"},
            {"index": 5, "type": "callout", "role": "conclusion",
             "tts": "অয়লারের মহান দৃষ্টি, সতেরো শতকের পঞ্চাশের দশকে তিনি লক্ষ করেন পলিহেড্রনের ক্ষেত্রেও একই সম্পর্ক ধরে। এটি টপোলজির জন্মের অন্যতম ধাপ।"},
        ],
    },
    "sec-tree": {
        "title": "স্প্যানিং ট্রি",
        "audio_file": "sec_02_sec-tree.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, স্প্যানিং ট্রি। প্রমাণের প্রথম ধাপ হলো গ্রাফের মেরুদণ্ড বাছা।"},
            {"index": 1, "type": "p",
             "tts": "প্রমাণের প্রথম ধাপ, গ্রাফের একটি স্প্যানিং ট্রি বাছুন, সব শীর্ষকে যুক্ত করে এমন উপগ্রাফ যাতে কোনো চক্র নেই। একটি ভি শীর্ষের ট্রিতে ই সমান ভি বিয়োগ এক টি ধার থাকে।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে চক্র বাদ দিয়ে গ্রাফের মেরুদণ্ড তৈরি করা। বাদ পড়া ধারগুলো পরে ফেরত আনা হবে।"},
            {"index": 3, "type": "p",
             "tts": "ট্রির কোনো চক্র নেই, তাই শুধু বাইরের অঞ্চল নামে একটিমাত্র ফলক। সেখানে ভি বিয়োগ ই প্লাস এফ সমান দুই, অর্থাৎ সূত্রটি ট্রির ক্ষেত্রে প্রমাণিত।"},
            {"index": 4, "type": "formula-box", "role": "conclusion",
             "tts": "গাণিতিক সূত্র, ট্রির ধার সমান ভি বিয়োগ এক এবং ট্রির ফলক সমান এক। অর্থাৎ শুধু বাইরের অঞ্চল।"},
        ],
    },
    "sec-dual": {
        "title": "ডুয়াল গ্রাফ",
        "audio_file": "sec_03_sec-dual.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, ডুয়াল গ্রাফ। বাদ পড়া ধারগুলো ফিরিয়ে আনলেই বাকি প্রমাণ শেষ।"},
            {"index": 1, "type": "p",
             "tts": "এখন বাদ পড়া ধারগুলো ফিরিয়ে আনুন। প্রতিটি বাদ দেওয়া ধার একটি নতুন চক্র তৈরি করে এবং ফলককে দুই ভাগে ভাগ করে, অর্থাৎ ই বাড়ে এক, এফও বাড়ে এক।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে ফলককে বিন্দু বানিয়ে তৈরি ডুয়াল গ্রাফ। মূল গ্রাফের ফলকগুলো এখানে নতুন শীর্ষ হয়েছে।"},
            {"index": 3, "type": "p",
             "tts": "প্রতিটি ধার ফেরত দিলে ভি বিয়োগ ই প্লাস এফ এর মান অপরিবর্তিত থাকে, কারণ বিয়োগ এক প্লাস এক শূন্য। অতএব শেষ পর্যন্ত মান দুই থাকে, আর এভাবেই পুরো প্রমাণ শেষ।"},
            {"index": 4, "type": "callout", "role": "conclusion",
             "tts": "ডুয়ালিটি, ফলকগুলোকে বিন্দু বানিয়ে ও ধারগুলোকে প্রথিক্রম করে যে গ্রাফ পাই তাকে ডুয়াল গ্রাফ বলে। মূল ও ডুয়ালের ভূমিকা বিনিময়যোগ্য।"},
        ],
    },
    "sec-generalize": {
        "title": "অন্য পৃষ্ঠে",
        "audio_file": "sec_04_sec-generalize.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, অন্য পৃষ্ঠে। অয়লারের সূত্র গোলক ও টোরাসে কীভাবে কাজ করে।"},
            {"index": 1, "type": "p",
             "tts": "গোলকের ক্ষেত্রেও ভি বিয়োগ ই প্লাস এফ সমান দুই, কিন্তু টোরাসে শূন্য। সাধারণভাবে এই মানকে বলা হয় অয়লার বৈশিষ্ট্য চাই, যা পৃষ্ঠের গঠনগত পরিচয়।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে গোলকপৃষ্ঠে অঙ্কিত গ্রাফ, একই সূত্র প্রযোজ্য। পৃষ্ঠ বদলালে সূত্রের মান বদলায়।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, অয়লার বৈশিষ্ট্য চাই সমান ভি বিয়োগ ই প্লাস এফ। গোলকে দুই, টোরাসে শূন্য।"},
            {"index": 4, "type": "p", "role": "conclusion",
             "tts": "এই কারণেই কে তিন তিন সমতলে আঁকা যায় না, কিন্তু টোরাসে যায়। পৃষ্ঠের চাই বদলালে সীমাবদ্ধতাও বদলায়।"},
        ],
    },
    "sec-takeaway": {
        "title": "শিক্ষণীয় বিষয়",
        "audio_file": "sec_05_sec-takeaway.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, শিক্ষণীয় বিষয়। সূত্র মুখস্থ করার বদলে প্রমাণের গঠন বোঝা।"},
            {"index": 1, "type": "p",
             "tts": "একটি সূত্র মুখস্থ করার বদলে তার প্রমাণের গঠন বোঝা গণিতের আসল আনন্দ। স্প্যানিং ট্রি ও এক ধার ফেরত, মাত্র দুটি ধাপে পুরো ফল।"},
            {"index": 2, "type": "p", "role": "conclusion",
             "tts": "এই কোর্সের ধাঁধাগুলোতে আমরা বারবার দেখেছি, সঠিক দৃষ্টিভঙ্গি বা ইনভ্যারিয়েন্ট খুঁজে পেলে কঠিনতা অদৃশ্য হয়ে যায়। সেই দৃষ্টিভঙ্গিটিই আমাদের সবচেয়ে বড় শিক্ষা।"},
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
    "verify_result_path": os.path.join(HERE, "_verify_puzzles10_result.json"),
}

if __name__ == "__main__":
    core.run(CFG, verify_only="--verify-only" in sys.argv[1:])
