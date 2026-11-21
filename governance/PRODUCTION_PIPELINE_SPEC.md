# Technical Specification: Unified Production Pipeline & Web Platform Interface Spec (PRODUCTION_PIPELINE_SPEC)

**Document:** `governance/PRODUCTION_PIPELINE_SPEC.md`  
**Status:** Approved (EGM Remediation for WEB_PLATFORM_AGENT_BOUNDARIES & LESSON_PRODUCTION_STANDARD)  
**Author:** Antigravity (Lead System Architect)  
**Date:** 2026-11-05  

---

## 1. Overview & Problem Statement

### The Problem
The EGM Review (Stages 5–9) of `WEB_PLATFORM_AGENT_BOUNDARIES.md` (34 Blockers, 25 Majors) and `LESSON_PRODUCTION_STANDARD.md` (40 Blockers, 34 Majors) revealed critical structural failures:
1. **Critical Governance Fork:** `LESSON_PRODUCTION_STANDARD.md` and `AGENT_WORKFLOW_GUIDELINES.md` maintain conflicting, unaligned specifications:
   - Asset paths diverge between `media_vault/` and `departments/media_production/`.
   - TTS engine is hardcoded to `PradeepNeural` versus context-driven Edge-TTS / Gemini Flash routing.
   - SFX stem processing is completely absent in Lesson Standard versus Demucs v4 + Wiener filtering in Workflow Guidelines.
   - Phonetic dictionaries are fragmented (5 mappings versus 19 complete mappings).
2. **Missing Executable Interface Contracts:** Both documents serve as governance constitutions or philosophy manifests rather than technical implementation specifications. Developers and subagents have zero typed TypeScript/JSON schemas for the 9 core Web Components, audio manifests, bookmark ribbons, and video players.
3. **No Audio/Video Concurrency State Machine:** The "sole audio authority" mandate lacks a formal state machine definition (e.g., `IDLE`, `VIDEO_PLAYING`, `NARRATION_PLAYING`) with deterministic 0ms cross-pause resolution.
4. **Unspecified Offline & Accessibility Standards:** "Offline KaTeX textbook" lacks concrete offline implementation architectures (IIFE manifests, self-hosted fonts, Service Worker cache strategies), and WCAG 2.1 AA accessibility requirements (MathML, keyboard navigation, color contrast) are unquantified.

### Goals
- **Single Source of Truth:** Unify and reconcile all governance documents into one canonical normative specification: `PRODUCTION_PIPELINE_SPEC.md`.
- **Complete Interface Contract Package:** Define executable TypeScript interfaces and JSON schemas for:
  - Narration Engine & Audio Manifests (`manifest.js` / `manifest.json`)
  - Universal Web Components (`<b1b-navbar>`, `<b1b-hero-player>`, `<b1b-section>`, `<b1b-media-tab>`, `<b1b-callout>`, `<b1b-figure>`, `<b1b-formula>`, `<b1b-quiz>`, `<b1b-interactive-lab>`)
  - Curriculum Index (`curriculum_index.json`) and Lesson metadata
- **Canonical Media Taxonomy:** Reconcile all storage paths under the clean `departments/` root hierarchy, establishing deterministic symlinks or builds for web runtime delivery.
- **Normative Audio & TTS Pipeline:** Formally integrate the complete 19-symbol phonetic dictionary, Demucs v4 2-stem separation, acoustic silence delimiters (`\n\n... ... ...\n\n`), and EBU R128 (-14.0 LUFS) normalization.
- **Formal Playback State Machine:** Define the deterministic state transition table for video and teacher narration concurrency.
- **Offline & WCAG 2.1 AA Compliance:** Specify zero-CORS `file:///` and Service Worker offline architectures, complete with keyboard controls and accessible KaTeX/MathML standards.

### Non-Goals
- Changing the creative pedagogical narration tone or identity of 3Blue1Brown.
- Introducing heavy JavaScript single-page application frameworks (React/Vue/Angular); the platform strictly uses lightweight, zero-dependency native Web Components.

---

## 2. Technical Plan

### 2.1 Canonical Media & Asset Taxonomy Reconciliation
All disparate paths (`media_vault/`, `departments/media_production/`, and `web_platform/assets/`) are unified under a single canonical filesystem taxonomy:

