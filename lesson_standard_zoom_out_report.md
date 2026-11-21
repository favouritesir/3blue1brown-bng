# EGM Zoom-Out Review: LESSON_PRODUCTION_STANDARD.md

## Paraphrase of the Document

This document establishes the master architectural and execution guidelines for building a Bengali-language educational platform that mirrors 3Blue1Brown's lesson content (100% fidelity to the official site) while exceeding it in UI/UX sophistication. It defines three core pillars:

1. **Core Philosophy**: Content parity with 3B1B's official lessons + premium interactive UI (floating TOC drawer, quick chapter stepper, prev/next navigation cards, Watch/Read dual modes, interactive canvas labs/quizzes).
2. **Audio vs Textbook Segregation**: Strict separation between TTS scripts (phonetic Bengali only, zero Latin characters, em-dash for pauses) and textbook notes (natural pedagogical Bengali with KaTeX math notation).
3. **Style & File Structure**: Shared CSS/JS across lessons, local figure assets per lesson, local dubbed videos with YouTube switcher in both Watch and Read modes.

---

## Findings

### 🔴 Blocker: No Implementation Architecture or Technology Decisions
**The document specifies *what* to build but not *how* or *with what*.** Critical missing decisions:
- Frontend framework (React? Vue? Svelte? Vanilla JS with modules? Astro? Next.js?)
- Build system and deployment target (static site? SSR? Edge functions?)
- State management for Watch/Read modes, TOC drawer, chapter stepper
- Video player implementation (native `<video>`? HLS.js? Video.js? Mux? Custom theater mode?)
- KaTeX rendering strategy (server-side? client-side? mathjax fallback?)
- Interactive canvas lab framework (Canvas API? WebGL? Three.js? P5.js? Custom?)
- Quiz system data model and persistence (localStorage? IndexedDB? Supabase? Firebase?)

**Impact**: Every subagent will make independent, incompatible technology choices. The "shared CSS/JS" mandate becomes impossible to enforce without a defined module system.

---

### 🔴 Blocker: No Content Ingestion Pipeline Defined
**How do 3B1B lessons actually get into this platform?** The document assumes content parity but provides zero mechanism:
- No source-of-truth definition (scrape 3b1b.com? Use their GitHub repo? Manual curation?)
- No schema for lesson metadata (title, chapter order, video URL, figures, quiz questions, transcript)
- No validation that "100% fidelity" is achieved (automated diff? Manual QA checklist?)
- No handling of 3B1B updates (new lessons, revised content, retired content)
- No copyright/licensing strategy for redistributing 3B1B content (even dubbed)

**Impact**: Content operations will be chaotic, inconsistent, and legally risky.

---

### 🔴 Blocker: Audio Production Pipeline Underspecified
The TTS rules are precise (phonetic Bengali, em-dash pauses) but the *production workflow* is absent:
- Who writes phonetic scripts? (LLM prompt? Human reviewer? Hybrid?)
- Which TTS engine? (Edge-TTS? Google Cloud TTS? ElevenLabs? Coqui? Local model?)
- Voice selection per character (the document mentions "character voice casting" in other standards but not here)
- Audio post-processing: normalization (EBU R128?), silence trimming, chapter segmentation
- Sync with video: forced alignment? Manual timestamping? WhisperX?
- Quality gates: automated pronunciation validation? Human QA sampling rate?

**Impact**: Audio quality will vary wildly; the "100% pronunciation purity" rule becomes unenforceable.

---

### 🟡 Major: Watch/Read Mode Architecture Undefined
The dual-mode UX is a headline feature but lacks structural definition:
- **Watch Mode**: "Theater player + 5-chapter playlist drawer" — Is this a single-page app with hash routing? Separate HTML per chapter? How does the playlist drawer persist state across chapters?
- **Read Mode**: "Full offline KaTeX-rich textbook" — Is this a separate render of the same content? Same HTML with CSS toggle? Progressive enhancement?
- **Mode Switching**: Instant toggle? Page reload? URL structure (`/lesson/01/watch` vs `/lesson/01/read`)?
- **Shared State**: Scroll position, playback position, completed quizzes — synced across modes?

**Impact**: Inconsistent UX, broken deep links, mode-switching friction.

---

### 🟡 Major: Interactive Canvas Labs & Quiz System — No Data Model
"Interactive canvas labs and quiz system with correct/incorrect feedback and 'show answer' button" implies:
- Question schema (multiple choice? free-form math input? drag-and-drop on canvas?)
- Answer validation logic (client-side? server-side?)
- Progress tracking (per user? anonymous? local-only?)
- Lab state serialization (save/resume canvas drawings?)
- Accessibility (keyboard navigation, screen reader support for canvas)

**Impact**: Each lab becomes a one-off custom implementation; no reusable component library.

---

### 🟡 Major: File Structure Mandate Conflicts with Modern Tooling
`../../assets/css/lesson.css` and `../../assets/js/lesson.js` relative paths assume:
- A specific directory depth (lessons at `lessons/la_0X/index.html`)
- No bundler (Vite, Webpack, esbuild) that rewrites asset paths
- No CSS/JS code-splitting or tree-shaking
- Global namespace pollution risk in `lesson.js`

**Impact**: Forces a fragile, non-scalable static-site structure. Modern frameworks will fight this convention.

---

### 🟡 Major: Video Hosting & Delivery Strategy Absent
"Local high-quality dubbed videos (`../../media_vault/lesson_0X/...`) and original YouTube switcher" raises:
- Storage: Git LFS? S3/R2? Bunny.net? Mux? Cloudflare Stream?
- Encoding: H.264? H.265? AV1? Multiple bitrates (adaptive streaming)?
- CDN: Who serves multi-GB video files? Cost model?
- YouTube switcher: Embed API? `youtube-nocookie.com`? Legal compliance for dubbing over YT embed?
- Offline/Read mode: How does "local video" work in a browser without Service Worker precaching?

