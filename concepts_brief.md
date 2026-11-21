# 3Blue1Brown Bengali Interactive Platform (3b1b-bn)

* **Author:** Bangla Resource Factory CEO
* **Date:** 2026-11-04

## Overview

A modern, standalone, dependency-free Bengali interactive web clone of 3Blue1Brown (3b1b.com). It adapts the 3Blue1Brown mathematics catalog into native, pedagogically articulate Bengali, featuring interactive SVG/Canvas visualizations, comprehensive lesson articles, and studio-grade Bengali dubbed video/audio streams with original sound effects (SFX) preserved and zero vocal bleed.

## Analysis & EGM Architectural Resolutions

### 1. Dependency-Free Frontend & Offline Math Rendering
- **Math Rendering (Resolved Blocker 1):** MathJax/KaTeX will be vendored directly as lightweight local static scripts under `web_platform/assets/libs/`. No runtime CDN fetches (and zero compromised `polyfill.io` calls); the site runs 100% offline and locally without build steps.
- **Modern Vanilla Web Shell:** Built with native HTML5, modular CSS with 3b1b dark/light tokens, and vanilla ES6 components. Clean, reactive, and instantly viewable via simple browser preview (`file://` or local dev server).

### 2. Delta Sweep & Asset Preservation Policy (Resolved Blocker 2)
- **Targeted Delta Sweep:** Rather than an uncontrolled blanket deletion, we execute a verified delta sweep:
  - Keep and migrate completed, high-value production assets (original `.m4a` audio, extracted SVG/media figures, and validated Bengali master transcripts).
  - Purge broken, unverified, one-off test scripts and temporary scratch files.
  - Archive obsolete `.typ` files under `references/archive/`.

### 3. Canonical Folder Taxonomy & Single Source of Truth
- **Unified Structure (Resolved Major 3):**
  ```text
  departments/learning_paths/stem_mathematics/3blue1brown_courses/
  ├── web_platform/                   # Main standalone web app
  │   ├── index.html                  # Main catalog & course directory
  │   ├── assets/                     # Shared styles, scripts, vendored MathJax
  │   └── courses/                    # Course routes
  │       └── linear_algebra/         # e.g., Essence of Linear Algebra
  │           ├── lesson_01/index.html
  │           └── lesson_02/index.html
  └── media_vault/                    # Canonical audio/video stems and dubbing archives
  ```

### 4. Swarm Execution: Phased Pipeline Queue (Resolved Major 4)
- To strictly respect the host machine limit (8GB RAM / Host Mandate of max 3 concurrent heavy processes):
  - **Phase 1 (Design & Shell):** Lead Web Architect builds `web_platform` shell, shared design tokens, and canonical `curriculum_index.json`.
  - **Phase 2 (Content Batch 1):** Two concurrent Content Adapters adapt Lessons 1 and 2 (Bengali text + interactive SVGs).
  - **Phase 3 (Audio Dubbing & Muxing):** Audio Engineers run Edge-TTS batching (`bn-BD-PradeepNeural`), stem gating, and SFX mixing with resource governor monitoring.
  - **Phase 4 (Iterative Scale):** Subsequent lessons processed sequentially in batches of 2-3.

### 5. Dual-Track Web Player with Zero Vocal Bleed (Resolved Major 5)
- **Player Architecture:** Custom HTML5 synchronized media component.
  - Source video plays with `.volume = 0` (or `muted`) to ensure 100% elimination of original English speech.
  - Bengali narration audio plays concurrently through HTML5 `<audio>` alongside an isolated original SFX bed.
  - Sidechain ducking ensures SFX rings clear in natural pauses, with zero English bleed.

## Goals vs. Non-Goals

* **In-Scope Goals:**
  - Fast, responsive, offline-ready 3b1b web platform in Bengali.
  - High-pedagogy Bengali content adhering to BRF educational standards.
  - Vendored local math libraries (offline MathJax/KaTeX).
  - Edge-TTS dubbing pipeline with zero English vocal bleed and pristine SFX retention.
  - Phased subagent execution respecting resource governance.

* **Out-of-Scope Non-Goals:**
  - React/Next.js runtime dependencies or npm install requirements.
  - Google AI Studio multi-voice TTS (single-speaker lecture format strictly utilizes Edge-TTS).
  - Destructive blanket purge of existing valuable assets.

## Alternatives Weighed

- **Alternative 1: Direct Next.js Repo Clone (`3b1b/3Blue1Brown.com`)**:
  - *Rejected by author:* Heavy npm dependency graph adds operational fragility and build friction.
- **Alternative 2: CDN-reliant Web Pages**:
  - *Rejected by author:* Online CDN scripts prevent pure offline local usage and risk external outage/security issues.
- **Alternative 3: Unbounded 10-Agent Swarm**:
  - *Rejected by author:* Exceeds host hardware limits (8GB RAM). Phased 2-3 concurrent queue delivers stable, unthrottled results.

## Key Decisions & Staging for Implementation

1. **Gate Clearance:** EGM Zoom-Out review findings integrated; blockers resolved.
2. **Phase 1 Execution:** Delta sweep of working directory; scaffold `web_platform/` with offline assets and theme shell.
3. **Phase 2 Execution:** Dispatch Content Adapters and Dubbing Subagents in controlled queues.
