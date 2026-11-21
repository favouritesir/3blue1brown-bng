# -*- coding: utf-8 -*-
"""Gold-standard TEACHER NARRATION AUDIO for Puzzles Lesson 04 (cube shadow)."""
import os
import sys

import _puzzles_audio_core as core

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
LESSON = "lesson_04"
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "puzzles", LESSON)
PAGE_PATH = os.path.join(WORKSPACE, "courses", "puzzles", LESSON + ".html")

EXPECTED_TYPES = {
    "sec-question": ["h2", "p", "figure", "p", "callout"],
    "sec-alice":    ["h2", "p", "figure", "p", "formula-box"],
    "sec-bob":      ["h2", "p", "figure", "p", "formula-box"],
    "sec-answer":   ["h2", "p", "figure", "formula-box", "callout"],
    "sec-takeaway": ["h2", "p", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-question": "sec_01_sec-question.mp3",
    "sec-alice":    "sec_02_sec-alice.mp3",
    "sec-bob":      "sec_03_sec-bob.mp3",
    "sec-answer":   "sec_04_sec-answer.mp3",
    "sec-takeaway": "sec_05_sec-takeaway.mp3",
}
GLOBAL_REQUIRED = ["কোশি", "অ্যালিস", "বব", "তিন ভাগের দুই"]

SECTIONS_DATA = {
    "sec-question": {
        "title": "প্রশ্নটি",
        "audio_file": "sec_01_sec-question.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, প্রশ্নটি। একটি ঘনককে ইচ্ছামতো ঘুরিয়ে আলোর নিচে রাখলে ছায়ার গড় ক্ষেত্রফল কত হবে।"},
            {"index": 1, "type": "p",
             "tts": "একক বাহুর ঘনকের ক্ষেত্রে উত্তর কী, সেটাই আমরা খুঁজব। একদিকে অ্যালিস কঠিন সমাকলনের পথে যান, অন্যদিকে বব একটি সুন্দর সূত্রের পথে যান।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে আলো ঘনকের উপর পড়ছে এবং নিচে তার ছায়া পড়েছে। ঘনকের অবস্থান বদলালে ছায়ার আকারও বদলায়। প্রশ্ন হলো, সমস্ত অবস্থানের গড় কত।"},
            {"index": 3, "type": "p",
             "tts": "অ্যালিস হিসাবের দিকে যান, বিভিন্ন অবস্থানের জন্য কোণের ফাংশন লিখে সমাকলন করতে থাকেন। বব অন্য পথে যান, তিনি একটি সাধারণ জ্যামিতিক সূত্র খুঁজছেন।"},
            {"index": 4, "type": "callout", "role": "conclusion",
             "tts": "এই পাঠের সৌন্দর্য হলো দুই পথ। এক পথে কঠিন সমাকলন, অন্য পথে কয়েক লাইনের সুন্দর যুক্তি, অথচ উত্তর একই।"},
        ],
    },
    "sec-alice": {
        "title": "অ্যালিসের পথ: সরাসরি হিসাব",
        "audio_file": "sec_02_sec-alice.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, অ্যালিসের পথ, সরাসরি হিসাব। ঘনকের অবস্থান তিনটি কোণ দিয়ে বর্ণনা করা যায়।"},
            {"index": 1, "type": "p",
             "tts": "প্রতিটি কোণের উপর ছায়ার ক্ষেত্রফল নির্ভর করে। তারপর সব অবস্থানের উপর গড় বের করতে হয়।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে ঘনকের তিনটি ঘূর্ণন কোণ, আর প্রতিটি অবস্থান একটি আলাদা ছায়া দিচ্ছে। তিন কোণের এই বিচরণই অ্যালিসের সমাকলনের ক্ষেত্র।"},
            {"index": 3, "type": "p",
             "tts": "এটি করা যায়, কিন্তু ত্রিমাত্রিক ঘূর্ণনের উপর সমাকলন ধৈর্য ও দক্ষতা দাবি করে। হিসাব সঠিক হলেও পথটি দীর্ঘ।"},
            {"index": 4, "type": "formula-box", "role": "conclusion",
             "tts": "গাণিতিক সূত্র, গড় ছায়ার ক্ষেত্রফল পাওয়া যায় চার পাই দিয়ে ভাগ করে গোলকের সমস্ত অবস্থানে ছায়ার ক্ষেত্রফলের সমাকলন করে। অ্যালিসের পথ ঠিক এই সমাকলনটি সমাধান করতে চাইছে।"},
        ],
    },
    "sec-bob": {
        "title": "ববের পথ: কসাই-র সূত্র",
        "audio_file": "sec_03_sec-bob.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, ববের পথ, কোশির সূত্র। বব একটি সমতল তলের প্রক্ষেপিত ক্ষেত্রফল নিয়ে ভাবেন।"},
            {"index": 1, "type": "p",
             "tts": "বব লক্ষ করেন যে একটি সমতল তলের প্রক্ষেপিত ক্ষেত্রফল তার নিজ ক্ষেত্রফলের কোণের কসাইনের পরম মান গুণ। গোলকে কোণের কসাইনের পরম মানের গড় হলো এক ভাগের দুই ভাগ।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে তলের প্রক্ষেপিত ক্ষেত্রফল কোণের কসাইন দ্বারা নির্ধারিত হচ্ছে। তলটি যত বাঁকে, প্রক্ষেপণ তত সংকুচিত হয়।"},
            {"index": 3, "type": "p",
             "tts": "যেকোনো উত্তল বস্তুর ছায়ার ক্ষেত্রফল সমান তার মোট পৃষ্ঠতলের ক্ষেত্রফলের চার ভাগের এক ভাগ। এটি কোশির প্রক্ষেপণ সূত্র নামে পরিচিত।"},
            {"index": 4, "type": "formula-box", "role": "conclusion",
             "tts": "গাণিতিক সূত্র, গড় ছায়ার ক্ষেত্রফল সমান মোট পৃষ্ঠতলের ক্ষেত্রফলের চার ভাগের এক ভাগ। এই এক লাইনেই পুরো উত্তর লুকানো আছে।"},
        ],
    },
    "sec-answer": {
        "title": "উত্তর",
        "audio_file": "sec_04_sec-answer.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, উত্তর। এখন অ্যালিস ও ববের দুই পথের হিসাব এক জায়গায় মিলবে।"},
            {"index": 1, "type": "p",
             "tts": "একক বাহুর ঘনকের মোট পৃষ্ঠতল ছয় গুণ এক অর্থাৎ ছয়। সুতরাং গড় ছায়ার ক্ষেত্রফল ছয় ভাগের চার, অর্থাৎ তিন ভাগের দুই।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে মোট পৃষ্ঠতল ছয় আর তার এক চতুর্থাংশ তিন ভাগের দুই। ছয়টি তলের অবদানই এই গড়ে মিলেছে।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, গড় ছায়ার ক্ষেত্রফল সমান ছয় ভাগের চার, অর্থাৎ তিন ভাগের দুই। সরল জ্যামিতি আর সমাকলন একই উত্তর দিচ্ছে।"},
            {"index": 4, "type": "callout", "role": "conclusion",
             "tts": "কেন এক চতুর্থাংশ। দৃশ্যমান তলগুলোর যোগফল মোটের অর্ধেক, আবার গড়ে কোণের কসাইনের পরম মানও এক ভাগের দুই। এই দুই অর্ধেক মিলে এক চতুর্থাংশ তৈরি করে।"},
        ],
    },
    "sec-takeaway": {
        "title": "শিক্ষণীয় বিষয়",
        "audio_file": "sec_05_sec-takeaway.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, শিক্ষণীয় বিষয়। কঠিন হিসাব শুরু করার আগে একটু থামা দরকার।"},
            {"index": 1, "type": "p",
             "tts": "কঠিন হিসাব শুরু করার আগে জিজ্ঞেস করুন, কোনো সাধারণ সূত্র কি কাজে আসবে। কখনো কোনো সুপরিচিত জ্যামিতিক তথ্য পুরো সমস্যাটিকে সরল করে দেয়।"},
            {"index": 2, "type": "p", "role": "conclusion",
             "tts": "এই একই সূত্র যেকোনো উত্তল বস্তুর জন্য কাজ করে। গোলক, শঙ্কু বা অ্যাপল আকৃতির বস্তুর গড় ছায়াও একই নিয়মে পাওয়া যায়।"},
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
    "verify_result_path": os.path.join(HERE, "_verify_puzzles04_result.json"),
}

if __name__ == "__main__":
    core.run(CFG, verify_only="--verify-only" in sys.argv[1:])
