# EGM Zoom-Out Review: WEB_PLATFORM_AGENT_BOUNDARIES.md

**Document:** `governance/WEB_PLATFORM_AGENT_BOUNDARIES.md`  
**Reviewer:** EGM Zoom-Out Reviewer (egm-zoom-out)  
**Date:** 2026-11-05  
**Protocol:** Zoom-Out Standard (Purpose → Scope → Audience → Structure → Gaps → Risks → Traceability)

---

## Paraphrase

This document establishes the governance constitution for a 3Blue1Brown Bengali web platform. It codifies **five absolute architectural invariants** (no dubbed hero audio bar, no overlapping audio/video, mandatory teacher narration engine, no horizontal scrollbar on bookmarks, default to local Bengali video) and **eight strict agent territory assignments** with zero-collision file boundaries across course fleets (Linear Algebra, Calculus, Differential Equations, Lockdown Math, Neural Networks, Probability) plus an Audio Synthesis Fleet and a Lead Agent. The intent is to prevent agent conflicts, enforce UX consistency, and enable parallel development across a multi-course mathematics platform.

---

## Findings

### 1. Purpose Clarity
**🟢 Nit** — Purpose is immediately clear from the title and Section 1. The document solves a real coordination problem: preventing 8+ agent fleets from clobbering each other's files while enforcing non-negotiable UX rules. No ambiguity about *what* this governs.

### 2. Scope Boundaries
**🟡 Major** — Boundaries are explicit *for file paths* but silent on:
- **Runtime behavior contracts**: What constitutes "teacher narration playing" vs "video playing"? No state machine or event bus spec.
- **Cross-fleet shared components**: `lesson.css` / `lesson.js` are owned by Lead Agent but *used* by all fleets — no extension/override protocol defined.
- **Audio Synthesis Fleet interface**: Generates `manifest.json` + `manifest.js` but no schema, naming convention (`sec_*.mp3` is vague), or validation criteria.
- **Deployment/hosting**: `file://` offline support mentioned but no build, bundling, or CI scope.
- **Versioning/rollback**: "Permanent" rules but no mechanism to evolve them (RFC process? ADR log?).

**What's explicitly out of scope:** Content authoring (scripts, pedagogy), video production, TTS engine selection beyond `bn-BD-PradeepNeural`, analytics, accessibility audit, i18n beyond Bengali.

### 3. Audience Fit
**🟡 Major** — Detail level assumes readers already know:
- The exact directory tree (`departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/...`)
- What `narration_engine.js` API looks like (events, methods, karaoke data format)
- How `manifest.js` / `manifest.json` differ and when each loads
- The HTML structure of `#smartAudioPill`, `#heroLocalBox`, `#heroYtBox`, bookmark chips

**Missing for onboarding:** A glossary, a repository tree diagram, or links to the component specs. New agent instances would need a separate "platform orientation" document.

### 4. Structural Coherence
**🟢 Nit** — Two clean sections: invariants → assignments. Table format for assignments is scannable. Rules are actionable (CSS snippets, file paths, forbidden patterns). Flow is logical.

**Minor friction:** Section 1 mixes UX rules (audio bar, scrollbar) with technical mandates (manifest location, voice ID). A sub-section split (UX Invariants vs Technical Invariants) would improve reference speed.

### 5. Missing Critical Elements (Blockers for Implementation)
**🔴 Blocker** — The following are absent and **required before any fleet starts work**:

| Missing Element | Why It Blocks |
|---|---|
| **`narration_engine.js` interface spec** | All lessons integrate with it; fleets cannot implement "section listen buttons" or "live karaoke highlighting" without event names, method signatures, and data contracts. |
| **`manifest.json` / `manifest.js` schema** | Audio Synthesis Fleet produces these; lesson HTML/JS consumes them. No schema = integration guesswork. |
| **`lesson.css` / `lesson.js` exported API** | Lead Agent owns them; all fleets depend on them. No documented hooks, CSS custom properties, or JS module exports = fragile coupling. |
| **Bookmark component spec** | "Chips must wrap" but no markup pattern, ARIA roles, or state management (active, completed, locked). |
| **Hero video component spec** | `#heroLocalBox` / `#heroYtBox` toggling logic, fallback behavior, YouTube API loading strategy. |
| **Audio Synthesis Fleet deliverable checklist** | `sec_*.mp3` naming, loudness target (EBU R128 -14 LUFS?), silence padding, manifest generation script. |
| **Conflict resolution protocol** | "Zero collision" is aspirational. What happens when Calculus needs a CSS variable Linear Algebra defined? When Audio Synthesis needs a new manifest field? |
| **Definition of "Lesson"** | Granularity: one HTML file per lesson? What about multi-part lessons, supplements, exercises? |

