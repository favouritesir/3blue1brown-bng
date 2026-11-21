# -*- coding: utf-8 -*-
"""
Builder for Differential Equations Lesson 06:
Wave Equation and Vibrations (তরঙ্গ সমীকরণ ও কম্পন)
"""

import json
import os
from pathlib import Path

BASE_DIR = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses")

MASTER_SCRIPT_DIR = (
    BASE_DIR
    / "differential_equations"
    / "lesson_06_wave_equation"
    / "dubbing_pipeline"
)
MASTER_SCRIPT_FILE = MASTER_SCRIPT_DIR / "3b1b_diffeq_l06_bangla_master_script.json"

AUDIO_DIR = BASE_DIR / "web_platform" / "assets" / "audio" / "differential_equations" / "lesson_06"
MANIFEST_JSON_FILE = AUDIO_DIR / "manifest.json"
MANIFEST_JS_FILE = AUDIO_DIR / "manifest.js"

DATA_DIR = BASE_DIR / "web_platform" / "data" / "differential_equations"
DATA_JSON_FILE = DATA_DIR / "lesson_06.json"

MASTER_SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 1. AUTHENTIC BENGALI MASTER DUBBING SCRIPT
# ~45 cues, strictly following:
# - Phonetic acronym rules (AI -> এআই, 1D -> ওয়ানডি, 2D -> টুডি, etc.)
# - Math axis & symbols safeguards (x -> এক্স, t -> টি, u -> ইউ, c -> সি)
# - Authentic Bengali educator persona (Grant Sanderson)
# - Mathematical derivation of wave equation: d^2u/dt^2 = c^2 d^2u/dx^2,
#   standing waves, vibrating strings, d'Alembert's traveling wave solution f(x-ct) + g(x+ct)
# ==============================================================================

