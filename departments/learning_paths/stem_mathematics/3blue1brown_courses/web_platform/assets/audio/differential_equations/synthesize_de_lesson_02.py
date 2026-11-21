import asyncio
import os
import json
import subprocess
from pathlib import Path
import edge_tts

VOICE = "bn-BD-PradeepNeural"
RATE = "-2%"
PITCH = "+0Hz"

OUTPUT_DIR = Path(r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/differential_equations/lesson_02")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Lesson 02: The pendulum problem and phase space (পেন্ডুলাম মেকানিক্স এবং ফেজ স্পেস)
# 4 Pedagogical Sections:
# 1. sec_01_pendulum_intro.mp3: পেন্ডুলামের সমস্যা ও ছোট কোণ অনুমান
# 2. sec_02_nonlinear.mp3: অরৈখিক ব্যবস্থার জটিলতা
# 3. sec_03_phase_space.mp3: ফেজ স্পেস কী? কোণ বনাম কৌণিক বেগ
# 4. sec_04_energy_loop.mp3: শক্তি সংরক্ষণ ও ফেজ লুপ

SECTIONS_DATA = [
    {
        "id": "sec-pendulum-intro",
        "title": "পেন্ডুলামের সমস্যা ও ছোট কোণ অনুমান",
        "audio_file": "sec_01_pendulum_intro.mp3",
        "cues_file": "sec_01_pendulum_intro_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "প্রথম পরিচ্ছেদ: পেন্ডুলামের চিরায়ত সমস্যা ও ছোট কোণ অনুমান।"
            },
            {
                "index": 1,
                "type": "chapter-quote",
                "text": "পদার্থবিজ্ঞানী রিচার্ড ফাইনম্যান বলেছিলেন: একই সমীকরণ একই ধরণের ঘটনার জন্ম দেয়। তাই কোনো একটি মৌলিক সমস্যা গভীরভাবে বুঝতে পারলে প্রকৃতির বহু রহস্য উন্মোচিত হয়।"
            },
            {
                "index": 2,
                "type": "p",
                "text": "শিক্ষার্থী বন্ধুরা, গত অধ্যায়ে আমরা প্রথম ক্রমের সাধারণ ডিফারেনশিয়াল সমীকরণ এবং স্লোপ ফিল্ডের জ্যামিতিক সৌন্দর্য দেখেছি। আজ আমরা প্রবেশ করব পদার্থবিজ্ঞানের অন্যতম বিখ্যাত ও ক্লাসিক্যাল সমস্যায়—দোলক বা সরল পেন্ডুলামের গতি।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "ধরা যাক, এল দৈর্ঘ্যের একটি হালকা অবিস্তার্য সুতোর এক প্রান্তে এম ভরের একটি গোলক ঝুলিয়ে দেওয়া হলো। উলম্ব রেখার সাথে সুতোটি যে কোণ তৈরি করে, তাকে আমরা বলি থিটা। সময়ের সাথে সাথে থিটার মান কীভাবে পরিবর্তিত হবে, তা বলাই আমাদের প্রধান লক্ষ্য।"
            },
            {
                "index": 4,
                "type": "figure",
                "text": "পাশের চিত্রে লক্ষ্য করো: এল দৈর্ঘ্যের পেন্ডুলাম, উলম্বের সাথে কোণ থিটা, এবং অভিকর্ষজ ত্বরণ জি এর প্রভাবে গতিশীল দোলক।"
            },
            {
                "index": 5,
                "type": "p",
                "text": "নিউটনীয় বলবিদ্যা প্রয়োগ করলে দেখা যায়, গোলকটির ওপর দুটি প্রধান বল কাজ করে—সুতোর টান এবং খাড়া নিচের দিকে ক্রিয়াশীল অভিকর্ষ বল এম জি। গতির স্পর্শক বরাবর বলের উপাংশ হলো মাইনাস এম জি সাইন থিটা।"
            },
            {
                "index": 6,
                "type": "formula-box",
                "text": "নিউটনীয় বলবিদ্যার সমীকরণ: ডি স্কয়ার থিটা বাই ডি টি স্কয়ার যোগ জি বাই এল সাইন থিটা সমান শূন্য।"
            },
            {
                "index": 7,
                "type": "p",
                "text": "খেয়াল করো, এটি একটি দ্বিতীয় ক্রমের ডিফারেনশিয়াল সমীকরণ। সাধারণত বিদ্যালয়ের পদার্থবিজ্ঞান ক্লাসে শিক্ষক একটি চতুর অনুমান করে নেন: যদি কোণ থিটা খুব ছোট হয়, তবে সাইন থিটা প্রায় সমান থিটা।"
            },
            {
                "index": 8,
                "type": "callout",
                "text": "ছোট কোণ অনুমান বা স্মল অ্যাঙ্গেল অ্যাপ্রক্সিমেশন: যখন থিটার মান শূন্যের খুব কাছাকাছি, তখন সাইন থিটার মান প্রায় থিটার সমান ধরা হয়। ফলে সমীকরণটি দাঁড়ায় ডি স্কয়ার থিটা বাই ডি টি স্কয়ার যোগ জি বাই এল থিটা সমান শূন্য। এটি একটি রৈখিক সমীকরণ, যার সমাধান অতি সহজ সরল ছন্দিত স্পন্দন—অর্থাৎ সাইন ও কোসাইন তরঙ্গের মিষ্টি সুর!"
            },
            {
                "index": 9,
                "type": "p",
                "text": "কিন্তু বাস্তব পৃথিবীতে যদি পেন্ডুলামটিকে অনেক উঁচুতে তুলে ছেড়ে দেওয়া হয়, তবে কী ঘটবে? তখন কি এই সুন্দর রৈখিক অনুমান টিকে থাকবে?"
            }
        ]
    },
    {
        "id": "sec-nonlinear",
        "title": "অরৈখিক ব্যবস্থার জটিলতা",
        "audio_file": "sec_02_nonlinear.mp3",
        "cues_file": "sec_02_nonlinear_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "দ্বিতীয় পরিচ্ছেদ: অরৈখিক ব্যবস্থার জটিলতা ও বিশুদ্ধ সমাধানহীনতার বাস্তবতা।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "যখন পেন্ডুলামটিকে নব্বই ডিগ্রি বা একশত আশি ডিগ্রির কাছাকাছি কোণে নিয়ে ছেড়ে দেওয়া হয়, তখন থিটা আর ছোট থাকে না। তখন সাইন থিটাকে কেবল থিটা বলে উড়িয়ে দেওয়ার কোনো সুযোগ থাকে না।"
            },
            {
                "index": 2,
                "type": "figure",
                "text": "গ্রাফিক্সে লক্ষ্য করো: বড় কোণে সাইন থিটা বক্ররেখা এবং সোজা সরলরেখা থিটার মাঝে তৈরি হওয়া তীব্র ব্যবধান।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "সাইন থিটা পদটি উপস্থিত থাকার কারণে এই সমীকরণটি হয়ে ওঠে পুরোপুরি নন-লিনিয়ার বা অরৈখিক। আর এই একটি অরৈখিক পদই যেন গণিতবিদদের জন্য এক বিশাল দেয়াল তুলে দেয়!"
            },
            {
                "index": 4,
                "type": "formula-box",
                "text": "অরৈখিক ডিফারেনশিয়াল সমীকরণ: কৌণিক ত্বরণ ডি স্কয়ার থিটা বাই ডি টি স্কয়ার সমান মাইনাস জি বাই এল সাইন থিটা।"
            },
            {
                "index": 5,
                "type": "p",
                "text": "আপনি যদি সাধারণ বীজগণিতীয় বা ক্যালকুলাসের প্রাথমিক ফাংশন—যেমন পলিনমিয়াল, সাইন, কস কিংবা এক্সপোনেনশিয়াল দিয়ে এর অবিকল এবং নিখুঁত সূত্র লিখতে চান, তবে আপনি ব্যর্থ হবেন। এটি সাধারণ প্রাথমিক ফাংশনের মাধ্যমে সমাধানযোগ্য নয়; এর জন্য প্রয়োজন পড়ে জটিল উপবৃত্তাকার সমাকলন বা এলিপ্টিক ইন্টিগ্রাল।"
            },
            {
                "index": 6,
                "type": "callout",
                "text": "গাণিতিক অন্তর্দৃষ্টি: বাস্তব জগতের নব্বই শতাংশেরও বেশি গতিশীল ব্যবস্থা অরৈখিক। নিখুঁত কাগজের সূত্রের জন্য বসে থাকলে বিজ্ঞান স্থবির হয়ে যেত। তাই গণিতবিদ অঁরি পোয়াঁকারে আমাদের শিখিয়েছেন এক সম্পূর্ণ নতুন জ্যামিতিক দৃষ্টিভঙ্গি—সমীকরণ সমাধান না করেও কীভাবে পুরো ব্যবস্থার ভবিষ্যৎ চিত্র এক নিমেষে দেখে ফেলা যায়!"
            },
            {
                "index": 7,
                "type": "p",
                "text": "সেই জ্যামিতিক দৃষ্টিভঙ্গির নামই হলো ফেজ স্পেস। আসুন দেখি কীভাবে দ্বিতীয় ক্রমের এই সমীকরণকে আমরা দুটি প্রথম ক্রমের সমীকরণের যুগলবন্দীতে রূপান্তর করতে পারি।"
            }
        ]
    },
    {
        "id": "sec-phase-space",
        "title": "ফেজ স্পেস কী? কোণ বনাম কৌণিক বেগ",
        "audio_file": "sec_03_phase_space.mp3",
        "cues_file": "sec_03_phase_space_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "তৃতীয় পরিচ্ছেদ: ফেজ স্পেস কী? কোণ বনাম কৌণিক বেগ।"
            },
            {
                "index": 1,
                "type": "chapter-quote",
                "text": "অঁরি পোয়াঁকারের দর্শন: ব্যবস্থার প্রতিটি মুহূর্তের সম্পূর্ণ অবস্থাকে মহাবিশ্বের একটি একক বিন্দু হিসেবে কল্পনা করো। তখন সময়ের সাথে সেই বিন্দুর গতিপথই হবে সম্পূর্ণ গতিবিদ্যার মানচিত্র।"
            },
            {
                "index": 2,
                "type": "p",
                "text": "দ্বিতীয় ক্রমের সমীকরণ নিয়ে কাজ করার সবচেয়ে শক্তিশালী কৌশল হলো একটি নতুন চলক প্রবর্তন করা। লক্ষ্য করো, পেন্ডুলামের যেকোনো মুহূর্তের গতি নির্ধারণ করতে দুটি তথ্য আবশ্যক: এক, পেন্ডুলামটি কোথায় আছে—অর্থাৎ কোণ থিটা; এবং দুই, এটি কত দ্রুত ঘুরছে—অর্থাৎ কৌণিক বেগ, যাকে আমরা বলি ওমেগা।"
            },
            {
                "index": 3,
                "type": "formula-box",
                "text": "যুগল সমীকরণ ব্যবস্থা: ডি থিটা বাই ডি টি সমান ওমেগা, এবং ডি ওমেগা বাই ডি টি সমান মাইনাস জি বাই এল সাইন থিটা।"
            },
            {
                "index": 4,
                "type": "p",
                "text": "দারুণ এক রূপান্তর ঘটে গেল! একটি দ্বিতীয় ক্রমের জটিল সমীকরণ ভেঙে পরিণত হলো দুটি প্রথম ক্রমের সমীকরণের একটি সুন্দর সিস্টেমে।"
            },
            {
                "index": 5,
                "type": "figure",
                "text": "ফেজ স্পেসের সমতল চিত্র: অনুভূমিক অক্ষে কোণ থিটা এবং উলম্ব অক্ষে কৌণিক বেগ ওমেগা।"
            },
            {
                "index": 6,
                "type": "p",
                "text": "এখন একটি দ্বিমাত্রিক স্থানাঙ্ক ব্যবস্থা কল্পনা করো। অনুভূমিক এক্স অক্ষে বসাও কোণ থিটা, আর উলম্ব ওয়াই অক্ষে বসাও কৌণিক বেগ ওমেগা। এই সমতলের প্রতিটি বিন্দু থিটা কমা ওমেগা পেন্ডুলামের একটি সম্পূর্ণ শারীরিক অবস্থাকে নির্দেশ করে। একেই বলা হয় ফেজ স্পেস বা স্টেট স্পেস।"
            },
            {
                "index": 7,
                "type": "callout",
                "text": "ফেজ ভেক্টর ফিল্ডের মূল নীতি: ফেজ স্পেসের প্রতিটি বিন্দুতে একটি ছোট বেগ ভেক্টর আঁকা থাকে, যার অনুভূমিক উপাংশ হলো ওমেগা এবং উলম্ব উপাংশ হলো মাইনাস জি বাই এল সাইন থিটা। পেন্ডুলামের গতি আর কিছুই নয়, এই ফেজ সমতলে একটি কণার মসৃণ ভ্রমণ!"
            },
            {
                "index": 8,
                "type": "p",
                "text": "যদি ওমেগা ধনাত্মক হয়, তবে থিটা ডানদিকে বৃদ্ধি পায়। আর যদি ওমেগা ঋণাত্মক হয়, তবে থিটা বামদিকে কমে যায়। এই কারণে ফেজ স্পেসের উপরের অর্ধে গতি সর্বদা ডানমুখী এবং নিচের অর্ধে গতি সর্বদা বামমুখী হয়ে এক ঘূর্ণায়মান প্রবাহ তৈরি করে।"
            }
        ]
    },
    {
        "id": "sec-energy-loop",
        "title": "শক্তি সংরক্ষণ ও ফেজ লুপ",
        "audio_file": "sec_04_energy_loop.mp3",
        "cues_file": "sec_04_energy_loop_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "চতুর্থ পরিচ্ছেদ: শক্তি সংরক্ষণ ও ফেজ স্পেসের বন্ধ কক্ষপথ।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "এবার লক্ষ্য করো সবচেয়ে জাদুকরী ঘটনাটি। যদি পেন্ডুলামের ওপর কোনো ঘর্ষণ বা বায়ুর বাধা না থাকে, তবে সিস্টেমের মোট যান্ত্রিক শক্তি সর্বদা ধ্রুবক থাকে।"
            },
            {
                "index": 2,
                "type": "figure",
                "text": "চিত্রে শক্তি সংরক্ষণ: গতিশক্তি হাফ এম এল স্কয়ার ওমেগা স্কয়ার এবং বিভব শক্তি এম জি এল ইনটু এক মাইনাস কস থিটার ধ্রুবক যোগফল।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "পেন্ডুলাম যখন নিচের সর্বনিম্ন বিন্দু পার হয়, তখন বিভব শক্তি শূন্য এবং গতিশক্তি সর্বোচ্চ—অর্থাৎ ফেজ স্পেসে ওমেগার মান শীর্ষ বিন্দুতে পৌঁছায়। আবার যখন পেন্ডুলাম দুই প্রান্তে সর্বোচ্চ উচ্চতায় পৌঁছায়, তখন বেগ শূন্য হয়ে যায়—অর্থাৎ ওমেগা স্পর্শ করে অনুভূমিক থিটা অক্ষকে।"
            },
            {
                "index": 4,
                "type": "formula-box",
                "text": "মোট শক্তি সমীকরণ: হাফ এম এল স্কয়ার ওমেগা স্কয়ার যোগ এম জি এল ইনটু এক মাইনাস কস থিটা সমান ধ্রুবক শক্তি ই।"
            },
            {
                "index": 5,
                "type": "p",
                "text": "ফেজ স্পেসে এই ধ্রুবক শক্তির সমীকরণটি আঁকলে কী রূপ দেখতে পাওয়া যায়? এটি তৈরি করে একটি সম্পূর্ণ মসৃণ ও বন্ধ লুপ বা ক্লোজড ট্র্যাজেক্টরি!"
            },
            {
                "index": 6,
                "type": "callout",
                "text": "ফেজ পোর্ট্রেটের দুটি চমৎকার অঞ্চল: এক, দোলন অঞ্চল—যেখানে শক্তি কম থাকলে বিন্দুটি মূলবিন্দু শূন্য শূন্য-র চারপাশে ডিম্বাকৃতির মতো বদ্ধ লুপে চক্রাকারে ঘুরতে থাকে। দুই, ঘূর্ণন অঞ্চল—যেখানে প্রাথমিক শক্তি এত বেশি থাকে যে পেন্ডুলাম পুরো বৃত্ত সম্পূর্ণ করে বারবার বনবন করে ঘুরতে থাকে। তখন ফেজ স্পেসে তৈরি হয় তরঙ্গায়িত খোলা রেখা!"
            },
            {
                "index": 7,
                "type": "p",
                "text": "এই দুই অঞ্চলের সীমারেখাকে বলা হয় সেপারাট্রিক্স বা বিভাজক বক্ররেখা—যেখানে পেন্ডুলাম ঠিক খাড়া উল্টো অবস্থায় অর্থাৎ থিটা সমান পাই কোণে গিয়ে নিখুঁত ভারসাম্য খোঁজার চেষ্টা করে।"
            },
            {
                "index": 8,
                "type": "p",
                "text": "দেখলেন তো? একটি জটিল দ্বিতীয় ক্রমের অরৈখিক সমীকরণ, যার কোনো সহজ বীজগণিতীয় সূত্র ছিল না, ফেজ স্পেসের জ্যামিতিতে তা কত নিখুঁত, প্রাণবন্ত ও প্রাঞ্জল এক চিত্রকর্মে পরিণত হলো! এটিই ৩Blue1Brown ও আধুনিক গণিতের আসল রূপান্তরমূলক জাদু।"
            }
        ]
    }
]

