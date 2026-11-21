# Final regression plan — run when all 53 lessons are completed

## Gate 0 — Tracker integrity
- `verify_completed_artifacts.py` → expect 53 completed, 0 problems.
- `board_data.json` → 53 completed = tracker; homepage + board HTTP 200.
- 6 courses board row counts: LA 15, Calc 12, Neural 4, Prob 6, DiffEq 6, Lockdown 10.

## Gate 1 — Static audits
- `regression_audit.py` → all component pages, 0 issues (script order, manifest, narration engine last).
- `audit_video_src.py` → 0 unexpected missing (only the 6 no-official-video pages: calc L12, prob L05, DE L03/L06, lockdown L10 — plus DE? verify).
- `audit_expressive_audio.py` → 53 manifests, 0 FORBIDDEN labels, 0 missing backups.

## Gate 2 — Live browser spot-check (Playwright channel=chrome, http://127.0.0.1:8085)
One page per course: linear_algebra/L01, calculus/L01, neural_networks/L01,
probability/L01, differential_equations/L01, lockdown_math/L01.
Check: 0 page errors, 0 console errors (except expected offline media),
components once, quiz click feedback, navbar stepper total matches B1B_COURSES,
theme toggle, teacher narration pill play/pause, keyboard shortcuts (←/→/space).
Also one mobile viewport (390×844) check: stepper not clipped.

## Gate 3 — Fill re-render backlog (23 old videos)
Source: `FILL_RERENDER_BACKLOG.md`. After 53/53, spawn 8 parallel re-render agents
with IMPROVED_DUB_FILL_POLICY into `experiments/fill_v2/` (NEVER overwrite working).
Verify each: ffprobe full duration + median_fill>=0.72 + max_internal_gap<=1.5s.
Swap video-src ONLY after verification. Keep old as backup.
Priority order (highest first): videos with timeline_scale>2.0 and no median_fill recorded:
calc L01 (3.09), L03 (2.63), L07 (2.21), L05 (2.09), L04 (2.04),
LA L01 (2.82), L09 (2.73), L10, L05 (2.13), L06 (2.02), L15 (2.82),
neural L01 (1.64), etc.
NOTE: this is an enhancement, not a blocker for 53/53 completion — user's "zero bugs"
target includes audible silent pockets, so it must be done before final report.

## Gate 4 — Cleanup
- Delete `.bak_pre_component` legacy static files ONLY after component replacements verified.
- Keep all backups of videos/manifests; do not destroy working versions.
- Update PROGRESS_SNAPSHOT to 53/53 and final review artifact `LESSON_01_FINAL_REVIEW.md`-style
  report for the whole site.
