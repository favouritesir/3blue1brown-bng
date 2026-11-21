# improve_fill_policy.md — video dub speech-fill fix (applies to ALL future lessons)

## Problem
Master scripts author ~600 s of Bengali cues, but source videos are ~900–1100 s.
The pipeline scales cue windows (e.g. 1.64×–3.08×) to span the full video.
With `atempo >= 1.0` pad-only, speech fills only ~53% of each stretched window
→ long silent pockets mid-lecture (agent measured ~47% silence, ~3 s gaps).

## Fix — apply in every build_lXX_clean.py from now on
1. **Allow gentle slowdown**: replace `tempo = max(1.0, min(2.2, natural/target))`
   with `tempo = max(0.82, min(2.2, natural/target))`.
   - 0.82× is only ~18% slower — still natural Bengali, removes most dead air.
   - Keep atempo <= 2.2 ceiling (no chipmunk voice).
2. **Pad remainder only** after slowdown. Never truncate speech.
3. **Expansion first**: for cues where natural speech < 60% of the (scaled) target
   even at 0.82×, expand the Bengali script with 1–2 extra pedagogical sentences
   (what to notice / why it matters) before synthesis — this improves teaching quality AND fill.
4. **Measure fill ratio** after render: per cue, `speech_samples / window_samples`;
   median should be >= 0.72 and no single gap > 1.5 s inside a cue window.
   Record `median_fill` and `max_internal_gap_s` in verification.json.
5. Keep: absolute sample placement `start*44100`, NO SFX, loudnorm -14,
   full-video canvas padding before `-shortest`, lightweight volumedetect.

## Existing lessons needing later re-render (fill ratio < 0.72)
- neural_networks/lesson_01 (measured 0.53 by video agent)
- Any lesson whose verification.json shows `timeline_scale > 1.5` with pad-only tempo >= 1.0:
  calculus L01 (3.09×), L02 (1.71×), L03 (2.63×), L04 (2.04×), L05 (2.09×),
  L06 (1.69×), L07 (?), LA L08–L15 (various).
These remain functional (no cut, correct sync) but may have audible silent pockets.
Re-render with the improved policy when the main migration is complete.

---
Add this rule to `governance/COMPONENT_FIRST_PIPELINE.md` section 3 table.