async def run():
    print("======================================================================")
    print("Master Bengali Teacher Audio Synthesis — Differential Equations Lesson 02")
    print("Voice: bn-BD-PradeepNeural | Rate: -2% | Mode: Authentic Pedagogical Teacher")
    print(f"Target Directory: {OUTPUT_DIR}")
    print("======================================================================\n")

    # Generate 350ms silence file
    silence_mp3 = OUTPUT_DIR / "silence_350ms.mp3"
    sil_cmd = f'ffmpeg -y -f lavfi -i anullsrc=r=24000:cl=mono -t 0.35 -c:a libmp3lame -b:a 192k "{silence_mp3}"'
    subprocess.run(sil_cmd, shell=True, check=True, capture_output=True)

    manifest_sections = {}

    for sec in SECTIONS_DATA:
        sec_title = sec["title"]
        audio_file = sec["audio_file"]
        cues_file = sec["cues_file"]

        sec_audio_path = OUTPUT_DIR / audio_file
        sec_cues_path = OUTPUT_DIR / cues_file

        if sec_audio_path.exists() and sec_cues_path.exists() and sec_audio_path.stat().st_size > 10000:
            print(f"⏩ Section {sec_title} already synthesized, loading existing cues...", flush=True)
            with open(sec_cues_path, "r", encoding="utf-8") as f:
                c_data = json.load(f)
            manifest_sections[sec["id"]] = {
                "section_id": sec["id"],
                "alias": audio_file.replace(".mp3", ""),
                "title": sec_title,
                "audio_file": audio_file,
                "total_duration_ms": c_data.get("total_duration_ms", 0),
                "cues": c_data.get("cues", [])
            }
            continue

        print(f"\n▶ Section: {sec_title} -> {audio_file}", flush=True)

        item_cues = []
        temp_files = []
        current_time_ms = 0.0

        for item in sec["items"]:
            idx = item["index"]
            item_text = item["text"]
            temp_mp3 = OUTPUT_DIR / f"tmp_{sec['id']}_{idx}.mp3"
            temp_files.append(temp_mp3)

            for attempt in range(5):
                try:
                    comm = edge_tts.Communicate(item_text, voice=VOICE, rate=RATE, pitch=PITCH)
                    await comm.save(str(temp_mp3))
                    if temp_mp3.exists() and temp_mp3.stat().st_size > 500:
                        break
                    else:
                        raise RuntimeError("Chunk file empty or too small")
                except Exception as e:
                    print(f"  [!] Retry {attempt+1} for cue {idx}: {e}")
                    await asyncio.sleep(1.0)

            # Get duration with ffprobe
            cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{temp_mp3}"'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            try:
                dur_sec = float(res.stdout.strip())
            except Exception:
                dur_sec = 2.0

            dur_ms = dur_sec * 1000.0

            item_cues.append({
                "index": idx,
                "type": item["type"],
                "text": item_text,
                "start_ms": round(current_time_ms, 1),
                "end_ms": round(current_time_ms + dur_ms, 1),
                "duration_ms": round(dur_ms, 1)
            })

            print(f"  Cue {idx:02d} [{item['type']}]: {dur_sec:.2f}s | {item_text[:45]}...", flush=True)

            # 350ms pause between pedagogical items
            current_time_ms += dur_ms + 350.0

        # Concat audio files with 350ms natural silence gap
        concat_txt = OUTPUT_DIR / f"concat_{sec['id']}.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for i, tf in enumerate(temp_files):
                abs_p = str(tf.resolve()).replace("\\", "/")
                f.write(f"file '{abs_p}'\n")
                if i < len(temp_files) - 1:
                    sil_p = str(silence_mp3.resolve()).replace("\\", "/")
                    f.write(f"file '{sil_p}'\n")

        raw_sec_mp3 = OUTPUT_DIR / f"raw_{audio_file}"
        concat_cmd = f'ffmpeg -y -f concat -safe 0 -i "{concat_txt}" -c:a libmp3lame -b:a 192k "{raw_sec_mp3}"'
        subprocess.run(concat_cmd, shell=True, check=True, capture_output=True)

        # Apply EBU R128 loudness normalization (-14 LUFS, -1.0 dBTP peak)
        norm_cmd = f'ffmpeg -y -i "{raw_sec_mp3}" -af "loudnorm=I=-14.0:TP=-1.0:LRA=11.0" -c:a libmp3lame -b:a 192k "{sec_audio_path}"'
        subprocess.run(norm_cmd, shell=True, check=True, capture_output=True)

        # Cleanup temp chunks
        for tf in temp_files:
            if tf.exists():
                tf.unlink()
        if raw_sec_mp3.exists():
            raw_sec_mp3.unlink()
        if concat_txt.exists():
            concat_txt.unlink()

        # Measure final normalized duration
        cmd_final = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{sec_audio_path}"'
        res_final = subprocess.run(cmd_final, shell=True, capture_output=True, text=True)
        final_dur_sec = float(res_final.stdout.strip())
        final_dur_ms = final_dur_sec * 1000.0

        # Save individual cues JSON
        cue_data = {
            "section_id": sec["id"],
            "title": sec_title,
            "audio_file": audio_file,
            "total_duration_ms": round(final_dur_ms, 1),
            "cues": item_cues
        }
        with open(sec_cues_path, "w", encoding="utf-8") as f:
            json.dump(cue_data, f, ensure_ascii=False, indent=2)

        # Record for master manifest
        manifest_sections[sec["id"]] = {
            "section_id": sec["id"],
            "alias": audio_file.replace(".mp3", ""),
            "title": sec_title,
            "audio_file": audio_file,
            "total_duration_ms": round(final_dur_ms, 1),
            "cues": item_cues
        }

        print(f"✅ Generated {audio_file} ({final_dur_sec:.2f}s, {len(item_cues)} cues)")

    if silence_mp3.exists():
        silence_mp3.unlink()

    # Save manifest.json
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_data = {
        "course": "differential_equations",
        "lesson": "lesson_02",
        "title": "অধ্যায় ০২ — পেন্ডুলামের সমস্যা ও ফেজ স্পেস",
        "voice": VOICE,
        "mode": "authentic_teacher",
        "sections": manifest_sections
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)

    # Save manifest.js for offline file:// support (window.TEACHER_AUDIO_MANIFEST)
    manifest_js_path = OUTPUT_DIR / "manifest.js"
    with open(manifest_js_path, "w", encoding="utf-8") as f:
        f.write("window.TEACHER_AUDIO_MANIFEST = " + json.dumps(manifest_data, ensure_ascii=False, indent=2) + ";\n")

    print(f"\n🎉 manifest.json generated at {manifest_path}!")
    print(f"🎉 manifest.js generated at {manifest_js_path}!")
    print("\n✅ All 4 sections synthesized and mastered to studio quality (-14 LUFS) successfully!")

if __name__ == "__main__":
    asyncio.run(run())
