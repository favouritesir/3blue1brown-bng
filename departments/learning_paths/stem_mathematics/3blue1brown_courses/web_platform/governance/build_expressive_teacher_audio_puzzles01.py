# -*- coding: utf-8 -*-
"""Gold-standard TEACHER NARRATION AUDIO for Puzzles Lesson 01.

22 expressive, fully phonetic Bengali cues in 5 narrated sections; exact DOM
ids/counts/types from the narration_engine.js live DOM snapshot. Replaces the
placeholder manifest with measured-ms timings, bumps the page cache-buster,
and verifies everything in headless Chrome (channel=chrome).

Usage:  python governance/build_expressive_teacher_audio_puzzles01.py
        python governance/build_expressive_teacher_audio_puzzles01.py --verify-only
"""
import os
import sys

import _puzzles_audio_core as core

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
LESSON = "lesson_01"
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "puzzles", LESSON)
PAGE_PATH = os.path.join(WORKSPACE, "courses", "puzzles", LESSON + ".html")

# Normalized narration_engine.js DOM block types per section (authoritative).
EXPECTED_TYPES = {
    "sec-im-o":       ["h2", "p", "figure", "p", "callout"],
    "sec-deconstruct": ["h2", "p", "figure", "h3", "p", "callout"],
    "sec-intuition":   ["h2", "p", "figure", "p"],
    "sec-perspective": ["h2", "p", "chapter-quote", "callout"],
    "sec-takeaway":    ["h2", "p", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-im-o":        "sec_01_sec-im-o.mp3",
    "sec-deconstruct": "sec_02_sec-deconstruct.mp3",
    "sec-intuition":   "sec_03_sec-intuition.mp3",
    "sec-perspective": "sec_04_sec-perspective.mp3",
    "sec-takeaway":    "sec_05_sec-takeaway.mp3",
}
GLOBAL_REQUIRED = ["আই এম ও", "অন্তর্দৃষ্টি"]

SECTIONS_DATA = {
    "sec-im-o": {
        "title": "আইএমও ও এই বছরের চ্যালেঞ্জ",
        "audio_file": "sec_01_sec-im-o.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, আই এম ও ও এই বছরের চ্যালেঞ্জ। শতাধিক দেশের শ্রেষ্ঠ তরুণ গণিতবিদদের এই প্রতিযোগিতার সবচেয়ে কঠিন প্রশ্নটি নিয়েই আমাদের যাত্রা শুরু।"},
            {"index": 1, "type": "p",
             "tts": "প্রতি বছর শতাধিক দেশের শ্রেষ্ঠ তরুণ গণিতবিদরা আন্তর্জাতিক গণিত অলিম্পিয়াডে অংশ নেন। দুই দিনে ছয়টি করে প্রমাণভিত্তিক প্রশ্ন থাকে এবং প্রতিটির মান সাত। স্কুলস্তরের গণিতের এটি সবচেয়ে কঠিন মঞ্চ।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে সমতলে ছড়ানো কয়েকটি বিন্দু। কঠিন ধাঁধা প্রায়ই শুরু হয় সরল চিত্র আঁকা দিয়ে। প্রথমে চোখে দেখা এই সরলতাই পরে গভীর অন্তর্দৃষ্টির পথ দেখায়।"},
            {"index": 3, "type": "p",
             "tts": "২০২৫ সালের ষষ্ঠ ও শেষ প্রশ্নটি আলাদা করে চমকপ্রদ ছিল। এটি ছিল সবচেয়ে কঠিন, আর সেই সময়কার শীর্ষ কৃত্রিম বুদ্ধিমত্তা মডেলগুলোও এটি সমাধান করতে পারেনি। তাই প্রশ্নটির পেছনের চিন্তাভাবনাটি বোঝাই আমাদের মূল লক্ষ্য।"},
            {"index": 4, "type": "callout", "role": "conclusion",
             "tts": "বিশেষ নোট, এই পাঠে আমরা কী শিখব। লক্ষ্য কেবল উত্তর জানা নয়, বরং দেখা যে কীভাবে একটি অচেনা সমস্যার সাথে খেলা, সরল উদাহরণ তৈরি এবং সঠিক দৃষ্টিভঙ্গি খোঁজা এই তিনটি ধাপ পথ দেখায়। এই তিন ধাপই পরের সব পাঠের ভিত্তি হবে।"},
        ],
    },
    "sec-deconstruct": {
        "title": "পাঠ্য পড়া ও সরল উদাহরণ",
        "audio_file": "sec_02_sec-deconstruct.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, পাঠ্য পড়া ও সরল উদাহরণ। কঠিন প্রশ্নের ভাষা ভেঙে ছোট ছোট অংশে বোঝার অভ্যাস এখানে গড়ে তুলব।"},
            {"index": 1, "type": "p",
             "tts": "যেকোনো কঠিন প্রশ্নের প্রথম কাজ হলো বাক্যগুলোকে ছোট ছোট অংশে ভেঙে বোঝা। প্রতিটি শর্তের অর্থ নিজের শব্দে বলুন, তারপর কাগজে একটি ছোট উদাহরণ আঁকুন। এই সরল অভ্যাসই বিমূর্ত সমস্যাকে হাতের নাগালে নিয়ে আসে।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে একটি ছোট উদাহরণ আঁকার মাধ্যমে বিমূর্ত শর্তগুলো নির্দিষ্ট রূপ নিচ্ছে। বড় সমস্যার অদৃশ্য গঠন এখানে দুই তিনটি বিন্দু আর রেখার মধ্যে স্পষ্ট হয়ে ওঠে।"},
            {"index": 3, "type": "h3",
             "tts": "খেলা থেকেই শুরু। গ্রান্ট স্যান্ডারসনের কাছে খেলা মানে হলো শর্তগুলোর সাথে কলমে কথা বলা, যার মাধ্যমে লুকানো নিয়ম ধীরে ধীরে দৃশ্যমান হয়।"},
            {"index": 4, "type": "p",
             "tts": "দুই বা তিনটি বস্তু নিয়ে প্রশ্নটি চেষ্টা করে দেখুন। সাধারণত ক্ষুদ্রতম ক্ষেত্রেই লুকানো থাকে সেই নিয়ম, যা পরে বড় ক্ষেত্রেও কাজ করে। তাই ছোট উদাহরণ কোনো পালানোর পথ নয়, বরং আবিষ্কারের প্রথম ধাপ।"},
            {"index": 5, "type": "callout", "role": "conclusion",
             "tts": "বিশেষ নোট, পর্যবেক্ষণ। গ্রান্ট স্যান্ডারসন বার বার দেখান যে খেলা কোনো অপ্রয়োজনীয় কাজ নয়। এটি হলো অন্তর্দৃষ্টি অর্জনের প্রথম বৈজ্ঞানিক পদ্ধতি।"},
        ],
    },
    "sec-intuition": {
        "title": "অন্তর্দৃষ্টির পথ",
        "audio_file": "sec_03_sec-intuition.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, অন্তর্দৃষ্টির পথ। কৃত্রিম বুদ্ধিমত্তা যখন চেনা ধাঁচে হিসাব করে, তখন মানুষের প্রয়োজন হয় নতুন পথ বানানোর।"},
            {"index": 1, "type": "p",
             "tts": "কৃত্রিম বুদ্ধিমত্তা মডেলগুলো প্রচলিত ধাঁচে হিসাব করতে পারে। কিন্তু যখন কোনো তৈরি করা ধাঁচই কাজ করে না, তখন প্রয়োজন হয় নতুন করণীয় উপায় বানানোর। এইখানেই মানুষের কৌতূহল ও সৃজনশীলতা আসল পরীক্ষার মুখোমুখি হয়।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে একাধিক সম্ভাব্য পথ, আর সেগুলোর মধ্যে সঠিক দৃষ্টিভঙ্গিটি বেছে নেওয়া হচ্ছে। ভুল পথে অনেকক্ষণ হাঁটার পরও সঠিক কোণটি খুঁজে পেলে পুরো সমস্যা হঠাৎ সরল হয়ে যায়।"},
            {"index": 3, "type": "p", "role": "conclusion",
             "tts": "এই ভিডিওর মূল শিক্ষা হলো, উত্তরের চেয়ে গুরুত্বপূর্ণ হলো সেই মানসিক প্রক্রিয়া। তার মাধ্যমে আমরা অজানার সাথে পরিচিত হই এবং নিজেদের ধারণাকে সংশোধন করি।"},
        ],
    },
    "sec-perspective": {
        "title": "দৃষ্টিভঙ্গি বদল",
        "audio_file": "sec_04_sec-perspective.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, দৃষ্টিভঙ্গি বদল। এক পা পেছনে গিয়ে পুরো গঠন নতুন করে দেখলে অনেক জটিলতা সরল হয়।"},
            {"index": 1, "type": "p",
             "tts": "অনেক সময় সমস্যা কঠিন থাকে কারণ আমরা ভুল কোণ থেকে দেখি। এক পা পেছনে গিয়ে পুরো গঠনটি নতুনভাবে দেখলে জটিলতা সরল হয়ে যায়।"},
            {"index": 2, "type": "chapter-quote",
             "tts": "উদ্ধৃতি, গণিতের সমস্যা বা ধাঁধা প্রকৃত গণিতের জন্য ততটুকু গুরুত্বপূর্ণ, যতখানি গল্প বা উপাখ্যান শিশুর জন্য বাস্তব জীবন বোঝার ক্ষেত্রে গুরুত্বপূর্ণ। বলেছেন টেরেন্স টাও।"},
            {"index": 3, "type": "callout", "role": "conclusion",
             "tts": "বিশেষ নোট, মনে রাখবেন। কোনো প্রশ্নের সাথে প্রথমে লড়াই করুন, হিসাবের সরঞ্জাম নয়। সঠিক প্রশ্নটি খুঁজে পাওয়াই অর্ধেক সমাধান।"},
        ],
    },
    "sec-takeaway": {
        "title": "শিক্ষণীয় বিষয়",
        "audio_file": "sec_05_sec-takeaway.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, শিক্ষণীয় বিষয়। আন্তর্জাতিক গণিত অলিম্পিয়াডের মতো প্রতিযোগিতা আমাদের নতুন ধারণা তৈরির তাগিদ দেয়।"},
            {"index": 1, "type": "p",
             "tts": "আন্তর্জাতিক গণিত অলিম্পিয়াডের মতো প্রতিযোগিতা আমাদের মনে করিয়ে দেয় যে কঠিন সমস্যা সমাধান মানেই নতুন ধারণা তৈরি করা। পুরনো সূত্র মুখস্থ করলে নতুন ধাঁধার সামনে হার মানতে হয়।"},
            {"index": 2, "type": "p", "role": "conclusion",
             "tts": "পরবর্তী পাঠগুলোতে আমরা ঠিক এই একই দৃষ্টিভঙ্গি ব্যবহার করে কয়েকটি বিখ্যাত ধাঁধা সমাধান করব। ইনভ্যারিয়েন্ট, সম্ভাবনা, জ্যামিতি ও গ্রাফ তত্ত্বের মাধ্যমে সেই পথ আমাদের সামনে খুলে যাবে।"},
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
    "verify_result_path": os.path.join(HERE, "_verify_puzzles01_result.json"),
}

if __name__ == "__main__":
    core.run(CFG, verify_only="--verify-only" in sys.argv[1:])
