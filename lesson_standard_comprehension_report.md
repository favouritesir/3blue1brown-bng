# Lesson Production Standard — Comprehension Report

---

## Feature Spec Paraphrase

The document establishes a **master production standard** for building a Bengali-language platform that mirrors the 3Blue1Brown lesson catalog (`3blue1brown.com/lessons/...`) with **100% content fidelity** — every section, text, diagram, quiz, and mathematical formula must be present, unabridged. The platform must **exceed the source site's UX** with modern interactive affordances: a floating table-of-contents drawer, quick chapter stepper in the navbar, preview-card chapter navigation, dual **Watch Mode** (theater player + 5-chapter playlist drawer) and **Read Mode** (full offline KaTeX-rich textbook), plus an interactive canvas lab and quiz system with instant feedback and "show answer" controls.

A strict **audio/textbook segregation** governs content authoring:
- **Speech/Audio Script (TTS)**: 100% pronunciation purity — zero Latin glyphs (`x, y, z`) or dots; all technical terms phonetically transcribed into Bengali (`এক্স অক্ষ`, `ওয়াই অক্ষ`, `আই হ্যাট`, `ডিটারমিন্যান্ট`); em-dashes (`—`) for natural breath pauses.
- **Reading Textbook/Article Notes**: Fluent, pedagogically rich Bengali; standard math notation in KaTeX blocks (`$x, y$`, `$\hat{i}, \hat{j}$`, `$\det(A)$`, matrix environments); no mechanical/Google-Translate output.

**Shared asset discipline**: every lesson consumes a single shared CSS (`../../assets/css/lesson.css`) and JS (`../../assets/js/lesson.js`); figures/diagrams live in per-lesson local directories (`../../assets/figures/la_0X/`) for offline loading; each page embeds a local high-quality dubbed video (`../../media_vault/lesson_0X/...`) alongside a YouTube switcher for both Watch and Read modes.

---

## Implementation Plan Paraphrase

Inferred from the philosophy, segregation rules, and structure rules:

1. **Content Ingestion Pipeline**
   - Scrape/import each 3B1B lesson page (HTML + assets) → parse into structured sections (text, diagrams, quizzes, formulas).
   - Maintain a canonical lesson manifest mapping source sections → platform components.

2. **Dual-Render Authoring System**
   - **Audio Script Generator**: Transform source math notation → phonetic Bengali (rule-based + LLM-assisted); inject em-dash breath marks; validate zero Latin glyphs.
   - **Textbook Renderer**: Convert source math → KaTeX blocks; author fluent Bengali prose around them; enforce no machine-translation artifacts.
   - Both outputs stored as separate artifacts per lesson.

3. **Frontend Architecture**
   - Single-page lesson template consuming shared `lesson.css` / `lesson.js`.
   - **Watch Mode**: `<video>` player (local MP4/WebM + YouTube fallback) + playlist drawer (5-chapter window).
   - **Read Mode**: Scrollable KaTeX-rich article with interactive canvas/quiz widgets.
   - Floating TOC drawer (persistent across modes), chapter stepper in navbar, preview-card nav at page bottom.

4. **Asset Management**
   - Figures: downloaded, versioned, placed under `assets/figures/la_0X/`; referenced by relative path.
   - Dubbed videos: encoded to target quality, placed under `media_vault/lesson_0X/`; manifest tracks duration, codec, sync points.
   - YouTube IDs mapped per lesson for switcher fallback.

5. **Interactive Layer**
   - Canvas Lab: WebGL/Canvas components mirroring 3B1B animations (likely driven by a scene description format).
   - Quiz System: JSON-defined questions with validation logic, "show answer" reveal, localized feedback strings.

6. **Quality Gates**
   - Audio script lint: regex scan for forbidden Latin/dots; phonetic glossary compliance.
   - Textbook lint: KaTeX syntax check; Bengali fluency heuristics (no literal translation patterns).
   - Asset integrity: local file existence, video playability, figure dimensions.
   - Cross-mode parity: every source section rendered in both Watch and Read.

7. **Build/Deploy**
   - Static site generation (or SSR) emitting per-lesson HTML + shared assets.
   - CDN upload for `assets/` and `media_vault/` with cache headers.
   - Manifest JSON for search, navigation, and playlist construction.

---

## Comprehension Findings

### 🔴 Blocker

