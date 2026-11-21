# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Number Theory Lesson 02
("Visualizing all Pythagorean triples", Bengali) to the gold standard.

  * 26 cues in 5 narrated sections with EXACTLY the same section IDs,
    audio_file names, cue types and cue order as the live narrationEngine DOM.
    The non-narrated sec-lab (data-no-narration) is NOT included.
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time), so the build is fully reproducible.
  * Figure cues are genuine 2-4 sentence natural Bengali explanations; the
    artificial label "চিত্র প্রদর্শনী" is explicitly forbidden and checked.
  * Phonetic safeguards: Pythagorean -> পাইথাগোরিয়ান, Gaussian -> গাউসিয়ান,
    factorization -> ফ্যাক্টরাইজেশন, conjugate -> কনজুগেট, ring -> রিং.
    No TeX, Latin letters, dashes, brackets or markup.
  * Per-cue prosody: h2 -5%/+2Hz, chapter-quote -3%, p +2%, figure -4%,
    callout +0%, formula-box -8%, conclusion -3%. Real 350 ms cue gaps.
  * ffmpeg -c copy concatenation into the existing mp3 names; exact-ms
    manifest.json + manifest.js with a page cache-buster bump (1 -> 2).
  * Headless Chrome (channel=chrome) verification: DOM <-> manifest 1:1,
    0 duplicates, 0 quiz/media-tab types, non-zero mp3s, valid JSON,
    0 page errors, 0 forbidden labels, KaTeX annotations present.

Usage:
    python governance/build_expressive_teacher_audio_nt02.py            # build + verify
    python governance/build_expressive_teacher_audio_nt02.py --verify-only
