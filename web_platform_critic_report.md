# EGM Critic Review: WEB_PLATFORM_AGENT_BOUNDARIES.md
**Target Document:** `governance/WEB_PLATFORM_AGENT_BOUNDARIES.md`  
**Review Date:** 2026-11-05  
**Context:** Zoom-Out Report (`zoom_out_report.md`) + Comprehension Report (`comprehension_report.md`)  
**Reviewers:** egm-design, egm-structural, egm-style  

---

## 1. egm-design — Invariant Design, Problem Fit, Trade-offs
*Are the architectural invariants well-designed? Do they solve the right problems? Are trade-offs acknowledged?*

### 🔴 Blocker

| # | Finding | Evidence / Reasoning |
|---|---------|---------------------|
| D1 | **No invariants for audio/video synchronization** | The document declares "NO OVERLAPPING AUDIO / VIDEO" (Rule 6) and "SOLE AUDIO AUTHORITY" but provides **zero invariants** for *how* this is enforced. No state machine, no event contracts, no race-condition handling. The Comprehension Report (§9, Global Instruction §6) mandates deterministic slicing with acoustic delimiters (`\n\n... ... ...\n\n`), zero-drift alignment, and EBU R128 loudness normalization — none of which appear here. Without synchronization invariants, agents will implement conflicting pause/resume logic. |
| D2 | **Agent boundaries ignore cross-cutting concerns** | The boundary table (Section 2) partitions by *directory*, but critical concerns — **audio generation**, **manifest management**, **global UI components** (`#smartAudioPill`, `#mainVideo`, narration engine) — are shared. The Audio Synthesis Fleet owns `assets/audio/<course>/<lesson>/` but the Lead Agent owns `narration_engine.js` which *consumes* those manifests. Who owns the manifest schema? Who version-bumps `manifest.js` when audio format changes? No ownership, no contract. |
| D3 | **Hardcoded voice/engine decisions without rationale** | Rule 10 mandates `bn-BD-PradeepNeural` (Edge-TTS) for all teacher narration. Global Instructions §1 explicitly requires **context-driven TTS selection**: Edge-TTS for lectures/tutorials, Google AI Studio (`gemini-3.8-flash-tts`) for drama/multi-character/high-emotion content. This document bakes a single-engine choice into architecture without acknowledging the trade-off (simplicity vs. expressive range). |

### 🟡 Major

| # | Finding | Evidence / Reasoning |
|---|---------|---------------------|
| D4 | **No offline-first invariants despite `file://` requirement** | Rule 9 mandates "100% offline `file://` support" via `manifest.js` preloading. But no invariants define: cache-busting strategy, manifest versioning, fallback when audio files missing, or how agents coordinate offline asset validation. The Comprehension Report (§9, Finding 9) notes temp cleanup is aspirational with no mechanism — same gap here for offline asset integrity. |
| D5 | **Booking chip wrap rule (Rule 12) is a UI invariant without component ownership** | "NO HORIZONTAL SCROLLBAR ON BOOKMARKS" mandates `flex-wrap: wrap` or CSS Grid. But which agent owns the bookmark component? Lead Agent owns `lesson.css` — but course fleets own their lesson HTML. If a fleet adds a bookmark variant, who enforces the wrap invariant? No lint rule, no shared component, no design token. |
| D6 | **Default-to-local-video rule (Rule 13) lacks fallback/telemetry** | Hero containers must initialize with `#heroLocalBox` visible, `#heroYtBox` hidden. No invariant for: local video missing/corrupt, network detection for YouTube fallback, user preference persistence, or analytics on which source users actually watch. |

### 🟢 Nit

| # | Finding | Evidence / Reasoning |
|---|---------|---------------------|
| D7 | **Rule numbering mixes semantic categories** | Rules 1–14 mix: audio architecture (1, 6, 7, 10, 11), UI constraints (12, 13), agent governance (2–5, 8, 9, 14). A design document should separate *system invariants* from *agent governance* from *UI/UX standards*. |

---

## 2. egm-structural — Structure, Dependencies, Abstraction Consistency
*Sound structure? Missing sections, circular dependencies, inconsistent abstractions?*

### 🔴 Blocker

| # | Finding | Evidence / Reasoning |
|---|---------|---------------------|
| S1 | **No interface contracts between agents** | The boundary table assigns file *ownership* but defines **zero interfaces**: no manifest schema (JSON Schema / TypeScript types), no event bus specification (how narration engine signals video pause), no audio asset delivery protocol (does Audio Fleet write directly to `assets/audio/`? via PR? via MCP tool?). The Zoom-Out Report (Finding 4) and Comprehension Report (Finding 2, 3) both flag this as a blocker for the parent framework — it applies equally here. |
| S2 | **Circular dependency: Lead Agent ↔ Course Fleets via global assets** | Lead Agent owns `narration_engine.js` (consumes manifests) and `curriculum_index.json` (indexes all courses). Course Fleets own lesson HTML and audio folders. Audio Fleet writes manifests consumed by Lead Agent's engine. **No dependency direction is declared.** If Linear Algebra Fleet adds `lesson_06.html` with new audio sections, who updates `curriculum_index.json`? Lead Agent? Fleet? Audio Fleet? No protocol. |
| S3 | **Missing section: Agent Communication & Coordination Protocol** | The document is titled "MULTI-AGENT GOVERNANCE" but contains **no governance mechanics**: no task queue, no handoff format, no escalation path, no review gates. Section 2 is a static territory map, not a governance framework. |

