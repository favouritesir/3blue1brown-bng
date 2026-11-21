import asyncio
import os
import json
import subprocess
import edge_tts

VOICE = "bn-BD-PradeepNeural"
RATE = "-2%"
PITCH = "+0Hz"

OUTPUT_DIR = r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/linear_algebra/lesson_03"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SECTIONS_DATA = [
    {
        "id": "sec-transformations-are-functions",
        "alias": "sec_01_transformations",
        "title": "১. রূপান্তর আসলে একটি ফাংশন (Transformations are Functions)",
        "audio_file": "sec_01_transformations.mp3",
        "cues_file": "sec_01_transformations_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "প্রথম পরিচ্ছেদ: রূপান্তর আসলে একটি ফাংশন।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "লিনিয়ার অ্যালজেব্রার মূল প্রাণকেন্দ্র হলো রৈখিক রূপান্তর বা লিনিয়ার ট্রান্সফরমেশন এবং তাদের সাথে ম্যাট্রিক্সের অবিচ্ছেদ্য সম্পর্ক বোঝা। কিন্তু এই বিষয়ে প্রবেশ করার আগে আমাদের স্পষ্ট হতে হবে—রূপান্তর বলতে আমরা আসলে কী বুঝি?"
            },
            {
                "index": 2,
                "type": "p",
                "text": "সহজ কথায়, একটি রূপান্তর মূলত একটি ফাংশন ছাড়া কিছুই নয়। সাধারণ উচ্চমাধ্যমিক গণিতে আমরা এমন ফাংশন দেখে অভ্যস্ত যা একটি বাস্তব সংখ্যা ইনপুট নেয় এবং আরেকটি সংখ্যা আউটপুট দেয়—যেমন এফ অব এক্স সমান এক্স স্কয়ার। কিন্তু লিনিয়ার অ্যালজেব্রায় আমরা এমন এক চমৎকার ফাংশনের কথা বলি যা একটি ভেক্টর ইনপুট গ্রহণ করে এবং আরেকটি ভেক্টর আউটপুট প্রদান করে।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "তাহলে প্রশ্ন জাগতে পারে: যদি এটি কেবলই একটি ফাংশন হয়, তবে গণিতবিদরা কেন একে ফাংশন না বলে বিশেষভাবে রূপান্তর বা ট্রান্সফরমেশন নাম দেন? এর কারণ হলো জ্যামিতিক দৃষ্টিশক্তি! রূপান্তর শব্দটি আমাদের মনের ভেতর একটি নিখুঁত জ্যামিতিক গতির অনুভূতি এনে দেয়—যেন পুরো দ্বিমাত্রিক বা ত্রিমাত্রিক স্থানটি নিজে নড়াচড়া করছে, মোচড় খাচ্ছে বা প্রসারিত হচ্ছে।"
            },
            {
                "index": 4,
                "type": "p",
                "text": "একটি ইনপুট ভেক্টরকে তার আউটপুট ভেক্টরে পরিবর্তিত হতে দেখার সবচেয়ে কল্পনাপ্রসূত ও প্রাণবন্ত উপায় হলো ভেক্টরটিকে এক স্থান থেকে অন্য স্থানে গতিশীল বা মুভ হতে দেখা।"
            },
            {
                "index": 5,
                "type": "p",
                "text": "এবার সমগ্র রূপান্তরটিকে একনজরে অনুধাবন করতে হলে, স্থানের প্রতিটি ভেক্টরকে তীরের বদলে কেবল তার শীর্ষবিন্দু হিসেবে কল্পনা করুন। যখন সব বিন্দু একসাথে নড়ে যায়, তখন পুরো তলটি একটি গ্রিডের মতো নতুন রূপ ধারণ করে।"
            },
            {
                "index": 6,
                "type": "callout",
                "text": "বিশেষ নোট: মূল অন্তর্দৃষ্টি—রূপান্তরকে যখন আমরা স্থানের একটি মসৃণ আকৃতি পরিবর্তন হিসেবে দেখি, তখন জটিল সমীকরণ নিমেষেই দৃশ্যমান জ্যামিতিক সত্যে পরিণত হয়।"
            }
        ]
    },
    {
        "id": "sec-what-makes-linear",
        "alias": "sec_02_linearity",
        "title": "২. একটি রূপান্তরকে কী 'রৈখিক' (Linear) করে তোলে?",
        "audio_file": "sec_02_linearity.mp3",
        "cues_file": "sec_02_linearity_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "দ্বিতীয় পরিচ্ছেদ: একটি রূপান্তরকে কী রৈখিক করে তোলে?"
            },
            {
                "index": 1,
                "type": "p",
                "text": "স্থানকে কোটি কোটি উপায়ে বাঁকানো, প্যাঁচানো বা বিকৃত করা সম্ভব। কিন্তু লিনিয়ার অ্যালজেব্রায় আমরা রূপান্তরের একটি বিশেষ ও শৃঙ্খলাবদ্ধ শ্রেণি নিয়ে কাজ করি—যাকে বলা হয় রৈখিক রূপান্তর বা লিনিয়ার ট্রান্সফরমেশন।"
            },
            {
                "index": 2,
                "type": "p",
                "text": "জ্যামিতিকভাবে একটি রূপান্তরকে রৈখিক হতে হলে ঠিক দুটি অলঙ্ঘনীয় শর্ত পূরণ করতে হয়: এক, সমস্ত সরলরেখাকে সরলরেখাই থাকতে হবে, অর্থাৎ রূপান্তরের পর কোনো রেখা বক্র বা বাঁকা হতে পারবে না। এবং দুই, মূলবিন্দু অপরিবর্তিত ও স্থির থাকতে হবে; অর্থাৎ মূলবিন্দু শূন্য কমা শূন্য তার নিজের স্থানেই অটল থাকবে, এটি অন্য কোথাও সরতে পারবে না।"
            },
            {
                "index": 3,
                "type": "figure",
                "text": "চিত্র প্রদর্শনী: রৈখিক রূপান্তরের দুই মূল বৈশিষ্ট্য—সরলরেখা সরলই থাকে এবং মূলবিন্দু নিজ স্থানে স্থির থাকে।"
            },
            {
                "index": 4,
                "type": "p",
                "text": "এই দুটি নিয়মকে একত্রিত করলে একটি চমৎকার দৃশ্যমান ফলাফল পাওয়া যায়: স্থানাঙ্ক গ্রিডের সমস্ত রেখা সমান্তরাল এবং সমান দূরত্ব বজায় রাখবে। অর্থাৎ গ্রিড লাইনস রিমেইন প্যারালাল অ্যান্ড ইভেনলি স্পেসড।"
            },
            {
                "index": 5,
                "type": "figure",
                "text": "চিত্র প্রদর্শনী: গ্রিড লাইনগুলো সমান্তরাল ও সমদূরত্বে অবস্থান করে—এটিই রৈখিকতার নিখুঁত চাক্ষুষ পরিচয়।"
            },
            {
                "index": 6,
                "type": "p",
                "text": "বিপরীতে, যদি মূলবিন্দু সরে যায় কিংবা কোনো সরলরেখা ধনুকের মতো বাঁকা হয়ে যায়, তবে সেই রূপান্তরটি অরৈখিক বা নন-লিনিয়ার বলে গণ্য হয়।"
            },
            {
                "index": 7,
                "type": "figure",
                "text": "চিত্র প্রদর্শনী: অরৈখিক রূপান্তর—মূলবিন্দু স্থানচ্যুত হয়েছে।"
            },
            {
                "index": 8,
                "type": "figure",
                "text": "চিত্র প্রদর্শনী: অরৈখিক রূপান্তর—সরলরেখাগুলো বেঁকে গেছে।"
            }
        ]
    },
    {
        "id": "sec-describing-transformations",
        "alias": "sec_03_basis_tracking",
        "title": "৩. ভিত্তি ভেক্টর দিয়েই সম্পূর্ণ রূপান্তরের বর্ণনা",
        "audio_file": "sec_03_basis_tracking.mp3",
        "cues_file": "sec_03_basis_tracking_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "তৃতীয় পরিচ্ছেদ: ভিত্তি ভেক্টর দিয়েই সম্পূর্ণ রূপান্তরের বর্ণনা।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "এখন আসে লিনিয়ার অ্যালজেব্রার সবচেয়ে গভীর ও বিস্ময়কর সত্য: আপনি কীভাবে একটি রৈখিক রূপান্তরকে সংখ্যার মাধ্যমে খাতায় লিখে রাখবেন? আপাতদৃষ্টিতে মনে হতে পারে, তলের কোটি কোটি বিন্দুর নতুন অবস্থান লিখতে অসীম তথ্যের প্রয়োজন।"
            },
            {
                "index": 2,
                "type": "p",
                "text": "কিন্তু উত্তর হলো—না! মাত্র দুটি ভেক্টরের নতুন অবস্থান জানলেই পুরো রূপান্তরটি সম্পূর্ণ নির্ধারিত হয়ে যায়। আর সেই দুটি ভেক্টর হলো আমাদের পরম পরিচিত ভিত্তি ভেক্টর: আই হ্যাট এবং জে হ্যাট।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "অধ্যায় দুই থেকে আমরা জানি, যেকোনো ভেক্টর ভি সমান কলাম ভেক্টর এক্স ওয়াই আসলে ভিত্তি ভেক্টর দুটির একটি রৈখিক সমন্বয়: ভেক্টর ভি সমান এক্স গুণ আই হ্যাট যোগ ওয়াই গুণ জে হ্যাট।"
            },
            {
                "index": 4,
                "type": "p",
                "text": "রৈখিক রূপান্তরের প্রধান বৈশিষ্ট্যই হলো—এটি রৈখিক সমন্বয় ও অনুপাতকে অবিকল সংরক্ষণ করে। রূপান্তরের পরে গ্রিড লাইনগুলো যেহেতু সমান্তরাল ও সমদূরত্বে থাকে, তাই রূপান্তরিত ভেক্টর টি অব ভি ঠিক একই স্কেলার এক্স ও ওয়াই দ্বারা রূপান্তরিত ভিত্তি ভেক্টর দুটির যোগফল হবে! অর্থাৎ টি অব ভি সমান এক্স গুণ টি অব আই হ্যাট যোগ ওয়াই গুণ টি অব জে হ্যাট।"
            },
            {
                "index": 5,
                "type": "p",
                "text": "এর অর্থ হলো: যদি আপনি কেবল জানেন রূপান্তরের পর আই হ্যাট কোথায় গিয়ে পৌঁছায় এবং জে হ্যাট কোথায় গিয়ে পৌঁছায়, তবে আপনি মহাবিশ্বের যেকোনো ভেক্টরের নতুন অবস্থান একমুহূর্তেই নিখুঁতভাবে গণনা করে ফেলতে পারবেন!"
            }
        ]
    },
    {
        "id": "sec-matrix-notation",
        "alias": "sec_04_matrix2x2",
        "title": "৪. ম্যাট্রিক্স নোটেশন ও ভেক্টর গুণনের জ্যামিতিক সত্য",
        "audio_file": "sec_04_matrix2x2.mp3",
        "cues_file": "sec_04_matrix2x2_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "চতুর্থ পরিচ্ছেদ: ম্যাট্রিক্স নোটেশন ও ভেক্টর গুণনের জ্যামিতিক সত্য।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "এবার আসা যাক সবচেয়ে গুরুত্বপূর্ণ মুহূর্তে: ম্যাট্রিক্স কী?"
            },
            {
                "index": 2,
                "type": "p",
                "text": "ধরা যাক, একটি নির্দিষ্ট রূপান্তরের পর আই হ্যাট অবতরণ করে স্থানাঙ্ক এক কমা মাইনাস দুই এ এবং জে হ্যাট গিয়ে পৌঁছায় তিন কমা শূন্য তে। গণিতবিদরা এই ফলাফল দুটিকে পাশাপাশি সাজিয়ে একটি সুন্দর বন্ধনীর ভেতর লেখেন: টু বাই টু ম্যাট্রিক্স—প্রথম কলামে এক ও মাইনাস দুই, এবং দ্বিতীয় কলামে তিন ও শূন্য।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "এখানে প্রথম কলামটি হলো রূপান্তরিত আই হ্যাটের অবস্থান এবং দ্বিতীয় কলামটি হলো রূপান্তরিত জে হ্যাটের অবস্থান!"
            },
            {
                "index": 4,
                "type": "p",
                "text": "এবার যদি আমরা জানতে চাই ভেক্টর এক্স ওয়াই এই রূপান্তরের পর কোথায় যাবে, তবে কেবল সমীকরণে মান বসিয়ে পাই: এক্স গুণ কলাম এক মাইনাস দুই যোগ ওয়াই গুণ কলাম তিন শূন্য সমান এক্স যোগ তিন ওয়াই, এবং নিচে মাইনাস দুই এক্স যোগ শূন্য ওয়াই।"
            },
            {
                "index": 5,
                "type": "p",
                "text": "আর ঠিক এভাবেই জন্ম নেয় ম্যাট্রিক্স ও ভেক্টরের গুণন! যেখানে টু বাই টু ম্যাট্রিক্স এ, বি, সি, ডি কে ভেক্টর এক্স ওয়াই দিয়ে গুণ করলে পাওয়া যায় এক্স গুণ প্রথম কলাম এ সি যোগ ওয়াই গুণ দ্বিতীয় কলাম বি ডি।"
            },
            {
                "index": 6,
                "type": "figure",
                "text": "চিত্র প্রদর্শনী: ম্যাট্রিক্স গুণনের প্রকৃত অর্থ—কলামগুলো হলো রূপান্তরিত ভিত্তি ভেক্টর, আর এক্স ও ওয়াই হলো তাদের স্কেলার ওজন।"
            },
            {
                "index": 7,
                "type": "p",
                "text": "ঐতিহ্যগতভাবে স্কুল-কলেজে শেখানো হয়: 'সারি দিয়ে কলামকে গুণ করে যোগ করো'—যা শিক্ষার্থীরা মুখস্থ করে ক্লান্ত হয়ে পড়ে। কিন্তু আসল জ্যামিতিক বাস্তবতা হলো: একটি টু বাই টু ম্যাট্রিক্স আসলে কোনো সংখ্যাতালিকা নয়, এটি একটি দ্বি-মাত্রিক রূপান্তরের সংক্ষিপ্ত রূপ—যার কলাম দুটি নির্দেশ করে আই হ্যাট এবং জে হ্যাট রূপান্তরের পর ঠিক কোথায় গিয়ে দাঁড়িয়েছে।"
            },
            {
                "index": 8,
                "type": "callout",
                "text": "বিশেষ নোট: সারসংক্ষেপ—যখনই আপনি কোনো টু বাই টু ম্যাট্রিক্স দেখবেন, নিজের মনে বলবেন: প্রথম কলাম হলো আই হ্যাটের নতুন ঠিকানা, এবং দ্বিতীয় কলাম হলো জে হ্যাটের নতুন ঠিকানা!"
            },
            {
                "index": 9,
                "type": "p",
                "text": "নিচের ইন্টারেক্টিভ ক্যালকুলেটরে ম্যাট্রিক্সের উপাদান এবং ইনপুট ভেক্টর পরিবর্তন করে দেখুন। সিস্টেম তৎক্ষণাৎ কলামভিত্তিক রৈখিক সমন্বয়, আউটপুট ভেক্টর এবং ডিটারমিন্যান্ট গণনা করে দেখাবে।"
            }
        ]
    }
]

