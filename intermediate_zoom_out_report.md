# Intermediate Zoom-Out Review Report: AGENT_WORKFLOW_GUIDELINES.md

## Document Paraphrase (Updated)

This document proposes an **orchestration framework for "Dub Studio & BRF"** — a Bengali dubbing/production pipeline. It establishes four core principles (Lead Orchestrator stays free; no raw machine translation; clean folder taxonomy; keep only perfect works) and defines three sub-agent roles with model assignments: Script Adapter (high-reasoning LLM), Audio-Visual Sync Engineer, and QA Agent. The document is a strategic/architectural guideline, not an implementation spec.

**Context from prior reviews**: Three review stages have been completed:
- **Stage 5 (Initial Zoom-Out)**: Identified 3 Blockers, 3 Majors, 1 Nit — fundamental gaps in scope, contracts, observability, and alignment with global instructions.
- **Stage 6 (Comprehension)**: Confirmed 5 Blockers (undefined BRF, no invocation mechanism, missing TTS selection, no SFX pipeline, no delimiter protocol) and 8 Majors (vague models, uncodified QA, missing naming conventions, aspirational cleanup, no feedback loop, missing phonetic/gender/loudness rules).
- **Stage 7 (Critic Consolidated)**: 12 Blockers across design, structural, and style dimensions — including zero handoff contracts, no error/retry/escalation, no observability, no versioning, no security, no CI gates, terminology drift, unenforceable principles, and mixed audience.

---

## Findings

### 1. Synthesis Progress — What Has Been Added/Mitigated 🟢

| Area | Prior State (Stage 5) | Current State (Post-Stages 6-7) | Mitigation Status |
|------|----------------------|--------------------------------|-------------------|
| **BRF Definition** | Blocker — undefined acronym | **Still Blocker** — comprehension & critic both flag as unresolved | ❌ Not addressed |
| **Handoff Contracts** | Blocker — missing schemas | **Still Blocker** — critic details 3 critical missing schemas with formats | ❌ Not addressed |
| **TTS Engine Selection** | Not explicitly flagged | **Now Blocker** — comprehension identifies total absence vs. global instructions | ⚠️ Gap widened |
| **SFX Preservation / Demucs** | Not explicitly flagged | **Now Blocker** — comprehension maps to global instruction §8 (NVIDIA Mistral role) | ⚠️ Gap widened |
| **Delimiter Protocol** | Not explicitly flagged | **Now Blocker** — comprehension maps to global instruction §9 (`... ... ...` slicing) | ⚠️ Gap widened |
| **Error/Retry/Escalation** | Blocker — missing policy | **Still Blocker** — critic adds concrete failure scenarios (rate limits, timeouts, drift) | ❌ Not addressed |
| **Observability/Logging** | Blocker — missing requirements | **Still Blocker** — critic specifies distributed traces, structured logs, metrics, audit trail | ❌ Not addressed |
| **Versioning/Rollback** | Blocker — missing strategy | **Still Blocker** — critic adds immutable storage, diff/blame, content-addressing needs | ❌ Not addressed |
| **Security/Secrets** | Blocker — absent | **Still Blocker** — critic details TTS API keys, cloud creds, webhook secrets | ❌ Not addressed |
| **CI Gates/Testing** | Blocker — undefined | **Still Blocker** — critic lists 6 specific automated checks (loudness, drift, bleed, phonetic, taxonomy) | ❌ Not addressed |
| **Model Versioning** | Major — hardcoded names | **Blocker** — critic elevates: maintenance debt, no alias/registry pattern | ⚠️ Severity escalated |
| **QA Measurability** | Major — vague criteria | **Blocker** — critic demands ms drift, LUFS tolerance, dB bleed, detection method | ⚠️ Severity escalated |
| **Sub-Agent Rationale** | Major — no justification | **Blocker** — design critic: no rationale for 3 vs. 5+ agents (SFX, Publishing, Localization QA) | ⚠️ Severity escalated |
| **Terminology Consistency** | Nit — mixed usage | **Blocker** — style critic: "Sub-Agent"/"Sub-Agents"/"সাব-এজेंट" drift breaks search/grep | ⚠️ Severity escalated |
| **Principle Enforceability** | Major — decrees not rules | **Blocker** — style critic: no measurable acceptance criteria, cannot codify to CI | ⚠️ Severity escalated |

**Summary**: **Zero Blockers from Stage 5 have been resolved.** Three Stage 5 Blockers persist unchanged. **Five new Blockers emerged** from deeper comprehension (TTS, SFX, delimiters, phonetic, gender, loudness). **Four Majors escalated to Blockers** under structural/style scrutiny. The document has **not evolved** — reviews only deepened understanding of its gaps.

