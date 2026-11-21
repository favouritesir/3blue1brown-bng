# -*- coding: utf-8 -*-
"""
Rebuild the TEACHER NARRATION AUDIO for Number Theory Lesson 03
("The hidden pi inside prime regularity", Bengali) to the gold standard.

  * 21 cues in 4 narrated sections with EXACTLY the same section IDs,
    audio_file names, cue types and cue order as the live narrationEngine DOM.
    The non-narrated sec-lab (data-no-narration) is NOT included.
  * All spoken scripts are embedded below as SECTIONS_DATA (no external input
    files are read at build time), so the build is fully reproducible.
  * Figure cues are genuine 2-4 sentence natural Bengali explanations; the
    artificial label "চিত্র প্রদর্শনী" is explicitly forbidden and checked.
  * Phonetic safeguards: Leibniz -> লাইবনিজ, Gaussian -> গাউসিয়ান,
    Euler -> অয়লার, arctan -> আর্কট্যান, lattice -> ল্যাটিস.
    No TeX, Latin letters, dashes, brackets or markup.
  * Per-cue prosody: h2 -5%/+2Hz, chapter-quote -3%, p +2%, figure -4%,
    callout +0%, formula-box -8%, conclusion -3%. Real 350 ms cue gaps.
  * ffmpeg -c copy concatenation into the existing mp3 names; exact-ms
    manifest.json + manifest.js with a page cache-buster bump (1 -> 2).
  * Headless Chrome (channel=chrome) verification: DOM <-> manifest 1:1,
    0 duplicates, 0 quiz/media-tab types, non-zero mp3s, valid JSON,
    0 page errors, 0 forbidden labels, KaTeX annotations present.

Usage:
    python governance/build_expressive_teacher_audio_nt03.py            # build + verify
    python governance/build_expressive_teacher_audio_nt03.py --verify-only
"""
from _nt_expressive_core import LessonConfig, main

EXPECTED_TYPES = {
    "sec-leibniz-series": ["h2", "p", "formula-box", "figure", "p", "formula-box"],
    "sec-gaussian":       ["h2", "p", "figure", "p", "formula-box", "callout"],
    "sec-product":        ["h2", "p", "figure", "formula-box", "p", "formula-box"],
    "sec-conclusion":     ["h2", "p", "p"],
}
EXPECTED_AUDIO_FILES = {
    "sec-leibniz-series": "sec_01_sec-leibniz-series.mp3",
    "sec-gaussian":       "sec_02_sec-gaussian.mp3",
    "sec-product":        "sec_03_sec-product.mp3",
    "sec-conclusion":     "sec_04_sec-conclusion.mp3",
}
EXPECTED_COUNT = {
    "sec-leibniz-series": 6, "sec-gaussian": 6,
    "sec-product": 6, "sec-conclusion": 3,
}

