# -*- coding: utf-8 -*-
"""
Builder for 3Blue1Brown Essence of Probability Lesson 03:
Bayes' Rule and Diagnostic Testing / বেইজের সূত্র ও মেডিক্যাল টেস্টের হেঁয়ালি

Deliverables:
1. Authentic Bengali master script:
   departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_probability/lesson_03_bayes_rule/dubbing_pipeline/3b1b_prob_l03_bangla_master_script.json
2. Audio cues manifest:
   departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/probability/lesson_03/manifest.json
   departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/probability/lesson_03/manifest.js
3. Single-Shell Lesson Data JSON:
   departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/data/probability/lesson_03.json
"""

import json
import os
from pathlib import Path

BASE_DIR = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses")

MASTER_SCRIPT_PATH = (
    BASE_DIR
    / "essence_of_probability"
    / "lesson_03_bayes_rule"
    / "dubbing_pipeline"
    / "3b1b_prob_l03_bangla_master_script.json"
)
AUDIO_DIR = BASE_DIR / "web_platform" / "assets" / "audio" / "probability" / "lesson_03"
MANIFEST_JSON_PATH = AUDIO_DIR / "manifest.json"
MANIFEST_JS_PATH = AUDIO_DIR / "manifest.js"
DATA_JSON_PATH = BASE_DIR / "web_platform" / "data" / "probability" / "lesson_03.json"

MASTER_SCRIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
DATA_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 1. AUTHENTIC BENGALI MASTER DUBBING SCRIPT (50+ Rich Cues)
# ==============================================================================