### 🟡 Major

| # | Finding | Evidence / Reasoning |
|---|---------|---------------------|
| S4 | **Inconsistent abstraction levels in boundary table** | Row 1 (Lead Agent) lists 6 specific files. Rows 2–7 (Course Fleets) list directory patterns. Row 8 (Audio Fleet) lists a parametric path template. The abstraction level jumps from *concrete file list* → *directory scope* → *path template*. This makes automated boundary validation impossible. |
| S5 | **No versioning / migration strategy for manifests** | Rule 9 references `manifest.js` and `manifest.json` as the contract between Audio Fleet and Narration Engine. No version field, no backward-compatibility policy, no migration tooling. When Audio Fleet adds a new field (e.g., `loudnessNormalized: true`), does Narration Engine break? |
| S6 | **Course fleet boundaries are directory-based, not feature-based** | Fleets are assigned by *course directory* (Linear Algebra, Calculus, etc.). But shared components — narration engine, bookmark UI, video player, curriculum index — cut across all courses. Directory-based boundaries create **implicit coupling** through shared globals with no ownership model. |
| S7 | **Missing: Asset pipeline integration** | Audio Fleet generates `sec_*.mp3`, `manifest.json`, `manifest.js`. No specification of: naming convention for `sec_*` (section index? timestamp?), audio encoding parameters (bitrate, sample rate, EBU R128 compliance), manifest.js module format (ESM? UMD? global var?), or how Lead Agent's build/validation pipeline consumes these. |

### 🟢 Nit

| # | Finding | Evidence / Reasoning |
|---|---------|---------------------|
| S8 | **Document structure lacks standard governance sections** | Missing: Change Log, Review Cadence, Exception Process, Deprecation Policy, Glossary. The Zoom-Out Report (Recommendation 5) recommends a "Decision Log" appendix — absent here. |
| S9 | **Table format limits extensibility** | Markdown table cannot express: conditional boundaries (e.g., "Audio Fleet owns X *unless* course uses Google AI Studio TTS"), temporal boundaries (e.g., "Fleet owns lesson_02–05 *after* Lead Agent approves lesson_01 pattern"), or tooling enforcement (ESLint rules, pre-commit hooks). |

---

## 3. egm-style — Clarity, Consistency, Actionability, Terminology
*Clear, consistent, actionable? Terminology precise?*

### 🔴 Blocker

| # | Finding | Evidence / Reasoning |
|---|---------|---------------------|
| Y1 | **"STRICT BOUNDARY (DO NOT TOUCH)" column is unactionable** | The column header uses all-caps imperative but the cells contain **prose restrictions** ("MUST NOT touch...", "Confined strictly to..."), not machine-checkable rules. No file globs, no AST patterns, no CODEOWNERS syntax. An agent cannot programmatically verify compliance. |
| Y2 | **Terminology drift: "Fleet" vs "Agent" vs "Subagent"** | Title: "MULTI-AGENT GOVERNANCE". Table: "Agent / Subagent ID" column. Rows: "Linear Algebra **Fleet**", "Calculus **Fleet**", "Audio Synthesis **Fleet**". Lead row: "Lead Agent (Antigravity)". Three different terms for the same concept. Comprehension Report (Finding 18) notes the parent framework has the same issue. |

### 🟡 Major

| # | Finding | Evidence / Reasoning |
|---|---------|---------------------|
| Y3 | **Rule language mixes constraint types without distinction** | Rules 1, 6, 7, 12, 13 are **runtime invariants** (must hold during execution). Rules 2–5, 8, 9, 10, 11, 14 are **governance constraints** (who may edit what). Rules 10, 11 are **implementation decisions** (voice choice, manifest format). Mixing them in one numbered list obscures which are testable, which are enforceable, which are negotiable. |
| Y4 | **Ambiguous references: "Antigravity", "Smart Teacher Narration Engine"** | Lead Agent labeled "(Antigravity)" — is this a model name? A codename? A tool? Rule 11 references "Smart Teacher Narration Engine" as a proper noun but it's never defined. Rule 7 says narration engine is `narration_engine.js` — is "Smart Teacher Narration Engine" the same thing? The UI element names (`#smartAudioPill`, `#mainVideo`, `#heroLocalBox`, `#heroYtBox`) appear without a UI component inventory. |
| Y5 | **Bengali/English terminology inconsistency** | Rule 10: `bn-BD-PradeepNeural` (technical). Rule 11: "🎙️ শিক্ষকের কণ্ঠে শুনুন" (Bengali UI label). Rule 13: "▶ অরিজিনাল ভিডিও" (Bengali button label). No glossary mapping UI string IDs → Bengali text → English meaning. Comprehension Report (Finding 14) flags mixed-language headers in parent doc — same issue here in UI strings. |
| Y6 | **No actionable acceptance criteria for any rule** | "NO HORIZONTAL SCROLLBAR ON BOOKMARKS" — how does an agent verify? Visual regression test? CSS lint rule? Manual QA? "TEACHER NARRATION AUDIO IS MANDATORY" — mandatory for *every* lesson? What about intro/outro lessons with no narration? No criteria. |

