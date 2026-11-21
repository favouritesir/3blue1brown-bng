# Pending video-src swaps (do after video agents finish)

These pages were migrated before their dubbed video existed, so they use a
placeholder or wrong path. Swap to the real experiment file when ffprobe confirms.

| Lesson | Current (wrong/placeholder) | Replace with |
|---|---|---|
| calculus L08 | `data:video/mp4;base64,...` (self-contained tiny placeholder) | `../../media_vault/calculus/lesson_08/experiments/3b1b_calculus_08_full_dubbed.mp4` |
| calculus L10 | DONE — fixed to `3b1b_calculus_10_full_dubbed.mp4` (2026-11-20) | — |

After each swap, re-run `governance/audit_video_src.py` → expect 0 missing (data URIs still flagged benignly).