# Generate a small 350ms silence file for natural pacing between items
SILENCE_MP3 = os.path.join(OUTPUT_DIR, "silence_350ms.mp3")

def make_silence_file():
    if not os.path.exists(SILENCE_MP3):
        cmd = f'ffmpeg -y -f lavfi -i anullsrc=r=24000:cl=mono -t 0.35 -c:a libmp3lame -b:a 192k "{SILENCE_MP3}"'
        subprocess.run(cmd, shell=True, check=True, capture_output=True)

async def synthesize_section(sec):
    audio_path = os.path.join(OUTPUT_DIR, sec["audio_file"])
    cues_path = os.path.join(OUTPUT_DIR, sec["cues_file"])
    
    if os.path.exists(audio_path) and os.path.exists(cues_path) and os.path.getsize(audio_path) > 5000:
        print(f"⏩ Section {sec['title']} already synthesized, loading existing cues...")
        with open(cues_path, "r", encoding="utf-8") as f:
            return json.load(f)

    print(f"\n🎙️ Synthesizing Section: {sec['title']} ({sec['audio_file']})...")
    
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
                    print(f"  [{idx+1}/{len(sec['items'])}] Generated cue {idx}")
                    break
                else:
                    raise RuntimeError("Generated file too small or empty")
            except Exception as e:
                print(f"  Retry {attempt+1} for item {idx}: {e}")
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
        
        # Add 350ms silence between cues
        current_time_ms += dur_ms + 350.0

    # Build ffmpeg concat list with inter-cue silence
    concat_list_file = os.path.join(OUTPUT_DIR, f"concat_{sec['alias']}.txt")
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for i, t_file in enumerate(temp_files):
            abs_p = os.path.abspath(t_file).replace("\\", "/")
            f.write(f"file '{abs_p}'\n")
            if i < len(temp_files) - 1:
                silence_abs = os.path.abspath(SILENCE_MP3).replace("\\", "/")
                f.write(f"file '{silence_abs}'\n")

    unnorm_mp3 = os.path.join(OUTPUT_DIR, f"unnorm_{sec['audio_file']}")
    concat_cmd = f'ffmpeg -y -f concat -safe 0 -i "{concat_list_file}" -c:a libmp3lame -b:a 192k "{unnorm_mp3}"'
    subprocess.run(concat_cmd, shell=True, check=True, capture_output=True)

    # Apply EBU R128 loudness normalization (-14 LUFS, -1.0 dBTP peak)
    norm_cmd = f'ffmpeg -y -i "{unnorm_mp3}" -af "loudnorm=I=-14.0:TP=-1.0:LRA=7" -c:a libmp3lame -b:a 192k "{audio_path}"'
    subprocess.run(norm_cmd, shell=True, check=True, capture_output=True)

    # Clean up temporary files
    for t_file in temp_files:
        if os.path.exists(t_file):
            os.remove(t_file)
    if os.path.exists(concat_list_file):
        os.remove(concat_list_file)
    if os.path.exists(unnorm_mp3):
        os.remove(unnorm_mp3)

    # Save Section Cues JSON
    cues_data = {
        "section_id": sec["id"],
        "alias": sec["alias"],
        "title": sec["title"],
        "audio_file": sec["audio_file"],
        "total_duration_ms": round(current_time_ms - 350.0, 1),
        "cues": item_cues
    }
    with open(cues_path, "w", encoding="utf-8") as f:
        json.dump(cues_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Generated {sec['audio_file']} ({round((current_time_ms-350)/1000, 2)}s, {len(item_cues)} cues)")
    return cues_data

async def main():
    print("=========================================================================")
    print("Master Bengali Teacher Audio Synthesis — Linear Algebra Lesson 03")
    print("Voice: bn-BD-PradeepNeural | Mode: Authentic Warm Math Teacher")
    print("Standard: EBU R128 Loudness Normalization (-14.0 LUFS, -1.0 dBTP peak)")
    print("=========================================================================")
    make_silence_file()

    manifest_sections = {}
    for sec in SECTIONS_DATA:
        cues_data = await synthesize_section(sec)
        # Store under both primary ID and alias for maximum compatibility
        manifest_sections[sec["id"]] = cues_data
        manifest_sections[sec["alias"]] = cues_data

    # Remove silence file
    if os.path.exists(SILENCE_MP3):
        os.remove(SILENCE_MP3)

    # Create consolidated manifest.json
    manifest = {
        "course": "linear_algebra",
        "lesson": "lesson_03",
        "title": "অধ্যায় ০৩ — রৈখিক রূপান্তর ও ম্যাট্রিক্স",
        "voice": VOICE,
        "mode": "authentic_teacher",
        "sections": manifest_sections
    }

    manifest_json_path = os.path.join(OUTPUT_DIR, "manifest.json")
    with open(manifest_json_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # Create manifest.js for local file:// cross-origin free loading
    manifest_js_path = os.path.join(OUTPUT_DIR, "manifest.js")
    with open(manifest_js_path, "w", encoding="utf-8") as f:
        f.write("window.TEACHER_AUDIO_MANIFEST = " + json.dumps(manifest, ensure_ascii=False, indent=2) + ";\n")

    print(f"\n🎉 All 4 section MP3s, cues JSONs, manifest.json and manifest.js generated successfully in:")
    print(OUTPUT_DIR)

if __name__ == "__main__":
    asyncio.run(main())
