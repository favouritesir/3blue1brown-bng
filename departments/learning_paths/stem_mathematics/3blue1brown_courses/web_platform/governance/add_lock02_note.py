p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/governance/REMAINING_SERIES_STRATEGY.md'
s=open(p,encoding='utf-8').read()
note = """
## Lockdown L02 discrepancy (FIX via expressive audio rebuild)
- `assets/audio/lockdown_math/lesson_02/manifest.json` (and .js) held STALE calendar-puzzle/modular-arithmetic content (4 narrated sections: sec-calendar-puzzle, sec-clock-modulo, sec-leap-years, sec-doomsday-trick; 13 cues) — NOT the exponential-growth/epidemics topic from the authoritative `data/lockdown_math/lesson_02.json`.
- Component page was built with those 4 calendar-themed narrated IDs (to keep DOM↔manifest parity) + 5 data-ID study sections carrying the real exponential-growth content.
- FIX: expressive audio builder MUST extract the LIVE DOM narrated IDs (the 4 calendar-themed ones) but write scripts about the ACTUAL exponential-growth content shown in those sections (linear vs exponential, doubling time, SIR model, logistic curve, flattening the curve). Keep section IDs/audio_file names; regenerate manifest ✓. After rebuild, manifest texts = exponential-growth topic (no stale calendar text). Flag any residual calendar text.
"""
if 'Lockdown L02 discrepancy' not in s:
    s += '\n' + note
open(p,'w',encoding='utf-8').write(s)
print('note added:', 'Lockdown L02 discrepancy' in s)
