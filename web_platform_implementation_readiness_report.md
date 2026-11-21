# WEB PLATFORM IMPLEMENTATION READINESS REVIEW

**Document:** `governance/WEB_PLATFORM_AGENT_BOUNDARIES.md`  
**Date:** 2026-11-05  
**Reviewers:** egm-implementation-readiness, egm-codebase-details, egm-style  
**Status:** 🔴 **NO-GO** — Critical blockers prevent implementation start

---

## REVIEWER 1: egm-implementation-readiness
*Can this be implemented as written? What's missing for a dev to start coding?*

### 🔴 Blocker
| # | Finding | Missing for Dev Start |
|---|---------|----------------------|
| 1 | **No file tree / directory structure defined** | The spec references paths like `departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/audio/<course>/<lesson>/` but never defines the root directory, whether `web_platform/` sits at repo root or under `departments/`, or how courses map to folders. A dev cannot create files without knowing the exact tree. |
| 2 | **`narration_engine.js` is mandated but undefined** | Rule #7 says "Teacher Narration Audio (`narration_engine.js`) IS MANDATORY" but the spec nowhere describes its API, event model, how it reads `manifest.js`/`manifest.json`, how it controls the floating pill (`#smartAudioPill`), top banner, section buttons, or karaoke highlighting. No interface contract = unbuildable. |
| 3 | **`manifest.js` / `manifest.json` schema absent** | The spec says audio is "driven by `manifest.js` (preloaded script for 100% offline file:// support) and `manifest.json`" but gives zero schema: required fields, section timing format, URL vs. local path handling, versioning. Audio Synthesis Fleet cannot generate valid manifests; Lesson agents cannot consume them. |
| 4 | **No lesson HTML template / component contract** | Agents are assigned `lesson_01.html` through `lesson_05.html` but the spec never defines: required DOM IDs (`#mainVideo`, `#heroLocalBox`, `#heroYtBox`, `#smartAudioPill`), CSS class names, script load order, how a lesson declares its sections for karaoke, or how it binds to `narration_engine.js`. Every fleet would invent their own → collision. |
| 5 | **`curriculum_index.json` structure undefined** | Lead Agent owns it; all fleets likely need to read it for navigation/course listing. No schema = each fleet guesses. |
| 6 | **Video asset naming & location convention missing** | Rules mention `#heroLocalBox` (local Bengali video) and `#heroYtBox` (YouTube) but never say where video files live, naming pattern (`lesson_01_bn.mp4`?), codec/container requirements, or how the lesson HTML references them. |
| 7 | **No build / deployment / offline support spec** | "100% offline file:// support" is claimed but no guidance on: service worker? bundler? relative paths? CORS for `file://`? How `manifest.js` is "preloaded"? A dev cannot verify offline works without this. |
| 8 | **Agent coordination protocol unspecified** | "Lead Agent exercises supervisory review and coordinates all child agents" — but how? PR reviews? Shared lint config? CI gates? No process = social problem, not technical, but blocks parallel work. |

### 🟡 Major
| # | Finding |
|---|---------|
| 9 | **No versioning / migration strategy** for manifests, audio schema, or lesson template. Future changes will break existing lessons silently. |
| 10 | **No testing strategy** — unit tests for `narration_engine.js`, integration tests for audio/video mutual exclusion, visual regression for bookmark wrap, offline verification. |
| 11 | **Accessibility requirements absent** — karaoke highlighting must meet WCAG (contrast, focus order, screen reader announcements). Not mentioned. |
| 12 | **Performance budgets missing** — max JS bundle size, audio preload strategy, video lazy-load, time-to-interactive on low-end devices. |

### 🟢 Nit
| # | Finding |
|---|---------|
| 13 | Table uses "Agent - Linear Algebra Fleet" etc. — inconsistent naming vs. "Lead Agent (Antigravity)". Pick one convention. |
| 14 | Date format in header: "2026-11-05" — ISO is fine, but confirm team standard. |

---

## REVIEWER 2: egm-codebase-details
*Codebase-specific constraints (greenfield — what must exist)*