---

### 2. New Risks Emerging from Synthesis 🔴

#### 2.1 **Architecture Drift from Global Instructions (Critical)**
The global instructions (`master-voice-dubbing` skill) contain a **fully specified production pipeline**:
- Context-driven TTS selection (Edge-TTS vs Google AI Studio) with batching protocol
- Continuous master block generation with `\n\n... ... ...\n\n` acoustic delimiters
- NVIDIA Mistral Large 4 1T for Demucs 2-stem separation + Wiener filtering + hard gating
- EBU R128 loudness normalization (-14 LUFS, -1 dBTP)
- Phonetic acronym safeguard (AI→এআই, x-অক্ষ→এক্স অক্ষ)
- Gender/voice integrity locking (male→male, female→female)
- SFX bed preservation at -3 dB headroom
- Deterministic silence-gap slicing + 25-30ms crossfading

**Risk**: This framework document **neither references nor subordinates to** the global instructions. If implemented as-is, it will produce a **parallel, incompatible pipeline** that violates every audio quality mandate. The Lead Orchestrator would spawn sub-agents that know nothing of batching, delimiters, Demucs, or EBU R128.

#### 2.2 **Silent Contract Assumptions Will Cause Runtime Integration Failures (Critical)**
Three sub-agents are defined with **zero interface contracts**:
- Script Adapter → Sync Engineer: What format? SRT? Word-level JSON? Custom schema with emotion tags? Delimiter-embedded?
- Sync Engineer → QA: Sync map? Loudness metrics? Drift measurements? Rendered WAV + sidecar JSON?
- QA → Lead: Pass/fail boolean? Structured report with thresholds? Annotated timeline?

**Risk**: Each sub-agent pair will negotiate formats at runtime. The Lead Orchestrator (meant to stay free) becomes a **format mediator**, violating Principle 1. Integration bugs will surface only in production dub runs (30+ min), wasting compute and human review time.

#### 2.3 **No Resilience for Long-Running Dub Jobs (High)**
Dub jobs run 3-30+ minutes (per global instructions: "3-5 minute master blocks"). Failure modes with **no handling**:
- TTS API rate limit / quota exhaustion mid-block
- Network timeout during large audio download/upload
- Sync Engineer detects drift > threshold — retry? re-slice? escalate?
- QA fails segment — re-spawn Script Adapter? Sync Engineer? Human review?
- Sub-agent OOM / crash — checkpoint exists? Resume from where?

**Risk**: A single transient failure **kills the entire pipeline**. No dead-letter queue, no retry-with-backoff, no human escalation path. "Lead Always Free" becomes "Lead Always Helpless" when sub-agents fail silently.

#### 2.4 **"Production Verified" Is an Unauditable Claim (High)**
Principle 4: "Keep Only Perfect Works" / "Production Verified". But:
- No versioning of master audio, scripts, sync maps
- No immutable artifact storage (content-addressed?)
- No audit trail linking QA pass to specific artifact hashes
- No diff/blame across versions
- No automated gates — "verified" = human says so

**Risk**: When a "perfect" master later fails downstream (e.g., YouTube loudness penalty, viewer reports sync drift), **no rollback, no root cause, no accountability**. Teams will create shadow folders (`_v2`, `_fixed`) defeating the principle.

#### 2.5 **Folder Taxonomy Coupled to Source, Not Pipeline Stage (Medium)**
Taxonomy: `departments/media_production/youtube_channels/<channel>/<topic>/<slug>/`
**Operational queries this structure cannot answer efficiently**:
- "All items pending QA"
- "All items with sync drift > 50ms"
- "All items using Google AI Studio TTS (for cost audit)"
- "All items missing phonetic acronym expansion"

**Risk**: Dashboards, CI gates, and cost tracking must fight the filesystem. Teams will create parallel indexes (databases, spreadsheets) duplicating metadata.

#### 2.6 **Terminology Drift Will Break Tooling & Onboarding (Medium)**
Inconsistent terms: "Sub-Agents", "Sub-Agents", "সাব-এজেন্ট", "Sub-Agent Allocation", "Script Adapter & Cultural Translator" (not labeled sub-agent).
**Risk**: Grep/search fails. Automated doc linters fail. New hires cannot build a mental glossary. Glossary appendix is now a **requirement, not a nice-to-have**.

#### 2.7 **Mixed Audience Creates Maintenance Schism (Medium)**
Same document targets:
- Architects (principles, taxonomy)
- Engineers (model names, `atempo`, sidechain mixing)
- QA (audit criteria)
- Ops (folder paths, cleanup)

