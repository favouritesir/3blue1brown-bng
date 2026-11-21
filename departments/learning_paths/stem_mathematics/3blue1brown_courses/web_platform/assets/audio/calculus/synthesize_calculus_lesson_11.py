import asyncio
import os
import json
import re
import subprocess
import edge_tts

VOICE = "bn-BD-PradeepNeural"
RATE = "-2%"
PITCH = "+0Hz"

OUTPUT_DIR = r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/calculus/lesson_11"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 5 sections aligned directly with data/calculus/lesson_11.json
# All text strictly phonetically transliterated into Bengali:
# Zero bare Latin letters: x -> এক্স, y -> ওয়াই, t -> টি, u -> ইউ, dx -> ডি এক্স, dy -> ডি ওয়াই, dy/dx -> ডি ওয়াই বাই ডি এক্স, dt -> ডি টি, du -> ডি ইউ, etc.

SECTIONS_CONFIG = [
    {
        "id": "sec-the-dx-paradox",
        "alias": "sec_01_the_dx_paradox",
        "title": "১. ডি এক্স-এর হেঁয়ালি ও গণিতের সবচেয়ে ফলপ্রসূ মিথ্যা (The Paradox of dx)",
        "audio_file": "sec_01_the_dx_paradox.mp3",
        "cues_file": "sec_01_the_dx_paradox_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "প্রথম পরিচ্ছেদ: ডি এক্স-এর হেঁয়ালি ও গণিতের সবচেয়ে ফলপ্রসূ রূপক।"
            },
            {
                "index": 1,
                "type": "chapter-quote",
                "text": "উদ্ধৃতি: লাইবনিজের ডি এক্স প্রতীকটি কোনো যাদুকরী বিভ্রান্তি নয়; এটি গণিতের সবচেয়ে সুবিধাজনক ও গভীর সংকেত যা জটিল সত্যকে সহজাত অনুভূতিতে রূপ দেয়।"
            },
            {
                "index": 2,
                "type": "p",
                "text": "ক্যালকুলাসের ক্লাসরুমে প্রায় প্রতিটি শিক্ষার্থী একটি গভীর দ্বন্দ্বে পড়ে। শিক্ষক যখন বোর্ডে লেখেন লিমিট ডেল্টা এক্স টেন্ডস টু জিরো ডেল্টা ওয়াই বাই ডেল্টা এক্স সমান ডি ওয়াই বাই ডি এক্স, তখন তিনি সতর্ক করে বলেন: মনে রাখবে, ডি ওয়াই বাই ডি এক্স কোনো একক ভগ্নাংশ নয়! এটি একটি একক অপারেটর।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "কিন্তু ঠিক পরের ক্লাসেই যখন চেইন রুল বা ইন্টিগ্রেশন বাই সাবস্টিটিউশন শেখানো হয়, তখন উভয় পক্ষে নিশ্চিন্তে ডি এক্স গুণ করা হয় এবং সাধারণ ভগ্নাংশের মতোই কাটাকাটি করা হয়: ডি ওয়াই বাই ডি টি সমান ডি ওয়াই বাই ডি এক্স গুণ ডি এক্স বাই ডি টি!"
            },
            {
                "index": 4,
                "type": "p",
                "text": "যদি ডি এক্স কোনো পৃথক সংখ্যা না-ই হবে, তবে একে কীভাবে আলাদা করা যায়? আবার ডি এক্স যদি একটি সাধারণ সংখ্যাই হয়, তবে তাকে সাধারণ ভগ্নাংশ বলতে এত দ্বিধা কেন?"
            },
            {
                "index": 5,
                "type": "p",
                "text": "এই প্রশ্নের গভীরে রয়েছে গণিতের তিন শতাব্দীর দার্শনিক বিবর্তন। নিউটন ও লাইবনিজ যখন ষোলোশো আশির দশকে ক্যালকুলাস সৃষ্টি করেন, তখন তারা ডি এক্স ও ডি ওয়াই-কে বিবেচনা করেছিলেন ইনফিনিটেসিমাল বা অসীম ক্ষুদ্র অথচ অশূন্য রাশি হিসেবে।"
            },
            {
                "index": 6,
                "type": "formula-box",
                "text": "দার্শনিক দ্বন্দ্ব: সীমার কঠোর অনুপাত ডি ওয়াই বাই ডি এক্স বনাম লাইবনিজের পৃথক ডিফারেনশিয়াল প্রতীক ডি ওয়াই সমান এফ প্রাইম অফ এক্স গুণ ডি এক্স।"
            },
            {
                "index": 7,
                "type": "callout",
                "text": "দার্শনিক প্রশ্ন: যদি ডি এক্স শূন্য হয়, তবে ভাগফল অনির্ণেয় শূন্য বাই শূন্য। আর যদি ডি এক্স শূন্য না হয়, তবে হিসাবের শেষে আমরা ডি এক্স-যুক্ত পদগুলোকে উড়িয়ে দিই কোন অধিকারে? বিশপ বার্কলি আঠারো শতকে এদের ব্যঙ্গ করেছিলেন বিদায়ী রাশির প্রেতাত্মা বলে।"
            },
            {
                "index": 8,
                "type": "p",
                "text": "এই দ্বন্দ্ব মেটাতে কশি এবং ভাইয়ারস্ট্রাস পরবর্তীতে আনলেন সীমার কঠোর সংজ্ঞা, কিন্তু লাইবনিজের সহজ প্রতীকবাদ আজও গণিতের সবচেয়ে শক্তিশালী ভাষা হয়ে টিকে আছে।"
            }
        ]
    },
    {
        "id": "sec-tangent-line-geometry",
        "alias": "sec_02_tangent_line_geometry",
        "title": "২. স্পর্শক রেখার জগতে ডি এক্স ও ডি ওয়াই (Tangent Line Geometry)",
        "audio_file": "sec_02_tangent_line_geometry.mp3",
        "cues_file": "sec_02_tangent_line_geometry_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "দ্বিতীয় পরিচ্ছেদ: স্পর্শক রেখার জগতে ডি এক্স ও ডি ওয়াই।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "গ্রান্ট স্যান্ডারসন এবং আধুনিক জ্যামিতিক ক্যালকুলাসের দৃষ্টিকোণ থেকে ডি এক্স-এর সবচেয়ে সুন্দর ও সন্তোষজনক ব্যাখ্যাটি হলো: স্পর্শক রেখার ওপর পরিবর্তন।"
            },
            {
                "index": 2,
                "type": "p",
                "text": "ধরা যাক একটি মসৃণ বক্ররেখা ওয়াই সমান এফ অফ এক্স। লেখচিত্রের যেকোনো নির্দিষ্ট বিন্দু এক্স নট, ওয়াই নট-এ আমরা একটি স্পর্শক সরলরেখা টানলাম।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "এখন আমরা ইনপুটকে সামান্য পরিমাণ নাড়া দিলাম। এই আনুভূমিক নাড়াচাড়াকে আমরা বলছি ডেল্টা এক্স বা ডি এক্স। লক্ষ্য করুন: ডি এক্স কিন্তু কোনো অলৌকিক অসীম ক্ষুদ্র ভূত নয়; এটি একটি বাস্তব, দৃশ্যমান, সসীম সংখ্যা—যেমন শূন্য দশমিক শূন্য এক বা শূন্য দশমিক এক!"
            },
            {
                "index": 4,
                "type": "p",
                "text": "এবার সবচেয়ে গুরুত্বপূর্ণ পার্থক্যটি খেয়াল করুন: ইনপুট ডি এক্স সরলে মূল বক্ররেখা বরাবর যে উল্লম্ব পরিবর্তন হয়, তা হলো ডেল্টা ওয়াই সমান এফ অফ এক্স যোগ ডি এক্স বিয়োগ এফ অফ এক্স। কিন্তু স্পর্শক সরলরেখা বরাবর যে উল্লম্ব পরিবর্তন হয়, ঠিক তাকেই বলা হয় ডি ওয়াই!"
            },
            {
                "index": 5,
                "type": "formula-box",
                "text": "জ্যামিতিক রূপ: ডেল্টা ওয়াই হলো বক্ররেখা বরাবর প্রকৃত পরিবর্তন, আর ডি ওয়াই সমান এফ প্রাইম অফ এক্স গুণ ডি এক্স হলো স্পর্শক রেখা বরাবর রৈখিক পরিবর্তন।"
            },
            {
                "index": 6,
                "type": "callout",
                "text": "বিরাট অন্তর্দৃষ্টি: স্পর্শক সরলরেখার জগতে ডি এক্স এবং ডি ওয়াই উভয়ই দুটি সাধারণ বাস্তব দৈর্ঘ্য। স্পর্শক রেখার খাড়া দৈর্ঘ্য ডি ওয়াই-কে ভূমির দৈর্ঘ্য ডি এক্স দিয়ে ভাগ করলে তা অবিকল ঢাল এফ প্রাইম অফ এক্স দেয়! স্পর্শকের তলে ডি ওয়াই বাই ডি এক্স শতভাগ একটি খাঁটি ভগ্নাংশ!"
            }
        ]
    },
    {
        "id": "sec-error-and-vanishing",
        "alias": "sec_03_error_and_vanishing",
        "title": "৩. ত্রুটি বিলোপ ও উচ্চতর ঘাত: কেন ডি এক্স স্কয়ার হারিয়ে যায়? (Vanishing Higher Powers)",
        "audio_file": "sec_03_error_and_vanishing.mp3",
        "cues_file": "sec_03_error_and_vanishing_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "তৃতীয় পরিচ্ছেদ: ত্রুটি বিলোপ ও উচ্চতর ঘাত—কেন ডি এক্স স্কয়ার হারিয়ে যায়?"
            },
            {
                "index": 1,
                "type": "p",
                "text": "এখন প্রশ্ন হলো: বক্ররেখার প্রকৃত পরিবর্তন ডেল্টা ওয়াই এবং স্পর্শকের রৈখিক পরিবর্তন ডি ওয়াই-এর মধ্যে যে ত্রুটি বা ব্যবধান থাকে, সেটি কত বড়?"
            },
            {
                "index": 2,
                "type": "p",
                "text": "টেইলর উপপাদ্য এবং বহুপদী বিশ্লেষণ থেকে আমরা জানি: ডেল্টা ওয়াই সমান এফ প্রাইম অফ এক্স ইনটু ডি এক্স, যোগ হাফ এফ ডাবল প্রাইম অফ এক্স ইনটু ডি এক্স স্কয়ার, যোগ উচ্চতর ঘাতসমূহ।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "অর্থাৎ ডেল্টা ওয়াই বিয়োগ ডি ওয়াই সমান হাফ এফ ডাবল প্রাইম অফ এক্স গুণ ডি এক্স স্কয়ার। এই পার্থক্যটি সরাসরি ডি এক্স স্কয়ার-এর সমানুপাতিক!"
            },
            {
                "index": 4,
                "type": "p",
                "text": "এবার সংখ্যার স্কেলিং নিয়ে ভাবুন: যদি ডি এক্স সমান শূন্য দশমিক শূন্য এক হয়, তবে ডি এক্স স্কয়ার হবে শূন্য দশমিক চারটা শূন্য এক! অর্থাৎ প্রথম ক্রমের পরিবর্তনের তুলনায় ত্রুটিটি একশ গুণ দ্রুত সংকুচিত হয়। ডি এক্স শূন্যের কাছাকাছি পৌঁছালে ত্রুটির অনুপাত পুরোপুরি শূন্য হয়ে যায়।"
            },
            {
                "index": 5,
                "type": "formula-box",
                "text": "সীমাস্থ রূপ: প্রথম ক্রমের পরিবর্তনের তুলনায় বক্রতার ত্রুটি দ্রুততর হারে বিলীন হওয়ায় সীমাস্থ অবস্থায় বক্ররেখার ঢাল ও স্পর্শক রেখার ঢাল অভিন্ন হয়ে ওঠে।"
            },
            {
                "index": 6,
                "type": "callout",
                "text": "কেন বীজগণিতীয় কাটাকাটি কাজ করে? কারণ চেইন রুল বা সাবস্টিটিউশনে আমরা মূলত স্পর্শকীয় রৈখিক রূপান্তরগুলোকে পরস্পরের সাথে গুণ করি। রৈখিক স্পর্শকের জগতে ভগ্নাংশ কাটাকাটি সম্পূর্ণ সুসংগত ও নিখুঁত।"
            },
            {
                "index": 7,
                "type": "p",
                "text": "তাহলে এবার ভাবা যাক, সমাকলনে ইন্টিগ্রাল চিহ্নের ভেতর ডি এক্স কী অর্থ বহন করে?"
            }
        ]
    },
    {
        "id": "sec-dx-in-integration",
        "alias": "sec_04_dx_in_integration",
        "title": "৪. সমাকলনে ডি এক্স: কেবল প্রতীক নয়, আয়তক্ষেত্রের বাস্তব প্রস্থ (dx in Integration)",
        "audio_file": "sec_04_dx_in_integration.mp3",
        "cues_file": "sec_04_dx_in_integration_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "চতুর্থ পরিচ্ছেদ: সমাকলনে ডি এক্স—কেবল প্রতীক নয়, আয়তক্ষেত্রের বাস্তব প্রস্থ।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "অনেক শিক্ষার্থী মনে করেন সমাকলন বা ইন্টিগ্রালে ডি এক্স কেবল একটি সমাপ্তি বন্ধনীর মতো—যা নির্দেশ করে চলকটি কোন অক্ষ বরাবর। কিন্তু এটি তার চেয়ে বহু গুণ বেশি বাস্তব ও জীবন্ত!"
            },
            {
                "index": 2,
                "type": "p",
                "text": "রিম্যান সমষ্টিতে আমরা ব্যবধিটিকে অসংখ্য ক্ষুদ্র অংশে ভাগ করি, যার প্রতিটির প্রস্থ ডেল্টা এক্স। প্রতিটি সরু আয়তক্ষেত্রের ক্ষেত্রফল হলো উচ্চতা গুণ প্রস্থ, অর্থাৎ এফ অফ এক্স ইনটু ডেল্টা এক্স।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "লাইবনিজ যখন ইন্টিগ্রাল চিহ্ন উদ্ভাবন করেন, তিনি লাতিন সুম্মা অর্থাৎ যোগফল শব্দের বড়হাতের এস-কে টেনে লম্বা করেছিলেন। আর ডি এক্স হলো সেই রিম্যান ফালির অতি ক্ষুদ্র ভিত্তি বা প্রস্থ।"
            },
            {
                "index": 4,
                "type": "p",
                "text": "ফলে ইন্টিগ্রাল এফ অফ এক্স ডি এক্স কোনো অলীক প্রতীক নয়; এটি অসীম সংখ্যক ক্ষেত্রফল ফালি এফ অফ এক্স গুণ ডি এক্স-এর একটি বাস্তব অবিচ্ছিন্ন যোগফল। যখন আমরা চলক প্রতিস্থাপন করি, ইউ সমান জি অফ এক্স ধরে ডি ইউ সমান জি প্রাইম অফ এক্স ডি এক্স লিখি, আমরা মূলত এক্স অক্ষের ফালির প্রস্থকে ইউ অক্ষের ফালির সাথে স্কেল করে নিচ্ছি।"
            },
            {
                "index": 5,
                "type": "formula-box",
                "text": "সমাকলনের রূপ: রিম্যান যোগফলের সীমায় ভিত্তি ডেল্টা এক্স সরাসরি ডিফারেনশিয়াল ডি এক্স-এ রূপান্তরিত হয়, এবং ডি ইউ সমান ডি ইউ বাই ডি এক্স গুণ ডি এক্স।"
            },
            {
                "index": 6,
                "type": "callout",
                "text": "ভৌত মাত্রা ও এককের সৌন্দর্য: পদার্থবিজ্ঞানে ডি এক্স-এর ভৌত গুরুত্ব অপরিসীম। যদি ভি অফ টি হয় মিটার প্রতি সেকেন্ডে বেগ এবং ডি টি হয় সেকেন্ডে সময়, তবে ভি অফ টি ডি টি-এর একক দাঁড়ায় মিটার! ডি টি না থাকলে সমাকলনের কোনো সঠিক ভৌত মাত্রা থাকত না।"
            }
        ]
    },
    {
        "id": "sec-modern-perspective",
        "alias": "sec_05_modern_perspective",
        "title": "৫. আধুনিক গণিতে ডি এক্স: স্পর্শক ভেক্টর ও ডিফারেনশিয়াল ফর্ম (Modern Differential Forms)",
        "audio_file": "sec_05_modern_perspective.mp3",
        "cues_file": "sec_05_modern_perspective_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "পঞ্চম পরিচ্ছেদ: আধুনিক গণিতে ডি এক্স—স্পর্শক ভেক্টর ও ডিফারেনশিয়াল ওয়ান-ফর্ম।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "বিশ শতকের আধুনিক গণিতবিদরা ডি এক্স-এর এই ধারণাকে আরও এক ধাপ এগিয়ে নিয়ে গেছেন, যাকে বলা হয় ডিফারেনশিয়াল ফর্ম।"
            },
            {
                "index": 2,
                "type": "p",
                "text": "সেখানে ডি এক্স-কে দেখা হয় একটি পরিমাপক যন্ত্র বা রৈখিক ফাংশনাল হিসেবে। আপনি এটিকে একটি স্পর্শক ভেক্টর ইনপুট দেবেন, আর এটি আপনাকে বলে দেবে সেই ভেক্টরটি এক্স অক্ষ বরাবর কতটুকু প্রসারিত হয়েছে।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "অতএব, ডি এক্স কোনো একক অচল ধারণা নয়। এটি একাধারে: প্রথমত, ইনপুটের একটি ছোট বাস্তব বিচ্যুতি। দ্বিতীয়ত, স্পর্শক রেখা বরাবর রৈখিক আসন্নায়নের ভিত্তি। তৃতীয়ত, সমাকলন ফালির অতি ক্ষুদ্র প্রস্থ ও মাত্রিক রূপক। এবং চতুর্থত, বহুমাত্রিক জ্যামিতিতে ভেক্টর পরিমাপক কভেক্টর বা ওয়ান-ফর্ম।"
            },
            {
                "index": 4,
                "type": "formula-box",
                "text": "আধুনিক রূপ: ডি এক্স অফ ভি সমান ভি এক্স, যা স্পর্শক ভেক্টরের অনুভূমিক উপাংশ পরিমাপক ওয়ান-ফর্ম হিসেবে কাজ করে।"
            },
            {
                "index": 5,
                "type": "callout",
                "text": "উপসংহার ও অন্তর্দৃষ্টি: পরের বার যখন কেউ বলবে ডি ওয়াই বাই ডি এক্স কোনো ভগ্নাংশ নয়, তখন মৃদু হেসে বলবেন: স্পর্শকের রৈখিক জগতে এটি একটি নিখুঁত খাঁটি ভগ্নাংশ, যা পরিবর্তনের হারকে জ্যামিতির পরম সত্যে প্রতিষ্ঠিত করে।"
            }
        ]
    }
]

