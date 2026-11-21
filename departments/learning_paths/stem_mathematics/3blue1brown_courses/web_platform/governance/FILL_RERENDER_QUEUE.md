# Fill re-render queue (Gate 3) — verified via detect_silent_pockets.py

## Completed/Launched batch 1 (8 agents)
- calculus L01 (29 pockets max 72s) ✅ launched
- calculus L02 (59 max 12s) ✅ launched
- calculus L03 (36 max 26s) ✅ launched
- calculus L04 (41 max 19s) ✅ launched
- calculus L05 (42 max 14s) ✅ launched
- calculus L06 (40 max 17s) ✅ launched
- calculus L07 (43 max 19s) ✅ launched
- neural_networks L01 (48 max 18s) ✅ launched

## Progress: 6/22 SWAPPED (Calc L01/L03/L04/L05/L07, Neural L01)
## Batch 2 LAUNCHED: LA L11/L12/L13/L14/L15 (+ Calc L02/L06 still in batch 1)
## Batch 3 (remaining after these): LA L02/L03/L04/L05/L06/L07/L09/L10 + Calc L10
All LA videos use `media_vault/lesson_XX/3b1b_lesson_XX_full_dubbed.mp4` (except L01 uses bangla_dubbed_video.mp4 — has 4 pockets incl 11s lead-in; L01 v2 file has only 2 pockets max 3s → could just swap to v2 as cheap win).
- LA L02 (19 max16) · L03 (36 max12) · L04 (28 max11) · L05 (11 max14) · L06 (33 max12) · L07 (34 max18) · L09 (33 max18) · L10 (33 max8) · L11 (25 max34) · L12 (26 max26) · L13 (30 max20) · L14 (24 max41) · L15 (23 max43)
- calculus L10 (20 max18)
- LA L01: swap video-src to existing `_v2.mp4` (2 pockets max3s) instead of full re-render (cheap win).
- LA L08: OK (2 pockets max3s) — no action.

## Method
Each agent: copy quality-gated script → NEW `experiments/fill_v2/` → heavy expansion → recompute scale from rendered speech → fill gate median_fill>=0.72 + max_internal_gap<=1.5s → output `*_fill2.mp4`. Parent verifies ffprobe + detect_silent_pockets (internal runs>2s == 0) → swaps video-src → updates tracker if needed.
