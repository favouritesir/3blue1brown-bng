# EGM Intermediate Zoom-Out Review: LESSON_PRODUCTION_STANDARD.md

## Paraphrase of the Document (Post-Review Synthesis)

The document establishes a master production standard for a Bengali 3Blue1Brown platform with three pillars: (1) 100% content fidelity to 3B1B lessons + premium UI/UX (floating TOC drawer, chapter stepper, preview navigation, dual Watch/Read modes, interactive canvas labs/quizzes); (2) strict audio/textbook segregation — TTS scripts use phonetic Bengali only (zero Latin glyphs, em-dash pauses) while textbooks use natural pedagogical Bengali with KaTeX math; (3) shared asset discipline — single CSS/JS across lessons, per-lesson figure directories, local dubbed videos with YouTube switcher in both modes.

Three prior reviews have exposed deep structural gaps:
- **Zoom-Out (Stage 5)**: 3 Blockers + 4 Majors — missing tech stack, content ingestion, audio pipeline, Watch/Read architecture, quiz data model, video strategy, a11y, i18n.
- **Comprehension (Stage 6)**: 5 Blockers + 8 Majors — undefined 3B1B content model, no lesson numbering scheme, incomplete phonetic rules, zero canvas/quiz spec, absent dubbing pipeline, shared asset versioning, KaTeX delimiters, offline/YouTube contradiction.
- **Critic (Stage 7)**: 11 Blockers + 12 Majors — no linkage to Dub Studio orchestration framework, ignores global TTS engine mandate, SFX preservation unaddressed, phonetic safeguard incomplete, missing interfaces/contracts, circular shared/local asset dependency, media vault path mismatch with canonical taxonomy, no build pipeline, ambiguous "offline" scope, no video quality spec, terminology without glossary.

---

## What Has Been Added / Mitigated Across Reviews

### ✅ Mitigated: Explicit Identification of the "Requirements vs. Decisions" Gap
All three reviews independently converge on the same core finding: **this document records desired outcomes without the structural decisions that make implementation coherent**. The Zoom-Out review framed it as "requirements sketch"; Comprehension identified specific undefined schemas (content model, lesson numbering, phonetic rules); Critic traced each gap to the Dub Studio orchestration framework (Global Instructions, Agent Workflow). The synthesis confirms this is not a review artifact — it is a fundamental property of the document.

### ✅ Added: Cross-Document Governance Misalignment
Critic Review (D1) revealed a **critical governance fracture**: `LESSON_PRODUCTION_STANDARD.md` and `AGENT_WORKFLOW_GUIDELINES.md` operate as parallel, unlinked authorities. The workflow doc mandates:
- Context-driven TTS selection (Edge-TTS vs. Google AI Studio `gemini-3.8-flash-tts`)
- Batching protocol (3–5 min master blocks, `\n\n... ... ...\n\n` delimiters)
- Voice identity lock (Steve=`Orus`, Maggie=`Aoede`)
- SFX preservation via Demucs 2-stem + Wiener filtering + hard gating (NVIDIA Mistral Large 4 1T)
- EBU R128 normalization (-14 LUFS, -1 dBTP)

**None of this appears in the Lesson Standard.** The standard's "phonetic Bengali, no Latin letters" (Section 2) is necessary but insufficient — it omits the *entire production chain* the workflow assumes.

### ✅ Added: Canonical Taxonomy Violation
Critic Review (S3) identified that `../../media_vault/lesson_0X/...` **does not exist** in the canonical folder taxonomy defined in the workflow doc (`departments/media_production/youtube_channels/`, `departments/learning_paths/stem_mathematics/`, etc.). This is a runtime 404 waiting to happen — not a style issue, a structural incompatibility between two governance documents.

### ✅ Added: Interface/Contract Vacuum
Critic Review (S1) formalized what Zoom-Out implied: the document specifies *file existence* but not *interoperability contracts*. Missing schemas:
- CSS custom properties exposed by `lesson.css`
- JS module exports from `lesson.js` (TOC API, stepper API, Watch/Read toggle, Quiz engine)
- Figure manifest (ID → path + alt + KaTeX label)
- Media vault manifest (dubbed path, YT ID, duration, chapters, sync map)
- Quiz data schema
- Sync map schema (video timestamps ↔ scroll positions ↔ TTS delimiters)

