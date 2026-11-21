import asyncio
import os
import json
import subprocess
import edge_tts

VOICE = "bn-BD-PradeepNeural"
RATE = "-2%"
PITCH = "+0Hz"

OUTPUT_DIR = r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/calculus/lesson_02"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SECTIONS_CONFIG = [
    {
        "id": "sec-paradox",
        "alias": "sec_01_paradox",
        "title": "১. তাৎক্ষণিক বেগ ও প্যারাডক্স (Instantaneous Velocity & The Paradox)",
        "audio_file": "sec_01_paradox.mp3",
        "cues_file": "sec_01_paradox_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "প্রথম পরিচ্ছেদ: তাৎক্ষণিক বেগ ও অন্তরীকরণের প্যারাডক্স।"
            },
            {
                "index": 1,
                "type": "chapter-quote",
                "text": "উদ্ধৃতি: সময়ের কোনো একটি একক মুহূর্তে সবকিছুই স্থির—তাহলে সেই স্থির মুহূর্তে গতির অস্তিত্ব থাকে কীভাবে?"
            },
            {
                "index": 2,
                "type": "p",
                "text": "শিক্ষার্থী বন্ধুরা, ক্যালকুলাসের দ্বিতীয় অধ্যায়ে তোমাদের স্বাগত জানাচ্ছি। ধরা যাক, তোমরা একটি সুন্দর হাইওয়ে দিয়ে গাড়ি চালিয়ে যাচ্ছ। হঠাৎ ড্যাশবোর্ডের স্পিডোমিটারের দিকে চোখ পড়ল এবং দেখলে কাঁটাটি ঠিক ষাট কিলোমিটার প্রতি ঘণ্টার ঘরে স্থির হয়ে আছে।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "কিন্তু একটু গভীরভাবে ভেবে দেখুন: এই ষাট কিলোমিটার প্রতি ঘণ্টা আসলে কীসের পরিমাপ? আমরা ছোটবেলা থেকেই জানি, বেগ মানে হলো অতিক্রান্ত দূরত্ব ভাগ প্রয়োজনীয় সময়। অর্থাৎ দূরত্ব ডেল্টা এস-কে সময়ের ব্যবধান ডেল্টা টি দিয়ে ভাগ করলে বেগ পাওয়া যায়।"
            },
            {
                "index": 4,
                "type": "figure",
                "text": "চিত্র প্রদর্শনী: চলন্ত গাড়ির স্পিডোমিটার এবং দূরত্বের লেখচিত্র—সময়ের যেকোনো মুহূর্তে তাৎক্ষণিক বেগের অস্তিত্ব।"
            },
            {
                "index": 5,
                "type": "p",
                "text": "এবার ভাবুন, একটি সুনির্দিষ্ট একক মুহূর্তের কথা—যেমন যাত্রা শুরুর ঠিক পাঁচ সেকেন্ডের মাথায়। সেই সুনির্দিষ্ট মুহূর্তে সময়ের কোনো ব্যবধান নেই, অর্থাৎ ডেল্টা টি সমান শূন্য। আর যদি সময়ই না থাকে, তবে গাড়িটি কোনো দূরত্বও অতিক্রম করতে পারে না, ফলে ডেল্টা এস সমানও শূন্য।"
            },
            {
                "index": 6,
                "type": "callout",
                "text": "বিশেষ নোট: অবকলনের কেন্দ্রীয় প্যারাডক্স—একটি একক মুহূর্তে যদি পরিবর্তনই না ঘটে, তবে শূন্য ভাগ শূন্য তো সম্পূর্ণ অনির্ণেয়! তাহলে স্পিডোমিটার কীভাবে সেই মুহূর্তে একটি নিশ্চিত সংখ্যা ষাট নির্দেশ করে?"
            },
            {
                "index": 7,
                "type": "p",
                "text": "এটিই হলো সেই বিখ্যাত প্যারাডক্স। একটি স্থির ছবিতে সবকিছু নিথর, কোনো গতি নেই। তাহলে গতির পরিমাপ কীভাবে একটি একক বিন্দুতে অবস্থান করতে পারে? এই ধাঁধার উত্তর খুঁজতেই জন্ম হয়েছিল ক্যালকুলাসের!"
            }
        ]
    },
    {
        "id": "sec-derivative-meaning",
        "alias": "sec_02_derivative_meaning",
        "title": "২. ডেরিভেটিভ কী? ডি টি ও ডি এস (What is a Derivative? dt and ds)",
        "audio_file": "sec_02_derivative_meaning.mp3",
        "cues_file": "sec_02_derivative_meaning_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "দ্বিতীয় পরিচ্ছেদ: ডেরিভেটিভের আসল অর্থ—ডি টি ও ডি এস এর অনুপাত।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "প্যারাডক্সটির চমৎকার সমাধান হলো: ক্যালকুলাস কখনো শূন্য দিয়ে শূন্যকে ভাগ করে না! বরং ক্যালকুলাস এমন এক সীমাস্থ প্রক্রিয়ার কথা বলে যা শূন্যের দিকে ধাবমান।"
            },
            {
                "index": 2,
                "type": "p",
                "text": "মনে করি, পাঁচ সেকেন্ড সময়ের পর আমরা অত্যন্ত ক্ষুদ্র একটি সময় ব্যবধান বিবেচনা করলাম, যাকে আমরা নাম দিলাম ডি টি। এই অতি সংক্ষিপ্ত সময়ে গাড়িটি খুব সামান্য একটু পথ অতিক্রম করল, যাকে আমরা বলছি ডি এস।"
            },
            {
                "index": 3,
                "type": "formula-box",
                "text": "গাণিতিক সূত্র: ক্ষুদ্র ব্যবধানে গড় বেগ সমান ডি এস বাই ডি টি।"
            },
            {
                "index": 4,
                "type": "p",
                "text": "এখানে ডি টি কিন্তু শূন্য নয়, বরং শূন্যের খুব কাছাকাছি—হয়তো এক সেকেন্ডের এক হাজার ভাগের এক ভাগ। ফলে এই অতি ক্ষুদ্র ব্যবধানে ডি এস ভাগ ডি টি আমাদের একটি প্রকৃত গড় বেগ প্রদান করে।"
            },
            {
                "index": 5,
                "type": "callout",
                "text": "বিশেষ নোট: ডেরিভেটিভের মূল রহস্য—ডি টি এর মান আমরা যতই ক্ষুদ্র থেকে ক্ষুদ্রতর করি না কেন, ডি এস বাই ডি টি এর অনুপাতটি হারিয়ে যায় না; বরং এটি একটি সুনির্দিষ্ট মানের দিকে ধাবিত হয়। এই সীমাস্থ মানটিই হলো ডেরিভেটিভ বা তাৎক্ষণিক বেগ।"
            },
            {
                "index": 6,
                "type": "p",
                "text": "তাই স্পিডোমিটার আসলে সময়ের একক মুহূর্তে গতি মাপে না; বরং এটি অত্যন্ত ক্ষুদ্র সময় ব্যবধানে সম্ভাব্য পরিবর্তনের শ্রেষ্ঠ সুষম আসন্নায়ন নির্দেশ করে।"
            },
            {
                "index": 7,
                "type": "p",
                "text": "গণিতের ভাষায়, দূরত্বের ফাংশন এস অব টি-এর পরিবর্তনের হার হলো ডি এস বাই ডি টি। ডি কথাটি এসেছে ডিফারেন্স বা ক্ষুদ্র পার্থক্য থেকে।"
            }
        ]
    },
    {
        "id": "sec-tangent-zoom",
        "alias": "sec_03_tangent_zoom",
        "title": "৩. জ্যামিতিক স্পর্শক ও গ্রাফ জুম (Geometric Tangent & Graph Zooming)",
        "audio_file": "sec_03_tangent_zoom.mp3",
        "cues_file": "sec_03_tangent_zoom_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "তৃতীয় পরিচ্ছেদ: জ্যামিতিক স্পর্শক ও বক্ররেখা জুম করার জাদু।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "ডেরিভেটিভের এই চমৎকার ভাবনাটিকে জ্যামিতিক লেখচিত্রে কীভাবে কল্পনা করা যায়? ধরা যাক, আনুভূমিক সময় অক্ষে টি এবং উল্লম্ব অক্ষে দূরত্ব এস স্থাপন করে আমরা একটি বক্ররেখা আঁকলাম।"
            },
            {
                "index": 2,
                "type": "figure",
                "text": "চিত্র প্রদর্শনী: সময়ের বিপরীতে দূরত্বের বক্ররেখা এবং ক্ষুদ্র ডি টি ও ডি এস দ্বারা গঠিত অন্তরক ত্রিভুজ।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "বক্ররেখার যেকোনো দুটি বিন্দুর মধ্যে যদি আমরা একটি ছেদক রেখা বা সিক্যান্ট লাইন টানি, তবে তার ঢাল হবে খাড়া উচ্চতা ডেল্টা এস ভাগ আনুভূমিক দৈর্ঘ্য ডেল্টা টি।"
            },
            {
                "index": 4,
                "type": "p",
                "text": "এবার গ্রান্ট স্যান্ডারসনের অন্যতম প্রিয় ভিজ্যুয়াল কৌশলটি লক্ষ্য করুন: লেখচিত্রের যেকোনো একটি নির্দিষ্ট বিন্দুতে অসম্ভব জুম করতে থাকুন। যতই জুম করবেন, সেই বাঁকা বক্ররেখাটি কিন্তু আর বাঁকা থাকবে না—এটি দেখতে প্রায় একটি নিখুঁত সরলরেখার মতো হয়ে যাবে!"
            },
            {
                "index": 5,
                "type": "callout",
                "text": "বিশেষ নোট: বক্ররেখার স্থানীয় রৈখিকতা—অত্যন্ত ক্ষুদ্র পরিসরে প্রতিটি মসৃণ বক্ররেখাই স্থানীয়ভাবে একটি সরলরেখা। আর সেই সরলরেখার যে ঢাল, তা-ই হলো ওই বিন্দুতে অঙ্কিত স্পর্শক রেখা বা ট্যানজেন্টের ঢাল।"
            },
            {
                "index": 6,
                "type": "p",
                "text": "অতএব, স্পর্শকের ঢাল আর কিছুই নয়—তা হলো ডি এস ভাগ ডি টি। পরিবর্তনের হারকে চোখে দেখার সবচেয়ে শক্তিশালী রূপ হলো এই স্পর্শক রেখার ঢাল।"
            }
        ]
    },
    {
        "id": "sec-x2-geometry",
        "alias": "sec_04_x2_geometry",
        "title": "৪. এক্স স্কয়ারের অন্তরীকরণ জ্যামিতি (Geometry of the Derivative of x^2)",
        "audio_file": "sec_04_x2_geometry.mp3",
        "cues_file": "sec_04_x2_geometry_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "চতুর্থ পরিচ্ছেদ: এক্স স্কয়ারের অন্তরীকরণ জ্যামিতিক দৃষ্টিতে।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "চলুন এবার একটি বাস্তব বীজগণিতীয় ফাংশন এফ অব এক্স সমান এক্স স্কয়ার নিয়ে জ্যামিতিক পরীক্ষা চালানো যাক। মুখস্থ সূত্র বলছে এর ডেরিভেটিভ টু এক্স। কিন্তু কেন টু এক্স?"
            },
            {
                "index": 2,
                "type": "figure",
                "text": "চিত্র প্রদর্শনী: এক্স বাহুবিশিষ্ট বর্গক্ষেত্রের দুই পাশে ডি এক্স প্রস্থের দুটি আয়তাকার ফালি এবং কোণায় অতিক্ষুদ্র বর্গক্ষেত্র।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "কল্পনা করুন একটি বর্গক্ষেত্র, যার প্রতিটি বাহুর দৈর্ঘ্য এক্স। তাহলে তার ক্ষেত্রফল হবে এক্স স্কয়ার। এবার বর্গক্ষেত্রের দৈর্ঘ্য ও প্রস্থ উভয় দিকে অতি সামান্য বৃদ্ধি ডি এক্স যোগ করা হলো।"
            },
            {
                "index": 4,
                "type": "p",
                "text": "প্রশ্ন হলো, ক্ষেত্রফলের মোট বৃদ্ধি ডি এফ কতটুকু হবে? চিত্রে তাকালে দেখা যায়, নতুন ক্ষেত্রফল তিনটি অংশে বিভক্ত হয়েছে।"
            },
            {
                "index": 5,
                "type": "formula-box",
                "text": "গাণিতিক সমীকরণ: মোট বৃদ্ধি ডি এফ সমান দুটি ফালির ক্ষেত্রফল টু এক্স গুণ ডি এক্স, যোগ কোণার অতি ক্ষুদ্র অংশ ডি এক্স স্কয়ার।"
            },
            {
                "index": 6,
                "type": "p",
                "text": "এবার উভয়পক্ষকে ডি এক্স দিয়ে ভাগ করলে আমরা পরিবর্তনের হার পাই: ডি এফ বাই ডি এক্স সমান টু এক্স যোগ ডি এক্স।"
            },
            {
                "index": 7,
                "type": "callout",
                "text": "বিশেষ নোট: ক্ষুদ্রাতিক্ষুদ্রের বিলোপ—ডি এক্স এর মান যখন শূন্যের দিকে ধাবিত হয়, তখন একা পড়ে থাকা ডি এক্স অংশটি পুরোপুরি নগণ্য হয়ে মিলিয়ে যায়। কিন্তু মূল দুই পাশের ফালির অনুপাত টু এক্স অক্ষত থেকে যায়!"
            },
            {
                "index": 8,
                "type": "p",
                "text": "এভাবেই আমরা পাই এক্স স্কয়ারের ডেরিভেটিভ সমান টু এক্স। এটি কোনো অলৌকিক জাদু নয়—বরং দুটি আয়তাকার ফালির উন্মোচিত জ্যামিতিক রূপ!"
            }
        ]
    }
]

