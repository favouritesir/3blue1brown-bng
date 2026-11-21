import asyncio
import os
import edge_tts
import mutagen.mp3

async def synthesize_conclusion():
    out_dir = r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/linear_algebra/lesson_01"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "sec_07_conclusion.mp3")

    text_parts = [
        "উপসংহার: লিনিয়ার অ্যালজেব্রার দুটি মৌলিক স্তম্ভ।",
        "পরবর্তী অধ্যায়গুলোতে তোমরা আরও স্পষ্ট বুঝতে পারবে কেন লিনিয়ার বীজগণিতের সবকিছুই মূলত দুটি মৌলিক ক্রিয়াকলাপের চারপাশে ঘোরে—ভেক্টর যোগ এবং স্কেলার গুণন।",
        "ভেক্টরকে তোমরা মহাশূন্যের তীরচিহ্ন ভাবছো নাকি সংখ্যার তালিকা—এই দুই দৃষ্টিভঙ্গির মাঝে স্বাধীনভাবে যাতায়াত করতে পারাই হলো লিনিয়ার অ্যালজেব্রার আসল পরাক্রম। এটি ডেটা অ্যানালিস্টকে চোখের সামনে ডেটা দেখার ভাষা দেয়, আর গ্রাফিক্স প্রোগ্রামারকে দেয় বিশ্ব নিয়ন্ত্রণের চাবিকাঠি।",
        "তো এই ছিল ভেক্টরের একেবারে মৌলিক ভিত্তি। পরবর্তী অধ্যায়ে আমরা প্রবেশ করব স্প্যান, ভিত্তি ভেক্টর এবং রৈখিক নির্ভরতার মোহনীয় জগতে!"
    ]

    full_text = " ... ... ... ".join(text_parts)
    communicate = edge_tts.Communicate(full_text, "bn-BD-PradeepNeural")
    await communicate.save(out_file)

    import subprocess, json
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", out_file]
    res = subprocess.check_output(cmd).decode().strip()
    dur_ms = float(res) * 1000
    print(f"Synthesized successfully: {out_file}, duration: {dur_ms:.1f}ms")

if __name__ == "__main__":
    asyncio.run(synthesize_conclusion())
