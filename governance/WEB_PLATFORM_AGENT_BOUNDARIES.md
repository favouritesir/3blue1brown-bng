> ⚠️ **গুরুত্বপূর্ণ নির্দেশিকা:** এই ডকুমেন্টের সমস্ত বিধান এখন প্ল্যাটফর্মের ক্যাননিক্যাল আর্কিটেকচারাল স্ট্যান্ডার্ড **[`governance/PRODUCTION_PIPELINE_SPEC.md`](./PRODUCTION_PIPELINE_SPEC.md)** দ্বারা পরিচালিত ও সমন্বিত। কোনো দ্বন্দ্ব দেখা দিলে `PRODUCTION_PIPELINE_SPEC.md` চূড়ান্ত বলে গণ্য হবে।

# 3BLUE1BROWN BENGALI WEB PLATFORM — MULTI-AGENT GOVERNANCE & FILE ARCHITECTURE MAPPING
# Date: 2026-11-05 | Lead Architect: Gemini 3.8 Flash Tiered

## 1. ABSOLUTE PERMANENT ARCHITECTURAL RULES (STRICT)
- **NO DUBBED HERO MASTER AUDIO BAR:** The hero master audio bar (`.audio-track-bar`, `🎧 বাংলা অডিও মাস্টার`) is COMPLETELY REMOVED and PERMANENTLY FORBIDDEN from all lessons. Only the video player (`#mainVideo`) and the Smart Teacher Narration Engine exist.
- **NO OVERLAPPING AUDIO / VIDEO:** Sole audio authority rule. Whenever any video plays, teacher narration automatically pauses. Whenever teacher narration plays, all videos pause.
- **TEACHER NARRATION AUDIO (`narration_engine.js`) IS MANDATORY:**
  - Located in `departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/<course>/<lesson>/`.
  - Driven by `manifest.js` (preloaded script for 100% offline file:// support) and `manifest.json`.
  - Natural educator voice: `bn-BD-PradeepNeural`.
  - UI: Floating audio pill (`#smartAudioPill`), top banner (`🎙️ শিক্ষকের কণ্ঠে শুনুন`), section listen buttons, and live karaoke text highlighting.
- **NO HORIZONTAL SCROLLBAR ON BOOKMARKS:** Bookmark chips MUST wrap to the next line (`flex-wrap: wrap; overflow-x: visible;` or CSS Grid `.bookmark-grid`). Never introduce horizontal overflow scrollbars.
- **DEFAULT TO LOCAL BENGALI VIDEO:** All lesson hero containers must initialize with `#heroLocalBox` visible and `#heroYtBox` hidden (`display: none;`). YouTube button must strictly be labeled `▶ অরিজিনাল ভিডিও`.

## 2. STRICT AGENT TERRITORY & FILE ASSIGNMENTS (ZERO COLLISION)
To prevent agents from overwriting or clobbering each other's work:

| Agent / Subagent ID | Assigned Domain / Files | STRICT BOUNDARY (DO NOT TOUCH) |
|---|---|---|
| **Lead Agent (Antigravity)** | `web_platform/index.html`, `lesson.css`, `lesson.js`, `narration_engine.js`, `curriculum_index.json`, `courses/linear_algebra/lesson_01.html` | Exercises supervisory review and coordinates all child agents. |
| **Agent - Linear Algebra Fleet** | `courses/linear_algebra/lesson_02.html` through `lesson_05.html` and corresponding audio folders. | MUST NOT touch `lesson_01.html` or global stylesheets without permission. |
| **Agent - Calculus Fleet** | `courses/calculus/` (`index.html`, `lesson_01.html`, `lesson_02.html`, audio) | Confined strictly to Calculus directory. |
| **Agent - Differential Equations Fleet** | `courses/differential_equations/` (`index.html`, `lesson_01.html`, `lesson_02.html`) | Confined strictly to Differential Equations directory. |
| **Agent - Lockdown Math Fleet** | `courses/lockdown_math/` (`index.html`, `lesson_01.html`, `lesson_02.html`) | Confined strictly to Lockdown Math directory. |
| **Agent - Neural Networks Fleet** | `courses/neural_networks/` (`index.html`, `lesson_01.html`) | Confined strictly to Neural Networks directory. |
| **Agent - Probability Fleet** | `courses/probability/` (`index.html`, `lesson_01.html`, `lesson_02.html`) | Confined strictly to Probability directory. |
| **Audio Synthesis Fleet** | `assets/audio/<course>/<lesson>/` | Generates `sec_*.mp3`, `manifest.json`, `manifest.js`. No HTML tampering. |
