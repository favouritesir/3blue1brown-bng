import asyncio
import os
import json
import subprocess
import edge_tts

VOICE = "bn-BD-PradeepNeural"
RATE = "-2%"
PITCH = "+0Hz"

OUTPUT_DIR = os.path.join(
    "departments",
    "learning_paths",
    "stem_mathematics",
    "3blue1brown_courses",
    "web_platform",
    "assets",
    "audio",
    "linear_algebra",
    "lesson_05"
)
os.makedirs(OUTPUT_DIR, exist_ok=True)

SECTIONS_DATA = [
    {
        "id": "sec_01_3d_space",
        "title": "ত্রিমাত্রিক জগতে রূপান্তর",
        "audio_file": "sec_01_3d_space.mp3",
        "cues_file": "sec_01_3d_space_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "প্রথম পরিচ্ছেদ: ত্রিমাত্রিক জগতে রূপান্তর।"
            },
            {
                "index": 1,
                "type": "chapter-quote",
                "text": "অধ্যায়ের শুরুতে দ্য সিম্পসন্সের একটি মজাদার দৃশ্য মনে পড়ে। লিসা জিজ্ঞেস করেছিল, বাবা কোথায়? উত্তরে অধ্যাপক ফ্রিংক বলেছিলেন, হাইপারবোলিক টপোলজিতে ডিগ্রিধারী যে কারও কাছে এটি স্পষ্ট যে, হোমার সিম্পসন ভুলবশত পা রেখেছে আমাদের তৃতীয় মাত্রায়!"
            },
            {
                "index": 2,
                "type": "p",
                "text": "শিক্ষার্থী বন্ধুরা, পূর্ববর্তী অধ্যায়গুলোতে আমরা লিনিয়ার রূপান্তর এবং ম্যাট্রিক্স নিয়ে যা কিছু শিখেছি, তার প্রায় সবকিছুই ছিল দ্বিমাত্রিক বা টুডি সমতলে। টুডি সমতলে কাজ করার সবচেয়ে বড় সুবিধা হলো, এটি ব্ল্যাকবোর্ডে বা কম্পিউটার স্ক্রিনে খুব সহজে এঁকে অনুধাবন করা যায়।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "তবে লিনিয়ার অ্যালজেব্রার সবচেয়ে সুন্দর সত্যটি হলো: টুডি সমতলে এর মূল দর্শনটি একবার পরিষ্কারভাবে বুঝে নিতে পারলে, উচ্চতর মাত্রাগুলোতে—যেমন থ্রিডি, চার মাত্রিক বা এন মাত্রিক স্পেসে—ঠিক একই নিয়ম সম্পূর্ণ অবিকৃত ও সুন্দরভাবে কাজ করে।"
            },
            {
                "index": 4,
                "type": "p",
                "text": "এই অধ্যায়ে আমরা তাই আমাদের চিরচেনা সমতল ফ্ল্যাটল্যান্ড ছেড়ে পা রাখব বাস্তব ত্রিমাত্রিক জগতে। আর দেখব কীভাবে তিনটি বেসিস ভেক্টর ট্র্যাক করার মাধ্যমে পুরো থ্রিডি স্পেসের যেকোনো রূপান্তরকে নিয়ন্ত্রণ করা যায়।"
            },
            {
                "index": 5,
                "type": "h3",
                "text": "ত্রিমাত্রিক জগতের তিনটি মৌলিক বেসিস ভেক্টর।"
            },
            {
                "index": 6,
                "type": "p",
                "text": "টুডি স্থানে যেমন দুটি স্থানাঙ্ক অক্ষ ছিল—এক্স অক্ষ এবং ওয়াই অক্ষ; তেমনি ত্রিমাত্রিক জগতে সমকোণে অবস্থান করে তিনটি অক্ষ: এক্স অক্ষ, ওয়াই অক্ষ, এবং উল্লম্ব জেড অক্ষ। এই তিন অক্ষ বরাবর তিনটি একক বেসিস ভেক্টর রয়েছে: আই হ্যাট, জে হ্যাট, এবং কে হ্যাট।"
            },
            {
                "index": 7,
                "type": "figure",
                "text": "পাশের চিত্রে লক্ষ্য করো: লাল তীরচিহ্নটি এক্স অক্ষ বরাবর আই হ্যাট, সবুজ তীরটি ওয়াই অক্ষ বরাবর জে হ্যাট, এবং নীল তীরটি উল্লম্ব জেড অক্ষ বরাবর কে হ্যাট বেসিস ভেক্টর নির্দেশ করছে।"
            },
            {
                "index": 8,
                "type": "p",
                "text": "থ্রিডি স্পেসের যেকোনো ভেক্টর ভি-কে আমরা এই তিনটি বেসিস ভেক্টরের স্কেলিং ও রৈখিক সমাবেশ আকারে প্রকাশ করতে পারি। এখানে স্থানাঙ্ক এক্স, ওয়াই এবং জেড হলো মূলত তিনটি স্পষ্ট নির্দেশনা—আই হ্যাট, জে হ্যাট এবং কে হ্যাটকে ঠিক কত গুণ টেনে প্রসারিত করে পরস্পর যোগ করতে হবে।"
            },
            {
                "index": 9,
                "type": "formula-box",
                "text": "স্ক্রিনের সমীকরণে দেখো: ভেক্টর ভি সমান এক্স গুণ আই হ্যাট যোগ ওয়াই গুণ জে হ্যাট যোগ জেড গুণ কে হ্যাট। অর্থাৎ কলাম ম্যাট্রিক্স এক্স, ওয়াই, জেড।"
            },
            {
                "index": 10,
                "type": "h3",
                "text": "ত্রিমাত্রিক রৈখিক রূপান্তরের মৌলিক জ্যামিতিক বৈশিষ্ট্য।"
            },
            {
                "index": 11,
                "type": "p",
                "text": "টুডি জগতের মতোই, একটি ত্রিমাত্রিক রূপান্তর তখনই লিনিয়ার হবে যখন দুটি শর্ত পূরণ হয়: প্রথমত, মূলবিন্দু বা অরিজিন শূন্য কমা শূন্য কমা শূন্য বিন্দুতেই স্থির থাকবে; এবং দ্বিতীয়ত, মহাকাশের সমস্ত গ্রিডরেখা সোজা থাকবে এবং সমান্তরাল তলগুলো রূপান্তরের পরেও পরস্পরের সমান্তরাল ও সমদূরত্বে বজায় থাকবে।"
            },
            {
                "index": 12,
                "type": "figure",
                "text": "পাশের চিত্রে লক্ষ্য করো: পুরো ত্রিমাত্রিক স্পেস একটি স্থিতিস্থাপক রবারের ঘনকের মতো সংকুচিত বা আবর্তিত হলেও মূলবিন্দু অনড় রয়েছে এবং প্রতিটি তল পরস্পরের সাথে সমান্তরাল অবস্থান ধরে রেখেছে।"
            },
            {
                "index": 13,
                "type": "p",
                "text": "ত্রিমাত্রিক স্থানে কোটি কোটি ভেক্টরকে তীরের মতো কল্পনা করা অসম্ভব। কিন্তু লিনিয়ার অ্যালজেব্রার জাদুকরী কৌশল হলো: পুরো স্পেসের পেছনে ছোটার দরকার নেই! কেবল লক্ষ্য করুন রূপান্তরের পর আমাদের তিনটি বেসিস ভেক্টর—আই হ্যাট, জে হ্যাট এবং কে হ্যাট—কোথায় গিয়ে পৌঁছাল।"
            }
        ]
    },
    {
        "id": "sec_02_matrix3x3",
        "title": "৩×৩ ম্যাট্রিক্স ও î, ĵ, k̂ ট্র্যাকিং",
        "audio_file": "sec_02_matrix3x3.mp3",
        "cues_file": "sec_02_matrix3x3_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "দ্বিতীয় পরিচ্ছেদ: তিন বাই তিন ম্যাট্রিক্স এবং আই হ্যাট, জে হ্যাট ও কে হ্যাট ট্র্যাকিং।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "রূপান্তরের পর আমাদের ভিত্তি ভেক্টর তিনটি মহাকাশের তিনটি নতুন অবস্থানে অবতরণ করে। আই হ্যাট রূপান্তরিত হয়ে পৌঁছায় এল অফ আই হ্যাটে, জে হ্যাট পৌঁছায় এল অফ জে হ্যাটে, এবং কে হ্যাট পৌঁছায় এল অফ কে হ্যাটে।"
            },
            {
                "index": 2,
                "type": "figure",
                "text": "চিত্রে দেখো, রূপান্তরের ধাক্কায় আই হ্যাট, জে হ্যাট এবং কে হ্যাট কীভাবে তিনটি ভিন্ন ভিন্ন ত্রিমাত্রিক স্থানাঙ্কে গিয়ে নোঙর ফেলল।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "এখন এই রূপান্তরিত তিনটি ভেক্টরকে পাশাপাশি তিনটি উল্লম্ব কলাম আকারে সাজিয়ে দিলেই আমরা পেয়ে যাই একটি তিন বাই তিন ম্যাট্রিক্স! এই নয়টি বাস্তব সংখ্যাই পুরো ত্রিমাত্রিক রূপান্তরের পূর্ণাঙ্গ ডিএনএ।"
            },
            {
                "index": 4,
                "type": "formula-box",
                "text": "স্ক্রিনের ফর্মুলা বক্সে তাকাও: ম্যাট্রিক্স এম সমান তিন বাই তিন ম্যাট্রিক্স। সবুজ রঙের প্রথম কলামটি এল অফ আই হ্যাট, লাল রঙের দ্বিতীয় কলামটি এল অফ জে হ্যাট, এবং নীল রঙের তৃতীয় কলামটি এল অফ কে হ্যাট।"
            },
            {
                "index": 5,
                "type": "h3",
                "text": "ত্রিমাত্রিক ম্যাট্রিক্স-ভেক্টর গুণনের জ্যামিতিক তাৎপর্য।"
            },
            {
                "index": 6,
                "type": "p",
                "text": "এখন যদি যেকোনো সাধারণ ভেক্টর এক্স, ওয়াই, জেড-কে এই ম্যাট্রিক্স দিয়ে গুণ করি, ফলাফল কী হবে? এটি কোনো অন্ধ বীজগাণিতিক সূত্র নয়! এটি হলো মূলত রূপান্তরিত কলাম তিনটির একটি ভারযুক্ত বা ওয়েইটেড যোগফল।"
            },
            {
                "index": 7,
                "type": "formula-box",
                "text": "সমীকরণটিতে লক্ষ্য করো: ম্যাট্রিক্স এম গুণ ভেক্টর ভি সমান এক্স গুণ প্রথম কলাম যোগ ওয়াই গুণ দ্বিতীয় কলাম যোগ জেড গুণ তৃতীয় কলাম। প্রতিটি উপাদান বেসিস ভেক্টরের স্কেলিং ছাড়া আর কিছুই নয়!"
            },
            {
                "index": 8,
                "type": "figure",
                "text": "ডায়াগ্রামে দেখো, মূল ভেক্টরটির স্থানাঙ্ক এক্স, ওয়াই এবং জেড কীভাবে নতুন রূপান্তরিত স্পেসে কলাম তিনটিকে সঠিক অনুপাতে মিশিয়ে আউটপুট ভেক্টর তৈরি করছে।"
            },
            {
                "index": 9,
                "type": "h3",
                "text": "বাস্তব উদাহরণ: ওয়াই অক্ষ এবং জেড অক্ষকে কেন্দ্র করে নব্বই ডিগ্রি ঘূর্ণন।"
            },
            {
                "index": 10,
                "type": "p",
                "text": "একটি চমৎকার উদাহরণ দেখা যাক। ধরো পুরো ত্রিমাত্রিক স্পেসকে ওয়াই অক্ষ স্থির রেখে তার চারদিকে নব্বই ডিগ্রি ঘোরানো হলো। এতে এক্স অক্ষের আই হ্যাট ঘুরে চলে যায় ঋণাত্মক জেড অক্ষে, জে হ্যাট ওয়াই অক্ষের ওপরেই অপরিবর্তিত থাকে, আর কে হ্যাট ঘুরে চলে আসে ধনাত্মক এক্স অক্ষে। এই তিনটি অবস্থান পাশাপাশি লিখলেই তৈরি হয়ে যায় আমাদের ঘূর্ণন ম্যাট্রিক্স।"
            },
            {
                "index": 11,
                "type": "figure",
                "text": "পাশের চিত্রে দেখো: ওয়াই অক্ষের সাপেক্ষে নব্বই ডিগ্রি ঘূর্ণনে প্রতিটি অক্ষ কীভাবে স্থান পরিবর্তন করছে এবং ম্যাট্রিক্সের কলামগুলোতে রূপ নিচ্ছে।"
            },
            {
                "index": 12,
                "type": "h3",
                "text": "ত্রিমাত্রিক ম্যাট্রিক্স গুণন ও রূপান্তরের ধারাবাহিক সংযোজন।"
            },
            {
                "index": 13,
                "type": "p",
                "text": "যখন আমরা দুটি তিন বাই তিন ম্যাট্রিক্স এ এবং বি গুণ করি, তার জ্যামিতিক অর্থ হলো প্রথমে বি রূপান্তরটি স্পেসে ঘটে, এরপর তার ওপর এ রূপান্তরটি কার্যকর হয়। আধুনিক থ্রিডি গেম ইঞ্জিন ও রোবোটিক্সে যেকোনো জটিল আবর্তনকে এভাবে আলাদা আলাদা অক্ষের ঘূর্ণন ম্যাট্রিক্স গুণের মাধ্যমে অত্যন্ত নিখুঁতভাবে তৈরি করা হয়।"
            },
            {
                "index": 14,
                "type": "callout-blue",
                "text": "একটি গুরুত্বপূর্ণ সতর্কতা মনে রাখতে হবে: ত্রিমাত্রিক স্থানে ঘূর্ণনের ক্রম অত্যন্ত সংবেদনশীল! এ গুণ বি এবং বি গুণ এ কখনোই এক নয়। তোমরা নিজের হাতে মোবাইল ফোন নিয়ে প্রথমে ডানে নব্বই ডিগ্রি এবং পরে উপরে নব্বই ডিগ্রি ঘুরিয়ে দেখো; এরপর উল্টো ক্রমে করো—দেখবে ফোনের চূড়ান্ত মুখ সম্পূর্ণ ভিন্ন দিকে চলে গেছে!"
            }
        ]
    },
    {
        "id": "sec_03_determinant3d",
        "title": "ত্রিমাত্রিক আয়তন স্কেলিং ও ডিটারমিন্যান্ট",
        "audio_file": "sec_03_determinant3d.mp3",
        "cues_file": "sec_03_determinant3d_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "তৃতীয় পরিচ্ছেদ: ত্রিমাত্রিক আয়তন স্কেলিং এবং ডিটারমিন্যান্ট।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "অধ্যায়ের সমাপনীতে গ্রান্ট স্যান্ডারসন একটি চমৎকার প্রশ্ন উত্থাপন করেছেন: ভিন্ন ভিন্ন মাত্রার মধ্যে কি লিনিয়ার রূপান্তর সম্ভব? উত্তর হলো—অবশ্যই সম্ভব! যেমন টুডি থেকে থ্রিডি রূপান্তর ঘটে তিন বাই দুই ম্যাট্রিক্সের সাহায্যে।"
            },
            {
                "index": 2,
                "type": "p",
                "text": "তিন বাই দুই ম্যাট্রিক্সে ইনপুট হলো টুডি ভেক্টর, কিন্তু আউটপুট হলো থ্রিডি মহাকাশে একটি সমতলীয় চাদর। উল্টোভাবে, থ্রিডি স্পেসের কোনো দৃশ্যকে আমাদের টুডি কম্পিউটার স্ক্রিনে ফুটিয়ে তোলার প্রক্রিয়াটি নিয়ন্ত্রিত হয় দুই বাই তিন ম্যাট্রিক্সের প্রজেকশন বা অভিক্ষেপের মাধ্যমে।"
            },
            {
                "index": 3,
                "type": "figure",
                "text": "চিত্রে দেখো, কীভাবে ইনপুট মাত্রার বেসিস ভেক্টরের সংখ্যা ম্যাট্রিক্সের কলাম সংখ্যা নির্ধারণ করে, আর আউটপুট মাত্রার স্থানাঙ্ক ম্যাট্রিক্সের রো সংখ্যা নির্ধারণ করে।"
            },
            {
                "index": 4,
                "type": "h3",
                "text": "ত্রিমাত্রিক আয়তন স্কেলিং এবং একক ঘনকের রূপান্তর।"
            },
            {
                "index": 5,
                "type": "p",
                "text": "এবার একটি অত্যন্ত গভীর জ্যামিতিক পর্যবেক্ষণ করা যাক। কল্পনা করো মূলবিন্দুতে আই হ্যাট, জে হ্যাট এবং কে হ্যাট দিয়ে তৈরি এক একক দৈর্ঘ্যের একটি কিউব বা ঘনক রয়েছে। যার আদি আয়তন ঠিক এক ঘন একক।"
            },
            {
                "index": 6,
                "type": "p",
                "text": "যেকোনো তিন বাই তিন লিনিয়ার রূপান্তর প্রয়োগ করলে পুরো স্পেসের সাথে এই ঘনকটিও টানটান হয়ে একটি বাক্সে পরিণত হয়। যেমন আই হ্যাট যদি দ্বিগুণ প্রসারিত হয়, জে হ্যাট তিনগুণ প্রসারিত হয় এবং কে হ্যাট একই থাকে, তবে নতুন বাক্সের আয়তন হবে দুই গুণ তিন গুণ এক, অর্থাৎ ঠিক ছয় ঘন একক!"
            },
            {
                "index": 7,
                "type": "callout-gold",
                "text": "পরবর্তী অধ্যায়ের সেতুবন্ধনে এটিই আমাদের সবচেয়ে বড় উপহার: পরবর্তী লেসনে আমরা শিখব ডিটারমিন্যান্ট। টুডি সমতলে ডিটারমিন্যান্ট যেমন ক্ষেত্রফলের পরিবর্তনের হার মাপত, থ্রিডি জগতে ডিটারমিন্যান্ট পরিমাপ করে: যেকোনো রৈখিক রূপান্তরের ফলে ত্রিমাত্রিক স্থানের কোনো বাক্সের আয়তন ঠিক কত গুণ প্রসারিত বা সংকুচিত হলো!"
            },
            {
                "index": 8,
                "type": "p",
                "text": "সারসংক্ষেপে শিক্ষার্থী বন্ধুরা মনে রাখবে: টুডিতে যেমন চারটি সংখ্যা দুটি কলামে স্পেস নিয়ন্ত্রণ করত, থ্রিডিতে তেমনি নয়টি সংখ্যা তিনটি কলামে পুরো ত্রিমাত্রিক মহাকাশকে নিয়ন্ত্রণ করে। আশা করি ত্রিমাত্রিক রূপান্তরের এই চমৎকার জ্যামিতিক সৌন্দর্য তোমরা গভীরভাবে উপলব্ধি করতে পেরেছ। ধন্যবাদ!"
            }
        ]
    }
]