Without these, every lesson author implements ad-hoc — the "shared CSS/JS" mandate becomes a shared liability.

### ✅ Added: Phonetic Safeguard Incompleteness Quantified
Critic Review (D4) enumerated **14 specific missing mappings** from Global Instructions §5 that the standard's examples (`এক্স অক্ষ`, `আই হ্যাট`, `ডিটারমিন্যান্ট`) do not cover:
`AI`→`এআই`, `3D`→`থ্রিডি`, `2D`→`টুডি`, `EGM`→`ইজিএম`, `SEO`→`এসইও`, `API`→`এপিআই`, `UI`→`ইউআই`, `ML`→`এমএল`, `z-অক্ষ`→`জেড অক্ষ`, `\hat{k}`→`কে হ্যাট`, plus Greek letters, operators, sub/superscripts, function names, arrow/set/logic symbols (Comprehension B3). The Script Adapter sub-agent cannot implement "100% pronunciation purity" from examples alone.

### ✅ Added: "Offline" Ambiguity Made Concrete
Critic Review (Y1) decomposed "পূর্ণাঙ্গ অফলাইন KaTeX সমৃद्ध টেক্সটবুক" into four mutually exclusive implementations: (a) Service Worker cached, (b) Electron/Tauri desktop app, (c) Static HTML with self-hosted KaTeX fonts, (d) PDF export. Each has radically different architecture. "সমৃদ্ধ" (rich) further expands to: interactive diagrams, collapsible proofs, annotation layer, search index — all unspecified.

---

## New Risks Emerging from Synthesis

### 🔴 Blocker: **Governance Fork Risk — Two Sources of Truth**
The Dub Studio system now has **two master governance documents** that contradict on asset paths, TTS pipeline, SFX handling, and agent responsibilities. Subagents receiving only one document will implement incompatible architectures.
- *Likelihood*: **Certain** — the documents exist in the same repo, reviewed in the same EGM cycle, with zero cross-references.
- *Severity*: **Blocker** — any lesson produced will satisfy one standard and violate the other.
- *Mitigation*: Immediate **Governance Unification** — either (a) merge into single `PRODUCTION_GOVERNANCE.md` with normative references, or (b) add explicit "Normative References" section in *both* documents mapping each requirement to its authoritative source.

### 🔴 Blocker: **Shared Asset Versioning Time Bomb**
Section 3 mandates `../../assets/css/lesson.css` and `../../assets/js/lesson.js` for *all* lessons with **no versioning, no extension mechanism, no migration path**. Critic (D8) and Comprehension (M1) both flag this. Zoom-Out (Finding 7) noted it conflicts with modern bundlers.
- *New synthesis risk*: The first lesson to need a custom animation (e.g., Lesson 03 canvas lab) **must fork** or **breaks all prior lessons**. There is no hook/plugin/API pattern. This is not "technical debt" — it is a **designed-in architectural failure mode**.
- *Mitigation*: Semantic versioning (`lesson.v1.css`, `lesson@^1.0` in lesson front-matter) + build-time resolution + explicit extension API in `lesson.js`.

### 🔴 Blocker: **Sync Contract Vacuum Between Watch/Read Modes**
Critic (D5) identified that the dual-mode UX has **no synchronization contract**:
- How do dubbed video timestamps map to Read Mode scroll positions?
- Do TTS batching delimiters (`\n\n... ... ...\n\n`) serve as sync anchors?
- What happens when `atempo` stretching (≤1.25×) makes TTS duration ≠ video duration?
- Does the 5-chapter playlist drawer persist state across mode switches?

The standard treats Watch/Read as independent features; the workflow assumes they are **temporally bound** via the acoustic delimiter protocol. This disconnect will produce **cumulative drift** — users switching modes mid-lesson lose their place.

