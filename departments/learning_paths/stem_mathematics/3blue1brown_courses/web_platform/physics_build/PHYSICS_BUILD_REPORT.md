# Physics course — build & verification report

Status: **13 / 13 lessons verified** (headless Chrome, `channel='chrome'`, `headless=True`, against a threaded range-capable local server on port 8092).

## What was created (new folders only)
- `courses/physics/lesson_01.html` … `lesson_13.html` + `courses/physics/index.html`
- `data/physics/lesson_01.json` … `lesson_13.json` (`course_id: "physics"`, `youtube_id`, Bengali sections/quizzes/figures)
- `assets/audio/physics/lesson_NN/manifest.json` + `manifest.js` (placeholder cues; narrated IDs match DOM exactly)
- `assets/figures/phys_NN/fig_XX.svg` (35 new teaching figures, each with a 2–4 sentence Bengali caption in the figure element)
- `media_vault/physics/lesson_NN/experiments/3b1b_physics_NN_full_dubbed.mp4` (tiny silent placeholder so the required `video-src` resolves; no real dub claimed)
- `physics_build/` (generator, clean content module, verifier, threaded verification server, `verify_report.json`)

No existing lesson, course library, or governance file was modified.

## Official-source grounding
All 13 slugs were fetched from `https://www.3blue1brown.com/lessons/<slug>` and each YouTube ID was confirmed by YouTube oEmbed (HTTP 200, matching title). IDs:
`EmKQsSDlaa4`, `YdOXS_9_P4U`, `hFMaT9oRbs4`, `QCX62YJCmGk`, `aXRTczANuIs`, `KTzGBJPuJwM`, `Cz4Q4QOuoo8`, `MzRCDLre1b4`, `MBnnXbOM5S4`, `xdIjYBtnvZU`, `_UoTTq651dE`, `Cld0p3a43fU`, `Iq1a_KJTWJ8`.

## Verification (per lesson, and course index)
- **0 console errors / 0 page errors** on load and after quiz interaction.
- **Components render exactly once**: search overlay, navbar, hero player, narration banner, bookmarks, TOC, article, watch panel, chapter nav, footer, back-to-top — single instance each; one `.site-nav`; one rendered `.quiz-block` per quiz.
- **Exact L01 script order** (KaTeX → stub → components → extended → main → lesson → narration engine; preloaded manifest first).
- **All content inside custom elements** (`b1b-section`, `b1b-figure`, `b1b-callout`, `b1b-formula`, `b1b-quote`, `b1b-quiz`, `b1b-fullscreen`, `b1b-vector-plane`, etc.).
- **Narrated IDs ↔ manifest parity**: DOM `section` ids (excluding `data-no-narration="true"` elements) equal the keys of both `manifest.json` and `manifest.js`; every section has non-empty cues.
- **Labs/quizzes marked non-narrated**: `data-no-narration="true"` on `sec-visualizer` and every `b1b-quiz`; browser confirms the lab is excluded from narration sections.
- **Quiz click**: every option clicked + “যাচাই করো” pressed; feedback element receives visible text for both quizzes on every lesson.
- **JSON ↔ HTML ↔ manifest parity**: section order/ids, figure counts, quiz counts (2 per lesson), `youtube_id`, `official_url`, and the exact required `video-src` string all match.
- **Links/assets**: all figure files resolve; course index returns 200 with 13 chapter rows and 0 errors.

Full machine-readable evidence: `physics_build/verify_report.json`.

## Limits / what is placeholder
- Teacher audio manifests contain generated placeholder timing text only — no claim of studio expressive audio.
- Dubbed videos are 1-second silent placeholders; real dubbing is out of scope for this task.
- Figures are newly generated schematic SVGs, not the original 3B1B animation frames.
