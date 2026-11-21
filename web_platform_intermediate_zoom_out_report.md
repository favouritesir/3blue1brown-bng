# EGM Intermediate Zoom-Out Review: WEB_PLATFORM_AGENT_BOUNDARIES.md

**Document:** `governance/WEB_PLATFORM_AGENT_BOUNDARIES.md`  
**Reviewer:** EGM Intermediate Zoom-Out Reviewer (egm-zoom-out)  
**Date:** 2026-11-05  
**Protocol:** Zoom-Out Standard (Synthesis of Stage 5 Zoom-Out + Stage 6 Comprehension + Stage 7 Critic)  
**Context Reports:** `web_platform_zoom_out_report.md` (Stage 5), `web_platform_comprehension_report.md` (Stage 6), `web_platform_critic_report.md` (Stage 7)

---

## Paraphrase (Synthesized)

The three prior reviews converge on a single verdict: **this document is a territorial map masquerading as a governance constitution**. It declares eight agent fleets and five architectural invariants but provides **zero executable interfaces, zero synchronization contracts, zero coordination mechanics, and zero traceability for its own edicts**. The Stage 5 Zoom-Out found 8 blocker gaps and 7 high-severity risks. Stage 6 Comprehension confirmed 5 hard blockers (undefined paths, schemas, APIs, templates) and 7 major onboarding gaps. Stage 7 Critic added 8 new blockers across design/structure/style — including circular dependencies, unactionable boundaries, terminology drift, and direct violations of the Global Instructions (hardcoded single TTS voice ignoring context-driven selection mandate). **No review has mitigated any finding; they have only compounded evidence of the same root causes.** The high-level architecture remains **fundamentally incomplete** — not "partially specified" but **structurally unbuildable** without the missing interface layer.

---

## Findings

### 1. What Has Been "Added/Mitigated" by the Review Process Itself
**🟡 Major** — The reviews have not *changed* the document (it is frozen at v1). They have only **diagnosed**. What emerges is a *shared diagnostic consensus* that now exists as institutional knowledge:

| Consensus Insight | Stage 5 | Stage 6 | Stage 7 | Status |
|---|---|---|---|---|
| **No interface contracts exist** | Finding 5 (Blocker) | Findings B3, B4, B5 | S1 (Blocker), D2 (Blocker) | **Confirmed ×3** |
| **Lead Agent is a bottleneck** | Risk 1 (High) | — | S2 (Blocker: circular dep) | **Confirmed ×2** |
| **Audio Fleet ↔ Lesson decoupling** | Risk 3 (Medium) | — | D2 (Blocker) | **Confirmed ×2** |
| **Offline `file://` is aspirational** | Risk 4 (Medium) | M5 (Major) | D4 (Blocker) | **Confirmed ×3** |
| **Single voice hardcoded violates Global Instructions** | Risk 6 (Low) | — | **D3 (Blocker)** | **Escalated to Blocker** |
| **No governance mechanics (only territory map)** | — | M4 (Major) | **S3 (Blocker)** | **Confirmed ×2** |
| **Terminology drift (Fleet/Agent/Subagent)** | — | — | **Y2 (Blocker)** | **Newly surfaced** |
| **Manifest versioning absent** | Finding 5 (Blocker) | — | **S5 (Major)** | **Confirmed ×2** |

**Net mitigation: Zero.** The document remains unmodified. The review process has only converted "suspected gaps" into "triple-confirmed blockers."

---

### 2. New Risks Emerging from Synthesis (Cross-Report Compounding)

#### 2.1 **Architecture × Governance Category Error** — 🔴 Blocker
**Synthesis:** Stage 5 (§7) noted "Rules are stated as edicts without traceability." Stage 7 (D7, Y3, S3) reveals the deeper cause: **the document conflates three distinct rule categories into one numbered list:**
- **Runtime Invariants** (must hold at execution: sole audio authority, no horizontal scrollbar, local video default)
- **Governance Constraints** (who may edit what: fleet territories, Lead Agent ownership)
- **Implementation Decisions** (voice choice, manifest format, CSS technique)

**Emergent Risk:** Agents cannot distinguish *testable runtime contracts* from *negotiable governance policies* from *changeable implementation details*. A fleet questioning `bn-BD-PradeepNeural` (implementation decision) gets the same "STRICT/ PERMANENT" shut-down as one violating sole audio authority (runtime invariant). This **paralyzes legitimate technical discourse** and **masks the fact that runtime invariants have no verification mechanism**.

