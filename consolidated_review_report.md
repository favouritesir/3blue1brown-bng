# Consolidated Review Report: AGENT_WORKFLOW_GUIDELINES.md

**Document:** `governance/AGENT_WORKFLOW_GUIDELINES.md` (57 lines)  
**Review Mode:** Uninterrupted Full Flow (Consolidated)  
**Date:** 2026-11-05  
**Stages Completed:** 5 (Initial Zoom-Out), 6 (Comprehension), 7 (Critic), 8 (Intermediate Zoom-Out)  
**Stage 9 (Implementation Readiness):** Complete (`implementation_readiness_report.md`)

---

## Executive Summary

**Verdict: DO NOT IMPLEMENT.** The document is a **requirements sketch (~20% complete)**, not an implementable architecture. It captures high-level principles and three sub-agent roles but lacks every structural element needed for production: interface contracts, error handling, observability, versioning, security, CI gates, configuration management, decision traceability, and alignment with the governing `master-voice-dubbing` skill.

**Aggregate Severity (Stages 5-9):**
- 🔴 **Blocker: 32** (17 Stages 5-8 + 7 IR + 8 CB + 5 ST)
- 🟡 **Major: 15** (4 Stages 5-8 + 6 IR + 5 CB + 4 ST)
- 🟢 **Nit: 13** (5 Stages 5-8 + 2 IR + 2 CB + 4 ST)

**Readiness Verdict (Stage 9): 🟡 CONDITIONAL GO** — The document is a valid high-level governance framework but **not implementation-ready**. It lacks a Detailed Implementation Plan entirely.

---

## Stage-by-Stage Synthesis

### Stage 5: Initial Zoom-Out Review (`zoom_out_report.md`)
**Top Blockers:**
1. **Scope Boundaries Undefined** — BRF undefined; content types unspecified; relationship to global instructions absent
2. **Missing Critical Elements** — Zero handoff contracts, error policy, observability, versioning, security, CI gates
3. **Risk/Blind Spots** — Model version lock-in, global instructions conflict, no idempotency, single-point-of-failure Lead

### Stage 6: Comprehension Test (`comprehension_report.md`)
**Key Finding:** Document is **not self-contained**. A reader needs external knowledge for:
- BRF definition (nowhere in doc)
- Sub-agent invocation mechanism (CLI? MCP? HTTP?)
- TTS selection logic (Edge-TTS vs Google AI Studio) — mandated by global instructions
- SFX/Demucs pipeline — mandated by global instructions (§8)
- Acoustic delimiter protocol (`\n\n... ... ...\n\n`) — mandated by global instructions (§9)
- Phonetic acronym safeguard (AI→এআই, x-অক্ষ→এক্স অক্ষ) — mandated by global instructions (§5)
- Gender/voice integrity locking — mandated by global instructions (§6)
- EBU R128 loudness normalization — mandated by global instructions (§9)

**5 Blockers, 8 Majors, 5 Nits**

### Stage 7: Critic Review (`critic_report.md`)
**Three Reviewers, 25 Findings:**

| Reviewer | Blockers | Majors | Nits |
|----------|----------|--------|------|
| egm-design | 3 | 2 | 1 |
| egm-structural | 6 | 3 | 1 |
| egm-style | 3 | 3 | 3 |
| **Total** | **12** | **8** | **5** |

**Top Structural Blockers (egm-structural):**
1. Zero handoff contracts/schemas between sub-agents
2. No error/retry/escalation policy
3. No observability/logging/audit requirements
4. No versioning/rollback strategy
5. No security/secrets handling
6. No CI gates (loudness, drift, bleed, phonetic, taxonomy)

**Top Design Blockers (egm-design):**
1. No explicit problem statement/scope
2. Hardcoded model versions in framework doc
3. Sub-agent decomposition lacks rationale

**Top Style Blockers (egm-style):**
1. Inconsistent bilingual header convention
2. Terminology drift ("Sub-Agent" vs "Sub-Agents" vs "সাব-এজেন্ট")
3. "BRF" used once, never defined

### Stage 8: Intermediate Zoom-Out (`intermediate_zoom_out_report.md`)
**Synthesis Verdict:** **Zero Blockers resolved.** Document has not evolved through review — reviews only deepened understanding of gaps.

