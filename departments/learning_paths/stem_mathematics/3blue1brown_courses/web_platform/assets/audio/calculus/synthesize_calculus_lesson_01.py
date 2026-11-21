import asyncio
import os
import json
import subprocess
import edge_tts

VOICE = "bn-BD-PradeepNeural"
RATE = "-2%"
PITCH = "+0Hz"

OUTPUT_DIR = r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/calculus/lesson_01"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SECTIONS_CONFIG = [
    {
        "id": "sec-intro",
        "title": "ক্যালকুলাসের সারমর্ম ও ভূমিকা",
        "audio_file": "sec_01_intro.mp3",
        "cues_file": "sec_01_intro_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "প্রথম পরিচ্ছেদ: গণিতের মূল কৌশল, সহজ অংশে বিভাজন।"
            },
            {
                "index": 1,
                "type": "chapter-quote",
                "text": "বিখ্যাত গণিতবিদ ডেভিড হিলবার্ট বলেছিলেন: গণিত চর্চার মূল শিল্পই হলো এমন একটি বিশেষ ক্ষেত্র খুঁজে বের করা, যার ভেতরে সার্বজনীনতার সমস্ত বীজ সুপ্ত থাকে।"
            },
            {
                "index": 2,
                "type": "p",
                "text": "সাধারণত কলেজ বা বিশ্ববিদ্যালয়ে ক্যালকুলাস শেখানোর সময় শিক্ষার্থীদের একগাদা কঠিন সূত্র মুখস্থ করতে দেওয়া হয়—যেমন এক্স স্কয়ারের ডেরিভেটিভ টু এক্স, চেইন রুল, প্রোডাক্ট রুল কিংবা সমাকলনের তালিকা। কিন্তু এই সূত্রগুলোর পেছনে মূল যে প্রাণবন্ত ভাবনা বা গভীর দর্শন লুকিয়ে আছে, তা বেশিরভাগ সময় আলোচনায় আসে না।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "ক্যালকুলাসের মূল সারমর্ম বুঝতে হলে আমাদের জানতে হবে গণিতবিদদের সবচেয়ে শক্তিশালী কৌশলটি।"
            },
            {
                "index": 4,
                "type": "callout",
                "text": "বিশেষ দ্রষ্টব্য, ক্যালকুলাসের কেন্দ্রীয় দর্শন: যেকোনো জটিল ও দুর্বোধ্য সমস্যাকে অসংখ্য ক্ষুদ্রাতিক্ষুদ্র এবং সহজ অংশে ভাগ করা, প্রতিটির জন্য একটি ভালো আসন্নায়ন তৈরি করা, এবং তারপর সীমাস্থ অবস্থায় সেগুলোকে পুনরায় একত্রিত করে নিখুঁত সমাধানে পৌঁছানো।"
            },
            {
                "index": 5,
                "type": "p",
                "text": "এই পুরো যাত্রায় দুটি প্রধান অস্ত্র বারবার ঘুরে ফিরে আসবে: সমাকলন বা ইন্টিগ্রাল, যার মাধ্যমে অসংখ্য ক্ষুদ্র ক্ষুদ্র অংশের যোগফল থেকে মোট ফলাফল বের করা হয়; এবং অন্তরীকরণ বা ডেরিভেটিভ, যার মাধ্যমে কোনো পরিবর্তনের তাৎক্ষণিক হার পরিমাপ করা হয়।"
            }
        ]
    },
    {
        "id": "sec-circle-rings",
        "title": "বৃত্তের ক্ষেত্রফল পাই আর স্কয়ার ও রিং আনরোলিং",
        "audio_file": "sec_02_circle_area.mp3",
        "cues_file": "sec_02_circle_area_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "দ্বিতীয় পরিচ্ছেদ: বৃত্তের ক্ষেত্রফল ও বলয় উন্মোচন।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "ছোটবেলা থেকেই আমরা জানি যে ক্যাপিটাল আর ব্যাসার্ধবিশিষ্ট একটি বৃত্তের ক্ষেত্রফল হলো পাই আর স্কয়ার।"
            },
            {
                "index": 2,
                "type": "formula-box",
                "text": "গাণিতিক সূত্র: বৃত্তের ক্ষেত্রফল সমান পাই ক্যাপিটাল আর স্কয়ার।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "কিন্তু কখনো কি ভেবে দেখেছেন, কেন এই সূত্রটি সত্য? পাই তো মূলত একটি বৃত্তের পরিধি ও তার ব্যাসের অনুপাত, অর্থাৎ সি বাই টু আর। তাহলে পরিধির ধ্রুবকটি ক্ষেত্রফলের ভেতরে ব্যাসার্ধের বর্গের সাথে কীভাবে এমন নিখুঁতভাবে জড়িয়ে গেল?"
            },
            {
                "index": 4,
                "type": "p",
                "text": "চলুন গ্রান্ট স্যান্ডারসনের মতো করে ভাবা যাক। ধরা যাক আমাদের কাছে একটি বৃত্ত আছে। আমরা যদি একে সোজা গ্রিড দিয়ে মাপতে যাই, তবে বৃত্তের বাঁকা সীমানা কখনোই সরল বর্গাকৃতির সাথে খাপ খাবে না। কিন্তু যদি আমরা বৃত্তটিকে কতগুলো সমকেন্দ্রিক পাতলা বলয়ে বা রিংয়ে কেটে ফেলি?"
            },
            {
                "index": 5,
                "type": "figure",
                "text": "চিত্র এক-এ লক্ষ্য করো: বৃত্তকে অসংখ্য সমকেন্দ্রিক পাতলা বলয়ে ভাগ করা হয়েছে, যেখানে প্রতিটি বলয়ের ব্যাসার্ধ ছোট হাতের আর এবং অতিক্ষুদ্র বেধ হলো ডি আর।"
            },
            {
                "index": 6,
                "type": "p",
                "text": "মনে করি মূল বৃত্তটির কেন্দ্র থেকে ছোট হাতের আর দূরত্বে অবস্থিত যেকোনো একটি নির্দিষ্ট বলয় নেওয়া হলো। এই বলয়টির বেধ অত্যন্ত পাতলা—যাকে ক্যালকুলাসের ভাষায় আমরা বলি ডি আর, অর্থাৎ ব্যাসার্ধের অতিক্ষুদ্র বৃদ্ধি।"
            },
            {
                "index": 7,
                "type": "callout",
                "text": "বিশেষ বিশ্লেষণ, একটি বলয়কে সোজা করা: যদি আমরা এই পাতলা বলয়টিকে এক জায়গায় কাঁচি দিয়ে কেটে সোজা লম্বা ফিতার মতো বিছিয়ে দিই, তবে সেটি প্রায় একটি নিখুঁত আয়তক্ষেত্র তৈরি করবে! এই আয়তক্ষেত্রের দৈর্ঘ্য হবে মূল বলয়ের পরিধির সমান টু পাই আর, আর এর প্রস্থ বা উচ্চতা হবে বলয়টির পাতলা বেধ ডি আর। অতএব, এই একক বলয়ের অতিক্ষুদ্র ক্ষেত্রফল ডি এ হবে টু পাই আর গুণ ডি আর।"
            },
            {
                "index": 8,
                "type": "formula-box",
                "text": "গাণিতিক সমীকরণ: অতিক্ষুদ্র ক্ষেত্রফল ডি এ প্রায় সমান টু পাই আর গুণ ডি আর।"
            },
            {
                "index": 9,
                "type": "p",
                "text": "অবশ্যই, যেহেতু বলয়টির ভেতরের পরিধি টু পাই আর এবং বাইরের পরিধি টু পাই ইনটু আর যোগ ডি আর কিছুটা আলাদা, তাই এটি পুরোপুরি সোজা আয়তক্ষেত্র না হয়ে সামান্য ট্রাপিজয়েড হয়। কিন্তু ডি আর এর মান যত ক্ষুদ্র থেকে ক্ষুদ্রতর হবে, এই পার্থক্য ততই অদৃশ্য হয়ে যাবে এবং আয়তক্ষেত্রের আসন্নায়নটি পরম নির্ভুলতার দিকে ধাবিত হবে!"
            }
        ]
    },
    {
        "id": "sec-slope-rate",
        "title": "পরিবর্তনের হার ও ঢাল",
        "audio_file": "sec_03_derivative.mp3",
        "cues_file": "sec_03_derivative_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "তৃতীয় পরিচ্ছেদ: পরিবর্তনের হার ও ঢালের অনুসন্ধান।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "ক্যালকুলাসের অপর পিঠ হলো পরিবর্তনের হার অনুসন্ধান করা। বৃত্তের ক্ষেত্রফলের উদাহরণটিতেই যদি আমরা প্রশ্ন করি:"
            },
            {
                "index": 2,
                "type": "chapter-quote",
                "text": "যদি বৃত্তের ব্যাসার্ধ ছোট হাতের আর-কে খুব সামান্য পরিমাণ ডি আর বৃদ্ধি করা হয়, তবে ক্ষেত্রফল ক্যাপিটাল এ ঠিক কতটুকু বৃদ্ধি পাবে?"
            },
            {
                "index": 3,
                "type": "p",
                "text": "বৃত্তের পরিধিতে যুক্ত হওয়া নতুন অংশের ক্ষেত্রফলই হলো সেই বৃদ্ধি ডি এ। আমরা আগেই দেখেছি, এই বৃদ্ধি হলো একদম বাইরের বলয়টির ক্ষেত্রফল, যার মান টু পাই আর গুণ ডি আর।"
            },
            {
                "index": 4,
                "type": "p",
                "text": "উভয়পক্ষকে ডি আর দিয়ে ভাগ করলে আমরা পাই:"
            },
            {
                "index": 5,
                "type": "formula-box",
                "text": "সমীকরণে দেখো: ডি এ বাই ডি আর সমান টু পাই আর।"
            },
            {
                "index": 6,
                "type": "p",
                "text": "এটি এক পরম জাদুকরী উপলব্ধি! বৃত্তের ক্ষেত্রফলের পরিবর্তনের হার, অর্থাৎ ডি এ বাই ডি আর, হুবহু তার পরিধি টু পাই আর এর সমান। কারণ ব্যাসার্ধ সামান্য একটু বাড়ালে বৃত্তের ক্ষেত্রফল কেবল তার পরিধি বরাবরই নতুন স্তর হিসেবে বিস্তৃত হতে পারে।"
            },
            {
                "index": 7,
                "type": "p",
                "text": "সাধারণভাবে, যেকোনো ফাংশন এফ অব এক্স-এর জন্য: ইনপুটের ক্ষুদ্র পরিবর্তন হলো ডি এক্স, আউটপুটের সংশ্লিষ্ট বৃদ্ধি হলো ডি এফ, এবং পরিবর্তনের তাৎক্ষণিক হার বা লেখচিত্রের স্পর্শকের ঢাল হলো ডি এফ বাই ডি এক্স।"
            }
        ]
    }
]

