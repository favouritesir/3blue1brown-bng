# Alignment-preserving dub pipeline (fix for systematic content↔time drift)

## Problem (confirmed 2026-11-21)
`check_alignment_drift.py`: 97/102 lessons have >60s drift between final cue placements and ORIGINAL master-script cue times (max 1420s). Root cause: "scale recomputed from rendered speech" places cues contiguously, discarding original `start` times. At time T, Bengali narration often discusses a different sub-topic than the video shows.

## Correct approach
1. Load original master script (`.../dubbing_pipeline/3b1b_*_bangla_master_script.json`) with authoritative `start`/`end`/`bn` per cue.
2. TTS each cue's `bn` text (edge-tts bn-BD-PradeepNeural, robust retries).
3. For each cue window `[start, end]`:
   - natural speech ≤ window → place at `start*44100`, pad remainder (gap ≤ 1.5s target; if larger, EXPAND that cue's text with 1–2 extra pedagogical sentences about the SAME sub-topic and re-synth, still within window).
   - natural speech > window → atempo up to 2.2 (`atempo=min(2.2, natural/window)`); if still > window, split/shorten text (never truncate audio).
4. Absolute sample placement at ORIGINAL start (never recompute contiguous scale).
5. Full-video canvas padding before `-shortest`; loudnorm -14; NO SFX; `-c:v copy`.
6. Verify: ffprobe full duration, internal silent runs>2s == 0, **max drift vs master script <= 2 frames** (this is the NEW mandatory gate).

## Pilot
`build_aligned_la01.py` — Linear Algebra L01 (98 master cues, original 591s video). Will write to `experiments/aligned_v2/` (never overwrite working video). After pilot passes drift gate, apply to all lessons in batches.

## Tracker honesty
Lessons re-rendered with aligned pipeline get a `fill_v2`/`aligned_v2` marker in verification.json; until re-rendered, drift remains (documented in CROSSCHECK_STATUS_2026_11_21.md).