```text
departments/
├── learning_paths/
│   └── stem_mathematics/
│       └── 3blue1brown_courses/
│           ├── <course_slug>/                     # e.g., essence_of_linear_algebra
│           │   └── lesson_<XX>_<slug>/            # Production master & pipeline
│           │       ├── dubbing_pipeline/
│           │       │   ├── master_script.json
│           │       │   └── stems_isolated/        # Demucs 2-stem WAVs
│           │       └── notes/
│           └── web_platform/                      # Client runtime delivery
│               ├── assets/
│               │   ├── audio/<course>/<lesson>/   # sec_*.mp3, manifest.js, manifest.json
│               │   ├── figures/<course_prefix>/   # SVGs, web-optimized media
│               │   ├── css/                       # main.css, lesson.css, narration.css
│               │   ├── js/                        # lesson_components.js, narration_engine.js
│               │   └── libs/katex/                # Self-hosted KaTeX & webfonts
│               ├── courses/<course_slug>/         # lesson_<XX>.html or single-shell SPA
│               └── data/<course_slug>/            # lesson_<XX>.json structured data
```

### 2.2 Audio/Video Concurrency State Machine
To guarantee the **Sole Audio Authority Rule** with 0ms deterministic resolution, the global media controller operates under a strict finite state machine:

| Current State | Trigger Event | Next State | Action / Invariant |
|:---|:---|:---|:---|
| **`IDLE`** | `VIDEO_PLAY_CLICK` | **`VIDEO_PLAYING`** | Start video; ensure narration paused |
| **`IDLE`** | `NARRATION_PLAY_CLICK` | **`NARRATION_PLAYING`** | Start narration audio; ensure video paused |
| **`VIDEO_PLAYING`** | `NARRATION_PLAY_CLICK` | **`NARRATION_PLAYING`** | Immediately pause video (0ms); start narration |
| **`VIDEO_PLAYING`** | `VIDEO_PAUSE_CLICK` | **`IDLE`** | Pause video; state becomes IDLE |
| **`NARRATION_PLAYING`**| `VIDEO_PLAY_CLICK` | **`VIDEO_PLAYING`** | Immediately pause narration (0ms); start video |
| **`NARRATION_PLAYING`**| `NARRATION_PAUSE_CLICK`| **`IDLE`** | Pause narration; state becomes IDLE |

### 2.3 Interface Contract Package (TypeScript & JSON Schemas)

#### 1. Audio Manifest Contract (`manifest.json` & `manifest.js`)
```typescript
interface AudioCue {
  index: number;
  type: "h2" | "h3" | "p" | "figure" | "callout" | "formula-box" | "chapter-quote";
  text: string;
  start_ms: number;
  end_ms: number;
  duration_ms: number;
}

interface AudioSection {
  title: string;
  audio_file: string;
  total_duration_ms: number;
  cues: AudioCue[];
}

interface TeacherAudioManifest {
  course: string;
  lesson: string;
  voice: "bn-BD-PradeepNeural" | "bn-BD-NabanitaNeural" | "gemini_flash_tts";
  mode: "authentic_teacher";
  sections: Record<string, AudioSection>;
}
```

#### 2. Web Component Interface Registry
- `<b1b-navbar>`: Props: `courseTitle`, `courseUrl`, `currentLesson`, `totalLessons`, `prevUrl`, `nextUrl`.
- `<b1b-hero-player>`: Props: `localVideoSrc`, `youtubeId`, `defaultMode` ('local' | 'youtube'). Emits `playStateChanged`.
- `<b1b-section>`: Props: `sectionId`, `sectionTitle`, `narrateEnabled`. Integrates karaoke cue highlights.
- `<b1b-quiz>`: Props: `question`, `options`, `correctIndex`, `explanation`, `revealAllowed`.
- `<b1b-interactive-lab>`: Props: `labType`, `controlsConfig`, `themeResponsive`. Synchronizes with day/night observers.

### 2.4 Complete Phonetic Safeguard Dictionary (19 Symbols & Rules)
All subagents and TTS pipelines must strictly apply the 19 canonical transliterations:
1. `AI` ➔ **`এআই`**
2. `3D` ➔ **`থ্রিডি`**
3. `2D` ➔ **`টুডি`**
4. `API` ➔ **`এপিআই`**
5. `UI` ➔ **`ইউআই`**
6. `EGM` ➔ **`ইজিএম`**
7. `SEO` ➔ **`এসইও`**
8. `ML` ➔ **`এমএল`**
9. `x-অক্ষ` ➔ **`এক্স অক্ষ`**
10. `y-অক্ষ` ➔ **`ওয়াই অক্ষ`**
11. `z-অক্ষ` ➔ **`জেড অক্ষ`**
12. `\hat{i}` ➔ **`আই হ্যাট`**
13. `\hat{j}` ➔ **`জে হ্যাট`**
14. `\hat{k}` ➔ **`কে হ্যাট`**
15. $dx, dt, df$ ➔ **`ডি এক্স`**, **`ডি টি`**, **`ডি এফ`**
16. $\vec{v}, \vec{w}$ ➔ **`ভেক্টর ভি`**, **`ভেক্টর ডব্লিউ`**
17. $\nabla \cdot \vec{F}$ ➔ **`ডাইভারজেন্স অফ এফ`**
18. $x_1, x_2$ ➔ **`এক্স ওয়ান`**, **`এক্স টু`**
19. $x^2$ ➔ **`এক্স স্কয়ার`**, $\pi R^2$ ➔ **`পাই আর স্কয়ার`**