### 🟡 Major: **Quiz/Canvas Lab — From "Feature" to "Unspecified Platform"**
All three reviews flag the quiz/canvas system as zero-spec. Synthesis reveals a deeper risk: **these are not lesson features — they are platform infrastructure**. Each lesson's quiz needs: question schema (MCQ? numeric? symbolic? graph?), validation logic (client/server?), state persistence (localStorage? IndexedDB? server?), analytics events, ARIA accessibility. Each canvas lab needs: rendering library (Canvas API? P5.js? Three.js?), scene description format, state serialization (save/resume drawings?), keyboard/screen-reader access.
- *Risk*: Building Lesson 01 without a **platform-level Interactive Component Specification** guarantees N custom implementations for N lessons.
- *Mitigation*: `INTERACTIVE_COMPONENT_SPEC.md` as a prerequisite gate before Lesson 01 authoring.

### 🟡 Major: **Video Quality Spec Absence = Perceptible Quality Jumps**
Critic (Y2): "High-quality" is not a spec. Missing: container, codec, resolution, bitrate, color space, audio codec/bitrate, loudness target (EBU R128 -14 LUFS per global §6). The YouTube switcher will have **visible/audible quality jumps** between local and YT streams — defeating the "premium UX" promise.
- *Mitigation*: `VIDEO_DELIVERY_STRATEGY.md` with encoding ladder, CDN, adaptive streaming, and **mandatory loudness normalization** matching the dubbing pipeline.

### 🟡 Major: **Accessibility Retrofit Cost Compounding**
Zero a11y requirements across all three reviews. Bengali educational platform serving diverse learners — no ARIA labels for TOC drawer/stepper, no keyboard navigation for video player/canvas labs, no MathML fallback for KaTeX, no color contrast/reduced-motion standards, no captions for dubbed videos (Bengali + English?).
- *Synthesis risk*: Retrofitting a11y after N lessons = **N× cost**. Baking it into component library from Day 1 = 1× cost.
- *Mitigation*: `ACCESSIBILITY_REQUIREMENTS.md` as companion to `INTERACTIVE_COMPONENT_SPEC.md`.

### 🟡 Major: **Internationalization Architecture Debt**
Comprehension (M8) and Zoom-Out both flag: hardcoded Bengali strings, no translation keys, no locale switching, no font loading strategy for Bengali (Noto Sans Bengali? Custom variable font?).
- *Synthesis risk*: "3Blue1Brown Bengali Platform" implies a branded product line. Adding Hindi/Tamil/English later requires **full rewrite** of every lesson HTML/JS.
- *Mitigation*: i18n infrastructure (string extraction, locale bundles, font strategy) defined *before* Lesson 01 template.

---

## High-Level Architecture: Verified or Fundamentally Incomplete?

### Verdict: **FUNDAMENTALLY INCOMPLETE**

The document **cannot serve as an implementation standard**. It is a **feature wishlist with structural contradictions**. The 11 Blocker findings from Critic Review alone represent architectural gaps that will cause:

| Failure Mode | Root Cause | Evidence |
|--------------|------------|----------|
| Runtime 404s | `media_vault` path not in canonical taxonomy | Critic S3 |
| Vocal bleed in dubbed audio | SFX pipeline (Demucs + Wiener + gating) unreferenced | Critic D3, Global §8 |
| Inconsistent phonetic output | 14 missing acronym/symbol mappings | Critic D4, Global §5 |
| Broken shared assets | No versioning/extension mechanism | Critic D8, Comp M1, ZO 7 |
| Untestable quiz/canvas labs | No contracts/schemas | Critic S1/D6, Comp B4/M6 |
| Watch/Read sync drift | No sync contract, delimiter protocol ignored | Critic D5, Global §9 |
| Legal exposure | No copyright/licensing strategy for 3B1B content | ZO 2 |
| Video delivery failure at scale | No hosting/encoding/CDN/cost model | ZO 8 |

### What Would Make It "Verified"

The architecture becomes verifiable only when **all five companion specifications exist and are ratified**:

| Spec | Purpose | Blockers It Resolves |
|------|---------|---------------------|
| `TECH_STACK_DECISIONS.md` | Framework, build, deployment, state, component model | ZO 1, Critic S4 |
| `CONTENT_INGESTION_PIPELINE.md` | 3B1B source model, schema, validation, sync, legal | ZO 2, Comp B1/B2 |
| `AUDIO_PRODUCTION_SPEC.md` | TTS engine, voice map, batching, delimiters, post-processing, QA | ZO 3, Critic D2, Global §1/§9 |
| `VIDEO_DELIVERY_STRATEGY.md` | Hosting, encoding, CDN, adaptive, offline, legal | ZO 8, Critic Y2, S3 |
| `WATCH_READ_ARCHITECTURE.md` | Routing, state sharing, mode switching, URL, sync contract | ZO 4, Critic D5 |
| `INTERACTIVE_COMPONENT_SPEC.md` | Quiz schema, canvas API, progress, a11y | ZO 5, Critic D6/S7, Comp B4/M6 |
| `ACCESSIBILITY_REQUIREMENTS.md` | WCAG target, component checklist, testing | ZO 9, Critic (implied) |
| `INTERFACES_CONTRACTS.md` | CSS props, JS exports, figure/media/quiz/sync schemas | Critic S1/S2 |

**Plus**: Normative References section in *both* Lesson Standard and Workflow Doc linking each requirement to its authoritative source.

---

## Recommendations (Synthesis-Ordered)

### 🔴 Immediate (Governance Unification — Week 0)
1. **Add "Normative References" to `LESSON_PRODUCTION_STANDARD.md`** — Map each section to Global Instructions / Workflow Doc sections (e.g., "Section 2 adopts Global Instructions §1, §5, §6, §8, §9 verbatim").
2. **Add "Normative References" to `AGENT_WORKFLOW_GUIDELINES.md`** — Map each pipeline stage to Lesson Standard sections.
3. **Resolve `media_vault` vs. `departments/` taxonomy** — Either extend canonical taxonomy with documented `media_vault` root, or rewrite Lesson Standard paths to match `departments/media_production/...`.

### 🔴 Prerequisite Gates (Before Lesson 01 — Week 1)
4. **Ratify `TECH_STACK_DECISIONS.md`** — Framework, bundler, deployment, state, component model.
5. **Ratify `INTERFACES_CONTRACTS.md`** — CSS props, JS exports, figure/media/quiz/sync schemas.
6. **Ratify `AUDIO_PRODUCTION_SPEC.md`** — TTS engine, voice map, batching, delimiters, loudness, SFX separation.
7. **Publish exhaustive Phonetic Mapping JSON** — Machine-readable acronym/symbol → Bengali table for Script Adapter.

### 🟡 Parallel Tracks (Week 1–2)
8. **`CONTENT_INGESTION_PIPELINE.md`** — 3B1B content model, lesson manifest, validation, sync cadence.
9. **`VIDEO_DELIVERY_STRATEGY.md`** — Encoding ladder, CDN, adaptive streaming, offline SW strategy.
10. **`WATCH_READ_ARCHITECTURE.md`** — Routing, state sharing, sync contract (timestamps ↔ scroll ↔ delimiters).
11. **`INTERACTIVE_COMPONENT_SPEC.md`** — Quiz schema, canvas lab API, progress, a11y.
12. **`ACCESSIBILITY_REQUIREMENTS.md`** — WCAG AA target, component checklist, test protocol.

### 🟢 Polish (Week 2+)
13. Add document metadata (version, date, authors, changelog, related docs).
14. Fix terminology consistency (Floating TOC vs Sidebar TOC, imperative tone, acronym expansions).
15. Prototype Lesson 01 end-to-end using *all* ratified specs; document every deviation as spec amendment.

---

## Final Verdict

**This document remains a requirements sketch.** The three reviews have not "improved" it — they have **excavated its foundational incompleteness**. Each review layer revealed deeper structural fractures: Zoom-Out found missing decisions; Comprehension found undefined schemas; Critic found cross-governance contradictions and contract vacuums.

**Do not authorize lesson production from this standard alone.** The path forward is not "fix the document" — it is **ratify the eight companion specifications** listed above, then **rewrite this standard as a thin conformance layer** that normatively references them.

**Next Step**: Run `egm-draft` to produce `ARCHITECTURAL_DECISIONS.md` (ratified tech stack + interfaces + contracts) and `PRODUCTION_GOVERNANCE.md` (unified Lesson Standard + Workflow Doc with normative references). Only after board ratification of those artifacts should Lesson 01 prototyping begin.

---
*Report generated by EGM Intermediate Zoom-Out Reviewer (egm-zoom-out) synthesizing: zoom_out_report.md (Stage 5), comprehension_report.md (Stage 6), critic_report.md (Stage 7).*