**Risk**: Tactical details (model versions, `atempo` params) **rot the strategic doc**. Engineers edit governance to update a model alias. Architects avoid the doc because it's cluttered with implementation noise. Split into: **ADR (architecture decisions)** + **Runbook (operational config)** + **Contracts (schemas)**.

---

### 3. High-Level Architecture Verification Status ❌

| Architectural Pillar | Verified? | Evidence |
|---------------------|-----------|----------|
| **Scope & Definitions** | ❌ No | BRF undefined; content types unspecified; relationship to global instructions undefined |
| **Sub-Agent Decomposition** | ❌ No | 3 agents declared without rationale; missing SFX, Publishing, Localization QA per global instructions |
| **Interface Contracts** | ❌ No | Zero schemas for any handoff; formats, protocols, error payloads all absent |
| **Error Handling & Resilience** | ❌ No | No retry, escalation, checkpoint, dead-letter, or timeout policies |
| **Observability & Audit** | ❌ No | No traces, logs, metrics, or audit trail requirements |
| **Versioning & Rollback** | ❌ No | No mechanism for artifact versioning, immutable storage, or recovery |
| **Security & Secrets** | ❌ No | No pattern for API keys, credentials, rotation, or least-privilege |
| **Testing & CI Gates** | ❌ No | No automated validation (loudness, drift, bleed, phonetic, taxonomy) |
| **Configuration Management** | ❌ No | Model names, paths, thresholds hardcoded in governance doc |
| **Decision Traceability** | ❌ No | Principles lack rationale, trade-offs, alternatives considered |
| **Terminology & Style** | ❌ No | Bilingual inconsistency, term drift, mixed numerals, no glossary |
| **Alignment with Global Instructions** | ❌ No | Direct conflict on TTS, SFX, delimiters, loudness, phonetics, gender integrity |

**Verdict**: **The high-level architecture is fundamentally incomplete.** It captures ~20% of the required architectural surface (principles + 3 roles). The remaining 80% (contracts, resilience, observability, versioning, security, testing, config, alignment, traceability) is absent. **This document cannot serve as an ADR or implementation basis.**

---

## Summary Severity Count (Post-Synthesis)

| Severity | Count | Source |
|----------|-------|--------|
| 🔴 **Blocker** | **17** | 3 (Stage 5) + 5 new (comprehension) + 4 escalated (critic) + 5 persistent |
| 🟡 **Major** | **4** | 3 (Stage 5) - 4 escalated + 5 new comprehension majors not escalated |
| 🟢 **Nit** | **5** | Mostly style/formatting; terminology drift escalated to Blocker |

---

## Recommendation (Updated)

**Do not implement from this document.** The gap between this framework and the production reality defined in global instructions has **widened**, not narrowed, through review.

**Minimum viable architecture requires**:

1. **Section 0: Scope & Definitions** — Define BRF, content types, out-of-scope, explicit relationship to `master-voice-dubbing` skill (subordinate? supersede? profile?)
2. **Handoff Contracts (Appendix/Schema Files)** — JSON schemas for: TimedScript (with delimiters), SyncMap, QAReport, EscalationEvent
3. **Operational Config Extraction** — `config/agent-workflow.yaml` with: model aliases, folder paths, thresholds (drift ms, LUFS, bleed dB), TTS selection rules, retry policies
4. **Non-Functional Requirements Sections** — Error/retry/escalation, observability (traces/logs/metrics), versioning (content-addressed artifacts), security (secret injection), CI gates (6 automated checks)
5. **Decision Log Appendix** — Each principle → rationale, trade-offs, alternatives considered, revisit trigger
6. **Sub-Agent Rationale & Expansion** — Justify 3 vs. 5+; add SFX/Foley Agent (Demucs), Publishing/Metadata Agent, Localization QA Agent
7. **Glossary & Style Standardization** — Single bilingual convention, terminology lock, "Sub-Agent" definition, numeral convention
8. **Principle → Acceptance Criteria Mapping** — Each principle → measurable check + automated gate

**Only after these 8 additions** does this become a viable ADR + runbook + contract suite hybrid.

---

## Next Review Gate

**Proceed to egm-draft (design document)** only after:
- [ ] Scope & BRF defined
- [ ] At least 2 handoff contracts drafted (Script Adapter → Sync Engineer, Sync Engineer → QA)
- [ ] Config file structure proposed
- [ ] Decision log template created
- [ ] Glossary seeded with 10+ terms

The current document is a **requirements sketch**, not an architecture. Treat it as such.