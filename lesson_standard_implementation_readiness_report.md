# LESSON_PRODUCTION_STANDARD.md — Implementation Readiness Review

**Document**: `governance/LESSON_PRODUCTION_STANDARD.md`  
**Review Date**: 2026-11-05  
**Reviewers**: egm-implementation-readiness, egm-codebase-details, egm-style  
**Context**: Greenfield 3Blue1Brown Bengali Platform — Lesson Production Standard

---

## Executive Summary

The document is a **philosophy/guidelines artifact**, not an implementation specification. It establishes *what* the platform should achieve but provides almost zero *how*. A developer cannot start coding from this alone. **Verdict: NO-GO** — requires a detailed technical specification (data models, component contracts, API schemas, build pipeline, test strategy) before any implementation work begins.

---

## 1. egm-implementation-readiness — Can this be implemented as written?

### 🔴 Blockers

| # | Finding | Why It Blocks Implementation |
|---|---------|------------------------------|
| IR-01 | **No data model / content schema** | The doc mandates "100% fidelity to 3b1b lessons" but defines no schema for lesson content (sections, diagrams, quizzes, formulas, video timestamps, KaTeX blocks). Devs need a JSON/TypeScript schema to build parsers, renderers, and validators. |
| IR-02 | **No component interface contracts** | Features like "Floating TOC Drawer", "Quick Chapter Stepper", "Watch/Read mode switcher", "Interactive Canvas Lab", "Quiz System" are named but have zero props, events, state, or API definitions. Cannot build reusable components without interfaces. |
| IR-03 | **No asset pipeline specification** | Mentions `../../assets/figures/la_0X/`, `../../media_vault/lesson_0X/`, shared CSS/JS — but no build-time asset processing (optimization, hashing, CDN, fallback), no manifest format, no versioning strategy. |
| IR-04 | **No video player / dubbing integration spec** | "Local high-quality dubbed video + YouTube switcher" — no player library choice (Video.js? Plyr? native?), no caption/track format (VTT?), no sync protocol for dubbed audio, no playlist drawer data structure. |
| IR-05 | **No KaTeX rendering strategy** | "Full offline KaTeX-rich textbook" — but no decision on server-side vs client-side rendering, macro definitions, delimiter config, fallback fonts, math accessibility (MathML/ARIA), or performance budget for heavy formulas. |
| IR-06 | **No quiz/interactive canvas data model** | "Correct/incorrect feedback, 'Show Answer' button" — no question schema (multiple choice? free-form? numeric? diagram-based?), no state persistence (localStorage? IndexedDB? server?), no analytics events. |
| IR-07 | **No TTS script format / phonetic validation** | Mandates phonetic Bengali (`এক্স অক্ষ`, `আই হ্যাট`) but provides no machine-readable format (SSML? custom markdown?), no validation rules, no dictionary of approved phonetic mappings, no CI lint for forbidden Latin chars. |
| IR-08 | **No navigation / routing architecture** | "Quick chapter stepper", "prev/next chapter cards", "5-chapter playlist drawer" — implies a lesson graph but no route params, no lesson metadata registry, no programmatic navigation API. |
| IR-09 | **No offline / PWA strategy** | "Full offline KaTeX textbook", "local assets" — but no service worker config, no cache-first vs stale-while-revalidate policy, no background sync, no install prompt UX. |
| IR-10 | **No accessibility (a11y) requirements** | Zero mention of WCAG, keyboard navigation, screen reader support for math, color contrast, focus management in drawers/modals, reduced motion. Legal/usability risk. |

### 🟡 Major Gaps

