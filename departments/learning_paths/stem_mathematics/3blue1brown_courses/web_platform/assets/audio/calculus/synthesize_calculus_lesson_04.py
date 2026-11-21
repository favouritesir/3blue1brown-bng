import asyncio
import os
import json
import subprocess
import edge_tts

VOICE = "bn-BD-PradeepNeural"
RATE = "-2%"
PITCH = "+0Hz"

OUTPUT_DIR = r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/calculus/lesson_04"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SECTIONS_CONFIG = [
    {
        "id": "sec-product-intro",
        "alias": "sec_01_product_intro",
        "title": "১. প্রোডাক্ট রুল ও সাধারণ ভুল ধারণা (The Product Rule & Common Misconceptions)",
        "audio_file": "sec_01_product_intro.mp3",
        "cues_file": "sec_01_product_intro_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "প্রথম পরিচ্ছেদ: প্রোডাক্ট রুল ও গুণফলের অন্তরজের সাধারণ বিভ্রান্তি।"
            },
            {
                "index": 1,
                "type": "chapter-quote",
                "text": "উদ্ধৃতি: প্রাকৃতিক পরিবর্তনের রহস্য কোনো একক নিয়মে বাঁধা নয়; একাধিক পরিবর্তনের মিথস্ক্রিয়া থেকেই জন্ম নেয় ক্যালকুলাসের প্রকৃত সৌন্দর্য।"
            },
            {
                "index": 2,
                "type": "p",
                "text": "শিক্ষার্থী বন্ধুরা, ক্যালকুলাসের চতুর্থ অধ্যায়ে তোমাদের স্বাগতম। আজকের আলোচনার কেন্দ্রে রয়েছে ক্যালকুলাসের সবচেয়ে শক্তিশালী দুটি অস্ত্র: প্রোডাক্ট রুল এবং চেইন রুল।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "ধরা যাক, আপনাকে দুটি ফাংশন এফ অব এক্স এবং জি অব এক্স এর গুণফলের অন্তরজ বের করতে বলা হলো। নতুন যেকোনো শিক্ষার্থীর মনে প্রথমেই খুব সহজ একটি ধারণা আসে—যদি যোগফলের অন্তরজ আলাদা আলাদা অন্তরজের যোগফল হয়, তবে গুণফলের অন্তরজও হয়তো হবে এফ প্রাইম গুণ জি প্রাইম!"
            },
            {
                "index": 4,
                "type": "callout",
                "text": "সতর্কবার্তা: এটি ক্যালকুলাসের সবচেয়ে বিপজ্জনক ফাঁদ! আপাতদৃষ্টিতে অত্যন্ত নিখুঁত ও প্রতিসম মনে হলেও, এফ গুণ জি এর অন্তরজ কখনোই এফ প্রাইম গুণ জি প্রাইম নয়।"
            },
            {
                "index": 5,
                "type": "p",
                "text": "কেন এই অনুমানটি ভুল এবং কেন আসল সূত্রটি দেখতে কিছুটা অদ্ভুত ও অপ্রতিসম? পাঠ্যবইয়ে লেখা থাকে: বাম গুণ ডানের ডেরিভেটিভ, যোগ ডান গুণ বামের ডেরিভেটিভ। কিন্তু এই নিয়মের পেছনের জ্যামিতিক সত্যটি কী? চলুন একটি চমৎকার আয়তক্ষেত্রের মাধ্যমে তা উন্মোচন করা যাক।"
            }
        ]
    },
    {
        "id": "sec-rectangle-geometry",
        "alias": "sec_02_rectangle_geometry",
        "title": "২. আয়তক্ষেত্রের বৃদ্ধি ও প্রোডাক্ট রুলের জ্যামিতিক প্রমাণ (Geometric Proof via Rectangle Expansion)",
        "audio_file": "sec_02_rectangle_geometry.mp3",
        "cues_file": "sec_02_rectangle_geometry_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "দ্বিতীয় পরিচ্ছেদ: আয়তক্ষেত্রের সম্প্রসারণ ও প্রোডাক্ট রুলের প্রমাণ।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "দুটি রাশির গুণফলকে জ্যামিতিকভাবে বোঝার শ্রেষ্ঠ রূপ হলো একটি আয়তক্ষেত্র কল্পনা করা। মনে করি, আয়তক্ষেত্রের উচ্চতা হলো এফ অব এক্স এবং এর ভূমি হলো জি অব এক্স। সুতরাং আয়তক্ষেত্রের মোট ক্ষেত্রফল হলো এফ অব এক্স গুণ জি অব এক্স।"
            },
            {
                "index": 2,
                "type": "figure",
                "text": "চিত্র এক-এ লক্ষ্য করুন: এফ এবং জি বাহুবিশিষ্ট একটি আয়তক্ষেত্র, যার দুই পাশে ডি এফ এবং ডি জি বৃদ্ধির ফলে তিনটি নতুন ক্ষেত্রফল সৃষ্টি হয়েছে।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "এবার যদি মূল ইনপুট এক্স-কে খুব সামান্য পরিমাণ বৃদ্ধি ডি এক্স দেওয়া হয়, তবে এফ বাহুটি সামান্য বেড়ে হয়ে যাবে এফ যোগ ডি এফ, এবং একই সাথে জি বাহুটিও বেড়ে হয়ে যাবে জি যোগ ডি জি।"
            },
            {
                "index": 4,
                "type": "p",
                "text": "তাহলে পুরো আয়তক্ষেত্রের ক্ষেত্রফল ঠিক কতটুকু বৃদ্ধি পেল? জ্যামিতিকভাবে তাকালে স্পষ্ট দেখা যায়, নতুন ক্ষেত্রফলটি তিনটি আলাদা খণ্ডে বিভক্ত:"
            },
            {
                "index": 5,
                "type": "callout",
                "text": "তিনটি অংশের বিভাজন: প্রথমত, ওপরের লম্বা ফালি, যার ক্ষেত্রফল জি গুণ ডি এফ। দ্বিতীয়ত, ডান পাশের খাড়া ফালি, যার ক্ষেত্রফল এফ গুণ ডি জি। এবং তৃতীয়ত, ওপরের কোণায় পড়ে থাকা পুঁচকে বর্গাকার কোণা, যার ক্ষেত্রফল ডি এফ গুণ ডি জি।"
            },
            {
                "index": 6,
                "type": "formula-box",
                "text": "ক্ষেত্রফলের মোট বৃদ্ধি: ডি অফ এফ জি সমান এফ ডি জি, যোগ জি ডি এফ, যোগ ডি এফ গুণ ডি জি।"
            },
            {
                "index": 7,
                "type": "p",
                "text": "এবার অন্তরজ বের করতে আমরা পুরো সমীকরণটিকে ডি এক্স দিয়ে ভাগ করব। লক্ষ্য করুন, প্রথম পদটি হয় এফ ইনটু ডি জি ডি এক্স; দ্বিতীয় পদটি হয় জি ইনটু ডি এফ ডি এক্স। কিন্তু কোণার অংশটিতে রয়েছে ডি এফ গুণ ডি জি ভাগ ডি এক্স!"
            },
            {
                "index": 8,
                "type": "p",
                "text": "ডি এক্স এর মান যত শূন্যের কাছাকাছি পৌঁছাবে, ডি এফ ও ডি জি উভয়ই শূন্যের দিকে ধাবিত হবে। ফলে দুটি অতিক্ষুদ্রের গুণফল হওয়ার কারণে কোণার এই অংশটি ফালি দুটির তুলনায় সীমাহীন ক্ষুদ্র হয়ে বিলীন হয়ে যায়!"
            },
            {
                "index": 9,
                "type": "formula-box",
                "text": "চূড়ান্ত প্রোডাক্ট রুল: ডি ডি এক্স অফ এফ জি সমান এফ ইনটু ডি জি বাই ডি এক্স, যোগ জি ইনটু ডি এফ বাই ডি এক্স।"
            },
            {
                "index": 10,
                "type": "p",
                "text": "অসাধারণ! মুখস্থ করার কোনো প্রয়োজনই নেই। একটি বাহু স্থির থাকা অবস্থায় অন্য বাহুর প্রসারণই তৈরি করে দুটি আয়তাকার ফালি, যা সরাসরি প্রোডাক্ট রুলের দুটি পদের জন্ম দেয়।"
            }
        ]
    },
    {
        "id": "sec-chain-intro",
        "alias": "sec_03_chain_rule",
        "title": "৩. চেইন রুল ও তিনটি সংখ্যা রেখা (The Chain Rule & Three Number Lines)",
        "audio_file": "sec_03_chain_rule.mp3",
        "cues_file": "sec_03_chain_rule_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "তৃতীয় পরিচ্ছেদ: চেইন রুল ও ফাংশনের সংযোজনের দৃশ্যরূপ।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "এবার আসা যাক ক্যালকুলাসের দ্বিতীয় জাদুকরী নিয়মে—চেইন রুল। এটি ব্যবহৃত হয় যখন একটি ফাংশনের ফলাফল সরাসরি আরেকটি ফাংশনের ভেতরে ইনপুট হিসেবে প্রবেশ করে, অর্থাৎ এফ অফ জি অফ এক্স।"
            },
            {
                "index": 2,
                "type": "p",
                "text": "যেমন সাইন অফ এক্স স্কয়ার। এখানে ভেতরের ফাংশন হলো জি সমান এক্স স্কয়ার, আর বাইরের ফাংশন হলো এফ সমান সাইন।"
            },
            {
                "index": 3,
                "type": "figure",
                "text": "চিত্র দুই-এ দেখুন: পরপর তিনটি সমান্তরাল সংখ্যা রেখা—প্রথমটি ইনপুট এক্স, দ্বিতীয়টি মধ্যবর্তী জি, এবং তৃতীয়টি চূড়ান্ত আউটপুট এফ।"
            },
            {
                "index": 4,
                "type": "p",
                "text": "যদি আমরা প্রথম রেখায় এক্স-কে সামান্য একটু নাড়িয়ে ডি এক্স করি, তবে ডেরিভেটিভের সংজ্ঞামতে দ্বিতীয় রেখায় জি সরে যাবে ডি জি পরিমাণ, যা হলো জি প্রাইম এক্স গুণ ডি এক্স।"
            },
            {
                "index": 5,
                "type": "callout",
                "text": "চেইন বিক্রিয়ার মূল চাবিকাঠি: জি-এর এই অতি ক্ষুদ্র পরিবর্তন ডি জি সরাসরি পরবর্তী ফাংশন এফ-এর ইনপুট বৃদ্ধি হিসেবে কাজ করে! তাই তৃতীয় রেখায় এফ-এর যে পরিবর্তন ঘটবে, তা হবে এফ প্রাইম জি গুণ ডি জি।"
            },
            {
                "index": 6,
                "type": "formula-box",
                "text": "মান প্রতিস্থাপন: ডি এফ সমান এফ প্রাইম অফ জি, গুণ জি প্রাইম অফ এক্স, গুণ ডি এক্স।"
            },
            {
                "index": 7,
                "type": "p",
                "text": "উভয়পক্ষকে ডি এক্স দিয়ে ভাগ করলেই আমরা পাই ক্যালকুলাসের অমর চেইন রুল: ডি এফ বাই ডি এক্স সমান ডি এফ বাই ডি জি গুণ ডি জি বাই ডি এক্স।"
            },
            {
                "index": 8,
                "type": "p",
                "text": "লাইবনিজের চমৎকার ভগ্নাংশ প্রতীকে তাকালে মনে হয় মাঝখানের ডি জি দুটি যেন কাটাকাটি চলে গেল! এটি স্রেফ কাকতালীয় নয়; এটি ক্ষুদ্রাতিক্ষুদ্র অনুপাতের নিখুঁত ধারাবাহিকতা নির্দেশ করে।"
            }
        ]
    },
    {
        "id": "sec-gears-examples",
        "alias": "sec_04_gears_examples",
        "title": "৪. গিয়ার অ্যানালজি ও সমন্বিত প্রয়োগ (Gear Ratio Analogy & Real Examples)",
        "audio_file": "sec_04_gears_examples.mp3",
        "cues_file": "sec_04_gears_examples_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "চতুর্থ পরিচ্ছেদ: গিয়ার রূপক ও বাস্তব গাণিতিক প্রয়োগ।"
            },
            {
                "index": 1,
                "type": "chapter-quote",
                "text": "গিয়ার রূপক: গিয়ার এ যদি গিয়ার বি-কে ঘোরায়, এবং বি যদি সি-কে ঘোরায়, তবে সি-এর ঘূর্ণন গতি হবে দুটি গিয়ার অনুপাতের সাধারণ গুণফল।"
            },
            {
                "index": 2,
                "type": "p",
                "text": "ভাবুন তিনটি দাঁতযুক্ত গিয়ার চাকা। গিয়ার এ এক পাক ঘুরলে যদি গিয়ার বি দুই পাক ঘোরে, এবং বি এক পাক ঘুরলে যদি সি তিন পাক ঘোরে; তবে এ এক পাক ঘুরলে সি মোট কত পাক ঘুরবে? সহজ হিসাব: দুই গুণ তিন, অর্থাৎ ছয় পাক! চেইন রুল মূলত এই গুণন প্রক্রিয়া ছাড়া আর কিছুই নয়।"
            },
            {
                "index": 3,
                "type": "figure",
                "text": "চিত্র তিন-এ দেখুন: পরস্পর সংযুক্ত তিনটি গিয়ার এবং গতি সঞ্চালনের ধারাবাহিক বিবর্ধন অনুপাত।"
            },
            {
                "index": 4,
                "type": "p",
                "text": "চলুন আমাদের সাইন অফ এক্স স্কয়ার উদাহরণটিতে এটি প্রয়োগ করে দেখা যাক। এখানে বাইরের ফাংশন সাইন জি-এর ডেরিভেটিভ হলো কস জি, অর্থাৎ কস অফ এক্স স্কয়ার। আর ভেতরের ফাংশন এক্স স্কয়ারের ডেরিভেটিভ হলো টু এক্স।"
            },
            {
                "index": 5,
                "type": "formula-box",
                "text": "চূড়ান্ত সমাধান: ডি ডি এক্স অফ সাইন অফ এক্স স্কয়ার সমান কস অফ এক্স স্কয়ার গুণ টু এক্স।"
            },
            {
                "index": 6,
                "type": "callout",
                "text": "সারসংক্ষেপ ও অন্তর্দৃষ্টি: প্রোডাক্ট রুল শেখায় কীভাবে দুটি স্বাধীন প্রসারণের যোগফল ক্ষেত্রফলের পরিবর্তন ঘটায়, আর চেইন রুল শেখায় কীভাবে ধারাবাহিক পরিবর্তনের হারগুলো পরস্পরের সাথে গুণ হয়ে সামগ্রিক সংবেদনশীলতা তৈরি করে।"
            },
            {
                "index": 7,
                "type": "p",
                "text": "ক্যালকুলাসের গভীরতম তৃপ্তি লুকিয়ে আছে এই দৃশ্যগুলো নিজের চোখে দেখতে পাওয়ার মাঝে। যখন আপনি গণিতের ভেতরের জ্যামিতিটি স্পষ্ট অনুভব করতে পারবেন, তখন কঠিনতম সমীকরণটিও আপনার কাছে অর্থবহ ও জীবন্ত হয়ে উঠবে।"
            }
        ]
    }
]

