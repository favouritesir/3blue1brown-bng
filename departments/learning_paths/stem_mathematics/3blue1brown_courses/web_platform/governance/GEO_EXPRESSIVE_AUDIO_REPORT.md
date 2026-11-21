# Geometry Course — Expressive Teacher Narration Audio (Gold Standard)

**Scope:** `courses/geometry/lesson_01.html` … `lesson_06.html` only (new/this course).
**Voice:** `bn-BD-PradeepNeural` · **Gap:** 350 ms · **Builders:** `build_expressive_teacher_audio_geo01.py` … `geo06.py`
**Verification:** `verify_geo_expressive_build.py` — headless Chrome `channel="chrome"`, live HTTP (port 8085).

## Per-lesson results

| Lesson | Cues | Sections | Duration | Figures | DOM↔manifest | Verification |
|---|---:|---:|---:|---:|---|---|
| 01 — Sphere surface area | 37 | 6 | 446.43 s (07:26) | 7 | 1:1 | PASSED — all green |
| 02 — Conic sections / Dandelin | 29 | 6 | 337.79 s (05:38) | 5 | 1:1 | PASSED — all green |
| 03 — Higher-dimensional spheres | 26 | 6 | 277.43 s (04:37) | 4 | 1:1 | PASSED — all green |
| 04 — Quaternions / 3-sphere | 27 | 6 | 330.34 s (05:30) | 5 | 1:1 | PASSED — all green |
| 05 — qvq⁻¹ rotation formula | 25 | 6 | 262.54 s (04:23) | 3 | 1:1 | PASSED — all green |
| 06 — Dimensions / tesseract / 10D | 26 | 6 | 283.82 s (04:44) | 4 | 1:1 | PASSED — all green |
| **TOTAL** | **170** | **36** | **1938.34 s (32:18)** | **28** | **1:1** | **ALL 6 GREEN** |

### Per-section cue counts (exact DOM order)

- **L01** sec-intro 7, sec-cylinder-label 8, sec-archimedes 6, sec-shadow 8, sec-general 5, sec-conclusion 3
- **L02** sec-intro 6, sec-cone-setup 4, sec-dandelin 5, sec-proof 7, sec-other-conics 4, sec-conclusion 3
- **L03** sec-intro 5, sec-volume 6, sec-concentration 5, sec-curse 3, sec-paradox 4, sec-conclusion 3
- **L04** sec-intro 7, sec-complex 4, sec-stereographic 5, sec-visualize 4, sec-why 4, sec-conclusion 3
- **L05** sec-intro 4, sec-axis-angle 4, sec-formula 7, sec-double-cover 4, sec-interpolation 3, sec-conclusion 3
- **L06** sec-intro 5, sec-dimension 4, sec-hypercube 6, sec-flatland 4, sec-physics 4, sec-conclusion 3

> Note: live DOM has one extra `chapter-quote` in each `sec-intro` versus the old placeholders;
> new manifests follow the **live DOM** (authoritative), which is what the browser audits against.

## Steps completed (per lesson 01–06)

1. Placeholder `manifest.json` + `manifest.js` backed up to
   `assets/audio/geometry/lesson_NN/_backup_before_expressive_build/`.
2. Live DOM extracted via narration-engine selector in headless Chrome `channel="chrome"`
   with KaTeX `<annotation>` markers → `governance/geoNN_dom_blocks.json` (0 page errors).
3. Expressive phonetic Bengali scripts embedded for every cue: figure cues are 2–4 sentence
   natural explanations; no artificial `চিত্র প্রদর্শনী` label; safeguards applied
   (গোলক, ক্ষেত্রফল, পৃষ্ঠ, আয়তন, কোয়াটার্নিয়ন, মাত্রা, ঘূর্ণন, শঙ্কু, ড্যান্ডেলিন, …).
   Prosody: h2 −5%/+2Hz, chapter-quote −3%, p +2%, figure −4%, callout +0%, formula-box −8%, conclusion −3%.
4. MP3s synthesized with robust retries; real 350 ms silence chunks; per-section `ffmpeg -c copy` concat.
5. New `manifest.json` + `manifest.js` (`window.TEACHER_AUDIO_MANIFEST`) with measured ms timings,
   exact DOM ids/counts/types, and original `sec_0N_<section-id>.mp3` filenames.
6. Page cache-buster bumped `manifest.js?v=7` → `?v=8` on all six lesson pages.
7. Builder written: `governance/build_expressive_teacher_audio_geoNN.py`.

## Verification checklist (all six, headless Chrome channel=chrome)

- `window.TEACHER_AUDIO_MANIFEST` valid JSON on disk and in browser, byte-identical
- section keys == the 6 canonical DOM ids; no alias/extra keys
- DOM ↔ manifest 1:1 per section (types + counts, in order), runtime engine binding aligned
- 0 duplicate DOM cue texts, 0 duplicate spoken manifest texts
- 0 quiz / media-tab cue types; 0 `চিত্র প্রদর্শনী` labels; 0 Latin/markup/em-dash in speech
- every MP3 HTTP 200 + non-zero on disk + positive ffprobe duration ≈ manifest total
- cue timings positive, 0 overlaps, exact 350 ms gaps, totals match last cue end
- 0 page errors, backup folder present

**Full machine output:** `governance/_geo_verify.log` (and `_geo0N_build.log`).
