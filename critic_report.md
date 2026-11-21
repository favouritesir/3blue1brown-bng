# Consolidated Critic Review: AGENT_WORKFLOW_GUIDELINES.md

**Document:** `governance/AGENT_WORKFLOW_GUIDELINES.md` (57 lines)
**Context:** Zoom-Out Report findings incorporated
**Reviewers:** egm-design, egm-structural, egm-style
**Date:** 2026-11-05

---

## 1. egm-design — Feature Design & Problem Fit

### 🔴 Blocker

#### 1.1 No Explicit Problem Statement / Scope Definition
**Finding:** The document never defines *what problem it solves* or *what content types* it governs. "Dub Studio & BRF" appears in the title but BRF is undefined. Is this for YouTube kids' content (Steve & Maggie)? Educational STEM (3Blue1Brown)? Long-form courses? Shorts? The master-voice-dubbing skill references specific pipelines (batching, SFX preservation, EBU R128) — this doc doesn't acknowledge them.

**Impact:** Agents cannot self-onboard; scope creep is inevitable; the framework may conflict with the more detailed global instructions.

#### 1.2 Hardcoded Model Names Create Maintenance Debt
**Finding:** Section 2 hardcodes "Gemini 1.5 Pro / Claude 3.5 Sonnet / GPT-4o" as the Script Adapter model. Model versions age in months. A *framework* document should reference **model aliases** or a **model registry**, not specific versions.

**Impact:** Every model update requires editing a governance doc; leads cannot swap models per-task without governance churn.