master_script_cues = [
    {
        "id": 1,
        "start": 0.0,
        "end": 7.5,
        "duration": 7.5,
        "en": "In our previous study of partial differential equations, we watched how heat relentlessly smooths out irregularities.",
        "bn": "আংশিক ডিফারেনশিয়াল সমীকরণের পূর্ববর্তী পাঠে আমরা দেখেছি কীভাবে তাপ সমীকরণ স্থানিক যেকোনো খাঁজ বা বক্রতাকে নির্দয়ভাবে মসৃণ করে দেয়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 2,
        "start": 8.0,
        "end": 16.5,
        "duration": 8.5,
        "en": "In the heat equation, the time derivative was first-order. Energy dissipated, high frequencies dissolved, and the universe slid towards irreversible equilibrium.",
        "bn": "তাপ সমীকরণে সময়ের অন্তরজটি ছিল প্রথম ক্রমের। ফলে শক্তি অপচয়িত হতো, উচ্চ কম্পাঙ্কগুলো দ্রুত মিলিয়ে যেত এবং ব্যবস্থাটি একমুখীভাবে সাম্যাবস্থায় পৌঁছাত।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 3,
        "start": 17.0,
        "end": 26.0,
        "duration": 9.0,
        "en": "Now, what happens if we change that single first time derivative into a second time derivative?",
        "bn": "কিন্তু এবার ভাবুন তো, সময়ের সেই প্রথম অন্তরজের জায়গায় যদি আমরা দ্বিতীয় অন্তরজ বা ত্বরণ বসিয়ে দিই, তবে কী ঘটবে?",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 4,
        "start": 26.5,
        "end": 35.5,
        "duration": 9.0,
        "en": "Everything changes. Dissipation disappears. Waves ripple across space without decaying, bouncing back and forth for eternity.",
        "bn": "মুহূর্তেই দৃশ্যপট বদলে যায়। শক্তির অপচয় উধাও হয়ে যায়। তরঙ্গ স্থান জুড়ে বিন্দুমাত্র ক্ষয় না পেয়ে অনন্তকালের জন্য দুলতে ও প্রতিধ্বনিত হতে থাকে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 5,
        "start": 36.0,
        "end": 44.8,
        "duration": 8.8,
        "en": "This is the domain of the wave equation, the foundational heartbeat of acoustics, optics, electromagnetism, and musical instruments.",
        "bn": "এটাই হলো তরঙ্গ সমীকরণ—শব্দবিজ্ঞান, আলোকবিজ্ঞান, তড়িৎচৌম্বকীয় তরঙ্গ এবং বাদ্যযন্ত্রের স্পন্দনের মূল প্রাণশক্তি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 6,
        "start": 45.3,
        "end": 54.5,
        "duration": 9.2,
        "en": "To see where this equation comes from, let us picture the simplest physical wave system imaginable: a stretched guitar string.",
        "bn": "এই সমীকরণ কোথা থেকে আসে তা গভীরভাবে উপলব্ধি করতে চলুন কল্পনা করি সবচেয়ে আদিম এক ব্যবস্থা—একটি টানটান বাঁধা গিটারের তার।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 7,
        "start": 55.0,
        "end": 64.0,
        "duration": 9.0,
        "en": "Let u of x comma t denote the vertical displacement of the string at horizontal position x at time t.",
        "bn": "ধরা যাক, অনুভূমিক অবস্থান এক্স এবং সময় টি-তে তারটির উল্লম্ব সরণকে প্রকাশ করা হচ্ছে ইউ অব এক্স কমা টি দিয়ে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 8,
        "start": 64.5,
        "end": 73.8,
        "duration": 9.3,
        "en": "Now isolate a microscopic segment of the string between x and x plus delta x, having linear mass density mu.",
        "bn": "এবার অবস্থান এক্স এবং এক্স প্লাস ডেল্টা এক্স-এর মধ্যবর্তী অতি ক্ষুদ্র একটি অংশ কেটে আলাদা করে ভাবুন, যার প্রতি একক দৈর্ঘ্যের ভর মিউ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 9,
        "start": 74.3,
        "end": 83.5,
        "duration": 9.2,
        "en": "Tension capital T pulls tangentially on both ends of this segment. If the string is curved, these two tension forces do not balance.",
        "bn": "তারের টান ক্যাপিটাল টি এই ক্ষুদ্র অংশের দুই প্রান্তে স্পর্শক বরাবর টানছে। যদি তারটি বাঁকা বা বক্র থাকে, তবে এই দুই প্রান্তের টান বল পরস্পরকে কাটাকাটি করে না।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 10,
        "start": 84.0,
        "end": 93.0,
        "duration": 9.0,
        "en": "The net vertical force is approximately capital T times the difference in slopes between the two ends.",
        "bn": "উল্লম্ব দিকে নিট প্রযুক্ত বল দাঁড়ায় টান ক্যাপিটাল টি গুণিতক দুই প্রান্তের ঢালের ব্যবধান বা পার্থক্যের সমান।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 11,
        "start": 93.5,
        "end": 102.8,
        "duration": 9.3,
        "en": "And the difference in slopes per unit length delta x is, by definition, the second spatial derivative: the local curvature!",
        "bn": "আর একক দৈর্ঘ্য ডেল্টা এক্স-এ ঢালের ব্যবধানই তো ক্যালকুলাসের সংজ্ঞানুযায়ী দূরত্বের দ্বিতীয় অন্তরজ—অর্থাৎ স্থানীয় বক্রতা!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 12,
        "start": 103.3,
        "end": 112.5,
        "duration": 9.2,
        "en": "By Newton's second law, net force equals mass times acceleration. Mass is mu delta x, and vertical acceleration is the second time derivative of u.",
        "bn": "নিউটনের দ্বিতীয় সূত্র অনুযায়ী, নিট বল সমান ভর গুণ ত্বরণ। ভর হলো মিউ গুণ ডেল্টা এক্স, আর উল্লম্ব ত্বরণ হলো সময়ের সাপেক্ষে দ্বিতীয় অন্তরজ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 13,
        "start": 113.0,
        "end": 122.5,
        "duration": 9.5,
        "en": "Equating force and mass times acceleration, delta x cancels cleanly on both sides, yielding the one-dimensional wave equation.",
        "bn": "বল ও ভর গুণ ত্বরণকে সমান বসালে উভয় পাশ থেকে ডেল্টা এক্স নিখুঁতভাবে কাটা যায়, আর আমরা পাই একমাত্রিক তরঙ্গ সমীকরণ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 14,
        "start": 123.0,
        "end": 133.0,
        "duration": 10.0,
        "en": "The second partial derivative of u with respect to t equals c squared times the second partial derivative of u with respect to x.",
        "bn": "সময়ের সাপেক্ষে দ্বিতীয় আংশিক অন্তরজ ডেল স্কয়ার ইউ বাই ডেল টি স্কয়ার সমান সি স্কয়ার গুণ দূরত্বের সাপেক্ষে দ্বিতীয় আংশিক অন্তরজ ডেল স্কয়ার ইউ বাই ডেল এক্স স্কয়ার।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 15,
        "start": 133.5,
        "end": 142.8,
        "duration": 9.3,
        "en": "Here, c is the wave propagation speed, given by the square root of tension capital T divided by linear mass density mu.",
        "bn": "এখানে সি হলো তরঙ্গের গতিবেগ, যার মান তারের টান ক্যাপিটাল টি ভাগ ভর ঘনত্ব মিউ-এর বর্গমূলের সমান।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 16,
        "start": 143.3,
        "end": 152.2,
        "duration": 8.9,
        "en": "Pause and look at the physical poetry: spatial curvature creates acceleration, which continuously updates velocity, which shifts displacement.",
        "bn": "এক মুহূর্তের জন্য এই ভৌত কাব্যের দিকে তাকান: স্থানিক বক্রতা তৈরি করে ত্বরণ, ত্বরণ সৃষ্টি করে বেগ, আর বেগ বদলে দেয় তরঙ্গের রূপ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 17,
        "start": 152.7,
        "end": 161.8,
        "duration": 9.1,
        "en": "Unlike heat, which immediately pulls a peak downward, inertia carries a moving wave right through equilibrium into the opposite direction.",
        "bn": "তাপের মতো এটি কোনো চূড়াকে সরাসরি শূন্যে বিলীন করে না; বরং জড়তার কারণে গতিশীল তার সাম্যাবস্থা ভেদ করে উল্টো দিকে ছুটে যায়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 18,
        "start": 162.3,
        "end": 171.5,
        "duration": 9.2,
        "en": "Now, how do we solve this partial differential equation? There are two historically magnificent perspectives: standing waves and traveling waves.",
        "bn": "এবার প্রশ্ন হলো, এই আংশিক সমীকরণ আমরা সমাধান করব কীভাবে? ইতিহাসে এর দুটি অমর দৃষ্টিভঙ্গি রয়েছে: স্থির তরঙ্গ এবং অগ্রগামী তরঙ্গ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 19,
        "start": 172.0,
        "end": 181.2,
        "duration": 9.2,
        "en": "Let us explore the standing wave approach first, using separation of variables for a guitar string pinned firmly at both ends, from zero to L.",
        "bn": "চলুন প্রথমে দেখি চলক পৃথকীকরণ পদ্ধতি, যেখানে দুই প্রান্তে দৃঢ়ভাবে আটকানো দৈর্ঘ্য এল-এর একটি তার বিবেচনা করা হয়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 20,
        "start": 181.7,
        "end": 190.8,
        "duration": 9.1,
        "en": "We guess a product solution: u of x comma t equals a purely spatial profile capital X of x multiplied by a pure time oscillation capital T of t.",
        "bn": "আমরা সমাধান কল্পনা করি দুটি স্বাধীন ফাংশনের গুণফল হিসেবে: ইউ অব এক্স কমা টি সমান স্থানিক অপেক্ষক ক্যাপিটাল এক্স গুণিতক কালিক অপেক্ষক ক্যাপিটাল টি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 21,
        "start": 191.3,
        "end": 200.5,
        "duration": 9.2,
        "en": "Plugging this into the wave equation and dividing by c squared X T, we cleanly separate the variables across the equals sign.",
        "bn": "তরঙ্গ সমীকরণে এটি বসিয়ে উভয় পাশে সি স্কয়ার গুণ এক্স টি দিয়ে ভাগ করলে সমীকরণের দুই পাশে চলক দুটি সম্পূর্ণ আলাদা হয়ে যায়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 22,
        "start": 201.0,
        "end": 210.2,
        "duration": 9.2,
        "en": "T double prime over c squared T equals X double prime over X. Since one side depends solely on t and the other solely on x, both must equal a constant, minus k squared.",
        "bn": "টি ডাবল প্রাইম বাই সি স্কয়ার টি সমান এক্স ডাবল প্রাইম বাই এক্স। যেহেতু একপাশ কেবল সময়ের ওপর এবং অন্যপাশ কেবল দূরত্বের ওপর নির্ভরশীল, উভয়কেই সমান হতে হবে একটি ধ্রুবক মাইনাস কে স্কয়ার-এর।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 23,
        "start": 210.7,
        "end": 219.8,
        "duration": 9.1,
        "en": "For the boundary conditions where displacement is zero at x equals zero and x equals L, spatial solutions are pure sines: sine of n pi x over L.",
        "bn": "উভয় প্রান্তে শূন্য সরণের শর্ত আরোপ করলে স্থানিক সমাধানগুলো দাঁড়ায় সাইন এন পাই এক্স বাই এল।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 24,
        "start": 220.3,
        "end": 229.5,
        "duration": 9.2,
        "en": "Meanwhile, the time equation is a classic harmonic oscillator: T double prime plus omega squared T equals zero, where omega equals c times n pi over L.",
        "bn": "আর সময় সমীকরণটি হয়ে ওঠে একটি ক্লাসিক্যাল সরল স্পন্দন সমীকরণ, যার কৌণিক কম্পাঙ্ক ওমেগা সমান সি গুণ এন পাই বাই এল।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 25,
        "start": 230.0,
        "end": 239.5,
        "duration": 9.5,
        "en": "Notice the crucial difference from the heat equation: here, time solutions are cosines and sines, pure un-damped oscillations, not exponential decays!",
        "bn": "তাপ সমীকরণের সাথে সবচেয়ে বড় পার্থক্যটি লক্ষ্য করুন: এখানে কালিক অংশটি সূচকীয় ক্ষয় নয়, বরং কোসাইন এবং সাইনের অবিরত ও অবমন্দহীন নিখুঁত দোলন!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 26,
        "start": 240.0,
        "end": 249.2,
        "duration": 9.2,
        "en": "These are the natural standing modes or harmonics of musical strings: the fundamental note for n equals one, the octave overtone for n equals two, and so on.",
        "bn": "এগুলোই হলো বাদ্যযন্ত্রের তারের প্রাকৃতিক আইগেনমোড বা সুরের হারমোনিক্স: এন সমান এক-এর জন্য মূল সুর বা ফান্ডামেন্টাল এবং উচ্চতর মানের জন্য অষ্টক উপরি সুর।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 27,
        "start": 249.7,
        "end": 259.0,
        "duration": 9.3,
        "en": "Now let us turn to the second perspective, perhaps the most elegant mathematical discovery in wave physics: d'Alembert's traveling wave solution.",
        "bn": "এবার চলুন দ্বিতীয় এবং সবচেয়ে চিত্তাকর্ষক জ্যামিতিক দৃষ্টিভঙ্গির দিকে তাকাই: জঁ লে রঁ দ্য'আলেমবার্টের অগ্রগামী তরঙ্গ সমাধান।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 28,
        "start": 259.5,
        "end": 268.8,
        "duration": 9.3,
        "en": "In 1747, French mathematician Jean le Rond d'Alembert noticed that the wave operator factors like the difference of two squares.",
        "bn": "১৭৪৭ সালে ফরাসি গণিতবিদ দ্য'আলেমবার্ট লক্ষ্য করেন যে তরঙ্গ সমীকরণের ডিফারেনশিয়াল অপারেটরকে দুটি বর্গের বিয়োগফলের মতো উৎপাদকে বিশ্লেষণ করা যায়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 29,
        "start": 269.3,
        "end": 278.5,
        "duration": 9.2,
        "en": "The second derivative with respect to t minus c squared times the second derivative with respect to x factors into two directional transport operators.",
        "bn": "সময়ের দ্বিতীয় অন্তরজ মাইনাস সি স্কয়ার গুণ দূরত্বের দ্বিতীয় অন্তরজকে দুটি অভিমুখী ট্রান্সপোর্ট অপারেটরে ভেঙে ফেলা যায়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 30,
        "start": 279.0,
        "end": 288.2,
        "duration": 9.2,
        "en": "Partial with respect to t minus c partial with respect to x, acting on partial with respect to t plus c partial with respect to x, of u equals zero.",
        "bn": "ডেল বাই ডেল টি মাইনাস সি ডেল বাই ডেল এক্স গুণিতক ডেল বাই ডেল টি প্লাস সি ডেল বাই ডেল এক্স অব ইউ সমান শূন্য।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 31,
        "start": 288.7,
        "end": 298.0,
        "duration": 9.3,
        "en": "By introducing characteristic coordinates, xi equals x minus c t, and eta equals x plus c t, the entire wave equation collapses to: the mixed partial derivative of u with respect to xi and eta equals zero!",
        "bn": "বৈশিষ্ট্যমূলক স্থানাঙ্ক জাই সমান এক্স মাইনাস সি টি এবং এটা সমান এক্স প্লাস সি টি সংজ্ঞায়িত করলে পুরো তরঙ্গ সমীকরণটি দাঁড়ায়: ডেল স্কয়ার ইউ বাই ডেল জাই ডেল এটা সমান শূন্য!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 32,
        "start": 298.5,
        "end": 307.8,
        "duration": 9.3,
        "en": "Integrating once with respect to xi gives a function of eta; integrating again gives a function of xi plus a function of eta.",
        "bn": "উভয় পাশে ক্রমান্বয়ে দুইবার সমাকলন করলে আমরা পাই পরম সুন্দর এক সার্বিক রূপ: ইউ অব এক্স কমা টি সমান এফ অব এক্স মাইনাস সি টি যোগ জি অব এক্স প্লাস সি টি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 33,
        "start": 308.3,
        "end": 317.5,
        "duration": 9.2,
        "en": "This is d'Alembert's formula: every solution to the wave equation is simply the superposition of two traveling shapes!",
        "bn": "এটাই দ্য'আলেমবার্টের অমর সূত্র: তরঙ্গ সমীকরণের প্রতিটি সমাধান কেবল দুটি বিপরীতমুখী চলন্ত তরঙ্গের সাধারণ উপরিপাত!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 34,
        "start": 318.0,
        "end": 327.2,
        "duration": 9.2,
        "en": "f of x minus c t is an arbitrary shape moving rigidly to the right with constant speed c, without changing its form by even a single pixel.",
        "bn": "এফ অব এক্স মাইনাস সি টি হলো যেকোনো আকৃতির একটি তরঙ্গ যা তার রূপ বিন্দুমাত্র না বদলে ধ্রুব বেগ সি নিয়ে ডান দিকে ছুটে চলে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 35,
        "start": 327.7,
        "end": 337.0,
        "duration": 9.3,
        "en": "And g of x plus c t is an arbitrary shape moving rigidly to the left with constant speed c.",
        "bn": "আর জি অব এক্স প্লাস সি টি হলো একই বেগে অপরিবর্তিত অবয়বে বাম দিকে ধাবমান আরেকটি স্বাধীন তরঙ্গ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 36,
        "start": 337.5,
        "end": 346.8,
        "duration": 9.3,
        "en": "If you pluck a string at rest with an initial triangular displacement f of x, what happens?",
        "bn": "যদি আপনি একটি টানটান তারের মাঝখানে টেনে ছেড়ে দেন, তবে ঠিক কী ঘটবে?",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 37,
        "start": 347.3,
        "end": 356.5,
        "duration": 9.2,
        "en": "The initial peak splits into two half-amplitude replicas: one travels to the right, and the other travels to the left.",
        "bn": "আদি ত্রিভুজাকার খাঁজটি সমান অর্ধেক উচ্চতার দুটি তরঙ্গে বিভক্ত হয়ে যায়: একটি ছুটে যায় ডানে এবং অপরটি ছুটে যায় বামে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 38,
        "start": 357.0,
        "end": 366.2,
        "duration": 9.2,
        "en": "When they strike a pinned boundary, they reflect upside-down with phase inversion, returning to pass straight through each other without distortion.",
        "bn": "প্রান্তের দৃঢ় সীমান্তে আঘাত হেনে তারা উল্টো দশায় প্রতিফলিত হয় এবং কোনো বিকৃতি ছাড়াই একে অপরকে অতিক্রম করে চলে যায়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 39,
        "start": 366.7,
        "end": 376.0,
        "duration": 9.3,
        "en": "This brings us to the profound concept of wave energy and conservation.",
        "bn": "এখান থেকেই উন্মোচিত হয় তরঙ্গ সমীকরণের আরেকটি মহিমান্বিত রূপ: শক্তির নিত্যতা ও সংরক্ষণ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 40,
        "start": 376.5,
        "end": 385.8,
        "duration": 9.3,
        "en": "The total energy of the vibrating string consists of two parts: kinetic energy from vertical motion, and potential energy from string stretching.",
        "bn": "কম্পনশীল তারের মোট শক্তি দুটি উপাদানে গঠিত: উল্লম্ব গতির গতিশক্তি এবং তারের প্রসারণজনিত স্থিতিশক্তি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 41,
        "start": 386.3,
        "end": 395.5,
        "duration": 9.2,
        "en": "Kinetic energy density is one half mu times partial u partial t squared. Potential energy density is one half tension T times partial u partial x squared.",
        "bn": "গতিশক্তি হলো হাফ মিউ গুণ ডেল ইউ বাই ডেল টি স্কয়ার, আর স্থিতিশক্তি হলো হাফ টান টি গুণ ডেল ইউ বাই ডেল এক্স স্কয়ার।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 42,
        "start": 396.0,
        "end": 405.5,
        "duration": 9.5,
        "en": "If you differentiate the total energy integral with respect to time and substitute the wave equation, you find that dE dt is strictly zero!",
        "bn": "সমগ্র তারের ওপর এই শক্তির যোগফলকে সময়ের সাপেক্ষে অন্তরীকরণ করে তরঙ্গ সমীকরণ বসালে দেখা যায় ডিই বাই ডিটি নিখুঁতভাবে শূন্য!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 43,
        "start": 406.0,
        "end": 415.2,
        "duration": 9.2,
        "en": "Energy is perfectly conserved. It flows back and forth between kinetic motion and elastic tension, never dissipating into heat.",
        "bn": "শক্তি অবিকল সংরক্ষিত থাকে। এটি নিরবচ্ছিন্নভাবে গতিশক্তি ও স্থিতিশক্তির মাঝে রূপ বদলায়, কিন্তু কখনোই ক্ষয়প্রাপ্ত হয়ে উত্তাপে বিলীন হয় না।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 44,
        "start": 415.7,
        "end": 425.5,
        "duration": 9.8,
        "en": "The heat equation was the physics of diffusion, smoothing, and memory loss. The wave equation is the physics of propagation, coherence, and memory preservation.",
        "bn": "তাপ সমীকরণ ছিল ব্যাপন, মসৃণকরণ এবং অতীতের তথ্য মুছে ফেলার সমীকরণ। আর তরঙ্গ সমীকরণ হলো তথ্য সংরক্ষণ, সংগতি এবং দূর-দূরান্তে বার্তা প্রেরণের এক চিরন্তন ছন্দ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 45,
        "start": 426.0,
        "end": 436.0,
        "duration": 10.0,
        "en": "From the sound waves reaching your ears to the light from distant galaxies traversing billions of light-years, the universe speaks through the wave equation.",
        "bn": "আমাদের কানে পৌঁছানো সুরের মূর্ছনা থেকে শুরু করে কোটি আলোকবর্ষ দূর থেকে আসা নক্ষত্রের আলো—সমগ্র মহাবিশ্ব কথা বলে এই একটিমাত্র অপূর্ব সমীকরণের সুরে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    }
]

print(f"Total master script cues: {len(master_script_cues)}")

with open(MASTER_SCRIPT_FILE, "w", encoding="utf-8") as f:
    json.dump(master_script_cues, f, ensure_ascii=False, indent=2)

print("Saved master script JSON.")

# ==============================================================================
# 2. AUDIO CUES MANIFEST & SECTION CUES GENERATION
# 5 Sections:
# 1. sec-wave-intro: সূচনা ও তাপ সমীকরণ বনাম তরঙ্গ সমীকরণ
# 2. sec-wave-derivation: টানটান তারের নিউটনীয় ব্যবকলন ও তরঙ্গ বেগ c = sqrt(T/mu)
# 3. sec-standing-waves: স্থির তরঙ্গ, চলক পৃথকীকরণ ও সুরের হারমোনিক্স
# 4. sec-dalembert: দ্য'আলেমবার্টের পদ্ধতি ও বিপরীতমুখী চলন্ত তরঙ্গ f(x-ct) + g(x+ct)
# 5. sec-energy-harmonics: শক্তির নিত্যতা, তথ্য সংরক্ষণ ও মহাজাগতিক বিস্তার
# ==============================================================================

section_specs = [
    {
        "section_id": "sec-wave-intro",
        "alias": "sec_01_wave_intro",
        "title": "তরঙ্গ সমীকরণের সূচনা: তাপের মসৃণকরণ বনাম অবিরাম স্পন্দন",
        "audio_file": "sec_01_wave_intro.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "text": "প্রথম পরিচ্ছেদ: তরঙ্গ সমীকরণের সূচনা—তাপের মসৃণকরণ বনাম অবিরাম স্পন্দন।",
                "duration_ms": 6200.0
            },
            {
                "index": 1,
                "type": "chapter-quote",
                "text": "জঁ লে রঁ দ্য'আলেমবার্ট বলেছিলেন: প্রকৃতি কম্পনের মাঝে কোনো জটিল ধাঁধা লুকায়নি; সে কেবল স্থান ও সময়কে তরঙ্গের ছন্দে বেঁধে দিয়েছে।",
                "duration_ms": 9400.0
            },
            {
                "index": 2,
                "type": "p",
                "text": "শিক্ষার্থী বন্ধুরা, গত অধ্যায়ে আমরা আংশিক ডিফারেনশিয়াল সমীকরণের জগতে পা রেখে তাপ সমীকরণ প্রত্যক্ষ করেছি। সেখানে সময়ের অন্তরজটি ছিল প্রথম ক্রমের।",
                "duration_ms": 13800.0
            },
            {
                "index": 3,
                "type": "p",
                "text": "প্রথম ডেরিভেটিভ থাকার কারণে যে কোনো ধারালো খাঁজ বা তাপমাত্রা একমুখীভাবে মসৃণ হয়ে শূন্যে মিলিয়ে যেত—তথ্য মুছে যেত এবং এনট্রপি বৃদ্ধি পেত।",
                "duration_ms": 13500.0
            },
            {
                "index": 4,
                "type": "figure",
                "text": "গ্রাফিক্সে তুলনা দেখুন: বামে তাপ সমীকরণের ক্ষয়িষ্ণু মসৃণতা, আর ডানে তরঙ্গ সমীকরণের অক্ষত বিস্তারে অবিরাম দোলায়মান তরঙ্গের ছন্দ।",
                "duration_ms": 10500.0
            },
            {
                "index": 5,
                "type": "p",
                "text": "কিন্তু সময়ের সেই প্রথম অন্তরজের জায়গায় যদি আমরা দ্বিতীয় অন্তরজ বা ত্বরণ বসিয়ে দিই? মুহূর্তেই দৃশ্যপট বদলে যায়। ব্যবস্থার ক্ষয়িষ্ণুতা বিলুপ্ত হয় এবং তরঙ্গ বিন্দুমাত্র রূপ না হারিয়ে স্থান জুড়ে অনন্তকাল ছুটে চলে।",
                "duration_ms": 18200.0
            },
            {
                "index": 6,
                "type": "formula-box",
                "text": "একমাত্রিক তরঙ্গ সমীকরণ: ডেল স্কয়ার ইউ বাই ডেল টি স্কয়ার সমান সি স্কয়ার গুণ ডেল স্কয়ার ইউ বাই ডেল এক্স স্কয়ার।",
                "duration_ms": 9800.0
            },
            {
                "index": 7,
                "type": "callout",
                "text": "পদার্থবিজ্ঞানের রূপান্তর: তাপ সমীকরণ হলো ব্যাপন ও বিস্মৃতির সমীকরণ। আর তরঙ্গ সমীকরণ হলো ত্বরণ, জড়তা ও স্মৃতি সংরক্ষণের এক চিরন্তন বিশ্বস্ত সংকেতবাহক।",
                "duration_ms": 16400.0
            }
        ]
    },
    {
        "section_id": "sec-wave-derivation",
        "alias": "sec_02_wave_derivation",
        "title": "টানটান তারের ব্যবকলন ও তরঙ্গ বেগ c = √(T/μ)",
        "audio_file": "sec_02_wave_derivation.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "text": "দ্বিতীয় পরিচ্ছেদ: টানটান তারের ব্যবকলন ও তরঙ্গ বেগ সি সমান রুট ওভার টি বাই মিউ।",
                "duration_ms": 6800.0
            },
            {
                "index": 1,
                "type": "p",
                "text": "এই মহিমান্বিত সমীকরণটি কোথা থেকে জন্ম নেয়? চলুন সবচেয়ে সহজ একটি ভৌত ব্যবস্থা বিবেচনা করি: দুই প্রান্তে বাঁধা টানটান একটি গিটারের তার।",
                "duration_ms": 12400.0
            },
            {
                "index": 2,
                "type": "p",
                "text": "তারটির অবস্থান এক্স এবং সময় টি-তে উল্লম্ব সরণ ইউ অব এক্স কমা টি। এবার এক্স থেকে এক্স প্লাস ডেল্টা এক্স দৈর্ঘ্যের অতি ক্ষুদ্র একটি অংশ কেটে আলাদা করে ভাবুন।",
                "duration_ms": 14200.0
            },
            {
                "index": 3,
                "type": "figure",
                "text": "ডায়াগ্রামে লক্ষ্য করুন: ক্ষুদ্র তারের অংশের দুই প্রান্তে স্পর্শক টান বল টি এবং উল্লম্ব উপাংশের অসমতা।",
                "duration_ms": 8600.0
            },
            {
                "index": 4,
                "type": "p",
                "text": "তারটি যদি বাঁকা বা বক্র থাকে, তবে দুই প্রান্তের স্পর্শক টান হুবহু একই সরলরেখায় থাকে না। তাদের ঢালের ব্যবধানের কারণে একটি ঊর্ধ্বমুখী বা নিম্নমুখী নিট উল্লম্ব বল সৃষ্টি হয়।",
                "duration_ms": 15800.0
            },
            {
                "index": 5,
                "type": "formula-box",
                "text": "নিট উল্লম্ব বল: এফ সমান ক্যাপিটাল টি গুণ ডেল স্কয়ার ইউ বাই ডেল এক্স স্কয়ার গুণ ডেল্টা এক্স।",
                "duration_ms": 9200.0
            },
            {
                "index": 6,
                "type": "p",
                "text": "নিউটনের দ্বিতীয় সূত্র বলে বল সমান ভর গুণ ত্বরণ। ভর মিউ ডেল্টা এক্স এবং ত্বরণ ডেল স্কয়ার ইউ বাই ডেল টি স্কয়ার বসিয়ে দিলে উভয় পাশ থেকে ডেল্টা এক্স কাটাকাটি হয়ে অবিকল তরঙ্গ সমীকরণটি বেরিয়ে আসে!",
                "duration_ms": 17800.0
            },
            {
                "index": 7,
                "type": "callout",
                "text": "তরঙ্গ গতিবেগের রহস্য: সি সমান রুট ওভার টি বাই মিউ। তারের টান যত বেশি হবে তরঙ্গ তত দ্রুত ছুটবে; আর তার যত ভারী ও মোটা হবে তরঙ্গ তত ধীরগতিতে সঞ্চালিত হবে।",
                "duration_ms": 15400.0
            }
        ]
    },
    {
        "section_id": "sec-standing-waves",
        "alias": "sec_03_standing_waves",
        "title": "স্থির তরঙ্গ, চলক পৃথকীকরণ ও সুরের হারমোনিক্স",
        "audio_file": "sec_03_standing_waves.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "text": "তৃতীয় পরিচ্ছেদ: স্থির তরঙ্গ, চলক পৃথকীকরণ ও সুরের হারমোনিক্স।",
                "duration_ms": 5900.0
            },
            {
                "index": 1,
                "type": "p",
                "text": "তরঙ্গ সমীকরণ সমাধানের প্রথম ধ্রুপদী পথ হলো চলক পৃথকীকরণ পদ্ধতি বা সেপারেশন অব ভেরিয়েবলস।",
                "duration_ms": 9800.0
            },
            {
                "index": 2,
                "type": "p",
                "text": "আমরা ধরে নিই সমাধানটি স্থান ও সময়ের দুটি পৃথক অপেক্ষকের গুণফল: ইউ অব এক্স কমা টি সমান ক্যাপিটাল এক্স অব এক্স গুণিতক ক্যাপিটাল টি অব টি।",
                "duration_ms": 13400.0
            },
            {
                "index": 3,
                "type": "formula-box",
                "text": "চলক পৃথকীকরণ রূপ: এক বাই সি স্কয়ার গুণ টি ডাবল প্রাইম বাই টি সমান এক্স ডাবল প্রাইম বাই এক্স সমান মাইনাস কে স্কয়ার।",
                "duration_ms": 11200.0
            },
            {
                "index": 4,
                "type": "p",
                "text": "দুই প্রান্তে আটকানো সীমান্ত শর্ত থেকে স্থানিক সমাধানগুলো পাওয়া যায় বিশুদ্ধ সাইন তরঙ্গ হিসেবে। আর সময় সমীকরণটি হয়ে ওঠে একটি অবমন্দহীন সাধারণ সরল ছন্দিত স্পন্দন!",
                "duration_ms": 16200.0
            },
            {
                "index": 5,
                "type": "figure",
                "text": "অ্যানিমেশনে লক্ষ্য করুন: তারের স্থির তরঙ্গ—এন সমান ১ মূল সুর, এন সমান ২ দ্বিতীয় হারমোনিক বা একটি নিস্পন্দ বিন্দু, এবং উচ্চতর কম্পন মোড।",
                "duration_ms": 11500.0
            },
            {
                "index": 6,
                "type": "callout",
                "text": "সঙ্গীতের গাণিতিক ভিত্তি: গিটার বা বেহালার তারে এই আইগেনমোডগুলোই হলো মূল সুর ও উপরি সুর। তাদের সুষম উপরিপাতই বাদ্যযন্ত্রের সমৃদ্ধ সুর ও টিম্বার তৈরি করে।",
                "duration_ms": 15200.0
            }
        ]
    },
    {
        "section_id": "sec-dalembert",
        "alias": "sec_04_dalembert",
        "title": "দ্য'আলেমবার্টের পদ্ধতি ও বিপরীতমুখী চলন্ত তরঙ্গ f(x-ct) + g(x+ct)",
        "audio_file": "sec_04_dalembert.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "text": "চতুর্থ পরিচ্ছেদ: দ্য'আলেমবার্টের পদ্ধতি ও বিপরীতমুখী চলন্ত তরঙ্গ।",
                "duration_ms": 6100.0
            },
            {
                "index": 1,
                "type": "p",
                "text": "স্থির তরঙ্গ বাদ্যযন্ত্রের বদ্ধ তারের জন্য চমৎকার। কিন্তু মুক্ত মাধ্যমে ছড়িয়ে পড়া তরঙ্গের ক্ষেত্রে কী ঘটে? ১৭৪৭ সালে জঁ লে রঁ দ্য'আলেমবার্ট আবিষ্কার করেন এক জাদুকরী সত্য।",
                "duration_ms": 16500.0
            },
            {
                "index": 2,
                "type": "formula-box",
                "text": "দ্য'আলেমবার্টের সাধারণ সমাধান: ইউ অব এক্স কমা টি সমান এফ অব এক্স মাইনাস সি টি যোগ জি অব এক্স প্লাস সি টি।",
                "duration_ms": 10800.0
            },
            {
                "index": 3,
                "type": "p",
                "text": "সমীকরণের অপারেটরটিকে দুটি প্রথম ক্রমের বিপরীতমুখী ট্রান্সপোর্ট অপারেটরে উৎপাদকে বিশ্লেষণ করা যায়। জাই সমান এক্স মাইনাস সি টি এবং এটা সমান এক্স প্লাস সি টি বসালে সমীকরণটি হয়ে যায় ডেল স্কয়ার ইউ বাই ডেল জাই ডেল এটা সমান শূন্য!",
                "duration_ms": 19500.0
            },
            {
                "index": 4,
                "type": "figure",
                "text": "চলমান সিমুলেশনে দেখুন: একটি একক প্রাথমিক পালস বা ত্রিভুজাকার খাঁজ কীভাবে দুটি সমান অর্ধ-উচ্চতার তরঙ্গে বিভক্ত হয়ে ডানে ও বামে ছুটে যায়।",
                "duration_ms": 11800.0
            },
            {
                "index": 5,
                "type": "callout",
                "text": "অনড় স্থানান্তর নীতি: এফ অব এক্স মাইনাস সি টি মানে হলো আকৃতি বিন্দুমাত্র না বদলে অবিকল গতিবেগ সি নিয়ে ডান দিকে সরে যাওয়া। কোনো ক্ষয় নেই, কোনো বিকৃতি নেই!",
                "duration_ms": 15900.0
            }
        ]
    },
    {
        "section_id": "sec-energy-harmonics",
        "alias": "sec_05_energy_harmonics",
        "title": "শক্তির নিত্যতা, তথ্য সংরক্ষণ ও মহাজাগতিক বিস্তার",
        "audio_file": "sec_05_energy_harmonics.mp3",
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "text": "পঞ্চম পরিচ্ছেদ: শক্তির নিত্যতা, তথ্য সংরক্ষণ ও মহাজাগতিক বিস্তার।",
                "duration_ms": 6200.0
            },
            {
                "index": 1,
                "type": "p",
                "text": "তরঙ্গ সমীকরণের সবচেয়ে মনোমুগ্ধকর বৈশিষ্ট্য হলো শক্তির কঠোর নিত্যতা। কম্পনশীল তারের মোট শক্তি দুটি উপাদানে বিভক্ত: উল্লম্ব গতির গতিশক্তি এবং টানজনিত স্থিতিশক্তি।",
                "duration_ms": 16400.0
            },
            {
                "index": 2,
                "type": "formula-box",
                "text": "শক্তির নিত্যতা সমীকরণ: সময়ের সাপেক্ষে মোট শক্তি ই-এর পরিবর্তন ডিই বাই ডিটি সমান অবিকল শূন্য।",
                "duration_ms": 9400.0
            },
            {
                "index": 3,
                "type": "p",
                "text": "গতিশক্তি ও স্থিতিশক্তি অনবরত একে অপরে রূপান্তরিত হয়, ঠিক যেমন একটি পেন্ডুলাম বা সরল ছন্দিত স্পন্দকে ঘটে। কোনো শক্তি উত্তাপে হারিয়ে যায় না।",
                "duration_ms": 14200.0
            },
            {
                "index": 4,
                "type": "figure",
                "text": "গ্রাফে লক্ষ্য করুন: গতিশক্তি ও স্থিতিশক্তির ফেজ বিনিময়—যখন তার সম্পূর্ণ সোজা তখন সমস্ত শক্তি গতিশক্তিতে এবং যখন সর্বোচ্চ স্থানচ্যুত তখন সমস্ত শক্তি স্থিতিশক্তিতে জমা হয়।",
                "duration_ms": 12800.0
            },
            {
                "index": 5,
                "type": "callout",
                "text": "তথ্য সংরক্ষণের বার্তা: তাপ সমীকরণ তথ্য মুছে ফেলে, কিন্তু তরঙ্গ সমীকরণ তথ্যকে কোটি কোটি আলোকবর্ষ দূরে মহাকাশের বুক চিরে অবিকল পৌঁছে দেয়। আলোক তরঙ্গ ও মহাকর্ষীয় তরঙ্গের অস্তিত্ব এই সমীকরণেরই অমর দান।",
                "duration_ms": 18500.0
            }
        ]
    }
]

