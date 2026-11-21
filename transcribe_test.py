from faster_whisper import WhisperModel

model = WhisperModel("tiny", device="cpu", compute_type="int8")
segments, info = model.transcribe("test_intro_0_15.wav", word_timestamps=True)

print("Detected language:", info.language)
for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
    for word in segment.words:
        print(f"   {word.start:.2f} - {word.end:.2f}: {word.word}")