async def synthesize_section(sec):
    audio_path = os.path.join(OUTPUT_DIR, sec["audio_file"])
    cues_path = os.path.join(OUTPUT_DIR, sec["cues_file"])
    
    if os.path.exists(audio_path) and os.path.exists(cues_path) and os.path.getsize(audio_path) > 1000:
        print(f"⏩ Section {sec['title']} ({sec['audio_file']}) already generated, loading cues...")
        with open(cues_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return sec["id"], sec["title"], sec["audio_file"], sec["cues_file"], data["total_duration_ms"], data["cues"]
        
    print(f"\n🎙️ Synthesizing Section: {sec['title']} ({sec['audio_file']})...")
    
    item_cues = []
    current_time_ms = 0.0
    temp_files = []
    
    for item in sec["items"]:
        item_text = item["text"]
        idx = item["index"]
        temp_mp3 = os.path.join(OUTPUT_DIR, f"tmp_{sec['id']}_{idx}.mp3")
        temp_files.append(temp_mp3)
        
        # Check if item temp file exists
        if os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 1000:
            print(f"  [{idx+1}/{len(sec['items'])}] Reusing existing temp for cue {idx}")
            success = True
        else:
            success = False
            for attempt in range(5):
                try:
                    communicate = edge_tts.Communicate(item_text, voice=VOICE, rate=RATE, pitch=PITCH)
                    await communicate.save(temp_mp3)
                    if os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 1000:
                        print(f"  [{idx+1}/{len(sec['items'])}] Generated cue {idx}")
                        success = True
                        break
                    else:
                        raise RuntimeError("File too small")
                except Exception as e:
                    print(f"Retry {attempt+1} for item {idx}: {e}")
                    await asyncio.sleep(1.0)
        
        if not success:
            raise RuntimeError(f"Failed to synthesize item {idx}: {item_text}")
        
        # Measure duration with ffprobe
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{temp_mp3}"'
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
        for t_file in temp_files:
            abs_p = os.path.abspath(t_file).replace("\\", "/")
            f.write(f"file '{abs_p}'\n")
            
    # Concatenate using ffmpeg with high-quality MP3 encoding
    concat_cmd = f'ffmpeg -y -f concat -safe 0 -i "{concat_list_file}" -c:a libmp3lame -b:a 192k "{audio_path}"'
    subprocess.run(concat_cmd, shell=True, check=True, capture_output=True)
    
    # Clean up temp files
    for t_file in temp_files:
        if os.path.exists(t_file):
            try:
                os.remove(t_file)
            except Exception:
                pass
    if os.path.exists(concat_list_file):
        try:
            os.remove(concat_list_file)
        except Exception:
            pass
        
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
    return sec["id"], sec["title"], sec["audio_file"], sec["cues_file"], round(current_time_ms, 1), item_cues

async def main():
    print("=" * 70)
    print("Master Bengali Teacher Audio Synthesis — Lesson 05 (3D Transformations)")
    print(f"Voice: {VOICE} | Folder: {OUTPUT_DIR}")
    print("=" * 70)
    
    manifest_sections = {}
    
    for sec in SECTIONS_DATA:
        sec_id, title, audio_file, cues_file, total_duration_ms, item_cues = await synthesize_section(sec)
        manifest_sections[sec_id] = {
            "title": title,
            "audio_file": audio_file,
            "cues_file": cues_file,
            "total_duration_ms": total_duration_ms,
            "cues": item_cues
        }
        
    manifest_data = {
        "course": "linear_algebra",
        "lesson": "lesson_05",
        "voice": VOICE,
        "mode": "authentic_teacher",
        "sections": manifest_sections
    }
    
    manifest_json_path = os.path.join(OUTPUT_DIR, "manifest.json")
    with open(manifest_json_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)
        
    manifest_js_path = os.path.join(OUTPUT_DIR, "manifest.js")
    with open(manifest_js_path, "w", encoding="utf-8") as f:
        f.write("window.TEACHER_AUDIO_MANIFEST = " + json.dumps(manifest_data, ensure_ascii=False, indent=2) + ";\n")
        
    print(f"\n🎉 Saved manifest.json and manifest.js successfully in {OUTPUT_DIR}!")

if __name__ == "__main__":
    asyncio.run(main())
