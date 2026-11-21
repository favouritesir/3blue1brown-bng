# 🎙️ Dub Studio Operations & Automated Dubbing Architecture

## 1. Executive Summary
Dub Studio is dedicated to automated, high-fidelity Bengali dubbing of English and foreign-language tutorials and educational videos. As CEO / Studio Director, this operations plan outlines the operational pipeline, verified engine capabilities, voice profile settings, and ready-to-run workflows.

---

## 2. Dubbing Pipeline Workflow
1. **Source Ingestion (`yt-dlp` / Local Media):**
   - Ingests direct YouTube links or local video files.
   - Extracts source captions (`.vtt`) or auto-generated subtitles.
2. **Cue Optimization & Smart Merging:**
   - Cleans HTML formatting tags from VTT files.
   - Merges adjacent cues (< 0.8s gap and < 5.5s window) to ensure natural sentence construction.
3. **Resilient Bengali Translation Layer:**
   - **Tier 1:** High-speed, natural Google Translate client endpoint (`dict-chrome-ex`).
   - **Tier 2:** `MyMemoryTranslator` (en-GB to bn-IN) failover.
   - **Tier 3:** Graceful raw text retention ensuring pipeline never halts on API errors.
4. **Bangla Neural TTS Generation (`edge-tts`):**
   - Default Male Voice: `bn-BD-PradeepNeural`
   - Default Female Voice: `bn-BD-NabanitaNeural`
   - Generates segment audio files with exact timestamp metrics.
5. **Precision Audio Synchronization & Time-Stretching (`FFmpeg`):**
   - Dynamic `atempo` adjustment (up to 1.45x) to maintain lip-sync and cue timing.
   - Microsecond precision silence padding to align speech to source timestamps.
6. **Video Merging & Audio Mixing:**
   - Lossless video copy (`-c:v copy`).
   - Clean audio replacement or ambient background mixing (`--mix-background` at 15% volume).
   - Exports final MP4 directly into `output/`.

---

## 3. Operational Command Reference
- **Standard Dub:**
  ```bash
  python dubber.py "https://www.youtube.com/watch?v=VIDEO_ID"
  ```
- **Female Voice (Nabanita):**
  ```bash
  python dubber.py "https://www.youtube.com/watch?v=VIDEO_ID" --voice bn-BD-NabanitaNeural
  ```
- **With Original Background Audio Mixed:**
  ```bash
  python dubber.py "https://www.youtube.com/watch?v=VIDEO_ID" --mix-background
  ```

---

## 4. Current Status
- Engine environment verified and operational.
- FFmpeg 9.0.2 with audio filter support active.
- Resilient translation verified with live Bengali output.
- Standing studio operations active and ready for batch tutorial processing.
