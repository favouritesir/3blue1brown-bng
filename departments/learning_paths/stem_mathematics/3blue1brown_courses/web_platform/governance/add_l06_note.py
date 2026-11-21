note = """
## CALCULUS L06 — `/lessons/implicit-differentiation` (পরবর্তী ব্যাচ)
Chapter 7 · "Implicit differentiation, what's going on here?" · May 3 2017 · epigraph **Errett Bishop** · সেকশন: Implicit Curves (circle x²+y²=5², tangent (3,4), 2x·dx+2y·dy=0 → −x/y → −3/4); Related Rates (5m ladder, top 4m dropping 1m/s → dx/dt=4/3); Implicit Differentiation (S=x²+y² two-variable, dS=2x·dx+2y·dy, on-circle dS=0); Another example sin(x)·y²=x; ln(x) derivative via e^y=x → 1/x; Exercises (y²−x²=1 at (1,√2) → 1/√2); Next limits. Video `qb40J4N1fa4` · next `kfF40MiS7zA` (limits).
"""
p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/governance/OFFICIAL_SOURCE_NOTES.md'
s=open(p,encoding='utf-8').read()
marker='## নীতি'
if 'CALCULUS L06' not in s:
    s=s.replace(marker, note + '\n' + marker)
open(p,'w',encoding='utf-8').write(s)
print('L06 note added:', 'CALCULUS L06' in s)
