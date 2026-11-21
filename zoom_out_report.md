# Zoom-Out Review Report: AGENT_WORKFLOW_GUIDELINES.md

## Document Paraphrase

This document proposes an **orchestration framework for "Dub Studio & BRF"** — a Bengali dubbing/production pipeline. It establishes four core principles (Lead Orchestrator stays free; no raw machine translation; clean folder taxonomy; keep only perfect works) and defines three sub-agent roles with model assignments: Script Adapter (high-reasoning LLM), Audio-Visual Sync Engineer, and QA Agent. The document is a strategic/architectural guideline, not an implementation spec.

---

## Findings

### 1. Purpose Clarity — 🟡 Major
**Issue:** The document's purpose is *implicit* rather than explicit. It never states: "This framework governs X pipeline for Y content types serving Z audience." The title mentions "Dub Studio & BRF" but BRF is undefined. Is this for YouTube dubbing? Educational content? Kids' shows (Steve & Maggie referenced in global instructions)? The scope of *what* gets dubbed remains ambiguous.

**Impact:** New contributors cannot self-onboard; they must infer context from tribal knowledge.

---

### 2. Scope Boundaries — 🔴 Blocker
**Issue:** No explicit boundaries. What is **out of scope**?
- Does this cover *video editing*, *thumbnail creation*, *metadata/SEO*, *publishing*?
- Does "BRF" mean a specific pipeline (e.g., "Bengali Rendering Framework") or a content brand?
- Are live-action, animation, and screencast workflows all covered identically?
- Where does this framework end and the **global instructions** (master-voice-dubbing skill) begin? The global instructions are far more detailed (batching, SFX preservation, EBU R128, Demucs separation) — this document doesn't reference or subordinate to them.

**Impact:** Scope creep inevitable; agents may duplicate or conflict with the master dubbing skill.

---

### 3. Audience Fit — 🟡 Major
**Issue:** The document mixes **strategic principles** (for architects/leads) with **tactical model names** (Gemini 1.5 Pro, Claude 3.5 Sonnet). Model versions age fast — hardcoding them in a "framework" document creates maintenance debt. The folder taxonomy is operational detail better suited to a runbook or config file.

**Impact:** Framework becomes stale quickly; leads must edit a governance doc to update a model alias.

---

### 4. Structural Coherence — 🟢 Nit
**Strength:** Principles → Sub-agents flows logically. Bengali + English bilingual headers aid the target team.

**Gap:** Section 2 lists *responsibilities* but not *interfaces* (inputs/outputs, handoff contracts, SLAs). How does Script Adapter pass timed cues to Sync Engineer? What format? JSON? SRT? A custom schema? Without contracts, integration is ad-hoc.

---

### 5. Missing Critical Elements — 🔴 Blocker
| Missing Element | Why It Matters |
|----------------|----------------|
| **Handoff contracts / data schemas** | Sub-agents cannot integrate without agreed I/O formats (timed scripts, sync maps, QA reports). |
| **Error/retry/escalation policy** | What happens when Sync Engineer detects drift > threshold? When QA fails? |
| **Observability / logging requirements** | No mention of traces, metrics, or audit logs for debugging multi-agent runs. |
| **Versioning & rollback strategy** | "Keep Only Perfect Works" is a principle, but no mechanism for versioning master audio, scripts, or sync maps. |
| **Security / secrets handling** | API keys for TTS engines, cloud storage — not addressed. |
| **Testing / CI gates** | No automated validation steps defined (e.g., loudness check, sync drift check). |
| **BRF definition** | The acronym in the title is never expanded. |

---

### 6. Risk / Blind Spots — 🔴 Blocker
| Risk | Likelihood | Severity |
|------|------------|----------|
| **Model version lock-in** | High | High — hardcoded model names will rot |
| **Global instructions conflict** | High | Critical — this doc doesn't acknowledge the master-voice-dubbing skill's detailed protocols (batching, SFX, Demucs, EBU R128, delimiter standard) |
| **No idempotency / resumability** | Medium | High — long-running dub jobs need checkpoint/restart |
| **Single-point-of-failure: Lead Orchestrator** | Medium | Medium — "always free" but no deputy/fallback defined |
| **Folder taxonomy rigidity** | Medium | Low — hardcoded paths may not fit new content types (podcasts, shorts, courses) |
| **QA agent underspecified** | High | High — "audit sync" is vague; no measurable criteria (drift ms, loudness LUFS, bleed dB) |

---

### 7. Decision Traceability — 🟡 Major
**Issue:** Principles are stated as decrees without **rationale** or **trade-off acknowledgment**.
- *Why* "Lead Orchestrator Always Free"? (Cost? Latency? Reliability? Human-in-the-loop?)
- *Why* those three sub-agents specifically? Why not a "Localization QA" separate from "Technical QA"?
- *Why* folder taxonomy structured by *source type* (departments/media_production/youtube_channels) rather than *output type* or *workflow stage*?
- *Why* "Keep Only Perfect Works" — what about iterative improvement, A/B versions, or archival?

**Impact:** Future maintainers cannot evaluate whether a principle still applies when context changes.

---

## Summary Severity Count
- 🔴 **Blocker**: 3 (Scope Boundaries, Missing Critical Elements, Risk/Blind Spots)
- 🟡 **Major**: 3 (Purpose Clarity, Audience Fit, Decision Traceability)
- 🟢 **Nit**: 1 (Structural Coherence — minor interface gap)

---

## Recommendation
**Do not implement from this document alone.** It needs:
1. A **Scope & Definitions** section (define BRF, content types, out-of-scope)
2. **Interface contracts** between sub-agents (JSON schemas or protobuf)
3. **Explicit alignment** with the master-voice-dubbing skill (subordinate or supersede?)
4. **Operational details** (model aliases, folder paths) moved to a config file / runbook
5. **Rationale traceability** — add "Decision Log" appendix linking each principle to a trade-off
6. **Observability, error handling, versioning, security** sections

Once these are added, this becomes a viable architecture decision record (ADR) + runbook hybrid.