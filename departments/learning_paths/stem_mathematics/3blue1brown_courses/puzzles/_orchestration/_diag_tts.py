import asyncio
import edge_tts

SHORT = "আসুন এক ছোট উদাহরণ দিয়ে শুরু করি।"
LONG = ("আসুন এই ধাপে ছোট এক উদাহরণ নিয়ে শুরু করি। "
        "ছোট একটি উদাহরণ দিয়ে শুরু করলে জটিলতা অনেক কমে যায়; সবচেয়ে সরল ক্ষেত্রটিতে যা সত্য, তা প্রায়শই বড় ক্ষেত্রেও কাজ করে। "
        "আগের ধাপটি মিলিয়ে দেখলে সম্পর্কটি আরও পরিষ্কার হয়ে ওঠে; গণিতের প্রতিটি নতুন ধারণা আগের ধারণার ওপরেই দাঁড়িয়ে থাকে।")


async def try_one(label, text, rate):
    try:
        p = rf"C:\Users\Ashik\AppData\Local\Temp\opencode\diag_{label}_{rate.replace('+', 'p').replace('%', '')}.mp3"
        await edge_tts.Communicate(text, "bn-BD-PradeepNeural", rate=rate).save(p)
        import os
        print(label, rate, "OK", os.path.getsize(p))
    except Exception as e:
        print(label, rate, "ERR", type(e).__name__)


async def main():
    for rate in ("+0%", "-5%", "+5%"):
        await try_one("short", SHORT, rate)
    for rate in ("+0%", "-5%", "+5%", "+0%", "-5%"):
        await try_one("long", LONG, rate)


asyncio.run(main())
