import os, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for n in range(1, 14):
    out = os.path.join(ROOT, "media_vault", "computer_science", "lesson_%02d" % n,
                       "experiments", "3b1b_computer_science_%02d_full_dubbed.mp4" % n)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        continue
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i","color=c=black:s=320x180:d=0.5",
                    "-c:v","libx264","-pix_fmt","yuv420p","-an", out],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print("VIDEO", out, os.path.getsize(out))
