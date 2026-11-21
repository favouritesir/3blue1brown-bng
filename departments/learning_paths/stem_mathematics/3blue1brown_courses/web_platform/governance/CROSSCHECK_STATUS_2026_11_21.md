# Cross-check status — 2026-11-21 (user-reported bookmark/content mismatch)

## What the user found (VALID)
Screenshot showed stale bookmarks (01:04, 02:20, 02:38) that did not match the video content. Investigation confirmed:
- Lockdown L02 bookmarks were 820s/1695s/2630s/3500s while its video is only 536s — from an OLD 1-hour calendar-puzzle page. Manifest section IDs were also stale (`sec-calendar-puzzle` etc.; audio texts were later rewritten to exponential-growth but IDs/bookmarks were not).
- We had only verified structure parity, never CONTENT↔TIME alignment. User is right.

## Fixed
- `fix_bookmarks_v3.py`: ALL 112 lesson pages' bookmarks regenerated from FINAL manifest section timings, SCALED to actual video duration (manifest audio span may differ from final video). Overflow bookmarks eliminated. Verified LA L01 now max 08:11 within 09:51 video; L02 within 09:59 ✅.
- Manifest still has legacy section IDs on a few pages (cosmetic, no functional impact); audio texts are correct.

## Full cross-check (`full_crosscheck.py`) — current accurate state
15 courses, 112 lessons:
- **Audio**: real expressive audio on ALL lessons except physics (audio agent still running, 3/13 done) ✅
- **Video real**: LA 15/15, calc 11/12, NN 4/4, DE 4/6, group-theory 2/2, number-theory 3/3, lockdown 9/10, probability 5/6, fractals 3/4, why-pi 1/8
- **Video placeholder/pending**: analysis 0/10, geometry 0/6, puzzles 0/10, physics 0/13, topology 0/3, why-pi 7/8 — video agents running or queued
- **No-official-video pages** (intentionally no video): calc L12, DE L03/L06, prob L05, lockdown L10

## Tracker
`completed_lessons.json` = 62 (53 original + 9 new with real audio+video: fractals L01/L03/L04, group-theory L01/L02, number-theory L01-L03, why-pi L01). `board_data.json` regenerated: 15 courses, 62 completed, 50 under_review. New lessons are added ONLY when both real audio and real video exist.

## Still to verify (HONEST GAP)
**Content↔video semantic alignment** at matching timestamps: our dubbed audio is generated from manifest cue texts (authored from official articles) and placed with recomputed scale; the original video at the same second may be discussing a different sub-topic. A true cross-check requires comparing original-video subtitles (yt-dlp auto-subs) with our narration text at the same timestamp. This has NOT been done yet and must be done before claiming "zero bugs".