#### 2.2 **Interface Vacuum Creates Silent Contract Drift** — 🔴 Blocker
**Synthesis:** Stage 5 (Finding 5: 8 missing specs), Stage 6 (B3, B4, B5: manifest, engine API, lesson template), Stage 7 (S1, S7: no contracts, no asset pipeline spec).

**Emergent Risk:** Without explicit contracts, **each fleet will implicitly invent its own interface** to the shared layer:
- Linear Algebra Fleet builds `lesson_02.html` assuming `manifest.json` has `sections[].words[]` for karaoke.
- Audio Fleet produces `manifest.json` with only `sections[].sentences[]`.
- `narration_engine.js` (Lead) expects `sections[].timestamps[]`.

**All three pass local validation. Integration fails at runtime.** The "zero collision" file boundary **guarantees interface drift** because it discourages cross-fleet communication *precisely where interfaces live* (manifest schema, engine events, DOM contracts).

#### 2.3 **Circular Dependency + No Coordination Protocol = Deadlock** — 🔴 Blocker
**Synthesis:** Stage 7 S2 identifies the cycle: Lead owns `narration_engine.js` (consumes manifests) + `curriculum_index.json` (indexes courses). Course Fleets own lessons + audio folders. Audio Fleet writes manifests consumed by Lead's engine.

**Emergent Risk:** When Linear Algebra Fleet adds `lesson_06.html` with a new audio section type:
1. Fleet needs `curriculum_index.json` updated → Lead Agent gate.
2. Fleet needs Audio Fleet to generate new manifest format → Audio Fleet gate.
3. Audio Fleet needs manifest schema version bump → Lead Agent gate (owns `narration_engine.js`).
4. Lead Agent needs Fleet to test new engine version → Fleet gate.

**Four-way deadlock.** No escalation path exists (S3: "Missing Agent Communication & Coordination Protocol"). The "zero collision" territory map **institutionalizes the cycle** by giving each party veto power over the others' dependencies.

#### 2.4 **Global Instructions Violation Baked Into Architecture** — 🔴 Blocker
**Synthesis:** Stage 7 D3: Rule 10 mandates `bn-BD-PradeepNeural` for *all* teacher narration. Global Instructions §1 **explicitly requires context-driven TTS selection**: Edge-TTS for lectures/tutorials, Google AI Studio (`gemini-3.8-flash-tts`) for drama/multi-character/high-emotion content.

**Emergent Risk:** This is not a "low risk" (Stage 5) — it is an **architectural violation of the parent framework's mandatory protocol**. If Lockdown Math Fleet needs dramatic character voices (Steve/Maggie style), they **cannot comply** without breaking the "STRICT BOUNDARY" rule. The document **forbids the very capability the parent framework requires**. This will force either:
- Silent non-compliance (fleets use Google Studio anyway → architecture fracture), or
- Formal exception requests with no process (M4, S3) → governance paralysis.

#### 2.5 **Terminology Drift as Governance Erosion Vector** — 🟡 Major
**Synthesis:** Stage 7 Y2: "Fleet" vs "Agent" vs "Subagent" used interchangeably. Stage 6 M1, M2: Agent IDs are informal labels, not deployable configs.

**Emergent Risk:** In a Paperclip/orchestration context, **"Agent - Linear Algebra Fleet" is not a hireable agent**. It has no prompt, no tool permissions, no MCP server mapping. The governance document **describes a social arrangement, not a technical deployment topology**. When the board asks "which agent owns Calculus lesson_03?", the answer cannot be resolved to a running process. This **decouples governance from execution** — the map does not match the territory.

#### 2.6 **Offline-First Claim Without Threat Model** — 🟡 Major
**Synthesis:** Stage 5 Risk 4, Stage 6 M5, Stage 7 D4: `file://` support claimed via `manifest.js` preload. But: Chrome blocks `file://` XHR/fetch, ES modules fail, no service worker, no cache manifest, no integrity verification.

**Emergent Risk:** The architecture **assumes a browser capability that does not exist by default**. Agents building to this spec will produce lessons that **work in the Lead Agent's test environment (local server) but fail for end users opening `index.html` directly**. No agent owns "offline validation" — it falls in the cracks between Lead (engine), Fleets (lessons), Audio (manifests).

---

### 3. High-Level Architecture: Verified or Fundamentally Incomplete?

#### Verdict: **FUNDAMENTALLY INCOMPLETE** — 🔴 Blocker