| # | Finding | Impact |
|---|---------|--------|
| IR-11 | **No error boundary / fallback strategy** | What happens when a figure fails to load? Video fails? KaTeX parse error? Quiz state corrupted? |
| IR-12 | **No internationalization architecture** | Bengali is primary, but what about English fallback? RTL? Number formatting? Date/time? |
| IR-13 | **No performance budgets** | Target FCP/LCP/TTI? Bundle size limits? Image/video compression targets? |
| IR-14 | **No testing strategy** | Unit? Integration? E2E? Visual regression for math rendering? A11y audit? Phonetic script validation? |
| IR-15 | **No deployment / CI/CD pipeline** | Static export? SSR? Edge? Preview deployments? Asset fingerprinting? Rollback? |
| IR-16 | **No content authoring workflow** | How do content creators write lessons? Markdown? CMS? Custom editor? Review/approval flow? |
| IR-17 | **No versioning / migration plan** | Lesson schema v1 → v2? Asset path changes? Breaking CSS/JS changes? |
| IR-18 | **No analytics / telemetry spec** | What events? Privacy compliance? Consent? |

### 🟢 Nits

| # | Finding |
|---|---------|
| IR-19 | Document uses Bengali section numbers (১, ২, ৩) — inconsistent with typical technical spec numbering. |
| IR-20 | Relative paths (`../../assets/...`) assume a specific folder depth; brittle for nested routes. |

---

## 2. egm-codebase-details — Greenfield Constraints (What Must Exist)

### 🔴 Blockers

| # | Required Artifact | Description |
|---|-------------------|-------------|
| CD-01 | **Lesson Content Schema (TypeScript + JSON Schema)** | `LessonManifest` with: `id`, `slug`, `title`, `description`, `chapterIndex`, `totalChapters`, `sections[]` (each with `type: 'text'|'figure'|'quiz'|'formula'|'video'`, `content`, `metadata`), `figures[]` (src, alt, caption, dimensions), `quizzes[]` (schema below), `video` (youtubeId, dubbedSrc, duration, chapters[]), `katexMacros`, `phoneticScript` (validated). |
| CD-02 | **Quiz Question Schema** | `type: 'single'|'multiple'|'numeric'|'text'|'diagram'`, `prompt` (markdown+KaTeX), `options[]` (label, isCorrect, feedback), `answer` (for non-MC), `explanation`, `difficulty`, `tags`. |
| CD-03 | **Component Interface Registry** | TypeScript interfaces for every named UI component: `FloatingTOCDrawer`, `ChapterStepper`, `NavCard`, `WatchModePlayer`, `ReadModeTextbook`, `PlaylistDrawer`, `InteractiveCanvas`, `QuizWidget`, `VideoSwitcher`. Each: `props`, `emits`, `slots`, `state`, `methods`. |
| CD-04 | **Asset Manifest & Pipeline Config** | Vite/esbuild config: `assetsDir: 'assets'`, `publicDir: 'media_vault'`, figure optimization (WebP/AVIF, multiple sizes), video transcoding (H.264 + WebM, multiple bitrates), manifest.json with hashes, CDN base URL, cache headers. |
| CD-05 | **KaTeX Configuration Module** | `katex-config.ts`: delimiters (`$$...$$`, `$...$`, `\[...\]`, `\(...\)`), macros (\\hat, \\vec, \\mathbb, \\mathcal, custom), `throwOnError: false`, `trust: false`, SSR + hydration strategy, math ML output for a11y. |
| CD-06 | **Phonetic Script Validator** | CLI/lint rule: scans `.phonetic.md` or frontmatter, fails on Latin letters (`/[a-zA-Z]/` except approved acronyms), validates against `phonetic-dictionary.json` (এক্স, ওয়াই, জেড, আই হ্যাট, জে হ্যাট, কে হ্যাট, ডিটারমিন্যান্ট, ডট, দশমিক, etc.), suggests replacements. |
| CD-07 | **Routing & Lesson Registry** | File-system or manifest-based router: `/lessons/:slug`, `/lessons/:slug/watch`, `/lessons/:slug/read`, `/lessons/:slug/quiz/:quizId`. Registry: `lessons.index.json` with metadata for stepper, prev/next, playlist. |
| CD-08 | **Service Worker / PWA Config** | Workbox config: precache manifest, runtime caching (figures: cache-first, video: stale-while-revalidate, API: network-first), offline fallback page, background sync for quiz progress, install prompt. |
| CD-09 | **Video Player Wrapper Component** | Abstraction over Video.js/Plyr: `src` (dubbed|youtube), `tracks[]` (captions VTT), `chapters[]` (start, end, title), `onTimeUpdate`, `onChapterChange`, `switchSource()`, `playlistDrawer` integration. |
| CD-10 | **Shared Design Token System** | CSS custom properties / Tailwind config: colors, spacing, typography (Bengali font stack: Noto Sans Bengali, Hind Siliguri), motion tokens (reduced-motion), dark mode, focus-visible styles. |