### 🟢 Nit

| # | Finding | Evidence / Reasoning |
|---|---------|---------------------|
| Y7 | **Date format inconsistency** | Header: "Date: 2026-11-05" (ISO). No timezone. No "Last Updated" vs "Created" distinction. |
| Y8 | **Emoji usage inconsistent** | Rule 11: "🎙️", Rule 13: "▶". Rule 1, 6, 7, 12: no emoji. Either standardize as visual anchors for all rules or remove. |
| Y9 | **Section 1 title claims "ABSOLUTE PERMANENT ARCHITECTURAL RULES" but Section 2 is agent governance** | Two different rule categories under one "ABSOLUTE" banner. Dilutes the meaning of "absolute." |

---

## Consolidated Severity Summary

| Reviewer | 🔴 Blocker | 🟡 Major | 🟢 Nit | Total |
|----------|------------|----------|--------|-------|
| **egm-design** | 3 | 3 | 1 | 7 |
| **egm-structural** | 3 | 4 | 2 | 9 |
| **egm-style** | 2 | 4 | 3 | 9 |
| **TOTAL** | **8** | **11** | **6** | **25** |

---

## Cross-Reviewer Synthesis: Root Causes

| Root Cause | Manifestations |
|------------|----------------|
| **No interface-first design** | S1 (no contracts), S2 (circular deps), D2 (shared ownership), Y1 (unactionable boundaries) |
| **Governance ≠ Architecture conflation** | D7 (mixed rule types), S3 (missing coordination protocol), Y3 (constraint mixing) |
| **Terminology & abstraction drift** | Y2 (Fleet/Agent/Subagent), S4 (inconsistent abstraction levels), Y4 (undefined proper nouns) |
| **Offline/Determinism requirements unmet** | D1 (sync invariants), D4 (offline invariants), S5 (manifest versioning) |
| **Parent framework gaps inherited** | All D1/D2/D3 trace to Global Instructions §1, §6, §9; S1/S7 trace to Comprehension Findings 2, 3, 4, 5, 8, 9 |

---

## Recommendations (Priority Order)

1. **🔴 Define Interface Contracts First** — Before any agent writes code, publish: Manifest JSON Schema (with version), Narration Engine ↔ Video Player event bus (TypeScript types), Audio Fleet delivery protocol (file naming, encoding, manifest.js module format).
2. **🔴 Resolve Circular Dependency** — Declare explicit dependency direction: Course Fleets → Lead Agent (via PR to `curriculum_index.json`), Audio Fleet → Lead Agent (manifest schema version bump), Lead Agent → Course Fleets (read-only consumption of lesson HTML).
3. **🔴 Split Document** — Separate: (a) *System Invariants* (runtime rules with testable criteria), (b) *Agent Governance Charter* (territories, escalation, review gates), (c) *UI/UX Standards* (component inventory, string glossary, CSS tokens).
4. **🟡 Standardize Terminology** — Pick one: "Agent" or "Fleet" or "Subagent". Define in glossary. Apply consistently.
5. **🟡 Make Boundaries Machine-Checkable** — Replace prose with: CODEOWNERS patterns, ESLint `no-restricted-paths` rules, pre-commit hooks for manifest schema validation.
6. **🟡 Align with Global Instructions** — Explicitly reference Master Dubbing Skill (§1 TTS selection, §6 sync protocol, §8 Demucs separation, §9 delimiter standard) and declare: *subordinate*, *supersedes*, or *extends* for each relevant rule.
7. **🟢 Add Governance Metadata** — Version, owner, review cadence, change log, exception process.

---

## Verdict

**Do not authorize agent work from this document in its current state.** The 8 Blocker findings represent fundamental architectural gaps (no synchronization invariants, no interface contracts, circular dependencies, unactionable boundaries) that will cause agent collisions, runtime bugs, and unmaintainable coupling. Complete Recommendations 1–3 before spawning course fleets.

---
*Report generated by EGM Critic Review Synthesizer*