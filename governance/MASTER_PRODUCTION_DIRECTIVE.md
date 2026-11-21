# 3BLUE1BROWN BENGALI WEB PLATFORM — MASTER PRODUCTION & ARCHITECTURAL BRIEF
# Date: 2026-11-05 | Lead System Architect: Antigravity

## 0. GLOBAL STRATEGY PIVOT: ISOMORPHIC SINGLE-SHELL WEB COMPONENTS ARCHITECTURE
**MANDATORY ARCHITECTURAL DIRECTIVE (Approved by Board):**
1. **DO NOT WRITE LEGACY STATIC MONOLITHIC HTML LESSON PAGES:**
   - Any agent working on upcoming courses/series (Calculus, Probability, Differential Equations, Lockdown Math, Neural Networks, etc.) MUST NOT waste time generating heavy static monolithic HTML pages.
   - **ROLE OF UPCOMING LESSON BUILDERS:** Focus strictly on producing high-quality **RESOURCES ONLY**:
     - Accurate Bengali Master Scripts (`..._bangla_master_script.json`)
     - Pedagogically audited audio manifests (`manifest.js`, `manifest.json`, `..._cues.json`)
     - Clean SVG vector diagrams and figures in `assets/figures/`
     - Pure structured lesson data/markdown/KaTeX blocks.
2. **ISOMORPHIC SINGLE-SHELL PROGRESSIVE SPA TARGET:**
   - All courses and lessons will render through the universal Web Components shell (`<b1b-navbar>`, `<b1b-hero-player>`, `<b1b-section>`, `<b1b-media-tab>`, `<b1b-callout>`, `<b1b-figure>`, `<b1b-formula>`, `<b1b-quiz>`, `<b1b-interactive-lab>`, `<b1b-chapter-nav>`, `<b1b-footer>`).
   - The shell loads once; clicking next/prev chapter dynamically swaps the article view in under 50ms without full-page reloads, preserving KaTeX, fonts, audio engine state, and eliminating screen flicker.

## 1. COMPREHENSIVE PLATFORM ARCHITECTURAL MANDATES (STRICT RULES)
Every subagent, contributor, and automated script MUST adhere strictly to these permanent standards:

### A. Media & Playback Authority (Zero Overlap & Single Sound Rule)
1. **NO DUBBED HERO MASTER AUDIO BAR:**
   - The hero master audio bar (`.audio-track-bar`, `🎧 বাংলা অডিও মাস্টার`) is permanently abolished and MUST NEVER be re-introduced into any lesson.
   - The video player (`#mainVideo`) and the Smart Teacher Narration Engine (`narration_engine.js`) are the SOLE authorized media players.
2. **STRICT SINGLE AUDIO AUTHORITY:**
   - Any video play event (`play`) MUST immediately pause teacher narration and all other videos.
   - Any teacher narration play event MUST immediately pause all video players (local HTML5 and YouTube iframes).
   - Only ONE audio/video source may produce sound at any millisecond across the platform.
3. **DEFAULT VIDEO PLAYBACK:**
   - In all lesson pages, the local Bengali video (`#heroLocalBox`) is ALWAYS displayed by default (`display: block`).
   - YouTube iframe (`#heroYtBox`) is hidden by default (`display: none`).
   - The toggle button MUST strictly be labeled **`▶ অরিজিনাল ভিডিও`** (never "মূল ইউটিউব").

### B. Smart Teacher Narration Engine Standards
1. **VOICE PROFILE & PHILOSOPHY:**
   - Synthesized using Edge-TTS male educator voice **`bn-BD-PradeepNeural`** (pacing: `-2%`, natural pedagogical cadence).
   - Delivery is that of a warm, articulate, caring Bengali mathematics educator explaining concepts and figures live to students.
