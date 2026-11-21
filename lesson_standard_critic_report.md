# EGM Critic Review: LESSON_PRODUCTION_STANDARD.md

**Document Under Review:** `governance/LESSON_PRODUCTION_STANDARD.md`  
**Context Sources:** `zoom_out_report.md` (AGENT_WORKFLOW_GUIDELINES.md review), `comprehension_report.md`  
**Reviewers:** egm-design, egm-structural, egm-style  
**Severity Scale:** 🔴 Blocker | 🟡 Major | 🟢 Nit  

---

## 1. egm-design — Principles, Problem Fit, Trade-offs

### 🔴 Blocker

| # | Finding | Why It Blocks |
|---|---------|---------------|
| D1 | **No explicit linkage to the Dub Studio orchestration framework** | The document governs *lesson production standards* but exists in a system where `AGENT_WORKFLOW_GUIDELINES.md` (reviewed in zoom_out/comprehension) defines a multi-agent pipeline with Script Adapter, Sync Engineer, QA Agent, TTS batching, Demucs separation, EBU R128 normalization, and acoustic delimiter protocols. This standard never references, subordinates to, or aligns with that pipeline. **Result:** Two parallel governance docs that will diverge. |
| D2 | **Audio vs Textbook segregation (Section 2) ignores the TTS engine selection mandate** | Global instructions §1 mandate **context-driven TTS selection**: Edge-TTS for lectures/tutorials/single-speaker; Google AI Studio (`gemini-3.8-flash-tts`) for multi-character drama/high-emotion. Section 2 only says "phonetic Bengali, no Latin letters" — it does not specify *which engine*, *batching protocol*, *delimiter strategy* (`\n\n... ... ...\n\n`), or *voice identity lock*. The Script Adapter sub-agent (from workflow) cannot implement this standard without those decisions. |
| D3 | **SFX preservation & vocal bleed elimination (Global §6, §8) unaddressed** | The standard mentions "local high-quality dubbed video" and "YouTube video switcher" but says nothing about: 2-stem Demucs separation + Wiener filtering + hard gating (assigned to NVIDIA Mistral Large 4 1T per Global §8), EBU R128 loudness normalization (-14 LUFS, -1 dBTP), or zero-bleed dialogue gating. A lesson with background music/SFX will ship with English vocal bleed or crushed dynamics. |
| D4 | **Phonetic acronym safeguard (Global §5) partially implemented but incomplete** | Section 2 correctly requires `এক্স অক্ষ`, `ওয়াই অক্ষ`, `আই হ্যাট`, `ডিটারমিন্যান্ট`. **Missing:** `AI`→`এআই`, `3D`→`থ্রিডি`, `2D`→`টুডি`, `EGM`→`ইজিএম`, `SEO`→`এসইও`, `API`→`এপিআই`, `UI`→`ইউআই`, `ML`→`এমএল`, `z-অক্ষ`→`জেড অক্ষ`, `\hat{k}`→`কে হ্যাট`. Without an exhaustive reference table, Script Adapter output will be inconsistent. |

### 🟡 Major

| # | Finding | Impact |
|---|---------|--------|
| D5 | **Watch/Read mode duality (Section 1.2) lacks sync contract** | Watch Mode = Theater Player + 5-chapter playlist drawer. Read Mode = Full offline KaTeX textbook. The standard does not define: (a) how timestamps from the dubbed video map to scroll positions in Read Mode, (b) whether the TTS batching delimiters (`... ... ...`) serve as sync anchors, (c) what happens when video duration ≠ TTS duration after `atempo` stretching. |
| D6 | **Interactive Canvas Lab & Quiz System (Section 1.2) has no data schema** | "Correct/wrong feedback and 'Show Answer' button" — no specification for: question format (JSON? YAML?), answer validation logic, state persistence (localStorage? server?), analytics events, or accessibility (ARIA). Each lesson will invent its own. |
| D7 | **Floating TOC Drawer & Quick Chapter Stepper — UX decisions without rationale** | Why a *floating button* vs. persistent sidebar? Why *stepper* (`‹ ০১ / ০৫ ›`) vs. dropdown? No trade-off acknowledgment (mobile vs desktop, touch vs keyboard, RTL considerations for Bengali). |
| D8 | **No versioning/rollback strategy for lesson artifacts** | "Shared CSS/JS" (Section 3) implies a single `lesson.css` and `lesson.js` for *all* lessons. A breaking change in Lesson 05 breaks Lessons 01-04. No semantic versioning, no feature flags, no migration path. |

### 🟢 Nit

| # | Finding | Note |
|---|---------|------|
| D9 | **Principle statements lack "Decision Log" traceability** | Per zoom_out_report §7, principles should carry rationale: *Why* shared CSS/JS? (Bundle size? Consistency? Cacheability?) *Why* local figures only? (Offline-first? CDN cost? Version pinning?) Future maintainers cannot evaluate if context changed. |