### 2.5 Offline Strategy & WCAG 2.1 AA Accessibility
- **Zero-CORS Offline Support:** Audio manifests are distributed as self-executing IIFE scripts (`manifest.js` setting `window.TEACHER_AUDIO_MANIFEST`), allowing local execution under `file:///` without browser CORS violations.
- **Self-Hosted Assets:** KaTeX CSS/fonts and Hind Siliguri / Noto Serif fonts are fully self-hosted under `assets/libs/` and `assets/fonts/`.
- **WCAG 2.1 AA Compliance:**
  - KaTeX equations are rendered with MathML hidden fallbacks (`aria-label` equations).
  - High-contrast visualizer grids: minimum 4.5:1 text-to-background contrast in both light (`#f8fafc`) and dark (`#0b0c12`) themes.
  - Complete keyboard control: `Spacebar` (play/pause), `ArrowLeft`/`ArrowRight` (karaoke cue seek), `ArrowUp`/`ArrowDown` (section jump).

---

## 3. Alternatives Considered

### Alternative 1: Maintaining Two Separate Governance Documents
- **Concept:** Keeping `WEB_PLATFORM_AGENT_BOUNDARIES.md` for agents and `LESSON_PRODUCTION_STANDARD.md` for human reviewers.
- **Why Rejected:**
  - *Governance Fork:* Caused immediate divergence in media paths (`media_vault/` vs `departments/`), TTS engine choice, and phonetic rules.
  - *Maintenance Overhead:* Changes to audio or video contracts required dual synchronized updates, causing drift.
- **Decision:** *Rejected by author:* Reconciled into a single unified specification (`PRODUCTION_PIPELINE_SPEC.md`).

### Alternative 2: Pure REST API / Cloud CDN for Audio Manifests
- **Concept:** Fetching JSON manifests via `fetch('/api/audio/manifest.json')` from a remote server or local web server.
- **Why Rejected:**
  - *Breaks Offline Student Use:* When opened directly via local file browsers (`file:///D:/.../lesson_01.html`), modern browser security blocks cross-origin `fetch()` requests.
- **Decision:** *Rejected by author:* Dual-export strategy: `manifest.json` for tooling and IIFE `manifest.js` (`window.TEACHER_AUDIO_MANIFEST = {...}`) for zero-CORS local offline playback.

### Alternative 3: Complex Single Page App (SPA) Frameworks (React / Svelte)
- **Concept:** Rebuilding the entire curriculum as a Next.js or React web app.
- **Why Rejected:**
  - *Bloat & Build Tooling Overhead:* Requires continuous Node.js build steps, hydration overhead, and massive `node_modules` footprints.
  - *Offline Vulnerability:* Native browser execution of vanilla Web Components is faster, self-contained, and requires zero compilation steps.
- **Decision:** *Rejected by author:* Zero-dependency isomorphic Web Components.

---

## 4. Detailed Implementation & Consolidation Plan

### 4.1 Governance Consolidation Map
- Merge `governance/WEB_PLATFORM_AGENT_BOUNDARIES.md` and `governance/LESSON_PRODUCTION_STANDARD.md` into:  
  **`governance/PRODUCTION_PIPELINE_SPEC.md`**
- Update existing documents to point normatively to `PRODUCTION_PIPELINE_SPEC.md` as the single canonical source of truth.

### 4.2 Machine-Enforced Linting & Boundary Rules
- Implement an automated governance validator (`validate_platform_governance.py`) that checks:
  1. No `.audio-track-bar` elements exist in any lesson.
  2. All audio references use the canonical `assets/audio/` or `departments/` taxonomy.
  3. All KaTeX blocks are accompanied by accessible labels.
  4. Both `manifest.js` and `manifest.json` exist for every lesson.
  5. All 19 phonetic safeguards are verified with regex in speech scripts.