**Critical Emergent Risks:**
1. **Architecture Drift from Global Instructions (Critical)** — This framework neither references nor subordinates to `master-voice-dubbing` skill. If implemented as-is, it produces a **parallel, incompatible pipeline** violating every audio quality mandate (batching, delimiters, Demucs, EBU R128, phonetics, gender integrity).
2. **Silent Contract Assumptions (Critical)** — Three sub-agents, zero interface contracts. Lead Orchestrator becomes format mediator, violating Principle 1.
3. **No Resilience for Long-Running Jobs (High)** — 3-30 min dub jobs have no retry, checkpoint, dead-letter, or escalation.
4. **"Production Verified" Unauditable (High)** — No versioning, immutable storage, audit trail, or automated gates.
5. **Folder Taxonomy Coupled to Source, Not Pipeline Stage (Medium)** — Cannot answer operational queries efficiently.

**Architectural Pillar Verification: 0/13 verified**

---

### Stage 9: Implementation Readiness (`implementation_readiness_report.md`)
**Three Reviewers, 37 Findings:**

| Reviewer | Blockers | Majors | Nits |
|----------|----------|--------|------|
| egm-implementation-readiness | 7 | 6 | 2 |
| egm-codebase-details | 8 | 5 | 2 |
| egm-style | 5 | 4 | 4 |
| **Total** | **20** | **15** | **8** |

**Top Blockers (egm-implementation-readiness):**
1. **No Detailed Implementation Plan** — Document ends at Section 2; no architecture, data models, APIs, orchestration, state management, error handling, deployment, or testing strategy
2. **Orchestration mechanism undefined** — "Spawn sub-agents" has zero detail: process/thread/queue/RPC, agent interface, context passing, timeout/cancellation, failure recovery
3. **No agent communication protocol** — No I/O schemas, message formats, streaming/batch, partial results, progress reporting, inter-agent dependencies
4. **Model selection aspirational** — No abstraction layer, fallback chain, cost budget, rate-limit handling, prompt templates, evaluation criteria
5. **No data/storage specification** — Taxonomy shows directories but no persistence layer, metadata schema, indexing, cleanup/retention
6. **Audio-visual sync vague** — "Microsecond-level" false precision (perceptual tolerance ~20-40ms); no formats, tolerance, drift correction, reference impl
7. **QA criteria unmeasurable** — "Natural Bengali" / "robotic language" subjective; no automated metrics, thresholds, golden files, CI integration

**Top Blockers (egm-codebase-details — Greenfield Requirements):**
1. No project structure/entry point (`pyproject.toml`, module layout, CLI, config schema, plugin system)
2. No agent runtime/abstraction layer (base `Agent` class with `run()`, lifecycle, cancellation)
3. No LLM provider abstraction (unified interface: auth, streaming, retry, cost tracking, model registry)
4. No media processing pipeline (FFmpeg wrapper, silence slicing, time-stretch, sidechain, EBU R128, AAC mux)
5. No persistence/state layer (job queue, status enum, artifact metadata, idempotency keys, transactions)
6. No orchestration engine (DAG scheduler/workflow engine: parallel spawn, fan-in, partial failure, checkpoint resume)
7. No configuration management (typed config: endpoints, keys, roots, limits, policies, thresholds, TTLs)
8. No testing infrastructure (fixtures, mock LLM/media, golden files, property-based sync tests)

**Top Blockers (egm-style — Precision Deficits):**
1. "Natural Bengali" / "No robotic language" subjective, not testable
2. "Microsecond-level" — false precision; should state "max drift ≤ 20ms"
3. "Most suitable & powerful model" — unmeasurable; needs benchmarks, latency budget, cost ceiling, quality threshold
4. "Auto-deleted after processing" — no TTL, no failure mode
5. "Production Verified" — no definition; needs gate criteria

---

## Updated Traceability Matrix: Raw Findings → Consolidated Action Items