# Compute cue timestamps
audio_sections_dict = {}
for sec in section_specs:
    current_time_ms = 0.0
    sec_cues = []
    for c in sec["cues"]:
        start_ms = round(current_time_ms, 1)
        dur_ms = round(c["duration_ms"], 1)
        end_ms = round(start_ms + dur_ms, 1)
        sec_cues.append({
            "index": c["index"],
            "type": c["type"],
            "text": c["text"],
            "start_ms": start_ms,
            "end_ms": end_ms,
            "duration_ms": dur_ms
        })
        current_time_ms = end_ms + 350.0  # natural phrase breath pause
    
    total_dur_ms = round(sec_cues[-1]["end_ms"] if sec_cues else 0.0, 1)
    
    sec_data = {
        "section_id": sec["section_id"],
        "alias": sec["alias"],
        "title": sec["title"],
        "audio_file": sec["audio_file"],
        "total_duration_ms": total_dur_ms,
        "cues": sec_cues
    }
    
    # Save section cue json file
    sec_cue_file = AUDIO_DIR / f"{sec['alias']}_cues.json"
    with open(sec_cue_file, "w", encoding="utf-8") as f:
        json.dump(sec_data, f, ensure_ascii=False, indent=2)
    
    audio_sections_dict[sec["section_id"]] = sec_data

