import asyncio
import os
import json
import edge_tts

VOICE = "bn-BD-PradeepNeural"
RATE = "-2%"
PITCH = "+0Hz"

OUTPUT_DIR = r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/lesson_01"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Teacher narration script organized by section and sequential items/blocks
# We write authentic, warm, articulate native Bengali teacher explanations.
SECTIONS_DATA = [
    {
        "id": "sec-interpretations",
        "title": "ভেক্টরের তিনটি ব্যাখ্যা",
        "audio_file": "sec_01_interpretations.mp3",
        "cues_file": "sec_01_interpretations_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "প্রথম পরিচ্ছেদ: ভেক্টরের তিনটি ব্যাখ্যা।"
            },
            {
                "index": 1,
                "type": "chapter-quote",
                "text": "বিখ্যাত গণিতবিদ হের্মান ওয়াইল একবার বলেছিলেন, 'সংখ্যাকে স্থানাঙ্ক হিসেবে উপস্থাপন করা একটি সহিংস কাজ।' কথাটি একটু গভীর, তাই না? কিন্তু পুরো কোর্সে আমরা এর চমৎকার সত্যতা উপলব্ধি করব।"
            },
            {
                "index": 2,
                "type": "p",
                "text": "শিক্ষার্থী বন্ধুরা, লিনিয়ার অ্যালজেব্রার মূল ভিত্তিই হলো ভেক্টর। কিন্তু শুরুতেই একটি মৌলিক প্রশ্ন করা যাক—ভেক্টর আসলে কী? মজার বিষয় হলো, এই প্রশ্নের উত্তর সম্পূর্ণ নির্ভর করে আপনি কার সাথে কথা বলছেন তার ওপর।"
            },
            {
                "index": 3,
                "type": "figure",
                "text": "পাশের চিত্রে লক্ষ্য করো—একটি ভেক্টরকে তীর চিহ্ন হিসেবে দেখানো হয়েছে। এই তীর চিহ্নটির একটি শুরু আছে, আর আছে একটি সুনির্দিষ্ট মুখ বা শীর্ষ।"
            },
            {
                "index": 4,
                "type": "p",
                "text": "ভেক্টরকে বোঝার জন্য মোটাদাগে তিনটি দৃষ্টিভঙ্গি প্রচলিত রয়েছে। একটি পদার্থবিদের দৃষ্টিভঙ্গি, দ্বিতীয়টি কম্পিউটার বিজ্ঞানীর দৃষ্টিভঙ্গি, এবং তৃতীয়টি গণিতবিদের দৃষ্টিভঙ্গি।"
            },
            {
                "index": 5,
                "type": "figure",
                "text": "চিত্রে দেখো, তিনটি ভিন্ন জগত কীভাবে ভেক্টরকে দেখছে। পদার্থবিজ্ঞানী দেখছেন বাস্তব শূন্যে একটি তীর, কম্পিউটার বিজ্ঞানী দেখছেন সংখ্যার তালিকা, আর গণিতবিদ দেখছেন বিমূর্ত এক সুন্দর সম্পর্ক।"
            },
            {
                "index": 6,
                "type": "callout-blue",
                "text": "প্রথমে পদার্থবিদের চোখ দিয়ে দেখি। পদার্থবিদের কাছে ভেক্টর হলো মহাকাশে একটি তীর চিহ্ন। এর কেবল দুটি জিনিস আছে: এক, দৈর্ঘ্য অর্থাৎ ম্যাগনিচিউড; এবং দুই, দিক বা ডিরেকশন। যতক্ষণ দৈর্ঘ্য এবং দিক একই থাকছে, আপনি এই তীরটিকে মহাবিশ্বের যেখানে খুশি সরিয়ে নিতে পারেন, ভেক্টরটি কিন্তু বদলাবে না।"
            },
            {
                "index": 7,
                "type": "figure",
                "text": "এই চিত্রে দেখতে পাচ্ছো, কীভাবে তীরের দৈর্ঘ্য দিয়ে তার মান বা ম্যাগনিচিউড বোঝানো হয়, আর তীরের মুখ দিয়ে তার দিক নির্দেশ করা হয়।"
            },
            {
                "index": 8,
                "type": "p",
                "text": "যেসব ভেক্টর একটি দ্বিমাত্রিক সমতলে আঁকা যায়, তারা হলো টুডি ভেক্টর। আর আমাদের চারপাশের ত্রিমাত্রিক বাস্তব জগতে যেসব ভেক্টর গতি বা বল নির্দেশ করে, তারা হলো থ্রিডি ভেক্টর।"
            },
            {
                "index": 9,
                "type": "figure",
                "text": "ডায়াগ্রামটি লক্ষ্য করো—বামপাশে কাগজের সমতলে টুডি ভেক্টর, আর ডানপাশে ত্রিমাত্রিক স্পেসে থ্রিডি ভেক্টরের চমৎকার ভিজ্যুয়ালাইজেশন।"
            },
            {
                "index": 10,
                "type": "callout-gold",
                "text": "এবার আসা যাক কম্পিউটার বিজ্ঞানীর দৃষ্টিভঙ্গিতে। কম্পিউটার বিজ্ঞানীর কাছে কোনো তীরচিহ্ন নেই, তাঁর কাছে ভেক্টর হলো সংখ্যার একটি সুবিন্যস্ত তালিকা। যেমন রিয়েল এস্টেট সফটওয়্যারে একটি বাড়ির আয়তন এবং দামকে আমরা এভাবে একটি কলামে সাজিয়ে প্রকাশ করতে পারি।"
            },
            {
                "index": 11,
                "type": "formula-box",
                "text": "স্ক্রিনে সমীকরণটি দেখো: ভেক্টর ভি হাউজ সমান কলাম ম্যাট্রিক্স—উপরে দুই হাজার ছয়শত বর্গফুট, আর নিচে তিন লাখ ডলার। এখানে দুটি সংখ্যা সুনির্দিষ্ট ক্রমে বসেছে।"
            },
            {
                "index": 12,
                "type": "code-showcase",
                "text": "কোড স্নsnippet-এ লক্ষ্য করো, কম্পিউটার মেমোরিতে ভেক্টর মানেই একটি ইন্ডেক্সযুক্ত অ্যারো অব নাম্বার্স। যেখানে সোয়াপ ও মার্জ অপারেশনের মাধ্যমে উপাদানগুলোকে প্রক্রিয়াজাত করা হয়।"
            },
            {
                "index": 13,
                "type": "callout-green",
                "text": "সবশেষে গণিতবিদের দৃষ্টিভঙ্গি। গণিতবিদ এই দুই জগতকে এক সুতোয় গাঁথেন। গণিতবিদের কাছে ভেক্টর হলো এমন যেকোনো গাণিতিক অবজেক্ট, যার ওপর দুটি মৌলিক অপারেশন করা সম্ভব—একটি হলো দুটি ভেক্টর যোগ করা, এবং অন্যটি হলো যেকোনো ভেক্টরকে একটি সাধারণ সংখ্যা বা স্কেলার দিয়ে গুণ করা।"
            },
            {
                "index": 14,
                "type": "figure",
                "text": "এই শেষ চিত্রে দেখো গণিতবিদের সার্বজনীন প্রকাশ। লিনিয়ার অ্যালজেব্রার পুরো কাঠামোটি দাঁড়িয়ে আছে এই যোগ এবং স্কেলার গুণনের নিয়মের ওপর।"
            }
        ]
    },
    {
        "id": "sec-coordinates",
        "title": "কোঅর্ডিনেট সিস্টেম ও মূলবিন্দু",
        "audio_file": "sec_02_coordinates.mp3",
        "cues_file": "sec_02_coordinates_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "দ্বিতীয় পরিচ্ছেদ: কোঅর্ডিনেট সিস্টেম ও মূলবিন্দু।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "শিক্ষার্থী বন্ধুরা, এবার চলো আমরা তীরচিহ্ন এবং সংখ্যার তালিকার মাঝে সংযোগ স্থাপন করি। দ্বিমাত্রিক বা টুডি স্পেসে কাজ করার সময় আমাদের দুটি অক্ষ প্রয়োজন—একটি আনুভূমিক এক্স অক্ষ, এবং অন্যটি উল্লম্ব ওয়াই অক্ষ।"
            },
            {
                "index": 2,
                "type": "figure",
                "text": "চিত্রে লক্ষ্য করো এক্স অক্ষ এবং ওয়াই অক্ষ সমকোণে পরস্পরকে ছেদ করেছে।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "যে বিন্দুতে অক্ষ দুটি মিলিত হয়, সেটাই হলো আমাদের মূলবিন্দু বা অরিজিন। লিনিয়ার অ্যালজেব্রায় সব ভেক্টরের লেজ বা টেল এই মূলবিন্দুতেই স্থায়ীভাবে নোঙর করে রাখা হয়।"
            },
            {
                "index": 4,
                "type": "figure",
                "text": "চিত্রে কেন্দ্রবিন্দুটি দেখো—এটাই হলো শূন্য কমা শূন্য স্থানাঙ্কের মূলবিন্দু।"
            },
            {
                "index": 5,
                "type": "figure",
                "text": "গ্রিড লাইনের এই চিত্রে তাকালে তোমরা দেখতে পাবে, প্রতিটি বর্গ একক কীভাবে পুরো সমতলকে পরিমাপযোগ্য এক ছকে রূপ দেয়।"
            },
            {
                "index": 6,
                "type": "p",
                "text": "তাহলে একটি ভেক্টরের স্থানাঙ্ক আসলে কী? স্থানাঙ্ক হলো মূলত মূলবিন্দু থেকে ভেক্টরের মাথায় পৌঁছানোর একজোড়া নির্দেশনা। প্রথম সংখ্যাটি বলে অনুভূমিকভাবে ডানে বা বামে কতটুকু যেতে হবে, আর দ্বিতীয় সংখ্যাটি বলে উল্লম্বভাবে উপরে বা নিচে কতটুকু যেতে হবে।"
            },
            {
                "index": 7,
                "type": "figure",
                "text": "পাশের চিত্রে দেখো, মূলবিন্দু থেকে শুরু হয়ে কীভাবে একটি তীর নির্দিষ্ট স্থানাঙ্কে পৌঁছাচ্ছে।"
            },
            {
                "index": 8,
                "type": "figure",
                "text": "স্থানাঙ্কের এই উপস্থাপনায় লক্ষ্য করো—অনুভূমিক চলন এবং উল্লম্ব চলন মিলে ভেক্টরটির শীর্ষবিন্দু নির্ধারণ করছে।"
            },
            {
                "index": 9,
                "type": "formula-box",
                "text": "সূত্রের দিকে তাকাও: ভেক্টর ভি সমান কলাম ম্যাট্রিক্স—উপরে এক্স উপাদান, নিচে ওয়াই উপাদান। আমরা লিনিয়ার অ্যালজেব্রায় ভেক্টরকে সাধারণত এভাবে কলাম ব্র্যাকেটে লিখি।"
            },
            {
                "index": 10,
                "type": "p",
                "text": "উদাহরণস্বরূপ, কলাম ভেক্টর তিন, মাইনাস দুই। এর অর্থ কী? এর অর্থ হলো মূলবিন্দু থেকে শুরু করে এক্স অক্ষ বরাবর তিন একক ডানে যাও, তারপর ওয়াই অক্ষ বরাবর দুই একক সোজা নিচে নেমে আসো।"
            },
            {
                "index": 11,
                "type": "figure",
                "text": "আর যখন আমরা ত্রিমাত্রিক বা থ্রিডি ভেক্টরে যাই, তখন চিত্রে দেখো আরেকটি অক্ষ যুক্ত হয়—জেড অক্ষ। যা স্ক্রিন বা কাগজের বাইরে সোজা তোমার দিকে প্রসারিত।"
            }
        ]
    },
    {
        "id": "sec-addition",
        "title": "ভেক্টর যোগ",
        "audio_file": "sec_03_addition.mp3",
        "cues_file": "sec_03_addition_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "তৃতীয় পরিচ্ছেদ: ভেক্টর যোগ।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "এবার চলো দেখি দুটি ভেক্টরকে কীভাবে যোগ করতে হয়। জ্যামিতিকভাবে ভেক্টর যোগের নিয়মটি অত্যন্ত চমৎকার ও বাস্তবসম্মত। প্রথম ভেক্টরের মাথায় বা টিপে দ্বিতীয় ভেক্টরের লেজ বা টেল বসাও। এরপর মূলবিন্দু থেকে দ্বিতীয় ভেক্টরের মাথা পর্যন্ত নতুন যে তীরটি পাবে, সেটাই হলো তাদের যোগফল।"
            },
            {
                "index": 2,
                "type": "figure",
                "text": "প্রস্তুতি চিত্রে দুটি আলাদা ভেক্টর দেখতে পাচ্ছো—এখন আমরা এদের যুক্ত করব।"
            },
            {
                "index": 3,
                "type": "figure",
                "text": "চিত্রে লক্ষ্য করো—প্রথম ভেক্টরের শীর্ষ থেকে দ্বিতীয় ভেক্টর শুরু হলো, এবং গোড়া থেকে শীর্ষ পর্যন্ত টানা ভেক্টরটিই হলো লব্ধি বা যোগফল ভেক্টর।"
            },
            {
                "index": 4,
                "type": "formula-box",
                "text": "বীজগণিতের সূত্রে দেখো: কলাম ভেক্টর এক্স ওয়ান ওয়াই ওয়ান যোগ কলাম ভেক্টর এক্স টু ওয়াই টু সমান কলাম ভেক্টর এক্স ওয়ান যোগ এক্স টু, এবং নিচে ওয়াই ওয়ান যোগ ওয়াই টু। অর্থাৎ উপাংশ অনুযায়ী সাধারণ যোগ।"
            },
            {
                "index": 5,
                "type": "figure",
                "text": "এই উপাংশ চিত্রে তাকালে তোমরা পরিষ্কার দেখতে পাবে—এক্স দিকের চলনগুলো একসাথে যোগ হয়েছে, আর ওয়াই দিকের চলনগুলো একসাথে যোগ হয়ে চূড়ান্ত ফলাফল তৈরি করেছে।"
            },
            {
                "index": 6,
                "type": "figure",
                "text": "সংখ্যারেখার সাথে তুলনা করলেও বিষয়টি একদম এক—যেমন সংখ্যারেখায় দুই একক এগিয়ে আবার তিন একক এগোনো মানে মোট পাঁচ একক পথ অতিক্রম করা।"
            },
            {
                "index": 7,
                "type": "callout-blue",
                "text": "কেন এই সংজ্ঞাটি এত চমৎকার? কারণ বাস্তব পদার্থবিদ্যায় যখন একটি বস্তুর ওপর দুটি বল বা ফোর্স একসাথে কাজ করে, তাদের সম্মিলিত প্রভাব ঠিক এই ভেক্টর যোগফলের সমান হয়।"
            }
        ]
    },
    {
        "id": "sec-scalar",
        "title": "স্কেলার গুণন (Scalar Multiplication)",
        "audio_file": "sec_04_scalar.mp3",
        "cues_file": "sec_04_scalar_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "চতুর্থ পরিচ্ছেদ: স্কেলার গুণন বা স্কেলিং।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "এবার আসো দ্বিতীয় মৌলিক অপারেশনে—একটি ভেক্টরকে একটি সাধারণ সংখ্যা দিয়ে গুণ করা। লিনিয়ার অ্যালজেব্রায় সাধারণ সংখ্যাগুলোকে বলা হয় স্কেলার। কারণ তারা ভেক্টরকে স্কেল করে, অর্থাৎ প্রসারিত বা সংকুচিত করে।"
            },
            {
                "index": 2,
                "type": "formula-box",
                "text": "সমীকরণে দেখো: স্কেলার কে গুণ কলাম ভেক্টর এক্স ওয়াই সমান কলাম ভেক্টর কে গুণ এক্স, এবং নিচে কে গুণ ওয়াই। অর্থাৎ স্কেলারটি প্রতিটি উপাদানকে আলাদাভাবে গুণ করে।"
            },
            {
                "index": 3,
                "type": "figure",
                "text": "চিত্রে লক্ষ্য করো: কে সমান দুই হলে ভেক্টরটি তার আগের দিকের ওপরই ঠিক দ্বিগুণ লম্বা হয়ে প্রসারিত হয়।"
            },
            {
                "index": 4,
                "type": "figure",
                "text": "আর কে সমান এক তৃতীয়াংশ হলে চিত্রে দেখো ভেক্টরটি সংকুচিত হয়ে তার আগের দৈর্ঘ্যের এক তৃতীয়াংশ হয়ে যায়।"
            },
            {
                "index": 5,
                "type": "figure",
                "text": "সবচেয়ে আকর্ষণীয় হলো ঋণাত্মক স্কেলার! কে সমান মাইনাস এক দশমিক পাঁচ হলে চিত্রে দেখো ভেক্টরটি একশত আশি ডিগ্রি ঘুরে বিপরীতমুখী হয়ে যায় এবং দেড়গুণ প্রসারিত হয়।"
            }
        ]
    },
    {
        "id": "sec-basis",
        "title": "ভিত্তি ভেক্টর — আই হ্যাট ও জে হ্যাট",
        "audio_file": "sec_05_basis.mp3",
        "cues_file": "sec_05_basis_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "পঞ্চম পরিচ্ছেদ: ভিত্তি ভেক্টর — আই হ্যাট ও জে হ্যাট।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "শিক্ষার্থী বন্ধুরা, এবার আমরা একটি অত্যন্ত গভীর ধারণায় প্রবেশ করছি। টুডি সমতলে সমস্ত স্থানাঙ্ক ব্যবস্থার মূলে রয়েছে দুটি বিশেষ একক ভেক্টর—এক্স অক্ষ বরাবর একক দৈর্ঘ্যের ভেক্টর হলো আই হ্যাট, এবং ওয়াই অক্ষ বরাবর একক দৈর্ঘ্যের ভেক্টর হলো জে হ্যাট।"
            },
            {
                "index": 2,
                "type": "formula-box",
                "text": "স্ক্রিনের ফর্মুলায় লক্ষ্য করো: আই হ্যাট সমান কলাম ভেক্টর এক শূন্য, এবং জে হ্যাট সমান কলাম ভেক্টর শূন্য এক।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "এখন জাদুকরী বিষয়টি দেখো! যেকোনো টুডি ভেক্টরকে কিন্তু আমরা এই আই হ্যাট এবং জে হ্যাটের স্কেলিং ও যোগফল আকারে প্রকাশ করতে পারি।"
            },
            {
                "index": 4,
                "type": "formula-box",
                "text": "সমীকরণে দেখো: ভেক্টর তিন, মাইনাস দুই আসলে হলো তিন গুণ আই হ্যাট যোগ মাইনাস দুই গুণ জে হ্যাট। অর্থাৎ আই হ্যাটকে তিন গুণ টেনে প্রসারিত করো, জে হ্যাটকে দুই গুণ উল্টো দিকে টেনে নাও, তারপর দুটিকে যোগ করো!"
            },
            {
                "index": 5,
                "type": "callout-gold",
                "text": "গ্রান্ট স্যান্ডারসন এটি অত্যন্ত সুন্দরভাবে তুলে ধরেছেন—স্থানাঙ্ক কোনো স্থায়ী পরম সত্য নয়। স্থানাঙ্ক হলো আমরা কোন ভিত্তি ভেক্টর জোড়াকে বেছে নিয়েছি তার সাপেক্ষে মহাকাশ পরিমাপের এক চমৎকার মানবিক চুক্তি মাত্র। যদি আমরা এই ভিত্তি ভেক্টর দুটিকে বদলে দিই, পুরো বিশ্বের স্থানাঙ্ক বদলে যাবে!"
            },
            {
                "index": 6,
                "type": "p",
                "text": "নিচের ইন্টারেক্টিভ ল্যাবে তোমরা নিজের হাতে এক্স এবং ওয়াই উপাংশ বদলে আই হ্যাট ও জে হ্যাটের সমন্বয়ে কীভাবে ভেক্টর গঠিত হয় তা পরীক্ষা করে দেখতে পারো।"
            }
        ]
    },
    {
        "id": "sec-visualizer",
        "title": "ইন্টারেক্টিভ ভেক্টর ভিজ্যুয়ালাইজার",
        "audio_file": "sec_06_visualizer.mp3",
        "cues_file": "sec_06_visualizer_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "ষষ্ঠ পরিচ্ছেদ: ইন্টারেক্টিভ ভেক্টর ভিজ্যুয়ালাইজার।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "এবার শিক্ষার্থী বন্ধুরা, তোমরা নিজেরাই একজন গণিতবিদ হয়ে ওঠো! নিচের ক্যানভাসে মাউস দিয়ে ভেক্টরের লাল বিন্দুটি ধরে টেনে বিভিন্ন দিকে নাড়াও। আর নিচের স্লাইডার দিয়ে স্কেলার কে এর মান পরিবর্তন করে দেখো কীভাবে ভেক্টরটি প্রসারিত, সংকুচিত কিংবা দিক উল্টে যায়। শুভ অনুসন্ধান!"
            }
        ]
    }
]

