# -*- coding: utf-8 -*-
"""
Production Generator for Differential Equations Lesson 05:
The Heat Equation and Fourier Transforms (তাপ সমীকরণ ও ফুরিয়ার রূপান্তর)
"""

import json
from pathlib import Path

BASE_DIR = Path("departments/learning_paths/stem_mathematics/3blue1brown_courses")

# Target Paths
SCRIPT_DIR = BASE_DIR / "differential_equations" / "lesson_05_heat_equation" / "dubbing_pipeline"
SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
SCRIPT_FILE = SCRIPT_DIR / "3b1b_diffeq_l05_bangla_master_script.json"

AUDIO_DIR = BASE_DIR / "web_platform" / "assets" / "audio" / "differential_equations" / "lesson_05"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_JSON = AUDIO_DIR / "manifest.json"
MANIFEST_JS = AUDIO_DIR / "manifest.js"

DATA_DIR = BASE_DIR / "web_platform" / "data" / "differential_equations"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / "lesson_05.json"

# ==============================================================================
# 1. MASTER DUBBING SCRIPT (Zero Text Dropping, Authentic Bengali STEM Educator)
# ==============================================================================
master_script = [
    {
        "id": 1,
        "start": 0.0,
        "end": 7.4,
        "duration": 7.4,
        "en": "In this chapter, we delve deeper into the heat equation and unravel the full mathematical machinery behind Fourier series and Fourier transforms.",
        "bn": "এই অধ্যায়ে আমরা তাপ সমীকরণের গভীরে প্রবেশ করব এবং ফুরিয়ার ধারা ও ফুরিয়ার রূপান্তরের পেছনের পূর্ণ গাণিতিক সৌন্দর্য উন্মোচন করব।",
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
        "en": "Recall our foundational partial differential equation: partial u over partial t equals alpha times the second spatial derivative of u.",
        "bn": "স্মরণ করুন আমাদের মৌলিক আংশিক ডিফারেনশিয়াল সমীকরণটি: ডেল ইউ বাই ডেল টি সমান আলফা গুণ ডেল স্কয়ার ইউ বাই ডেল এক্স স্কয়ার।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 3,
        "start": 17.1,
        "end": 26.0,
        "duration": 8.9,
        "en": "Here u of x and t denotes temperature at position x at time t, and alpha is the thermal diffusivity of the rod.",
        "bn": "এখানে অবস্থান এক্স এবং সময় টি-তে তাপমাত্রা হলো ইউ অব এক্স কমা টি, এবং আলফা হলো উপাদানটির তাপীয় ব্যাপন সহগ বা থার্মাল ডিফিউসিভিটি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 4,
        "start": 26.6,
        "end": 35.8,
        "duration": 9.2,
        "en": "The second derivative measures local curvature, meaning any point cooler than the average of its neighbors warms up, and hotter points cool down.",
        "bn": "দ্বিতীয় স্থানিক অন্তরজ স্থানীয় বক্রতা পরিমাপ করে; অর্থাৎ কোনো বিন্দু প্রতিবেশীদের গড়ের চেয়ে ঠান্ডা হলে উত্তপ্ত হয়, আর বেশি গরম হলে শীতল হয়ে পড়ে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 5,
        "start": 36.4,
        "end": 45.5,
        "duration": 9.1,
        "en": "However, a partial differential equation alone cannot uniquely determine reality without boundary conditions.",
        "bn": "তবে কেবল সমীকরণ দিয়ে বাস্তব গতিপ্রকৃতি নির্দিষ্ট করা যায় না, যতক্ষণ না আমরা রডের দুই প্রান্তের সীমানা শর্ত নির্ধারণ করছি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 6,
        "start": 46.1,
        "end": 55.2,
        "duration": 9.1,
        "en": "Consider a finite rod of length L. What happens at the ends x equals zero and x equals L?",
        "bn": "ধরা যাক এল দৈর্ঘ্যের একটি রড। এক্স সমান শূন্য এবং এক্স সমান এল অবস্থানে কী ঘটছে, তা আমাদের পরিষ্কারভাবে জানতে হবে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 7,
        "start": 55.8,
        "end": 64.8,
        "duration": 9.0,
        "en": "If the ends are clamped to ice baths at zero degrees, u of 0, t equals zero and u of L, t equals zero. These are Dirichlet boundary conditions.",
        "bn": "রডের দুই প্রান্ত যদি শূন্য ডিগ্রির বরফে ডুবিয়ে রাখা হয়, তবে ইউ অব শূন্য কমা টি এবং ইউ অব এল কমা টি সর্বদা শূন্য থাকে—একে বলা হয় ডিরিক্লেট সীমানা শর্ত।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 8,
        "start": 65.4,
        "end": 74.5,
        "duration": 9.1,
        "en": "Alternatively, if the ends are perfectly insulated so no heat escapes, the spatial derivative partial u over partial x must vanish at both endpoints. These are Neumann conditions.",
        "bn": "অন্যদিকে দুই প্রান্ত যদি অন্তরক দিয়ে মোড়ানো থাকে যাতে কোনো তাপ বের হতে না পারে, তবে প্রান্তে তাপের নতি ডেল ইউ বাই ডেল এক্স শূন্য হতে হয়—এগুলো নয়ম্যান সীমানা শর্ত।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 9,
        "start": 75.1,
        "end": 84.0,
        "duration": 8.9,
        "en": "To solve this PDE with fixed zero endpoints, Joseph Fourier proposed a powerful technique: separation of variables.",
        "bn": "স্থির শূন্য সীমানা শর্তে এই সমীকরণ সমাধানে জোসেফ ফুরিয়ার একটি অসাধারণ কৌশলের প্রস্তাব দেন: চলক পৃথকীকরণ পদ্ধতি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 10,
        "start": 84.6,
        "end": 93.8,
        "duration": 9.2,
        "en": "We guess that the temperature u of x, t splits into the product of a spatial function capital X of x and a time function capital T of t.",
        "bn": "আমরা ধরে নিই তাপমাত্রা ইউ অব এক্স কমা টি হলো কেবল অবস্থানের ফাংশন ক্যাপিটাল এক্স অব এক্স এবং কেবল সময়ের ফাংশন ক্যাপিটাল টি অব টি-এর গুণফল।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 11,
        "start": 94.4,
        "end": 103.5,
        "duration": 9.1,
        "en": "Substituting into the heat equation, we get X times T prime equals alpha times X double prime times T.",
        "bn": "তাপ সমীকরণে এটি প্রতিস্থাপন করলে আমরা পাই এক্স গুণ টি প্রাইম সমান আলফা গুণ এক্স ডাবল প্রাইম গুণ টি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 12,
        "start": 104.1,
        "end": 113.2,
        "duration": 9.1,
        "en": "Dividing both sides by alpha times X times T separates the variables: T prime over alpha T equals X double prime over X.",
        "bn": "উভয়পক্ষকে আলফা গুণ এক্স গুণ টি দিয়ে ভাগ করলে চলক দুটি আলাদা হয়ে যায়: টি প্রাইম বাই আলফা টি সমান এক্স ডাবল প্রাইম বাই এক্স।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 13,
        "start": 113.8,
        "end": 122.9,
        "duration": 9.1,
        "en": "A function purely of time equaling a function purely of space must both equal a universal constant, which we call minus lambda squared.",
        "bn": "সময়ের একটি ফাংশন যদি কেবল অবস্থানের একটি ফাংশনের সমান হয়, তবে তাদের উভয়কেই একটি ধ্রুবকের সমান হতে হবে—যাকে আমরা বলি মাইনাস ল্যাম্বডা স্কয়ার।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 14,
        "start": 123.5,
        "end": 132.5,
        "duration": 9.0,
        "en": "This splits our single PDE into two ordinary differential equations that we already know how to solve.",
        "bn": "এর মাধ্যমে আমাদের একটিমাত্র আংশিক সমীকরণ ভেঙে দুটি সাধারণ ডিফারেনশিয়াল সমীকরণ বা ওডিই-তে রূপান্তরিত হয়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 15,
        "start": 133.1,
        "end": 142.2,
        "duration": 9.1,
        "en": "For space, X double prime plus lambda squared X equals zero, which has sine and cosine solutions.",
        "bn": "স্থানের জন্য সমীকরণটি হলো এক্স ডাবল প্রাইম যোগ ল্যাম্বডা স্কয়ার এক্স সমান শূন্য, যার সমাধান হলো সাইন ও কোসাইন তরঙ্গ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 16,
        "start": 142.8,
        "end": 151.8,
        "duration": 9.0,
        "en": "Applying the zero boundary conditions at 0 and L forces the cosine term to vanish and quantizes lambda to n pi over L.",
        "bn": "শূন্য এবং এল বিন্দুতে সীমানা শর্ত বসালে কোসাইন পদ বাদ পড়ে এবং ল্যাম্বডার মান কোয়ান্টায়িত হয়ে দাঁড়ায় এন পাই বাই এল।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 17,
        "start": 152.4,
        "end": 161.5,
        "duration": 9.1,
        "en": "So the allowed spatial profiles are pure standing sine waves: sine of n pi x over L, where n is a positive integer.",
        "bn": "সুতরাং অনুমোদিত স্থানিক রূপগুলো হলো বিশুদ্ধ সাইন তরঙ্গ: সাইন অব এন পাই এক্স বাই এল, যেখানে এন যেকোনো ধনাত্মক পূর্ণসংখ্যা।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 18,
        "start": 162.1,
        "end": 171.0,
        "duration": 8.9,
        "en": "Meanwhile, the time equation T prime equals minus alpha lambda squared T solves to a decaying exponential: e to the minus alpha times n pi over L squared times t.",
        "bn": "অপরদিকে সময়ের সমীকরণ টি প্রাইম সমান মাইনাস আলফা ল্যাম্বডা স্কয়ার টি সমাধান দিলে পাওয়া যায় সূচকীয় ক্ষয়: ই টু দ্য পাওয়ার মাইনাস আলফা গুণ এন পাই বাই এল হোল স্কয়ার টি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 19,
        "start": 171.6,
        "end": 180.8,
        "duration": 9.2,
        "en": "Notice the exponent: the decay rate is proportional to n squared! Higher harmonics with more wiggles decay exponentially faster.",
        "bn": "সূচকটি গভীরভাবে লক্ষ্য করুন: ক্ষয়ের গতিবেগ এন স্কয়ারের সমানুপাতিক! উচ্চ কম্পাঙ্কের তরঙ্গগুলো কয়েক মুহূর্তেই তীব্র গতিতে মিলিয়ে যায়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 20,
        "start": 181.4,
        "end": 190.5,
        "duration": 9.1,
        "en": "A harmonic with n equals two decays four times faster than n equals one; n equals three decays nine times faster.",
        "bn": "এন সমান দুই মোড এন সমান এক মোডের চেয়ে চার গুণ দ্রুত ক্ষয়প্রাপ্ত হয়; আর এন সমান তিন ক্ষয় হয় নয় গুণ দ্রুত বেগে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 21,
        "start": 191.1,
        "end": 200.2,
        "duration": 9.1,
        "en": "This is the mathematical reason why heat flow is the ultimate smoother: sharp corners and rapid fluctuations instantly melt away.",
        "bn": "এটাই হলো তাপ প্রবাহের অবিরাম মসৃণকরণের মূল গাণিতিক রহস্য: যেকোনো তীক্ষ্ণ খাঁজ এবং দ্রুত কম্পন সাথে সাথে বিলীন হয়ে যায়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 22,
        "start": 200.8,
        "end": 209.8,
        "duration": 9.0,
        "en": "Only the lowest fundamental harmonic, n equals one, survives for any substantial duration before total cooling.",
        "bn": "কেবলমাত্র মৌলিক তরঙ্গ এন সমান এক দীর্ঘ সময় ধরে টিকে থাকে, যতক্ষণ না পুরো রডটি পরিবেশের তাপমাত্রায় পৌঁছায়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 23,
        "start": 210.4,
        "end": 219.5,
        "duration": 9.1,
        "en": "Now came Joseph Fourier's daring, revolutionary leap: what if the initial temperature is NOT a pure sine wave?",
        "bn": "এখানেই জোসেফ ফুরিয়ারের অমর ও বৈপ্লবিক সাহসিকতা: প্রাথমিক তাপমাত্রা যদি কোনো বিশুদ্ধ সাইন তরঙ্গ না হয়ে একটি জটিল খাঁজকাটা বক্ররেখা হয়?",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 24,
        "start": 220.1,
        "end": 229.2,
        "duration": 9.1,
        "en": "Fourier claimed that ANY function f of x can be represented as an infinite sum of these sine harmonics.",
        "bn": "ফুরিয়ার দাবি করেন যে যেকোনো ফাংশন এফ অব এক্স-কে এই সাইন তরঙ্গগুলোর একটি অসীম যোগফল আকারে প্রকাশ করা সম্ভব!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 25,
        "start": 229.8,
        "end": 238.8,
        "duration": 9.0,
        "en": "Contemporary mathematicians like Lagrange and Laplace were deeply skeptical. How could smooth waves add up to a jagged step function?",
        "bn": "লাগ্রাঞ্জ ও লাপ্লাসের মতো শীর্ষ গণিতবিদরা তীব্র সন্দেহ প্রকাশ করেছিলেন: কতগুলো মসৃণ তরঙ্গ যোগ করে কীভাবে ধারালো সিঁড়ির মতো ফাংশন তৈরি হতে পারে?",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 26,
        "start": 239.4,
        "end": 248.5,
        "duration": 9.1,
        "en": "Yet Fourier was correct. The key lies in the orthogonality of sine functions over the interval 0 to L.",
        "bn": "অথচ ফুরিয়ারই সঠিক ছিলেন। এর চাবিকাঠি নিহিত রয়েছে শূন্য থেকে এল ব্যবধিতে সাইন তরঙ্গগুলোর পারস্পরিক লম্বতা বা অর্থোগোনালিটিতে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 27,
        "start": 249.1,
        "end": 258.2,
        "duration": 9.1,
        "en": "Integrating the product of sine of n pi x over L and sine of m pi x over L from 0 to L yields zero whenever n does not equal m.",
        "bn": "দুটি ভিন্ন কম্পাঙ্কের সাইন তরঙ্গের গুণফলের সমাকলন সর্বদা শূন্য হয়, ঠিক যেমন লম্ব ভেক্টরদের ডট প্রোডাক্ট শূন্য হয়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 28,
        "start": 258.8,
        "end": 268.0,
        "duration": 9.2,
        "en": "This orthogonality allows us to project the initial function onto each harmonic basis vector and isolate each coefficient b sub n.",
        "bn": "এই অর্থোগোনালিটি ব্যবহার করে আমরা প্রাথমিক ফাংশনটিকে প্রতিটি হারমোনিকের ওপর প্রক্ষেপণ করে সহগ বি এন নিখুঁতভাবে বের করতে পারি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 29,
        "start": 268.6,
        "end": 277.8,
        "duration": 9.2,
        "en": "The formula for b sub n is 2 over L times the integral from 0 to L of f of x times sine of n pi x over L dx.",
        "bn": "বি এন সহগের সূত্রটি হলো টু বাই এল গুণ শূন্য থেকে এল পর্যন্ত এফ অব এক্স গুণ সাইন অব এন পাই এক্স বাই এল-এর ইন্টিগ্রাল ডি এক্স।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 30,
        "start": 278.4,
        "end": 287.5,
        "duration": 9.1,
        "en": "Because the heat equation is linear, the principle of superposition guarantees that the general solution is the infinite sum of these decaying modes.",
        "bn": "যেহেতু তাপ সমীকরণ সম্পূর্ণ রৈখিক, উপরিপাত নীতি অনুযায়ী পূর্ণ সমাধানটি হলো এই ক্ষয়িষ্ণু মোডগুলোর সমষ্টি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 31,
        "start": 288.1,
        "end": 297.2,
        "duration": 9.1,
        "en": "u of x, t equals the sum from n equals 1 to infinity of b sub n e to the minus alpha times n pi over L squared t times sine of n pi x over L.",
        "bn": "ইউ অব এক্স কমা টি সমান সামেশন এন সমান এক থেকে অসীম পর্যন্ত বি এন গুণ ই টু দ্য পাওয়ার মাইনাস আলফা গুণ এন পাই বাই এল স্কয়ার টি গুণ সাইন এন পাই এক্স বাই এল।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 32,
        "start": 297.8,
        "end": 306.8,
        "duration": 9.0,
        "en": "Every complex temperature distribution is broken into independent notes, each decaying at its own natural exponential tempo.",
        "bn": "যেকোনো জটিল তাপমাত্রা যেন একটি সিম্ফনির সুর—প্রতিটি সুর তার নিজস্ব গতিতে ক্ষয়প্রাপ্ত হয়ে শান্তিতে রূপ নেয়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 33,
        "start": 307.4,
        "end": 316.5,
        "duration": 9.1,
        "en": "Now let us take this concept to its ultimate mathematical horizon: what happens if our rod is infinitely long, stretching from minus infinity to plus infinity?",
        "bn": "এবার আসুন এই ধারণাকে তার চূড়ান্ত দিগন্তে নিয়ে যাই: আমাদের ধাতব দণ্ডটি যদি সীমাবদ্ধ না হয়ে অসীম দীর্ঘ হয়, মাইনাস অসীম থেকে প্লাস অসীম পর্যন্ত?",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 34,
        "start": 317.1,
        "end": 326.2,
        "duration": 9.1,
        "en": "As length L approaches infinity, the discrete frequency spacing delta k equals pi over L shrinks toward zero.",
        "bn": "দৈর্ঘ্য এল যখন অসীমের দিকে ধাবিত হয়, তখন বিচ্ছিন্ন কম্পাঙ্ক ব্যবধান ডেল্টা কে সমান পাই বাই এল সংকুচিত হয়ে শূন্যের কাছাকাছি পৌঁছে যায়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 35,
        "start": 326.8,
        "end": 335.8,
        "duration": 9.0,
        "en": "The discrete sum over integer harmonics smoothly transforms into a continuous integral over all real frequencies k.",
        "bn": "তখন বিচ্ছিন্ন পদের যোগফল অবিচ্ছিন্ন সমাকলনে রূপান্তরিত হয়—সমস্ত বাস্তব কম্পাঙ্ক কে-এর ওপর ইন্টিগ্রাল আকারে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 36,
        "start": 336.4,
        "end": 345.5,
        "duration": 9.1,
        "en": "This is the birth of the Fourier Transform: decomposing a non-periodic signal on an infinite domain into a continuum of frequencies.",
        "bn": "এভাবেই জন্ম নেয় ফুরিয়ার রূপান্তর: একটি অসীম ডোমেইনে যেকোনো অ-পর্যায়বৃত্ত ফাংশনকে অবিচ্ছিন্ন কম্পাঙ্কের বর্ণালিতে ভেঙে ফেলার কালজয়ী পদ্ধতি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 37,
        "start": 346.1,
        "end": 355.2,
        "duration": 9.1,
        "en": "The continuous Fourier transform capital F of k is the integral of f of x times e to the minus i k x dx from minus infinity to infinity.",
        "bn": "অবিচ্ছিন্ন ফুরিয়ার রূপান্তর ক্যাপিটাল এফ অব কে হলো মাইনাস অসীম থেকে অসীম পর্যন্ত এফ অব এক্স গুণ ই টু দ্য পাওয়ার মাইনাস আই কে এক্স ডি এক্স-এর ইন্টিগ্রাল।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 38,
        "start": 355.8,
        "end": 365.0,
        "duration": 9.2,
        "en": "In Fourier space, spatial derivatives turn into simple multiplication by i times k, transforming differential equations into algebraic equations.",
        "bn": "ফুরিয়ার জগতে ক্যালকুলাসের অন্তরজ সাধারণ বীজগাণিতিক গুণনে রূপ নেয়: ডেরিভেটিভের বদলে আসে কেবল আই গুণ কে দিয়ে গুণ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 39,
        "start": 365.6,
        "end": 374.8,
        "duration": 9.2,
        "en": "Applying the Fourier transform to the infinite heat equation turns it into d u-hat over dt equals minus alpha k squared u-hat.",
        "bn": "অসীম তাপ সমীকরণে ফুরিয়ার রূপান্তর প্রয়োগ করলে এটি দাঁড়ায় ডি ইউ হ্যাট বাই ডি টি সমান মাইনাস আলফা কে স্কয়ার ইউ হ্যাট।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 40,
        "start": 375.4,
        "end": 384.5,
        "duration": 9.1,
        "en": "The solution in frequency space is immediate: u-hat of k, t equals u-hat of k, 0 times e to the minus alpha k squared t.",
        "bn": "ফ্রিকোয়েন্সি স্পেসে এর সমাধান চোখের পলকেই স্পষ্ট: ইউ হ্যাট অব কে কমা টি সমান প্রাথমিক ইউ হ্যাট গুণ ই টু দ্য পাওয়ার মাইনাস আলফা কে স্কয়ার টি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 41,
        "start": 385.1,
        "end": 394.2,
        "duration": 9.1,
        "en": "Taking the inverse Fourier transform reveals that heat diffusion is mathematically equivalent to convolution with a Gaussian heat kernel.",
        "bn": "বিপরীত ফুরিয়ার রূপান্তর নিলে দেখা যায় তাপের ব্যাপন প্রক্রিয়াটি মূলত একটি গাউসিয়ান তাপীয় কার্নেলের সাথে কনভোলিউশন বা সমন্বয়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 42,
        "start": 394.8,
        "end": 404.0,
        "duration": 9.2,
        "en": "The heat kernel is 1 over the square root of 4 pi alpha t times e to the minus x squared over 4 alpha t, spreading out like a bell curve over time.",
        "bn": "এই তাপীয় কার্নেলটি হলো ওয়ান বাই রুট ফোর পাই আলফা টি গুণ ই টু দ্য পাওয়ার মাইনাস এক্স স্কয়ার বাই ফোর আলফা টি—যা সময়ের সাথে সাথে একটি বেল কার্ভের মতো প্রসারিত হয়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 43,
        "start": 404.6,
        "end": 413.8,
        "duration": 9.2,
        "en": "This profound connection links partial differential equations, Fourier analysis, probability theory, and quantum mechanics in one glorious circle.",
        "bn": "এই অমর আবিষ্কার আংশিক ডিফারেনশিয়াল সমীকরণ, ফুরিয়ার বিশ্লেষণ, সম্ভাবনা তত্ত্ব এবং কোয়ান্টাম মেকানিক্সকে এক অবিচ্ছেদ্য ঐক্যের সূত্রে বেঁধেছে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 44,
        "start": 414.4,
        "end": 425.0,
        "duration": 10.6,
        "en": "From heat spreading through a thin iron rod to modern image compression and quantum wavefunctions, Fourier's vision remains one of the crowning triumphs of mathematical thought.",
        "bn": "একটি সরু লোহার রডে তাপ ছড়ানো থেকে শুরু করে আধুনিক ডিজিটাল ইমেজ কম্প্রেশন এবং কোয়ান্টাম তরঙ্গ ফাংশন—ফুরিয়ারের এই দূরদৃষ্টি গণিত ইতিহাসের এক চিরভাস্বর বিজয়স্তম্ভ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    }
]

with open(SCRIPT_FILE, "w", encoding="utf-8") as f:
    json.dump(master_script, f, ensure_ascii=False, indent=2)

print(f"Master script generated with {len(master_script)} items.")

# ==============================================================================
# 2. AUDIO MANIFEST & SECTION CUES (Strict 5-Section Parity)
# ==============================================================================
# Sections:
# sec-heat-pde-review: cues 1..8
# sec-boundary-separation: cues 9..16
# sec-sine-harmonics-decay: cues 17..22
# sec-fourier-orthogonality: cues 23..32
# sec-continuous-fourier-transform: cues 33..44

sections_audio = {
    "sec-heat-pde-review": {
        "section_id": "sec-heat-pde-review",
        "alias": "sec_01_heat_pde_review",
        "title": "তাপ সমীকরণ ও সীমানা শর্তের ভৌত তাৎপর্য",
        "audio_file": "sec_01_heat_pde_review.mp3",
        "cues_meta": [
            {"type": "h2", "text": "প্রথম পরিচ্ছেদ: তাপ সমীকরণ ও সীমানা শর্তের ভৌত তাৎপর্য।"},
            {"type": "chapter-quote", "text": "জোসেফ ফুরিয়ার: প্রকৃতির গভীর পর্যবেক্ষণই গাণিতিক বিশ্লেষণের সবচেয়ে সমৃদ্ধ ভিত্তি।"},
            {"type": "p", "text": master_script[1]["bn"]},
            {"type": "formula-box", "text": "একমাত্রিক তাপ সমীকরণ: ডেল ইউ বাই ডেল টি সমান আলফা গুণ ডেল স্কয়ার ইউ বাই ডেল এক্স স্কয়ার।"},
            {"type": "p", "text": master_script[3]["bn"]},
            {"type": "p", "text": master_script[4]["bn"]},
            {"type": "callout", "text": "সীমানা শর্তের দ্বৈত রূপ: দুই প্রান্ত নির্দিষ্ট তাপমাত্রায় থাকলে ডিরিক্লেট শর্ত, আর তাপ নিরোধক দিয়ে মোড়ানো থাকলে নয়ম্যান শর্ত প্রযোজ্য হয়।"},
            {"type": "figure", "text": "অ্যানিমেশনে লক্ষ্য করুন: নির্দিষ্ট শূন্য তাপমাত্রা এবং রুদ্ধ প্রান্তের ভিন্ন ভিন্ন ভৌত প্রভাব।"}
        ]
    },
    "sec-boundary-separation": {
        "section_id": "sec-boundary-separation",
        "alias": "sec_02_boundary_separation",
        "title": "চলক পৃথকীকরণ পদ্ধতি ও আইগেনমান সমস্যা",
        "audio_file": "sec_02_boundary_separation.mp3",
        "cues_meta": [
            {"type": "h2", "text": "দ্বিতীয় পরিচ্ছেদ: চলক পৃথকীকরণ পদ্ধতি ও আইগেনমান সমস্যা।"},
            {"type": "p", "text": master_script[8]["bn"]},
            {"type": "p", "text": master_script[9]["bn"]},
            {"type": "formula-box", "text": "চলক পৃথকীকরণ: টি প্রাইম বাই আলফা টি সমান এক্স ডাবল প্রাইম বাই এক্স সমান মাইনাস ল্যাম্বডা স্কয়ার।"},
            {"type": "p", "text": master_script[12]["bn"]},
            {"type": "p", "text": master_script[13]["bn"]},
            {"type": "formula-box", "text": "স্থানিক ওডিই: এক্স ডাবল প্রাইম যোগ ল্যাম্বডা স্কয়ার এক্স সমান শূন্য, যার সাধারণ রূপ সাইন ও কোসাইনের সমন্বয়।"},
            {"type": "callout", "text": "কোয়ান্টায়িত কম্পাঙ্ক: দুই প্রান্তের শূন্য শর্ত ল্যাম্বডাকে এন পাই বাই এল মানে আবদ্ধ করে ফেলে, যেখানে এন ধনাত্মক পূর্ণসংখ্যা।"}
        ]
    },
    "sec-sine-harmonics-decay": {
        "section_id": "sec-sine-harmonics-decay",
        "alias": "sec_03_sine_harmonics_decay",
        "title": "সাইন হারমোনিক্স ও উচ্চ কম্পাঙ্কের তীব্র ক্ষয়",
        "audio_file": "sec_03_sine_harmonics_decay.mp3",
        "cues_meta": [
            {"type": "h2", "text": "তৃতীয় পরিচ্ছেদ: সাইন হারমোনিক্স ও উচ্চ কম্পাঙ্কের তীব্র ক্ষয়।"},
            {"type": "p", "text": master_script[16]["bn"]},
            {"type": "formula-box", "text": "সময়ের সমাধান: টি অব টি সমান ই টু দ্য পাওয়ার মাইনাস আলফা গুণ এন পাই বাই এল হোল স্কয়ার টি।"},
            {"type": "p", "text": master_script[18]["bn"]},
            {"type": "figure", "text": "গ্রাফে দেখুন: এন সমান দুই মোড চার গুণ দ্রুত এবং এন সমান তিন মোড নয় গুণ দ্রুত গতিতে মিলিয়ে যায়।"},
            {"type": "p", "text": master_script[20]["bn"]},
            {"type": "callout", "text": "তাপের মসৃণকরণ রহস্য: উচ্চ কম্পাঙ্কের তীব্র ক্ষয়ের কারণেই তাপ প্রবাহ যেকোনো খাঁজ ও অমসৃণতাকে মুহূর্তের মধ্যে গলিয়ে একাকার করে দেয়।"}
        ]
    },
    "sec-fourier-orthogonality": {
        "section_id": "sec-fourier-orthogonality",
        "alias": "sec_04_fourier_orthogonality",
        "title": "ফুরিয়ার ধারা, উপরিপাত নীতি ও অর্থোগোনালিটি",
        "audio_file": "sec_04_fourier_orthogonality.mp3",
        "cues_meta": [
            {"type": "h2", "text": "চতুর্থ পরিচ্ছেদ: ফুরিয়ার ধারা, উপরিপাত নীতি ও অর্থোগোনালিটি।"},
            {"type": "p", "text": master_script[22]["bn"]},
            {"type": "p", "text": master_script[23]["bn"]},
            {"type": "callout", "text": "ঐতিহাসিক বিতর্ক: মসৃণ তরঙ্গ যোগ করে কীভাবে ধারালো সিঁড়ির ধাপ তৈরি সম্ভব? লাগ্রাঞ্জ ও লাপ্লাস এই দাবির তীব্র বিরোধিতা করেছিলেন।"},
            {"type": "formula-box", "text": "সাইন তরঙ্গের অর্থোগোনালিটি: শূন্য থেকে এল পর্যন্ত দুটি ভিন্ন কম্পাঙ্কের সাইন তরঙ্গের গুণফলের সমাকলন সর্বদা শূন্য।"},
            {"type": "p", "text": master_script[27]["bn"]},
            {"type": "formula-box", "text": "ফুরিয়ার সহগ নির্ণয়: বি এন সমান টু বাই এল গুণ শূন্য থেকে এল পর্যন্ত এফ অব এক্স সাইন এন পাই এক্স বাই এল ডি এক্স।"},
            {"type": "formula-box", "text": "পূর্ণ সাধারণ সমাধান: ইউ অব এক্স কমা টি সমান সামেশন বি এন গুণ ক্ষয়িষ্ণু সূচক গুণ সাইন তরঙ্গ।"},
            {"type": "p", "text": master_script[31]["bn"]}
        ]
    },
    "sec-continuous-fourier-transform": {
        "section_id": "sec-continuous-fourier-transform",
        "alias": "sec_05_continuous_fourier_transform",
        "title": "অসীম দণ্ড, ফুরিয়ার রূপান্তর ও গাউসিয়ান তাপীয় কার্নেল",
        "audio_file": "sec_05_continuous_fourier_transform.mp3",
        "cues_meta": [
            {"type": "h2", "text": "পঞ্চম পরিচ্ছেদ: অসীম দণ্ড, ফুরিয়ার রূপান্তর ও গাউসিয়ান তাপীয় কার্নেল।"},
            {"type": "p", "text": master_script[32]["bn"]},
            {"type": "p", "text": master_script[33]["bn"]},
            {"type": "formula-box", "text": "অবিচ্ছিন্ন ফুরিয়ার রূপান্তর: এফ অব কে সমান ইন্টিগ্রাল মাইনাস অসীম থেকে অসীম এফ অব এক্স ই টু দ্য পাওয়ার মাইনাস আই কে এক্স ডি এক্স।"},
            {"type": "p", "text": master_script[37]["bn"]},
            {"type": "formula-box", "text": "ফ্রিকোয়েন্সি স্পেসে ওডিই: ডি ইউ হ্যাট বাই ডি টি সমান মাইনাস আলফা কে স্কয়ার ইউ হ্যাট।"},
            {"type": "figure", "text": "গাউসিয়ান কার্নেল বিস্তার: একটি বিন্দুতে থাকা তাপ সময়ের সাথে কীভাবে প্রসারিত বেল কার্ভে রূপ নেয়।"},
            {"type": "formula-box", "text": "গাউসিয়ান ফান্ডামেন্টাল সমাধান: ওয়ান বাই রুট ফোর পাই আলফা টি গুণ ই টু দ্য পাওয়ার মাইনাস এক্স স্কয়ার বাই ফোর আলফা টি।"},
            {"type": "callout", "text": "মহাজাগতিক সংযোগ: আংশিক ডিফারেনশিয়াল সমীকরণ, ফুরিয়ার বিশ্লেষণ ও সম্ভাবনা তত্ত্বের অপূর্ব ঐক্য।"}
        ]
    }
}

manifest_sections = {}

for sec_id, data in sections_audio.items():
    cues_list = []
    current_time_ms = 0.0
    for idx, c in enumerate(data["cues_meta"]):
        char_count = len(c["text"])
        duration_ms = max(4500.0, char_count * 68.0)
        cues_list.append({
            "index": idx,
            "type": c["type"],
            "text": c["text"],
            "start_ms": round(current_time_ms, 1),
            "end_ms": round(current_time_ms + duration_ms, 1),
            "duration_ms": round(duration_ms, 1)
        })
        current_time_ms += duration_ms + 350.0

    total_sec_ms = round(current_time_ms, 1)
    sec_cue_file = AUDIO_DIR / f"{data['alias']}_cues.json"
    sec_cue_data = {
        "section_id": sec_id,
        "title": data["title"],
        "audio_file": data["audio_file"],
        "total_duration_ms": total_sec_ms,
        "cues": cues_list
    }
    with open(sec_cue_file, "w", encoding="utf-8") as f:
        json.dump(sec_cue_data, f, ensure_ascii=False, indent=2)

    manifest_sections[sec_id] = {
        "section_id": sec_id,
        "alias": data["alias"],
        "title": data["title"],
        "audio_file": data["audio_file"],
        "total_duration_ms": total_sec_ms,
        "cues": cues_list
    }

manifest_obj = {
    "course": "differential_equations",
    "lesson": "lesson_05",
    "title": "অধ্যায় ০৫ — তাপ সমীকরণ ও ফুরিয়ার রূপান্তর",
    "voice": "bn-BD-PradeepNeural",
    "mode": "authentic_teacher",
    "sections": manifest_sections
}

with open(MANIFEST_JSON, "w", encoding="utf-8") as f:
    json.dump(manifest_obj, f, ensure_ascii=False, indent=2)

with open(MANIFEST_JS, "w", encoding="utf-8") as f:
    f.write("window.TEACHER_AUDIO_MANIFEST = " + json.dumps(manifest_obj, ensure_ascii=False, indent=2) + ";\n")

print(f"Manifest JSON and JS written successfully.")

# ==============================================================================
# 3. SINGLE-SHELL LESSON DATA JSON (departments/.../lesson_05.json)
# ==============================================================================
lesson_05_data = {
    "meta": {
        "course_id": "differential_equations",
        "course_title_en": "Essence of Differential Equations",
        "course_title_bn": "ডিফারেনশিয়াল সমীকরণের মূলভাব",
        "lesson_id": "lesson_05",
        "lesson_number": 5,
        "lesson_number_bn": "০৫",
        "title_en": "The Heat Equation and Fourier Transforms",
        "title_bn": "অধ্যায় ০৫: তাপ সমীকরণ ও ফুরিয়ার রূপান্তর — সীমানা শর্ত ও হারমোনিক বিশ্লেষণ",
        "subtitle_bn": "সীমানা শর্তের ভৌত প্রভাব, চলক পৃথকীকরণ, সাইন হারমোনিক্সের তীব্র সূচকীয় ক্ষয় এবং অসীম ডোমেইনে ফুরিয়ার রূপান্তর ও গাউসিয়ান তাপীয় কার্নেল",
        "duration": "১৫:৫০",
        "youtube_id": "ToIXSwZ1pJU",
        "theme_color": "#f97316",
        "theme_color_rgb": "249, 115, 22",
        "audio_manifest": "../../assets/audio/differential_equations/lesson_05/manifest.json",
        "audio_manifest_js": "../../assets/audio/differential_equations/lesson_05/manifest.js",
        "prev_lesson": {
            "id": "lesson_04",
            "number_bn": "০৪",
            "title_bn": "অধ্যায় ০৪: তাপ সমীকরণ ও ফুরিয়ার ধারা — আংশিক ডিফারেনশিয়াল সমীকরণের রহস্য",
            "href": "lesson_04.html"
        },
        "next_lesson": {
            "id": "lesson_06",
            "number_bn": "০৬",
            "title_bn": "অধ্যায় ০৬: তরঙ্গ সমীকরণ ও দ্বিঘাত ব্যবস্থার গতিবিদ্যা (The Wave Equation)",
            "href": "lesson_06.html"
        }
    },
    "hero": {
        "badge_bn": "ডিফারেনশিয়াল সমীকরণ • পঞ্চম অধ্যায়",
        "headline_bn": "তাপ সমীকরণ ও ফুরিয়ার রূপান্তর: অবিচ্ছিন্ন সীমানা ও হারমোনিক সুর",
        "subheadline_bn": "একটি সীমাবদ্ধ দণ্ডে শূন্য বা রুদ্ধ সীমানা শর্ত কীভাবে সমীকরণের সমাধানকে প্রভাবিত করে? চলক পৃথকীকরণের মাধ্যমে কীভাবে জটিল আংশিক সমীকরণ দুটি সহজ ওডিই-তে ভেঙে যায়? এবং দণ্ডটি অসীম দীর্ঘ হলে কীভাবে ফুরিয়ার ধারা রূপ নেয় অবিচ্ছিন্ন ফুরিয়ার রূপান্তর ও গাউসিয়ান কার্নেলে?",
        "key_takeaway_bn": "তাপ সমীকরণ $\\frac{\\partial u}{\\partial t} = \\alpha \\frac{\\partial^2 u}{\\partial x^2}$ সমাধান করতে সীমানা শর্ত স্থানিক কম্পাঙ্ককে $\\lambda_n = \\frac{n\\pi}{L}$ কোয়ান্টায়িত করে। উচ্চ কম্পাঙ্কের মোডগুলো $e^{-\\alpha (n\\pi/L)^2 t}$ হারে প্রচণ্ড গতিতে মিলিয়ে যায়। অসীম দণ্ডে এই রূপান্তর ফুরিয়ার ইন্টিগ্রাল ও গাউসিয়ান বেল কার্ভে বিস্তৃত হয়।"
    },
    "bookmarks": [
        {
            "time": "০০:০০",
            "seconds": 0,
            "title_bn": "তাপ সমীকরণ ও সীমানা শর্তের ভৌত তাৎপর্য"
        },
        {
            "time": "০৩:১০",
            "seconds": 190,
            "title_bn": "চলক পৃথকীকরণ পদ্ধতি ও আইগেনমান সমস্যা"
        },
        {
            "time": "০৬:৪৫",
            "seconds": 405,
            "title_bn": "উচ্চ কম্পাঙ্কের সূচকীয় ক্ষয় ও তাপের মসৃণকরণ"
        },
        {
            "time": "১০:১৫",
            "seconds": 615,
            "title_bn": "ফুরিয়ার ধারা, উপরিপাত নীতি ও অর্থোগোনালিটি"
        },
        {
            "time": "১৩:২০",
            "seconds": 800,
            "title_bn": "অসীম দণ্ড, ফুরিয়ার রূপান্তর ও গাউসিয়ান তাপীয় কার্নেল"
        }
    ],
    "toc": [
        {
            "id": "sec-heat-pde-review",
            "title_bn": "১. তাপ সমীকরণ ও সীমানা শর্তের ভৌত তাৎপর্য"
        },
        {
            "id": "sec-boundary-separation",
            "title_bn": "২. চলক পৃথকীকরণ পদ্ধতি ও আইগেনমান সমস্যা"
        },
        {
            "id": "sec-sine-harmonics-decay",
            "title_bn": "৩. সাইন হারমোনিক্স ও উচ্চ কম্পাঙ্কের তীব্র ক্ষয়"
        },
        {
            "id": "sec-fourier-orthogonality",
            "title_bn": "৪. ফুরিয়ার ধারা, উপরিপাত নীতি ও অর্থোগোনালিটি"
        },
        {
            "id": "sec-continuous-fourier-transform",
            "title_bn": "৫. অসীম দণ্ড, ফুরিয়ার রূপান্তর ও গাউসিয়ান কার্নেল"
        },
        {
            "id": "sec-interactive-lab",
            "title_bn": "৬. ইন্টারেক্টিভ ল্যাব: ফুরিয়ার ক্ষয় ও ব্যাপন সিমুলেটর"
        },
        {
            "id": "sec-quizzes",
            "title_bn": "৭. ধারণা যাচাই ও বহুনির্বাচনী কুইজ"
        }
    ],
    "sections": [
        {
            "id": "sec-heat-pde-review",
            "alias": "sec_01_heat_pde_review",
            "number_bn": "১",
            "title_bn": "তাপ সমীকরণ ও সীমানা শর্তের ভৌত তাৎপর্য (The Heat Equation & Boundary Conditions)",
            "quote": {
                "text_bn": "প্রকৃতির গভীর পর্যবেক্ষণই গাণিতিক বিশ্লেষণের সবচেয়ে সমৃদ্ধ ভিত্তি।",
                "author_bn": "জোসেফ ফুরিয়ার"
            },
            "paragraphs": [
                "পূর্ববর্তী অধ্যায়ে আমরা তাপ সমীকরণের ভৌত ও জ্যামিতিক তাৎপর্য আবিষ্কার করেছি। সমীকরণটি ছিল একটি একমাত্রিক ধাতব রডে অবস্থান $x$ এবং সময় $t$-এর ফাংশন হিসেবে তাপমাত্রা $u(x, t)$-এর পরিবর্তনের নিয়ম।",
                "স্থানীয় দ্বিতীয় স্থানিক অন্তরজ $\\frac{\\partial^2 u}{\\partial x^2}$ বক্রতা পরিমাপ করে। যখন কোনো বিন্দুর তাপমাত্রা তার আশপাশের প্রতিবেশী বিন্দুগুলোর গড়ের চেয়ে নিচে অবস্থান করে (হাসিমুখী বা অবতল বক্রতা), তখন দ্বিতীয় ডেরিভেটিভ ধনাত্মক হয় এবং বিন্দুটি উত্তপ্ত হতে শুরু করে। বিপরীতে, উত্তল পাহাড়ের চূড়ার মতো বিন্দুটি প্রতিবেশীদের চেয়ে উষ্ণ হলে তা শীতল হয়ে পড়ে।",
                "কিন্তু বাস্তবে কেবল এই সমীকরণটি কোনো সমাধান নির্দিষ্ট করতে পারে না। বাস্তব জগতে যেকোনো গতিশীল ব্যবস্থাকে সুনির্দিষ্ট করতে আমাদের প্রয়োজন সীমানা শর্ত (Boundary Conditions)। উদাহরণস্বরূপ, $L$ দৈর্ঘ্যের একটি রডের দুই প্রান্ত $x=0$ এবং $x=L$-এ কী ঘটছে? যদি দুই প্রান্তকে নির্দিষ্ট তাপমাত্রায় (যেমন শূন্য ডিগ্রি সেলসিয়াসের বরফে) ডুবিয়ে রাখা হয়, তবে একে বলা হয় ডিরিক্লেট (Dirichlet) সীমানা শর্ত। আর যদি দুই প্রান্তকে নিখুঁত তাপ নিরোধক দিয়ে আবদ্ধ করা হয় যাতে কোনো তাপ ভেতরে প্রবেশ বা বাইরে বের হতে না পারে, তবে প্রান্তে তাপের নতি বা ফ্লাক্স শূন্য হতে হয়—একে বলা হয় নয়ম্যান (Neumann) সীমানা শর্ত।"
            ],
            "formulas": [
                {
                    "latex": "\\frac{\\partial u}{\\partial t} = \\alpha \\frac{\\partial^2 u}{\\partial x^2}, \\quad 0 < x < L, \\; t > 0",
                    "caption_bn": "একমাত্রিক তাপ সমীকরণ যেখানে $\\alpha$ তাপীয় ব্যাপন সহগ।"
                },
                {
                    "latex": "u(0, t) = 0 \\quad \\text{এবং} \\quad u(L, t) = 0 \\quad (\\text{Homogeneous Dirichlet})",
                    "caption_bn": "দুই প্রান্তে স্থির শূন্য তাপমাত্রার সমসত্ত্ব ডিরিক্লেট সীমানা শর্ত।"
                },
                {
                    "latex": "\\left.\\frac{\\partial u}{\\partial x}\\right|_{x=0} = 0 \\quad \\text{এবং} \\quad \\left.\\frac{\\partial u}{\\partial x}\\right|_{x=L} = 0 \\quad (\\text{Insulated Neumann})",
                    "caption_bn": "দুই প্রান্তে তাপীয় প্রবাহহীন নয়ম্যান অন্তরক সীমানা শর্ত।"
                }
            ],
            "callout": {
                "title_bn": "সীমানা শর্তের অপরিসীম গুরুত্ব",
                "text_bn": "আংশিক ডিফারেনশিয়াল সমীকরণের সাধারণ সমাধান অসীম সংখ্যক ফাংশনের একটি বিশাল পরিবার। শুধুমাত্র বাস্তব সীমানা শর্তই মহাবিশ্বের কোটি কোটি সম্ভাবনার মধ্য থেকে একটি মাত্র বাস্তব সমাধানকে বেছে নেয়।"
            },
            "closing_thought_bn": "একটি আংশিক সমীকরণ যার মধ্যে স্থান ও কাল যুগপৎ জড়িয়ে রয়েছে, তাকে কীভাবে আমরা আমাদের পরিচিত সাধারণ ডিফারেনশিয়াল সমীকরণের সাহায্যে সমাধান করতে পারি?"
        },
        {
            "id": "sec-boundary-separation",
            "alias": "sec_02_boundary_separation",
            "number_bn": "২",
            "title_bn": "চলক পৃথকীকরণ পদ্ধতি ও আইগেনমান সমস্যা (Separation of Variables)",
            "paragraphs": [
                "জটিল আংশিক সমীকরণ সমাধানের জন্য জোসেফ ফুরিয়ার গণিত ইতিহাসের সবচেয়ে কার্যকর হাতিয়ারগুলোর একটি প্রবর্তন করেন: চলক পৃথকীকরণ (Separation of Variables)।",
                "আমরা অনুমান করি যে অজ্ঞাত অপেক্ষক $u(x, t)$ স্থানিক ফাংশন $X(x)$ এবং কালিক ফাংশন $T(t)$-এর গুণফল হিসেবে বিচ্ছিন্নযোগ্য: $u(x, t) = X(x) T(t)$। এই অনুমানকে তাপ সমীকরণে বসালে আমরা পাই $X(x) T'(t) = \\alpha X''(x) T(t)$।",
                "উভয়পক্ষকে $\\alpha X(x) T(t)$ দিয়ে ভাগ করলে সমীকরণটি দাঁড়ায় $\\frac{T'(t)}{\\alpha T(t)} = \\frac{X''(x)}{X(x)}$। লক্ষ্য করুন: বামপক্ষটি কেবলমাত্র সময় $t$-এর ফাংশন, আর ডানপক্ষটি কেবলমাত্র অবস্থান $x$-এর ফাংশন। একটি স্বাধীন চলকের ফাংশন অন্য একটি স্বাধীন চলকের ফাংশনের সাথে সর্বদা সমান হতে পারে কেবলমাত্র তখনই, যখন উভয়েই একটি সার্বজনীন ধ্রুবকের সমান হয়! একে আমরা পৃথকীকরণ ধ্রুবক $-\\lambda^2$ হিসেবে চিহ্নিত করি।",
                "এখান থেকে আমরা দুটি পৃথক সাধারণ ডিফারেনশিয়াল সমীকরণ পাই: স্থানিক সমীকরণ $X''(x) + \\lambda^2 X(x) = 0$ এবং কালিক সমীকরণ $T'(t) + \\alpha \\lambda^2 T(t) = 0$। স্থানিক সমীকরণটির সাধারণ সমাধান হলো সাইন ও কোসাইনের সমন্বয়: $X(x) = A \\cos(\\lambda x) + B \\sin(\\lambda x)$। সীমানা শর্ত $X(0) = 0$ প্রয়োগ করলে $A = 0$ হতে বাধ্য হয়; এবং $X(L) = 0$ প্রয়োগ করলে পাওয়া যায় $\\sin(\\lambda L) = 0$।"
            ],
            "formulas": [
                {
                    "latex": "\\frac{T'(t)}{\\alpha T(t)} = \\frac{X''(x)}{X(x)} = -\\lambda^2",
                    "caption_bn": "চলক পৃথকীকরণ অনুপাত এবং আইগেনমান ধ্রুবক $-\\lambda^2$।"
                },
                {
                    "latex": "\\lambda_n = \\frac{n\\pi}{L}, \\quad X_n(x) = \\sin\\left(\\frac{n\\pi x}{L}\\right), \\quad n = 1, 2, 3, \\dots",
                    "caption_bn": "কোয়ান্টায়িত স্থানিক তরঙ্গদৈর্ঘ্য ও অনুমোদিত আইগেনফাংশনসমূহ।"
                }
            ],
            "callout": {
                "title_bn": "কোয়ান্টাম মেকানিক্সের পূর্বাভাস!",
                "text_bn": "একটি সীমাবদ্ধ রডে স্থানিক কম্পাঙ্ক $\\lambda$ যেকোনো সংখ্যা হতে পারে না—সীমানা শর্ত তাকে পূর্ণসংখ্যার গুণিতকে কোয়ান্টায়িত হতে বাধ্য করে। ঠিক এই একই গাণিতিক নীতি এক শতাব্দী পরে শ্রোডিঙ্গার সমীকরণে পরমাণুর শক্তিস্তরের কোয়ান্টাইজেশন ব্যাখ্যা করেছিল!"
            },
            "closing_thought_bn": "অনুমোদিত স্থানিক আকারগুলো হলো স্ট্যান্ডিং সাইন ওয়েভ। কিন্তু সময়ের সাথে সাথে এদের বিস্তার কীভাবে পরিবর্তিত হয়?"
        },
        {
            "id": "sec-sine-harmonics-decay",
            "alias": "sec_03_sine_harmonics_decay",
            "number_bn": "৩",
            "title_bn": "সাইন হারমোনিক্স ও উচ্চ কম্পাঙ্কের তীব্র ক্ষয় (Exponential Decay of Modes)",
            "paragraphs": [
                "স্থানিক আইগেনফাংশন নির্ধারিত হওয়ার পর এবার সময়ের অংশের সমাধান দেখা যাক: $T'(t) = -\\alpha \\lambda_n^2 T(t)$। এটি প্রথম ক্রমের অতি পরিচিত সূচকীয় সমীকরণ, যার সমাধান $T_n(t) = e^{-\\alpha \\lambda_n^2 t} = e^{-\\alpha \\left(\\frac{n\\pi}{L}\\right)^2 t}$।",
                "অতএব, প্রতিটি পূর্ণ সমাধান বা ফান্ডামেন্টাল মোড হলো একটি ক্ষয়িষ্ণু সাইন তরঙ্গ: $u_n(x, t) = e^{-\\alpha \\left(\\frac{n\\pi}{L}\\right)^2 t} \\sin\\left(\\frac{n\\pi x}{L}\\right)$।",
                "এখানেই লুকিয়ে আছে তাপ সমীকরণের সবচেয়ে বৈপ্লবিক পদার্থবিজ্ঞান। সূচকের দিকে তাকান: ক্ষয়ের হার $n^2$-এর সমানুপাতিক! এর অর্থ হলো, $n=1$ (মৌলিক মোড) যে গতিতে ঠান্ডা হয়, $n=2$ মোড তার চেয়ে $2^2 = 4$ গুণ দ্রুত ঠান্ডা হয়; $n=3$ মোড ক্ষয় হয় $3^2 = 9$ গুণ দ্রুত বেগে; আর $n=10$ মোড বিলীন হয় ১০০ গুণ তীব্রতায়!",
                "বাস্তব জীবনে এর চাক্ষুষ অর্থ কী? তাপমাত্রার যেকোনো তীক্ষ্ণ বা খাঁজকাটা পরিবর্তন উচ্চ কম্পাঙ্কের হারমোনিক্স দ্বারা গঠিত। যেহেতু উচ্চ কম্পাঙ্কগুলো প্রায় চোখের পলকে মিলিয়ে যায়, তাই তাপ প্রবাহ যেকোনো আকৃতিকে অবিশ্বাস্য দ্রুততায় মসৃণ করে ফেলে। কিছুক্ষণ অতিবাহিত হলেই সমস্ত সূক্ষ্ম খাঁজ বিলুপ্ত হয়ে কেবল মসৃণতম $n=1$ আর্চটি অবশিষ্ট থাকে।"
            ],
            "formulas": [
                {
                    "latex": "u_n(x, t) = \\exp\\left( -\\alpha \\left(\\frac{n\\pi}{L}\\right)^2 t \\right) \\sin\\left(\\frac{n\\pi x}{L}\\right)",
                    "caption_bn": "$n$-তম মৌলিক তাপীয় মোড ও এর সূচকীয় ক্ষয়।"
                },
                {
                    "latex": "\\tau_n = \\frac{L^2}{\\alpha \\pi^2 n^2} \\implies \\tau_2 = \\frac{1}{4}\\tau_1, \\quad \\tau_3 = \\frac{1}{9}\\tau_1",
                    "caption_bn": "বিভিন্ন হারমোনিক মোডের বৈশিষ্ট্যমূলক আয়ুষ্কাল বা রিলাক্সেশন টাইম।"
                }
            ],
            "callout": {
                "title_bn": "এনট্রপি ও সময়ের একমুখী তীর",
                "text_bn": "উচ্চ কম্পাঙ্কের এই বিস্ফোরক ক্ষয় তথ্য হারানোর নামান্তর। সময়ের সাথে সাথে তাপ উচ্চ কম্পাঙ্কের সমস্ত অতীত স্মৃতি চিরতরে মুছে ফেলে। এ কারণেই অতীতের নিখুঁত অবস্থা পুনরুদ্ধার করা অসম্ভব, যা তাপগতিবিদ্যার দ্বিতীয় সূত্রের মূল ভিত্তি।"
            },
            "closing_thought_bn": "যদি প্রাথমিক তাপমাত্রা কেবল একটি সাইন তরঙ্গ না হয়ে যেকোনো এবড়োখেবড়ো রেখা হয়, তবে তাকে কীভাবে এই মোডগুলোর মাধ্যমে সমাধান করা যায়?"
        },
        {
            "id": "sec-fourier-orthogonality",
            "alias": "sec_04_fourier_orthogonality",
            "number_bn": "৪",
            "title_bn": "ফুরিয়ার ধারা, উপরিপাত নীতি ও অর্থোগোনালিটি (Fourier Series & Orthogonality)",
            "paragraphs": [
                "ধরা যাক, শুরুতে রডের তাপমাত্রা একটি মসৃণ সাইন তরঙ্গ নয়; বরং এক অর্ধেক ফুটন্ত পানিতে এবং অপর অর্ধেক বরফে রাখা ছিল, ফলে কেন্দ্রে একটি খাড়া স্টেপ ফাংশন তৈরি হয়েছে: $u(x, 0) = f(x)$।",
                "জোসেফ ফুরিয়ার ১৮০৭ সালে ঘোষণা করেছিলেন যে যেকোনো ফাংশন $f(x)$-কে অসীম সংখ্যক সাইন তরঙ্গের যোগফল হিসেবে লেখা সম্ভব: $f(x) = \\sum_{n=1}^{\\infty} b_n \\sin\\left(\\frac{n\\pi x}{L}\\right)$। তৎকালীন গণিতের পণ্ডিতরা এই ধারণাকে অবাস্তব বলে উড়িয়ে দিতে চেয়েছিলেন।",
                "কিন্তু ফুরিয়ারের ভিত্তি ছিল সাইন অপেক্ষকের অর্থোগোনালিটি বা লম্বতা সম্পর্ক। রৈখিক বীজগণিতে যেমন দুটি লম্ব ভেক্টরের ডট প্রোডাক্ট শূন্য হয়, তেমনি ফাংশন স্পেসে দুটি ভিন্ন কম্পাঙ্কের সাইন তরঙ্গের গুণফলের ইন্টিগ্রাল শূন্য হয়: $\\int_0^L \\sin\\left(\\frac{n\\pi x}{L}\\right) \\sin\\left(\\frac{m\\pi x}{L}\\right) dx = 0$ (যখন $n \\neq m$), এবং $n=m$ হলে এর মান দাঁড়ায় $L/2$।",
                "এই অর্থোগোনালিটি সমীকরণের উভয়পাশে $\\sin\\left(\\frac{m\\pi x}{L}\\right)$ দিয়ে গুণ করে সমাকলন করলে প্রতিটি সহগ $b_n$ স্পষ্টভাবে বেরিয়ে আসে: $b_n = \\frac{2}{L}\\int_0^L f(x) \\sin\\left(\\frac{n\\pi x}{L}\\right) dx$। যেহেতু তাপ সমীকরণ রৈখিক, তাই সমীকরণের সাধারণ সমাধান হলো প্রতিটি ক্ষয়িষ্ণু মোডের সরাসরি উপরিপাত (Superposition)।"
            ],
            "formulas": [
                {
                    "latex": "\\int_0^L \\sin\\left(\\frac{n\\pi x}{L}\\right) \\sin\\left(\\frac{m\\pi x}{L}\\right) dx = \\begin{cases} 0, & n \\neq m \\\\ \\frac{L}{2}, & n = m \\end{cases}",
                    "caption_bn": "সাইন আইগেনফাংশনসমূহের অর্থোগোনালিটি সম্পর্ক।"
                },
                {
                    "latex": "b_n = \\frac{2}{L}\\int_0^L f(x) \\sin\\left(\\frac{n\\pi x}{L}\\right) dx",
                    "caption_bn": "ফুরিয়ার সাইন ধারার সহগ নির্ণয়ের সূত্র।"
                },
                {
                    "latex": "u(x, t) = \\sum_{n=1}^{\\infty} b_n \\exp\\left( -\\alpha \\left(\\frac{n\\pi}{L}\\right)^2 t \\right) \\sin\\left(\\frac{n\\pi x}{L}\\right)",
                    "caption_bn": "সীমাবদ্ধ দণ্ডে তাপ সমীকরণের পূর্ণ সাধারণ সমাধান।"
                }
            ],
            "callout": {
                "title_bn": "ফাংশন স্পেসে ভিত্তি ভেক্টর",
                "text_bn": "ঠিক যেমন ত্রিমাত্রিক জগতে যেকোনো ভেক্টরকে $\\hat{i}, \\hat{j}, \\hat{k}$ ভিত্তি ভেক্টরের লিনিয়ার কম্বিনেশন হিসেবে প্রকাশ করা যায়, তেমনি অসীম মাত্রিক ফাংশন স্পেসে সাইন তরঙ্গগুলো হলো অর্থোগোনাল ভিত্তি ভেক্টর!"
            },
            "closing_thought_bn": "দণ্ডের দৈর্ঘ্য $L$ যদি ক্রমশ বৃদ্ধি পেয়ে অসীমে চলে যায়, তখন বিচ্ছিন্ন ধারার কী রূপান্তর ঘটে?"
        },
        {
            "id": "sec-continuous-fourier-transform",
            "alias": "sec_05_continuous_fourier_transform",
            "number_bn": "৫",
            "title_bn": "অসীম দণ্ড, ফুরিয়ার রূপান্তর ও গাউসিয়ান কার্নেল (The Fourier Transform & Heat Kernel)",
            "paragraphs": [
                "এবার কল্পনা করুন আমাদের ধাতব দণ্ডটি সীমাবদ্ধ নয়; এটি মাইনাস অসীম থেকে প্লাস অসীম পর্যন্ত বিস্তৃত ($-\\infty < x < \\infty$)।",
                "যখন $L \\to \\infty$, তখন পাশাপাশি দুটি অনুমোদিত কম্পাঙ্কের মধ্যবর্তী দূরত্ব $\\Delta k = \\frac{\\pi}{L} \\to 0$ হয়ে যায়। বিচ্ছিন্ন পূর্ণসংখ্যার যোগফল তখন মসৃণভাবে একটি অবিচ্ছিন্ন সমাকলনে রূপান্তরিত হয়। এখান থেকেই জন্ম নেয় আধুনিক বিজ্ঞানের অন্যতম শ্রেষ্ঠ আবিষ্কার—ফুরিয়ার রূপান্তর (Fourier Transform)।",
                "ফুরিয়ার রূপান্তরের মাধ্যমে আমরা বাস্তব স্থান $x$-এর ফাংশন $f(x)$-কে কম্পাঙ্ক $k$-এর অবিচ্ছিন্ন বর্ণালি $\\hat{f}(k)$-তে রূপান্তর করি। এই রূপান্তরের সবচেয়ে জাদুকরী বৈশিষ্ট্য হলো এটি স্থানিক ডেরিভেটিভকে সাধারণ গুণনে রূপান্তর করে: $\\mathcal{F}\\left\\{\\frac{\\partial^2 u}{\\partial x^2}\\right\\} = -k^2 \\hat{u}(k, t)$। ফলে জটিল আংশিক সমীকরণটি রূপান্তরিত হয় একটি অতি সহজ ওডিই-তে: $\\frac{d\\hat{u}}{dt} = -\\alpha k^2 \\hat{u}$।",
                "ফ্রিকোয়েন্সি স্পেসে সমাধান হলো $\\hat{u}(k, t) = \\hat{u}(k, 0) e^{-\\alpha k^2 t}$। বিপরীত ফুরিয়ার রূপান্তর নিলে দেখা যায়, এটি মূলত প্রাথমিক তাপমাত্রার সাথে একটি প্রসার্য গাউসিয়ান বেল কার্ভের কনভোলিউশন! এই বেল কার্ভটিই হলো তাপ সমীকরণের মৌলিক সমাধান বা হিট কার্নেল (Heat Kernel)। শুরুতে একটি একক বিন্দুতে কেন্দ্রীভূত তাপ সময়ের সাথে সাথে একটি নিখুঁত নরম ঘণ্টার মতো দুই পাশে ছড়িয়ে পড়ে।"
            ],
            "formulas": [
                {
                    "latex": "\\hat{f}(k) = \\int_{-\\infty}^{\\infty} f(x) e^{-i k x} dx, \\quad f(x) = \\frac{1}{2\\pi}\\int_{-\\infty}^{\\infty} \\hat{f}(k) e^{i k x} dk",
                    "caption_bn": "অবিচ্ছিন্ন ফুরিয়ার রূপান্তর ও বিপরীত রূপান্তর জোড়।"
                },
                {
                    "latex": "\\Phi(x, t) = \\frac{1}{\\sqrt{4\\pi\\alpha t}} \\exp\\left( -\\frac{x^2}{4\\alpha t} \\right)",
                    "caption_bn": "একমাত্রিক তাপ সমীকরণের মৌলিক সমাধান (গাউসিয়ান হিট কার্নেল)।"
                },
                {
                    "latex": "u(x, t) = (f * \\Phi)(x, t) = \\int_{-\\infty}^{\\infty} f(y) \\frac{1}{\\sqrt{4\\pi\\alpha t}} e^{-\\frac{(x-y)^2}{4\\alpha t}} dy",
                    "caption_bn": "অসীম ডোমেইনে কনভোলিউশনের মাধ্যমে পূর্ণ সমাধান।"
                }
            ],
            "callout": {
                "title_bn": "ব্রাউনিয়ান গতি ও সম্ভাবনা তত্ত্ব",
                "text_bn": "গাউসিয়ান হিট কার্নেল অবিকল স্বাভাবিক সম্ভাবনা বণ্টনের মতো। এটি কোনো কাকতালীয় বিষয় নয়—অণুদের এলোমেলো ব্রাউনিয়ান গতির সামগ্রিক ম্যাক্রোস্কোপিক রূপই হলো এই তাপ সমীকরণ!"
            },
            "closing_thought_bn": "একটি লোহার রডের তাপ পরিবাহিতা থেকে জন্ম নিয়ে ফুরিয়ার ধারা ও রূপান্তর আজ কোয়ান্টাম বলবিদ্যা, সিগন্যাল প্রসেসিং এবং আধুনিক তথ্যপ্রযুক্তির মেরুদণ্ডে পরিণত হয়েছে।"
        }
    ],
    "quizzes": [
        {
            "id": "quiz-1",
            "question_bn": "১. সমসত্ত্ব ডিরিক্লেট সীমানা শর্তে ($u(0, t) = u(L, t) = 0$) তাপ সমীকরণ সমাধানের সময় স্থানিক সমাধান $X(x)$-এ কোসাইন পদটি ($\\cos(\\lambda x)$) কেন বাদ পড়ে যায়?",
            "correct_index": 1,
            "options": [
                {
                    "text_bn": "কারণ কোসাইন ফাংশন সময়ের সাপেক্ষে ক্ষয়প্রাপ্ত হতে পারে না",
                    "feedback_bn": "ভুল! সময়ের ক্ষয় কালিক সমীকরণ $T(t)$ দ্বারা নির্ধারিত হয়, স্থানিক অপেক্ষকের জন্য নয়।"
                },
                {
                    "text_bn": "কারণ $x=0$ বিন্দুতে $X(0) = A\\cos(0) + B\\sin(0) = A = 0$ হতে হয়, ফলে কোসাইনের সহগ $A$ শূন্য হয়ে যায়",
                    "feedback_bn": "চমৎকার ও সম্পূর্ণ সঠিক! যেহেতু $\\cos(0) = 1$ এবং $\\sin(0) = 0$, তাই বাম প্রান্তের শূন্য সীমানা শর্ত পূরণ করতে হলে কোসাইনের বিস্তার $A$-কে অবশ্যই শূন্য হতে হবে।"
                },
                {
                    "text_bn": "কারণ কোসাইনের দ্বিতীয় ডেরিভেটিভ ঋণাত্মক হতে পারে না",
                    "feedback_bn": "ভুল! সাইন এবং কোসাইন উভয়েরই দ্বিতীয় ডেরিভেটিভ নিজের ঋণাত্মক মানের সমানুপাতিক।"
                },
                {
                    "text_bn": "কারণ ডিরিক্লেট সীমানা শর্তে শুধুমাত্র জোড় কম্পাঙ্কের তরঙ্গ অনুমোদিত",
                    "feedback_bn": "ভুল! ডিরিক্লেট শর্তে সমস্ত পূর্ণসংখ্যা কম্পাঙ্ক ($n=1, 2, 3, \\dots$) সাইন তরঙ্গের আকারে অনুমোদিত।"
                }
            ],
            "explanation_bn": "স্থানিক সমাধান $X(x) = A\\cos(\\lambda x) + B\\sin(\\lambda x)$। বাম প্রান্তের সীমানা শর্ত $X(0) = 0$ বসালে আমরা পাই $A(1) + B(0) = 0 \\implies A = 0$। ফলে কেবল সাইন পদটি অবশিষ্ট থাকে।"
        },
        {
            "id": "quiz-2",
            "question_bn": "২. তাপ সমীকরণ $\\frac{\\partial u}{\\partial t} = \\alpha \\frac{\\partial^2 u}{\\partial x^2}$-এ $n$-তম মোডের ক্ষয় ফ্যাক্টর $e^{-\\alpha \\left(\\frac{n\\pi}{L}\\right)^2 t}$। যদি কম্পাঙ্ক সূচক $n=1$ থেকে বৃদ্ধি পেয়ে $n=3$ হয়, তবে তাপীয় মোডটির ক্ষয়ের গতিবেগ কত গুণ বৃদ্ধি পায়?",
            "correct_index": 2,
            "options": [
                {
                    "text_bn": "৩ গুণ",
                    "feedback_bn": "ভুল! ক্ষয়ের হার কম্পাঙ্কের সমানুপাতিক নয়, বরং বর্গের সমানুপাতিক।"
                },
                {
                    "text_bn": "৬ গুণ",
                    "feedback_bn": "ভুল! এটি দ্বিগুণ বা তিনগুণ বৃদ্ধির সরল সম্পর্ক নয়।"
                },
                {
                    "text_bn": "৯ গুণ",
                    "feedback_bn": "একদম নিখুঁত! সূচকে ক্ষয় হার $\\propto n^2$। তাই $n=3$ হলে ক্ষয়ের তীব্রতা $3^2 = 9$ গুণ বৃদ্ধি পায়!"
                },
                {
                    "text_bn": "২৭ গুণ",
                    "feedback_bn": "ভুল! এটি ঘনকের সমানুপাতিক নয়।"
                }
            ],
            "explanation_bn": "দ্বিতীয় স্থানিক অন্তরজের কারণে দুইবার ব্যবকলনের ফলে স্থানিক কম্পাঙ্ক $\\left(\\frac{n\\pi}{L}\\right)$ বাইরে এসে বর্গাকার রূপ ধারণ করে। ফলে সূচকে ক্ষয় হার $-\\alpha \\lambda_n^2 = -\\alpha \\frac{n^2 \\pi^2}{L^2}$ হয়, যা $n^2$-এর সমানুপাতিক।"
        },
        {
            "id": "quiz-3",
            "question_bn": "৩. সীমাবদ্ধ দণ্ডের ফুরিয়ার ধারা (Fourier Series) থেকে অসীম দণ্ডের অবিচ্ছিন্ন ফুরিয়ার রূপান্তরে (Fourier Transform) উত্তরণের মূল গাণিতিক প্রক্রিয়াটি কী?",
            "correct_index": 0,
            "options": [
                {
                    "text_bn": "দণ্ডের দৈর্ঘ্য $L \\to \\infty$ হওয়ায় পাশাপাশি দুই কম্পাঙ্কের ব্যবধান $\\Delta k = \\frac{\\pi}{L} \\to 0$ হয়, ফলে বিচ্ছিন্ন পদের সামেশন অবিচ্ছিন্ন সমাকলনে ($\\int dk$) রূপান্তরিত হয়",
                    "feedback_bn": "অসাধারণ ও গভীর অন্তর্দৃষ্টিসম্পন্ন উত্তর! দৈর্ঘ্য অসীম হওয়ার সাথে সাথে বিচ্ছিন্ন ফ্রিকোয়েন্সি লাইনগুলো অবিচ্ছিন্ন বর্ণালিতে পরিণত হয় এবং রিমান সামেশন সমাকলনে রূপ নেয়।"
                },
                {
                    "text_bn": "তাপ সমীকরণটি রৈখিক থেকে অরৈখিক সমীকরণে পরিবর্তিত হয়",
                    "feedback_bn": "ভুল! তাপ সমীকরণ সব সময়ই একটি রৈখিক ডিফারেনশিয়াল সমীকরণ।"
                },
                {
                    "text_bn": "শুধুমাত্র সময়ের ডেরিভেটিভ বাদ দিয়ে স্থানিক ডেরিভেটিভকে শূন্য ধরা হয়",
                    "feedback_bn": "ভুল! এটি স্টেডি-স্টেট ল্যাপ্লাস সমীকরণ নয়, এখানে তাপ গতিশীলভাবে ছড়ায়।"
                },
                {
                    "text_bn": "সাইন এবং কোসাইন তরঙ্গগুলো পলিনোমিয়ালে রূপান্তরিত হয়",
                    "feedback_bn": "ভুল! ফুরিয়ার রূপান্তরে সাইন-কোসাইন অবিচ্ছিন্ন জটিল সূচকীয় তরঙ্গ $e^{-ikx}$-এ রূপ নেয়।"
                }
            ],
            "explanation_bn": "যখন ব্যবধির দৈর্ঘ্য $L$ অসীমের দিকে ধাবিত হয়, তখন বিচ্ছিন্ন ফুরিয়ার ধারার প্রতিটি মোডের মধ্যবর্তী ব্যবধান $\\Delta k = \\pi/L$ শূন্যের দিকে পৌঁছায়। ফলে ধারার যোগফল অবিচ্ছিন্ন ইন্টিগ্রালে রূপ নেয়, যা ফুরিয়ার রূপান্তরের জন্ম দেয়।"
        }
    ],
    "interactive_components": [
        {
            "id": "heat-diffusion-fourier-lab",
            "title_bn": "ইন্টারেক্টিভ ল্যাব: ফুরিয়ার হারমোনিক্স ও তাপীয় ব্যাপন সিমুলেটর",
            "type": "heat_equation_canvas",
            "parameters": [
                {
                    "name": "initial_condition",
                    "label_bn": "প্রাথমিক তাপমাত্রার প্রোফাইল",
                    "type": "select",
                    "options": [
                        { "value": "step", "label_bn": "স্টেপ ফাংশন (অর্ধেক উষ্ণ, অর্ধেক বরফ)" },
                        { "value": "triangle", "label_bn": "ত্রিভুজাকার তাপীয় শিখা (Triangular Peak)" },
                        { "value": "single_sine", "label_bn": "মৌলিক সাইন মোড (n = 1)" },
                        { "value": "high_harmonic", "label_bn": "উচ্চ কম্পাঙ্ক মিশ্রণ (n = 1, 3, 5)" }
                    ],
                    "default": "step"
                },
                {
                    "name": "diffusivity",
                    "label_bn": "তাপীয় ব্যাপন সহগ α",
                    "min": 0.02,
                    "max": 0.4,
                    "default": 0.1,
                    "step": 0.01
                },
                {
                    "name": "fourier_terms",
                    "label_bn": "ফুরিয়ার ধারার পদ সংখ্যা (N)",
                    "min": 1,
                    "max": 40,
                    "default": 12,
                    "step": 1
                },
                {
                    "name": "boundary_type",
                    "label_bn": "সীমানা শর্তের ধরন",
                    "type": "select",
                    "options": [
                        { "value": "dirichlet", "label_bn": "দুই প্রান্তে শূন্য তাপমাত্রা (Dirichlet)" },
                        { "value": "neumann", "label_bn": "দুই প্রান্ত তাপ নিরোধক দিয়ে মোড়ানো (Neumann)" }
                    ],
                    "default": "dirichlet"
                }
            ],
            "metrics": [
                {
                    "id": "elapsed_time",
                    "label_bn": "অতিক্রান্ত সময় t",
                    "unit": "s"
                },
                {
                    "id": "max_temperature",
                    "label_bn": "সর্বোচ্চ তাপমাত্রা u_max",
                    "unit": "°C"
                },
                {
                    "id": "decay_ratio",
                    "label_bn": "উচ্চ কম্পাঙ্ক ক্ষয় শতাংশ (High Frequency Dissipation)",
                    "unit": "%"
                }
            ],
            "description_bn": "সিমুলেটরে লক্ষ্য করুন কীভাবে প্রাথমিক খাঁজকাটা ফাংশন ফুরিয়ার সাইন ধারার মাধ্যমে গঠিত হয় এবং সময় অতিবাহিত হওয়ার সাথে সাথে কীভাবে উচ্চ কম্পাঙ্কগুলো সবার আগে মিলিয়ে গিয়ে একটি নিখুঁত মসৃণ বক্ররেখায় পরিণত হয়।"
        }
    ],
    "key_formulas": [
        {
            "name_bn": "একমাত্রিক তাপ ব্যাপন সমীকরণ (1D Heat PDE)",
            "latex": "\\frac{\\partial u}{\\partial t} = \\alpha \\frac{\\partial^2 u}{\\partial x^2}"
        },
        {
            "name_bn": "চলক পৃথকীকরণ রূপ (Separation of Variables)",
            "latex": "u(x, t) = X(x)T(t) \\implies \\frac{T'(t)}{\\alpha T(t)} = \\frac{X''(x)}{X(x)} = -\\lambda^2"
        },
        {
            "name_bn": "কোয়ান্টায়িত স্থানিক আইগেনফাংশন ও আইগেনমান",
            "latex": "X_n(x) = \\sin\\left(\\frac{n\\pi x}{L}\\right), \\quad \\lambda_n = \\frac{n\\pi}{L}, \\quad n \\in \\mathbb{N}"
        },
        {
            "name_bn": "একক হারমোনিক মোডের সূচকীয় ক্ষয়",
            "latex": "u_n(x, t) = \\exp\\left( -\\alpha \\left(\\frac{n\\pi}{L}\\right)^2 t \\right) \\sin\\left(\\frac{n\\pi x}{L}\\right)"
        },
        {
            "name_bn": "ফুরিয়ার সাইন ধারা বিস্তৃতি ও সহগ",
            "latex": "f(x) = \\sum_{n=1}^{\\infty} b_n \\sin\\left(\\frac{n\\pi x}{L}\\right), \\quad b_n = \\frac{2}{L}\\int_0^L f(x)\\sin\\left(\\frac{n\\pi x}{L}\\right)dx"
        },
        {
            "name_bn": "পূর্ণ সাধারণ সমাধান (General Solution)",
            "latex": "u(x, t) = \\sum_{n=1}^{\\infty} b_n e^{-\\alpha \\left(\\frac{n\\pi}{L}\\right)^2 t} \\sin\\left(\\frac{n\\pi x}{L}\\right)"
        },
        {
            "name_bn": "অবিচ্ছিন্ন ফুরিয়ার রূপান্তর (Continuous Fourier Transform)",
            "latex": "\\hat{f}(k) = \\int_{-\\infty}^{\\infty} f(x) e^{-i k x} dx"
        },
        {
            "name_bn": "মৌলিক গাউসিয়ান তাপীয় কার্নেল (Heat Kernel)",
            "latex": "\\Phi(x, t) = \\frac{1}{\\sqrt{4\\pi\\alpha t}} \\exp\\left( -\\frac{x^2}{4\\alpha t} \\right)"
        }
    ],
    "glossary": [
        {
            "term_en": "Dirichlet Boundary Condition",
            "term_bn": "ডিরিক্লেট সীমানা শর্ত",
            "definition_bn": "সীমানা শর্তের এমন রূপ যেখানে ডোমেইনের প্রান্তে ফাংশনের মান সরাসরি নির্দিষ্ট করে দেওয়া হয় (যেমন দুই প্রান্তে শূন্য ডিগ্রি তাপমাত্রা)।"
        },
        {
            "term_en": "Neumann Boundary Condition",
            "term_bn": "নয়ম্যান সীমানা শর্ত",
            "definition_bn": "সীমানা শর্ত যেখানে প্রান্তে ফাংশনের স্বাভাবিক অন্তরজ বা ফ্লাক্স নির্দিষ্ট করা হয় (যেমন রডের অন্তরক প্রান্তে তাপের প্রবাহ শূন্য)।"
        },
        {
            "term_en": "Separation of Variables",
            "term_bn": "চলক পৃথকীকরণ",
            "definition_bn": "আংশিক ডিফারেনশিয়াল সমীকরণ সমাধানের একটি ক্লাসিক্যাল পদ্ধতি যেখানে অজ্ঞাত ফাংশনকে একাধিক স্বাধীন চলকের পৃথক ফাংশনের গুণফল ধরা হয়।"
        },
        {
            "term_en": "Orthogonality",
            "term_bn": "অর্থোগোনালিটি বা পারস্পরিক লম্বতা",
            "definition_bn": "একটি নির্দিষ্ট ব্যবধিতে দুটি ভিন্ন ফাংশনের গুণফলের নির্দিষ্ট সমাকলন শূন্য হওয়ার গাণিতিক বৈশিষ্ট্য।"
        },
        {
            "term_en": "Fourier Transform",
            "term_bn": "ফুরিয়ার রূপান্তর",
            "definition_bn": "একটি অসীম ডোমেইনে অবস্থিত ফাংশনকে অবিচ্ছিন্ন কম্পাঙ্কের সাইন ও কোসাইন তরঙ্গের সমাহারে বিশ্লিষ্ট করার রূপান্তর।"
        },
        {
            "term_en": "Heat Kernel (Fundamental Solution)",
            "term_bn": "তাপীয় কার্নেল (মৌলিক সমাধান)",
            "definition_bn": "অসীম ডোমেইনে তাপ সমীকরণের গ্রিন্স ফাংশন, যা একটি বিন্দুতে থাকা তাপীয় শক্তির সময়ের সাথে সাথে গাউসিয়ান বেল কার্ভে বিস্তারের রূপ।"
        }
    ]
}

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(lesson_05_data, f, ensure_ascii=False, indent=2)

print(f"Single-shell Lesson 05 Data JSON written to {DATA_FILE}.")

