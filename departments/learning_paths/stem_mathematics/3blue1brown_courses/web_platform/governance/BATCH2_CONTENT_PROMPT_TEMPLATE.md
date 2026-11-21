# Batch 2 content agent prompt template (copy & fill {TOPIC})

Build component-based Bengali lesson pages for ALL lessons of official 3B1B "{TITLE}" topic as a NEW course. New folders only; don't touch existing lessons/library.
READ: `governance/topic_lesson_map.json` key `{KEY}` (slugs: {SLUGS}). Gold: `courses/linear_algebra/lesson_01.html`. Rules: `governance/COMPONENT_FIRST_PIPELINE.md` rule 6. Official: `https://www.3blue1brown.com/lessons/<slug>` (webfetch); YouTube IDs via oEmbed from official page.
FOR EACH slug: (1) `data/{DIR}/lesson_NN.json` (course_id='{DIR}', natural Bengali sections/quizzes/figures, official youtube_id); (2) `courses/{DIR}/lesson_NN.html` exact L01 components/script order, all content in custom elements, narrated IDs match NEW `assets/audio/{DIR}/lesson_NN/manifest.json`+js (placeholder fine), non-narrated labs/quizzes data-no-narration=true, video-src `../../media_vault/{DIR}/lesson_NN/experiments/3b1b_{DIR}_NN_full_dubbed.mp4`; (3) `courses/{DIR}/index.html`.
VERIFY all in headless Chrome channel=chrome: 0 errors, components once, quiz click, parity. Report. Don't claim unless verified.

## Queue (launch one per free slot)
| Topic | Key | Data dir | Slugs |
|---|---|---|---|
| Computer Science | computer-science | computer_science | entropy, cross-entropy, arithmetic-codes, wordle, wordle-2, bitcoin, 256-bit-security, epidemic-simulations, hamming-codes, hamming-codes-2, grover, grover-clarification, hanoi-and-sierpinski |
| Guest Videos | guest-videos | guest_videos | diffusion-models, incomplete-cubes, phase-change, alpha-geometry, euclid |
| Talks | talks | talks | harvey-mudd-speech, tedx-talk, transformers-talk, pedagogical-curse, ego-and-math |
| Videos Elsewhere | videos-elsewhere | videos_elsewhere | bertrands-paradox, hyperdarts, prime-number-race, feynmans-lost-lecture, image-convolution, seam-carving, discrete-fourier-transform, diffusion-equation |
| Best Of | best-of | best_of | (14 slugs — mostly overlap other topics; can be a curated local index linking to existing lessons instead of duplicates) |