| Priority | Consolidated Action Item | Source Findings | Severity |
|----------|--------------------------|-----------------|----------|
| **P0** | **Define Scope & BRF** — Add Section 0: scope, content types, out-of-scope, explicit relationship to `master-voice-dubbing` skill | S5#2, S6#1, S7-1.1, S7-2.7, S8#2.1 | 🔴 |
| **P0** | **Add Handoff Contracts** — JSON schemas for: TimedScript (with delimiters), SyncMap, QAReport, EscalationEvent | S5#5, S6#2, S7-2.1, S7-2.8, S8#2.2 | 🔴 |
| **P0** | **Align with Global Instructions** — Subordinate or profile the `master-voice-dubbing` skill; incorporate TTS selection, batching, delimiters, Demucs, EBU R128, phonetics, gender integrity | S5#3, S6#3-5, S7-1.1, S8#2.1 | 🔴 |
| **P0** | **Error/Retry/Escalation Policy** — Define retry logic, dead-letter queue, human escalation, checkpoint/resume for 30+ min jobs | S5#5, S6#9, S7-2.2, S8#2.3, IR-8, IR-9, CB-7 | 🔴 |
| **P0** | **Observability & Audit Requirements** — Distributed traces, structured logs, metrics, audit trail for "Production Verified" | S5#5, S7-2.3, S8#2.4, IR-9, CB-12 | 🔴 |
| **P0** | **Versioning & Rollback Strategy** — Content-addressed artifact storage, immutable versions, diff/blame, rollback mechanism | S5#5, S6#8, S7-2.4, S8#2.4, IR-11 | 🔴 |
| **P0** | **Security/Secrets Handling** — Pattern for TTS API keys, cloud creds, webhook secrets: injection, rotation, least-privilege | S5#5, S7-2.5, IR-10 | 🔴 |
| **P0** | **CI Gates & Automated Testing** — 6 gates: loudness (-14 LUFS), drift threshold, bleed detection, phonetic validity, taxonomy conformance, sync validation | S5#5, S6#6, S7-2.6, S7-2.9, IR-7, CB-8, ST-1, ST-5 | 🔴 |
| **P0** | **Write Detailed Implementation Plan (Section 3+)** — Architecture, agent runtime, orchestration, data models, APIs | IR-1, IR-2, IR-3, CB-1, CB-2, CB-6 | 🔴 |
| **P0** | **Define LLM Provider Abstraction + Model Selection Policy** — Unified interface, model registry, fallbacks, cost guards | IR-4, CB-3, ST-3 | 🔴 |
| **P0** | **Design Persistence Layer & Storage Abstraction** — Schema, indexing, retention | IR-5, CB-5, CB-11 | 🔴 |
| **P0** | **Spec Audio Processing Pipeline** — Formats, tolerances, reference implementation | IR-6, CB-4, ST-2, ST-7, ST-8 | 🔴 |
| **P0** | **Define QA Gates & Automated Metrics** — Golden sets, thresholds, CI integration, rework loop | IR-7, CB-8, ST-1, ST-5 | 🔴 |
| **P1** | **Extract Operational Config** — `config/agent-workflow.yaml`: model aliases, folder paths, thresholds, TTS rules, retry policies | S5#3, S6#6, S7-1.2, S7-2.7, IR-12, IR-13, CB-7 | 🟡 |
| **P1** | **Sub-Agent Rationale & Expansion** — Justify 3 vs 5+ agents; add SFX/Foley (Demucs), Publishing/Metadata, Localization QA | S5#5, S6#13, S7-1.3, S7-2.8, CB-9, CB-10 | 🟡 |
| **P1** | **Decision Log Appendix** — Each principle → rationale, trade-offs, alternatives considered, revisit trigger | S5#7, S7-1.4, S7-3.4 | 🟡 |
| **P1** | **Glossary & Style Standardization** — Single bilingual convention, terminology lock, numeral convention, 10+ terms | S7-3.1, S7-3.2, S7-3.7, S8#2.6, ST-10, ST-11 | 🟡 |
| **P1** | **Principle → Acceptance Criteria Mapping** — Each principle → measurable check + automated gate | S7-1.4, S7-3.4, S7-3.5, ST-1, ST-3, ST-5 | 🟡 |
| **P1** | **Add Observability, Error Handling, Config, Concurrency Control** | IR-8, IR-9, IR-10, IR-12, CB-7, CB-12 | 🟡 |
| **P1** | **Versioning/Rework Loop + Bengali Preprocessing Lib** | IR-11, CB-9, ST-6 | 🟡 |
| **P1** | **Temp Cleanup Policy + GPU/Container Spec** | ST-4, IR-13, CB-10 | 🟡 |
| **P2** | **Folder Taxonomy Refactor** — Decouple from source type; add pipeline-stage metadata (status, drift, TTS engine, QA result) | S5#4, S7-1.5, S7-2.10, S8#2.5 | 🟢 |
| **P2** | **Style/Convention Cleanup** — Language, schemas, config, placeholders | ST-9, ST-10, IR-14, IR-15, ST-11, ST-12, ST-13, CB-14, CB-15 | 🟢 |