---

## 2. egm-structural — Structure, Dependencies, Abstractions

### 🔴 Blocker

| # | Finding | Why It Blocks |
|---|---------|---------------|
| S1 | **Missing "Interfaces & Contracts" section** | The document specifies *what* files exist (CSS, JS, figures, media) but not *how* they interoperate: (a) What CSS custom properties does `lesson.css` expose for lessons to consume? (b) What JS modules/events does `lesson.js` export (TOC drawer API, stepper API, Watch/Read toggle, Quiz engine)? (c) What is the figure manifest format (JSON? YAML?) mapping figure IDs to local paths + alt text + KaTeX labels? (d) What is the media vault manifest schema (dubbed video path, YouTube ID, duration, chapters, sync map)? Without contracts, each lesson author implements ad-hoc. |
| S2 | **Circular/ambiguous dependency: Shared assets vs. lesson-local assets** | Section 3: "All lessons use shared CSS (`../../assets/css/lesson.css`) and JS (`../../assets/js/lesson.js`)." Simultaneously: "Each lesson's figures load from its own local directory (`../../assets/figures/la_0X/`)." **Conflict:** If `lesson.css` references figure paths, it couples to lesson-specific structure. If `lesson.js` expects a global figure registry, lesson-local directories break it. The abstraction boundary is undefined. |
| S3 | **Media vault path references a non-existent structure** | `../../media_vault/lesson_0X/...` — but the folder taxonomy from AGENT_WORKFLOW_GUIDELINES.md (comprehension_report §9) defines: `departments/media_production/youtube_channels/`, `departments/learning_paths/stem_mathematics/`, etc. **No `media_vault` exists in the canonical taxonomy.** This will cause 404s at runtime. |
| S4 | **No build/deployment pipeline specification** | The standard assumes static HTML + local assets. But: (a) KaTeX requires font loading — self-hosted or CDN? (b) Shared JS/CSS — bundled per-lesson or served from common origin? (c) Figure optimization (SVG→WebP, retina variants)? (d) Video transcoding (H.264/HEVC/AV1, multiple bitrates for adaptive streaming)? None addressed. |

### 🟡 Major

| # | Finding | Impact |
|---|---------|--------|
| S5 | **Section numbering inconsistency** | Section 1 uses Bengali numerals (১, ২), Section 2 uses Bengali numerals, Section 3 uses Arabic numerals (3). Structural incoherence. |
| S6 | **Watch/Read mode switcher — no state management contract** | How does the user's mode preference persist? `localStorage`? URL hash? Server-side? If Watch Mode loads a 5-chapter playlist drawer, does Read Mode load the same playlist as a linear TOC? No shared state model defined. |
| S7 | **Quiz system — no integration point with `lesson.js`** | Is the quiz engine *inside* `lesson.js` (monolith) or a separate module loaded on demand? If separate, what is the import path? If inside, how does a lesson author add custom question types? |
| S8 | **Figure directory naming (`la_0X`) assumes linear lessons only** | What about: supplemental lessons, appendix lessons, multi-series courses, or non-sequential "labs"? The `la_0X` pattern bakes a false assumption into the structure. |

### 🟢 Nit

| # | Finding | Note |
|---|---------|------|
| S9 | **Table in Section 2 uses HTML `<br>` inside markdown cells** | Works in GitHub rendering but fragile in other markdown processors. Prefer native markdown line breaks or separate rows. |
| S10 | **Relative paths (`../../assets/...`) assume fixed depth** | If lesson nesting changes (e.g., `courses/linear-algebra/lesson_01/index.html` vs `lessons/la_01/index.html`), paths break. Should define a root-relative or asset-manifest-based resolution strategy. |

---

## 3. egm-style — Clarity, Consistency, Actionability, Terminology

### 🔴 Blocker

| # | Finding | Why It Blocks |
|---|---------|---------------|
| Y1 | **"Offline KaTeX সমৃদ্ধ টেক্সটবুক" (Section 1.2) — ambiguous scope** | Does "offline" mean: (a) Service Worker cached, (b) Electron/Tauri desktop app, (c) Static HTML with self-hosted KaTeX fonts, (d) PDF export? Each has radically different implementation. "সমৃদ্ধ" (rich) is subjective — does it include: interactive diagrams, collapsible proofs, annotation layer, search index? |
| Y2 | **"স্থানীয় উচ্চমানের ডাবড ভিডিও" — no quality spec** | "High-quality" is not a spec. Missing: container (MP4/MOV/WebM), codec (H.264/HEVC/AV1/VP9), resolution (1080p/4K), bitrate (CBR/VBR, target Mbps), color space (sRGB/P3/Rec.2020), audio codec (AAC/Opus), audio bitrate, loudness target (EBU R128 -14 LUFS per global instructions). Without this, "switcher" between YouTube and local will have visible/audible quality jumps. |
| Y3 | **Bengali/English terminology mixing without glossary** | Terms used: "Watch মোড", "Read মোড", "KaTeX", "TOC Drawer", "Stepper", "Playlist Drawer", "Canvas Lab", "Sidebar সূচিপত্র". No definitions. A new contributor cannot distinguish product terminology from implementation terminology. |