### 🔴 Blocker
| # | Required Artifact (Must Exist Before Coding) | Status |
|---|---------------------------------------------|--------|
| 1 | **Repo root `package.json` / `pnpm-workspace.yaml`** with workspaces for each fleet (`apps/web-platform`, `packages/narration-engine`, `packages/audio-synthesis`, `packages/shared-ui`) | ❌ Missing |
| 2 | **`tsconfig.json` / `eslint.config.js` / `prettier.config.js`** shared config at root, extended by all packages | ❌ Missing |
| 3 | **Directory skeleton** matching the claimed paths:<br>`departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/`<br>├── `index.html`<br>├── `lesson.css`<br>├── `lesson.js`<br>├── `narration_engine.js`<br>├── `curriculum_index.json`<br>├── `courses/`<br>│   ├── `linear_algebra/`<br>│   │   ├── `lesson_01.html` … `lesson_05.html`<br>│   ├── `calculus/` …<br>│   ├── `differential_equations/` …<br>│   ├── `lockdown_math/` …<br>│   ├── `neural_networks/` …<br>│   └── `probability/` …<br>└── `assets/audio/`<br>    ├── `linear_algebra/lesson_01/`<br>    │   ├── `sec_01.mp3` …<br>    │   ├── `manifest.json`<br>    │   └── `manifest.js`<br>    └── … | ❌ Missing (only governance doc exists) |
| 4 | **`narration_engine.js` TypeScript interface definition** (`packages/narration-engine/src/types.ts`) exposing:<br>- `init(manifestUrl: string): Promise<void>`<br>- `playSection(sectionId: string): void`<br>- `pause(): void`<br>- `on(event: 'sectionstart'|'sectionend'|'karaoke', cb: Fn)`<br>- `destroy(): void` | ❌ Missing |
| 5 | **`manifest.json` JSON Schema** (`packages/narration-engine/schema/manifest.schema.json`) with required fields:<br>`version`, `courseId`, `lessonId`, `sections: [{ id, title, startTime, endTime, audioUrl, text }]` | ❌ Missing |
| 6 | **Lesson HTML template** (`packages/shared-ui/templates/lesson.html`) with all required IDs, data-attributes for sections, script module imports, and CSP nonce placeholder | ❌ Missing |
| 7 | **Shared CSS design tokens** (`packages/shared-ui/src/tokens.css`) for colors, spacing, typography (Bengali font stack), bookmark chip styles (`.bookmark-grid`), pill/banner components | ❌ Missing |
| 8 | **Video asset manifest** convention (`assets/video/<course>/<lesson>/video_bn.mp4`, `video_en.mp4`) + FFmpeg transcode script for Bengali dub | ❌ Missing |
| 9 | **CI pipeline** (`.github/workflows/ci.yml`) running: lint, type-check, unit tests, visual regression (Playwright), offline smoke test (serve `file://`), bundle size check | ❌ Missing |
| 10 | **Audio Synthesis Fleet tooling** — Node script that takes TTS output, segments by section, writes `sec_*.mp3`, generates `manifest.json` + `manifest.js` (UMD/ESM dual) validating against schema | ❌ Missing |

### 🟡 Major
| # | Constraint |
|---|------------|
| 11 | **Bengali font licensing** — confirm `Noto Sans Bengali` or `Hind Siliguri` is bundled/self-hosted (no Google Fonts CDN for offline). |
| 12 | **File:// CORS workaround** — `manifest.js` must be a self-executing IIFE assigning to `window.__LESSON_MANIFEST__` because `fetch('manifest.json')` fails on `file://`. Spec says "preloaded script" but doesn't mandate this pattern. |
| 13 | **Shared component library** — bookmark chips, audio pill, karaoke highlighter should be in `packages/shared-ui` as Web Components or vanilla JS modules, not duplicated per lesson. |
| 14 | **Git hooks** — `husky` + `lint-staged` to enforce boundaries (e.g., Linear Algebra Fleet cannot modify `packages/shared-ui` or `courses/calculus/`). |

### 🟢 Nit
| # | Constraint |
|---|------------|
| 15 | Use `pnpm` workspaces (faster, stricter) over npm/yarn. |
| 16 | Enforce `.editorconfig` for line endings (LF), indent (2 spaces), charset (UTF-8). |

---

## REVIEWER 3: egm-style
*Is the spec precise enough? (unambiguous, measurable, testable)*

### 🔴 Blocker
| # | Ambiguity / Unmeasurable / Untestable |
|---|----------------------------------------|
| 1 | **"Natural educator voice: `bn-BD-PradeepNeural`"** — Not testable. Edge TTS voice availability varies by region/version. Spec must define fallback chain and acceptance criteria (e.g., "SSML `<voice name='bn-BD-PradeepNeural'>` must render without error; fallback to `bn-BD-NabanitaNeural`"). |
| 2 | **"Live karaoke text highlighting"** — Zero spec: word-level vs. sentence-level? Sync tolerance (±ms)? Highlight style (background? underline? color?). No acceptance test possible. |
| 3 | **"Floating audio pill (`#smartAudioPill`), top banner (`🎙️ শিক্ষকের কণ্ঠে শুনুন`), section listen buttons"** — No markup, no CSS, no state machine (playing/paused/loading/error), no keyboard accessibility, no touch target size. "Floating" = where? z-index? Responsive behavior? |
| 4 | **"Sole audio authority rule. Whenever any video plays, teacher narration automatically pauses. Whenever teacher narration plays, all videos pause."** — Race condition undefined: what if both start in same event loop tick? Who wins? Spec needs explicit state machine: `IDLE | VIDEO_PLAYING | NARRATION_PLAYING` with transition rules and 0ms conflict resolution. |
| 5 | **"Bookmark chips MUST wrap to the next line (`flex-wrap: wrap; overflow-x: visible;` or CSS Grid `.bookmark-grid`)"** — "or" gives two valid implementations → visual inconsistency. Pick one and specify exact CSS. |
| 6 | **"YouTube button must strictly be labeled `▶ অরিজিনাল ভিডিও`"** — What about aria-label? Icon-only fallback? Focus style? Disabled state when offline? |
| 7 | **"Default to local Bengali video: `#heroLocalBox` visible and `#heroYtBox` hidden (`display: none;`)"** — `display: none` removes from accessibility tree. Should be `hidden` attribute or `visibility: hidden` + `aria-hidden="true"`? Spec doesn't say. |
| 8 | **Agent boundary table uses "MUST NOT touch" but no enforcement mechanism** — Not machine-checkable. Needs ESLint rule or CI path guard. |
| 9 | **"Audio Synthesis Fleet generates `sec_*.mp3`, `manifest.json`, `manifest.js`. No HTML tampering."** — `manifest.js` format unspecified (CommonJS? ESM? IIFE? global var?). "No HTML tampering" unenforceable without tooling. |
| 10 | **"100% offline file:// support"** — Untestable claim without: test matrix (Chrome/Firefox/Safari/Edge local file), service worker scope, CSP for `file://`, relative path resolution rules. |