| # | Finding | Why It Blocks |
|---|---------|---------------|
| B1 | **"3Blue1Brown official website" content model undefined** | The standard mandates "every section, text, diagram, quiz, formula" from `3blue1brown.com/lessons/...` but never defines what those sections *are* (e.g., does each lesson have a fixed schema? Are quizzes per-section or per-lesson? Are diagrams SVG/Canvas/Video?). Without a source content model, ingestion and parity testing are impossible. |
| B2 | **No lesson identification/numbering scheme** | Paths reference `la_0X` and `lesson_0X` but the standard never defines: how many lessons? What is "0X" (zero-padded decimal? hex?); is there a master index? How do chapters map to lessons? The "5-chapter playlist drawer" implies a chapter↔lesson relationship that is nowhere specified. |
| B3 | **Phonetic transcription rules are incomplete** | The table gives examples (`এক্স অক্ষ`, `আই হ্যাট`, `ডিটারমিন্যান্ট`) but no systematic rules: how to handle Greek letters (α, β, γ, θ, λ, μ, σ, π, φ, ω), operators (∇, ∂, ∫, ∑, ∏), sub/superscripts, function names (sin, cos, log, det, tr, span, ker, im, re), arrow notation (→, ↦, ⇒), set symbols (∈, ⊂, ∪, ∩, ∅), logic symbols (∀, ∃, ¬, ∧, ∨). A TTS author cannot achieve "100% pronunciation purity" from examples alone. |
| B4 | **Interactive canvas lab & quiz system — zero spec** | The philosophy lists "interactive canvas lab and quiz system (correct/incorrect feedback and 'show answer' button)" as a required feature, but the document contains **no data model, no component API, no state management rules, no authoring format**. Implementation cannot start without at least a minimal spec. |
| B5 | **Video dubbing pipeline entirely absent** | The standard requires "local high-quality dubbed video" in `media_vault/lesson_0X/` and a YouTube switcher, but says nothing about: source video acquisition (YouTube-dl? official downloads?), alignment method (forced alignment? manual?), TTS engine (Edge? Google? ElevenLabs?), audio post-processing (loudness normalization, noise gate), video container/codec/bitrate, subtitle/caption tracks, or sync verification. This is a major production workstream with zero guidance. |

### 🟡 Major

| # | Finding | Impact |
|---|---------|--------|
| M1 | **"Shared CSS/JS" — no versioning or extension mechanism** | All lessons *must* use `../../assets/css/lesson.css` and `../../assets/js/lesson.js`. If Lesson 3 needs a custom animation or quiz variant, how does it extend without forking? No hook/plugin/API pattern described. |
| M2 | **Figure directory naming (`la_0X`) vs lesson directory (`lesson_0X`) inconsistency** | Figures live under `la_0X`, videos under `lesson_0X`. Is `la` = "linear algebra"? What about other series (calculus, neural nets)? No namespace convention defined. |
| M3 | **KaTeX delimiter strategy unspecified** | Textbook mode requires "KaTeX blocks" — but are delimiters `$$...$$`, `\[...\]`, `$...$`, or a custom wrapper? Inline vs display? No escaping rules for Bengali text containing `$` or `\`. |
| M4 | **Offline-first claim vs YouTube switcher contradiction** | "Read mode = full offline KaTeX-rich textbook" yet every page has a YouTube switcher. If offline is a hard requirement, YouTube cannot be a runtime dependency. Is the switcher only for Watch mode? Not clarified. |
| M5 | **No accessibility (a11y) requirements** | Bengali platform serving educational content — no mention of ARIA labels, keyboard navigation for TOC drawer/stepper, screen-reader math announcements (MathML fallback?), color contrast, reduced-motion for animations. |
| M6 | **Quiz/answer data model missing** | "Show answer" button implies stored answers. Are they client-side (exposed in bundle)? Server-validated? What question types (MCQ, numeric, symbolic, graph)? No schema. |
| M7 | **Playlist drawer "5 chapters" — hardcoded constant?** | Why 5? Is it a UI window size? A curriculum grouping? If lessons > 5, how does pagination work? If < 5, empty slots? |
| M8 | **No i18n/l10n infrastructure** | The standard is Bengali-only today, but "3Blue1Brown Bengali Platform" implies a branded product. No string extraction, locale switching, or RTL/LTR considerations (irrelevant for Bengali but good practice). |

### 🟢 Nit

| # | Finding | Note |
|---|---------|------|
| N1 | **Section numbering uses Bengali numerals (১, ২, ৩) but code paths use Latin** | Minor cognitive friction; not harmful. |
| N2 | **"Floating TOC Drawer" vs "Sidebar TOC Drawer" — mixed terminology** | Line 12: "সাইডবার সূচিপত্র ড্রয়ার (Floating TOC Drawer)". Pick one. |
| N3 | **Em-dash rule: "এম-ড্যাশ (`—`) ব্যবহার করতে হবে" but no keyboard/input guidance** | Authors need to know how to type it (Alt+0151? `---` ligature? Unicode U+2014?). |
| N4 | **No glossary appendix for phonetic mappings** | The examples (`এক দশমিক আট` for `1.8`, `ডিটারমিন্যান্ট` for `determinant`) suggest a glossary should exist as a living document. |
| N5 | **Markdown table in Section 2 uses `<br>` for line breaks** | Works in GitHub/GitLab but not all Markdown renderers; consider multi-line cells or explicit `<br>` note. |

---

*End of Comprehension Report*