async def synthesize_section(sec):
    audio_path = os.path.join(OUTPUT_DIR, sec["audio_file"])
    cues_path = os.path.join(OUTPUT_DIR, sec["cues_file"])
    
    if os.path.exists(audio_path) and os.path.exists(cues_path) and os.path.getsize(audio_path) > 10000:
        print(f"⏩ Section {sec['title']} ({sec['audio_file']}) already generated. Reading existing cues...")
        with open(cues_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["cues"], data["total_duration_ms"]

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
        
    with open(cues_path, "w", encoding="utf-8") as f:
        json.dump({
            "section_id": sec["id"],
            "alias": sec["alias"],
            "title": sec["title"],
            "audio_file": sec["audio_file"],
            "total_duration_ms": round(current_time_ms, 1),
            "cues": item_cues
        }, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Generated {sec['audio_file']} ({round(current_time_ms/1000, 2)}s, {len(item_cues)} cues)")
    return item_cues, round(current_time_ms, 1)

async def main():
    print("======================================================================")
    print("Master Bengali Teacher Audio Synthesis — Calculus Lesson 02")
    print("Voice: bn-BD-PradeepNeural | Mode: Authentic Warm Math Educator")
    print("======================================================================")
    
    manifest_data = {
        "course": "calculus",
        "lesson": "lesson_02",
        "title": "অধ্যায় ০২ — অবকলনের প্যারাডক্স: তাৎক্ষণিক পরিবর্তনের হার",
        "voice": VOICE,
        "mode": "authentic_teacher",
        "sections": {}
    }
    
    for sec in SECTIONS_CONFIG:
        item_cues, total_dur = await synthesize_section(sec)
        
        sec_dict = {
            "section_id": sec["id"],
            "alias": sec["alias"],
            "title": sec["title"],
            "audio_file": sec["audio_file"],
            "total_duration_ms": total_dur,
            "cues": item_cues
        }
        
        # Dual-key registration for bulletproof DOM matching
        manifest_data["sections"][sec["id"]] = sec_dict
        manifest_data["sections"][sec["alias"]] = sec_dict
        
    # Write manifest.json
    manifest_json_path = os.path.join(OUTPUT_DIR, "manifest.json")
    with open(manifest_json_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)
    print(f"\n🎉 manifest.json generated at {manifest_json_path}!")
    
    # Write manifest.js (for offline file:// without CORS blockage)
    manifest_js_path = os.path.join(OUTPUT_DIR, "manifest.js")
    with open(manifest_js_path, "w", encoding="utf-8") as f:
        f.write("window.TEACHER_AUDIO_MANIFEST = " + json.dumps(manifest_data, ensure_ascii=False, indent=2) + ";\n")
    print(f"🎉 manifest.js generated at {manifest_js_path}!")

if __name__ == "__main__":
    asyncio.run(main())
