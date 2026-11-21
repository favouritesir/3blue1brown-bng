import os
import subprocess
import glob

# Check if we can run whisper or speech recognition, or inspect audio energy / duration
print("Checking available python packages...")
for pkg in ['whisper', 'speech_recognition', 'faster_whisper', 'librosa']:
    try:
        __import__(pkg)
        print(f"  {pkg}: available")
    except ImportError:
        print(f"  {pkg}: not installed")