SECTIONS_DATA = {
    "sec-leibniz-series": {
        "title": "লাইবনিটজের ধারা ও লুকোনো বৃত্ত",
        "audio_file": "sec_01_sec-leibniz-series.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "প্রথম পরিচ্ছেদ, লাইবনিজের ধারা আর লুকোনো বৃত্ত।"},
            {"index": 1, "type": "p",
             "tts": "সতেরো শতকের সাতের দশকে গটফ্রিড লাইবনিজ এক আশ্চর্য সূত্র আবিষ্কার করেছিলেন। এক বিয়োগ এক ভাগ তিন প্লাস এক ভাগ পাঁচ বিয়োগ এক ভাগ সাত প্লাস এক ভাগ নয়, এইভাবে চলতে থাকে, আর যোগফল হয় পাই ভাগ চার। বাঁ দিকে কেবল সাধারণ ভগ্নাংশ, ডান দিকে বৃত্তের পরিমাপ, এই মিলনই বিস্ময়কর।"},
            {"index": 2, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, এন সমান শূন্য থেকে অসীম পর্যন্ত ঋণাত্মক একের এন ঘাত ভাগ দুই এন প্লাস একের যোগফল, সমান এক বিয়োগ এক ভাগ তিন প্লাস এক ভাগ পাঁচ বিয়োগ এক ভাগ সাত, ইত্যাদি, সমান পাই ভাগ চার।"},
            {"index": 3, "type": "figure",
             "tts": "এই গ্রাফে আংশিক যোগফলগুলো পাই ভাগ চারের হলুদ ড্যাশ্ড রেখার ওপর দিয়ে দোলে। প্রথম পদ এক, তারপর শূন্য দশমিক ছয় ছয় সাত, শূন্য দশমিক আট ছয় সাত, শূন্য দশমিক সাত দুই চার, করে ক্রমশ কাছে আসে। প্রতিটি নতুন পদ আগেরের চেয়ে ছোট, তাই দোলন ক্রমশ শান্ত হয়ে সঠিক মানের দিকে এগিয়ে যায়।"},
            {"index": 4, "type": "p",
             "tts": "এই সূত্রের সহজ ব্যাখ্যা আসে আর্কট্যান ফাংশন থেকে। জ্যামিতিক ধারা এক ভাগের এক প্লাস টি স্কয়ার সমান এক বিয়োগ টি স্কয়ার প্লাস টি পাওয়ার ফোর বিয়োগ, ইত্যাদি কে শূন্য থেকে এক পর্যন্ত ইন্টিগ্রেট করলে আর্কট্যান এক পাওয়া যায়। আর আর্কট্যান এক সমান পাই ভাগ চার।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, আর্কট্যান এক্স সমান শূন্য থেকে এক্স পর্যন্ত এক ভাগের এক প্লাস টি স্কয়ারের ইন্টিগ্রাল, সমান এক্স বিয়োগ এক্স কিউব ভাগ তিন প্লাস এক্স পাওয়ার ফাইভ ভাগ পাঁচ, ইত্যাদি।"},
        ],
    },

    "sec-gaussian": {
        "title": "গাউসিয়ান পূর্ণসংখ্যা ও দুই বর্গের যোগফল",
        "audio_file": "sec_02_sec-gaussian.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "দ্বিতীয় পরিচ্ছেদ, গাউসিয়ান পূর্ণসংখ্যা আর দুই বর্গের যোগফল।"},
            {"index": 1, "type": "p",
             "tts": "জটিল তলে পূর্ণসংখ্যার বিন্দুগুলো এ প্লাস বি আই এক একটি বর্গাকার ল্যাটিস তৈরি করে, একে গাউসিয়ান পূর্ণসংখ্যা বলে। ব্যাসার্ধ আর এর বৃত্তের ভেতরে কতগুলো বিন্দু আছে তা গণনা করা যায়। প্রশ্ন হলো, কোন কোন পূর্ণসংখ্যা দুইটি বর্গের যোগফল হিসেবে লেখা যায়।"},
            {"index": 2, "type": "figure",
             "tts": "এই ছবিতে বৃত্তের ভেতরের ল্যাটিস বিন্দুগুলো দেখানো হয়েছে। হলুদ বিন্দুগুলো এমন সংখ্যা যারা দুই বর্গের যোগফল, যেমন পাঁচ সমান এক স্কয়ার প্লাস দুই স্কয়ার, তেরো সমান দুই স্কয়ার প্লাস তিন স্কয়ার। বাকি বিন্দুগুলো কোনো বর্গ যুগল থেকে আসে না। ছবিতে দেখা যায় এই বিশেষ সংখ্যাগুলোর ঘনত্ব কতটা।"},
            {"index": 3, "type": "p",
             "tts": "প্রতিটি গাউসিয়ান পূর্ণসংখ্যার নর্ম এ প্লাস বি আই সমান এ স্কয়ার প্লাস বি স্কয়ার। এখন প্রশ্ন দাঁড়ায়, কোন কোন পূর্ণসংখ্যা এনের জন্য এ স্কয়ার প্লাস বি স্কয়ার সমান এন সমাধান আছে। দুই বর্গের যোগফলের এই প্রশ্নটি সরাসরি নর্মের গুণনীয়ক থেকে উত্তর পায়।"},
            {"index": 4, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, নর্ম এ প্লাস বি আই সমান এ স্কয়ার প্লাস বি স্কয়ার, সমান এ প্লাস বি আই গুণ এ বিয়োগ বি আই।"},
            {"index": 5, "type": "callout",
             "tts": "বিশেষ নোট, প্রাইমের দুই শ্রেণি। যে প্রাইম চার কে প্লাস এক আকারের, যেমন পাঁচ, তেরো, সতেরো, তা গাউসিয়ান পূর্ণসংখ্যায় দুটি গুণনীয়কে ভেঙে যায়। কিন্তু চার কে প্লাস তিন আকারের প্রাইম ভেঙে যায় না, তাই দুই বর্গের যোগফলে শুধু প্রথম শ্রেণির প্রাইমের জোড় সংখ্যক ঘাতই চলে। দুইয়ের ক্ষেত্রে রয়েছে এক একক ব্যতিক্রম।"},
        ],
    },

    "sec-product": {
        "title": "অয়লারের গুণফলে পাই",
        "audio_file": "sec_03_sec-product.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "তৃতীয় পরিচ্ছেদ, অয়লারের গুণফলে পাই।"},
            {"index": 1, "type": "p",
             "tts": "এখন বৃত্তের ভেতরের বিন্দু সংখ্যা দুইভাবে গণনা করি। একদিকে এটি প্রায় পাই আর স্কয়ার। অন্যদিকে প্রতিটি গাউসিয়ান পূর্ণসংখ্যার নর্ম এনের জন্য আর টু অফ এন সংখ্যক উপায়ে বিন্দু পড়ে, তাই মোট যোগফল আর টু অফ এন। দুই হিসাব মিলিয়ে অয়লারের বিখ্যাত গুণফল পাওয়া যায়।"},
            {"index": 2, "type": "figure",
             "tts": "এই ছবিতে বলয়গুলো ধাপে ধাপে প্রাইমের গুণনীয়ক যোগ করতে দেখায়। পাঁচের ফ্যাক্টর পাঁচ ভাগ চার, তেরোর তেরো ভাগ বারো, আর তিনের তিন ভাগ চার, সাতের সাত ভাগ আট, এভাবে গুণ করে ক্রমশ পাই ভাগ চারের কাছে পৌঁছানো যায়। প্রতিটি বলয় একটি নতুন প্রাইমের অবদান দেখায়।"},
            {"index": 3, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, পাই ভাগ চার সমান চার একের সমান প্রাইমগুলোর পি ভাগ পি বিয়োগ একের গুণফল, গুণ চার তিনের সমান প্রাইমগুলোর পি ভাগ পি প্লাস একের গুণফল।"},
            {"index": 4, "type": "p",
             "tts": "সূত্রটি পড়া যায় এভাবে, প্রতিটি চার কে প্লাস এক প্রাইম পাই ভাগ চার কে পি ভাগ পি বিয়োগ এক গুণ বাড়ায়, আর প্রতিটি চার কে প্লাস তিন প্রাইম পি ভাগ পি প্লাস এক গুণ কমায়। পাঁচ দিয়ে শুরু করে ক্রমশ গুণ করতে থাকলে মানটি স্থির হয়ে পাই ভাগ চারে পৌঁছায়।"},
            {"index": 5, "type": "formula-box",
             "tts": "গাণিতিক সূত্র, পাই ভাগ চার সমান সব প্রাইম পি তে এক বিয়োগ কাই ফোর অফ পি ভাগ পি এর গুণফলের বিপরীত, যেখানে কাই ফোর অফ দুই সমান শূন্য, চার একের সমান প্রাইমে এক, আর চার তিনের সমান প্রাইমে ঋণাত্মক এক।"},
        ],
    },

    "sec-conclusion": {
        "title": "দুই ধারার মিলন ও উপসংহার",
        "audio_file": "sec_04_sec-conclusion.mp3",
        "cues": [
            {"index": 0, "type": "h2",
             "tts": "চতুর্থ পরিচ্ছেদ, দুই ধারার মিলন আর উপসংহার।"},
            {"index": 1, "type": "p",
             "tts": "এখন লাইবনিজের মূল ধারাটি আবার দেখুন, এক বিয়োগ এক ভাগ তিন প্লাস এক ভাগ পাঁচ, এই যোগ বিয়োগের পর্যায়ক্রম আসলে কাই ফোর অফ এনের মতোই। চার কে প্লাস একে ধনাত্মক, চার কে প্লাস তিনে ঋণাত্মক, আর দুইয়ে শূন্য। তাই লাইবনিজের ধারা আর অয়লারের গুণফল একই গাণিতিক বস্তুর দুটি রূপ।"},
            {"index": 2, "type": "p", "role": "conclusion",
             "tts": "আরও এক কথা, একই কৌশল বেসেল সমস্যায় কাজ করে, এক প্লাস এক ভাগ চার প্লাস এক ভাগ নয়, ইত্যাদি সমান পাই স্কয়ার ভাগ ছয়। শুধু সেখানে কাই ফোরের বদলে সব প্রাইম অংশ নেয়। আধুনিক সংখ্যাতত্ত্বে ধারা আর গুণফলের এই মিলন এক অত্যন্ত শক্তিশালী হাতিয়ার।"},
        ],
    },
}

CFG = LessonConfig(
    number=3,
    course="number_theory",
    title="অধ্যায় ০৩ — প্রাইম নিয়মিততায় লুকোনো পাই",
    sections_data=SECTIONS_DATA,
    expected_types=EXPECTED_TYPES,
    expected_audio_files=EXPECTED_AUDIO_FILES,
    expected_count=EXPECTED_COUNT,
    total_cues=21,
    required_phonetic={
        "লাইবনিজ": "Leibniz safeguard",
        "গাউসিয়ান": "Gaussian safeguard",
        "অয়লার": "Euler safeguard",
        "আর্কট্যান": "arctan safeguard",
        "ল্যাটিস": "lattice safeguard",
    },
)

if __name__ == "__main__":
    main(CFG)
