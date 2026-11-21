# -*- coding: utf-8 -*-
"""
Generator script for 3Blue1Brown Calculus Lesson 09:
"What does area have to do with slope?" / "ক্ষেত্রফলের সাথে ঢালের কী সম্পর্ক?"
"""

import os
import json

base_dir = os.path.abspath(r"departments/learning_paths/stem_mathematics/3blue1brown_courses")

script_dir = os.path.join(base_dir, r"essence_of_calculus/lesson_09_area_slope/dubbing_pipeline")
audio_dir = os.path.join(base_dir, r"web_platform/assets/audio/calculus/lesson_09")
data_dir = os.path.join(base_dir, r"web_platform/data/calculus")

os.makedirs(script_dir, exist_ok=True)
os.makedirs(audio_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

# -------------------------------------------------------------------------
# 1. BENGALI MASTER SCRIPT (dubbing_pipeline/3b1b_calculus_l09_bangla_master_script.json)
# -------------------------------------------------------------------------
master_script_cues = [
    {
        "id": 1,
        "start": 0.0,
        "end": 8.5,
        "duration": 8.5,
        "en": "At first glance, finding the area under a curve and finding the slope of a curve seem like completely unrelated problems.",
        "bn": "প্রথম দেখায় মনে হতে পারে, একটি বক্ররেখার নিচের ক্ষেত্রফল নির্ণয় করা এবং কোনো বক্ররেখার স্পর্শক ঢাল নির্ণয় করা সম্পূর্ণ ভিন্ন দুটি জ্যামিতিক সমস্যা।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 2,
        "start": 8.8,
        "end": 18.2,
        "duration": 9.4,
        "en": "On the one hand, finding a slope is about zooming in on a tiny neighborhood of a single point to see the local rate of change.",
        "bn": "একদিকে ঢাল বা অন্তরীকরণ হলো একটি নির্দিষ্ট বিন্দুর অতি ক্ষুদ্র প্রতিবেশে জুম করে পরিবর্তনের তাৎক্ষণিক স্থানীয় হার প্রত্যক্ষ করা।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 3,
        "start": 18.5,
        "end": 28.5,
        "duration": 10.0,
        "en": "On the other hand, finding an area is about slicing up a whole region into infinitely many thin rectangles and adding them all up.",
        "bn": "অন্যদিকে ক্ষেত্রফল বা সমাকলন হলো একটি সম্পূর্ণ অঞ্চলকে অসীম সংখ্যক সরু আয়তক্ষেত্রে চিরে টুকরো টুকরো করে তাদের সবগুলোকে একসাথে যোগ করা।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 4,
        "start": 29.0,
        "end": 39.5,
        "duration": 10.5,
        "en": "Yet, these two operations are intimately connected. In fact, they are exact inverses of each other.",
        "bn": "তা সত্ত্বেও, এই দুটি প্রক্রিয়া একে অপরের সাথে অত্যন্ত গভীরভাবে জড়িত। বাস্তবিক অর্থে, তারা পরস্পরের নিখুঁত বিপরীত বা বিপরীতমুখী অপারেশন।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 5,
        "start": 40.0,
        "end": 50.8,
        "duration": 10.8,
        "en": "This deep connection is known as the Fundamental Theorem of Calculus, and our goal here is to make it feel completely natural.",
        "bn": "এই গভীর সংযোগটিই হলো ক্যালকুলাসের মৌলিক উপপাদ্য, বা ফান্ডামেন্টাল থিওরেম অফ ক্যালকুলাস। আর আমাদের আজকের লক্ষ্য হলো একে একদম স্বাভাবিক ও সহজাত করে তোলা।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 6,
        "start": 51.5,
        "end": 62.0,
        "duration": 10.5,
        "en": "To see why this inverse relationship holds, let's define what you might call an accumulation function, or an area function, A(x).",
        "bn": "এই বিপরীত সম্পর্কটি কেন ঘটে তা বুঝতে, চলুন আমরা একটি সঞ্চয়ন ফাংশন বা ক্ষেত্রফল ফাংশন এ অফ এক্স সংজ্ঞায়িত করি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 7,
        "start": 62.5,
        "end": 74.0,
        "duration": 11.5,
        "en": "Suppose you have some graph, y equals f of t. Think of t as moving along the horizontal axis, starting at 0 and going up to some value x.",
        "bn": "ধরা যাক আমাদের কাছে একটি লেখচিত্র আছে, ওয়াই সমান এফ অফ টি। কল্পনা করুন অনুভূমিক অক্ষ বরাবর টি শূন্য থেকে শুরু করে একটি নির্দিষ্ট মান এক্স পর্যন্ত অগ্রসর হচ্ছে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 8,
        "start": 74.5,
        "end": 86.5,
        "duration": 12.0,
        "en": "The function A(x) represents the total area under that curve between 0 and x. As x moves to the right, that area grows.",
        "bn": "এ অফ এক্স ফাংশনটি শূন্য থেকে এক্স সীমার মধ্যে বক্ররেখার নিচের মোট ক্ষেত্রফল নির্দেশ করে। এক্স যত ডানে সরবে, এই ক্ষেত্রফল ততই পুঞ্জীভূত হয়ে বৃদ্ধি পাবে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 9,
        "start": 87.0,
        "end": 97.5,
        "duration": 10.5,
        "en": "Now ask yourself the central question of calculus: what is the derivative of this area function? That is, what is dA divided by dx?",
        "bn": "এবার নিজেকে ক্যালকুলাসের সেই মূল প্রশ্নটি করুন: এই ক্ষেত্রফল ফাংশনের ডেরিভেটিভ বা অন্তরজ কী হবে? অর্থাৎ ডিএ ভাগ ডিএক্স এর মান কত?",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 10,
        "start": 98.0,
        "end": 109.2,
        "duration": 11.2,
        "en": "Remember what a derivative means. You nudge the input x by a tiny amount, dx, and you observe the resulting change in the output, dA.",
        "bn": "মনে করে দেখুন অন্তরজের জ্যামিতিক অর্থ কী। ইনপুট এক্সকে অতি ক্ষুদ্র পরিমাণ ডিএক্স নাড়া বা ধাক্কা দিলে আউটপুটে যে পরিবর্তন ডিএ ঘটে, তারই অনুপাত হলো ডেরিভেটিভ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 11,
        "start": 109.8,
        "end": 121.5,
        "duration": 11.7,
        "en": "Geometrically, what does that change in area, dA, look like on our graph? It's a thin sliver of area added to the right edge of the shape.",
        "bn": "জ্যামিতিকভাবে আমাদের লেখচিত্রে ক্ষেত্রফলের এই পরিবর্তন ডিএ দেখতে কেমন হবে? এটি ক্ষেত্রটির ডান প্রান্তে যুক্ত হওয়া একটি অত্যন্ত সরু ফালি বা স্লাইস।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 12,
        "start": 122.0,
        "end": 133.0,
        "duration": 11.0,
        "en": "How wide is this sliver? Its width is exactly dx, the little nudge that we gave to x.",
        "bn": "এই সরু ফালিটি কতটা চওড়া? এর প্রস্থ ঠিক ডিএক্স পরিমাণ, ঠিক যতটা আমরা এক্স ইনপুটকে ডানদিকে সরিয়েছিলাম।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 13,
        "start": 133.5,
        "end": 145.0,
        "duration": 11.5,
        "en": "And how tall is it? Well, its height is almost completely constant across that tiny width, and that height is simply f(x), the value of the function.",
        "bn": "আর এর উচ্চতা কত? এই অতি ক্ষুদ্র প্রস্থ জুড়ে এর উচ্চতা প্রায় পুরোপুরি স্থির থাকে, এবং সেই উচ্চতা আর কিছুই নয়—সরাসরি ফাংশনটির উচ্চতা এফ অফ এক্স!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 14,
        "start": 145.5,
        "end": 157.0,
        "duration": 11.5,
        "en": "Sure, there is a tiny curved region on top, but that little cap has an area proportional to dx squared, which vanishes to zero as dx shrinks.",
        "bn": "অবশ্যই ওপরে একটি অতি ক্ষুদ্র বাঁকানো চূড়া রয়েছে, কিন্তু সেই ক্ষুদ্র অংশের ক্ষেত্রফল ডিএক্স স্কয়ারের সমানুপাতিক, যা ডিএক্স সংকুচিত হওয়ার সাথে সাথে নিমেষেই মিলিয়ে যায়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 15,
        "start": 157.5,
        "end": 169.5,
        "duration": 12.0,
        "en": "So to first order, the change in area dA is approximately the height f(x) times the width dx: dA is about f(x) times dx.",
        "bn": "কাজেই প্রথম ক্রমের নিখুঁত হিসেবে, ক্ষেত্রফলের বৃদ্ধি ডিএ হলো উচ্চতা এফ অফ এক্স এবং প্রস্থ ডিএক্সের গুণফল: ডিএ সমান প্রায় এফ অফ এক্স গুণ ডিএক্স।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 16,
        "start": 170.0,
        "end": 182.2,
        "duration": 12.2,
        "en": "Now divide both sides by dx: dA divided by dx equals f(x). Pause and reflect on that for a moment, because this is the big reveal.",
        "bn": "এবার উভয় পক্ষকে ডিএক্স দিয়ে ভাগ করুন: ডিএ ভাগ ডিএক্স সমান এফ অফ এক্স! একটু থেমে এই সমীকরণটির দিকে গভীর দৃষ্টিতে তাকান, কারণ এটিই ক্যালকুলাসের সবচেয়ে বড় চমক!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 17,
        "start": 182.8,
        "end": 194.0,
        "duration": 11.2,
        "en": "The derivative of the area function is simply the height of the original curve! The rate at which area accumulates is literally the function itself.",
        "bn": "ক্ষেত্রফল ফাংশনের ঢাল বা অন্তরজ হলো মূল বক্ররেখার তাৎক্ষণিক উচ্চতা! যে হারে ক্ষেত্রফল পুঞ্জীভূত বা সঞ্চিত হয়, তা সরাসরি ওই ফাংশনের মানেরই সমান।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 18,
        "start": 194.5,
        "end": 206.5,
        "duration": 12.0,
        "en": "This tells us that finding the area under a curve is equivalent to finding a function whose derivative is the curve you're looking at.",
        "bn": "এটি আমাদের দ্ব্যর্থহীনভাবে জানিয়ে দেয়: কোনো বক্ররেখার নিচের ক্ষেত্রফল খোঁজা মানে এমন একটি ফাংশন খুঁজে বের করা, যার অন্তরজ হলো সেই মূল বক্ররেখাটি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 19,
        "start": 207.0,
        "end": 218.5,
        "duration": 11.5,
        "en": "In other words, integration is the inverse operation of differentiation. An integral is an antiderivative.",
        "bn": "অন্য কথায়, সমাকলন বা ইন্টিগ্রেশন হলো অবকলন বা ডিফারেনসিয়েশনের বিপরীত প্রক্রিয়া। একটি ইন্টিগ্রাল হলো মূলত একটি অ্যান্টিডেরিভেটিভ বা বিপরীত অন্তরজ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 20,
        "start": 219.0,
        "end": 230.5,
        "duration": 11.5,
        "en": "Let's put this into practice with a concrete example. Suppose f(x) is x squared, and we want to find the area under the parabola from 0 to x.",
        "bn": "চলুন একটি বাস্তব উদাহরণের মাধ্যমে এটি যাচাই করা যাক। ধরা যাক এফ অফ এক্স সমান এক্স স্কয়ার, এবং আমরা শূন্য থেকে এক্স পর্যন্ত এই প্যারাবোলার নিচের ক্ষেত্রফল বের করতে চাই।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 21,
        "start": 231.0,
        "end": 242.0,
        "duration": 11.0,
        "en": "Instead of painfully summing up infinitely many rectangles, we just ask: what function has a derivative equal to x squared?",
        "bn": "অসীম সংখ্যক আয়তক্ষেত্রের ক্ষেত্রফল কষ্ট করে যোগ না করে, আমরা কেবল প্রশ্ন করি: কোন ফাংশনের অন্তরজ নিলে এক্স স্কয়ার পাওয়া যায়?",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 22,
        "start": 242.5,
        "end": 254.0,
        "duration": 11.5,
        "en": "Well, we know the power rule: the derivative of x cubed is 3 times x squared. So the derivative of one-third x cubed is exactly x squared.",
        "bn": "পাওয়ার রুল থেকে আমরা জানি: এক্স কিউবের ডেরিভেটিভ হলো থ্রি এক্স স্কয়ার। কাজেই এক-তৃতীয়াংশ এক্স কিউবের ডেরিভেটিভ হবে ঠিক এক্স স্কয়ার!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 23,
        "start": 254.5,
        "end": 266.0,
        "duration": 11.5,
        "en": "Therefore, our area function A(x) must be one-third x cubed! Just like that, an impossible summation problem turns into a simple algebraic antiderivative.",
        "bn": "সুতরাং আমাদের ক্ষেত্রফল ফাংশন এ অফ এক্স অবশ্যই এক-তৃতীয়াংশ এক্স কিউব হবে! চোখের পলকে একটি দুরূহ যোগের সমস্যা সহজ বীজগণিতীয় অ্যান্টিডেরিভেটিভে রূপ নিল।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 24,
        "start": 266.5,
        "end": 278.2,
        "duration": 11.7,
        "en": "Now what if you don't start at 0? What if you want the area between some starting point a and an ending point b?",
        "bn": "কিন্তু যদি আপনার যাত্রা শূন্য থেকে শুরু না হয়ে যেকোনো সাধারণ শুরুর বিন্দু এ থেকে শেষ বিন্দু বি পর্যন্ত হয়, তবে ক্ষেত্রফল কীভাবে হিসেব করবেন?",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 25,
        "start": 278.8,
        "end": 290.0,
        "duration": 11.2,
        "en": "Well, the area from a to b is just the total area from 0 to b, minus the area from 0 to a: that is, A(b) minus A(a).",
        "bn": "এ থেকে বি পর্যন্ত ক্ষেত্রফল হলো শূন্য থেকে বি পর্যন্ত মোট ক্ষেত্রফল থেকে শূন্য থেকে এ পর্যন্ত ক্ষেত্রফলের সাধারণ বিয়োগফল: অর্থাৎ এ অফ বি বিয়োগ এ অফ এ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 26,
        "start": 290.5,
        "end": 302.0,
        "duration": 11.5,
        "en": "If capital F(x) is any antiderivative of f(x), then A(x) equals F(x) plus some constant C. When you subtract, that constant cancels out completely.",
        "bn": "যদি ক্যাপিটাল এফ অফ এক্স ফাংশনটি স্মল এফের যেকোনো অ্যান্টিডেরিভেটিভ হয়, তবে বিয়োগ করার সময় ধ্রুবক সি সম্পূর্ণ কেটে গিয়ে বিলুপ্ত হয়ে যায়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 27,
        "start": 302.5,
        "end": 314.5,
        "duration": 12.0,
        "en": "Leaving us with the famous formula: the integral from a to b of f(x) dx equals F(b) minus F(a).",
        "bn": "ফলে আমরা পাই ইতিহাসের সেই অবিস্মরণীয় সূত্র: এ থেকে বি সীমায় স্মল এফ অফ এক্স ডিএক্সের সমাকলন সমান ক্যাপিটাল এফ অফ বি বিয়োগ ক্যাপিটাল এফ অফ এ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 28,
        "start": 315.0,
        "end": 326.5,
        "duration": 11.5,
        "en": "To make this even more intuitive and grounded in the physical world, let's look at velocity and distance.",
        "bn": "এই সত্যটিকে বাস্তব পৃথিবীর সাথে আরও দৃঢ়ভাবে যুক্ত করতে এবং আরও হৃদয়ঙ্গম করতে, চলুন বেগ ও দূরত্বের উদাহরণের দিকে তাকানো যাক।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 29,
        "start": 327.0,
        "end": 339.0,
        "duration": 12.0,
        "en": "Imagine driving a car whose speed varies continuously over time, described by a velocity function v(t).",
        "bn": "কল্পনা করুন আপনি এমন একটি গাড়ি চালাচ্ছেন যার গতি সময়ের সাথে সাথে অবিরত পরিবর্তিত হচ্ছে, যা ভি অফ টি বেগ ফাংশন দ্বারা বর্ণিত।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 30,
        "start": 339.5,
        "end": 351.0,
        "duration": 11.5,
        "en": "If velocity were constant, distance would just be velocity multiplied by time: distance equals rate times time.",
        "bn": "বেগ যদি সবসময় ধ্রুবক থাকত, তবে অতিক্রান্ত দূরত্ব হতো কেবল বেগ গুণ সময়: দূরত্ব সমান বেগ গুণ সময়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 31,
        "start": 351.5,
        "end": 363.0,
        "duration": 11.5,
        "en": "On a graph of velocity against time, that product, velocity times time, is represented visually as the area of a rectangle.",
        "bn": "সময়ের বিপরীতে বেগের একটি লেখচিত্রে বেগ এবং সময়ের গুণফলটি জ্যামিতিকভাবে একটি আয়তক্ষেত্রের ক্ষেত্রফল হিসেবে ফুটে ওঠে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 32,
        "start": 363.5,
        "end": 375.0,
        "duration": 11.5,
        "en": "When velocity changes continuously, we chop the trip into tiny intervals of time, dt. During each tiny slice, velocity is virtually constant, v(t).",
        "bn": "কিন্তু বেগ যখন অবিরাম পরিবর্তিত হয়, তখন আমরা ভ্রমণটিকে অতি ক্ষুদ্র ক্ষুদ্র সময় ব্যবধান ডিটিতে বিভক্ত করি। প্রতিটি ডিটি সময়ে বেগ প্রায় ধ্রুবক ভি অফ টি থাকে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 33,
        "start": 375.5,
        "end": 387.5,
        "duration": 12.0,
        "en": "So the tiny distance traveled during that moment is ds, which equals v(t) times dt. That is the area of a single microscopic vertical strip.",
        "bn": "ফলে সেই অতি ক্ষুদ্র মুহূর্তে অতিক্রান্ত দূরত্ব ডিএস সমান ভি অফ টি গুণ ডিটি। এটি মূলত লেখচিত্রের একটি অতি সূক্ষ্ম উল্লম্ব ফালির ক্ষেত্রফল।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 34,
        "start": 388.0,
        "end": 400.0,
        "duration": 12.0,
        "en": "Summing up all those tiny distances, ds, gives the total distance s(t). But summing up all those strips is also the area under the velocity curve!",
        "bn": "এই প্রতিটি ক্ষুদ্র দূরত্ব ডিএস যোগ করলে যেমন মোট দূরত্ব এস অফ টি পাওয়া যায়, ঠিক তেমনি প্রতিটি ফালির ক্ষেত্রফল যোগ করলে বেগের লেখচিত্রের নিচের মোট ক্ষেত্রফল পাওয়া যায়!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 35,
        "start": 400.5,
        "end": 412.0,
        "duration": 11.5,
        "en": "Meanwhile, from our very first lessons on derivatives, we know that velocity is the derivative of distance: v(t) equals ds divided by dt.",
        "bn": "একই সাথে, অন্তরীকরণের প্রথম পাঠ থেকেই আমরা জানি যে বেগ হলো দূরত্বের অন্তরজ: অর্থাৎ ভি অফ টি সমান ডিএস ভাগ ডিটি।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 36,
        "start": 412.5,
        "end": 424.5,
        "duration": 12.0,
        "en": "So distance s(t) is a function whose derivative is v(t), and distance is also the area under the curve of v(t).",
        "bn": "অতএব দূরত্ব এস অফ টি এমন একটি ফাংশন যার ডেরিভেটিভ হলো বেগ ভি অফ টি, আবার দূরত্ব নিজেই হলো ভি অফ টি লেখচিত্রের নিচের ক্ষেত্রফল!",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 37,
        "start": 425.0,
        "end": 437.0,
        "duration": 12.0,
        "en": "There it is again: the total accumulated change is computed by taking the antiderivative and evaluating the endpoints: s(b) minus s(a).",
        "bn": "দেখুন একই সত্য আবারও স্পষ্ট হয়ে উঠল: মোট পুঞ্জীভূত পরিবর্তন হিসাব করা হয় অ্যান্টিডেরিভেটিভ নিয়ে প্রান্তবিন্দু দুটির মান বিয়োগের মাধ্যমে: এস অফ বি বিয়োগ এস অফ এ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 38,
        "start": 437.5,
        "end": 449.0,
        "duration": 11.5,
        "en": "Now, what happens if the curve dips below the horizontal axis, where f(x) is negative?",
        "bn": "এখন প্রশ্ন হলো, যদি বক্ররেখাটি অনুভূমিক এক্স অক্ষের নিচে নেমে যায়, যেখানে এফ অফ এক্স ঋণাত্মক, তখন কী ঘটবে?",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 39,
        "start": 449.5,
        "end": 461.5,
        "duration": 12.0,
        "en": "In that region, the height f(x) is negative, so the product f(x) times dx is also negative. The integral counts this as negative area.",
        "bn": "সেই অঞ্চলে উচ্চতা এফ অফ এক্স ঋণাত্মক হওয়ায় উচ্চতা ও ডিএক্সের গুণফলটিও ঋণাত্মক হয়ে যায়। ইন্টিগ্রাল একে চিহ্নযুক্ত ঋণাত্মক ক্ষেত্রফল হিসেবে গণ্য করে।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 40,
        "start": 462.0,
        "end": 473.5,
        "duration": 11.5,
        "en": "Physically, in our car example, negative velocity means driving in reverse, which decreases your total displacement from the origin.",
        "bn": "ভৌতভাবে গাড়ির উদাহরণে ঋণাত্মক বেগ মানে হলো গাড়িটি পেছনের দিকে ব্যাক করছে, যার ফলে শুরুর অবস্থান থেকে নিট সরণ কমে যায়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 41,
        "start": 474.0,
        "end": 486.0,
        "duration": 12.0,
        "en": "So a definite integral always computes the net signed area, or the net accumulated change between two bounds.",
        "bn": "সুতরাং একটি নির্দিষ্ট যোগজ বা ডেফিনিট ইন্টিগ্রাল সর্বদাই দুটি সীমার মধ্যে নিট চিহ্নযুক্ত ক্ষেত্রফল বা পুঞ্জীভূত মোট পরিবর্তনের হিসাব দেয়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 42,
        "start": 486.5,
        "end": 498.0,
        "duration": 11.5,
        "en": "Another beautiful perspective is the average value of a function over an interval from a to b.",
        "bn": "আরেকটি চমকপ্রদ দৃষ্টিভঙ্গি হলো এ থেকে বি ব্যবধিতে একটি পরিবর্তনশীল ফাংশনের গড় মান বা এভারেজ ভ্যালু নির্ণয়।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 43,
        "start": 498.5,
        "end": 510.5,
        "duration": 12.0,
        "en": "If you take the total area under the curve and divide it by the length of the interval, b minus a, you get a single constant height.",
        "bn": "আপনি যদি বক্ররেখার নিচের মোট ক্ষেত্রফলকে ব্যবধির মোট দৈর্ঘ্য বি বিয়োগ এ দিয়ে ভাগ করেন, তবে আপনি একটি সমতল বা ধ্রুবক উচ্চতা পাবেন।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 44,
        "start": 511.0,
        "end": 523.0,
        "duration": 12.0,
        "en": "This constant height creates a rectangle with the exact same area as the original curvy shape. That height is the true average value of f(x).",
        "bn": "এই ধ্রুবক উচ্চতাটি মূল অসম বাঁকানো আকারের অবিকল সমান ক্ষেত্রফলবিশিষ্ট একটি একক আয়তক্ষেত্র গঠন করে। এই উচ্চতাই হলো ফাংশনটির আসল গড় মান।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 45,
        "start": 523.5,
        "end": 535.5,
        "duration": 12.0,
        "en": "So whether you think of integration as summing up tiny slices or as the inverse of taking a derivative, they are two sides of the exact same coin.",
        "bn": "সুতরাং আপনি সমাকলনকে অতি ক্ষুদ্র ফালির যোগফল হিসেবে ভাবুন কিংবা অবকলনের বিপরীত অপারেশন হিসেবে দেখুন—তারা মূলত একই মুদ্রার এপিঠ-ওপিঠ।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    },
    {
        "id": 46,
        "start": 536.0,
        "end": 548.0,
        "duration": 12.0,
        "en": "Slope measures local rate of change; area accumulates that rate back into the total change. That is the fundamental heartbeat of calculus.",
        "bn": "ঢাল পরিমাপ করে পরিবর্তনের তাৎক্ষণিক স্থানীয় হার, আর ক্ষেত্রফল সেই হারকে পুঞ্জীভূত করে ফিরিয়ে দেয় সামগ্রিক পরিবর্তন। এটিই ক্যালকুলাসের অমূল্য হৃদস্পন্দন।",
        "voice": "bn-BD-PradeepNeural",
        "persona": "Grant Sanderson (Narrator)",
        "tempo_estimate": 1.0,
        "sync_strategy": "dynamic_atempo_fit"
    }
]

# Write master script JSON
master_script_file = os.path.join(script_dir, "3b1b_calculus_l09_bangla_master_script.json")
with open(master_script_file, "w", encoding="utf-8") as f:
    json.dump(master_script_cues, f, ensure_ascii=False, indent=2)
print(f"Master script written: {master_script_file} ({len(master_script_cues)} cues)")

# -------------------------------------------------------------------------
# 2. AUDIO CUES MANIFEST (assets/audio/calculus/lesson_09/manifest.json & manifest.js)
# -------------------------------------------------------------------------
audio_manifest_data = {
    "course": "calculus",
    "lesson": "lesson_09",
    "title": "অধ্যায় ০৯ — ক্ষেত্রফলের সাথে ঢালের কী সম্পর্ক? (ক্যালকুলাসের মৌলিক উপপাদ্য)",
    "voice": "bn-BD-PradeepNeural",
    "mode": "authentic_teacher",
    "sections": {
        "sec-area-slope-mystery": {
            "section_id": "sec-area-slope-mystery",
            "alias": "sec_01_area_slope_mystery",
            "title": "১. ক্ষেত্রফল ও ঢালের রহস্যময় সংযোগ (The Area-Slope Mystery)",
            "audio_file": "sec_01_area_slope_mystery.mp3",
            "total_duration_ms": 115000.0,
            "cues": [
                {
                    "index": 0,
                    "type": "h2",
                    "text": "প্রথম পরিচ্ছেদ: ক্ষেত্রফল ও ঢালের আপাত বৈপরীত্য ও রহস্যময় সংযোগ।",
                    "start_ms": 0.0,
                    "end_ms": 5200.0,
                    "duration_ms": 5200.0
                },
                {
                    "index": 1,
                    "type": "chapter-quote",
                    "text": "উদ্ধৃতি: পরিবর্তনের হার বের করা আর সামগ্রিক যোগফল নির্ণয় করা আপাতদৃষ্টিতে বিপরীত হলেও, তারা মূলত একই মুদ্রার এপিঠ-ওপিঠ।",
                    "start_ms": 5500.0,
                    "end_ms": 14200.0,
                    "duration_ms": 8700.0
                },
                {
                    "index": 2,
                    "type": "p",
                    "text": "প্রথম দেখায় মনে হতে পারে, একটি বক্ররেখার নিচের ক্ষেত্রফল পরিমাপ করা এবং স্পর্শক রেখার ঢাল নির্ণয় করা সম্পূর্ণ ভিন্ন দুটি জ্যামিতিক সমস্যা।",
                    "start_ms": 14500.0,
                    "end_ms": 25800.0,
                    "duration_ms": 11300.0
                },
                {
                    "index": 3,
                    "type": "p",
                    "text": "ঢাল বা অন্তরীকরণ হলো একটি নির্দিষ্ট বিন্দুর অতি ক্ষুদ্র প্রতিবেশে জুম করে তাৎক্ষণিক স্থানীয় পরিবর্তনের হার প্রত্যক্ষ করা। অন্যদিকে সমাকলন হলো পুরো অঞ্চলকে অসীম সংখ্যক সরু ফালিতে কেটে তাদের যোগ করা।",
                    "start_ms": 26100.0,
                    "end_ms": 42500.0,
                    "duration_ms": 16400.0
                },
                {
                    "index": 4,
                    "type": "figure",
                    "text": "চিত্র প্রদর্শনী: স্পর্শক ঢাল বনাম বক্ররেখার নিচের সূক্ষ্ম আয়তাকার ফালিগুলোর রিম্যান যোগফল।",
                    "start_ms": 42800.0,
                    "end_ms": 52000.0,
                    "duration_ms": 9200.0
                },
                {
                    "index": 5,
                    "type": "p",
                    "text": "তা সত্ত্বেও এই দুটি প্রক্রিয়া পরস্পরের নিখুঁত বিপরীতমুখী অপারেশন। একেই বলা হয় ক্যালকুলাসের মৌলিক উপপাদ্য, বা ফান্ডামেন্টাল থিওরেম অফ ক্যালকুলাস।",
                    "start_ms": 52300.0,
                    "end_ms": 68000.0,
                    "duration_ms": 15700.0
                },
                {
                    "index": 6,
                    "type": "callout",
                    "text": "মৌলিক প্রশ্ন: কেন বক্ররেখার নিচের ক্ষেত্রফল খোঁজার সমাধান লুকিয়ে থাকে আরেকটি ফাংশনের ঢাল খোঁজার ভেতর?",
                    "start_ms": 68300.0,
                    "end_ms": 81000.0,
                    "duration_ms": 12700.0
                }
            ]
        },
        "sec-accumulation-function": {
            "section_id": "sec-accumulation-function",
            "alias": "sec_02_accumulation_function",
            "title": "২. সঞ্চয়ন ফাংশন A(x) ও অতি ক্ষুদ্র ধাপ dx (The Accumulation Function)",
            "audio_file": "sec_02_accumulation_function.mp3",
            "total_duration_ms": 124000.0,
            "cues": [
                {
                    "index": 0,
                    "type": "h2",
                    "text": "দ্বিতীয় পরিচ্ছেদ: সঞ্চয়ন ফাংশন এ অফ এক্স এবং অতি ক্ষুদ্র বৃদ্ধি ডিএক্স।",
                    "start_ms": 0.0,
                    "end_ms": 5100.0,
                    "duration_ms": 5100.0
                },
                {
                    "index": 1,
                    "type": "p",
                    "text": "এই বিপরীত সম্পর্ক বুঝতে চলুন আমরা একটি সঞ্চয়ন ফাংশন এ অফ এক্স সংজ্ঞায়িত করি, যা শূন্য থেকে এক্স সীমার মধ্যে বক্ররেখার নিচের মোট ক্ষেত্রফল ধারণ করে।",
                    "start_ms": 5400.0,
                    "end_ms": 19500.0,
                    "duration_ms": 14100.0
                },
                {
                    "index": 2,
                    "type": "p",
                    "text": "এবার ইনপুট এক্সকে সামান্য নাড়া দিয়ে ডিএক্স পরিমাণ বৃদ্ধি করুন। এর ফলে ক্ষেত্রফলে যে অতি সূক্ষ্ম বৃদ্ধি ডিএ ঘটে, তা ডান প্রান্তে যুক্ত হওয়া একটি সরু আয়তাকার ফালি।",
                    "start_ms": 19800.0,
                    "end_ms": 36000.0,
                    "duration_ms": 16200.0
                },
                {
                    "index": 3,
                    "type": "figure",
                    "text": "চিত্র প্রদর্শনী: ডিএক্স প্রস্থের সরু ফালি এবং তার উচ্চতা এফ অফ এক্স।",
                    "start_ms": 36300.0,
                    "end_ms": 44500.0,
                    "duration_ms": 8200.0
                },
                {
                    "index": 4,
                    "type": "p",
                    "text": "ফালিটির প্রস্থ হলো ডিএক্স এবং এর উচ্চতা সরাসরি মূল ফাংশনের উচ্চতা এফ অফ এক্স। সুতরাং ক্ষেত্রফলের ক্ষুদ্র বৃদ্ধি ডিএ সমান প্রায় এফ অফ এক্স গুণ ডিএক্স।",
                    "start_ms": 44800.0,
                    "end_ms": 61000.0,
                    "duration_ms": 16200.0
                },
                {
                    "index": 5,
                    "type": "callout",
                    "text": "বিশেষ নোট: ওপরে থাকা অতি ক্ষুদ্র বক্র শীর্ষভাগটির ক্ষেত্রফল ডিএক্স স্কয়ারের সমানুপাতিক, যা ডিএক্স শূন্যের দিকে গেলে নিখুঁতভাবে বিলুপ্ত হয়ে যায়।",
                    "start_ms": 61300.0,
                    "end_ms": 77500.0,
                    "duration_ms": 16200.0
                }
            ]
        },
        "sec-fundamental-theorem": {
            "section_id": "sec-fundamental-theorem",
            "alias": "sec_03_fundamental_theorem",
            "title": "৩. ক্যালকুলাসের মৌলিক উপপাদ্য: dA/dx = f(x) (The Fundamental Theorem)",
            "audio_file": "sec_03_fundamental_theorem.mp3",
            "total_duration_ms": 138000.0,
            "cues": [
                {
                    "index": 0,
                    "type": "h2",
                    "text": "তৃতীয় পরিচ্ছেদ: ক্যালকুলাসের মৌলিক উপপাদ্য এবং অ্যান্টিডেরিভেটিভের সন্ধান।",
                    "start_ms": 0.0,
                    "end_ms": 5500.0,
                    "duration_ms": 5500.0
                },
                {
                    "index": 1,
                    "type": "p",
                    "text": "উভয় পক্ষকে ডিএক্স দিয়ে ভাগ করলেই উন্মোচিত হয় মহাজাগতিক সত্য: ডিএ ভাগ ডিএক্স সমান এফ অফ এক্স! ক্ষেত্রফল বৃদ্ধির হার হুবহু মূল ফাংশনের উচ্চতার সমান।",
                    "start_ms": 5800.0,
                    "end_ms": 22000.0,
                    "duration_ms": 16200.0
                },
                {
                    "index": 2,
                    "type": "p",
                    "text": "এর মানে হলো, ক্ষেত্রফল বের করার দুরূহ কাজ মূলত এমন একটি ফাংশন ক্যাপিটাল এফ অফ এক্স খোঁজা, যার অন্তরজ হলো স্মল এফ অফ এক্স।",
                    "start_ms": 22300.0,
                    "end_ms": 36500.0,
                    "duration_ms": 14200.0
                },
                {
                    "index": 3,
                    "type": "figure",
                    "text": "চিত্র প্রদর্শনী: প্যারাবোলা এক্স স্কয়ারের ক্ষেত্রফল কীভাবে এক-তৃতীয়াংশ এক্স কিউব হয়।",
                    "start_ms": 36800.0,
                    "end_ms": 46200.0,
                    "duration_ms": 9400.0
                },
                {
                    "index": 4,
                    "type": "p",
                    "text": "যখন আমরা এ থেকে বি সীমার ক্ষেত্রফল খুঁজি, তখন তা দাঁড়ায় এ অফ বি বিয়োগ এ অফ এ, যা অ্যান্টিডেরিভেটিভের মান ক্যাপিটাল এফ অফ বি বিয়োগ ক্যাপিটাল এফ অফ এ এর সমান।",
                    "start_ms": 46500.0,
                    "end_ms": 64000.0,
                    "duration_ms": 17500.0
                },
                {
                    "index": 5,
                    "type": "callout",
                    "text": "ক্যালকুলাসের মূল উপপাদ্য: ইন্টিগ্রাল এ থেকে বি এফ অফ এক্স ডিএক্স সমান ক্যাপিটাল এফ অফ বি বিয়োগ ক্যাপিটাল এফ অফ এ।",
                    "start_ms": 64300.0,
                    "end_ms": 78000.0,
                    "duration_ms": 13700.0
                }
            ]
        },
        "sec-velocity-distance": {
            "section_id": "sec-velocity-distance",
            "alias": "sec_04_velocity_distance",
            "title": "৪. বেগ বনাম দূরত্ব এবং নিট সরণের ভৌত রূপ (Velocity and Distance Intuition)",
            "audio_file": "sec_04_velocity_distance.mp3",
            "total_duration_ms": 128000.0,
            "cues": [
                {
                    "index": 0,
                    "type": "h2",
                    "text": "চতুর্থ পরিচ্ছেদ: বেগ ও দূরত্বের সম্পর্কের মাধ্যমে অন্তর্দৃষ্টি গভীর করা।",
                    "start_ms": 0.0,
                    "end_ms": 5000.0,
                    "duration_ms": 5000.0
                },
                {
                    "index": 1,
                    "type": "p",
                    "text": "চলন্ত গাড়ির ক্ষেত্রে বেগ ভি অফ টি হলো দূরত্বের অন্তরজ: ভি সমান ডিএস ভাগ ডিটি। আবার অতি ক্ষুদ্র সময় ডিটিতে অতিক্রান্ত দূরত্ব হলো ডিএস সমান বেগ গুণ ডিটি।",
                    "start_ms": 5300.0,
                    "end_ms": 22000.0,
                    "duration_ms": 16700.0
                },
                {
                    "index": 2,
                    "type": "figure",
                    "text": "চিত্র প্রদর্শনী: বেগের লেখচিত্রের নিচে প্রতিটি ক্ষুদ্র ফালি ডিএস এবং সামগ্রিক সরণ এস অফ টি।",
                    "start_ms": 22300.0,
                    "end_ms": 31500.0,
                    "duration_ms": 9200.0
                },
                {
                    "index": 3,
                    "type": "p",
                    "text": "সবগুলো ডিএস যোগ করলে যেমন মোট অতিক্রান্ত দূরত্ব মেলে, তেমনি বেগের বক্ররেখার নিচের ক্ষেত্রফল পরিমাপ করলেও হুবহু একই মোট সরণ পাওয়া যায়।",
                    "start_ms": 31800.0,
                    "end_ms": 47500.0,
                    "duration_ms": 15700.0
                },
                {
                    "index": 4,
                    "type": "callout",
                    "text": "ভৌত অন্তর্দৃষ্টি: ডেরিভেটিভ যেখানে তাৎক্ষণিক বেগ দেয়, ক্ষেত্রফল বা ইন্টিগ্রেশন সেখানে পুঞ্জীভূত সম্পূর্ণ পথ বা সরণ ফিরিয়ে দেয়।",
                    "start_ms": 47800.0,
                    "end_ms": 62500.0,
                    "duration_ms": 14700.0
                }
            ]
        },
        "sec-signed-area-average": {
            "section_id": "sec-signed-area-average",
            "alias": "sec_05_signed_area_average",
            "title": "৫. ঋণাত্মক ক্ষেত্রফল ও ফাংশনের গড় মান (Negative Areas and Average Value)",
            "audio_file": "sec_05_signed_area_average.mp3",
            "total_duration_ms": 118000.0,
            "cues": [
                {
                    "index": 0,
                    "type": "h2",
                    "text": "পঞ্চম পরিচ্ছেদ: ঋণাত্মক ক্ষেত্রফল এবং ফাংশনের গড় মানের চমৎকার রূপায়ন।",
                    "start_ms": 0.0,
                    "end_ms": 5400.0,
                    "duration_ms": 5400.0
                },
                {
                    "index": 1,
                    "type": "p",
                    "text": "যদি বক্ররেখাটি এক্স অক্ষের নিচে নেমে যায়, তবে উচ্চতা ঋণাত্মক হওয়ায় ক্ষেত্রফলের বৃদ্ধিও ঋণাত্মক হয়। এটি উল্টো দিকে চলা গাড়ির সরণ কমে যাওয়ার মতো।",
                    "start_ms": 5700.0,
                    "end_ms": 21500.0,
                    "duration_ms": 15800.0
                },
                {
                    "index": 2,
                    "type": "p",
                    "text": "এছাড়াও একটি ফাংশনের মোট ক্ষেত্রফলকে ব্যবধির দৈর্ঘ্য বি বিয়োগ এ দিয়ে ভাগ করলে মেলে ফাংশনটির গড় মান, যা অসম বক্ররেখাকে একটি সমতল আয়তক্ষেত্রের রূপ দেয়।",
                    "start_ms": 21800.0,
                    "end_ms": 38500.0,
                    "duration_ms": 16700.0
                },
                {
                    "index": 3,
                    "type": "figure",
                    "text": "চিত্র প্রদর্শনী: ফাংশনের পরিবর্তনশীল উচ্চতা বনাম গড় উচ্চতার আয়তক্ষেত্র।",
                    "start_ms": 38800.0,
                    "end_ms": 47000.0,
                    "duration_ms": 8200.0
                },
                {
                    "index": 4,
                    "type": "callout",
                    "text": "উপসংহার: ক্ষেত্রফল এবং ঢাল হলো পরিবর্তনের একই মুদ্রার এপিঠ-ওপিঠ—একটি স্থানীয় অনুপাত মাপে, অন্যটি সামগ্রিক পুঞ্জীভবন ঘটায়।",
                    "start_ms": 47300.0,
                    "end_ms": 61500.0,
                    "duration_ms": 14200.0
                }
            ]
        }
    }
}

manifest_file = os.path.join(audio_dir, "manifest.json")
with open(manifest_file, "w", encoding="utf-8") as f:
    json.dump(audio_manifest_data, f, ensure_ascii=False, indent=2)
print(f"Audio manifest JSON written: {manifest_file}")

manifest_js_content = "window.TEACHER_AUDIO_MANIFEST = " + json.dumps(audio_manifest_data, ensure_ascii=False, indent=2) + ";\n"
manifest_js_file = os.path.join(audio_dir, "manifest.js")
with open(manifest_js_file, "w", encoding="utf-8") as f:
    f.write(manifest_js_content)
print(f"Audio manifest JS written: {manifest_js_file}")

# Write individual section cue json files as well
for sec_key, sec_data in audio_manifest_data["sections"].items():
    cue_filename = f"{sec_data['alias']}_cues.json"
    cue_filepath = os.path.join(audio_dir, cue_filename)
    with open(cue_filepath, "w", encoding="utf-8") as f:
        json.dump(sec_data["cues"], f, ensure_ascii=False, indent=2)
    print(f"Section cue file written: {cue_filepath}")

# -------------------------------------------------------------------------
# 3. SINGLE-SHELL LESSON DATA JSON (data/calculus/lesson_09.json)
# -------------------------------------------------------------------------
lesson_data = {
    "meta": {
        "course_id": "calculus",
        "course_title_en": "Essence of Calculus",
        "course_title_bn": "ক্যালকুলাসের মূল সারমর্ম",
        "lesson_id": "lesson_09",
        "lesson_number": 9,
        "lesson_number_bn": "০৯",
        "title_en": "What does area have to do with slope?",
        "title_bn": "অধ্যায় ০৯: ক্ষেত্রফলের সাথে ঢালের কী সম্পর্ক? (What does area have to do with slope?)",
        "subtitle_bn": "সঞ্চয়ন ফাংশন $A(x)$, ক্ষুদ্র ফালির বৃদ্ধি $dA \\approx f(x)\\,dx$, এবং ক্যালকুলাসের মৌলিক উপপাদ্য $\\frac{dA}{dx} = f(x)$",
        "duration": "13:21",
        "youtube_id": "FnJqaIESC2s",
        "theme_color": "#f59e0b",
        "theme_color_rgb": "245, 158, 11",
        "audio_manifest": "../../assets/audio/calculus/lesson_09/manifest.json",
        "audio_manifest_js": "../../assets/audio/calculus/lesson_09/manifest.js",
        "prev_lesson": {
            "id": "lesson_08",
            "number_bn": "০৮",
            "title_bn": "যোগজীকরণ ও রিম্যান যোগফল (Integration and Riemann Sums)",
            "href": "lesson_08.html"
        },
        "next_lesson": {
            "id": "lesson_10",
            "number_bn": "১০",
            "title_bn": "উচ্চতর মাত্রার অন্তরক বা হায়ার অর্ডার ডেরিভেটিভ (Higher Order Derivatives)",
            "href": "lesson_10.html"
        }
    },
    "hero": {
        "badge_bn": "ক্যালকুলাস • নবম অধ্যায়",
        "headline_bn": "ক্ষেত্রফল ও ঢালের রহস্যময় যুগলবন্দি",
        "subheadline_bn": "স্পর্শকের ঢাল বের করা আর বক্ররেখার নিচের ক্ষেত্রফল খোঁজা সম্পূর্ণ ভিন্ন জ্যামিতিক সমস্যা মনে হলেও, কেন তারা পরস্পরের নিখুঁত বিপরীত প্রক্রিয়া?",
        "key_takeaway_bn": "ক্ষেত্রফল ফাংশন $A(x)$ এর বৃদ্ধির হার $\\frac{dA}{dx}$ অবিকল মূল বক্ররেখার উচ্চতা $f(x)$ এর সমান; ফলে সমাকলন হলো অন্তরীকরণের ঠিক বিপরীত বা অ্যান্টিডেরিভেটিভ।"
    },
    "sections": [
        {
            "id": "sec-area-slope-mystery",
            "alias": "sec_01_area_slope_mystery",
            "number_bn": "১",
            "title_bn": "ক্ষেত্রফল ও ঢালের আপাত বৈপরীত্য ও রহস্যময় সংযোগ (The Area-Slope Mystery)",
            "quote": {
                "text_bn": "পরিবর্তনের হার বের করা আর সামগ্রিক যোগফল নির্ণয় করা আপাতদৃষ্টিতে ভিন্ন হলেও, তারা মূলত একই মুদ্রার এপিঠ-ওপিঠ।",
                "author_bn": "গ্রান্ট স্যান্ডারসন (৩ব্লু১ব্রাউন)"
            },
            "paragraphs": [
                "ক্যালকুলাসের প্রথম পাঠগুলোতে আমরা স্পর্শকের ঢাল বা অন্তরজ (Derivative) নিয়ে আলোচনা করেছি। সেখানে আমাদের সম্পূর্ণ মনোযোগ ছিল একটি একক বিন্দুর অতি ক্ষুদ্র প্রতিবেশের ওপর—ইনপুটকে সামান্য একটু নাড়া দিলে আউটপুট কীভাবে সাড়া দেয় তা দেখা। এটি একটি চরম স্থানীয় (Local) পরিমাপ।",
                "অন্যদিকে, সমাকলন বা যোগজীকরণে (Integration) আমরা একটি বিস্তৃত ব্যবধির ওপর বক্ররেখার নিচের সমগ্র আবদ্ধ অঞ্চলের ক্ষেত্রফল নির্ণয় করি। এটি অসীম সংখ্যক সরু সরু আয়তাকার ফালির যোগফল (Global Summation)।",
                "প্রথম দর্শনে মনে হওয়া খুবই স্বাভাবিক যে, একটি একক বিন্দুতে জুম করে স্পর্শকের ঢাল খোঁজা এবং হাজার হাজার ফালি যোগ করে সমগ্র ক্ষেত্রফল নির্ণয় করার মধ্যে কোনো প্রত্যক্ষ সম্পর্ক থাকার কথা নয়। কিন্তু এই দুটি ধারণাই গণিতের ইতিহাসে সবচেয়ে শক্তিশালী উপপাদ্য দ্বারা অবিচ্ছেদ্যভাবে যুক্ত: ক্যালকুলাসের মৌলিক উপপাদ্য (Fundamental Theorem of Calculus)।"
            ],
            "formulas": [
                {
                    "latex": "\\frac{df}{dx} = \\lim_{\\Delta x \\to 0} \\frac{f(x+\\Delta x) - f(x)}{\\Delta x} \\quad \\text{বনাম} \\quad \\int_a^b f(x)\\,dx = \\lim_{N \\to \\infty} \\sum_{i=1}^N f(x_i)\\,\\Delta x",
                    "caption_bn": "অন্তরীকরণের স্থানীয় ঢাল এবং সমাকলনের বৈশ্বিক যোগফল।"
                }
            ],
            "callout": {
                "title_bn": "মৌলিক প্রশ্ন: ক্যালকুলাসের হৃদস্পন্দন",
                "text_bn": "কেন একটি বক্ররেখার নিচের ক্ষেত্রফল বের করতে গিয়ে আমরা সরাসরি এমন একটি ফাংশন খুঁজি যার ডেরিভেটিভ হলো মূল বক্ররেখাটি? এই আপাত অলৌকিক সম্পর্ক কীভাবে জ্যামিতিকভাবে বাস্তবায়িত হয়?"
            },
            "closing_thought_bn": "এই রহস্যের চাবিকাঠি লুকিয়ে আছে 'সঞ্চয়ন ফাংশন' (Accumulation Function)-এর জ্যামিতিক রূপায়ণের ভেতরে।"
        },
        {
            "id": "sec-accumulation-function",
            "alias": "sec_02_accumulation_function",
            "number_bn": "২",
            "title_bn": "সঞ্চয়ন ফাংশন $A(x)$ ও অতি ক্ষুদ্র ধাপ $dx$ (The Accumulation Function)",
            "paragraphs": [
                "এই রহস্যের মূল সমাধানটি বুঝতে চলুন আমরা একটি গতিশীল ক্ষেত্রফল ফাংশন বা সঞ্চয়ন ফাংশন $A(x)$ কল্পনা করি। ধরা যাক আমাদের কাছে একটি লেখচিত্র রয়েছে $y = f(t)$। আমরা স্থির করলাম $0$ থেকে শুরু করে ডানদিকে একটি চলন্ত সীমা $x$ পর্যন্ত বক্ররেখার নিচের আবদ্ধ ক্ষেত্রফল পরিমাপ করব।",
                "অর্থাৎ, $A(x)$ হলো এমন একটি ফাংশন যা ইনপুট হিসেবে $x$ নেয় এবং আউটপুট হিসেবে শূন্য থেকে $x$ পর্যন্ত সঞ্চিত মোট ক্ষেত্রফল ফিরিয়ে দেয়। $x$ যত ডানে সরবে, $A(x)$ এর মান ততই বাড়তে থাকবে।",
                "এখন নিজেকে ক্যালকুলাসের সবচেয়ে মৌলিক প্রশ্নটি করুন: এই ক্ষেত্রফল ফাংশন $A(x)$ এর অন্তরজ বা ডেরিভেটিভ কী হবে? অর্থাৎ $\\frac{dA}{dx}$ এর মান কত?",
                "অন্তরজের সংজ্ঞা অনুসারে, আমরা ইনপুট $x$-কে অতি ক্ষুদ্র পরিমাণ $dx$ ডানদিকে নাড়া দিই। এর ফলে সঞ্চিত ক্ষেত্রফলে একটি ক্ষুদ্র সংযোজন ঘটে, যাকে আমরা বলছি $dA$।"
            ],
            "formulas": [
                {
                    "latex": "A(x) = \\int_0^x f(t)\\,dt",
                    "caption_bn": "চলন্ত প্রান্তবিন্দু $x$ বিশিষ্ট সঞ্চয়ন বা ক্ষেত্রফল ফাংশন।"
                },
                {
                    "latex": "dA = A(x + dx) - A(x)",
                    "caption_bn": "ইনপুট $x$-এ $dx$ বৃদ্ধির ফলে ক্ষেত্রফলের অতি ক্ষুদ্র বৃদ্ধি।"
                }
            ],
            "callout": {
                "title_bn": "জ্যামিতিক রূপ: ক্ষেত্রফলের ক্ষুদ্র ফালি",
                "text_bn": "লেখচিত্রের দিকে তাকালে দেখা যায়, এই বাড়তি ক্ষেত্রফল $dA$ হলো মূল ক্ষেত্রটির ঠিক ডান প্রান্তে যুক্ত হওয়া একটি অত্যন্ত সরু খাড়া ফালি (Sliver of Area)।"
            }
        },
        {
            "id": "sec-fundamental-theorem",
            "alias": "sec_03_fundamental_theorem",
            "number_bn": "৩",
            "title_bn": "ক্যালকুলাসের মৌলিক উপপাদ্য: $dA/dx = f(x)$ (The Fundamental Theorem)",
            "paragraphs": [
                "এবার এই ক্ষুদ্র ফালিটির জ্যামিতিক মাত্রার দিকে তাকান। ফালিটির প্রস্থ কত? ফালিটির প্রস্থ অবিকল $dx$, কারণ আমরা $x$-কে ঠিক $dx$ পরিমাণ সরিয়েছি।",
                "আর ফালিটির উচ্চতা কত? অত্যন্ত ক্ষুদ্র এই প্রস্থ জুড়ে বক্ররেখার উচ্চতা প্রায় সম্পূর্ণ ধ্রুবক থাকে, এবং সেই উচ্চতা আর কিছুই নয়—সরাসরি $x$ বিন্দুতে বক্ররেখার উচ্চতা $f(x)$!",
                "ফালিটির শীর্ষে অতি সামান্য একটু বাঁকা অংশ বা ক্যাপ থাকতে পারে, কিন্তু সেই অংশের ক্ষেত্রফল $\\approx \\frac{1}{2}\\,dx\\,df$, যা $(dx)^2$-এর সমানুপাতিক। $dx \\to 0$ সীমাতে এই ক্ষুদ্র অংশটি নিখুঁতভাবে মিলিয়ে যায়।",
                "সুতরাং প্রথম ক্রমের নিখুঁত হিসেবে: $dA \\approx f(x) \\cdot dx$। এবার উভয় পক্ষকে $dx$ দিয়ে ভাগ করলেই উন্মোচিত হয় মহাজাগতিক সত্য: $\\frac{dA}{dx} = f(x)$!"
            ],
            "formulas": [
                {
                    "latex": "dA \\approx f(x)\\,dx \\implies \\frac{dA}{dx} = f(x)",
                    "caption_bn": "ক্ষেত্রফলের বৃদ্ধির হার অবিকল মূল ফাংশনের উচ্চতার সমান।"
                },
                {
                    "latex": "\\int_a^b f(x)\\,dx = F(b) - F(a) \\quad \\text{যেখানে } F'(x) = f(x)",
                    "caption_bn": "ক্যালকুলাসের মৌলিক উপপাদ্যের সমাকলিত রূপ।"
                }
            ],
            "callout": {
                "title_bn": "অবিস্মরণীয় অন্তর্দৃষ্টি: বিপরীতমুখী অপারেশন",
                "text_bn": "ক্ষেত্রফল ফাংশন $A(x)$-এর পরিবর্তনের হার বা ঢাল হলো সরাসরি $f(x)$। এর মানে হলো ক্ষেত্রফল বের করা মানে এমন একটি ফাংশন $F(x)$ খুঁজে বের করা যার ডেরিভেটিভ হলো $f(x)$! যোগজীকরণ এবং ব্যবকলন একে অপরের নিখুঁত বিপরীত।"
            },
            "closing_thought_bn": "উদাহরণস্বরূপ, $f(x) = x^2$ হলে তার ক্ষেত্রফল ফাংশন এমন একটি ফাংশন যার অন্তরজ $x^2$। আমরা জানি $\\frac{d}{dx}(\\frac{1}{3}x^3) = x^2$, সুতরাং ক্ষেত্রফল অবিকল $\\frac{1}{3}x^3$!"
        },
        {
            "id": "sec-velocity-distance",
            "alias": "sec_04_velocity_distance",
            "number_bn": "৪",
            "title_bn": "বেগ বনাম দূরত্ব এবং নিট সরণের ভৌত রূপ (Velocity & Distance Intuition)",
            "paragraphs": [
                "এই গাণিতিক ধারণাকে বাস্তব পৃথিবীর অভিজ্ঞতার সাথে মেলাতে সবচেয়ে চমৎকার উদাহরণ হলো একটি চলমান গাড়ির বেগ ও দূরত্ব।",
                "মনে করুন একটি গাড়ির বেগ সময়ের সাথে সাথে অবিরত পরিবর্তিত হচ্ছে, যাকে আমরা $v(t)$ বলছি। বেগ যদি স্থির থাকত, তবে অতিক্রান্ত দূরত্ব হতো কেবল $\\text{বেগ} \\times \\text{সময়}$। বেগের লেখচিত্রে এই গুণফলটি একটি আয়তক্ষেত্রের ক্ষেত্রফল ছাড়া আর কিছুই নয়।",
                "কিন্তু যখন বেগ অনবরত ওঠানামা করে, তখন পুরো ভ্রমণকে আমরা অতি ক্ষুদ্র সময় ব্যবধান $dt$-তে ভাগ করি। প্রতিটি ক্ষুদ্র মুহূর্তে গাড়িটি সামান্য একটু পথ অতিক্রম করে: $ds = v(t)\\,dt$।",
                "এই প্রতিটি ক্ষুদ্র দূরত্ব $ds$ মূলত বেগের লেখচিত্রের নিচে $dt$ প্রস্থ ও $v(t)$ উচ্চতার একটি ক্ষুদ্র ফালির ক্ষেত্রফল। সবগুলো ফালির ক্ষেত্রফল যোগ করলে যেমন মোট ক্ষেত্রফল মেলে, তেমনি সবগুলো ক্ষুদ্র দূরত্ব $ds$ যোগ করলে মোট সরণ $s(t)$ মেলে।"
            ],
            "formulas": [
                {
                    "latex": "v(t) = \\frac{ds}{dt} \\implies ds = v(t)\\,dt",
                    "caption_bn": "তাৎক্ষণিক বেগ ও অতি ক্ষুদ্র দূরত্বের সম্পর্ক।"
                },
                {
                    "latex": "\\text{Total Displacement} = \\int_{t_1}^{t_2} v(t)\\,dt = s(t_2) - s(t_1)",
                    "caption_bn": "বেগের লেখচিত্রের ক্ষেত্রফল হিসেবে নিট সরণ।"
                }
            ],
            "callout": {
                "title_bn": "ভৌত জগতের দ্বৈত রূপ",
                "text_bn": "দূরত্ব ফাংশনের ঢাল হলো তাৎক্ষণিক বেগ ($v = \\frac{ds}{dt}$), আর বেগের লেখচিত্রের ক্ষেত্রফল হলো পুঞ্জীভূত দূরত্ব ($s = \\int v\\,dt$)। এখানে স্পষ্ট দেখা যায় কীভাবে ক্ষেত্রফল এবং ঢাল পরস্পরের বিপরীত প্রক্রিয়া হিসেবে কাজ করে।"
            }
        },
        {
            "id": "sec-signed-area-average",
            "alias": "sec_05_signed_area_average",
            "number_bn": "৫",
            "title_bn": "চিহ্নযুক্ত ক্ষেত্রফল ও ফাংশনের গড় মান (Signed Area & Average Value)",
            "paragraphs": [
                "এখন একটি স্বাভাবিক প্রশ্ন জাগতে পারে: যদি কোনো বক্ররেখা অনুভূমিক অক্ষের নিচে চলে যায়, অর্থাৎ $f(x) < 0$ হয়, তখন কী ঘটে?",
                "সেই অঞ্চলে ফালির উচ্চতা $f(x)$ ঋণাত্মক হওয়ায় ক্ষেত্রফলের বৃদ্ধি $dA = f(x)\\,dx$ ঋণাত্মক হয়। ক্যালকুলাসের সংজ্ঞায় অক্ষের নিচের ক্ষেত্রফল ঋণাত্মক হিসেবে পরিগণিত হয়। ভৌতভাবে, ঋণাত্মক বেগ মানে গাড়িটি পেছনের দিকে ব্যাক করছে, যার ফলে মোট সরণ হ্রাস পায়।",
                "আর একটি চমৎকার ধারণা হলো কোনো ফাংশনের গড় মান (Average Value)। যদি $a$ থেকে $b$ ব্যবধিতে বক্ররেখার নিচের মোট ক্ষেত্রফলকে ব্যবধির দৈর্ঘ্য $b - a$ দিয়ে ভাগ করা হয়, তবে আমরা এমন একটি ধ্রুবক উচ্চতা পাই যা একটি নিখুঁত আয়তক্ষেত্র তৈরি করে যার ক্ষেত্রফল মূল বক্ররেখার ক্ষেত্রফলের হুবহু সমান।"
            ],
            "formulas": [
                {
                    "latex": "f_{\\text{avg}} = \\frac{1}{b - a} \\int_a^b f(x)\\,dx",
                    "caption_bn": "একটি ব্যবধিতে ফাংশনের গড় মানের গাণিতিক সংজ্ঞা।"
                },
                {
                    "latex": "\\text{Area} = f_{\\text{avg}} \\cdot (b - a)",
                    "caption_bn": "গড় উচ্চতার আয়তক্ষেত্রের ক্ষেত্রফল মূল বক্ররেখার ক্ষেত্রফলের সমান।"
                }
            ],
            "callout": {
                "title_bn": "উপসংহার: ক্যালকুলাসের একীভূত রূপ",
                "text_bn": "অন্তরীকরণ (Differentiation) কোনো রাশির প্রতি মুহূর্তে পরিবর্তনের স্থানীয় তীব্রতা পরিমাপ করে, আর সমাকলন (Integration) সেই পরিবর্তনগুলোকে একত্রিত করে আদি রাশিটি পুনরুদ্ধার করে।"
            }
        }
    ],
    "quizzes": [
        {
            "id": "quiz-1",
            "question_bn": "১. ক্ষেত্রফল ফাংশন $A(x) = \\int_0^x f(t)\\,dt$ এর ডেরিভেটিভ $\\frac{dA}{dx}$ কেন হুবহু মূল ফাংশন $f(x)$ এর সমান হয়?",
            "correct_index": 1,
            "options": [
                {
                    "text_bn": "কারণ ক্ষেত্রফলের একক এবং ঢালের একক সর্বদা সমান হতে হয়",
                    "feedback_bn": "ভুল! ক্ষেত্রফল এবং ঢালের মাত্রা বা একক সাধারণত ভিন্ন হয়।"
                },
                {
                    "text_bn": "কারণ $x$ কে $dx$ পরিমাণ বৃদ্ধি করলে নতুন যুক্ত হওয়া ক্ষেত্রফলের ফালির উচ্চতা হয় $f(x)$ এবং প্রস্থ হয় $dx$, ফলে $\\frac{dA}{dx} = \\frac{f(x)\\,dx}{dx} = f(x)$",
                    "feedback_bn": "চমৎকার ও নিখুঁত! জ্যামিতিকভাবে ক্ষুদ্র ফালির ক্ষেত্রফল $dA \\approx f(x)\\,dx$, যা ভাগ করলে সরাসরি উচ্চতা $f(x)$ ফেরত দেয়।"
                },
                {
                    "text_bn": "কারণ এটি কেবল একটি কাকতালীয় বীজগাণিতিক সূত্র যা প্রমাণ করা যায় না",
                    "feedback_bn": "ভুল! এটি ক্যালকুলাসের মৌলিক উপপাদ্য দ্বারা সম্পূর্ণ দৃশ্যমান ও প্রমাণিত।"
                },
                {
                    "text_bn": "কারণ সমাকলনের চিহ্নের ভেতর ডেরিভেটিভ বসালে সব শূন্য হয়ে যায়",
                    "feedback_bn": "ভুল! এটি গাণিতিকভাবে অবাস্তব।"
                }
            ],
            "explanation_bn": "ইনপুট $x$ সামান্য $dx$ সরলে ক্ষেত্রফলের যে বৃদ্ধি $dA$ ঘটে, তা মূলত $f(x)$ উচ্চতা ও $dx$ প্রস্থের একটি অতি সরু আয়তাকার ফালি। ফলে $\\frac{dA}{dx} = f(x)$।"
        },
        {
            "id": "quiz-2",
            "question_bn": "২. যদি $f(x) = 3x^2$ হয়, তবে $x = 0$ থেকে $x = 2$ পর্যন্ত বক্ররেখার নিচের আবদ্ধ ক্ষেত্রফলের মান কত?",
            "correct_index": 2,
            "options": [
                {
                    "text_bn": "১২",
                    "feedback_bn": "ভুল! ১২ হলো $x=2$ বিন্দুতে স্পর্শকের ঢাল, ক্ষেত্রফল নয়।"
                },
                {
                    "text_bn": "৬",
                    "feedback_bn": "ভুল! এটি সঠিক সমাকলন মান নয়।"
                },
                {
                    "text_bn": "৮",
                    "feedback_bn": "অসাধারণ! $3x^2$-এর অ্যান্টিডেরিভেটিভ হলো $x^3$। সুতরাং ক্ষেত্রফল $F(2) - F(0) = 2^3 - 0 = 8$।"
                },
                {
                    "text_bn": "২৪",
                    "feedback_bn": "ভুল! হিসাবটি পুনরায় পরীক্ষা করুন।"
                }
            ],
            "explanation_bn": "মৌলিক উপপাদ্য অনুসারে, $\\int_0^2 3x^2\\,dx = [x^3]_0^2 = 2^3 - 0 = 8$।"
        },
        {
            "id": "quiz-3",
            "question_bn": "৩. বেগ-সময় লেখচিত্রের নিচের ক্ষেত্রফল ভৌতভাবে কী নির্দেশ করে?",
            "correct_index": 0,
            "options": [
                {
                    "text_bn": "ওই সময় ব্যবধানে গাড়িটির অতিক্রান্ত মোট সরণ বা অবস্থানের নিট পরিবর্তন",
                    "feedback_bn": "একেবারে সঠিক! যেহেতু বেগ $v = \\frac{ds}{dt}$, তাই ক্ষুদ্র দূরত্ব $ds = v\\,dt$ এর সমষ্টি হলো মোট সরণ।"
                },
                {
                    "text_bn": "গাড়িটির ত্বরণ বা এক্সিলারেশন",
                    "feedback_bn": "ভুল! ত্বরণ হলো বেগ লেখচিত্রের স্পর্শক ঢাল, ক্ষেত্রফল নয়।"
                },
                {
                    "text_bn": "গাড়ির ইঞ্জিনের তাপমাত্রা",
                    "feedback_bn": "ভুল! এর সাথে দূরত্বের প্রত্যক্ষ সম্পর্ক নেই।"
                },
                {
                    "text_bn": "গাড়ির চাকার ঘূর্ণন সংখ্যা",
                    "feedback_bn": "ভুল! এটি সরাসরি সরণ বা ক্ষেত্রফল নির্দেশ করে।"
                }
            ],
            "explanation_bn": "প্রতিটি ক্ষুদ্র ফালি $v(t)\\,dt$ হলো ওই অতি ক্ষুদ্র সময়ের সরণ $ds$। এদের সমন্বিত ক্ষেত্রফল হলো মোট সরণ $s(t_2) - s(t_1)$।"
        },
        {
            "id": "quiz-4",
            "question_bn": "৪. একটি নির্দিষ্ট ব্যবধি $[a, b]$-তে কোনো ফাংশন $f(x)$-এর নিচের ক্ষেত্রফলকে ব্যবধির দৈর্ঘ্য $(b - a)$ দিয়ে ভাগ করলে কী পাওয়া যায়?",
            "correct_index": 3,
            "options": [
                {
                    "text_bn": "ফাংশনের সর্বোচ্চ চরম মান (Maximum)",
                    "feedback_bn": "ভুল! চরম মানের জন্য প্রথম ডেরিভেটিভ শূন্য করতে হয়।"
                },
                {
                    "text_bn": "বক্ররেখার বক্রতার ব্যাসার্ধ",
                    "feedback_bn": "ভুল! এটি দ্বিতীয় অন্তরকের সাথে সম্পর্কিত।"
                },
                {
                    "text_bn": "ফাংশনটির মোট ক্ষেত্রফলের দ্বিগুণ",
                    "feedback_bn": "ভুল! ক্ষেত্রফলকে দৈর্ঘ্য দিয়ে ভাগ করলে উচ্চতা পাওয়া যায়।"
                },
                {
                    "text_bn": "ব্যবধিটিতে ফাংশনটির গড় উচ্চতা বা গড় মান ($f_{\\text{avg}}$)",
                    "feedback_bn": "অসাধারণ! ক্ষেত্রফলকে ভূমির দৈর্ঘ্য দিয়ে ভাগ করলে প্রাপ্ত উচ্চতাটিই হলো ফাংশনটির গড় মান।"
                }
            ],
            "explanation_bn": "ক্ষেত্রফল $=$ ভূমি $\\times$ গড় উচ্চতা, সুতরাং $f_{\\text{avg}} = \\frac{1}{b-a}\\int_a^b f(x)\\,dx$।"
        }
    ],
    "interactive_components": [
        {
            "id": "accumulation-area-sim",
            "title_bn": "ইন্টারেক্টিভ সিমুলেটর: সঞ্চয়ন ফাংশন ও সরু ফালির বৃদ্ধি",
            "type": "canvas_visualizer",
            "description_bn": "স্লাইডার টেনে $x$-এর মান পরিবর্তন করুন এবং দেখুন কীভাবে $dx$ বৃদ্ধির সাথে সাথে $dA \\approx f(x)\\,dx$ ক্ষেত্রফল ফালি যুক্ত হয় এবং $\\frac{dA}{dx}$ সরাসরি বক্ররেখার উচ্চতা নির্দেশ করে।"
        },
        {
            "id": "velocity-distance-bridge",
            "title_bn": "ইন্টারেক্টিভ ল্যাব: বেগ থেকে দূরত্বের দ্বৈত রূপ",
            "type": "motion_simulator",
            "description_bn": "বেগের লেখচিত্র পরিবর্তন করে দেখুন কীভাবে নিচের ক্ষেত্রফল বাস্তব গাড়ির অতিক্রান্ত পথের সমান হয় এবং ঋণাত্মক বেগে ক্ষেত্রফল হ্রাস পায়।"
        }
    ]
}

lesson_data_file = os.path.join(data_dir, "lesson_09.json")
with open(lesson_data_file, "w", encoding="utf-8") as f:
    json.dump(lesson_data, f, ensure_ascii=False, indent=2)
print(f"Lesson data JSON written: {lesson_data_file}")
print("ALL LESSON 09 RESOURCES SUCCESSFULLY GENERATED.")
