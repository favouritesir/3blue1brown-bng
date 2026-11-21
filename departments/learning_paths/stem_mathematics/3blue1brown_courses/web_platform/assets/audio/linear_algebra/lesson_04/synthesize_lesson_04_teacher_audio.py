import asyncio
import os
import json
import subprocess
from pathlib import Path
import edge_tts

VOICE = "bn-BD-PradeepNeural"
RATE = "-2%"
PITCH = "+0Hz"

OUTPUT_DIR = Path(r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/linear_algebra/lesson_04")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 4 Key Pedagogical Sections matching the lesson topics & user requirements:
# sec_01_composition.mp3: দুটি রূপান্তরের সংযোজন (ঘূর্ণন অতঃপর শিরিং)
# sec_02_matrix_multiplication.mp3: ডান থেকে বামে পড়ার কারণ ও ম্যাট্রিক্স গুণন
# sec_03_algebraic_view.mp3: বীজগাণিতিক সূত্র বনাম জ্যামিতিক অন্তর্দৃষ্টি
# sec_04_associativity.mp3: সংযোজন বিধি বা অ্যাসোসিয়েটিভিটি

SECTIONS_DATA = [
    {
        "id": "sec-composition",
        "title": "দুটি রূপান্তরের সংযোজন (ঘূর্ণন অতঃপর শিরিং)",
        "audio_file": "sec_01_composition.mp3",
        "cues_file": "sec_01_composition_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "প্রথম পরিচ্ছেদ: মুখস্থ নিয়মের বাইরে — রূপান্তরের ধারাবাহিক সংযোজন।"
            },
            {
                "index": 1,
                "type": "chapter-quote",
                "text": "গ্রান্ট স্যান্ডারসন যথার্থই বলেছেন: ম্যাট্রিক্স গুণন কোনো খাপছাড়া বা মুখস্থ করার শুকনো অ্যালগরিদম নয়; এটি আসলে একটি রূপান্তরের ঠিক পর আরেকটি রূপান্তর প্রয়োগ করার জ্যামিতিক ফলশ্রুতি মাত্র।"
            },
            {
                "index": 2,
                "type": "p",
                "text": "শিক্ষার্থী বন্ধুরা, স্কুল-কলেজে আমাদের প্রায়শই ম্যাট্রিক্স গুণনের একটি অদ্ভুত ও যান্ত্রিক নিয়ম শেখানো হয়—প্রথম ম্যাট্রিক্সের প্রতিটি সারি দিয়ে দ্বিতীয় ম্যাট্রিক্সের প্রতিটি কলামের উপাদান গুণ করে যোগ করো। কিন্তু কেন? এই নিয়মটি আসলে কোথা থেকে এলো?"
            },
            {
                "index": 3,
                "type": "p",
                "text": "গত পর্বে আমরা দেখেছি যে প্রতিটি ম্যাট্রিক্স হলো দ্বিমাত্রিক বা ত্রিমাত্রিক স্থানকে রূপান্তরিত করার একটি একক জ্যামিতিক প্রক্রিয়া—যেখানে গ্রিড রেখাগুলো সর্বদা সমান্তরাল ও সমদূরবর্তী থাকে এবং মূলবিন্দু সম্পূর্ণ স্থির থাকে।"
            },
            {
                "index": 4,
                "type": "figure",
                "text": "পাশের চিত্রে লক্ষ্য করো: আগের পর্বের সারসংক্ষেপ—একটি ম্যাট্রিক্স মানেই স্থানের একটি সুনির্দিষ্ট রৈখিক রূপান্তর।"
            },
            {
                "index": 5,
                "type": "p",
                "text": "কিন্তু বাস্তব জীবনে ও বিজ্ঞানে একটি রূপান্তর সম্পন্ন করার পর প্রায়শই তার ওপর আরেকটি রূপান্তর প্রয়োগ করার দরকার পড়ে। ধরা যাক, আপনি প্রথমে দ্বিমাত্রিক সমতলটিকে ঘড়ির কাঁটার বিপরীতে নব্বই ডিগ্রি কোণে ঘোরালেন, এবং ঠিক তার পর সমতলটির ওপর একটি অনুভূমিক শিরিং বা মোচড় প্রয়োগ করলেন।"
            },
            {
                "index": 6,
                "type": "figure",
                "text": "ভিজ্যুয়াল চিত্রে লক্ষ্য করো: ঘূর্ণন অতঃপর শিরিং রূপান্তরের ধারাবাহিক প্রয়োগ কীভাবে পুরো স্থানটিকে নতুন রূপ দিচ্ছে।"
            },
            {
                "index": 7,
                "type": "p",
                "text": "শুরু থেকে শেষ পর্যন্ত পুরো সম্মিলিত প্রভাবটি নিজেই আরেকটি সম্পূর্ণ নতুন রৈখিক রূপান্তর! এই যৌথ রূপান্তরটিকে গণিতের ভাষায় বলা হয় দুটি পৃথক রূপান্তরের সংযোজন বা কম্পোজিশন।"
            },
            {
                "index": 8,
                "type": "formula-box",
                "text": "স্ক্রিনে লক্ষ্য করো: ভেক্টর ভি এর ওপর প্রথমে রূপান্তর বি কার্যকর হয়ে তৈরি হয় বি গুণ ভেক্টর ভি। এরপর তার ওপর রূপান্তর এ প্রয়োগ করলে পাওয়া যায় এ ইনটু বি ভেক্টর ভি, যা সমান এ বি ইনটু ভেক্টর ভি।"
            },
            {
                "index": 9,
                "type": "insight-box",
                "text": "লিনিয়ার অ্যালজেব্রার কেন্দ্রীয় দর্শনটি গভীরভাবে মনে রাখো: দুটি ম্যাট্রিক্সের গুণফল এ বি হলো সেই একক যৌগিক রূপান্তর, যা প্রথমে রূপান্তর বি এবং ঠিক তার পর রূপান্তর এ প্রয়োগ করলে সামগ্রিক স্থানে ঘটে থাকে।"
            }
        ]
    },
    {
        "id": "sec-tracking",
        "title": "ভিত্তি ভেক্টর ট্র্যাকিং ও ম্যাট্রিক্স গুণন",
        "audio_file": "sec_02_matrix_multiplication.mp3",
        "cues_file": "sec_02_matrix_multiplication_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "দ্বিতীয় পরিচ্ছেদ: ভিত্তি ভেক্টর ট্র্যাকিং ও ডান থেকে বামে পড়ার রহস্য।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "যেহেতু দুটি ধারাবাহিক রৈখিক রূপান্তরের সমন্বয় নিজেও একটি খাঁটি রৈখিক রূপান্তর, তাই এর নিজস্ব একটি একক টু বাই টু ম্যাট্রিক্স থাকবে। সেই ম্যাট্রিক্সটি আমরা কীভাবে বের করব? বরাবরের মতোই শিশুতোষ সহজ: শুধুমাত্র লক্ষ্য করো পুরো প্রক্রিয়ার শেষে আমাদের দুটি আদি ভিত্তি ভেক্টর আই হ্যাট এবং জে হ্যাট শেষমেশ কোথায় গিয়ে পৌঁছাল!"
            },
            {
                "index": 2,
                "type": "figure",
                "text": "চিত্রে লক্ষ্য করো: ঘূর্ণন ও শিরিং শেষে আই হ্যাট পৌঁছায় স্থানাঙ্ক এক, এক-এ এবং জে হ্যাট পৌঁছায় স্থানাঙ্ক মাইনাস এক, শূন্য-তে।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "আই হ্যাট ছিল এক শূন্য। নব্বই ডিগ্রি ঘোরার পর এটি পৌঁছায় শূন্য এক-এ। এবার অনুভূমিক শিরিং প্রয়োগ করলে এর এক্স স্থানাঙ্ক ওয়াই স্থানাঙ্কের পরিমাণ ডানে সরে গিয়ে চূড়ান্তভাবে অবতরণ করে এক, এক-এ! সুতরাং যৌথ ম্যাট্রিক্সের প্রথম কলাম হবে এক, এক।"
            },
            {
                "index": 4,
                "type": "p",
                "text": "আর জে হ্যাট ছিল শূন্য এক। নব্বই ডিগ্রি ঘোরার পর এটি পৌঁছায় মাইনাস এক শূন্য-তে। যেহেতু এর ওয়াই স্থানাঙ্ক শূন্য, তাই অনুভূমিক শিরিং প্রয়োগ করলেও এটি অপরিবর্তিত থাকে। ফলে দ্বিতীয় কলাম হয় মাইনাস এক, শূন্য।"
            },
            {
                "index": 5,
                "type": "formula-box",
                "text": "সুতরাং সমীকরণে দেখো: শিরিং ম্যাট্রিক্স ইনটু ঘূর্ণন ম্যাট্রিক্স সমান যৌথ যৌগিক ম্যাট্রিক্স—যার প্রথম কলামে এক এক, এবং দ্বিতীয় কলামে মাইনাস এক শূন্য।"
            },
            {
                "index": 6,
                "type": "p",
                "text": "এবার একটি অতি গুরুত্বপূর্ণ বিষয় লক্ষ্য করো: আমরা যখন লিখি এ বি ইনটু ভেক্টর ভি, তখন প্রথমে কোন রূপান্তরটি কার্যকর হয়? বি আগে, তারপর এ! অর্থাৎ এটি ডান থেকে বামে পড়তে হয়।"
            },
            {
                "index": 7,
                "type": "callout-blue",
                "text": "ফাংশন নোটেশনের ঐতিহ্যের কথা ভাবুন: আমরা যখন এফ অব জি অব এক্স লিখি, ইনপুট এক্স এর সবচেয়ে কাছে থাকে জি। তাই আগে জি কার্যকর হয়, তারপর তার ওপর এফ কাজ করে। ঠিক তেমনি ভেক্টর ভি এর সবচেয়ে কাছে থাকা ডানপাশের ম্যাট্রিক্স বি আগে কাজ করে, আর বামপাশের ম্যাট্রিক্স এ পরে কার্যকর হয়।"
            }
        ]
    },
    {
        "id": "sec-algebraic-view",
        "title": "বীজগাণিতিক সূত্র বনাম জ্যামিতিক অন্তর্দৃষ্টি",
        "audio_file": "sec_03_algebraic_view.mp3",
        "cues_file": "sec_03_algebraic_view_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "তৃতীয় পরিচ্ছেদ: বীজগাণিতিক সূত্র বনাম জ্যামিতিক অন্তর্দৃষ্টি ও বিনিময়হীনতা।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "এবার আসুন প্রতীকী বীজগণিত দিয়ে দেখা যাক যেকোনো দুটি সাধারণ টু বাই টু ম্যাট্রিক্সের জন্য সূত্রটি কীভাবে নিজে থেকেই বেরিয়ে আসে—কোনো সূত্র মুখস্থ না করেই!"
            },
            {
                "index": 2,
                "type": "figure",
                "text": "ডায়াগ্রামটি লক্ষ্য করো: সাধারণ চলক দিয়ে দুটি ম্যাট্রিক্সের যৌথ রূপান্তর প্রতিপাদন।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "প্রথম রূপান্তরের পর আই হ্যাট পৌঁছায় প্রথম কলাম ই, জি-তে। এর ওপর দ্বিতীয় রূপান্তর প্রয়োগ করলে পাওয়া যায় এ ই যোগ বি জি, এবং নিচে সি ই যোগ ডি জি। এটিই গুণফল ম্যাট্রিক্সের প্রথম কলাম!"
            },
            {
                "index": 4,
                "type": "p",
                "text": "একইভাবে জে হ্যাট প্রথম রূপান্তরের পর পৌঁছায় এফ, এইচ-এ। এর ওপর দ্বিতীয় রূপান্তর চালালে পাওয়া যায় এ এফ যোগ বি এইচ, এবং নিচে সি এফ যোগ ডি এইচ। এটি হলো দ্বিতীয় কলাম!"
            },
            {
                "index": 5,
                "type": "formula-box",
                "text": "এই দুটি কলাম পাশাপাশি বসালেই আমরা পাই পাঠ্যবইয়ের সেই চিরায়ত রূপ: প্রথম ম্যাট্রিক্স গুণ দ্বিতীয় ম্যাট্রিক্স সমান তাদের উপাংশভিত্তিক ডট গুণন সমন্বয়।"
            },
            {
                "index": 6,
                "type": "p",
                "text": "কিন্তু বাস্তব সংখ্যার গুণনের মতো ম্যাট্রিক্স গুণন কি বিনিময় বিধি মেনে চলে? কখনই নয়! এ বি সাধারণত বি এ এর সমান হয় না। অর্থাৎ ম্যাট্রিক্স গুণন একটি বিনিময়হীন অপারেশন।"
            },
            {
                "index": 7,
                "type": "figure",
                "text": "চিত্রে লক্ষ্য করো: আগে শিরিং ও পরে ঘূর্ণন করলে স্থানটি যে রূপ নেয়, আগে ঘূর্ণন ও পরে শিরিং করলে তার চেয়ে সম্পূর্ণ ভিন্ন আকৃতি তৈরি হয়।"
            },
            {
                "index": 8,
                "type": "callout-gold",
                "text": "বাস্তব জীবনের একটি উদাহরণ চিন্তা করো: আগে জুতো পরে তারপর মোজা পরা, আর আগে মোজা পরে তারপর জুতো পরা কি এক কথা? কখনই না! ঠিক তেমনি জ্যামিতিক রূপান্তরের ক্রম উল্টে দিলে পুরো মহাবিশ্বের স্থানাঙ্ক ব্যবস্থা বদলে যায়।"
            }
        ]
    },
    {
        "id": "sec-associativity",
        "title": "সংযোগ বিধি বা অ্যাসোসিয়েটিভিটি",
        "audio_file": "sec_04_associativity.mp3",
        "cues_file": "sec_04_associativity_cues.json",
        "items": [
            {
                "index": 0,
                "type": "h2",
                "text": "চতুর্থ পরিচ্ছেদ: সংযোজন বিধি বা অ্যাসোসিয়েটিভিটি — জ্যামিতিক উপলব্ধি।"
            },
            {
                "index": 1,
                "type": "p",
                "text": "ম্যাট্রিক্স গুণন বিনিময় বিধি না মানলেও, এটি একটি অত্যন্ত চমৎকার ধর্ম নিখুঁতভাবে মেনে চলে—তা হলো সংযোজন বিধি বা অ্যাসোসিয়েটিভিটি: বন্ধনীতে এ বি ইনটু সি সমান এ ইনটু বন্ধনীতে বি সি।"
            },
            {
                "index": 2,
                "type": "formula-box",
                "text": "সমীকরণে দেখো: বন্ধনীতে এ বি ইনটু সি সমান এ ইনটু বন্ধনীতে বি সি।"
            },
            {
                "index": 3,
                "type": "p",
                "text": "যদি তুমি স্কুল বা কলেজে বীজগণিতের সাহায্যে তিন-তিনটি ম্যাট্রিক্সের প্রতীকী গুণ করে এটি প্রমাণ করতে যাও, তবে পৃষ্ঠার পর পৃষ্ঠা সমীকরণ লিখে ক্লান্ত হয়ে পড়বে। কিন্তু জ্যামিতিক চোখে তাকালে এটি স্বতঃসিদ্ধভাবে জলের মতো পরিষ্কার!"
            },
            {
                "index": 4,
                "type": "figure",
                "text": "অ্যানিমেশনে লক্ষ্য করো: তিনটি রূপান্তরের ধারাবাহিক প্রবাহ।"
            },
            {
                "index": 5,
                "type": "p",
                "text": "বন্ধনীতে এ বি ইনটু সি মানে হলো—প্রথমে স্থানে রূপান্তর সি ঘটাও, তারপর এ বি এর যৌথ রূপান্তর প্রয়োগ করো। আর এ ইনটু বন্ধনীতে বি সি মানে হলো—প্রথমে ক্রমান্বয়ে সি ও বি ঘটাও, তারপর রূপান্তর এ প্রয়োগ করো।"
            },
            {
                "index": 6,
                "type": "callout-blue",
                "text": "উভয় ক্ষেত্রেই কিন্তু মহাবিশ্বের সমতলটি হুবহু একই ক্রমে প্রথমে সি, তারপর বি, এবং সবশেষে এ এর মধ্য দিয়েই পরিবর্তিত হচ্ছে! রূপান্তরের এই মৌলিক ক্রম যেহেতু একচুলও বদলায়নি, তাই উভয়ের চূড়ান্ত সম্মিলিত ম্যাট্রিক্স অভিন্ন হতে বাধ্য।"
            },
            {
                "index": 7,
                "type": "p",
                "text": "নিচের ইন্টারেক্টিভ সিমুলেটরে তোমরা নিজের হাতে রূপান্তরের ক্রম অদলবদল করে দেখো এবং কুইজগুলোর উত্তর দিয়ে তোমার ধারণা যাচাই করে নাও। শুভ পদচারণা!"
            }
        ]
    }
]