# Safeguard check against any Latin characters in cue texts
latin_pattern = re.compile(r'[a-zA-Z]')

def verify_zero_latin():
    violations = []
    for sec in SECTIONS_CONFIG:
        for itm in sec["items"]:
            matches = latin_pattern.findall(itm["text"])
            if matches:
                violations.append((sec["id"], itm["index"], itm["text"], matches))
    if violations:
        for v in violations:
            print(f"❌ Latin characters detected in {v[0]} cue {v[1]}: {v[3]} -> '{v[2]}'")
        raise ValueError("Strict Phonetic Safeguard Failed: Found bare Latin letters in TTS text!")
    print("✅ Strict Phonetic Safeguard Passed: 100% clean Bengali phonetics with zero Latin characters.")

async def synthesize_all():
    verify_zero_latin()
    
    manifest_sections = {}
    
    for sec in SECTIONS_CONFIG:
        audio_path = os.path.join(OUTPUT_DIR, sec["audio_file"])
        cues_path = os.path.join(OUTPUT_DIR, sec["cues_file"])
        
        print(f"\n🎙️ Synthesizing Section: {sec['title']} -> {sec['audio_file']}...")
        
        item_cues = []
        current_time_ms = 0.0
        temp_files = []
        
        for item in sec["items"]:
            item_text = item["text"]
            idx = item["index"]
            temp_mp3 = os.path.join(OUTPUT_DIR, f"tmp_{sec['alias']}_{idx}.mp3")
            temp_files.append(temp_mp3)
            
            for attempt in range(5):
                try:
                    communicate = edge_tts.Communicate(item_text, voice=VOICE, rate=RATE, pitch=PITCH)
                    await communicate.save(temp_mp3)
                    if os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 1000:
                        break
                    else:
                        raise RuntimeError("File too small")
                except Exception as e:
                    print(f"Retry {attempt+1} for item {idx}: {e}")
                    await asyncio.sleep(1.5)
            
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
            
            # Natural teacher pause between items (350ms)
            current_time_ms += dur_ms + 350.0

        # Build concat file
        concat_list_file = os.path.join(OUTPUT_DIR, f"concat_{sec['alias']}.txt")
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for t_file in temp_files:
                abs_p = os.path.abspath(t_file).replace("\\", "/")
                f.write(f"file '{abs_p}'\n")
                
        concat_cmd = f'ffmpeg -y -f concat -safe 0 -i "{concat_list_file}" -c:a libmp3lame -b:a 192k "{audio_path}"'
        subprocess.run(concat_cmd, shell=True, check=True, capture_output=True)
        
        # Cleanup temp files
        for t_file in temp_files:
            if os.path.exists(t_file):
                os.remove(t_file)
        if os.path.exists(concat_list_file):
            os.remove(concat_list_file)
            
        total_duration_ms = round(current_time_ms - 350.0, 1)
        
        # Save individual cues JSON
        section_cues_data = {
            "section_id": sec["id"],
            "alias": sec["alias"],
            "title": sec["title"],
            "audio_file": sec["audio_file"],
            "total_duration_ms": total_duration_ms,
            "cues": item_cues
        }
        with open(cues_path, "w", encoding="utf-8") as f:
            json.dump(section_cues_data, f, ensure_ascii=False, indent=2)
            
        manifest_sections[sec["id"]] = section_cues_data
        print(f"✅ Finished {sec['id']}: Duration = {total_duration_ms} ms ({total_duration_ms/1000:.1f} s)")

    # Construct Master Audio Manifest
    manifest = {
        "course": "calculus",
        "lesson": "lesson_11",
        "title": "অধ্যায় ১১ — ডি এক্স এর প্রকৃত অর্থ (What does dx really mean?)",
        "voice": VOICE,
        "mode": "authentic_teacher",
        "sections": manifest_sections
    }
    
    manifest_json_path = os.path.join(OUTPUT_DIR, "manifest.json")
    with open(manifest_json_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        
    manifest_js_path = os.path.join(OUTPUT_DIR, "manifest.js")
    with open(manifest_js_path, "w", encoding="utf-8") as f:
        f.write("window.TEACHER_AUDIO_MANIFEST = " + json.dumps(manifest, ensure_ascii=False, indent=2) + ";\n")
        
    print(f"\n🎉 Master manifests created at:")
    print(f"  - {manifest_json_path}")
    print(f"  - {manifest_js_path}")

if __name__ == "__main__":
    asyncio.run(synthesize_all())
