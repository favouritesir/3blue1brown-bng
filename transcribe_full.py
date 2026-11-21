from faster_whisper import WhisperModel
import json

model = WhisperModel("base", device="cpu", compute_type="int8")
orig_path = "departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/original_audio.wav"
segments, info = model.transcribe(orig_path, word_timestamps=True)

all_words = []
for segment in segments:
    for word in segment.words:
        all_words.append({
            "word": word.word,
            "start": round(word.start, 3),
            "end": round(word.end, 3),
            "prob": round(word.probability, 3)
        })

print(f"Total transcribed words: {len(all_words)}")
with open("word_level_vocal_timeline.json", "w", encoding="utf-8") as f:
    json.dump(all_words, f, indent=2)
print("Saved word_level_vocal_timeline.json")