---

## Updated Readiness Verdict

| Criterion | Status | Notes |
|-----------|--------|-------|
| **Scope Defined** | ❌ No | BRF undefined; content types missing |
| **Architecture Complete** | ❌ No | 80% missing (contracts, resilience, obs, versioning, security, testing, config, alignment, traceability) |
| **Contracts Specified** | ❌ No | Zero handoff schemas |
| **Non-Functionals Addressed** | ❌ No | Error, obs, versioning, security, CI all absent |
| **Alignment with Governing Skill** | ❌ No | Direct conflict on every audio mandate |
| **Detailed Implementation Plan Exists** | ❌ No | Document ends at Section 2 |
| **Agent Runtime Defined** | ❌ No | No interface, orchestration, communication protocol |
| **LLM Abstraction Specified** | ❌ No | No unified interface, model registry, fallbacks |
| **Audio Pipeline Specified** | ❌ No | No formats, tolerances, reference impl |
| **QA Gates Defined** | ❌ No | No automated metrics, golden sets, thresholds |
| **Config Schema Exists** | ❌ No | No typed config for tunables |
| **Implementable As-Is** | ❌ **NO** | Cannot serve as ADR, runbook, or contract suite |

**Go/No-Go: NO-GO** (Conditional Go only after all P0 items implemented)

---

## Recommended Next Steps (Updated)

1. **Immediate (Before egm-draft):**
   - [ ] Define BRF, scope, and relationship to `master-voice-dubbing` skill
   - [ ] Draft 2 handoff contracts (Script Adapter → Sync Engineer, Sync Engineer → QA)
   - [ ] Propose `config/agent-workflow.yaml` structure
   - [ ] Create decision log template
   - [ ] Seed glossary with 10+ terms
   - [ ] **Write Detailed Implementation Plan (Section 3+)** — Architecture, agent runtime, orchestration, data models, APIs
   - [ ] **Define LLM Provider Abstraction + Model Selection Policy** — Unified interface, model registry, fallbacks, cost guards
   - [ ] **Design Persistence Layer & Storage Abstraction** — Schema, indexing, retention
   - [ ] **Spec Audio Processing Pipeline** — Formats, tolerances (≤20ms drift), reference implementation
   - [ ] **Define QA Gates & Automated Metrics** — Golden sets, thresholds, CI integration, rework loop

2. **Short-term (Architecture Completion):**
   - [ ] Add Error/Observability/Versioning/Security/CI sections
   - [ ] Expand sub-agent roster with rationale (SFX, Publishing, Localization QA)
   - [ ] Standardize bilingual convention and terminology
   - [ ] Map each principle to measurable acceptance criteria + automated gate
   - [ ] Temp cleanup policy + GPU/container spec
   - [ ] Versioning/rework loop + Bengali preprocessing lib

3. **Then:** Re-run EGM review (Stages 5-9) on the expanded document.

---

## Artifacts Generated (Updated)

| Report | Path | Description |
|--------|------|-------------|
| Zoom-Out (Stage 5) | `zoom_out_report.md` | Initial architectural assessment |
| Comprehension (Stage 6) | `comprehension_report.md` | Self-containment test with paraphrases |
| Critic (Stage 7) | `critic_report.md` | 3-reviewer antagonistic review (25 findings) |
| Intermediate Zoom-Out (Stage 8) | `intermediate_zoom_out_report.md` | Post-synthesis risk assessment |
| Implementation Readiness (Stage 9) | `implementation_readiness_report.md` | 3-reviewer readiness assessment (37 findings) |
| **Consolidated (This)** | `consolidated_review_report.md` | Cross-stage synthesis with traceability matrix |

---

*Review conducted via EGM Goldfish Review Protocol (Uninterrupted Full Flow preset). All individual reports written to working directory per Artifact-First Delivery mandate.*