#### 1.3 Sub-Agent Decomposition Lacks Rationale
**Finding:** Three sub-agents are declared (Script Adapter, Audio-Visual Sync Engineer, QA) with no justification for *why these three* and *why not others* (e.g., separate Localization QA vs Technical QA, a dedicated SFX/Foley Agent per the master skill's Demucs requirement, a Publishing/Metadata Agent).

**Impact:** Future maintainers cannot evaluate whether the decomposition still fits when content types expand (podcasts, shorts, live-action).

---

### 🟡 Major

#### 1.4 "Lead Orchestrator Always Free" — Trade-offs Unacknowledged
**Finding:** Principle 1 declares the lead must never block. But no discussion of:
- Cost implications (spawning many sub-agents = more API calls)
- Latency overhead (handoff chains)
- Failure modes (what if sub-agent fails? no escalation path defined)
- Human-in-the-loop checkpoints

**Impact:** The principle reads as dogma, not a design decision with understood trade-offs.

#### 1.5 Folder Taxonomy Coupled to Source Type, Not Workflow Stage
**Finding:** The taxonomy (`departments/media_production/youtube_channels/<channel>/...`) organizes by *source origin*, not *pipeline stage* (raw → translated → timed → synced → QA → publish-ready). This makes it hard to query "all items pending QA" or "all items with sync drift > 50ms".

**Impact:** Operational tooling (dashboards, CI gates) must fight the filesystem structure.

---

### 🟢 Nit

#### 1.6 "Keep Only Perfect Works" — No Versioning/Iteration Mechanism
**Finding:** Principle 4 bans incomplete files but provides no mechanism for: A/B versions, iterative improvement, archival of superseded takes, or rollback when a "perfect" master later fails QA.

**Impact:** Teams will create shadow folders (`_v2`, `_fixed`, `_archive`) defeating the principle.

---

## 2. egm-structural — Architecture, Interfaces, Dependencies

### 🔴 Blocker

#### 2.1 Zero Handoff Contracts / Data Schemas Between Sub-Agents
**Finding:** Section 2 lists *responsibilities* but not *interfaces*. Critical missing contracts:
| Handoff | Missing Schema |
|---------|----------------|
| Script Adapter → Sync Engineer | Timed script format (SRT? JSON with word-level timestamps? Custom schema with emotion tags?) |
| Sync Engineer → QA | Sync map format, loudness metrics, drift measurements |
| QA → Lead | Pass/fail criteria, measurable thresholds (drift ms, LUFS, bleed dB) |

**Impact:** Integration is ad-hoc; each sub-agent pair must negotiate formats at runtime — violates "Lead Always Free" (lead must mediate format disputes).

#### 2.2 No Error / Retry / Escalation Policy
**Finding:** What happens when:
- Sync Engineer detects drift > threshold?
- QA fails a segment?
- TTS API rate-limits or returns error?
- Sub-agent times out?

No retry logic, no dead-letter queue, no human escalation path defined.

**Impact:** Long-running dub jobs (30+ min) have no resilience; a single transient failure kills the pipeline.

#### 2.3 No Observability / Logging / Audit Requirements
**Finding:** No mention of:
- Distributed traces across sub-agents
- Structured logs (JSON) for debugging
- Metrics emission (latency, error rate, drift distribution)
- Audit trail for "Production Verified" claim

**Impact:** Debugging multi-agent runs is guesswork; compliance/audit impossible.

#### 2.4 No Versioning & Rollback Strategy for Artifacts
**Finding:** Principle 4 ("Keep Only Perfect Works") implies versioning but provides zero mechanism for:
- Versioning master audio, scripts, sync maps
- Immutable artifact storage (content-addressed?)
- Rollback to previous "perfect" version
- Diff/blame across versions

**Impact:** "Perfect" is a moving target; no way to recover when a later discovery invalidates an earlier pass.

#### 2.5 Security / Secrets Handling Absent
**Finding:** TTS API keys (Google AI Studio, Edge-TTS), cloud storage credentials, webhook secrets — not addressed. Sub-agents need credentials; no pattern for secret injection, rotation, or least-privilege.

**Impact:** Credentials hardcoded or leaked in logs; no audit of secret access.

#### 2.6 No Testing / CI Gates Defined
**Finding:** No automated validation steps:
- Loudness check (EBU R128 -14 LUFS)
- Sync drift check (threshold?)
- Vocal bleed detection
- Bengali phonetic validity (acronym expansion, no raw Latin)
- Folder taxonomy conformance

**Impact:** "Production Verified" is a manual claim, not an automated gate.

---

### 🟡 Major

#### 2.7 BRF Acronym Undefined — Architectural Ambiguity
**Finding:** Title references "BRF" but document never expands it. Is it "Bengali Rendering Framework"? "Batch Rendering Flow"? "Bengali Resource Format"? The master-voice-dubbing skill doesn't use this acronym.

**Impact:** Cannot determine if this doc *is* the BRF spec, *governs* BRF, or *replaces* BRF.

#### 2.8 Sub-Agent Interfaces Underspecified — "Audio-Visual Sync Engineer" Has No Inputs
**Finding:** Sync Engineer responsibility: "map audio timing per timestamp, microsecond-level time-stretch (`atempo`) and sidechain mixing." But:
- Input format? (Script Adapter output? Raw SRT? EDL?)
- Output format? (FFmpeg filtergraph? DAW session? Rendered WAV?)
- Configuration? (target loudness, drift threshold, crossfade params)

**Impact:** Sync Engineer is a black box; cannot be implemented, tested, or replaced independently.

#### 2.9 QA Agent Underspecified — "Audit Sync" Is Not Measurable
**Finding:** QA responsibility: "audit whether translation has robotic language and whether audio synced properly with video." No measurable criteria:
- Max allowed drift (ms)?
- Loudness tolerance (± LUFS)?
- Bleed threshold (dB)?
- Robotic language detection method (heuristic? LLM judge? perceptual metric?)

**Impact:** QA cannot be automated; "pass/fail" is subjective.

---

### 🟢 Nit

#### 2.10 Folder Taxonomy Rigidity
**Finding:** Hardcoded paths (`departments/media_production/youtube_channels/...`) assume all content fits YouTube channel → topic → playlist hierarchy. New content types (podcasts, shorts, courses, live streams) may not map cleanly.

**Impact:** Teams will create parallel structures (`departments/podcasts/...`) duplicating tooling.

---

## 3. egm-style — Clarity, Consistency, Actionability, Terminology

### 🔴 Blocker

#### 3.1 Bilingual Headers Inconsistent — English Sometimes Missing, Sometimes Partial
**Finding:** Section headers mix patterns:
- `## 1. Core Principles (কোর নীতিমালা)` — English + Bengali
- `### ক. এজেন্ট সবসময় মুক্ত থাকবে (Lead Orchestrator Always Free)` — Bengali letter + Bengali + English in parens
- `## 2. সাব-এজেন্ট কাঠামো ও মডেল নির্বাচন গাইডলাইন (Sub-Agent Allocation)` — Bengali + English in parens

**Inconsistency:** Sometimes English is the primary with Bengali gloss, sometimes Bengali primary with English gloss. No consistent convention.

**Impact:** Cognitive load for bilingual readers; tooling (TOC generators, linters) cannot parse reliably.

#### 3.2 Terminology Drift: "Sub-Agent" vs "Sub-Agents" vs "সাব-এজেন্ট"
**Finding:** Document uses:
- "Sub-Agents" (capitalized, plural) — line 7
- "সাব-এজেন্ট" (Bengali) — line 8, 48
- "Sub-Agent Allocation" (English, singular) — section 2 title
- "Script Adapter & Cultural Translator" — role title (not "Sub-Agent")

**Impact:** Search/grep fails; glossary needed.

#### 3.3 "BRF" Used in Title, Never Defined, Never Used Again
**Finding:** Acronym appears *only* in title. Violates "define on first use" principle.

**Impact:** Reader cannot determine document's relationship to BRF.

---

### 🟡 Major

#### 3.4 Principles Stated as Decrees, Not Actionable Rules
**Finding:** Principles use "will not" / "must not" language but lack *enforceable criteria*:
- "Lead Agent will not do long heavy work directly" → How long? How heavy? Measured how?
- "No raw machine translator" → How to detect? Automated check?
- "Keep only perfect works" → Who verifies? What checklist?

**Impact:** Principles cannot be codified into CI gates or automated policy.

#### 3.5 Section 2 Responsibilities Are Vague Verbs, Not Deliverables
**Finding:** "নিখুঁতভাবে বিশ্লেষণ করে দায়িত্ব অনুযায়ী... স্পন করবে" (analyze precisely and spawn per responsibility) — what is the *output artifact* of this analysis? A task graph? A JSON spec? A prompt template?

**Impact:** Implementer must invent the deliverable format.

#### 3.6 Mixed Audience: Strategic Principles + Tactical Model Names
**Finding:** Same document addresses:
- Architects (principles, taxonomy)
- Engineers (model names, `atempo`, sidechain mixing)
- QA (audit criteria)

**Impact:** No single reader finds the right density; tactical details rot the strategic doc.

---

### 🟢 Nit

#### 3.7 Bengali Numerals vs Arabic Numerals Inconsistent
**Finding:** Section numbers use Arabic (1, 2) but subsection letters use Bengali (ক, খ, গ, ঘ). Section 2 sub-items use Arabic (1, 2, 3).

**Impact:** Minor visual inconsistency; TOC parsing complexity.

#### 3.8 Code Block for Taxonomy Uses `text` Not `tree` or `yaml`
**Finding:** Fence says ```text but content is a tree diagram. No syntax highlighting benefit; could be ```tree or plain markdown list.

#### 3.9 Trailing Whitespace / Formatting Noise
**Finding:** Line 43 has `---` horizontal rule but no blank line before Section 2. Minor but indicates missing style guide.

---

## Consolidated Severity Summary

| Severity | egm-design | egm-structural | egm-style | **Total** |
|----------|------------|----------------|-----------|-----------|
| 🔴 Blocker | 3 | 6 | 3 | **12** |
| 🟡 Major | 2 | 3 | 3 | **8** |
| 🟢 Nit | 1 | 1 | 3 | **5** |

**Overall:** **Do not implement from this document.** It requires fundamental structural additions (contracts, error handling, observability, versioning, security), design rationale, and style standardization before it can serve as an architecture decision record or runbook.

---

## Priority Remediation Order

1. **Define Scope & BRF** — Add Section 0: Scope, Definitions, Out-of-Scope, Relationship to master-voice-dubbing skill
2. **Add Handoff Contracts** — JSON schemas for all sub-agent I/O (timed script, sync map, QA report)
3. **Extract Operational Config** — Model aliases, folder paths, thresholds → `config/agent-workflow.yaml`
4. **Add Error/Observability/Versioning/Security Sections** — Non-negotiable for production
5. **Add Decision Log Appendix** — Each principle → rationale, trade-offs, alternatives considered
6. **Standardize Bilingual Convention** — Pick one: English-primary + Bengali gloss, or Bengali-primary + English gloss. Apply consistently.
7. **Make Principles Enforceable** — Convert each to measurable acceptance criteria + automated check
8. **Resolve Terminology** — Glossary: "Sub-Agent", "BRF", "Script Adapter", "Sync Engineer", "QA Agent", "Production Verified"