---

## 5. Critical User Journeys (CUJs)

### CUJ 1: Student Views a Bengali Lesson Offline
*   **Given**: Student has downloaded the `web_platform/` folder and opens `courses/linear_algebra/lesson_01.html` via `file:///` in browser.
*   **When**: Page loads; KaTeX renders locally; `manifest.js` executes as IIFE setting `window.TEACHER_AUDIO_MANIFEST`.
*   **Then**: 
    - Lesson renders with Bengali textbook content (KaTeX math, SVG figures, callouts).
    - Hero video defaults to local dubbed Bengali MP4 (YouTube hidden).
    - Floating audio pill (`#smartAudioPill`) visible; clicking plays teacher narration with karaoke highlight.
    - Zero English vocal bleed; original SFX preserved at -3dB headroom.

### CUJ 2: Student Switches Between Video and Teacher Narration
*   **Given**: Lesson page loaded; student clicks play on hero video (`VIDEO_PLAYING` state).
*   **When**: Student clicks floating audio pill or section listen button (`NARRATION_PLAY_CLICK` trigger).
*   **Then**: 
    - Video pauses immediately (0ms cross-pause); narration starts from corresponding timestamp.
    - State machine transitions: `VIDEO_PLAYING` → `NARRATION_PLAYING`.
    - Karaoke highlight syncs to narration audio position.

### CUJ 3: Student Navigates Course via Chapter Stepper
*   **Given**: Student on `lesson_01.html`; `curriculum_index.json` loaded.
*   **When**: Student clicks next chapter stepper (`‹ ০১ / ০৫ ›`) or prev/next navigation cards.
*   **Then**: 
    - Browser navigates to `lesson_02.html` (or previous).
    - Navbar updates course title, lesson number, progress.
    - Scroll position resets; mode preference (Watch/Read) persists via `localStorage`.

### CUJ 4: Content Adapter Produces Lesson Assets
*   **Given**: Source 3B1B English transcript + video + figures downloaded.
*   **When**: Content Adapter runs pipeline: (a) Phonetic Bengali script generation → (b) Edge-TTS batch synthesis → (c) Demucs v4 stem separation → (d) Wiener filtering + hard gating → (e) EBU R128 normalization → (f) Silence delimiter insertion → (g) Audio slicing & manifest generation.
*   **Then**: 
    - `master_script.json` with phonetic Bengali (all 19 safeguards applied).
    - `stems_isolated/` with clean vocal + SFX WAVs.
    - `sec_*.mp3` segments + `manifest.json` + `manifest.js` (IIFE) in `assets/audio/linear_algebra/lesson_01/`.
    - All files pass `validate_platform_governance.py` checks.

---

## 6. Non-Functional Requirements

### 6.1 Performance & Latency
- **Initial Load (Offline)**: < 2s `file:///` load for lesson page (KaTeX + CSS + hero image).
- **KaTeX Rendering**: < 100ms for typical lesson math content.
- **Audio Manifest Parse**: < 50ms IIFE execution + `window.TEACHER_AUDIO_MANIFEST` availability.
- **Karaoke Sync Latency**: < 20ms drift between audio position and highlight update.
- **Bundle Size**: Zero JS framework; `lesson_components.js` < 50KB gzipped.

### 6.2 Rollout & Rollback
- **Feature Flags**: `localStorage` keys for mode preference (`watch` | `read`), theme (`light` | `dark`), narration enabled.
- **Backward Compatibility**: Audio manifest schema versioned (`manifest.version`); lessons declare `requires: "manifest@^1.0"`.
- **Rollback**: Git revert of `web_platform/` changes; canonical taxonomy in `departments/` immutable once published.

### 6.3 Security & Privacy
- **Zero External Requests**: Offline-first; no CDN, no analytics, no tracking.
- **CORS Safety**: `file:///` execution uses IIFE manifests; no `fetch()` calls.
- **Content Integrity**: Subresource Integrity (SRI) hashes for self-hosted KaTeX/fonts in production builds.

### 6.4 Accessibility (WCAG 2.1 AA)
- **Keyboard Navigation**: All interactive elements reachable and operable via keyboard.
- **Screen Reader**: MathML hidden fallbacks for KaTeX; ARIA labels for audio controls, video player, karaoke regions.
- **Color Contrast**: 4.5:1 minimum text/background in both themes; 3:1 for UI components.
- **Reduced Motion**: `prefers-reduced-motion` disables drawer animations, karaoke highlight transitions.
- **Focus Management**: Visible focus rings; logical tab order through navbar, hero, sections, audio pill.

