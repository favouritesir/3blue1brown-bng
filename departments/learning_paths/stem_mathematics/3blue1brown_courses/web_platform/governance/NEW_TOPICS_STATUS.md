# New topic expansion (user request 2026-11-21: "সব টপিকের local পেজ বানাই")

## Source of truth
- Official 3B1B sitemap: 178 lesson URLs
- Official topic→lesson map extracted from site bundle `Header-qk6vXxWo.js` → `governance/topic_lesson_map.json` (20 topics, 157 unique slugs)

## Delivered already
- **20 local topic landing pages** at `courses/topics/<key>.html` (all official lessons listed with official links), linked from homepage (#topic-collections local library). Verified: 20/20 HTTP 200, correct lesson counts, 20 homepage links ✅.

## Full treatment — batch 1 (8 content agents, 46 lessons)
**Batch 1 ALL CONTENT DONE (46 lessons)**: topology(3), fractals(4), number-theory(3), group-theory(2), geometry(6), puzzles(10), why-pi(8), analysis(10).
**Batch 2 STARTED**: physics(13) CONTENT DONE ✅ (13/13 live verified). Remaining content: computer-science(13), guest-videos(5), talks(5), videos-elsewhere(8), best-of(overlap).
Physics audio batch RUNNING (13 lessons); video pending.
Each agent: data JSON + component lesson page + placeholder manifest + topic index. Verify with headless Chrome.

## Video phase started
- group_theory: 2 lessons — video batch RUNNING (official IDs verified, fill-gate pipeline)
- number_theory: 3 lessons — video batch RUNNING (audio DONE ✅)
- fractals: 4 lessons — video batch RUNNING (audio DONE ✅)
- geometry: 6 lessons — video batch RUNNING (audio DONE ✅)
- why_pi: 8 lessons — video batch RUNNING (audio DONE ✅; IDs resolved from official slugs by agent)
- topology: 3 lessons — video batch RUNNING (audio DONE ✅; pages currently 404 for video, this fixes)

## Audio phase started
- fractals: 4 lessons — audio batch RUNNING
- group_theory: 2 lessons — audio batch RUNNING
- number_theory: 3 lessons — audio batch RUNNING
- geometry: 6 lessons — audio batch RUNNING
- puzzles: 10 lessons — audio batch RUNNING
- why_pi: 8 lessons — audio batch RUNNING
- topology: 3 lessons — audio batch RUNNING
- analysis: 10 lessons — audio batch RUNNING (8 audio batches total, batch 1 audio complete once these finish)
Next: video agents for fractals/group_theory; audio+video for remaining content batches as they complete.

## Remaining after batch 1 (≈29 lessons + overlaps)
physics(13), computer-science(13), guest-videos(5), talks(5), videos-elsewhere(8), best-of(14 — overlaps other topics; may only need landing page/links).
Also: existing 6 series can be expanded to full official counts (LA 15→16, Calc 12→17, NN 4→11, Prob 6→9, DE 6→10, Lockdown 10→11) in a later batch if desired.

## Pipeline per topic after content
1. Content agent → component page + data JSON + placeholder manifest
2. Expressive audio agent (gold standard, rebuild manifest, phonetic safeguards)
3. Video agent (official YouTube ID from lesson page, fill policy, quality gate, mux)
4. Swap video-src from placeholder to final experiment file; update tracker/board/curriculum
5. Verify all audits green

NOTE: use `serve_range.py 8085` (not `python -m http.server`) for bookmark seeking to work.