### 🟡 Major Gaps

| # | Required Artifact | Description |
|---|-------------------|-------------|
| CD-11 | **Content Authoring CLI/SDK** | `create-lesson`, `validate-lesson`, `preview-lesson`, `build-lesson` commands. Markdown frontmatter + KaTeX + figure references + quiz blocks. |
| CD-12 | **Visual Regression Test Suite** | Playwright + pixelmatch for: KaTeX rendering across browsers, drawer animations, video player states, quiz feedback states. |
| CD-13 | **A11y Test Automation** | axe-core integration in CI: color contrast, keyboard traps, ARIA labels on drawers/player, math ML presence, focus order. |
| CD-14 | **Analytics Event Schema** | `lesson_view`, `mode_switch`, `chapter_navigate`, `quiz_attempt`, `quiz_complete`, `video_play`, `video_complete`, `asset_load_error`. |
| CD-15 | **Error Boundary & Fallback UI Components** | `<FigureFallback>`, `<VideoError>`, `<KaTeXError>`, `<QuizError>`, `<OfflineBanner>`. |
| CD-16 | **Content Migration Scripts** | v1→v2 schema migration, asset path rewrites, phonetic dictionary updates. |

### 🟢 Nits

| # | Note |
|---|------|
| CD-17 | Use `lesson-01` not `la_0X` for directory naming — more readable, matches slug. |
| CD-18 | Consider monorepo (Turborepo/Nx) for shared packages: `ui`, `content-schema`, `phonetic-validator`, `katex-config`, `player`. |

---

## 3. egm-style — Specification Precision (Unambiguous, Measurable, Testable)

### 🔴 Blockers

| # | Finding | Why It Fails Precision Test |
|---|---------|----------------------------|
| ST-01 | **"100% fidelity to official website" — untestable** | No diff tool, no snapshot baseline, no tolerance definition. "Exact same content" is subjective (whitespace? rendering differences? interactive vs static?). |
| ST-02 | **"More interactive & modern than original" — unmeasurable** | No interaction latency budget, no feature parity matrix, no UX benchmark. "Modern" is a moving target. |
| ST-03 | **"Phonetic Bengali" — no formal grammar** | Examples given (`এক্স অক্ষ`, `আই হ্যাট`) but no exhaustive rule set. Edge cases: subscripts (`x₁` → `এক্স সাব এক`?), superscripts (`x²` → `এক্স স্কয়ার`?), operators (`∇·F` → `ডেলিভা ডট এফ`?), Greek (`α, β, γ` → `অ্যালফা, বিটা, গামা`?). |
| ST-04 | **"Natural, fluent, rich pedagogical Bengali" — subjective** | No style guide: sentence length, vocabulary level, honorifics, active/passive preference, terminology consistency (determinant = `ডিটারমিন্যান্ট` always? or `নির্ণায়ক`?). |
| ST-05 | **"Interactive canvas lab" — no scope** | What interactions? Drag? Plot? Slider? Parameter sweep? Export? No acceptance criteria. |
| ST-06 | **"Offline KaTeX-rich textbook" — ambiguous** | Does "offline" mean Service Worker cached? Pre-rendered HTML? PDF export? Electron app? No definition. |
| ST-07 | **Relative paths (`../../assets/...`) — not portable** | Breaks if route depth changes. Should be absolute from root or import-aliased. |

