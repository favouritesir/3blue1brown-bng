# -*- coding: utf-8 -*-
"""Gold-standard TEACHER NARRATION AUDIO for Puzzles Lesson 07 (generating functions)."""
import os
import sys

import _puzzles_audio_core as core

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
LESSON = "lesson_07"
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "puzzles", LESSON)
PAGE_PATH = os.path.join(WORKSPACE, "courses", "puzzles", LESSON + ".html")

EXPECTED_TYPES = {
    "sec-puzzle":    ["h2", "p", "figure", "p", "callout"],
    "sec-gf":        ["h2", "p", "figure", "formula-box", "p"],
    "sec-coeff":     ["h2", "p", "figure", "h3", "p", "callout"],
    "sec-olympiad":  ["h2", "p", "figure", "p"],
    "sec-takeaway":  ["h2", "p", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-puzzle":   "sec_01_sec-puzzle.mp3",
    "sec-gf":       "sec_02_sec-gf.mp3",
    "sec-coeff":    "sec_03_sec-coeff.mp3",
    "sec-olympiad": "sec_04_sec-olympiad.mp3",
    "sec-takeaway": "sec_05_sec-takeaway.mp3",
}
GLOBAL_REQUIRED = ["জেনারেটিং ফাংশন", "একক মূল", "আই এম ও"]

SECTIONS_DATA = {
    "sec-puzzle": {
        "title": "ধাঁধা ও উপসেট",
        "audio_file": "sec_01_sec-puzzle.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, ধাঁধা ও উপসেট। এক থেকে এন পর্যন্ত সংখ্যার সেট থেকে নির্দিষ্ট যোগফলবিশিষ্ট উপসেট গণনা করব।"},
            {"index": 1, "type": "p",
             "tts": "ধরা যাক এক, দুই, তিন থেকে শুরু করে এন পর্যন্ত একটি সেট। কতগুলো উপসেট আছে যাদের উপাদানের যোগফল কোনো নির্দিষ্ট মানের সমান। সরাসরি গণনা দ্রুতই অসম্ভব হয়ে পড়ে।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে একটি সেট থেকে বিভিন্ন উপসেট বাছা হচ্ছে। প্রতিটি উপাদানকে নেওয়া বা না নেওয়া এই দুই অবস্থার একটিতে রাখা হয়।"},
            {"index": 3, "type": "p",
             "tts": "প্রতিটি উপাদানের দুটি অবস্থা, নেওয়া বা না নেওয়া। এম টি উপাদানের জন্য দুইয়ের ঘাত এম সম্ভাবনা। কিন্তু আমাদের কেবল কয়েকটির যোগফল গণনা করতে হবে।"},
            {"index": 4, "type": "callout", "role": "conclusion",
             "tts": "যোগফলভিত্তিক শর্ত সরাসরি যাচাই করতে হলে অসংখ্য উপসেট দেখতে হয়। আমাদের চাই একবারেই সব উত্তর বের করার উপায়।"},
        ],
    },
    "sec-gf": {
        "title": "জেনারেটিং ফাংশন",
        "audio_file": "sec_02_sec-gf.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, জেনারেটিং ফাংশন। প্রতিটি উপাদানকে এক প্লাস এক্সের ঘাত দিয়ে প্রতিনিধিত্ব করব।"},
            {"index": 1, "type": "p",
             "tts": "প্রতিটি উপাদানের জন্য এক প্লাস এক্সের ঘাত কে বসান। এক মানে নেওয়া হয়নি, এক্সের ঘাত কে মানে নেওয়া হয়েছে। সবগুলোর গুণফলের বহুপদীতে ঘাতের সহগই সেই যোগফলের উপসেট সংখ্যা।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে গুণফলের ঘাত ও সহগ, প্রতিটি ঘাত এক একটি যোগফল। এক্সের ঘাত যত বাড়ে, সেই যোগফলের উপসেট সংখ্যা সহগ হিসেবে বসে।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এক থেকে এন পর্যন্ত এক প্লাস এক্সের ঘাত কে থেকে শুরু করে সবগুলোর গুণফল সমান সব ঘাতের সহগের যোগ, অর্থাৎ এস সহগ গুণ এক্সের ঘাত এস। প্রতিটি ঘাত এক একটি যোগফলের কথা বলে।"},
            {"index": 4, "type": "p", "role": "conclusion",
             "tts": "এখানে এস সহগ হলো ঠিক এস যোগফলবিশিষ্ট উপসেটের সংখ্যা। গুণের নিয়মই নিশ্চিত করে যে প্রতিটি উপসেট ঠিক একবার গণনা হয়।"},
        ],
    },
    "sec-coeff": {
        "title": "সহগ বের করা",
        "audio_file": "sec_03_sec-coeff.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, সহগ বের করা। জেনারেটিং ফাংশন লিখে ফেললেই কাজ শেষ হয় না, সহগ বের করাও দরকার।"},
            {"index": 1, "type": "p",
             "tts": "এখন প্রশ্ন দাঁড়ায়, এই বহুপদীর নির্দিষ্ট ঘাতের সহগ কীভাবে পাওয়া যায়। একগুচ্ছ জটিল গুণফল না করে কিছু কৌশল কাজে দেয়।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে নির্দিষ্ট ঘাতের সহগ উৎপন্ন করা হচ্ছে। ঘাতটিকে আলাদা করে দেখলে সহগের গঠন স্পষ্ট হয়।"},
            {"index": 3, "type": "h3",
             "tts": "মূলের ফিল্টার। এক্সে এক, ঋণাত্মক এক বা একক মূল বসিয়ে বিশেষ যোগফলের যোগ বা বিয়োগ বের করা যায়।"},
            {"index": 4, "type": "p",
             "tts": "এক্সে এক, ঋণাত্মক এক বা অন্য একক মূল বসিয়ে কিছু বিশেষ যোগফলের যোগ বা বিয়োগ বের করা যায়। এটি একক মূল ফিল্টার নামে পরিচিত।"},
            {"index": 5, "type": "callout", "role": "conclusion",
             "tts": "সব সহগের যোগফল পেতে এক্সে এক বসান, তখন মোট উপসেট পাওয়া যায় দুইয়ের ঘাত এন। জোড় বিজোড় আলাদা করতে এক্সে ঋণাত্মক এক বসান।"},
        ],
    },
    "sec-olympiad": {
        "title": "অলিম্পিয়াডের কৌশল",
        "audio_file": "sec_04_sec-olympiad.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, অলিম্পিয়াডের কৌশল। বড় সংখ্যার ক্ষেত্রে হিসাবের বদলে গঠন দেখতে হয়।"},
            {"index": 1, "type": "p",
             "tts": "আসল আই এম ও প্রশিক্ষণ সমস্যায় সংখ্যা এত বড় হয় যে হিসাবের বদলে গঠন দেখতে হয়। জেনারেটিং ফাংশন সেই গঠনকে একটিমাত্র বহুপদীতে ধরে আনে।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে বড় সেটের জন্য গঠনই হলো পথ। অসংখ্য উপসেটের মধ্যে নিয়মটি একটিমাত্র বহুপদীর ভেতরে লুকানো।"},
            {"index": 3, "type": "p", "role": "conclusion",
             "tts": "একবার সঠিক বহুপদী লিখে ফেললে বাকিটা কেবল বীজগণিত। এটি মানুষের জন্য সহজ, কম্পিউটারের জন্যও দক্ষ।"},
        ],
    },
    "sec-takeaway": {
        "title": "শিক্ষণীয় বিষয়",
        "audio_file": "sec_05_sec-takeaway.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, শিক্ষণীয় বিষয়। গণনার ধাঁধায় প্রশ্ন বদলে ফেলা প্রায়ই মুক্তি দেয়।"},
            {"index": 1, "type": "p",
             "tts": "গণনার ধাঁধায় কত প্রশ্নটিকে কোন ফাংশন প্রশ্নে বদলে ফেলা প্রায়ই মুক্তি দেয়। বহুপদীর সহগের ভাষায় গণনা আরও স্বচ্ছ হয়।"},
            {"index": 2, "type": "p", "role": "conclusion",
             "tts": "এই একই ধারণা পরে চেসবোর্ড ও গ্রাফতত্ত্বের ধাঁধায় আবার দেখা যাবে। সঠিক ফাংশনটি খুঁজে পেলে অনেক কঠিন প্রশ্ন সহজ হয়।"},
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
    "verify_result_path": os.path.join(HERE, "_verify_puzzles07_result.json"),
}

if __name__ == "__main__":
    core.run(CFG, verify_only="--verify-only" in sys.argv[1:])