---

## 7. Additional Resources

*   `governance/AGENT_WORKFLOW_GUIDELINES.md` — Multi-agent orchestration framework (subordinate to this spec)
*   `governance/WEB_PLATFORM_AGENT_BOUNDARIES.md` — Legacy agent territory map (superseded)
*   `governance/LESSON_PRODUCTION_STANDARD.md` — Legacy production standard (superseded)
*   `concepts_brief.md` — Original EGM ideation brief with architectural resolutions
*   `master-voice-dubbing` skill — Studio-grade Bengali dubbing protocols (normative reference for §2.4, §2.5)
*   3Blue1Brown official lessons (`3blue1brown.com/lessons/`) — Content fidelity reference
*   EBU R128 / ITU-R BS.1770 — Loudness normalization standard
*   Demucs v4 (Facebook Research) — 2-stem separation model
*   Edge-TTS `bn-BD-PradeepNeural` / `bn-BD-NabanitaNeural` — Voice specifications

---

## 8. Future Improvements

*   **Multi-Language Support**: Extend phonetic dictionary and TTS voice map for Hindi/English toggle.
*   **Interactive Proof Explorer**: Collapsible proof steps with KaTeX, linked to video timestamps.
*   **Adaptive Video Streaming**: HLS/DASH for dubbed videos with quality selector (requires minimal Service Worker).
*   **Analytics Opt-In**: Privacy-preserving local analytics (lesson completion, quiz scores) exported on demand.
*   **PWA Installability**: Full manifest + Service Worker for "Add to Home Screen" on mobile.

---

## 9. Open Questions

*   **Q1**: Exact `curriculum_index.json` schema — should it embed lesson metadata or reference separate `lesson_XX.json` files?
*   **Q2**: KaTeX macro definitions — standard 3B1B macros vs. custom Bengali pedagogical macros?
*   **Q3**: Demucs v4 model artifact storage — bundle in repo (Git LFS) or download at build time?
*   **Q4**: Exact EBU R128 target: -14.0 LUFS integrated, -1.0 dBTP true peak — confirm for Bengali speech + SFX mix.
*   **Q5**: Service Worker cache strategy for 500MB+ dubbed video assets — stale-while-revalidate vs. cache-first?

---

## 10. Detailed Implementation Plan

### 10.1 Target Files to Create/Modify

#### 1. `governance/PRODUCTION_PIPELINE_SPEC.md` (Create)
*   **Type / Scope**: Canonical normative specification (this document).
*   **Proposed Changes**: Single source of truth replacing `WEB_PLATFORM_AGENT_BOUNDARIES.md` and `LESSON_PRODUCTION_STANDARD.md`.

#### 2. `web_platform/assets/js/narration_engine.js` (Create)
*   **Type / Scope**: Vanilla ES6 module (IIFE-compatible).
*   **Proposed Changes**: 
    - Implements state machine (§2.2) with `IDLE` | `VIDEO_PLAYING` | `NARRATION_PLAYING`.
    - Consumes `window.TEACHER_AUDIO_MANIFEST` (IIFE manifest).
    - Controls `#smartAudioPill`, section listen buttons, karaoke highlighting.
    - Emits `playStateChanged` events for external sync.

#### 3. `web_platform/assets/css/main.css` (Create)
*   **Type / Scope**: Design token system + global styles.
*   **Proposed Changes**: CSS custom properties for colors, spacing, typography (Bengali font stack), motion tokens, dark/light themes, WCAG contrast ratios.

#### 4. `web_platform/assets/css/lesson.css` (Create)
*   **Type / Scope**: Lesson-specific component styles.
*   **Proposed Changes**: Hero player, section layout, bookmark grid (`.bookmark-grid` with `flex-wrap: wrap`), floating audio pill, karaoke highlight animations.

#### 5. `web_platform/assets/js/lesson_components.js` (Create)
*   **Type / Scope**: Vanilla Web Component definitions.
*   **Proposed Changes**: Register 9 components: `<b1b-navbar>`, `<b1b-hero-player>`, `<b1b-section>`, `<b1b-media-tab>`, `<b1b-callout>`, `<b1b-figure>`, `<b1b-formula>`, `<b1b-quiz>`, `<b1b-interactive-lab>`.

