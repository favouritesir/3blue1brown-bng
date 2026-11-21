# -*- coding: utf-8 -*-
"""Gold-standard TEACHER NARRATION AUDIO for Puzzles Lesson 05 (Moser circle)."""
import os
import sys

import _puzzles_audio_core as core

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
LESSON = "lesson_05"
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "puzzles", LESSON)
PAGE_PATH = os.path.join(WORKSPACE, "courses", "puzzles", LESSON + ".html")

EXPECTED_TYPES = {
    "sec-pattern":  ["h2", "p", "figure", "p", "callout"],
    "sec-count":    ["h2", "p", "figure", "p", "formula-box"],
    "sec-break":    ["h2", "p", "figure", "h3", "p"],
    "sec-general":  ["h2", "p", "figure", "p"],
    "sec-takeaway": ["h2", "p", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-pattern":  "sec_01_sec-pattern.mp3",
    "sec-count":    "sec_02_sec-count.mp3",
    "sec-break":    "sec_03_sec-break.mp3",
    "sec-general":  "sec_04_sec-general.mp3",
    "sec-takeaway": "sec_05_sec-takeaway.mp3",
}
GLOBAL_REQUIRED = ["মোজার", "এন নির্বাচন চার", "একত্রিশ"]

SECTIONS_DATA = {
    "sec-pattern": {
        "title": "প্রলোভনসংকুল প্যাটার্ন",
        "audio_file": "sec_01_sec-pattern.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, প্রলোভনসংকুল প্যাটার্ন। বৃত্তের উপর এনটি বিন্দু নিয়ে জোড়াগুলো রেখা দিয়ে জোড়া দিলে কত অঞ্চল তৈরি হয়।"},
            {"index": 1, "type": "p",
             "tts": "প্রথম কয়েকটি উত্তর হলো এক, দুই, চার, আট, ষোলো। স্বাভাবিকভাবেই মনে হয় পরবর্তী উত্তর বত্রিশ হবে। কিন্তু ছয়টি বিন্দুর ক্ষেত্রে পাওয়া যায় একত্রিশ, অর্থাৎ প্যাটার্ন ভেঙে পড়ে।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে বৃত্তের বিন্দুগুলোকে জোড়া দেওয়া রেখাগুলো অঞ্চল তৈরি করছে। রেখা যত বাড়ে, অঞ্চলের সংখ্যাও তত বাড়ে।"},
            {"index": 3, "type": "p",
             "tts": "প্রথম পাঁচটি ক্ষেত্রে দুইয়ের ঘাত দেখে আমরা সহজেই বত্রিশের আশা করি। কিন্তু ষষ্ঠ ক্ষেত্রে সেই ধারা ভেঙে একত্রিশ আসে। গণিতে এমন ভাঙা প্যাটার্ন নতুন কিছু শিখায়।"},
            {"index": 4, "type": "callout", "role": "conclusion",
             "tts": "আশ্চর্যের বিষয় হলো, এক দুই চার আট ষোলোর পর আসে একত্রিশ। প্রথম পাঁচটি ক্ষেত্রে দুইয়ের ঘাত, ষষ্ঠে নয়।"},
        ],
    },
    "sec-count": {
        "title": "সঠিক গণনা",
        "audio_file": "sec_02_sec-count.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, সঠিক গণনা। অঞ্চলের সংখ্যা হিসাব করতে রেখা ও ছেদবিন্দু গণনা করব।"},
            {"index": 1, "type": "p",
             "tts": "প্রতিটি নতুন রেখা যতগুলো পুরনো রেখাকে ছেদ করে, ততগুলো নতুন অঞ্চল যোগ করে। মোট অঞ্চল সমান শুরুর এক প্লাস রেখার সংখ্যা প্লাস ছেদবিন্দুর সংখ্যা।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে প্রতিটি ছেদবিন্দু নতুন অঞ্চল তৈরি করছে। দুটি রেখা পরস্পর ছেদ করার সাথে সাথেই বৃত্তের ভেতরে একটা নতুন ঘর তৈরি হয়।"},
            {"index": 3, "type": "p",
             "tts": "রেখার সংখ্যা হলো এন নির্বাচন দুই। ছেদবিন্দুর সংখ্যা হলো এন নির্বাচন চার, কারণ যেকোনো চার বিন্দু থেকে ঠিক একটি ছেদবিন্দু পাওয়া যায়।"},
            {"index": 4, "type": "formula-box", "role": "conclusion",
             "tts": "গাণিতিক সূত্র, অঞ্চলের সংখ্যা সমান এন নির্বাচন চার প্লাস এন নির্বাচন দুই প্লাস এক। এই সূত্রটি ছয় বা তার বেশি বিন্দুর ক্ষেত্রেও কাজ করে।"},
        ],
    },
    "sec-break": {
        "title": "কেন ৩২ নয়",
        "audio_file": "sec_03_sec-break.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, কেন বত্রিশ নয়। এই সূত্র দিয়ে ষষ্ঠ ক্ষেত্রের হিসাব করলেই কারণটা ধরা পড়ে।"},
            {"index": 1, "type": "p",
             "tts": "এন সমান ছয় হলে এন নির্বাচন চার হলো পনেরো এবং এন নির্বাচন দুইও পনেরো। সুতরাং অঞ্চলের সংখ্যা পনেরো প্লাস পনেরো প্লাস এক অর্থাৎ একত্রিশ, বত্রিশ নয়।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে এক দুই চার আট ষোলোর পর ষষ্ঠ পদে একত্রিশ এসেছে। দুইয়ের ঘাতের ধারা এখানেই ভেঙে পড়ে।"},
            {"index": 3, "type": "h3",
             "tts": "গভীর কারণ। দুইয়ের ঘাত আসত যদি প্রতিটি নতুন বিন্দু আগের সব রেখাকে নতুনভাবে ছেদ করত।"},
            {"index": 4, "type": "p", "role": "conclusion",
             "tts": "কিন্তু ছয়টি বিন্দুতে কিছু ছেদ একই জায়গায় মিলে যায়। এই সংঘর্ষের কারণেই বত্রিশের জায়গায় একত্রিশ পাওয়া যায়।"},
        ],
    },
    "sec-general": {
        "title": "সাধারণীকরণ",
        "audio_file": "sec_04_sec-general.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, সাধারণীকরণ। মোজারের মূল প্রশ্ন ছিল বৃত্ত নয়, বরং গোলক।"},
            {"index": 1, "type": "p",
             "tts": "মোজারের মূল প্রশ্ন ছিল বৃত্ত নয়, গোলক। গোলকের বিন্দুগুলোকে বড় বৃত্ত দিয়ে ভাগ করলে কতগুলো অঞ্চল পাওয়া যায়, সেটা তিনি জানতে চেয়েছিলেন।"},
            {"index": 2, "type": "figure",
             "tts": "চিত্রে দেখা যাচ্ছে গোলকের উপর বৃহত্তম বৃত্ত দিয়ে পৃষ্ঠ ভাগ করা হয়েছে। একাধিক বড় বৃত্ত পরস্পর ছেদ করে গোলকের উপর নতুন নতুন অঞ্চল তৈরি করে।"},
            {"index": 3, "type": "p", "role": "conclusion",
             "tts": "এখানে শিক্ষা হলো, প্যাটার্ন দেখে উত্তর বলা আর গঠন বুঝে উত্তর বের করা এক জিনিস নয়। দ্বিতীয়টি কঠিন, কিন্তু অনেক বেশি নির্ভরযোগ্য।"},
        ],
    },
    "sec-takeaway": {
        "title": "শিক্ষণীয় বিষয়",
        "audio_file": "sec_05_sec-takeaway.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, শিক্ষণীয় বিষয়। প্যাটার্ন ভাঙা কোনো ব্যর্থতা নয়।"},
            {"index": 1, "type": "p",
             "tts": "গণিতবিদেরা প্যাটার্ন ভাঙাকে ব্যর্থতা হিসেবে দেখেন না। বরং এটি নতুন গঠন আবিষ্কারের সংকেত।"},
            {"index": 2, "type": "p", "role": "conclusion",
             "tts": "পরবর্তী পাঠে আমরা দেখব কীভাবে উচ্চ মাত্রা ব্যবহার করে এ ধরনের জ্যামিতিক জটিলতা সরল করা যায়। নতুন মাত্রা অনেক অসম্ভবকেই সম্ভব করে তোলে।"},
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
    "verify_result_path": os.path.join(HERE, "_verify_puzzles05_result.json"),
}

if __name__ == "__main__":
    core.run(CFG, verify_only="--verify-only" in sys.argv[1:])
