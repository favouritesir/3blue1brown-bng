p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/governance/OFFICIAL_SOURCE_NOTES.md'
s=open(p,encoding='utf-8').read()
note = """
## CALCULUS L07 — `/lessons/limits` (পরবর্তী ব্যাচ)
Chapter 8 · "Limits and the definition of derivatives" · May 4 2017 · epigraph Anonymous Professor: "Calculus is all about making curvy things look straight" · সেকশন: Formal Definition of the derivative (df/dx as rise-over-run at x=2, nudge dx, derivative = what ratio approaches as dx→0; lim with dx→0; standard uses Δx or h instead of d; formal definition f'(x)=lim_{h→0}[f(x+h)−f(x)]/h; no "infinitely small" in it); No infinitely small rant (h = concrete finitely small nudge like 0.001; dx should be interpreted as finite nudge + limit); Why we care (zoom e^x at x=0 slope→1; how far to zoom? applied accuracy game vs mathematician's rigor; next ε-δ definition); footnote on infinitesimals/hyperreals. Video `kfF40MiS7zA` · next ε-δ lesson.

"""
if 'CALCULUS L07' not in s:
    s=s.replace('## নীতি', note + '## নীতি')
open(p,'w',encoding='utf-8').write(s)
print('L07 added:', 'CALCULUS L07' in s)