async def synthesize_section(sec):
    audio_path = os.path.join(OUTPUT_DIR, sec["audio_file"])
    cues_path = os.path.join(OUTPUT_DIR, sec["cues_file"])
    
    if os.path.exists(audio_path) and os.path.exists(cues_path):
        print(f"⏩ Section {sec['title']} already exists, skipping...")
        return
    
    print(f"\n🎙️ Synthesizing Section: {sec['title']} ({sec['audio_file']})...")
    
    # We will synthesize each item and record precise start/end timestamps,
    # concatenating the audio into a single seamless section master MP3!
    item_cues = []
    current_time_ms = 0.0
    
    temp_files = []
    
    for item in sec["items"]:
        item_text = item["text"]
        idx = item["index"]
        temp_mp3 = os.path.join(OUTPUT_DIR, f"tmp_{sec['id']}_{idx}.mp3")
        temp_files.append(temp_mp3)
        
        for attempt in range(5):
            try:
                communicate = edge_tts.Communicate(item_text, voice=VOICE, rate=RATE)
                await communicate.save(temp_mp3)
                if os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 1000:
                    print(f"  [{idx+1}/{len(sec['items'])}] Generated cue {idx}")
                    break
                else:
                    raise RuntimeError("File too small")
            except Exception as e:
                print(f"Retry {attempt+1} for item {idx}: {e}")
                await asyncio.sleep(1.5)
        
        # Measure duration with ffprobe/ffmpeg
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{temp_mp3}"'
        import subprocess
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        try:
            dur_sec = float(res.stdout.strip())
        except Exception as e:
            dur_sec = 2.0
            print(f"Warning: could not parse duration for item {idx}: {e}")
            
        dur_ms = dur_sec * 1000.0
        
        item_cues.append({
            "index": idx,
            "type": item["type"],
            "text": item_text,
            "start_ms": round(current_time_ms, 1),
            "end_ms": round(current_time_ms + dur_ms, 1),
            "duration_ms": round(dur_ms, 1)
        })
        
        # Add slight natural teacher pause between items (350ms)
        current_time_ms += dur_ms + 350.0

    # Create concat list for ffmpeg
    concat_list_file = os.path.join(OUTPUT_DIR, f"concat_{sec['id']}.txt")
    with open(concat_list_file, "w", encoding="utf-8") as f:
        # We need a small silence audio or we can just concatenate with ffmpeg concat demuxer
        for t_file in temp_files:
            abs_p = os.path.abspath(t_file).replace("\\", "/")
            f.write(f"file '{abs_p}'\n")
            
    # Concatenate using ffmpeg with high-quality MP3 encoding
    concat_cmd = f'ffmpeg -y -f concat -safe 0 -i "{concat_list_file}" -c:a libmp3lame -b:a 192k "{audio_path}"'
    subprocess.run(concat_cmd, shell=True, check=True, capture_output=True)
    
    # Clean up temp files
    for t_file in temp_files:
        if os.path.exists(t_file):
            os.remove(t_file)
    if os.path.exists(concat_list_file):
        os.remove(concat_list_file)
        
    # Write cues JSON
    with open(cues_path, "w", encoding="utf-8") as f:
        json.dump({
            "section_id": sec["id"],
            "title": sec["title"],
            "audio_file": sec["audio_file"],
            "total_duration_ms": round(current_time_ms, 1),
            "cues": item_cues
        }, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Generated {sec['audio_file']} ({round(current_time_ms/1000, 2)}s, {len(item_cues)} cues)")

async def main():
    print("======================================================================")
    print("Master Bengali Teacher Audio Synthesis — Lesson 01 (Vectors)")
    print("Voice: bn-BD-PradeepNeural | Mode: Authentic Warm Math Teacher")
    print("======================================================================")
    for sec in SECTIONS_DATA:
        await synthesize_section(sec)
    print("\n🎉 All 6 sections synthesized and saved successfully!")

if __name__ == "__main__":
    asyncio.run(main())