"""
from _nt_expressive_core import LessonConfig, main

EXPECTED_TYPES = {
    "sec-familiar-triangles": ["h2", "p", "figure", "formula-box", "p"],
    "sec-unit-circle":        ["h2", "p", "figure", "p", "formula-box", "formula-box", "callout"],
    "sec-complex-numbers":    ["h2", "p", "figure", "formula-box", "p", "callout", "formula-box"],
    "sec-all-triples":        ["h2", "p", "figure", "p"],
    "sec-conclusion":         ["h2", "p", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-familiar-triangles": "sec_01_sec-familiar-triangles.mp3",
    "sec-unit-circle":        "sec_02_sec-unit-circle.mp3",
    "sec-complex-numbers":    "sec_03_sec-complex-numbers.mp3",
    "sec-all-triples":        "sec_04_sec-all-triples.mp3",
    "sec-conclusion":         "sec_05_sec-conclusion.mp3",
}
EXPECTED_COUNT = {
    "sec-familiar-triangles": 5, "sec-unit-circle": 7,
    "sec-complex-numbers": 7, "sec-all-triples": 4, "sec-conclusion": 3,
}

SECTIONS_DATA = {
    "sec-familiar-triangles": {
        "title": "পরিচিত ত্রিভুজ ও মূল প্রশ্ন",
        "audio_file": "sec_01_sec-familiar-triangles.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, পরিচিত ত্রিভুজ আর মূল প্রশ্ন।"},
            {"index": 1, "type": "p",
             "tts": "স্কুলে আমরা কয়েকটি বিশেষ সমকোণী ত্রিভুজ শিখে থাকি, তিন চার পাঁচ, পাঁচ বারো তেরো, আট পনেরো সতেরো। পাইথাগোরিয়ান সূত্র বলে, বাহু তিনটির দৈর্ঘ্য যদি এ, বি আর সি হয় তবে এ স্কয়ার প্লাস বি স্কয়ার সমান সি স্কয়ার। প্রশ্ন হলো, এই সমীকরণের সমস্ত পূর্ণসংখ্যা সমাধান কীভাবে পাওয়া যায়?"},
            {"index": 2, "type": "figure",
             "tts": "এই চিত্রে ত্রিভুজের তিন বাহুর ওপর তিনটি বর্গ আঁকা হয়েছে। দুটি ছোট বর্গের ক্ষেত্রফল এ স্কয়ার আর বি স্কয়ার যোগ করলে বড় বর্গের ক্ষেত্রফল সি স্কয়ারের সমান হয়। এই ছবিটিই পাইথাগোরিয়ান উপপাদ্যের জ্যামিতিক রূপ, যা সংখ্যার সমীকরণকে ক্ষেত্রফলে রূপ দেয়।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এ স্কয়ার প্লাস বি স্কয়ার সমান সি স্কয়ার।"},
            {"index": 4, "type": "p", "role": "conclusion",
             "tts": "কোনো ট্রিপলকে দুই, তিন বা যেকোনো সংখ্যা দিয়ে গুণ করলে নতুন ট্রিপল পাওয়া যায়। তিন চার পাঁচ থেকে ছয় আট দশ, নয় বারো পনেরো, ইত্যাদি। কিন্তু এগুলো আসল নতুন নয়, কারণ একই আকারের স্কেল মাত্র বদলেছে, তাই আমরা আদিম ট্রিপল খোঁজছি যেগুলো আর ভাগ করা যায় না।"},
        ],
    },

    "sec-unit-circle": {
        "title": "একক বৃত্ত, পরিমেয় বিন্দু ও ইউক্লিডের সূত্র",
        "audio_file": "sec_02_sec-unit-circle.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, একক বৃত্ত, পরিমেয় বিন্দু আর ইউক্লিডের সূত্র।"},
            {"index": 1, "type": "p",
             "tts": "সি দিয়ে ভাগ করে সমীকরণকে সরল করি, এ ভাগ সি স্কয়ার প্লাস বি ভাগ সি স্কয়ার সমান এক। অর্থাৎ আমাদের কাজ হলো একক বৃত্ত এক্স স্কয়ার প্লাস ওয়াই স্কয়ার সমান একের ওপর এমন সব বিন্দু খোঁজা যাদের এক্স ও ওয়াই পরিমেয় সংখ্যা। এই রূপান্তরের ফলে জ্যামিতির প্রশ্নটি বীজগণিতের প্রশ্নে দাঁড়ায়।"},
            {"index": 2, "type": "figure",
             "tts": "এই ছবিতে মূলবিন্দুর বাঁয়ের বিন্দু থেকে একটি রেখা বৃত্তকে কাটছে, আর ছেদবিন্দুটি এক্স ও ওয়াই স্থানাঙ্কে চিহ্নিত। রেখার ঢাল টি যুক্তিসহ একটি পরিমেয় সংখ্যা হওয়ায় ছেদবিন্দুটিও পরিমেয় হয়। বৃত্তের ওপরের প্রতিটি বিন্দু এইভাবে একটি নতুন ট্রিপল জন্ম দেয়।"},
            {"index": 3, "type": "p",
             "tts": "রেখার সমীকরণ ওয়াই সমান টি গুণ এক্স প্লাস এক কে এক্স স্কয়ার প্লাস ওয়াই স্কয়ার সমান একে বসিয়ে সমাধান করলে পাই, এক্স সমান এক বিয়োগ টি স্কয়ার ভাগের এক প্লাস টি স্কয়ার, আর ওয়াই সমান দুই টি ভাগের এক প্লাস টি স্কয়ার। এখানে টি একটি পরিমেয় ঢাল, তাই এক্স ও ওয়াইও পরিমেয়। পরে এম আর এন দিয়ে টি কে প্রকাশ করে পূর্ণসংখ্যার সূত্র পাওয়া যায়।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এক্স সমান এক বিয়োগ টি স্কয়ার ভাগ এক প্লাস টি স্কয়ার, ওয়াই সমান দুই টি ভাগ এক প্লাস টি স্কয়ার।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এ, বি, সি সমান এম স্কয়ার বিয়োগ এন স্কয়ার, দুই এম এন, এম স্কয়ার প্লাস এন স্কয়ার।"},
            {"index": 6, "type": "callout",
             "tts": "বিশেষ নোট, আদিম হওয়ার শর্ত। প্রত্যেকটি আদিম ট্রিপল ঠিক একটি করে জোড়া এম আর এন থেকে আসে, যেখানে এম বড় এন থেকে, জিসিডি এম কমা এন সমান এক, আর এম ও এন এক জোড় এক বিজোড়। এই শর্তগুলো ছাড়া একই ট্রিপল বারবার আসবে।"},
        ],
    },

    "sec-complex-numbers": {
        "title": "জটিল সংখ্যা ও গাউসিয়ান পূর্ণসংখ্যা",
        "audio_file": "sec_03_sec-complex-numbers.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, জটিল সংখ্যা আর গাউসিয়ান পূর্ণসংখ্যা।"},
            {"index": 1, "type": "p",
             "tts": "একই সমীকরণকে জটিল সংখ্যার ভাষায় লেখা যায়, এ স্কয়ার প্লাস বি স্কয়ার সমান এ প্লাস বি আই গুণ এ বিয়োগ বি আই। এখানে এ প্লাস বি আই আর এ বিয়োগ বি আই পরস্পরের কনজুগেট, আর তাদের গুণফল একটি পূর্ণবর্গ। এই পদ্ধতিটি বীজগণিতকে গাউসিয়ান পূর্ণসংখ্যার রিংয়ে নিয়ে যায়।"},
            {"index": 2, "type": "figure",
             "tts": "এই জটিল তলে একটি বিন্দু এ প্লাস বি আই দেখানো হয়েছে, সাথে তার অনুভূমিক ও উল্লম্ব উপাদান এ আর বি। বিন্দুটির মূলবিন্দু থেকে দূরত্বের বর্গই হলো এ স্কয়ার প্লাস বি স্কয়ার, অর্থাৎ সি স্কয়ার। ছবিতে দেখা যায় কীভাবে একটি জটিল সংখ্যার নর্মই ট্রিপলের তৃতীয় বাহু নির্ধারণ করে।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এ প্লাস বি আই গুণ এ বিয়োগ বি আই সমান এ স্কয়ার প্লাস বি স্কয়ার সমান সি স্কয়ার।"},
            {"index": 4, "type": "p",
             "tts": "গাউসিয়ান পূর্ণসংখ্যার রিংয়ে অনন্য ফ্যাক্টরাইজেশন প্রযোজ্য, যেমন সাধারণ পূর্ণসংখ্যায় প্রতিটি সংখ্যা প্রাইমের গুণফলে ভেঙে যায়। পাঁচ কে ভেঙে দেখা যায়, পাঁচ সমান দুই প্লাস আই গুণ দুই বিয়োগ আই। এই ভাঙা আর তার কনজুগেটের ভাঙা মিলে একটি বর্গ তৈরি করে, যা থেকে ট্রিপলের উৎপত্তি।"},
            {"index": 5, "type": "callout",
             "tts": "বিশেষ নোট, কেন চার কে প্লাস তিন প্রাইম বাধা। সি স্কয়ার একটি পূর্ণবর্গ, তাই তার ফ্যাক্টরাইজেশনে প্রতিটি গাউসিয়ান প্রাইমের ঘাত জোড়। কিন্তু চার কে প্লাস তিন আকারের প্রাইম গাউসিয়ান পূর্ণসংখ্যায় ভেঙে যায় না, ফলে সি স্কয়ারে তার ঘাত জোড় হতে পারে না। তাই এই প্রাইমগুলো কোনো আদিম ট্রিপলের হতে পারে না।"},
            {"index": 6, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এম প্লাস এন আইয়ের বর্গ সমান এম স্কয়ার বিয়োগ এন স্কয়ার প্লাস দুই এম এন আই, তাই এ, বি, সি সমান এম স্কয়ার বিয়োগ এন স্কয়ার, দুই এম এন, এম স্কয়ার প্লাস এন স্কয়ার।"},
        ],
    },

    "sec-all-triples": {
        "title": "সমস্ত ট্রিপলের মানচিত্র",
        "audio_file": "sec_04_sec-all-triples.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, সমস্ত ট্রিপলের মানচিত্র।"},
            {"index": 1, "type": "p",
             "tts": "এখন সব টুকরো মিলছে। যেকোনো আদিম ট্রিপলের এ প্লাস বি আই অবশ্যই কোনো গাউসিয়ান পূর্ণসংখ্যার বর্গের সমান, একক গুণক ছাড়া। কারণ সি স্কয়ারের ফ্যাক্টরাইজেশনে প্রতিটি প্রাইমের ঘাত জোড় হওয়ায় ভেতরের সংখ্যাটিও বর্গ হতে বাধ্য।"},
            {"index": 2, "type": "figure",
             "tts": "এই চিত্রটি আবার দেখুন, এখন বর্গগুলোর ক্ষেত্রফল শুধু সংখ্যা নয়, বরং জটিল সংখ্যার নর্মের গুণফল। বাঁয়ের বর্গ এ স্কয়ার, ওপরের বর্গ বি স্কয়ার আর ডানের বর্গ সি স্কয়ার, তিনটি মিলে পাইথাগোরিয়ান সমীকরণ গড়ে তোলে। প্রতিটি বর্গই একটি গাউসিয়ান সংখ্যার বর্গের প্রতীক।"},
            {"index": 3, "type": "p", "role": "conclusion",
             "tts": "এই জোড়া নির্মাণ থেকে ট্রিপলের এক বৃক্ষ তৈরি হয়। মূলে তিন চার পাঁচ, তার থেকে শাখা হিসেবে পাঁচ বারো তেরো, আট পনেরো সতেরো, সাত চব্বিশ পঁচিশ, কুড়ি একুশ ঊনত্রিশ, ইত্যাদি। প্রতিটি শাখা আগের একটি গাউসিয়ান সংখ্যাকে আবার বর্গ করে পাওয়া যায়।"},
        ],
    },

    "sec-conclusion": {
        "title": "বীজগণিত ও জ্যামিতির মিলন",
        "audio_file": "sec_05_sec-conclusion.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "পঞ্চম পরিচ্ছেদ, বীজগণিত আর জ্যামিতির মিলন।"},
            {"index": 1, "type": "p",
             "tts": "আমরা শুরু করেছিলাম তিনটি সংখ্যার এক সরল সমীকরণ দিয়ে, এ স্কয়ার প্লাস বি স্কয়ার সমান সি স্কয়ার। শেষ করছি জটিল সংখ্যার অনন্য ফ্যাক্টরাইজেশনে। একক বৃত্তের পরিমেয় বিন্দু, জটিল তলের ল্যাটিস আর বর্গের জ্যামিতি, এসব মিলে একই গল্প বলে।"},
            {"index": 2, "type": "p", "role": "conclusion",
             "tts": "এই পদ্ধতি শক্তিশালী কারণ এটি কেবল বের করে না, বোঝায়ও। কেন চার কে প্লাস তিন প্রাইম আদিম ট্রিপলে আসতে পারে না, কেন আলাদা এম এন জোড়া আলাদা ট্রিপল দেয়, কেন প্রতিটি আদিম ট্রিপল ঠিক একবার আসে, সবকিছুর উত্তর মিলে যায় একক ফ্যাক্টরাইজেশনের জ্যামিতি থেকে।"},
        ],
    },
}

CFG = LessonConfig(
    number=2,
    course="number_theory",
    title="অধ্যায় ০২ — সমস্ত পাইথাগোরিয়ান ট্রিপলের দৃশ্যায়ন",
    sections_data=SECTIONS_DATA,
    expected_types=EXPECTED_TYPES,
    expected_audio_files=EXPECTED_AUDIO_FILES,
    expected_count=EXPECTED_COUNT,
    total_cues=26,
    required_phonetic={
        "পাইথাগোরিয়ান": "Pythagorean safeguard",
        "গাউসিয়ান": "Gaussian safeguard",
        "ফ্যাক্টরাইজেশন": "factorization safeguard",
        "কনজুগেট": "conjugate safeguard",
    },
)

if __name__ == "__main__":
    main(CFG)