2. **STRICT PHONETIC SAFEGUARDS:**
   - All LaTeX and acronyms must be phonetically transliterated into natural Bengali:
     - `\hat{i}` -> `আই হ্যাট`, `\hat{j}` -> `জে হ্যাট`, `\hat{k}` -> `কে হ্যাট`
     - `\vec{v}` -> `ভেক্টর ভি`, `\vec{w}` -> `ভেক্টর ডব্লিউ`
     - `2D` -> `টুডি`, `3D` -> `থ্রিডি`, `x-অক্ষ` -> `এক্স অক্ষ`, `y-অক্ষ` -> `ওয়াই অক্ষ`
     - $dx, dt, df$ -> `ডি এক্স`, `ডি টি`, `ডি এফ`
     - $\pi R^2$ -> `পাই আর স্কয়ার`
3. **FILE TAXONOMY & ZERO-CORS OFFLINE SUPPORT:**
   - Audio files MUST follow the strict directory structure:  
     `departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/<course_id>/<lesson_id>/`
   - Every audio directory MUST contain both `manifest.json` and `manifest.js` (`window.TEACHER_AUDIO_MANIFEST = {...}`).
   - `<script src="../../assets/audio/.../manifest.js"></script>` MUST be linked in `<head>` so that offline `file:///` viewing works without browser CORS blockage.
4. **SYNCHRONIZED KARAOKE & KEYBOARD NAVIGATION:**
   - Clicking next/prev items (`>>` / `<<`) or pressing `ArrowRight` / `ArrowLeft` MUST immediately jump the audio to that exact cue (`currentTime = cue.start_ms / 1000`) and visually highlight the active DOM element.
   - Pressing `Spacebar` toggles play/pause for narration (in Read mode) or video (in Watch mode).
   - Pressing `ArrowDown` / `ArrowUp` jumps to next/prev section.

### C. Typography & UI Standards

### D. Theme Consistency, SVG Visualizer & Light Mode Persistence Standard (STRICT RULE)
1. **SYNCHRONOUS HEAD THEME INITIALIZER (ZERO-FOUC & RELOAD BUG FIX):**
   - Every HTML page MUST have an immediate synchronous theme initialization script placed at the very start of `<head>`, before any stylesheet or deferred scripts:
     ```html
     <script>(function(){const t=localStorage.getItem('3b1b-theme')||'dark';document.documentElement.setAttribute('data-theme',t);if(t==='dark')document.documentElement.classList.add('dark');else document.documentElement.classList.remove('dark');})();</script>
     ```
   - This guarantees that when a user refreshes or navigates in light mode, `document.documentElement` receives `data-theme="light"` synchronously before inline SVG visualizer scripts or DOM rendering occurs, preventing white-on-white invisible elements.
2. **CSS-DRIVEN SVG STYLING & CLASS ARCHITECTURE:**
   - Visualizer SVGs must never rely solely on fragile hardcoded presentation attributes in JavaScript.
   - All SVG grid lines, axes, and tick text must have explicit semantic CSS classes: `.grid-line`, `.axis-line`, and `.axis-text`.
   - `assets/css/lesson.css` enforces light and dark theme contrast:
     ```css
     .viz-svg .grid-line { stroke: rgba(255, 255, 255, 0.18); stroke-width: 1.2px; }
     [data-theme="light"] .viz-svg .grid-line, :root:not(.dark) .viz-svg .grid-line { stroke: rgba(0, 0, 0, 0.18) !important; }
     .viz-svg .axis-line { stroke: rgba(255, 255, 255, 0.65); stroke-width: 2px; }
     [data-theme="light"] .viz-svg .axis-line, :root:not(.dark) .viz-svg .axis-line { stroke: rgba(0, 0, 0, 0.7) !important; }
     .viz-svg .axis-text { fill: rgba(255, 255, 255, 0.7); }
     [data-theme="light"] .viz-svg .axis-text, :root:not(.dark) .viz-svg .axis-text { fill: rgba(0, 0, 0, 0.75) !important; }
     ```
3. **REACTIVE MUTATIONOBSERVER ON ROOT ELEMENT:**
   - All interactive visualizers MUST attach a `MutationObserver` to `document.documentElement` observing `attributes` (`data-theme`, `class`).
   - When the user toggles the theme, the observer immediately re-renders the grid (`buildGrid()`) and updates vectors (`updateVisualizer()`) with 0ms delay.