**Impact**: Video delivery will fail at scale; legal exposure from unauthorized dubbing distribution.

---

### 🟡 Major: No Accessibility (a11y) Requirements
Zero mention of:
- WCAG compliance level (AA? AAA?)
- Keyboard navigation for TOC drawer, chapter stepper, video player, canvas labs
- Screen reader announcements for mode switches, quiz feedback
- Color contrast, focus indicators, reduced motion preferences
- Captions/subtitles for dubbed videos (Bengali + English?)

**Impact**: Platform excludes users with disabilities; potential legal liability.

---

### 🟡 Major: No Internationalization (i18n) Architecture
The document is Bengali-specific but a "platform" implies extensibility:
- Hardcoded Bengali strings in HTML/JS vs. translation keys
- RTL/LTR support (not needed for Bengali but for future languages)
- Number formatting, date formatting
- Font loading strategy for Bengali (Noto Sans Bengali? Custom variable font?)

**Impact**: Adding another language requires full rewrite.

---

### 🟢 Nit: Versioning & Governance Metadata Missing
- No document version, author, last-reviewed date, or change log
- No "supersedes" or "related documents" references
- No approval/sign-off trail

**Impact**: Hard to track evolution; reviewers can't verify currency.

---

### 🟢 Nit: "Advance Beyond Vanilla" Examples Are UI Patterns, Not Architecture
The five bullet points (TOC drawer, chapter stepper, nav cards, Watch/Read, canvas labs) describe *features*, not *architectural principles*. No guidance on:
- Component composition model
- Design token system (colors, spacing, typography scale)
- Motion/animation standards (Framer Motion? CSS transitions? Web Animations API?)
- Responsive breakpoints
- Performance budgets (LCP, TBT, CLS targets)

**Impact**: Visual inconsistency across lessons; performance regressions undetected.

---

## Risk Summary & Blind Spots

| Risk | Likelihood | Severity | Mitigation |
|------|------------|----------|------------|
| **Tech stack fragmentation** | Very High | Blocker | Ratify framework + build system in a companion `TECH_STACK_DECISIONS.md` |
| **Content drift from 3B1B source** | High | Blocker | Define ingestion pipeline + automated diff + scheduled sync |
| **Audio quality variance** | High | Blocker | Specify TTS engine, voice map, QA gates, post-processing chain |
| **Video delivery failure at scale** | Medium | Major | Choose CDN + encoding ladder + cost model before Lesson 1 |
| **Legal exposure (copyright)** | Medium | Major | Document licensing strategy; consult IP counsel |
| **a11y retrofit cost** | High | Major | Bake a11y into component library from Day 1 |
| **Mobile UX degradation** | Medium | Major | Define responsive behavior for all 5 UI patterns |

---

## Decision Traceability Gap

The document **cannot be traced to concrete decisions or trade-offs** because it records *requirements* without recording *decisions*. For each mandate, we need:

| Mandate | Decision Needed | Trade-off Example |
|---------|-----------------|-------------------|
| Shared CSS/JS | Monorepo? Framework? Bundler? | Vanilla JS + esbuild (simple, no framework lock-in) vs. Astro (islands, fast) vs. Next.js (ecosystem, Vercel) |
| Phonetic TTS scripts | Engine + voice + prompt template | Edge-TTS (free, good Bengali) vs. Google Neural2 (paid, better prosody) vs. ElevenLabs (paid, best expressiveness) |
| Local video + YT switcher | Hosting + encoding + legal | Self-host on R2 + H.264 1080p (control, cost) vs. Mux (adaptive, expensive) vs. YT embed only (free, no control) |
| Canvas labs | Rendering library + state model | Canvas API (light, manual) vs. P5.js (educational, heavy) vs. Three.js (3D, overkill) |

---

## Recommendations (Priority Order)

1. **🔴 Create `TECH_STACK_DECISIONS.md`** — Ratify framework, build tool, deployment, state management, component model.
2. **🔴 Create `CONTENT_INGESTION_PIPELINE.md`** — Define source, schema, validation, sync cadence, legal basis.
3. **🔴 Create `AUDIO_PRODUCTION_SPEC.md`** — TTS engine, voice map, script authoring workflow, post-processing, QA gates.
4. **🔴 Create `VIDEO_DELIVERY_STRATEGY.md`** — Hosting, encoding, CDN, adaptive streaming, offline support, legal.
5. **🟡 Create `WATCH_READ_ARCHITECTURE.md`** — Routing, state sharing, mode switching, URL structure, SSR vs CSR.
6. **🟡 Create `INTERACTIVE_COMPONENT_SPEC.md`** — Quiz schema, canvas lab API, progress tracking, accessibility.
7. **🟡 Create `ACCESSIBILITY_REQUIREMENTS.md`** — WCAG target, component a11y checklist, testing protocol.
8. **🟢 Add document metadata** — Version, date, authors, changelog, related docs.

---

## Verdict

**This document is a requirements sketch, not an architectural standard.** It defines *desired outcomes* without the *structural decisions* that make implementation coherent, scalable, and verifiable. Treat it as the input to a decision-making process (EGM Draft → Review → Ratify), not as a finished governance artifact.

**Next Step**: Run `egm-draft` to convert these findings into a decision-record document (`ARCHITECTURAL_DECISIONS.md`) that the team can ratify before any code is written.