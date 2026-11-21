# Feature Spec Paraphrase

The **Dub Studio & BRF Orchestration & Agent Architecture Framework** defines a governance model for producing high-quality Bengali dubbing and educational content through a hierarchical multi-agent system.

**Core objectives:**
- **Lead Orchestrator Freedom**: The primary agent never executes long-running, blocking work (translation line-by-line, file downloads, audio generation). Instead, it analyzes tasks and spawns specialized sub-agents, assigning each the most capable model for its domain.
- **Translation Integrity**: All Bengali output must be authored by high-reasoning LLMs — never raw machine translation (Google Translate, MyMemory). Output must read as native conversational/academic Bengali, with domain-appropriate terminology for math, science, and code.
- **Strict Folder Taxonomy**: All work is organized under a canonical hierarchy: `departments/media_production/youtube_channels/`, `departments/learning_paths/stem_mathematics/`, `departments/research_academic/`, `departments/books_docs/`, `departments/rnd_lab/`. Every channel, course, or project has a deterministic path.
- **Clean Repository Policy**: Only 100%-complete, production-verified artifacts persist in the main catalog. Intermediate/temporary work lives in `temp_dub/` and is auto-purged on completion.

**Sub-agent roles defined:**
1. **Script Adapter & Cultural Translator** — High-reasoning LLM (Gemini 1.5 Pro / Claude 3.5 Sonnet / GPT-4o tier). Translates English scripts into natural, pedagogically sound Bengali dialogue.
2. **Audio-Visual & Time-Sync Engineer** — Maps timestamps, performs microsecond-level time-stretching (`atempo`), and handles sidechain mixing for lip-sync accuracy.
3. **QA & Content Verification Agent** — Audits translations for robotic phrasing/inconsistencies and validates audio-video sync.

---

# Implementation Plan Paraphrase

*Inferred from the principles and sub-agent definitions — the document does not contain an explicit implementation plan.*

**Architecture:**
- A **Lead Orchestrator** (always-free coordinator) receives high-level dubbing tasks, decomposes them, and spawns three specialized sub-agents in parallel or sequence.
- Each sub-agent is assigned a model tier matching its cognitive load: heavy reasoning for translation, specialized DSP/audio tooling for sync, verification logic for QA.
- Communication between agents is implicit — the document assumes a task-passing mechanism but does not specify APIs, message formats, or orchestration runtime.

**Workflow (inferred):**
1. Lead Orchestrator ingests source video + English script/transcript.
2. Spawns **Script Adapter** → produces natural Bengali script with timing cues.
3. Spawns **Audio-Visual Sync Engineer** → takes Bengali script + original audio timestamps → generates time-aligned Bengali audio (TTS + `atempo` stretching + sidechain mix with preserved SFX bed).
4. Spawns **QA Agent** → validates linguistic quality + temporal sync against video frames.
5. On pass: artifacts promoted to canonical `departments/` path; temps purged.
6. On fail: feedback loop to relevant sub-agent (mechanism unspecified).

**Missing implementation pieces:**
- No TTS engine selection logic (Edge-TTS vs Google AI Studio vs other).
- No specification for "BRF" (referenced in title, never defined).
- No sub-agent invocation protocol (CLI? MCP? HTTP? in-process?).
- No state management, checkpointing, or retry policy.
- No observability/logging/tracing requirements.
- No versioning or rollback strategy for promoted artifacts.

---

# Comprehension Findings

## 🔴 Blocker

| # | Finding | Why It Blocks |
|---|---------|---------------|
| 1 | **"BRF" is undefined** | The framework title references "BRF Orchestration" but the acronym never appears again. A reader cannot know if this is a typo, a separate system, or the name of the orchestration layer itself. |
| 2 | **No sub-agent invocation mechanism** | The document says the Lead Orchestrator "spawns" sub-agents but provides zero detail: CLI commands? MCP tools? HTTP endpoints? In-process function calls? Without this, the architecture cannot be implemented. |
| 3 | **TTS engine selection absent** | Section 5 of the global instructions (provided to the parent session) mandates context-driven TTS selection (Edge-TTS vs Google AI Studio) with batching protocols. The framework document ignores this entirely — no decision logic, no batching, no delimiter strategy. |
| 4 | **No audio separation / SFX preservation pipeline** | Global instruction §8 assigns NVIDIA Mistral Large 4 1T for Demucs 2-stem separation + Wiener filtering + hard gating. The framework mentions "sidechain mixing" but not stem separation, SFX bed extraction, or vocal bleed elimination. |
| 5 | **No delimiter / slicing protocol for continuous TTS** | Global instruction §9 requires `\n\n... ... ...\n\n` acoustic delimiters for deterministic slicing. The framework has no mention of this, making the Audio-Visual Sync Engineer's output non-deterministic. |

## 🟡 Major

| # | Finding | Impact |
|---|---------|--------|
| 6 | **Model assignment is vague** | "Gemini 1.5 Pro / Claude 3.5 Sonnet / GPT-4o সমমানের মডেল" — no version pinning, no fallback chain, no cost/latency tradeoff guidance. |
| 7 | **No QA criteria codified** | "Audit for robotic phrasing" and "validate sync" are subjective. No metrics (e.g., BLEU, COMET, sync tolerance in ms), no automated checks, no pass/fail thresholds. |
| 8 | **Folder taxonomy lacks file naming conventions** | The hierarchy shows directories but not file names (e.g., `script.bn.txt`, `audio_dubbed.wav`, `sync_report.json`). Implementers will invent inconsistent names. |
| 9 | **Temp directory cleanup policy is aspirational** | "Auto-deleted on completion" — no mechanism described (cron? post-hook? orchestrator responsibility?). Failure mid-pipeline leaves orphaned temps. |
| 10 | **No feedback loop specification** | When QA fails, how does the Lead Orchestrator route corrections? Re-spawn same agent? Escalate to human? Modify prompt and retry? |
| 11 | **Phonetic acronym safeguard missing** | Global instruction §5 requires `AI`→`এআই`, `x-অক্ষ`→`এক্স অক্ষ`, etc. The Script Adapter role does not reference this rule. |
| 12 | **Gender/voice integrity rules absent** | Global instruction §6 mandates male→male, female→female voice locking with audible vocal bursts. No sub-agent owns this. |
| 13 | **Loudness normalization not assigned** | EBU R128 (-14 LUFS, -1 dBTP) required by global instructions. Not mentioned in any sub-agent role. |

## 🟢 Nit

| # | Finding | Note |
|---|---------|------|
| 14 | **Mixed language in headers** | Section 1 uses Bengali headings (ক, খ, গ, ঘ) but Section 2 uses Arabic numerals (1, 2, 3). Inconsistent. |
| 15 | **Code block shows incomplete tree** | The `departments/` tree ends abruptly at `rnd_lab/` with no children — looks unfinished. |
| 16 | **"BRF" appears only in title** | If it means "Bengali Rendering Framework" or similar, it should be defined or removed. |
| 17 | **No document version/date/owner** | Governance docs typically carry metadata for change control. |
| 18 | **"Sub-Agent Allocation" section only lists 3 agents** | Title implies a guide for *all* sub-agents; only three are defined. Are there more? |