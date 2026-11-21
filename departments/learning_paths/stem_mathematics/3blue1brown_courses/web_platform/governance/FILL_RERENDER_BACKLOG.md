# Dub-fill re-render backlog

`audit_fill_policy.py` (2026-11-20) scanned all 26 `verification.json`. Result:

## Already compliant (new pipeline with improved fill policy)
- calculus L08: fill 0.9994, gap 0.03s ✅
- calculus L09: fill 0.928, gap 1.18s ✅
- probability L01: fill 0.883, gap 1.27s ✅
- calculus L10: first pass fill 0.494 → **agent is re-rendering with corrected metric** (in progress)

## Need re-render AFTER main 53-lesson migration completes
23 older videos have NO `median_fill` recorded (old pipeline). Any with
`timeline_scale > 1.5` almost certainly has silent pockets (pad-only, atempo>=1.0):

Linear Algebra (all 15): L01 scale 2.82, L02 ?, L03 1.71, L04 0.92(may be ok), L05 2.13,
L06 2.02, L07 1.74, L08 1.43, L09 2.73, L10 ?, ... — re-render with atempo floor 0.82.
Calculus: L01 (3.09), L02 (1.71), L03 (2.63), L04 (2.04), L05 (2.09), L06 (1.69), L07 (2.21).
Neural L01 (1.64).

## Action
When all lessons have content+video+audio and tracker is 53/53, spawn a dedicated
batch of re-render agents (8 parallel) using `IMPROVED_DUB_FILL_POLICY.md`, one per
lesson, writing to `experiments/fill_v2/` (NEW folder — never overwrite working versions),
verify ffprobe full duration + median_fill>=0.72, then swap video-src to the new file
ONLY after verification. Keep old dubbed videos as backups under `experiments/`.