master_script = [
    {
        "id": 1,
        "start": 0.0,
        "end": 7.2,
        "duration": 7.2,
        "en": "Imagine taking a medical test for a rare disease. The lab informs you the test is ninety-nine percent accurate.",
        "bn": "কল্পনা করুন একটি বাস্তব পরিস্থিতি: আপনি একটি অত্যন্ত বিরল রোগের রক্ত পরীক্ষা করালেন। ল্যাবরেটরি থেকে জানানো হলো টেস্টটি নিরানব্বই শতাংশ নির্ভুল।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 2,
        "start": 7.8,
        "end": 15.4,
        "duration": 7.6,
        "en": "A few days later, the report arrives, and it says positive. Naturally, you might panic, assuming you are almost certainly sick.",
        "bn": "কয়েকদিন পর রিপোর্ট হাতে এলো এবং সেখানে লেখা পজিটিভ। যে কারো তাৎক্ষণিক প্রতিক্রিয়া হবে তীব্র আতঙ্ক—ধরে নেওয়া যে তিনি নিশ্চিতভাবেই রোগে আক্রান্ত।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 3,
        "start": 16.0,
        "end": 24.2,
        "duration": 8.2,
        "en": "After all, ninety-nine percent accurate sounds like a ninety-nine percent chance of having the disease. But this is where intuition fails completely.",
        "bn": "কারণ সাধারণ কাণ্ডজ্ঞানে মনে হয়, ৯৯ শতাংশ নির্ভুল টেস্টে পজিটিভ আসা মানে রোগ থাকার সম্ভাবনাও ৯৯ শতাংশ। কিন্তু এখানেই আমাদের স্বজ্ঞা সম্পূর্ণ মুখ থুবড়ে পড়ে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 4,
        "start": 24.8,
        "end": 33.5,
        "duration": 8.7,
        "en": "In reality, the probability you actually have the disease might be less than ten percent! In fact, you are overwhelmingly likely to be completely healthy.",
        "bn": "বাস্তব সত্যটি হলো: আপনার সত্যি সত্যি রোগাক্রান্ত হওয়ার সম্ভাবনা হয়তো দশ শতাংশেরও কম! অর্থাৎ পজিটিভ রিপোর্ট সত্ত্বেও আপনি সুস্থ থাকার সম্ভাবনাই সবচেয়ে বেশি!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 5,
        "start": 34.0,
        "end": 42.6,
        "duration": 8.6,
        "en": "This shocking counter-intuitive result is known as the false positive paradox, and understanding it is one of the greatest triumphs of probability theory.",
        "bn": "এই আপাত অবিশ্বাস্য ফলাফলটি গণিতে ফলস পজিটিভ প্যারাডক্স নামে পরিচিত। আর এই রহস্যের সমাধান সম্ভাব্যতা তত্ত্বের অন্যতম উজ্জ্বল ও বাস্তবমুখী বিজয়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 6,
        "start": 43.2,
        "end": 51.5,
        "duration": 8.3,
        "en": "The mathematics that governs this phenomenon is Bayes' rule—a foundational law for updating beliefs in the light of new evidence.",
        "bn": "এই বাস্তবতাকে নিয়ন্ত্রণকারী মূল গাণিতিক চালিকাশক্তি হলো বেইজের সূত্র—নতুন প্রমাণের উপস্থিতিতে বিশ্বাসকে যৌক্তিকভাবে হালনাগাদ করার এক অনন্য রাজকীয় ভিত্তি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 7,
        "start": 52.0,
        "end": 60.8,
        "duration": 8.8,
        "en": "To see why our initial intuition was so terribly flawed, let's unpack what ninety-nine percent accuracy actually means in a medical context.",
        "bn": "আমাদের প্রাথমিক অনুমান কেন এতটা ভুল ছিল তা বুঝতে হলে আসুন প্রথমে দেখা যাক চিকিৎসা বিজ্ঞানে ৯৯ শতাংশ নির্ভুলতা বলতে আসলে কী বোঝায়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 8,
        "start": 61.4,
        "end": 70.2,
        "duration": 8.8,
        "en": "A diagnostic test has two separate performance metrics: sensitivity, also called true positive rate, and specificity, or true negative rate.",
        "bn": "যেকোনো ডায়াগনস্টিক টেস্টের দুটি সম্পূর্ণ পৃথক বৈশিষ্ট্য থাকে: সেনসিটিভিটি বা ট্রু পজিটিভ রেট, এবং স্পেসিফিসিটি বা ট্রু নেগেটিভ রেট।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 9,
        "start": 70.8,
        "end": 79.5,
        "duration": 8.7,
        "en": "Sensitivity asks: Given that a patient is truly sick, what is the probability the test correctly turns positive? Here, that's ninety-nine percent.",
        "bn": "সেনসিটিভিটি প্রশ্ন করে: যদি একজন রোগী সত্যিই আক্রান্ত হন, তবে টেস্টটি পজিটিভ হওয়ার সম্ভাবনা কত? আমাদের সমস্যায় এটি হলো ৯৯ শতাংশ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 10,
        "start": 80.0,
        "end": 88.5,
        "duration": 8.5,
        "en": "Specificity asks: Given that a person is healthy, what is the probability the test correctly reads negative? That is also ninety-nine percent.",
        "bn": "স্পেসিফিসিটি প্রশ্ন করে: একজন সুস্থ মানুষের ক্ষেত্রে টেস্টটি নির্ভুল নেগেটিভ রিপোর্ট দেওয়ার সম্ভাবনা কত? এটিও ধরা যাক ৯৯ শতাংশ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 11,
        "start": 89.0,
        "end": 97.2,
        "duration": 8.2,
        "en": "This means there is a one percent false positive rate: one percent of completely healthy people will be incorrectly flagged as positive.",
        "bn": "এর অর্থ হলো ফলস পজিটিভের হার মাত্র এক শতাংশ: সম্পূর্ণ সুস্থ মানুষের প্রতি একশত জনের একজন ভুলবশত পজিটিভ শনাক্ত হবেন।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 12,
        "start": 97.8,
        "end": 106.5,
        "duration": 8.7,
        "en": "So far, everything seems reassuringly precise. But there is a crucial third number that human brains almost always ignore: the base rate.",
        "bn": "এখন পর্যন্ত সবকিছু অত্যন্ত নিখুঁত মনে হচ্ছে। কিন্তু এখানে তৃতীয় একটি অতি গুরুত্বপূর্ণ সংখ্যা রয়েছে যা মানব মস্তিষ্ক প্রায়শই পুরোপুরি ভুলে যায়: বেস রেট।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 13,
        "start": 107.0,
        "end": 115.5,
        "duration": 8.5,
        "en": "The base rate, or prior probability, is the overall prevalence of the disease in the general population before taking any test.",
        "bn": "বেস রেট বা প্রাইয়র প্রবাবিলিটি হলো কোনো পরীক্ষা করানোর আগে সামগ্রিক জনসংখ্যার মধ্যে সেই রোগটির স্বাভাবিক বিস্তারের হার।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 14,
        "start": 116.0,
        "end": 124.5,
        "duration": 8.5,
        "en": "Suppose this disease is rare: it affects only one in every one thousand people. That is a prior probability P of D equal to point zero zero one.",
        "bn": "ধরা যাক রোগটি অত্যন্ত বিরল: প্রতি এক হাজার জনে মাত্র একজনের এই রোগটি থাকে। অর্থাৎ প্রাইয়র সম্ভাবনা পি অব ডি সমান শূন্য দশমিক শূন্য শূন্য এক।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 15,
        "start": 125.0,
        "end": 133.8,
        "duration": 8.8,
        "en": "When people hear about the ninety-nine percent test accuracy, they fixate on that number and suffer from what psychologists call the base rate fallacy.",
        "bn": "মানুষ যখন টেস্টের ৯৯ শতাংশ নির্ভুলতার কথা শোনে, তখন তাদের চোখ কেবল সেই সংখ্যাতেই আটকে থাকে—মনোবিজ্ঞানে একে বলা হয় বেস রেট ফ্যালাসি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 16,
        "start": 134.4,
        "end": 143.0,
        "duration": 8.6,
        "en": "To eradicate this cognitive trap once and for all, let's step away from confusing percentage symbols and look at natural frequencies and visual geometry.",
        "bn": "এই মানসিক ফাঁদটি চিরতরে উপড়ে ফেলতে আসুন বিভ্রান্তিকর শতকরা চিহ্নের বদলে প্রাকৃতিক সংখ্যার ফ্রিকোয়েন্সি ট্রি এবং জ্যামিতিক ক্ষেত্রফলের সাহায্য নিই।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 17,
        "start": 143.6,
        "end": 152.2,
        "duration": 8.6,
        "en": "Consider a representative sample of one thousand people randomly selected from this population.",
        "bn": "কল্পনা করুন একটি প্রতিনিধিত্বমূলক সমাজ যেখানে দৈবভাবে এক হাজার জন মানুষকে একত্র করা হয়েছে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 18,
        "start": 152.8,
        "end": 161.5,
        "duration": 8.7,
        "en": "Because the disease prevalence is one in one thousand, exactly one person in this group has the disease, while nine hundred ninety-nine are healthy.",
        "bn": "যেহেতু রোগের বিস্তার প্রতি হাজারে একজন, তাই এই এক হাজার জনের মধ্যে গড়ে ঠিক একজন মানুষ রোগাক্রান্ত, আর বাকি নয়শত নিরানব্বই জন সম্পূর্ণ সুস্থ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 19,
        "start": 162.0,
        "end": 170.5,
        "duration": 8.5,
        "en": "Now, we administer the ninety-nine percent accurate test to every single one of these one thousand individuals. What happens?",
        "bn": "এবার আমরা এই এক হাজার জনের প্রত্যেককে সেই ৯৯ শতাংশ নির্ভুল টেস্টটি প্রয়োগ করলাম। বলুন তো ল্যাবে কী ঘটবে?",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 20,
        "start": 171.0,
        "end": 179.8,
        "duration": 8.8,
        "en": "First, take the single infected person. With ninety-nine percent sensitivity, the test detects the virus and yields a true positive result.",
        "bn": "প্রথমে সেই একক অসুস্থ মানুষটির কথা ভাবুন। ৯৯ শতাংশ সংবেদনশীলতার কারণে টেস্টটি প্রায় নিশ্চিতভাবেই সঠিক পজিটিভ রিপোর্ট প্রদান করবে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 21,
        "start": 180.4,
        "end": 189.0,
        "duration": 8.6,
        "en": "Now, take the nine hundred ninety-nine healthy individuals. With ninety-nine percent specificity, ninety-nine percent of them test negative.",
        "bn": "এবার বাকি নয়শত নিরানব্বই জন সুস্থ ব্যক্তির দিকে তাকান। ৯৯ শতাংশ নির্দিষ্টতার কারণে তাদের শতকরা ৯৯ ভাগই নির্ভুল নেগেটিভ রিপোর্ট পাবেন।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 22,
        "start": 189.6,
        "end": 198.5,
        "duration": 8.9,
        "en": "That is roughly nine hundred eighty-nine correct negative reports. But what about the remaining one percent of healthy people?",
        "bn": "অর্থাৎ প্রায় নয়শত উননব্বই জন ব্যক্তি সঠিক নেগেটিভ ফল পাবেন। কিন্তু সুস্থ ব্যক্তিদের অবশিষ্ট এক শতাংশের কী দশা হবে?",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 23,
        "start": 199.0,
        "end": 207.8,
        "duration": 8.8,
        "en": "One percent of nine hundred ninety-nine is approximately ten people! These ten healthy people receive a false positive result.",
        "bn": "নয়শত নিরানব্বই জনের এক শতাংশ হলো প্রায় দশ জন মানুষ! এই দশ জন সম্পূর্ণ সুস্থ ব্যক্তি ভুলবশত পজিটিভ রিপোর্ট হাতে পাবেন!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 24,
        "start": 208.4,
        "end": 217.2,
        "duration": 8.8,
        "en": "Now step back and gather everyone who tested positive into a room. How many people are standing in that room?",
        "bn": "এবার একটু পেছনে সরে এসে চিন্তা করুন: যারা যারা পজিটিভ রিপোর্ট পেয়েছেন, তাদের সবাইকে যদি একটি কক্ষে একত্র করা হয়, তবে সেখানে কতজন মানুষ থাকবেন?",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 25,
        "start": 217.8,
        "end": 226.5,
        "duration": 8.7,
        "en": "There is one genuinely sick person who tested positive, and ten healthy people who also tested positive. That makes eleven positive people in total!",
        "bn": "সেখানে উপস্থিত থাকবেন একজন সত্যিকারের অসুস্থ ব্যক্তি, আর তার সাথে সুস্থ কিন্তু ফলস পজিটিভ পাওয়া দশ জন ব্যক্তি—সর্বমোট এগারো জন মানুষ!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 26,
        "start": 227.0,
        "end": 235.8,
        "duration": 8.8,
        "en": "If you are one of those eleven people holding a positive test, what is the chance you are actually sick?",
        "bn": "এখন আপনি যদি সেই এগারো জন পজিটিভ রিপোর্টধারীর একজন হন, তবে আপনার সত্যি সত্যি অসুস্থ হওয়ার সম্ভাবনা কত?",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 27,
        "start": 236.4,
        "end": 245.2,
        "duration": 8.8,
        "en": "It is simply one out of eleven! One divided by eleven is approximately nine point zero nine percent—less than ten percent!",
        "bn": "তা হলো মাত্র এগারো জনের ভেতর একজন! এক ভাগ এগারো সমান প্রায় নয় দশমিক শূন্য নয় শতাংশ—দশ শতাংশেরও কম!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 28,
        "start": 245.8,
        "end": 254.5,
        "duration": 8.7,
        "en": "Look at that tree diagram: the healthy population is so vast that even a tiny one percent error rate produces ten times more false alarms than true detections.",
        "bn": "ফ্রিকোয়েন্সি ট্রির দিকে তাকান: সুস্থ মানুষের সংখ্যা এত বিপুল যে মাত্র এক শতাংশ ভুলের পরেও সত্যিকারের অসুস্থ মানুষের চেয়ে দশ গুণ বেশি ফলস অ্যালার্ম সৃষ্টি হয়!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 29,
        "start": 255.0,
        "end": 263.8,
        "duration": 8.8,
        "en": "Now let's translate this into our signature geometric representation: a two-dimensional area diagram of the sample space.",
        "bn": "এবার আসুন এই ঘটনাকে আমাদের পরিচিত জ্যামিতিক রূপকল্পে রূপান্তর করি: নমুনা ক্ষেত্রের একটি টুডি ক্ষেত্রফল চিত্রে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 30,
        "start": 264.4,
        "end": 273.2,
        "duration": 8.8,
        "en": "Imagine a unit square representing the total universe of possibilities, with width equal to one and height equal to one.",
        "bn": "কল্পনা করুন একটি এক একক দৈর্ঘ্যের বর্গক্ষেত্র, যার প্রস্থ এক এবং উচ্চতা এক, যা আমাদের সমগ্র নমুনা মহাবিশ্ব নির্দেশ করে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 31,
        "start": 273.8,
        "end": 282.5,
        "duration": 8.7,
        "en": "We divide the square horizontally by the prior: a microscopic vertical strip on the left represents disease D, with width point zero zero one.",
        "bn": "আমরা বর্গক্ষেত্রটিকে অনুভূমিকভাবে ভাগ করি: বাম পাশে মাত্র শূন্য দশমিক শূন্য শূন্য এক প্রস্থের অতি সরু একটি স্ট্রিপ হলো রোগাক্রান্ত মানুষের অঞ্চল ডি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 32,
        "start": 283.0,
        "end": 291.8,
        "duration": 8.8,
        "en": "The remaining ninety-nine point nine percent of the square represents the healthy population, not D.",
        "bn": "আর বর্গক্ষেত্রের বাকি ৯৯.৯ শতাংশ সুবিশাল অঞ্চলটি অধিকার করে সুস্থ মানুষের দল, যাকে আমরা বলি নট ডি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 33,
        "start": 292.4,
        "end": 301.2,
        "duration": 8.8,
        "en": "Now we slice vertically based on the test result: in the disease strip, ninety-nine percent of the height is colored green for true positives.",
        "bn": "এবার টেস্ট রিপোর্টের ভিত্তিতে উল্লম্বভাবে কাটুন: রোগাক্রান্ত সরু স্ট্রিপটির ৯৯ শতাংশ উচ্চতা ট্রু পজিটিভ হিসেবে সবুজ রঙে চিহ্নিত হবে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 34,
        "start": 301.8,
        "end": 310.5,
        "duration": 8.7,
        "en": "Its area is width point zero zero one times height point nine nine, giving point zero zero zero nine nine.",
        "bn": "এর ক্ষেত্রফল হলো প্রস্থ শূন্য দশমিক শূন্য শূন্য এক গুণ উচ্চতা শূন্য দশমিক নয় নয়, যার মান শূন্য দশমিক শূন্য শূন্য শূন্য নয় নয়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 35,
        "start": 311.0,
        "end": 319.8,
        "duration": 8.8,
        "en": "In the healthy region, only a thin sliver of one percent height is colored red for false positives.",
        "bn": "অপরদিকে সুস্থ ব্যক্তিদের সুবিশাল অঞ্চলে মাত্র এক শতাংশ উচ্চতার অতি পাতলা একটি ফালি ফলস পজিটিভ হিসেবে লাল রঙে রঞ্জিত হবে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 36,
        "start": 320.4,
        "end": 329.2,
        "duration": 8.8,
        "en": "Its area is width point nine nine nine times height point zero one, which equals point zero zero nine nine nine.",
        "bn": "এর ক্ষেত্রফল হলো প্রস্থ শূন্য দশমিক নয় নয় নয় গুণ উচ্চতা শূন্য দশমিক শূন্য এক, অর্থাৎ শূন্য দশমিক শূন্য শূন্য নয় নয় নয়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 37,
        "start": 329.8,
        "end": 338.5,
        "duration": 8.7,
        "en": "When a positive test occurs, our universe crops! We throw away all negative regions and only keep the positive areas.",
        "bn": "এখন যখনই টেস্ট পজিটিভ এলো, আমাদের মহাবিশ্ব ক্রপ বা সংকুচিত হয়ে গেল! সমস্ত নেগেটিভ অঞ্চল বিলুপ্ত হয়ে শুধু পজিটিভ অঞ্চলগুলো অবশিষ্ট রইল।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 38,
        "start": 339.0,
        "end": 347.8,
        "duration": 8.8,
        "en": "The conditional probability P of D given positive is the green area divided by the sum of green and red areas.",
        "bn": "শর্তাধীন সম্ভাব্যতা পি অব ডি গিভেন পজিটিভ হলো কেবল সবুজ ক্ষেত্রফল ভাগ সবুজ ও লাল ক্ষেত্রফলের সমষ্টি!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 39,
        "start": 348.4,
        "end": 357.2,
        "duration": 8.8,
        "en": "The red rectangle is roughly ten times wider than the green rectangle! That geometric reality directly explains why false alarms dominate.",
        "bn": "জ্যামিতিকভাবে স্পষ্ট দেখা যায়: লাল আয়তক্ষেত্রটি সবুজ আয়তক্ষেত্রের চেয়ে প্রায় দশ গুণ বেশি চওড়া! এই কারণেই ফলস অ্যালার্মের আধিপত্য তৈরি হয়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 40,
        "start": 357.8,
        "end": 366.5,
        "duration": 8.7,
        "en": "Now let us write this geometric insight into the formal algebraic language of probability: Bayes' Theorem.",
        "bn": "এবার আসুন এই নিখুঁত জ্যামিতিক উপলব্ধিকে সম্ভাব্যতার আনুষ্ঠানিক সার্বজনীন ভাষায় প্রকাশ করি: বেইজের উপপাদ্য।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 41,
        "start": 367.0,
        "end": 376.0,
        "duration": 9.0,
        "en": "By definition, the conditional probability P of D given positive equals P of D and positive divided by the total probability P of positive.",
        "bn": "শর্তাধীন সম্ভাবনার মৌলিক সূত্র অনুযায়ী, পি অব ডি গিভেন পজিটিভ সমান লবে পি অব ডি এবং পজিটিভের যৌথ সম্ভাবনা, আর হরে মোট পি অব পজিটিভ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 42,
        "start": 376.6,
        "end": 385.5,
        "duration": 8.9,
        "en": "The numerator is the product rule: prior P of D multiplied by likelihood P of positive given D.",
        "bn": "গুণন বিধি অনুসারে লবটি হলো: প্রাইয়র পি অব ডি গুণ লাইকলিহুড পি অব পজিটিভ গিভেন ডি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 43,
        "start": 386.0,
        "end": 395.2,
        "duration": 9.2,
        "en": "The denominator expands via the Law of Total Probability: true positives plus false positives.",
        "bn": "আর হরটি সমগ্র সম্ভাব্যতা নীতির মাধ্যমে প্রসারিত হয়: ট্রু পজিটিভ ক্ষেত্রফল যোগ ফলস পজিটিভ ক্ষেত্রফল।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 44,
        "start": 395.8,
        "end": 405.0,
        "duration": 9.2,
        "en": "Putting it together gives the classic formula: P of D given positive equals P of positive given D times P of D, over P of positive given D times P of D plus P of positive given not D times P of not D.",
        "bn": "একত্র করলে আমরা পাই বেইজের মূল সমীকরণ: পি অব ডি গিভেন পজিটিভ সমান, উপরে পি অব পজিটিভ গিভেন ডি গুণ পি অব ডি; আর নিচে ট্রু পজিটিভ ও ফলস পজিটিভের যোগফল।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 45,
        "start": 405.6,
        "end": 414.5,
        "duration": 8.9,
        "en": "Notice the four foundational terms: Prior belief, Likelihood of evidence, Marginal total evidence, and Posterior updated belief.",
        "bn": "বেইজিয়ান চিন্তার চারটি কেন্দ্রীয় স্তম্ভ লক্ষ্য করুন: প্রাইয়র বা পূর্ববর্তী বিশ্বাস, লাইকলিহুড বা প্রমাণের সম্ভাবনা, মার্জিনাল বা সমগ্র প্রমাণ, এবং পোস্টেরিয়র বা হালনাগাদ বিশ্বাস।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 46,
        "start": 415.0,
        "end": 424.0,
        "duration": 9.0,
        "en": "Now comes a profound question: If one test leaves you at only nine percent certainty, is medical testing useless? Far from it!",
        "bn": "এবার একটি গভীর দার্শনিক প্রশ্ন আসে: একটি টেস্ট পজিটিভ আসার পরেও যদি সম্ভাবনা মাত্র নয় শতাংশ থাকে, তবে কি মেডিকেল টেস্টের কোনো মূল্য নেই? মোটেই না!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 47,
        "start": 424.6,
        "end": 433.8,
        "duration": 9.2,
        "en": "Look at how much your belief jumped: from point one percent to nine percent—a ninety-fold increase in probability from a single piece of evidence!",
        "bn": "লক্ষ্য করুন আপনার বিশ্বাসে কতটা উল্লম্ফন ঘটেছে: শূন্য দশমিক এক শতাংশ থেকে সরাসরি নয় শতাংশ—একটিমাত্র প্রমাণের কারণে সম্ভাবনা নব্বই গুণ বৃদ্ধি পেয়েছে!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 48,
        "start": 434.4,
        "end": 443.5,
        "duration": 9.1,
        "en": "And what happens if you take a second, independent test from a different laboratory, and it also comes back positive?",
        "bn": "আর যদি আপনি সম্পূর্ণ ভিন্ন ল্যাবরেটরি থেকে দ্বিতীয় একটি স্বাধীন টেস্ট করান এবং সেটিও পজিটিভ আসে, তখন কী ঘটবে?",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 49,
        "start": 444.0,
        "end": 453.2,
        "duration": 9.2,
        "en": "This is the magic of Bayesian updating: your old posterior becomes your new prior! You start the second calculation with a prior of nine percent.",
        "bn": "এটাই বেইজিয়ান আপডেটিংয়ের আসল জাদু: আপনার প্রথম টেস্টের পোস্টেরিয়র হয়ে ওঠে দ্বিতীয় টেস্টের নতুন প্রাইয়র! আপনি নয় শতাংশ প্রাইয়র নিয়ে দ্বিতীয় সমীকরণ শুরু করবেন।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 50,
        "start": 453.8,
        "end": 463.0,
        "duration": 9.2,
        "en": "Plugging point zero nine into Bayes' rule yields a posterior of ninety-one percent! Two consecutive positive tests turn ambiguity into near certainty.",
        "bn": "সেই নয় শতাংশকে বেইজের সূত্রে বসালে দ্বিতীয় পোস্টেরিয়র পৌঁছে যায় একানব্বই শতাংশে! দুটি ধারাবাহিক পজিটিভ টেস্ট অনিশ্চয়তাকে সরিয়ে সুদৃঢ় নিশ্চয়তা নিয়ে আসে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 51,
        "start": 463.6,
        "end": 473.0,
        "duration": 9.4,
        "en": "This is how rational thinking operates: extraordinary claims require extraordinary evidence, and beliefs evolve step by step as evidence accumulates.",
        "bn": "যৌক্তিক বৈজ্ঞানিক চিন্তার সৌন্দর্য ঠিক এখানেই: অসাধারণ দাবির জন্য অসাধারণ প্রমাণের প্রয়োজন হয়, এবং একের পর এক প্রমাণের আলোয় বিশ্বাস ক্রমাগত সত্যের দিকে ধাবিত হয়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 52,
        "start": 473.6,
        "end": 483.5,
        "duration": 9.9,
        "en": "Bayes' rule is not just a formula for medical tests; it is the universal mathematics of learning, scientific inquiry, and machine intelligence.",
        "bn": "বেইজের সূত্র কেবল রক্ত পরীক্ষার অংক নয়; এটি সত্যের সন্ধান, বিজ্ঞানচর্চা এবং আধুনিক কৃত্রিম বুদ্ধিমত্তার যৌক্তিক শিক্ষার সার্বজনীন মূলভিত্তি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    }
]

with open(MASTER_SCRIPT_PATH, "w", encoding="utf-8") as f:
    json.dump(master_script, f, ensure_ascii=False, indent=2)

print(f"Master script generated with {len(master_script)} cues.")