### E. Gemini Multimodal Visual & Audio Auditor Mandate
1. **DEDICATED GEMINI PEDAGOGICAL AUDITOR:**
   - Every lesson figure, diagram, and canvas interactive must undergo explicit multimodal visual inspection.
   - The teacher's audio narration and cue text must describe exactly what the student sees in the figure (e.g., arrow direction, length scaling, coordinate grid projection, matrix rotation angle).
   - Gemini Multimodal Auditor continuously validates all lessons from Chapter 01 to the latest and reports discrepancies in `governance/GEMINI_PEDAGOGICAL_AUDIT_REPORT.md`.
1. **NO HORIZONTAL SCROLLBAR ON BOOKMARKS:**
   - Bookmark ribbons MUST use CSS Grid (`.bookmark-grid`, `repeat(auto-fill, minmax(230px, 1fr))`) or wrapping (`flex-wrap: wrap; overflow-x: visible;`).
   - Never allow horizontal overflow scrollbars on bookmark ribbons.
2. **BENGALI NUMERAL SAFEGUARD:**
   - All chapter headings and labels MUST use two-digit padded numerals (`অধ্যায় ০১`, `অধ্যায় ০২`, etc.) with `display: inline-block; line-height: 1.6; font-weight: 600;` to prevent the digit `১` from rendering clipped as a comma `,`.
3. **DUAL FONT SUPPORT:**
   - All pages support instant font switching via `toggleFont()`:
     - Default: **Hind Siliguri** (`'Hind Siliguri', 'Noto Sans Bengali', sans-serif`)
     - Alternative: **Noto Serif Bengali** (`'Noto Serif Bengali', 'Kalpurush', serif`)
   - The user's preference is saved in `localStorage['3b1b-font']`.

---

## 2. ACTIVE SUBAGENT WORK DISTRIBUTION & PROGRESS LOG

| Subagent ID | Task / Course Domain | Status | Key Deliverable |
|---|---|---|---|
| `ses_e55cdedb0ffewVOg65hH4ksybc` | Linear Algebra Lesson 02 Audio | Running | `sec_01` to `sec_04` MP3s + cues for Basis & Span |
| `ses_e55cdd40fffesMaAH9UZDQ49M5` | Linear Algebra Lesson 03 Audio | **COMPLETED** | 4 section MP3s + cues + `manifest.js` deployed |
| `ses_e55cd1fd6ffe4Ut5umg5te6dRP` | Linear Algebra Lesson 04 Audio | **COMPLETED** | 4 section MP3s + cues + `manifest.js` deployed |
| `ses_e55ccfc22ffeckOJ12r56U073D` | Linear Algebra Lesson 05 Audio | Running | 3D Transformations audio + cues manifest |
| `ses_e55ccd3bdffeWB8N7AGLWoBnm0` | Calculus Lesson 01 Audio | **COMPLETED** | 3 section MP3s + circle rings cues deployed |
| `ses_e55cd9ff3ffe3ReyBylMHlMAsB` | Calculus Lesson 02 Page | Running | Derivative Paradox + Zoom Curve visualizer |
| `ses_e55cd7ab1ffeBMg1EifN9OV6Jp` | Differential Equations L02 | Running | Pendulum & Phase Space simulation |
| `ses_e55cd57eaffeRQuXTvNxfHNT1w` | Probability Lesson 02 Page | **COMPLETED** | Bayes Medical Test 1000-dot simulator |
| `ses_e55cd3b7dffeIcsFc25kOgSpT6` | Lockdown Math Lesson 02 | Running | Modulo 7 Calendar Wheel visualizer |
| `ses_e55ce0807ffeOrUXJ39I6P9xND` | Neural Networks Lesson 01 | Running | Digit drawing grid + forward propagation lab |

---

## 3. LEAD AGENT SUPERVISORY DIRECTIVE
- No agent may modify files outside their designated subfolder.
- The Lead Agent continuously audits generated files before merging or updating the curriculum index.