async def synthesize_section(sec):
    audio_path = os.path.join(OUTPUT_DIR, sec["audio_file"])
    cues_path = os.path.join(OUTPUT_DIR, sec["cues_file"])
    
    if os.path.exists(audio_path) and os.path.exists(cues_path) and os.path.getsize(audio_path) > 10000:
        print(f"⏩ Section {sec['title']} ({sec['audio_file']}) already generated. Skipping.")
        return

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
    
    # Cleanup temp
    for t_file in temp_files:
        if os.path.exists(t_file):
            os.remove(t_file)
    if os.path.exists(concat_list_file):
        os.remove(concat_list_file)
        
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
    print("Master Bengali Teacher Audio Synthesis — Calculus Lesson 01")
    print("Voice: bn-BD-PradeepNeural | Mode: Authentic Warm Math Educator")
    print("======================================================================")
    
    manifest_data = {
        "course": "calculus",
        "lesson": "lesson_01",
        "voice": VOICE,
        "mode": "authentic_teacher",
        "sections": {}
    }
    
    for sec in SECTIONS_CONFIG:
        await synthesize_section(sec)
        
        cues_path = os.path.join(OUTPUT_DIR, sec["cues_file"])
        with open(cues_path, "r", encoding="utf-8") as f:
            sec_cues_data = json.load(f)
            
        manifest_data["sections"][sec["id"]] = {
            "title": sec["title"],
            "audio_file": sec["audio_file"],
            "total_duration_ms": sec_cues_data["total_duration_ms"],
            "cues": sec_cues_data["cues"]
        }
        
    manifest_path = os.path.join(OUTPUT_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 manifest.json generated at {manifest_path}!")

if __name__ == "__main__":
    asyncio.run(main())
