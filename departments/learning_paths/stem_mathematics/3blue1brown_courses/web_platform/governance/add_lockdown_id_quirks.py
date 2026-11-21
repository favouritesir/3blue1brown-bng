p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/governance/VIDEO_ID_DATA_QUIRKS.md'
s=open(p,encoding='utf-8').read()
note='''
## Lockdown Math ID sweep — 2026-11-20 (verify_lockdown_authors.py + yt-dlp)
- L04 `5PcpBw5HbWo` (404, case typo) -> `5PcpBw5Hbwo` (3B1B "Complex number fundamentals | Ep.3") FIXED
- L06 `d_bZk5f2Z8Y` (404) -> `ZA4JkHKZM50` (3B1B continuous-probability clip) FIXED
- L07 `b3NxrZOup_U` (404) -> `GNcFjFmqEc8` (3B1B area/geometry related clip) FIXED
- L09 `fNk_zzaMoSs` (topic mismatch) -> `LyGKycYT2v0` (3B1B "Dot products and duality | Ch9") FIXED
- L10 `LqbZpur38nw` ("Beyond Mandelbrot", topic mismatch) -> NO dedicated 3B1B higher-degree-polynomial video; treat as content+audio ONLY + disclose (like probability L05, diffeq L06). SKIP video agent.
- L03 `bT1p5tJwn_0` (jbstatistics) -> `8idr1WZ1A7Q` (3B1B binomial) — fixed earlier; video rebuilt from official source.
- L08 `d-o3eB9sfls` verified 3B1B "Why is pi here? Basel problem" ✅
- L05 `mvmuCPvRoWQ` verified 3B1B "Euler's formula ... group theory" ✅
- Prob L05 `i3AkTO9HLXo` is Normalized Nerd (NOT 3B1B) -> content+audio only (already done).
IMPORTANT: oEmbed-verify each id right before launching its video agent (IDs can be stale/mistyped).
'''
if 'Lockdown Math ID sweep' not in s:
    s += '\n' + note
open(p,'w',encoding='utf-8').write(s)
print('note added:', 'Lockdown Math ID sweep' in s)