#### 6. `web_platform/assets/libs/katex/` (Create - Vendored)
*   **Type / Scope**: Self-hosted KaTeX v0.16+ + webfonts.
*   **Proposed Changes**: Copy KaTeX dist + Bengali-compatible fonts (Hind Siliguri, Noto Sans Bengali) for offline rendering.

#### 7. `web_platform/courses/<course_slug>/lesson_<XX>.html` (Create per lesson)
*   **Type / Scope**: Lesson entry point (standalone HTML).
*   **Proposed Changes**: 
    - Loads `main.css`, `lesson.css`, `lesson_components.js`, `narration_engine.js`.
    - Embeds `manifest.js` as `<script src="../../assets/audio/<course>/<lesson>/manifest.js"></script>`.
    - Hero: `#heroLocalBox` (local video, default visible) + `#heroYtBox` (YouTube embed, hidden).
    - Sections: `<b1b-section>` with `data-cue-index` for karaoke.
    - Mode toggle: Watch (hero + playlist drawer) | Read (full textbook scroll).

#### 8. `web_platform/data/<course_slug>/lesson_<XX>.json` (Create per lesson)
*   **Type / Scope**: Structured lesson metadata.
*   **Proposed Changes**: Sections, figures, quizzes, formulas, video chapters, KaTeX blocks — consumed by components for Read mode rendering.

#### 9. `departments/learning_paths/stem_mathematics/3blue1brown_courses/<course_slug>/lesson_<XX>_<slug>/dubbing_pipeline/master_script.json` (Create per lesson)
*   **Type / Scope**: Production master script with phonetic Bengali.
*   **Proposed Changes**: All 19 phonetic safeguards applied; timestamps aligned to source video; speaker diarization; TTS batching delimiters (`\n\n... ... ...\n\n`).

#### 10. `departments/learning_paths/stem_mathematics/3blue1brown_courses/<course_slug>/lesson_<XX>_<slug>/dubbing_pipeline/stems_isolated/` (Create per lesson)
*   **Type / Scope**: Demucs v4 2-stem WAV outputs.
*   **Proposed Changes**: `vocals.wav` (clean Bengali narration), `no_vocals.wav` (pristine SFX bed).

#### 11. `web_platform/assets/audio/<course>/<lesson>/sec_*.mp3` (Create per lesson)
*   **Type / Scope**: Final dubbed audio segments.
*   **Proposed Changes**: Sliced from master TTS at silence delimiters; EBU R128 normalized; sidechain-ducked with SFX bed.

#### 12. `web_platform/assets/audio/<course>/<lesson>/manifest.json` & `manifest.js` (Create per lesson)
*   **Type / Scope**: Audio manifest (JSON + IIFE).
*   **Proposed Changes**: Conforms to `TeacherAudioManifest` interface (§2.3.1); `manifest.js` sets `window.TEACHER_AUDIO_MANIFEST`.

#### 13. `validate_platform_governance.py` (Create)
*   **Type / Scope**: CI governance validator.
*   **Proposed Changes**: Checks 5 rules (§4.2); exits non-zero on violation; integrated in GitHub Actions.

#### 14. `.github/workflows/ci.yml` (Create)
*   **Type / Scope**: CI pipeline.
*   **Proposed Changes**: Lint, type-check, unit tests, visual regression (Playwright), offline smoke test (`file://`), governance validation, bundle size check.

#### 15. `curriculum_index.json` (Create)
*   **Type / Scope**: Course catalog metadata.
*   **Proposed Changes**: Course list, lesson ordering, titles, slugs, video durations, YouTube IDs, local video paths.

### 10.2 Verification Plan

*   **Compilation/Build**: `npm run build` (esbuild: bundles JS, copies assets, generates `manifest.js` IIFE).
*   **Unit Tests**: `npm test` (Vitest: narration_engine state machine, component rendering, phonetic validator).
*   **Static Analysis & Linting**: `npm run lint` (ESLint + `no-restricted-paths` for fleet boundaries).
*   **Test Coverage Requirement**: 85%+ branch coverage for core logic (state machine, manifest parsing, karaoke sync).
*   **E2E/Integration**: `npm run e2e` (Playwright: offline load, video/narration mutual exclusion, bookmark wrap at 320/768/1440px, keyboard navigation, Bengali font render).
*   **Governance Validation**: `python validate_platform_governance.py` on all lesson HTML + assets.
*   **Audio Quality Gates**: Automated EBU R128 check (-14 LUFS ±0.5), zero vocal bleed verification (spectral diff vs. English source), phonetic safeguard regex scan.

---

*Drafted with EGM*