async def synthesize_all():
    print("=" * 70)
    print("🎙️ Linear Algebra Lesson 04 — Studio Teacher Narration Synthesis")
    print(f"Voice: {VOICE} | Target: {OUTPUT_DIR}")
    print("=" * 70)

    silence_mp3 = OUTPUT_DIR / "silence_gap.mp3"
    # Generate 350ms silence gap for natural pacing
    subprocess.run(
        f'ffmpeg -y -f lavfi -i anullsrc=r=24000:cl=mono -t 0.35 -c:a libmp3lame -b:a 192k "{silence_mp3}"',
        shell=True, check=True, capture_output=True
    )

    manifest_sections = {}

    for sec in SECTIONS_DATA:
        sec_title = sec["title"]
        audio_file = sec["audio_file"]
        cues_file = sec["cues_file"]
        sec_audio_path = OUTPUT_DIR / audio_file
        sec_cues_path = OUTPUT_DIR / cues_file

        if sec_audio_path.exists() and sec_cues_path.exists():
            print(f"⏩ Section {sec_title} already synthesized, loading existing cues...")
            with open(sec_cues_path, "r", encoding="utf-8") as f:
                c_data = json.load(f)
            manifest_sections[sec["id"]] = {
                "title": sec_title,
                "audio_file": audio_file,
                "total_duration_ms": c_data.get("total_duration_ms", 0),
                "cues": c_data.get("cues", [])
            }
            continue

        print(f"\n▶ Section: {sec_title} -> {audio_file}")

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

            print(f"  Cue {idx:02d} [{item['type']}]: {dur_sec:.2f}s | {item_text[:45]}...")

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
        "course": "linear_algebra",
        "lesson": "lesson_04",
        "voice": VOICE,
        "mode": "authentic_teacher",
        "sections": manifest_sections
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"🎉 All 4 section MP3s and manifest.json created successfully at:")
    print(f"   {manifest_path}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(synthesize_all())