| Architecture Layer | Specified? | Verified? | Gap Severity |
|---|---|---|---|
| **Runtime Invariants (Behavioral Contracts)** | ❌ Declared only | ❌ No state machine, no event bus, no race handling | Blocker |
| **Interface Contracts (Manifest, Engine, DOM)** | ❌ 0/8 specs exist | ❌ Triple-confirmed missing | Blocker |
| **Agent Deployment Topology** | ❌ Social labels only | ❌ No prompts, tools, MCP mappings | Blocker |
| **Coordination & Governance Mechanics** | ❌ Territory map only | ❌ No queues, gates, escalation, review cadence | Blocker |
| **Asset Pipeline (Audio → Manifest → Engine)** | ❌ Path template only | ❌ No naming, encoding, versioning, delivery protocol | Blocker |
| **Offline/Determinism Guarantees** | ❌ Claimed, not specified | ❌ No threat model, no validation, no fallback | Blocker |
| **Parent Framework Alignment** | ❌ Violates §1 TTS mandate | ❌ Hardcoded single voice | Blocker |
| **Decision Traceability (ADRs)** | ❌ None | ❌ No history, no evolution path | Blocker |

**The document specifies *file ownership* but not *system behavior*.** It answers "who edits what" but not "how the system works." **File ownership is necessary but insufficient for architecture.** A fleet can own `lesson_02.html` perfectly and still produce a lesson that:
- Deadlocks audio/video playback (no sync invariant)
- Fails karaoke (no manifest/engine contract)
- Breaks offline (no `file://` threat model)
- Uses wrong TTS voice (violates parent framework)
- Cannot be integrated (no curriculum index protocol)

---

### 4. Synthesis: The "Zero Collision" Paradox

**🔴 Blocker — Core Architectural Contradiction**

The document's central promise — **"Strict Agent Territory & File Assignments (Zero Collision)"** — **creates the very collisions it fears** by drawing boundaries at the *file level* while the *system contracts* live in the *interfaces between files*:

```
┌─────────────────────────────────────────────────────────────┐
│  FILE BOUNDARIES (Specified)                                │
│  ─────────────────────────────────────────────────────────  │
│  Lead: index.html, lesson.css, lesson.js, narration_engine  │
│  Fleets: courses/<course>/lesson_*.html                     │
│  Audio: assets/audio/<course>/<lesson>/                     │
│  → "Zero collision" ✓                                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  SYSTEM CONTRACTS (Unspecified — LIVE IN THE GAPS)          │
│  ─────────────────────────────────────────────────────────  │
│  narration_engine.js  ←── manifest schema ──→  Audio Fleet  │
│       │                                               │     │
│       │ lesson.js / lesson.css                        │     │
│       ▼                                               ▼     │
│  Course Fleets (HTML, DOM IDs, CSS classes)  ←── CURRICULUM INDEX │
│       ▲                                               ▲     │
│       │ bookmark component, hero video, audio pill  │     │
│       └────────────────── SHARED GLOBALS ────────────┘     │
│  → Collision guaranteed: every fleet touches globals        │
│     with no ownership, no API, no versioning                │
└─────────────────────────────────────────────────────────────┘
```

**The "STRICT BOUNDARY (DO NOT TOUCH)" column is a fiction.** Course fleets **must** touch `lesson.css`/`lesson.js` globals (via their HTML) to function. The Audio Fleet **must** align manifest schema with `narration_engine.js`. The Lead Agent **must** update `curriculum_index.json` for every fleet's lessons. **Every arrow in the diagram above is a required collaboration that the territory map forbids.**

---

## Summary Verdict (Updated from Stage 5)

| Dimension | Stage 5 Rating | Stage 6/7 Delta | **Intermediate Verdict** |
|---|---|---|---|
| Purpose Clarity | ✅ Clear | — | ✅ Clear (but purpose = territory map, not architecture) |
| Scope Boundaries | ⚠️ Incomplete | +3 blockers (S1, S2, S3) | 🔴 **Fundamentally unbounded** |
| Audience Fit | ⚠️ Tribal knowledge | +2 blockers (Y2, M1/M2) | 🔴 **Un-onboardable** |
| Structural Coherence | ✅ Clean | -1 (Y3: mixed constraint types) | ⚠️ **Coherent but wrong structure** |
| **Missing Critical Elements** | 🔴 8 Blockers | +8 Blockers (D1, D2, D3, S1, S2, S3, Y1, Y2) | 🔴 **16 Blockers — unbuildable** |
| **Risk / Blind Spots** | 🔴 7 High | +6 synthesized risks (§2 above) | 🔴 **13 compounding risks** |
| Decision Traceability | ⚠️ No ADR | — | 🔴 **Zero traceability** |
| **Parent Framework Alignment** | — | 🔴 **Violates §1 TTS mandate** | 🔴 **Non-compliant** |

