# Web Platform Agent Boundaries — Comprehension Report

---

## Feature Spec Paraphrase

This document establishes a **governance constitution** for the "3Blue1Brown Bengali Web Platform" — a multi-course, offline-capable educational website hosting Bengali-dubbed versions of 3Blue1Brown's STEM mathematics videos. The constitution defines two layers:

**Architectural Rules (invariant, permanent):**
1. **No Dubbed Hero Master Audio Bar** — The legacy global audio bar (`.audio-track-bar`) is permanently banned. The only audio surfaces are the HTML5 video player (`#mainVideo`) and a new **Smart Teacher Narration Engine** (`narration_engine.js`).
2. **Sole Audio Authority** — Video playback and teacher narration are mutually exclusive: playing one auto-pauses the other. No overlapping audio ever.
3. **Mandatory Teacher Narration** — Every lesson must ship narration audio assets under `departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/<course>/<lesson>/`, driven by a `manifest.js` (preloaded script for offline `file://` support) and `manifest.json`. Voice: Edge-TTS `bn-BD-PradeepNeural`. UI components: floating audio pill (`#smartAudioPill`), top banner, per-section listen buttons, live karaoke highlighting.
4. **No Horizontal Scrollbar on Bookmarks** — Bookmark chips must wrap (`flex-wrap: wrap` or CSS Grid `.bookmark-grid`); horizontal overflow scrollbars are forbidden.
5. **Default to Local Bengali Video** — Hero section initializes with local video container (`#heroLocalBox`) visible and YouTube embed (`#heroYtBox`) hidden. The YouTube toggle button label is fixed as `▶ অরিজিনাল ভিডিও`.

**Agent Territory Assignments (zero-collision):**
- **Lead Agent (Antigravity)** — Owns global platform shell: `web_platform/index.html`, `lesson.css`, `lesson.js`, `narration_engine.js`, `curriculum_index.json`, plus Linear Algebra Lesson 01. Supervises all child agents.
- **Course Fleets (6 total)** — Each fleet owns its course directory exclusively (Linear Algebra lessons 02–05, Calculus, Differential Equations, Lockdown Math, Neural Networks, Probability). No cross-course file access without permission.
- **Audio Synthesis Fleet** — Owns all `assets/audio/<course>/<lesson>/` folders. Generates `sec_*.mp3`, `manifest.json`, `manifest.js`. Forbidden from touching HTML.

---

## Implementation Plan Paraphrase

Inferred from the rules and assignments, the implementation approach would be:

1. **Platform Shell First** — Lead Agent builds the global scaffold: `index.html` (landing/page frame), shared `lesson.css`/`lesson.js` (lesson page template + narration engine integration), `narration_engine.js` (core audio logic: mutual-exclusion playback, manifest loading, karaoke sync, UI pill/banner/buttons), and `curriculum_index.json` (course/lesson registry). Lesson 01 of Linear Algebra serves as the reference implementation.

2. **Course Fleet Parallelization** — Each course fleet receives a directory sandbox. They clone/adapt the reference lesson structure (HTML + audio folder) for their assigned lessons. They **must not** modify global stylesheets or the reference lesson without Lead Agent approval. This enables parallel workstreams with zero merge conflicts.

3. **Audio Synthesis Pipeline** — Audio Synthesis Fleet operates independently on the audio tree. For each lesson, they produce section-level MP3s (`sec_*.mp3`), a JSON manifest (metadata: durations, timestamps, text), and a JS manifest (preload script for offline `file://` execution). They hand off completed audio folders to the relevant course fleet for integration.

4. **Integration Contract** — Course fleets integrate audio by referencing the manifest files in their lesson HTML. The `narration_engine.js` (owned by Lead) reads `manifest.js`/`manifest.json` at runtime — no build step required, preserving `file://` offline capability.

5. **Gatekeeping & Review** — Lead Agent reviews all PRs against the architectural rules (no hero audio bar, sole audio authority, bookmark wrapping, local-video default, correct YouTube label). Cross-cutting changes (global CSS/JS, narration engine) require Lead sign-off.

6. **Offline-First Delivery** — The `manifest.js` preload pattern ensures the platform works fully offline when opened via `file://` — a hard requirement implied by the "100% offline file:// support" note.

---

## Comprehension Findings

### 🔴 Blocker