### 🟡 Major
| # | Imprecision |
|---|-------------|
| 11 | "Lead Agent (Antigravity)" — "Antigravity" appears nowhere else. Is this a codename, a GitHub handle, a bot? |
| 12 | Course list (Linear Algebra, Calculus, Differential Equations, Lockdown Math, Neural Networks, Probability) — no mapping to 3B1B playlist IDs or YouTube URLs. Fleets can't fetch source material. |
| 13 | "lesson_01.html through lesson_05.html" — assumes exactly 5 lessons per course. What if Calculus has 8? Spec should say "N lessons per course, defined in `curriculum_index.json`". |
| 14 | No i18n strategy — UI strings hardcoded in Bengali (`🎙️ শিক্ষকের কণ্ঠে শুনুন`, `▶ অরিজিনাল ভিডিও`). What if platform adds English/Hindi later? |
| 15 | No error handling spec — network failure loading manifest, audio decode error, video 404, TTS quota exceeded. |

### 🟢 Nit
| # | Style / Consistency |
|---|---------------------|
| 16 | Mixed heading levels: `## 1. ABSOLUTE...`, `## 2. STRICT...` — fine, but numbered headings redundant with `##`. |
| 17 | Emoji in headings (`🎧`, `🎙️`, `▶`) — renders inconsistently across OS. Use text + CSS `::before` for icons. |
| 18 | "Zero Collision" in section title but table says "MUST NOT touch... without permission" — "permission" implies exceptions exist. Contradiction. |

---

## READINESS VERDICT

| Reviewer | Verdict |
|----------|---------|
| egm-implementation-readiness | 🔴 **NO-GO** — 8 blockers, 4 major gaps |
| egm-codebase-details | 🔴 **NO-GO** — 10 required artifacts missing |
| egm-style | 🔴 **NO-GO** — 10 untestable/ambiguous specs |

### OVERALL: 🔴 **NO-GO**

**A developer cannot start coding today.** The document is a governance charter, not an implementation spec.

---

## MINIMUM VIABLE SPEC CHECKLIST (to reach GO)

Before any fleet writes code, the Lead Architect must produce:

1. **`SPEC.md`** (this file expanded) containing:
   - Complete directory tree with every folder/file
   - `narration_engine.js` TypeScript interface + event contract
   - `manifest.json` JSON Schema + `manifest.js` output format (IIFE → `window.__LESSON_MANIFEST__`)
   - Lesson HTML template with all required IDs, data-attributes, module graph
   - CSS design tokens + component styles (bookmark grid, audio pill, banner, karaoke)
   - Video/audio asset naming & location convention
   - State machine for mutual-exclusion audio/video (with timing guarantees)
   - Accessibility requirements (WCAG 2.1 AA) for every component
   - Offline `file://` strategy (CSP, relative paths, service worker optional)
   - Error handling & fallback matrix
   - Performance budgets

2. **Repo scaffold** (items 1–10 in egm-codebase-details 🔴 Blocker table)

3. **CI pipeline** with boundary enforcement (ESLint rule: `no-restricted-paths` per fleet)

4. **Acceptance test suite** (Playwright) covering:
   - Offline load (`file://`) → video plays, narration works, karaoke syncs
   - Mutual exclusion: video play → narration pauses; narration play → video pauses
   - Bookmark wrap at 320px, 768px, 1440px viewports
   - Keyboard navigation of audio pill, section buttons, YouTube toggle
   - Bengali font renders without FOIT/FOUT

5. **Agent onboarding doc** — how to claim a lesson, run dev server, run tests, open PR, get Lead review.

---

*Report generated by EGM Implementation Readiness Reviewer (synthesizer)*  
*D:\0PEN CODE\Dub Studio\web_platform_implementation_readiness_report.md*