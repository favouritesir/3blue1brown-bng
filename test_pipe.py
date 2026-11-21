import asyncio, os, subprocess, edge_tts

async def test():
    c = edge_tts.Communicate("টেইলর ধারা ও উচ্চতর সান্নিধ্যকরণ", voice="bn-BD-PradeepNeural")
    await c.save("test_t1.mp3")
    cmd_sil = 'ffmpeg -y -f lavfi -i anullsrc=r=24000:cl=mono -t 0.350 -b:a 192k test_sil.mp3'
    subprocess.run(cmd_sil, shell=True, check=True)
    with open("test_concat.txt", "w") as f:
        f.write(f"file '{os.path.abspath('test_t1.mp3').replace(chr(92), '/')}'\n")
        f.write(f"file '{os.path.abspath('test_sil.mp3').replace(chr(92), '/')}'\n")
        f.write(f"file '{os.path.abspath('test_t1.mp3').replace(chr(92), '/')}'\n")
    cmd_cat = 'ffmpeg -y -f concat -safe 0 -i test_concat.txt -c:a libmp3lame -b:a 192k test_out.mp3'
    subprocess.run(cmd_cat, shell=True, check=True)
    
    # Check duration
    cmd_prob = 'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 test_out.mp3'
    res = subprocess.run(cmd_prob, shell=True, capture_output=True, text=True)
    print("Concatenated duration:", res.stdout.strip())
    
    for f in ["test_t1.mp3", "test_sil.mp3", "test_concat.txt", "test_out.mp3"]:
        if os.path.exists(f): os.remove(f)
    print("Test passed successfully!")

asyncio.run(test())