| # | Finding | Why It Blocks |
|---|---------|---------------|
| B1 | **`departments/learning_paths/...` path prefix is undefined** | The audio path rule (Rule 7) references `departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/...` but the agent table uses `assets/audio/<course>/<lesson>/` (relative). No root directory or repo structure is defined. A reader cannot map these to actual filesystem locations. |
| B2 | **`curriculum_index.json` schema is unspecified** | Lead Agent owns this file but its structure (course list, lesson metadata, audio manifest references, versioning) is never described. Course fleets need this to generate correct navigation/links. |
| B3 | **`manifest.json` / `manifest.js` format is unspecified** | Audio Synthesis Fleet produces these; `narration_engine.js` consumes them. Without a schema (fields: `sections[]`, `duration`, `text`, `timestamp`, `mp3_path`, etc.), integration is guesswork. |
| B4 | **`narration_engine.js` API/interface is undefined** | The engine is "mandatory" and owned by Lead, but its public methods (e.g., `init(manifestUrl)`, `playSection(id)`, `pauseAll()`), event hooks, and karaoke highlighting contract are not documented. Course fleets cannot integrate correctly. |
| B5 | **Lesson HTML template / required DOM IDs are not specified** | Rules reference `#mainVideo`, `#smartAudioPill`, `#heroLocalBox`, `#heroYtBox`, `.bookmark-grid` — but no canonical lesson HTML skeleton is provided. Each fleet would invent their own, violating consistency. |

### 🟡 Major

| # | Finding | Impact |
|---|---------|--------|
| M1 | **"Lead Agent (Antigravity)" — identity unresolved** | "Antigravity" appears to be a codename or provider-specific model alias. No mapping to an actual agent configuration, prompt, or MCP server is given. A new reader cannot instantiate this agent. |
| M2 | **Course fleet agent IDs are informal labels** | "Agent - Linear Algebra Fleet", "Agent - Calculus Fleet", etc. — no agent config IDs, prompts, or tool permissions listed. Cannot be hired/deployed in Paperclip or similar orchestration. |
| M3 | **Audio Synthesis Fleet's generation process is opaque** | "Generates `sec_*.mp3`, `manifest.json`, `manifest.js`" — but *how*? Edge-TTS CLI? Custom script? Batch job? No toolchain, voice parameters (rate, pitch), or quality gates described. |
| M4 | **No versioning / change management protocol** | Rules are "PERMANENT" and "STRICT" but no mechanism for proposing, reviewing, or versioning rule changes exists. How does a fleet request an exception (e.g., "need to touch global CSS for a course-specific component")? |
| M5 | **Offline `file://` support has hidden constraints** | `manifest.js` as a "preloaded script" implies `<script src="manifest.js">` in HTML. But `file://` CORS restrictions block ES modules and `fetch()`. The document assumes this works without addressing `file://` security policies (e.g., Chrome blocks `file://` XHR by default). |
| M6 | **Karaoke highlighting contract missing** | "Live karaoke text highlighting" is a UI requirement but no data format (per-word timestamps? per-sentence?) or DOM integration pattern (CSS classes, `data-` attributes) is defined. |
| M7 | **Bookmark system is referenced but not designed** | "Bookmark chips" and `.bookmark-grid` appear in Rule 12 but no bookmark data model, persistence (localStorage? URL hash?), or navigation behavior is described. |

### 🟢 Nit

| # | Finding | Note |
|---|---------|------|
| N1 | **Date format ambiguity** | "2026-11-05" — ISO 8601, clear, but no timezone. Trivial. |
| N2 | **"Tiered" in "Gemini 3.8 Flash Tiered" is unexplained** | Likely a model variant/tier label; not actionable. |
| N3 | **Emoji-heavy rule labels** | `🎧 বাংলা অডিও মাস্টার`, `🎙️ শিক্ষকের কণ্ঠে শুনুন`, `▶ অরিজিনাল ভিডিও` — fine for human readers, but if these strings are used as code identifiers (e.g., `innerText` checks), they become brittle. |
| N4 | **Inconsistent path notation** | Rule 7 uses absolute-from-root path; agent table uses relative `assets/audio/...`. Pick one convention. |
| N5 | **No glossary** | Terms like "Hero", "Fleet", "Master Audio Bar", "Smart Teacher Narration Engine" are used without definitions. Helpful for onboarding. |

---

*End of Comprehension Report*