async def synthesize_all():
    manifest_sections = {}
    
    for sec in SECTIONS_CONFIG:
        audio_path = os.path.join(OUTPUT_DIR, sec["audio_file"])
        cues_path = os.path.join(OUTPUT_DIR, sec["cues_file"])
        
        if os.path.exists(audio_path) and os.path.exists(cues_path) and os.path.getsize(audio_path) > 10000:
            print(f"⏩ Section {sec['title']} ({sec['audio_file']}) already generated. Reading existing cues...")
            with open(cues_path, "r", encoding="utf-8") as f:
                section_cues_data = json.load(f)
                manifest_sections[sec["id"]] = section_cues_data
            continue
            
        print(f"\n🎙️ Synthesizing Section: {sec['title']} -> {sec['audio_file']}...")
        
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
                    communicate = edge_tts.Communicate(item_text, voice=VOICE, rate=RATE, pitch=PITCH)
                    await communicate.save(temp_mp3)
                    if os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 1000:
                        print(f"  [{idx+1}/{len(sec['items'])}] Generated cue {idx}")
                        break
                    else:
                        raise RuntimeError("File too small")
                except Exception as e:
                    print(f"Retry {attempt+1} for item {idx}: {e}")
                    await asyncio.sleep(2.0)
            
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
        concat_list_file = os.path.join(OUTPUT_DIR, f"concat_{sec['id']}.txt")
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
        "lesson": "lesson_04",
        "title": "অধ্যায় ০৪ — চেইন রুল ও প্রোডাক্ট রুলের চাক্ষুষ রূপ (Visualizing the Chain Rule and Product Rule)",
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