### 🟡 Major Gaps

| # | Finding | Required Precision |
|---|---------|-------------------|
| ST-08 | **No acceptance criteria for any feature** | Each bullet needs: Given/When/Then or checklist (e.g., "Floating TOC Drawer: opens on click, closes on ESC/outside click, highlights active section on scroll, persists state in sessionStorage"). |
| ST-09 | **No responsive breakpoints defined** | Mobile (<640), tablet (640-1024), desktop (>1024)? Drawer behavior per breakpoint? |
| ST-10 | **No motion/animation specs** | Duration, easing, reduced-motion behavior for: drawer slide, stepper transition, card flip, playlist expand. |
| ST-11 | **No color/contrast tokens** | "Premium UI" needs design tokens: primary/secondary/accent, semantic colors (success/warning/error), focus ring, selection. |
| ST-12 | **No typography scale** | Bengali + Latin mixed: font families, sizes, line heights, letter spacing for headings/body/captions/code/math. |
| ST-13 | **No icon system spec** | SVG sprite? Font? Component library? Naming convention? |
| ST-14 | **No loading/empty/error states** | Skeleton screens? Spinners? Placeholder illustrations? Retry buttons? |
| ST-15 | **No content length guidelines** | Max sections per lesson? Max quiz questions? Max video duration? Figure size limits? |

### 🟢 Nits

| # | Finding |
|---|---------|
| ST-16 | Mix of Bengali and English technical terms in spec — pick one language for the spec itself. |
| ST-17 | Em-dash (`—`) mandated for TTS pauses but no guidance on frequency, duration mapping, or SSML `<break>` alternative. |

---

## Cross-Reviewer Synthesis: Top 10 Blockers to Resolve First

| Priority | Artifact | Owner | Dependencies |
|----------|----------|-------|--------------|
| 1 | Lesson Content Schema (TS + JSON Schema) | Lead Architect | — |
| 2 | Phonetic Script Validator + Dictionary | Linguist + Engineer | #1 |
| 3 | KaTeX Configuration Module | Frontend Lead | #1 |
| 4 | Component Interface Registry | Frontend Lead | #1 |
| 5 | Asset Pipeline & Manifest Config | DevOps + Frontend | #1 |
| 6 | Routing & Lesson Registry | Frontend Lead | #1 |
| 7 | Video Player Wrapper + Switcher Spec | Frontend Lead | #4, #5 |
| 8 | Quiz Schema + State Persistence | Frontend + Backend | #1 |
| 9 | PWA / Service Worker Config | DevOps | #5 |
| 10 | A11y Baseline + Test Automation | QA + Frontend | #4 |

---

## Readiness Verdict

### ❌ NO-GO

**The LESSON_PRODUCTION_STANDARD.md document is not implementation-ready.**

It functions as a **vision/philosophy document**, not a technical specification. A developer receiving this document would have to invent ~90% of the technical decisions themselves, leading to inconsistency, rework, and architectural drift.

### Required Before Go

1. **Produce a Technical Specification Document** (separate from this) covering all 🔴 Blocker items above.
2. **Prototype & validate** the Lesson Content Schema with 2 real 3b1b lessons.
3. **Implement the Phonetic Validator** and run it on existing dubbed scripts.
4. **Spike the KaTeX + SSR + a11y** rendering path.
5. **Define the Component Interface Registry** in TypeScript (can be stubs).
6. **Get stakeholder sign-off** on the spec (product, design, engineering, linguistics).

### Recommended Next Step

Commission an **EGM Draft** phase (using `egm-draft` skill) to produce the Technical Specification from this guideline, then run a full **EGM Review** (`egm-review`) on that spec before any coding begins.

---

*Report generated by EGM Implementation Readiness Reviewer (synthesizer: egm-implementation-readiness, egm-codebase-details, egm-style)*