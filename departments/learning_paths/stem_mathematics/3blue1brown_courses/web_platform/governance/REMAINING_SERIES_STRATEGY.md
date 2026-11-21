# Remaining series strategy (after current batch)

## Probability (data authoritative; ids verified via oEmbed)
- L03 `8idr1WZ1A7Q` Binomial distributions part 1 ✅ notes ready
- L04 `ZA4JkHKZM50` "probability of 0 ≠ impossible" part 2 ✅ (verified)
- L05 `i3AkTO9HLXo` = Normalized Nerd (NOT 3B1B) ⚠ NO official video exists → build content page from data JSON; video phase: disclose third-party source OR skip dubbed video (parity rule). See VIDEO_ID_DATA_QUIRKS.md.
- L06 `zeJD6dqJ5lo` But what is the CLT? ✅ (verified earlier)

## Differential Equations — 6 lessons, only 4 official 3B1B videos
- L1 `p_di4Zn4wz4` (tourist's guide / unsolvable) ✅
- L2 `ly4S0oi3Yz8` (partial DE) — id fixed
- L3 Oscillations/Damping — NO official 3B1B video → **content + audio ONLY + disclose** (do NOT launch a video agent; no dubbed video; excluded from verify_completed_artifacts video check)
- L4 `ToIXSwZ1pJU` (solving heat equation) ✅
- L5 `r6sGWTCMz2k` (Fourier series) — id fixed
- L6 Wave equation — NO official 3B1B video → **content + audio ONLY + disclose** (same as L3; excluded from video check)
All content authoritative from `data/differential_equations/lesson_XX.json`.

## Lockdown Math — 10 lessons, IDs FIXED 2026-11-20 (top-level + meta both set via fix_lockdown_ids.py)
- L1 `MHXO86wKeDY` (was wrong `ZA4JkHKZM50` = probability part2) — verified "simpler quadratic formula Ep1"
- L2 `Kas0tIxDvrg`, L3 `bT1p5tJwn_0`, L4 `5PcpBw5HbWo`, L5 `mvmuCPvRoWQ`, L6 `d_bZk5f2Z8Y`, L7 `b3NxrZOup_U`, L8 `d-o3eB9sfls`, L9 `fNk_zzaMoSs`, L10 `LqbZpur38nw`
- Still oEmbed spot-check each before its video agent (IDs came from data; only L1 independently verified).

## Neural Networks
- L03 `Ilg3gGewQ5U` backpropagation ✅ notes ready
- L04 `tIeHLnjs5U8` backprop calculus ✅ notes ready

## Universal rules for all remaining
- Phase 1: component page from data JSON + official notes; narrated IDs = manifest keys; DOM↔manifest parity; quiz click; 0 errors.
- Phase 2: video via improved fill policy (atempo floor 0.82, median_fill>=0.72), verify ffprobe full duration.
- Phase 3: expressive audio via gold builders, verify 1:1, 0 "চিত্র প্রদর্শনী".
- After each: swap video-src, update completed_lessons.json, regenerate board_data.json.
- Reuse `governance/verify_lesson_page.py`, `verify_completed_artifacts.py`, `audit_video_src.py`, `regression_audit.py`.


## Lockdown L02 discrepancy (FIX via expressive audio rebuild)
- `assets/audio/lockdown_math/lesson_02/manifest.json` (and .js) held STALE calendar-puzzle/modular-arithmetic content (4 narrated sections: sec-calendar-puzzle, sec-clock-modulo, sec-leap-years, sec-doomsday-trick; 13 cues) — NOT the exponential-growth/epidemics topic from the authoritative `data/lockdown_math/lesson_02.json`.
- Component page was built with those 4 calendar-themed narrated IDs (to keep DOM↔manifest parity) + 5 data-ID study sections carrying the real exponential-growth content.
- FIX: expressive audio builder MUST extract the LIVE DOM narrated IDs (the 4 calendar-themed ones) but write scripts about the ACTUAL exponential-growth content shown in those sections (linear vs exponential, doubling time, SIR model, logistic curve, flattening the curve). Keep section IDs/audio_file names; regenerate manifest ✓. After rebuild, manifest texts = exponential-growth topic (no stale calendar text). Flag any residual calendar text.
