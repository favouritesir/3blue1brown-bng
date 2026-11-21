# Why Pi (কেন পাই) — new component-based Bengali course

Status: **BUILT + VERIFIED (headless Chrome, `channel='chrome'`, `headless=True`)**.
Verification ran on `http://localhost:8085/...` and exited 0. Full machine-readable
result: `build_why_pi/verify_report.json`.

## New folders only (no existing lesson/library file touched)
Base: `departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/`

- `courses/why_pi/` — `index.html` + `lesson_01.html` … `lesson_08.html`
- `data/why_pi/` — `lesson_01.json` … `lesson_08.json` (`course_id: "why_pi"`)
- `assets/audio/why_pi/lesson_NN/` — `manifest.json`, `manifest.js` (placeholder,
  defines `window.TEACHER_AUDIO_MANIFEST`), plus silent placeholder mp3s
- `assets/figures/why_pi/lesson_NN/` — 25 labelled SVG figures
- `media_vault/why_pi/lesson_NN/experiments/3b1b_why_pi_NN_full_dubbed.mp4` — 8 tiny
  valid placeholder MP4s (so no 404 / missing-video errors)
- `build_why_pi/` — generator + verification scripts + this report

## 8 lessons (official 3B1B slugs from `governance/topic_lesson_map.json → why-pi`)
| # | slug | Title (BN / EN) |
|---|------|-----------------|
| 01 | clacks | একটি গণনার ধাঁধার সবচেয়ে অপ্রত্যাশিত উত্তর / The most unexpected answer to a counting puzzle |
| 02 | colliding-blocks-v2 | সংঘর্ষরত ব্লকরা কীভাবে পাই গণনা করে / Why colliding blocks compute pi |
| 03 | clacks-via-light | সংঘর্ষরত ব্লকরা আলোর রশ্মির মতো আচরণ করে / How colliding blocks act like a beam of light |
| 04 | basel-problem | পাই কেন এখানে? আর কেন তার বর্গ? / A geometric answer to the Basel problem |
| 05 | leibniz-formula | মৌলিক সংখ্যার নিয়মিততায় লুকোনো পাই / Pi hiding in prime regularities |
| 06 | gaussian-integral | স্বাভাবিক বণ্টনে পাই কেন? / Why π is in the normal distribution |
| 07 | wallis-product | ওয়ালিস গুণফল — একটি জ্যামিতিক প্রমাণ / The Wallis product for pi |
| 08 | pi-was-628 | পাই প্রায় ৬.২৮৩১৮৫… হতে পারত / How pi was almost 6.283185 |

## Verification results (all 8 + index)
- **0 errors**: 0 console errors, 0 page exceptions on every lesson and the index.
- **Components once**: every custom element on the page is registered
  (`customElements.get(tag)`); all 11 singleton components appear exactly once;
  rendered quiz-block count equals the `b1b-quiz` host count (no double render).
- **Quiz click**: on every lesson the first quiz option + “যাচাই করো” was clicked and
  the feedback became visible with the correct `correct-fb`/`wrong-fb` state.
- **Parity with gold `courses/linear_algebra/lesson_01.html`**: identical set of 21
  `b1b-*` component tags on every lesson; same strict script load order; same
  `video-src` shape at the required `media_vault/why_pi/...` path.
- **Narrated-ID parity**: DOM narrated section ids == manifest `sections` keys for
  every lesson; `manifest.js` is byte-for-byte the same object as `manifest.json`.
- **Data**: each JSON has `course_id: why_pi`, ≥3 sections with figures/formulas,
  and ≥1 quiz.

KaTeX rendered 21–51 formulas per lesson; 2–4 figures rendered per lesson.
Browser-level Chrome warnings (e.g. WebGPU `powerPreference`) were not counted as
application errors — only `console.error` and uncaught exceptions were.
