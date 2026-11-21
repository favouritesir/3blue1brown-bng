# Analysis course — build & verification report

## Scope
New course only. Nothing in the existing 53-lesson library / shared assets was modified.
Source of truth: `governance/topic_lesson_map.json` → `analysis` (10 slugs).
Reference page: `courses/linear_algebra/lesson_01.html` (component set, script load order, navbar/hero/watch/footer).
Metadata: official `https://www.3blue1brown.com/lessons/<slug>` pages (titles, dates, YouTube IDs).

## Created (all new folders)
- `data/analysis/lesson_01.json` … `lesson_10.json` — `course_id="analysis"`, natural Bengali prose, epigraph, 4 sections each, formulas, figures, 2 quizzes each, official URL + video ID.
- `courses/analysis/lesson_01.html` … `lesson_10.html` — exact L01 components (search overlay, navbar, hero player with the required `video-src`, bookmarks, TOC, article sections with quote/p/figure/callout/formula/quiz, watch panel, chapter nav, footer, back-to-top).
- `courses/analysis/index.html` — 10 chapter rows, course title «বিশ্লেষণ».
- `assets/audio/analysis/lesson_NN/manifest.json` + `manifest.js` — 4 narrated sections per lesson, 224 cues total; IDs match the HTML section IDs 1:1.
- `assets/figures/an_01` … `an_10` — 35 SVG figures referenced by `<b1b-figure>`.
- `media_vault/analysis/lesson_NN/experiments/3b1b_analysis_NN_full_dubbed.mp4` — required paths.
- Build/verification sources: `analysis_build/build_analysis.py`, `content.py`, `content2.py`, `verify_analysis.py`, `verify_result.json`.

Placeholders (explicit): narration MP3s are silent and the MP4s are 1-second black clips. They exist so the required paths resolve with zero 404s; they are not real dubs.

## Verification — headless Chrome (`channel="chrome"`, `headless=True`)
Run: `python analysis_build/verify_analysis.py` against `http://127.0.0.1:8085` (range-capable static server).
Raw result: `analysis_build/verify_result.json`.

| Lesson | Slug | Page errors | Console errors | 4xx | Parity | Components once | Quiz clicks | Result |
|---|---|---:|---:|---:|---|---|---|---|
| 01 | zeta | 0 | 0 | 0 | pass | pass | 2/2 correct + 2/2 wrong | OK |
| 02 | print-gallery | 0 | 0 | 0 | pass | pass | 2/2 + 2/2 | OK |
| 03 | fourier-transforms | 0 | 0 | 0 | pass | pass | 2/2 + 2/2 | OK |
| 04 | uncertainty-principle | 0 | 0 | 0 | pass | pass | 2/2 + 2/2 | OK |
| 05 | fourier-series | 0 | 0 | 0 | pass | pass | 2/2 + 2/2 | OK |
| 06 | borwein | 0 | 0 | 0 | pass | pass | 2/2 + 2/2 | OK |
| 07 | convolutions | 0 | 0 | 0 | pass | pass | 2/2 + 2/2 | OK |
| 08 | winding-numbers | 0 | 0 | 0 | pass | pass | 2/2 + 2/2 | OK |
| 09 | inventing-math | 0 | 0 | 0 | pass | pass | 2/2 + 2/2 | OK |
| 10 | music-and-measure-theory | 0 | 0 | 0 | pass | pass | 2/2 + 2/2 | OK |
| index | — | 0 | — | 0 | 10 rows, correct hrefs | — | — | OK |

Checks performed per lesson:
- `pageerror` + console `error` + HTTP ≥400 listeners attached before navigation; all empty.
- `article.article` and `b1b-article` appear exactly once; each `b1b-*` host has exactly one rendered wrapper (quiz/callout/figure/formula/quote/section); navbar, hero, watch panel, TOC, footer once.
- Quiz: for every quiz, clicked the correct option → `✅ correct-fb`; reloaded, clicked a wrong option → `❌ wrong-fb` (20 quizzes × 2 paths = 40 successful click assertions).
- Parity: DOM section IDs == `manifest.json` keys == `manifest.js` keys == narration-engine IDs; per-section cue-type sequence (h2, p, chapter-quote, callout, figure, formula-box) matches the DOM block sequence exactly; engine block count == cue count; `manifest.js` deep-equals `manifest.json`.
- `course_id="analysis"`, `official_url` matches the slug, exactly 2 quizzes per data file, and hero/watch `video-src` equals the required analysis path.

Result: **10/10 lessons OK, index OK — all claims above verified, not assumed.**