### 🟡 Major

| # | Finding | Impact |
|---|---------|--------|
| Y4 | **Imperative vs. declarative tone inconsistency** | Section 1: "হতে হবে" (must), "রাখতে হবে" (must keep). Section 2: "নিশ্চিত করতে হবে" (must ensure), "রাখা যাবে না" (cannot keep). Section 3: "ব্যবহার করতে হবে" (must use), "লোড হবে" (will load — passive/future). Mix of requirement, constraint, and implementation prediction. |
| Y5 | **"ফ্লোটিং বাটন চেপে" — colloquial/imprecise** | "চেপে" (press/hold) suggests a long-press gesture, but a TOC drawer typically toggles on click. If it *is* a long-press, say "দীর্ঘ চাপ" (long press). If click, say "ক্লিক করলে" (on click). |
| Y6 | **No cross-references to global instructions or workflow doc** | The document stands alone but operates inside a system with: phonetic safeguard rules (§5 global), TTS batching/delimiter protocol (§9 global), SFX separation pipeline (§8 global), agent roles (workflow doc). Zero references. Reader cannot trace requirements upstream. |
| Y7 | **Acronyms introduced without expansion** | "TOC" (Table of Contents), "KaTeX", "UI/UX" — first use should expand. Especially critical for Bengali-first team members. |

### 🟢 Nit

| # | Finding | Note |
|---|---------|------|
| Y8 | **Markdown table alignment broken in Section 2** | The `|---|---|` separator row has no pipes at edges in source (rendered fine on GitHub but technically invalid). |
| Y9 | **Section 3 bullet list uses hyphens; Section 1.2 uses numbered list** | Pick one convention for "feature lists" vs. "requirement lists". |
| Y10 | **Trailing whitespace in "Watch মোড (থিয়েটার প্লেয়ার + ৫টি অধ্যায়ের প্লেলিস্ট ড্রয়ার) এবং Read মোড (পূর্ণাঙ্গ অফলাইন KaTeX সমৃদ্ধ টেক্সটবুক)।"** | Minor but visible in diff. |

---

## Consolidated Severity Summary

| Reviewer | 🔴 Blocker | 🟡 Major | 🟢 Nit | Total |
|----------|------------|----------|--------|-------|
| egm-design | 4 | 4 | 1 | 9 |
| egm-structural | 4 | 4 | 2 | 10 |
| egm-style | 3 | 4 | 3 | 10 |
| **TOTAL** | **11** | **12** | **6** | **29** |

---

## Top 5 Must-Fix Before Implementation

1. **Add "Interfaces & Contracts" section** defining: CSS custom properties, JS module exports, figure manifest schema, media vault manifest schema, quiz data schema, sync map schema (timestamps ↔ scroll positions ↔ TTS delimiters).
2. **Align media paths with canonical taxonomy** (`departments/...`) or formally extend the taxonomy with a `media_vault` root — documented in *both* this standard and the workflow doc.
3. **Specify TTS engine selection, batching, delimiters, voice lock, loudness, SFX separation** — either inline or by normative reference to Global Instructions §1, §5, §6, §8, §9 with explicit "Lesson Production adopts Global Instructions §X.Y verbatim."
4. **Define "Offline KaTeX Textbook" concretely**: Service Worker strategy, font self-hosting, interactive feature matrix, export formats.
5. **Version the shared assets**: `lesson.v1.css`, `lesson.v1.js` with semver; lessons declare `requires: "lesson@^1.0"` in front-matter; build system resolves.

---

## Recommendation

**Do not ship lessons from this standard alone.** It is a *feature wishlist* masquerading as a production standard. The 11 Blocker findings represent architectural gaps that will cause: runtime 404s (media vault), vocal bleed in dubbed audio (missing SFX pipeline), inconsistent phonetic output (incomplete safeguard), broken shared assets (no versioning), and untestable quiz/canvas labs (no contracts).

**Path forward:**
1. Create a **Lesson Production Interface Specification** (contracts, schemas, APIs) as a sister document.
2. Add **Normative References** section linking each requirement to Global Instructions / Workflow Doc sections.
3. Run a **structural refactor** of the asset taxonomy to unify `media_vault` with `departments/`.
4. Conduct a **phonetic terminology audit** — publish the exhaustive acronym/symbol → Bengali mapping as a machine-readable JSON consumed by Script Adapter.
5. Prototype **one lesson end-to-end** (Lesson 01) using this standard + workflow pipeline; document every deviation as a spec amendment.

---

*Report generated by EGM Critic Review synthesis (egm-design, egm-structural, egm-style) incorporating zoom_out_report.md and comprehension_report.md context.*