manifest_data = {
    "course": "differential_equations",
    "lesson": "lesson_06",
    "title": "অধ্যায় ০৬ — তরঙ্গ সমীকরণ ও কম্পন",
    "voice": "bn-BD-PradeepNeural",
    "mode": "authentic_teacher",
    "sections": audio_sections_dict
}

with open(MANIFEST_JSON_FILE, "w", encoding="utf-8") as f:
    json.dump(manifest_data, f, ensure_ascii=False, indent=2)

with open(MANIFEST_JS_FILE, "w", encoding="utf-8") as f:
    f.write("window.TEACHER_AUDIO_MANIFEST = " + json.dumps(manifest_data, ensure_ascii=False, indent=2) + ";\n")

print("Saved audio cues manifest JSON and JS.")

# ==============================================================================
# 3. SINGLE-SHELL LESSON DATA JSON (with full KaTeX, Quizzes & Interactive Lab)
# ==============================================================================

lesson_06_data = {
    "meta": {
        "course_id": "differential_equations",
        "course_title_en": "Essence of Differential Equations",
        "course_title_bn": "ডিফারেনশিয়াল সমীকরণের মূলভাব",
        "lesson_id": "lesson_06",
        "lesson_number": 6,
        "lesson_number_bn": "০৬",
        "title_en": "The Wave Equation and Vibrations",
        "title_bn": "অধ্যায় ০৬: তরঙ্গ সমীকরণ ও কম্পন — স্থান ও কালের অবিরাম স্পন্দন",
        "subtitle_bn": "সময়ের দ্বিতীয় অন্তরজ কীভাবে ক্ষয়হীন তরঙ্গের জন্ম দেয়, টানটান তারের নিউটনীয় ব্যবকলন, স্থির তরঙ্গের সুরের হারমোনিক্স এবং দ্য'আলেমবার্টের বিপরীতমুখী তরঙ্গের অমর সমাধান $f(x - ct) + g(x + ct)$",
        "duration": "১৮:৪০",
        "youtube_id": "ToIXSwZ1pJU",
        "theme_color": "#06b6d4",
        "theme_color_rgb": "6, 182, 212",
        "audio_manifest": "../../assets/audio/differential_equations/lesson_06/manifest.json",
        "audio_manifest_js": "../../assets/audio/differential_equations/lesson_06/manifest.js",
        "prev_lesson": {
            "id": "lesson_05",
            "number_bn": "০৫",
            "title_bn": "ফেজ পোর্ট্রেট এবং রৈখিক ওডিই সিস্টেম (Phase Portraits & Linear Systems)",
            "href": "lesson_05.html"
        },
        "next_lesson": {
            "id": "lesson_07",
            "number_bn": "০৭",
            "title_bn": "ল্যাপ্লাস রূপান্তর: রূপান্তরের বীজগণিত (The Laplace Transform)",
            "href": "lesson_07.html"
        }
    },
    "hero": {
        "badge_bn": "ডিফারেনশিয়াল সমীকরণ • ষষ্ঠ অধ্যায়",
        "headline_bn": "তরঙ্গ সমীকরণ ও কম্পন: স্থান ও কালের মহাজাগতিক নৃত্য",
        "subheadline_bn": "তাপ সমীকরণ সবকিছুকে মসৃণ ও বিলীন করে দিত। কিন্তু যখন সময়ের প্রথম ডেরিভেটিভের বদলে ত্বরণ বা দ্বিতীয় ডেরিভেটিভ আসে, তখন কেন ক্ষয়হীন অনন্ত তরঙ্গের জন্ম হয়? কীভাবে একটি টানটান তারের ক্ষুদ্র নিউটনীয় বল থেকে জন্ম নেয় সঙ্গীত ও আলোর সার্বজনীন সমীকরণ?",
        "key_takeaway_bn": "একমাত্রিক তরঙ্গ সমীকরণ $\\frac{\\partial^2 u}{\\partial t^2} = c^2 \\frac{\\partial^2 u}{\\partial x^2}$ নির্দেশ করে যে স্থানিক বক্রতা ত্বরণ তৈরি করে। এর দুটি অমর সমাধান রয়েছে: চলক পৃথকীকরণে প্রাপ্ত সুরের স্থায়ী তরঙ্গ $\\sin(kx)\\cos(\\omega t)$, এবং দ্য'আলেমবার্টের সার্বিক অগ্রগামী তরঙ্গ সমাধান $u(x, t) = f(x - ct) + g(x + ct)$, যা শক্তি ও স্মৃতিকে চিরকাল অবিকল সংরক্ষণ করে।"
    },
    "bookmarks": [
        {
            "time": "০০:০০",
            "seconds": 0,
            "title_bn": "তরঙ্গ সমীকরণের সূচনা: তাপের মসৃণকরণ বনাম অবিরাম স্পন্দন"
        },
        {
            "time": "০৩:৪০",
            "seconds": 220,
            "title_bn": "টানটান তারের ব্যবকলন ও তরঙ্গ বেগ c = √(T/μ)"
        },
        {
            "time": "০৭:৩০",
            "seconds": 450,
            "title_bn": "স্থির তরঙ্গ, চলক পৃথকীকরণ ও সুরের হারমোনিক্স"
        },
        {
            "time": "১১:১৫",
            "seconds": 675,
            "title_bn": "দ্য'আলেমবার্টের পদ্ধতি ও বিপরীতমুখী চলন্ত তরঙ্গ f(x-ct) + g(x+ct)"
        },
        {
            "time": "১৫:২০",
            "seconds": 920,
            "title_bn": "শক্তির নিত্যতা, তথ্য সংরক্ষণ ও মহাজাগতিক বিস্তার"
        }
    ],
    "toc": [
        {
            "id": "sec-wave-intro",
            "title_bn": "১. তরঙ্গ সমীকরণের সূচনা: তাপের মসৃণকরণ বনাম অবিরাম স্পন্দন"
        },
        {
            "id": "sec-wave-derivation",
            "title_bn": "২. টানটান তারের ব্যবকলন ও তরঙ্গ বেগ c = √(T/μ)"
        },
        {
            "id": "sec-standing-waves",
            "title_bn": "৩. স্থির তরঙ্গ, চলক পৃথকীকরণ ও সুরের হারমোনিক্স"
        },
        {
            "id": "sec-dalembert",
            "title_bn": "৪. দ্য'আলেমবার্টের পদ্ধতি ও বিপরীতমুখী চলন্ত তরঙ্গ f(x-ct) + g(x+ct)"
        },
        {
            "id": "sec-energy-harmonics",
            "title_bn": "৫. শক্তির নিত্যতা, তথ্য সংরক্ষণ ও মহাজাগতিক বিস্তার"
        },
        {
            "id": "sec-interactive-lab",
            "title_bn": "৬. ইন্টারেক্টিভ তারের কম্পন ও দ্য'আলেমবার্ট ল্যাব"
        },
        {
            "id": "sec-quizzes",
            "title_bn": "৭. ধারণা যাচাই ও বহুনির্বাচনী কুইজ"
        }
    ],
    "sections": [
        {
            "id": "sec-wave-intro",
            "alias": "sec_01_wave_intro",
            "number_bn": "১",
            "title_bn": "তরঙ্গ সমীকরণের সূচনা: তাপের মসৃণকরণ বনাম অবিরাম স্পন্দন (Introduction: Diffusion vs. Oscillation)",
            "quote": {
                "text_bn": "প্রকৃতি কম্পনের মাঝে কোনো জটিল ধাঁধা লুকায়নি; সে কেবল স্থান ও সময়কে তরঙ্গের ছন্দে বেঁধে দিয়েছে।",
                "author_bn": "জঁ লে রঁ দ্য'আলেমবার্ট"
            },
            "paragraphs": [
                "আগের অধ্যায়ে আমরা আংশিক ডিফারেনশিয়াল সমীকরণের জগতে পা রেখে তাপ সমীকরণ প্রত্যক্ষ করেছিলাম: $\\frac{\\partial T}{\\partial t} = \\alpha \\frac{\\partial^2 T}{\\partial x^2}$। সেখানে লক্ষ্য করেছিলেন সময়ের অন্তরজটি ছিল প্রথম ক্রমের (First-order in time)।",
                "প্রথম ডেরিভেটিভ থাকার কারণে যে কোনো ধারালো খাঁজ বা তাপমাত্রা একমুখীভাবে মসৃণ হয়ে শূন্যে মিলিয়ে যেত। উচ্চ ফ্রিকোয়েন্সিগুলো ধ্বংস হয়ে যেত, তথ্য হারিয়ে যেত এবং ব্যবস্থাটি অপরিবর্তনীয়ভাবে তাপীয় সাম্যাবস্থায় পৌঁছাত।",
                "কিন্তু এবার এক মহাবিস্ময়কর প্রশ্ন ভাবুন: সময়ের সেই প্রথম অন্তরজের জায়গায় যদি আমরা দ্বিতীয় অন্তরজ—অর্থাৎ ত্বরণ বসিয়ে দিই? $\\frac{\\partial^2 u}{\\partial t^2} = c^2 \\frac{\\partial^2 u}{\\partial x^2}$। মাত্র একটি ডেরিভেটিভের ক্রম বৃদ্ধির সাথে সাথে পুরো বিশ্বব্রহ্মাণ্ডের গতিবিধি বদলে যায়! শক্তির অপচয় বিলুপ্ত হয়, তরঙ্গের রূপ অক্ষত থাকে এবং স্থান জুড়ে সংকেত অবিকল অনন্তকালের জন্য প্রতিধ্বনিত হতে থাকে।"
            ],
            "formulas": [
                {
                    "latex": "\\frac{\\partial^2 u}{\\partial t^2} = c^2 \\frac{\\partial^2 u}{\\partial x^2}",
                    "caption_bn": "একমাত্রিক তরঙ্গ সমীকরণ (1D Wave Equation)।"
                }
            ],
            "callout": {
                "title_bn": "তাপ সমীকরণ বনাম তরঙ্গ সমীকরণ",
                "text_bn": "• তাপ সমীকরণ (Heat Equation, $\\partial_t u = \\alpha \\partial_x^2 u$): প্যারাবলিক পিডিই। এতে কোনো জড়তা নেই। এটি মসৃণ করে, তথ্য নিশ্চিহ্ন করে, এবং এনট্রপি বাড়ায়।\n• তরঙ্গ সমীকরণ (Wave Equation, $\\partial_t^2 u = c^2 \\partial_x^2 u$): হাইপারবোলিক পিডিই। এতে জড়তা রয়েছে। এটি সংকেত ও তথ্যকে স্থানান্তর করে, কোনো ক্ষয় ছাড়াই রূপ ও বিস্তার অবিকল ধরে রাখে।"
            },
            "closing_thought_bn": "কেন স্থানিক দ্বিতীয় অন্তরজ বা বক্রতার সাথে সময়ের দ্বিতীয় অন্তরজ বা ত্বরণের সমতা তরঙ্গের এই অবিরাম স্পন্দন সৃষ্টি করে?"
        },
        {
            "id": "sec-wave-derivation",
            "alias": "sec_02_wave_derivation",
            "number_bn": "২",
            "title_bn": "টানটান তারের ব্যবকলন ও তরঙ্গ বেগ c = √(T/μ) (Derivation from a Vibrating String)",
            "paragraphs": [
                "এই সমীকরণটি কীভাবে প্রকৃতির নিয়ম থেকে স্বাভাবিকভাবে উঠে আসে? চলুন কল্পনা করি সবচেয়ে আদিম এক ব্যবস্থা: দুই প্রান্তে দৃঢ়ভাবে আটকানো একটি টানটান গিটারের তার।",
                "ধরা যাক, অনুভূমিক অবস্থান $x$ এবং সময় $t$-তে তারটির উল্লম্ব সরণ হলো $u(x, t)$। এবার অবস্থান $x$ এবং $x + \\Delta x$-এর মধ্যবর্তী অতি ক্ষুদ্র একটি অংশ কেটে আলাদা করে ভাবুন। তারের প্রতি একক দৈর্ঘ্যের ভর $\\mu$ (Linear mass density), এবং তারটিতে অনুভূমিক টান বল $T$ কাজ করছে।",
                "যদি তারটি বাঁকা থাকে, তবে দুই প্রান্তের টান স্পর্শক রেখা বরাবর ক্রিয়া করায় পুরোপুরি পরস্পরকে প্রশমিত করতে পারে না। ডান প্রান্তের ঢাল $\\left.\\frac{\\partial u}{\\partial x}\\right|_{x+\\Delta x}$ এবং বাম প্রান্তের ঢাল $\\left.\\frac{\\partial u}{\\partial x}\\right|_x$ সমান না হওয়ায় একটি নিট উল্লম্ব বল সৃষ্টি হয়।",
                "এই দুই ঢালের ব্যবধানকে $\\Delta x$ দিয়ে ভাগ করলে ক্যালকুলাসের সংজ্ঞানুযায়ী স্থানিক দ্বিতীয় অন্তরজ $\\frac{\\partial^2 u}{\\partial x^2}$ বা বক্রতা পাওয়া যায়। নিউটনের দ্বিতীয় সূত্র $F = ma$ প্রয়োগ করলে ভর $(\\mu \\Delta x)$ এবং উল্লম্ব ত্বরণ $\\frac{\\partial^2 u}{\\partial t^2}$-এর সাথে সমতা স্থাপন করলেই ডেল্টা এক্স কাটাকাটি হয়ে অবিকল তরঙ্গ সমীকরণটি প্রকাশিত হয়।"
            ],
            "formulas": [
                {
                    "latex": "F_{\\text{net, vertical}} \\approx T \\left( \\left.\\frac{\\partial u}{\\partial x}\\right|_{x+\\Delta x} - \\left.\\frac{\\partial u}{\\partial x}\\right|_x \\right) \\approx T \\frac{\\partial^2 u}{\\partial x^2} \\Delta x",
                    "caption_bn": "বক্রতার কারণে টানটান তারের ক্ষুদ্র অংশে নিট উল্লম্ব প্রত্যয়নী বল।"
                },
                {
                    "latex": "(\\mu \\Delta x) \\frac{\\partial^2 u}{\\partial t^2} = T \\frac{\\partial^2 u}{\\partial x^2} \\Delta x \\implies \\frac{\\partial^2 u}{\\partial t^2} = \\left( \\frac{T}{\\mu} \\right) \\frac{\\partial^2 u}{\\partial x^2}",
                    "caption_bn": "নিউটনের দ্বিতীয় সূত্র প্রয়োগে তরঙ্গ সমীকরণ লাভ।"
                },
                {
                    "latex": "c = \\sqrt{\\frac{T}{\\mu}}",
                    "caption_bn": "তরঙ্গ সঞ্চালনের গতিবেগ (Wave Propagation Speed)।"
                }
            ],
            "callout": {
                "title_bn": "তরঙ্গ গতিবেগের ভৌত স্বজ্ঞা",
                "text_bn": "সমীকরণ $c = \\sqrt{T/\\mu}$ আমাদের প্রতিদিনের অভিজ্ঞতার সাথে নিখুঁতভাবে মেলে:\n• টান বৃদ্ধি ($T \\uparrow$): গিটারের তার যত বেশি টাইট করা হয়, টান বৃদ্ধি পাওয়ায় তরঙ্গের বেগ $c$ তত বাড়ে এবং স্বরতীক্ষ্ণতা বা কম্পাঙ্ক বৃদ্ধি পায়।\n• ভর বৃদ্ধি ($\\mu \\uparrow$): মোটা বা ভারী তারের জড়তা বেশি হওয়ায় তরঙ্গের গতি ধীর হয়, ফলে বাদ্যযন্ত্রের খাদ বা লো-ফ্রিকোয়েন্সি নোট তৈরি হয়।"
            },
            "closing_thought_bn": "স্থানিক বক্রতা সৃষ্টি করে ত্বরণ, যা বেগকে পরিবর্তন করে সরণ ঘটায়—এভাবেই তারের প্রতিটি কণা পার্শ্ববর্তী কণার সাথে শৃঙ্খলিত হয়ে তরঙ্গ ছড়ায়।"
        },
        {
            "id": "sec-standing-waves",
            "alias": "sec_03_standing_waves",
            "number_bn": "৩",
            "title_bn": "স্থির তরঙ্গ, চলক পৃথকীকরণ ও সুরের হারমোনিক্স (Standing Waves & Separation of Variables)",
            "paragraphs": [
                "একটি টানটান গিটারের তার যখন দুই প্রান্তে দৃঢ়ভাবে আটকানো থাকে ($u(0, t) = u(L, t) = 0$), তখন তরঙ্গ মুক্তভাবে প্রবাহিত হতে পারে না; বরং দুই প্রান্ত থেকে অবিরাম প্রতিফলিত হয়ে একটি সুনির্দিষ্ট ছন্দে স্থির দাঁড়িয়ে থাকে। একে বলে স্থির তরঙ্গ (Standing Wave)।",
                "এই ধরনের বাউন্ডারি ভ্যালু সমস্যা সমাধানের সবচেয়ে শক্তিশালী পদ্ধতি হলো চলক পৃথকীকরণ (Separation of Variables)। আমরা ধরে নিই সমাধানটি স্থানিক ও কালিক অংশের গুণফল: $u(x, t) = X(x) T(t)$।",
                "তরঙ্গ সমীকরণে এটি প্রতিস্থাপন করে $c^2 X T$ দিয়ে উভয় পক্ষে ভাগ করলে পাওয়া যায়: $\\frac{T''(t)}{c^2 T(t)} = \\frac{X''(x)}{X(x)}$। বামপাশ কেবল সময়ের এবং ডানপাশ কেবল দূরত্বের ফাংশন হওয়ায় উভয়কেই একটি ঋণাত্মক ধ্রুবক $-k^2$-এর সমান হতে হবে।",
                "সীমান্ত শর্ত $X(0) = X(L) = 0$ প্রয়োগ করলে স্থানিক সমাধান দাঁড়ায় সাইন তরঙ্গ: $X_n(x) = \\sin\\left(\\frac{n \\pi x}{L}\\right)$। আর কালিক সমীকরণটি রূপ নেয় একটি অবমন্দহীন সাধারণ স্পন্দকে: $T_n''(t) + \\omega_n^2 T_n(t) = 0$, যার কৌণিক কম্পাঙ্ক $\\omega_n = c \\frac{n \\pi}{L}$।"
            ],
            "formulas": [
                {
                    "latex": "u(x, t) = X(x)T(t) \\implies \\frac{1}{c^2}\\frac{T''(t)}{T(t)} = \\frac{X''(x)}{X(x)} = -k^2",
                    "caption_bn": "চলক পৃথকীকরণ পদ্ধতি: স্থান ও কাল সম্পূর্ণ স্বাধীন সমীকরণে বিভক্ত।"
                },
                {
                    "latex": "\\omega_n = c \\frac{n \\pi}{L} = \\frac{n \\pi}{L}\\sqrt{\\frac{T}{\\mu}}, \\quad n = 1, 2, 3, \\dots",
                    "caption_bn": "বাদ্যযন্ত্রের প্রাকৃতিক কৌণিক কম্পাঙ্ক (Harmonics / Normal Modes)।"
                },
                {
                    "latex": "u_n(x, t) = \\sin\\left( \\frac{n \\pi x}{L} \\right) \\left[ A_n \\cos(\\omega_n t) + B_n \\sin(\\omega_n t) \\right]",
                    "caption_bn": "একটি একক স্থায়ী তরঙ্গ মোডের (Normal Mode) অবিকল গাণিতিক সমাধান।"
                }
            ],
            "callout": {
                "title_bn": "বাদ্যযন্ত্রের সুর ও হারমোনিক্স",
                "text_bn": "• $n=1$ (Fundamental Mode): মূল সুর। তারের মাঝখানে সর্বোচ্চ বিস্তার এবং দুই প্রান্তে দুটি নিস্পন্দ বিন্দু (Nodes)।\n• $n=2$ (First Overtone): অষ্টক সুর। মাঝখানে একটি অতিরিক্ত নিস্পন্দ বিন্দু গঠিত হয় এবং কম্পাঙ্ক অবিকল দ্বিগুণ হয়ে যায়।\n• সাধারণ সুর: যেকোনো বাস্তব বাদ্যযন্ত্র বাজানো হলে সমস্ত স্বাভাবিক মোডের রৈখিক উপরিপাত ঘটে: $u(x, t) = \\sum_{n=1}^\\infty u_n(x, t)$। বিভিন্ন মোডের বিস্তারের অনুপাতই নির্ধারণ করে সুরের বর্ণ বা টিম্বার (Timbre)।"
            },
            "closing_thought_bn": "কিন্তু তারটি যদি অসীম দীর্ঘ হয় বা মুক্ত স্থানে শব্দ বা আলোর তরঙ্গ ছড়ায়, তবে তার গতিপ্রকৃতি কেমন হবে?"
        },
        {
            "id": "sec-dalembert",
            "alias": "sec_04_dalembert",
            "number_bn": "৪",
            "title_bn": "দ্য'আলেমবার্টের পদ্ধতি ও বিপরীতমুখী চলন্ত তরঙ্গ f(x-ct) + g(x+ct) (d'Alembert's Traveling Wave Solution)",
            "paragraphs": [
                "১৭৪৭ সালে ফরাসি দার্শনিক ও গণিতবিদ জঁ লে রঁ দ্য'আলেমবার্ট তরঙ্গ সমীকরণকে এমন এক দৃষ্টিতে দেখেছিলেন যা গণিতের ইতিহাসে সবচেয়ে মার্জিত সমাধানগুলোর একটি হিসেবে স্বীকৃত।",
                "তিনি লক্ষ্য করেন যে তরঙ্গ সমীকরণের ডিফারেনশিয়াল অপারেটরটিকে দুটি বর্গের বিয়োগফলের মতো উৎপাদকে বিশ্লেষণ করা যায়: $\\left( \\frac{\\partial^2}{\\partial t^2} - c^2 \\frac{\\partial^2}{\\partial x^2} \\right) = \\left( \\frac{\\partial}{\\partial t} - c \\frac{\\partial}{\\partial x} \\right) \\left( \\frac{\\partial}{\\partial t} + c \\frac{\\partial}{\\partial x} \\right)$।",
                "এবার বৈশিষ্ট্যমূলক স্থানাঙ্ক (Characteristic Coordinates) সংজ্ঞায়িত করুন: $\\xi = x - ct$ এবং $\\eta = x + ct$। চেইন রুল প্রয়োগ করলে তরঙ্গ সমীকরণটি সংকুচিত হয়ে দাঁড়ায়: $\\frac{\\partial^2 u}{\\partial \\xi \\partial \\eta} = 0$!",
                "উভয় পক্ষে ক্রমান্বয়ে দুইবার সমাকলন করলে সরাসরি সাধারণ সমাধান বেরিয়ে আসে: $u(x, t) = f(x - ct) + g(x + ct)$। এর চেয়ে সরল ও গভীর সমাধান আর হতে পারে না!"
            ],
            "formulas": [
                {
                    "latex": "\\left( \\frac{\\partial}{\\partial t} - c\\frac{\\partial}{\\partial x} \\right)\\left( \\frac{\\partial}{\\partial t} + c\\frac{\\partial}{\\partial x} \\right)u = 0 \\implies \\frac{\\partial^2 u}{\\partial \\xi \\partial \\eta} = 0",
                    "caption_bn": "অপারেটর উৎপাদকীকরণ ও বৈশিষ্ট্যমূলক স্থানাঙ্কে রূপান্তর।"
                },
                {
                    "latex": "u(x, t) = f(x - ct) + g(x + ct)",
                    "caption_bn": "দ্য'আলেমবার্টের সার্বিক তরঙ্গ সমাধান (d'Alembert's General Solution)।"
                },
                {
                    "latex": "u(x, t) = \\frac{u_0(x - ct) + u_0(x + ct)}{2} + \\frac{1}{2c}\\int_{x - ct}^{x + ct} v_0(s)\\,ds",
                    "caption_bn": "প্রাথমিক সরণ $u_0(x)$ ও আদি বেগ $v_0(x)$ সাপেক্ষে দ্য'আলেমবার্টের পূর্ণাঙ্গ রূপ।"
                }
            ],
            "callout": {
                "title_bn": "দ্য'আলেমবার্ট সমাধানের জ্যামিতিক তাৎপর্য",
                "text_bn": "• $f(x - ct)$: একটি অনড় আকার যা বিন্দুমাত্র বিকৃত না হয়ে ধ্রুব বেগ $c$ নিয়ে ডান দিকে এগিয়ে চলেছে।\n• $g(x + ct)$: একই আকৃতির বা ভিন্ন আকৃতির অপর একটি তরঙ্গ যা বেগ $c$ নিয়ে বাম দিকে ছুটে চলেছে।\n• পালস বিভাজন: যদি আপনি একটি তারকে স্থির অবস্থায় কোনো খাঁজে টেনে ছেড়ে দেন ($v_0 = 0$), তবে আদি আকৃতি $u_0(x)$ সমান দুটি অর্ধেক উচ্চতার তরঙ্গে বিভক্ত হয়: একটি ডানমুখী $\\frac{1}{2}u_0(x-ct)$ এবং অন্যটি বামমুখী $\\frac{1}{2}u_0(x+ct)$।"
            },
            "closing_thought_bn": "দুটি বিপরীতমুখী চলন্ত তরঙ্গ যখন পরস্পরের মুখোমুখি হয়, তখন তারা কোনো শক্তি ক্ষয় বা সংঘর্ষ ছাড়াই একে অপরকে অতিক্রম করে চলে যায়—এটাই রৈখিক উপরিপাতের পরম সৌন্দর্য।"
        },
        {
            "id": "sec-energy-harmonics",
            "alias": "sec_05_energy_harmonics",
            "number_bn": "৫",
            "title_bn": "শক্তির নিত্যতা, তথ্য সংরক্ষণ ও মহাজাগতিক বিস্তার (Energy Conservation & The Preservation of Signals)",
            "paragraphs": [
                "তরঙ্গ সমীকরণের পদার্থবৈজ্ঞানিক আত্মা নিহিত রয়েছে এর নিখুঁত শক্তি সংরক্ষণে। তাপ সমীকরণে যেখানে শক্তির রূপ একমুখীভাবে তাপে রূপান্তরিত হয়ে হারিয়ে যায়, তরঙ্গ সমীকরণে সেখানে শক্তি চিরকাল সম্পূর্ণ সংরক্ষিত থাকে।",
                "কম্পনশীল তারের মোট যান্ত্রিক শক্তি $E(t)$ দুটি উপাদানের সমন্বয়: উল্লম্ব অণুগুলোর গতিশক্তি (Kinetic Energy) এবং তারের ক্ষুদ্র বক্রতার জন্য সঞ্চিত স্থিতিস্থাপক স্থিতিশক্তি (Potential Energy)।",
                "সমগ্র তারের ওপর এই শক্তির যোগফলকে সময়ের সাপেক্ষে ব্যবকলন করে তরঙ্গ সমীকরণ এবং আংশিক সমাকলন প্রয়োগ করলে দেখা যায় $\\frac{dE}{dt} = 0$! এর অর্থ হলো, ঘর্ষণ বা সান্দ্রতাহীন মাধ্যমে তরঙ্গ শক্তি স্থান থেকে স্থানে পরিবাহিত হয়, কিন্তু মহাবিশ্বে তার মোট পরিমাণ এক ফোঁটাও কমে না।"
            ],
            "formulas": [
                {
                    "latex": "E(t) = \\int_0^L \\left[ \\frac{1}{2}\\mu \\left( \\frac{\\partial u}{\\partial t} \\right)^2 + \\frac{1}{2}T \\left( \\frac{\\partial u}{\\partial x} \\right)^2 \\right] dx",
                    "caption_bn": "কম্পনশীল তারের মোট গতিশক্তি ও স্থিতিশক্তির সমাকলন।"
                },
                {
                    "latex": "\\frac{dE}{dt} = \\int_0^L \\left[ \\mu \\frac{\\partial u}{\\partial t}\\frac{\\partial^2 u}{\\partial t^2} + T \\frac{\\partial u}{\\partial x}\\frac{\\partial^2 u}{\\partial x \\partial t} \\right] dx = 0",
                    "caption_bn": "তরঙ্গ সমীকরণ ও আংশিক সমাকলনের মাধ্যমে শক্তির অটল নিত্যতা প্রমাণ।"
                },
                {
                    "latex": "\\frac{\\partial^2 \\vec{E}}{\\partial t^2} = c^2 \\nabla^2 \\vec{E}, \\quad \\frac{\\partial^2 \\vec{B}}{\\partial t^2} = c^2 \\nabla^2 \\vec{B}, \\quad c = \\frac{1}{\\sqrt{\\mu_0 \\varepsilon_0}}",
                    "caption_bn": "ম্যাক্সওয়েলের তড়িৎচৌম্বকীয় তরঙ্গ সমীকরণ ও আলোর গতিবেগ।"
                }
            ],
            "callout": {
                "title_bn": "মহাজাগতিক বার্তা ও আলোর গতিবেগ",
                "text_bn": "১৮৬৫ সালে জেমস ক্লার্ক ম্যাক্সওয়েল যখন তাঁর তড়িৎ ও চুম্বকত্বের সমীকরণগুলোকে একত্রিত করেন, তখন শূন্যস্থানে তড়িৎক্ষেত্র $\\vec{E}$ এবং চৌম্বকক্ষেত্র $\\vec{B}$-এর জন্য হুবহু ত্রিমাত্রিক তরঙ্গ সমীকরণটি বেরিয়ে আসে!\nসেখানে তরঙ্গের বেগ ছিল $c = 1/\\sqrt{\\mu_0 \\varepsilon_0}$, যা নির্ভুলভাবে আলোর পরিমাপকৃত গতিবেগের সমান। ম্যাক্সওয়েল উপলব্ধি করেছিলেন: আলো নিজেই একটি তরঙ্গ সমীকরণ মেনে চলা তড়িৎচৌম্বকীয় আলোড়ন! এই সমীকরণই কোটি আলোকবর্ষ দূর থেকে নক্ষত্রের আলো ও মহাকর্ষীয় তরঙ্গকে অবিকৃত অবস্থায় আমাদের টেলিস্কোপে পৌঁছে দেয়।"
            },
            "closing_thought_bn": "ক্যালকুলাসের দ্বিতীয় ক্রমের এই রূপান্তর স্থান ও কালের মাঝে এমন এক সেতুবন্ধন রচনা করে, যা আমাদের মহাবিশ্বকে আলো, সঙ্গীত ও চেতনার রঙে রাঙিয়ে তোলে।"
        }
    ],
    "quizzes": [
        {
            "id": "quiz-1",
            "question_bn": "১. একমাত্রিক তরঙ্গ সমীকরণ $\\frac{\\partial^2 u}{\\partial t^2} = c^2 \\frac{\\partial^2 u}{\\partial x^2}$-এ স্থানিক দ্বিতীয় অন্তরজ $\\frac{\\partial^2 u}{\\partial x^2}$-এর স্বজ্ঞাত ভৌতিক তাৎপর্য কী?",
            "correct_index": 1,
            "options": [
                {
                    "text_bn": "এটি তরঙ্গের মোট শক্তির অপচয়ের হার নির্দেশ করে",
                    "feedback_bn": "ভুল! তরঙ্গ সমীকরণে কোনো শক্তির অপচয় নেই, এটি একটি ক্ষয়হীন সংরক্ষণশীল সমীকরণ।"
                },
                {
                    "text_bn": "এটি তারের স্থানীয় বক্রতা পরিমাপ করে, যা স্পর্শক টানের অসমতার কারণে তারের কণাটির ওপর নিট উল্লম্ব প্রত্যয়নী বল ও ত্বরণ তৈরি করে",
                    "feedback_bn": "চমৎকার ও সম্পূর্ণ সঠিক! তার বাঁকা হলে দুই প্রান্তের স্পর্শক টানের উল্লম্ব উপাংশগুলোর ব্যবধান ঘটে, যা নিউটনের দ্বিতীয় সূত্রানুযায়ী কণার উল্লম্ব ত্বরণ $\\frac{\\partial^2 u}{\\partial t^2}$ সৃষ্টি করে।"
                },
                {
                    "text_bn": "এটি তরঙ্গের অনুভূমিক গতিবেগকে সরাসরি পরিমাপ করে",
                    "feedback_bn": "ভুল! কণাগুলো কেবল উল্লম্বভাবে স্পন্দিত হয়; অনুভূমিক গতিবেগ $c$ একটি ধ্রুবক সহগ।"
                },
                {
                    "text_bn": "এটি তারের তাপীয় ব্যাপন সহগের সমানুপাতিক",
                    "feedback_bn": "ভুল! তাপীয় ব্যাপন তাপ সমীকরণের বৈশিষ্ট্য, তরঙ্গ সমীকরণের নয়।"
                }
            ],
            "explanation_bn": "টানটান তারের জন্য স্থানিক দ্বিতীয় অন্তরজ হলো বক্রতার পরিমাপ। স্থানীয় বক্রতাই বলে দেয় দুই প্রান্তের টান বলের দিক কতটা ভিন্ন, যার ফলে সৃষ্টি হয় নিট ঊর্ধ্বমুখী বা নিম্নমুখী বল এবং ত্বরণ।"
        },
        {
            "id": "quiz-2",
            "question_bn": "২. তারের টান $T$ চারগুণ বৃদ্ধি করা হলে এবং প্রতি একক দৈর্ঘ্যের ভর $\\mu$ অপরিবর্তিত থাকলে তারের মধ্য দিয়ে তরঙ্গ সঞ্চালনের গতিবেগ $c = \\sqrt{T/\\mu}$ এবং তারের মূল সুরের কম্পাঙ্ক কত গুণ বৃদ্ধি পাবে?",
            "correct_index": 2,
            "options": [
                {
                    "text_bn": "৪ গুণ বৃদ্ধি পাবে",
                    "feedback_bn": "ভুল! বেগ টানের সমানুপাতিক নয়, বরং টানের বর্গমূলের সমানুপাতিক।"
                },
                {
                    "text_bn": "১৬ গুণ বৃদ্ধি পাবে",
                    "feedback_bn": "ভুল! এটি বর্গের সমানুপাতিক নয়।"
                },
                {
                    "text_bn": "২ গুণ বৃদ্ধি পাবে",
                    "feedback_bn": "একদম নিখুঁত! যেহেতু $c = \\sqrt{T/\\mu}$, তাই টান চারগুণ ($4T$) হলে তরঙ্গের বেগ $\\sqrt{4} = 2$ গুণ বৃদ্ধি পায়। আর মৌলিক কম্পাঙ্ক $f_1 = \\frac{c}{2L}$ হওয়ায় কম্পাঙ্কও অবিকল ২ গুণ বৃদ্ধি পাবে!"
                },
                {
                    "text_bn": "কোনো পরিবর্তন হবে না, কেবল বিস্তার দ্বিগুণ হবে",
                    "feedback_bn": "ভুল! টান বাড়ালে বেগ ও কম্পাঙ্ক উভয়ই প্রত্যক্ষভাবে বৃদ্ধি পায়।"
                }
            ],
            "explanation_bn": "তরঙ্গ বেগ $c = \\sqrt{T/\\mu}$ টানের বর্গমূলের সাথে পরিবর্তিত হয়। ফলে টান ৪ গুণ হলে বেগ দ্বিগুণ হয় এবং বাদ্যযন্ত্রের তারে উৎপন্ন সুরের কম্পাঙ্কও দ্বিগুণ (এক অক্টেভ উপরে) উঠে যায়।"
        },
        {
            "id": "quiz-3",
            "question_bn": "৩. দ্য'আলেমবার্টের সমাধান $u(x, t) = f(x - ct) + g(x + ct)$-এর ক্ষেত্রে শুরুতে স্থির থাকা একটি তারের কেন্দ্রবিন্দুতে ত্রিভুজাকার খাঁজ তুলে ছেড়ে দিলে ($v_0(x) = 0$) তরঙ্গের গতিপ্রকৃতি কেমন হয়?",
            "correct_index": 0,
            "options": [
                {
                    "text_bn": "প্রাথমিক ত্রিভুজাকার খাঁজটি সমান অর্ধেক উচ্চতার দুটি অভিন্ন তরঙ্গে বিভক্ত হয়ে যায়, যার একটি বেগ $c$ নিয়ে ডান দিকে এবং অপরটি বেগ $c$ নিয়ে বাম দিকে কোনো বিকৃতি ছাড়াই ছুটে চলে",
                    "feedback_bn": "অসাধারণ উত্তর! দ্য'আলেমবার্টের সূত্রানুযায়ী $u(x, t) = \\frac{1}{2}u_0(x - ct) + \\frac{1}{2}u_0(x + ct)$। ফলে আদি স্পন্দন অবিকল দুটি সমান বিপরীতমুখী অর্ধাংশে ভাগ হয়ে স্থান জুড়ে স্থানান্তরিত হয়।"
                },
                {
                    "text_bn": "তরঙ্গটি তাৎক্ষণিকভাবে মসৃণ হয়ে তাপ সমীকরণের মতো এক নিমেষে সমতল হয়ে যায়",
                    "feedback_bn": "ভুল! এটি তরঙ্গ সমীকরণ, তাপ সমীকরণ নয়। এতে কোনো শক্তি অপচয় বা মসৃণ হয়ে মিলিয়ে যাওয়ার প্রক্রিয়া নেই।"
                },
                {
                    "text_bn": "পুরো খাঁজটি তার মূল স্থানেই আটকে থাকে এবং কেবল বিস্তার সময়ের সাথে বাড়তে থাকে",
                    "feedback_bn": "ভুল! মুক্ত বা চলন্ত অবস্থায় খাঁজটি স্থির থাকে না, বরং স্থান জুড়ে সঞ্চালিত হয়।"
                },
                {
                    "text_bn": "তরঙ্গটি কেবল ডান দিকে প্রবাহিত হয়, বাম দিকে কোনো তরঙ্গ সৃষ্টি হতে পারে না",
                    "feedback_bn": "ভুল! প্রতিসাম্যের কারণে উভয় দিকেই সমান বিস্তারের তরঙ্গ ছুটে যায়।"
                }
            ],
            "explanation_bn": "আদি বেগ শূন্য হলে দ্য'আলেমবার্ট সূত্র $u(x, t) = \\frac{1}{2}[u_0(x - ct) + u_0(x + ct)]$ প্রদান করে। অর্থাৎ যেকোনো প্রাথমিক আকৃতি দুটি অর্ধ-বিস্তারের অবিকৃত রূপ নিয়ে বিপরীত দুই দিকে আলোর বেগে বা মাধ্যম-বেগে ছুটে যায়।"
        }
    ],
    "interactive_components": [
        {
            "id": "wave-equation-simulator",
            "title_bn": "ইন্টারেক্টিভ ল্যাব: টানা তারের কম্পন ও দ্য'আলেমবার্ট তরঙ্গ সিমুলেটর",
            "type": "wave_equation_canvas",
            "parameters": [
                {
                    "name": "initial_shape",
                    "label_bn": "প্রাথমিক তারের সরণ (Initial Displacement)",
                    "type": "select",
                    "options": [
                        { "value": "pluck_triangle", "label_bn": "টানটান গিটারের খাঁজ (Plucked Triangle)" },
                        { "value": "fundamental_sine", "label_bn": "একক মূল সুর (Fundamental Sine Mode)" },
                        { "value": "harmonic_multi", "label_bn": "মিশ্র হারমোনিকস (Harmonic Superposition)" },
                        { "value": "gaussian_pulse", "label_bn": "কেন্দ্রে গাউসিয়ান পালস (Traveling Wave Pulse)" }
                    ],
                    "default": "pluck_triangle"
                },
                {
                    "name": "tension",
                    "label_bn": "তারের টান T (Tension in Newtons)",
                    "min": 10.0,
                    "max": 200.0,
                    "default": 100.0,
                    "step": 5.0
                },
                {
                    "name": "linear_density",
                    "label_bn": "তারের রৈখিক ঘনত্ব μ (Linear Mass Density)",
                    "min": 0.001,
                    "max": 0.05,
                    "default": 0.01,
                    "step": 0.001
                },
                {
                    "name": "boundary_type",
                    "label_bn": "প্রান্তীয় সীমান্ত শর্ত (Boundary Condition)",
                    "type": "select",
                    "options": [
                        { "value": "fixed", "label_bn": "উভয় প্রান্তে আটকানো (Fixed Ends / Nodes)" },
                        { "value": "free", "label_bn": "মুক্ত প্রান্ত (Free Ends / Antinodes)" },
                        { "value": "periodic", "label_bn": "অনন্ত পর্যায়বৃত্ত সীমান্ত (Periodic Ring)" }
                    ],
                    "default": "fixed"
                }
            ],
            "metrics": [
                {
                    "id": "wave_speed",
                    "label_bn": "তরঙ্গ গতিবেগ c = √(T/μ)",
                    "unit": "m/s"
                },
                {
                    "id": "fundamental_freq",
                    "label_bn": "মূল সুরের কম্পাঙ্ক f₁",
                    "unit": "Hz"
                },
                {
                    "id": "kinetic_energy",
                    "label_bn": "মোট গতিশক্তি K(t)",
                    "unit": "J"
                },
                {
                    "id": "potential_energy",
                    "label_bn": "মোট স্থিতিশক্তি U(t)",
                    "unit": "J"
                },
                {
                    "id": "total_energy",
                    "label_bn": "মোট সংরক্ষিত শক্তি E = K + U",
                    "unit": "J"
                }
            ],
            "description_bn": "উপরে দেখুন বাস্তব সময়ে তারের গতিশীল স্পন্দন এবং নিচে পর্যবেক্ষণ করুন গতিশক্তি ও স্থিতিশক্তির ফেজ রূপান্তর। লক্ষ্য করুন কীভাবে টান বৃদ্ধি করলে তরঙ্গের গতিবেগ বৃদ্ধি পায় এবং কীভাবে প্রতিফলনের সময় স্থির তরঙ্গ বা বিপরীতমুখী চলন্ত তরঙ্গের জন্ম হয়।"
        }
    ],
    "key_formulas": [
        {
            "name_bn": "একমাত্রিক তরঙ্গ সমীকরণ (1D Wave Equation)",
            "latex": "\\frac{\\partial^2 u}{\\partial t^2} = c^2 \\frac{\\partial^2 u}{\\partial x^2}, \\quad c = \\sqrt{\\frac{T}{\\mu}}"
        },
        {
            "name_bn": "চলক পৃথকীকরণ আইগেনমোড (Normal Modes)",
            "latex": "u_n(x, t) = \\sin\\left(\\frac{n \\pi x}{L}\\right)\\left[ A_n \\cos(\\omega_n t) + B_n \\sin(\\omega_n t) \\right], \\quad \\omega_n = \\frac{n \\pi c}{L}"
        },
        {
            "name_bn": "দ্য'আলেমবার্টের সার্বিক রূপ (d'Alembert's Traveling Waves)",
            "latex": "u(x, t) = f(x - ct) + g(x + ct)"
        },
        {
            "name_bn": "আদি শর্ত সাপেক্ষে দ্য'আলেমবার্ট সূত্র (Initial Value Wave Formula)",
            "latex": "u(x, t) = \\frac{u_0(x - ct) + u_0(x + ct)}{2} + \\frac{1}{2c}\\int_{x - ct}^{x + ct} v_0(s)\\,ds"
        },
        {
            "name_bn": "শক্তির নিত্যতা সমাকলন (Wave Energy Conservation)",
            "latex": "E = \\int_0^L \\left[ \\frac{1}{2}\\mu \\left(\\frac{\\partial u}{\\partial t}\\right)^2 + \\frac{1}{2}T \\left(\\frac{\\partial u}{\\partial x}\\right)^2 \\right] dx, \\quad \\frac{dE}{dt} = 0"
        },
        {
            "name_bn": "ত্রিমাত্রিক তরঙ্গ সমীকরণ ও ডেল'আলেমবার্টিয়ান (3D Wave Equation & D'Alembertian)",
            "latex": "\\Box u = \\frac{1}{c^2}\\frac{\\partial^2 u}{\\partial t^2} - \\nabla^2 u = 0, \\quad \\nabla^2 = \\frac{\\partial^2}{\\partial x^2} + \\frac{\\partial^2}{\\partial y^2} + \\frac{\\partial^2}{\\partial z^2}"
        }
    ],
    "glossary": [
        {
            "term_en": "Wave Equation",
            "term_bn": "তরঙ্গ সমীকরণ",
            "definition_bn": "একটি দ্বিতীয় ক্রমের রৈখিক আংশিক ডিফারেনশিয়াল সমীকরণ যা স্থান ও কালের মধ্য দিয়ে কোনো মাধ্যমের স্পন্দন বা তরঙ্গের ক্ষয়হীন সঞ্চালনকে বর্ণনা করে।"
        },
        {
            "term_en": "d'Alembert's Solution",
            "term_bn": "দ্য'আলেমবার্টের সমাধান",
            "definition_bn": "তরঙ্গ সমীকরণের সাধারণ রূপ যা প্রমাণ করে প্রতিটি সমাধান দুটি বিপরীতমুখী অনড় চলন্ত তরঙ্গের যোগফল: $f(x - ct) + g(x + ct)$।"
        },
        {
            "term_en": "Standing Wave",
            "term_bn": "স্থির তরঙ্গ",
            "definition_bn": "সীমান্তে আটকানো মাধ্যমে বিপরীতমুখী তরঙ্গের উপরিপাতের ফলে সৃষ্ট তরঙ্গ, যেখানে কিছু নির্দিষ্ট বিন্দু (নিস্পন্দ বিন্দু) সর্বদাই স্থির থাকে।"
        },
        {
            "term_en": "Harmonics / Normal Modes",
            "term_bn": "সুরের হারমোনিক্স বা স্বাভাবিক মোড",
            "definition_bn": "একটি বাদ্যযন্ত্রের তারের নিজস্ব প্রাকৃতিক কম্পন মোড, যার কম্পাঙ্কগুলো মূল সুরের পূর্ণসংখ্যা গুণিতক।"
        },
        {
            "term_en": "Wave Speed (c)",
            "term_bn": "তরঙ্গ গতিবেগ",
            "definition_bn": "মাধ্যমে তরঙ্গের ফেজ সঞ্চালনের গতিবেগ, যা তারের টান ও ভর ঘনত্বের অনুপাতের বর্গমূল $c = \\sqrt{T/\\mu}$ দ্বারা নির্ধারিত হয়।"
        }
    ]
}

with open(DATA_JSON_FILE, "w", encoding="utf-8") as f:
    json.dump(lesson_06_data, f, ensure_ascii=False, indent=2)

print("Saved lesson_06.json successfully.")