---

## Recommendations (Priority Order — Must Complete Before Any Fleet Work)

### 🔴 **Phase 0: Interface Contracts (Prerequisite for All Work)**
1. **Publish `docs/architecture/interfaces/`** with machine-checkable specs:
   - `manifest.schema.json` (JSON Schema + TypeScript types, versioned)
   - `narration_engine.api.ts` (Event bus: `AudioEvent`, `VideoEvent`, `KaraokeEvent`; state machine)
   - `lesson_component.spec.md` (Required DOM IDs, CSS custom properties, JS hooks for hero, bookmarks, audio pill)
   - `audio_delivery.protocol.md` (Naming: `sec_{lesson}_{section}_{idx}.mp3`; encoding: 128kbps Opus, -14 LUFS; `manifest.js` as UMD global `window.__LESSON_MANIFEST__`)

### 🔴 **Phase 1: Resolve Circular Dependency**
2. **Declare explicit dependency direction** (one-way only):
   - Course Fleets → Lead Agent: **Read-only** consumption of `lesson.css`/`lesson.js`/`narration_engine.js`; **PR-based** updates to `curriculum_index.json` (Lead merges)
   - Audio Fleet → Lead Agent: **Schema-versioned** manifest delivery (Audio Fleet bumps `manifestVersion`; Lead Agent updates engine with backward-compat)
   - Lead Agent → Course Fleets: **Semantic versioned** global releases (`lesson.css` v1.2.0, `narration_engine.js` v2.0.0) with changelog

3. **Add `governance/COORDINATION_PROTOCOL.md`** with:
   - Task queue format (YAML/JSON for fleet work items)
   - Handoff checklist (Audio → Fleet: manifest + audio + verification script)
   - Escalation path (Fleet Lead → Platform Lead → Architect)
   - Review gates (Pre-flight: manifest validation; Post-integration: offline smoke test)

### 🔴 **Phase 2: Align with Global Instructions**
4. **Revise Rule 10** to implement **context-driven TTS selection** per Global Instructions §1:
   - Default: `bn-BD-PradeepNeural` (Edge-TTS) for lectures/tutorials
   - Opt-in per course/lesson: Google AI Studio (`gemini-3.8-flash-tts`) for drama/multi-character
   - Audio Fleet owns engine selection logic; manifests carry `ttsEngine` + `voiceId` fields

5. **Add offline threat model** (`docs/architecture/offline_threat_model.md`):
   - `file://` CORS matrix (Chrome/Firefox/Safari/Edge)
   - Manifest delivery: inline `<script>` + `localStorage` fallback
   - Audio: `<audio preload="metadata">` + `localStorage` blob cache
   - Validation script: `npm run verify:offline` (headless Chrome `file://`)

### 🟡 **Phase 3: Governance Hardening**
6. **Split document into three** (per Stage 7 Rec 3):
   - `governance/SYSTEM_INVARIANTS.md` (Runtime rules with testable acceptance criteria)
   - `governance/AGENT_CHARTER.md` (Territories, coordination protocol, escalation, review cadence)
   - `standards/UI_UX_SPEC.md` (Component inventory, string glossary, CSS tokens, accessibility baseline)

7. **Make boundaries machine-checkable**:
   - `CODEOWNERS` for GitHub enforcement
   - ESLint `no-restricted-paths` for cross-fleet imports
   - Pre-commit: `manifest.schema.json` validation, `curriculum_index.json` schema check

8. **Add governance metadata**: Version, owner, review cadence (monthly), change log, exception process template, deprecation policy.

---

## Final Verdict

**Do not authorize any fleet work.** The document in its current state is a **territory map without a machine**. The 16 blocker findings (8 original + 8 from Critic) and 6 synthesized compounding risks represent **architectural absence**, not incompleteness. The "zero collision" file boundaries **guarantee interface collisions** by forbidding the cross-fleet collaboration that shared globals require. The hardcoded TTS voice **violates the parent framework's mandatory protocol**. No agent can be deployed from the informal "Fleet" labels.

**Minimum viable path:** Complete Phases 0–1 (interface contracts + dependency resolution + Global Instructions alignment) → validate with a **single pilot lesson** (Linear Algebra lesson_02, end-to-end: audio generation → manifest → lesson HTML → offline verification) → then authorize fleet parallelization.

---

*Report generated by EGM Intermediate Zoom-Out Review Synthesizer*  
*Cross-referenced: zoom_out_report.md (Stage 5) + comprehension_report.md (Stage 6) + critic_report.md (Stage 7)*