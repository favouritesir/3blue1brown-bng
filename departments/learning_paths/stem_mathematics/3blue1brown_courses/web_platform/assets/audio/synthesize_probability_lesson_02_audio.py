import asyncio
import os
import json
import subprocess
import edge_tts

VOICE = "bn-BD-PradeepNeural"
RATE = "-2%"
PITCH = "+0Hz"

OUTPUT_DIR = r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/probability/lesson_02"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SECTIONS_DATA = [
    {
        "id": "sec-puzzle",
        "alias": "sec_01_medical_paradox",
        "title": "মেডিকেল টেস্ট ধাঁধা",
        "audio_file": "sec_01_medical_paradox.mp3",
        "cues_file": "sec_01_medical_paradox_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "প্রথম পরিচ্ছেদ: মেডিকেল টেস্ট ধাঁধা।"
            },
            {
                "index": 1,
                "type": "chapter-quote",
                "text": "উদ্ধৃতি: নতুন কোনো প্রমাণের মুখে নিজের বিশ্বাসকে ঠিক কতটা হালনাগাদ করা উচিত—তা পরিমাপ করার অনন্য গাণিতিক ভিত্তি হলো বেজের সূত্র।—গ্রান্ট স্যান্ডারসন, থ্রি ব্লু ওয়ান ব্রাউন।"
            },
            {
                "index": 2,
                "type": "p",
                "text": "কল্পনা করুন একটি বাস্তব পরিস্থিতি। একজন ব্যক্তি সম্পূর্ণ সুস্থ বোধ করছেন, কিন্তু রুটিন চেকআপের জন্য একটি রক্ত পরীক্ষা করালেন। কিছুদিন পর ল্যাব থেকে রিপোর্ট এলো: তিনি একটি অত্যন্ত মারাত্মক ভাইরাসে পজিটিভ শনাক্ত হয়েছেন।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "ল্যাবরেটরি থেকে জানানো হলো টেস্টটির তিনটি মূল বৈশিষ্ট্য:"
            },
            {
                "index": 4,
                "type": "p",
                "text": "প্রথমত, টেস্টের সংবেদনশীলতা বা ট্রু পজিটিভ রেট ৯৯ শতাংশ। অর্থাৎ কারো যদি সত্যি সত্যি রোগ থাকে, তবে টেস্টটি ৯৯ শতাংশ ক্ষেত্রে নির্ভুল পজিটিভ ফলাফল দেয়, আর ফলস নেগেটিভের সম্ভাবনা মাত্র এক শতাংশ।"
            },
            {
                "index": 5,
                "type": "p",
                "text": "দ্বিতীয়ত, নির্দিষ্টতা বা ট্রু নেগেটিভ রেট ৯৯ শতাংশ। অর্থাৎ একজন সুস্থ মানুষকে টেস্ট করলে ৯৯ শতাংশ ক্ষেত্রে নেগেটিভ রিপোর্ট আসে, আর সুস্থ মানুষের ভুল পজিটিভ আসার সম্ভাবনা মাত্র এক শতাংশ।"
            },
            {
                "index": 6,
                "type": "p",
                "text": "এবং তৃতীয়ত, রোগটির বিস্তার বা প্রাইয়র প্রবাবিলিটি। রোগটি সমাজে অত্যন্ত বিরল—প্রতি এক হাজার জনে মাত্র একজনের এই রোগ থাকে; অর্থাৎ পি অব ডি সমান শূন্য দশমিক শূন্য শূন্য এক, বা মাত্র শূন্য দশমিক এক শতাংশ।"
            },
            {
                "index": 7,
                "type": "callout",
                "text": "বিশেষ নোট: মৌলিক প্রশ্ন—রোগীর রোগাক্রান্ত হওয়ার সম্ভাবনা কত? টেস্ট যেহেতু ৯৯ শতাংশ সঠিক এবং ফলাফল পজিটিভ এসেছে, অধিকাংশ মানুষের তাৎক্ষণিক উত্তর হয়: রোগীর রোগ থাকার সম্ভাবনা নিশ্চয়ই ৯৯ শতাংশ! কিন্তু গণিত আমাদের জানায়: এই রোগীর সত্যি সত্যি রোগ থাকার সম্ভাবনা ৯৯ শতাংশ নয়—বরং মাত্র নয় শতাংশ, অর্থাৎ প্রায় এগারো জনের মধ্যে মাত্র একজন!"
            },
            {
                "index": 8,
                "type": "p",
                "text": "কেন এমন অবিশ্বাস্য ঘটনা ঘটে? ৯৯ শতাংশ নির্ভুল টেস্ট কীভাবে পজিটিভ ফল দেওয়ার পরেও শতকরা ৯০ ভাগের বেশি ক্ষেত্রে ভুল প্রমাণিত হয়? একেই বলে ফলস পজিটিভ প্যারাডক্স বা ভ্রান্ত পজিটিভের ধাঁধা।"
            }
        ]
    },
    {
        "id": "sec-base-rate",
        "alias": "sec_02_base_rate",
        "title": "বেস রেট ফ্যালাসি (Base Rate Fallacy)",
        "audio_file": "sec_02_base_rate.mp3",
        "cues_file": "sec_02_base_rate_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "দ্বিতীয় পরিচ্ছেদ: বেস রেট ফ্যালাসি—আমাদের মস্তিষ্কের অন্ধবিন্দু।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "আমাদের সহজাত প্রবৃত্তি কেবল একটি সংখ্যার দিকে তাকায়—টেস্টের নির্ভুলতা বা এক্যুরেসি ৯৯ শতাংশ। কিন্তু আমাদের মস্তিষ্ক মূল জনসংখ্যার প্রাথমিক ভারসাম্য বা বেস রেট পুরোপুরি ভুলে যায়।"
            },
            {
                "index": 2,
                "type": "p",
                "text": "আসুন ভগ্নাংশের জটিল হিসাবের বদলে বাস্তব এক হাজার জন মানুষের একটি দল কল্পনা করি।"
            },
            {
                "index": 3,
                "type": "formula-box",
                "text": "গাণিতিক সূত্র: মোট জনসংখ্যা সমান এক হাজার জন।"
            },
            {
                "index": 4,
                "type": "p",
                "text": "যেহেতু প্রতি এক হাজার জনে মাত্র একজন আক্রান্ত, তাই এই এক হাজার জনকে দুটি দলে ভাগ করা যায়: অসুস্থ দল মাত্র একজন মানুষ, এবং সুস্থ দল বাকি নয়শত নিরানব্বই জন মানুষ।"
            },
            {
                "index": 5,
                "type": "p",
                "text": "এবার এই এক হাজার জনের সবাইকে সেই ৯৯ শতাংশ নির্ভুল টেস্টটি করা হলো। ফলাফল কী দাঁড়াবে? অসুস্থ দলের সেই একমাত্র অসুস্থ মানুষটির টেস্ট ৯৯ শতাংশ সম্ভাবনায় পজিটিভ আসবে, অর্থাৎ আমরা পাব প্রায় একজন ট্রু পজিটিভ।"
            },
            {
                "index": 6,
                "type": "p",
                "text": "কিন্তু সুস্থ দলের দিকে তাকান: বাকি নয়শত নিরানব্বই জন মানুষ সম্পূর্ণ সুস্থ! টেস্টের ফলস পজিটিভ রেট মাত্র এক শতাংশ বা শূন্য দশমিক শূন্য এক। কিন্তু নয়শত নিরানব্বই জনের এক শতাংশ কত? নয়শত নিরানব্বই গুণ শূন্য দশমিক শূন্য এক সমান প্রায় দশ জন! অর্থাৎ সুস্থ দল থেকে ভুলবশত প্রায় দশ জন ফলস পজিটিভ রিপোর্ট পাবেন!"
            },
            {
                "index": 7,
                "type": "callout",
                "text": "বিশেষ নোট: মহাবিশ্ব সংকোচনের জাদু। এখন ল্যাবরেটরির সব পজিটিভ রিপোর্ট একত্র করা হলো। মোট কতজন পজিটিভ পেলেন? অসুস্থ দল থেকে একজন এবং সুস্থ দল থেকে দশ জন—মোট এগারো জন মানুষ পজিটিভ রিপোর্ট হাতে দাঁড়িয়ে আছেন। আপনি যদি এই এগারো জনের একজন হন, তবে আপনার সত্যি রোগ থাকার সম্ভাবনা কত? এগারো জনের মধ্যে কেবল একজন সত্যি অসুস্থ! সুতরাং পি অব ডিজিজ গিভেন পজিটিভ সমান এক ভাগ এগারো, যা প্রায় নয় দশমিক এক শতাংশ!"
            },
            {
                "index": 8,
                "type": "p",
                "text": "সুস্থ মানুষের বিশাল সংখ্যা নয়শত নিরানব্বই জন টেস্টের সামান্য এক শতাংশ ত্রুটিকে বহুগুণে বিবর্ধিত করে ফেলেছে। এটিই হলো বেস রেট ফ্যালাসি—প্রমাণ শক্তিশালী হলেও যদি মূল ঘটনাটি অত্যন্ত বিরল হয়, তবে প্রাপ্ত প্রমাণের বেশিরভাগই আসলে ফলস অ্যালার্ম!"
            }
        ]
    },
    {
        "id": "sec-grid-partition",
        "alias": "sec_03_grid_partition",
        "title": "ক্ষেত্রফল বিভাজন ও জনসংখ্যা গ্রিড",
        "audio_file": "sec_03_grid_partition.mp3",
        "cues_file": "sec_03_grid_partition_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "তৃতীয় পরিচ্ছেদ: ক্ষেত্রফল বিভাজন ও জনসংখ্যা গ্রিড।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "থ্রি ব্লু ওয়ান ব্রাউন সম্ভাব্যতা বোঝাতে সবসময় দুটি শক্তিশালী জ্যামিতিক হাতিয়ার ব্যবহার করেন: সম্ভাব্যতার বৃক্ষ বা প্রোবাবিলিটি ট্রি, এবং ক্ষেত্রফল বিভাজন গ্রিড বা এরিয়া পার্টিশন গ্রিড।"
            },
            {
                "index": 2,
                "type": "figure",
                "text": "চিত্র প্রদর্শনী: সম্ভাব্যতার বৃক্ষচিত্রে দেখা যাচ্ছে—এক হাজার মানুষের মধ্যে মাত্র একজন আক্রান্ত এবং নয়শত নিরানব্বই জন সুস্থ। আক্রান্ত ব্যক্তি থেকে পাওয়া যায় শূন্য দশমিক নয় নয় জন ট্রু পজিটিভ, কিন্তু সুস্থ মানুষদের এক শতাংশ থেকে চলে আসে নয় দশমিক নয় নয় জন ফলস পজিটিভ!"
            },
            {
                "index": 3,
                "type": "p",
                "text": "এবার এটিকে ক্ষেত্রফল হিসেবে চিন্তা করুন: সমগ্র নমুনা ক্ষেত্র একটি বড় আয়তক্ষেত্র। বামপাশে একটি অত্যন্ত সরু খাড়া স্ট্রিপ হলো রোগাক্রান্ত মানুষের অঞ্চল, যার প্রস্থ মাত্র শূন্য দশমিক শূন্য শূন্য এক। ডানপাশের বিশাল অংশ হলো সুস্থ মানুষ, যার প্রস্থ শূন্য দশমিক নয় নয় নয়।"
            },
            {
                "index": 4,
                "type": "p",
                "text": "টেস্ট পজিটিভ আসার অর্থ হলো আমরা এই দুই অঞ্চল থেকে কেবল পজিটিভ অংশটুকু কেটে আলাদা করলাম। বামদিকের সরু স্ট্রিপের ৯৯ শতাংশ উচ্চতার ক্ষেত্রফল হলো শূন্য দশমিক শূন্য শূন্য শূন্য নয় নয়। কিন্তু ডানদিকের চওড়া স্ট্রিপের মাত্র এক শতাংশ উচ্চতার ক্ষেত্রফল হলো শূন্য দশমিক শূন্য শূন্য নয় নয় নয়—যা বামদিকের ক্ষেত্রফলের চেয়ে প্রায় দশ গুণ বড়!"
            },
            {
                "index": 5,
                "type": "h3",
                "text": "ইন্টারেক্টিভ মেডিকেল বেজ সিমুলেটর—এক হাজার মানুষের ডট গ্রিড।"
            },
            {
                "index": 6,
                "type": "p",
                "text": "নিচের সিমুলেটরে এক হাজারটি বিন্দু দিয়ে সমগ্র জনসংখ্যাকে দেখানো হয়েছে। স্লাইডার পরিবর্তন করে দেখুন কীভাবে রোগের বিস্তার এবং টেস্টের নির্ভুলতা পরিবর্তনের সাথে সাথে ট্রু পজিটিভ ও ফলস পজিটিভের অনুপাত নাটকীয়ভাবে পরিবর্তিত হয়।"
            },
            {
                "index": 7,
                "type": "callout",
                "text": "বিশেষ নোট: পরীক্ষা করে দেখুন—রোগের বিস্তার স্লাইডারটি টেনে একশ জনে অর্থাৎ দশ শতাংশে তুলুন। লক্ষ্য করুন কীভাবে ফলস পজিটিভের চেয়ে ট্রু পজিটিভ বৃদ্ধি পায় এবং পোস্টেরিয়র সম্ভাব্যতা মুহূর্তেই ৯১ শতাংশে পৌঁছে যায়!"
            }
        ]
    },
    {
        "id": "sec-formula",
        "alias": "sec_04_bayes_formula",
        "title": "বেজের সূত্রের চূড়ান্ত রূপ",
        "audio_file": "sec_04_bayes_formula.mp3",
        "cues_file": "sec_04_bayes_formula_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "চতুর্থ পরিচ্ছেদ: বেজের সূত্রের চূড়ান্ত রূপ ও ফিলোসফি।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "এবার আমরা এই সুন্দর জ্যামিতিক বাস্তবতাকে সার্বজনীন গাণিতিক সংকেতে রূপান্তর করব। আমরা শর্তাধীন সম্ভাব্যতার মৌলিক সংজ্ঞা থেকে জানি:"
            },
            {
                "index": 2,
                "type": "formula-box",
                "text": "গাণিতিক সূত্র: পি অব ডি গিভেন পজিটিভ সমান পি অব ডি ইন্টারসেকশন পজিটিভ ভাগ পি অব পজিটিভ।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "গুণনের নিয়ম অনুসারে লবকে লেখা যায়:"
            },
            {
                "index": 4,
                "type": "formula-box",
                "text": "গাণিতিক সূত্র: পি অব ডি ইন্টারসেকশন পজিটিভ সমান পি অব ডি গুণ পি অব পজিটিভ গিভেন ডি।"
            },
            {
                "index": 5,
                "type": "p",
                "text": "এবং সমগ্র সম্ভাব্যতা নীতি অনুসারে হর পি অব পজিটিভ হলো সমস্ত উৎস থেকে আসা মোট পজিটিভ ক্ষেত্রফল—অর্থাৎ ট্রু পজিটিভ যোগ ফলস পজিটিভ:"
            },
            {
                "index": 6,
                "type": "formula-box",
                "text": "গাণিতিক সূত্র: পি অব পজিটিভ সমান পি অব ডি গুণ পি অব পজিটিভ গিভেন ডি, যোগ পি অব নট ডি গুণ পি অব পজিটিভ গিভেন নট ডি।"
            },
            {
                "index": 7,
                "type": "p",
                "text": "এই দুটি অংশকে একত্র করলেই পাওয়া যায় ইতিহাসখ্যাত বেজের উপপাদ্য:"
            },
            {
                "index": 8,
                "type": "formula-box",
                "text": "গাণিতিক সূত্র: পি অব ডি গিভেন পজিটিভ সমান, উপরে পি অব ডি গুণ পি অব পজিটিভ গিভেন ডি; এবং নিচে পি অব ডি গুণ পি অব পজিটিভ গিভেন ডি যোগ পি অব নট ডি গুণ পি অব পজিটিভ গিভেন নট ডি।"
            },
            {
                "index": 9,
                "type": "p",
                "text": "বেজিয়ান দর্শনের চারটি স্তম্ভ হলো: প্রাইয়র বা প্রাথমিক বিশ্বাস, লাইকলিহুড বা প্রমাণ দেখার সম্ভাবনা, মার্জিনাল বা সমগ্র প্রমাণের হার, এবং পোস্টেরিয়র বা প্রমাণ সাপেক্ষে আমাদের হালনাগাদ বিশ্বাস!"
            },
            {
                "index": 10,
                "type": "callout",
                "text": "বিশেষ নোট: দ্বিতীয় টেস্টের ক্ষমতা। যদি প্রথম টেস্ট পজিটিভ আসার পর রোগী আরেকটি স্বাধীন দ্বিতীয় টেস্ট করান এবং সেটিও পজিটিভ আসে, তবে কী ঘটবে? এবার তার প্রাইয়র আর শূন্য দশমিক এক শতাংশ থাকবে না—এবার তার নতুন প্রাইয়র হবে প্রথম টেস্টের পোস্টেরিয়র ফল, অর্থাৎ নয় শতাংশ! এই নতুন প্রাইয়র নিয়ে দ্বিতীয়বার হিসাব করলে তার আক্রান্ত হওয়ার সম্ভাবনা নয় শতাংশ থেকে এক লাফে ৯১ শতাংশে উন্নীত হবে! বিজ্ঞান ও যুক্তি এভাবেই একের পর এক প্রমাণ যোগ করে সত্যের দ্বারপ্রান্তে পৌঁছায়।"
            }
        ]
    }
]

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
    print("Master Bengali Teacher Audio Synthesis — Probability Lesson 02")
    print("Bayes' Rule & Medical Test Paradox")
    print("Voice: bn-BD-PradeepNeural | Mode: Authentic Warm Math Teacher")
    print("Standard: EBU R128 Loudness Normalization (-14.0 LUFS, -1.0 dBTP peak)")
    print("=========================================================================")
    make_silence_file()

    manifest_sections = {}
    for sec in SECTIONS_DATA:
        cues_data = await synthesize_section(sec)
        # Store under primary ID, alias, and extra mapping keys
        manifest_sections[sec["id"]] = cues_data
        manifest_sections[sec["alias"]] = cues_data
        if sec["id"] == "sec-grid-partition":
            manifest_sections["sec-tree-area"] = cues_data
            manifest_sections["sec-simulator"] = cues_data

    # Remove silence file
    if os.path.exists(SILENCE_MP3):
        os.remove(SILENCE_MP3)

    # Create consolidated manifest.json
    manifest = {
        "course": "probability",
        "lesson": "lesson_02",
        "title": "অধ্যায় ০২ — বেজের সূত্র এবং মেডিকেল টেস্ট প্যারাডক্স",
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