### 6. Risk / Blind Spots
**🔴 Blocker** — Unverified assumptions that will cause failures:

| Risk | Likelihood | Impact |
|---|---|---|
| **Lead Agent becomes bottleneck** | High | All global changes (CSS, JS, index.html, curriculum index) route through one agent. No parallelism for cross-cutting concerns. |
| **`lesson_01.html` as template drift** | High | Linear Algebra Fleet owns `lesson_02–05` but `lesson_01` is Lead-owned. If `lesson_01` evolves, fleets won't know to update their lessons. No template sync mechanism. |
| **Audio Synthesis Fleet decoupled from lesson structure** | Medium | Fleet generates audio + manifests but has zero visibility into lesson HTML structure (section IDs, timing markers). Karaoke highlighting will desync. |
| **No offline-first validation** | Medium | `file://` support claimed but no service worker, no cache manifest, no test matrix for browser file:// restrictions (CORS, module loading). |
| **Single voice ID hardcoded** | Low | `bn-BD-PradeepNeural` baked in. If Edge TTS deprecates it or a course needs a different persona (e.g., younger voice for Lockdown Math), every lesson breaks. |
| **No accessibility baseline** | Medium | "Karaoke highlighting" implies visual-only. No screen-reader announcements, no keyboard nav for audio pill, no reduced-motion respect. |
| **YouTube iframe vs local video sync** | Medium | Two players, one "sole audio authority" rule. No spec for how `postMessage` / YouTube Player API coordinates with `narration_engine.js`. |

### 7. Decision Traceability
**🟡 Major** — Rules are stated as edicts without traceability:

| Rule | Missing Trace |
|---|---|
| No dubbed hero audio bar | What user research / A/B test / stakeholder decision killed it? |
| `bn-BD-PradeepNeural` mandatory | Why not `NabanitaNeural`? Why not Google Studio voices? |
| `flex-wrap: wrap` for bookmarks | Why not CSS Grid? Mobile breakpoint tested? |
| Local video default over YouTube | Bandwidth? Copyright? Offline-first philosophy? |
| 8 fleet split (not 6, not 10) | Course dependency graph? Team capacity? |
| Lead Agent owns `curriculum_index.json` | Why not a dedicated Curriculum Agent? |

Without ADRs (Architecture Decision Records) or linked RFCs, future maintainers cannot evaluate whether to relax a rule.

---

## Summary Verdict

| Dimension | Rating |
|---|---|
| Purpose Clarity | ✅ Clear |
| Scope Boundaries | ⚠️ Incomplete (runtime, interfaces, evolution) |
| Audience Fit | ⚠️ Assumes tribal knowledge |
| Structural Coherence | ✅ Clean |
| **Missing Critical Elements** | 🔴 **Blockers present** |
| **Risk / Blind Spots** | 🔴 **High-severity unverified assumptions** |
| Decision Traceability | ⚠️ No ADR trail |

**Recommendation:** **Do not greenlight fleet work** until the 8 blocker items in §5 are specced (interface contracts, schemas, component specs, conflict protocol) and the 7 risks in §6 have mitigation plans documented. This document is a *constitution* — it needs an accompanying *implementer's manual* and *decision log*.

---

## Suggested Next Steps

1. **Create `docs/architecture/interfaces/`** with:
   - `narration_engine.api.md` (TypeScript interfaces + event definitions)
   - `manifest.schema.json` (JSON Schema for both `.json` and `.js` variants)
   - `lesson_component.spec.md` (HTML structure, CSS custom props, JS hooks for hero, bookmarks, audio pill)
2. **Add `governance/ADR/`** folder; retroactively file ADRs for each Section 1 rule.
3. **Define "Template Sync Protocol"**: How `lesson_01.html` changes propagate to fleet-owned lessons (PR template? Automated diff check?).
4. **Specify Audio Synthesis ↔ Lesson contract**: Section ID ↔ `sec_*.mp3` mapping, timing metadata, karaoke word-boundary data format.
5. **Run a "Day 0" tabletop**: Simulate Calculus Fleet adding a new CSS variable → who reviews? How does Linear Algebra learn? Document the flow.