import os
import re
import json
import asyncio
import subprocess
import edge_tts

VOICE = "bn-BD-PradeepNeural"
AUDIO_DIR = os.path.dirname(os.path.abspath(__file__))

def get_mp3_duration_ms(file_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(res.stdout.strip()) * 1000.0

def sanitize_for_tts(text: str) -> str:
    t = text.replace("—", ", ")
    t = t.replace("–", ", ")
    t = t.replace("-", " ")
    t = re.sub(r'\s+', ' ', t).strip()
    return t

# Section 3 updated text cues matching new 3B1B authentic content
SEC_03_CUES = [
    {
        "index": 0,
        "type": "h2",
        "raw_text": "স্প্যান ধারণা — ভেক্টরের রাজত্ব",
        "tts": "তৃতীয় পরিচ্ছেদ: স্প্যান ধারণা — ভেক্টরের রাজত্ব।"
    },
    {
        "index": 1,
        "type": "p",
        "raw_text": "দুটি ভেক্টর ভি ও ডব্লিউ-এর সমস্ত সম্ভাব্য রৈখিক সমন্বয় মিলে যে সেট তৈরি হয়, তাকে বলে তাদের স্প্যান...",
        "tts": "দুটি ভেক্টর, ভেক্টর ভি এবং ভেক্টর ডব্লিউ এর সমস্ত সম্ভাব্য রৈখিক সমন্বয় মিলে যে সেট তৈরি হয়, তাকে বলে তাদের স্প্যান। এই পরিভাষা দিয়ে যদি আমরা আগের অংশটিকে নতুন করে বলি: বেশিরভাগ দ্বিমাত্রিক ভেক্টর জোড়ার স্প্যান হলো পুরো দ্বিমাত্রিক স্পেসের সমস্ত ভেক্টর; কিন্তু যখন তারা কাকতালীয়ভাবে একই রেখায় অবস্থিত হয়, তখন তাদের স্প্যান হলো কেবল সেই রেখার ওপর শীর্ষবিন্দু থাকা ভেক্টরগুলো।"
    },
    {
        "index": 2,
        "type": "formula-box",
        "raw_text": "Span(v, w) = { av + bw | a, b in R }",
        "tts": "গাণিতিক সূত্র: স্প্যান অব ভেক্টর ভি এবং ভেক্টর ডব্লিউ হলো এমন সমস্ত ভেক্টর এ গুণ ভেক্টর ভি যোগ বি গুণ ভেক্টর ডব্লিউ এর সেট, যেখানে এ এবং বি হলো বাস্তব সংখ্যা।"
    },
    {
        "index": 3,
        "type": "figure",
        "raw_text": "দুটি ভিন্নমুখী ভেক্টরের সমস্ত রৈখিক সমন্বয় মিলে পুরো ২ডি সমতল তৈরি হয়",
        "tts": "চিত্র প্রদর্শনী: দুটি ভিন্নমুখী ভেক্টরের সমস্ত রৈখিক সমন্বয় মিলে পুরো টুডি সমতল তৈরি হয়।"
    },
    {
        "index": 4,
        "type": "p",
        "raw_text": "মনে আছে আমরা কীভাবে বলেছিলাম লিনিয়ার বীজগণিত ভেক্টর যোগ এবং স্কেলার গুণনের চারপাশে ঘোরে...",
        "tts": "মনে আছে আমরা কীভাবে বলেছিলাম লিনিয়ার বীজগণিত ভেক্টর যোগ এবং স্কেলার গুণনের চারপাশে ঘোরে? দুটি ভেক্টরের স্প্যান মূলত একটি প্রশ্ন করার চমৎকার উপায়: কেবল ভেক্টর যোগ এবং স্কেলার গুণনের এই মৌলিক অপারেশন দুটি ব্যবহার করে আপনি কোন কোন সম্ভাব্য ভেক্টরে পৌঁছাতে সক্ষম?"
    },
    {
        "index": 5,
        "type": "quiz-block",
        "raw_text": "Quiz 1: What two vectors will only produce vectors that lie on a single line?",
        "tts": "অনুশীলন প্রশ্ন: নিচের কোন দুটি ভেক্টরের রৈখিক সমন্বয় শুধুমাত্র একটি সরলরেখায় অবস্থিত ভেক্টর তৈরি করবে? প্রথম বিকল্পে ভেক্টর ভি হলো দুই তিন এবং ভেক্টর ডব্লিউ হলো মাইনাস এক, মাইনাস এক দশমিক পাঁচ। লক্ষ্য করুন এরা পরস্পরের সমান্তরাল, তাই উত্তর হবে প্রথম বিকল্পটি।"
    },
    {
        "index": 6,
        "type": "quiz-block",
        "raw_text": "Quiz 2: What is the span of [3, -2] and [-6, 4]?",
        "tts": "অনুশীলন প্রশ্ন দুই: তিন মাইনাস দুই এবং মাইনাস ছয় চার এই দুটি ভেক্টরের স্প্যান কী? যেহেতু দ্বিতীয় ভেক্টরটি প্রথমটির ঠিক মাইনাস দুই গুণ, অর্থাৎ এরা সমান্তরাল, তাই এদের স্প্যান হবে একটি সরলরেখা।"
    },
    {
        "index": 7,
        "type": "p",
        "raw_text": "স্প্যান ধারণাটি একটি মাত্র ভেক্টরের জন্যও প্রযোজ্য...",
        "tts": "স্প্যান ধারণাটি একটি মাত্র ভেক্টরের জন্যও প্রযোজ্য। একটি অশূন্য ভেক্টর ভি এর স্প্যান হলো তার ভেতর দিয়ে যাওয়া সম্পূর্ণ সরলরেখা।"
    },
    {
        "index": 8,
        "type": "h3",
        "raw_text": "ভেক্টর বনাম বিন্দু",
        "tts": "ভেক্টর বনাম বিন্দু।"
    },
    {
        "index": 9,
        "type": "p",
        "raw_text": "মানুষ কীভাবে সাধারণত ভেক্টরকে বিন্দু হিসেবে চিন্তা করে...",
        "tts": "মানুষ কীভাবে সাধারণত ভেক্টরকে বিন্দু হিসেবে চিন্তা করে, তা নিয়ে কথা বলার জন্য এটি একটি উপযুক্ত সময়। একটি সরলরেখার ওপর রাখা ভেক্টরের বিশাল সংগ্রহ নিয়ে ভাবাটা ভীষণ ঘিঞ্জি ও জটিল মনে হয়; আর সমতল পূর্ণ করে ফেলা সমস্ত দ্বিমাত্রিক ভেক্টরকে একসাথে ভাবতে গেলে পরিস্থিতি আরও বেশি জটিল ও বিশৃঙ্খল হয়ে ওঠে।"
    },
    {
        "index": 10,
        "type": "media-tab",
        "raw_text": "Media tab arrow",
        "tts": "মিডিয়া অ্যানিমেশন: তীরচিহ্ন থেকে বিন্দুতে রূপান্তর।"
    },
    {
        "index": 11,
        "type": "p",
        "raw_text": "তাই যখন ভেক্টরের এই ধরনের সংগ্রহ নিয়ে কাজ করা হয়...",
        "tts": "তাই যখন ভেক্টরের এই ধরনের সংগ্রহ নিয়ে কাজ করা হয়, তখন স্থানটিতে প্রতিটি ভেক্টরকে কেবল তার শীর্ষবিন্দু দ্বারা একটি বিন্দু হিসেবে উপস্থাপন করাটা প্রচলিত নিয়ম। এভাবে আপনি যদি কোনো নির্দিষ্ট সরলরেখার ওপর শীর্ষবিন্দু থাকা প্রতিটি সম্ভাব্য ভেক্টর নিয়ে ভাবতে চান, তবে আপনাকে শুধু সেই রেখাটি নিয়ে ভাবলেই চলে।"
    },
    {
        "index": 12,
        "type": "media-tab",
        "raw_text": "Media tab point_line",
        "tts": "চিত্র ও ভিডিও: এক ভেক্টরের স্প্যান, একটি সরলরেখা।"
    },
    {
        "index": 13,
        "type": "p",
        "raw_text": "একইভাবে, সমস্ত সম্ভাব্য দ্বিমাত্রিক ভেক্টর নিয়ে ভাবতে...",
        "tts": "একইভাবে, সমস্ত সম্ভাব্য দ্বিমাত্রিক ভেক্টর নিয়ে ভাবতে প্রতিটি ভেক্টরকে তার শীর্ষবিন্দুর অবস্থান হিসেবে কল্পনা করুন। তারপর তাদের সবাইকে একসাথে ভাবতে তীরচিহ্নগুলোকে বাদ দিয়ে কেবল অসীম সমতল চাদরটি কল্পনা করলেই চলবে — যা মূলত দ্বিমাত্রিক স্থান।"
    },
    {
        "index": 14,
        "type": "media-tab",
        "raw_text": "Media tab point_space",
        "tts": "চিত্র ও ভিডিও: দুই ভেক্টরের স্প্যান, সমতল।"
    },
    {
        "index": 15,
        "type": "p",
        "raw_text": "সাধারণত, আপনি যখন একটি একক ভেক্টর নিয়ে ভাবছেন...",
        "tts": "সাধারণত, আপনি যখন একটি একক ভেক্টর নিয়ে ভাবছেন, তখন তাকে একটি তীর হিসেবে চিন্তা করুন; আর যখন ভেক্টরের কোনো সম্পূর্ণ সংগ্রহ বা গোষ্ঠী নিয়ে ভাবছেন, তখন তাদের বিন্দু হিসেবে চিন্তা করাটাই সবচেয়ে সুবিধাজনক ও পরিষ্কার।"
    },
    {
        "index": 16,
        "type": "h3",
        "raw_text": "ত্রিমাত্রিক স্থানে স্প্যান (Span in 3D)",
        "tts": "ত্রিমাত্রিক স্থানে স্প্যান বা স্প্যান ইন থ্রিডি।"
    },
    {
        "index": 17,
        "type": "p",
        "raw_text": "আমরা যখন ত্রিমাত্রিক স্থানে ভেক্টর নিয়ে ভাবতে শুরু করি...",
        "tts": "আমরা যখন ত্রিমাত্রিক স্থানে ভেক্টর নিয়ে ভাবতে শুরু করি, তখন স্প্যানের ধারণাটি আরও বেশি চমকপ্রদ ও গভীর হয়ে ওঠে। উদাহরণস্বরূপ, আপনি যদি ত্রিমাত্রিক স্থানে দুটি ভেক্টর নেন যা একই দিকে নির্দেশ করছে না, তবে তাদের স্প্যান বলতে আসলে কী বোঝায়?"
    },
    {
        "index": 18,
        "type": "figure",
        "raw_text": "থ্রিডি স্থানে দুটি অ-সমান্তরাল ভেক্টর",
        "tts": "চিত্র প্রদর্শনী: থ্রিডি স্থানে দুটি অ সমান্তরাল ভেক্টর, সমতল তৈরির আগের অবস্থা।"
    },
    {
        "index": 19,
        "type": "p",
        "raw_text": "তাদের স্প্যান হলো ওই দুটি ভেক্টরের সম্ভাব্য সমস্ত রৈখিক সমন্বয়ের সেট...",
        "tts": "তাদের স্প্যান হলো ওই দুটি ভেক্টরের সম্ভাব্য সমস্ত রৈখিক সমন্বয়ের সেট। অর্থাৎ, আপনি শুরুতে যে দুটি ভেক্টর নিয়েছেন তাদের প্রতিটিকে যেকোনো উপায়ে স্কেল করে যোগ করার মাধ্যমে যেসব ভেক্টর তৈরি করতে পারবেন, তাদের সম্মিলিত সংগ্রহই হলো এদের স্প্যান।"
    },
    {
        "index": 20,
        "type": "figure",
        "raw_text": "থ্রিডিতে দুটি ভেক্টরের রৈখিক সমন্বয়",
        "tts": "চিত্র প্রদর্শনী: থ্রিডিতে দুটি ভেক্টরের রৈখিক সমন্বয়, স্কেলার ঘুরিয়ে মান পরিবর্তন।"
    },
    {
        "index": 21,
        "type": "p",
        "raw_text": "আপনি কল্পনা করতে পারেন দুটি নব বা ডায়াল ঘুরিয়ে...",
        "tts": "আপনি কল্পনা করতে পারেন দুটি নব বা ডায়াল ঘুরিয়ে রৈখিক সমন্বয়ের স্কেলার দুটির মান বদলাচ্ছেন, স্কেল করা ভেক্টরগুলোকে যোগ করছেন এবং ফলাফল হিসেবে পাওয়া ভেক্টরের শীর্ষবিন্দুকে লক্ষ্য করছেন। সেই শীর্ষবিন্দুটি ত্রিমাত্রিক স্থানের মূলবিন্দুগামী একটি সমতল পাতলা চাদর খোদাই করে তৈরি করে।"
    },
    {
        "index": 22,
        "type": "media-tab",
        "raw_text": "SpanOfTwoVectorsIn3d",
        "tts": "মিডিয়া প্রদর্শনী: থ্রিডিতে দুই ভেক্টরের স্প্যান — মূলবিন্দুগামী সমতল চাদর।"
    },
    {
        "index": 23,
        "type": "p",
        "raw_text": "এই সমতল চাদরটিই হলো ওই দুটি ভেক্টরের স্প্যান...",
        "tts": "এই সমতল চাদরটিই হলো ওই দুটি ভেক্টরের স্প্যান। আরও স্পষ্টভাবে বললে, যেসব ভেক্টরের শীর্ষবিন্দু এই সমতল চাদরে অবস্থান করে, তাদের সম্পূর্ণ সেটটিই হলো এই দুটি ভেক্টরের স্প্যান। ভাবতেই কী অপূর্ব এক মানসিক চিত্র, তাই না?"
    },
    {
        "index": 24,
        "type": "p",
        "raw_text": "এখন যদি আমরা এর সাথে একটি তৃতীয় ভেক্টর যুক্ত করি...",
        "tts": "এখন যদি আমরা এর সাথে একটি তৃতীয় ভেক্টর যুক্ত করি, এবং তিনটি ভেক্টরের সম্মিলিত স্প্যান বিবেচনা করি, তবে কী ঘটবে? তিনটি ভেক্টরের রৈখিক সমন্বয় দুটি ভেক্টরের মতোই সংজ্ঞায়িত: তিনটি স্কেলার বেছে নিন, সেগুলো দিয়ে প্রতিটি ভেক্টরকে স্কেল করুন, তারপর তাদের যোগ করুন। আর পুনরায়, এদের স্প্যান হলো সম্ভাব্য সব রৈখিক সমন্বয়ের সেট।"
    },
    {
        "index": 25,
        "type": "figure",
        "raw_text": "LinearCombinationOfThreeVectorsWithLines",
        "tts": "চিত্র প্রদর্শনী: তিনটি ভেক্টরের রৈখিক সমন্বয়।"
    },
    {
        "index": 26,
        "type": "p",
        "raw_text": "যখন আমরা একটি তৃতীয় ভেক্টর যোগ করি, তখন দুটি ভিন্ন ঘটনা ঘটতে পারে...",
        "tts": "যখন আমরা একটি তৃতীয় ভেক্টর যোগ করি, তখন দুটি ভিন্ন ঘটনা ঘটতে পারে।"
    },
    {
        "index": 27,
        "type": "p",
        "raw_text": "১. আপনার তৃতীয় ভেক্টরটি যদি কাকতালীয়ভাবে প্রথম দুটি ভেক্টরের স্প্যান করা সমতলের ওপরই অবস্থান করে...",
        "tts": "এক নম্বর: আপনার তৃতীয় ভেক্টরটি যদি কাকতালীয়ভাবে প্রথম দুটি ভেক্টরের স্প্যান করা সমতলের ওপরই অবস্থান করে, তবে স্প্যানের কোনো পরিবর্তন হবে না — আপনি এক অর্থে সেই একই সমতল চাদরেই বন্দি রয়ে যাবেন। অন্য কথায়, প্রথম দুটির রৈখিক সমন্বয়ের সাথে তৃতীয় ভেক্টরের কোনো স্কেল করা সংস্করণ যোগ করলেও আপনি নতুন কোনো ভেক্টরে পৌঁছানোর সুযোগ পাবেন না।"
    },
    {
        "index": 28,
        "type": "media-tab",
        "raw_text": "ThirdVectorIsInSpan",
        "tts": "মিডিয়া প্রদর্শনী: তৃতীয় ভেক্টর স্প্যানের সমতলের মধ্যে অবস্থিত।"
    },
    {
        "index": 29,
        "type": "p",
        "raw_text": "২. আর আপনি যদি এলোমেলোভাবে যেকোনো একটি তৃতীয় ভেক্টর বেছে নেন...",
        "tts": "দুই নম্বর: আর আপনি যদি এলোমেলোভাবে যেকোনো একটি তৃতীয় ভেক্টর বেছে নেন, তবে এটি প্রায় নিশ্চিতভাবেই প্রথম দুটির সমতলে অবস্থান করবে না। যেহেতু এটি একটি সম্পূর্ণ স্বতন্ত্র দিকে মুখ করে আছে, তাই এটি সম্ভাব্য প্রতিটি ত্রিমাত্রিক ভেক্টরের প্রবেশদ্বার খুলে দেয়! এটি ভাবার সেরা উপায় হলো: আপনি নতুন তৃতীয় ভেক্টরটিকে স্কেল করার সাথে সাথে এটি প্রথম দুটি ভেক্টরের স্প্যান করা সমতলকে পুরো ত্রিমাত্রিক স্থানজুড়ে সুইপ করে সমস্ত স্থান পূর্ণ করে ফেলে।"
    },
    {
        "index": 30,
        "type": "media-tab",
        "raw_text": "ThirdVectorIsNotInSpan",
        "tts": "মিডিয়া প্রদর্শনী: তৃতীয় ভেক্টর স্প্যানের বাইরে — সমগ্র থ্রিডি স্থান ঝাড়ু দিয়ে পূর্ণ করা।"
    },
    {
        "index": 31,
        "type": "p",
        "raw_text": "এটি মূলত স্থানের তিনটি পূর্ণ মাত্রা অর্জন করতে...",
        "tts": "এটি মূলত স্থানের তিনটি পূর্ণ মাত্রা অর্জন করতে আপনার হাতের তিনটি মুক্তভাবে পরিবর্তনশীল স্কেলারের পূর্ণ সদ্ব্যবহার করার মতো।"
    }
]

async def build_sec_03():
    temp_dir = os.path.join(AUDIO_DIR, "temp_sec_03")
    os.makedirs(temp_dir, exist_ok=True)
    
    chunk_paths = []
    cues_manifest = []
    
    current_ms = 0.0
    gap_ms = 350.0
    
    print(f"Synthesizing {len(SEC_03_CUES)} cues for sec_03_span.mp3...")
    for cue in SEC_03_CUES:
        idx = cue["index"]
        text = sanitize_for_tts(cue["tts"])
        chunk_file = os.path.join(temp_dir, f"cue_{idx:02d}.mp3")
        
        # Check if already generated
        if not os.path.exists(chunk_file) or os.path.getsize(chunk_file) == 0:
            print(f"Generating cue {idx}: {text[:40]}...")
            success = False
            for attempt in range(4):
                try:
                    communicate = edge_tts.Communicate(text, VOICE)
                    await communicate.save(chunk_file)
                    success = True
                    break
                except Exception as e:
                    print(f"  Attempt {attempt+1} failed ({e}), retrying...")
                    await asyncio.sleep(0.5 * (attempt + 1))
            if not success:
                raise RuntimeError(f"Failed to generate audio for cue {idx}")
        else:
            print(f"Cue {idx} already exists ({os.path.getsize(chunk_file)} bytes), skipping synthesis.")
            
        duration_ms = get_mp3_duration_ms(chunk_file)
        cues_manifest.append({
            "index": idx,
            "type": cue["type"],
            "text": text,
            "start_ms": round(current_ms, 1),
            "end_ms": round(current_ms + duration_ms, 1),
            "duration_ms": round(duration_ms, 1)
        })
        chunk_paths.append(chunk_file)
        current_ms += duration_ms + gap_ms
        
        duration_ms = get_mp3_duration_ms(chunk_file)
        
        cues_manifest.append({
            "index": idx,
            "type": cue["type"],
            "text": text,
            "start_ms": round(current_ms, 1),
            "end_ms": round(current_ms + duration_ms, 1),
            "duration_ms": round(duration_ms, 1)
        })
        
        chunk_paths.append(chunk_file)
        current_ms += duration_ms + gap_ms

    final_audio = os.path.join(AUDIO_DIR, "sec_03_span.mp3")
    final_cues_json = os.path.join(AUDIO_DIR, "sec_03_span_cues.json")
    
    # Concatenate using ffmpeg
    list_file = os.path.join(temp_dir, "chunks.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for p in chunk_paths:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
            
    os.system(f'ffmpeg -y -f concat -safe 0 -i "{list_file}" -c copy "{final_audio}"')
    
    with open(final_cues_json, "w", encoding="utf-8") as f:
        json.dump(cues_manifest, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully generated {final_audio}")
    print(f"Total duration: {round(current_ms, 1)} ms ({round(current_ms/60000, 2)} mins)")
    
    # Clean temp files
    for p in chunk_paths:
        try: os.remove(p)
        except: pass
    try: os.remove(list_file)
    except: pass
    try: os.rmdir(temp_dir)
    except: pass
    
    # Update manifest.json & manifest.js
    manifest_json_path = os.path.join(AUDIO_DIR, "manifest.json")
    manifest_js_path = os.path.join(AUDIO_DIR, "manifest.js")
    
    with open(manifest_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    data["sections"]["sec-span"]["total_duration_ms"] = round(current_ms, 1)
    data["sections"]["sec-span"]["cues"] = cues_manifest
    
    with open(manifest_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    with open(manifest_js_path, "w", encoding="utf-8") as f:
        f.write("window.TEACHER_AUDIO_MANIFEST = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n")
        
    print("manifest.json and manifest.js successfully updated!")

if __name__ == "__main__":
    asyncio.run(build_sec_03())
